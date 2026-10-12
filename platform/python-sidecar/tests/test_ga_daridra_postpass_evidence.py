"""ga_vichara Option A (SS N-545): the daridra post-pass leaves ONE durable evidence record per (chart, ayanamsha, build).

Contract: the frozen `post_pass_evidence/1` (N431/post_pass_evidence_record_v1.md). When daridra does not form the post-pass writes no chart_facts row,
so an empty slice is indistinguishable from "the post-pass never ran"; the census may only call the slice empty-by-conditional when the run itself
recorded "evaluated N entries, found nothing". These tests pin: ONE record per ayanamsha on BOTH branches; no chart_facts write when not formed;
no record on dry run / the substep's early returns / any raise; a failed evidence write FAILS the substep (never passes quietly); the record's exact keys.
Pure unit tests, no database (W1-W8 of the design, section 4.1).
"""
from __future__ import annotations

import ast
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import ga_writers.ga_daridra_postpass as pp
import ga_writers.ga_vichara_writer as gw
from test_ga8_writer import AY_ID, BUILD_ID, CHART_ID, MOCK_CHART_OUTPUT
from test_ga_daridra_postpass import CHART as DARIDRA_CHART, DARIDRA_ENTRY, SIDECAR, _RecConn
from test_lane3_deliverable_c_dosha_cancellation import _dosha_entry

AYA = "lahiri_chitrapaksha"
PAYLOAD_KEYS = {"schema", "post_pass", "ayanamsha_id", "slice", "entries_evaluated", "formed", "rows_written", "prior_rows_deleted"}


def _evidence(conn):
    return [(s, p) for s, p in conn.executed if s.startswith("INSERT INTO orchestrator_event_register")]


def _setup(monkeypatch, catalog, chart):
    monkeypatch.setattr(pp._gsw, "_load_dosha_catalog", lambda conn: catalog)
    monkeypatch.setattr(pp._gsw, "compute_chart", lambda inputs, ayanamsha_id: chart)
    monkeypatch.setattr(pp._gsw, "_validate_chart_output_complete", lambda c: None)
    monkeypatch.setattr(pp, "authorize_chart_fact_delete", lambda *a, **k: None)


def _emit(conn):
    return pp.emit_daridra_label_post_pass(conn, CHART_ID, BUILD_ID, AYA, birth_params={"x": 1})


# W1: daridra does NOT form -> exactly one record; the only chart_facts statement is the subject-scoped DELETE
def test_w1_not_formed_writes_one_record_and_nothing_to_chart_facts(monkeypatch):
    _setup(monkeypatch, [DARIDRA_ENTRY], MOCK_CHART_OUTPUT)
    conn = _RecConn()
    assert _emit(conn) == 0
    (sql, params), = _evidence(conn)
    event_type, chart_id, asset_id, run_id, rows_present, substeps_remaining, emitted_by, payload = params
    assert (event_type, chart_id, asset_id, run_id, rows_present, substeps_remaining) == (
        "writer.post_pass_evaluated", CHART_ID, "ga_vichara", BUILD_ID, 0, None)
    p = json.loads(payload)
    assert set(p) == PAYLOAD_KEYS
    assert p == {"schema": "post_pass_evidence/1", "post_pass": "daridra_dosha_label", "ayanamsha_id": AYA,
                 "slice": {"table": "chart_facts", "fact_category": "dosha_label", "fact_subject": "daridra"},
                 "entries_evaluated": 1, "formed": False, "rows_written": 0, "prior_rows_deleted": 1}
    cf = [s for s, _ in conn.executed if "chart_facts" in s]
    assert len(cf) == 1 and cf[0].startswith("DELETE FROM chart_facts") and "fact_subject = %s" in cf[0]
    assert not any(s.startswith("INSERT INTO chart_facts") for s, _ in conn.executed)


