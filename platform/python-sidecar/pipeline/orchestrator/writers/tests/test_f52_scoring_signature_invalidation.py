"""PARIŚEṢA F-52 gate: the delta fingerprint must catch a SCORING-MECHANISM change.

THE DEFECT
----------
PARIṢKĀRA MR-38 folded the writer's row SHAPE into
`compute_substep_fingerprint`, and its own SCOPE note stated the gap it left
open in plain language: value-computation changes "remain covered ONLY by the
ENGINE_VERSION standing rule".

PARIŚEṢA F-52/F-21 is that gap realised in production. `w23_tara_bala` (W2.3)
and `w30_nodal_drishti` (W3.0 — later-tradition Rahu/Ketu 5/7/9 special
aspects, enabled by default) were wired into `engine.py`'s lambda_v3 product:

    raw_lambda = promise * permission * activity * tara_modifier
                 * w30_modifier * quality_gates

That MOVES every stored window's `lambda_v3` and rewrites the served
`term_breakdown.formula` string — but adds, removes and renames NO column, so
MR-38's fold saw nothing; `ENGINE_VERSION` was not bumped for it; every stored
fingerprint still matched; the delta-skip fired; and already-materialised
windows kept their PRE-mechanism scores. Confirmed live on the canonical chart
(F-21's reproducer): every served window's `term_breakdown` carries the old
formula string with zero occurrences of `tara_modifier` / `w30_modifier`.

Concretely (F-52): as of 2026-08-15 Ketu transits Leo and casts a classical
5th aspect onto natal Venus (7th-lord + marriage kāraka), yet the served
marriage window shows zero Rahu/Ketu contribution — because the window was
scored before the mechanism existed and nothing ever invalidated it.

THE GATE
--------
  (a) A stored fingerprint computed under a PRE-`w30_nodal_drishti` engine
      signature must NOT match the fingerprint recomputed under the current
      engine — `run_substep` must call `find_threshold_crossings` (a real
      re-score), not take the skip path. THIS IS THE ACTUAL F-52 SCENARIO.
  (b) Flipping a mechanism's default toggle changes the signature.
  (c) Editing a mechanism's `compute()` body changes the signature.
  (d) Changing the lambda_v3 / term_breakdown formula constants changes it.
  (e) With nothing changed, the signature and the fingerprint are stable, and
      the skip path still works (no over-invalidation on every run).

TDD note: every test below asserting signature-sensitivity was RED against the
pre-fix source — `services.gochara_v3.scoring_signature` did not exist and
`compute_substep_fingerprint`'s payload had no scoring-mechanism input at all,
so a pre-w30 engine and the current engine produced the IDENTICAL fingerprint.
"""
from __future__ import annotations

import pytest

import pipeline.orchestrator.writers.ka_gochara_v3_century_materialize as mod
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    ASSET_ID,
    ENGINE_VERSION,
    GocharaV3CenturyMaterializeWriter,
    compute_substep_fingerprint,
)
from services.gochara_v3 import engine as engine_mod
from services.gochara_v3.scoring_signature import (
    discover_engine_mechanisms,
    scoring_signature,
    scoring_signature_digest,
    toggle_flag_name,
)

BUILD_STATE_TABLE = "kala_gochara_v2_build_state"
TABLE = mod.TABLE

# The engine's pre-W3.0 formula strings, verbatim from the served evidence
# F-21 cites (no tara_modifier / w30_modifier terms).
PRE_MECHANISM_LAMBDA_FORMULA = (
    "lambda_v3 = PROMISE * PERMISSION * activity * quality_gates"
)
PRE_MECHANISM_TERM_FORMULA = (
    "PROMISE × PERMISSION × activity × quality_gates"
)


# ---------------------------------------------------------------------------
# Fake DB connection (mirrors test_mr38_fingerprint_version_fold.py's pattern).
# ---------------------------------------------------------------------------


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
    """Records every SQL statement. Forbids commit/rollback/close (§N.2)."""

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
        build_id="test-build-f52",
        db_conn=conn,
        config={"chart_id": "482012f1-710e-4a25-994a-93821f5871aa", **extra_config},
    )


