# Olist acceptance report

**15 of 15 cases passed.** pytest exited with code `0`.

Run recorded at `2026-11-20T07:03:24+00:00` on `Darwin 25.6.0 / arm64` with Python `3.11.16`.

The suite used version **2** of the Olist dataset. DuckDB snapshot `a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840`. [Olist dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

KaggleHub resolves the dataset, then pytest builds a fresh DuckDB database and starts the application on a temporary local port. A separate Python reference reads the original CSVs, sums monetary values with decimal arithmetic and calculates the statistical intervals. Business questions run in English using offline demo mode.

Each request uses the same snapshot. The application saves query history in the temporary environment and the test session shuts down the server. Case timings cover requests and assertions. Dataset preparation happens once before the cases run.

[Recorded results](results.json) · [Source file hashes and environment](manifest.json) · [Watch the K03 terminal run (MP4)](https://raw.githubusercontent.com/Romanticjojo/ecommerce-operations-agent/main/evaluation/kaggle_olist/media/K03-revenue.mp4)

## Reproduce the run

From the root of the repository or the standalone test archive, create a Python 3.11 environment and install the dependencies.

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r evaluation/kaggle_olist/requirements.txt
```

With the default options, pytest calls KaggleHub to resolve the latest dataset version.

```python
import kagglehub
path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")
print("Path to dataset files:", path)
```

To reproduce this run, specify the recorded version. The second command runs only the revenue case and prints the HTTP request, expected total and observed total.

```sh
.venv/bin/python -m pytest -q evaluation/kaggle_olist/cases.py --olist-version 2
.venv/bin/python -m pytest -q -s evaluation/kaggle_olist/cases.py::test_k03_revenue --olist-version 2 --olist-trace --olist-output runtime/k03
```

The full suite writes `REPORT.md`, `results.json` and `manifest.json` to `runtime/kaggle-acceptance/`. The single-case command writes its own copies to `runtime/k03/`.

## Data and environment

Olist publishes the source data under CC BY-NC-SA 4.0. Record counts exclude the header and count CSV records across embedded line breaks.

| Source file | Use | Records | Bytes | SHA-256 |
|---|---|---:|---:|---|
| `olist_customers_dataset.csv` | Imported | 99,441 | 9,033,957 | `983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2` |
| `olist_geolocation_dataset.csv` | Audit only | 1,000,163 | 61,273,883 | `b514f6fc991b9566aeba02aa5d67e2c3630f034b60a0e05aa0d082a3b66d88d6` |
| `olist_order_items_dataset.csv` | Imported | 112,650 | 15,438,671 | `0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279` |
| `olist_order_payments_dataset.csv` | Imported | 103,886 | 5,777,138 | `4f713964f2815dbbaa40b9488268c55aac3627bfce5aa96cf58d1f3616de3cc0` |
| `olist_order_reviews_dataset.csv` | Imported | 99,224 | 14,451,670 | `012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7` |
| `olist_orders_dataset.csv` | Imported | 99,441 | 17,654,914 | `8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf` |
| `olist_products_dataset.csv` | Imported | 32,951 | 2,379,446 | `3e6569628a17fbc75fd206ee357b59e20364b9afa90f5b6cd5b4d624c58aa9cc` |
| `olist_sellers_dataset.csv` | Imported | 3,095 | 174,703 | `1f643d2b950373b85735e7794b20986f528d7a000432e7c6f9bcbb44d0846a0e` |
| `product_category_name_translation.csv` | Imported | 71 | 2,613 | `a81f0d1f27b27e7293f761bc79e3ce8f348ee39c4b3ed3e49bde38f478586278` |

Package versions used in this run include `kagglehub 1.0.3`, `kagglesdk 0.1.38`, `duckdb 2.0.0`, `scipy 1.17.1`, `pytest 9.2.0`, `fastapi 0.165.0`, `uvicorn 0.54.0`.

## Results by case

| Case | Check | Result | Time (ms) |
|---|---|---|---:|
| K01 | Imported tables match the source files | PASS | 113.15 |
| K02 | Total delivered orders | PASS | 148.12 |
| K03 | Item revenue from delivered orders | PASS | 116.01 |
| K04 | Average order value | PASS | 122.16 |
| K05 | Monthly delivered orders in 2017 | PASS | 108.22 |
| K06 | Top ten categories by 2018 item revenue | PASS | 104.33 |
| K07 | January revenue with an exclusive end date | PASS | 99.42 |
| K08 | Item and payment totals for orders with multiple rows | PASS | 22.99 |
| K09 | Delivery investigation cohort and exclusions | PASS | 54.92 |
| K10 | Difference in negative review rates by delivery timestamp | PASS | 52.49 |
| K11 | Sensitivity to measuring delays by calendar day | PASS | 53.39 |
| K12 | Revenue request for a year without orders | PASS | 94.35 |
| K13 | Reversed date range | PASS | 1.71 |
| K14 | Clarification for an unavailable profit metric | PASS | 11.65 |
| K15 | Replaying a saved revenue query | PASS | 126.27 |

## Case evidence

Request date ranges include the start and exclude the end. Monetary values are in Brazilian reais (BRL). Each case records its inputs and comparisons, including the executed SQL when available.

### K01 · Imported tables match the source files

Fetch the catalog and compare the row count and SHA-256 of each imported file with its downloaded CSV. The import covers seven core tables and the category translation table. The download manifest also includes geolocation.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "GET",
      "path": "/api/catalog",
      "input": null,
      "http_status": 200
    }
  ],
  "checks": [
    {
      "label": "Row counts and SHA-256 hashes of imported CSVs",
      "expected": {
        "olist_customers_dataset.csv": {
          "rows": 99441,
          "sha256": "983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2"
        },
        "olist_order_items_dataset.csv": {
          "rows": 112650,
          "sha256": "0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279"
        },
        "olist_order_payments_dataset.csv": {
          "rows": 103886,
          "sha256": "4f713964f2815dbbaa40b9488268c55aac3627bfce5aa96cf58d1f3616de3cc0"
        },
        "olist_order_reviews_dataset.csv": {
          "rows": 99224,
          "sha256": "012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7"
        },
        "olist_orders_dataset.csv": {
          "rows": 99441,
          "sha256": "8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf"
        },
        "olist_products_dataset.csv": {
          "rows": 32951,
          "sha256": "3e6569628a17fbc75fd206ee357b59e20364b9afa90f5b6cd5b4d624c58aa9cc"
        },
        "olist_sellers_dataset.csv": {
          "rows": 3095,
          "sha256": "1f643d2b950373b85735e7794b20986f528d7a000432e7c6f9bcbb44d0846a0e"
        },
        "product_category_name_translation.csv": {
          "rows": 71,
          "sha256": "a81f0d1f27b27e7293f761bc79e3ce8f348ee39c4b3ed3e49bde38f478586278"
        }
      },
      "actual": {
        "olist_orders_dataset.csv": {
          "rows": 99441,
          "sha256": "8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf"
        },
        "olist_order_items_dataset.csv": {
          "rows": 112650,
          "sha256": "0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279"
        },
        "olist_order_payments_dataset.csv": {
          "rows": 103886,
          "sha256": "4f713964f2815dbbaa40b9488268c55aac3627bfce5aa96cf58d1f3616de3cc0"
        },
        "olist_order_reviews_dataset.csv": {
          "rows": 99224,
          "sha256": "012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7"
        },
        "olist_customers_dataset.csv": {
          "rows": 99441,
          "sha256": "983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2"
        },
        "olist_products_dataset.csv": {
          "rows": 32951,
          "sha256": "3e6569628a17fbc75fd206ee357b59e20364b9afa90f5b6cd5b4d624c58aa9cc"
        },
        "olist_sellers_dataset.csv": {
          "rows": 3095,
          "sha256": "1f643d2b950373b85735e7794b20986f528d7a000432e7c6f9bcbb44d0846a0e"
        },
        "product_category_name_translation.csv": {
          "rows": 71,
          "sha256": "a81f0d1f27b27e7293f761bc79e3ce8f348ee39c4b3ed3e49bde38f478586278"
        }
      }
    },
    {
      "label": "Dataset source and snapshot ID",
      "expected": [
        "olist",
        "a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840"
      ],
      "actual": [
        "olist",
        "a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840"
      ]
    }
  ]
}
```

</details>

### K02 · Total delivered orders

Ask for the delivered order count. Count distinct order IDs with status delivered in the orders CSV and compare the total with the response.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "Show total delivered order count.",
        "mode": "demo",
        "language": "en"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT COUNT(DISTINCT order_id) AS order_count FROM order_summary WHERE status = 'delivered' HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "Distinct delivered orders",
      "expected": [
        {
          "order_count": 96478
        }
      ],
      "actual": [
        {
          "order_count": 96478
        }
      ]
    }
  ]
}
```

</details>

### K03 · Item revenue from delivered orders

Ask for total item revenue. Sum item prices for delivered orders using decimal arithmetic, then compare the API result with the CSV total to the cent in Brazilian reais.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "What is total item revenue?",
        "mode": "demo",
        "language": "en"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "Delivered item revenue (BRL)",
      "expected": [
        {
          "item_revenue": 13221498.11
        }
      ],
      "actual": [
        {
          "item_revenue": 13221498.11
        }
      ]
    }
  ]
}
```

