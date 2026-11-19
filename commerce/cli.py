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
    commands.add_parser("olist", help="Download the course dataset from Kaggle (Olist v2) and import it")
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
    elif options.command == "olist":
        try:
            import kagglehub
        except ModuleNotFoundError as exc:
            if exc.name != "kagglehub":
                raise
            parser.exit(2, "Install the dataset tools: python -m pip install -r evaluation/kaggle_olist/requirements.txt\n")
        directory = kagglehub.dataset_download("olistbr/brazilian-ecommerce/versions/2")
        audit = build_db(Path(directory), database(), "olist")
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
