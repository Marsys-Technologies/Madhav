"""
tests/test_mr15_av_gate_loud_failure.py — PARIṢKĀRA MR-15.

GAP (MASTER_REMEDIATION_REGISTER MR-15 / PG-22, recon L266): AV
(Ashtakavarga) gating is a flagship gochara_v3 mechanism, but it was
silently degraded during the only production build that has ever run — the
underlying query failure (a nonexistent 'bhava_num' column on
bg_transit_av_gates; see services/gochara_v3/tests/
test_mr15_av_gate_bhava_num_fix.py for the schema-level fix and proof) was
logged at INFO and never surfaced anywhere an operator would see it.

This file covers the OTHER half of the MR-15 remediation: even after the
schema is fixed, ANY future AV-gate fetch failure (transient DB error,
future schema drift, etc.) must be visible in the writer's own build
report (WriterResult.notes), not just a log line. This is the same
Earned-Signal discipline CLAUDE.md §N.8 already states: a status/signal
without a real, visible detector behind it is null, not green — and
"the operator can grep application logs" is not a real detector for a
per-chart build report.

TDD discipline: RED against the pre-fix
ka_gochara_v3_century_materialize.py (which fetches ClassContext but never
inspects av_gate_fetch_error at all); GREEN after the fix folds it into
WriterResult.notes + logs at ERROR.
"""
from __future__ import annotations

import logging

import pytest

import pipeline.orchestrator.writers.ka_gochara_v3_century_materialize as mod
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    ASSET_ID,
    GocharaV3CenturyMaterializeWriter,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TABLE = "kala_gochara_windows_v2"


# ── Fake DB connection (no real DB required) — mirrors
# test_w34_century_horizon.py's fakes so this file is self-contained. ──────


class _FakeCursor:
    def __init__(self, owner: "_FakeConn"):
        self._owner = owner

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        return self._owner.execute(sql, params)

    def fetchall(self):
        return self._owner.rows_for_next

    def fetchone(self):
        rows = self._owner.rows_for_next
        return rows[0] if rows else None


class _FakeConn:
    def __init__(self, responder=None):
        self.responder = responder or (lambda sql, params: [])
        self.statements: list[tuple[str, object]] = []
        self.rows_for_next: list[dict] = []

    def cursor(self):
        return _FakeCursor(self)

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        self.rows_for_next = self.responder(sql, params)
        return _FakeCursor(self)

    def commit(self):  # pragma: no cover
        raise AssertionError("writer called commit() — forbidden by §N.2")

    def rollback(self):  # pragma: no cover
        raise AssertionError("writer called rollback() — forbidden by §N.2")

    def close(self):  # pragma: no cover
        raise AssertionError("writer called close() — forbidden by §N.2")


def _ctx(conn, **extra_config) -> ContextSpec:
    return ContextSpec(
        asset_id=ASSET_ID,
        build_id="test-build-mr15",
        db_conn=conn,
        config={"chart_id": CHART_ID, **extra_config},
    )


_DISCOVERED_CLASSES = [
    "career_advancement", "major_gain", "marriage",
    "illness_acute", "chronic_onset", "surgery",
]


def _responder(*, targets=("Venus",), stored_fp=None, rows_exist=False):
    def responder(sql: str, params=None) -> list[dict]:
        s = sql.lower()
        if "gochara_resonance_map" in s and "distinct" in s and "target_ref" not in s:
            return [{"event_class": ec} for ec in _DISCOVERED_CLASSES]
        if "gochara_resonance_map" in s and "target_ref" in s:
            return [{"target_ref": t} for t in targets]
        if "kala_gochara_v2_build_state" in s and sql.strip().upper().startswith("SELECT"):
            if stored_fp is None:
                return []
            return [{"class_fingerprint": stored_fp}]
        if TABLE in s and "limit 1" in s:
            return [{"1": 1}] if rows_exist else []
        return []
    return responder


