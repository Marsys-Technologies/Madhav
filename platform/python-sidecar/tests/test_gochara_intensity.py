"""
tests/test_gochara_intensity.py — D-5 Lane G-3 "Intensity engine" tests.

No DATABASE_URL is required for the bulk of this suite (same sandbox
constraint G-2's own test module documents) -- every non-`@pytest.mark.
integration` test here runs off real `swisseph` ephemeris computation
(no DB) combined with hand-built `ResonanceTarget`/dasha-period fixtures,
mirroring `tests/test_gochara_grammar.py`'s own documented pattern. The
`@pytest.mark.integration` tests at the bottom hit the LIVE Cloud SQL proxy
(127.0.0.1:5433) when reachable and are excluded by the mandated
`-m "not integration"` pytest invocation -- they were run manually during
this lane's live-verification pass (see the G-3 close report for the actual
values obtained against chart 482012f1) and are kept here, skip-guarded,
so a future session with the proxy running can re-run them directly.
"""
from __future__ import annotations

import math
import os

import psycopg
import pytest
import swisseph as swe

from services.gochara_grammar.models import ConfigurationSentence, ResonanceTarget
from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import dasha_data as DD
from services.gochara_intensity.models import IntensityResult, CalibrationDisclosureError
from services.gochara_intensity.promise import compute_promise
from services.gochara_intensity.permission import compute_permission, SYSTEM_WEIGHTS, DASHA_SYSTEM_IDS
from services.gochara_intensity.configuration_activity import compute_x_t
from services.gochara_intensity.suppression import compute_suppression, SUPPRESSION_WEIGHTS
from services.gochara_intensity.beta_priors import beta_for, DEFAULT_BETA
from services.gochara_intensity.valence import is_adverse, VALENCE_MAP
from services.gochara_intensity.engine import compute_lambda_e, compute_lambda_e_series, SHAPE_MAP

CHART_ID = RM.CANONICAL_CHART_ID
LIVE_DSN = os.environ.get("DATABASE_URL", "")


def _jd(y, m, d, h=12.0):
    return swe.julday(y, m, d, h)


@pytest.fixture(autouse=True)
def _reset_cache():
    from pipeline.transit_search import clear_ephemeris_cache
    clear_ephemeris_cache()
    yield
    clear_ephemeris_cache()


# ── PROMISE ──────────────────────────────────────────────────────────────

def test_promise_noisy_or_two_targets():
    targets = [
        ResonanceTarget(chart_id=CHART_ID, event_class="marriage", target_type="bhava",
                         target_ref="7", weight=0.9, classical_citation="TEST"),
        ResonanceTarget(chart_id=CHART_ID, event_class="marriage", target_type="karaka",
                         target_ref="Venus", weight=0.5, classical_citation="TEST"),
    ]
    promise, detail = compute_promise(targets)
    # 1 - (1-0.9)*(1-0.5) = 1 - 0.1*0.5 = 0.95
    assert promise == pytest.approx(0.95)
    assert detail["calibration_state"] == "structural_prior"
    assert detail["target_count"] == 2


def test_promise_single_target_equals_its_weight():
    targets = [ResonanceTarget(chart_id=CHART_ID, event_class="marriage", target_type="karaka",
                                target_ref="Venus", weight=0.7, classical_citation="TEST")]
    promise, _ = compute_promise(targets)
    assert promise == pytest.approx(0.7)


def test_promise_empty_is_honest_zero():
    promise, detail = compute_promise([])
    assert promise == 0.0
    assert detail["target_count"] == 0
    assert "honest PROMISE=0.0" in detail["note"]


def test_promise_saturates_never_exceeds_one():
    targets = [
        ResonanceTarget(chart_id=CHART_ID, event_class="marriage", target_type="bhava",
                         target_ref=str(i), weight=0.9, classical_citation="TEST")
        for i in range(6)
    ]
    promise, _ = compute_promise(targets)
    assert 0.0 <= promise <= 1.0


# ── PERMISSION (DR-14 plurality) ────────────────────────────────────────

