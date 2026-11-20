"""HTTP adapter for the local, single-user workbench."""

import json
import time
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Literal
from uuid import uuid4

import duckdb

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import agent, data, history, skills, stats
from .schema import RAW, TRANSLATION, VIEWS
from .settings import ROOT, database, home, model_status, pinned_database


class DateRange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: date | None = None
    end: date | None = None

    @model_validator(mode="after")
    def valid_window(self):
        if self.start and self.end and self.start >= self.end:
            raise ValueError("End date must be later than start date. The end date is exclusive.")
        return self


class Question(DateRange):
    question: str = Field(min_length=1, max_length=1500)
    skill_id: str | None = Field(default=None, max_length=40)
    language: Literal["en", "zh"] = "en"
    mode: Literal["auto", "model", "demo"] = "auto"


    @field_validator("skill_id")
    @classmethod
    def known_skill(cls, value):
        if value is not None and value not in skills.SKILLS:
            raise ValueError("Choose a skill from /api/skills.")
        return value


class Investigation(DateRange):
    grain: Literal["day", "timestamp"] = "timestamp"


@contextmanager
def snapshot():
    try:
        with pinned_database(database()) as db:
            yield db
    except FileNotFoundError:
        raise HTTPException(
            503, detail="Import the Olist dataset before submitting a query."
        )


def envelope(run, question, started):
    run.update(
        request_id=str(uuid4()),
        question=question,
        created_at=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        timing_ms=round((time.monotonic() - started) * 1000, 2),
    )
    encoded = jsonable_encoder(run)
    history.save(encoded)
    return encoded


def make_app():
    app = FastAPI(title="Commerce Lens", version="1.1.0")
    hosts = ["127.0.0.1", "localhost", "[::1]", "testserver"]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    @app.middleware("http")
    async def local_requests(request: Request, call_next):
        origin = request.headers.get("origin")
        if (
            request.method == "POST"
            and origin
            and origin != str(request.base_url).rstrip("/")
        ):
            return JSONResponse(
                {"detail": "Requests must originate from this workbench."}, status_code=403
            )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    def health():
        return {"status": "ok", "data_ready": database().is_file()}

    @app.get("/api/config/status")
    def config():
        return model_status()

    @app.get("/api/skills")
    def skill_catalog():
        return {"skills": skills.catalog()}

    @app.get("/api/catalog")
    def catalog():
        with snapshot() as db:
            c = data.catalog(db)
            tables = list(c["tables"])
            with duckdb.connect(str(db), read_only=True) as conn:
                for view in tables:
                    if view["name"] in VIEWS:
                        view["rows"] = conn.execute(
                            f"SELECT COUNT(*) FROM {view['name']}"
                        ).fetchone()[0]
        for name, info in c["audit"]["files"].items():
            schema = RAW.get(name, TRANSLATION)
            tables.append(
                {
                    "name": name,
                    "rows": info["rows"],
                    "grain": "Source CSV record",
                    "columns": info.get("columns")
                    or [{"name": col, "type": kind} for col, kind in schema.items()],
                }
            )
        return {
            **c,
            "tables": tables,
            "snapshot": c["snapshot_id"],
            "quality": c["audit"]["quality"],
        }

    @app.get("/api/overview")
    def overview():
        with snapshot() as db:
            item = data.overview(db)
        return {
            **item,
            **item["date_range"],
            "snapshot": item["snapshot_id"],
            "monthly": item["monthly_sales"],
            "categories": item["top_categories"],
        }

    @app.post("/api/query")
    def query(q: Question):
        started = time.monotonic()
        with snapshot() as db:
            c = data.catalog(db)
            result = agent.ask(db, **q.model_dump(mode="json"))
            result.setdefault("evidence", {}).update(
                snapshot=c["snapshot_id"], source=c["source"]
            )
        return envelope(result, q.question, started)

    @app.post("/api/investigation")
    def investigate(q: Investigation):
        started = time.monotonic()
        with snapshot() as db:
            result = stats.investigate(db, **q.model_dump(mode="json"))
        groups = [{"group": name, **row} for name, row in result["groups"].items()]
        result.update(
            groups=groups,
            snapshot=result["snapshot_id"],
            mode="statistics",
            evidence={
                "sql": result["sql"],
                "snapshot": result["snapshot_id"],
                "filters": result["filters"],
                "grain": result["grain"],
                "metric_ids": ["negative_rate", "risk_difference"],
            },
        )
        return envelope(result, "Late delivery and negative reviews", started)

    @app.get("/api/runs")
    def runs():
        return {"runs": history.recent()}

    @app.get("/api/runs/{request_id}")
    def run(request_id: str):
        record = history.lookup(request_id)
        if record is None:
            raise HTTPException(404, detail="Analysis run not found.")
        return record

    @app.get("/api/evaluation")
    def evaluation():
        path = home() / "evaluation.json"
        if not path.is_file():
            return {"status": "not_run", "summary": [], "results": []}
        return json.loads(path.read_text())

    front = ROOT / "frontend" / "dist"
    if front.is_dir():
        app.mount("/", StaticFiles(directory=front, html=True), name="workbench")
    return app


app = make_app()
