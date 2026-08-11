"""MR-38 gate: fold the writer's row-shape into the delta fingerprint.

GOCHARA-UTKARSA / PARIṢKĀRA register MR-38.

BACKGROUND (the defect this closes)
------------------------------------
MR-13/14 changed the row shape `ka_gochara_v3_century_materialize.py` writes
(added the `term_breakdown`/`lambda_v3_ci_low`/`lambda_v3_ci_high`/`ci_source`
columns to both INSERT templates and to `_build_row`) WITHOUT bumping
`ENGINE_VERSION` (still "v3.0" — `ENGINE_VERSION`'s documented purpose is
narrower: "bumped whenever the scoring engine changes in a way that would
move a stored window", not "bumped whenever the row shape changes"). Because
`compute_substep_fingerprint`'s only inputs were (event_class, era_slice_key,
engine_version, resonance_targets), a chart already built under the OLD row
shape recomputes the IDENTICAL fingerprint after the MR-13/14 code change —
the delta-skip (`stored_fingerprint == recomputed_fingerprint AND rows_exist`)
fires and the authorized rebuild silently no-ops, leaving the new columns
NULL forever on already-built rows. This was caught in rehearsal, not by any
test — this file is that missing test, plus the fix.

FIX
---
`STAGING_ROW_SCHEMA_COLUMNS` (from `INSERT_SQL`, the calibration/staging
template written every substep) and `ROW_SCHEMA_COLUMNS` (from
`INSERT_PROD_SQL`, the production template) are BOTH derived directly from
the actual SQL templates executed — never a hand-maintained duplicate list
that could itself drift — and BOTH folded into
`compute_substep_fingerprint`'s hashed payload alongside `engine_version`. A
future MR that adds/removes/renames a column in EITHER template therefore
automatically changes every substep's fingerprint — no human has to remember
to bump `ENGINE_VERSION` for a row-shape change ever again. This composes
cleanly with any future `ENGINE_VERSION` bump (a distinct, orthogonal input
to the same hashed payload).

SCOPE (PARĪKṢAKA F-3, honesty correction — an earlier draft of this file and
the writer's own summary docstring overstated the claim as "the inputs AND
the writer's output contract are both unchanged"): the fold covers ROW SHAPE
only — which columns exist in either INSERT template. It does NOT cover
VALUE-COMPUTATION changes (e.g. MR-13's honest-valence-derivation fix, which
changed what VALUE a column gets without changing the column LIST) — those
remain covered ONLY by the `ENGINE_VERSION` standing rule, exactly as before
MR-38. A fingerprint match after MR-38 means "the inputs and the writer's
column list are unchanged" — not "the writer's computed values are
unchanged".

GATE (per MR-38 register text)
-------------------------------
  (a) A synthetic writer-version bump forces cache invalidation and a real
      rewrite (find_threshold_crossings gets called; the writer does not
      silently skip).
  (b) Re-running with no version change and no input change correctly skips
      (find_threshold_crossings does NOT get called).

PARĪKṢAKA F-2 (staging template coverage): the initial version of this fix
folded `ROW_SCHEMA_COLUMNS` (production, `INSERT_PROD_SQL`) only —
`INSERT_SQL` (staging, `kala_gochara_windows_v2`, executed every substep
alongside the production write) was not folded, so a staging-only column
change would still have silently no-opped. Closed by also folding
`STAGING_ROW_SCHEMA_COLUMNS`; see `test_staging_row_schema_columns_*` and
`test_fingerprint_changes_when_staging_only_row_schema_changes` below.

TDD note: at the point this file was authored, `ROW_SCHEMA_COLUMNS` did not
exist on the module and `compute_substep_fingerprint`'s payload did not
depend on row shape at all — every test below that references
`mod.ROW_SCHEMA_COLUMNS` or asserts row-shape sensitivity was RED against the
pre-fix source (AttributeError / assertion failure) before the fix in this
same change landed it GREEN.
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

BUILD_STATE_TABLE = "kala_gochara_v2_build_state"
TABLE = mod.TABLE


# ---------------------------------------------------------------------------
# Fake DB connection (mirrors test_w34_century_horizon.py's pattern — no real
# DB required; kept self-contained so this file doesn't depend on another
# test module's internals).
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
        build_id="test-build-mr38",
        db_conn=conn,
        config={"chart_id": "482012f1-710e-4a25-994a-93821f5871aa", **extra_config},
    )


def _responder(*, targets=("Venus", "Jupiter"), stored_fp=None, rows_exist=False):
    def responder(sql: str, params=None):
        s = sql.lower()
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


# ===========================================================================
# Unit level: the fingerprint payload is sensitive to the writer's row shape,
# not just to engine_version.
# ===========================================================================


def test_row_schema_columns_constant_exists_and_is_nonempty():
    """The writer must expose a ROW_SCHEMA_COLUMNS signature of what it writes."""
    assert hasattr(mod, "ROW_SCHEMA_COLUMNS"), (
        "ka_gochara_v3_century_materialize must expose ROW_SCHEMA_COLUMNS — "
        "the writer's output-contract signature folded into every substep's "
        "delta fingerprint (MR-38)."
    )
    assert len(mod.ROW_SCHEMA_COLUMNS) > 0


def test_row_schema_columns_derived_from_insert_prod_sql():
    """ROW_SCHEMA_COLUMNS must be the ACTUAL column list of INSERT_PROD_SQL —
    not a hand-maintained duplicate that could itself drift. Every column
    named in the real INSERT template must appear in the signature."""
    for known_col in (
        "chart_id", "event_class", "generation", "era_slice_key",
        "term_breakdown", "lambda_v3_ci_low", "lambda_v3_ci_high", "ci_source",
    ):
        assert known_col in mod.ROW_SCHEMA_COLUMNS, (
            f"{known_col!r} is a real column in INSERT_PROD_SQL but missing "
            f"from ROW_SCHEMA_COLUMNS={mod.ROW_SCHEMA_COLUMNS!r} — the "
            f"signature has drifted from what the writer actually writes."
        )


def test_fingerprint_changes_when_row_schema_changes(monkeypatch):
    """Core MR-38 assertion: simulate the MR-13/14 defect directly. Two
    fingerprints computed with IDENTICAL (event_class, era_slice_key,
    engine_version, resonance_targets) but DIFFERENT ROW_SCHEMA_COLUMNS
    (simulating 'before' vs 'after' a row-shape change that did not bump
    ENGINE_VERSION) MUST differ. Before the MR-38 fix, this fails: the
    fingerprint payload has no row-schema input at all, so identical
    (event_class, era_slice_key, engine_version, targets) always produces
    the identical hash regardless of row shape."""
    args = ("marriage", "g3_1984_1994", ENGINE_VERSION, ["Venus"])

    monkeypatch.setattr(mod, "ROW_SCHEMA_COLUMNS", ("chart_id", "event_class"))
    fp_old_schema = compute_substep_fingerprint(*args)

    monkeypatch.setattr(
        mod, "ROW_SCHEMA_COLUMNS",
        ("chart_id", "event_class", "term_breakdown", "lambda_v3_ci_low"),
    )
    fp_new_schema = compute_substep_fingerprint(*args)

    assert fp_old_schema != fp_new_schema, (
        "MR-38 regression: compute_substep_fingerprint must be sensitive to "
        "ROW_SCHEMA_COLUMNS. A row-shape change (e.g. MR-13/14 adding "
        "term_breakdown/lambda_v3_ci_low/lambda_v3_ci_high/ci_source columns) "
        "must change the fingerprint even when event_class, era_slice_key, "
        "engine_version, and resonance_targets are all unchanged — otherwise "
        "an authorized rebuild silently no-ops (the exact MR-38 defect)."
    )


def test_fingerprint_stable_when_row_schema_unchanged():
    """Sanity: identical inputs including the real (unpatched) ROW_SCHEMA_COLUMNS
    still produce a deterministic, identical fingerprint (AC8 preserved)."""
    args = ("marriage", "g3_1984_1994", ENGINE_VERSION, ["Venus", "Jupiter"])
    assert compute_substep_fingerprint(*args) == compute_substep_fingerprint(*args)


# ===========================================================================
# PARĪKṢAKA F-2 — the staging template (INSERT_SQL / kala_gochara_windows_v2)
# must be folded too, not just the production template.
# ===========================================================================


def test_staging_row_schema_columns_constant_exists_and_is_nonempty():
    """The writer must expose STAGING_ROW_SCHEMA_COLUMNS — the calibration/
    staging INSERT's output-contract signature, distinct from the production
    one, folded into every substep's delta fingerprint (MR-38, F-2)."""
    assert hasattr(mod, "STAGING_ROW_SCHEMA_COLUMNS"), (
        "ka_gochara_v3_century_materialize must expose "
        "STAGING_ROW_SCHEMA_COLUMNS — the staging INSERT_SQL's output-"
        "contract signature. Folding only the production template "
        "(ROW_SCHEMA_COLUMNS) leaves a staging-only column change free to "
        "silently no-op (PARĪKṢAKA F-2)."
    )
    assert len(mod.STAGING_ROW_SCHEMA_COLUMNS) > 0


