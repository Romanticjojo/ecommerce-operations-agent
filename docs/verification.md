# Verification record

The November 19, 2026 engineering check-in ran locally on an Apple M4 (10 cores, 16 GB) with Python 3.11, Node.js 22 and Chromium/Chrome. That check-in recorded **17 passing backend and integration tests**. A separate acceptance suite subsequently passed **15 of 15** cases against version 2 of the Brazilian E-Commerce Public Dataset by Olist. The figures below retain their original test conditions. [Olist acceptance report](../evaluation/kaggle_olist/verified/REPORT.md) · [CI runs by commit](https://github.com/Romanticjojo/ecommerce-operations-agent/actions)

## Version 1.1 acceptance · November 20, 2026

| Check | Result |
|---|---|
| Regression and integration | 38 tests passed, including eligibility, multiple-review attribution, Portuguese cues, empty periods, model routing and skill history. |
| Original Olist end-to-end suite | 15 cases passed against a fresh v2 import. |
| Skill execution and evidence | All nine English procedures returned an operating conclusion. Replaying each query reproduced every result field and row. |
| Independent CSV oracle | All 784 seller ranks, scores, components and denominators matched. The top 20 product rows and the overall population of 92,673 rated orders matched. |
| Browser acceptance | Headless Chrome at 390, 768 and 1,440 pixels. Ran nine skills, checked both lateness definitions, data reference and previous bookmarks. Compared the full ranking export to the API, paged to the final sellers, and selected an individual product for its three-point trend and next action. |
| Build and model coverage | Built the production React bundle and started the native service. A local provider fixture tested skill routing and rejected unsupported restrictions. A live provider evaluation remains pending. |

[Run the skill checks](../evaluation/skill_checks/REPORT.md) · [Independent ranking oracle](../evaluation/skill_checks/merchant_oracle.py) · [Desktop skill directory](images/analysis-skills.png) · [Merchant result](images/merchant-ranking.png)

## Olist data and independent checks

The acceptance suite counted CSV records and recorded SHA-256 hashes, sizes and usage for nine source files. DuckDB imported seven business tables and the English category translation. The geolocation file has 1,000,163 records and is included only in the download audit. The analytical snapshot is `a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840`. One observed build took approximately 0.7 seconds, excluding download. [Source manifest](../evaluation/kaggle_olist/verified/manifest.json)

The source contains 99,441 orders, 112,650 item lines, 103,886 payment records and 99,224 review records. Its purchase dates run from September 2016 to October 2018. An independent Python pass over the CSVs using decimal arithmetic confirmed **96,478 delivered orders**, **BRL 13,221,498.11** in delivered item revenue and **BRL 137.04** average order value. Cross-checks also covered payment totals and both contingency tables.

| Late-delivery definition | Negative / late orders | Negative / on-time orders |
|---|---:|---:|
| Actual timestamp after estimated timestamp | 4,142 / 7,661 | 8,130 / 88,163 |
| Actual local date after estimated date | 3,983 / 6,381 | 8,289 / 89,443 |

The analysis excluded 2,963 undelivered orders, then eight with missing delivery times, then 646 without valid reviews. Of the 95,824 eligible orders, 525 had multiple eligible reviews. Using timestamps, the late group's negative-review rate exceeded the on-time group's by **44.84 percentage points**. The 95% Newcombe-Wilson interval was **43.71 to 45.97 points**, with Pearson p < 0.001. The comparison measures an association among reviewed orders. It does not identify a causal effect.

## Requirements and observed behavior

| Item | Evidence at the engineering check-in |
|---|---|
| FR-01 · Sales | The 2018 category leader was `health_beauty` at BRL 755,724.50. The January 2017 delivered count was 750. Checks covered API results, chart, table and copied SQL. |
| FR-02 · Investigation | Known samples covered the risk difference, interval, both tests, empty groups and constant outcomes. The independent source-data check confirmed the counts above. |
| FR-03 · Evidence | Browser checks exercised executed SQL, filters, metric definitions, snapshot, run ID, history retrieval and JSON download. |
| NFR-01 · Execution | The supplied suite verified syntax-tree limits, read-only access, external-access rejection, timeout cleanup and a subsequent successful query. |
| NFR-02 · Reproducibility | Identical imports, preservation of a working snapshot after an invalid import, reference SQL execution, locked dependencies and clean-clone startup were checked. Live-model and review targets remain pending. |
| NFR-03 · Performance and UI | Running each of 50 distinct reference queries once gave a local SQL p95 of 16.68 ms. This timing measures the stated machine and queries. Browser checks covered six routes at 320, 390, 768 and 1,440 px and at 200% zoom, including overflow, script errors, query, copy, export and investigation. |
| Model interface | A controlled HTTP provider exercised response shape, error mapping, repair count, usage and cost handling. A real provider is required to evaluate the model. |

## Benchmark interpretation

The benchmark has ten questions each on filters, multi-table semantics, aggregation/ranking, time series and review/delivery, plus five expected clarification or rejection cases. All 50 independent reference SQL queries executed on the Olist snapshot. The reference run provides expected results and timing.

The original offline parser passed **11 of 55** questions overall and **9 of 50** answerable questions. The remaining questions often reached clarification. The numbers describe the offline parser and the recorded question set. Real-model accuracy, execution success, end-to-end latency, token use and cost require a fresh direct/full comparison. The targets of at least 90% result accuracy and 95% SQL success require a human-reviewed benchmark and a configured model. [Reference run](../evaluation/verified/reference-results.csv) · [Offline run](../evaluation/verified/offline-results.csv)

## Reproduction

Run the following from the repository root with the documented dependencies installed.

```sh
python -m pytest -q
python -m pytest -q evaluation/kaggle_olist/cases.py --olist-version 2
python scripts/browser_smoke.py http://127.0.0.1:8731
python -m commerce.cli evaluate --mode model
```

The browser check requires a running workbench, Playwright and Chromium. The last command requires configured model access. The original clean-clone startup check installed locked Python and npm dependencies, built the UI, generated 3,116 synthetic orders and served the workbench. The current course workflow imports Olist v2 with `python -m commerce.cli olist`. It keeps Kaggle CSVs, credentials and personal history outside the published source. [Operator guide](operator-guide.md) · [Four-page project update](course/project-update.pdf)
