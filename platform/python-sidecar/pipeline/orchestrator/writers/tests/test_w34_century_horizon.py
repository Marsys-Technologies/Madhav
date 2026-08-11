"""Tests for W3.4 Century horizon + slice receipts.

GOCHARA-UTKARSA campaign, wave W3.4. No DB required — all tests use
fixture-based fakes.

Acceptance criteria covered:
  AC1: plan_substeps is implemented — returns a list of dicts with at least
       'substep_key' and 'substep_label' (SubStep has .key and .label).
  AC2: Full-century plan covers all event_classes × all decade slices
       (60 substeps for 6 classes × 10 decades).
  AC3: run_substep materializes rows with correct era_slice_key.
       (Structural test — verifies DELETE+INSERT SQL and era_slice_key column.)
  AC4: Delta fingerprint is computed and stored; re-submit of unchanged
       substep skips re-materialization.
  AC5: Wall-clock time is logged at DEBUG per substep.
       (Verified via log capture.)
  AC6: I2 constraint — no imports from gochara_grammar/*, gochara_intensity/*,
       or ka_gochara_sweep/*.
  AC7: I4 — empty resonance targets → honest 0 rows, no fabrication.
  AC8: Unit tests: plan_substeps structure, fingerprint computation,
       era_slice_key format.
"""
from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from datetime import date

import pytest

import pipeline.orchestrator.writers.ka_gochara_v3_century_materialize as mod
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    ASSET_ID,
    DECADE_COUNT,
    DECADE_SLICES,
    ENGINE_VERSION,
    EVENT_CLASSES,
    GENERATION_PROD,
    GENERATION_V3,
    PROD_TABLE,
    TABLE,
    GocharaV3CenturyMaterializeWriter,
    build_decade_slices,
    compute_substep_fingerprint,
)
from services.gochara_v3.resolution_hierarchy import HierarchyResult, WindowResolutionRecord
from services.gochara_v3.shape_conformance_vocab import (
    SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
)

# PARIṢKĀRA MR-11(b): run_substep now calls build_resolution_hierarchy (not
# find_threshold_crossings directly) — every test below that used to
# monkeypatch mod.find_threshold_crossings now monkeypatches
# mod.build_resolution_hierarchy instead, returning a HierarchyResult. This
# constant is the "found nothing" case (mirrors the old `lambda *a,**k: []`).
_EMPTY_HIERARCHY = HierarchyResult(
    era_windows=[], month_windows=[], day_windows=[],
    resolution_facet={"era": 0, "month": 0, "day": 0},
)


# ---------------------------------------------------------------------------
# Forbidden import patterns (I2, AC6)
# ---------------------------------------------------------------------------

_FORBIDDEN_IMPORT_PATTERNS = [
    r"from\s+services\.gochara_grammar",
    r"import\s+services\.gochara_grammar",
    r"from\s+services\.gochara_intensity",
    r"import\s+services\.gochara_intensity",
    r"from\s+services\.ka_gochara_sweep",
    r"import\s+services\.ka_gochara_sweep",
]


def _module_source_excluding_docstring(module) -> str:
    """Return the module source with its own leading docstring stripped.

    The docstring legitimately names the forbidden prefixes for documentation
    purposes. The I2 invariant is about EXECUTABLE code, not documentation.
    """
    source = inspect.getsource(module)
    doc = module.__doc__
    if doc and doc in source:
        return source.replace(doc, "", 1)
    return source


# ---------------------------------------------------------------------------
# Fake DB connection (no real DB required)
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
        build_id="test-build-w34",
        db_conn=conn,
        config={"chart_id": "482012f1-710e-4a25-994a-93821f5871aa", **extra_config},
    )


# MR-16: the default discovered-classes set for _responder — matches the
# historical EVENT_CLASSES 6-class scope so every pre-MR-16 test in this file
# (which assumed a static 60-substep plan) keeps working unchanged when it
# doesn't care about dynamic discovery itself. Tests that specifically
# exercise the new dynamic behaviour pass their own `discovered_classes`.
_DEFAULT_DISCOVERED_CLASSES = list(EVENT_CLASSES)


def _responder(
    *,
    targets: list[str] = ("Venus",),
    stored_fp: str | None = None,
    rows_exist: bool = False,
    discovered_classes: list[str] | None = None,
):
    """Build a query responder for _FakeConn."""
    classes = _DEFAULT_DISCOVERED_CLASSES if discovered_classes is None else discovered_classes

    def responder(sql: str, params=None) -> list[dict]:
        s = sql.lower()
        # MR-16: the dynamic event-class discovery query — DISTINCT
        # event_class, no target_ref column — must be checked BEFORE the
        # target_ref branch below (the two queries share the table name).
        if "gochara_resonance_map" in s and "distinct" in s and "event_class" in s and "target_ref" not in s:
            return [{"event_class": ec} for ec in classes]
        if "gochara_resonance_map" in s and "target_ref" in s:
            return [{"target_ref": t} for t in targets]
        if BUILD_STATE_TABLE in s and sql.strip().upper().startswith("SELECT"):
            if stored_fp is None:
                return []
            return [{"class_fingerprint": stored_fp}]
        if TABLE in s and "limit 1" in s:
            if rows_exist:
                return [{"1": 1}]
            return []
        return []
    return responder


BUILD_STATE_TABLE = "kala_gochara_v2_build_state"


# ===========================================================================
# AC6 — I2 constraint: no forbidden imports in module code
# ===========================================================================


def test_i2_no_gochara_grammar_imports():
    """AC6: gochara_grammar must not be imported in the writer's code."""
    source = _module_source_excluding_docstring(mod)
    for pattern in _FORBIDDEN_IMPORT_PATTERNS[:2]:
        assert not re.search(pattern, source), (
            f"I2 violation: pattern {pattern!r} found in "
            f"ka_gochara_v3_century_materialize.py code"
        )


def test_i2_no_gochara_intensity_imports():
    """AC6: gochara_intensity must not be imported in the writer's code."""
    source = _module_source_excluding_docstring(mod)
    for pattern in _FORBIDDEN_IMPORT_PATTERNS[2:4]:
        assert not re.search(pattern, source), (
            f"I2 violation: pattern {pattern!r} found in "
            f"ka_gochara_v3_century_materialize.py code"
        )


def test_i2_no_ka_gochara_sweep_imports():
    """AC6: ka_gochara_sweep must not be imported in the writer's code."""
    source = _module_source_excluding_docstring(mod)
    for pattern in _FORBIDDEN_IMPORT_PATTERNS[4:]:
        assert not re.search(pattern, source), (
            f"I2 violation: pattern {pattern!r} found in "
            f"ka_gochara_v3_century_materialize.py code"
        )


def test_writer_production_table_is_kala_gochara_windows():
    """W5.4 repoint (UTK-R1): PROD_TABLE is kala_gochara_windows (production surface).
    The writer now intentionally references kala_gochara_windows for generation='3.0'
    writes. The generation='3.0' predicate invariant is enforced by the mutation-guard
    test (test_ka_gochara_v3_mutation_guard.py), not by banning the table name."""
    from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import PROD_TABLE
    assert PROD_TABLE == "kala_gochara_windows", (
        f"PROD_TABLE must be 'kala_gochara_windows' (UTK-R1), got {PROD_TABLE!r}"
    )


# ===========================================================================
# AC1 + AC2 — plan_substeps structure (event_class set = whatever
# gochara_resonance_map holds for this chart; DEFAULT fixture = historical 6)
# ===========================================================================


def test_plan_substeps_returns_list_of_substeps():
    """AC1: plan_substeps returns a non-empty list."""
    conn = _FakeConn(_responder())
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    assert isinstance(steps, list)
    assert len(steps) > 0


def test_plan_substeps_each_has_key_and_label():
    """AC1: each SubStep has a non-empty .key and .label."""
    conn = _FakeConn(_responder())
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    for step in steps:
        assert hasattr(step, "key"), "SubStep must have .key"
        assert hasattr(step, "label"), "SubStep must have .label"
        assert step.key, f"SubStep.key must be non-empty, got {step.key!r}"
        assert step.label, f"SubStep.label must be non-empty, got {step.label!r}"


def test_plan_substeps_60_total():
    """AC2: exactly len(EVENT_CLASSES) × 10 decade_slices substeps, when the
    chart's resonance map holds the DEFAULT discovered-classes fixture
    (`_responder()`'s default, `_DEFAULT_DISCOVERED_CLASSES` — MR-16's
    per-chart-dynamic `_discover_event_classes` query, mocked here to return
    the full documentation-only EVENT_CLASSES set).

    PARIṢKĀRA MR-12: EVENT_CLASSES gained 'business_launch' (the first
    genuinely chain-canonical class), so this is now 7 × 10 = 70, not the
    original W3.4 baseline of 60 (6 × 10). The count is derived from
    len(EVENT_CLASSES) rather than a re-hardcoded literal so this test
    documents the relationship instead of re-drifting the next time
    EVENT_CLASSES changes. (Today's LIVE resonance map for the two canonical
    charts is still the historical 6-class scope, pre-R2-rebuild — this test
    fixture's default is the writer's discoverable UNIVERSE, not a claim
    about current production coverage; see test_plan_substeps_*_discovered_
    classes below for the dynamic-discovery-specific tests.)
    """
    conn = _FakeConn(_responder())
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    expected = len(EVENT_CLASSES) * DECADE_COUNT
    assert expected == 70, (
        f"MR-12 sanity: expected len(EVENT_CLASSES) * DECADE_COUNT == 70 "
        f"(7 classes x 10 decades), got {expected}"
    )
    assert len(steps) == expected, (
        f"Expected {expected} substeps ({len(EVENT_CLASSES)} classes × "
        f"{DECADE_COUNT} decades), got {len(steps)}"
    )


