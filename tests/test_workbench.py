
import pytest
from fastapi.testclient import TestClient

from commerce import data
from commerce.api import make_app
from commerce.benchmark import evaluate, same_rows
from commerce.settings import database


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("LENS_HOME", str(tmp_path / "running"))
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    csv_dir = tmp_path / "csv"
    data.demo_data(csv_dir)
    data.build_db(csv_dir, database(), "demo")
    return TestClient(make_app())


def test_answer_matches_dashboard_and_persisted_evidence(workspace):
    overview = workspace.get("/api/overview").json()
    assert overview["source"] == "demo"
    res = workspace.post(
        "/api/query",
        json={
            "question": "What is total item revenue?",
            "mode": "demo",
            "language": "en",
        },
    )
    assert res.status_code == 200
    answer = res.json()
    assert answer["status"] == "ok"
    assert answer["table"][0]["item_revenue"] == pytest.approx(overview["item_revenue"])
    assert answer["evidence"]["snapshot"] == overview["snapshot"]
    assert answer["evidence"]["sql"]
    assert workspace.get("/api/runs/" + answer["request_id"]).json() == answer
    assert (
        workspace.get("/api/runs").json()["runs"][0]["request_id"]
        == answer["request_id"]
    )
    catalog = workspace.get("/api/catalog").json()
    assert all(t["rows"] >= 0 and t["columns"] for t in catalog["tables"])
    assert not list(database().parent.glob(".request-*.duckdb"))


def test_research_endpoint_with_filters_and_sample_accounting(workspace):
    res = workspace.post(
        "/api/investigation",
        json={"grain": "day", "start": "2017-01-01", "end": "2019-01-01"},
    )
    assert res.status_code == 200
    body = res.json()
    assert {r["group"] for r in body["groups"]} == {"late", "on_time"}
    assert (
        sum(row["n"] for row in body["groups"]) == body["exclusions"]["included_orders"]
    )
    assert body["evidence"]["sql"]
    assert (
        workspace.post(
            "/api/investigation", json={"start": "2020-01-01", "end": "2019-01-01"}
        ).status_code
        == 422
    )
    assert (
        workspace.get("/api/runs/" + body["request_id"]).json()["mode"] == "statistics"
    )


def test_origin_and_no_data(workspace):
    denied = workspace.post(
        "/api/query",
        json={"question": "x"},
        headers={"origin": "https://elsewhere.example"},
    )
    assert denied.status_code == 403
    database().unlink()
    assert workspace.get("/api/health").json()["data_ready"] is False
    assert workspace.get("/api/overview").status_code == 503
    assert workspace.get("/api/runs/unknown").status_code == 404


def test_benchmark_reference_does_not_claim_model_accuracy(workspace, tmp_path):
    report = evaluate(database(), "reference", output=tmp_path / "exports")
    assert (
        len(report["results"]) == 55
        and report["summary"][0]["reference_sql_count"] == 50
    )
    assert report["summary"][0]["accuracy"] is None
    assert workspace.get("/api/evaluation").json()["snapshot"] == report["snapshot"]
    assert (tmp_path / "exports" / "results.csv").is_file()
    assert same_rows([(1,), (1,), (2,)], [[2], [1], [1]], False, 1e-5)
    assert not same_rows([(1,), (1,), (2,)], [[2], [2], [1]], False, 1e-5)
