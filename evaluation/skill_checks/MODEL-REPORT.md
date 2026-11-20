# Model-planned skills on Olist v2

**24 of 26 end-to-end cases passed with Qwen2.5-1.5B-Instruct.** All nine skill-button requests and the nine initial free-form questions reached the intended procedure. Two additional phrasings produced invalid plans. Both recovered when the operator chose the named skill and applied the date controls.

The workbench and the real, locally loaded model ran in separate processes. Each test submitted an ordinary HTTP request to `/api/query` with mode set to `auto`. The application called `/v1/chat/completions`, validated the returned plan and ran the procedure in DuckDB. All 26 responses carried provider-reported token usage. The database was the Olist v2 snapshot `a0fc02b4ba5e65b648f23d3e6171549b0e2b34f7950f34ed65e617a5ab042840`.

| Cases | What was exercised | Passed |
|---|---|---:|
| Q01–Q09 | Free-form questions covering each of the nine skill IDs | 9 / 9 |
| B01–B09 | The same requests the workbench sends when a user chooses a skill | 9 / 9 |
| D01–D02 | Intersect a named calendar year with an entered start date; select a period outside Olist coverage | 2 / 2 |
| U01–U02 | Cart-abandonment and causal coupon-lift questions, both requiring unavailable data | 2 / 2 |
| H01–H04 | Four additional questions introduced after the initial prompt revisions | 2 / 4 |

A case passes when the response records the configured model, expected status, skill, date bounds and snapshot. For a skill, its SQL, every table row and its conclusion must match an explicit offline execution on the same snapshot. For an unsupported question, the check requires clarification with no executed query. Independent source-CSV reconciliation is covered by the [merchant score oracle](merchant_oracle.py). The 26 cases are engineering acceptance examples. The initial 22 informed integration fixes; the sample does not estimate accuracy on arbitrary business questions. [All inputs, plans, usage, output and checks](model-results.json) · [Executable cases](model_routing.py)

## What the test caught

- Earlier, clicking **Run skill** bypassed the provider even when a model was configured. Both the button and free-form paths now use the planner in model mode. In demo mode the same buttons work offline.
- The local model sometimes wrapped JSON in a Markdown fence or used empty optional date strings. The adapter accepts an isolated fenced JSON object and unspecified dates. Surrounding prose, multiple answers and invalid dates still fail validation.
- In D01 the model picked the merchant scorecard and supplied the UI start date, but omitted the requested calendar year. The controller preserved the explicit year and applied the final window from April 1, 2018 through January 1, 2019, end exclusive. The answer covered 346 sellers.
- In U02 the model proposed price and volume for a causal coupon question. The application checked the data scope and returned clarification before executing SQL. The machine-readable record retains the proposed plan and the reason it was stopped.
- H02 (a support team prioritizing complaints) and H03 (replenishment through June 30, 2018) both exhausted the single repair and returned `invalid_plan` with zero data rows. Repeating H02 via **Reviews and aftercare** returned 21 rows. Repeating H03 via **Product sales outlook** with **End date = 2018-07-01** returned 15 rows. Both selected-skill responses matched the reference SQL and data. These recovery runs are separate from the 24 passes.
- A headless Chrome run selected **Merchant scorecard**, observed a real provider response, displayed all 784 eligible sellers and advanced to the second page. The first seller scored 93.76/100. [Browser screenshot](../../docs/images/model-skill-run.png)

## Assistant-supplied planner control

Four further free-form HTTP requests were made against the same snapshot. A loopback relay forwarded the application's actual planner messages to the current Codex session. The assistant returned one JSON plan for each request. The normal controller then handled validation, SQL and the English conclusion. These four orchestration controls all matched their expected outcomes; this was an assisted test and its requests are excluded from the Qwen results. [Questions, returned plans, date bounds and conclusions](assistant-control.json)

| Question | Plan and observed outcome |
|---|---|
| Chinese request for the 2018 seller ranking | Merchant scorecard, calendar year 2018. Ranked 536 eligible sellers. The leader scored 92.25/100. |
| Next reorder using only purchases before July 2018 | Product sales outlook, exclusive end July 1, 2018. Returned 15 SKU rows. |
| Products with recurring written complaints | Reviews and aftercare. Returned the overall population plus 20 product rows. |
| Exact current warehouse inventory | Clarification; no query ran. |

## Reproduce with a compatible provider

Use the endpoint and model ID you want to evaluate. The published real-model run used the official Q4_K_M weights with SHA-256 `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`. The workbench sent temperature 0. The server ran with one slot, an 8,192-token context and a 256-token generation limit. [Model revision](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/tree/91cad51170dc346986eccefdc2dd33a9da36ead9) · [llama.cpp build b12559](https://github.com/ggml-org/llama.cpp/releases/tag/b12559)

With that model and runtime installed, start the model in one terminal.

```sh
llama-server -m /path/to/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  --alias qwen2.5-1.5b-instruct-q4_k_m --host 127.0.0.1 --port 18741 \
  --parallel 1 -c 8192 -n 256 --no-webui
```

Start a separate workbench against a copy of your imported Olist snapshot. Run the following from the repository root in a second terminal. This keeps the evaluation traffic in its own run history.

```sh
trial_dir=$(mktemp -d)
cp runtime/commerce.duckdb "$trial_dir/commerce.duckdb"
LENS_HOME="$trial_dir" LLM_BASE_URL=http://127.0.0.1:18741/v1 \
  LLM_MODEL=qwen2.5-1.5b-instruct-q4_k_m LLM_API_KEY='' PORT=18742 ./scripts/start.sh
```

From a third terminal, run the acceptance cases.

```sh
.venv/bin/python -m evaluation.skill_checks.model_routing \
  --app-url http://127.0.0.1:18742 --out runtime/my-model-results.json
```

The runner writes every outcome and exits with status 1 if any case fails. Results may vary with model, quantization, runtime and prompt version. For a hosted provider, configure its actual endpoint, model ID and key on the server. The endpoint used for this report required no key. The unconfigured installation continues to use demo mode.
