# E-commerce Operations Agent

**DSC 200 · Data Science Programming · Fall 2026**
Commerce Lens is the local workbench for the *E-commerce Operations Agent*. Ask about Brazilian marketplace orders, run nine repeatable operations analyses, or inspect the data and SQL behind an answer.

**The default is offline demo mode.** With the course dataset imported, all nine analysis skills run on real Olist records with no API key. An optional compatible model can interpret free-form questions. The workbench identifies whether a particular run used a local skill or a provider.

[Download the current complete project ZIP](https://github.com/Romanticjojo/ecommerce-operations-agent/releases/latest/download/commerce-lens.zip) · [Four-page course project update (PDF)](docs/course/project-update.pdf) · [Original v1.0 walkthrough (MP4)](https://raw.githubusercontent.com/Romanticjojo/ecommerce-operations-agent/main/docs/media/K03-workbench.mp4)

![The English question workspace showing the skill directory and merchant scorecard scope](docs/images/analysis-skills.png)

## Run the course dataset locally

Install Docker with Docker Compose. From the repository root, run:

```sh
docker compose build
docker compose run --rm workbench python -m commerce.cli olist
docker compose up -d --wait
```

Open [the workbench](http://127.0.0.1:8731). The import downloads **version 2** of `olistbr/brazilian-ecommerce` through KaggleHub, builds a local DuckDB database and installs it into the shared Compose volume. The first import requires internet access. Subsequent starts only need `docker compose up -d --wait`. The overview identifies the dataset currently loaded. Use `docker compose down` to stop.

For a native installation on macOS or Linux, use Python 3.11 and Node.js 22:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r evaluation/kaggle_olist/requirements.txt
.venv/bin/python -m commerce.cli olist
./scripts/start.sh
```

The native script builds the frontend and serves it on port 8731. Set `PORT` to choose another port and `LENS_HOME` to choose the local database directory (default `runtime/`). Native and container installations use separate storage. If you already have the official CSVs, use `.venv/bin/python -m commerce.cli import /path/to/unzipped-olist`. To try the UI without the Kaggle download, starting an empty installation without the import creates a small synthetic fixture. All course figures below use Olist v2.

## Data scope and worked examples

The **Brazilian E-Commerce Public Dataset by Olist** contains anonymized marketplace orders. Version 2 has **99,441 orders**, purchased from **September 4, 2016 through October 17, 2018**. These are partial calendar years. We retain orders, items, payments, customers, products, sellers and reviews as separate relations. The category translation CSV supplies English labels. The ninth CSV, geolocation, is audited for its row count and fingerprint. The analysis skills use order records, item lines and state codes. [Official dataset and data license](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) · [Data dictionary](docs/data-dictionary.md)

| Task | How to reproduce it in the English UI | Olist v2 result or interpretation |
|---|---|---|
| Reconcile sales | Ask **What is total item revenue?** Open the query evidence. | **BRL 13,221,498.11** across 96,478 delivered orders. The figure sums item prices and excludes freight. Item and payment totals are aggregated separately. |
| Compare products over time | Ask **Show the top 10 product categories by item revenue in 2018.** Switch from chart to table. | Ranks categories by delivered item revenue within the recorded portion of 2018. Date filters use purchase time, with an exclusive end date. |
| Investigate negative reviews | Open **Ask the agent → Delivery comparison** and run the timestamp comparison. Repeat with the calendar-day definition. | Among 95,824 eligible reviewed orders, 4,142 of 7,661 late orders and 8,130 of 88,163 on-time orders scored 1–2. The difference was **44.84 percentage points**. The comparison establishes an association. |

The primary review analysis selects one eligible review per delivered order and requires valid scores plus actual and estimated delivery times. Group denominators, the 95% confidence interval and exclusions are available in the investigation. The dataset does not establish why an individual customer gave a low score. Live storefront actions, causal estimates and automated interventions are outside this course project.

## Run an analysis skill

Open **Ask the agent → Questions & skills**. Choose a procedure, read its scope, and select **Run skill**. Use **Purchase dates** to change the observation window. The result includes its SQL, assumptions and snapshot. Use **Export result** for the full data, or **Run history** to revisit the decision.

| Skill | Decision or output |
|---|---|
| Sales and growth | Compare revenue, buyers, purchase frequency, basket value and category contributions. |
| Customer retention and value | Compare 90-day repeat purchase and spend across first-purchase categories. |
| Products and categories | Identify unit gains and losses, then check how many sellers serve each category. |
| Price and volume | Compare realized price and unit changes for the same SKU across adjacent months. |
| Seller performance and growth | Find sellers with sustained revenue growth and inspect their market share. |
| Delivery performance | Identify state lanes and single-seller order groups with frequent late deliveries. |
| Reviews and aftercare | Find products with a high volume of low ratings, recurring feedback themes and Portuguese sentiment cues. |
| Merchant scorecard | Inspect and export every eligible seller's rank, adjusted score and underlying counts. |
| Product sales outlook | Compare SKU unit trajectories and select a next-month inventory or assortment check. |

The two former sidebar pages now live under **Ask the agent**. **Delivery comparison** retains both lateness definitions, confidence intervals and exclusions. **Data reference** covers tables, metric definitions and import quality. Overview links and existing bookmarks open these tools directly.

The full Olist v2 scorecard ranks **784 sellers**. The product review analysis covers **92,673** attributable rated orders. A historical SKU example sold **2 → 8 → 21 units** in May–July 2018, supporting a small August reorder test after a stock check. [Merchant scoring and Portuguese sentiment rules](docs/merchant-scoring.md) · [Sales and planning methods](docs/operations-methods.md) · [Results for all nine skills](evaluation/skill_checks/REPORT.md)

## Configure a language model

The agent accepts an OpenAI-compatible Chat Completions endpoint. In the **project root**, next to `compose.yaml`, copy `.env.example` to `.env` on first setup and edit the local file.

```dotenv
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=your-provider-model-id
LLM_API_KEY=your-local-key
```

Use the provider's **base URL**, including any required version prefix. The adapter appends `/chat/completions`. Set the exact **model ID** supported by the provider. The **API key** can be empty for a local endpoint that accepts unauthenticated requests. When using Docker, the endpoint must be reachable from the container. Keep credentials out of Git.

Recreate the container with `docker compose up -d --force-recreate --wait`, or restart `./scripts/start.sh` for a native installation. Open the mode control in the upper right to check the configured model ID. Submit a sales question and inspect its evidence to verify a real call. For a free-form model run, the agent sends the question, permitted schema and skill descriptions to the provider. Selected skills and recognized offline questions execute locally. Raw comments stay inside the database. It compiles the returned plan and executes the query against local reporting views.

## Reproduce the checks

From the project root with the native environment installed:

```sh
.venv/bin/python -m pytest -q tests
.venv/bin/python -m pytest -q evaluation/kaggle_olist/cases.py --olist-version 2
.venv/bin/python -m commerce.cli evaluate --mode reference
.venv/bin/python -m commerce.cli evaluate --mode demo --output runtime/demo-report
```

The application suite checks imports, statistics, query restrictions, model-adapter contracts and HTTP behavior. The 15 Kaggle acceptance cases run a real local API against a fresh snapshot and compare it to calculations from the original CSVs. The 55-question benchmark is a separate experiment. Measuring real-model direct-SQL versus structured-plan accuracy requires a configured provider and `python -m commerce.cli evaluate --mode model`. Human review of the benchmark and real-model evaluation remain pending. [Acceptance report](evaluation/kaggle_olist/verified/REPORT.md) · [Runnable test package](evaluation/kaggle_olist/olist-kaggle-acceptance.zip) · [Recorded K03 test (MP4)](https://raw.githubusercontent.com/Romanticjojo/ecommerce-operations-agent/main/evaluation/kaggle_olist/media/K03-revenue.mp4)

## Course and engineering materials

| Material | Location |
|---|---|
| Project update, requirements selected for grading, three UML diagrams and six selected tests | [PDF](docs/course/project-update.pdf) · [Editable source](docs/course/project-update.md) |
| Requirements, architecture and acceptance criteria | [PRD](docs/PRD.md) · [Architecture](docs/architecture.md) · [Acceptance plan](docs/acceptance.md) |
| Data model, metric definitions and local operation | [Data dictionary](docs/data-dictionary.md) · [Operator guide](docs/operator-guide.md) |
| Check-in status, limitations and design decisions | [Verification](docs/verification.md) · [Project status](docs/project-status.md) · [Design](DESIGN.md) · [Source review](docs/source-review.md) |

The project update reserves the personal reflection for the students, as required by the rubric. The team must confirm its actual work distribution before submission.

The code is distributed under the [MIT license](LICENSE). Olist publishes its dataset under CC BY-NC-SA 4.0. The repository distributes code, download instructions and aggregate results. Design references include [DB-GPT](https://github.com/eosphoros-ai/DB-GPT) and [DesignMD Apple](https://designmd.me/discover/apple).