def test_plan_substeps_covers_all_event_classes():
    """AC2: every DISCOVERED event_class appears in the plan."""
    conn = _FakeConn(_responder())
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    keys_found = {s.key.split("::", 1)[0] for s in steps}
    assert keys_found == set(EVENT_CLASSES), (
        f"Missing event classes: {set(EVENT_CLASSES) - keys_found}"
    )


def test_plan_substeps_covers_all_decade_slices():
    """AC2: every decade slice appears in the plan."""
    conn = _FakeConn(_responder())
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    era_keys_found = {s.key.split("::", 1)[1] for s in steps if "::" in s.key}
    expected_era_keys = {d.era_slice_key for d in DECADE_SLICES}
    assert era_keys_found == expected_era_keys, (
        f"Missing era slices: {expected_era_keys - era_keys_found}"
    )


def test_plan_substeps_each_class_has_10_decades():
    """AC2: each event class has exactly 10 substeps (one per decade)."""
    conn = _FakeConn(_responder())
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    from collections import Counter
    class_counts = Counter(s.key.split("::", 1)[0] for s in steps)
    for ec in EVENT_CLASSES:
        assert class_counts[ec] == 10, (
            f"event_class={ec!r} has {class_counts[ec]} substeps, expected 10"
        )


def test_plan_substeps_no_duplicate_keys():
    """AC2: all substep keys are unique."""
    conn = _FakeConn(_responder())
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    keys = [s.key for s in steps]
    assert len(keys) == len(set(keys)), "Duplicate substep keys found"


def test_plan_substeps_key_format():
    """AC2: substep_key format is '{event_class}::{era_slice_key}'."""
    conn = _FakeConn(_responder())
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    for step in steps:
        assert "::" in step.key, (
            f"substep_key must contain '::' separator, got {step.key!r}"
        )
        ec, era_key = step.key.split("::", 1)
        assert ec in EVENT_CLASSES, f"Unknown event_class {ec!r} in substep_key"
        assert era_key.startswith("g3_"), (
            f"era_slice_key must start with 'g3_', got {era_key!r}"
        )


# ===========================================================================
# MR-16 — dynamic event-class discovery (kills the hardcoded 6)
# ===========================================================================
#
# TDD discipline: these tests are RED against the pre-MR-16 writer (whose
# plan_substeps ignored the DB entirely and always iterated the hardcoded
# EVENT_CLASSES list); GREEN once plan_substeps discovers its event-class
# set live from gochara_resonance_map via _discover_event_classes.


def test_plan_substeps_class_set_follows_resonance_map_not_hardcoded_list():
    """Core MR-16 assertion: a fixture resonance map with a DIFFERENT class
    set than EVENT_CLASSES (some overlapping, some entirely new W3.1 classes
    never in the hardcoded 6) produces a plan over EXACTLY that set — never
    silently substituting/falling back to EVENT_CLASSES."""
    custom_classes = ["career_entry", "romantic_start", "bereavement"]
    conn = _FakeConn(_responder(discovered_classes=custom_classes))
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))

    keys_found = {s.key.split("::", 1)[0] for s in steps}
    assert keys_found == set(custom_classes), (
        f"plan_substeps must follow the discovered resonance-map classes "
        f"exactly, got {keys_found}, expected {set(custom_classes)}"
    )
    # None of the hardcoded EVENT_CLASSES leaked in — proves there is no
    # silent fallback/union with the historical list.
    assert not (keys_found & set(EVENT_CLASSES) - set(custom_classes)), (
        "plan_substeps leaked a hardcoded EVENT_CLASSES member that was "
        "not in the fixture's discovered set — a fallback is still active"
    )


def test_plan_substeps_class_count_scales_with_resonance_map_n_classes():
    """N classes discovered -> N × 10 decade substeps, for several N —
    proves the substep COUNT is driven by live discovery, not a fixed 6."""
    for n_classes, classes in (
        (1, ["marriage"]),
        (3, ["marriage", "major_gain", "career_advancement"]),
        (9, [f"custom_class_{i}" for i in range(9)]),
        (27, [f"class_{i}" for i in range(27)]),  # full W3.1 ceiling
    ):
        conn = _FakeConn(_responder(discovered_classes=classes))
        steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
        assert len(steps) == n_classes * 10, (
            f"discovered {n_classes} classes -> expected {n_classes * 10} "
            f"substeps (× 10 decades), got {len(steps)}"
        )


def test_plan_substeps_empty_resonance_map_is_honest_zero_substeps():
    """I4 at the plan level (MR-16): a chart with NO gochara_resonance_map
    rows at all produces a ZERO-substep plan — never a fallback to
    EVENT_CLASSES (which would silently plan 60 substeps for a chart G-1
    has not been run for yet)."""
    conn = _FakeConn(_responder(discovered_classes=[]))
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    assert steps == [], (
        f"Expected zero substeps for an empty resonance map, got {len(steps)}: "
        f"{[s.key for s in steps]}"
    )


def test_plan_substeps_does_not_query_target_ref_at_plan_time():
    """plan_substeps' discovery query is a DISTINCT event_class read — it
    must not also issue the per-class target_ref fetch (that happens later,
    per-substep, inside run_substep) — keeps the plan-time query cheap (one
    query total, not one per event_class)."""
    responder_calls: list[str] = []

    def _tracking_responder(sql, params=None):
        responder_calls.append(sql)
        return [{"event_class": ec} for ec in ("marriage", "major_gain")]

    conn = _FakeConn(_tracking_responder)
    GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))

    target_ref_queries = [s for s in responder_calls if "target_ref" in s.lower()]
    assert target_ref_queries == [], (
        f"plan_substeps must not fetch target_ref (per-substep concern), "
        f"issued: {target_ref_queries}"
    )


def test_discover_event_classes_is_distinct_and_ordered():
    """_discover_event_classes issues a DISTINCT ... ORDER BY event_class
    query (ascending, matching ka_gochara_sweep's sibling implementation) —
    a static-source guard so a future edit can't silently drop ORDER BY/
    DISTINCT and reintroduce nondeterministic substep ordering."""
    source = inspect.getsource(mod._discover_event_classes)
    assert "DISTINCT" in source.upper(), (
        "_discover_event_classes must use SELECT DISTINCT event_class"
    )
    assert "ORDER BY" in source.upper(), (
        "_discover_event_classes must use ORDER BY for deterministic ordering"
    )
    assert "gochara_resonance_map" in source, (
        "_discover_event_classes must read from gochara_resonance_map"
    )


def test_discover_event_classes_genuine_empty_query_still_returns_empty_list():
    """PARĪKṢAKA F1 anti-fallback invariant, unchanged: a query that RUNS
    SUCCESSFULLY and finds zero rows (the honest "G-1 hasn't built this
    chart yet" case) must still return [] — never a fallback to
    EVENT_CLASSES (the exact hardcoded-6 defect this fix removes)."""
    conn = _FakeConn(_responder(discovered_classes=[]))
    result = mod._discover_event_classes(conn, "482012f1-710e-4a25-994a-93821f5871aa")
    assert result == [], (
        f"_discover_event_classes must return [] for a genuinely empty "
        f"resonance map, got {result}"
    )


def test_discover_event_classes_db_failure_propagates(monkeypatch):
    """PARĪKṢAKA F1 (MATERIAL): a DB error during discovery must PROPAGATE,
    never be swallowed into an empty list. The orchestrator's own
    no-op-completion re-probe (asset_runner.py:625-645, the SATYA-DĪPA fix)
    wraps its `plan_substeps(ctx)` call in a try/except that treats ANY
    exception as "conservatively incomplete" (fail-closed) and a `[]`
    result as "genuinely done" — swallowing the error here would make a
    transient query failure indistinguishable from an honestly empty
    resonance map and could promote a FAILED build to state='lit'
    (remaining_count=0 -> plan_complete=True). See _discover_event_classes'
    own docstring for the full rationale."""
    def _raising_responder(sql, params=None):
        raise RuntimeError("simulated connection failure")

    conn = _FakeConn(_raising_responder)
    with pytest.raises(RuntimeError, match="simulated connection failure"):
        mod._discover_event_classes(conn, "482012f1-710e-4a25-994a-93821f5871aa")


def test_plan_substeps_propagates_discovery_db_failure():
    """PARĪKṢAKA F1: the exception must propagate all the way OUT of
    plan_substeps too — plan_substeps must not add its own try/except
    around the _discover_event_classes call that would re-introduce the
    swallow one level up."""
    def _raising_responder(sql, params=None):
        raise RuntimeError("simulated connection failure")

    conn = _FakeConn(_raising_responder)
    writer = GocharaV3CenturyMaterializeWriter()
    with pytest.raises(RuntimeError, match="simulated connection failure"):
        writer.plan_substeps(_ctx(conn))


