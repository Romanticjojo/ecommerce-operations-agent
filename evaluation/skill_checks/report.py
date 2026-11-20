"""Produce the English skill run report for an installed Olist v2 snapshot."""
import argparse
from pathlib import Path

import duckdb

from commerce.agent import ask
from commerce.data import catalog, rows
from commerce.skills import catalog as skill_catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = catalog(args.database)
    if source["source"] != "olist":
        parser.error("Run the Olist importer first.")
    report = ["# Olist analysis skills acceptance", "",
              f"Snapshot `{source['snapshot_id']}`. Source purchase dates cover {source['date_range']['start']} through {source['date_range']['end']}.",
              "", "Each procedure below ran locally without a model provider, using the full date range. "
              "The check reran the SQL from the answer against the snapshot and compared every field of every output row. "
              "The merchant oracle separately recomputes the score and rankings from the original CSV files.", ""]
    with duckdb.connect(str(args.database), read_only=True) as con:
        for spec in skill_catalog():
            answer = ask(args.database, spec["question"], mode="demo", skill_id=spec["id"])
            evidence = answer["evidence"]
            assert answer["status"] == "ok" and answer["mode"] == "skill", (spec["id"], answer["status"])
            assert evidence["sql_success"] and rows(con, evidence["sql"]) == answer["table"], spec["id"]
            report.extend([f"## {spec['title']}", "", spec["question"], "", answer["answer"], "",
                           f"SQL replay matched all {len(answer['table']):,} result rows.", ""])
    report.extend(["## Reproduce", "", "After importing Olist v2, run these commands from the project root. "
                   "Supply the extracted Kaggle directory containing the original CSVs as the first oracle argument.", "",
                   "```sh", "python -m evaluation.skill_checks.report runtime/commerce.duckdb /tmp/olist-skills.md",
                   "python -m evaluation.skill_checks.merchant_oracle /path/to/olist-csvs runtime/commerce.duckdb", "```", ""])
    args.output.write_text("\n".join(report), encoding="utf-8")
    print(f"Verified {len(skill_catalog())} skills. Wrote {args.output}.")


if __name__ == "__main__":
    main()