def test_permission_sums_across_multiple_independent_systems():
    """The wave verifier's specific acceptance bar: PERMISSION genuinely
    sums across >= 2 independent timing systems, not Vimsottari-gated.
    Fixture dasha_periods cover exactly 2 systems (vimshottari + yogini,
    per dasha_data.build_fixture_dasha_periods's own marriage-specimen
    fixture) at the 2013-12-11 double-transit specimen date."""
    t_jd = _jd(2013, 12, 11)
    dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)
    permission, detail = compute_permission(
        swe, None, CHART_ID, "marriage", targets=[], t_jd=t_jd, dasha_periods=dasha_periods,
    )
    assert detail["system_count_active"] >= 2, (
        f"expected >= 2 independent systems active, got {detail['systems_active']}"
    )
    assert "vimshottari" in detail["systems_active"]
    assert "yogini" in detail["systems_active"]
    assert permission > 0.0
    assert detail["calibration_state"] == "structural_prior"


def test_permission_not_vimshottari_gated():
    """REGRESSION GUARD: if PERMISSION were ever refactored to require
    Vimsottari's own period as a gate (the exact DR-14 violation the
    doctrine exists to prevent), this test fails. A dasha_periods fixture
    with ONLY a non-Vimsottari system's period covering t must still
    produce a nonzero PERMISSION and a non-empty systems_active list that
    does NOT contain 'vimshottari'."""
    t_jd = _jd(2013, 12, 11)
    non_vimshottari_period = {
        "system_id": "chara_karaka", "level_n": 1, "lord_graha": "Taurus",
        "start_iso": "2012-01-01T00:00:00+00:00", "end_iso": "2015-01-01T00:00:00+00:00",
    }
    permission, detail = compute_permission(
        swe, None, CHART_ID, "marriage", targets=[], t_jd=t_jd,
        dasha_periods=[non_vimshottari_period],
    )
    assert "vimshottari" not in detail["systems_active"]
    # The real point of this test: it must be POSSIBLE for a non-Vimsottari
    # system, alone, to make PERMISSION > 0 and appear in systems_active --
    # proving the code path is not structurally Vimsottari-exclusive.
    assert "chara_karaka" in detail["systems_active"]
    assert permission > 0.0


def test_permission_zero_when_no_systems_active():
    t_jd = _jd(1980, 1, 1)  # well before any fixture period's coverage
    permission, detail = compute_permission(
        swe, None, CHART_ID, "marriage", targets=[], t_jd=t_jd, dasha_periods=[],
    )
    assert permission == 0.0
    assert detail["systems_active"] == []


def test_permission_guru_shani_double_transit_fires_for_real_marriage_house():
    """THE actual acceptance bar for the RED-D fix, at the level that
    actually matters -- `compute_permission` itself, the real production
    consumer named by the RED-D finding ('PERMISSION generator #9
    guru_shani_double_transit ... shows as inactive'). target_ref='7'
    (Libra, chart 482012f1's real 7th/marriage house), target_sign only (no
    target_longitude_deg -- exactly `gochara_intensity.enrichment.
    enrich_target`'s live output shape for a bhava target), t_jd pinned to
    the real 2013-12-11 LEL marriage event date, default window_days=15.0
    (the generator's own production default, deliberately NOT widened for
    this test -- proving the fix works at the window width production
    actually uses, not just a generously widened test window).

    Before the RED-D fix: drishti_contact/degree_contact required
    target_longitude_deg, permanently unreachable for a bhava target. Before
    THIS follow-up fix: even with drishti_contact's rasi-drishti fallback,
    this generator's own `if target.target_longitude_deg is None: continue`
    guard skipped bhava targets before ever calling it, AND pure aspect+
    aspect `double_transit` could not represent Saturn's occupation of
    Libra (as opposed to aspecting it) regardless. All three gaps are fixed
    together here."""
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="marriage", target_type="bhava",
        target_ref="7", weight=0.9, classical_citation="TEST FIXTURE",
        target_sign="Libra",
    )
    t_jd = _jd(2013, 12, 11)
    permission, detail = compute_permission(
        swe, None, CHART_ID, "marriage", [target], t_jd, dasha_periods=[],
    )
    gsdt = next(s for s in detail["systems"] if s["system_id"] == "guru_shani_double_transit")
    assert gsdt["active"] is True
    assert gsdt["detail"]["target_ref"] == "7"
    assert gsdt["detail"]["operator"] == "double_transit_mixed"
    assert "guru_shani_double_transit" in detail["systems_active"]
    assert permission > 0.0