def test_event_classes_constant_no_longer_drives_plan_substeps():
    """Regression lock: even though EVENT_CLASSES the constant still exists
    (documentation-only, MR-16), plan_substeps must NOT reference it as a
    fallback or default anywhere in its own EXECUTABLE code (the docstring
    legitimately explains the historical constant by name)."""
    fn = GocharaV3CenturyMaterializeWriter.plan_substeps
    source = inspect.getsource(fn)
    # Strip the function's own leading docstring (its first triple-quoted
    # string) — it legitimately names EVENT_CLASSES for documentation; the
    # invariant under test is about EXECUTABLE code only.
    code_only = re.sub(r'""".*?"""', "", source, count=1, flags=re.DOTALL)
    assert "EVENT_CLASSES" not in code_only, (
        "plan_substeps must not reference the hardcoded EVENT_CLASSES "
        f"constant in its executable code (MR-16 kill-the-hardcoded-6 fix). "
        f"Code:\n{code_only}"
    )


# ===========================================================================
# MR-16 — honest per-class coverage-quality note
# ===========================================================================


def test_coverage_quality_note_tiers_by_live_target_count():
    """_coverage_quality_note buckets tier from the ACTUAL target_refs count
    passed in — never a static per-class label."""
    empty = mod._coverage_quality_note("marriage", [])
    thin = mod._coverage_quality_note("marriage", ["Venus"])
    moderate = mod._coverage_quality_note("marriage", ["Venus", "Jupiter", "7", "2"])
    rich = mod._coverage_quality_note("marriage", ["a", "b", "c", "d", "e", "f", "g"])

    assert empty["tier"] == "empty" and empty["target_count"] == 0
    assert thin["tier"] == "thin" and thin["target_count"] == 1
    assert moderate["tier"] == "moderate" and moderate["target_count"] == 4
    assert rich["tier"] == "rich" and rich["target_count"] == 7
    for note in (empty, thin, moderate, rich):
        assert "marriage" in note["note"]


def test_coverage_quality_note_never_invents_targets():
    """The note's target_count must always equal len(target_refs) exactly —
    it must never round up, pad, or otherwise invent coverage that was not
    actually fetched (I4)."""
    for refs in ([], ["Venus"], ["Venus", "Jupiter", "Mars"]):
        note = mod._coverage_quality_note("illness_acute", refs)
        assert note["target_count"] == len(refs)


def test_build_row_embeds_coverage_quality_in_suppression_state():
    """_build_row, given a coverage_quality note, serializes it under
    suppression_state['coverage_quality'] — the served, opaque-pass-through
    JSONB channel register_gochara_windows.ts already carries through to
    callers unmodified."""
    from services.gochara_v3.interval_solver import IntervalBoundary
    import json as _json

    boundary = IntervalBoundary(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=0.5,
        era_slice_key="g3_1984_1994",
    )
    note = {"tier": "thin", "target_count": 1, "note": "marriage: 1 target"}
    row = mod._build_row(
        "chart-x", "marriage", boundary, "g3_1984_1994",
        valence="neutral", is_adverse=False,
        peak_basis=mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
        coverage_quality=note,
        shape_conformance=SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    )
    parsed = _json.loads(row["suppression_state"])
    assert parsed["coverage_quality"] == note


def test_build_row_suppression_state_honest_degrade_without_coverage_quality():
    """Backward-compat / I4: omitting coverage_quality (pre-MR-16 call
    sites, if any survive) must still produce a valid suppression_state —
    never raise, never fabricate a note.

    UPDATED at rebase-merge time (PK-R-9, 2026-08-11): before MR-42 landed,
    omitting coverage_quality produced a bare `{}`. MR-42's own GATE is
    exactly that a computed row must NEVER carry a bare `{}` suppression_
    state (see `_build_suppression_state`) -- so the honest-empty shape
    this test now pins is the I4-degrade structured object (`term_breakdown`
    is ALSO omitted in this call, so `_build_suppression_state` takes its
    None-term_breakdown branch), not `{}`. `coverage_quality` omitted here
    simply means the `coverage_quality` KEY is absent from that structured
    object -- see the sibling
    test_build_row_embeds_coverage_quality_in_suppression_state for the
    present case."""
    from services.gochara_v3.interval_solver import IntervalBoundary
    import json as _json

    boundary = IntervalBoundary(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=0.5,
        era_slice_key="g3_1984_1994",
    )
    row = mod._build_row(
        "chart-x", "marriage", boundary, "g3_1984_1994",
        valence="neutral", is_adverse=False,
        peak_basis=mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
        shape_conformance=SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    )
    parsed = _json.loads(row["suppression_state"])
    assert parsed != {}
    assert parsed["mechanism"] == "quality_gates"
    assert parsed["value"] is None  # term_breakdown also omitted -> I4 degrade
    assert "coverage_quality" not in parsed


def test_run_substep_result_notes_carry_coverage_quality_tier(monkeypatch):
    """The per-substep build report (WriterResult.notes) — the ONLY
    orchestrator-visible surface for a heavy writer's free-text output —
    carries the coverage_quality tier, so a build-log/SSE consumer can see
    it without querying the row directly."""
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
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")

    result = writer.run_substep(ctx, step)
    assert "coverage_quality=" in result.notes, (
        f"Expected coverage_quality tier in WriterResult.notes, got: {result.notes!r}"
    )


_INSERT_TABLE_RE_F2 = re.compile(r"INSERT\s+INTO\s+(\S+)", re.IGNORECASE)


def _prod_insert_params(statements: list[tuple[str, object]]) -> list[dict]:
    """INSERT params whose SQL targets EXACTLY PROD_TABLE (not TABLE, the
    calibration/staging table — kala_gochara_windows is a strict prefix of
    kala_gochara_windows_v2, so a naive substring/startswith check
    over-matches; mirrors test_mr13/test_mr14's _inserts_for_table and the
    _dml_target_table fix in test_ka_gochara_v3_mutation_guard.py)."""
    out = []
    for sql, params in statements:
        if not isinstance(params, dict):
            continue
        m = _INSERT_TABLE_RE_F2.match(sql.strip())
        if m and m.group(1).lower() == PROD_TABLE.lower():
            out.append(params)
    return out


def test_run_substep_coverage_quality_target_count_matches_actual_targets(monkeypatch):
    """PARĪKṢAKA F2 (real detector, replaces the substring-only check above):
    the SERVED ROW's own suppression_state.coverage_quality.target_count —
    not just the presence of the substring 'coverage_quality=' somewhere in
    WriterResult.notes — must equal the ACTUAL number of resonance targets
    this substep fetched.

    This is a real detector for two defects the notes-substring test
    (test_run_substep_result_notes_carry_coverage_quality_tier, above)
    provably CANNOT catch, because a mutated run_substep can still emit a
    notes string containing 'coverage_quality=' while the row itself is
    wrong:
      (i)  coverage_quality=None passed to both _build_row call sites
           -> suppression_state has no 'coverage_quality' key at all.
      (ii) a HARDCODED note (e.g. {"tier": "rich", "target_count": 99})
           used at both _build_row call sites regardless of the actual
           fetch -> the notes text still says "coverage_quality=rich
           (99 target(s))" (a literal, well-formed substring match) but
           the row's target_count never reflects reality.

    Two DIFFERENT target-list sizes are exercised so a single hardcoded
    constant cannot coincidentally satisfy both — the classic "one example
    isn't a mutation-proof detector" trap.
    """
    from services.gochara_v3.interval_solver import IntervalBoundary
    import json as _json

    for targets in (["Venus"], ["Venus", "Jupiter", "Mars", "Saturn"]):
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
        try:
            import swisseph  # noqa: F401
        except ImportError:
            import types, sys
            sys.modules["swisseph"] = types.ModuleType("swisseph")

        result = writer.run_substep(ctx, step)
        assert result.rows_inserted == 1, f"targets={targets}"

        prod_rows = _prod_insert_params(conn.statements)
        assert len(prod_rows) == 1, (
            f"Expected exactly 1 production INSERT for targets={targets}, "
            f"got {len(prod_rows)}"
        )
        row = prod_rows[0]

        suppression_state = _json.loads(row["suppression_state"])
        assert "coverage_quality" in suppression_state, (
            f"suppression_state is missing 'coverage_quality' for targets="
            f"{targets} — coverage_quality=None was passed to _build_row "
            f"(mutation i: the note was dropped, not computed)"
        )
        actual_target_count = suppression_state["coverage_quality"]["target_count"]
        assert actual_target_count == len(targets), (
            f"coverage_quality.target_count={actual_target_count} for "
            f"targets={targets} (expected {len(targets)}) — the note does "
            f"not reflect the actual fetch; a hardcoded/stale value is "
            f"being used (mutation ii)"
        )


# ===========================================================================
# AC8 — Decade-slice structure
# ===========================================================================


def test_decade_slices_count():
    """AC8: exactly 10 decade slices."""
    slices = build_decade_slices()
    assert len(slices) == DECADE_COUNT == 10


def test_decade_slices_cover_century():
    """AC8: slices span from BIRTH_JD to BIRTH_JD + 100 years."""
    slices = build_decade_slices()
    assert slices[0].year_start == 1984
    assert slices[-1].year_end == 2084


def test_decade_slices_contiguous():
    """AC8: each slice's end_jd is the next slice's start_jd."""
    slices = build_decade_slices()
    for i in range(len(slices) - 1):
        assert abs(slices[i].end_jd - slices[i + 1].start_jd) < 1.0, (
            f"Slice {i} end_jd ({slices[i].end_jd}) != "
            f"slice {i+1} start_jd ({slices[i+1].start_jd})"
        )


