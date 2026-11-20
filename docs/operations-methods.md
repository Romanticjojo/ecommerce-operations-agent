# Operations analysis playbooks

In **Ask the agent**, open an analysis skill to see its question, scope and steps. Each run returns the actual query, selected purchase dates and result table. The calculation runs locally in both demo and model-enabled workspaces. Use **Run history** to reopen a result.

## What a month covers

A delivered item line counts as one sold unit. The order date is its purchase timestamp. Revenue is the sum of item prices in BRL, excluding freight. A customer’s persistent buyer key is `customer_unique_id`. The per-order `customer_id` links the order to this key.

The monthly playbooks accept a month only if its first and last calendar dates lie inside the snapshot’s span of delivered purchase dates and the selected filter. They also require at least one delivered purchase in each of the first and last seven days. A filter begins at the start date and ends immediately before the end date. For example, use June 1 through August 1 to include all of June and July. Sales and assortment use the latest qualifying consecutive pair. Seller growth and product outlook use the latest qualifying sequence of three. Price and volume uses all qualifying consecutive pairs.

These tests remove visibly truncated months and gaps. They cannot establish that every order was captured in an interior month. In Olist v2, August 29, 2018 is the final purchase date of a delivered order. The complete comparison months therefore end in July even though the source also includes later orders with other statuses.

## Sales and growth

1. Sum delivered item revenue and count distinct delivered orders by purchase month.
2. Count distinct identified buyers. Divide identified orders by identified buyers for purchase frequency. Divide total item revenue by delivered orders for average order value.
3. Subtract the previous month from the latest and show the five categories with the largest absolute revenue change. A category present in only one month contributes its full gain or loss. The category rows describe selected contributors and need not total platform growth.

In June and July 2018, item revenue moved from **BRL 856,077.86 to BRL 867,953.46**, a gain of BRL 11,875.60. Buyers rose from 6,061 to 6,100 and average order value rose from BRL 140.36 to BRL 140.92. Watches and gifts contributed BRL 10,137.22 of growth, while bed, bath and table declined by BRL 16,451.85. These component movements help select categories for investigation.

## Customer retention and value

1. Read each identified buyer’s first delivered order across the entire snapshot before applying the purchase-date filter. Order ID breaks a tie between identical timestamps.
2. Assign one first-order category per buyer using the highest sum of item prices in that order. Translated category name breaks a tie. Missing category information receives the label `unknown`.
3. Include a buyer only when the first purchase is in the selected range and 90 days of follow-up fit within both the selected end and the last observed delivered purchase timestamp. Count any additional distinct delivered order through day 90 as a repeat, including another order at the same timestamp.
4. For the 15 largest first-category cohorts, show eligible buyers, repeat buyers, repeat percentage, buyers without a repeat and mean 90-day item revenue per buyer.

On the full snapshot, **282 of 7,126** buyers whose first observed category was bed, bath and table returned within 90 days (3.96%). The remaining 6,844 form a historical segment for designing a win-back test. This observation window cannot establish permanent churn, purchases elsewhere or an individual buyer’s propensity to respond. The cohort also cannot measure first-visit conversion because Olist contains no visitor population.

## Products and categories

Count item lines, distinct sellers and distinct products by category. Report previous and latest unit counts and rank the top 15 by absolute change, with category name breaking ties. Track a category that gains its first observed sale or falls to zero in the comparison. The active seller and product counts refer to the latest month.

Bed, bath and table fell from **764 to 617 units** in June–July 2018. The category had 87 selling merchants in July. Check actual stock and seller capacity before making a sourcing decision. Completed purchases alone cannot reveal unavailable inventory, search demand or product views.

## Price and volume

For each product and month, require at least three delivered lines with positive prices. Compute the mean realized price per sold unit and round it to cents. Pair the same product across qualifying adjacent months and group pairs by price direction. Each pair contributes one observation. A product can contribute to several pairs. Report the number of pairs and distinct products, median percent price change, median signed change in units sold, and the percentage of pairs where unit sales increased.

On Olist v2 there were **535 higher-price pairs, 487 lower-price pairs and 1,561 unchanged-price pairs**. The median unit change was zero for all three groups. Promotion assignment, list prices, stock, browsing and a counterfactual comparison are unavailable. A pricing experiment would need an eligible control group, stock checks and margin data.

## Seller performance and growth

Use the seller on each delivered item line. Sum each seller’s item revenue in three consecutive months. Count each order once per participating seller. Keep sellers with at least five orders each month and positive revenue in the first two months. Rank eligible sellers by the number of month-to-month increases, then the weaker of their two percentage changes (to two decimals), latest revenue and seller ID. Return the first 15. Latest revenue share divides the seller’s revenue by all delivered marketplace item revenue in that month, including sellers outside the ranking.

For May–July 2018, seller `5656537e588803a555b8eb41f07a944b` recorded **BRL 175.61 → 617.94 → 896.06** on 9, 15 and 24 orders. The weaker monthly growth rate was 45.01%. Its July revenue represented 0.103% of the marketplace. This playbook prioritizes steady revenue growth. Use **Merchant scorecard** in Ask to rank service performance. Traffic concentration and exposure-to-purchase conversion require impression data.

## Product sales outlook

1. Count monthly delivered item lines per product ID and show its translated category. Within the three covered months, fill an absent product-month with zero observed units. Keep products with ten or more total units across the window.
2. Rank by the absolute change from the first to the last month. Latest units and product ID break ties. Return the first 15 for review. The **planning units** column is the median of the three counts, a reference for the following month.
3. For two successive increases, check stock, lead time and supplier capacity before testing a small reorder. For two successive decreases, check availability before reducing orders. Two opening zeroes flag a possible launch and two closing zeroes flag a possibly inactive listing. For mixed movement, monitor weekly demand before adjusting the plan.

For an **August 2018** planning exercise, furniture product `2ff995aead9c63a1f37a07b3664ead37` sold **2 → 8 → 21 units** from May through July. A small reorder test would be reasonable after verifying stock and lead time. In the same period, watches and gifts product `53b36df67ebb7c41585e8d54d6772e08` sold 114 → 9 → 11 units. The 11-unit median provides a reference while investigating the May spike. These are historical decisions at the snapshot horizon. Future demand, seasonality, listing activity, cancellations, lead times and on-hand stock require separate evidence before committing to an order.

## Reproduce

Run `.venv/bin/python -m pytest -q tests/test_operations_skills.py` for the controlled order fixtures. On the Olist v2 import, choose a skill with the date fields empty to reproduce the examples above. Pasting the SQL from its evidence panel into a read-only DuckDB connection to the same snapshot reproduces the result table. The analyses use the existing source tables and reporting views, so an existing v2 import can run them immediately.
