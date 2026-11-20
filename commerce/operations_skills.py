"""Replayable, read-only analyses of the existing Olist snapshot."""
from .data import rows
from .plans import iso_day


def _spec(title, description, scope, question, *steps):
    return dict(title=title, description=description, scope=scope, question=question, steps=list(steps))


SPECS = {
    'sales-growth': _spec(
        'Sales and growth', 'Break down the latest revenue change into buyers, buying frequency, basket value and category movements.',
        'Two consecutive covered months of delivered purchases. Amounts exclude freight.',
        'What drove the change in platform sales?',
        'Choose the latest pair of covered months.', 'Compare orders, buyers, orders per buyer and average order value.',
        'Identify the largest category contributions to the revenue change.'),
    'retention': _spec(
        'Customer retention and value', 'Compare repeat purchasing and 90-day spend by the category of a buyer’s first observed order.',
        'Identified buyers with 90 full days of follow-up. Inactivity is a historical signal for win-back tests.',
        'Which first-purchase categories lead to repeat purchases within 90 days?',
        'Find each buyer’s first delivered order across the snapshot.', 'Assign its leading category and require 90 days of follow-up.',
        'Count repeat buyers, buyers without a repeat and revenue per buyer.'),
    'assortment': _spec(
        'Products and categories', 'Find the categories with the largest changes in units sold and check how many sellers serve them.',
        'Two consecutive covered months. Delivered units and active sellers are observable. Stock and page views are unavailable.',
        'Which categories gained or lost the most units?',
        'Count delivered item lines by category and month.', 'Keep categories entering or leaving the observed assortment.',
        'Rank by absolute unit change and inspect active sellers and products.'),
    'price-volume': _spec(
        'Price and volume', 'Compare unit sales when the same product sold at a higher, lower or unchanged average price.',
        'Adjacent covered months with at least three priced units per SKU in both months. Pricing decisions require a controlled test.',
        'How did unit sales change when the same product sold at a different price?',
        'Measure monthly units and realized unit price per SKU.', 'Match the same SKU across consecutive months.',
        'Compare median unit changes for price increases, decreases and unchanged prices.'),
    'seller-growth': _spec(
        'Seller performance and growth', 'Find sellers with sustained item-revenue growth and measure their share of marketplace sales.',
        'Three consecutive covered months, with at least five distinct delivered orders per seller each month. Sales measure observed market share.',
        'Which sellers grew consistently across three months?',
        'Compare seller revenue in three covered months.', 'Count positive monthly changes and check minimum order volume.',
        'Rank by continuity and the weaker monthly growth rate, then inspect revenue share.'),
    'product-trend': _spec(
        'Product sales outlook', 'Track three monthly unit counts for each SKU and select a next-month stock or assortment check.',
        'Three consecutive covered months and at least ten delivered units per SKU across them. Planning quantities describe historical sales.',
        'Which products should I review for reordering next month?',
        'Build a three-month unit history per SKU, including zero-sales months.', 'Classify consecutive gains, declines or a mixed pattern.',
        'Use the median unit count as a planning reference and verify inventory before ordering.'),
}


def _date_literal(value, default):
    return f"DATE '{iso_day(value)}'" if value else default


def _covered_months(start, end):
    lower = _date_literal(start, "DATE '-infinity'")
    upper = _date_literal(end, "DATE 'infinity'")
    return f"""WITH delivered_dates AS (
    SELECT purchased_at::DATE AS day FROM order_summary WHERE status = 'delivered'
), coverage AS (
    SELECT min(day) AS first_day, max(day) AS last_day FROM delivered_dates
), covered AS (
    SELECT date_trunc('month', day)::DATE AS month
    FROM delivered_dates, coverage WHERE day IS NOT NULL
    GROUP BY month, first_day, last_day
    HAVING month >= greatest(first_day, {lower})
       AND last_day(month) <= last_day AND last_day(month) < {upper}
       AND min(day) <= month + 6 AND max(day) >= last_day(month) - 6
)"""


