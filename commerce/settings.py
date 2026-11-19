"""All local paths are relative to the checkout unless LENS_HOME is set."""

import os
from contextlib import contextmanager
from uuid import uuid4
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def home() -> Path:
    return Path(os.getenv("LENS_HOME") or ROOT / "runtime").expanduser().resolve()


def database() -> Path:
    return home() / "commerce.duckdb"


def model_status() -> dict:
    model = os.getenv("LLM_MODEL", "").strip()
    configured = bool(model and os.getenv("LLM_BASE_URL", "").strip())
    return {
        "configured": configured,
        "model": model or None,
        "mode": "model" if configured else "demo",
    }


@contextmanager
def pinned_database(target: Path):
    """Hold one immutable snapshot across all connections in a job."""
    pinned = target.with_name(f".request-{uuid4().hex}.duckdb")
    os.link(target, pinned)
    try:
        yield pinned
    finally:
        pinned.unlink(missing_ok=True)
