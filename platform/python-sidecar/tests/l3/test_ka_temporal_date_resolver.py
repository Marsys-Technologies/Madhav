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


# ── §8.4 iter-1 regression: birth-forward + ayanamsha-consistent resolution ────
from services.ka_temporal.date_resolver import resolve_birth_date

BIRTH = date(1984, 2, 5)  # native 482012f1


def _multi_ayanamsha_prebirth_timeline():
    """A PRE-BIRTH-INCLUSIVE, MULTI-AYANAMSHA raw chart_dashas span (1949→2100),
    mirroring prod. This fixture MASKS nothing: it deliberately contains the
    1951 Saturn AD that the pre-fix selector wrongly returned. Each DashaPeriod
    is tagged with its ayanamsha via a parallel dict so tests can filter as
    load_dasha_timeline's SQL does."""
    # (ayanamsha, DashaPeriod)
    return [
        # lahiri — full life cycle incl. pre-birth
        ("lahiri_chitrapaksha", DashaPeriod("Saturn", 2, date(1951, 4, 14), date(1952, 5, 23))),  # PRE-BIRTH
        ("lahiri_chitrapaksha", DashaPeriod("Saturn", 1, date(2010, 1, 1), date(2029, 1, 1))),
        ("lahiri_chitrapaksha", DashaPeriod("Saturn", 2, date(2012, 6, 1), date(2015, 3, 1))),
        # raman — DIFFERENT dates for the same lord (ayanamsha divergence)
        ("raman", DashaPeriod("Saturn", 2, date(1950, 1, 1), date(1951, 2, 1))),  # PRE-BIRTH
        ("raman", DashaPeriod("Saturn", 2, date(2020, 9, 1), date(2023, 4, 1))),
    ]


def _apply_load_semantics(rows, ayanamsha_id, birth_date):
    """Replicate load_dasha_timeline's SQL scoping (ayanamsha filter + birth
    forward) so the fixture drives resolve_activation_windows just like prod."""
    return [
        p for (a, p) in rows
        if a == ayanamsha_id and (birth_date is None or p.end >= birth_date)
    ]


class TestBirthForwardRegression:
    def test_prefix_selector_would_have_returned_prebirth(self):
        """Guard the guard: with NO birth bound the OLD behaviour resolves to the
        1951 pre-birth AD — proving the fixture actually exercises the bug."""
        raw = [p for (_, p) in _multi_ayanamsha_prebirth_timeline()
               if _  == "lahiri_chitrapaksha"]
        w = resolve_activation_windows({"constituent_lords": ["Saturn"]}, raw)  # no birth_date
        assert w.activation_start == date(1951, 4, 14)  # the DEFECT reproduced

    def test_birth_forward_window_is_in_life(self):
        """With birth_date the resolved window falls in the native's IN-LIFE
        Saturn AD (post-1984), never 1951."""
        tl = _apply_load_semantics(_multi_ayanamsha_prebirth_timeline(),
                                   "lahiri_chitrapaksha", BIRTH)
        w = resolve_activation_windows({"constituent_lords": ["Saturn"]}, tl, birth_date=BIRTH)
        assert w.activation_start == date(2012, 6, 1)
        assert w.activation_start >= BIRTH
        assert w.activation_peak >= BIRTH
        assert w.activation_end >= BIRTH
        assert all(p["date"] >= BIRTH.isoformat() for p in w.predicted_dates)
        assert all(p["start"] >= BIRTH.isoformat()
                   for p in w.active_dasha_periods if p.get("match_kind") == "exact_lord")

    def test_ayanamsha_consistent_resolution(self):
        """A raman predicate resolves against RAMAN periods (2020-09-01), not the
        lahiri periods (2012-06-01) — no cross-ayanamsha bleed."""
        tl = _apply_load_semantics(_multi_ayanamsha_prebirth_timeline(), "raman", BIRTH)
        w = resolve_activation_windows({"constituent_lords": ["Saturn"]}, tl, birth_date=BIRTH)
        assert w.activation_start == date(2020, 9, 1)     # raman, not lahiri's 2012
        assert w.activation_start >= BIRTH

    def test_straddling_period_start_clipped_to_birth(self):
        """A period that STARTS pre-birth and ENDS post-birth is kept but its
        start clips to birth (experienced portion, per ka_jivana_parva)."""
        tl = [DashaPeriod("Jupiter", 1, date(1980, 1, 1), date(1996, 1, 1))]  # straddles birth
        w = resolve_activation_windows({"constituent_lords": ["Jupiter"]}, tl, birth_date=BIRTH)
        assert w.activation_start == BIRTH
        assert w.active_dasha_periods[0]["start"] == BIRTH.isoformat()
        assert w.active_dasha_periods[0].get("clipped_to_birth") is True

    def test_convergence_peak_before_birth_falls_back_to_dasha(self):
        """A pre-birth convergence peak is rejected; resolution falls to the
        in-life dasha window."""
        tl = _apply_load_semantics(_multi_ayanamsha_prebirth_timeline(),
                                   "lahiri_chitrapaksha", BIRTH)
        w = resolve_activation_windows({"constituent_lords": ["Saturn"]}, tl,
                                       convergence_peak=date(1970, 1, 1), birth_date=BIRTH)
        assert w.resolution_source == "dasha_timeline"
        assert w.activation_start >= BIRTH


