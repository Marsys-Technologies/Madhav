"""Tests for MR-47 — shape_conformance writer fix (PARIṢKĀRA campaign,
ADJUDICATOR ruling PK-R-10).

GAP (before this fix): `ka_gochara_v3_century_materialize.py`'s `_build_row`
hardcoded `"temporal_shape": "interval"` for EVERY row it built — including
rows produced by the R8.12 shape-gate flat-production branch for
point-canonical event classes (marriage, illness_acute, surgery, and 10
other classes). Nothing tracked that a specific row was an honest
"envelope, not the real shape" — the §N.7 item 3 defect class ("no
wrapper-local constant may shadow an L1-computed value").

FIX: `_build_row` (and its chain sibling `_build_chain_row`, which shares
the SAME INSERT templates and therefore the SAME key set) now take
`shape_conformance` as a REQUIRED keyword parameter — no default, mirroring
the `peak_basis` discipline R8.8 already established. `run_substep` derives
the correct constant from `class_shape` (the SAME value it already fetched
via `_fetch_event_class_temporal_shape` for the R8.12 shape gate) — never a
proxy, never a bare literal.

No DB required — all tests use fixture-based fakes, mirroring the pattern in
test_w34_century_horizon.py / test_mr12_chain_production.py.
"""
from __future__ import annotations

import inspect
import json
import re

import pytest

import pipeline.orchestrator.writers.ka_gochara_v3_century_materialize as mod
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    ASSET_ID,
    GENERATION_PROD,
    PROD_TABLE,
    TABLE,
    GocharaV3CenturyMaterializeWriter,
    ROW_SCHEMA_COLUMNS,
    STAGING_ROW_SCHEMA_COLUMNS,
    _build_chain_row,
    _build_row,
)
from services.gochara_v3.interval_solver import IntervalBoundary, MilestoneScore
from services.gochara_v3.resolution_hierarchy import (
    HierarchyResult,
    WindowResolutionRecord,
)
from services.gochara_v3.shape_conformance_vocab import (
    SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE,
)

# ---------------------------------------------------------------------------
# Fake DB connection (mirrors test_w34_century_horizon.py's fixture pattern)
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
        self._id_counter = 0

    def cursor(self):
        return _FakeCursor(self)

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        rows = self.responder(sql, params)
        if rows is None and sql.strip().upper().startswith("INSERT") and "RETURNING ID" in sql.upper():
            self._id_counter += 1
            rows = [{"id": self._id_counter}]
        self.rows_for_next = rows or []
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
        build_id="test-build-mr47",
        db_conn=conn,
        config={"chart_id": "482012f1-710e-4a25-994a-93821f5871aa", **extra_config},
    )


BUILD_STATE_TABLE = "kala_gochara_v2_build_state"


def _ontology_responder(
    *,
    event_class: str,
    temporal_shape: str,
    milestone_template: list[dict] | None = None,
    irreversibility_milestone: str | None = None,
    targets: list[str] = ("Venus",),
    stored_fp: str | None = None,
    rows_exist: bool = False,
):
    """Query responder serving a brahma_event_ontology shape row for exactly
    one event_class, plus the standard resonance/build-state fixtures --
    mirrors test_mr12_chain_production.py's `_ontology_responder`. INSERT ...
    RETURNING id statements get None here (handled by _FakeConn's own
    auto-incrementing fallback)."""
    def responder(sql: str, params=None):
        s = sql.lower()
        if "brahma_event_ontology" in s and "temporal_shape" in s:
            return [{
                "temporal_shape": temporal_shape,
                "milestone_template": json.dumps(milestone_template) if milestone_template is not None else None,
                "irreversibility_milestone": irreversibility_milestone,
            }]
        if "gochara_resonance_map" in s and "distinct" in s and "event_class" in s and "target_ref" not in s:
            return [{"event_class": event_class}]
        if "gochara_resonance_map" in s and "target_ref" in s:
            return [{"target_ref": t} for t in targets]
        if BUILD_STATE_TABLE in s and sql.strip().upper().startswith("SELECT"):
            if stored_fp is None:
                return []
            return [{"class_fingerprint": stored_fp}]
        if TABLE in s and "limit 1" in s:
            return [{"1": 1}] if rows_exist else []
        return None  # let _FakeConn's RETURNING-id fallback handle INSERTs
    return responder