class _FakeClassContextWithAVError:
    """Stand-in for a ClassContext whose AV gate fetch failed. Carries only
    the attribute this lane's fix reads (av_gate_fetch_error) — anything
    else find_threshold_crossings would touch is monkeypatched away."""

    def __init__(self, error: str):
        self.av_gate_fetch_error = error
        self.av_gate_rows = ()


def _ensure_fake_swisseph():
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types
        import sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")


def _run_substep_with_av_gate_error(monkeypatch, error_message: str):
    from services.gochara_v3.interval_solver import IntervalBoundary

    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    fake_boundary = IntervalBoundary(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=0.72,
        era_slice_key=era_key,
    )

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
    monkeypatch.setattr(
        mod, "ClassContext",
        type(
            "FakeClassContext", (),
            {"fetch": staticmethod(lambda **k: _FakeClassContextWithAVError(error_message))},
        ),
        raising=False,
    )
    _ensure_fake_swisseph()

    return writer.run_substep(ctx, step)


# ── Tests ───────────────────────────────────────────────────────────────


def test_run_substep_surfaces_av_gate_fetch_error_in_notes(monkeypatch):
    """A degraded AV gate fetch must appear in WriterResult.notes — the
    field the orchestrator's build report is built from — not just a log
    line an operator would never read."""
    error_message = 'av_gate_rows fetch failed: column "bhava_num" does not exist'
    result = _run_substep_with_av_gate_error(monkeypatch, error_message)

    assert result.notes, "WriterResult.notes must not be empty"
    assert error_message in result.notes or "AV" in result.notes.upper(), (
        f"Expected the AV gate fetch failure to be visible in "
        f"WriterResult.notes; got notes={result.notes!r}"
    )


def test_run_substep_logs_av_gate_fetch_error_at_error_level(monkeypatch, caplog):
    """The writer must also log the degraded AV gate fetch at ERROR level
    (build-log visible in normal ERROR/WARNING filtering, not buried at
    DEBUG/INFO)."""
    error_message = 'av_gate_rows fetch failed: column "bhava_num" does not exist'

    with caplog.at_level(logging.DEBUG, logger=mod.__name__):
        _run_substep_with_av_gate_error(monkeypatch, error_message)

    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert error_records, (
        "Expected an ERROR-level log record for the degraded AV gate fetch — "
        f"got levels {[r.levelname for r in caplog.records]}"
    )
    assert any("av" in r.message.lower() for r in error_records), (
        f"ERROR record(s) found but none mention AV gating: "
        f"{[r.message for r in error_records]}"
    )


def test_run_substep_notes_unaffected_when_av_gate_fetch_succeeded(monkeypatch):
    """Sanity/non-regression: when av_gate_fetch_error is None (the normal,
    healthy path), the writer's notes must NOT claim a degradation that
    never happened."""
    from services.gochara_v3.interval_solver import IntervalBoundary

    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    fake_boundary = IntervalBoundary(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=0.72,
        era_slice_key=era_key,
    )

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
    monkeypatch.setattr(
        mod, "ClassContext",
        type(
            "FakeClassContext", (),
            {"fetch": staticmethod(lambda **k: _FakeClassContextWithAVError(None))},
        ),
        raising=False,
    )
    _ensure_fake_swisseph()

    result = writer.run_substep(ctx, step)
    assert "AV_GATE_DEGRADED" not in result.notes
    assert "av_gate" not in result.notes.lower()


def test_run_substep_still_works_when_context_has_no_av_gate_fetch_error_attr(monkeypatch):
    """Backward-compat: existing tests (test_w34_century_horizon.py) stub
    ClassContext.fetch to return a bare object() with NO attributes at all.
    The fix must use getattr(..., default) so it degrades gracefully
    instead of raising AttributeError on that stub."""
    from services.gochara_v3.interval_solver import IntervalBoundary

    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    fake_boundary = IntervalBoundary(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=0.72,
        era_slice_key=era_key,
    )

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    _ensure_fake_swisseph()

    result = writer.run_substep(ctx, step)
    assert result.rows_inserted == 1
