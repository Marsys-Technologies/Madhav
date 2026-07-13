"""Unit tests for ga_sensitive_degree_writer (WP-2.5 / LCA-10).

Independent classical-rule re-derivation: recompute a mrityu-bhaga degree and a gandanta
verdict from the cited source and assert the writer matches (B.10 / §N.4 no-JH-parity =
internal-consistency + classical-rule re-derivation).
"""
from jhora import const as jconst

from ga_writers import ga_sensitive_degree_writer as sut


# ── DB-realistic fixtures: chart_facts.sign_num is 1-BASED (Aries=1) ──────────────
# These guard the 1-based→0-based conversion in load_positions. The pure-builder tests
# below use the 0-based INTERNAL contract; only load_positions touches the DB axis.
class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._last = (sql, params)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return None


class _FakeConn:
    """Returns DB-realistic chart_facts rows (tuple_row shape) for load_positions."""
    def __init__(self, rows):
        self._rows = rows

    def cursor(self, *a, **k):
        return _FakeCursor(self._rows)


def _db_rows_for(graha_subject, sign_1based, deg, house):
    """Emit the chart_facts rows ga_positions_writer actually stores (sign_num 1-based)."""
    lon = (sign_1based - 1) * 30 + deg
    return [
        (graha_subject, "graha_position", "longitude_sidereal", None, float(lon)),
        (graha_subject, "graha_sign_attributes", "sign_num", None, float(sign_1based)),
        (graha_subject, "graha_sign_attributes", "degree_in_sign", None, float(deg)),
        (graha_subject, "graha_position", "house_d1", None, float(house)),
    ]


def test_load_positions_converts_1based_signnum_to_0based_native_sun():
    # Native FORENSIC anchor: Sun in Capricorn. chart_facts stores sign_num=10 (1-based).
    rows = _db_rows_for("SUN", 10, 22.0, 10)  # Capricorn 22°, house 10
    positions = sut.load_positions(_FakeConn(rows), "chart-native", "lahiri_chitrapaksha")
    # Canonical 0-based: Capricorn = 9, NOT 10.
    assert positions["Sun"]["sign_num"] == 9
    # Cited mrityu-bhaga for Sun in Capricorn must be 2.0° (base_longitudes[9][0]), not 3.0°.
    mb = sut.check_mrityu_bhaga("Sun", positions["Sun"]["sign_num"], positions["Sun"]["degree_in_sign"])
    assert mb["mrityu_bhaga_deg"] == 2.0
    assert jconst.mrityu_bhaga_base_longitudes[9][0] == 2   # 0-based Capricorn
    assert jconst.mrityu_bhaga_base_longitudes[10][0] == 3  # 1-based bug would have given 3


def test_load_positions_fallback_without_longitude_still_0based():
    # Only the 1-based sign_num + degree present (no longitude) → still convert to 0-based.
    rows = [
        ("MOON", "graha_sign_attributes", "sign_num", None, 11.0),      # Aquarius 1-based
        ("MOON", "graha_sign_attributes", "degree_in_sign", None, 15.0),
        ("MOON", "graha_position", "house_d1", None, 11.0),
    ]
    positions = sut.load_positions(_FakeConn(rows), "chart-x", "lahiri_chitrapaksha")
    assert positions["Moon"]["sign_num"] == 10   # Aquarius 0-based = 10

# rasi order: 0=Aries..11=Pisces; mrityu_bhaga cols [Sun,Moon,Mars,Merc,Jup,Ven,Sat,Rah,Ket,Mandi,Lagna]


def test_mrityu_bhaga_degree_matches_cited_pyjhora_table():
    # Independently read the cited PyJHora array and confirm the writer returns the same degree.
    for graha, col in sut._MB_COL.items():
        for sign_num in range(12):
            expected = float(jconst.mrityu_bhaga_base_longitudes[sign_num][col])
            assert sut.mrityu_bhaga_degree(graha, sign_num) == expected