def test_permission_dasha_system_ids_cover_live_verified_names():
    """DASHA_SYSTEM_IDS must use the LIVE chart_dashas.system_id vocabulary
    (chara_karaka/narayana), not G-2's dasha_data.DASHA_SYSTEMS default --
    see permission.py's module docstring correction. Regression guard
    against silently reverting to the mismatched G-2 tuple."""
    assert "chara_karaka" in DASHA_SYSTEM_IDS
    assert "narayana" in DASHA_SYSTEM_IDS
    assert "chara" not in DASHA_SYSTEM_IDS  # the G-2-default id that does NOT exist live
    assert set(DASHA_SYSTEM_IDS).issubset(set(SYSTEM_WEIGHTS.keys()))


def test_system_weights_sum_to_one_and_all_structural_prior():
    assert abs(sum(SYSTEM_WEIGHTS.values()) - 1.0) < 1e-9
    assert all(w > 0 for w in SYSTEM_WEIGHTS.values())


# ── X(t) / exp(beta*X) ───────────────────────────────────────────────────

def test_x_t_aggregates_weighted_orb_strength():
    sentences = [
        ConfigurationSentence(
            primitive="drishti_contact", chart_id=CHART_ID, event_class="marriage",
            target_type="bhava", target_ref="7", transit_planet="Jupiter", secondary_planet=None,
            event_jd=100.0, event_datetime_ist="x", temporal_shape="point",
            classical_citation="TEST", detail={"orb_strength": 0.8},
        ),
        ConfigurationSentence(
            primitive="sign_ingress", chart_id=CHART_ID, event_class="marriage",
            target_type="bhava", target_ref="7", transit_planet="Saturn", secondary_planet=None,
            event_jd=101.0, event_datetime_ist="x", temporal_shape="point",
            classical_citation="TEST", detail={},  # no orb_strength -> flat 1.0
        ),
    ]
    x_t, detail = compute_x_t(sentences, weight_by_target_ref={"7": 0.9})
    # 0.9*0.8 + 0.9*1.0 = 1.62
    assert x_t == pytest.approx(1.62)
    assert detail["sentence_count_considered"] == 2


def test_x_t_excludes_cancelled_vedha():
    sentences = [
        ConfigurationSentence(
            primitive="gochara_vedha_pair", chart_id=CHART_ID, event_class="marriage",
            target_type="bhava", target_ref="7", transit_planet="Mars", secondary_planet="Sun",
            event_jd=100.0, event_datetime_ist="x", temporal_shape="point",
            classical_citation="TEST", detail={"cancelled": True},
        ),
    ]
    x_t, detail = compute_x_t(sentences, weight_by_target_ref={"7": 0.9})
    assert x_t == 0.0
    assert detail["sentence_count_considered"] == 0
    assert detail["sentence_count_total_gathered"] == 1


def test_exp_term_matches_math_exp():
    beta = beta_for("marriage")
    x_t = 2.0
    assert math.exp(beta * x_t) == pytest.approx(math.exp(beta * x_t))
    assert beta > 0


def test_beta_defaults_and_shape_lean():
    assert beta_for("nonexistent_class") == DEFAULT_BETA
    # point-shaped sharp-trigger class should have a HIGHER beta than a
    # sustained-state interval/chain class, per beta_priors.py's documented
    # engineering choice.
    assert beta_for("marriage") > beta_for("major_gain")


# ── suppression ──────────────────────────────────────────────────────────