def _window(count):
    # Requiring the intervening month prevents two distant active months from becoming neighbours.
    previous = "JOIN covered p ON p.month = c.month - INTERVAL '1 month'"
    first = "JOIN covered f ON f.month = c.month - INTERVAL '2 months'" if count == 3 else ''
    return f""", window_months AS (
    SELECT c.month AS latest, p.month AS previous{', f.month AS first' if first else ''}
    FROM covered c {previous} {first}
    ORDER BY latest DESC LIMIT 1
)"""


_SALES = """, monthly AS (
    SELECT date_trunc('month', o.purchased_at)::DATE AS month, count(*) AS orders,
           count(DISTINCT c.customer_unique_id) AS buyers,
           count(c.customer_unique_id) / nullif(buyers, 0) AS frequency,
           sum(o.item_revenue) AS revenue, revenue / orders AS aov
    FROM order_summary o
    LEFT JOIN customers c USING(customer_id)
    CROSS JOIN window_months w
    WHERE o.status = 'delivered' AND o.purchased_at >= previous AND o.purchased_at < latest + INTERVAL '1 month'
    GROUP BY month
), categories AS (
    SELECT category, coalesce(sum(item_revenue) FILTER (WHERE purchased_at < latest), 0) AS prev,
           coalesce(sum(item_revenue) FILTER (WHERE purchased_at >= latest), 0) AS curr
    FROM category_sales CROSS JOIN window_months
    WHERE purchased_at >= previous AND purchased_at < latest + INTERVAL '1 month'
    GROUP BY category ORDER BY abs(curr - prev) DESC, category LIMIT 5
), measures AS (
    SELECT v.position, v.measure, v.unit, v.previous_value, v.latest_value
    FROM window_months JOIN monthly p ON p.month = previous JOIN monthly c ON c.month = latest,
    LATERAL (VALUES
      (1, 'Item revenue', 'BRL', p.revenue, c.revenue), (2, 'Delivered orders', 'orders', p.orders, c.orders),
      (3, 'Buyers', 'identified buyers', p.buyers, c.buyers), (4, 'Orders per buyer', 'orders / buyer', p.frequency, c.frequency),
      (5, 'Average order value', 'BRL / order', p.aov, c.aov)
    ) AS v(position, measure, unit, previous_value, latest_value)
    UNION ALL SELECT 6, 'Category / ' || category, 'BRL', prev, curr FROM categories
)
SELECT measure, unit, round(previous_value, 3) AS previous_value, round(latest_value, 3) AS latest_value,
       round(latest_value - previous_value, 3) AS change, previous AS previous_month, latest AS latest_month
FROM measures CROSS JOIN window_months ORDER BY position, abs(change) DESC NULLS LAST, measure"""


_ASSORTMENT = """
SELECT category, count(*) FILTER (WHERE purchased_at < latest) AS previous_units,
       count(*) FILTER (WHERE purchased_at >= latest) AS latest_units,
       latest_units - previous_units AS unit_change,
       count(DISTINCT seller_id) FILTER (WHERE purchased_at >= latest) AS active_sellers,
       count(DISTINCT product_id) FILTER (WHERE purchased_at >= latest) AS active_products,
       previous AS previous_month, latest AS latest_month
FROM category_sales CROSS JOIN window_months
WHERE purchased_at >= previous AND purchased_at < latest + INTERVAL '1 month'
GROUP BY category, previous, latest ORDER BY abs(unit_change) DESC, category LIMIT 15"""