# ── WP-S4-R45-iter2: fact_subject-token + house/varga bhava-lord fallbacks ────
from services.ka_temporal.date_resolver import extract_lords_from_text, lord_from_house_varga


class TestExtractLordsFromText:
    """WP-S4-R45-iter2 fallback #3: last-resort lord extraction from
    chart_facts.fact_subject strings for signals whose configuration_jsonb
    carries no direct graha/sign key at all (sambandha_grade, dispositor
    chains, ...)."""

    def test_two_graha_pair_subject(self):
        # sambandha_grade fact_subject: "D20_SUN_MER"
        assert extract_lords_from_text("D20_SUN_MER") == ["Sun", "Mercury"]

    def test_lord_placement_subject(self):
        # lord_in_house_per_varga fact_value_text shape reused as a subject-like string
        assert extract_lords_from_text("Mars_in_H7") == ["Mars"]

    def test_house_only_subject_no_match(self):
        # D9_H1 — pure house/varga identifier, no graha token: must NOT fabricate
        assert extract_lords_from_text("D108_H1") == []
        assert extract_lords_from_text("D9_H1") == []

    def test_no_false_positive_on_concatenated_word(self):
        # "SUNDER" must not match "Sun" via substring — normalize_graha is exact-match
        assert extract_lords_from_text("SUNDER_POINT") == []

    def test_dedup_and_order_preserved(self):
        assert extract_lords_from_text("SUN_SUN_MOON") == ["Sun", "Moon"]

    def test_empty_and_none(self):
        assert extract_lords_from_text("") == []
        assert extract_lords_from_text(None) == []

    def test_dispositor_chain_list_rendered_text(self):
        assert extract_lords_from_text("Jupiter→Sun") == ["Jupiter", "Sun"]


class TestLordFromHouseVarga:
    """WP-S4-R45-iter2 fallback #2: net_argala_per_varga and siblings carry
    house (int) + varga ("D9") but no direct graha key — resolve via the
    prefetched lord_in_house_per_varga map."""

    def _map(self):
        return {
            ("lahiri_chitrapaksha", "D9_H1"): "Mars",
            ("lahiri_chitrapaksha", "D9_H7"): "Venus",
            ("raman", "D9_H1"): "Saturn",
        }

    def test_resolves_from_map(self):
        assert lord_from_house_varga(self._map(), "lahiri_chitrapaksha", "D9", 1) == "Mars"

    def test_resolves_with_string_house(self):
        assert lord_from_house_varga(self._map(), "lahiri_chitrapaksha", "D9", "7") == "Venus"

    def test_ayanamsha_scoped(self):
        # Same (varga, house) resolves DIFFERENTLY per ayanamsha — no cross-bleed.
        assert lord_from_house_varga(self._map(), "raman", "D9", 1) == "Saturn"

    def test_missing_entry_returns_none(self):
        assert lord_from_house_varga(self._map(), "lahiri_chitrapaksha", "D9", 12) is None

    def test_missing_inputs_return_none(self):
        assert lord_from_house_varga(self._map(), None, "D9", 1) is None
        assert lord_from_house_varga(self._map(), "lahiri_chitrapaksha", None, 1) is None
        assert lord_from_house_varga(self._map(), "lahiri_chitrapaksha", "D9", None) is None

    def test_non_numeric_house_returns_none(self):
        assert lord_from_house_varga(self._map(), "lahiri_chitrapaksha", "D9", "not_a_house") is None


class TestResolveBirthDate:
    def test_from_birth_params_iso(self):
        bd = resolve_birth_date(None, "cid", {"datetime_iso": "1984-02-05T10:43:00+05:30"})
        assert bd == date(1984, 2, 5)

    def test_from_charts_fallback(self):
        class _Cur:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def execute(self, sql, params=None): pass
            def fetchone(self): return {"birth_date": date(1984, 2, 5)}
        class _Conn:
            def cursor(self, *a, **k): return _Cur()
        assert resolve_birth_date(_Conn(), "482012f1") == date(1984, 2, 5)

    def test_none_when_unavailable(self):
        assert resolve_birth_date(None, "cid", None) is None