def _patch_swe_and_context(monkeypatch):
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
        sys.modules["swisseph"] = types.ModuleType("swisseph")


def _v2_inserts(conn):
    return [
        params for sql, params in conn.statements
        if sql.strip().upper().startswith("INSERT INTO KALA_GOCHARA_WINDOWS_V2")
        and isinstance(params, dict)
    ]


def _prod_inserts(conn):
    return [
        params for sql, params in conn.statements
        if re.match(r"INSERT INTO KALA_GOCHARA_WINDOWS\s", sql.strip().upper())
        and isinstance(params, dict)
    ]


# ===========================================================================
# _build_row — shape_conformance is now a REQUIRED keyword parameter
# ===========================================================================


def _fake_boundary():
    return IntervalBoundary(
        enter_jd=2445736.5 + 10.0, exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0, peak_lambda=0.5, era_slice_key="g3_1984_1994",
    )


def test_build_row_requires_shape_conformance_kwarg():
    """No default: a caller that omits shape_conformance must fail loudly
    (TypeError), not silently build a row with an unmarked shape claim --
    the exact discipline `valence`/`is_adverse` (MR-13) and `peak_basis`
    (R8.8) already established for this function."""
    with pytest.raises(TypeError):
        _build_row(  # type: ignore[call-arg]
            "chart-x", "career_advancement", _fake_boundary(), "g3_1984_1994",
            valence="neutral", is_adverse=False,
            peak_basis=mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
        )


def test_build_row_stamps_shape_conformance_ontology_match():
    row = _build_row(
        "chart-x", "major_gain", _fake_boundary(), "g3_1984_1994",
        valence="gain", is_adverse=False,
        peak_basis=mod.peak_basis_vocab.LAMBDA_V3_ARGMAX,
        shape_conformance=SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
        resolution="day",
    )
    assert row["shape_conformance"] == SHAPE_CONFORMANCE_ONTOLOGY_MATCH
    # temporal_shape stamping itself is UNCHANGED by this fix (still 'interval'
    # for every _build_row call) — only the new field is added.
    assert row["temporal_shape"] == "interval"


def test_build_row_stamps_shape_conformance_point_class_envelope():
    row = _build_row(
        "chart-x", "marriage", _fake_boundary(), "g3_1984_1994",
        valence="neutral", is_adverse=False,
        peak_basis=mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
        shape_conformance=SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE,
        resolution=None,
    )
    assert row["shape_conformance"] == SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE
    assert row["temporal_shape"] == "interval"
    assert row["resolution"] is None


# ===========================================================================
# _build_chain_row — same required parameter (shares INSERT_SQL/INSERT_PROD_SQL)
# ===========================================================================


def _fake_milestone():
    return MilestoneScore(
        milestone_id="decision", milestone_jd=2445736.5 + 10.0, lambda_v3=0.5,
        is_above_threshold=True, is_irreversibility_milestone=False,
        intensity_result=None,
    )


def test_build_chain_row_requires_shape_conformance_kwarg():
    with pytest.raises(TypeError):
        _build_chain_row(  # type: ignore[call-arg]
            "chart-x", "business_launch", _fake_milestone(), "g3_1984_1994",
            valence="gain", is_adverse=False, generation=GENERATION_PROD,
            peak_basis=mod.peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET,
        )


def test_build_chain_row_stamps_shape_conformance_ontology_match():
    """A chain row's stored temporal_shape='chain' genuinely matches the
    ontology's declared 'chain' shape for a chain-canonical class -- it is
    never an envelope, so it always earns ONTOLOGY_MATCH."""
    row = _build_chain_row(
        "chart-x", "business_launch", _fake_milestone(), "g3_1984_1994",
        valence="gain", is_adverse=False, generation=GENERATION_PROD,
        peak_basis=mod.peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET,
        shape_conformance=SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    )
    assert row["shape_conformance"] == SHAPE_CONFORMANCE_ONTOLOGY_MATCH
    assert row["temporal_shape"] == "chain"