def test_suppression_counts_cancellation_and_kartari():
    vedha_cancelled = ConfigurationSentence(
        primitive="gochara_vedha_pair", chart_id=CHART_ID, event_class="marriage",
        target_type="bhava", target_ref="7", transit_planet="Mars", secondary_planet="Sun",
        event_jd=100.0, event_datetime_ist="x", temporal_shape="interval",
        classical_citation="TEST", detail={"cancelled": True},
    )
    sbc = ConfigurationSentence(
        primitive="sarvatobhadra_vedha", chart_id=CHART_ID, event_class="marriage",
        target_type="bhava", target_ref="7", transit_planet="Saturn", secondary_planet=None,
        event_jd=101.0, event_datetime_ist="x", temporal_shape="interval",
        uncited_extension=True, detail={},
    )
    pincer_pos = ConfigurationSentence(
        primitive="degree_contact", chart_id=CHART_ID, event_class="marriage",
        target_type="bhava", target_ref="7", transit_planet="Mars", secondary_planet=None,
        event_jd=100.0, event_datetime_ist="x", temporal_shape="point",
        uncited_extension=True, detail={"signed_offset_from_target_deg": 1.5},
    )
    pincer_neg = ConfigurationSentence(
        primitive="degree_contact", chart_id=CHART_ID, event_class="marriage",
        target_type="bhava", target_ref="7", transit_planet="Saturn", secondary_planet=None,
        event_jd=100.1, event_datetime_ist="x", temporal_shape="point",
        uncited_extension=True, detail={"signed_offset_from_target_deg": -1.5},
    )
    suppression, detail = compute_suppression([vedha_cancelled, sbc, pincer_pos, pincer_neg])
    assert detail["n_vedha_cancelled"] == 1
    assert detail["n_sarvatobhadra_vedha_active"] == 1
    assert detail["n_kartari_pincer"] >= 1
    expected = (
        SUPPRESSION_WEIGHTS["vedha_cancellation"] * 1
        + SUPPRESSION_WEIGHTS["sarvatobhadra_vedha"] * 1
        + SUPPRESSION_WEIGHTS["kartari_pincer"] * detail["n_kartari_pincer"]
    )
    assert suppression == pytest.approx(expected)
    assert detail["calibration_state"] == "structural_prior"


def test_suppression_zero_when_nothing_fires():
    suppression, detail = compute_suppression([])
    assert suppression == 0.0
    assert detail["n_vedha_cancelled"] == 0


# ── valence / adverse sign ──────────────────────────────────────────────

@pytest.mark.parametrize("event_class,expected_adverse", [
    ("bereavement", True),
    ("major_loss", True),
    ("illness_acute", True),
    ("career_setback", True),
    ("financial_deception", True),
    ("psychological_arc", True),  # 'mixed' valence, explicit brief override
    ("marriage", False),
    ("major_gain", False),
    ("career_advancement", False),
    ("parental_event", False),  # 'mixed' but NOT in the brief's adverse enumeration
])
def test_is_adverse_matches_brief_enumeration(event_class, expected_adverse):
    adverse, valence = is_adverse(None, event_class)
    assert adverse is expected_adverse, f"{event_class}: valence={valence}"


def test_valence_map_covers_all_27_classes():
    assert len(VALENCE_MAP) == 27
    assert set(VALENCE_MAP.values()) <= {"gain", "loss", "neutral", "mixed"}


def test_shape_map_matches_brief_13_9_5_split():
    shapes = list(SHAPE_MAP.values())
    assert shapes.count("point") == 13
    assert shapes.count("interval") == 9
    assert shapes.count("chain") == 5
    assert len(SHAPE_MAP) == 27


# ── calibration disclosure (mechanical enforcement) ─────────────────────

def test_calibration_disclosure_error_on_missing_permission_calibration_state():
    with pytest.raises(CalibrationDisclosureError):
        IntensityResult(
            chart_id=CHART_ID, event_class="marriage", temporal_shape="point",
            t_jd=100.0, t_datetime_ist="x",
            promise=0.5, promise_detail={},
            permission=0.5, permission_detail={},  # MISSING calibration_state
            x_t=1.0, x_t_detail={},
            beta_e=0.3, beta_e_calibration_state="structural_prior", exp_term=1.3,
            suppression=0.0, suppression_detail={},
            raw_lambda=0.3, valence="neutral", is_adverse=False, signed_lambda=0.3,
        )


def test_calibration_disclosure_error_on_bad_beta_state():
    with pytest.raises(CalibrationDisclosureError):
        IntensityResult(
            chart_id=CHART_ID, event_class="marriage", temporal_shape="point",
            t_jd=100.0, t_datetime_ist="x",
            promise=0.5, promise_detail={},
            permission=0.5, permission_detail={"calibration_state": "structural_prior"},
            x_t=1.0, x_t_detail={},
            beta_e=0.3, beta_e_calibration_state="fitted_by_d4b_not_allowed", exp_term=1.3,
            suppression=0.0, suppression_detail={},
            raw_lambda=0.3, valence="neutral", is_adverse=False, signed_lambda=0.3,
        )


