"""W2 — the sidecar route over the serving reader: POST /api/compute/gochara/v5/windows.

The route is exercised over a REAL connection to the A5.3 throwaway database (opened by the route's own `_connect`):

  200 with an envelope for a sealed generation; 200 WITH a refusal for an unsealed / unknown / out-of-horizon /
  inverted-range request (a refusal is an answer, not an error);
  422 for malformed input, before any connection is opened;
  a named 5xx — never an empty envelope — when the database is unreachable, lacks the schema, or the read fails;
  the connection the route opens refuses writes; the key check is fail-closed; `main.py` mounts the route under the
  existing API-key dependency; no registered writer's source closure contains it.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from routers import gochara_v5 as route
from services.gochara_kernel import serving_reader as rd

from .test_a53_inventory import CHART_ID, H0, H1
from .test_a53_p1_support import GEN
from .test_a53_scope_completeness import _complete_world
from .test_a53_window_verification_gate import CLS, _consistent_sky, world  # noqa: F401
from .test_w1_serving_reader import _seal, _sealed

UTC = timezone.utc
SIDECAR = Path(__file__).resolve().parents[3]
URL = "/api/compute/gochara/v5/windows"
KEY = {"x-api-key": "test-key"}
GOOD = {"chart_id": CHART_ID, "generation": GEN, "event_classes": [CLS]}


def _client(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI()
    app.include_router(route.router, prefix="/api/compute")
    monkeypatch.setenv("PYTHON_SIDECAR_API_KEY", "test-key")
    return TestClient(app)


@pytest.fixture()
def client(world, monkeypatch):
    """The route against the throwaway database: `_db_url` (the route's only source of a DSN) points at it."""
    monkeypatch.setattr(route, "_db_url", lambda: world.dsn)
    return _client(monkeypatch)


@pytest.fixture()
def offline(monkeypatch):
    """The route with NO database: any attempt to connect fails the test."""
    def refuse():
        raise AssertionError("the route opened a connection for a request it should have rejected")
    monkeypatch.setattr(route, "_connect", refuse)
    return _client(monkeypatch)


# ── 200: an envelope; a refusal is an answer ─────────────────────────────────────────────────────────────

def test_a_sealed_generation_is_answered_200_with_the_readers_envelope(world, client):
    _sealed(world)
    r = client.post(URL, json=GOOD, headers=KEY)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == rd.read_v5(world.conn, CHART_ID, GEN, event_classes=[CLS], limit=route.DEFAULT_LIMIT)
    assert body["refusal"] is None and len(body["windows"]) == 1 and body["requested"]["limit"] == route.DEFAULT_LIMIT
    assert body["served_horizon"] == {"start": H0.isoformat(), "end": H1.isoformat()}


def test_refusals_are_200_with_the_refusal_set_never_an_error_or_an_empty_list(world, client):
    _complete_world(world)                                         # published, not sealed
    r = client.post(URL, json=GOOD, headers=KEY)
    assert r.status_code == 200 and r.json()["refusal"]["code"] == "not_sealed" and r.json()["windows"] is None
    _seal(world)
    cases = [
        ({**GOOD, "generation": "9.9"}, "unknown_generation"),
        ({**GOOD, "date_from": "1990-01-01T00:00:00Z", "date_to": "1990-06-01T00:00:00Z"}, "outside_served_horizon"),
        ({**GOOD, "at_instant": "2031-01-01T00:00:00+05:30"}, "outside_served_horizon"),
        ({**GOOD, "date_from": "2025-02-01T00:00:00Z", "date_to": "2025-01-01T00:00:00Z"}, "invalid_range"),
    ]
    for payload, code in cases:
        r = client.post(URL, json=payload, headers=KEY)
        assert r.status_code == 200, (payload, r.text)
        assert r.json()["refusal"]["code"] == code and r.json()["windows"] is None
    ok = client.post(URL, json={**GOOD, "date_from": "2025-01-05T00:00:00Z", "limit": 1}, headers=KEY)
    assert ok.status_code == 200 and ok.json()["refusal"] is None and len(ok.json()["windows"]) == 1


def test_the_instant_and_range_parameters_reach_the_reader(world, client):
    _sealed(world)
    r = client.post(URL, json={**GOOD, "at_instant": "2025-01-15T05:30:00+05:30"}, headers=KEY).json()
    assert r["effective_range"] == {"start": datetime(2025, 1, 15, tzinfo=UTC).isoformat(),
                                    "end": datetime(2025, 1, 15, tzinfo=UTC).isoformat(), "kind": "instant"}
    assert len(r["windows"]) == 1
    quiet = client.post(URL, json={"chart_id": CHART_ID, "generation": GEN, "date_from": "2025-01-02T00:00:00Z",
                                   "date_to": "2025-01-08T00:00:00Z"}, headers=KEY).json()
    assert quiet["windows"] == [] and quiet["classes"][0]["zero_window_reading"] == "searched_complete_none"
    assert quiet["classes_source"] == "generation_search_inventory"


# ── 422: malformed input, rejected before any connection ─────────────────────────────────────────────────

@pytest.mark.parametrize("payload", [
    {**GOOD, "chart_id": "not-a-uuid"},
    {"chart_id": CHART_ID},                                                      # no generation
    {**GOOD, "generation": "5.0; DROP"},
    {**GOOD, "event_classes": []},
    {**GOOD, "event_classes": ["Marriage"]},
    {**GOOD, "event_classes": "marriage"},
    {**GOOD, "date_from": "2025-01-01T00:00:00"},                                # an instant without an offset
    {**GOOD, "date_from": "2025-01-01"},
    {**GOOD, "at_instant": "yesterday"},
    {**GOOD, "at_instant": "2025-01-15T00:00:00Z", "date_to": "2025-02-01T00:00:00Z"},
    {**GOOD, "limit": 0},
    {**GOOD, "limit": route.MAX_LIMIT + 1},
    {**GOOD, "limit": "many"},
    {**GOOD, "served_generation": "5.0"},                                        # an unknown field
])
def test_malformed_input_is_422_and_never_reaches_the_database(offline, payload):
    r = offline.post(URL, json=payload, headers=KEY)
    assert r.status_code == 422, (payload, r.status_code, r.text)
    assert "windows" not in r.json()


def test_a_well_formed_request_does_reach_the_connection(offline):
    """The 422 tests above pass for the right reason: a valid body gets as far as `_connect` (here: the 5xx path)."""
    r = offline.post(URL, json=GOOD, headers=KEY)
    assert r.status_code == 503 and r.json()["detail"] == {"error": "gochara_v5_database_unreachable"}


# ── 5xx: a named error, never an empty envelope ──────────────────────────────────────────────────────────

def _assert_named_error(r, status, name):
    assert r.status_code == status, r.text
    body = r.json()
    assert body == {"detail": {"error": name}}
    assert "windows" not in body and "refusal" not in body


def test_an_unreachable_database_is_a_named_503(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(route, "CONNECT_TIMEOUT_S", 1)
    monkeypatch.setattr(route, "_db_url", lambda: "postgresql://nobody@127.0.0.1:1/none")      # nothing listens there
    _assert_named_error(client.post(URL, json=GOOD, headers=KEY), 503, "gochara_v5_database_unreachable")
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.undo()
    client = _client(monkeypatch)
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        monkeypatch.delenv(key, raising=False)
    _assert_named_error(client.post(URL, json=GOOD, headers=KEY), 503, "gochara_v5_database_unreachable")


def test_a_database_without_the_serving_schema_is_a_named_503(world, monkeypatch):
    from psycopg.conninfo import make_conninfo
    monkeypatch.setattr(route, "_db_url", lambda: make_conninfo(world.dsn, dbname="postgres"))
    _assert_named_error(_client(monkeypatch).post(URL, json=GOOD, headers=KEY), 503, "gochara_v5_schema_missing")


def test_a_failed_read_is_a_named_500_and_the_connection_is_rolled_back_and_closed(world, client, monkeypatch):
    _sealed(world)
    opened = []
    real = route._connect

    def tracking():
        conn = real()
        opened.append(conn)
        return conn
    monkeypatch.setattr(route, "_connect", tracking)

    def boom(conn, *a, **kw):
        conn.execute("SELECT 1")                                   # a transaction is open when the reader fails
        raise RuntimeError("reader exploded")
    monkeypatch.setattr(rd, "read_v5", boom)
    _assert_named_error(client.post(URL, json=GOOD, headers=KEY), 500, "gochara_v5_read_failed")
    assert len(opened) == 1 and opened[0].closed

    def lost(conn, *a, **kw):
        import psycopg
        raise psycopg.OperationalError("server closed the connection unexpectedly")
    monkeypatch.setattr(rd, "read_v5", lost)
    _assert_named_error(client.post(URL, json=GOOD, headers=KEY), 503, "gochara_v5_database_unreachable")
    assert len(opened) == 2 and opened[1].closed


# ── read-only, never committed ───────────────────────────────────────────────────────────────────────────

def test_the_routes_connection_refuses_writes_in_and_out_of_a_transaction(world, monkeypatch):
    import psycopg
    monkeypatch.setattr(route, "_db_url", lambda: world.dsn)
    conn = route._connect()
    try:
        assert conn.read_only is True and conn.isolation_level == psycopg.IsolationLevel.REPEATABLE_READ
        assert conn.execute("SHOW transaction_read_only").fetchone()[0] == "on"
        assert conn.execute("SHOW transaction_isolation").fetchone()[0] == "repeatable read"
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("CREATE TABLE public.w2_must_not_exist (x int)")
        conn.rollback()
        conn.autocommit = True                                     # even outside the reader's transaction: the SESSION
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):  # default is read-only (server-enforced)
            conn.execute("CREATE TABLE public.w2_must_not_exist (x int)")
        assert int(conn.execute("SHOW statement_timeout").fetchone()[0].rstrip("ms").rstrip("s") or 0) > 0
    finally:
        route._close(conn)
    assert conn.closed
    assert world.conn.execute("SELECT to_regclass('public.w2_must_not_exist') IS NULL").fetchone()[0]


def test_the_route_never_commits(world, client, monkeypatch):
    _sealed(world)
    calls = []
    real = route._connect

    class Spy:
        def __init__(self, conn):
            self._conn = conn

        def commit(self):
            calls.append("commit")
            return self._conn.commit()

        def rollback(self):
            calls.append("rollback")
            return self._conn.rollback()

        def close(self):
            calls.append("close")
            return self._conn.close()

        def __getattr__(self, name):
            return getattr(self._conn, name)
    monkeypatch.setattr(route, "_connect", lambda: Spy(real()))
    assert client.post(URL, json=GOOD, headers=KEY).status_code == 200
    assert calls == ["rollback", "close"]
    src = Path(route.__file__).read_text(encoding="utf-8")
    assert ".commit(" not in src and not re.search(r"\b(INSERT|UPDATE|DELETE|TRUNCATE)\b", src)


# ── auth and mounting ────────────────────────────────────────────────────────────────────────────────────

def test_the_key_check_is_fail_closed(offline, monkeypatch):
    assert offline.post(URL, json=GOOD).status_code == 401
    assert offline.post(URL, json=GOOD, headers={"x-api-key": "wrong"}).status_code == 401
    monkeypatch.delenv("PYTHON_SIDECAR_API_KEY")
    assert offline.post(URL, json=GOOD, headers={"x-api-key": ""}).status_code == 503       # no key configured: not anonymous


def test_main_mounts_the_route_under_the_existing_api_key_dependency():
    src = (SIDECAR / "main.py").read_text(encoding="utf-8")
    assert "from routers import gochara_v5 as gochara_v5_router" in src
    assert ('app.include_router(gochara_v5_router.router, prefix="/api/compute", '
            'dependencies=[Depends(verify_api_key)])') in src
    paths = [r.path for r in route.router.routes]
    assert paths == ["/gochara/v5/windows"] and list(route.router.routes[0].methods) == ["POST"]


def test_no_registered_writer_closure_and_no_builder_module_includes_the_serving_path():
    """The reader and the route are read-side only: no writer digest or layer pin can move because of them, and the
    kernel's pinned implementation digest does not cover them."""
    from pipeline.orchestrator import asset_runner
    from pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all
    from services.gochara_kernel import implementation_registry

    discover_all()
    assert WRITER_REGISTRY
    for asset_id in sorted(WRITER_REGISTRY):
        paths = [p for p, _ in asset_runner._writer_source_files(asset_runner._writer_source_paths(asset_id))]
        assert not any(p.endswith("serving_reader.py") or p.endswith("routers/gochara_v5.py") for p in paths), asset_id
    for py in list(SIDECAR.glob("services/**/*.py")) + list(SIDECAR.glob("pipeline/**/*.py")):
        if py.name == "serving_reader.py":
            continue
        text = py.read_text(encoding="utf-8")
        assert "serving_reader" not in text and "routers.gochara_v5" not in text \
            and "routers import gochara_v5" not in text, py
    assert implementation_registry.problem() is None               # the lock is unchanged by this path
