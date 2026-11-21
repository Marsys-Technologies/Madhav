"""NIR-03 & NIR-08: durable phase telemetry, clock_timestamp(), and migration 1420 tests."""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar  # noqa: E402
from pipeline.orchestrator import events as ev  # noqa: E402
from pipeline.orchestrator import writer_runtime_support as wrs  # noqa: E402
from pipeline.orchestrator.writers import ContextSpec, SubStep, WriterBase, WriterResult  # noqa: E402


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
MIGRATION_1420 = REPO_ROOT / "platform/supabase/migrations/1420_nirmana_phase_telemetry_and_tajaka_window.sql"
ASSET_SEED = REPO_ROOT / "platform/scripts/seed/asset_registry_seed.ts"


class _FakeTelemetryCursor:
    def __init__(self, log: list[tuple[str, tuple | None]]):
        self._log = log

    def execute(self, sql: str, params=None):
        self._log.append((sql, params))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeTelemetryConn:
    def __init__(self):
        self.executed: list[tuple[str, tuple | None]] = []
        self.closed = False

    def cursor(self):
        return _FakeTelemetryCursor(self.executed)

    def close(self):
        self.closed = True


class _PhaseCursor:
    def __init__(self, *, columns_present: bool = True, integrity_sql: str | None = None, target_floor: int = 1):
        self.executed: list[tuple[str, tuple | None]] = []
        self._columns_present = columns_present
        self._integrity_sql = integrity_sql
        self._target_floor = target_floor

    def execute(self, sql: str, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        if not self.executed:
            return None
        sql = self.executed[-1][0]
        if "information_schema.columns" in sql:
            if "duration_seconds" in sql:
                return {"cnt": 2}
            return {"cnt": 8 if self._columns_present else 0}
        if "SELECT integrity_check_sql FROM asset_registry" in sql:
            return {"integrity_check_sql": self._integrity_sql} if self._integrity_sql else {}
        if "SELECT target_floor FROM asset_registry" in sql:
            return {"target_floor": self._target_floor}
        return None

    def fetchall(self):
        return []


class _PhaseConn:
    def __init__(self, cursor: _PhaseCursor | None = None):
        self.cur = cursor or _PhaseCursor()
        self.commits = 0
        self.rollbacks = 0
        self.ops: list[str] = []

    def cursor(self):
        return self.cur

    def commit(self):
        self.commits += 1
        self.ops.append("commit")

    def rollback(self):
        self.rollbacks += 1
        self.ops.append("rollback")


@pytest.fixture(autouse=True)
def _reset_phase_column_cache(monkeypatch):
    monkeypatch.setattr(wrs, "_PHASE_TELEMETRY_COLUMNS_PRESENT", None)
    monkeypatch.setattr(wrs, "_DURATION_COLUMNS_PRESENT", None)
    yield
    monkeypatch.setattr(wrs, "_PHASE_TELEMETRY_COLUMNS_PRESENT", None)
    monkeypatch.setattr(wrs, "_DURATION_COLUMNS_PRESENT", None)


def test_migration_1420_schema_and_ga_tajaka_seed_parity():
    sql = MIGRATION_1420.read_text()
    assert sql.startswith("-- Migration 1420:")
    assert "SET LOCAL lock_timeout = '5s';" in sql
    for col in (
        "phase text",
        "substep_index integer",
        "substep_total integer",
        "substep_label text",
        "compute_ms integer",
        "write_ms integer",
        "verify_ms integer",
        "publish_ms integer",
    ):
        assert col in sql
    assert "build_run_assets_phase_check" in sql
    assert "asset_id = 'ga_tajaka'" in sql
    assert "SET target_floor = NULL" in sql

    seed_text = ASSET_SEED.read_text()
    m_seed = re.search(
        r"asset_id:\s*'ga_tajaka'.*?volume_explanation:\s*'([^']+)'",
        seed_text,
        re.DOTALL,
    )
    assert m_seed is not None
    m_mig = re.search(
        r"c_target_expl\s+CONSTANT\s+text\s*:=\s*\n\s*'([^']+)';",
        sql,
        re.DOTALL,
    )
    assert m_mig is not None
    assert m_mig.group(1) == m_seed.group(1)


def test_asset_runner_uses_clock_timestamp_for_all_sql_timestamps():
    src = pathlib.Path(ar.__file__).read_text()
    # Strip comments so explanatory comments mentioning NOW() don't trigger.
    non_comment_lines = [
        line for line in src.splitlines() if not line.lstrip().startswith("#")
    ]
    code_only = "\n".join(non_comment_lines)
    assert "NOW()" not in code_only
    assert "clock_timestamp()" in code_only


def test_phase_telemetry_column_presence_probe_handles_pre_1420_and_test_doubles():
    class _MinimalCursor:
        def execute(self, sql, params=None):
            pass

    # Minimal test-double cursor without fetchone must NOT poison the cache.
    assert wrs._phase_telemetry_columns_present(_MinimalCursor()) is False
    assert wrs._PHASE_TELEMETRY_COLUMNS_PRESENT is None

    # Pre-1420 DB returns 0 matching columns -> False and cached.
    pre_cur = _PhaseCursor(columns_present=False)
    assert wrs._phase_telemetry_columns_present(pre_cur) is False
    assert wrs._PHASE_TELEMETRY_COLUMNS_PRESENT is False

    # Reset and verify 1420 DB returns True and cached.
    wrs._PHASE_TELEMETRY_COLUMNS_PRESENT = None
    cur_1420 = _PhaseCursor(columns_present=True)
    assert wrs._phase_telemetry_columns_present(cur_1420) is True
    assert wrs._PHASE_TELEMETRY_COLUMNS_PRESENT is True


def test_run_data_writer_persists_phases_substeps_and_ms_durations(monkeypatch):
    events: list[dict] = []
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: events.append(e))
    monkeypatch.setattr(ar, "discover_all", lambda: None)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, cid: {"chart_id": cid})
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [])
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda *a, **k: "upstream-h")
    monkeypatch.setattr(ar, "get_writer_source_hash", lambda aid: "writer-h")

    class _HeavyWriter(WriterBase):
        asset_id = "_test_heavy_phase"
        has_substeps = True

        def plan_substeps(self, ctx: ContextSpec):
            return [SubStep(key="s1", label="Step One"), SubStep(key="s2", label="Step Two")]

        def run_substep(self, ctx: ContextSpec, step: SubStep):
            return WriterResult(asset_id=self.asset_id, rows_inserted=5, rows_updated=0)

    monkeypatch.setattr(ar, "get_writer", lambda aid: _HeavyWriter)

    ticks = iter([1.0, 1.05, 1.05, 1.05, 1.15, 1.15, 1.35, 1.35, 1.40, 1.40, 1.42])
    monkeypatch.setattr(ar.time, "monotonic", lambda: next(ticks))

    cur = _PhaseCursor(columns_present=True)
    conn = _PhaseConn(cur)
    assert ar._run_data_writer(conn, cur, "run-1", "chart-1", "_test_heavy_phase") is True

    phase_events = [e for e in events if e.get("type") == "asset.phase"]
    assert [e["phase"] for e in phase_events] == ["writing", "verifying", "publishing", "complete"]
    assert phase_events[0]["substep_index"] == 1
    assert phase_events[0]["substep_total"] == 2
    assert phase_events[0]["substep_label"] == "Step One"
    assert phase_events[-1]["compute_ms"] == 50
    assert phase_events[-1]["write_ms"] == 300
    assert phase_events[-1]["verify_ms"] == 50
    assert phase_events[-1]["publish_ms"] == 20

    live_updates = [
        (sql, params)
        for sql, params in cur.executed
        if "UPDATE build_run_assets" in sql and "phase = %s" in sql
    ]
    assert [(params[0], params[1], params[2], params[3]) for _, params in live_updates] == [
        ("writing", 1, 2, "Step One"),
        ("writing", 2, 2, "Step Two"),
        ("verifying", None, None, None),
        ("publishing", None, None, None),
    ]
    final_updates = [
        (sql, params)
        for sql, params in cur.executed
        if "phase = 'complete'" in sql
    ]
    assert len(final_updates) == 1
    assert final_updates[0][1][:4] == (50, 300, 50, 20)


