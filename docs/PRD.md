# Product requirements

**E-commerce Operations Agent** helps small online retailers answer sales and delivery questions through the Commerce Lens workbench. The DSC 200 submission selects three functional and three nonfunctional requirements below. P0 means required for the release. P1 identifies an experience requirement. High stability reflects a business or correctness constraint. Medium stability marks an implementation target that may depend on hardware. [Source review](source-review.md) · [Verification record](verification.md)

## Problem and scope

Orders, item lines, payments and reviews have different grains. Joining them directly can count revenue multiple times. A plausible number is also hard to assess without the underlying query and population. Operators need to compare sales across periods or categories and determine whether reviewed late deliveries have higher negative-review rates.

The workbench translates a question into a bounded query or statistical operation, then returns rows, definitions, executed SQL, filters, snapshot and limitations. It uses the Brazilian E-Commerce Public Dataset by Olist for 2016–2018. The acceptance suite audits nine CSVs. The application imports eight, including the category translation, and leaves geolocation at the audit stage.

## User stories

| Reader | Tasks |
|---|---|
| Operator | Ask sales and order questions in plain English. Identify the purchase period and status filter. Compare monthly trends and category ranks. Distinguish product price, freight and payment value. Investigate the link between delivery and low review scores. |
| Analyst | Inspect sample sizes, exclusions, effect sizes and intervals. Compare timestamp and calendar-day definitions. Copy the actual SQL. Look up table grain and metric definitions. Review missing data and repeated reviews. |
| Workbench user | Clarify ambiguous questions. Recognize empty results and execution errors and recover from either. Use the major workflows on a phone or with a keyboard. |
| Local operator | Start with offline examples. Configure a compatible model through environment variables. Keep credentials and source data out of the public repository. Reproduce a deployment from a clean clone. |
| Reviewer and maintainer | Trace requirements to tests and observed results. Compare model workflows on the same benchmark. Change independently tested modules and rerun CI. |

## Functional requirements selected for grading

| ID | Requirement | Rank / stability | Verification |
|---|---|---|---|
| FR-01 | Answer supported sales, order, category and time questions with a correctly filtered table and a chart for grouped results. Use delivered orders by default and label monetary results in BRL. Return clarification or rejection for unsupported questions. | P0 / High | UT-01, FT-01, benchmark |
| FR-02 | Compare eligible late and on-time orders over the selected purchase period. For either delivery definition, report sample sizes, group rates, difference, 95% interval, test, exclusions and observational limitation. | P0 / High | UT-03, FT-02 |
| FR-03 | Give each accepted analysis request a retrievable run ID. Save outcome, executed SQL, metric, filters, snapshot, grain and warnings where applicable. Distinguish execution failures from empty results. | P0 / High | FT-01–FT-03 |

## Nonfunctional requirements selected for grading

| ID | Requirement | Rank / stability | Verification |
|---|---|---|---|
| NFR-01 | Validate parsed SQL and limit execution to read-only, resource-limited reporting views. Accept zero prohibited cases in the supplied suite. Keep model credentials out of responses and logs. | P0 / High | UT-02, FT-03 |
| NFR-02 | Reimport identical inputs reproducibly and pin dependencies. On a fixed snapshot and human-reviewed benchmark, target at least 90% result accuracy and 95% SQL success for a real model. Record unmeasured outcomes as pending. | P0 / High | UT-01, FT-04, evaluation report |
| NFR-03 | On roughly 100,000 orders, target local SQL p95 below 2 seconds. Enforce a 15-second query limit and a 1,000-row result cap. Support waiting and error states, mobile use and keyboard navigation. | P0 / Medium | PERF-01, FT-03, UX-01/02 |

## Supporting requirements

| ID | Deliverable | Rank |
|---|---|---|
| FR-04 | CSV import, data-quality report, data dictionary and metric catalog | P0 |
| FR-05 | Compatible model interface and clearly labeled offline demo | P0 |
| FR-06 | Direct and full model evaluation with per-question results and run summary | P0 |
| FR-07 | Apple-inspired workbench, chart/table switching and SQL copying | P1 |
| FR-08 | Local history and result export | P1 |
| NFR-04 | Local single-user service, same-origin API and loopback default | P0 |
| NFR-05 | Public source, dependencies, license information, repeatable startup and CI | P0 |

## Implementation and test decisions

Put delivered item revenue beside the purchase period, currency and freight definition on the overview. A user can check it in the workbench by asking “What is total item revenue?” Place the investigation link beside the review sample so users can compare the two delivery groups. Put copyable SQL first in the evidence panel.

Keep data import, metrics, model adapter, controller, execution, statistics, evidence, evaluation and UI separately testable. Aggregate items and payments independently. Use one eligible review per order for inference and calculate statistics in code. React and FastAPI support the custom workbench. Test monetary totals with hand-counted fixtures, guard behavior with an immutable snapshot, inference with known contingency tables, and the complete path through recorded evidence. A controlled HTTP provider verifies the integration contract. Model accuracy needs an actual model run. [Design review](superpowers/specs/2026-11-19-ecommerce-agent-design.md) · [Acceptance cases](acceptance.md)

## Boundaries

Scope covers sales analysis, negative-review investigation and evidence retrieval. Live stores, automated pricing or ordering, outbound messages, causal identification, unrestricted code execution, multi-tenant permissions, review-text model training, retrieval-augmented generation and multi-agent orchestration are outside this release. The project tracks real-data verification, real-model evaluation and human benchmark review separately.

## Operations skill extension

The November 20 release adds nine executable procedures and moves the data reference and delivery comparison into Ask. Its decision matrix, source constraints and acceptance checks are recorded in the [skill requirements](superpowers/specs/2026-11-20-analysis-skills.md) and [release plan](superpowers/plans/2026-11-20-analysis-skills.md).
