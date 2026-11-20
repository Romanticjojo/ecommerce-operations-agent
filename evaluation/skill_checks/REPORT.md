# Olist analysis skills acceptance

Snapshot `a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840`. Source purchase dates cover 2016-09-04 through 2018-10-17.

Each procedure below ran locally without a model provider, using the full date range. The check reran the SQL from the answer against the snapshot and compared every field of every output row. The merchant oracle separately recomputes the score and rankings from the original CSV files.

## Sales and growth

What drove the change in platform sales?

From 2018-06 to 2018-07, delivered item revenue moved from BRL 856,077.86 to BRL 867,953.46. Buyers moved from 6,061 to 6,100, orders per identified buyer from 1.006 to 1.010, and average order value from BRL 140.36 to BRL 140.92. The largest category gain shown was watches_gifts (BRL +10,137.22). The largest category decline shown was bed_bath_table (BRL -16,451.85).

SQL replay matched all 10 result rows.

## Customer retention and value

Which first-purchase categories lead to repeat purchases within 90 days?

Among the 15 largest first-purchase cohorts shown, bed_bath_table had the highest observed 90-day repeat rate: 282 of 7,126 buyers (3.96%). In the largest cohort (bed_bath_table), 6,844 of 7,126 had no repeat by day 90. Test a win-back offer against a holdout.

SQL replay matched all 15 result rows.

## Products and categories

Which categories gained or lost the most units?

Comparing 2018-06 with 2018-07, bed_bath_table had the largest absolute unit change (764 to 617). It had 87 active sellers in 2018-07. Check seller capacity and current stock before changing the assortment.

SQL replay matched all 15 result rows.

## Price and volume

How did unit sales change when the same product sold at a different price?

Across matched consecutive SKU-months, unchanged prices: +0 median units (1,561 pairs), higher prices: +0 median units (535 pairs), lower prices: +0 median units (487 pairs). Use these associations to select products for a pricing test.

SQL replay matched all 3 result rows.

## Seller performance and growth

Which sellers grew consistently across three months?

From 2018-05 through 2018-07, seller 5656537e588803a555b8eb41f07a944b ranked first among eligible sellers. Revenue rose in 2 of 2 comparisons. Its marketplace revenue share in 2018-07 was 0.103%. Use the order counts to size any seller-support pilot.

SQL replay matched all 15 result rows.

## Delivery performance

Which sellers and shipping lanes should we investigate for late delivery?

Seller ad781527c93d00d89a11eecd9dcad7c1 had 12 late deliveries among 33 orders (36.4%). State lane PR → AL had 11 late deliveries among 35 orders (31.4%). Check handover timing and the promised transit time for these groups.

SQL replay matched all 10 result rows.

## Reviews and aftercare

Which products receive the most low ratings, and what do their customers mention?

11,206 of 92,673 attributable rated orders received 1–2 stars (12.1%). Of 38,783 written reviews, 20,179 matched positive language only and 5,016 matched negative language only. Product 99a4788cb24856965c36a24e339b6058 has 53 low ratings across 397 rated orders. Delivery appears in 2,271 low ratings, the highest count among the four tracked themes. Start the review there.

SQL replay matched all 21 result rows.

## Merchant scorecard

How do merchants rank on customer ratings and on-time delivery?

Seller 48efc9d94a9834137efd9ea76b065a38 ranks first at 93.76/100 among 784 eligible sellers. It has 33 rated orders and 33 on-time arrivals in 33 timed deliveries. Inspect both adjusted components before selecting a seller for operational follow-up.

SQL replay matched all 784 result rows.

## Product sales outlook

Which products should I review for reordering next month?

For 2018-08 planning, product 53b36df67ebb7c41585e8d54d6772e08 (watches_gifts) moved from 114 to 9 to 11 units over 2018-05–2018-07. Its three-month median is 11 units. Hold the baseline and monitor weekly sales. For a small reorder test, check stock for 2ff995aead9c63a1f37a07b3664ead37 (2 → 8 → 21 units).

SQL replay matched all 15 result rows.

## Reproduce

After importing Olist v2, run these commands from the project root. Supply the extracted Kaggle directory containing the original CSVs as the first oracle argument.

```sh
python -m evaluation.skill_checks.report runtime/commerce.duckdb /tmp/olist-skills.md
python -m evaluation.skill_checks.merchant_oracle /path/to/olist-csvs runtime/commerce.duckdb
```