_DISCOVERED_CLASSES = [
    "career_advancement", "major_gain", "marriage",
    "illness_acute", "chronic_onset", "surgery",
]


def _responder(*, targets=("Venus", "Jupiter"), stored_fp=None, rows_exist=False):
    def responder(sql: str, params=None):
        s = sql.lower()
        if "gochara_resonance_map" in s and "distinct" in s and "target_ref" not in s:
            return [{"event_class": ec} for ec in _DISCOVERED_CLASSES]
        if "gochara_resonance_map" in s and "target_ref" in s:
            return [{"target_ref": t} for t in targets]
        if BUILD_STATE_TABLE in s and sql.strip().upper().startswith("SELECT"):
            if stored_fp is None:
                return []
            return [{"class_fingerprint": stored_fp}]
        if TABLE in s and "limit 1" in s:
            return [{"1": 1}] if rows_exist else []
        return []
    return responder


def _simulate_pre_w30_engine(monkeypatch):
    """Mutate the REAL engine module into its pre-W3.0 shape.

    Authentic simulation rather than a hand-built fake: we remove the engine's
    own `_w30` mechanism binding and restore the pre-W3.0 formula strings, so
    `discover_engine_mechanisms` walks a namespace genuinely shaped like the
    engine that scored the currently-served windows.
    """
    monkeypatch.delattr(engine_mod, "_w30", raising=True)
    monkeypatch.setattr(engine_mod, "LAMBDA_V3_FORMULA", PRE_MECHANISM_LAMBDA_FORMULA)
    monkeypatch.setattr(engine_mod, "TERM_BREAKDOWN_FORMULA", PRE_MECHANISM_TERM_FORMULA)


# ===========================================================================
# Signature level: the engine's scoring-mechanism set is discovered live.
# ===========================================================================


def test_w30_is_discovered_as_a_live_engine_mechanism():
    """`w30_nodal_drishti` must appear in the discovered mechanism set — it is
    wired into engine.py's production lambda_v3 product, so the fingerprint
    must know about it."""
    ids = [m["mechanism_id"] for m in discover_engine_mechanisms()]
    assert "w30_nodal_drishti" in ids, (
        f"w30_nodal_drishti is multiplied into engine.py's lambda_v3 product "
        f"but was not discovered by discover_engine_mechanisms(): {ids!r}"
    )
    assert "w23_tara_bala" in ids, (
        f"w23_tara_bala is multiplied into engine.py's lambda_v3 product but "
        f"was not discovered: {ids!r}"
    )


def test_discovered_mechanisms_carry_real_toggle_state_not_an_assumed_default():
    """Each discovered mechanism's `enabled` must be read from the engine's OWN
    toggle flag (§N.7 item 6 — an honest value, never an assumed-True default),
    and its compute() must be digested from real source."""
    by_id = {m["mechanism_id"]: m for m in discover_engine_mechanisms()}
    w30 = by_id["w30_nodal_drishti"]
    assert w30["toggle_flag"] == "_W30_NODAL_DRISHTI_ENABLED" == toggle_flag_name(
        "w30_nodal_drishti"
    )
    assert w30["enabled"] is getattr(engine_mod, "_W30_NODAL_DRISHTI_ENABLED"), (
        "the signature's `enabled` must BE the engine's live flag value, not a "
        "copy that can drift from it."
    )
    assert w30["compute_digest"] not in ("no-compute-callable", "source-unavailable")


def test_signature_records_the_engine_formula_constants():
    """The formula strings folded into the signature must be the engine's own
    canonical constants — the very strings emitted onto served rows — so the
    signature cannot drift from what F-21's reproducer reads."""
    sig = scoring_signature()
    assert sig["lambda_formula"] == engine_mod.LAMBDA_V3_FORMULA
    assert sig["term_breakdown_formula"] == engine_mod.TERM_BREAKDOWN_FORMULA
    assert "w30_modifier" in sig["term_breakdown_formula"]
    assert "tara_modifier" in sig["term_breakdown_formula"]