def test_mrityu_bhaga_fires_on_exact_degree():
    # Sun in Aries (rasi 0): cited mrityu-bhaga = row0 col0 = 20.
    mb_deg = jconst.mrityu_bhaga_base_longitudes[0][0]
    assert mb_deg == 20  # guards the delegated table did not shift
    res = sut.check_mrityu_bhaga("Sun", 0, float(mb_deg))
    assert res["fired"] is True
    assert res["orb_deg"] == 0.0
    # 5 degrees away → not fired (Sun tolerance is 1/3 deg)
    assert sut.check_mrityu_bhaga("Sun", 0, float(mb_deg) + 5.0)["fired"] is False


def test_gandanta_fires_at_end_of_water_sign():
    # Pisces (rasi 11) last 3°20' is gandanta; 29° is inside.
    assert sut.check_gandanta(11, 29.0)["fired"] is True
    assert sut.check_gandanta(11, 10.0)["fired"] is False
    # Aries (rasi 0) first 3°20' is gandanta; 1° inside.
    assert sut.check_gandanta(0, 1.0)["fired"] is True
    # Taurus (not fire/water) never gandanta.
    assert sut.check_gandanta(1, 1.0)["fired"] is False


def test_pushkara_matches_cited_arrays():
    for sign_num in range(12):
        pn = float(jconst.pushkara_navamsa[sign_num])
        res = sut.check_pushkara(sign_num, pn + 0.1)  # just inside the pushkara navamsa
        assert res["in_pushkara_navamsa"] is True
        assert res["pushkara_navamsa_start_deg"] == round(pn, 4)


def test_khareshwara_counts_are_in_range():
    d22 = sut.compute_22nd_drekkana(0, 5.0)   # Aries lagna
    assert 0 <= d22["twentysecond_drekkana_sign_num"] <= 11
    d64 = sut.compute_64th_navamsa(9, 22.0)   # Moon Capricorn
    assert 0 <= d64["sixtyfourth_navamsa_sign_num"] <= 11


def test_kartari_papa_when_hemmed_by_malefics():
    # Graha in house 3 hemmed by malefics in 2 (12th from it) and 4 (2nd from it).
    houses = {"Moon": 3, "Saturn": 2, "Mars": 4}
    res = sut.check_kartari("Moon", houses)
    assert res["fired"] is True
    assert res["kartari_type"] == "papa_kartari"


def test_kranti_declination_sign_and_bounds():
    kr = sut.compute_kranti(90.0)   # tropical Cancer 0 → max north declination ~+23.44
    assert kr["direction"] == "north"
    assert 23.0 <= kr["kranti_deg"] <= 23.5
    kr2 = sut.compute_kranti(270.0)  # tropical Capricorn 0 → max south
    assert kr2["direction"] == "south"


def test_build_rows_emit_all_facets_and_cite():
    positions = {
        "Lagna":   {"sign_num": 0, "degree_in_sign": 5.0, "longitude_sidereal": 5.0, "house_d1": 1},
        "Sun":     {"sign_num": 9, "degree_in_sign": 22.0, "longitude_sidereal": 292.0, "house_d1": 10, "nakshatra": "Shravana"},
        "Moon":    {"sign_num": 10, "degree_in_sign": 15.0, "longitude_sidereal": 315.0, "house_d1": 11, "nakshatra": "Purva Bhadrapada"},
        "Mars":    {"sign_num": 0, "degree_in_sign": 19.0, "longitude_sidereal": 19.0, "house_d1": 1, "nakshatra": "Bharani"},
    }
    rows = sut.build_sensitive_degree_rows("chart-x", "build-x", "lahiri_chitrapaksha", positions)
    keys = {r["fact_key"] for r in rows}
    assert "mrityu_bhaga" in keys
    assert "gandanta" in keys
    assert "pushkara" in keys
    assert "kartari" in keys
    assert "khareshwara_22nd_drekkana" in keys
    assert "khareshwara_64th_navamsa" in keys
    # every row cites and carries the sensitive_degree_check category
    for r in rows:
        assert r["fact_category"] == "sensitive_degree_check"
        assert r["citation_human"]
