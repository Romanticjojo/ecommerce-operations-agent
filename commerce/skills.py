"""Operator-selected SOPs. Only packaged queries receive a local database connection."""
import unicodedata

import duckdb

from . import operations_skills, review_skills
from .data import rows
from .plans import iso_day


FULFILLMENT = {
    "title": "Delivery performance",
    "description": "Locate seller and state-to-state lanes with frequent late deliveries.",
    "scope": "Delivered, single-seller orders with both timestamps, grouped by seller and shipping lane. At least 20 orders per group. Returns and refunds are unavailable.",
    "question": "Which sellers and shipping lanes should we investigate for late delivery?",
    "steps": [
        "Assign each delivered order to one seller and its origin and destination states.",
        "Compare actual and promised calendar dates and count the latest eligible low ratings.",
        "Rank the five highest late shares in each group type and inspect the sample before changing a promise.",
    ],
}

SKILLS = {
    **operations_skills.SPECS, "fulfillment": FULFILLMENT,
    **review_skills.SPECS,
}
ORDER = ("sales-growth", "retention", "assortment", "price-volume", "seller-growth",
         "fulfillment", "reviews-aftercare", "merchant-score", "product-trend")


def catalog():
    return [{"id": slug, **SKILLS[slug]} for slug in ORDER]


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split()).rstrip(".!? ")


# Exact phrases keep unsupported qualifiers (for example state, seller or coupon)
# from disappearing when routing an offline question to a fixed procedure.
_ALIASES = {
    "sales-growth": ("explain sales growth", "why did revenue change"),
    "retention": ("analyze customer retention", "which customers buy again"),
    "assortment": ("analyze product categories", "which categories are growing"),
    "price-volume": ("compare prices and sales volume", "analyze price and volume"),
    "seller-growth": ("which sellers are growing steadily", "analyze seller growth"),
    "fulfillment": ("which shipping lanes are late", "analyze fulfillment"),
    "reviews-aftercare": ("analyze review sentiment", "analyze product reviews"),
    "merchant-score": ("rank merchants", "rank sellers", "show merchant rankings"),
    "product-trend": ("analyze product sales trends", "which products should i reorder"),
}


def match(question):
    text = normalized(question)
    for slug, spec in SKILLS.items():
        if text in (slug, normalized(spec["title"]), normalized(spec["question"]), *_ALIASES[slug]):
            return slug
    return None


def fulfillment(con, start, end):
    conditions = ["o.order_status = 'delivered'", "o.order_delivered_customer_date IS NOT NULL",
                  "o.order_estimated_delivery_date IS NOT NULL"]
    if start:
        conditions.append(f"o.order_purchase_timestamp >= DATE '{iso_day(start)}'")
    if end:
        conditions.append(f"o.order_purchase_timestamp < DATE '{iso_day(end)}'")
    sql = f"""WITH sole_seller AS (
    SELECT order_id, min(seller_id) AS seller_id FROM order_items
    GROUP BY order_id HAVING count(DISTINCT seller_id) = 1 AND count(seller_id) = count(*)
), orders_in_scope AS (
    SELECT o.order_id, si.seller_id, s.seller_state AS origin, c.customer_state AS destination,
           o.order_delivered_customer_date::DATE > o.order_estimated_delivery_date::DATE AS late,
           r.review_score
    FROM orders o JOIN sole_seller si USING(order_id) JOIN sellers s USING(seller_id)
    LEFT JOIN customers c USING(customer_id) LEFT JOIN order_review_delivery r USING(order_id)
    WHERE {' AND '.join(conditions)}
), populations AS (
    SELECT 'Seller' AS level, seller_id AS entity, late, review_score FROM orders_in_scope
    UNION ALL
    SELECT 'State lane', origin || ' → ' || destination, late, review_score FROM orders_in_scope
    WHERE origin IS NOT NULL AND destination IS NOT NULL
), counted AS (
    SELECT level, entity, count(*) AS orders, count(*) FILTER (WHERE late) AS late_orders,
           100.0 * late_orders / orders AS late_pct,
           count(review_score) FILTER (WHERE late) AS late_reviewed,
           count(*) FILTER (WHERE late AND review_score <= 2) AS late_negative,
           count(review_score) FILTER (WHERE NOT late) AS on_time_reviewed,
           count(*) FILTER (WHERE NOT late AND review_score <= 2) AS on_time_negative
    FROM populations GROUP BY level, entity HAVING count(*) >= 20
), ranked AS (
    SELECT *, row_number() OVER (PARTITION BY level ORDER BY late_pct DESC, orders DESC, entity) AS position
    FROM counted
)
SELECT level, position, entity, orders, late_orders, round(late_pct, 1) AS late_pct,
       late_reviewed, late_negative, on_time_reviewed, on_time_negative
FROM ranked WHERE position <= 5 ORDER BY level, position"""
    table = rows(con, sql)
    findings = []
    for row in table:
        if row["position"] == 1:
            findings.append(f"{row['level']} {row['entity']} had {row['late_orders']:,} late deliveries "
                            f"among {row['orders']:,} orders ({row['late_pct']:.1f}%).")
    answer = (" ".join(findings) + " Check handover timing and the promised transit time for these groups."
              if findings else "No seller or state lane had 20 eligible deliveries in this period.")
    return {"answer": answer, "table": table, "sql": sql, "warnings": [
        "Seller and lane rows describe overlapping orders. A route is a pair of states. Timing reflects both merchant and carrier performance.",
        "A negative review scores 1 or 2. Use the delivery comparison in Ask to see both review rates, intervals and exclusions.",
    ]}


def run(db, slug, start, end):
    iso_day(start)
    iso_day(end)
    with duckdb.connect(str(db), read_only=True) as con:
        if slug == "fulfillment":
            return fulfillment(con, start, end)
        if slug in operations_skills.SPECS:
            return operations_skills.run(con, slug, start, end)
        if slug in review_skills.SPECS:
            return review_skills.run(con, slug, start, end)
    raise ValueError("unknown_skill")
