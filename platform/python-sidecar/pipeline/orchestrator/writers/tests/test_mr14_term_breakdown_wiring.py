"""MR-14 — term_breakdown production wiring (writer level).

PARIṢKĀRA remediation register, PG-6/PG-7, recon W1.5/W4.4.

GAP (before this fix): even once `interval_solver.find_threshold_crossings`
carries a peak-JD `term_breakdown`/CI decomposition on `IntervalBoundary`
(the companion fix in `services/gochara_v3/tests/test_mr14_term_breakdown_wiring.py`),
`ka_gochara_v3_century_materialize.py`'s `_build_row()` never read those
fields off the boundary, and `INSERT_SQL`/`INSERT_PROD_SQL` never named the 4
W1.5 columns at all — so even a fully-populated `IntervalBoundary` would still
serve `term_breakdown=NULL` to both `kala_gochara_windows_v2` (staging) and
`kala_gochara_windows` (production). This is the writer-side half of the
PG-6/PG-7 defect: "term_breakdown never produced anywhere in the code — root
cause of all-0.0 weights" in every W4.4 fit attempted so far
(PARISHKARA_LEDGER 2026-08-11 baseline: 0/120 gen-3.0 rows non-null).

FIX: `_build_row()` now accepts `term_breakdown`/`lambda_v3_ci_low`/
`lambda_v3_ci_high`/`ci_source` keyword parameters (default None, I4 honest
degrade) and both call sites in `run_substep` pass `boundary.term_breakdown`
etc. explicitly. `INSERT_SQL`/`INSERT_PROD_SQL` now name and bind all 4
columns (added to both tables by migrations 559/564 respectively — already
merged, this PR only wires the writer to use them).
"""
from __future__ import annotations

import json

import pytest

import pipeline.orchestrator.writers.ka_gochara_v3_century_materialize as mod
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    ASSET_ID,
    GENERATION_PROD,
    GENERATION_V3,
    PROD_TABLE,
    TABLE,
    GocharaV3CenturyMaterializeWriter,
)
from services.gochara_v3.resolution_hierarchy import HierarchyResult, WindowResolutionRecord

# ---------------------------------------------------------------------------
# Fake DB connection (mirrors test_mr13_valence_calibration_honesty.py)
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


BUILD_STATE_TABLE = "kala_gochara_v2_build_state"

ONTOLOGY_VALENCE_FIXTURE = {
    "career_advancement": "gain",
    "major_gain": "gain",
    "marriage": "neutral",
    "illness_acute": "loss",
    "chronic_onset": "loss",
    "surgery": "neutral",
}

_SAMPLE_TERM_BREAKDOWN = {
    "promise": 0.6,
    "permission": 0.5,
    "activity": 0.7,
    "quality_gates": 1.0,
    "lambda_v3": 0.21,
    "activity_terms": [
        {"primitive": "degree_contact", "target_ref": "graha:venus",
         "orb_decay": 0.9, "target_weight": 0.8, "p_i": 0.72},
    ],
    "formula": "PROMISE × PERMISSION × activity × quality_gates",
}


def _ctx(conn, chart_id="482012f1-710e-4a25-994a-93821f5871aa") -> ContextSpec:
    return ContextSpec(
        asset_id=ASSET_ID,
        build_id="test-build-mr14",
        db_conn=conn,
        config={"chart_id": chart_id},
    )


def _responder(*, targets=("Venus",), stored_fp=None, rows_exist=False,
               ontology_valence=None):
    ontology_valence = ontology_valence or {}

    def responder(sql: str, params=None) -> list[dict]:
        s = sql.lower()
        if "gochara_resonance_map" in s and "target_ref" in s:
            return [{"target_ref": t} for t in targets]
        if BUILD_STATE_TABLE in s and sql.strip().upper().startswith("SELECT"):
            if stored_fp is None:
                return []
            return [{"class_fingerprint": stored_fp}]
        if TABLE in s and "limit 1" in s:
            return [{"1": 1}] if rows_exist else []
        if "brahma_event_ontology" in s and "valence" in s:
            ec = params[0] if params else None
            if ec in ontology_valence:
                return [{"valence": ontology_valence[ec]}]
            return []
        return []
    return responder


