import duckdb
import pytest
from fastapi.testclient import TestClient

from commerce import data
from commerce.api import make_app
from commerce.settings import database


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    root = tmp_path_factory.mktemp("skills")
    with pytest.MonkeyPatch.context() as env:
        env.setenv("LENS_HOME", str(root))
        env.delenv("LLM_MODEL", raising=False)
        env.delenv("LLM_BASE_URL", raising=False)
        data.demo_data(root / "csv")
        data.build_db(root / "csv", database(), "demo")
        yield TestClient(make_app())


def test_each_skill_is_discoverable_executable_and_traceable(site):
    response = site.get("/api/skills")
    assert response.status_code == 200
    specs = response.json()["skills"]
    assert len({s["id"] for s in specs}) == 9
    for spec in specs:
        assert spec["description"] and spec["scope"] and len(spec["steps"]) >= 2
        body = site.post("/api/query", json={"question": spec["question"], "skill_id": spec["id"]}).json()
        assert body["status"] in {"ok", "insufficient_data"}, (spec["id"], body)
        evidence = body["evidence"]
        assert body["answer"] and body["mode"] == "skill" and body["usage"] is None
        assert evidence["skill_id"] == spec["id"] and evidence["sql"] and evidence["snapshot"]
        with duckdb.connect(str(database()), read_only=True) as con:
            assert data.rows(con, evidence["sql"]) == body["table"]
        assert site.get("/api/runs/" + body["request_id"]).json() == body


def test_skill_question_and_explicit_limits(site):
    spec = next(s for s in site.get("/api/skills").json()["skills"] if s["id"] == "fulfillment")
    ask = lambda **fields: site.post("/api/query", json={"question": spec["question"], **fields})
    run = ask().json()
    assert run["status"] == "ok" and run["evidence"]["skill_id"] == "fulfillment"
    assert any(r["level"] == "Seller" for r in run["table"])
    assert any(r["level"] == "State lane" for r in run["table"])
    assert ask(start="2035-01-01").json()["status"] == "insufficient_data"
    assert ask(skill_id="no-such-skill").status_code == 422
    assert ask(question=spec["question"] + " in New York").json()["status"] == "clarification_required"
    assert ask(question="Rank Peru only", skill_id="fulfillment").json()["status"] == "clarification_required"


def test_offline_aliases_respect_scope(site):
    post = lambda q: site.post("/api/query", json={"question": q, "mode": "demo"}).json()
    response = post("Rank merchants.")
    assert response["status"] == "ok"
    assert response["evidence"]["skill_id"] == "merchant-score"
    assert post("Rank merchants in Peru.")["status"] == "clarification_required"
