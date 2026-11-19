# E-commerce Operations Agent design review

**Decision date** — November 19, 2026. This record preserves the approved design and its original validation assumptions. The English release uses Commerce Lens as the workbench name. Consult the implementation and verification records for measured outcomes. [Project status](../../project-status.md) · [Verification record](../../verification.md)

## Product and system choice

An operator should be able to ask how sales performed, compare negative-review rates by delivery performance and inspect the data behind either answer. The deliverables include local source, a usable interface, testing and deployment instructions, acceptance evidence and a public GitHub repository.

| Option reviewed | Strengths | Costs and decision |
|---|---|---|
| React, FastAPI and DuckDB with a single controller | Custom workbench, explicit metrics, isolated execution and reproducible local experiments | Selected. The project implements its orchestration and provider adapter. |
| Application on the DB-GPT platform | Existing agents, AWEL, models and connectors | Requires a broader runtime, configuration and upgrades. Reconsider for a future multi-source deployment. |
| Streamlit | Quick Python-only classroom prototype | Fine-grained interaction and front-end/back-end separation are more limited. Retained as a design alternative. |

DB-GPT informed the workflow and tool contracts. The release uses its own implementation. Multi-agent orchestration, RAG, vector storage, a microservice cluster and automatic store actions are outside scope.

## Modules and interface

| Module | Contract | Main dependency |
|---|---|---|
| Import and audit | CSV directory to validated source tables, snapshot ID and quality report. A failed import preserves the working snapshot. | DuckDB and filesystem |
| Catalog and views | Fixed metric definitions, reporting schema and independent item/payment aggregates | Data layer |
| Model adapter | Question, schema and metrics to structured plan or candidate SQL. Handle timeouts, invalid responses and usage. | Compatible HTTP endpoint and server configuration |
| Controller | Route, plan, compile, validate, execute and assemble evidence with a bounded repair policy | Adapter, catalog, worker and statistics |
| SQL execution | Candidate SQL to bounded rows or structured error | SQLGlot and read-only DuckDB worker |
| Review analyzer | Sampling rule and purchase period to counts, rates, difference, interval, test and exclusions | Read-only analytical queries and SciPy |
| Evidence and history | Save plan context, execution evidence and exportable result | Local SQLite history |
| Evaluation | Fixed questions, snapshot and mode to question-level comparisons, aggregates and error examples | Same controller and independent reference SQL |
| Workbench | Overview, questions, investigation, data and metrics, evaluation, history and configuration status | Same-origin FastAPI service |

The overview identifies the actual dataset, date coverage and delivered sales. Questions, chart/table switching and expandable SQL share one analysis page. The investigation emphasizes the eligible sample and limits on interpretation. Evaluation identifies its source, mode and run state. The initial design called for Chinese navigation and bilingual input. The English edition uses English navigation, examples and user-facing documentation. Requests are independent, so a new query starts with a fresh set of filters. Model credentials stay in server-side settings. Mobile layouts, keyboard operation, labels and reduced motion are acceptance concerns. [Interface design](../../../DESIGN.md)

## Data and statistical semantics

The required CSVs are orders, order items, payments, reviews, customers, products and sellers. Category translation is optional for custom imports. The Olist v2 acceptance release audited all nine CSVs, imported all seven business tables plus translation and recorded geolocation in the source manifest. [Data dictionary](../../data-dictionary.md)

Orders, customers, products and sellers have their respective single-column keys. Item and payment keys combine the order with the item or payment sequence. Review IDs can repeat or occur across orders. Preserve the source row, report the multiplicity and select one eligible review per order for inference.

| View | Contract |
|---|---|
| `order_summary` | One row per order, with separately aggregated items and payments. |
| `category_sales` | Item grain with translated category when available, delivered orders and distinct order counts. |
| `monthly_sales` | Group delivered orders by purchase month. |
| `review_delivery` | One row per eligible review record for descriptive checks. |
| `order_review_delivery` | One eligible review per order, choosing the latest answer and creation times and then ascending review ID and source row. |

Item revenue sums recorded item prices on delivered orders and excludes freight. Order count is distinct at the requested grain. Average order value divides item revenue by order count with a null result for an empty denominator. Money is in BRL. Treat source times as local and timezone-unspecified. Purchase-date intervals include their start and exclude their end.