def test_build_row_and_build_chain_row_still_share_identical_key_set():
    """PARĪKṢAKA invariant (test_mr12's own gate): the two row-builders must
    keep carrying EXACTLY the same column keys -- no new DML statement is
    introduced for the shape_conformance addition, so the I1 mutation-guard's
    static source coverage stays valid unchanged."""
    interval_row = _build_row(
        "chart-x", "career_advancement", _fake_boundary(), "g3_1984_1994",
        valence="gain", is_adverse=False,
        peak_basis=mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
        shape_conformance=SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE,
    )
    chain_row = _build_chain_row(
        "chart-x", "business_launch", _fake_milestone(), "g3_1984_1994",
        valence="gain", is_adverse=False, generation=GENERATION_PROD,
        peak_basis=mod.peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET,
        shape_conformance=SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    )
    assert set(interval_row.keys()) == set(chain_row.keys())
    assert "shape_conformance" in interval_row
    assert "shape_conformance" in chain_row


# ===========================================================================
# INSERT_SQL / INSERT_PROD_SQL — column list carries shape_conformance
# ===========================================================================


def test_row_schema_columns_include_shape_conformance():
    assert "shape_conformance" in ROW_SCHEMA_COLUMNS, (
        "INSERT_PROD_SQL must write shape_conformance -- ROW_SCHEMA_COLUMNS "
        f"is derived directly from that SQL template. Got: {ROW_SCHEMA_COLUMNS}"
    )
    assert "shape_conformance" in STAGING_ROW_SCHEMA_COLUMNS, (
        "INSERT_SQL must write shape_conformance -- STAGING_ROW_SCHEMA_COLUMNS "
        f"is derived directly from that SQL template. Got: {STAGING_ROW_SCHEMA_COLUMNS}"
    )


# ===========================================================================
# Source guard — named constants only, never a bare literal (mirrors
# test_peak_basis_vocab_used_not_literal)
# ===========================================================================


def test_shape_conformance_vocab_used_not_literal():
    src = inspect.getsource(mod)
    assert '"shape_conformance": "ontology_match"' not in src, (
        "MR-47 VIOLATION: a bare shape_conformance dict-literal string was "
        "found in the writer's source -- must use shape_conformance_vocab "
        "constants."
    )
    assert '"shape_conformance": "point_class_context_envelope"' not in src, (
        "MR-47 VIOLATION: a bare shape_conformance dict-literal string was "
        "found in the writer's source -- must use shape_conformance_vocab "
        "constants."
    )
    assert "shape_conformance_vocab" in src
    assert "shape_conformance_vocab.SHAPE_CONFORMANCE_ONTOLOGY_MATCH" in src
    assert "shape_conformance_vocab.SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE" in src


# ===========================================================================
# run_substep — end-to-end dispatch, no real DB
# ===========================================================================


def test_run_substep_interval_hierarchy_rows_carry_ontology_match(monkeypatch):
    """R8.12 'interval' branch (real era⊃month⊃day hierarchy): every row
    this substep inserts must carry shape_conformance=ONTOLOGY_MATCH -- its
    stored temporal_shape genuinely equals the ontology's declared shape."""
    era = WindowResolutionRecord(
        window_id="era-1", parent_window_id=None, resolution_tier="era",
        enter_jd=2445736.5, exit_jd=2445736.5 + 500.0,
        peak_jd=2445736.5 + 100.0, peak_lambda=0.9,
    )
    hierarchy = HierarchyResult(
        era_windows=[era], month_windows=[], day_windows=[],
        resolution_facet={"era": 1, "month": 0, "day": 0},
    )
    conn = _FakeConn(_ontology_responder(
        event_class="major_gain", temporal_shape="interval", targets=["Venus"],
    ))
    ctx = _ctx(conn)
    writer = GocharaV3CenturyMaterializeWriter()
    steps = writer.plan_substeps(ctx)
    step = next(s for s in steps if s.key.startswith("major_gain::"))

    monkeypatch.setattr(mod, "build_resolution_hierarchy", lambda *a, **k: hierarchy)
    _patch_swe_and_context(monkeypatch)

    result = writer.run_substep(ctx, step)
    assert result.rows_inserted == 1

    for row in _v2_inserts(conn) + _prod_inserts(conn):
        assert row["shape_conformance"] == SHAPE_CONFORMANCE_ONTOLOGY_MATCH, (
            f"interval-hierarchy row must carry ONTOLOGY_MATCH, got "
            f"{row['shape_conformance']!r} (resolution={row.get('resolution')!r})"
        )
        assert row["resolution"] == "era"


