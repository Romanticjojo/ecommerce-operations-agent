# Olist 真实数据验收报告

**15 / 15 项通过**。pytest 退出码为 `0`。

运行时间（UTC） `2026-11-19T09:31:50+00:00`。数据来源为 [Olist 官方 Kaggle 数据集](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)，本次解析到版本 **2**。

操作系统 `Darwin 25.6.0 / arm64`，Python `3.11.16`。业务数据快照 `a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840`。

**共同前置条件**：KaggleHub 取得指定数据，在临时工作目录新建 DuckDB 快照；服务监听本机随机端口。预期数值由 Python CSV、Decimal 与独立统计公式计算。自然语言测试显式指定离线演示模式。

**共同后置条件**：HTTP 查询及统计仅访问该快照，历史写入临时数据库。会话结束时关闭服务。每项耗时只计调用与断言，下载和建库时间另计。该报告衡量指定数据集上的功能与数值一致性。

[机器可读结果](results.json) · [九个源文件的行数、字节数、SHA-256 与环境](manifest.json)

[观看 K03 本地测试全程（MP4）](https://github.com/Romanticjojo/ecommerce-operations-agent/raw/refs/heads/main/evaluation/kaggle_olist/media/K03-revenue.mp4)

## 在本地复现

以下命令在本仓库或完整测试包的根目录执行（Python 3.11）。首行创建虚拟环境，随后安装锁定的应用依赖与 KaggleHub。

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r evaluation/kaggle_olist/requirements.txt
```

本项目指定的数据集和下载入口如下。无版本号时由 KaggleHub 解析最新版；复查本报告时选用本次实测版本。

```python
import kagglehub
path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")
print("Path to dataset files:", path)
```

```sh
# 全套用例；pytest 会自行取数、建库并启动本机服务
.venv/bin/python -m pytest -q evaluation/kaggle_olist/cases.py --olist-version 2
# 单跑 K03，并显示实际 HTTP 输入与断言两侧的值
.venv/bin/python -m pytest -q -s evaluation/kaggle_olist/cases.py::test_k03_revenue --olist-version 2 --olist-trace --olist-output runtime/k03
```

整套用例的默认输出目录为 `runtime/kaggle-acceptance/`，上方 K03 命令使用独立的 `runtime/k03/`。两者均生成 REPORT.md、results.json 和 manifest.json。

## 本次运行的数据与环境

发布者 Olist；数据许可 CC BY-NC-SA 4.0。版本 2 的源文件如下。行数使用 CSV 解析器计数，不含表头。

| 源文件 | 用途 | 记录数 | 字节数 | SHA-256 |
|---|---|---:|---:|---|
| `olist_customers_dataset.csv` | 导入 | 99,441 | 9,033,957 | `983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2` |
| `olist_geolocation_dataset.csv` | 仅审计 | 1,000,163 | 61,273,883 | `b514f6fc991b9566aeba02aa5d67e2c3630f034b60a0e05aa0d082a3b66d88d6` |
| `olist_order_items_dataset.csv` | 导入 | 112,650 | 15,438,671 | `0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279` |
| `olist_order_payments_dataset.csv` | 导入 | 103,886 | 5,777,138 | `4f713964f2815dbbaa40b9488268c55aac3627bfce5aa96cf58d1f3616de3cc0` |
| `olist_order_reviews_dataset.csv` | 导入 | 99,224 | 14,451,670 | `012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7` |
| `olist_orders_dataset.csv` | 导入 | 99,441 | 17,654,914 | `8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf` |
| `olist_products_dataset.csv` | 导入 | 32,951 | 2,379,446 | `3e6569628a17fbc75fd206ee357b59e20364b9afa90f5b6cd5b4d624c58aa9cc` |
| `olist_sellers_dataset.csv` | 导入 | 3,095 | 174,703 | `1f643d2b950373b85735e7794b20986f528d7a000432e7c6f9bcbb44d0846a0e` |
| `product_category_name_translation.csv` | 导入 | 71 | 2,613 | `a81f0d1f27b27e7293f761bc79e3ce8f348ee39c4b3ed3e49bde38f478586278` |

运行依赖：`kagglehub 1.0.3`、`kagglesdk 0.1.38`、`duckdb 2.0.0`、`scipy 1.17.1`、`pytest 9.2.0`、`fastapi 0.165.0`、`uvicorn 0.54.0`。

## 用例总览

| 用例 | 检查内容 | 结果 | 耗时（ms） |
|---|---|---|---:|
| K01 | 导入清单与原始文件一致 | PASS | 101.74 |
| K02 | 汇总已送达订单 | PASS | 134.70 |
| K03 | 核对已送达商品成交额 | PASS | 116.74 |
| K04 | 核对客单价 | PASS | 119.77 |
| K05 | 2017 年逐月订单趋势 | PASS | 105.75 |
| K06 | 2018 年成交额前十品类 | PASS | 104.59 |
| K07 | 日期窗口按购买日左闭右开 | PASS | 98.38 |
| K08 | 多商品且多支付的订单不会放大金额 | PASS | 22.53 |
| K09 | 调查样本筛选与排除数 | PASS | 54.29 |
| K10 | 时间戳口径下的风险差与区间 | PASS | 54.88 |
| K11 | 自然日口径的敏感性分析 | PASS | 53.34 |
| K12 | 缺少订单时给出数据不足状态 | PASS | 93.62 |
| K13 | 拒绝反向日期区间 | PASS | 1.02 |
| K14 | 离线模式处理缺失的利润指标 | PASS | 11.68 |
| K15 | 历史记录与执行证据可重放 | PASS | 127.57 |

## 用例明细

HTTP 输入中的日期区间左闭右开；BRL 为巴西雷亚尔。Geo 文件包含地理位置数据，本系统使用其余八个 CSV。采集请求时保留实际执行的 SQL。

### K01 · 导入清单与原始文件一致

请求数据目录。对照下载目录中 CSV 的 SHA-256 和按 CSV 记录计数的行数，逐表核对七张核心表及翻译表。地理坐标文件只列入下载清单。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

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
      "label": "业务表、翻译表的行数与摘要",
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
      "label": "数据来源与导入快照",
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

### K02 · 汇总已送达订单

用英文查询订单数。以原始订单表中状态为 delivered 的不同订单 ID 数为期望值。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "Show total delivered order count.",
        "mode": "demo",
        "language": "zh"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT COUNT(DISTINCT order_id) AS order_count FROM order_summary WHERE status = 'delivered' HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "已送达订单数",
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

### K03 · 核对已送达商品成交额

请求“总销售额”。独立累加已送达订单下的商品价格，使用十进制定点数，单位 BRL，精确到分。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "总销售额",
        "mode": "demo",
        "language": "zh"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "商品成交额（BRL）",
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

### K04 · 核对客单价

请求“客单价”。将已送达商品成交额除以已送达订单数，比对保留两位小数的 BRL 金额。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "客单价",
        "mode": "demo",
        "language": "zh"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) / NULLIF(COUNT(DISTINCT order_id), 0) AS aov FROM order_summary WHERE status = 'delivered' HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "客单价（BRL）",
      "expected": 137.04,
      "actual": 137.04
    }
  ]
}
```

</details>

### K05 · 2017 年逐月订单趋势

请求 2017 年月度已送达订单数。从 CSV 按购买年月计数，完整比较每月标签、行数、数值及顺序。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "Show monthly delivered orders in 2017.",
        "mode": "demo",
        "language": "zh"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT CAST(DATE_TRUNC('MONTH', purchased_at) AS DATE) AS month, COUNT(DISTINCT order_id) AS order_count FROM order_summary WHERE status = 'delivered' AND NOT purchased_at IS NULL AND purchased_at >= CAST('2017-01-01' AS DATE) AND purchased_at < CAST('2018-01-01' AS DATE) GROUP BY month ORDER BY month) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "各月订单数",
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