# W2: daridra forms -> the row insert, THEN one record saying formed with rows_written 1
def test_w2_formed_writes_the_row_then_one_record(monkeypatch):
    _setup(monkeypatch, [DARIDRA_ENTRY], DARIDRA_CHART)
    conn = _RecConn()
    assert _emit(conn) == 1
    sqls = [s for s, _ in conn.executed]
    assert sum(s.startswith("INSERT INTO chart_facts") for s in sqls) == 1
    (sql, params), = _evidence(conn)
    p = json.loads(params[-1])
    assert p["formed"] is True and p["rows_written"] == 1 and p["entries_evaluated"] == 1 and params[4] == 1
    first_insert = next(i for i, s in enumerate(sqls) if s.startswith("INSERT INTO chart_facts"))
    ev = next(i for i, s in enumerate(sqls) if s.startswith("INSERT INTO orchestrator_event_register"))
    assert first_insert < ev


# W3: an empty / unreadable catalog raises BEFORE any delete or evidence
def test_w3_empty_catalog_raises_with_no_delete_and_no_evidence(monkeypatch):
    _setup(monkeypatch, [], DARIDRA_CHART)
    conn = _RecConn()
    with pytest.raises(RuntimeError, match="brahma_dosha_catalog"):
        _emit(conn)
    assert not _evidence(conn)
    assert not any(s.startswith("DELETE FROM chart_facts") for s, _ in conn.executed)


# W4: a READABLE catalog without a daridra entry -> evidence with entries_evaluated = 0 (the census refuses it)
def test_w4_catalog_without_daridra_records_zero_entries_evaluated(monkeypatch):
    _setup(monkeypatch, [_dosha_entry("kemadruma", "no planet beside the moon")], MOCK_CHART_OUTPUT)
    conn = _RecConn()
    assert _emit(conn) == 0
    (sql, params), = _evidence(conn)
    p = json.loads(params[-1])
    assert p["entries_evaluated"] == 0 and p["formed"] is False and p["rows_written"] == 0


# W5: the three early returns of the substep never reach the post-pass, so no record can exist for them
def test_w5_early_returns_emit_no_evidence(monkeypatch):
    calls = []
    monkeypatch.setattr(pp, "emit_daridra_label_post_pass", lambda *a, **k: calls.append(1) or 0)
    from test_ga_vichara_identity_and_asof import FakeConn
    conn = FakeConn()
    assert gw.build_ga_vichara_substep(CHART_ID, BUILD_ID, AYA, conn, dry_run=True) == 0
    monkeypatch.setattr(gw, "_load_chart_facts", lambda *a, **k: [])
    assert gw.build_ga_vichara_substep(CHART_ID, BUILD_ID, AYA, conn) == 0
    monkeypatch.setattr(gw, "_load_chart_facts", lambda *a, **k: [{"x": 1}])
    monkeypatch.setattr(gw, "_load_constants", lambda *a, **k: [])
    assert gw.build_ga_vichara_substep(CHART_ID, BUILD_ID, AYA, conn) == 0
    assert calls == []
    assert not [s for s in getattr(conn, "executed", []) if "orchestrator_event_register" in str(s)]


# W6: a failing evidence write FAILS the substep (loud), after a savepoint rollback; nothing is committed here
def test_w6_a_failed_evidence_write_raises(monkeypatch):
    _setup(monkeypatch, [DARIDRA_ENTRY], MOCK_CHART_OUTPUT)

    class _Failing(_RecConn):
        def execute(self, sql, params=None):
            s = " ".join(sql.split())
            if s.startswith("INSERT INTO orchestrator_event_register"):
                self.executed.append((s, params))
                raise RuntimeError('permission denied for table orchestrator_event_register')
            return super().execute(sql, params)
    conn = _Failing()
    with pytest.raises(RuntimeError, match="evidence record could NOT be written"):
        _emit(conn)
    sqls = [s for s, _ in conn.executed]
    assert "ROLLBACK TO SAVEPOINT post_pass_evidence" in sqls and "RELEASE SAVEPOINT post_pass_evidence" in sqls
    assert not any(s.upper().startswith(("COMMIT", "ROLLBACK;")) for s in sqls)