_PRICE = """, sku_month AS (
    SELECT month, product_id, count(*) AS units, round(avg(item_revenue), 2) AS price
    FROM category_sales JOIN covered ON date_trunc('month', purchased_at) = month
    WHERE product_id IS NOT NULL AND item_revenue > 0 GROUP BY month, product_id HAVING units >= 3
), pairs AS (
    SELECT c.product_id, c.month, p.month AS previous_month, c.units - p.units AS unit_change,
           100.0 * (c.price / p.price - 1) AS price_pct,
           CASE WHEN c.price > p.price THEN 'Higher' WHEN c.price < p.price THEN 'Lower' ELSE 'Unchanged' END AS price_direction
    FROM sku_month c JOIN sku_month p ON c.product_id = p.product_id AND p.month = c.month - INTERVAL '1 month'
)
SELECT price_direction, count(*) AS sku_month_pairs, count(DISTINCT product_id) AS distinct_products,
       round(median(price_pct), 2) AS median_price_change_pct, median(unit_change) AS median_unit_change,
       round(100.0 * avg((unit_change > 0)::INT), 2) AS pairs_with_unit_growth_pct,
       min(previous_month) AS from_month, max(month) AS through_month
FROM pairs GROUP BY price_direction ORDER BY sku_month_pairs DESC, price_direction"""


_SELLER = """, sellers AS (
    SELECT seller_id, coalesce(sum(item_revenue) FILTER (WHERE purchased_at < previous), 0) AS first_revenue,
           coalesce(sum(item_revenue) FILTER (WHERE purchased_at >= previous AND purchased_at < latest), 0) AS middle_revenue,
           coalesce(sum(item_revenue) FILTER (WHERE purchased_at >= latest), 0) AS latest_revenue,
           count(DISTINCT order_id) FILTER (WHERE purchased_at < previous) AS first_orders,
           count(DISTINCT order_id) FILTER (WHERE purchased_at >= previous AND purchased_at < latest) AS middle_orders,
           count(DISTINCT order_id) FILTER (WHERE purchased_at >= latest) AS latest_orders
    FROM category_sales CROSS JOIN window_months
    WHERE purchased_at >= first AND purchased_at < latest + INTERVAL '1 month'
    GROUP BY seller_id
), shares AS (
    SELECT *, 100.0 * latest_revenue / nullif(sum(latest_revenue) OVER (), 0) AS share FROM sellers
)
SELECT seller_id, first_revenue, middle_revenue, latest_revenue,
       ((middle_revenue > first_revenue)::INT + (latest_revenue > middle_revenue)::INT) AS growth_months,
       round(100.0 * least(middle_revenue / first_revenue - 1, latest_revenue / middle_revenue - 1), 2) AS weaker_growth_pct,
       first_orders, middle_orders, latest_orders, round(share, 3) AS latest_revenue_share_pct,
       first AS first_month, latest AS latest_month
FROM shares CROSS JOIN window_months
WHERE seller_id IS NOT NULL AND least(first_orders, middle_orders, latest_orders) >= 5 AND least(first_revenue, middle_revenue) > 0
ORDER BY growth_months DESC, weaker_growth_pct DESC, latest_revenue DESC, seller_id LIMIT 15"""


_PRODUCT = """, items AS (
    SELECT product_id, category, count(*) FILTER (WHERE purchased_at < previous) AS first_units,
           count(*) FILTER (WHERE purchased_at >= previous AND purchased_at < latest) AS middle_units,
           count(*) FILTER (WHERE purchased_at >= latest) AS latest_units
    FROM category_sales CROSS JOIN window_months
    WHERE product_id IS NOT NULL AND purchased_at >= first AND purchased_at < latest + INTERVAL '1 month'
    GROUP BY product_id, category HAVING count(*) >= 10
)
SELECT product_id, category, first_units, middle_units, latest_units,
       list_median([first_units, middle_units, latest_units]) AS planning_units,
       CASE WHEN first_units = 0 AND middle_units = 0 THEN 'Check the launch date and confirm demand before ordering'
            WHEN middle_units = 0 AND latest_units = 0 THEN 'Check whether the listing is still available'
            WHEN first_units < middle_units AND middle_units < latest_units THEN 'Test a small reorder after checking stock'
            WHEN first_units > middle_units AND middle_units > latest_units THEN 'Check availability before reducing orders'
            ELSE 'Hold the baseline and monitor weekly sales' END AS next_action,
       first AS first_month, previous AS middle_month, latest AS latest_month, (latest + INTERVAL '1 month')::DATE AS planning_month
FROM items CROSS JOIN window_months
ORDER BY abs(latest_units - first_units) DESC, latest_units DESC, product_id LIMIT 15"""


