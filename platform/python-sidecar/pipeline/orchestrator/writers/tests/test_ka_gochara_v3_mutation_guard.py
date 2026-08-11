"""W5.4 mutation-guard for ka_gochara_v3_century_materialize.

GOCHARA-UTKARSA campaign, wave W5.4.

Gate: UTK-R1 ADJUDICATOR ruling + W5.4 writer repoint.

INVARIANT (I1 generation predicate)
------------------------------------
Every DML statement in ka_gochara_v3_century_materialize.py that references
the production table (via the PROD_TABLE variable or the literal table name
'kala_gochara_windows') MUST carry the predicate generation='3.0'. This is
the W5.4 safety rail that prevents the writer from accidentally touching
generation='v1' rows on the two protected charts.

The DB trigger (migration 556, build_protected_assets_guard_row) enforces this
at runtime: a DELETE/UPDATE of a generation='v1' row on a protected chart raises
an exception. The mutation-guard enforces it statically at test time, as a second
independent layer per §N.8 (Earned-Signal Principle).

GUARD DESIGN
------------
The writer uses f-strings with `{PROD_TABLE}` (a variable reference, not the
literal table name) in its DML statements. The static guard therefore searches
for `PROD_TABLE` as a proxy for the table reference in DML context. It then
checks that the same logical statement block also carries generation='3.0'
(either as a literal `generation = '3.0'` predicate or as a reference to
`GENERATION_PROD`).

This design is equivalent to checking the literal table name but is accurate
for the f-string DML pattern the writer uses. The mutation test injects a DML
block containing the literal table name without the generation predicate to
prove the guard is a real detector.

MUTATION TEST DISCIPLINE (§N.8)
--------------------------------
A guard whose test always passes regardless of source content is not a guard —
it is a false signal. This module proves each guard assertion is a REAL DETECTOR
by mutating the writer's apparent source in-memory (via monkeypatch on
inspect.getsource) and verifying the guard FAILS under the mutation.

Three test groups:
  1. `test_*_clean_source`  — guards pass on the actual, unmodified writer source.
  2. `test_*_detects_mutation` — inject a DML without generation='3.0'; guard fires.
  3. Dry-run fixture test — confirms non-protected chart writes only generation='3.0'.

Dry-run fixture test (AC W5.4 acceptance criterion 4)
------------------------------------------------------
`test_dryrun_fixture_only_writes_generation_30_rows` verifies via mock inspection
that for a non-protected fixture chart (UUID not in the protected set) run_substep
produces only generation='3.0' rows on the production table. No real DB used.
"""
from __future__ import annotations

import inspect
import re

import pytest

import pipeline.orchestrator.writers.ka_gochara_v3_century_materialize as mod
from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    ASSET_ID,
    GENERATION_PROD,
    GENERATION_V3,
    PROD_TABLE,
    TABLE,
    GocharaV3CenturyMaterializeWriter,
)
from pipeline.orchestrator.writers import ContextSpec
from services.gochara_v3.resolution_hierarchy import HierarchyResult, WindowResolutionRecord

# PARIṢKĀRA MR-11(b): run_substep now calls build_resolution_hierarchy (not
# find_threshold_crossings directly). This fixture wraps a single
# IntervalBoundary-shaped fake in a one-era-window HierarchyResult, matching
# every downstream generation='3.0'/DML assertion these tests already make
# (an era-tier window is still one row per table, same as the old flat model).
def _single_era_hierarchy(*, enter_jd, exit_jd, peak_jd, peak_lambda) -> HierarchyResult:
    era = WindowResolutionRecord(
        window_id="mutation-guard-era-1",
        parent_window_id=None,
        resolution_tier="era",
        enter_jd=enter_jd,
        exit_jd=exit_jd,
        peak_jd=peak_jd,
        peak_lambda=peak_lambda,
    )
    return HierarchyResult(
        era_windows=[era], month_windows=[], day_windows=[],
        resolution_facet={"era": 1, "month": 0, "day": 0},
    )

# ---------------------------------------------------------------------------
# Guard constants
# ---------------------------------------------------------------------------

# Pattern for the production table referenced by variable name in source.
# The writer uses f-strings: f"DELETE FROM {PROD_TABLE} ..." — so we search
# for the variable name PROD_TABLE as a proxy for the table reference in DML.
PROD_TABLE_VAR_RE = re.compile(r"\bPROD_TABLE\b")

# Pattern for the literal table name (for constant declarations and comments).
PROD_TABLE_LITERAL_RE = re.compile(r"\bkala_gochara_windows\b")