def _patch_common(monkeypatch, boundaries):
    # PARIṢKĀRA MR-11(b): run_substep now calls build_resolution_hierarchy
    # (not find_threshold_crossings directly). Each fake boundary becomes an
    # era-tier WindowResolutionRecord -- term_breakdown/CI/ci_source carry
    # straight across (both dataclasses expose the same field names, and
    # resolution_hierarchy.build_era_windows's own MR-11(b) fix propagates
    # them from a real IntervalBoundary the same way this fixture does here).
    era_windows = [
        WindowResolutionRecord(
            window_id=f"mr14-era-{i}",
            parent_window_id=None,
            resolution_tier="era",
            enter_jd=b.enter_jd, exit_jd=b.exit_jd,
            peak_jd=b.peak_jd, peak_lambda=b.peak_lambda,
            term_breakdown=b.term_breakdown,
            lambda_v3_ci_low=b.lambda_v3_ci_low,
            lambda_v3_ci_high=b.lambda_v3_ci_high,
            ci_source=b.ci_source,
        )
        for i, b in enumerate(boundaries)
    ]
    fake_hierarchy = HierarchyResult(
        era_windows=era_windows, month_windows=[], day_windows=[],
        resolution_facet={"era": len(era_windows), "month": 0, "day": 0},
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


def _make_boundary(era_key: str, peak_lambda: float = 0.5, **w15_fields):
    """Build an IntervalBoundary, optionally carrying the W1.5 fields this
    fix adds (term_breakdown/lambda_v3_ci_low/lambda_v3_ci_high/ci_source).
    Omitting them exercises the pre-fix dataclass shape too (they default to
    None), which is exactly the honest-degrade case this fix must preserve.
    """
    from services.gochara_v3.interval_solver import IntervalBoundary
    return IntervalBoundary(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=peak_lambda,
        era_slice_key=era_key,
        **w15_fields,
    )


def _run_substep_for_class(monkeypatch, event_class: str, *, boundary,
                            ontology_valence=None,
                            chart_id="482012f1-710e-4a25-994a-93821f5871aa"):
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=["Venus"]))
    all_steps = writer.plan_substeps(_ctx(conn_dummy, chart_id))
    step = next(s for s in all_steps if s.key.startswith(f"{event_class}::"))

    conn = _FakeConn(_responder(
        targets=["Venus"], stored_fp=None, ontology_valence=ontology_valence,
    ))
    ctx = _ctx(conn, chart_id)
    _patch_common(monkeypatch, [boundary])

    writer.run_substep(ctx, step)
    return conn.statements


import re  # noqa: E402

_INSERT_TABLE_RE = re.compile(r"INSERT\s+INTO\s+(\S+)", re.IGNORECASE)


def _inserts_for_table(statements, table: str):
    out = []
    for sql, params in statements:
        if not isinstance(params, dict):
            continue
        m = _INSERT_TABLE_RE.match(sql.strip())
        if m and m.group(1).lower() == table.lower():
            out.append(params)
    return out


def _prod_inserts(statements):
    return _inserts_for_table(statements, PROD_TABLE)


def _v2_inserts(statements):
    return _inserts_for_table(statements, TABLE)


# ===========================================================================
# _build_row accepts + carries the W1.5 fields
# ===========================================================================


def test_build_row_accepts_term_breakdown_parameters():
    """_build_row must accept term_breakdown/lambda_v3_ci_low/
    lambda_v3_ci_high/ci_source as real parameters (this is the writer-side
    half of the PG-6/PG-7 wiring gap)."""
    import inspect
    sig = inspect.signature(mod._build_row)
    for name in ("term_breakdown", "lambda_v3_ci_low", "lambda_v3_ci_high", "ci_source"):
        assert name in sig.parameters, (
            f"_build_row must accept a `{name}` parameter to carry the W1.5 "
            f"decomposition through to the served row."
        )