def test_defer_writer_commits_uses_out_of_band_telemetry_and_preserves_rollback(monkeypatch):
    events: list[dict] = []
    tconn = _FakeTelemetryConn()
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: events.append(e))
    monkeypatch.setattr(ar, "discover_all", lambda: None)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, cid: {"chart_id": cid})
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [])
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda *a, **k: "upstream-h")
    monkeypatch.setattr(ar, "get_writer_source_hash", lambda aid: "writer-h")
    monkeypatch.setattr(ar, "_open_telemetry_conn", lambda conn: tconn)
    monkeypatch.setattr(ar, "_probe_asset", lambda *a, **k: (False, "integrity failed"))

    class _LightWriter(WriterBase):
        asset_id = "_test_light_defer"
        has_substeps = False

        def run(self, ctx: ContextSpec):
            ctx.db_conn.ops.append("writer_insert")
            return WriterResult(asset_id=self.asset_id, rows_inserted=10)

    monkeypatch.setattr(ar, "get_writer", lambda aid: _LightWriter)

    cur = _PhaseCursor(columns_present=True, integrity_sql="SELECT false")
    conn = _PhaseConn(cur)
    assert ar._run_data_writer(conn, cur, "run-1", "chart-1", "_test_light_defer") is False

    # Out-of-band telemetry connection recorded writing + verifying without committing main_conn.
    assert tconn.closed is True
    assert [params[0] for _, params in tconn.executed] == ["writing", "verifying"]

    # Main connection rolled back the uncommitted writer writes BEFORE committing the error row!
    assert conn.ops == ["writer_insert", "rollback", "commit"]
    error_updates = [
        (sql, params)
        for sql, params in cur.executed
        if "UPDATE build_run_assets" in sql and "phase = 'error'" in sql
    ]
    assert len(error_updates) == 1
    assert "post-write integrity check failed: integrity failed" in error_updates[0][1][0]
    assert [e["phase"] for e in events if e.get("type") == "asset.phase"] == ["writing", "verifying", "error"]


