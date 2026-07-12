"""Tests for services.ka_temporal.date_resolver (WP-2.1 / R-45).

The core regression these lock: an activation predicate with real constituent
lords MUST resolve to concrete (non-NULL) dates from the dasha timeline EVEN
WHEN no convergence peak is supplied — the LANE0 root cause.
"""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_temporal.date_resolver import (
    DashaPeriod,
    ActivationWindows,
    normalize_graha,
    resolve_activation_windows,
)


def _timeline():
    """A minimal Vimshottari-ish timeline: two MDs and two ADs."""
    return [
        DashaPeriod(lord="Saturn", level_n=1, start=date(2010, 1, 1), end=date(2029, 1, 1)),
        DashaPeriod(lord="Mercury", level_n=1, start=date(2029, 1, 1), end=date(2046, 1, 1)),
        DashaPeriod(lord="Saturn", level_n=2, start=date(2012, 6, 1), end=date(2015, 3, 1)),
        DashaPeriod(lord="Venus", level_n=2, start=date(2015, 3, 1), end=date(2018, 1, 1)),
    ]


class TestNormalizeGraha:
    def test_full_names(self):
        assert normalize_graha("Saturn") == "Saturn"
        assert normalize_graha("saturn") == "Saturn"

    def test_aliases_and_codes(self):
        assert normalize_graha("Sa") == "Saturn"
        assert normalize_graha("shani") == "Saturn"
        assert normalize_graha("guru") == "Jupiter"
        assert normalize_graha("true_node") == "Rahu"

    def test_unknown_and_empty(self):
        assert normalize_graha("Pluto") is None
        assert normalize_graha("") is None
        assert normalize_graha(None) is None


class TestResolveNoConvergence:
    """THE R-45 fix: dates come from the dasha timeline, not convergence."""

    def test_lord_resolves_to_real_dates(self):
        rule = {"constituent_lords": ["Saturn"]}
        w = resolve_activation_windows(rule, _timeline())
        assert w.resolution_source == "dasha_timeline"
        # Finer level (AD) preferred as the primary bound.
        assert w.activation_start == date(2012, 6, 1)
        assert w.activation_end == date(2015, 3, 1)
        assert w.activation_peak is not None
        assert w.activation_start <= w.activation_peak <= w.activation_end

    def test_predicted_dates_non_empty(self):
        """activation_predicted_dates_jsonb must NOT be empty — the fallback."""
        rule = {"constituent_lords": ["Saturn"]}
        w = resolve_activation_windows(rule, _timeline())
        assert len(w.predicted_dates) > 0
        assert all("date" in d and "source" in d for d in w.predicted_dates)
        assert all(d["source"] == "dasha_timeline" for d in w.predicted_dates)

    def test_active_dasha_periods_dated(self):
        rule = {"constituent_lords": ["Saturn"]}
        w = resolve_activation_windows(rule, _timeline())
        dated = [p for p in w.active_dasha_periods if p.get("match_kind") == "exact_lord"]
        assert len(dated) >= 1
        assert all("start" in p and "end" in p for p in dated)

    def test_alias_lord_still_matches(self):
        rule = {"constituent_lords": ["shani"]}  # alias for Saturn
        w = resolve_activation_windows(rule, _timeline())
        assert w.activation_start is not None

    def test_unresolvable_lord_leaves_dates_none(self):
        rule = {"constituent_lords": ["Sun"]}  # not in timeline
        w = resolve_activation_windows(rule, _timeline())
        assert w.resolution_source == "none"
        assert w.activation_start is None
        assert w.activation_peak is None
        # lord-only entry still recorded for provenance
        assert any(p.get("match_kind") == "lord_only_no_timeline" for p in w.active_dasha_periods)

    def test_empty_rule_and_empty_timeline(self):
        w = resolve_activation_windows({}, [])
        assert w.activation_start is None
        assert w.resolution_source == "none"
        assert w.proximity_score == 0.5


