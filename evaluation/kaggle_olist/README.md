# Olist acceptance tests

Fifteen pytest cases run Commerce Lens against the full Brazilian E-Commerce dataset published by Olist. The suite imports the source CSVs into a fresh DuckDB database, starts the real HTTP service on a temporary local port and compares its answers with independent calculations from the CSVs. The business questions use English and offline demo mode.

[Read the verified report](verified/REPORT.md) · [Inspect requests and results](verified/results.json) · [Check source files and versions](verified/manifest.json)

## Follow the revenue case

K03 asks **“What is total item revenue?”** The independent reference selects delivered order IDs and sums their item prices, excluding freight. On dataset version 2, the CSV calculation and the service both returned **BRL 13,221,498.11**. [Watch the terminal run (MP4)](media/K03-revenue.mp4) · [Inspect the recorded K03 result](media/K03-results.json)

To try the same question in the workbench, download the full application, import the Olist CSVs as described in the project README and run `./scripts/start.sh` from the project root. Open **Ask the agent**, confirm the header shows offline demo mode, enter the question and click **Run analysis**. Expand **Query evidence and SQL** to inspect the executed query. [Download the full application](https://github.com/Romanticjojo/ecommerce-operations-agent/archive/refs/heads/main.zip) · [Open the local workbench](http://127.0.0.1:8731/#ask) · [Watch the workbench recording (MP4)](https://raw.githubusercontent.com/Romanticjojo/ecommerce-operations-agent/main/docs/media/K03-workbench.mp4)

## Run the suite

Run these commands from the repository root or from the root of the standalone test archive on macOS or Linux with Python 3.11. Use version 2 to reproduce the published results.

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r evaluation/kaggle_olist/requirements.txt
.venv/bin/python -m pytest -q evaluation/kaggle_olist/cases.py \
  --olist-version 2 --olist-output runtime/kaggle-v2
```

To run against the latest version, omit `--olist-version 2`. The default download call is shown below. KaggleHub caches files by version after the first download. Set `KAGGLEHUB_CACHE` to choose a different cache directory.

```python
import kagglehub

path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")
print("Path to dataset files:", path)
```

To trace K03 by itself, run the following command.

```sh
.venv/bin/python -m pytest -q -s evaluation/kaggle_olist/cases.py::test_k03_revenue \
  --olist-version 2 --olist-trace --olist-output runtime/k03
```

Each run writes `REPORT.md`, `results.json` and `manifest.json` to the specified output directory. The default directory is `runtime/kaggle-acceptance/`. To run only the timestamp-based delivery investigation, add `-k k10`. The suite runs when you explicitly select `cases.py` and returns a failing exit code if an assertion fails.

## Coverage and source files

| File | Role |
|---|---|
| `cases.py` | Fifteen cases covering imports, sales metrics, multi-row joins, delivery and review statistics, invalid input and replay of saved SQL. |
| `oracle.py` | Reads the source CSVs, sums prices with decimal arithmetic, selects the latest valid review per order and computes the risk difference and its confidence interval. |
| `conftest.py` | Resolves the data version, builds the temporary database, starts the server and records HTTP requests and comparisons. |
| `reporting.py` | Generates the Markdown report, machine-readable results and manifest from the same pytest session. |
| `verified/` | Contains the archived results of the full version 2 run. |

The download contains nine CSVs. The importer loads seven core tables and a category translation table. The manifest also records the geolocation file's row count, byte size and SHA-256. Olist publishes the data under CC BY-NC-SA 4.0. [Olist dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
