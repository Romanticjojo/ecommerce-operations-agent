"""The input contract mirrors Olist header spelling, including the two 'lenght' columns."""

TEXT, INT, TIME, MONEY = 'VARCHAR', 'INTEGER', 'TIMESTAMP', 'DECIMAL(18,2)'
RAW = {
    'orders': {'order_id': TEXT, 'customer_id': TEXT, 'order_status': TEXT, 'order_purchase_timestamp': TIME,
               'order_approved_at': TIME, 'order_delivered_carrier_date': TIME, 'order_delivered_customer_date': TIME,
               'order_estimated_delivery_date': TIME},
    'order_items': {'order_id': TEXT, 'order_item_id': INT, 'product_id': TEXT, 'seller_id': TEXT,
                    'shipping_limit_date': TIME, 'price': MONEY, 'freight_value': MONEY},
    'order_payments': {'order_id': TEXT, 'payment_sequential': INT, 'payment_type': TEXT,
                       'payment_installments': INT, 'payment_value': MONEY},
    'order_reviews': {'review_id': TEXT, 'order_id': TEXT, 'review_score': INT, 'review_comment_title': TEXT,
                      'review_comment_message': TEXT, 'review_creation_date': TIME, 'review_answer_timestamp': TIME},
    'customers': {'customer_id': TEXT, 'customer_unique_id': TEXT, 'customer_zip_code_prefix': TEXT,
                  'customer_city': TEXT, 'customer_state': TEXT},
    'products': {'product_id': TEXT, 'product_category_name': TEXT, 'product_name_lenght': INT,
                 'product_description_lenght': INT, 'product_photos_qty': INT, 'product_weight_g': INT,
                 'product_length_cm': INT, 'product_height_cm': INT, 'product_width_cm': INT},
    'sellers': {'seller_id': TEXT, 'seller_zip_code_prefix': TEXT, 'seller_city': TEXT, 'seller_state': TEXT},
}
TRANSLATION = {'product_category_name': TEXT, 'product_category_name_english': TEXT}

KEYS = {'orders': ('order_id',), 'order_items': ('order_id', 'order_item_id'),
        'order_payments': ('order_id', 'payment_sequential'), 'customers': ('customer_id',),
        'products': ('product_id',), 'sellers': ('seller_id',),
        'category_translation': ('product_category_name',)}

VIEWS = {
    'order_summary': 'One row per order, all statuses. Filter status to delivered for sales.',
    'category_sales': 'One row per delivered order item. Count distinct order_id for order counts.',
    'monthly_sales': 'One row per purchase month with delivered orders.',
    'review_delivery': 'One row per valid review on a delivered order with complete delivery timestamps.',
    'order_review_delivery': 'One latest eligible review per delivered order, for inference.',
}

DESCRIPTIONS = {
    'order_id': 'Order identifier.', 'status': 'Source order status.',
    'purchased_at': 'Purchase timestamp in source local time.', 'item_revenue': 'Sum of item prices in BRL, excluding freight; on category_sales this is the item price.',
    'payment_total': 'Sum of recorded payments in BRL.', 'state': 'Customer state at purchase, or unknown.',
    'freight_total': 'Sum of item freight in BRL.', 'item_count': 'Count of order item rows.',
    'customer_id': 'Order-level customer key.', 'category': 'English category when translated, otherwise source category or unknown.',
    'product_id': 'Product identifier.', 'seller_id': 'Seller identifier.', 'order_item_id': 'Item sequence within order.',
    'freight_value': 'Item freight in BRL.', 'month': 'First date of the purchase month.',
    'order_count': 'Number of delivered orders.', 'aov': 'Item revenue per delivered order in BRL.',
    'review_id': 'Review identifier; repetitions are possible.', 'review_score': 'Integer rating from 1 to 5.',
    'late_timestamp': 'Actual delivery timestamp exceeds estimated timestamp.', 'late_day': 'Actual delivery date exceeds estimated date.',
    'actual_delivery': 'Customer delivery timestamp.', 'estimated_delivery': 'Estimated delivery timestamp.',
    'source_row': 'One-based CSV data record, excluding header.', 'review_creation_date': 'Survey creation timestamp.',
    'review_answer_timestamp': 'Survey answer timestamp.',
}

RAW_DESCRIPTIONS = {
    'customer_unique_id': 'Customer identifier across purchases.',
    'customer_zip_code_prefix': 'Customer postal-code prefix, stored as text.', 'customer_city': 'Customer city.',
    'customer_state': 'Two-letter customer state.', 'order_status': 'Recorded order status.',
    'order_purchase_timestamp': 'Order placement timestamp.', 'order_approved_at': 'Payment approval timestamp.',
    'order_delivered_carrier_date': 'Carrier handover timestamp.', 'order_delivered_customer_date': 'Customer delivery timestamp.',
    'order_estimated_delivery_date': 'Promised delivery timestamp.', 'shipping_limit_date': 'Seller handover deadline.',
    'price': 'Price of one item in BRL, excluding freight.', 'payment_sequential': 'Payment sequence within order.',
    'payment_type': 'Payment method.', 'payment_installments': 'Number of installments.',
    'payment_value': 'Recorded payment amount in BRL.', 'review_comment_title': 'Optional written review title.',
    'review_comment_message': 'Optional written review.', 'product_category_name': 'Original product category.',
    'product_category_name_english': 'English category translation.', 'product_name_lenght': 'Product title length in characters.',
    'product_description_lenght': 'Product description length in characters.', 'product_photos_qty': 'Count of product photos.',
    'product_weight_g': 'Product weight in grams.', 'product_length_cm': 'Product length in centimeters.',
    'product_height_cm': 'Product height in centimeters.', 'product_width_cm': 'Product width in centimeters.',
    'seller_zip_code_prefix': 'Seller postal-code prefix, stored as text.', 'seller_city': 'Seller city.', 'seller_state': 'Two-letter seller state.',
} | DESCRIPTIONS

