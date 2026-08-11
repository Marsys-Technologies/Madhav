"""Tests for MR-12 — chain production wiring (PARIṢKĀRA campaign).

GOCHARA-UTKARSA / PARIṢKĀRA campaign, register item MR-12: "Produce chain
rows (marriage first)". No DB required — all tests use fixture-based fakes,
mirroring the pattern in test_w34_century_horizon.py.

HONEST FINDING (disclosed here so the test suite itself carries the record,
not just the PR description): per the LIVE brahma_event_ontology (migration
456, unchanged by migration 555), 'marriage' is temporal_shape='point', NOT
'chain' -- explicitly, with the ontology's own note that a future v2 COULD
split it into a chain if per-milestone dates become available. It is not
chain-shaped today. kala_gochara_windows (migration 460, BRIEF_D5 §3,
BINDING) requires a row's shape to mirror the ontology's declared shape, and
brahma_event_ontology's own CHECK constraint (migration 456) forbids a
'chain'-shaped row without a real milestone_template of >=2 entries -- so a
literal "marriage produces chain rows" implementation is impossible without
either fabricating an ontology override (B.10 violation) or editing the
ontology itself (a native-ruled, out-of-lane change no CODE-ONLY session may
self-authorize).

This test file therefore does two honest things instead:
  1. Proves the wiring is GENERIC (event_class-agnostic) by exercising it
     against a SYNTHETIC/fixture ontology row for 'marriage' -- clearly
     marked synthetic throughout, never asserted as live truth. This is
     the literal "marriage chain with >=2 milestones is produced" proof the
     MR-12 deliverable asks for, satisfied honestly: the CODE path is
     class-name-agnostic and would produce exactly this shape for marriage
     the day the ontology is (if ever) amended to declare it a chain.
  2. Exercises the SAME code path against 'business_launch' -- the first
     class that is GENUINELY temporal_shape='chain' in the live ontology
     today (migration 456: 3-milestone template, irreversibility_milestone
     ='first_revenue', BRIEF_D4A Lane A-2's own worked example) -- as the
     real, non-fabricated "first chain rows this writer ever produces"
     claim.

See PARISHKARA_LEDGER.md "MR-12" entry (parishkara/campaign branch) for the
full disclosure and 00_ARCHITECTURE/llm_consumption_audit/briefs/
gochara_elevation/MASTER_REMEDIATION_REGISTER_v2_0.md for the register item
text this session found does not match the canonical ontology.
"""
from __future__ import annotations

import json

import pytest

import pipeline.orchestrator.writers.ka_gochara_v3_century_materialize as mod
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    ASSET_ID,
    ENGINE_VERSION,
    EVENT_CLASSES,
    GENERATION_PROD,
    GENERATION_V3,
    PROD_TABLE,
    TABLE,
    GocharaV3CenturyMaterializeWriter,
    _build_chain_row,
    _fetch_class_shape,
    _normalize_milestone_template,
)
from services.gochara_v3.interval_solver import IntervalBoundary, MilestoneScore
from services.gochara_v3.threshold import ThresholdConfig


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
        build_id="test-build-mr12",
        db_conn=conn,
        config={"chart_id": "482012f1-710e-4a25-994a-93821f5871aa", **extra_config},
    )


BUILD_STATE_TABLE = "kala_gochara_v2_build_state"

_BUSINESS_LAUNCH_TEMPLATE_RAW = [
    {"milestone_id": "decision", "name_en": "Decision to found/launch", "typical_offset_days_from_first": 0},
    {"milestone_id": "registration", "name_en": "Legal/business registration", "typical_offset_days_from_first": 45},
    {"milestone_id": "first_revenue", "name_en": "First revenue booked", "typical_offset_days_from_first": 120},
]