def test_era_slice_key_format():
    """AC8: era_slice_key format is 'g3_{year_start}_{year_end}'."""
    slices = build_decade_slices()
    for decade in slices:
        expected_key = f"g3_{decade.year_start}_{decade.year_end}"
        assert decade.era_slice_key == expected_key, (
            f"era_slice_key mismatch: got {decade.era_slice_key!r}, "
            f"expected {expected_key!r}"
        )


def test_era_slice_key_first_is_g3_1984_1994():
    """AC8: first slice is g3_1984_1994."""
    slices = build_decade_slices()
    assert slices[0].era_slice_key == "g3_1984_1994"


def test_era_slice_key_last_is_g3_2074_2084():
    """AC8: last slice is g3_2074_2084."""
    slices = build_decade_slices()
    assert slices[-1].era_slice_key == "g3_2074_2084"


def test_decade_slices_birth_jd():
    """AC8: first slice starts at BIRTH_JD ≈ 2445736.5 (1984-02-05)."""
    slices = build_decade_slices()
    # JD 2445736.5 is the well-known Julian Day for 1984-02-05 00:00 UTC.
    assert abs(slices[0].start_jd - 2445736.5) < 1.0, (
        f"First slice start_jd should be near 2445736.5 (1984-02-05), "
        f"got {slices[0].start_jd}"
    )


# ===========================================================================
# AC8 — Fingerprint computation
# ===========================================================================


def test_fingerprint_is_deterministic():
    """AC8: same inputs always produce the same fingerprint."""
    fp1 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Venus", "Jupiter"]
    )
    fp2 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Venus", "Jupiter"]
    )
    assert fp1 == fp2


def test_fingerprint_is_md5_hex():
    """AC8: fingerprint is a 32-character hex string (MD5)."""
    fp = compute_substep_fingerprint("marriage", "g3_1984_1994", "v3.0", ["Venus"])
    assert len(fp) == 32
    assert all(c in "0123456789abcdef" for c in fp)


def test_fingerprint_target_order_invariant():
    """AC8: target list order does not affect fingerprint (sorted internally)."""
    fp1 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Venus", "Jupiter"]
    )
    fp2 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Jupiter", "Venus"]
    )
    assert fp1 == fp2, "Fingerprint must be target-order invariant"


def test_fingerprint_changes_with_event_class():
    """AC8: different event_class → different fingerprint."""
    fp1 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Venus"]
    )
    fp2 = compute_substep_fingerprint(
        "career_advancement", "g3_1984_1994", "v3.0", ["Venus"]
    )
    assert fp1 != fp2


def test_fingerprint_changes_with_era_slice():
    """AC8: different era_slice_key → different fingerprint."""
    fp1 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Venus"]
    )
    fp2 = compute_substep_fingerprint(
        "marriage", "g3_1994_2004", "v3.0", ["Venus"]
    )
    assert fp1 != fp2


def test_fingerprint_changes_with_engine_version():
    """AC8: different engine_version → different fingerprint."""
    fp1 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Venus"]
    )
    fp2 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.1", ["Venus"]
    )
    assert fp1 != fp2


def test_fingerprint_changes_with_targets():
    """AC8: different resonance targets → different fingerprint."""
    fp1 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Venus"]
    )
    fp2 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Jupiter"]
    )
    assert fp1 != fp2


def test_fingerprint_empty_targets():
    """AC8: empty target list produces a valid (different) fingerprint."""
    fp1 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", []
    )
    fp2 = compute_substep_fingerprint(
        "marriage", "g3_1984_1994", "v3.0", ["Venus"]
    )
    assert isinstance(fp1, str) and len(fp1) == 32
    assert fp1 != fp2


# ===========================================================================
# AC7 — I4: empty resonance targets → honest 0 rows
# ===========================================================================


def test_empty_resonance_targets_returns_0_rows():
    """AC7: run_substep with no resonance targets returns 0 rows honestly."""
    conn = _FakeConn(_responder(targets=()))
    ctx = _ctx(conn)
    writer = GocharaV3CenturyMaterializeWriter()
    step = writer.plan_substeps(ctx)[0]  # first substep
    result = writer.run_substep(ctx, step)
    assert result.rows_inserted == 0
    assert "empty" in result.notes.lower() or "honest" in result.notes.lower()


def test_empty_resonance_targets_writes_nothing_to_db():
    """AC7: no SQL is issued against kala_gochara_windows_v2 for empty targets."""
    conn = _FakeConn(_responder(targets=()))
    ctx = _ctx(conn)
    writer = GocharaV3CenturyMaterializeWriter()
    step = writer.plan_substeps(ctx)[0]
    writer.run_substep(ctx, step)
    writes = [
        (sql, params) for sql, params in conn.statements
        if sql.strip().upper().startswith(("DELETE", "INSERT"))
        and TABLE in sql
    ]
    assert writes == [], (
        f"Writer must not issue DELETE/INSERT against {TABLE} "
        f"when resonance targets are empty (I4). Got: {writes}"
    )


# ===========================================================================
# AC4 — Delta fingerprint: skip on unchanged fingerprint
# ===========================================================================


def test_unchanged_fingerprint_skips_recompute(monkeypatch):
    """AC4: if stored fingerprint == computed fingerprint and rows exist, skip."""
    targets = ["Venus", "Jupiter"]
    # Compute what the fingerprint WILL be for the first substep.
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)
    expected_fp = compute_substep_fingerprint(ec, era_key, ENGINE_VERSION, targets)

    # Responder returns the matching stored fp AND claims rows exist.
    conn = _FakeConn(_responder(targets=targets, stored_fp=expected_fp, rows_exist=True))
    ctx = _ctx(conn)

    # Monkeypatch build_resolution_hierarchy to detect if it was called.
    called = []
    monkeypatch.setattr(
        mod, "build_resolution_hierarchy",
        lambda *a, **k: called.append(1) or _EMPTY_HIERARCHY,
    )

    result = writer.run_substep(ctx, step)

    assert called == [], (
        "build_resolution_hierarchy must NOT be called when fingerprint unchanged"
    )
    assert result.rows_inserted == 0
    assert "skip" in result.notes.lower() or "unchanged" in result.notes.lower()


def test_changed_fingerprint_triggers_recompute(monkeypatch):
    """AC4: if stored fingerprint differs, build_resolution_hierarchy is called."""
    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]

    # Return a STALE fingerprint to force a rebuild.
    conn = _FakeConn(_responder(targets=targets, stored_fp="stale_fingerprint_00000000"))
    ctx = _ctx(conn)

    called = []
    monkeypatch.setattr(
        mod, "build_resolution_hierarchy",
        lambda *a, **k: called.append(1) or _EMPTY_HIERARCHY,
    )
    # R8.12 shape gate: force 'interval' so this substep's class routes
    # through build_resolution_hierarchy (not the point-canonical flat path)
    # — the default discovered class (career_advancement) is 'point' per
    # live schema and would otherwise bypass build_resolution_hierarchy
    # entirely, making this test's monkeypatch a no-op.
    monkeypatch.setattr(mod, "_fetch_event_class_temporal_shape", lambda *a, **k: "interval")
    # Also monkeypatch ClassContext.fetch so it doesn't need a real DB.
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    # Ensure swisseph is importable (patch at module level if needed).
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types
        fake_swe = types.ModuleType("swisseph")
        import sys
        sys.modules["swisseph"] = fake_swe

    result = writer.run_substep(ctx, step)

    assert called == [1], (
        "build_resolution_hierarchy MUST be called when fingerprint changed"
    )


def test_no_stored_fingerprint_triggers_recompute(monkeypatch):
    """AC4: when there is no stored fingerprint, build_resolution_hierarchy is called."""
    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]

    # stored_fp=None → no record exists.
    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    called = []
    monkeypatch.setattr(
        mod, "build_resolution_hierarchy",
        lambda *a, **k: called.append(1) or _EMPTY_HIERARCHY,
    )
    monkeypatch.setattr(mod, "_fetch_event_class_temporal_shape", lambda *a, **k: "interval")
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        fake_swe = types.ModuleType("swisseph")
        sys.modules["swisseph"] = fake_swe

    writer.run_substep(ctx, step)
    assert called == [1]


# ===========================================================================
# AC3 — run_substep materializes correct era_slice_key in rows
# ===========================================================================


def test_run_substep_inserts_correct_era_slice_key(monkeypatch):
    """AC3: rows inserted into kala_gochara_windows_v2 carry the correct era_slice_key."""
    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    # Use the first substep: career_advancement::g3_1984_1994.
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    fake_era_window = WindowResolutionRecord(
        window_id="era-uuid-1",
        parent_window_id=None,
        resolution_tier="era",
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 400.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=0.72,
    )
    fake_hierarchy = HierarchyResult(
        era_windows=[fake_era_window], month_windows=[], day_windows=[],
        resolution_facet={"era": 1, "month": 0, "day": 0},
    )

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(
        mod, "build_resolution_hierarchy",
        lambda *a, **k: fake_hierarchy,
    )
    monkeypatch.setattr(mod, "_fetch_event_class_temporal_shape", lambda *a, **k: "interval")
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        fake_swe = types.ModuleType("swisseph")
        sys.modules["swisseph"] = fake_swe

    result = writer.run_substep(ctx, step)
    assert result.rows_inserted == 1

    # Verify the INSERT SQL carries the expected era_slice_key + resolution.
    inserts = [
        params for sql, params in conn.statements
        if sql.strip().upper().startswith("INSERT INTO KALA_GOCHARA_WINDOWS_V2")
        and isinstance(params, dict)
    ]
    assert len(inserts) == 1, f"Expected 1 INSERT, got {len(inserts)}"
    assert inserts[0]["era_slice_key"] == era_key, (
        f"era_slice_key in INSERT: {inserts[0]['era_slice_key']!r} != {era_key!r}"
    )
    assert inserts[0]["generation"] == GENERATION_V3
    assert inserts[0]["resolution"] == "era", (
        f"PARIṢKĀRA MR-11(b): era-tier window must carry resolution='era', "
        f"got {inserts[0]['resolution']!r}"
    )
    assert inserts[0]["parent_window_id"] is None, (
        "an era-tier window has no coarser parent -- parent_window_id must be None"
    )