METRICS = [
    {'id': 'item_revenue', 'label': 'Item revenue', 'definition': 'Sum of delivered item prices, excluding freight.', 'unit': 'BRL'},
    {'id': 'order_count', 'label': 'Delivered orders', 'definition': 'Distinct delivered orders by purchase date.', 'unit': 'orders'},
    {'id': 'aov', 'label': 'Average order value', 'definition': 'Delivered item revenue divided by delivered order count.', 'unit': 'BRL/order'},
    {'id': 'payment_total', 'label': 'Payment total', 'definition': 'Sum of independently aggregated recorded payments on delivered orders.', 'unit': 'BRL'},
    {'id': 'freight_total', 'label': 'Freight total', 'definition': 'Sum of freight values on delivered items.', 'unit': 'BRL'},
    {'id': 'reviewed_order_count', 'label': 'Reviewed orders', 'definition': 'Delivered orders with both delivery timestamps and a valid review.', 'unit': 'orders'},
    {'id': 'negative_count', 'label': 'Negative reviews', 'definition': 'Eligible orders scoring 1 or 2 in their selected review.', 'unit': 'orders'},
    {'id': 'negative_rate', 'label': 'Negative review rate', 'definition': 'Share scoring 1 or 2 among eligible delivered orders, using one review per order.', 'unit': 'fraction'},
    {'id': 'risk_difference', 'label': 'Risk difference', 'definition': 'Late minus on-time order-level negative review rate.', 'unit': 'fraction'},
]

CREATE_VIEWS = """
CREATE VIEW order_summary AS
WITH items AS (
    SELECT order_id, sum(price) AS item_revenue, sum(freight_value) AS freight_total, count(*) AS item_count
    FROM order_items GROUP BY order_id
), payments AS (
    SELECT order_id, sum(payment_value) AS payment_total FROM order_payments GROUP BY order_id
)
SELECT o.order_id, o.order_status AS status, o.order_purchase_timestamp AS purchased_at,
       coalesce(i.item_revenue, 0) AS item_revenue, coalesce(p.payment_total, 0) AS payment_total,
       coalesce(c.customer_state, 'unknown') AS state, coalesce(i.freight_total, 0) AS freight_total,
       coalesce(i.item_count, 0) AS item_count, o.customer_id
FROM orders o LEFT JOIN items i USING (order_id) LEFT JOIN payments p USING (order_id)
LEFT JOIN customers c ON c.customer_id=o.customer_id;

CREATE VIEW category_sales AS
SELECT o.order_id, o.order_purchase_timestamp AS purchased_at,
       coalesce(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
       i.price AS item_revenue, i.product_id, i.seller_id, i.order_item_id, i.freight_value,
       coalesce(c.customer_state, 'unknown') AS state
FROM orders o JOIN order_items i USING(order_id)
LEFT JOIN products p USING(product_id) LEFT JOIN category_translation t USING(product_category_name)
LEFT JOIN customers c USING(customer_id) WHERE o.order_status='delivered';

CREATE VIEW monthly_sales AS
SELECT date_trunc('month', purchased_at)::DATE AS month, count(*) AS order_count,
       sum(item_revenue) AS item_revenue, sum(item_revenue)/count(*) AS aov
FROM order_summary WHERE status='delivered' AND purchased_at IS NOT NULL GROUP BY 1;

CREATE VIEW review_delivery AS
SELECT o.order_id, o.order_purchase_timestamp AS purchased_at, r.review_id, r.review_score,
       o.order_delivered_customer_date AS actual_delivery, o.order_estimated_delivery_date AS estimated_delivery,
       actual_delivery > estimated_delivery AS late_timestamp,
       actual_delivery::DATE > estimated_delivery::DATE AS late_day,
       r.review_creation_date, r.review_answer_timestamp, r.source_row
FROM orders o JOIN order_reviews r USING(order_id)
WHERE o.order_status='delivered' AND r.review_score BETWEEN 1 AND 5
  AND actual_delivery IS NOT NULL AND estimated_delivery IS NOT NULL;

CREATE VIEW order_review_delivery AS
SELECT * FROM review_delivery
QUALIFY row_number() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC NULLS LAST,
    review_creation_date DESC NULLS LAST, review_id ASC NULLS LAST, source_row ASC)=1;
"""