def _ontology_responder(
    *,
    event_class: str,
    temporal_shape: str,
    milestone_template: list[dict] | None,
    irreversibility_milestone: str | None,
    targets: list[str] = ("Venus",),
    stored_fp: str | None = None,
    rows_exist: bool = False,
):
    """Build a query responder serving brahma_event_ontology shape rows in
    addition to the standard resonance/build-state fixtures."""
    def responder(sql: str, params=None) -> list[dict]:
        s = sql.lower()
        if "brahma_event_ontology" in s and "temporal_shape" in s:
            return [{
                "temporal_shape": temporal_shape,
                "milestone_template": json.dumps(milestone_template) if milestone_template is not None else None,
                "irreversibility_milestone": irreversibility_milestone,
            }]
        # MR-16: plan_substeps now discovers its event-class set dynamically
        # via _discover_event_classes (DISTINCT event_class, no target_ref
        # column) — must be checked BEFORE the target_ref branch below (both
        # queries share the gochara_resonance_map table name). This fixture
        # discovers exactly the one event_class this responder was built for,
        # matching the single-class-per-test shape every test in this file uses.
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
        return []
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


# ===========================================================================
# ENGINE_VERSION bump (Codex C2 — concurrent-lane identical edit)
# ===========================================================================


def test_engine_version_is_v3_1():
    assert ENGINE_VERSION == "v3.1", (
        f"ENGINE_VERSION must be bumped to 'v3.1' (MR-12/Codex C2 writer output "
        f"shape change), got {ENGINE_VERSION!r}"
    )


# ===========================================================================
# EVENT_CLASSES gains a genuinely chain-canonical class
# ===========================================================================


def test_business_launch_is_now_in_event_classes():
    """business_launch (temporal_shape='chain' per migration 456) is the
    first genuinely chain-canonical class this writer produces rows for."""
    assert "business_launch" in EVENT_CLASSES


def test_marriage_remains_in_event_classes_unaffected():
    """marriage stays in EVENT_CLASSES exactly as before -- MR-12 does not
    remove or alter its (point-shaped) production."""
    assert "marriage" in EVENT_CLASSES


# ===========================================================================
# _normalize_milestone_template — the ontology-shape adapter
# ===========================================================================


def test_normalize_milestone_template_maps_offset_key():
    raw = [{"milestone_id": "a", "name_en": "A", "typical_offset_days_from_first": 30}]
    normalized = _normalize_milestone_template(raw, irreversibility_milestone=None)
    assert normalized == [
        {"milestone_id": "a", "typical_offset_days": 30, "is_irreversibility_milestone": False}
    ]


def test_normalize_milestone_template_flags_irreversibility_milestone():
    raw = [
        {"milestone_id": "decision", "typical_offset_days_from_first": 0},
        {"milestone_id": "first_revenue", "typical_offset_days_from_first": 120},
    ]
    normalized = _normalize_milestone_template(raw, irreversibility_milestone="first_revenue")
    flags = {entry["milestone_id"]: entry["is_irreversibility_milestone"] for entry in normalized}
    assert flags == {"decision": False, "first_revenue": True}


def test_normalize_milestone_template_no_irreversibility_milestone_declared():
    raw = [{"milestone_id": "a", "typical_offset_days_from_first": 0}]
    normalized = _normalize_milestone_template(raw, irreversibility_milestone=None)
    assert normalized[0]["is_irreversibility_milestone"] is False


# ===========================================================================
# _fetch_class_shape — live-read + documented fallback
# ===========================================================================


def test_fetch_class_shape_marriage_is_point_not_chain():
    """Ground truth check: the writer's own fallback table must agree with
    the live ontology that marriage is 'point', never silently 'chain'."""
    conn = _FakeConn(lambda sql, params: [])  # force fallback path
    shape, template, irrev = _fetch_class_shape(conn, "marriage")
    assert shape == "point", (
        f"marriage must fall back to temporal_shape='point' (matches live "
        f"brahma_event_ontology, migration 456) — got {shape!r}"
    )
    assert template is None