def test_run_substep_delete_is_scoped_to_era_slice(monkeypatch):
    """AC3: the DELETE before INSERT is scoped to (chart_id, event_class,
    generation, era_slice_key) — it must not touch other slices."""
    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(mod, "build_resolution_hierarchy", lambda *a, **k: _EMPTY_HIERARCHY)
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")

    writer.run_substep(ctx, step)

    deletes = [
        (sql, params) for sql, params in conn.statements
        if sql.strip().upper().startswith("DELETE")
        and TABLE in sql
    ]
    assert len(deletes) == 1, f"Expected exactly 1 DELETE, got {len(deletes)}"
    _sql, params = deletes[0]
    # params: [chart_id, event_class, generation, era_slice_key]
    assert era_key in params, (
        f"DELETE params must include era_slice_key={era_key!r}, got {params}"
    )
    assert GENERATION_V3 in params, (
        f"DELETE params must include generation={GENERATION_V3!r}, got {params}"
    )


# ===========================================================================
# AC5 — Wall-clock time logged at DEBUG per substep
# ===========================================================================


def test_wall_clock_time_logged_at_debug(monkeypatch, caplog):
    """AC5: DEBUG log message with wall_clock_s appears after each substep."""
    import logging

    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(mod, "build_resolution_hierarchy", lambda *a, **k: _EMPTY_HIERARCHY)
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")

    with caplog.at_level(logging.DEBUG, logger=mod.__name__):
        result = writer.run_substep(ctx, step)

    assert result.duration_seconds >= 0.0

    debug_msgs = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    has_wall_clock = any("wall_clock_s" in m for m in debug_msgs)
    assert has_wall_clock, (
        f"Expected a DEBUG log containing 'wall_clock_s' — AC5. "
        f"Debug messages found: {debug_msgs}"
    )


# ===========================================================================
# FROZEN CONTRACT conformance
# ===========================================================================


def test_writer_is_registered():
    """Writer is discoverable via the registry."""
    from pipeline.orchestrator.writers import get_writer
    assert get_writer(ASSET_ID) is not None


def test_asset_id_matches_registration():
    assert GocharaV3CenturyMaterializeWriter.asset_id == ASSET_ID


def test_declares_heavy_writer():
    assert GocharaV3CenturyMaterializeWriter.has_substeps is True


def test_writer_never_calls_commit_or_rollback(monkeypatch):
    """§N.2: writer must not call commit/rollback/close."""
    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(mod, "build_resolution_hierarchy", lambda *a, **k: _EMPTY_HIERARCHY)
    monkeypatch.setattr(mod, "_fetch_event_class_temporal_shape", lambda *a, **k: "interval")
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")

    # If commit/rollback/close are called, _FakeConn raises AssertionError.
    result = writer.run_substep(ctx, step)
    assert result.rows_inserted == 0  # no rows (build_resolution_hierarchy returns empty)


def test_generation_constant():
    """generation label is 'g3_utkarsha'."""
    assert GENERATION_V3 == "g3_utkarsha"


def test_event_classes_constant():
    """The original 6 W3.4 event classes plus MR-12's business_launch
    addition (the first genuinely chain-canonical class this writer
    produces rows for — see ka_gochara_v3_century_materialize.py's
    _SHAPE_FALLBACK docstring for why business_launch, not marriage)."""
    expected = {
        "career_advancement",
        "major_gain",
        "marriage",
        "illness_acute",
        "chronic_onset",
        "surgery",
        "business_launch",
    }
    assert set(EVENT_CLASSES) == expected


def test_table_constant_is_v2():
    """Calibration/staging surface (TABLE) is kala_gochara_windows_v2."""
    assert TABLE == "kala_gochara_windows_v2"

def test_prod_table_constant():
    """W5.4 repoint: production surface (PROD_TABLE) is kala_gochara_windows."""
    assert PROD_TABLE == "kala_gochara_windows"

def test_generation_prod_constant():
    """W5.4 repoint: production generation label is '3.0'."""
    assert GENERATION_PROD == "3.0"


# ===========================================================================
# PARIṢKĀRA MR-11(b) — hierarchy wiring (era⊃month⊃day, parent_window_id,
# resolution). Written for the previously-unwired W3.3 resolution_hierarchy
# code, now called from run_substep via build_resolution_hierarchy.
# ===========================================================================


def test_engine_version_is_v3_1():
    """Codex C2: this lane changes writer OUTPUT SHAPE (hierarchy rows
    replace flat interval rows) -> ENGINE_VERSION must be bumped to the
    exact string 'v3.1' (concurrent PARIṢKĀRA lanes make the identical
    edit so git auto-merges)."""
    assert ENGINE_VERSION == "v3.1"


def _returning_id_responder(
    *, targets=("Venus",), stored_fp=None, rows_exist=False,
    discovered_classes: list[str] | None = None,
):
    """Like _responder, but INSERT ... RETURNING id statements get an
    incrementing fake bigint id back — the mechanism run_substep needs to
    resolve parent_window_id for child hierarchy rows.

    MR-16 compatibility: also answers the dynamic event-class discovery
    query (DISTINCT event_class, no target_ref) — without this, plan_substeps
    sees an empty resonance map and returns a 0-substep plan (I4), which
    would make every caller's `steps[0]` raise IndexError."""
    classes = _DEFAULT_DISCOVERED_CLASSES if discovered_classes is None else discovered_classes
    counter = {"n": 0}

    def responder(sql: str, params=None) -> list[dict]:
        s = sql.lower()
        if "gochara_resonance_map" in s and "distinct" in s and "event_class" in s and "target_ref" not in s:
            return [{"event_class": ec} for ec in classes]
        if "gochara_resonance_map" in s and "target_ref" in s:
            return [{"target_ref": t} for t in targets]
        if BUILD_STATE_TABLE in s and sql.strip().upper().startswith("SELECT"):
            if stored_fp is None:
                return []
            return [{"class_fingerprint": stored_fp}]
        if TABLE in s and "limit 1" in s:
            return [{"1": 1}] if rows_exist else []
        if sql.strip().upper().startswith("INSERT") and "RETURNING ID" in sql.upper():
            counter["n"] += 1
            return [{"id": counter["n"]}]
        return []

    return responder