### K06 · 2018 年成交额前十品类

按 CSV 关联已送达订单行、商品和品类翻译，缺翻译时回退到原始品类。按金额降序、品类名升序取十项，核对完整排名。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "2018 年哪些品类的商品成交额最高？",
        "mode": "demo",
        "language": "zh"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT category AS category, SUM(item_revenue) AS item_revenue FROM category_sales WHERE purchased_at >= CAST('2018-01-01' AS DATE) AND purchased_at < CAST('2019-01-01' AS DATE) GROUP BY category ORDER BY item_revenue DESC, category ASC LIMIT 10) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "前十品类及 BRL 金额",
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

### K07 · 日期窗口按购买日左闭右开

查询 2018-01-01 至 2018-02-01（不含）商品成交额。独立汇总购买月份为 2018-01 的商品行，并核对证据中的实际日期范围。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "总销售额",
        "mode": "demo",
        "language": "zh",
        "start": "2018-01-01",
        "end": "2018-02-01"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' AND purchased_at >= CAST('2018-01-01' AS DATE) AND purchased_at < CAST('2018-02-01' AS DATE) HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "一月商品成交额",
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
      "label": "日期边界",
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

### K08 · 多商品且多支付的订单不会放大金额

仅取商品行数和支付行数均大于一的已送达订单。独立 CSV 逐单累加商品及支付，再用只读连接检查 order_summary 中相同子集的行数和两种金额。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

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
      "label": "交叉子集的订单数、商品额与支付额",
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