The primary late flag compares full actual and estimated timestamps. A sensitivity analysis compares local dates. A score of 1 or 2 among valid scores of 1–5 is negative. Sequentially exclude undelivered orders, then missing delivery times, then missing valid scores. Report the mutually exclusive counts. Preserve both review-record descriptive data and order-level inference.

For the two independent order groups, report the 2 × 2 table, counts, rates, risk difference and Newcombe-Wilson 95% interval. Use two-sided Fisher exact testing for expected counts below 5 and uncorrected Pearson chi-squared otherwise. Empty groups yield insufficient data. Constant outcomes in two populated groups leave the test and p-value undefined. Results describe association.

## Planning, execution and failure handling

The full path is question → structured plan → compiled SQL → validation → read-only execution → result checks → answer and evidence. Plans constrain the intent, metric, dimensions, filters, dates, limit and language. Ambiguous questions can end in clarification. The deterministic compiler uses documented metrics and views for sales. An investigation uses fixed statistical code. The provider does not execute Python, read source files or choose the outcome of a statistical test.

Candidate SQL is limited to a single analytical SELECT or supported CTE with approved tables, columns, functions and syntax. The worker runs read-only with external access and extension loading disabled, under memory, thread and timeout limits. It requests at most 1,001 rows to detect truncation and returns at most 1,000. Evidence discloses truncation. The design sets a 15-second SQL deadline and a 60-second model default. At most one repair is allowed for supported structured-plan failures. Rejection, provider failure and invalid final plans end the run with a safe message and request ID.

Format numeric answers from deterministic results. Record executed SQL, snapshot, metric, filters, period, grain, row count, truncation, timing, model/prompt identifiers and warnings as applicable. In offline mode the interface identifies the local parser and uses its supported examples. Unknown wording can trigger clarification. Offline coverage and model accuracy have independent records.

## API and deployment

The design called for health, catalog, overview, query, investigation, run history, evaluation and configuration-status endpoints. The implemented service documents its routes at `/docs`. CSV import and batch evaluation use the local CLI.

The response includes a structured status, request ID, answer, table, chart, evidence, timing information and mode as applicable. Chart data is declarative. User and provider text are rendered as text. FastAPI serves the built workbench and API from the same origin. Native and container defaults bind to loopback for single-user operation.

The original plan supported a clean-start synthetic demo without model credentials. The English course edition adds the version-pinned Olist import workflow. Users obtain Olist under the publisher's data license. [Operator guide](../../operator-guide.md)

## Evaluation and acceptance

The 55 questions contain ten each on filtering, multi-table semantics, aggregation/ranking, time series and reviews/delivery, plus five ambiguous or unanswerable questions. Each carries input, reference SQL or expected status, tolerance, ordering rules and review state. Human review of this AI-drafted set is pending.

Compare direct text-to-SQL and the full workflow under the same snapshot, model, question set and recorded prompts. Both use the execution guard. Record actual tokens and latency. Leave cost null when pricing is unavailable. Targets for a real model are at least 90% result accuracy on answerable items, 95% SQL success and zero accepted prohibited cases in the supplied suite.

Acceptance includes join-multiplication regression, idempotent import, rollback, statistical boundary cases, browser workflows, mobile layouts, console checks, clean-clone startup and anonymous repository access. Track deployment, synthetic checks, Olist results and real-model/human-review status separately. [Acceptance cases](../../acceptance.md)

## Lifecycle and outstanding work

Requirements led to data contracts, planning and execution, statistics, workbench integration, evaluation and publication. Product and integration own scope and acceptance, data owns import and views, application engineering owns planning and execution, analysis owns inference, frontend owns the workbench, and quality owns testing. These are responsibility areas. Actual student assignments require team confirmation.

At design approval, the team had no real Olist snapshot, credentials for the chosen model or a human-reviewed benchmark. Later Olist verification addressed the first item. A configured provider and human review are still needed for benchmark claims. The public repository contains the technical deliverables, excludes original course attachments and personal information, and leaves the required development reflection to the students.