</details>

### K04 · Average order value

Divide item revenue from delivered orders by the number of distinct delivered orders. Compare the result with the reported average to the nearest cent.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "What is the average order value?",
        "mode": "demo",
        "language": "en"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) / NULLIF(COUNT(DISTINCT order_id), 0) AS aov FROM order_summary WHERE status = 'delivered' HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "Average order value (BRL)",
      "expected": 137.04,
      "actual": 137.04
    }
  ]
}
```

</details>

### K05 · Monthly delivered orders in 2017

Group delivered orders in the CSV by purchase month. Compare every month, count and position in the API response for 2017 with the reference series.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "Show monthly delivered orders in 2017.",
        "mode": "demo",
        "language": "en"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT CAST(DATE_TRUNC('MONTH', purchased_at) AS DATE) AS month, COUNT(DISTINCT order_id) AS order_count FROM order_summary WHERE status = 'delivered' AND NOT purchased_at IS NULL AND purchased_at >= CAST('2017-01-01' AS DATE) AND purchased_at < CAST('2018-01-01' AS DATE) GROUP BY month ORDER BY month) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "Delivered order count by month",
      "expected": [
        {
          "month": "2017-01-01",
          "order_count": 750
        },
        {
          "month": "2017-02-01",
          "order_count": 1653
        },
        {
          "month": "2017-03-01",
          "order_count": 2546
        },
        {
          "month": "2017-04-01",
          "order_count": 2303
        },
        {
          "month": "2017-05-01",
          "order_count": 3546
        },
        {
          "month": "2017-06-01",
          "order_count": 3135
        },
        {
          "month": "2017-07-01",
          "order_count": 3872
        },
        {
          "month": "2017-08-01",
          "order_count": 4193
        },
        {
          "month": "2017-09-01",
          "order_count": 4150
        },
        {
          "month": "2017-10-01",
          "order_count": 4478
        },
        {
          "month": "2017-11-01",
          "order_count": 7289
        },
        {
          "month": "2017-12-01",
          "order_count": 5513
        }
      ],
      "actual": [
        {
          "month": "2017-01-01",
          "order_count": 750
        },
        {
          "month": "2017-02-01",
          "order_count": 1653
        },
        {
          "month": "2017-03-01",
          "order_count": 2546
        },
        {
          "month": "2017-04-01",
          "order_count": 2303
        },
        {
          "month": "2017-05-01",
          "order_count": 3546
        },
        {
          "month": "2017-06-01",
          "order_count": 3135
        },
        {
          "month": "2017-07-01",
          "order_count": 3872
        },
        {
          "month": "2017-08-01",
          "order_count": 4193
        },
        {
          "month": "2017-09-01",
          "order_count": 4150
        },
        {
          "month": "2017-10-01",
          "order_count": 4478
        },
        {
          "month": "2017-11-01",
          "order_count": 7289
        },
        {
          "month": "2017-12-01",
          "order_count": 5513
        }
      ]
    }
  ]
}
```

