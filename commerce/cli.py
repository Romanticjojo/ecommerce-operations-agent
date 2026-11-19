"""Local administration. Run python -m commerce.cli --help."""

import argparse
import json
import tempfile
from pathlib import Path

from .settings import database, home


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Install the reproducible synthetic dataset")
    importer = commands.add_parser("import", help="Install the seven Olist CSV tables")
    importer.add_argument("directory", type=Path)
    evaluation = commands.add_parser(
        "evaluate", help="Run reference, demo or real model evaluations"
    )
    evaluation.add_argument(
        "--mode", choices=["reference", "demo", "model"], default="reference"
    )
    evaluation.add_argument("--limit", type=int)
    evaluation.add_argument(
        "--output", type=Path, help="Optional additional report directory"
    )
    options = parser.parse_args()
    home().mkdir(parents=True, exist_ok=True)
    if options.command == "evaluate":
        from .benchmark import evaluate

        result = evaluate(database(), options.mode, options.limit, options.output)
        print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
        return
    from .data import build_db, demo_data

    if options.command == "demo":
        with tempfile.TemporaryDirectory() as directory:
            demo_data(Path(directory))
            audit = build_db(Path(directory), database(), "demo")
    else:
        audit = build_db(options.directory, database(), "olist")
    print(
        json.dumps(
            {
                "snapshot": audit["snapshot_id"],
                "source": audit["source"],
                "tables": {k: v["rows"] for k, v in audit["files"].items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