class TestResolveWithConvergence:
    """When a convergence peak exists it refines the window (legacy behaviour)."""

    def test_peak_refines_window(self):
        rule = {"constituent_lords": ["Saturn"]}
        peak = date(2013, 6, 15)
        w = resolve_activation_windows(rule, _timeline(), convergence_peak=peak, signature_class="YOGA")
        assert w.resolution_source == "convergence"
        assert w.activation_peak == peak
        assert w.activation_start == date(2013, 6, 8)   # peak - 7 (YOGA)
        assert w.activation_end == date(2013, 6, 22)    # peak + 7
        assert len(w.predicted_dates) == 7

    def test_peak_without_timeline_match(self):
        """A convergence peak dates the activation even if lord not in timeline."""
        rule = {"constituent_lords": ["Sun"]}
        peak = date(2013, 6, 15)
        w = resolve_activation_windows(rule, _timeline(), convergence_peak=peak)
        assert w.activation_start is not None
        assert w.resolution_source == "convergence"


class TestProximityScore:
    def test_score_in_range(self):
        rule = {"constituent_lords": ["Saturn"], "dignity_score": 0.8}
        hook = {"non_affliction": 0.9}
        w = resolve_activation_windows(rule, _timeline(), strength_hook=hook)
        assert 0.0 <= w.proximity_score <= 1.0
        assert w.proximity_score == pytest.approx(0.72, abs=1e-6)

    def test_no_peak_defaults_half(self):
        w = resolve_activation_windows({"constituent_lords": ["Sun"]}, _timeline())
        assert w.proximity_score == 0.5


class TestWindowCap:
    def test_max_windows_bounds_periods(self):
        # Many matched periods, small cap.
        tl = [DashaPeriod(lord="Saturn", level_n=2, start=date(2000 + i, 1, 1),
                          end=date(2000 + i, 6, 1)) for i in range(20)]
        rule = {"constituent_lords": ["Saturn"]}
        w = resolve_activation_windows(rule, tl, max_windows=3)
        dated = [p for p in w.active_dasha_periods if p.get("match_kind") == "exact_lord"]
        assert len(dated) == 3


from services.ka_temporal.date_resolver import sign_lord, extract_lords_from_config


class TestSignLord:
    def test_known_signs(self):
        assert sign_lord("Aries") == "Mars"
        assert sign_lord("libra") == "Venus"
        assert sign_lord("Capricorn") == "Saturn"
        assert sign_lord("Aquarius") == "Saturn"
        assert sign_lord("Pisces") == "Jupiter"

    def test_unknown(self):
        assert sign_lord("Ophiuchus") is None
        assert sign_lord(None) is None


class TestExtractLordsFromConfig:
    """WP-2.1 root-cause fix: pull activating lords from real signal shapes."""

    def test_graha_keys(self):
        assert extract_lords_from_config({"planet": "Venus"}) == ["Venus"]
        assert extract_lords_from_config({"planet_a": "Jupiter", "planet_b": "Saturn"}) == ["Jupiter", "Saturn"]

    def test_three_letter_codes(self):
        # karaka_bhava_concordance uses bhava_lord: "SAT" / "MAR"
        assert extract_lords_from_config({"bhava_lord": "SAT"}) == ["Saturn"]
        assert extract_lords_from_config({"bhava_lord": "MAR"}) == ["Mars"]

    def test_sign_keys_to_rashi_lord(self):
        # aspect_jaimini_per_varga: source_sign / target_sign
        lords = extract_lords_from_config({"source_sign": "Sagittarius", "target_sign": "Libra"})
        assert lords == ["Jupiter", "Venus"]

    def test_on_sign_in_type_id(self):
        lords = extract_lords_from_config({}, signal_type_id="aspect_jaimini_per_varga:on_Aries")
        assert lords == ["Mars"]

    def test_fact_value_text_graha(self):
        # cusp_kp_lords:prana_lord -> fact_value_text "Venus"
        assert extract_lords_from_config({"fact_value_text": "Venus"}) == ["Venus"]

    def test_fact_value_text_non_graha_ignored(self):
        # dosha_label fact_value_text "Gulika Dosha" is not a graha
        assert extract_lords_from_config({"fact_value_text": "Gulika Dosha (Mandi)"}) == []

    def test_sade_sati_class_shortcut(self):
        assert extract_lords_from_config({"fact_key": "duration_days"},
                                         signal_type_class="sade_sati") == ["Saturn"]

    def test_vargottama_sign(self):
        lords = extract_lords_from_config({"d1_sign": "Cancer", "varga_sign": "Cancer"})
        assert lords == ["Moon"]

    def test_empty(self):
        assert extract_lords_from_config({}) == []
        assert extract_lords_from_config(None) == []

    def test_json_string_input(self):
        assert extract_lords_from_config('{"planet": "Mars"}') == ["Mars"]
