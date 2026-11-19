import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import duckdb
import pytest

from commerce import model
from commerce.agent import ask


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "fixture.duckdb"
    with duckdb.connect(str(path)) as con:
        con.execute("""CREATE TABLE order_summary AS SELECT * FROM (VALUES
            ('a', 'delivered', TIMESTAMP '2018-01-01', 30, 33, 'SP'),
            ('b', 'delivered', TIMESTAMP '2018-02-01', 40, 45, 'RJ'),
            ('c', 'delivered', TIMESTAMP '2017-12-31', 70, 71, 'SP'),
            ('d', 'canceled', TIMESTAMP '2018-01-02', 999, 999, 'SP')
            ) o(order_id,status,purchased_at,item_revenue,payment_total,state)""")
        con.execute("""CREATE VIEW category_sales AS SELECT order_id, purchased_at, item_revenue,
            CASE WHEN order_id='a' THEN 'art' ELSE 'books' END AS category FROM order_summary
            WHERE status='delivered'""")
        con.execute("""CREATE TABLE order_review_delivery AS SELECT order_id, purchased_at,
            CASE WHEN order_id='a' THEN 1 ELSE 4 END AS review_score,
            order_id='a' AS late_timestamp, FALSE AS late_day FROM order_summary WHERE status='delivered'""")
    return path


@pytest.fixture
def provider(monkeypatch):
    history, queue = [], []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            history.append((self.path, body, self.headers["Authorization"]))
            status, message, usage = queue.pop(0)
            content = message if isinstance(message, str) else json.dumps(message)
            response = {"choices": [{"message": {"content": content}}]}
            if usage:
                response["usage"] = usage
            self.send_response(status)
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

    # The local mock does not need reverse DNS for its HTTP server name.
    monkeypatch.setattr(socket, "getfqdn", lambda name: "localhost")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    monkeypatch.setenv("LLM_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setenv("LLM_MODEL", "test-provider")
    monkeypatch.setenv("LLM_API_KEY", "unit-test-placeholder")
    yield queue, history
    server.shutdown()
    server.server_close()
    thread.join()


def test_demo_sales_period_and_unknown(db):
    out = ask(db, "Show the top 10 product categories by item revenue in 2018.", mode="demo")
    assert out["status"] == "ok" and out["usage"] is None
    assert out["table"] == [{"category": "books", "item_revenue": 40}, {"category": "art", "item_revenue": 30}]
    assert out["chart"] == {"type": "bar", "x": "category", "y": "item_revenue"}
    assert out["evidence"]["filters"] == {"status": "delivered", "start": "2018-01-01", "end": "2019-01-01"}
    with duckdb.connect(str(db), read_only=True) as con:
        assert con.execute(out["evidence"]["sql"]).fetchall() == [("books", 40), ("art", 30)]
    scoped = ask(db, "按月统计商品成交额", mode="demo", start="2018-02-01", end="2018-03-01")
    assert scoped["table"] == [{"month": "2018-02-01", "item_revenue": 40}]
    assert ask(db, "What is average order value in 2018?", mode="demo")["table"] == [{"aov": 35}]
    assert ask(db, "Show monthly delivered orders in 2030.", mode="demo")["status"] == "insufficient_data"
    assert ask(db, "What is total item revenue for sellers in Peru?", mode="demo")["status"] == "clarification_required"


def test_model_plan_transport_evidence_and_baseline(db, provider, monkeypatch):
    queue, history = provider
    usage = {"prompt_tokens": 16, "completion_tokens": 4, "total_tokens": 20}
    monkeypatch.setenv("LLM_INPUT_USD_PER_MILLION", "2")
    monkeypatch.setenv("LLM_OUTPUT_USD_PER_MILLION", "4")
    queue.append((200, {"intent": "reviews", "metric": "negative_rate", "year": 2018}, usage))
    out = ask(db, "What share of eligible orders scored 1 or 2 in 2018?", language="en")
    assert out["mode"] == "model" and out["status"] == "ok" and out["table"] == [{"negative_rate": 0.5}]
    assert out["usage"] == usage and out["estimated_cost_usd"] == pytest.approx(0.000048)
    path, body, auth = history[0]
    assert path == "/v1/chat/completions" and body["model"] == "test-provider"
    assert auth == "Bearer unit-test-placeholder"
    assert str(db) not in json.dumps(body) and "unit-test-placeholder" not in json.dumps(out)
    queue.append((200, {"intent": "sql", "sql": "SELECT COUNT(*) AS n FROM order_summary"}, None))
    baseline = ask(db, "Count all orders", variant="direct")
    assert baseline["table"] == [{"n": 4}] and baseline["usage"] is None
    assert baseline["evidence"]["prompt_version"] != out["evidence"]["prompt_version"]


def test_model_rejection_errors_and_repair_budget(db, provider):
    queue, history = provider
    queue.append((200, {"intent": "sql", "sql": "DELETE FROM order_summary"}, None))
    rejected = ask(db, "Count orders", variant="direct")
    assert rejected["status"] == "rejected"
    assert rejected["evidence"]["generated_sql"] and not rejected["evidence"]["sql_success"]
    for status, content, code in [(401, "private error", "model_authentication"), (429, "", "model_rate_limited"),
                                  (503, "", "model_service_error"), (200, "invalid text", "model_invalid_response")]:
        queue.append((status, content, None))
        out = ask(db, "Count orders")
        assert out["status"] == "error" and out["evidence"]["error_code"] == code
        assert "private error" not in json.dumps(out)
    for _ in range(2):
        queue.append((200, {"intent": "unknown", "metric": "guessed"}, None))
    out = ask(db, "Count orders")
    assert out["status"] == "error" and out["evidence"]["repairs"] == 1 and len(history) == 7
    queue.append((200, {"intent": "sales", "metric": "order_count"}, None))
    assert ask(db, "Count delivered orders")["table"] == [{"order_count": 3}]


def test_provider_timeout_classification(monkeypatch):
    import httpx

    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:1/v1")
    monkeypatch.setenv("LLM_MODEL", "fixture")
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout("private provider diagnostic")
    monkeypatch.setattr(httpx, "stream", timeout)
    with pytest.raises(model.ModelError, match="model_timeout"):
        model.complete("count orders", "full", None, None)
