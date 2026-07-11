"""
test_r6a2_house_lord_yogas.py — R6A.2: real house-lord yoga detection (Y-10).

Covers:
  1. Unit tests per implemented family, driven through the REAL catalog rows
     (brahmagyan.l0_yogas.YOGAS_CORE) so the relation strings are proven to
     match end-to-end: Viparita (Harsha/Sarala/Vimala), Dhana family (2-11,
     5-9, 1-2, 9-11, Maha 2/5/9/11), Kendra-Trikona Raja, Dharma-Karmadhipati
     (all three sambandha modes), Lagna-9th raja, Daridra, Shakata (with the
     jupiter-in-kendra exclusion, Y-9 parity), Parivartana Raja (with the
     dainya guard), Pravrajya (nodes excluded).
  2. Y-10 closure proof: the FALSE "GA8 handles these" comment is gone from
     the source; every relation in the old skip tuple is now either
     implemented (fires in a synthetic test here) or carries a SPECIFIC floor
     reason in R6A2_FLOOR_REASONS — and floored relations genuinely return
     no firing (honest floor, no fabrication).
  3. Negative controls per family (no false positives).
  4. LESS-scope decisions locked by test: same-lord pairs never fire; the
     Kala Sarpa relation-form stays floored as a duplicate of
     ga_structural_writer._detect_kala_sarpa.

Pure deterministic functions — no DB, no LLM, no chart writes (the native
chart 482012f1 is never touched).
"""
from __future__ import annotations

import pathlib

import pytest