def test_signature_digest_is_deterministic():
    """No spurious invalidation: identical engine state → identical digest."""
    assert scoring_signature_digest() == scoring_signature_digest()


# ===========================================================================
# GATE (a) — THE ACTUAL F-52 SCENARIO, at the fingerprint level.
# ===========================================================================


def test_f52_adding_w30_mechanism_changes_the_signature(monkeypatch):
    """Wiring `w30_nodal_drishti` into the engine must change the scoring
    signature. Before this fix there was no signature at all, so the
    pre-mechanism and post-mechanism engines were indistinguishable to the
    delta-skip."""
    current = scoring_signature_digest()
    _simulate_pre_w30_engine(monkeypatch)
    pre = scoring_signature_digest()

    assert pre != current, (
        "F-52 regression: an engine WITHOUT w30_nodal_drishti wired in must "
        "produce a different scoring signature than one WITH it. Otherwise a "
        "mechanism that changes every window's lambda_v3 is invisible to the "
        "rebuild's delta-skip."
    )


def test_f52_adding_w30_mechanism_changes_the_substep_fingerprint(monkeypatch):
    """The signature change must actually reach `compute_substep_fingerprint`.

    Identical (event_class, era_slice_key, engine_version, resonance_targets)
    and identical row schema — the ONLY difference is that the engine gained
    the w30 nodal-drishti mechanism. The fingerprint MUST differ.
    """
    args = ("marriage", "g3_2024_2034", ENGINE_VERSION, ["Venus", "Jupiter"])
    fp_current = compute_substep_fingerprint(*args)

    _simulate_pre_w30_engine(monkeypatch)
    fp_pre = compute_substep_fingerprint(*args)

    assert fp_pre != fp_current, (
        "F-52 regression: compute_substep_fingerprint must be sensitive to the "
        "engine's scoring-mechanism set. Wiring w30_nodal_drishti (or "
        "w23_tara_bala) into the lambda_v3 product changes every window's "
        "computed value while adding no column — if the fingerprint does not "
        "change, an authorized rebuild silently no-ops and the served windows "
        "stay frozen at their pre-mechanism scores (the exact F-52/F-21 "
        "defect: Ketu's real 5th aspect onto natal Venus never reaching the "
        "served marriage window)."
    )