def test_prod_row_carries_term_breakdown_from_boundary(monkeypatch):
    """A boundary with a populated term_breakdown must produce a PRODUCTION
    row (kala_gochara_windows, generation='3.0') whose term_breakdown param
    is the same decomposition, JSON-encoded for the ::jsonb cast."""
    era_key = "g3_1984_1994"
    boundary = _make_boundary(
        era_key, peak_lambda=0.65,
        term_breakdown=dict(_SAMPLE_TERM_BREAKDOWN),
        lambda_v3_ci_low=0.52, lambda_v3_ci_high=0.78,
        ci_source="structural_prior",
    )
    statements = _run_substep_for_class(
        monkeypatch, "marriage", boundary=boundary,
        ontology_valence=ONTOLOGY_VALENCE_FIXTURE,
    )
    prod_rows = _prod_inserts(statements)
    assert len(prod_rows) == 1
    row = prod_rows[0]

    assert row["term_breakdown"] is not None, (
        "production row must carry a non-null term_breakdown when the "
        "boundary has one — this is the exact PG-6/PG-7 defect (0/120 "
        "gen-3.0 rows had term_breakdown before this fix)."
    )
    assert json.loads(row["term_breakdown"]) == _SAMPLE_TERM_BREAKDOWN
    assert row["lambda_v3_ci_low"] == 0.52
    assert row["lambda_v3_ci_high"] == 0.78
    assert row["ci_source"] == "structural_prior"


def test_v2_staging_row_carries_the_same_term_breakdown(monkeypatch):
    """The calibration/staging table row (kala_gochara_windows_v2) must
    carry the SAME term_breakdown as the production row — both come from
    the same _build_row call per boundary (mirrors the valence symmetry
    test in test_mr13)."""
    era_key = "g3_1984_1994"
    boundary = _make_boundary(
        era_key, peak_lambda=0.65,
        term_breakdown=dict(_SAMPLE_TERM_BREAKDOWN),
        lambda_v3_ci_low=0.52, lambda_v3_ci_high=0.78,
        ci_source="structural_prior",
    )
    statements = _run_substep_for_class(
        monkeypatch, "marriage", boundary=boundary,
        ontology_valence=ONTOLOGY_VALENCE_FIXTURE,
    )
    v2_rows = _v2_inserts(statements)
    assert len(v2_rows) == 1
    assert json.loads(v2_rows[0]["term_breakdown"]) == _SAMPLE_TERM_BREAKDOWN


def test_insert_sql_names_all_four_w15_columns():
    """Both INSERT templates must name term_breakdown/lambda_v3_ci_low/
    lambda_v3_ci_high/ci_source — a purely-string-level guard, independent
    of the functional tests above, so a future refactor that silently drops
    a column name from the SQL (while still passing a now-ignored param)
    still gets caught."""
    for name, sql in (("INSERT_SQL", mod.INSERT_SQL), ("INSERT_PROD_SQL", mod.INSERT_PROD_SQL)):
        for col in ("term_breakdown", "lambda_v3_ci_low", "lambda_v3_ci_high", "ci_source"):
            assert col in sql, f"{name} must name column {col!r}"


def test_row_honestly_none_when_boundary_has_no_decomposition(monkeypatch):
    """I4: a boundary with no term_breakdown (the pre-fix / evaluation-failure
    shape) must still produce a row — with term_breakdown/CI fields honestly
    None, never a fabricated value."""
    era_key = "g3_1984_1994"
    boundary = _make_boundary(era_key, peak_lambda=0.65)  # no W1.5 fields
    statements = _run_substep_for_class(
        monkeypatch, "marriage", boundary=boundary,
        ontology_valence=ONTOLOGY_VALENCE_FIXTURE,
    )
    prod_rows = _prod_inserts(statements)
    assert len(prod_rows) == 1
    row = prod_rows[0]
    assert row["term_breakdown"] is None
    assert row["lambda_v3_ci_low"] is None
    assert row["lambda_v3_ci_high"] is None
    assert row["ci_source"] is None


__all__ = []
