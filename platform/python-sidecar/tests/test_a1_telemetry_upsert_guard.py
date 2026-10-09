"""Suvarna E3.2 review fixes 2 + 3 — ga_writers/_telemetry.py upsert guard.

Fix 2: the ON CONFLICT DO UPDATE must not overwrite an already-stored
       duration_seconds / rows_per_second with NULL when the caller (every current
       caller) passes no duration. COALESCE(EXCLUDED.x, asset_throughput.x).
Fix 3: the upsert must not name duration_seconds / rows_per_second when the columns
       are absent (sidecar deployed before migration 1200) — gated on the SAME
       probe the orchestrator uses (asset_runner._duration_columns_present), never a
       divergent copy.

Two layers: (a) fake-connection tests that always run and pin the SQL shape and the
probe gating in both branches; (b) a live-Postgres behavioural test (skipped unless
TELEMETRY_TEST_DATABASE_URL names a disposable database called `telemetry_upsert_test`;
deliberately NOT DATABASE_URL, which may point at a real database).
"""
from __future__ import annotations

import os
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import _telemetry  # noqa: E402
from pipeline.orchestrator import asset_runner as ar  # noqa: E402
from pipeline.orchestrator import writer_runtime_support as wrs  # noqa: E402


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _ProbeCursor(_Ctx):
    def __init__(self, present: bool):
        self.present = present
        self.probes: list[str] = []

    def execute(self, sql, params=None):
        self.probes.append(sql)

    def fetchone(self):
        return {"?column?": 1} if self.present else None


class _FakeConn:
    def __init__(self, columns_present: bool):
        self.cursor_obj = _ProbeCursor(columns_present)
        self.upserts: list[tuple[str, list]] = []

    def transaction(self):
        return _Ctx()

    def cursor(self):
        return self.cursor_obj

    def execute(self, sql, params):
        self.upserts.append((sql, params))


@pytest.fixture(autouse=True)
def _reset_probe_cache(monkeypatch):
    monkeypatch.setattr(wrs, "_DURATION_COLUMNS_PRESENT", None)


def test_upsert_preserves_stored_duration_and_rate_via_coalesce():
    conn = _FakeConn(columns_present=True)
    _telemetry.update_asset_throughput(conn, "ga_x", "chart-1", "build-1", 10)
    sql, _ = conn.upserts[0]
    assert "COALESCE(EXCLUDED.duration_seconds, asset_throughput.duration_seconds)" in sql
    assert "COALESCE(EXCLUDED.rows_per_second, asset_throughput.rows_per_second)" in sql


def test_columns_present_names_duration_and_rate_and_passes_seven_params():
    conn = _FakeConn(columns_present=True)
    _telemetry.update_asset_throughput(
        conn, "ga_x", "chart-1", "build-1", 40, duration_seconds=8.0,
    )
    sql, params = conn.upserts[0]
    assert "duration_seconds" in sql and "rows_per_second" in sql
    assert params[-2:] == [8.0, 5.0]
    assert len(params) == 7


def test_columns_absent_omits_duration_and_rate_entirely():
    conn = _FakeConn(columns_present=False)
    _telemetry.update_asset_throughput(
        conn, "ga_x", "chart-1", "build-1", 40, duration_seconds=8.0,
    )
    assert len(conn.upserts) == 1, "the upsert itself must still be issued"
    sql, params = conn.upserts[0]
    assert "duration_seconds" not in sql
    assert "rows_per_second" not in sql
    assert len(params) == 5
    assert params[:4] == ["chart-1", "ga_x", "lit", 40]


def test_probe_is_the_orchestrators_own_cached_helper():
    """Same helper, same process cache: one information_schema probe across a
    telemetry write AND the orchestrator's own probe, never a divergent second one."""
    conn = _FakeConn(columns_present=True)
    _telemetry.update_asset_throughput(conn, "ga_x", "chart-1", "build-1", 1)
    _telemetry.update_asset_throughput(conn, "ga_y", "chart-1", "build-1", 1)
    assert ar._duration_columns_present(conn.cursor_obj) is True
    probes = [s for s in conn.cursor_obj.probes if "information_schema" in s]
    assert len(probes) == 1
    assert wrs._DURATION_COLUMNS_PRESENT is True


# ── live Postgres ────────────────────────────────────────────────────────────────

_DB_URL = os.environ.get("TELEMETRY_TEST_DATABASE_URL")


@pytest.mark.skipif(not _DB_URL, reason="needs TELEMETRY_TEST_DATABASE_URL (disposable db)")
class TestLivePostgres:
    @pytest.fixture()
    def conn(self):
        import psycopg

        assert "telemetry_upsert_test" in _DB_URL, (
            "TELEMETRY_TEST_DATABASE_URL must name the disposable `telemetry_upsert_test` db"
        )
        c = psycopg.connect(_DB_URL, autocommit=True)
        c.execute("DROP TABLE IF EXISTS asset_throughput")
        yield c
        c.execute("DROP TABLE IF EXISTS asset_throughput")
        c.close()

    @staticmethod
    def _create(conn, with_duration: bool):
        extra = ", duration_seconds double precision, rows_per_second double precision" if with_duration else ""
        conn.execute(
            f"""CREATE TABLE asset_throughput (
                  chart_id uuid, asset_id text NOT NULL, state text, rows_written int,
                  last_measured_build_id uuid, last_built_at timestamptz,
                  last_measured_at timestamptz{extra});
                CREATE UNIQUE INDEX ON asset_throughput (chart_id, asset_id) WHERE chart_id IS NOT NULL"""
        )

    CHART = "00000000-0000-4000-8000-0000000000c1"
    BUILD = "00000000-0000-4000-8000-0000000000d1"

    def test_stored_duration_and_rate_survive_a_null_telemetry_upsert(self, conn):
        self._create(conn, with_duration=True)
        conn.execute(
            "INSERT INTO asset_throughput (chart_id, asset_id, state, rows_written, duration_seconds, rows_per_second)"
            " VALUES (%s, 'ga_x', 'lit', 5, 12.5, 0.4)", [self.CHART],
        )
        _telemetry.update_asset_throughput(conn, "ga_x", self.CHART, self.BUILD, 99, state="lit")
        row = conn.execute(
            "SELECT rows_written, duration_seconds, rows_per_second FROM asset_throughput WHERE asset_id='ga_x'"
        ).fetchone()
        assert row == (99, 12.5, 0.4)

    def test_a_real_duration_still_overwrites(self, conn):
        self._create(conn, with_duration=True)
        _telemetry.update_asset_throughput(conn, "ga_x", self.CHART, self.BUILD, 10, duration_seconds=2.0)
        _telemetry.update_asset_throughput(conn, "ga_x", self.CHART, self.BUILD, 30, duration_seconds=3.0)
        row = conn.execute(
            "SELECT duration_seconds, rows_per_second FROM asset_throughput WHERE asset_id='ga_x'"
        ).fetchone()
        assert row == (3.0, 10.0)

    def test_pre_migration_schema_upsert_still_lands(self, conn):
        self._create(conn, with_duration=False)
        _telemetry.update_asset_throughput(conn, "ga_x", self.CHART, self.BUILD, 7, duration_seconds=1.0)
        row = conn.execute("SELECT state, rows_written FROM asset_throughput WHERE asset_id='ga_x'").fetchone()
        assert row == ("lit", 7)
