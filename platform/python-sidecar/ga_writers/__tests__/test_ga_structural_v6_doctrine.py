"""Unit tests for D-2 Lane V-6 doctrine completions in ga_structural_writer.py:
upapada wiring (CR-101), pañcadhā-maitrī compound matrix (CR-105),
kendrādhipati-doṣa PROPOSED ruling (ledger #49), and the manglik +
kala-sarpa-named-variant cancellation completion (CR-73).

Uses a synthetic chart_output + a no-op fake DB conn so these are pure-logic
regression tests (no live DB required) — the constituent_facts_array will be
empty in these fixtures (fake conn never resolves a real fact_id), which is
expected and asserted, not treated as a defect.
"""
from __future__ import annotations

from ga_writers import ga_structural_writer as sut


class _FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._last = (sql, params)

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class _FakeConn:
    def cursor(self, *a, **k):
        return _FakeCursor()


def _graha(name: str, sign: str, house: int, longitude: float | None = None) -> dict:
    sign_idx = sut.SIGN_NAMES.index(sign)
    return {
        "name": name,
        "sign": sign,
        "house": house,
        "longitude": longitude if longitude is not None else sign_idx * 30.0 + 15.0,
        "retrograde": False,
    }


# Native chart 482012f1: Lagna = Aries (CLAUDE.md §B FORENSIC anchor).
# Synthetic graha placements below are NOT the live chart — they are
# deliberately chosen to exercise each branch of the new rule logic; the
# lagna sign (Aries) IS the live chart's forensic anchor.
ARIES_LAGNA_CHART_OUTPUT = {
    "ascendant": {"sign": "Aries", "sign_id": 1},
    "grahas": [
        _graha("Sun", "Capricorn", 10),
        _graha("Moon", "Cancer", 4),        # rules only house 4 (kendra, no trikona)
        _graha("Mars", "Aries", 1),         # own sign, in lagna
        _graha("Mercury", "Gemini", 3),     # rules houses 3 & 6 (neither kendra nor trikona)
        _graha("Jupiter", "Sagittarius", 9),  # rules houses 9 & 12 (trikona present)
        _graha("Venus", "Taurus", 2),       # rules houses 2 & 7 (kendra present, no trikona)
        _graha("Saturn", "Capricorn", 10),  # rules houses 10 & 11
    ],
}


# ── _house_from_reference_sign ────────────────────────────────────────────────

def test_house_from_reference_sign_same_sign_is_house_1():
    assert sut._house_from_reference_sign("Aries", "Aries") == 1


def test_house_from_reference_sign_opposition_is_house_7():
    assert sut._house_from_reference_sign("Libra", "Aries") == 7


def test_house_from_reference_sign_wraps_correctly():
    # From Pisces (12th sign), Aries (1st sign) is house 2.
    assert sut._house_from_reference_sign("Aries", "Pisces") == 2


# ── Pañcadhā-maitrī: natural / temporal / compound ────────────────────────────

def test_natural_relation_matches_bphs_table_sun_moon_mutual_friends():
    assert sut._natural_relation("Sun", "Moon") == "friend"
    assert sut._natural_relation("Moon", "Sun") == "friend"


def test_natural_relation_sun_saturn_mutual_enemies():
    assert sut._natural_relation("Sun", "Saturn") == "enemy"
    assert sut._natural_relation("Saturn", "Sun") == "enemy"


def test_natural_relation_sun_mercury_asymmetric():
    # BPHS ch.3: Mercury is Sun's neutral (not friend/enemy); Sun is Mercury's friend.
    assert sut._natural_relation("Sun", "Mercury") == "neutral"
    assert sut._natural_relation("Mercury", "Sun") == "friend"


def test_temporal_relation_partition_is_total_and_disjoint():
    assert sut.TEMPORAL_FRIEND_HOUSES | sut.TEMPORAL_ENEMY_HOUSES == frozenset(range(1, 13))
    assert not (sut.TEMPORAL_FRIEND_HOUSES & sut.TEMPORAL_ENEMY_HOUSES)


def test_temporal_relation_same_sign_is_enemy_house_1():
    # House 1 (same sign) is in TEMPORAL_ENEMY_HOUSES per BPHS ch.4 v.19-20.
    chart_output = {
        "ascendant": {"sign": "Aries", "sign_id": 1},
        "grahas": [_graha("Sun", "Leo", 5), _graha("Moon", "Leo", 5)],
    }
    assert sut._temporal_relation("Sun", "Moon", chart_output) == "enemy"