def _retention(start, end):
    lower = _date_literal(start, "DATE '-infinity'")
    upper = _date_literal(end, "DATE 'infinity'")
    return f"""WITH orders_by_buyer AS (
    SELECT o.order_id, c.customer_unique_id AS buyer, o.purchased_at, o.item_revenue
    FROM order_summary o JOIN customers c USING(customer_id)
    WHERE o.status = 'delivered' AND c.customer_unique_id IS NOT NULL AND o.purchased_at IS NOT NULL
), first_order AS (
    SELECT * FROM orders_by_buyer
    QUALIFY row_number() OVER (PARTITION BY buyer ORDER BY purchased_at, order_id) = 1
), eligible AS (
    SELECT * FROM first_order
    WHERE purchased_at >= {lower} AND purchased_at + INTERVAL '90 days' < {upper}
      AND purchased_at + INTERVAL '90 days' <= (SELECT max(purchased_at) FROM order_summary WHERE status = 'delivered')
), first_category AS (
    SELECT c.order_id, c.category, sum(c.item_revenue) AS category_revenue
    FROM category_sales c JOIN eligible USING(order_id) GROUP BY c.order_id, c.category
    QUALIFY row_number() OVER (PARTITION BY c.order_id ORDER BY category_revenue DESC NULLS LAST, c.category) = 1
), buyer_window AS (
    SELECT e.buyer, coalesce(f.category, 'unknown') AS first_category,
           count(*) AS orders, sum(o.item_revenue) AS spend
    FROM eligible e JOIN orders_by_buyer o ON o.buyer = e.buyer
       AND o.purchased_at BETWEEN e.purchased_at AND e.purchased_at + INTERVAL '90 days'
    LEFT JOIN first_category f ON f.order_id = e.order_id GROUP BY e.buyer, f.category
)
SELECT first_category, count(*) AS buyers, count(*) FILTER (WHERE orders > 1) AS repeat_buyers,
       round(100.0 * repeat_buyers / buyers, 2) AS repeat_pct, buyers - repeat_buyers AS no_repeat_by_90d,
       round(avg(spend), 2) AS revenue_per_buyer_brl
FROM buyer_window GROUP BY first_category ORDER BY buyers DESC, first_category LIMIT 15"""


