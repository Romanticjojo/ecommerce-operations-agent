"""Compare real entry points against checked-in raw-table reference queries."""

import csv
import json
import math
import re
import os
import statistics
import tempfile
import time
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import duckdb

from .settings import ROOT, home, model_status, pinned_database


def normalized(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()[:10]
    if isinstance(value, str) and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}[T ]00:00:00(?:\.0+)?", value
    ):
        return value[:10]
    if isinstance(value, Decimal):
        return float(value)
    return value


def equal_cell(left, right, tolerance):
    left, right = normalized(left), normalized(right)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(left, right, rel_tol=1e-9, abs_tol=tolerance)
    return left == right


def same_rows(expected, actual, ordered, tolerance):
    if len(expected) != len(actual):
        return False

    def equals(row, other):
        return len(row) == len(other) and all(
            equal_cell(a, b, tolerance) for a, b in zip(row, other)
        )

    if ordered:
        return all(equals(x, y) for x, y in zip(expected, actual))
    remaining = list(actual)
    for row in expected:
        index = next((i for i, r in enumerate(remaining) if equals(row, r)), None)
        if index is None:
            return False
        remaining.pop(index)
    return True


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, mode="w", delete=False) as f:
        json.dump(
            obj, f, ensure_ascii=False, indent=2, default=normalized, allow_nan=False
        )
        temp = f.name
    os.replace(temp, path)


def summarize(records, variant):
    rows = [r for r in records if r["variant"] == variant]
    sql_rows = [r for r in rows if r["generated_sql"]]
    answerable = [r for r in rows if r["expected_status"] == "ok"]
    correct = sum(r["correct"] is True for r in rows)
    reference = variant == "reference"
    return dict(
        variant=variant,
        total=len(rows),
        correct=None if reference else correct,
        accuracy=None if reference else correct / len(rows),
        execution_accuracy=None
        if reference or not answerable
        else sum(r["correct"] for r in answerable) / len(answerable),
        sql_success_rate=None
        if not sql_rows
        else sum(r["sql_success"] for r in sql_rows) / len(sql_rows),
        median_ms=round(statistics.median(r["latency_ms"] for r in rows), 2),
        errors=dict(Counter(r["error_type"] for r in rows if r["error_type"])),
        reference_sql_count=sum(bool(r["reference_ran"]) for r in rows),
    )


def evaluate(db, mode, limit=None, output=None):
    with pinned_database(Path(db)) as snapshot:
        return _evaluate_snapshot(snapshot, mode, limit, output)


def _evaluate_snapshot(db, mode, limit, output):
    from .agent import ask
    from .data import catalog

    if mode == "model" and not model_status()["configured"]:
        raise SystemExit(
            "Set LLM_BASE_URL and LLM_MODEL before evaluating the real model."
        )
    cases = json.loads((ROOT / "evaluation" / "questions.json").read_text())
    if limit is not None:
        if not 1 <= limit <= len(cases):
            raise ValueError("limit must be between 1 and 55")
        cases = cases[:limit]
    variants = {
        "reference": ["reference"],
        "demo": ["demo"],
        "model": ["direct", "full"],
    }[mode]
    results = []
    with duckdb.connect(str(db), read_only=True) as conn:
        for case in cases:
            sql = case["reference_sql"]
            started = time.perf_counter()
            expected = conn.execute(sql).fetchall() if sql else []
            reference_ms = (time.perf_counter() - started) * 1000
            for variant in variants:
                start = time.perf_counter()
                status, correct, issue, actual_sql, sql_success = (
                    "reference_only",
                    None,
                    None,
                    None,
                    None,
                )
                usage = cost = prompt_version = None
                generated_sql = False
                if mode != "reference":
                    response = ask(
                        db,
                        case["question"],
                        mode=mode,
                        language="en",
                        variant="direct" if variant == "direct" else "full",
                    )
                    status = response["status"]
                    evidence = response.get("evidence") or {}
                    actual_sql = evidence.get("sql")
                    generated_sql = evidence.get("generated_sql", bool(actual_sql))
                    sql_success = evidence.get(
                        "sql_success",
                        bool(actual_sql and status in ("ok", "insufficient_data")),
                    )
                    if status != case["expected_status"]:
                        correct, issue = False, "status:" + status
                    elif sql:
                        actual = [list(row.values()) for row in response["table"]]
                        correct = same_rows(
                            expected, actual, case["ordered"], case["tolerance"]
                        )
                        issue = None if correct else "result_mismatch"
                    else:
                        correct = True
                    usage = response.get("usage")
                    cost = response.get("estimated_cost_usd")
                    prompt_version = evidence.get("prompt_version")
                results.append(
                    dict(
                        id=case["id"],
                        category=case["category"],
                        question=case["question"],
                        variant=variant,
                        status=status,
                        expected_status=case["expected_status"],
                        correct=correct,
                        reference_ran=bool(sql),
                        expected_rows=len(expected),
                        generated_sql=generated_sql,
                        sql_success=sql_success,
                        error_type=issue,
                        latency_ms=round(
                            reference_ms
                            if mode == "reference"
                            else (time.perf_counter() - start) * 1000,
                            2,
                        ),
                        usage=usage,
                        estimated_cost_usd=cost,
                        prompt_version=prompt_version,
                    )
                )
    meta = catalog(db)
    report = dict(
        status="completed",
        mode=mode,
        model=model_status()["model"] if mode == "model" else None,
        created_at=datetime.now(timezone.utc).isoformat(),
        snapshot=meta["snapshot_id"],
        source=meta["source"],
        human_review="pending",
        summary=[summarize(results, v) for v in variants],
        results=results,
    )
    write_json(home() / "evaluation.json", report)
    if output:
        output = Path(output)
        write_json(output / "report.json", report)
        with (output / "results.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(results)
    return report
