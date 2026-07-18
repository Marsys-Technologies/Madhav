"""
test_kala_trigger.py — D-3 T-5 TRIGGER lock acceptance tests.

Covers:
  - CR-87: chart_id REQUIRED (no default) at every entry point that can
    resolve to a specific chart.
  - Destructive interference proof: net activation LOWER than an
    additive-only baseline when a suppressive current fires (the CR-89 kill).
  - Guru-Śani (Jupiter+Saturn) joint-transit detection: fires only when BOTH
    planets hit; a single-planet hit does not.
  - Saham current: Dhana-saham fires on transit conjunction and on
    dasha-lord match.
  - Vedha-filter gap: a case the base `_c11_vedha_factor` (fed the wrong
    sign-number argument at both ka_sangam.engine call sites) misses, that
    `vedha_factor_corrected` (fed the correct house-from-Moon) catches.
  - school_consensus honest not_computed flag vs a real computed value.
  - audit_binder_stub_predicates: honest, code-observed stub count (NOT the
    doctrine doc's unverified "~90%" claim).

No writes to any chart_* / bodha_* / ka_sangam table — all fixtures are
in-memory FakeGochara/FakeConn doubles; no live DB connection is opened.
"""
from __future__ import annotations

import pytest


# ── Fakes ──────────────────────────────────────────────────────────────────

class FakeEvent:
    def __init__(self, orb_at_event_deg=0.0, applying_separating="applying", aspect_deg=0):
        self.orb_at_event_deg = orb_at_event_deg
        self.applying_separating = applying_separating
        self.extra = {"aspect_deg": aspect_deg}


class FakeGochara:
    """Keyed by (transit_planet, round(target_lon, 1)) -> list[FakeEvent]."""

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def find_aspects(self, transit_planet, target_lon, aspect_degrees, orb, start_jd, end_jd):
        key = (transit_planet, round(target_lon, 1))
        self.calls.append(key)
        return self.responses.get(key, [])


# ═══════════════════════════════════════════════════════════════════════════
# 1. CR-87 — chart_id REQUIRED, no default
# ═══════════════════════════════════════════════════════════════════════════

class TestCR87:
    def test_compute_trigger_currents_requires_chart_id(self):
        from services.kala_trigger.trigger import compute_trigger_currents

        with pytest.raises(ValueError, match="chart_id"):
            compute_trigger_currents(chart_id="")

        with pytest.raises(TypeError):
            # chart_id is keyword-only and has no default — omitting it entirely
            # must fail at the call boundary, not silently resolve to None.
            compute_trigger_currents()  # type: ignore[call-arg]

    def test_fetch_saham_facts_requires_chart_id(self):
        from services.kala_trigger.trigger import fetch_saham_facts

        with pytest.raises(ValueError, match="chart_id"):
            fetch_saham_facts(conn=None, chart_id="")


# ═══════════════════════════════════════════════════════════════════════════
# 2. Destructive interference — the CR-89 additive-only-model kill proof
# ═══════════════════════════════════════════════════════════════════════════

