# Source review and design decisions

The November 19, 2026 review gave precedence to the user's request, the course rubric and instructor feedback, then the original proposal. The AI-authored specification and blueprint supplied implementation suggestions. The original course PDFs remain in the user's attachments. The public materials omit student names, contact details and grading screenshots.

## Course rubric and proposal

The two-page **DSC 200 Project Update** rubric gives a deadline of Monday, November 23, 2026. It requests one PDF plus a source ZIP or an accessible GitHub repository. The specification has a four-page maximum unless a longer submission is justified. The engineering documentation is separate from the four-page submission.

The specification must explain the problem, goal, scope, work distribution, data schema, storage, assumptions and constraints. It needs at least three functional and three nonfunctional requirements, with the graded subset identified if more are listed. At least three UML diagram types each need an explanation and a reason for the choice. At least three unit and three functional cases each need inputs, steps, preconditions, expected results and postconditions. The check-in asks which requirements and tests pass, what is pending, and what the team would change in the specification. Students must write the one- or two-paragraph development reflection themselves. The rubric's Data Models heading and subitems show different point totals. The submission addresses all listed items. [Editable project update](course/project-update.md)

The original submission PDF has feedback on page 1, a scanned proposal on page 2 and a blank final page. Page 2 gives the exact title **E-commerce Operations Agent**. It identifies small online retailers and e-commerce operators as users and the **Brazilian E-Commerce Public Dataset by Olist** as the source, with about 100,000 orders across linked CSVs in 2016–2018. It describes anonymized data licensed CC BY-NC-SA 4.0. Source code and data retain separate licenses.

The proposal's five completion criteria covered natural-language questions, statistics and visualization, investigation of potential causes of negative reviews, evidence-backed recommendations, and validation and traceability. Instructor feedback asked the team to concentrate on two or three, identify the system approach, explain how accuracy would be verified and describe how linked tables would be queried. This release focuses on sales analysis, delivery and negative-review association, and evidence retrieval. The association cannot establish causation.

## Decisions on the AI drafts

| Suggestion | Decision and rationale |
|---|---|
| Sales plus negative-review analysis | Retain. Both have observable answers and respond to the instructor's request for focus. |
| One agent with bounded deterministic tools | Retain. A local controller and explicit tool contracts are practical to test and deploy. |
| DuckDB source tables and analytical views | Retain. Separate grains and preaggregate money to prevent multiplication when joining. |
| Streamlit workbench | Use React and FastAPI for the requested Apple-inspired interface and browser interactions. |
| 55 reference questions | Retain the fixed suite. Track independent human review explicitly. |
| 90% result accuracy and 95% SQL success | Retain as targets for real-model testing. |
| Treat each review as an independent observation | Use one review per order for inference and retain record-level descriptive statistics. |
| Six-week roadmap | Record actual stage deliverables and observed verification dates. |
| Automatic recommendations | Present evidence and hypotheses for an operator to investigate. Live operating actions and causal identification are outside scope. |

## Design references and data provenance

The design review inspected DB-GPT's README, AWEL DAG example and action interfaces at commit `decf2726ab7fcc8d5e7e0ea638d38362a7cc220f` (November 18, 2026 UTC). It informed typed workflow stages, tool contracts and the separation of execution from display. Commerce Lens implements this workflow in its own application. [Pinned README](https://github.com/eosphoros-ai/DB-GPT/blob/decf2726ab7fcc8d5e7e0ea638d38362a7cc220f/README.md) · [AWEL example](https://github.com/eosphoros-ai/DB-GPT/blob/decf2726ab7fcc8d5e7e0ea638d38362a7cc220f/examples/awel/simple_dag_example.py) · [Action interface](https://github.com/eosphoros-ai/DB-GPT/blob/decf2726ab7fcc8d5e7e0ea638d38362a7cc220f/packages/dbgpt-core/src/dbgpt/agent/core/action/base.py)

Light surfaces, near-black text, blue controls, system typography and fine dividers informed the workbench. The project supplies its own assets. [Design reference](https://designmd.me/discover/apple) · [Interface guide](../DESIGN.md)

The publisher's metadata for the downloaded Olist dataset identifies CC BY-NC-SA 4.0. Kaggle version 2 has nine files. The acceptance suite audits every file, the warehouse imports the seven business tables and category translation, and geolocation remains audit-only. End users obtain the original CSVs from the publisher. [Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) · [Source manifest](../evaluation/kaggle_olist/verified/manifest.json) · [Verification record](verification.md)
