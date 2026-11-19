"""Generate the acceptance report from observations recorded by pytest."""

import json


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)


def write_reports(directory, metadata, cases, exit_code):
    directory.mkdir(parents=True, exist_ok=True)
    passed = sum(c["status"] == "PASS" for c in cases)
    payload = {
        "pytest_exit_code": exit_code,
        "passed": passed,
        "total": len(cases),
        "environment": metadata,
        "cases": cases,
    }
    (directory / "results.json").write_text(dump(payload) + "\n", encoding="utf-8")
    (directory / "manifest.json").write_text(dump(metadata) + "\n", encoding="utf-8")
    version = metadata.get("resolved_version") or "unknown"
    lines = [
        "# Olist acceptance report",
        "",
        f"**{passed} of {len(cases)} cases passed.** pytest exited with code `{exit_code}`.",
        "",
        f"Run recorded at `{metadata.get('utc', 'unknown')}` on "
        f"`{metadata.get('platform', 'unknown')}` with Python `{metadata.get('python', 'unknown')}`.",
        "",
        f"The suite used version **{version}** of the Olist dataset. "
        f"DuckDB snapshot `{metadata.get('snapshot', 'unknown')}`. "
        "[Olist dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)",
        "",
        "KaggleHub resolves the dataset, then pytest builds a fresh DuckDB database and starts "
        "the application on a temporary local port. A separate Python reference reads the original "
        "CSVs, sums monetary values with decimal arithmetic and calculates the statistical intervals. "
        "Business questions run in English using offline demo mode.",
        "",
        "Each request uses the same snapshot. The application saves query history in the temporary "
        "environment and the test session shuts down the server. Case timings cover requests and "
        "assertions. Dataset preparation happens once before the cases run.",
        "",
        "[Recorded results](results.json) · [Source file hashes and environment](manifest.json) · "
        "[Watch the K03 terminal run (MP4)](https://raw.githubusercontent.com/Romanticjojo/ecommerce-operations-agent/main/evaluation/kaggle_olist/media/K03-revenue.mp4)",
        "",
        "## Reproduce the run",
        "",
        "From the root of the repository or the standalone test archive, create a Python 3.11 "
        "environment and install the dependencies.",
        "",
        "```sh",
        "python3.11 -m venv .venv",
        ".venv/bin/python -m pip install -r evaluation/kaggle_olist/requirements.txt",
        "```",
        "",
        "With the default options, pytest calls KaggleHub to resolve the latest dataset version.",
        "",
        "```python",
        "import kagglehub",
        'path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")',
        'print("Path to dataset files:", path)',
        "```",
        "",
        "To reproduce this run, specify the recorded version. The second command runs only "
        "the revenue case and prints the HTTP request, expected total and observed total.",
        "",
        "```sh",
        f".venv/bin/python -m pytest -q evaluation/kaggle_olist/cases.py --olist-version {metadata.get('resolved_version') or '2'}",
        f".venv/bin/python -m pytest -q -s evaluation/kaggle_olist/cases.py::test_k03_revenue --olist-version {metadata.get('resolved_version') or '2'} --olist-trace --olist-output runtime/k03",
        "```",
        "",
        "The full suite writes `REPORT.md`, `results.json` and `manifest.json` to "
        "`runtime/kaggle-acceptance/`. The single-case command writes its own copies to `runtime/k03/`.",
        "",
        "## Data and environment",
        "",
        f"Olist publishes the source data under {metadata.get('data_license', 'unknown')}. "
        "Record counts exclude the header and count CSV records across embedded line breaks.",
        "",
        "| Source file | Use | Records | Bytes | SHA-256 |",
        "|---|---|---:|---:|---|",
        *[
            f"| `{file}` | {'Audit only' if 'geolocation' in file else 'Imported'} | {entry['rows']:,} | {entry['bytes']:,} | `{entry['sha256']}` |"
            for file, entry in metadata.get("files", {}).items()
        ],
        "",
        "Package versions used in this run include "
        + ", ".join(
            f"`{key} {value}`" for key, value in metadata.get("packages", {}).items()
        )
        + ".",
        "",
        "## Results by case",
        "",
        "| Case | Check | Result | Time (ms) |",
        "|---|---|---|---:|",
    ]
    for case in cases:
        lines.append(
            f"| {case['id']} | {case['title']} | {case['status']} | {case['duration_ms']:.2f} |"
        )
    lines += [
        "",
        "## Case evidence",
        "",
        "Request date ranges include the start and exclude the end. Monetary values are in "
        "Brazilian reais (BRL). Each case records its inputs and comparisons, including the "
        "executed SQL when available.",
    ]
    for case in cases:
        lines += [
            "",
            f"### {case['id']} · {case['title']}",
            "",
            case["procedure"],
            "",
            f"**{case['status']}**",
            "",
            "<details><summary>Requests, executed SQL, expected values and observations</summary>",
            "",
            "```json",
            dump(
                {
                    "requests": case["requests"],
                    "checks": case["checks"],
                    **({"reason": case["reason"]} if "reason" in case else {}),
                }
            ),
            "```",
            "",
            "</details>",
        ]
    (directory / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
