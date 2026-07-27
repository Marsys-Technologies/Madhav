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


# ── MC-029 (Śodhana Builder T6 "YOGI-BINDU"): Yogi/Avayogi/Duplicate-Yogi/Sahayogi ────
# FORENSIC anchor: chart 482012f1 (Abhisek), ayanamsha=lahiri_chitrapaksha. Sun/Moon
# sidereal longitudes below are the LIVE chart_facts values for that (chart, ayanamsha)
# pair (confirmed via direct DB read this session) — NOT invented. Expected result,
# independently verified by the native before this pass:
#   Yogi point ~352.35 deg -> Revati -> Yogi Graha = Mercury
#   Avayogi point ~179.02 deg -> Chitra -> Avayogi Graha = Mars
_NATIVE_SUN_LONG = 291.962617284992
_NATIVE_MOON_LONG = 327.055230133129


def test_yogi_point_two_pass_matches_forensic_expectation():
    yogi_deg, div_arcsec, ok = sut._yogi_point_two_pass(_NATIVE_SUN_LONG, _NATIVE_MOON_LONG)
    assert ok is True
    assert div_arcsec <= 1.0
    assert abs(yogi_deg - 352.3511807514543) < 1e-6

    nak_name, nak_lord, sign_idx = sut._yogi_nakshatra_of(yogi_deg, sut._YOGI_FALLBACK_NAK_LORDS)
    assert nak_name == "Revati"
    assert nak_lord == "Mercury"
    assert sut.SIGNS[sign_idx] == "Pisces"


def test_avayogi_point_two_pass_matches_forensic_expectation():
    yogi_deg, _, _ = sut._yogi_point_two_pass(_NATIVE_SUN_LONG, _NATIVE_MOON_LONG)
    avayogi_deg, div_arcsec, ok = sut._avayogi_point_two_pass(yogi_deg)
    assert ok is True
    assert div_arcsec <= 1.0

    nak_name, nak_lord, sign_idx = sut._yogi_nakshatra_of(avayogi_deg, sut._YOGI_FALLBACK_NAK_LORDS)
    assert nak_name == "Chitra"
    assert nak_lord == "Mars"
    assert sut.SIGNS[sign_idx] == "Virgo"


def test_duplicate_yogi_and_sahayogi_are_the_sign_lord_of_yogi_rasi():
    yogi_deg, _, _ = sut._yogi_point_two_pass(_NATIVE_SUN_LONG, _NATIVE_MOON_LONG)
    _, _, sign_idx = sut._yogi_nakshatra_of(yogi_deg, sut._YOGI_FALLBACK_NAK_LORDS)
    assert sut.SIGNS[sign_idx] == "Pisces"
    assert sut._YOGI_FALLBACK_SIGN_LORDS[sign_idx] == "Jupiter"


class _FakeYogiCursor:
    """Mimics psycopg's cursor for reference_signs / reference_nakshatra reads."""
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._sql = sql

    def fetchall(self):
        return self._rows


class _FakeYogiConn:
    """Routes SELECT lord FROM reference_signs / vimshottari_lord FROM reference_nakshatra
    to DB-realistic fixture rows (mirrors the live values read from Postgres this session)."""
    _SIGN_ROWS = [
        ("mars",), ("venus",), ("mercury",), ("moon",), ("sun",), ("mercury",),
        ("venus",), ("mars",), ("jupiter",), ("saturn",), ("saturn",), ("jupiter",),
    ]
    _NAK_ROWS = [
        ("ketu",), ("venus",), ("sun",), ("moon",), ("mars",), ("rahu",), ("jupiter",),
        ("saturn",), ("mercury",), ("ketu",), ("venus",), ("sun",), ("moon",), ("mars",),
        ("rahu",), ("jupiter",), ("saturn",), ("mercury",), ("ketu",), ("venus",), ("sun",),
        ("moon",), ("mars",), ("rahu",), ("jupiter",), ("saturn",), ("mercury",),
    ]

    def cursor(self, *a, **k):
        # Distinguish by which query is about to run isn't possible without SQL sniffing
        # in this minimal fake, so return whichever fixture the caller's SQL implies —
        # ga_sensitive_degree_writer always queries signs before nakshatras in each of
        # _load_yogi_sign_lords / _load_yogi_nakshatra_lords (separate calls), so a
        # call-order-aware cursor is unnecessary: each function opens its own cursor and
        # immediately executes its own single SELECT, so we sniff the SQL text instead.
        return _SniffingCursor(self._SIGN_ROWS, self._NAK_ROWS)