def test_f52_gate_a_stale_pre_mechanism_fingerprint_forces_a_rescore(monkeypatch):
    """GATE (a), integration level: a fingerprint STORED when the engine had no
    w30 mechanism must not match today's, so `run_substep` performs a real
    re-score (`find_threshold_crossings` runs) instead of skipping.

    This is the end-to-end proof for the finding: the mechanism-version change
    invalidates previously-scored data rather than leaving it stale.
    """
    targets = ["Venus", "Jupiter"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    # Fingerprint as it would have been STORED by the pre-W3.0 build.
    with pytest.MonkeyPatch.context() as pre_mp:
        _simulate_pre_w30_engine(pre_mp)
        stale_fp = compute_substep_fingerprint(ec, era_key, ENGINE_VERSION, targets)

    # Sanity: the engine is back to its real (post-W3.0) shape.
    assert hasattr(engine_mod, "_w30")

    conn = _FakeConn(_responder(targets=targets, stored_fp=stale_fp, rows_exist=True))
    ctx = _ctx(conn)

    called = []
    monkeypatch.setattr(
        mod, "find_threshold_crossings",
        lambda *a, **k: called.append(1) or [],
    )
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import sys
        import types
        monkeypatch.setitem(sys.modules, "swisseph", types.ModuleType("swisseph"))

    writer.run_substep(ctx, step)

    assert called == [1], (
        "GATE (a) FAILED: a fingerprint stored before w30_nodal_drishti was "
        "wired into the engine must force a real re-score. Taking the skip "
        "path here is precisely F-52: served windows frozen at pre-mechanism "
        "scores while the codebase claims the mechanism is active."
    )


def test_f52_gate_e_unchanged_engine_still_skips(monkeypatch):
    """GATE (e): the fix must not over-invalidate. With the engine unchanged
    and rows present, the delta-skip still fires (no rebuild every run)."""
    targets = ["Venus", "Jupiter"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    expected_fp = compute_substep_fingerprint(ec, era_key, ENGINE_VERSION, targets)
    conn = _FakeConn(_responder(targets=targets, stored_fp=expected_fp, rows_exist=True))

    called = []
    monkeypatch.setattr(
        mod, "find_threshold_crossings",
        lambda *a, **k: called.append(1) or [],
    )

    result = writer.run_substep(_ctx(conn), step)

    assert called == [], (
        "GATE (e) FAILED: an unchanged engine must still skip. The F-52 fold "
        "must invalidate on real mechanism change, not on every run."
    )
    assert result.rows_inserted == 0


# ===========================================================================
# GATES (b)/(c)/(d) — toggle, compute() body, formula constants.
# ===========================================================================


def test_f52_gate_b_flipping_a_mechanism_toggle_changes_the_fingerprint(monkeypatch):
    """GATE (b): disabling `w30_nodal_drishti` by default changes every
    window's lambda_v3 (modifier forced to 1.0) while adding no column — the
    fingerprint must catch it."""
    args = ("marriage", "g3_2024_2034", ENGINE_VERSION, ["Venus"])
    fp_enabled = compute_substep_fingerprint(*args)

    monkeypatch.setattr(engine_mod, "_W30_NODAL_DRISHTI_ENABLED", False)
    fp_disabled = compute_substep_fingerprint(*args)

    assert fp_enabled != fp_disabled, (
        "GATE (b) FAILED: flipping _W30_NODAL_DRISHTI_ENABLED changes the "
        "scored value of every window and must invalidate stored fingerprints."
    )


def test_f52_gate_c_editing_a_mechanism_compute_body_changes_the_fingerprint(monkeypatch):
    """GATE (c): a value-computation change INSIDE a mechanism — e.g. altering
    the tara schedule or a nodal aspect offset — must invalidate, with no
    human bumping ENGINE_VERSION."""
    args = ("marriage", "g3_2024_2034", ENGINE_VERSION, ["Venus"])
    fp_before = compute_substep_fingerprint(*args)

    def _edited_compute(*a, **k):  # pragma: no cover - never called
        """A different compute() body (stands in for a modifier-schedule edit)."""
        raise NotImplementedError

    monkeypatch.setattr(engine_mod._w30, "compute", _edited_compute)
    fp_after = compute_substep_fingerprint(*args)

    assert fp_before != fp_after, (
        "GATE (c) FAILED: editing a mechanism's compute() body changes what "
        "value it contributes to lambda_v3 and must invalidate the fingerprint."
    )


def test_f52_gate_d_changing_the_served_formula_changes_the_fingerprint(monkeypatch):
    """GATE (d): the `term_breakdown.formula` string F-21's reproducer reads is
    persisted onto every row. Changing it must invalidate — a served row whose
    formula string disagrees with the engine's current formula is exactly the
    stale-data symptom F-21 reports."""
    args = ("marriage", "g3_2024_2034", ENGINE_VERSION, ["Venus"])
    fp_before = compute_substep_fingerprint(*args)

    monkeypatch.setattr(engine_mod, "TERM_BREAKDOWN_FORMULA", PRE_MECHANISM_TERM_FORMULA)
    fp_after = compute_substep_fingerprint(*args)

    assert fp_before != fp_after, (
        "GATE (d) FAILED: the persisted/served term_breakdown.formula string "
        "must be part of the fingerprint."
    )


def test_mr38_row_schema_fold_still_holds(monkeypatch):
    """Regression guard: F-52's fold must COMPOSE with MR-38's, not replace it.
    A row-shape change with the engine untouched must still invalidate."""
    args = ("marriage", "g3_1984_1994", ENGINE_VERSION, ["Venus"])
    monkeypatch.setattr(mod, "ROW_SCHEMA_COLUMNS", ("chart_id", "event_class"))
    fp_old = compute_substep_fingerprint(*args)
    monkeypatch.setattr(
        mod, "ROW_SCHEMA_COLUMNS", ("chart_id", "event_class", "term_breakdown"),
    )
    assert fp_old != compute_substep_fingerprint(*args)