</details>

### K06 · Top ten categories by 2018 item revenue

Join delivered items to products and category translations in the CSVs, keeping the source category when a translation is missing. Rank by revenue descending, then by category name ascending for ties. Compare all ten categories and amounts.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "What are the top 10 categories by item revenue in 2018?",
        "mode": "demo",
        "language": "en"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT category AS category, SUM(item_revenue) AS item_revenue FROM category_sales WHERE purchased_at >= CAST('2018-01-01' AS DATE) AND purchased_at < CAST('2019-01-01' AS DATE) GROUP BY category ORDER BY item_revenue DESC, category ASC LIMIT 10) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "Top ten categories and item revenue (BRL)",
      "expected": [
        {
          "category": "health_beauty",
          "item_revenue": 755724.5
        },
        {
          "category": "watches_gifts",
          "item_revenue": 687855.2
        },
        {
          "category": "bed_bath_table",
          "item_revenue": 532358.85
        },
        {
          "category": "sports_leisure",
          "item_revenue": 517166.26
        },
        {
          "category": "computers_accessories",
          "item_revenue": 496269.3
        },
        {
          "category": "housewares",
          "item_revenue": 391823.46
        },
        {
          "category": "furniture_decor",
          "item_revenue": 381649.57
        },
        {
          "category": "auto",
          "item_revenue": 343288.3
        },
        {
          "category": "baby",
          "item_revenue": 250615.79
        },
        {
          "category": "cool_stuff",
          "item_revenue": 227743.7
        }
      ],
      "actual": [
        {
          "category": "health_beauty",
          "item_revenue": 755724.5
        },
        {
          "category": "watches_gifts",
          "item_revenue": 687855.2
        },
        {
          "category": "bed_bath_table",
          "item_revenue": 532358.85
        },
        {
          "category": "sports_leisure",
          "item_revenue": 517166.26
        },
        {
          "category": "computers_accessories",
          "item_revenue": 496269.3
        },
        {
          "category": "housewares",
          "item_revenue": 391823.46
        },
        {
          "category": "furniture_decor",
          "item_revenue": 381649.57
        },
        {
          "category": "auto",
          "item_revenue": 343288.3
        },
        {
          "category": "baby",
          "item_revenue": 250615.79
        },
        {
          "category": "cool_stuff",
          "item_revenue": 227743.7
        }
      ]
    }
  ]
}
```

</details>

### K07 · January revenue with an exclusive end date

Request revenue for purchases from January 1 up to February 1, 2018. Sum delivered items purchased in January in the CSVs and check both date bounds in the query evidence.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "What is total item revenue?",
        "mode": "demo",
        "language": "en",
        "start": "2018-01-01",
        "end": "2018-02-01"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' AND purchased_at >= CAST('2018-01-01' AS DATE) AND purchased_at < CAST('2018-02-01' AS DATE) HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "January item revenue (BRL)",
      "expected": [
        {
          "item_revenue": 924645.0
        }
      ],
      "actual": [
        {
          "item_revenue": 924645.0
        }
      ]
    },
    {
      "label": "Purchase date bounds",
      "expected": [
        "2018-01-01",
        "2018-02-01"
      ],
      "actual": [
        "2018-01-01",
        "2018-02-01"
      ]
    }
  ]
}
```