def test_w6b_no_savepoint_means_a_loud_failure_too(monkeypatch):
    _setup(monkeypatch, [DARIDRA_ENTRY], MOCK_CHART_OUTPUT)

    class _NoSavepoint(_RecConn):
        def execute(self, sql, params=None):
            if "SAVEPOINT post_pass_evidence" in sql and sql.startswith("SAVEPOINT"):
                raise RuntimeError("no transaction")
            return super().execute(sql, params)
    with pytest.raises(RuntimeError, match="evidence savepoint"):
        _emit(_NoSavepoint())


# W7: structure: both branches of emit record evidence AFTER the delete and BEFORE returning; the substep calls the post-pass unguarded after its insert
def test_w7_structure_both_branches_record_after_delete():
    mod = ast.parse((SIDECAR / "ga_writers/ga_daridra_postpass.py").read_text())
    emit = next(n for n in mod.body if isinstance(n, ast.FunctionDef) and n.name == "emit_daridra_label_post_pass")
    calls = [(n.lineno, ast.unparse(n.func)) for n in ast.walk(emit) if isinstance(n, ast.Call)]
    delete_line = min(l for l, f in calls if f == "replace_prior_daridra_label_rows")
    rec_lines = sorted(l for l, f in calls if f == "record_post_pass_evidence")
    assert len(rec_lines) == 2 and all(l > delete_line for l in rec_lines)
    returns = sorted(n.lineno for n in ast.walk(emit) if isinstance(n, ast.Return))
    assert all(any(r > rl for r in returns) for rl in rec_lines)           # a return follows each record (nothing returns before it)
    ends = sorted(n.end_lineno for n in ast.walk(emit) if isinstance(n, ast.Call) and ast.unparse(n.func) == "record_post_pass_evidence")
    for end in ends:                                                       # the return follows the record directly: nothing else runs in between
        assert min(r for r in returns if r > end) - end <= 1
    body = (SIDECAR / "ga_writers/ga_vichara_writer.py").read_text()
    sub = body[body.index("def build_ga_vichara_substep"):]
    call = sub.index("emit_daridra_label_post_pass(")
    guard = sub[sub.rindex("\n", 0, call - 200): call]
    assert "if inserted" not in guard and "if rows" not in guard and "if all_rows" not in guard


# W8: the record is EXACTLY the frozen shape and the writer touches only the declared tables + the register
def test_w8_payload_shape_and_footprint():
    p = pp.post_pass_evidence_payload(AYA, entries_evaluated=1, formed=False, rows_written=0, prior_rows_deleted=0)
    assert set(p) == PAYLOAD_KEYS and p["slice"] == {"table": "chart_facts", "fact_category": "dosha_label", "fact_subject": "daridra"}
    for bad in (dict(entries_evaluated=-1), dict(entries_evaluated=True), dict(rows_written=1.5), dict(prior_rows_deleted=-1), dict(formed=1)):
        kw = dict(entries_evaluated=1, formed=False, rows_written=0, prior_rows_deleted=0)
        kw.update(bad)
        with pytest.raises(ValueError):
            pp.post_pass_evidence_payload(AYA, **kw)
    with pytest.raises(ValueError):
        pp.record_post_pass_evidence(_RecConn(), CHART_ID, BUILD_ID, AYA, entries_evaluated=1, formed=True, rows_written=0, prior_rows_deleted=0)
    with pytest.raises(ValueError):
        pp.record_post_pass_evidence(_RecConn(), CHART_ID, BUILD_ID, AYA, entries_evaluated=1, formed=False, rows_written=1, prior_rows_deleted=0)
    tree = ast.parse((SIDECAR / "ga_writers/ga_daridra_postpass.py").read_text())
    strings = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert not any("asset_throughput" in s for s in strings)                      # no build-state write (the orchestrator is the sole writer, N.2)
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not (calls & {"commit", "close", "rollback"})                          # never commits, closes or rolls back the orchestrator's connection


