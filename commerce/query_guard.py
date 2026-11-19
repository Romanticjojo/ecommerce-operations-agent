"""Validate a deliberately small DuckDB reporting dialect before running it in isolation."""
import json
import re
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import sqlglot
from sqlglot import exp


VIEWS = {
    "order_summary": {"order_id", "status", "purchased_at", "item_revenue", "payment_total", "state"},
    "category_sales": {"order_id", "purchased_at", "category", "item_revenue"},
    "monthly_sales": {"month", "order_count", "item_revenue", "aov"},
    "order_review_delivery": {"order_id", "purchased_at", "review_score", "late_timestamp", "late_day"},
}
MAX_ROWS = 1000


class QueryError(Exception):
    """Public error codes contain no database, credentials or provider details."""


class Rejected(QueryError):
    pass


class InvalidSQL(QueryError):
    pass


_ALLOWED = {
    exp.Select, exp.From, exp.Table, exp.Column, exp.Identifier, exp.Alias,
    exp.Literal, exp.Null, exp.Boolean, exp.Cast, exp.DataType, exp.Where,
    exp.And, exp.Or, exp.Not, exp.Is, exp.EQ, exp.NEQ, exp.GT, exp.GTE,
    exp.LT, exp.LTE, exp.Between, exp.In, exp.Paren, exp.Group, exp.Order,
    exp.Ordered, exp.Limit, exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max,
    exp.Round, exp.Distinct, exp.Nullif, exp.Coalesce, exp.Add, exp.Sub,
    exp.Mul, exp.Div, exp.Neg, exp.TimestampTrunc, exp.Var, exp.Star,
    exp.Case, exp.If, exp.With, exp.CTE, exp.TableAlias, exp.Having,
}


def _scope(select, sources):
    source = select.args.get("from_")
    table = source.this if source else None
    if type(table) is not exp.Table or type(table.this) is not exp.Identifier:
        raise Rejected("view_required")
    if table.db or table.catalog or table.name.lower() not in sources:
        raise Rejected("view_denied")
    names = sources[table.name.lower()]
    alias = table.alias_or_name.lower()
    outputs = {item.alias.lower() for item in select.expressions if item.alias}
    for column in select.find_all(exp.Column):
        if column.find_ancestor(exp.Select) is not select:
            continue
        if column.args.get("db") or column.args.get("catalog") or (column.table and column.table.lower() != alias):
            raise Rejected("column_denied")
        name = column.name.lower()
        if name not in names and not (
            name in outputs and column.find_ancestor(exp.Order, exp.Group, exp.Having)
        ):
            raise InvalidSQL("unknown_column")
    return {item.alias_or_name.lower() for item in select.expressions if item.alias_or_name}


def validate_sql(sql):
    if not isinstance(sql, str) or not 1 <= len(sql) <= 6000:
        raise Rejected("sql_size")
    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except (sqlglot.errors.SqlglotError, ValueError, RecursionError):
        raise InvalidSQL("invalid_sql") from None
    if len(statements) != 1 or type(statements[0]) is not exp.Select:
        raise Rejected("select_required")
    tree = statements[0]
    for i, node in enumerate(tree.walk()):
        if i >= 256 or type(node) not in _ALLOWED:
            raise Rejected("unsupported_expression")
        if isinstance(node, exp.Identifier) and not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]{0,62}", node.name):
            raise Rejected("identifier_denied")
        if isinstance(node, exp.Star) and type(node.parent) is not exp.Count:
            raise Rejected("explicit_columns_required")
        if isinstance(node, exp.Var) and (
            type(node.parent) is not exp.TimestampTrunc or node.name.upper() not in {"DAY", "MONTH", "YEAR"}
        ):
            raise Rejected("unit_denied")
        if isinstance(node, exp.DataType) and (node.expressions or node.this.value not in {"DATE", "TIMESTAMP", "DOUBLE", "INT", "BIGINT"}):
            raise Rejected("cast_denied")
        if isinstance(node, exp.Literal) and len(node.name) > 180:
            raise Rejected("literal_size")
        if isinstance(node, exp.Limit) and (
            not isinstance(node.expression, exp.Literal) or not node.expression.is_int
            or not 1 <= int(node.expression.this) <= MAX_ROWS
        ):
            raise Rejected("limit_denied")
        if isinstance(node, exp.TableAlias) and node.args.get("columns"):
            raise Rejected("column_alias_list_denied")
        if isinstance(node, exp.Select):
            if len(node.expressions) > 16 or node.args.get("kind") or node.args.get("operation_modifiers"):
                raise Rejected("select_shape")
    selects = list(tree.find_all(exp.Select))
    sources = dict(VIEWS)
    with_clause = tree.args.get("with_")
    if with_clause:
        if with_clause.args.get("recursive") or len(with_clause.expressions) != 1 or len(selects) != 2:
            raise Rejected("cte_denied")
        cte = with_clause.expressions[0]
        if type(cte.this) is not exp.Select or cte.alias.lower() in sources:
            raise Rejected("cte_denied")
        sources[cte.alias.lower()] = _scope(cte.this, sources)
    elif len(selects) != 1:
        raise Rejected("subquery_denied")
    _scope(tree, sources)
    # Execute the normalized syntax we inspected. Strip comments when rendering.
    return tree.sql(dialect="duckdb", comments=False)


def execute(db: Path, sql: str, *, timeout=15):
    started = perf_counter()
    validated = validate_sql(sql)
    executed_sql = f"SELECT * FROM ({validated}) AS result LIMIT {MAX_ROWS + 1}"
    try:
        worker = subprocess.run(
            [sys.executable, "-I", str(Path(__file__).with_name("query_worker.py"))],
            input=json.dumps({"db": str(db), "sql": executed_sql, "max_rows": MAX_ROWS}),
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        # subprocess.run kills and waits for the child before raising.
        raise QueryError("query_timeout") from None
    if worker.returncode:
        raise QueryError("query_execution_failed")
    result = json.loads(worker.stdout)
    if result.get("error"):
        raise QueryError(result["error"])
    return dict(result, sql=executed_sql, sql_ms=round((perf_counter() - started) * 1000, 2))