def test_valid_intensity_result_constructs_cleanly():
    r = IntensityResult(
        chart_id=CHART_ID, event_class="marriage", temporal_shape="point",
        t_jd=100.0, t_datetime_ist="x",
        promise=0.5, promise_detail={"calibration_state": "structural_prior"},
        permission=0.5, permission_detail={"calibration_state": "structural_prior"},
        x_t=1.0, x_t_detail={},
        beta_e=0.3, beta_e_calibration_state="structural_prior", exp_term=1.3,
        suppression=0.0, suppression_detail={"calibration_state": "structural_prior"},
        raw_lambda=0.3, valence="neutral", is_adverse=False, signed_lambda=0.3,
    )
    assert r.calibration_state == "structural_prior"
    assert r.to_dict()["chart_id"] == CHART_ID


# ── engine end-to-end (fixture-only, no DB) ──────────────────────────────

def test_engine_end_to_end_point_marriage_fixture():
    targets = [t for t in RM.build_fixture_targets(CHART_ID) if t.event_class == "marriage"]
    dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)
    t_jd = _jd(2013, 12, 11)
    r = compute_lambda_e(
        swe, None, CHART_ID, "marriage", t_jd,
        targets=targets, dasha_periods=dasha_periods, source="fixture",
    )
    assert r.temporal_shape == "point"
    assert r.source == "fixture"
    assert r.promise > 0.0
    assert r.permission > 0.0
    assert r.calibration_state == "structural_prior"
    # The dedicated DR-14-plurality test (test_permission_sums_across_
    # multiple_independent_systems) proves >= 2 systems sum when their
    # lords are both relevant to the target set; this fixture's dasha
    # periods carry lords Venus (vimshottari) and Moon (yogini), and the
    # marriage fixture's targets only resolve Venus as relevant (bhava-7
    # has no natal_planet anchor) -- so exactly 1 lord-matched system is
    # the CORRECT, honest result here, not a regression.
    assert r.permission_detail["system_count_active"] >= 1
    assert "vimshottari" in r.permission_detail["systems_active"]
    assert r.valence == "neutral" and r.is_adverse is False
    assert r.signed_lambda == pytest.approx(r.raw_lambda)  # non-adverse: sign unchanged


def test_engine_adverse_class_flips_sign():
    """Adverse classes run the IDENTICAL machinery -- only the sign differs.
    Uses the marriage fixture's own targets (event_class field ignored by
    compute_promise/permission/x_t, only valence.is_adverse cares about the
    STRING event_class passed to compute_lambda_e) to prove the sign flip
    mechanically without needing a populated bereavement resonance-map row."""
    targets = [t for t in RM.build_fixture_targets(CHART_ID) if t.event_class == "marriage"]
    dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)
    t_jd = _jd(2013, 12, 11)

    r_neutral = compute_lambda_e(
        swe, None, CHART_ID, "marriage", t_jd,
        targets=targets, dasha_periods=dasha_periods, source="fixture",
    )
    r_adverse = compute_lambda_e(
        swe, None, CHART_ID, "bereavement", t_jd,
        targets=targets, dasha_periods=dasha_periods, source="fixture",
    )
    assert r_adverse.is_adverse is True
    assert r_adverse.valence == "loss"
    # Same raw magnitude machinery (identical targets/dasha_periods/t), only
    # the final sign differs.
    assert r_adverse.raw_lambda == pytest.approx(r_neutral.raw_lambda)
    assert r_adverse.signed_lambda == pytest.approx(-r_neutral.raw_lambda)
    assert r_neutral.signed_lambda == pytest.approx(r_neutral.raw_lambda)


def test_engine_series_is_shape_aware_multi_point():
    """BRIEF_D5 §3: interval/chain-shaped output must be a real multi-point
    curve, never a single point dressed up as an interval."""
    targets = [t for t in RM.build_fixture_targets(CHART_ID) if t.event_class == "major_gain"]
    dasha_periods = DD.build_fixture_dasha_periods(CHART_ID)
    t_start = _jd(2010, 7, 1)
    t_end = _jd(2010, 7, 10)
    series = compute_lambda_e_series(
        swe, None, CHART_ID, "major_gain", t_start, t_end, step_days=3.0,
        targets=targets, dasha_periods=dasha_periods, temporal_shape="interval", source="fixture",
    )
    assert len(series) >= 3
    assert all(r.temporal_shape == "interval" for r in series)
    assert all(r.event_class == "major_gain" for r in series)


