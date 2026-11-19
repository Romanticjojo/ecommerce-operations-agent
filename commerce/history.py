"""Keep bounded local query history apart from the read-only analytical snapshot."""

import json
import sqlite3
from contextlib import contextmanager

from .settings import home


@contextmanager
def connection():
    home().mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(home() / "history.sqlite", timeout=8)
    try:
        db.execute("""CREATE TABLE IF NOT EXISTS runs
            (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, question TEXT NOT NULL,
             mode TEXT NOT NULL, status TEXT NOT NULL, body TEXT NOT NULL)""")
        with db:
            yield db
    finally:
        db.close()


def save(run):
    with connection() as db:
        db.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?)",
            (
                run["request_id"],
                run["created_at"],
                run["question"],
                run["mode"],
                run["status"],
                json.dumps(run, ensure_ascii=False, allow_nan=False),
            ),
        )
        db.execute(
            "DELETE FROM runs WHERE id IN (SELECT id FROM runs ORDER BY created_at DESC LIMIT -1 OFFSET 200)"
        )


def recent():
    with connection() as db:
        db.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in db.execute(
                "SELECT id AS request_id, created_at, question, mode, status FROM runs ORDER BY created_at DESC"
            )
        ]


def lookup(request_id):
    with connection() as db:
        row = db.execute("SELECT body FROM runs WHERE id = ?", (request_id,)).fetchone()
        return json.loads(row[0]) if row else None
