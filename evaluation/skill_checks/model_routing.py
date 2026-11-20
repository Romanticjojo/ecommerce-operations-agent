"""Exercise the real query API against any configured Chat Completions planner."""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import httpx


@dataclass(frozen=True)
class Case:
    name: str
    question: str
    skill: str | None
    status: str = "ok"
    ui_start: str | None = None
    ui_end: str | None = None
    expected_start: str | None = None
    expected_end: str | None = None
    selected: bool = False


def cases(catalog):
    questions = [
        ("sales-growth", "Break down our recent change in sales into shopper counts, orders per shopper and basket size."),
        ("retention", "How often did buyers return within ninety days, grouped by what they bought on their first order?"),
        ("assortment", "Which merchandise categories gained or lost the most units between the last two comparable months?"),
        ("price-volume", "Across matched products, how did unit sales move when the same SKU sold at a higher or lower price?"),
        ("seller-growth", "Find merchants whose sales revenue kept growing month after month."),
        ("fulfillment", "Which merchants and state-to-state shipping lanes have the most frequent late arrivals?"),
        ("reviews-aftercare", "Which products should customer support investigate based on Portuguese complaint themes and low star ratings?"),
        ("merchant-score", "Score and rank the sellers using their buyer ratings and on-time performance."),
        ("product-trend", "Use each SKU’s recent monthly unit trajectory to suggest a small reorder or an assortment check."),
    ]
    result = [Case("Q%02d" % i, question, slug) for i, (slug, question) in enumerate(questions, 1)]
    result.extend(Case("B%02d" % i, catalog[slug]["question"], slug, selected=True)
                  for i, (slug, _) in enumerate(questions, 1))
    result.extend([
        Case("D01", "Rank the merchants on ratings and punctuality for calendar year 2018.",
             "merchant-score", ui_start="2018-04-01", expected_start="2018-04-01", expected_end="2019-01-01"),
        Case("D02", catalog["product-trend"]["question"], "product-trend", "insufficient_data",
             ui_start="2030-01-01", expected_start="2030-01-01", selected=True),
        Case("U01", "How many visitors abandoned a shopping cart between visiting a product page and checking out?",
             None, "clarification_required"),
        Case("U02", "What incremental revenue did issuing discount coupons cause compared with a randomized control group?",
             None, "clarification_required"),
        Case("H01", "Shortlist merchants with consistently rising takings and show their share of the marketplace.",
             "seller-growth"),
        Case("H02", "Support can investigate just a few items. Where do poor ratings pile up, and what do the written comments mention?",
             "reviews-aftercare"),
        Case("H03", "Using purchases through June 30, 2018, which SKUs deserve a replenishment check based on monthly units?",
             "product-trend", expected_end="2018-07-01"),
        Case("H04", "How many units were physically in merchants’ warehouses yesterday?", None, "clarification_required"),
    ])
    return result


def submit(client, body):
    response = client.post("api/query", json=body)
    response.raise_for_status()
    return response.json()


def evaluate(client):
    def get(path):
        response = client.get(path)
        response.raise_for_status()
        return response.json()

    settings = get("api/config/status")
    if not settings["configured"]:
        raise SystemExit("Start the test workbench with a configured model endpoint and model ID.")
    source = get("api/overview")
    if source["source"] != "olist":
        raise SystemExit("Import Olist v2 in the test workspace first.")
    catalog = {s["id"]: s for s in get("api/skills")["skills"]}
    results = []
    for case in cases(catalog):
        payload = {"question": case.question, "mode": "auto"}
        if case.ui_start:
            payload["start"] = case.ui_start
        if case.ui_end:
            payload["end"] = case.ui_end
        if case.selected:
            payload["skill_id"] = case.skill
        run = submit(client, payload)
        ev = run["evidence"]
        filters = ev.get("filters", {})
        checks = {
            "model_path": run["mode"] == "model" and ev["model"] == settings["model"] and ev["model_ms"] > 0,
            "snapshot": ev["snapshot"] == source["snapshot_id"],
            "status": run["status"] == case.status,
            "skill": ev.get("skill_id") == case.skill,
        }
        if case.skill:
            expected = submit(client, {"question": catalog[case.skill]["question"], "skill_id": case.skill,
                                       "mode": "demo", "start": case.expected_start, "end": case.expected_end})
            checks.update(
                date_bounds=(filters.get("start"), filters.get("end")) == (case.expected_start, case.expected_end),
                execution=ev.get("execution") == "local_skill" and ev["sql_success"],
                reference=expected["status"] == case.status and expected["evidence"]["snapshot"] == ev["snapshot"]
                          and expected["table"] == run["table"] and expected["answer"] == run["answer"]
                          and expected["evidence"]["sql"] == ev["sql"],
            )
        else:
            checks["no_query"] = not ev["sql_success"] and not run["table"] and not ev.get("sql")
        result = {"id": case.name, "entry": "selected" if case.selected else "free_text", "question": case.question,
                  "expected": {"skill": case.skill, "status": case.status, "start": case.expected_start, "end": case.expected_end},
                  "actual": {"skill": ev.get("skill_id"), "status": run["status"], "filters": filters,
                             "rows": len(run["table"]), "plan": ev.get("plan"), "error": ev.get("error_code"),
                             "answer": run["answer"], "model_ms": ev["model_ms"], "usage": run.get("usage"),
                             "calendar_year": ev.get("calendar_year"), "scope_reason": ev.get("scope_reason"), "repairs": ev["repairs"]}, "checks": checks, "passed": all(checks.values())}
        results.append(result)
        print(case.name, "PASS" if result["passed"] else "FAIL", run["status"], ev.get("skill_id"), flush=True)
    return {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model": settings["model"],
            "snapshot": source["snapshot_id"], "prompt_version": ev["prompt_version"],
            "passed": sum(r["passed"] for r in results), "total": len(results), "cases": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-url", default="http://127.0.0.1:8731")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with httpx.Client(base_url=args.app_url.rstrip("/") + "/", timeout=160, trust_env=False) as client:
        report = evaluate(client)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"{report['passed']}/{report['total']} passed. Results in {args.out}")
    return int(report["passed"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
