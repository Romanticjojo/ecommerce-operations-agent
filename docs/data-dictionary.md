# Data dictionary and statistical methods

The Brazilian E-Commerce Public Dataset by Olist describes Brazilian marketplace orders purchased between September 2016 and October 2018. Prices and payments are in Brazilian reais (BRL). Source timestamps retain their local, timezone-unspecified values. Purchase-date filters include the start and exclude the end. The overview labels the earliest and latest observed purchase dates inclusively and uses all delivered orders for its sales metrics. [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

## Source files and import rules

The acceptance manifest records counts, byte sizes and SHA-256 hashes for **all nine CSVs** in Olist v2. The warehouse uses the seven business tables and the category translation, or **eight inputs** in this snapshot. The geolocation file is audit-only. Custom imports require the seven business files and may omit the translation. [Verified source manifest](../evaluation/kaggle_olist/verified/manifest.json)

| Source | Row grain or key | Representative fields | Olist v2 rows |
|---|---|---|---:|
| orders | One order, `order_id` | Customer, status, purchase, approval, carrier handoff, actual and estimated delivery | 99,441 |
| order_items | One item, `(order_id, order_item_id)` | Product, seller, shipping limit, price, freight value | 112,650 |
| order_payments | One payment, `(order_id, payment_sequential)` | Method, installments and payment value | 103,886 |
| order_reviews | One CSV record, tracked by `source_row` | Review ID, order ID, score, title, comment, creation and answer times | 99,224 |
| customers | One `customer_id` | Cross-order customer identifier, ZIP prefix, city, state | 99,441 |
| products | One `product_id` | Category, title and description lengths, photo count, weight (g), dimensions (cm) | 32,951 |
| sellers | One `seller_id` | ZIP prefix, city, state | 3,095 |
| product_category_name_translation | One Portuguese category label | English category label | 71 |
| geolocation | One source coordinate observation | ZIP prefix, latitude, longitude, city, state | 1,000,163 |

Business filenames follow `olist_<table>_dataset.csv`. The lookup is `product_category_name_translation.csv`. Read UTF-8 headers, quoted fields and multiline reviews. Reordered columns are supported if the original required fields are present. Empty fields represent nulls, ZIP prefixes are text and money is stored at decimal-cent precision. The source spellings `product_name_lenght` and `product_description_lenght` are preserved. `source_row` starts at 1 after the header and counts CSV records, including a multiline review as one record. [Schema definitions](../commerce/schema.py)

An import stops on missing required files or columns, invalid types or null/duplicate keys in keyed business tables. The importer replaces the current database only after completing all tables, views and audits. Review IDs can recur, including across orders. Orphan foreign keys remain visible in the audit. The audit records source fields, row counts, hashes, missing values, foreign-key failures, repeated and cross-order review IDs, orders with multiple eligible reviews, and delivered orders with no item lines. The snapshot ID covers the selected inputs and transformation version.

## Reporting views

| View | Grain | Purpose |
|---|---|---|
| `order_summary` | One order across all statuses | Aggregate items and payments separately, then attach the customer state. Expose revenue, payment total, freight and item count. Sales default to delivered orders. |
| `category_sales` | One item line on a delivered order | Prefer the translated category, then the source label, then `unknown`. Item price excludes freight. Count distinct orders per category. An order can appear in several categories. |
| `monthly_sales` | One observed purchase month with delivered orders | The month is its first date. Aggregate order count, item revenue and AOV. Exclude missing purchase timestamps. |
| `review_delivery` | One eligible review record | Require a delivered order, valid 1–5 score and both delivery times. Use for record-level descriptive counts. |
| `order_review_delivery` | One eligible delivered order | Take the latest answer time, then latest creation time, with nulls last. Break ties with ascending review ID and source row. Use for inference. |

`item_revenue` sums item prices. `freight_total` sums freight independently. `payment_total` counts each payment sequence once regardless of installments. For an order without corresponding non-null amounts, the summary uses zero and the audit retains missing-field counts. Overview `order_count` counts delivered orders and `aov` divides their item revenue by that count. An empty denominator returns null. Missing state is shown as `unknown`.

## Delivery and negative reviews

Within a selected purchase period, exclude the following mutually exclusive groups in order.

1. Orders outside delivered status.
2. Remaining orders missing actual or estimated delivery time.
3. Remaining orders with no eligible review score.

A score of 1 or 2 is negative. In the primary comparison, an order is late when its actual timestamp exceeds its estimated timestamp. In the sensitivity analysis it is late when its actual local date exceeds its estimated date. A parcel promised for May 10 at midnight and delivered May 10 at 14:00 counts as late by timestamp and on time by date. Both comparisons start from the same eligible orders.

The contingency table has rows for late and on-time orders and columns for negative and other eligible reviews. The risk difference subtracts the on-time negative-review rate from the late rate. A difference of 0.10 is ten percentage points. The 95% interval uses Newcombe method 10 with uncorrected Wilson score intervals. Use a two-sided Fisher exact test if any expected cell is below 5, otherwise Pearson's chi-squared test without continuity correction. For an empty group the status is `insufficient_data` and effect, interval and p-value are null. With two nonempty groups and a constant outcome, report the difference and interval and leave test and p-value null. Extremely small values may be displayed as p < 0.001.

Region, carrier, order mix and the customer's decision to review may affect the comparison. The result describes an association among reviewed orders. It cannot establish how many negative reviews an earlier delivery would prevent.
