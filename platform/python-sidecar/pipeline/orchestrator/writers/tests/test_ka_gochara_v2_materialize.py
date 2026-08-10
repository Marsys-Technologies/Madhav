"""Tests for the ka_gochara_v2_materialize writer (W2G lane G, item 19, REWORK).

Renamed from `test_ka_gochara_sweep_v2.py` (PR #1081, PARKED-HONEST) in the
lane G rework that followed the native ruling 2026-08-06
(SHAD_DARSHANA_STATE.md, "RULING — Lane G / W2G write-target"). The ruling's
four points map directly onto this file's test groups:

  1. "must NEVER set app.allow_protected_sweep_rewrite" -> the
     `test_writer_source_never_references_the_override_setting` static-source
     test below.
  2. "writes exclusively to its own surface ... does not delete, update, or
     insert into the protected ... rows" -> the untouchable-data-rail group,
     PLUS the new `test_writer_source_never_references_the_protected_table`
     static-source test (the strongest form of this assertion: not just "no
     statement in a recorded run touched it", but "the string does not exist
     in the module at all", so no code path -- reachable or not -- could ever
     construct one).

Everything here runs offline against a recording fake connection — no
database, no swisseph engine calls beyond real `import swisseph` (pure
ephemeris arithmetic, no I/O), no network. `materialize_event_class` (the
join+score step, already thoroughly tested against synthetic arcs and fake
grammar in `tests/test_w2g_materialize.py`) is monkeypatched here to a canned
double, so THESE tests isolate what is genuinely this module's own job:
FROZEN-contract conformance, generation-scoped idempotency against its OWN
table, the untouchable-data-rail defenses, delta-aware invalidation skip, and
honest empty/skip reporting.
"""
from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from datetime import date

import pytest

import pipeline.orchestrator.writers.ka_gochara as mod
import services.w2g.materialize as materialize_mod
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara import KaGocharaWriter
from services.w2g.materialize import GENERATION_V2, HORIZON_STATUS_PROGRESSIVE, MaterializeResult

# Alias for backward-compatibility with test assertions that reference the old class name
GocharaV2MaterializeWriter = KaGocharaWriter

# Word-boundary regex: matches the bare v1 table name but NOT as a prefix of
# `kala_gochara_windows_v2` (there is no \b between "s" and "_", both \w).
PROTECTED_TABLE_RE = re.compile(r"\bkala_gochara_windows\b")
OVERRIDE_SETTING = "allow_protected_sweep_rewrite"


def _source_excluding_module_docstring(module) -> str:
    """The module's source with its OWN leading docstring removed.

    The module docstring is documentation FOR HUMANS explaining the native
    ruling this writer conforms to — it legitimately quotes both forbidden
    strings verbatim (a docstring saying "this module must never reference
    X" necessarily contains the text "X"). The invariant this test actually
    needs to check is about CODE: no SQL statement, string constant used in
    a query, or executable code path may reference either string. Stripping
    exactly the module's own `__doc__` (not just "any comment", so a stray
    inline comment quoting the forbidden string for explanatory reasons
    elsewhere would still legitimately fail this check) keeps the test
    honest without becoming self-contradicting."""
    source = inspect.getsource(module)
    doc = module.__doc__
    if doc and doc in source:
        return source.replace(doc, "", 1)
    return source


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
        asset_id="ka_gochara",
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
    assert get_writer("ka_gochara") is not None


def test_asset_id_matches_registration():
    assert GocharaV2MaterializeWriter.asset_id == "ka_gochara"


def test_asset_id_is_not_the_superseded_name():
    # The prior (PARKED-HONEST, PR #1081) design's asset_id -- must never be
    # reused, since a stale asset_registry row for it still exists pending
    # migration 542's cleanup DELETE, and reusing the id would risk a caller
    # reading it and getting the wrong (deleted) row's stale expectations.
    assert GocharaV2MaterializeWriter.asset_id != "ka_gochara_sweep_v2"


def test_declares_itself_a_heavy_writer():
    assert GocharaV2MaterializeWriter.has_substeps is True


def test_plans_one_substep_per_populated_event_class():
    conn = _FakeConn(_responder(event_classes=("marriage", "major_gain")))
    steps = GocharaV2MaterializeWriter().plan_substeps(_ctx(conn))
    assert [s.key for s in steps] == ["marriage", "major_gain"]


def test_honest_empty_plan_when_no_resonance_map_rows():
    conn = _FakeConn(_responder(event_classes=()))
    steps = GocharaV2MaterializeWriter().plan_substeps(_ctx(conn))
    assert steps == []


def test_writer_never_touches_the_transaction(monkeypatch):
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    result = GocharaV2MaterializeWriter().run_substep(ctx, step)
    assert result.rows_inserted == 1  # reaching here proves no commit/rollback/close fired


def test_writer_never_writes_asset_throughput(monkeypatch):
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    GocharaV2MaterializeWriter().run_substep(ctx, step)
    for sql, _ in conn.statements:
        assert "asset_throughput" not in sql.lower()


# ── The untouchable-data rail (native ruling points 1 + 2) ───────────────────


