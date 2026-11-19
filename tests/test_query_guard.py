import hashlib

import duckdb
import pytest

from commerce.query_guard import InvalidSQL, QueryError, Rejected, execute, validate_sql


def test_ut02_allowed_query_and_rejection_preserve_database(tmp_path):
    db = tmp_path / "sample.duckdb"
    sentinel = tmp_path / "marker.csv"
    sentinel.write_text("marker\nprivate-fixture-marker\n")
    with duckdb.connect(str(db)) as con:
        con.execute("CREATE TABLE order_summary AS SELECT 'delivered' AS status, 30 AS item_revenue")
    before = hashlib.sha256(db.read_bytes()).digest()
    blocked = [
        "DROP TABLE order_summary", "UPDATE order_summary SET item_revenue = 0",
        "COPY order_summary TO 'outside.csv'", "ATTACH 'outside.duckdb' AS other",
        f"SELECT marker FROM read_csv('{sentinel}')",
        "SELECT id FROM read_parquet('fixture.parquet')",
        "SELECT id FROM read_csv('https://example.invalid/report.csv')",
        "SELECT table_name FROM information_schema.tables", "SELECT 1; SELECT 2",
        "SELECT a.status FROM order_summary a CROSS JOIN order_summary b",
        "WITH RECURSIVE t AS (SELECT status FROM order_summary) SELECT status FROM t",
        "SELECT status FROM (SELECT status FROM order_summary) AS s",
        "SELECT status FROM (SELECT table_name FROM information_schema.tables) AS nested",
        "SELECT * FROM order_summary", "SELECT status FROM order_summary LIMIT 5000",
    ]
    for sql in blocked:
        with pytest.raises(Rejected) as exc:
            execute(db, sql)
        assert "private-fixture-marker" not in str(exc.value)
    with pytest.raises(InvalidSQL, match="unknown_column"):
        validate_sql("SELECT secret FROM order_summary")
    sql = ("WITH delivered AS (SELECT item_revenue FROM order_summary WHERE status = 'delivered') "
           "SELECT SUM(item_revenue) AS revenue FROM delivered")
    assert execute(db, sql)["rows"] == [{"revenue": 30}]
    assert hashlib.sha256(db.read_bytes()).digest() == before
    assert sentinel.read_text() == "marker\nprivate-fixture-marker\n"


def test_worker_timeout_recovery_and_truncation(tmp_path):
    db = tmp_path / "large.duckdb"
    with duckdb.connect(str(db)) as con:
        con.execute("CREATE TABLE order_summary AS SELECT range AS item_revenue FROM range(1002)")
    sql = "SELECT item_revenue FROM order_summary ORDER BY item_revenue"
    with pytest.raises(QueryError, match="query_timeout"):
        execute(db, sql, timeout=0.001)
    result = execute(db, sql)
    assert result["truncated"] and len(result["rows"]) == 1000
    assert result["rows"][999] == {"item_revenue": 999}
    with duckdb.connect(str(db)) as con:
        assert con.execute("SELECT COUNT(*) FROM order_summary").fetchone() == (1002,)