def _conclusion(skill_id, table):
    r = table[0]
    if skill_id == 'retention':
        strongest = max(table, key=lambda x: (x['repeat_pct'], x['buyers']))
        return (f"Among the {len(table)} largest first-purchase cohorts shown, {strongest['first_category']} had the highest "
                f"observed 90-day repeat rate: {strongest['repeat_buyers']:,} of {strongest['buyers']:,} buyers "
                f"({strongest['repeat_pct']:.2f}%). In the largest cohort ({r['first_category']}), "
                f"{r['no_repeat_by_90d']:,} of {r['buyers']:,} had no repeat by day 90. Test a win-back offer against a holdout.")
    if skill_id == 'price-volume':
        comparisons = ', '.join(f"{p['price_direction'].lower()} prices: {p['median_unit_change']:+g} median units "
                                f"({p['sku_month_pairs']:,} pairs)" for p in table)
        return f"Across matched consecutive SKU-months, {comparisons}. Use these associations to select products for a pricing test."
    latest = r['latest_month'][:7]
    if skill_id == 'sales-growth':
        by_measure = {row['measure']: row for row in table}
        buyers, freq, aov = (by_measure[m] for m in ('Buyers', 'Orders per buyer', 'Average order value'))
        frequency = 'unavailable' if freq['latest_value'] is None or freq['previous_value'] is None else f"{freq['previous_value']:.3f} to {freq['latest_value']:.3f}"
        answer = (f"From {r['previous_month'][:7]} to {latest}, delivered item revenue moved from BRL {r['previous_value']:,.2f} "
                  f"to BRL {r['latest_value']:,.2f}. Buyers moved from {buyers['previous_value']:,.0f} to {buyers['latest_value']:,.0f}, "
                  f"orders per identified buyer from {frequency}, and average order value from BRL {aov['previous_value']:.2f} to BRL {aov['latest_value']:.2f}.")
        movers = [x for x in table if x['measure'].startswith('Category / ')]
        for direction, label in [(1, 'gain'), (-1, 'decline')]:
            mover = next((x for x in movers if direction * x['change'] > 0), None)
            if mover:
                answer += f" The largest category {label} shown was {mover['measure'][11:]} (BRL {mover['change']:+,.2f})."
        return answer
    if skill_id == 'assortment':
        return (f"Comparing {r['previous_month'][:7]} with {latest}, {r['category']} had the largest absolute unit change "
                f"({r['previous_units']:,} to {r['latest_units']:,}). It had {r['active_sellers']:,} active sellers in {latest}. "
                "Check seller capacity and current stock before changing the assortment.")
    if skill_id == 'seller-growth':
        share = r['latest_revenue_share_pct']
        share_text = 'unavailable' if share is None else f"{share:.3f}%"
        return (f"From {r['first_month'][:7]} through {latest}, seller {r['seller_id']} ranked first among eligible sellers. "
                f"Revenue rose in {r['growth_months']} of 2 comparisons. Its marketplace revenue share in {latest} "
                f"was {share_text}. Use the order counts to size any seller-support pilot.")
    answer = (f"For {r['planning_month'][:7]} planning, product {r['product_id']} ({r['category']}) moved "
              f"from {r['first_units']} to {r['middle_units']} to {r['latest_units']} units over {r['first_month'][:7]}–{latest}. "
              f"Its three-month median is {r['planning_units']:g} units. {r['next_action']}.")
    rising = next((p for p in table if p['first_units'] < p['middle_units'] < p['latest_units']), None)
    if rising and rising != r:
        answer += (f" For a small reorder test, check stock for {rising['product_id']} "
                   f"({rising['first_units']} → {rising['middle_units']} → {rising['latest_units']} units).")
    return answer


def run(con, skill_id, start=None, end=None):
    if skill_id not in SPECS:
        raise ValueError('unknown operations skill')
    if start and end and iso_day(start) >= iso_day(end):
        raise ValueError('invalid period')
    if skill_id == 'retention':
        sql = _retention(start, end)
        warnings = ['First means first observed in Olist. A missing repeat can reflect purchases outside the marketplace. The table shows the 15 largest eligible first-category cohorts.']
    else:
        sql = _covered_months(start, end)
        if skill_id == 'price-volume':
            sql += _PRICE
        else:
            sql += _window(3 if skill_id in ('seller-growth', 'product-trend') else 2)
            sql += {'sales-growth': _SALES, 'assortment': _ASSORTMENT, 'seller-growth': _SELLER, 'product-trend': _PRODUCT}[skill_id]
        warnings = ['Only whole calendar months inside the observed delivered-purchase span and selected dates qualify. Each month needs purchases in its first and last week.']
    warnings.append(SPECS[skill_id]['scope'])
    table = rows(con, sql)
    answer = _conclusion(skill_id, table) if table else 'No eligible comparison in this date range. Widen the purchase dates and check the coverage and sample rules.'
    return dict(answer=answer, table=table, sql=sql, warnings=warnings)