def test_fetch_class_shape_business_launch_is_chain():
    conn = _FakeConn(lambda sql, params: [])  # force fallback path
    shape, template, irrev = _fetch_class_shape(conn, "business_launch")
    assert shape == "chain"
    assert template is not None
    assert len(template) >= 2
    assert irrev == "first_revenue"


def test_fetch_class_shape_live_read_wins_over_fallback():
    """A live ontology row takes precedence over the documented fallback."""
    conn = _FakeConn(_ontology_responder(
        event_class="marriage",
        temporal_shape="point",
        milestone_template=None,
        irreversibility_milestone=None,
    ))
    shape, template, irrev = _fetch_class_shape(conn, "marriage")
    assert shape == "point"


def test_fetch_class_shape_unknown_class_defaults_to_interval_never_chain():
    """I4: an unrecognized event_class must never be invented as 'chain'."""
    conn = _FakeConn(lambda sql, params: [])
    shape, template, irrev = _fetch_class_shape(conn, "totally_unknown_class")
    assert shape == "interval"
    assert template is None


# ===========================================================================
# _build_chain_row — row-shape contract (same keys as _build_row)
# ===========================================================================


def test_build_chain_row_carries_milestone_fields():
    ms = MilestoneScore(
        milestone_id="first_revenue",
        milestone_jd=2445736.5 + 120.0,
        lambda_v3=0.61,
        is_above_threshold=True,
        is_irreversibility_milestone=True,
        intensity_result=None,
    )
    row = _build_chain_row(
        "482012f1-710e-4a25-994a-93821f5871aa", "business_launch", ms, "g3_1984_1994",
        valence="gain", is_adverse=False, generation=GENERATION_PROD,
        peak_basis=mod.peak_basis_vocab.LAMBDA_V3_ARGMAX,
    )
    assert row["temporal_shape"] == "chain"
    assert row["milestone_id"] == "first_revenue"
    assert row["is_irreversibility_milestone"] is True
    assert row["window_start"] == row["window_end"] == row["peak_date"]
    assert row["generation"] == GENERATION_PROD
    assert row["raw_intensity"] == pytest.approx(0.61)


def test_build_chain_row_same_key_set_as_interval_row():
    """The chain row dict must carry EXACTLY the columns INSERT_SQL/
    INSERT_PROD_SQL bind — no new DML is introduced for chains (I1
    mutation-guard coverage stays valid unchanged)."""
    from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import _build_row

    boundary = IntervalBoundary(
        enter_jd=2445736.5, exit_jd=2445737.5, peak_jd=2445737.0, peak_lambda=0.5,
        era_slice_key="g3_1984_1994",
    )
    interval_row = _build_row(
        "chart", "career_advancement", boundary, "g3_1984_1994",
        valence="gain", is_adverse=False,
        peak_basis=mod.peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
    )
    ms = MilestoneScore(
        milestone_id="m1", milestone_jd=2445737.0, lambda_v3=0.5,
        is_above_threshold=True, is_irreversibility_milestone=False,
        intensity_result=None,
    )
    chain_row = _build_chain_row(
        "chart", "business_launch", ms, "g3_1984_1994",
        valence="gain", is_adverse=False, generation=GENERATION_V3,
        peak_basis=mod.peak_basis_vocab.LAMBDA_V3_ARGMAX,
    )
    assert set(interval_row.keys()) == set(chain_row.keys())