def _run_hierarchy_substep(monkeypatch, hierarchy: HierarchyResult):
    """Shared setup: run the first substep with `hierarchy` as the mocked
    build_resolution_hierarchy result, using the RETURNING-id-aware
    responder. Returns (writer_result, conn)."""
    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_returning_id_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]

    conn = _FakeConn(_returning_id_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(mod, "build_resolution_hierarchy", lambda *a, **k: hierarchy)
    # R8.12 shape gate: force 'interval' so the default discovered class
    # (career_advancement, 'point' per live schema) still routes through
    # build_resolution_hierarchy for these hierarchy-focused tests.
    monkeypatch.setattr(mod, "_fetch_event_class_temporal_shape", lambda *a, **k: "interval")
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")

    result = writer.run_substep(ctx, step)
    return result, conn


def _v2_inserts(conn):
    return [
        params for sql, params in conn.statements
        if sql.strip().upper().startswith("INSERT INTO KALA_GOCHARA_WINDOWS_V2")
        and isinstance(params, dict)
    ]


def _prod_inserts(conn):
    # PROD_TABLE ('kala_gochara_windows') must NOT match the _v2 table --
    # anchor on the table name being immediately followed by whitespace.
    return [
        params for sql, params in conn.statements
        if re.match(r"INSERT INTO KALA_GOCHARA_WINDOWS\s", sql.strip().upper())
        and isinstance(params, dict)
    ]


def test_era_month_day_all_three_resolutions_persisted(monkeypatch):
    """A hierarchy with one window at each tier produces 3 v2 + 3 prod rows,
    each carrying its own resolution_tier as the `resolution` column."""
    era = WindowResolutionRecord(
        window_id="era-1", parent_window_id=None, resolution_tier="era",
        enter_jd=2445736.5, exit_jd=2445736.5 + 500.0,
        peak_jd=2445736.5 + 100.0, peak_lambda=0.9,
    )
    month = WindowResolutionRecord(
        window_id="month-1", parent_window_id="era-1", resolution_tier="month",
        enter_jd=2445736.5 + 10.0, exit_jd=2445736.5 + 40.0,
        peak_jd=2445736.5 + 25.0, peak_lambda=0.8,
    )
    day = WindowResolutionRecord(
        window_id="day-1", parent_window_id="month-1", resolution_tier="day",
        enter_jd=2445736.5 + 15.0, exit_jd=2445736.5 + 16.0,
        peak_jd=2445736.5 + 15.5, peak_lambda=0.75,
    )
    hierarchy = HierarchyResult(
        era_windows=[era], month_windows=[month], day_windows=[day],
        resolution_facet={"era": 1, "month": 1, "day": 1},
    )

    result, conn = _run_hierarchy_substep(monkeypatch, hierarchy)

    assert result.rows_inserted == 3
    v2_rows = _v2_inserts(conn)
    assert len(v2_rows) == 3
    resolutions = [r["resolution"] for r in v2_rows]
    assert resolutions == ["era", "month", "day"], (
        "hierarchy rows must be inserted parent-tier-first: era, then month, then day"
    )


def test_parent_window_id_resolved_to_db_assigned_bigint(monkeypatch):
    """A month window's parent_window_id (in BOTH kala_gochara_windows_v2
    and kala_gochara_windows) must resolve to the DB-assigned bigint `id`
    the era row received on its own INSERT ... RETURNING id -- never the
    hierarchy's internal UUID window_id, and never fabricated."""
    era = WindowResolutionRecord(
        window_id="era-uuid", parent_window_id=None, resolution_tier="era",
        enter_jd=2445736.5, exit_jd=2445736.5 + 500.0,
        peak_jd=2445736.5 + 100.0, peak_lambda=0.9,
    )
    month = WindowResolutionRecord(
        window_id="month-uuid", parent_window_id="era-uuid", resolution_tier="month",
        enter_jd=2445736.5 + 10.0, exit_jd=2445736.5 + 40.0,
        peak_jd=2445736.5 + 25.0, peak_lambda=0.8,
    )
    hierarchy = HierarchyResult(
        era_windows=[era], month_windows=[month], day_windows=[],
        resolution_facet={"era": 1, "month": 1, "day": 0},
    )

    result, conn = _run_hierarchy_substep(monkeypatch, hierarchy)

    v2_rows = _v2_inserts(conn)
    prod_rows = _prod_inserts(conn)
    assert len(v2_rows) == 2 and len(prod_rows) == 2

    era_v2, month_v2 = v2_rows[0], v2_rows[1]
    era_prod, month_prod = prod_rows[0], prod_rows[1]

    # The era row (no parent) carries parent_window_id=None on both tables.
    assert era_v2["parent_window_id"] is None
    assert era_prod["parent_window_id"] is None

    # The month row's parent_window_id must be an int (the RETURNING id from
    # the era row's own INSERT into the SAME table) -- never the string UUID
    # "era-uuid" the hierarchy used internally.
    assert isinstance(month_v2["parent_window_id"], int), (
        f"expected a resolved bigint id, got {month_v2['parent_window_id']!r}"
    )
    assert isinstance(month_prod["parent_window_id"], int), (
        f"expected a resolved bigint id, got {month_prod['parent_window_id']!r}"
    )
    # v2 and prod tables have INDEPENDENT id sequences in production -- the
    # writer must not cross-wire a v2-table id into the prod-table row (or
    # vice versa). With the fake responder's shared counter, era_v2 gets id=1
    # (first INSERT...RETURNING id call) and era_prod gets id=2 (second) --
    # month_v2's parent must equal era_v2's OWN id, month_prod's parent must
    # equal era_prod's OWN id.
    assert month_v2["parent_window_id"] != month_prod["parent_window_id"], (
        "v2-table and prod-table parent linkage must be resolved independently "
        "(separate id sequences) -- they must not collapse to the same id here"
    )


def test_dry_run_reports_hierarchy_tier_counts_and_writes_nothing(monkeypatch):
    """dry_run=True must report era/month/day counts and issue zero writes."""
    era = WindowResolutionRecord(
        window_id="era-1", parent_window_id=None, resolution_tier="era",
        enter_jd=2445736.5, exit_jd=2445736.5 + 500.0,
        peak_jd=2445736.5 + 100.0, peak_lambda=0.9,
    )
    hierarchy = HierarchyResult(
        era_windows=[era], month_windows=[], day_windows=[],
        resolution_facet={"era": 1, "month": 0, "day": 0},
    )

    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_returning_id_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]

    conn = _FakeConn(_returning_id_responder(targets=targets, stored_fp=None))
    ctx = ContextSpec(
        asset_id=ASSET_ID, build_id="test-build-w34", db_conn=conn,
        config={"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"},
        dry_run=True,
    )

    monkeypatch.setattr(mod, "build_resolution_hierarchy", lambda *a, **k: hierarchy)
    monkeypatch.setattr(mod, "_fetch_event_class_temporal_shape", lambda *a, **k: "interval")
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")

    result = writer.run_substep(ctx, step)

    assert result.rows_inserted == 0
    assert "era=1" in result.notes and "month=0" in result.notes and "day=0" in result.notes
    writes = [
        (sql, params) for sql, params in conn.statements
        if sql.strip().upper().startswith(("DELETE", "INSERT"))
    ]
    assert writes == [], f"dry_run must issue zero DELETE/INSERT, got: {writes}"


# ===========================================================================
# PK-R-8 R8.8 — peak_basis vocabulary: named constants, never a literal
# ===========================================================================


def test_peak_basis_vocab_used_not_literal():
    """R8.8 source guard: the writer's source must never assign the retired
    bare literal (the exact `"peak_basis": "gochara_lambda...` dict-literal
    shape the pre-R8.8 code used) -- this pattern does not appear anywhere in
    the file, including its own prose, since the writer's docstrings refer to
    the retired name in single-quoted prose form only ('gochara_lambda_v3'),
    never as a peak_basis dict-literal assignment. And the writer must
    reference the named vocab constants for both bases it emits."""
    src = inspect.getsource(mod)

    assert '"peak_basis": "gochara_lambda' not in src, (
        "R8.8 VIOLATION: a bare peak_basis dict-literal string was found in "
        "the writer's source -- must use peak_basis_vocab constants."
    )
    assert "peak_basis_vocab" in src
    assert "peak_basis_vocab.LAMBDA_V3_ARGMAX" in src
    assert "peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX" in src


def test_ontology_milestone_offset_not_in_genuine_peak_bases():
    """PK-R-8a (2026-08-11, ADJUDICATOR ruling, chain-basis question)
    detector: ONTOLOGY_MILESTONE_OFFSET names a DECLARED date (episode_
    anchor_jd + milestone_template[i].typical_offset_days), never a LOCATED
    peak -- it must never join GENUINE_PEAK_BASES (that set stays exactly
    {LAMBDA_V3_ARGMAX} and means "a located extremum"), and the writer must
    reference the constant (not a bare literal) for its chain rows."""
    assert mod.peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET not in mod.peak_basis_vocab.GENUINE_PEAK_BASES, (
        "PK-R-8a VIOLATION: ONTOLOGY_MILESTONE_OFFSET must never be admitted "
        "into GENUINE_PEAK_BASES -- a declared date is not a located peak."
    )
    assert mod.peak_basis_vocab.GENUINE_PEAK_BASES == frozenset({mod.peak_basis_vocab.LAMBDA_V3_ARGMAX}), (
        "GENUINE_PEAK_BASES drifted from its PK-R-8/PK-R-8a-ruled single member."
    )
    assert mod.peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET in mod.peak_basis_vocab.ALL_BASES

    vocab_src = inspect.getsource(mod.peak_basis_vocab)
    assert "PK-R-8a" in vocab_src, (
        "peak_basis_vocab.py must cite PK-R-8a as the ruling source for "
        "ONTOLOGY_MILESTONE_OFFSET (recorded-evidence discipline, R8.9's "
        "own 'a future lane that wants to add a basis here must cite the "
        "evidence' convention)."
    )

    writer_src = inspect.getsource(mod)
    assert "peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET" in writer_src, (
        "PK-R-8a VIOLATION: the writer must reference the named "
        "ONTOLOGY_MILESTONE_OFFSET constant for chain rows, never a bare "
        "string literal."
    )


def test_build_row_requires_peak_basis_kwarg():
    """_build_row must not have a default for peak_basis -- every caller is
    forced to supply an honestly-derived value (no silent fallback to a
    retired/wrong basis)."""
    sig = inspect.signature(mod._build_row)
    assert sig.parameters["peak_basis"].default is inspect.Parameter.empty


def test_no_midpoint_basis_emitted(monkeypatch):
    """Every row this writer inserts must carry a peak_basis from {ARGMAX,
    COARSE_ARGMAX} -- LAMBDA_V3_MIDPOINT (defined for documentation only,
    R8.8) must never appear on an emitted row."""
    era = WindowResolutionRecord(
        window_id="era-1", parent_window_id=None, resolution_tier="era",
        enter_jd=2445736.5, exit_jd=2445736.5 + 500.0,
        peak_jd=2445736.5 + 100.0, peak_lambda=0.9,
    )
    month = WindowResolutionRecord(
        window_id="month-1", parent_window_id="era-1", resolution_tier="month",
        enter_jd=2445736.5 + 10.0, exit_jd=2445736.5 + 40.0,
        peak_jd=2445736.5 + 25.0, peak_lambda=0.8,
    )
    day = WindowResolutionRecord(
        window_id="day-1", parent_window_id="month-1", resolution_tier="day",
        enter_jd=2445736.5 + 15.0, exit_jd=2445736.5 + 16.0,
        peak_jd=2445736.5 + 15.5, peak_lambda=0.75,
    )
    hierarchy = HierarchyResult(
        era_windows=[era], month_windows=[month], day_windows=[day],
        resolution_facet={"era": 1, "month": 1, "day": 1},
    )
    result, conn = _run_hierarchy_substep(monkeypatch, hierarchy)

    v2_rows = _v2_inserts(conn)
    assert len(v2_rows) == 3
    for row in v2_rows:
        assert row["peak_basis"] != mod.peak_basis_vocab.LAMBDA_V3_MIDPOINT, (
            f"R8.8 VIOLATION: row carries the prohibited midpoint basis: {row}"
        )
        assert row["peak_basis"] in (
            mod.peak_basis_vocab.LAMBDA_V3_ARGMAX,
            mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
        )


