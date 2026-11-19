"""Private stdin/stdout protocol for a short-lived read-only DuckDB worker."""
import datetime
from decimal import Decimal
import json
import math
import sys

import duckdb


def value(cell):
    if isinstance(cell, datetime.date):
        return cell.isoformat()
    if isinstance(cell, Decimal):
        cell = float(cell)
    if isinstance(cell, float) and not math.isfinite(cell):
        raise ValueError("nonfinite_result")
    return cell


def run(request):
    config = {
        "enable_external_access": "false", "autoinstall_known_extensions": "false",
        "autoload_known_extensions": "false", "threads": "1", "memory_limit": "128MB",
        "max_temp_directory_size": "0B", "lock_configuration": "true",
    }
    with duckdb.connect(request["db"], read_only=True, config=config) as connection:
        max_rows = request["max_rows"]
        cursor = connection.execute(request["sql"])
        columns = [item[0] for item in cursor.description]
        rows = []
        size = 0
        for raw in cursor.fetchall():
            if len(rows) == max_rows:
                return {"rows": rows, "truncated": True}
            row = dict(zip(columns, map(value, raw)))
            size += len(json.dumps(row, ensure_ascii=False))
            if size > 2_000_000:
                raise ValueError("result_size")
            rows.append(row)
    return {"rows": rows, "truncated": False}


if __name__ == "__main__":
    try:
        print(json.dumps(run(json.load(sys.stdin)), allow_nan=False))
    except (duckdb.Error, ValueError, OverflowError):
        print(json.dumps({"error": "query_execution_failed"}))
