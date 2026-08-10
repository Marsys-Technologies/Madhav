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
    GENERATION_V3,
    TABLE,
    GocharaV3CenturyMaterializeWriter,
    build_decade_slices,
    compute_substep_fingerprint,
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


def _responder(
    *,
    targets: list[str] = ("Venus",),
    stored_fp: str | None = None,
    rows_exist: bool = False,
):
    """Build a query responder for _FakeConn."""
    def responder(sql: str, params=None) -> list[dict]:
        s = sql.lower()
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


def test_writer_never_references_protected_v1_table():
    """The string 'kala_gochara_windows\\b' (bare v1 table name) must not
    appear in the writer's code (only the _v2 variant is allowed)."""
    source = _module_source_excluding_docstring(mod)
    # \\b is a word boundary: matches "kala_gochara_windows" but NOT
    # "kala_gochara_windows_v2" (no word-boundary between "s" and "_").
    matches = re.findall(r"\bkala_gochara_windows\b", source)
    assert matches == [], (
        f"Writer must not reference bare kala_gochara_windows table "
        f"(found {len(matches)} occurrence(s))"
    )


# ===========================================================================
# AC1 + AC2 — plan_substeps structure and 60-substep century plan
# ===========================================================================


def test_plan_substeps_returns_list_of_substeps():
    """AC1: plan_substeps returns a non-empty list."""
    conn = _FakeConn()  # plan_substeps is static — no DB queries
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    assert isinstance(steps, list)
    assert len(steps) > 0


def test_plan_substeps_each_has_key_and_label():
    """AC1: each SubStep has a non-empty .key and .label."""
    conn = _FakeConn()
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    for step in steps:
        assert hasattr(step, "key"), "SubStep must have .key"
        assert hasattr(step, "label"), "SubStep must have .label"
        assert step.key, f"SubStep.key must be non-empty, got {step.key!r}"
        assert step.label, f"SubStep.label must be non-empty, got {step.label!r}"


def test_plan_substeps_60_total():
    """AC2: exactly 6 event_classes × 10 decade_slices = 60 substeps."""
    conn = _FakeConn()
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    assert len(steps) == 60, (
        f"Expected 60 substeps (6 classes × 10 decades), got {len(steps)}"
    )


def test_plan_substeps_covers_all_event_classes():
    """AC2: every event_class appears in the plan."""
    conn = _FakeConn()
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    keys_found = {s.key.split("::", 1)[0] for s in steps}
    assert keys_found == set(EVENT_CLASSES), (
        f"Missing event classes: {set(EVENT_CLASSES) - keys_found}"
    )


def test_plan_substeps_covers_all_decade_slices():
    """AC2: every decade slice appears in the plan."""
    conn = _FakeConn()
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    era_keys_found = {s.key.split("::", 1)[1] for s in steps if "::" in s.key}
    expected_era_keys = {d.era_slice_key for d in DECADE_SLICES}
    assert era_keys_found == expected_era_keys, (
        f"Missing era slices: {expected_era_keys - era_keys_found}"
    )


def test_plan_substeps_each_class_has_10_decades():
    """AC2: each event class has exactly 10 substeps (one per decade)."""
    conn = _FakeConn()
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    from collections import Counter
    class_counts = Counter(s.key.split("::", 1)[0] for s in steps)
    for ec in EVENT_CLASSES:
        assert class_counts[ec] == 10, (
            f"event_class={ec!r} has {class_counts[ec]} substeps, expected 10"
        )


def test_plan_substeps_no_duplicate_keys():
    """AC2: all substep keys are unique."""
    conn = _FakeConn()
    steps = GocharaV3CenturyMaterializeWriter().plan_substeps(_ctx(conn))
    keys = [s.key for s in steps]
    assert len(keys) == len(set(keys)), "Duplicate substep keys found"


def test_plan_substeps_key_format():
    """AC2: substep_key format is '{event_class}::{era_slice_key}'."""
    conn = _FakeConn()
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

    # Monkeypatch find_threshold_crossings to detect if it was called.
    called = []
    monkeypatch.setattr(
        mod, "find_threshold_crossings",
        lambda *a, **k: called.append(1) or [],
    )

    result = writer.run_substep(ctx, step)

    assert called == [], (
        "find_threshold_crossings must NOT be called when fingerprint unchanged"
    )
    assert result.rows_inserted == 0
    assert "skip" in result.notes.lower() or "unchanged" in result.notes.lower()


def test_changed_fingerprint_triggers_recompute(monkeypatch):
    """AC4: if stored fingerprint differs, find_threshold_crossings is called."""
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
        mod, "find_threshold_crossings",
        lambda *a, **k: called.append(1) or [],
    )
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
        "find_threshold_crossings MUST be called when fingerprint changed"
    )


def test_no_stored_fingerprint_triggers_recompute(monkeypatch):
    """AC4: when there is no stored fingerprint, find_threshold_crossings is called."""
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
    from services.gochara_v3.interval_solver import IntervalBoundary

    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    # Use the first substep: career_advancement::g3_1984_1994.
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

    monkeypatch.setattr(
        mod, "find_threshold_crossings",
        lambda *a, **k: [fake_boundary],
    )
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

    # Verify the INSERT SQL carries the expected era_slice_key.
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


def test_run_substep_delete_is_scoped_to_era_slice(monkeypatch):
    """AC3: the DELETE before INSERT is scoped to (chart_id, event_class,
    generation, era_slice_key) — it must not touch other slices."""
    from services.gochara_v3.interval_solver import IntervalBoundary

    targets = ["Venus"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    conn = _FakeConn(_responder(targets=targets, stored_fp=None))
    ctx = _ctx(conn)

    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [])
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

    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [])
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

    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [])
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
    assert result.rows_inserted == 0  # no rows (find_threshold_crossings returns [])


def test_generation_constant():
    """generation label is 'g3_utkarsha'."""
    assert GENERATION_V3 == "g3_utkarsha"


def test_event_classes_constant():
    """6 expected event classes are defined."""
    expected = {
        "career_advancement",
        "major_gain",
        "marriage",
        "illness_acute",
        "chronic_onset",
        "surgery",
    }
    assert set(EVENT_CLASSES) == expected


def test_table_constant_is_v2():
    """Writer targets kala_gochara_windows_v2, not the protected v1 table."""
    assert TABLE == "kala_gochara_windows_v2"
    assert TABLE != "kala_gochara_windows"
