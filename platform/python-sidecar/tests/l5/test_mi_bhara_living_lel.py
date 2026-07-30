"""
test_mi_bhara_living_lel — ṢAḌ-DARŚANA W2 Lane E · the LIVING-LEL CALIBRATION PLANE (item 39)
and the auto-filed prospective falsifier ledger (item 20).

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.6; brief `SHAD_DARSHANA_BRIEF_v2_0.md` §3 W2, §2.5.5.

§4 is GATE W2's own acceptance criterion, verbatim from the brief:

    "the LEL-absent scenario verified: a chart with no LEL serves structural-prior weights,
     `no_lived_history_recorded` STORY flags, and an honest calibration_maturity of zero —
     the D6 three-scenario contract GATED, not just designed"

so those assertions are written as a gate rather than as ordinary coverage: each of the three
clauses is asserted separately and by name, and the weights clause is asserted BIT-IDENTICALLY
against the priors, not approximately.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.mi_bhara.basis import FieldBasis, ParameterVector, SegmentBasis  # noqa: E402
from services.mi_bhara.fit import ScoredEvent, fit_event_class  # noqa: E402
from services.mi_bhara.living_lel import (  # noqa: E402
    NO_LIVED_HISTORY_FLAG,
    OUTCOME_HIT,
    OUTCOME_MISS,
    OUTCOME_UNRESOLVED,
    PROSPECTIVE_FOR_CALIBRATED,
    PROSPECTIVE_FOR_PROVISIONAL,
    RECALIBRATION_ASSET_SET,
    TIER_CALIBRATED,
    TIER_CALIBRATED_PROVISIONAL,
    TIER_CONCURRENT,
    TIER_STRUCTURAL_PRIOR,
    LelEventRef,
    OpenPrediction,
    calibration_receipt,
    compute_calibration_maturity,
    lapsed_predictions,
    no_lel_calibration_maturity,
    recalibration_dispatch,
    score_predictions_against_event,
    tier_for,
    tier_migrations,
)

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
CLASSES = ["career_change", "health_crisis", "relocation", "recognition"]

MCP_ENVELOPE_TS = (
    Path(__file__).parent.parent.parent.parent.parent
    / "platform-mcp" / "src" / "lib" / "kala_envelope.ts"
)


# ── §1 — item 20: falsifier auto-scoring ───────────────────────────────────────────────

def _pred(pid, cls, lo, hi, filed, window_id="kfw_deadbeefdeadbeefdeadbeef"):
    return OpenPrediction(
        prediction_id=pid,
        event_class=cls,
        window_start=lo,
        window_end=hi,
        filed_at_t=filed,
        window_id=window_id,
    )


def test_an_event_inside_the_window_is_a_hit_and_carries_its_lead_time():
    ev = LelEventRef(event_id="ev1", event_class="career_change", t=15_800.0)
    scored = score_predictions_against_event(ev, [_pred("p1", "career_change", 15_700, 15_900, 15_557)])
    assert len(scored) == 1
    assert scored[0].outcome == OUTCOME_HIT
    assert scored[0].matched_event_id == "ev1"
    assert scored[0].lead_time_days == pytest.approx(243.0)
    assert scored[0].is_prospective is True
    assert scored[0].window_id == "kfw_deadbeefdeadbeefdeadbeef"


def test_the_same_class_outside_the_window_is_a_miss_because_the_claim_was_about_WHEN():
    ev = LelEventRef(event_id="ev1", event_class="career_change", t=16_500.0)
    scored = score_predictions_against_event(ev, [_pred("p1", "career_change", 15_700, 15_900, 15_557)])
    assert scored[0].outcome == OUTCOME_MISS
    assert scored[0].matched_event_id is None


def test_a_different_class_does_not_resolve_the_prediction_at_all():
    ev = LelEventRef(event_id="ev1", event_class="health_crisis", t=15_800.0)
    assert score_predictions_against_event(ev, [_pred("p1", "career_change", 15_700, 15_900, 15_557)]) == []


def test_a_prediction_filed_AFTER_the_event_is_not_prospective():
    """Backfill wearing a prediction's clothes. `is_prospective` must be a fact about the
    filing time, not a label anyone chose (Elevation §7 — prospective/backfill separation)."""
    ev = LelEventRef(event_id="ev1", event_class="career_change", t=15_800.0)
    scored = score_predictions_against_event(ev, [_pred("p1", "career_change", 15_700, 15_900, 15_900)])
    assert scored[0].outcome == OUTCOME_HIT
    assert scored[0].is_prospective is False
    assert scored[0].lead_time_days == pytest.approx(-100.0)


def test_a_lapsed_window_is_unresolved_not_a_miss():
    """An unobserved window is not evidence the claim was wrong — only that nothing was
    recorded. Counting it as a miss would grade the model on the native's diary-keeping.
    (`brahma_prospective_ledger` carries the matching `lapsed_unobserved` lifecycle value,
    added by migration 466 for exactly this distinction.)"""
    out = lapsed_predictions([_pred("p1", "career_change", 15_700, 15_900, 15_557)], as_of_t=16_000.0)
    assert len(out) == 1 and out[0].outcome == OUTCOME_UNRESOLVED
    assert lapsed_predictions([_pred("p1", "career_change", 15_700, 15_900, 15_557)], as_of_t=15_800.0) == []


# ── §2 — the maturity index and tier migration ─────────────────────────────────────────

def test_event_class_coverage_is_a_fraction_of_the_ontology_not_of_the_events():
    """57 events all in one class must read as THIN coverage, which is the truth."""
    m = compute_calibration_maturity(
        lel_events=[LelEventRef(f"e{i}", "career_change", float(i)) for i in range(57)],
        prospective_resolutions=4,
        known_event_classes=CLASSES,
        weights_version="v1_2026-08-14_abhisek",
        chart_skill_score=0.19,
    )
    assert m.n_events == 57
    assert m.event_class_coverage == pytest.approx(0.25)
    assert m.prospective_resolutions == 4


def test_an_empty_ontology_is_zero_coverage_not_a_division_error():
    m = compute_calibration_maturity(
        lel_events=[], prospective_resolutions=0, known_event_classes=[],
        weights_version=None, chart_skill_score=None,
    )
    assert m.event_class_coverage == 0.0


def test_tier_promotion_requires_the_prospective_record_not_merely_a_long_diary():
    assert tier_for(TIER_CONCURRENT, 0) == TIER_CONCURRENT
    assert tier_for(TIER_CONCURRENT, PROSPECTIVE_FOR_PROVISIONAL) == TIER_CALIBRATED_PROVISIONAL
    assert tier_for(TIER_CONCURRENT, PROSPECTIVE_FOR_CALIBRATED) == TIER_CALIBRATED


def test_a_structurally_weak_window_is_never_promoted_by_maturity_alone():
    """§5.6: `confidence_tier` is the MINIMUM across robustness dimensions, and maturity may
    only promote above `concurrent`. A window that failed a robustness check does not become
    `calibrated` because the chart has a long history."""
    assert tier_for(TIER_STRUCTURAL_PRIOR, 999) == TIER_STRUCTURAL_PRIOR


def test_tier_migrations_are_deterministic_and_report_only_actual_changes():
    before = {"career": TIER_STRUCTURAL_PRIOR, "health": TIER_CONCURRENT, "wealth": TIER_CONCURRENT}
    after = {"career": TIER_CALIBRATED_PROVISIONAL, "health": TIER_CONCURRENT, "wealth": TIER_CALIBRATED}
    migs = tier_migrations(before, after)
    assert [m.scope for m in migs] == ["career", "wealth"], "sorted, and no no-op rows"
    assert migs[0].from_tier == TIER_STRUCTURAL_PRIOR
    assert migs[0].to_tier == TIER_CALIBRATED_PROVISIONAL


# ── §3 — the portal calibration receipt (§7.6, a W2 deliverable) ───────────────────────

def test_the_receipt_has_the_exact_shape_the_design_specifies():
    ev = LelEventRef("ev1", "career_change", 15_800.0)
    scored = score_predictions_against_event(
        ev,
        [
            _pred("p1", "career_change", 15_700, 15_900, 15_557),
            _pred("p2", "career_change", 15_750, 15_850, 15_600),
        ],
    )
    before = no_lel_calibration_maturity()
    after = compute_calibration_maturity(
        lel_events=[ev], prospective_resolutions=2, known_event_classes=CLASSES,
        weights_version="v1_2026-08-14_abhisek", chart_skill_score=0.19,
    )
    receipt = calibration_receipt(
        scored=scored,
        maturity_before=before,
        maturity_after=after,
        migrations=tier_migrations(
            {"career": TIER_STRUCTURAL_PRIOR}, {"career": TIER_CALIBRATED_PROVISIONAL}
        ),
    )
    assert set(receipt) == {
        "predictions_scored", "hits", "misses", "unresolved",
        "maturity_before", "maturity_after", "tier_migrations",
    }
    assert set(receipt["predictions_scored"][0]) == {
        "prediction_id", "window_id", "outcome", "lead_time_days", "is_prospective"
    }
    assert receipt["hits"] == 2 and receipt["misses"] == 0
    assert receipt["tier_migrations"] == [
        {"scope": "career", "from": TIER_STRUCTURAL_PRIOR, "to": TIER_CALIBRATED_PROVISIONAL}
    ]


def test_the_receipt_counts_are_derived_from_its_own_rows_and_cannot_disagree_with_them():
    """A receipt whose headline numbers did not add up to its own row list would be exactly
    the populated-looking-but-hollow envelope §N.6 item 3 forbids."""
    ev = LelEventRef("ev1", "career_change", 16_500.0)
    scored = score_predictions_against_event(ev, [_pred("p1", "career_change", 15_700, 15_900, 15_557)])
    scored += lapsed_predictions([_pred("p2", "career_change", 14_000, 14_100, 13_900)], as_of_t=16_500.0)
    receipt = calibration_receipt(
        scored=scored,
        maturity_before=no_lel_calibration_maturity(),
        maturity_after=no_lel_calibration_maturity(),
        migrations=[],
    )
    assert receipt["hits"] + receipt["misses"] + receipt["unresolved"] == len(
        receipt["predictions_scored"]
    )
    assert receipt["misses"] == 1 and receipt["unresolved"] == 1


# ── §2.5.5 — the recalibration is a TRACKED build run, never a side channel ────────────

def test_the_lel_append_dispatch_is_a_standard_scoped_orchestrator_build_run():
    d = recalibration_dispatch(chart_id=CHART, triggering_event_ids=["ev1", "ev2"])
    assert d.to_request_body() == {
        "chart_id": CHART,
        "scope": "asset_set",
        "scope_target": "mi_bhara",
        "action": "rebuild",
    }
    assert d.reason == "lel_append"
    assert d.triggering_event_ids == ("ev1", "ev2")
    assert RECALIBRATION_ASSET_SET == ("mi_bhara",)


def test_the_dispatch_module_cannot_itself_recompute_anything():
    """§2.5.5's "NO SIDE-CHANNEL RECOMPUTATION", asserted structurally rather than promised:
    `living_lel.py` opens no connection, imports no optimiser, and calls no writer. A module
    that could both decide to recalibrate and perform the recalculation is one refactor away
    from being the side channel the rule forbids."""
    src = (
        Path(__file__).parent.parent.parent / "services" / "mi_bhara" / "living_lel.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("psycopg", "cursor(", "execute(", "scipy", "asset_throughput", "commit("):
        assert forbidden not in src, f"living_lel.py must not reference {forbidden!r}"


# ══════════════════════════════════════════════════════════════════════════════════════
#  §4 — GATE W2's LEL-ABSENT ACCEPTANCE CRITERION (brief §3 W2; design §7.6)
# ══════════════════════════════════════════════════════════════════════════════════════

def test_GATE_lel_absent_clause_1_structural_prior_weights_bit_identical():
    """Clause 1 of 3: "a chart with no LEL serves STRUCTURAL-PRIOR WEIGHTS".

    Bit-identical, not approximately: `n_eff = 0 ⇒ φ̂ = φ⁰` exactly, with no branch anywhere
    in the fitting path. The priors here are the twelve §5.1 C-5 covariates plus two clocks
    and one vighna — the real parameter shape, not a toy.
    """
    import math

    covariates = tuple(f"x{i}" for i in range(1, 13))
    basis = FieldBasis(
        event_class="career_change",
        system_ids=("vimshottari", "yogini"),
        covariate_ids=covariates,
        vighna_ids=("vedha",),
        segments=(
            SegmentBasis(
                0.0, 36_525.0, math.log(1e-4),
                log_a_start=(0.3, 0.1), log_a_end=(0.4, 0.2),
                x_start=tuple(0.1 * i for i in range(12)),
                x_end=tuple(0.05 * i for i in range(12)),
                u_start=(0.2,), u_end=(0.4,),
            ),
        ),
    )
    prior = ParameterVector(
        w=(0.60, 0.35),
        beta=(0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.15, 0.25, 0.35, 0.45, 0.55),
        rho=(0.40,),
    )
    result = fit_event_class(basis=basis, events=[], prior=prior, horizon_end=36_525.0)

    assert result.theta_shipped.w == prior.w
    assert result.theta_shipped.beta == prior.beta
    assert result.theta_shipped.rho == prior.rho
    assert all(o.n_eff == 0 for o in result.shrinkage)
    assert all(o.shrunk_value == o.prior_value for o in result.shrinkage)
    assert result.any_clipped is False


def test_GATE_lel_absent_clause_2_no_lived_history_recorded_flag_is_available_by_name():
    """Clause 2 of 3: "`no_lived_history_recorded` STORY flags".

    The flag is a named constant so the STORY facade and the writer cannot spell it
    differently — a flag that two surfaces spell two ways is a flag neither can be filtered on.
    """
    assert NO_LIVED_HISTORY_FLAG == "no_lived_history_recorded"


def test_GATE_lel_absent_clause_3_calibration_maturity_is_an_honest_zero():
    """Clause 3 of 3: "an honest calibration_maturity of ZERO".

    Honest zero, not absent block and not null-everything: `n_events`,
    `prospective_resolutions` and `event_class_coverage` are genuine ZEROS (the measurement
    was made and it came out zero), while `weights_version` and `skill_score` are genuine
    NULLS (no calibration produced a version; skill is not measurable). Conflating the two
    would be either an invented measurement or a hidden one.
    """
    m = compute_calibration_maturity(
        lel_events=[],
        prospective_resolutions=0,
        known_event_classes=CLASSES,
        weights_version="v0_classical",   # a version IS pinned — it is a prior, not a fit
        chart_skill_score=None,
    )
    assert m == no_lel_calibration_maturity()
    assert m.to_envelope_dict() == {
        "n_events": 0,
        "prospective_resolutions": 0,
        "event_class_coverage": 0,
        "weights_version": None,
        "skill_score": None,
    }


def test_GATE_the_python_and_typescript_lel_absent_maturity_agree_field_for_field():
    """The same honest zero must be served whether the envelope was assembled by the
    TypeScript facade (`kala_envelope.ts::noLelCalibrationMaturity`) or filled from this
    writer. Asserted by reading the TS source, so the two cannot drift silently."""
    assert MCP_ENVELOPE_TS.exists(), MCP_ENVELOPE_TS
    ts = MCP_ENVELOPE_TS.read_text(encoding="utf-8")
    start = ts.index("export function noLelCalibrationMaturity()")
    body = ts[start : ts.index("}", ts.index("return {", start))]
    for field, literal in (
        ("n_events", "0"),
        ("prospective_resolutions", "0"),
        ("event_class_coverage", "0"),
        ("weights_version", "null"),
        ("skill_score", "null"),
    ):
        assert f"{field}: {literal}" in body, (
            f"kala_envelope.ts::noLelCalibrationMaturity has drifted from the Python twin at "
            f"field {field!r}"
        )


def test_GATE_lel_absent_scoring_yields_underpowered_rather_than_a_flattering_zero():
    """The fourth consequence §7.6's table names: `skill_state = 'underpowered'`. A chart with
    no history must not report skill 0 as though zero had been MEASURED."""
    from services.mi_bhara.skill import SKILL_UNDERPOWERED, compute_skill

    s = compute_skill(
        chart_id=CHART,
        weights_version="v0_classical",
        event_class="career_change",
        model_log_intensity=[],
        null_log_intensity_per_replicate=[],
        model_integral=0.0,
        null_integrals=[],
    )
    assert s.skill_state == SKILL_UNDERPOWERED
    assert s.n_events == 0


def test_GATE_the_lel_growing_scenario_migrates_tiers_visibly():
    """The third D6 scenario: tiers migrate visibly and auditably as prospective resolutions
    accrue. Asserted as the actual promotion sequence, so a threshold change is visible."""
    seq = [tier_for(TIER_CONCURRENT, n) for n in (0, 2, 3, 11, 12)]
    assert seq == [
        TIER_CONCURRENT,
        TIER_CONCURRENT,
        TIER_CALIBRATED_PROVISIONAL,
        TIER_CALIBRATED_PROVISIONAL,
        TIER_CALIBRATED,
    ]


def test_GATE_events_from_another_chart_can_never_enter_this_charts_maturity():
    """`life_events` is chart-scoped since migration 423 and the LEL read is `(chart_id,
    event_id)`-keyed. The maturity computation is over the events it is HANDED, so this
    asserts the shape of the contract: nothing here reaches for a global event set."""
    src = (
        Path(__file__).parent.parent.parent / "services" / "mi_bhara" / "db.py"
    ).read_text(encoding="utf-8")
    lel_query_start = src.index("def fetch_lel_events")
    lel_query = src[lel_query_start : src.index("def ", lel_query_start + 10)]
    assert "WHERE chart_id = %s" in lel_query, (
        "the LEL read must be chart-scoped — an unscoped read would pull another native's "
        "history into this chart's calibration"
    )
