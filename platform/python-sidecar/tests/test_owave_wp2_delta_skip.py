"""O-wave WP-2 (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.2) -- delta-skip.

Verifies the pre-execution gate in _run_data_writer: when
previous_receipt_matches_inputs says every input digest already matches the
last complete receipt, the writer is never invoked and the skip is recorded
via _skip_no_delta (asset_throughput -> 'lit', build_run_assets.disposition
= 'skip_no_delta', output_changed = FALSE). Also verifies the gate's
fail-open/opt-out edges: force=True, a missing declared_deps/has_cowriters
(legacy caller), and an exception raised by the matcher itself.

All fakes -- no live DB. Writer is NOT @register-decorated (would pollute the
global registry and break test_has_writer_completeness).
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar
from pipeline.orchestrator import output_digest as output_digest_module
from pipeline.orchestrator import provenance as provenance_module
from pipeline.orchestrator.writers import WriterBase, WriterResult


class FakeCursor:
    def __init__(self):
        self.executed: list[tuple[str, object]] = []
        self.rowcount = 1
        self._next_fetch = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        s = " ".join(sql.split())
        self._next_fetch = None
        if "SELECT integrity_check_sql FROM asset_registry" in s:
            self._next_fetch = {"integrity_check_sql": None}
        elif "SELECT target_floor FROM asset_registry" in s:
            self._next_fetch = {"target_floor": None}

    def fetchone(self):
        return self._next_fetch

    def fetchall(self):
        return []

    def params_for(self, keyword: str) -> list[tuple]:
        return [p for s, p in self.executed if keyword in s]

    def sql_ran(self, keyword: str) -> bool:
        return any(keyword in s for s, _ in self.executed)


class FakeConn:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class _CountingWriter(WriterBase):
    asset_id = "_test_owave_wp2"
    invocations = 0

    def run(self, ctx):
        type(self).invocations += 1
        return WriterResult(asset_id=self.asset_id, rows_inserted=3, rows_updated=0)


def _base_monkeypatches(monkeypatch, *, matches: bool | Exception):
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)
    monkeypatch.setattr(ar, "discover_all", lambda: None)
    monkeypatch.setattr(ar, "get_writer", lambda aid: _CountingWriter)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, cid: {"chart_id": cid})
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda cur, aid, cid, *a: "hash-upstream")
    monkeypatch.setattr(ar, "get_writer_source_hash", lambda aid: "hash-writer")
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [])
    monkeypatch.setattr(
        output_digest_module, "compute_output_digest",
        lambda cur, *, asset_id: ("output-a", "b" * 64),
    )
    monkeypatch.setattr(
        provenance_module, "previous_output_digest",
        lambda cur, *, asset_id, chart_id, partition_key: None,
    )
    monkeypatch.setattr(provenance_module, "capture_and_persist_receipt", lambda cur, **kw: ("fresh", []))

    calls: list[dict] = []

    def _fake_matches(cur, **kwargs):
        calls.append(kwargs)
        if isinstance(matches, Exception):
            raise matches
        return matches

    monkeypatch.setattr(provenance_module, "previous_receipt_matches_inputs", _fake_matches)
    return calls


def _run(monkeypatch, *, matches: bool | Exception, declared_deps=(), has_cowriters=False, force=False):
    calls = _base_monkeypatches(monkeypatch, matches=matches)
    _CountingWriter.invocations = 0
    conn = FakeConn()
    cur = FakeCursor()
    ok = ar._run_data_writer(
        conn, cur, "run-1", "chart-abc", _CountingWriter.asset_id,
        declared_deps=list(declared_deps) if declared_deps is not None else None,
        has_cowriters=has_cowriters, force=force,
    )
    return ok, cur, conn, calls


# ── _skip_no_delta (direct) ────────────────────────────────────────────────

def test_skip_no_delta_restores_lit_and_records_disposition(monkeypatch):
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)
    conn = FakeConn()
    cur = FakeCursor()

    result = ar._skip_no_delta(conn, cur, "run-1", "chart-abc", "_test_owave_wp2")

    assert result is True
    throughput_calls = cur.params_for("SET state = 'lit'")
    assert len(throughput_calls) == 1
    assert throughput_calls[0] == ("chart-abc", "_test_owave_wp2")
    disposition_calls = cur.params_for("disposition = 'skip_no_delta'")
    assert len(disposition_calls) == 1
    assert disposition_calls[0] == ("run-1", "_test_owave_wp2")
    assert conn.commits >= 1


# ── Gate integration inside _run_data_writer ───────────────────────────────

def test_matching_receipt_skips_the_writer_entirely(monkeypatch):
    ok, cur, conn, calls = _run(monkeypatch, matches=True)
    assert ok is True
    assert _CountingWriter.invocations == 0
    assert cur.sql_ran("disposition = 'skip_no_delta'")
    assert not cur.sql_ran("disposition = 'build'")
    assert len(calls) == 1


def test_non_matching_receipt_executes_the_writer_normally(monkeypatch):
    ok, cur, conn, calls = _run(monkeypatch, matches=False)
    assert ok is True
    assert _CountingWriter.invocations == 1
    assert cur.sql_ran("disposition = 'build'")
    assert not cur.sql_ran("disposition = 'skip_no_delta'")


def test_force_bypasses_the_gate_even_when_the_receipt_matches(monkeypatch):
    ok, cur, conn, calls = _run(monkeypatch, matches=True, force=True)
    assert ok is True
    assert _CountingWriter.invocations == 1
    assert cur.sql_ran("disposition = 'build'")
    # The matcher must not even be consulted once force=True short-circuits it.
    assert calls == []


def test_legacy_caller_with_no_declared_deps_never_gates(monkeypatch):
    """declared_deps=None (a direct-call fixture, not the production scheduler
    path) skips the gate exactly like it already skips receipt capture."""
    ok, cur, conn, calls = _run(monkeypatch, matches=True, declared_deps=None)
    assert ok is True
    assert _CountingWriter.invocations == 1
    assert calls == []


def test_legacy_caller_with_no_has_cowriters_never_gates(monkeypatch):
    ok, cur, conn, calls = _run(monkeypatch, matches=True, has_cowriters=None)
    assert ok is True
    assert _CountingWriter.invocations == 1
    assert calls == []


def test_matcher_exception_fails_open_into_normal_execution(monkeypatch):
    """A broken delta-skip DECISION must never become a failed or silently
    skipped BUILD -- plan §3.2 point 4."""
    ok, cur, conn, calls = _run(monkeypatch, matches=RuntimeError("boom"))
    assert ok is True
    assert _CountingWriter.invocations == 1
    assert cur.sql_ran("disposition = 'build'")
    assert not cur.sql_ran("disposition = 'skip_no_delta'")


# ── force threading through run_asset ──────────────────────────────────────

def test_run_asset_threads_force_into_the_main_data_path(monkeypatch):
    monkeypatch.setattr(ar, "deps_unsatisfied", lambda *a, **k: [])
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)

    captured: list[dict] = []

    def _fake_run_data_writer(conn, cur, run_id, chart_id, asset_id, declared_deps=None,
                               natural_key_partition=None, has_cowriters=None, force=False):
        captured.append({"force": force})
        return True

    monkeypatch.setattr(ar, "_run_data_writer", _fake_run_data_writer)
    monkeypatch.setattr(ar, "_DEP_ASSERT_MODE", "off")

    cur = FakeCursor()
    conn = FakeConn()
    ar.run_asset(conn, cur, "run-1", "chart-abc", "_test_owave_wp2", 0,
                 declared_deps=[], has_cowriters=False, force=True)

    assert captured == [{"force": True}]


def test_run_asset_defaults_force_to_false(monkeypatch):
    monkeypatch.setattr(ar, "deps_unsatisfied", lambda *a, **k: [])
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)

    captured: list[dict] = []

    def _fake_run_data_writer(conn, cur, run_id, chart_id, asset_id, declared_deps=None,
                               natural_key_partition=None, has_cowriters=None, force=False):
        captured.append({"force": force})
        return True

    monkeypatch.setattr(ar, "_run_data_writer", _fake_run_data_writer)
    monkeypatch.setattr(ar, "_DEP_ASSERT_MODE", "off")

    cur = FakeCursor()
    conn = FakeConn()
    ar.run_asset(conn, cur, "run-1", "chart-abc", "_test_owave_wp2", 0,
                 declared_deps=[], has_cowriters=False)

    assert captured == [{"force": False}]