def test_build_chain_row_computed_suppression_state_carries_quality_gates_never_bare_empty():
    """PARĪKṢAKA F-2 (2026-08-11): a computed chain row's suppression_state
    must carry the SAME truthful, structured quality_gates mechanism MR-42
    guarantees for interval rows (`_build_row`) -- never a bare `{}`. Before
    this fix, `_build_chain_row` built `suppression_state` from a
    standalone `{"coverage_quality": ...} if coverage_quality else {}` dict
    that (a) could be bare `{}` whenever coverage_quality was omitted and
    (b) NEVER forwarded the real `quality_gates` value already sitting in
    `milestone.intensity_result.term_breakdown` -- the exact §N.7-item-4
    defect MR-42 was written to kill, silently still reachable via the
    chain-row path alone. `_build_chain_row` now routes through the SAME
    `_build_suppression_state(term_breakdown, coverage_quality)` `_build_row`
    uses."""
    import types

    fake_intensity_result = types.SimpleNamespace(
        term_breakdown={
            "promise": 0.8, "permission": 0.6, "activity": 0.55, "quality_gates": 0.72,
            "lambda_v3": 0.2376, "activity_terms": [], "formula": "x",
        },
        lambda_v3_ci_low=0.19, lambda_v3_ci_high=0.28, ci_source="structural_prior",
    )
    ms = MilestoneScore(
        milestone_id="first_revenue", milestone_jd=2445736.5 + 120.0, lambda_v3=0.2376,
        is_above_threshold=True, is_irreversibility_milestone=True,
        intensity_result=fake_intensity_result,
    )
    coverage_note = {"tier": "rich", "target_count": 5, "note": "business_launch: 5 targets"}

    row = _build_chain_row(
        "482012f1-710e-4a25-994a-93821f5871aa", "business_launch", ms, "g3_1984_1994",
        valence="gain", is_adverse=False, generation=GENERATION_PROD,
        peak_basis=mod.peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET,
        coverage_quality=coverage_note,
    )
    parsed = json.loads(row["suppression_state"])
    assert parsed != {}
    assert parsed["mechanism"] == "quality_gates"
    assert parsed["value"] == 0.72
    assert parsed["coverage_quality"] == coverage_note

    # Same computed-row guarantee holds even without a coverage_quality note
    # (the I4-degrade-shaped object, per _build_suppression_state) -- still
    # never bare {}.
    row_no_coverage = _build_chain_row(
        "482012f1-710e-4a25-994a-93821f5871aa", "business_launch", ms, "g3_1984_1994",
        valence="gain", is_adverse=False, generation=GENERATION_PROD,
        peak_basis=mod.peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET,
    )
    parsed_no_coverage = json.loads(row_no_coverage["suppression_state"])
    assert parsed_no_coverage != {}
    assert parsed_no_coverage["mechanism"] == "quality_gates"
    assert parsed_no_coverage["value"] == 0.72
    assert "coverage_quality" not in parsed_no_coverage


# ===========================================================================
# run_substep — chain dispatch, end-to-end (fixture-only, no real DB)
# ===========================================================================


def _fake_score_chain_milestones(template_len: int):
    """Return a fake score_chain_milestones that produces one MilestoneScore
    per template entry, honoring milestone_id/is_irreversibility_milestone
    from the (already-normalized) template passed in."""
    def fn(swe, context, episode_anchor_jd, milestone_template, threshold_config):
        return [
            MilestoneScore(
                milestone_id=entry["milestone_id"],
                milestone_jd=episode_anchor_jd + entry["typical_offset_days"],
                lambda_v3=0.5,
                is_above_threshold=True,
                is_irreversibility_milestone=entry["is_irreversibility_milestone"],
                intensity_result=None,
            )
            for entry in milestone_template
        ]
    return fn