def test_era_rows_carry_coarse_label_month_day_carry_argmax(monkeypatch):
    """Era-tier rows are stamped LAMBDA_V3_COARSE_ARGMAX (the era peak is a
    50-sample coarse dense scan, not day-precision); month/day-tier rows are
    stamped LAMBDA_V3_ARGMAX (the day-refined true argmax, R8.5). A writer
    that stamped ARGMAX on an era row would over-claim day-precision on a
    row whose peak was never day-refined -- this is exactly what this test
    would catch (mutate the era branch to LAMBDA_V3_ARGMAX -> RED)."""
    era = WindowResolutionRecord(
        window_id="era-1", parent_window_id=None, resolution_tier="era",
        enter_jd=2445736.5, exit_jd=2445736.5 + 500.0,
        peak_jd=2445736.5 + 100.0, peak_lambda=0.9,
    )
    month = WindowResolutionRecord(
        window_id="month-1", parent_window_id="era-1", resolution_tier="month",
        enter_jd=2445736.5 + 10.0, exit_jd=2445736.5 + 40.0,
        peak_jd=2445736.5 + 25.0, peak_lambda=0.8,
    )
    hierarchy = HierarchyResult(
        era_windows=[era], month_windows=[month], day_windows=[],
        resolution_facet={"era": 1, "month": 1, "day": 0},
    )
    result, conn = _run_hierarchy_substep(monkeypatch, hierarchy)

    v2_rows = _v2_inserts(conn)
    era_row = next(r for r in v2_rows if r["resolution"] == "era")
    month_row = next(r for r in v2_rows if r["resolution"] == "month")

    assert era_row["peak_basis"] == mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX, (
        f"R8.8 VIOLATION: era row must carry LAMBDA_V3_COARSE_ARGMAX, got {era_row['peak_basis']!r}"
    )
    assert month_row["peak_basis"] == mod.peak_basis_vocab.LAMBDA_V3_ARGMAX, (
        f"R8.8 VIOLATION: month row must carry LAMBDA_V3_ARGMAX, got {month_row['peak_basis']!r}"
    )


def test_shape_gated_flat_rows_carry_coarse_label_and_null_resolution(monkeypatch):
    """R8.12 shape-gated flat production (point-canonical classes): rows
    carry resolution=NULL and peak_basis=LAMBDA_V3_COARSE_ARGMAX (the
    IntervalBoundary peak is interval_solver's own 50-sample coarse scan,
    never day-refined)."""
    from services.gochara_v3.interval_solver import IntervalBoundary

    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]  # career_advancement -- 'point' per live schema
    ec, era_key = step.key.split("::", 1)

    fake_boundary = IntervalBoundary(
        enter_jd=2445736.5 + 10.0, exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0, peak_lambda=0.72, era_slice_key=era_key,
    )

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)
    # No _fetch_event_class_temporal_shape override -- default responder
    # answers nothing for brahma_event_ontology, so the writer's own
    # conservative fallback ('point') applies, matching career_advancement's
    # real live-schema shape.
    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")

    writer.run_substep(ctx, step)

    v2_rows = _v2_inserts(conn)
    assert len(v2_rows) == 1
    assert v2_rows[0]["resolution"] is None
    assert v2_rows[0]["parent_window_id"] is None
    assert v2_rows[0]["peak_basis"] == mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX


# ===========================================================================
# MR-42 — truthful suppression_state (PK-R-5, 2026-08-11)
# ===========================================================================
#
# GAP: `_build_row` used to write `"suppression_state": json.dumps({})`
# unconditionally on every interval row -- no computation behind it, a
# reader could not distinguish "nothing fired" from "nothing was asked",
# even though the real v3 suppression detail (quality_gates) was already
# computed and sitting in `boundary.term_breakdown['quality_gates']` a few
# lines away. Fix: `_build_suppression_state` forwards that real value into
# a structured `{"mechanism": "quality_gates", "value": ..., "note": ...}`
# object -- GATE: post-rebuild interval rows carry a truthful, structured
# suppression_state; a unit test asserts the writer cannot emit the bare {}
# for a computed row.


def test_engine_version_bumped_to_v3_1():
    """MR-42 (Codex C2 convention): ENGINE_VERSION bumped v3.0 -> v3.1
    because this writer's OUTPUT SHAPE changed (suppression_state is no
    longer an unconditional {}) -- every stored fingerprint must invalidate
    under the new engine version rather than being silently skipped as
    'unchanged' by the fingerprint check."""
    assert ENGINE_VERSION == "v3.1"


def test_build_suppression_state_never_bare_empty_dict_for_a_computed_row():
    """THE core MR-42 regression guard: for ANY term_breakdown a computed
    row could plausibly carry (quality_gates present at any value,
    including the 'nothing fired' 1.0 case, or even a term_breakdown that
    is missing the quality_gates key entirely), `_build_suppression_state`
    must never return a bare `{}` -- it always names the mechanism."""
    from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
        _build_suppression_state,
    )

    computed_term_breakdowns = [
        {"promise": 0.8, "permission": 0.6, "activity": 0.5, "quality_gates": 1.0,
         "lambda_v3": 0.24, "activity_terms": [], "formula": "x"},
        {"promise": 0.8, "permission": 0.6, "activity": 0.5, "quality_gates": 0.15,
         "lambda_v3": 0.036, "activity_terms": [{"a": 1}], "formula": "x"},
        {"promise": 0.0, "permission": 0.0, "activity": 0.0},  # honest degrade: no quality_gates key
        {},  # pathological empty-but-not-None term_breakdown
    ]
    for tb in computed_term_breakdowns:
        state = _build_suppression_state(tb)
        assert state != {}, f"_build_suppression_state must never return bare {{}} for a computed row, got {{}} for input {tb!r}"
        assert state.get("mechanism") == "quality_gates"
        assert "value" in state

    # I4 honest-degrade case (peak evaluation failed, term_breakdown is None
    # itself, not merely missing a key) -- STILL not a bare {}: the reader
    # can tell "we tried and couldn't" (value=None + note) apart from
    # "we checked, nothing fired" (value=1.0).
    degraded_state = _build_suppression_state(None)
    assert degraded_state != {}
    assert degraded_state["mechanism"] == "quality_gates"
    assert degraded_state["value"] is None
    assert "note" in degraded_state and degraded_state["note"]


def test_build_suppression_state_forwards_real_quality_gates_value():
    """The forwarded value is the REAL quality_gates figure already computed
    by the engine (via term_breakdown), not a re-derived or fabricated one."""
    from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
        _build_suppression_state,
    )

    tb = {"promise": 0.9, "permission": 0.7, "activity": 0.6, "quality_gates": 0.42,
          "lambda_v3": 0.2268, "activity_terms": [], "formula": "PROMISE x PERMISSION x activity x quality_gates"}
    state = _build_suppression_state(tb)
    assert state["value"] == 0.42


def test_build_row_writes_structured_suppression_state_not_bare_empty_dict():
    """`_build_row` (the actual row-construction function every INSERT goes
    through) must serialize a structured suppression_state, sourced from
    `term_breakdown`, never the old bare `json.dumps({})`."""
    import json as _json
    from services.gochara_v3.interval_solver import IntervalBoundary
    from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import _build_row

    boundary = IntervalBoundary(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=0.55,
        era_slice_key="g3_1984_1994",
        term_breakdown={
            "promise": 0.8, "permission": 0.6, "activity": 0.5, "quality_gates": 0.72,
            "lambda_v3": 0.55, "activity_terms": [], "formula": "x",
        },
    )
    row = _build_row(
        "482012f1-710e-4a25-994a-93821f5871aa", "career_advancement", boundary,
        "g3_1984_1994", valence="gain", is_adverse=False,
        peak_basis=mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
        term_breakdown=boundary.term_breakdown,
        shape_conformance=SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    )
    decoded = _json.loads(row["suppression_state"])
    assert decoded != {}
    assert decoded["mechanism"] == "quality_gates"
    assert decoded["value"] == 0.72


def test_run_substep_inserted_rows_carry_truthful_suppression_state(monkeypatch):
    """End-to-end (writer-level) proof: a real `run_substep` call, with a
    fake `find_threshold_crossings` returning a boundary that carries a
    computed `term_breakdown`, must produce INSERT statements (both the
    calibration/staging v2 row and the production row) whose
    `suppression_state` param decodes to a structured, non-empty object --
    never the pre-MR-42 bare `{}`."""
    import json as _json
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
        peak_lambda=0.61,
        era_slice_key=era_key,
        term_breakdown={
            "promise": 0.9, "permission": 0.5, "activity": 0.7, "quality_gates": 0.85,
            "lambda_v3": 0.61, "activity_terms": [], "formula": "x",
        },
    )

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")

    result = writer.run_substep(ctx, step)
    # NOTE: rows_inserted only counts the v2 (calibration/staging) insert
    # loop's success counter (see `inserted += 1` in run_substep) -- the
    # prod-table insert is a second, separately-tried statement that does
    # not increment this same counter. Both INSERTs still land (asserted
    # below via conn.statements), this assertion just pins the counter's
    # own documented scope rather than assuming it double-counts.
    assert result.rows_inserted == 1

    inserts = [
        params for sql, params in conn.statements
        if sql.strip().upper().startswith("INSERT INTO")
        and isinstance(params, dict) and "suppression_state" in params
    ]
    assert len(inserts) == 2, f"Expected 2 INSERTs (v2 + prod) carrying suppression_state, got {len(inserts)}"
    for params in inserts:
        decoded = _json.loads(params["suppression_state"])
        assert decoded != {}, f"suppression_state must never be bare {{}} for a computed row, got {params['suppression_state']!r}"
        assert decoded["mechanism"] == "quality_gates"
        assert decoded["value"] == 0.85