def test_event_register_insert_columns_match_the_orchestrator_register():
    """The evidence INSERT uses the register's own eight columns: a drift of `events._INSERT_SQL` (or of this text) turns this red."""
    from pipeline.orchestrator import events
    cols = lambda s: [c.strip() for c in s.split("(", 1)[1].split(")", 1)[0].split(",")]      # noqa: E731
    assert cols(" ".join(pp._EVIDENCE_INSERT_SQL.split())) == cols(" ".join(events._INSERT_SQL.split()))


# ── the designed channel (persist_event) behind the same seam; the default stays closure-free until the owner approves the ONE allowlist line ──

def test_channel_and_allowlist_cannot_drift_apart():
    """Flipping EVIDENCE_CHANNEL to the designed channel without the allowlist line would make every substep fail loudly in production: this test refuses that state."""
    from pipeline.orchestrator import events
    assert pp.EVIDENCE_CHANNEL in ("direct_insert", "persist_event")
    if pp.EVIDENCE_CHANNEL == "persist_event":
        assert pp.POST_PASS_EVENT_TYPE in events.DEFAULT_DURABLE_EVENT_TYPES


def test_designed_channel_writes_through_persist_event_when_allowlisted(monkeypatch):
    _setup(monkeypatch, [DARIDRA_ENTRY], MOCK_CHART_OUTPUT)
    monkeypatch.setattr(pp, "EVIDENCE_CHANNEL", "persist_event")
    monkeypatch.setenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", pp.POST_PASS_EVENT_TYPE)
    conn = _RecConn()
    assert _emit(conn) == 0
    (sql, params), = _evidence(conn)
    event_type, chart_id, asset_id, run_id, rows_present, substeps_remaining, emitted_by, stored = params
    assert (event_type, chart_id, asset_id, run_id, rows_present) == ("writer.post_pass_evaluated", CHART_ID, "ga_vichara", BUILD_ID, 0)
    stored = json.loads(stored)
    assert PAYLOAD_KEYS <= set(stored)                                  # the stored payload is the whole event: the frozen keys + type/chart_id/asset_id/run_id/rows_present
    assert stored["formed"] is False and stored["entries_evaluated"] == 1 and stored["ayanamsha_id"] == AYA
    assert not any(s.startswith("INSERT INTO chart_facts") for s, _ in conn.executed)


def test_designed_channel_without_the_allowlist_line_fails_the_substep_loudly(monkeypatch):
    _setup(monkeypatch, [DARIDRA_ENTRY], MOCK_CHART_OUTPUT)
    monkeypatch.setattr(pp, "EVIDENCE_CHANNEL", "persist_event")
    monkeypatch.delenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", raising=False)
    with pytest.raises(RuntimeError, match="persist_event returned False"):
        _emit(_RecConn())


def test_designed_channel_a_failing_insert_fails_the_substep(monkeypatch):
    _setup(monkeypatch, [DARIDRA_ENTRY], MOCK_CHART_OUTPUT)
    monkeypatch.setattr(pp, "EVIDENCE_CHANNEL", "persist_event")
    monkeypatch.setenv("ORCHESTRATOR_DURABLE_EVENT_TYPES", pp.POST_PASS_EVENT_TYPE)

    class _Conn(_RecConn):
        def cursor(self, row_factory=None):
            cur = super().cursor(row_factory)
            real = cur.execute

            def execute(sql, params=None):
                if " ".join(sql.split()).startswith("INSERT INTO orchestrator_event_register"):
                    raise RuntimeError("permission denied for table orchestrator_event_register")
                return real(sql, params)
            cur.execute = execute
            return cur
    with pytest.raises(RuntimeError, match="persist_event returned False"):
        _emit(_Conn())


def test_unknown_channel_is_refused(monkeypatch):
    _setup(monkeypatch, [DARIDRA_ENTRY], MOCK_CHART_OUTPUT)
    monkeypatch.setattr(pp, "EVIDENCE_CHANNEL", "somewhere_else")
    with pytest.raises(RuntimeError, match="unknown EVIDENCE_CHANNEL"):
        _emit(_RecConn())