from brahmagyan.l0_yogas import YOGAS_CORE
from ga_writers.ga_yoga_writer import (
    SIGN_NUMBERS,
    ChartState,
    R6A2_FLOOR_REASONS,
    R6A2_LORD_ASSOCIATION_RELATIONS,
    R6A2_VIPARITA_RELATIONS,
    _check_house_lord_association,
    _check_kendra_trikona_raja,
    _evaluate_yoga,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _catalog(canonical_id: str) -> dict:
    entry = next(y for y in YOGAS_CORE if y["canonical_id"] == canonical_id)
    # _load_yoga_catalog would deliver these keys from the DB row; the seed
    # dicts carry them directly.
    assert entry.get("formation_rule_jsonb"), f"{canonical_id} has no formation rule"
    return entry


def _state(lagna_sign: str, placements: dict[str, str]) -> ChartState:
    """Build a ChartState from a lagna sign + {planet: sign} placements.
    Houses derive from signs (whole-sign); house_d1 rows are included so
    constituent_fact_ids resolve (fact_id per planet)."""
    facts: list[dict] = [{
        "fact_id": "f_lagna_sign",
        "fact_subject": "lagna",
        "fact_category": "graha_position",
        "fact_key": "sign",
        "fact_value_text": lagna_sign,
        "fact_value_num": None,
    }]
    lagna_num = SIGN_NUMBERS[lagna_sign]
    for planet, sign in placements.items():
        house = ((SIGN_NUMBERS[sign] - lagna_num) % 12) + 1
        facts.append({
            "fact_id": f"f_{planet}_house",
            "fact_subject": planet,
            "fact_category": "graha_position",
            "fact_key": "house_d1",
            "fact_value_num": house,
            "fact_value_text": None,
        })
        facts.append({
            "fact_id": f"f_{planet}_sign",
            "fact_subject": planet,
            "fact_category": "graha_position",
            "fact_key": "sign",
            "fact_value_text": sign,
            "fact_value_num": None,
        })
    return ChartState(facts)


def _fire(canonical_id: str, state: ChartState) -> dict | None:
    return _evaluate_yoga(_catalog(canonical_id), state)


# Aries-lagna negative-control chart: verified by hand to contain NO
# conjunction, NO mutual Parashari aspect and NO exchange between any pair of
# house lords relevant to the implemented lord-association yogas, no dusthana
# lord in a dusthana, and no dusthana placement of the 11th/1st lords.
# (Moon 12 / Jupiter 5 ARE 6/8 apart — so this chart is NOT used as the
# Shakata negative; Shakata has its own dedicated negatives below.)
_NEG = {
    "mars": "taurus",       # H2  (lagna + 8th lord)
    "sun": "gemini",        # H3  (5th lord)
    "moon": "pisces",       # H12 (4th lord)
    "mercury": "aquarius",  # H11 (3rd/6th lord)
    "jupiter": "leo",       # H5  (9th/12th lord)
    "venus": "virgo",       # H6  (2nd/7th lord)
    "saturn": "capricorn",  # H10 (10th/11th lord, own sign)
}


def _neg_state() -> ChartState:
    return _state("aries", dict(_NEG))


# ── 1. Viparita Raja Yoga family (Phaladeepika Ch.7) ──────────────────────────


class TestViparitaFamily:
    def test_harsha_fires_6th_lord_in_8th(self):
        # Aries lagna: 6th = Virgo, lord Mercury; Mercury in Scorpio = H8.
        pos = dict(_NEG, mercury="scorpio")
        res = _fire("vipareeta_harsha", _state("aries", pos))
        assert res is not None and res["fired"]
        assert res["constituent_planets"] == ["mercury"]
        assert res["constituent_houses"] == [8]
        assert res["constituent_fact_ids"] == ["f_mercury_house"]

    def test_sarala_fires_8th_lord_in_12th(self):
        # Aries lagna: 8th = Scorpio, lord Mars; Mars in Pisces = H12.
        pos = dict(_NEG, mars="pisces")
        res = _fire("vipareeta_sarala", _state("aries", pos))
        assert res is not None and res["constituent_planets"] == ["mars"]
        assert res["constituent_houses"] == [12]

    def test_vimala_fires_12th_lord_in_6th(self):
        # Aries lagna: 12th = Pisces, lord Jupiter; Jupiter in Virgo = H6.
        pos = dict(_NEG, jupiter="virgo")
        res = _fire("vipareeta_vimala", _state("aries", pos))
        assert res is not None and res["constituent_planets"] == ["jupiter"]
        assert res["constituent_houses"] == [6]

    def test_own_dusthana_counts(self):
        # 6th lord in the 6th itself fires Harsha (catalog: "6th, 8th or 12th").
        pos = dict(_NEG, mercury="virgo", venus="libra")  # Mercury H6; move Venus off Virgo
        res = _fire("vipareeta_harsha", _state("aries", pos))
        assert res is not None and res["constituent_houses"] == [6]

    def test_negative_control(self):
        st = _neg_state()
        for cid in ("vipareeta_harsha", "vipareeta_sarala", "vipareeta_vimala"):
            assert _fire(cid, st) is None


# ── 2. Dharma-Karmadhipati (BPHS Ch.39) — all three sambandha modes ───────────


class TestDharmaKarmadhipati:
    # Aries lagna: 9th lord Jupiter, 10th lord Saturn.

    def test_fires_by_conjunction(self):
        pos = dict(_NEG, jupiter="gemini", saturn="gemini")
        res = _fire("dharma_karmadhipati", _state("aries", pos))
        assert res is not None and res["fired"]
        assert sorted(res["constituent_planets"]) == ["jupiter", "saturn"]
        assert res["constituent_houses"] == [3]
        assert set(res["constituent_fact_ids"]) == {"f_jupiter_house", "f_saturn_house"}

    def test_fires_by_mutual_aspect_opposition(self):
        pos = dict(_NEG, jupiter="aries", saturn="libra")  # H1 vs H7 — mutual 7th
        res = _fire("dharma_karmadhipati", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["jupiter", "saturn"]
        assert res["constituent_houses"] == [1, 7]

    def test_fires_by_exchange(self):
        pos = dict(_NEG, jupiter="capricorn", saturn="sagittarius")
        res = _fire("dharma_karmadhipati", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["jupiter", "saturn"]

    def test_one_way_aspect_does_not_fire(self):
        # Jupiter H3, Saturn H5: Jupiter aspects 7/9/11 from H3; Saturn aspects
        # 7/8/2 from H5 — neither aspects the other; no exchange/conjunction.
        pos = dict(_NEG, jupiter="gemini", saturn="leo")
        assert _fire("dharma_karmadhipati", _state("aries", pos)) is None

    def test_same_lord_never_fires_less_scope(self):
        # Taurus lagna: Saturn lords BOTH 9th (Capricorn) and 10th (Aquarius).
        pos = {
            "saturn": "capricorn", "sun": "leo", "moon": "cancer",
            "mars": "scorpio", "mercury": "gemini", "jupiter": "pisces",
            "venus": "libra",
        }
        assert _fire("dharma_karmadhipati", _state("taurus", pos)) is None

    def test_negative_control(self):
        assert _fire("dharma_karmadhipati", _neg_state()) is None


# ── 3. Kendra-Trikona Raja Yoga (BPHS Ch.39) ──────────────────────────────────


class TestKendraTrikonaRaja:
    def test_fires_4th_and_5th_lords_conjunct(self):
        # Aries lagna: 4th lord Moon + 5th lord Sun conjunct in Leo (H5).
        pos = dict(_NEG, moon="leo", sun="leo")
        res = _fire("kendra_trikona_raja_yoga", _state("aries", pos))
        assert res is not None and res["fired"]
        assert sorted(res["constituent_planets"]) == ["moon", "sun"]
        assert res["constituent_houses"] == [5]

    def test_stub_replaced_negative(self):
        # The old stub returned False unconditionally; now assert the REAL
        # evaluator returns None only because no association exists.
        assert _check_kendra_trikona_raja(_neg_state()) is None
        assert _fire("kendra_trikona_raja_yoga", _neg_state()) is None

    def test_stub_replaced_positive_direct(self):
        pos = dict(_NEG, moon="leo", sun="leo")
        hit = _check_kendra_trikona_raja(_state("aries", pos))
        assert hit is not None and hit["association_mode"] == "conjunction"


# ── 4. Dhana family (BPHS Ch.41) + Lagna-9th raja (BPHS Ch.40) ────────────────


class TestDhanaFamily:
    def test_dhana_2_11_conjunction(self):
        # Aries lagna: 2nd lord Venus + 11th lord Saturn conjunct in Gemini.
        pos = dict(_NEG, venus="gemini", saturn="gemini")
        res = _fire("dhana_yoga_2_11", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["saturn", "venus"]

    def test_dhana_5_9_conjunction(self):
        pos = dict(_NEG, sun="sagittarius", jupiter="sagittarius")
        res = _fire("dhana_yoga_5_9", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["jupiter", "sun"]

    def test_dhana_lagna_2_exchange(self):
        # Mars (1st lord) in Taurus, Venus (2nd lord) in Aries — exchange.
        pos = dict(_NEG, mars="taurus", venus="aries")
        res = _fire("dhana_yoga_lagna_2", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["mars", "venus"]

    def test_dhana_9_11_mutual_aspect(self):
        pos = dict(_NEG, jupiter="aries", saturn="libra")  # opposition
        res = _fire("dhana_yoga_9_11", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["jupiter", "saturn"]

    def test_maha_dhana_any_pair(self):
        # 5th lord Sun + 11th lord Saturn conjunct → pair (5,11) fires.
        pos = dict(_NEG, sun="cancer", saturn="cancer")
        res = _fire("dhana_yoga_2_5_9_11", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["saturn", "sun"]

    def test_raja_lagna_9(self):
        # Mars (1st lord) conjunct Jupiter (9th lord) in Leo.
        pos = dict(_NEG, mars="leo", jupiter="leo")
        res = _fire("raja_yoga_lagna_9th", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["jupiter", "mars"]

    def test_negative_control_all(self):
        st = _neg_state()
        for cid in ("dhana_yoga_2_11", "dhana_yoga_5_9", "dhana_yoga_lagna_2",
                    "dhana_yoga_9_11", "dhana_yoga_2_5_9_11", "raja_yoga_lagna_9th"):
            assert _fire(cid, st) is None, cid


# ── 5. Daridra (Saravali) ──────────────────────────────────────────────────────


class TestDaridra:
    def test_fires_11th_lord_in_dusthana(self):
        # Aries lagna: 11th lord Saturn in Virgo (H6); move Venus off Virgo.
        pos = dict(_NEG, saturn="virgo", venus="libra")
        res = _fire("daridra_yoga", _state("aries", pos))
        assert res is not None
        assert res["constituent_planets"] == ["saturn"]
        assert res["constituent_houses"] == [6]

    def test_fires_lagna_lord_in_12th(self):
        pos = dict(_NEG, mars="pisces", moon="aquarius")  # Mars H12; Moon moved off Pisces
        res = _fire("daridra_yoga", _state("aries", pos))
        assert res is not None
        # NOTE: Mars in Pisces is ALSO the 8th lord in the 12th — but here we
        # assert only the daridra branch (lagna lord in dusthana).
        assert res["constituent_planets"] == ["mars"]

    def test_negative_control(self):
        assert _fire("daridra_yoga", _neg_state()) is None


# ── 6. Shakata (Saravali/BPHS) — exclusion parity with ga_structural Y-9 ──────


class TestShakata:
    def test_fires_moon_jupiter_shadashtaka_jupiter_not_kendra(self):
        # Aries lagna: Moon Taurus (H2), Jupiter Sagittarius (H9) → 8th from
        # Moon; Jupiter H9 not a kendra → fires.
        pos = dict(_NEG, moon="taurus", jupiter="sagittarius")
        res = _fire("shakata_dur_yoga", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["jupiter", "moon"]
        assert res["constituent_houses"] == [2, 9]

    def test_excluded_when_jupiter_in_kendra_from_lagna(self):
        # Moon Taurus (H2), Jupiter Libra (H7) → 6th from Moon BUT Jupiter in
        # a kendra from lagna → the catalog exclude clause suppresses firing
        # (same verdict ga_structural's Y-9 exclusion enforcement produces).
        pos = dict(_NEG, moon="taurus", jupiter="libra")
        assert _fire("shakata_dur_yoga", _state("aries", pos)) is None

    def test_negative_not_6_8_apart(self):
        pos = dict(_NEG, moon="pisces", jupiter="gemini")  # H12 vs H3 → 4th from Moon
        assert _fire("shakata_dur_yoga", _state("aries", pos)) is None


# ── 7. Parivartana Raja (BPHS Ch.39) with dainya guard ────────────────────────


class TestParivartanaRaja:
    def test_fires_4_5_exchange(self):
        # Aries lagna: Moon (4th lord) in Leo, Sun (5th lord) in Cancer —
        # exchange between two auspicious houses; neither lords a dusthana.
        pos = dict(_NEG, moon="leo", sun="cancer")
        res = _fire("parivartana_raja_yoga", _state("aries", pos))
        assert res is not None
        assert sorted(res["constituent_planets"]) == ["moon", "sun"]
        assert res["constituent_houses"] == [4, 5]

    def test_dainya_guard_blocks_dusthana_lord(self):
        # Mars in Cancer (H4) / Moon in Aries (H1) is a 1<->4 exchange, but
        # Mars also lords the 8th (Scorpio) for Aries lagna → dainya guard
        # blocks the raja label (LESS-scope conservative reading).
        pos = dict(_NEG, mars="cancer", moon="aries")
        assert _fire("parivartana_raja_yoga", _state("aries", pos)) is None

    def test_negative_control(self):
        assert _fire("parivartana_raja_yoga", _neg_state()) is None


# ── 8. Pravrajya (BPHS Ch.36) ──────────────────────────────────────────────────


class TestPravrajya:
    def test_fires_four_classical_in_one_house(self):
        pos = dict(_NEG, sun="capricorn", mercury="capricorn", venus="capricorn")
        # Saturn already in Capricorn (H10) → 4 classical grahas together.
        res = _fire("pravrajya_yoga", _state("aries", pos))
        assert res is not None
        assert res["constituent_planets"] == ["mercury", "saturn", "sun", "venus"]
        assert res["constituent_houses"] == [10]

    def test_nodes_do_not_count(self):
        # Only 3 classical grahas + Rahu/Ketu in one house → no firing.
        pos = dict(_NEG, sun="capricorn", mercury="capricorn",
                   rahu="capricorn", ketu="capricorn")
        assert _fire("pravrajya_yoga", _state("aries", pos)) is None

    def test_negative_control(self):
        assert _fire("pravrajya_yoga", _neg_state()) is None


# ── 9. Y-10 closure: false comment gone; floors are honest and specific ───────


_WRITER_SRC = (
    pathlib.Path(__file__).resolve().parents[1] / "ga_writers" / "ga_yoga_writer.py"
).read_text(encoding="utf-8")

# The exact relation tuple that sat behind the false comment pre-R6A.2.
_OLD_SKIP_TUPLE = {
    "4th_and_9th_lords_in_mutual_kendra",
    "5th_and_6th_lords_in_mutual_kendra",
    "lagna_lord_and_9th_lord_associate",
    "association_of_2nd_and_11th_lords",
    "association_of_5th_and_9th_lords",
    "association_among_2_5_9_11_lords",
    "association_of_lagna_and_2nd_lords",
    "association_of_9th_and_11th_lords",
    "9th_lord_own_or_exalted_in_kendra_trikona",
    "mercury_venus_jupiter_in_kendra_trikona_or_2nd",
    "benefics_in_upachayas_3_6_10_11_from_lagna_or_moon",
    "benefics_in_6_7_8_from_lagna",
    "lagna_lord_exalted_in_kendra_aspected_by_jupiter",
    "venus_lagna_lord_9th_lord_strong_and_related",
    "four_or_more_planets_in_one_house",
    "four_plus_planets_in_one_house",
    "6th_lord_in_6_8_or_12",
    "8th_lord_in_6_8_or_12",
    "12th_lord_in_6_8_or_12",
    "debilitated_planet_with_cancelled_debility",
    "mutual_exchange_of_signs_between_two_auspicious_house_lords",
    "kendra_and_trikona_lords_as_benefics_in_kendras",
    "benefics_in_2nd_and_12th_from_a_house_or_planet",
    "saturn_strongest_in_a_4plus_grouping_or_aspecting_moon_with_ketu",
    "11th_lord_in_dusthana_or_lagna_lord_in_6_8_12",
    "moon_jupiter_in_6_8_from_each_other",
}

# Relations R6A.2 actually implements in _evaluate_yoga.
_IMPLEMENTED = (
    set(R6A2_LORD_ASSOCIATION_RELATIONS)
    | set(R6A2_VIPARITA_RELATIONS)
    | {
        "9th_and_10th_lords_associate_conjunction_aspect_or_exchange",
        "kendra_lord_and_trikona_lord_associate",
        "association_among_2_5_9_11_lords",
        "11th_lord_in_dusthana_or_lagna_lord_in_6_8_12",
        "moon_jupiter_in_6_8_from_each_other",
        "mutual_exchange_of_signs_between_two_auspicious_house_lords",
        "four_or_more_planets_in_one_house",
    }
)


class TestY10Closure:
    def test_false_comment_removed(self):
        assert (
            "The ga_structural writer (GA8) does yoga_fires rows that handle these"
            not in _WRITER_SRC
        ), "the FALSE Y-10 comment must not survive R6A.2"

    def test_every_old_skip_relation_dispositioned(self):
        # Each relation from the pre-R6A.2 skip tuple is now either implemented
        # or carries a specific honest floor reason — no silent gaps.
        for rel in sorted(_OLD_SKIP_TUPLE):
            assert rel in _IMPLEMENTED or rel in R6A2_FLOOR_REASONS, rel

    def test_no_relation_both_implemented_and_floored(self):
        assert not (_IMPLEMENTED & set(R6A2_FLOOR_REASONS))

    def test_floor_reasons_are_specific(self):
        for rel, reason in R6A2_FLOOR_REASONS.items():
            assert len(reason) > 30, rel
            assert "GA8" not in reason  # never the old false claim

    def test_floored_relation_returns_none_even_when_pattern_present(self):
        # Kahala: 4th & 9th lords in mutual kendra IS present (Moon H4,
        # Jupiter H10 → mutual kendra), but the {lagna_lord strong}
        # co-requirement is unevaluable → honest floor, no firing.
        pos = dict(_NEG, moon="cancer", jupiter="capricorn")
        assert _fire("kahala", _state("aries", pos)) is None

    def test_kala_sarpa_relation_form_stays_floored_as_duplicate(self):
        # The dosha-form lives in ga_structural_writer._detect_kala_sarpa;
        # the relation-form catalog entry must not fire a second authority.
        assert "all_seven_planets_hemmed_rahu_ketu_one_side" in R6A2_FLOOR_REASONS
        assert "_detect_kala_sarpa" in R6A2_FLOOR_REASONS[
            "all_seven_planets_hemmed_rahu_ketu_one_side"
        ]
        # All 7 planets on one side of the nodal axis → still no yoga-writer row.
        pos = {
            "sun": "taurus", "moon": "gemini", "mars": "cancer",
            "mercury": "taurus", "jupiter": "leo", "venus": "gemini",
            "saturn": "cancer", "rahu": "aries", "ketu": "libra",
        }
        assert _fire("kala_sarpa_yoga", _state("aries", pos)) is None


# ── 10. Generic association helper (any (h1, h2) pair) ────────────────────────


class TestGenericHouseLordAssociation:
    def test_arbitrary_pair(self):
        # Generic contract: works for ANY pair, e.g. (3, 6) — Aries lagna:
        # Mercury lords both Gemini(3) and Virgo(6) → same-lord → None.
        assert _check_house_lord_association(_neg_state(), 3, 6) is None
        # (2, 7): Venus lords both → None (same lord).
        assert _check_house_lord_association(_neg_state(), 2, 7) is None
        # (3, 4): Mercury vs Moon — put them conjunct.
        pos = dict(_NEG, mercury="leo", moon="leo")
        hit = _check_house_lord_association(_state("aries", pos), 3, 4)
        assert hit is not None and hit["association_mode"] == "conjunction"
        assert sorted(hit["lords"]) == ["mercury", "moon"]

    def test_returns_none_without_lagna(self):
        st = ChartState([{
            "fact_id": "f1", "fact_subject": "moon",
            "fact_category": "graha_position", "fact_key": "sign",
            "fact_value_text": "leo", "fact_value_num": None,
        }])
        assert _check_house_lord_association(st, 9, 10) is None