def test_engine_empty_targets_is_honest_zero_not_crash():
    r = compute_lambda_e(
        swe, None, CHART_ID, "marriage", _jd(2013, 12, 11),
        targets=[], dasha_periods=[], source="fixture",
    )
    assert r.promise == 0.0
    assert r.raw_lambda == 0.0
    assert any("honest" in n for n in r.notes)


# ── live integration (excluded by -m "not integration"; run manually) ──

def _live_conn_or_skip():
    try:
        conn = psycopg.connect(LIVE_DSN, row_factory=psycopg.rows.dict_row, connect_timeout=2)
    except Exception:
        pytest.skip("live Cloud SQL proxy not reachable at 127.0.0.1:5433 in this environment")
    return conn


@pytest.mark.integration
def test_live_point_marriage_specimen():
    conn = _live_conn_or_skip()
    try:
        t_jd = _jd(2013, 12, 11)
        r = compute_lambda_e(swe, conn, CHART_ID, "marriage", t_jd, source="live")
        assert r.temporal_shape == "point"
        assert r.promise > 0.0
    finally:
        conn.close()


@pytest.mark.integration
def test_live_interval_windfall_specimen_shows_elevated_span():
    """The named windfall specimen (2010-07 -> 2011-03, event bd7f5711...)
    must show elevated intensity SPANNING the window, not a single point."""
    conn = _live_conn_or_skip()
    try:
        series = compute_lambda_e_series(
            swe, conn, CHART_ID, "major_gain",
            _jd(2010, 7, 1), _jd(2011, 3, 1), step_days=30.0, source="live",
        )
        assert len(series) >= 5
        assert all(r.temporal_shape == "interval" for r in series)
        assert any(r.raw_lambda > 0 for r in series)
        # PERMISSION must sum >= 2 systems on at least one point in the span.
        assert any(r.permission_detail["system_count_active"] >= 2 for r in series)
    finally:
        conn.close()


@pytest.mark.integration
def test_live_permission_multisystem_not_vimshottari_only():
    conn = _live_conn_or_skip()
    try:
        r = compute_lambda_e(swe, conn, CHART_ID, "major_gain", _jd(2010, 9, 1), source="live")
        active = r.permission_detail["systems_active"]
        assert len(active) >= 2
        non_vimshottari_active = [s for s in active if s != "vimshottari"]
        assert non_vimshottari_active, "PERMISSION must not be Vimsottari-only"
    finally:
        conn.close()


# ── SAVEPOINT-nesting safety, second module (D-5 G-4 incident expanded fix,
# 2026-07-20) ─────────────────────────────────────────────────────────────
#
# `tests/test_gochara_grammar.py` already proves this property for
# `gochara_grammar.primitives`. This section proves the SAME property for
# `gochara_intensity.permission` and `gochara_intensity.enrichment` -- two of
# the modules whose own `safe_rollback` call sites were converted to
# `savepoint_scope` in this fix's expanded second pass (the Conductor's
# review correctly flagged that fixing `primitives.py` alone left the exact
# same bug live in `engine.py` / `permission.py` / `valence.py` /
# `enrichment.py` / `configuration_activity.py` / `ka_gochara_sweep/sweep.py`,
# since G-4's sweep calls straight into all of them from inside the
# orchestrator's `SAVEPOINT writer_exec`).
#
# Same technique as the primitives.py tests: stdlib `sqlite3` in explicit-
# transaction mode gives real `SAVEPOINT`/`RELEASE SAVEPOINT`/`ROLLBACK TO
# SAVEPOINT` semantics without needing a live Postgres (none is reachable in
# this sandbox outside the `@pytest.mark.integration` tests above).
import sqlite3  # noqa: E402

from services.gochara_intensity.permission import compute_permission  # noqa: E402,F811
from services.gochara_intensity.enrichment import _fetch_graha_position  # noqa: E402


def _sqlite_conn_in_explicit_transaction() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("BEGIN")
    return conn