class TestDestructiveInterference:
    def test_suppressive_current_lowers_net_below_additive_baseline(self):
        from services.kala_trigger.trigger import compute_trigger_currents, compose_with_ka_sangam

        # Saturn conjunct (0 deg orb) the Mechanism's activation longitude —
        # the strongest possible malefic-over-mechanism hit.
        gochara = FakeGochara({
            ("Saturn", 100.0): [FakeEvent(orb_at_event_deg=0.0, applying_separating="applying", aspect_deg=0)],
        })

        trig = compute_trigger_currents(
            chart_id="test-chart-cr89",
            mechanism_lon=100.0,
            gochara_service=gochara,
            w_jd_start=2451545.0,
            w_jd_end=2451560.0,
            orb_deg=5.0,
        )

        # malefic_transit_over_mechanism = orb_strength(0,5,'applying') * weight[0]=1.0 == 1.0
        assert trig["components"]["malefic_transit_over_mechanism"] == pytest.approx(1.0, abs=1e-6)
        # papa_kartari not configured -> 0.0
        assert trig["components"]["papa_kartari_sandwich"] == pytest.approx(0.0, abs=1e-6)
        # suppressive = -(1 - (1-0.6*1.0)*(1-0.6*0.0)) = -(1 - 0.4) = -0.6
        assert trig["suppressive"] == pytest.approx(-0.6, abs=1e-4)

        # An additive-only world (CR-89's model): ka_sangam reports a HIGH
        # convergence score purely from additive/saturating currents.
        additive_only_baseline = 0.8

        net = compose_with_ka_sangam(additive_only_baseline, trig)

        # THE PROOF: net activation is LOWER than the additive-only baseline
        # — genuine cancellation, impossible under an additive-only model.
        assert net < additive_only_baseline
        assert net == pytest.approx(0.2, abs=1e-4)

    def test_no_suppressive_current_leaves_baseline_unchanged(self):
        """Control: with no malefic/papa-kartari data, suppressive == 0 and
        net == the baseline exactly (proves the suppression above is caused
        by the malefic hit, not by some other clamping artifact)."""
        from services.kala_trigger.trigger import compute_trigger_currents, compose_with_ka_sangam

        trig = compute_trigger_currents(chart_id="test-chart-cr89-control")
        assert trig["suppressive"] == pytest.approx(0.0, abs=1e-9)
        baseline = 0.8
        assert compose_with_ka_sangam(baseline, trig) == pytest.approx(baseline, abs=1e-9)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Guru-Śani (Jupiter+Saturn) double-transit
# ═══════════════════════════════════════════════════════════════════════════