def test_run_substep_point_canonical_envelope_rows_carry_point_class_envelope(monkeypatch):
    """R8.12 flat-production (else) branch for a point-canonical class: every
    row must carry shape_conformance=POINT_CLASS_CONTEXT_ENVELOPE -- the
    honest 'this is an envelope, not a genuine interval production' marker
    PK-R-10 requires."""
    fake_boundaries = [
        IntervalBoundary(
            enter_jd=2445736.5 + 10.0, exit_jd=2445736.5 + 20.0,
            peak_jd=2445736.5 + 15.0, peak_lambda=0.72, era_slice_key="g3_1984_1994",
        ),
        IntervalBoundary(
            enter_jd=2445736.5 + 100.0, exit_jd=2445736.5 + 900.0,
            peak_jd=2445736.5 + 500.0, peak_lambda=0.81, era_slice_key="g3_1984_1994",
        ),
    ]
    conn = _FakeConn(_ontology_responder(
        event_class="marriage", temporal_shape="point", targets=["Venus"],
    ))
    ctx = _ctx(conn)
    writer = GocharaV3CenturyMaterializeWriter()
    steps = writer.plan_substeps(ctx)
    step = next(s for s in steps if s.key.startswith("marriage::"))

    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: fake_boundaries)
    _patch_swe_and_context(monkeypatch)

    result = writer.run_substep(ctx, step)
    assert result.rows_inserted == 2

    v2_rows = _v2_inserts(conn)
    assert len(v2_rows) == 2
    for row in v2_rows + _prod_inserts(conn):
        # R2 SEV-2 fix: point-canonical flat rows now carry resolution='era'
        # (was NULL pre-R2) so buildNestedHierarchy places them in roots.
        assert row["resolution"] == "era", (
            f"R2 SEV-2: point-canonical flat row must carry resolution='era', "
            f"got {row['resolution']!r}"
        )
        assert row["temporal_shape"] == "interval"
        assert row["shape_conformance"] == SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE, (
            f"R8.12 flat-envelope row for a point-canonical class must carry "
            f"POINT_CLASS_CONTEXT_ENVELOPE, got {row['shape_conformance']!r}"
        )


def test_run_substep_chain_rows_carry_ontology_match(monkeypatch):
    """The chain branch (_build_chain_row) also earns ONTOLOGY_MATCH -- a
    chain row is never an envelope, it is genuinely chain-shaped whenever the
    ontology declares the class chain-canonical."""
    template_raw = [
        {"milestone_id": "decision", "name_en": "Decision", "typical_offset_days_from_first": 0},
        {"milestone_id": "registration", "name_en": "Registration", "typical_offset_days_from_first": 45},
        {"milestone_id": "first_revenue", "name_en": "First revenue", "typical_offset_days_from_first": 120},
    ]
    conn = _FakeConn(_ontology_responder(
        event_class="business_launch", temporal_shape="chain",
        milestone_template=template_raw, irreversibility_milestone="first_revenue",
        targets=["Jupiter"],
    ))
    ctx = _ctx(conn)
    writer = GocharaV3CenturyMaterializeWriter()
    steps = writer.plan_substeps(ctx)
    step = next(s for s in steps if s.key.startswith("business_launch::"))

    fake_boundary = IntervalBoundary(
        enter_jd=2445736.5, exit_jd=2445736.5 + 200.0, peak_jd=2445736.5 + 90.0,
        peak_lambda=0.6, era_slice_key=step.key.split("::", 1)[1],
    )

    def _fake_score_chain_milestones(swe, context, episode_anchor_jd, milestone_template, threshold_config):
        return [
            MilestoneScore(
                milestone_id=entry["milestone_id"],
                milestone_jd=episode_anchor_jd + entry["typical_offset_days"],
                lambda_v3=0.5, is_above_threshold=True,
                is_irreversibility_milestone=entry["is_irreversibility_milestone"],
                intensity_result=None,
            )
            for entry in milestone_template
        ]

    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
    monkeypatch.setattr(mod, "score_chain_milestones", _fake_score_chain_milestones)
    _patch_swe_and_context(monkeypatch)

    result = writer.run_substep(ctx, step)
    assert result.rows_inserted == 3

    for row in _v2_inserts(conn) + _prod_inserts(conn):
        assert row["temporal_shape"] == "chain"
        assert row["shape_conformance"] == SHAPE_CONFORMANCE_ONTOLOGY_MATCH, (
            f"chain row must carry ONTOLOGY_MATCH, got {row['shape_conformance']!r}"
        )