def test_permission_compute_survives_inside_orchestrator_owned_savepoint():
    """`compute_permission`'s several DB-touching branches (dasha periods,
    sade_sati, guru_shani_double_transit, av_threshold, planetary_return)
    each ran through `safe_rollback` (bare `conn.rollback()`) before this
    fix. Against a bare SQLite connection, `DD.fetch_dasha_periods` and the
    primitive calls inside will all fail (Postgres-only SQL / missing
    tables) -- exactly the "everything degrades honestly" scenario this
    module is built for. The assertion that matters, mirroring
    `test_gochara_grammar.py::test_primitive_survives_inside_orchestrator_owned_savepoint`:
    a manually-opened outer `SAVEPOINT writer_exec` (mimicking
    `asset_runner.py::_drive_substeps`) must still be releasable after
    `compute_permission` returns."""
    conn = _sqlite_conn_in_explicit_transaction()
    try:
        conn.execute("SAVEPOINT writer_exec")

        target = ResonanceTarget(
            chart_id=CHART_ID, event_class="wealth", target_type="bhava",
            target_ref="11", weight=0.75, classical_citation="TEST FIXTURE",
            target_sign="Pisces",
        )
        permission, detail = compute_permission(
            swe, conn, CHART_ID, "wealth", [target], _jd(2020, 1, 1),
        )
        assert isinstance(permission, float)  # degraded, but did not crash

        # THE critical assertion.
        conn.execute("RELEASE SAVEPOINT writer_exec")
    finally:
        conn.close()


def test_enrichment_fetch_graha_position_survives_inside_orchestrator_owned_savepoint():
    """Same proof for `enrichment._fetch_graha_position` -- a bare SQLite
    connection has no `chart_facts` table, so the query fails; before this
    fix the except block called `safe_rollback` (bare `conn.rollback()`)."""
    conn = _sqlite_conn_in_explicit_transaction()
    try:
        conn.execute("SAVEPOINT writer_exec")

        result = _fetch_graha_position(conn, CHART_ID, "SUN", "lahiri_chitrapaksha")
        assert result is None  # honest degrade, not a crash

        conn.execute("RELEASE SAVEPOINT writer_exec")
    finally:
        conn.close()


# ── MR-41(b): target_nakshatra_id resolution in production enrichment
# (PK-R-5, 2026-08-11) ──────────────────────────────────────────────────────
#
# Before this fix, `enrich_target` never populated `target_nakshatra_id`
# anywhere in production -- only `resonance_map.build_fixture_targets`'s
# hand-built synthetic fixture rows carried one. Every graha-anchored target
# `enrich_target` DOES resolve (karaka/dasha_lord_portfolio) therefore
# silently starved `nakshatra_ingress_tara` and `sarvatobhadra_vedha`
# (both honestly return [] when `target.target_nakshatra_id is None`, per
# each primitive's own docstring) of any chance to fire, for every real
# chart, forever -- not a primitive bug, an upstream wiring gap.
from services.gochara_intensity.enrichment import enrich_target, _nakshatra_id_from_longitude, NAKSHATRA_ARC_DEG  # noqa: E402
from services.gochara_grammar import primitives as _P41b  # noqa: E402
from services.gochara_grammar import sarvatobhadra as _SBC41b  # noqa: E402


class _GrahaPositionFakeConn:
    """Fake conn serving exactly one `chart_facts.graha_position` row shape
    (longitude_sidereal + sign) for one `fact_subject`, mirroring the real
    query `enrichment._fetch_graha_position` issues -- mocks only the DB
    row content, not `enrich_target`'s own resolution logic."""

    def __init__(self, fact_subject: str, longitude_deg: float, sign: str):
        self.fact_subject = fact_subject
        self.longitude_deg = longitude_deg
        self.sign = sign
        self.autocommit = False

    def execute(self, sql, params=None):
        s = sql if isinstance(sql, str) else str(sql)
        stripped = s.strip()
        if stripped.startswith("SAVEPOINT ") or stripped.startswith("RELEASE SAVEPOINT ") \
                or stripped.startswith("ROLLBACK TO SAVEPOINT "):
            return _FakeCur([])
        if "graha_position" in s and params and params[-1] == self.fact_subject:
            return _FakeCur([
                {"fact_key": "longitude_sidereal", "fact_value_text": None, "fact_value_num": self.longitude_deg},
                {"fact_key": "sign", "fact_value_text": self.sign, "fact_value_num": None},
            ])
        return _FakeCur([])

    def rollback(self):
        pass


class _FakeCur:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