# Pattern for a valid generation='3.0' predicate (SQL literal or variable ref).
# Accepts: generation='3.0'  OR  generation = '3.0'  OR  GENERATION_PROD
GENERATION_30_RE = re.compile(r"generation\s*=\s*'3\.0'|GENERATION_PROD")

# DML verbs that constitute data-modifying statements.
DML_VERB_RE = re.compile(r"\b(DELETE|INSERT|UPDATE)\b", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Source helpers
# ---------------------------------------------------------------------------


def _source_excluding_module_docstring(module) -> str:
    """Return module source with its leading docstring stripped.

    The docstring legitimately names table names for documentation purposes.
    The invariant is about EXECUTABLE code, not documentation.
    """
    source = inspect.getsource(module)
    doc = module.__doc__
    if doc and doc in source:
        return source.replace(doc, "", 1)
    return source


def _extract_prod_table_dml_contexts(source: str) -> list[str]:
    """Extract logical DML contexts from source that reference the production table.

    A 'context' is a run of contiguous non-blank lines that together contain:
      * a DML keyword (DELETE/INSERT/UPDATE), AND
      * a reference to PROD_TABLE (the variable name used in f-strings)

    Returns a list of such context strings. An empty list means no DML contexts
    referencing the production table were found — which should itself trigger an
    assertion failure (the guard has nothing to check, i.e. false-green risk).
    """
    found: list[str] = []
    lines = source.splitlines()
    i = 0
    while i < len(lines):
        # Accumulate a block of non-blank lines.
        block_lines: list[str] = []
        while i < len(lines) and lines[i].strip():
            block_lines.append(lines[i])
            i += 1
        block = "\n".join(block_lines)
        if DML_VERB_RE.search(block) and PROD_TABLE_VAR_RE.search(block):
            found.append(block)
        # Skip blank line(s).
        while i < len(lines) and not lines[i].strip():
            i += 1
    return found


def _assert_all_prod_dml_contexts_carry_generation_30(source: str) -> list[str]:
    """Return DML context blocks that touch PROD_TABLE but lack the generation='3.0' guard.

    Returns violating blocks. Empty return = all clean.
    This IS the guard — calling it on real source and asserting [] is the clean test;
    calling it on mutated source and asserting non-[] proves the guard is real.
    """
    contexts = _extract_prod_table_dml_contexts(source)
    violating: list[str] = []
    for ctx_block in contexts:
        if not GENERATION_30_RE.search(ctx_block):
            violating.append(ctx_block)
    return violating


# ===========================================================================
# Group 1: Guards pass on the actual, unmodified writer source
# ===========================================================================


def test_all_prod_dml_carry_generation_30_on_clean_source():
    """Every DML context touching PROD_TABLE in the writer carries generation='3.0'
    or GENERATION_PROD in the actual, unmodified source.

    If this test fails it is a REAL guard failure in the writer, not a test defect.
    """
    source = _source_excluding_module_docstring(mod)
    violating = _assert_all_prod_dml_contexts_carry_generation_30(source)
    assert violating == [], (
        f"GUARD FAILURE: {len(violating)} DML context(s) referencing PROD_TABLE "
        f"in the writer do NOT carry generation='3.0' or GENERATION_PROD. "
        f"Violating context(s):\n" + "\n---\n".join(violating)
    )


def test_prod_dml_contexts_are_non_empty():
    """The guard has real DML contexts to check — non-vacuous (§N.8).

    If PROD_TABLE_VAR_RE never matches a DML block, the guard's clean-source test
    trivially passes with nothing checked. This test asserts there is at least
    one such context, so the clean-source guard is not vacuously green.
    """
    source = _source_excluding_module_docstring(mod)
    contexts = _extract_prod_table_dml_contexts(source)
    assert len(contexts) >= 1, (
        f"Expected at least one DML context referencing PROD_TABLE in the writer source. "
        f"If the writer has no such context, the guard is vacuous (§N.8). "
        f"Check that the writer uses PROD_TABLE in its DML blocks."
    )


def test_prod_table_constant_is_in_source():
    """PROD_TABLE is declared as 'kala_gochara_windows' in the writer source."""
    source = _source_excluding_module_docstring(mod)
    # The constant declaration: PROD_TABLE = "kala_gochara_windows"
    assert PROD_TABLE_LITERAL_RE.search(source), (
        f"Expected the writer source to contain the literal 'kala_gochara_windows' "
        f"(in the PROD_TABLE constant declaration). "
        f"If this is missing, the writer has no production table reference."
    )


# ===========================================================================
# Group 2: Mutation tests — prove the guard is a real detector (§N.8)
# ===========================================================================


def test_guard_detects_delete_referencing_prod_table_without_generation(monkeypatch):
    """Inject a DELETE referencing PROD_TABLE WITHOUT generation='3.0' into the
    writer's apparent source, and verify the guard catches it.

    This is the §N.8 Earned-Signal Principle applied to the guard itself:
    a test that always passes regardless of source content is not a guard.
    This test proves the guard WOULD fail when the predicate is missing.
    """
    original_source = inspect.getsource(mod)
    # Inject a DELETE block that references PROD_TABLE with no generation predicate.
    # The injected block has a DML verb + PROD_TABLE ref but NO generation='3.0'.
    injected_source = (
        original_source
        + "\n"
        + "# _MUTATION_TEST_MISSING_GENERATION_PREDICATE\n"
        + "_BAD_DML_BLOCK = (\n"
        + "    f'DELETE FROM {PROD_TABLE} WHERE chart_id = %s AND event_class = %s'\n"
        + ")\n"
    )

    monkeypatch.setattr(
        inspect,
        "getsource",
        lambda obj: injected_source if obj is mod else inspect.getsource.__wrapped__(obj),
    )

    source = _source_excluding_module_docstring(mod)
    violating = _assert_all_prod_dml_contexts_carry_generation_30(source)
    assert violating != [], (
        "MUTATION TEST FAILED: the injected DELETE referencing PROD_TABLE "
        "without generation='3.0' was NOT detected by the guard — "
        "the guard is not a real detector (§N.8)."
    )


def test_guard_detects_insert_referencing_prod_table_without_generation(monkeypatch):
    """Inject an INSERT referencing PROD_TABLE WITHOUT generation='3.0' and verify
    the guard catches it."""
    original_source = inspect.getsource(mod)
    injected_source = (
        original_source
        + "\n"
        + "# _MUTATION_TEST_INSERT_MISSING_GENERATION\n"
        + "_BAD_INSERT = (\n"
        + "    f'INSERT INTO {PROD_TABLE} (chart_id, event_class) VALUES (%s, %s)'\n"
        + ")\n"
    )

    monkeypatch.setattr(
        inspect,
        "getsource",
        lambda obj: injected_source if obj is mod else inspect.getsource.__wrapped__(obj),
    )

    source = _source_excluding_module_docstring(mod)
    violating = _assert_all_prod_dml_contexts_carry_generation_30(source)
    assert violating != [], (
        "MUTATION TEST FAILED: the injected INSERT referencing PROD_TABLE "
        "without generation='3.0' was NOT detected by the guard — "
        "the guard is not a real detector (§N.8)."
    )


def test_guard_does_not_flag_correctly_guarded_dml(monkeypatch):
    """Inject a DELETE referencing PROD_TABLE WITH generation='3.0' and verify
    the guard does NOT flag it (a correctly guarded DML is not a violation)."""
    original_source = inspect.getsource(mod)
    injected_source = (
        original_source
        + "\n"
        + "# _MUTATION_TEST_CORRECT_PREDICATE\n"
        + "_GOOD_DELETE = (\n"
        + "    f\"DELETE FROM {PROD_TABLE} WHERE chart_id = %s AND generation='3.0'\"\n"
        + ")\n"
    )

    monkeypatch.setattr(
        inspect,
        "getsource",
        lambda obj: injected_source if obj is mod else inspect.getsource.__wrapped__(obj),
    )

    source = _source_excluding_module_docstring(mod)
    violating = _assert_all_prod_dml_contexts_carry_generation_30(source)
    assert violating == [], (
        "Guard falsely flagged a DML block that correctly carries generation='3.0'. "
        f"Violating blocks (should be empty): {violating}"
    )


def test_guard_does_not_flag_generation_prod_variable(monkeypatch):
    """Inject a DELETE referencing PROD_TABLE with GENERATION_PROD (the variable)
    rather than the literal '3.0' — the guard must accept this form too."""
    original_source = inspect.getsource(mod)
    injected_source = (
        original_source
        + "\n"
        + "# _MUTATION_TEST_GENERATION_PROD_VARIABLE\n"
        + "_GOOD_DELETE_VAR = (\n"
        + "    f'DELETE FROM {PROD_TABLE} WHERE generation = {GENERATION_PROD!r}'\n"
        + ")\n"
        + "_ALSO_VALID = f'DELETE FROM {PROD_TABLE} WHERE x = %s AND GENERATION_PROD'\n"
    )

    monkeypatch.setattr(
        inspect,
        "getsource",
        lambda obj: injected_source if obj is mod else inspect.getsource.__wrapped__(obj),
    )

    source = _source_excluding_module_docstring(mod)
    violating = _assert_all_prod_dml_contexts_carry_generation_30(source)
    assert violating == [], (
        "Guard falsely flagged a DML block using GENERATION_PROD variable. "
        f"Violating blocks (should be empty): {violating}"
    )


# ===========================================================================
# Group 3: Constant correctness
# ===========================================================================


def test_generation_prod_constant_value():
    """GENERATION_PROD must be exactly '3.0' — the UTK-R1 mandated label."""
    assert GENERATION_PROD == "3.0", (
        f"GENERATION_PROD must be '3.0' (UTK-R1), got {GENERATION_PROD!r}"
    )


def test_prod_table_constant_value():
    """PROD_TABLE must be 'kala_gochara_windows' — the UTK-R1 production target."""
    assert PROD_TABLE == "kala_gochara_windows", (
        f"PROD_TABLE must be 'kala_gochara_windows' (UTK-R1), got {PROD_TABLE!r}"
    )


def test_generation_v3_unchanged():
    """GENERATION_V3 (calibration surface) must remain 'g3_utkarsha' (W3.4 spec)."""
    assert GENERATION_V3 == "g3_utkarsha", (
        f"GENERATION_V3 must be 'g3_utkarsha', got {GENERATION_V3!r}"
    )


def test_table_and_prod_table_are_distinct():
    """TABLE (calibration) and PROD_TABLE (production) must be different tables."""
    assert TABLE != PROD_TABLE, (
        f"TABLE ({TABLE!r}) and PROD_TABLE ({PROD_TABLE!r}) must be different. "
        f"The writer dual-writes: calibration to TABLE, production to PROD_TABLE."
    )


# ===========================================================================
# Group 4: Dry-run fixture test (AC W5.4 criterion 4)
# ===========================================================================

# Protected chart IDs — writer must never write generation='v1' for these.
# The fixture test uses a completely different (non-protected) chart.
_PROTECTED_CHART_IDS = {
    "482012f1-710e-4a25-994a-93821f5871aa",  # native (Abhisek Mohanty)
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a",  # Abhinandan
}

# A fixture chart UUID that is NOT in the protected set.
_FIXTURE_CHART_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


class _TrackingCursor:
    """Cursor that records DML and returns empty rows."""

    def __init__(self, owner: "_TrackingConn"):
        self._owner = owner

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._owner._record(sql, params)
        return self

    def fetchall(self):
        return self._owner._rows_for_next

    def fetchone(self):
        rows = self._owner._rows_for_next
        return rows[0] if rows else None


class _TrackingConn:
    """Records every SQL statement. Forbids commit/rollback/close (§N.2)."""

    def __init__(self, responder=None):
        self._responder = responder or (lambda sql, params: [])
        self._rows_for_next: list = []
        self.statements: list[tuple[str, object]] = []

    def _record(self, sql, params):
        self.statements.append((sql, params))
        self._rows_for_next = self._responder(sql, params)

    def cursor(self):
        return _TrackingCursor(self)

    def execute(self, sql, params=None):
        self._record(sql, params)
        return _TrackingCursor(self)

    def commit(self):  # pragma: no cover
        raise AssertionError("writer called commit() — forbidden by §N.2")

    def rollback(self):  # pragma: no cover
        raise AssertionError("writer called rollback() — forbidden by §N.2")

    def close(self):  # pragma: no cover
        raise AssertionError("writer called close() — forbidden by §N.2")


def _make_responder(targets=("Venus",), stored_fp=None, rows_exist=False):
    """Build a query responder for _TrackingConn."""
    def responder(sql: str, params=None):
        s = sql.lower()
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


def _make_ctx(conn, chart_id: str) -> ContextSpec:
    return ContextSpec(
        asset_id=ASSET_ID,
        build_id="test-w54-fixture",
        db_conn=conn,
        config={"chart_id": chart_id},
    )


def test_fixture_chart_is_not_protected():
    """Sanity: the fixture chart UUID is not in the protected set."""
    assert _FIXTURE_CHART_ID not in _PROTECTED_CHART_IDS, (
        f"Fixture chart {_FIXTURE_CHART_ID!r} must not be in the protected set."
    )


def test_dryrun_fixture_only_writes_generation_30_rows(monkeypatch):
    """AC W5.4 criterion 4: for a non-protected fixture chart, all DML issued
    against the production table (kala_gochara_windows) carries generation='3.0'.

    Verifies via mock inspection (no real DB). Asserts:
      1. At least one DML against the production table was issued.
      2. Every such statement carries generation='3.0' (in SQL literal or params).
    """
    era_key = "g3_1984_1994"
    fake_hierarchy = _single_era_hierarchy(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=0.65,
    )

    monkeypatch.setattr(mod, "build_resolution_hierarchy", lambda *a, **k: fake_hierarchy)
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

    conn = _TrackingConn(_make_responder(targets=("Venus",), stored_fp=None))
    ctx = _make_ctx(conn, _FIXTURE_CHART_ID)

    writer = GocharaV3CenturyMaterializeWriter()
    steps = writer.plan_substeps(ctx)
    step = next(s for s in steps if s.key == f"career_advancement::{era_key}")
    result = writer.run_substep(ctx, step)

    # Collect DML statements whose SQL references the production table name
    # (after f-string evaluation at runtime, the SQL contains the literal name).
    prod_dml = [
        (sql, params) for sql, params in conn.statements
        if PROD_TABLE in sql  # runtime-evaluated SQL contains the literal table name
        and sql.strip().upper().startswith(("DELETE", "INSERT", "UPDATE"))
    ]

    assert len(prod_dml) >= 1, (
        f"Expected at least one DML statement against {PROD_TABLE!r} for the "
        f"fixture chart, but found none. All statements: {conn.statements}"
    )

    # Every prod DML must carry generation='3.0'.
    # DELETE: literal `generation = '3.0'` is in the SQL string.
    # INSERT: generation value '3.0' is in the params dict.
    violations: list[tuple[str, object]] = []
    gen_30_sql_re = re.compile(r"generation\s*=\s*'3\.0'")
    for sql, params in prod_dml:
        has_in_sql = bool(gen_30_sql_re.search(sql))
        has_in_params = (
            isinstance(params, dict) and params.get("generation") == GENERATION_PROD
        )
        if not (has_in_sql or has_in_params):
            violations.append((sql, params))

    assert violations == [], (
        f"FIXTURE TEST FAILED: {len(violations)} DML statement(s) against "
        f"{PROD_TABLE!r} do NOT carry generation='3.0'. Violations:\n"
        + "\n---\n".join(f"SQL: {s!r}\nPARAMS: {p!r}" for s, p in violations)
    )


def test_dryrun_fixture_no_generation_v1_rows(monkeypatch):
    """I1 invariant: no DML against the production table ever carries generation='v1'.

    This is the I1 invariant as a runtime test: the writer must never produce
    generation='v1' rows against kala_gochara_windows, regardless of chart ID.
    """
    era_key = "g3_1984_1994"
    fake_hierarchy = _single_era_hierarchy(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=0.65,
    )

    monkeypatch.setattr(mod, "build_resolution_hierarchy", lambda *a, **k: fake_hierarchy)
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

    conn = _TrackingConn(_make_responder(targets=("Venus",), stored_fp=None))
    ctx = _make_ctx(conn, _FIXTURE_CHART_ID)
    writer = GocharaV3CenturyMaterializeWriter()
    steps = writer.plan_substeps(ctx)
    step = next(s for s in steps if s.key == f"career_advancement::{era_key}")
    writer.run_substep(ctx, step)

    # No DML against PROD_TABLE should produce generation='v1'.
    v1_re = re.compile(r"generation\s*=\s*'v1'")
    v1_violations: list[tuple[str, object]] = []
    for sql, params in conn.statements:
        if PROD_TABLE not in sql:
            continue
        if not sql.strip().upper().startswith(("DELETE", "INSERT", "UPDATE")):
            continue
        has_v1_in_sql = bool(v1_re.search(sql))
        has_v1_in_params = isinstance(params, dict) and params.get("generation") == "v1"
        if has_v1_in_sql or has_v1_in_params:
            v1_violations.append((sql, params))

    assert v1_violations == [], (
        f"I1 VIOLATION: {len(v1_violations)} DML statement(s) against "
        f"{PROD_TABLE!r} carry generation='v1'. Violations:\n"
        + "\n---\n".join(f"SQL: {s!r}\nPARAMS: {p!r}" for s, p in v1_violations)
    )