def test_staging_row_schema_columns_derived_from_insert_sql():
    """STAGING_ROW_SCHEMA_COLUMNS must be the ACTUAL column list of
    INSERT_SQL (the staging/calibration template) — not a hand-maintained
    duplicate, and not silently aliased to ROW_SCHEMA_COLUMNS (the production
    template) either — both templates currently share the same 24 columns,
    but the signature must be independently derived from INSERT_SQL so a
    future divergence between the two templates is still caught."""
    for known_col in (
        "chart_id", "event_class", "generation", "era_slice_key",
        "term_breakdown", "lambda_v3_ci_low", "lambda_v3_ci_high", "ci_source",
    ):
        assert known_col in mod.STAGING_ROW_SCHEMA_COLUMNS, (
            f"{known_col!r} is a real column in INSERT_SQL but missing from "
            f"STAGING_ROW_SCHEMA_COLUMNS={mod.STAGING_ROW_SCHEMA_COLUMNS!r}."
        )
    assert mod._extract_insert_columns(mod.INSERT_SQL) == mod.STAGING_ROW_SCHEMA_COLUMNS, (
        "STAGING_ROW_SCHEMA_COLUMNS must be derived from INSERT_SQL via "
        "_extract_insert_columns, not hand-maintained or copied from the "
        "production signature."
    )