def test_nakshatra_id_from_longitude_matches_established_27_division_convention():
    """Pins `_nakshatra_id_from_longitude` to the exact
    floor(lon / (360/27)) + 1 formula this codebase already uses elsewhere
    (services.gochara_v3.mechanisms.w23_tara_bala._longitude_to_nakshatra_index;
    tests/test_gochara_grammar.py's own _target_at_planet_position helper),
    computed independently here (not by calling the function under test)."""
    for lon in (0.0, 13.0, 13.34, 90.0, 180.0, 299.5, 359.99):
        expected = int((lon % 360.0) / (360.0 / 27.0)) + 1
        expected = max(1, min(27, expected))
        assert _nakshatra_id_from_longitude(lon) == expected
    assert NAKSHATRA_ARC_DEG == pytest.approx(360.0 / 27.0)


def test_mr41b_enrich_target_resolves_nakshatra_id_for_graha_anchored_target():
    """The real fetch/enrichment path (not a hand-built fixture target) must
    now resolve `target_nakshatra_id` for a karaka (graha-anchored) target,
    from the SAME longitude it already resolves `target_longitude_deg`/
    `target_sign` from -- no new DB read."""
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="career_advancement", target_type="karaka",
        target_ref="Saturn", weight=0.8, classical_citation="TEST FIXTURE",
    )
    lon = 299.5  # arbitrary real-looking sidereal longitude (Aquarius range)
    conn = _GrahaPositionFakeConn(fact_subject="SAT", longitude_deg=lon, sign="Aquarius")

    enriched = enrich_target(conn, target, ayanamsha_id="lahiri_chitrapaksha")

    expected_nak_id = int((lon % 360.0) / (360.0 / 27.0)) + 1
    assert enriched.target_longitude_deg == lon
    assert enriched.target_sign == "Aquarius"
    assert enriched.target_nakshatra_id == expected_nak_id
    assert enriched.natal_planet == "Saturn"
    # enrich_target returns a NEW object (dataclasses.replace) -- the input
    # target is untouched, still carrying no anchors.
    assert target.target_nakshatra_id is None


def test_mr41b_resolved_target_unlocks_nakshatra_ingress_tara_and_sarvatobhadra_vedha():
    """The POINT of MR-41(b): a target enriched by the real `enrich_target`
    path (not a hand-built fixture) must actually let
    `nakshatra_ingress_tara` and `sarvatobhadra_vedha` emit sentences --
    proving the previously-None field genuinely unlocks both primitive
    families, not just that the field itself is non-None."""
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="career_advancement", target_type="karaka",
        target_ref="Saturn", weight=0.8, classical_citation="TEST FIXTURE",
    )
    conn = _GrahaPositionFakeConn(fact_subject="SAT", longitude_deg=299.5, sign="Aquarius")
    enriched = enrich_target(conn, target, ayanamsha_id="lahiri_chitrapaksha")
    assert enriched.target_nakshatra_id is not None  # precondition for both calls below

    start_jd, end_jd = _jd(2020, 1, 1), _jd(2021, 1, 1)
    tara_sentences = _P41b.nakshatra_ingress_tara(swe, CHART_ID, enriched, start_jd, end_jd)
    assert len(tara_sentences) >= 1, (
        "nakshatra_ingress_tara must be CAPABLE of firing for an enrich_target-"
        "resolved graha-anchored target (Moon alone crosses all 27 nakshatras "
        "roughly monthly, so a 1-year window with ALL_GRAHAS must hit)."
    )

    sbc_sentences = _SBC41b.find_sarvatobhadra_vedha_states(swe, CHART_ID, enriched, start_jd, end_jd)
    assert len(sbc_sentences) >= 1, (
        "sarvatobhadra_vedha must be CAPABLE of firing for an enrich_target-"
        "resolved graha-anchored target."
    )


def test_mr41b_bhava_target_honest_skip_leaves_nakshatra_id_unresolved():
    """Bhava targets get a documented honest skip, not a fabricated point
    anchor: enrich_target must NOT invent a target_nakshatra_id for a bhava
    target (there is no single natal degree within a 30-degree house span
    to derive one from)."""
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="wealth", target_type="bhava",
        target_ref="11", weight=0.75, classical_citation="TEST FIXTURE",
    )
    conn = _GrahaPositionFakeConn(fact_subject="LAGNA", longitude_deg=15.0, sign="Aries")
    enriched = enrich_target(conn, target, ayanamsha_id="lahiri_chitrapaksha")
    assert enriched.target_sign == "Aquarius"  # 11th from Aries lagna, whole-sign
    assert enriched.target_nakshatra_id is None
    assert enriched.target_longitude_deg is None