def test_maitri_compound_table_covers_all_6_combinations():
    naturals = {"friend", "neutral", "enemy"}
    temporals = {"friend", "enemy"}
    for n in naturals:
        for t in temporals:
            assert (n, t) in sut.MAITRI_COMPOUND_TABLE
    assert sut.MAITRI_COMPOUND_TABLE[("friend", "friend")] == "adhi_mitra"
    assert sut.MAITRI_COMPOUND_TABLE[("enemy", "enemy")] == "adhi_shatru"
    assert sut.MAITRI_COMPOUND_TABLE[("friend", "enemy")] == "sama"
    assert sut.MAITRI_COMPOUND_TABLE[("enemy", "friend")] == "sama"


def test_build_panchadha_maitri_rows_emits_42_ordered_pairs():
    rows = sut._build_panchadha_maitri_rows(
        _FakeConn(), ARIES_LAGNA_CHART_OUTPUT,
        "chart-test", "build-test", "lahiri_chitrapaksha",
        "2026-07-16T00:00:00Z", "test/1.0.0",
    )
    # 7 grahas x 6 other grahas = 42 ordered (directional) pairs.
    assert len(rows) == 42
    for row in rows:
        assert row["fact_category"] == "panchadha_maitri"
        assert row["fact_value_text"] in {"adhi_mitra", "mitra", "sama", "shatru", "adhi_shatru"}
        assert row["fact_value_jsonb"]["compound_rule_id"] == sut.MAITRI_COMPOUND_RULE_ID


# ── Kendrādhipati-doṣa (PROPOSED) ──────────────────────────────────────────────

def test_kendradhipati_dosha_aries_lagna_moon_and_venus_flagged():
    """Aries lagna (the native's own forensic lagna): Moon rules ONLY house 4
    (kendra, no trikona) -> kendradhipati active. Venus rules houses 2 & 7
    (kendra present, no trikona) -> kendradhipati active. Mercury rules
    houses 3 & 6 (neither kendra nor trikona) -> not applicable (no kendra
    ruled at all). Jupiter rules houses 9 & 12 (trikona present) -> not
    kendra-only, unafflicted."""
    rows = sut._build_kendradhipati_dosha_rows(
        _FakeConn(), ARIES_LAGNA_CHART_OUTPUT,
        "chart-test", "build-test", "lahiri_chitrapaksha",
        "2026-07-16T00:00:00Z", "test/1.0.0",
    )
    by_planet = {r["fact_value_jsonb"]["planet"]: r for r in rows}

    assert by_planet["Moon"]["fact_value_jsonb"]["kendradhipati_active"] is True
    assert by_planet["Venus"]["fact_value_jsonb"]["kendradhipati_active"] is True
    assert by_planet["Jupiter"]["fact_value_jsonb"]["kendradhipati_active"] is False
    # Mercury rules no kendra house at all here -> not emitted as active,
    # and correctly absent from the "kendra ruled" set.
    assert by_planet["Mercury"]["fact_value_jsonb"]["kendradhipati_active"] is False

    for row in rows:
        assert row["fact_value_jsonb"]["doctrine_status"] == "PROPOSED"
        assert "[PROPOSED, not binding]" in row["citation_human"]


def test_kendradhipati_dosha_covers_all_natural_benefics_present_in_chart():
    rows = sut._build_kendradhipati_dosha_rows(
        _FakeConn(), ARIES_LAGNA_CHART_OUTPUT,
        "chart-test", "build-test", "lahiri_chitrapaksha",
        "2026-07-16T00:00:00Z", "test/1.0.0",
    )
    planets_seen = {r["fact_value_jsonb"]["planet"] for r in rows}
    assert planets_seen == {"Jupiter", "Venus", "Mercury", "Moon"}


# ── Manglik cancellation (CR-73) ──────────────────────────────────────────────

def test_cancel_manglik_own_sign_cancels():
    chart_output = {
        "ascendant": {"sign": "Aries", "sign_id": 1},
        "grahas": [
            _graha("Mars", "Aries", 1),       # own sign
            _graha("Jupiter", "Gemini", 3),
            _graha("Venus", "Leo", 5),
        ],
    }
    verdict = sut._cancel_manglik(None, chart_output, _FakeConn(), "chart-test", "lahiri_chitrapaksha")
    assert verdict["bhanga_active"] is True
    assert "mars_own_or_exalt_sign" in verdict["bhanga_rule_fired"]