def test_fingerprint_changes_when_staging_only_row_schema_changes(monkeypatch):
    """PARĪKṢAKA F-2 core assertion: a STAGING-ONLY column change (INSERT_SQL
    edited without touching INSERT_PROD_SQL — e.g. a calibration-only column
    added to kala_gochara_windows_v2) must still change the fingerprint, even
    though ROW_SCHEMA_COLUMNS (production) is completely unchanged. Before
    the F-2 fix, only ROW_SCHEMA_COLUMNS fed the payload, so this scenario
    would silently no-op exactly like the original MR-38 defect, one column
    over."""
    args = ("marriage", "g3_1984_1994", ENGINE_VERSION, ["Venus"])

    # Hold the production signature fixed; vary ONLY the staging signature.
    monkeypatch.setattr(mod, "ROW_SCHEMA_COLUMNS", ("chart_id", "event_class"))
    monkeypatch.setattr(mod, "STAGING_ROW_SCHEMA_COLUMNS", ("chart_id", "event_class"))
    fp_before = compute_substep_fingerprint(*args)

    monkeypatch.setattr(
        mod, "STAGING_ROW_SCHEMA_COLUMNS",
        ("chart_id", "event_class", "staging_only_calibration_column"),
    )
    # ROW_SCHEMA_COLUMNS (production) is left untouched — this is the
    # "staging-only" part of the scenario.
    fp_after = compute_substep_fingerprint(*args)

    assert fp_before != fp_after, (
        "PARĪKṢAKA F-2 regression: a column added to INSERT_SQL (staging) "
        "with INSERT_PROD_SQL (production) completely unchanged must still "
        "change the fingerprint — otherwise a staging-only row-shape change "
        "silently no-ops exactly like the original MR-38 defect."
    )


# ===========================================================================
# Integration level (run_substep): (a) synthetic version bump forces rewrite;
# (b) unchanged version + inputs correctly skips.
# ===========================================================================


def test_gate_a_synthetic_version_bump_forces_rewrite(monkeypatch):
    """GATE (a): a stored fingerprint computed under an OLD writer-version
    signature must NOT match the fingerprint recomputed under the CURRENT
    signature — run_substep must call find_threshold_crossings (a real
    rewrite), not take the skip path."""
    targets = ["Venus", "Jupiter"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    # Simulate a fingerprint stored BEFORE a writer-version bump (a shorter
    # ROW_SCHEMA_COLUMNS standing in for "the pre-change row shape").
    real_schema = mod.ROW_SCHEMA_COLUMNS
    monkeypatch.setattr(mod, "ROW_SCHEMA_COLUMNS", real_schema[:2])
    stale_fp = compute_substep_fingerprint(ec, era_key, ENGINE_VERSION, targets)
    monkeypatch.setattr(mod, "ROW_SCHEMA_COLUMNS", real_schema)

    conn = _FakeConn(_responder(targets=targets, stored_fp=stale_fp, rows_exist=True))
    ctx = _ctx(conn)

    called = []
    monkeypatch.setattr(
        mod, "find_threshold_crossings",
        lambda *a, **k: called.append(1) or [],
    )
    # A real rewrite reaches ClassContext.fetch (and swisseph import) before
    # find_threshold_crossings — stub both so the rewrite path can complete,
    # matching the pattern in test_ka_gochara_v3_mutation_guard.py.
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
        "GATE (a) FAILED: a stale fingerprint (computed under an old "
        "ROW_SCHEMA_COLUMNS, simulating a pre-version-bump row shape) must "
        "force find_threshold_crossings to run — the writer must NOT take "
        "the skip path when the stored fingerprint does not match the "
        "current writer's output-contract signature."
    )


def test_gate_b_unchanged_version_and_inputs_skips(monkeypatch):
    """GATE (b): re-running with no version change and no input change
    correctly skips (find_threshold_crossings NOT called)."""
    targets = ["Venus", "Jupiter"]
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=targets))
    steps = writer.plan_substeps(_ctx(conn_dummy))
    step = steps[0]
    ec, era_key = step.key.split("::", 1)

    expected_fp = compute_substep_fingerprint(ec, era_key, ENGINE_VERSION, targets)

    conn = _FakeConn(_responder(targets=targets, stored_fp=expected_fp, rows_exist=True))
    ctx = _ctx(conn)

    called = []
    monkeypatch.setattr(
        mod, "find_threshold_crossings",
        lambda *a, **k: called.append(1) or [],
    )

    result = writer.run_substep(ctx, step)

    assert called == [], (
        "GATE (b) FAILED: find_threshold_crossings must NOT be called when "
        "the fingerprint (including row schema) is unchanged and rows exist."
    )
    assert result.rows_inserted == 0
    assert "skip" in result.notes.lower() or "unchanged" in result.notes.lower()
