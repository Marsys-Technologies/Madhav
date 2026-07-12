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


# ── DB-realistic (1-based sign_num) path: guards the 1-based→0-based conversion ──────
class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return None


class _FakeConn:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self, *a, **k):
        return _FakeCursor(self._rows)


_SUBJ = {"Lagna": "LAGNA", "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
         "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT", "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN"}


def _db_rows_from_positions_0based(positions_0based):
    """Render POSITIONS (0-based) as the DB-realistic chart_facts rows ga_positions stores:
    sign_num 1-BASED + longitude_sidereal."""
    rows = []
    for g, rec in positions_0based.items():
        s0 = rec["sign_num"]
        deg = rec["degree_in_sign"]
        lon = s0 * 30 + deg
        subj = _SUBJ[g]
        rows.append((subj, "graha_position", "longitude_sidereal", None, float(lon)))
        rows.append((subj, "graha_sign_attributes", "sign_num", None, float(s0 + 1)))  # 1-based
        rows.append((subj, "graha_sign_attributes", "degree_in_sign", None, float(deg)))
        if rec.get("house_d1"):
            rows.append((subj, "graha_position", "house_d1", None, float(rec["house_d1"])))
    return rows


def test_db_realistic_1based_path_equals_0based_and_matches_cited_arc():
    # Feed the writer the DB-realistic (1-based sign_num) chart_facts rows and confirm the
    # loaded positions are 0-based and produce the SAME ayurdaya as the direct 0-based dict.
    db_rows = _db_rows_from_positions_0based(POSITIONS)
    loaded = sut.load_positions(_FakeConn(db_rows), "chart-native", "lahiri_chitrapaksha")
    assert loaded["Sun"]["sign_num"] == 9   # Capricorn 0-based, NOT 10 (1-based bug)

    rows_db = sut.build_ayurdaya_rows("c", "b", "lahiri_chitrapaksha", loaded)
    rows_direct = sut.build_ayurdaya_rows("c", "b", "lahiri_chitrapaksha", POSITIONS)

    def _total(rows, subject):
        return next(r["fact_value_num"] for r in rows
                   if r["fact_key"] == "total_years" and r["fact_subject"] == subject)

    for method in ("PINDAYU", "NISARGAYU", "AMSAYU"):
        assert abs(_total(rows_db, method) - _total(rows_direct, method)) < 1e-6

    # Independent cited-arc recompute of the Nisargayu TOTAL from 0-based longitudes.
    exp = 0.0
    for pid in range(7):  # Sun..Saturn
        gname = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"][pid]
        s0 = POSITIONS[gname]["sign_num"]
        lon = s0 * 30 + POSITIONS[gname]["degree_in_sign"]
        arc = (360 + lon - jconst.planet_deep_exaltation_longitudes[pid]) % 360
        full = jconst.nisargayu_full_longevity_of_planets[pid]
        exp += full * arc / 360.0 if arc > 180.0 else full - full * arc / 360.0
    lagna_years = (POSITIONS["Lagna"]["sign_num"] * 30 + POSITIONS["Lagna"]["degree_in_sign"]) / 30.0
    exp += lagna_years
    assert abs(_total(rows_db, "NISARGAYU") - round(exp, 4)) < 1e-3