def test_writer_source_never_references_the_protected_table():
    """The strongest form of the "never touches kala_gochara_windows" claim:
    not "no statement in one recorded run happened to touch it" but "the
    string does not appear anywhere in this module's source", so no code
    path -- reachable in a test or not -- could ever construct a statement
    against it. `\\bkala_gochara_windows\\b` deliberately does NOT match
    inside `kala_gochara_windows_v2` (no word boundary between "s" and "_",
    both \\w characters) -- this asserts absence of the BARE v1 name, not
    absence of this writer's own table. Scoped to CODE, not the module's own
    explanatory docstring (see `_source_excluding_module_docstring`)."""
    source = _source_excluding_module_docstring(mod)
    matches = PROTECTED_TABLE_RE.findall(source)
    assert matches == [], (
        f"ka_gochara.py must never reference the protected "
        f"kala_gochara_windows table (found {len(matches)} occurrence(s)) — "
        f"native ruling point 2"
    )
    # services/w2g/materialize.py issues no SQL at all (it is a pure
    # join+score function taking an injected query fn / arc source; see its
    # own module docstring) -- verified structurally, not by a source-text
    # grep, since that module's docstring legitimately DESCRIBES the served
    # row shape ("kala_gochara_windows-shaped rows") without ever executing a
    # statement against any table.
    assert "execute(" not in inspect.getsource(materialize_mod), (
        "services/w2g/materialize.py must remain a pure function module -- "
        "no direct SQL execution of any kind, against any table"
    )


def test_writer_source_never_references_the_override_setting():
    """Native ruling point 1, verbatim: 'The W2G writer must NEVER set
    app.allow_protected_sweep_rewrite, in any code path.' Checked by absence
    of the setting name anywhere in the writer's CODE (see
    `_source_excluding_module_docstring` — the module docstring itself
    legitimately quotes the ruling verbatim) — not just absence from
    statements issued in one test run."""
    source = _source_excluding_module_docstring(mod)
    assert OVERRIDE_SETTING not in source, (
        f"ka_gochara.py must never reference "
        f"app.{OVERRIDE_SETTING} — native ruling point 1 is a hard rule, "
        f"not a style preference"
    )


def test_table_constant_is_the_writers_own_surface():
    assert mod.TABLE == "kala_gochara_windows_v2"
    assert mod.TABLE != "kala_gochara_windows"


def test_every_statement_this_writer_issues_targets_its_own_table_only(monkeypatch):
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    GocharaV2MaterializeWriter().run_substep(ctx, step)

    windows_v2_statements = [(s, p) for s, p in conn.statements if "kala_gochara_windows_v2" in s.lower()]
    assert windows_v2_statements, "the writer must issue at least one kala_gochara_windows_v2 statement"
    for sql, _params in conn.statements:
        assert not PROTECTED_TABLE_RE.search(sql), (
            f"statement referenced the protected v1 table: {sql!r}"
        )


def test_every_kala_gochara_windows_v2_statement_is_generation_scoped(monkeypatch):
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    GocharaV2MaterializeWriter().run_substep(ctx, step)

    windows_statements = [(s, p) for s, p in conn.statements if "kala_gochara_windows_v2" in s.lower()]
    assert windows_statements, "the writer must issue at least one kala_gochara_windows_v2 statement"
    for sql, params in windows_statements:
        upper = sql.strip().upper()
        if upper.startswith("DELETE"):
            assert "GENERATION = %S" in sql.upper()
            assert params[-1] == GENERATION_V2 or GENERATION_V2 in params
        elif upper.startswith("INSERT"):
            assert "ON CONFLICT" not in sql.upper(), (
                "this writer never uses ON CONFLICT DO UPDATE against its own "
                "table either -- keeps collision counting honest"
            )
            assert params.get("generation") == GENERATION_V2


def test_delete_is_scoped_to_chart_event_class_and_generation(monkeypatch):
    monkeypatch.setattr(mod, "materialize_event_class",
                         lambda *a, **k: MaterializeResult(rows=[_served_row()], contacts_evaluated=1, targets_resolved=1))
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", _fake_targets)
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    GocharaV2MaterializeWriter().run_substep(ctx, step)

    deletes = [(s, p) for s, p in conn.statements
               if s.strip().upper().startswith("DELETE") and "kala_gochara_windows_v2" in s.lower()]
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
        return sql.strip().upper().startswith("INSERT INTO KALA_GOCHARA_WINDOWS_V2") \
            and params is not None and params.get("peak_date") == date(2026, 9, 2)

    conn = _FakeConn(_responder(), fail_on=fail_on)
    ctx = _ctx(conn)
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    result = GocharaV2MaterializeWriter().run_substep(ctx, step)

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
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    result = GocharaV2MaterializeWriter().run_substep(ctx, step)

    assert materialize_called == [], "an unchanged fingerprint must short-circuit BEFORE materialize is even called"
    assert result.rows_inserted == 0
    assert "unchanged" in result.notes.lower()
    assert not [s for s, _ in conn.statements
                if "kala_gochara_windows_v2" in s.lower() and s.strip().upper().startswith(("DELETE", "INSERT"))]


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
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    result = GocharaV2MaterializeWriter().run_substep(ctx, step)

    assert materialize_called == [1]
    assert result.rows_inserted == 1


# ── Honest empty / skip reporting ─────────────────────────────────────────────


def test_no_targets_for_event_class_is_honest_empty_not_fatal(monkeypatch):
    monkeypatch.setattr(mod.RM, "fetch_resonance_targets", lambda *a, **k: [])
    conn = _FakeConn(_responder())
    ctx = _ctx(conn)
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    result = GocharaV2MaterializeWriter().run_substep(ctx, step)
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
    step = GocharaV2MaterializeWriter().plan_substeps(ctx)[0]
    result = GocharaV2MaterializeWriter().run_substep(ctx, step)
    assert result.rows_inserted == 0
    assert not [s for s, _ in conn.statements
                if "kala_gochara_windows_v2" in s.lower() and s.strip().upper().startswith(("DELETE", "INSERT"))]


def test_horizon_is_progressive_partial_by_default():
    from services.w2g.materialize import progressive_horizon
    h = progressive_horizon(date(2026, 8, 6))
    assert h.status == HORIZON_STATUS_PROGRESSIVE
