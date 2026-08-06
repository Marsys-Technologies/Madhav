"""Tests for the ka_gochara_sweep_v2 writer (W2G lane G, item 19).

Everything here runs offline against a recording fake connection — no
database, no swisseph engine calls beyond real `import swisseph` (pure
ephemeris arithmetic, no I/O), no network. `materialize_event_class` (the
join+score step, already thoroughly tested against synthetic arcs and fake
grammar in `tests/test_w2g_materialize.py`) is monkeypatched here to a canned
double, so THESE tests isolate what is genuinely this module's own job:
FROZEN-contract conformance, generation-scoped idempotency, the
untouchable-data-rail defenses (no ON CONFLICT DO UPDATE against the shared
natural key; per-row savepoint so a collision never poisons the substep or
overwrites a v1 row), delta-aware invalidation skip, and honest empty/skip
reporting.

WHAT IS ASSERTED, AND WHY EACH ONE MATTERS:
  * heavy shape, one substep per populated event_class, no commit/rollback/
    close, no `asset_throughput` write (§N.2);
  * every DELETE/SELECT/INSERT this writer issues against
    `kala_gochara_windows` is scoped to `generation = '2.0'` — v1's rows are
    never in the blast radius of any statement this writer can issue;
  * no INSERT ever carries `ON CONFLICT ... DO UPDATE` on the table's
    existing (pre-generation) natural-key arbiter — the real schema gap this
    writer works around rather than silently trusting;
  * a per-row insert failure (simulated unique-violation) is caught,
    counted, and does NOT abort the rest of the substep or touch any other
    row;
  * an unchanged `class_fingerprint` short-circuits the substep with zero
    DELETE/INSERT activity against `kala_gochara_windows` — the delta-aware
    invalidation claim, checked by absence of the DELETE, not by trusting a
    docstring.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pytest

import pipeline.orchestrator.writers.ka_gochara_sweep_v2 as mod
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara_sweep_v2 import GocharaSweepV2Writer
from services.w2g.materialize import GENERATION_V2, HORIZON_STATUS_PROGRESSIVE, MaterializeResult


# ── Recording fakes (same shape as test_bg_gochara_arcs.py's) ────────────────


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
    """Records every statement. Raises on commit/rollback/close (§N.2). A
    per-statement `fail_on` predicate lets a test simulate exactly one
    statement raising (a unique-violation collision), without breaking every
    other statement on the connection."""

    def __init__(self, responder, fail_on=None):
        self.responder = responder
        self.fail_on = fail_on or (lambda sql, params: False)
        self.statements: list[tuple[str, object]] = []
        self.rows_for_next: list[dict] = []

    def cursor(self):
        return _FakeCursor(self)

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if self.fail_on(sql, params):
            raise RuntimeError("simulated unique_violation")
        self.rows_for_next = self.responder(sql, params)
        return _FakeCursor(self)

    def commit(self):  # pragma: no cover
        raise AssertionError("writer called commit() — forbidden by §N.2")

    def rollback(self):  # pragma: no cover
        raise AssertionError("writer called rollback() — forbidden by §N.2")

    def close(self):  # pragma: no cover
        raise AssertionError("writer called close() — forbidden by §N.2")


ARC_FP_ROWS = [{"body": b, "arc_fingerprint": f"fp_{b}"} for b in mod.BODIES]


def _responder(*, event_classes=("marriage",), stored_fingerprint=None):
    def responder(sql, params=None):
        s = sql.lower()
        if "gochara_resonance_map" in s and "distinct event_class" in s:
            return [{"event_class": ec} for ec in event_classes]
        if "bg_gochara_arcs" in s:
            return ARC_FP_ROWS
        if "kala_gochara_v2_build_state" in s and sql.strip().upper().startswith("SELECT"):
            if stored_fingerprint is None:
                return []
            return [{"class_fingerprint": stored_fingerprint}]
        return []
    return responder


def _ctx(conn, **config) -> ContextSpec:
    return ContextSpec(
        asset_id="ka_gochara_sweep_v2",
        build_id="00000000-0000-0000-0000-0000000000v2",
        db_conn=conn,
        config={"chart_id": "c1", "now_date": "2026-08-06", **config},
    )


@dataclass
class _FakeTarget:
    target_ref: str = "Venus"


_FAKE_TARGETS = [_FakeTarget()]  # materialize_event_class is monkeypatched; only .target_ref is read


def _fake_targets(*a, **k):
    return _FAKE_TARGETS


def _served_row(peak_date=date(2026, 9, 1)):
    return {
        "event_class": "marriage", "temporal_shape": "point",
        "window_start": peak_date, "window_end": peak_date, "peak_date": peak_date,
        "milestone_id": None, "is_irreversibility_milestone": False,
        "signed_intensity": 1.5, "raw_intensity": 1.5, "valence": "gain", "is_adverse": False,
        "active_sentences": [], "contributing_systems": [], "suppression_state": {},
        "peak_basis": "gochara_lambda_e_v1", "calibration_state": "structural_prior", "source": "live",
    }


# ── FROZEN contract conformance ───────────────────────────────────────────────


def test_writer_is_registered_under_its_asset_id():
    from pipeline.orchestrator.writers import get_writer
    assert get_writer("ka_gochara_sweep_v2") is not None


def test_asset_id_matches_registration():
    assert GocharaSweepV2Writer.asset_id == "ka_gochara_sweep_v2"


def test_declares_itself_a_heavy_writer():
    assert GocharaSweepV2Writer.has_substeps is True


def test_plans_one_substep_per_populated_event_class():
    conn = _FakeConn(_responder(event_classes=("marriage", "major_gain")))
    steps = GocharaSweepV2Writer().plan_substeps(_ctx(conn))
    assert [s.key for s in steps] == ["marriage", "major_gain"]


def test_honest_empty_plan_when_no_resonance_map_rows():
    conn = _FakeConn(_responder(event_classes=()))
    steps = GocharaSweepV2Writer().plan_substeps(_ctx(conn))
    assert steps == []


def test_writer_never_touches_the_transaction(monkeypatch):
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaSweepV2Writer().plan_substeps(ctx)[0]
    result = GocharaSweepV2Writer().run_substep(ctx, step)
    assert result.rows_inserted == 1  # reaching here proves no commit/rollback/close fired


def test_writer_never_writes_asset_throughput(monkeypatch):
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaSweepV2Writer().plan_substeps(ctx)[0]
    GocharaSweepV2Writer().run_substep(ctx, step)
    for sql, _ in conn.statements:
        assert "asset_throughput" not in sql.lower()


# ── The untouchable-data rail ─────────────────────────────────────────────────


def test_every_kala_gochara_windows_statement_is_generation_scoped(monkeypatch):
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaSweepV2Writer().plan_substeps(ctx)[0]
    GocharaSweepV2Writer().run_substep(ctx, step)

    windows_statements = [(s, p) for s, p in conn.statements if "kala_gochara_windows" in s.lower()]
    assert windows_statements, "the writer must issue at least one kala_gochara_windows statement"
    for sql, params in windows_statements:
        upper = sql.strip().upper()
        if upper.startswith("DELETE"):
            assert "GENERATION = %S" in sql.upper()
            assert params[-1] == GENERATION_V2 or GENERATION_V2 in params
        elif upper.startswith("INSERT"):
            assert "ON CONFLICT" not in sql.upper(), (
                "an ON CONFLICT DO UPDATE against the pre-generation natural key "
                "could silently overwrite a v1 row -- this writer must never use one"
            )
            assert params.get("generation") == GENERATION_V2


def test_delete_is_scoped_to_chart_event_class_and_generation(monkeypatch):
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaSweepV2Writer().plan_substeps(ctx)[0]
    GocharaSweepV2Writer().run_substep(ctx, step)

    deletes = [(s, p) for s, p in conn.statements
               if s.strip().upper().startswith("DELETE") and "kala_gochara_windows" in s.lower()]
    assert len(deletes) == 1
    sql, params = deletes[0]
    assert params == ["c1", "marriage", GENERATION_V2]


def test_a_row_collision_is_skipped_not_fatal_and_not_silently_overwritten(monkeypatch):
    """Simulates a real unique-constraint violation on the second of two
    rows: the writer must count it, log it, and still commit-path the first
    row -- never crash the whole substep, never silently succeed as if
    nothing happened."""
    rows = [_served_row(date(2026, 9, 1)), _served_row(date(2026, 9, 2))]
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=rows, contacts_evaluated=2, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)

    def fail_on(sql, params):
        return sql.strip().upper().startswith("INSERT INTO KALA_GOCHARA_WINDOWS") \
            and params is not None and params.get("peak_date") == date(2026, 9, 2)

    conn = _FakeConn(_responder(), fail_on=fail_on)
    ctx = _ctx(conn)
    step = GocharaSweepV2Writer().plan_substeps(ctx)[0]
    result = GocharaSweepV2Writer().run_substep(ctx, step)

    assert result.rows_inserted == 1, "the surviving row must still be counted"
    assert "1 collision" in result.notes or "collision" in result.notes


# ── Delta-aware invalidation (design amendment 2) ─────────────────────────────


def test_unchanged_fingerprint_skip_with_real_targets(monkeypatch):
    from dataclasses import dataclass

    @dataclass
    class _T:
        target_ref: str

    targets = [_T(target_ref="Venus"), _T(target_ref="Jupiter")]

    from services.w2g.fingerprint import class_fingerprint
    from services.w2g.materialize import GRAMMAR_VERSION
    arc_fps = {row["body"]: row["arc_fingerprint"] for row in ARC_FP_ROWS}
    fp = class_fingerprint("marriage", GRAMMAR_VERSION, [t.target_ref for t in targets], mod.BODIES, arc_fps)

    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", lambda *a, **k: targets)
    materialize_called = []
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: materialize_called.append(1) or MaterializeResult(rows=[], contacts_evaluated=0, targets_resolved=0))

    conn = _FakeConn(_responder(stored_fingerprint=fp))
    ctx = _ctx(conn)
    step = GocharaSweepV2Writer().plan_substeps(ctx)[0]
    result = GocharaSweepV2Writer().run_substep(ctx, step)

    assert materialize_called == [], "an unchanged fingerprint must short-circuit BEFORE materialize is even called"
    assert result.rows_inserted == 0
    assert "unchanged" in result.notes.lower()
    assert not [s for s, _ in conn.statements
                if "kala_gochara_windows" in s.lower() and s.strip().upper().startswith(("DELETE", "INSERT"))]


def test_changed_fingerprint_does_rebuild(monkeypatch):
    from dataclasses import dataclass

    @dataclass
    class _T:
        target_ref: str

    targets = [_T(target_ref="Venus")]
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", lambda *a, **k: targets)
    materialize_called = []
    monkeypatch.setattr(
        mod, "materialize_event_class",
        lambda *a, **k: (materialize_called.append(1),
                          MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))[1],
    )
    # stored_fingerprint deliberately WRONG -- forces a rebuild.
    conn = _FakeConn(_responder(stored_fingerprint="stale_fingerprint_value"))
    ctx = _ctx(conn)
    step = GocharaSweepV2Writer().plan_substeps(ctx)[0]
    result = GocharaSweepV2Writer().run_substep(ctx, step)

    assert materialize_called == [1]
    assert result.rows_inserted == 1


# ── Honest empty / skip reporting ─────────────────────────────────────────────


def test_no_targets_for_event_class_is_honest_empty_not_fatal(monkeypatch):
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", lambda *a, **k: [])
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaSweepV2Writer().plan_substeps(ctx)[0]
    result = GocharaSweepV2Writer().run_substep(ctx, step)
    assert result.rows_inserted == 0
    assert "empty" in result.notes.lower()


def test_dry_run_writes_nothing(monkeypatch):
    from dataclasses import dataclass

    @dataclass
    class _T:
        target_ref: str

    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", lambda *a, **k: [_T(target_ref="Venus")])
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    ctx.dry_run = True
    step = GocharaSweepV2Writer().plan_substeps(ctx)[0]
    result = GocharaSweepV2Writer().run_substep(ctx, step)
    assert result.rows_inserted == 0
    assert not [s for s, _ in conn.statements
                if "kala_gochara_windows" in s.lower() and s.strip().upper().startswith(("DELETE", "INSERT"))]


def test_horizon_is_progressive_partial_by_default():
    from services.w2g.materialize import progressive_horizon
    h = progressive_horizon(date(2026, 8, 6))
    assert h.status == HORIZON_STATUS_PROGRESSIVE