def test_pre_1420_schema_graceful_fallback(monkeypatch):
    events: list[dict] = []
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: events.append(e))
    monkeypatch.setattr(ar, "discover_all", lambda: None)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, cid: {"chart_id": cid})
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [])
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda *a, **k: "upstream-h")
    monkeypatch.setattr(ar, "get_writer_source_hash", lambda aid: "writer-h")

    class _SimpleWriter(WriterBase):
        asset_id = "_test_pre_1420"
        has_substeps = False

        def run(self, ctx: ContextSpec):
            return WriterResult(asset_id=self.asset_id, rows_inserted=3)

    monkeypatch.setattr(ar, "get_writer", lambda aid: _SimpleWriter)

    cur = _PhaseCursor(columns_present=False)
    conn = _PhaseConn(cur)
    assert ar._run_data_writer(conn, cur, "run-1", "chart-1", "_test_pre_1420") is True

    for sql, _ in cur.executed:
        if "information_schema.columns" in sql:
            continue
        assert "compute_ms" not in sql
        assert "phase =" not in sql

    # SSE phase events still emit even on pre-1420 DB schemas.
    assert [e["phase"] for e in events if e.get("type") == "asset.phase"] == [
        "writing", "verifying", "publishing", "complete"
    ]


def test_service_health_probe_and_skip_paths_emit_and_persist_phases(monkeypatch):
    events: list[dict] = []
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: events.append(e))

    import pipeline.orchestrator.service_probes as sp
    monkeypatch.setattr(sp, "run_health_probe", lambda aid, cfg: {"status": "GREEN", "message": "ok"})
    monkeypatch.setattr(sp, "probe_output_fingerprint", lambda *a, **k: "fp-1")
    monkeypatch.setattr(ar, "_persist_probe_receipt", lambda *a, **k: True)

    cur = _PhaseCursor(columns_present=True)
    conn = _PhaseConn(cur)
    ar._run_service_health_probe(conn, cur, "run-1", None, "bg_panchanga", {"probe_type": "panchanga_engine"})

    assert [e["phase"] for e in events if e.get("type") == "asset.phase"] == [
        "verifying", "publishing", "complete"
    ]
    assert any("phase = 'complete'" in sql for sql, _ in cur.executed)

    # _skip_no_delta persists and emits phase='skipped'
    events.clear()
    cur2 = _PhaseCursor(columns_present=True)
    conn2 = _PhaseConn(cur2)
    wrs._PHASE_TELEMETRY_COLUMNS_PRESENT = None
    assert ar._skip_no_delta(conn2, cur2, "run-2", "chart-1", "ga_positions", compute_ms=17) is True
    assert any("phase = 'skipped'" in sql for sql, _ in cur2.executed)
    assert events[0] == ev.build_phase_event(
        chart_id="chart-1", asset_id="ga_positions", run_id="run-2", phase="skipped", compute_ms=17
    )