### K09 · 调查样本筛选与排除数

运行配送调查，检查未送达、缺配送时间、缺有效评价、纳入分析四项互斥计数；与原始文件逐单分类结果比对。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

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
      "label": "订单纳入与排除",
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

### K10 · 时间戳口径下的风险差与区间

按每单最新有效评价，将签收时间晚于预计时间的订单分入延迟组。独立计算两组差评数、率、风险差及 Newcombe-Wilson 95% 区间，比较到小数点后九位。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

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
      "label": "时间戳分组与统计量",
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
      "label": "版本 2 的大样本检验",
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

### K11 · 自然日口径的敏感性分析

将实际和预计签收时间截到日期后重算两组，核对各组样本量和差评数；同日较晚签收的订单归入准时组。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

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
      "label": "按日分组（订单数、差评数）",
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

### K12 · 缺少订单时给出数据不足状态

查询 2099 年的成交额。此数据版本在该年度没有订单，预期状态为 insufficient_data 且结果表为空。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "What is total item revenue in 2099?",
        "mode": "demo",
        "language": "zh"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' AND purchased_at >= CAST('2099-01-01' AS DATE) AND purchased_at < CAST('2100-01-01' AS DATE) HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "状态与结果表",
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

### K13 · 拒绝反向日期区间

对差评调查提交早于起始日的结束日。预期返回 HTTP 422，响应包含日期范围校验错误。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

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
      "label": "说明结束日期必须晚于开始日期",
      "expected": true,
      "actual": true
    }
  ]
}
```

</details>

### K14 · 离线模式处理缺失的利润指标

提问税后净利润。离线问题目录没有该指标，预期请求澄清，结果表为空，且没有执行 SQL。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "2018 年税后净利润是多少？",
        "mode": "demo",
        "language": "zh"
      },
      "http_status": 200
    }
  ],
  "checks": [
    {
      "label": "澄清状态、行数与执行 SQL",
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

### K15 · 历史记录与执行证据可重放

查询 2017 年商品成交额，按返回 ID 取回历史记录。核对快照、问题、SQL 和输出，在同一只读快照重放该 SQL，并与 2017 年 CSV 合计对账。

**实测判定**：PASS。

<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>

```json
{
  "requests": [
    {
      "method": "POST",
      "path": "/api/query",
      "input": {
        "question": "What is total item revenue in 2017?",
        "mode": "demo",
        "language": "zh"
      },
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' AND purchased_at >= CAST('2017-01-01' AS DATE) AND purchased_at < CAST('2018-01-01' AS DATE) HAVING COUNT(*) > 0) AS result LIMIT 1001"
    },
    {
      "method": "GET",
      "path": "/api/runs/eae6fad0-c15c-4fb7-829c-fb11f0d464cd",
      "input": null,
      "http_status": 200,
      "executed_sql": "SELECT * FROM (SELECT SUM(item_revenue) AS item_revenue FROM order_summary WHERE status = 'delivered' AND purchased_at >= CAST('2017-01-01' AS DATE) AND purchased_at < CAST('2018-01-01' AS DATE) HAVING COUNT(*) > 0) AS result LIMIT 1001"
    }
  ],
  "checks": [
    {
      "label": "历史记录完整回读",
      "expected": true,
      "actual": true
    },
    {
      "label": "历史快照",
      "expected": "a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840",
      "actual": "a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840"
    },
    {
      "label": "CSV、历史表格、SQL 重放（BRL）",
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
