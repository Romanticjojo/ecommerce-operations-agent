"""Opt-in real-data acceptance run. See README.md for the exact commands."""

import hashlib
import inspect
import json
import platform
import socket
import threading
import time
from contextlib import ExitStack
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import httpx
import pytest
import uvicorn

from oracle import Reference

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
HANDLE = "olistbr/brazilian-ecommerce"


def pytest_addoption(parser):
    parser.addoption(
        "--olist-trace",
        action="store_true",
        help="Print download, import, HTTP and comparison evidence (use with -s)",
    )
    parser.addoption(
        "--olist-version", default=None, help="Kaggle version number; default: latest"
    )
    parser.addoption(
        "--olist-output",
        default="runtime/kaggle-acceptance",
        help="Generated report directory",
    )


def pytest_configure(config):
    config.olist_results = {}
    config.olist_metadata = {}


@pytest.fixture(scope="session")
def trace(request):
    def emit(message):
        if request.config.getoption("--olist-trace"):
            print(message, flush=True)

    return emit


@pytest.fixture(scope="session")
def site(request, tmp_path_factory, trace):
    import kagglehub
    from commerce.api import make_app
    from commerce.data import build_db

    version_id = request.config.getoption("--olist-version")
    if version_id is not None and not str(version_id).isdigit():
        raise ValueError("--olist-version requires a numeric version")
    handle = f"{HANDLE}/versions/{version_id}" if version_id else HANDLE
    # The no-version invocation is the latest-version API requested for this project.
    trace(f"KaggleHub dataset: {handle}")
    folder = Path(kagglehub.dataset_download(handle))
    trace(
        f"CSV files available: {len(list(folder.glob('*.csv')))}. Computing independent CSV reference ..."
    )
    ref = Reference(folder)
    directory = tmp_path_factory.mktemp("kaggle-olist")
    db = directory / "commerce.duckdb"
    audit = build_db(folder, db, "olist")
    trace(
        f"DuckDB ready: {len(audit['files'])} input tables, {audit['files']['orders']['rows']:,} orders."
    )
    requested_version = folder.name if folder.parent.name == "versions" else version_id
    request.config.olist_metadata.update(
        {
            "dataset": HANDLE,
            "request": handle,
            "resolved_version": requested_version,
            "source_url": f"https://www.kaggle.com/datasets/{HANDLE}",
            "data_license": "CC BY-NC-SA 4.0",
            "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "platform": f"{platform.system()} {platform.release()} / {platform.machine()}",
            "python": platform.python_version(),
            "packages": {
                name: version(name)
                for name in (
                    "kagglehub",
                    "kagglesdk",
                    "duckdb",
                    "scipy",
                    "pytest",
                    "fastapi",
                    "uvicorn",
                )
            },
            "snapshot": audit["snapshot_id"],
            "files": ref.files,
            "app_sha256": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((ROOT / "commerce").glob("*.py"))
            },
            "suite_sha256": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(PACK.glob("*.py"))
            },
        }
    )
    with ExitStack() as stack:
        env = stack.enter_context(pytest.MonkeyPatch.context())
        env.setenv("LENS_HOME", str(directory))
        sock = stack.enter_context(socket.socket())
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(
            uvicorn.Config(make_app(), log_level="error", access_log=False)
        )
        thread = threading.Thread(
            target=server.run, kwargs={"sockets": [sock]}, daemon=True
        )
        thread.start()

        def stop():
            server.should_exit = True
            thread.join(timeout=10)

        stack.callback(stop)
        client = stack.enter_context(
            httpx.Client(
                base_url=f"http://127.0.0.1:{port}", timeout=20, trust_env=False
            )
        )
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        assert client.get("/api/health").json()["data_ready"]
        trace("Local HTTP server ready. Dataset snapshot: " + audit["snapshot_id"][:16])
        yield client, ref, db, audit["snapshot_id"]


class Probe:
    def __init__(self, site, record, trace):
        self.trace = trace
        self.client, self.ref, self.db, self.snapshot = site
        self.record = record

    def api(self, method, path, body=None, code=200):
        response = (
            self.client.request(method, path, json=body)
            if body is not None
            else self.client.request(method, path)
        )
        info = response.json()
        event = {
            "method": method,
            "path": path,
            "input": body,
            "http_status": response.status_code,
        }
        evidence = info.get("evidence") or {}
        if evidence.get("sql"):
            event["executed_sql"] = evidence["sql"]
        self.record["requests"].append(event)
        self.trace(
            f"{method} {path}  {json.dumps(body, ensure_ascii=False)}  ->  HTTP {response.status_code}"
        )
        assert response.status_code == code
        return info

    def ask(self, text, **filters):
        return self.api(
            "POST",
            "/api/query",
            {"question": text, "mode": "demo", "language": "en", **filters},
        )

    def check(self, label, expected, actual):
        self.record["checks"].append(
            {"label": label, "expected": expected, "actual": actual}
        )
        self.trace(f"{label}\n  Expected: {expected}\n  Observed: {actual}")
        assert actual == expected, label


@pytest.fixture
def probe(site, request, trace):
    return Probe(site, request.config.olist_results[request.node.nodeid], trace)


def pytest_collection_modifyitems(config, items):
    for item in items:
        if Path(item.path).resolve() != PACK / "cases.py":
            continue
        lines = inspect.getdoc(item.obj).splitlines()
        config.olist_results[item.nodeid] = dict(
            id=item.name.split("_")[1].upper(),
            title=lines[0],
            procedure=" ".join(lines[1:]),
            status="NOT RUN",
            requests=[],
            checks=[],
            duration_ms=0,
        )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = (yield).get_result()
    row = item.config.olist_results.get(item.nodeid)
    if row is None:
        return
    row["duration_ms"] += (
        round(result.duration * 1000, 2) if result.when == "call" else 0
    )
    if result.failed or result.skipped:
        row["status"] = "FAIL" if result.failed else "SKIP"
        row["reason"] = (
            str(call.excinfo.value)[:600] if call.excinfo else str(result.outcome)
        )
    elif result.when == "call":
        row["status"] = "PASS"


def pytest_sessionfinish(session, exitstatus):
    cases = list(session.config.olist_results.values())
    if not cases:
        return
    from reporting import write_reports

    write_reports(
        Path(session.config.getoption("--olist-output")),
        session.config.olist_metadata,
        cases,
        int(exitstatus),
    )
