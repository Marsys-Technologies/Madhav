"""Unit tests for ga_ayurdaya_writer (WP-2.5 / LCA-16).

Proves: (1) all THREE methods emitted, method-attributed; (2) an independent classical
re-derivation of a Nisargayu base contribution matches the writer (B.10); (3) the
applicability rule is served alongside; (4) maraka significators present.
"""
from jhora import const as jconst

from ga_writers import ga_ayurdaya_writer as sut


# native-ish positions: Sun debilitated Capricorn(9), Saturn exalted Libra(6), etc.
POSITIONS = {
    "Lagna":   {"sign_num": 0,  "degree_in_sign": 10.0, "house_d1": 1},
    "Sun":     {"sign_num": 9,  "degree_in_sign": 22.0, "house_d1": 10},
    "Moon":    {"sign_num": 10, "degree_in_sign": 15.0, "house_d1": 11},
    "Mars":    {"sign_num": 8,  "degree_in_sign": 5.0,  "house_d1": 9},
    "Mercury": {"sign_num": 9,  "degree_in_sign": 2.0,  "house_d1": 10},
    "Jupiter": {"sign_num": 8,  "degree_in_sign": 20.0, "house_d1": 9},
    "Venus":   {"sign_num": 9,  "degree_in_sign": 25.0, "house_d1": 10},
    "Saturn":  {"sign_num": 6,  "degree_in_sign": 20.0, "house_d1": 7},
    "Rahu":    {"sign_num": 1,  "degree_in_sign": 0.0,  "house_d1": 2},
    "Ketu":    {"sign_num": 7,  "degree_in_sign": 0.0,  "house_d1": 8},
}


def test_all_three_methods_emitted_with_attribution():
    rows = sut.build_ayurdaya_rows("chart-x", "build-x", "lahiri_chitrapaksha", POSITIONS)
    method_totals = {r["fact_subject"] for r in rows
                     if r["fact_key"] == "total_years"}
    assert method_totals == {"PINDAYU", "NISARGAYU", "AMSAYU"}
    # each total row carries its method + a classification and cites the delegated source
    for r in rows:
        if r["fact_key"] == "total_years":
            assert r["fact_value_text"] in ("alpayu", "madhyayu", "purnayu")
            assert r["fact_value_num"] is not None
            assert "aayu" in r["citation_human"] or "PyJHora" in r["citation_human"]


def test_nisargayu_base_matches_independent_classical_rederivation():
    pp = sut.build_planet_positions(POSITIONS)
    totals = sut.compute_method_totals(pp)
    # Independent re-derivation of Saturn's Nisargayu base contribution from the cited rule:
    #   arc = norm360(360 + planet_long - deep_exaltation_long)
    #   base = full * arc/360  (arc>180)  else  full - full*arc/360
    sat_id = 6
    sat_long = POSITIONS["Saturn"]["sign_num"] * 30 + POSITIONS["Saturn"]["degree_in_sign"]
    exalt = jconst.planet_deep_exaltation_longitudes[sat_id]
    arc = (360 + sat_long - exalt) % 360
    full = jconst.nisargayu_full_longevity_of_planets[sat_id]
    expected = full * arc / 360.0 if arc > 180.0 else full - full * arc / 360.0
    got = totals["nisargayu"]["per_graha"][sat_id]
    assert abs(got - expected) < 1e-6


def test_pindayu_full_constants_are_the_cited_values():
    # guards the delegated Pindayu full-longevity array did not drift
    assert jconst.pindayu_full_longevity_of_planets == [19, 25, 15, 12, 15, 21, 20]
    assert jconst.nisargayu_full_longevity_of_planets == [20, 1, 2, 9, 18, 20, 50]


def test_applicability_rule_served_and_valid():
    rows = sut.build_ayurdaya_rows("chart-x", "build-x", "lahiri_chitrapaksha", POSITIONS)
    appl = [r for r in rows if r["fact_key"] == "applicable_method"]
    assert len(appl) == 1
    assert appl[0]["fact_value_text"] in ("pindayu", "nisargayu", "amsayu")


def test_maraka_significators_present_and_include_saturn():
    rows = sut.build_ayurdaya_rows("chart-x", "build-x", "lahiri_chitrapaksha", POSITIONS)
    mar = [r for r in rows if r["fact_key"] == "maraka_grahas"]
    assert len(mar) == 1
    assert "Saturn" in mar[0]["fact_value_text"]


def test_classification_bands():
    assert sut.classify_ayus(20) == "alpayu"
    assert sut.classify_ayus(50) == "madhyayu"
    assert sut.classify_ayus(80) == "purnayu"
