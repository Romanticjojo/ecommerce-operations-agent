# Operator guide

## Prepare a dataset

For the DSC 200 project, use the Brazilian E-Commerce Public Dataset by Olist, version 2. Install the Kaggle dependencies in the project's virtual environment and run the importer from the repository root.

```sh
python -m pip install -r evaluation/kaggle_olist/requirements.txt
python -m commerce.cli olist
```

The Docker image includes KaggleHub. Local installation, Docker, existing CSV directories and the separate synthetic fixture workflow are covered in the README. Confirm the dataset label, source dates and snapshot in the workbench before interpreting a result. Olist v2 covers purchases from September 2016 through October 2018. [Startup instructions](../README.md) · [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

## Ask an operational question

Offline demo mode recognizes a limited set of sales totals, order trends, category rankings, average order value and review questions. Try one of these examples.

- Show the top 10 product categories by item revenue in 2018.
- Show monthly delivered orders in 2017.
- What is total item revenue?
- What is average order value?
- Are late deliveries associated with negative customer reviews?

Model mode supports plans for sales totals, monthly trends, category or customer-state breakdowns and order-level review analysis. Specify the metric and grouping. Purchase-date filters include the start date and exclude the end date. The application reads server-side model configuration at startup. The planner mode and the source of the data are independent. For example, an offline planner can query a real Olist snapshot.

## Choose a skill or open the data reference

Open **Ask the agent → Questions & skills**. On desktop select a skill by name. On a small screen use **Choose an analysis skill**. Each skill lists its purpose, supported scope, example and analysis steps. The date fields use the local purchase date and an exclusive end. In offline demo mode these procedures run directly. In model mode, look for **Model-planned skill** before running and **Live model** alongside **Local analysis skill** on success. The provider plans the call and the local engine produces the English conclusion. Select **Back to custom question** to resume free-form questions.

For a keyboard-only demo, type **Rank merchants** or **Analyze product sales trends** into the question field. The scorecard presents all eligible sellers with pagination, score components and full JSON export. The product outlook presents an individual SKU's three monthly observations and its conditional next action. [Merchant scoring](merchant-scoring.md) · [Sales, retention and outlook methods](operations-methods.md)

**Delivery comparison** retains the original statistical investigation, including timestamp and calendar-day sensitivity. A lane's late-order percentage in the **Delivery performance** skill measures a different outcome from the comparison's negative-review percentage. **Data reference** contains snapshot source, table definitions, metric catalog and import-quality checks. The overview links open each tool in context.

## Interpret the metrics

| Metric | Definition |
|---|---|
| Item revenue | Sum of item prices on delivered orders. Freight is separate. |
| Order count | Distinct delivered orders at the requested grain. Category counts can overlap. |
| Average order value | Delivered item revenue divided by the number of delivered orders. |
| Payment total | Aggregate payment sequences per order before joining. |
| Negative review | A score of 1 or 2 among valid scores from 1 to 5. |
| Late delivery | Actual delivery after the estimate. The primary comparison uses timestamps, with calendar dates available as a sensitivity check. |
| Risk difference | Late negative-review rate minus on-time negative-review rate, expressed in percentage points. |

The investigation selects one review per eligible order. It takes the latest answer, then the latest creation time and breaks remaining ties by review ID and source row. Raw review records remain available for descriptive analysis. Orders without a valid score or both delivery times are excluded. With two nonempty groups, the analyzer calculates a Newcombe-Wilson interval. For variable outcomes it selects a two-sided Fisher exact test if an expected cell count is below 5, otherwise Pearson's chi-squared test without continuity correction. The comparison describes an observational association. [Methods and exclusions](data-dictionary.md)

## Find and maintain the implementation

| Location | Responsibility |
|---|---|
| `commerce/data.py`, `schema.py`, `demo.py` | Import source tables, create views, report data quality and generate synthetic fixtures. |
| `commerce/model.py`, `plans.py`, `agent.py` | Interpret a question, generate or compile SQL and assemble a traceable answer. |
| `commerce/query_guard.py`, `query_worker.py` | Validate candidate SQL and execute it in a read-only worker. |
| `commerce/stats.py`, `benchmark.py` | Investigate review rates and evaluate the two model variants against references. |
| `commerce/api.py`, `history.py` | Serve the UI and API and retain up to 200 local requests in SQLite. |
| `frontend/src/` | React workbench. Rebuild through the native startup script or the container build after a UI change. |

FastAPI exposes interactive request and endpoint documentation at `/docs`. When changing a metric, update its catalog definition, independent reference SQL, tests and acceptance record together.

## Troubleshooting

| Symptom | Checks and recovery |
|---|---|
| Synthetic data still appears | Confirm the Olist import finished. Refresh the page and check snapshot and source row counts. Native and container deployments use separate data locations. |
| The workbench asks for clarification | Check the active mode, try a listed example and supply a metric, grouping or date. A configured model can interpret a broader range of wording. |
| Model request fails | Check the provider's API path/version, model name, network reachability and credentials on the server. |
| Container cannot reach a model on the host | Use the host address supported by Docker. Loopback inside a container points to that container. |
| Missing CSV or invalid type | Check exact headers, original filenames, encoding and the import error. |
| Evaluation has no model scores | Run the model evaluation with one snapshot and one model configuration. Set pricing if a cost estimate is needed. |
| Local port is occupied | Use `PORT=8732 ./scripts/start.sh` or `PORT=8732 docker compose up -d`. |
| Reproduce an earlier analysis | Export its evidence from history and keep the matching source CSV hashes. Recreate the snapshot in a separate `LENS_HOME` and run the saved query. |

Students can use the test record and release history when documenting what they personally worked on. The course requires the students' own development reflection.