class _SniffingCursor(_FakeYogiCursor):
    def __init__(self, sign_rows, nak_rows):
        super().__init__(None)
        self._sign_rows = sign_rows
        self._nak_rows = nak_rows

    def execute(self, sql, params=None):
        self._rows = self._nak_rows if "reference_nakshatra" in sql else self._sign_rows


def test_load_yogi_sign_lords_from_l0_reference_signs():
    lords = sut._load_yogi_sign_lords(_FakeYogiConn())
    assert lords == sut._YOGI_FALLBACK_SIGN_LORDS  # DB fixture matches classical fallback


def test_load_yogi_nakshatra_lords_from_l0_reference_nakshatra():
    lords = sut._load_yogi_nakshatra_lords(_FakeYogiConn())
    assert lords == sut._YOGI_FALLBACK_NAK_LORDS  # DB fixture matches classical fallback


class _BrokenConn:
    """Simulates an unreachable L0 reference table — every function must fall back to
    the classical constant tables rather than raising or fabricating a divergent value."""
    def cursor(self, *a, **k):
        raise RuntimeError("no DB in this test")


def test_yogi_lord_loaders_fall_back_when_db_unreachable():
    assert sut._load_yogi_sign_lords(_BrokenConn()) == sut._YOGI_FALLBACK_SIGN_LORDS
    assert sut._load_yogi_nakshatra_lords(_BrokenConn()) == sut._YOGI_FALLBACK_NAK_LORDS


def test_build_yogi_points_rows_full_native_chart():
    positions = {
        "Sun":  {"longitude_sidereal": _NATIVE_SUN_LONG},
        "Moon": {"longitude_sidereal": _NATIVE_MOON_LONG},
    }
    rows = sut.build_yogi_points_rows("chart-native", "lahiri_chitrapaksha", "build-x",
                                       positions, _BrokenConn())

    assert rows, "expected Yogi-system rows"
    for r in rows:
        assert r["fact_category"] == "sensitive_point_yogi"
        assert r["verification_pass_status"] == "two_pass_verified"
        assert r["citation_human"]

    by_subj_key = {(r["fact_subject"], r["fact_key"]): r for r in rows}
    assert by_subj_key[("YOGI", "assigned_graha")]["fact_value_text"] == "Mercury"
    assert by_subj_key[("YOGI", "nakshatra")]["fact_value_text"] == "Revati"
    assert by_subj_key[("AVAYOGI", "assigned_graha")]["fact_value_text"] == "Mars"
    assert by_subj_key[("AVAYOGI", "nakshatra")]["fact_value_text"] == "Chitra"
    assert by_subj_key[("DUPLICATE_YOGI", "assigned_graha")]["fact_value_text"] == "Jupiter"
    assert by_subj_key[("SAHAYOGI", "assigned_graha")]["fact_value_text"] == "Jupiter"
    # Duplicate-Yogi and Sahayogi are the SAME classical quantity (see SAHAYOGI_CITATION)
    assert (by_subj_key[("DUPLICATE_YOGI", "assigned_graha")]["fact_value_text"]
            == by_subj_key[("SAHAYOGI", "assigned_graha")]["fact_value_text"])


def test_build_yogi_points_rows_skips_cleanly_without_sun_or_moon():
    assert sut.build_yogi_points_rows("chart-x", "lahiri_chitrapaksha", "build-x",
                                       {"Sun": {"longitude_sidereal": 10.0}}, _BrokenConn()) == []
    assert sut.build_yogi_points_rows("chart-x", "lahiri_chitrapaksha", "build-x",
                                       {}, _BrokenConn()) == []


def test_yogi_rows_use_distinct_fact_ids_from_sensitive_degree_check_rows():
    """Regression guard: the YOGI_CATEGORY plumbing through _fact_id/_row must actually
    change the category-scoped hash, not silently collide with FACT_CATEGORY rows sharing
    the same subject/key (there is no such collision today, but this locks the contract)."""
    fid_yogi = sut._fact_id("YOGI", "assigned_graha", "chart-x", "lahiri_chitrapaksha",
                             "build-x", category=sut.YOGI_CATEGORY)
    fid_default = sut._fact_id("YOGI", "assigned_graha", "chart-x", "lahiri_chitrapaksha",
                                "build-x")
    assert fid_yogi != fid_default