# ===========================================================================
# PK-R-8 R8.12 — shape gate: no hierarchy for point-canonical classes
# ===========================================================================


def test_no_hierarchy_for_point_canonical_classes(monkeypatch):
    """R8.12 detector: running the writer for a point-canonical class
    (marriage -- confirmed 'point' in live brahma_event_ontology schema)
    must produce ZERO rows with a non-null resolution column, regardless of
    how many find_threshold_crossings intervals are found. Removing the
    shape gate (routing marriage through build_resolution_hierarchy like an
    interval-shaped class) would turn this RED."""
    from services.gochara_v3.interval_solver import IntervalBoundary

    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets, discovered_classes=["marriage"]))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = next(s for s in steps if s.key.startswith("marriage::"))
    ec, era_key = step.key.split("::", 1)

    fake_boundaries = [
        IntervalBoundary(
            enter_jd=2445736.5 + 10.0, exit_jd=2445736.5 + 20.0,
            peak_jd=2445736.5 + 15.0, peak_lambda=0.72, era_slice_key=era_key,
        ),
        IntervalBoundary(
            enter_jd=2445736.5 + 100.0, exit_jd=2445736.5 + 900.0,
            peak_jd=2445736.5 + 500.0, peak_lambda=0.81, era_slice_key=era_key,
        ),
    ]

    conn = _FakeConn(_responder(targets=targets, stored_fp=None, discovered_classes=["marriage"]))
    ctx = _ctx(conn)
    # No shape override -- 'marriage' falls to the writer's own conservative
    # default ('point'), which happens to match its real live-schema shape.
    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: fake_boundaries)
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")

    result = writer.run_substep(ctx, step)
    assert result.rows_inserted == 2

    v2_rows = _v2_inserts(conn)
    assert len(v2_rows) == 2
    for row in v2_rows:
        assert row["resolution"] is None, (
            f"R8.12 VIOLATION: point-canonical class produced a row with "
            f"resolution={row['resolution']!r} -- hierarchy tiers must never "
            f"be produced for a point-canonical class."
        )


# ===========================================================================
# PARĪKṢAKA F-3 (2026-08-11) — R8.13 peak-accounting has a real detector
# ===========================================================================
#
# GAP: R8.13 requires WriterResult.notes to carry the full production
# peak-accounting string (era_windows/peaks_scanned/peaks_admitted/
# peaks_retained/month_rows/day_rows) plus a NAMED zero_peaks_reason
# whenever peaks_retained==0 -- but before this fix, nothing in the test
# suite actually parsed `result.notes` and asserted on those fields, and
# ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90 / ZERO_PEAKS_ERA_WINDOW_TOO_SHORT were
# asserted NOWHERE (only ZERO_PEAKS_FLAT_LAMBDA_CURVE's sibling constant
# existed in the module, with no test exercising either of these two
# specifically). Fixed: three tests below (a) pin every one of R8.13's six
# named fields in `notes` from HierarchyResult counters that are DELIBERATELY
# distinct from list lengths (so a `notes` string built from re-deriving
# len(...) rather than the real counters would still be caught wrong), and
# (b) exercise the two previously-unasserted zero_peaks_reason causes with
# separate, distinct test cases.

from services.gochara_v3.resolution_hierarchy import (  # noqa: E402
    EraWindowAccounting,
    ZERO_PEAKS_ERA_WINDOW_TOO_SHORT,
    ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90,
)


def test_writer_notes_carry_full_r813_peak_accounting_string(monkeypatch):
    """R8.13 detector: WriterResult.notes must report era_windows,
    peaks_scanned, peaks_admitted, peaks_retained, month_rows, day_rows as
    explicit `key=value` substrings, sourced from HierarchyResult's own
    counters (NOT re-derived from len(month_windows)/len(day_windows) alone
    -- peaks_scanned/peaks_admitted have no corresponding list length at
    all, so a notes string that omitted them would still show 1 era /
    1 month / 1 day but silently drop the scan-funnel accounting)."""
    era = WindowResolutionRecord(
        window_id="era-1", parent_window_id=None, resolution_tier="era",
        enter_jd=2445736.5, exit_jd=2445736.5 + 500.0,
        peak_jd=2445736.5 + 100.0, peak_lambda=0.9,
    )
    month = WindowResolutionRecord(
        window_id="month-1", parent_window_id="era-1", resolution_tier="month",
        enter_jd=2445736.5 + 10.0, exit_jd=2445736.5 + 40.0,
        peak_jd=2445736.5 + 25.0, peak_lambda=0.8,
    )
    day = WindowResolutionRecord(
        window_id="day-1", parent_window_id="month-1", resolution_tier="day",
        enter_jd=2445736.5 + 15.0, exit_jd=2445736.5 + 16.0,
        peak_jd=2445736.5 + 15.5, peak_lambda=0.75,
    )
    hierarchy = HierarchyResult(
        era_windows=[era], month_windows=[month], day_windows=[day],
        resolution_facet={"era": 1, "month": 1, "day": 1},
        # Deliberately distinct from the 1/1/1 list lengths above, so the
        # test can tell "notes reports the real funnel counters" apart from
        # "notes just re-derived len(...) three times".
        peaks_scanned=7, peaks_admitted=4, peaks_retained=1,
    )

    result, conn = _run_hierarchy_substep(monkeypatch, hierarchy)

    assert "era_windows=1" in result.notes, result.notes
    assert "peaks_scanned=7" in result.notes, result.notes
    assert "peaks_admitted=4" in result.notes, result.notes
    assert "peaks_retained=1" in result.notes, result.notes
    assert "month_rows=1" in result.notes, result.notes
    assert "day_rows=1" in result.notes, result.notes


def test_writer_notes_report_zero_peaks_no_candidate_above_p90(monkeypatch):
    """R8.13 detector: ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90 (candidates were
    found by the local-maxima scan but none cleared the era window's own
    P90 admission threshold) must appear verbatim in WriterResult.notes as
    `zero_peaks_reason=no_candidate_above_p90` -- this exact reason constant
    was asserted NOWHERE in the suite before this fix."""
    era = WindowResolutionRecord(
        window_id="era-1", parent_window_id=None, resolution_tier="era",
        enter_jd=2445736.5, exit_jd=2445736.5 + 500.0,
        peak_jd=2445736.5 + 100.0, peak_lambda=0.9,
    )
    hierarchy = HierarchyResult(
        era_windows=[era], month_windows=[], day_windows=[],
        resolution_facet={"era": 1, "month": 0, "day": 0},
        peaks_scanned=4, peaks_admitted=0, peaks_retained=0,
        zero_peaks_reason=ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90,
    )

    result, conn = _run_hierarchy_substep(monkeypatch, hierarchy)

    assert f"zero_peaks_reason={ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90}" in result.notes, result.notes
    assert "peaks_scanned=4" in result.notes, result.notes
    assert "peaks_admitted=0" in result.notes, result.notes
    assert "peaks_retained=0" in result.notes, result.notes
    assert "month_rows=0" in result.notes, result.notes
    assert "day_rows=0" in result.notes, result.notes


def test_writer_notes_report_zero_peaks_era_window_too_short(monkeypatch):
    """R8.13 detector: ZERO_PEAKS_ERA_WINDOW_TOO_SHORT (the era window's own
    reused coarse-series slice had <3 points -- interior-point local-max
    detection cannot run at all) must appear verbatim in WriterResult.notes
    as `zero_peaks_reason=era_window_too_short` -- this exact reason
    constant, distinct from NO_CANDIDATE_ABOVE_P90 above, was ALSO asserted
    NOWHERE before this fix."""
    era = WindowResolutionRecord(
        window_id="era-1", parent_window_id=None, resolution_tier="era",
        enter_jd=2445736.5, exit_jd=2445736.5 + 500.0,
        peak_jd=2445736.5 + 100.0, peak_lambda=0.9,
    )
    hierarchy = HierarchyResult(
        era_windows=[era], month_windows=[], day_windows=[],
        resolution_facet={"era": 1, "month": 0, "day": 0},
        # peaks_scanned=0 (era window too short to even find candidates) --
        # distinct funnel shape from the NO_CANDIDATE_ABOVE_P90 case above,
        # which scans some candidates but admits none.
        peaks_scanned=0, peaks_admitted=0, peaks_retained=0,
        zero_peaks_reason=ZERO_PEAKS_ERA_WINDOW_TOO_SHORT,
    )

    result, conn = _run_hierarchy_substep(monkeypatch, hierarchy)

    assert f"zero_peaks_reason={ZERO_PEAKS_ERA_WINDOW_TOO_SHORT}" in result.notes, result.notes
    assert "peaks_scanned=0" in result.notes, result.notes
    assert ZERO_PEAKS_ERA_WINDOW_TOO_SHORT != ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90, (
        "fixture sanity: the two zero_peaks_reason constants exercised by "
        "these two tests must actually be distinct strings"
    )