class TestGuruShaniDoubleTransit:
    def test_both_planets_hit_fires(self):
        from services.kala_trigger.trigger import guru_shani_double_transit

        gochara = FakeGochara({
            ("Jupiter", 50.0): [FakeEvent(orb_at_event_deg=1.0, applying_separating="applying", aspect_deg=0)],
            ("Saturn", 50.0): [FakeEvent(orb_at_event_deg=1.0, applying_separating="applying", aspect_deg=0)],
        })
        result = guru_shani_double_transit(50.0, gochara, 2451545.0, 2451560.0, orb_deg=5.0)
        assert result["jupiter_hit"] is True
        assert result["saturn_hit"] is True
        assert result["score"] > 0.0

    def test_single_planet_hit_does_not_fire(self):
        from services.kala_trigger.trigger import guru_shani_double_transit

        gochara = FakeGochara({
            ("Jupiter", 50.0): [FakeEvent(orb_at_event_deg=1.0, applying_separating="applying", aspect_deg=0)],
            # Saturn: no configured response -> no hit
        })
        result = guru_shani_double_transit(50.0, gochara, 2451545.0, 2451560.0, orb_deg=5.0)
        assert result["jupiter_hit"] is True
        assert result["saturn_hit"] is False
        assert result["score"] == pytest.approx(0.0, abs=1e-9)

    def test_no_gochara_service_is_safe(self):
        from services.kala_trigger.trigger import guru_shani_double_transit

        result = guru_shani_double_transit(50.0, None, None, None)
        assert result["score"] == pytest.approx(0.0, abs=1e-9)
        assert result["jupiter_hit"] is False and result["saturn_hit"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. Saham currents — Dhana Saham
# ═══════════════════════════════════════════════════════════════════════════

class TestSahamCurrent:
    def test_dhana_saham_fires_on_transit_conjunction(self):
        from services.kala_trigger.trigger import saham_current

        saham_facts = {"SAHAM_DHANA": {"longitude_sidereal": 200.0, "house_d1": 5.0}}
        score = saham_current(
            saham_facts, "SAHAM_DHANA",
            transiting_planet_lon=201.0,  # 1 deg orb of the saham point
            orb_deg=3.0,
        )
        assert score > 0.5

    def test_dhana_saham_fires_on_dasha_lord_match(self):
        from services.kala_trigger.trigger import saham_current

        saham_facts = {"SAHAM_DHANA": {"longitude_sidereal": 200.0}}
        score = saham_current(
            saham_facts, "SAHAM_DHANA",
            dasha_lord="Jupiter", saham_lord="Jupiter",
        )
        assert score == pytest.approx(0.6, abs=1e-9)

    def test_unknown_saham_scores_zero(self):
        from services.kala_trigger.trigger import saham_current

        assert saham_current({}, "SAHAM_DHANA") == 0.0

    def test_generalizes_to_other_saham_names(self):
        """Not hardcoded to SAHAM_DHANA — any key from
        ga_sensitive_writer._SAHAM_FORMULAS works."""
        from services.kala_trigger.trigger import saham_current

        saham_facts = {"SAHAM_RAJYA": {"longitude_sidereal": 10.0}}
        score = saham_current(saham_facts, "SAHAM_RAJYA", transiting_planet_lon=10.5, orb_deg=3.0)
        assert score > 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 5. Vedha-filter extension — catches a case the base filter misses (CR-102)
# ═══════════════════════════════════════════════════════════════════════════

class TestVedhaFilterGap:
    def test_corrected_filter_catches_sign_vs_house_from_moon_gap(self):
        """
        Moon in Cancer (0-based idx 3). Jupiter transits Taurus (1-based sign
        idx 2). Classical house-from-Moon = ((2-1-3) % 12) + 1 = 11 (the
        11th-from-Moon, Jupiter's BEST transit per BPHS Gochara — see
        brahmagyan/l0_transit.py: "Jupiter 11th from Moon — best transit;
        vedha from 8th"). A vedha rule keys off transit_to_house=11.

        The BASE `_c11_vedha_factor` (as called by both ka_sangam.engine
        call sites) is fed the RASI SIGN NUMBER (2) instead of the
        house-from-Moon (11) — 2 != 11, so it misses the rule entirely and
        reports 1.0 (neutral / no vedha), even though this transit IS
        classically vedha-eligible.
        """
        from services.kala_trigger.trigger import vedha_factor_corrected, house_from_moon
        from services.ka_sangam.engine import _c11_vedha_factor, EnrichmentContext

        vedha_rules = [{"graha": "Jupiter", "transit_to_house": 11, "vedha_house": 8}]
        moon_sign_idx_0based = 3   # Cancer
        transit_sign_idx_1based = 2  # Taurus

        assert house_from_moon(transit_sign_idx_1based, moon_sign_idx_0based) == 11

        # Base filter: fed the sign number directly (the actual call-site bug).
        old_factor = _c11_vedha_factor(
            "Jupiter", transit_sign_idx_1based, EnrichmentContext(vedha_rules=vedha_rules)
        )
        assert old_factor == pytest.approx(1.0), (
            "base filter should MISS this rule (fed sign number, not house-from-Moon)"
        )

        # Corrected filter: fed the real house-from-Moon.
        corrected_factor = vedha_factor_corrected(
            "Jupiter", transit_sign_idx_1based, moon_sign_idx_0based, vedha_rules
        )
        assert corrected_factor == pytest.approx(0.3), (
            "corrected filter should CATCH the vedha rule"
        )
        assert corrected_factor < old_factor

    def test_compute_trigger_currents_reports_gap_caught(self):
        from services.kala_trigger.trigger import compute_trigger_currents

        vedha_rules = [{"graha": "Jupiter", "transit_to_house": 11, "vedha_house": 8}]
        trig = compute_trigger_currents(
            chart_id="test-chart-vedha",
            vedha_rules=vedha_rules,
            vedha_planet="Jupiter",
            transit_sign_idx_1based=2,
            moon_sign_idx_0based=3,
        )
        vf = trig["components"]["vedha_filter"]
        assert vf["gap_caught"] is True
        assert vf["corrected_factor_house_from_moon"] < vf["old_factor_sign_number_bug"]

    def test_no_vedha_planet_reports_none(self):
        from services.kala_trigger.trigger import compute_trigger_currents

        trig = compute_trigger_currents(chart_id="test-chart-no-vedha")
        assert trig["components"]["vedha_filter"] is None


# ═══════════════════════════════════════════════════════════════════════════
# 5b. Weight overrides — D-3 ADMIT lane wiring (T-6): 0.2/0.2 admitted weights
#     vs the module's own unratified 0.5/0.6 defaults
# ═══════════════════════════════════════════════════════════════════════════

class TestWeightOverride:
    def test_default_weights_are_the_modules_own_unratified_constants(self):
        """Baseline: omitting overrides uses TRIGGER_ADDITIVE_WEIGHTS /
        TRIGGER_SUPPRESSIVE_WEIGHTS (0.5/0.5 additive, 0.6/0.6 suppressive)
        — this is what a caller gets WITHOUT explicitly opting into the
        admitted weights, and must stay the un-admitted default."""
        from services.kala_trigger.trigger import (
            compute_trigger_currents, TRIGGER_ADDITIVE_WEIGHTS, TRIGGER_SUPPRESSIVE_WEIGHTS,
        )

        trig = compute_trigger_currents(chart_id="test-chart-default-weights")
        assert trig["weights_used"]["additive"] == TRIGGER_ADDITIVE_WEIGHTS
        assert trig["weights_used"]["suppressive"] == TRIGGER_SUPPRESSIVE_WEIGHTS
        assert trig["weights_used"]["additive"]["guru_shani_double_transit"] == pytest.approx(0.5)
        assert trig["weights_used"]["suppressive"]["malefic_transit_over_mechanism"] == pytest.approx(0.6)

    def test_admitted_0_2_0_2_weights_are_actually_used_not_the_defaults(self):
        """THE wiring proof: passing the ADMIT-lane winning weights
        (additive=0.2/0.2, suppressive=0.2/0.2) must change the served
        suppressive/additive math relative to the module's own 0.5/0.6
        defaults — proves a caller genuinely reaches this override path,
        not just that the parameter exists."""
        from services.kala_trigger.trigger import compute_trigger_currents

        admitted_additive = {"guru_shani_double_transit": 0.2, "saham_activation": 0.2}
        admitted_suppressive = {"malefic_transit_over_mechanism": 0.2, "papa_kartari_sandwich": 0.2}

        gochara = FakeGochara({
            ("Saturn", 100.0): [FakeEvent(orb_at_event_deg=0.0, applying_separating="applying", aspect_deg=0)],
        })

        trig_admitted = compute_trigger_currents(
            chart_id="test-chart-admitted-weights",
            mechanism_lon=100.0, gochara_service=gochara,
            w_jd_start=2451545.0, w_jd_end=2451560.0, orb_deg=5.0,
            additive_weights=admitted_additive,
            suppressive_weights=admitted_suppressive,
        )
        trig_default = compute_trigger_currents(
            chart_id="test-chart-admitted-weights",
            mechanism_lon=100.0, gochara_service=gochara,
            w_jd_start=2451545.0, w_jd_end=2451560.0, orb_deg=5.0,
        )

        # Reported weights_used reflect exactly what was passed in — a caller
        # (or a fresh-context verifier) can assert the ADMITTED values were
        # genuinely used, not silently substituted back to the defaults.
        assert trig_admitted["weights_used"]["additive"] == admitted_additive
        assert trig_admitted["weights_used"]["suppressive"] == admitted_suppressive

        # suppressive = -(1 - (1 - 0.2*1.0)*(1 - 0.2*0.0)) = -(1 - 0.8) = -0.2
        assert trig_admitted["suppressive"] == pytest.approx(-0.2, abs=1e-4)
        # default: -(1 - (1 - 0.6*1.0)*(1 - 0.6*0.0)) = -0.6 (module's own constant)
        assert trig_default["suppressive"] == pytest.approx(-0.6, abs=1e-4)
        assert trig_admitted["suppressive"] != trig_default["suppressive"]

    def test_compose_with_ka_sangam_at_admitted_weights(self):
        """End-to-end composition proof at the admitted weights (mirrors the
        ADMIT lane's own train-scoring composition contract)."""
        from services.kala_trigger.trigger import compute_trigger_currents, compose_with_ka_sangam

        admitted_additive = {"guru_shani_double_transit": 0.2, "saham_activation": 0.2}
        admitted_suppressive = {"malefic_transit_over_mechanism": 0.2, "papa_kartari_sandwich": 0.2}
        gochara = FakeGochara({
            ("Saturn", 100.0): [FakeEvent(orb_at_event_deg=0.0, applying_separating="applying", aspect_deg=0)],
        })
        trig = compute_trigger_currents(
            chart_id="test-chart-compose-admitted",
            mechanism_lon=100.0, gochara_service=gochara,
            w_jd_start=2451545.0, w_jd_end=2451560.0, orb_deg=5.0,
            additive_weights=admitted_additive,
            suppressive_weights=admitted_suppressive,
        )
        baseline = 0.8
        net = compose_with_ka_sangam(baseline, trig)
        assert net == pytest.approx(0.6, abs=1e-4)  # 0.8 + (-0.2)
        # At the module's own 0.6 default this same malefic hit would have
        # pulled the baseline all the way down to 0.2 (see TestDestructiveInterference
        # above) — the admitted 0.2/0.2 weights are a materially gentler suppression.
        assert net > 0.2


# ═══════════════════════════════════════════════════════════════════════════
# 6. school_consensus repair-or-honest-flag
# ═══════════════════════════════════════════════════════════════════════════

class TestSchoolConsensusHonestFlag:
    def test_no_data_is_not_computed_not_silently_zero(self):
        from services.kala_trigger.trigger import school_consensus_score

        result = school_consensus_score("CAREER_PEAK", None)
        assert result["computed"] is False
        assert result["score"] == 0.0
        assert result["schools_agreeing"] is None
        assert "not_computed" in result["reason"]

    def test_real_data_is_computed_true(self):
        from services.kala_trigger.trigger import school_consensus_score

        result = school_consensus_score("CAREER_PEAK", {"CAREER": 5})
        assert result["computed"] is True
        assert result["schools_agreeing"] == 5
        assert result["score"] == pytest.approx(5 / 7.0, abs=1e-6)

    def test_real_data_but_no_domain_match_is_not_computed(self):
        from services.kala_trigger.trigger import school_consensus_score

        result = school_consensus_score("UNKNOWN_CLASS", {"CAREER": 5})
        assert result["computed"] is False
        assert result["score"] == 0.0

    def test_genuinely_zero_schools_agreeing_is_still_computed_true(self):
        """The core honesty fix: a REAL zero must be distinguishable from
        'never computed' — both must not collapse to the same signal."""
        from services.kala_trigger.trigger import school_consensus_score

        result = school_consensus_score("HEALTH_CRISIS", {"HEALTH": 0})
        assert result["computed"] is True
        assert result["schools_agreeing"] == 0
        assert result["score"] == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 7. ka_yojaka/binder.py stub-predicate audit — honest, code-observed count
# ═══════════════════════════════════════════════════════════════════════════

class TestBinderStubAudit:
    def test_audit_runs_and_reports_honest_counts(self):
        from services.kala_trigger.trigger import audit_binder_stub_predicates

        result = audit_binder_stub_predicates()
        assert result["total_builders"] >= 1
        assert 0 <= result["stub_count"] <= result["total_builders"]
        assert set(result["detail"].keys())  # non-empty
        # Every detail entry has the signal_sensitive probe result recorded.
        for sig_class, info in result["detail"].items():
            assert "signal_sensitive" in info
        # This audit must never restate the doctrine doc's unverified figure
        # as fact — the note field is the honesty guardrail on the function itself.
        assert "not confirmed" in result["note"] or "unverified" in result["note"]