</details>

### K08 · Item and payment totals for orders with multiple rows

Select delivered orders with multiple item rows and multiple payment rows. Sum each file separately per order. Compare the order count, item revenue and payments with the same cohort in the read-only order_summary view.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "DuckDB read-only",
      "executed_sql": "SELECT count(*),sum(item_revenue),sum(payment_total) FROM order_summary\n        WHERE status='delivered' AND item_count>1 AND order_id IN\n        (SELECT order_id FROM order_payments GROUP BY order_id HAVING count(*)>1)"
    }
  ],
  "checks": [
    {
      "label": "Order count, item revenue and payments for the cohort",
      "expected": {
        "orders": 274,
        "items_brl": 54397.39,
        "payments_brl": 66795.94
      },
      "actual": {
        "orders": 274,
        "items_brl": 54397.39,
        "payments_brl": 66795.94
      }
    }
  ]
}
```

</details>

### K09 · Delivery investigation cohort and exclusions

Classify each source order as undelivered, missing a delivery timestamp, missing a valid review, or included. Compare the counts with the delivery investigation.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/investigation",
      "input": {
        "grain": "timestamp"
      },
      "http_status": 200,
      "executed_sql": "SELECT late_timestamp AS late, count(*) AS n,\n       count(*) FILTER (WHERE review_score <= 2) AS negative\nFROM order_review_delivery WHERE TRUE GROUP BY 1 ORDER BY 1"
    }
  ],
  "checks": [
    {
      "label": "Included and excluded orders",
      "expected": {
        "total_orders": 99441,
        "not_delivered": 2963,
        "missing_delivery_time": 8,
        "no_valid_review": 646,
        "included_orders": 95824
      },
      "actual": {
        "total_orders": 99441,
        "not_delivered": 2963,
        "missing_delivery_time": 8,
        "no_valid_review": 646,
        "included_orders": 95824
      }
    }
  ]
}
```

</details>

### K10 · Difference in negative review rates by delivery timestamp