def test_cancel_manglik_no_ground_stands_uncancelled():
    chart_output = {
        "ascendant": {"sign": "Aries", "sign_id": 1},
        "grahas": [
            _graha("Mars", "Cancer", 4),      # debilitated, 4th house
            _graha("Jupiter", "Virgo", 6),    # not kendra, no aspect on Mars's house 4 (offset check below)
            _graha("Venus", "Gemini", 3),     # not kendra
        ],
    }
    verdict = sut._cancel_manglik(None, chart_output, _FakeConn(), "chart-test", "lahiri_chitrapaksha")
    assert verdict["bhanga_active"] is False


def test_cancel_manglik_jupiter_kendra_cancels():
    chart_output = {
        "ascendant": {"sign": "Aries", "sign_id": 1},
        "grahas": [
            _graha("Mars", "Cancer", 4),
            _graha("Jupiter", "Libra", 7),    # Jupiter in kendra (house 7)
            _graha("Venus", "Gemini", 3),
        ],
    }
    verdict = sut._cancel_manglik(None, chart_output, _FakeConn(), "chart-test", "lahiri_chitrapaksha")
    assert verdict["bhanga_active"] is True
    assert "jupiter_in_kendra_h7" in verdict["bhanga_rule_fired"]


# ── Kala Sarpa named-variant wiring (CR-73) ───────────────────────────────────

def test_kala_sarpa_named_variant_house_table_covers_all_12_houses():
    assert set(sut.KALA_SARPA_NAMED_VARIANT_HOUSE.values()) == set(range(1, 13))
    assert len(sut.KALA_SARPA_NAMED_VARIANT_HOUSE) == 12


def test_kala_sarpa_named_variant_detector_only_fires_for_its_own_house():
    # All 7 classical grahas hemmed strictly between Rahu (house 1) and Ketu (house 7).
    chart_output = {
        "ascendant": {"sign": "Aries", "sign_id": 1},
        "grahas": [
            _graha("Rahu", "Aries", 1),
            _graha("Ketu", "Libra", 7),
            _graha("Sun", "Taurus", 2),
            _graha("Moon", "Gemini", 3),
            _graha("Mars", "Cancer", 4),
            _graha("Mercury", "Leo", 5),
            _graha("Jupiter", "Virgo", 6),
            _graha("Venus", "Taurus", 2),
            _graha("Saturn", "Gemini", 3),
        ],
    }
    d1_state = sut._extract_chart_state(chart_output)

    detector_h1 = sut._make_kala_sarpa_named_variant_detector(1)
    detector_h2 = sut._make_kala_sarpa_named_variant_detector(2)
    assert detector_h1(chart_output) is not None   # Rahu is in house 1 -> anant fires
    assert detector_h2(chart_output) is None        # Rahu is NOT in house 2 -> kulik does not fire


def test_registries_have_no_missing_cancellation_for_new_bespoke_detectors():
    """CR-73 registry hygiene: every BESPOKE_DOSHA_DETECTORS entry must have
    a DOSHA_CANCELLATIONS entry (mirrors the file's own existing invariant)."""
    for canonical_id in sut.BESPOKE_DOSHA_DETECTORS:
        assert canonical_id in sut.DOSHA_CANCELLATIONS, (
            f"{canonical_id} has a bespoke detector but no cancellation callable"
        )


def test_manglik_and_kala_sarpa_variants_registered_in_cancellations():
    assert "manglik" in sut.DOSHA_CANCELLATIONS
    for canonical_id in sut.KALA_SARPA_NAMED_VARIANT_HOUSE:
        assert canonical_id in sut.DOSHA_CANCELLATIONS
        assert canonical_id in sut.BESPOKE_DOSHA_DETECTORS


# ── STRUCTURAL_SUB_BUILDERS registry completeness (mirrors the file's own
#    completeness-auditing discipline) ─────────────────────────────────────────

def test_new_families_registered_in_structural_sub_builders():
    family_keys = {entry[0] for entry in sut.STRUCTURAL_SUB_BUILDERS}
    assert "upapada" in family_keys
    assert "panchadha_maitri" in family_keys
    assert "kendradhipati_dosha" in family_keys
