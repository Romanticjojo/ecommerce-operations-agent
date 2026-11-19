# Project status and release history

The November 19, 2026 check-in selected three outcomes from the original proposal: sales questions, a delivery and negative-review investigation, and traceable evidence. Commerce Lens is the local web interface for **E-commerce Operations Agent**. The course release uses Olist's Brazilian marketplace data for 2016–2018. [Verification record](verification.md) · [GitHub Actions](https://github.com/Romanticjojo/ecommerce-operations-agent/actions)

| Stage | Deliverable | Evidence |
|---|---|---|
| Requirements | Three course priorities, a compatible provider API and requirements linked to tests | PRD, design decisions and rubric review |
| Data and metrics | Seven business tables, optional category translation, five reporting views, audit and synthetic fixtures. On Olist v2, eight CSVs imported and all nine source files audited. | Dictionary, warehouse tests, independent Olist reconciliation |
| Agent | Typed plan, metric compiler, read-only worker, answer and evidence | HTTP contract, bounded repair, rejection and timeout tests |
| Statistics | Order-level inference, review-record descriptions, calendar-day sensitivity, tests and intervals | Hand-counted fixture and two Olist contingency tables |
| Workbench | Overview, questions, investigation, data dictionary, evaluation and history | Desktop/mobile browser, copy, export and keyboard checks |
| Evaluation | 55 questions, raw-table references, offline coverage and real-model comparison runner | Verified CSV outputs. Real-model results and human review are pending. |
| Deployment | Native launcher, Python/npm lock files, Docker and CI | Clean install and release checks |
| Maintenance | Versioned source, run history, snapshot hashes, license and repeatable checks | Metric changes require corresponding dictionary, reference, test and report changes. |

## Design decisions and evidence

The full workflow asks a model for a structured plan. The backend compiles the metric, time window and grouping into SQL. The direct baseline asks for SQL. Both share the same execution limits. This makes the effect of planning testable under the same conditions.

The public source includes a reproducible synthetic generator and a version-pinned Olist import path. Independent aggregates over Olist CSVs confirmed the reported sales and review counts. Provider-specific accuracy, token consumption and timing still require a run on the chosen model. [Olist acceptance report](../evaluation/kaggle_olist/verified/REPORT.md)

The English edition uses English navigation, demo prompts, documentation and a four-page course brief. The technical materials are ready for students to review. Actual team assignments and a first-person development reflection remain student inputs. [Editable course brief](course/project-update.md)