Use each order's latest valid review. Flag deliveries that arrived after the estimated timestamp. Independently compute each group's negative review count and rate, the risk difference, and its Newcombe-Wilson 95% confidence interval. Compare to nine decimal places.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/investigation",
      "input": {
        "grain": "timestamp"
      },
      "http_status": 200,
      "executed_sql": "SELECT late_timestamp AS late, count(*) AS n,\n       count(*) FILTER (WHERE review_score <= 2) AS negative\nFROM order_review_delivery WHERE TRUE GROUP BY 1 ORDER BY 1"
    }
  ],
  "checks": [
    {
      "label": "Review counts, rates, risk difference and interval",
      "expected": {
        "groups": {
          "late": {
            "n": 7661,
            "negative": 4142,
            "rate": 0.540660488
          },
          "on_time": {
            "n": 88163,
            "negative": 8130,
            "rate": 0.092215555
          }
        },
        "risk_difference": 0.448444933,
        "ci95": [
          0.437103082,
          0.459740616
        ]
      },
      "actual": {
        "groups": {
          "late": {
            "n": 7661,
            "negative": 4142,
            "rate": 0.540660488
          },
          "on_time": {
            "n": 88163,
            "negative": 8130,
            "rate": 0.092215555
          }
        },
        "risk_difference": 0.448444933,
        "ci95": [
          0.437103082,
          0.459740616
        ]
      }
    },
    {
      "label": "Pearson chi-squared test with p below 0.001",
      "expected": [
        "pearson_chi2",
        true
      ],
      "actual": [
        "pearson_chi2",
        true
      ]
    }
  ]
}
```

</details>

### K11 · Sensitivity to measuring delays by calendar day

Compare actual and estimated delivery dates, counting same-day arrivals as on time. Check the order count and negative review count for both groups against the CSVs.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/investigation",
      "input": {
        "grain": "day"
      },
      "http_status": 200,
      "executed_sql": "SELECT late_day AS late, count(*) AS n,\n       count(*) FILTER (WHERE review_score <= 2) AS negative\nFROM order_review_delivery WHERE TRUE GROUP BY 1 ORDER BY 1"
    }
  ],
  "checks": [
    {
      "label": "Orders and negative reviews under the calendar-day definition",
      "expected": {
        "late": [
          6381,
          3983
        ],
        "on_time": [
          89443,
          8289
        ]
      },
      "actual": {
        "late": [
          6381,
          3983
        ],
        "on_time": [
          89443,
          8289
        ]
      }
    }
  ]
}
```

</details>

### K12 · Revenue request for a year without orders

Ask for 2099 item revenue. This dataset has no orders from that year. Expect the insufficient_data status and an empty result table.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "What is total item revenue in 2099?",
        "mode": "demo",
        "language": "en"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' AND purchased_at >= CAST('2099-01-01' AS DATE) AND purchased_at < CAST('2100-01-01' AS DATE) HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "Status and result table",
      "expected": [
        "insufficient_data",
        []
      ],
      "actual": [
        "insufficient_data",
        []
      ]
    }
  ]
}
```

</details>

### K13 · Reversed date range

Submit a delivery investigation with an end date earlier than its start. Expect HTTP 422 and a validation error that explains the required date order.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/investigation",
      "input": {
        "start": "2018-02-01",
        "end": "2018-01-01"
      },
      "http_status": 422
    }
  ],
  "checks": [
    {
      "label": "Validation error explains the required date order",
      "expected": true,
      "actual": true
    }
  ]
}
```

</details>

### K14 · Clarification for an unavailable profit metric

Ask for after-tax net profit, which the offline catalog does not cover. Expect a request for clarification, zero result rows and no executed SQL.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "What was net profit after tax in 2018?",
        "mode": "demo",
        "language": "en"
      },
      "http_status": 200
    }
  ],
  "checks": [
    {
      "label": "Clarification status, row count and executed SQL",
      "expected": [
        "clarification_required",
        0,
        null
      ],
      "actual": [
        "clarification_required",
        0,
        null
      ]
    }
  ]
}
```

</details>

### K15 · Replaying a saved revenue query

Ask for 2017 item revenue and retrieve the saved run by ID. Check its snapshot, question, SQL and output. Replay the SQL on the same read-only snapshot and reconcile both amounts with the 2017 CSV total.

**PASS**

<details><summary>Requests, executed SQL, expected values and observations</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "What is total item revenue in 2017?",
        "mode": "demo",
        "language": "en"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' AND purchased_at >= CAST('2017-01-01' AS DATE) AND purchased_at < CAST('2018-01-01' AS DATE) HAVING COUNT(*) > 0) AS result LIMIT 1001"
    },
    {
      "method": "GET",
      "path": "/api/runs/23a54b6f-0452-4f92-a96d-f554e122a6b5",
      "input": null,
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' AND purchased_at >= CAST('2017-01-01' AS DATE) AND purchased_at < CAST('2018-01-01' AS DATE) HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "Retrieved run matches the original response",
      "expected": true,
      "actual": true
    },
    {
      "label": "Saved snapshot ID",
      "expected": "a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840",
      "actual": "a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840"
    },
    {
      "label": "CSV total compared with saved and replayed totals (BRL)",
      "expected": [
        5962902.01,
        5962902.01
      ],
      "actual": [
        5962902.01,
        5962902.01
      ]
    }
  ]
}
```

</details>