class TestRunSubstepChainDispatch:
    """The literal MR-12 deliverable: 'a marriage chain with >=2 milestones
    is produced' -- proven via a SYNTHETIC ontology fixture (see module
    docstring for why marriage is NOT chain-shaped in the live ontology
    today). This proves the mechanism is class-name-agnostic."""

    def test_synthetic_marriage_chain_produces_ge_2_milestone_rows(self, monkeypatch):
        raw_template = [
            {"milestone_id": "engagement", "name_en": "Engagement", "typical_offset_days_from_first": 0},
            {"milestone_id": "ceremony", "name_en": "Ceremony", "typical_offset_days_from_first": 60},
            {"milestone_id": "registration", "name_en": "Registration", "typical_offset_days_from_first": 90},
        ]
        conn = _FakeConn(_ontology_responder(
            event_class="marriage",
            temporal_shape="chain",  # SYNTHETIC override — not live ontology truth
            milestone_template=raw_template,
            irreversibility_milestone="ceremony",
            targets=["Venus"],
            stored_fp=None,
        ))
        ctx = _ctx(conn)
        writer = GocharaV3CenturyMaterializeWriter()
        steps = writer.plan_substeps(ctx)
        step = next(s for s in steps if s.key.startswith("marriage::"))

        fake_boundary = IntervalBoundary(
            enter_jd=2445736.5, exit_jd=2445736.5 + 200.0, peak_jd=2445736.5 + 90.0,
            peak_lambda=0.6, era_slice_key=step.key.split("::", 1)[1],
        )
        monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
        monkeypatch.setattr(mod, "score_chain_milestones", _fake_score_chain_milestones(3))
        _patch_swe_and_context(monkeypatch)

        result = writer.run_substep(ctx, step)

        assert result.rows_inserted >= 2, (
            f"Expected >= 2 milestone rows for a synthetic marriage chain, "
            f"got {result.rows_inserted}. notes={result.notes!r}"
        )
        assert result.rows_inserted == 3

        chain_inserts = [
            params for sql, params in conn.statements
            if sql.strip().upper().startswith("INSERT INTO KALA_GOCHARA_WINDOWS_V2")
            and isinstance(params, dict)
        ]
        assert len(chain_inserts) == 3
        milestone_ids = {row["milestone_id"] for row in chain_inserts}
        assert milestone_ids == {"engagement", "ceremony", "registration"}
        irrev_flags = {row["milestone_id"]: row["is_irreversibility_milestone"] for row in chain_inserts}
        assert irrev_flags == {"engagement": False, "ceremony": True, "registration": False}
        for row in chain_inserts:
            assert row["temporal_shape"] == "chain"

    def test_business_launch_real_chain_produces_prod_rows_generation_30(self, monkeypatch):
        """The REAL (non-synthetic) first chain-canonical class: business_launch,
        per the live ontology (migration 456)."""
        conn = _FakeConn(_ontology_responder(
            event_class="business_launch",
            temporal_shape="chain",
            milestone_template=_BUSINESS_LAUNCH_TEMPLATE_RAW,
            irreversibility_milestone="first_revenue",
            targets=["Jupiter"],
            stored_fp=None,
        ))
        ctx = _ctx(conn)
        writer = GocharaV3CenturyMaterializeWriter()
        steps = writer.plan_substeps(ctx)
        step = next(s for s in steps if s.key.startswith("business_launch::"))

        fake_boundary = IntervalBoundary(
            enter_jd=2445736.5, exit_jd=2445736.5 + 200.0, peak_jd=2445736.5 + 90.0,
            peak_lambda=0.6, era_slice_key=step.key.split("::", 1)[1],
        )
        monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
        monkeypatch.setattr(mod, "score_chain_milestones", _fake_score_chain_milestones(3))
        _patch_swe_and_context(monkeypatch)

        result = writer.run_substep(ctx, step)
        assert result.rows_inserted == 3

        prod_inserts = [
            params for sql, params in conn.statements
            if sql.strip().upper().startswith("INSERT INTO KALA_GOCHARA_WINDOWS")
            and "KALA_GOCHARA_WINDOWS_V2" not in sql.strip().upper()
            and isinstance(params, dict)
        ]
        assert len(prod_inserts) == 3
        for row in prod_inserts:
            assert row["generation"] == GENERATION_PROD == "3.0"
            assert row["temporal_shape"] == "chain"
            assert row["milestone_id"] in {"decision", "registration", "first_revenue"}
        irrev_row = next(r for r in prod_inserts if r["milestone_id"] == "first_revenue")
        assert irrev_row["is_irreversibility_milestone"] is True

    def test_chain_class_with_no_milestone_template_is_honest_skip_not_fabrication(self, monkeypatch):
        """I4: a chain-shaped class whose milestone_template is empty/unavailable
        gets a skipped_reason/quality note, never invented rows."""
        conn = _FakeConn(_ontology_responder(
            event_class="business_launch",
            temporal_shape="chain",
            milestone_template=None,  # honest gap
            irreversibility_milestone=None,
            targets=["Jupiter"],
            stored_fp=None,
        ))
        ctx = _ctx(conn)
        writer = GocharaV3CenturyMaterializeWriter()
        steps = writer.plan_substeps(ctx)
        step = next(s for s in steps if s.key.startswith("business_launch::"))

        called = []
        monkeypatch.setattr(
            mod, "find_threshold_crossings",
            lambda *a, **k: called.append(1) or [],
        )
        monkeypatch.setattr(mod, "score_chain_milestones", lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("score_chain_milestones must not be called with no template")
        ))
        _patch_swe_and_context(monkeypatch)

        result = writer.run_substep(ctx, step)
        assert result.rows_inserted == 0
        assert "skip" in result.notes.lower() or "honest" in result.notes.lower() or "gap" in result.notes.lower()

        writes = [
            (sql, params) for sql, params in conn.statements
            if sql.strip().upper().startswith(("DELETE", "INSERT"))
            and (TABLE in sql or PROD_TABLE in sql)
        ]
        assert writes == [], (
            f"No fabricated rows may be written for a chain class with no "
            f"milestone_template (I4). Got: {writes}"
        )

    def test_chain_rows_carry_generation_3_0_on_production_table(self, monkeypatch):
        """I1 mutation-guard invariant extends to chain rows: every DML on the
        production table carries generation='3.0'."""
        conn = _FakeConn(_ontology_responder(
            event_class="business_launch",
            temporal_shape="chain",
            milestone_template=_BUSINESS_LAUNCH_TEMPLATE_RAW,
            irreversibility_milestone="first_revenue",
            targets=["Jupiter"],
            stored_fp=None,
        ))
        ctx = _ctx(conn)
        writer = GocharaV3CenturyMaterializeWriter()
        steps = writer.plan_substeps(ctx)
        step = next(s for s in steps if s.key.startswith("business_launch::"))

        fake_boundary = IntervalBoundary(
            enter_jd=2445736.5, exit_jd=2445736.5 + 200.0, peak_jd=2445736.5 + 90.0,
            peak_lambda=0.6, era_slice_key=step.key.split("::", 1)[1],
        )
        monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
        monkeypatch.setattr(mod, "score_chain_milestones", _fake_score_chain_milestones(3))
        _patch_swe_and_context(monkeypatch)

        writer.run_substep(ctx, step)

        prod_deletes_and_inserts = [
            (sql, params) for sql, params in conn.statements
            if "KALA_GOCHARA_WINDOWS" in sql.strip().upper()
            and "KALA_GOCHARA_WINDOWS_V2" not in sql.strip().upper()
            and sql.strip().upper().startswith(("DELETE", "INSERT"))
        ]
        assert len(prod_deletes_and_inserts) > 0
        for sql, params in prod_deletes_and_inserts:
            if isinstance(params, dict):
                assert params.get("generation") == "3.0"
            else:
                assert "3.0" in str(params) or "generation" in sql.lower()

    def test_chain_dry_run_reports_would_produce_count_and_writes_nothing(self, monkeypatch):
        conn = _FakeConn(_ontology_responder(
            event_class="business_launch",
            temporal_shape="chain",
            milestone_template=_BUSINESS_LAUNCH_TEMPLATE_RAW,
            irreversibility_milestone="first_revenue",
            targets=["Jupiter"],
            stored_fp=None,
        ))
        ctx = ContextSpec(
            asset_id=ASSET_ID,
            build_id="test-build-mr12-dryrun",
            db_conn=conn,
            config={"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"},
            dry_run=True,
        )
        writer = GocharaV3CenturyMaterializeWriter()
        steps = writer.plan_substeps(ctx)
        step = next(s for s in steps if s.key.startswith("business_launch::"))

        fake_boundary = IntervalBoundary(
            enter_jd=2445736.5, exit_jd=2445736.5 + 200.0, peak_jd=2445736.5 + 90.0,
            peak_lambda=0.6, era_slice_key=step.key.split("::", 1)[1],
        )
        monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
        _patch_swe_and_context(monkeypatch)

        result = writer.run_substep(ctx, step)
        assert result.rows_inserted == 0
        writes = [
            (sql, params) for sql, params in conn.statements
            if sql.strip().upper().startswith(("DELETE", "INSERT"))
        ]
        assert writes == []

    def test_chain_rows_never_carry_argmax_basis(self, monkeypatch):
        """PK-R-8a (2026-08-11, ADJUDICATOR ruling) detector: a chain row's
        date is DECLARED by brahma_event_ontology's milestone_template
        (episode_anchor_jd + typical_offset_days), not LOCATED by a peak
        search -- LAMBDA_V3_ARGMAX means "a located extremum" and must
        NEVER appear on a chain row. Every chain row (both the v2/staging
        insert and the production insert) must carry peak_basis=
        ONTOLOGY_MILESTONE_OFFSET and resolution=NULL (chain rows are not
        hierarchy-tier-classified -- no era/month/day tier applies).

        Verify by reverting run_substep's chain branch to its pre-PK-R-8a
        stamp (`ms, "day", peak_basis_vocab.LAMBDA_V3_ARGMAX, None, None`)
        -- this test must go RED."""
        conn = _FakeConn(_ontology_responder(
            event_class="business_launch",
            temporal_shape="chain",
            milestone_template=_BUSINESS_LAUNCH_TEMPLATE_RAW,
            irreversibility_milestone="first_revenue",
            targets=["Jupiter"],
            stored_fp=None,
        ))
        ctx = _ctx(conn)
        writer = GocharaV3CenturyMaterializeWriter()
        steps = writer.plan_substeps(ctx)
        step = next(s for s in steps if s.key.startswith("business_launch::"))

        fake_boundary = IntervalBoundary(
            enter_jd=2445736.5, exit_jd=2445736.5 + 200.0, peak_jd=2445736.5 + 90.0,
            peak_lambda=0.6, era_slice_key=step.key.split("::", 1)[1],
        )
        monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: [fake_boundary])
        monkeypatch.setattr(mod, "score_chain_milestones", _fake_score_chain_milestones(3))
        _patch_swe_and_context(monkeypatch)

        result = writer.run_substep(ctx, step)
        assert result.rows_inserted == 3

        all_inserts = [
            params for sql, params in conn.statements
            if sql.strip().upper().startswith("INSERT INTO")
            and "KALA_GOCHARA_WINDOWS" in sql.strip().upper()
            and isinstance(params, dict)
        ]
        assert len(all_inserts) == 6, f"expected 3 v2 + 3 prod inserts, got {len(all_inserts)}"
        for row in all_inserts:
            assert row["peak_basis"] == mod.peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET, (
                f"PK-R-8a VIOLATION: chain row peak_basis={row['peak_basis']!r}, "
                f"expected ONTOLOGY_MILESTONE_OFFSET (never a located-peak basis "
                f"like LAMBDA_V3_ARGMAX on a DECLARED chain milestone)."
            )
            assert row["resolution"] is None, (
                f"PK-R-8a VIOLATION: chain row resolution={row['resolution']!r}, "
                f"expected NULL -- chain rows are not hierarchy-tier-classified."
            )
            assert row["parent_window_id"] is None
