"""Bhava/Hora/Ghati/Vighati Lagna: the Sun must be read AT sunrise (TI-l1-special-lagna-offset-001).

PyJHora 4.8.6 ``drik.special_ascendant`` evaluates the Sun at (sunrise + tz hours): it hands
``sunrise()[2]`` (already a local JD) PLUS tz/24 to ``charts.divisional_chart``, which subtracts the
timezone again. ``pyjhora_adapter.special_lagnas`` now computes these four itself, byte-for-byte
upstream except for that one JD.

Definition under test (BPHS Ch.5 "Special Ascendants", R. Santhanam ed.; corpus chunks
bphs_pg0061_c01 / bphs_pg0062_c01 / bphs_pg0063_c01): add the time elapsed since sunrise, at the
lagna's own rate, "to the Sun's longitude as at Sun rise":
  * Bhava  : "every 5 ghatis (or 120 minutes) constitute one" sign -> 0.25 deg/min
  * Hora   : "Hora Lagna repeats itself every 2.5 ghatis (60 minutes)" -> 0.5 deg/min
  * Ghatika: "Consider the number of ghatis past as number of Rasis ... Vighatis divided by 2 to
             arrive at degrees" -> 30 deg per 24 min = 1.25 deg/min
  * worked example in the text (Sun at sunrise 132 deg, birth 12 gh 30 vi after sunrise):
    Bhava 207 deg, Hora 282 deg, Ghatika 147 deg (375 deg mod 360).
Vighati Lagna is NOT in the BPHS corpus chunks: its 15 deg/min rate is PyJHora's and is checked
here only for the Sun-at-sunrise base, never as classical truth.

The independent re-derivation below uses swisseph directly (Hindu rising: disc centre, no
refraction -- the convention PyJHora's ``drik.sunrise`` uses, RISE_FLAGS=897) and shares no code with
the adapter. It is a CI-time check, not a per-row runtime verdict, so it does not by itself justify a
``two_pass_verified`` tier; it also shares the Swiss ephemeris and the sunrise convention with the
engine, and does not cover Vighati.
"""
from __future__ import annotations

import os

import pytest

from panchang_engine.swiss_state import serialized_swiss_state

# (datetime_iso, lat, lon, tz): four timezones incl. negative and large positive offsets.
CASES = [
    ("2011-02-06T11:00:00", 23.26, 77.41, 5.5),
    ("1995-07-15T16:30:00", 40.71, -74.00, -4.0),
    ("2003-11-02T09:15:00", 35.68, 139.69, 9.0),
    ("2020-03-20T14:45:00", -33.87, 151.20, 11.0),
]
AYANAMSHAS = ["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"]
# rates in deg/min from the BPHS passage quoted above (Vighati: PyJHora's, unaudited)
RATES = {"bhava_lagna": 0.25, "hora_lagna": 0.5, "ghati_lagna": 1.25}
VIGHATI_RATE = 15.0
TOL_DEG = 0.005


def _inputs(dt, lat, lon, tz):
    return {"datetime_iso": dt, "latitude_deg": lat, "longitude_deg": lon,
            "tz_offset_hours": tz, "place_name": "synthetic", "subject_label": "syn"}


@serialized_swiss_state
def _independent(dt, lat, lon, tz, ayanamsha_id, extra_sun_hours=0.0):
    """Sun's sidereal longitude at TRUE sunrise (+ optional hours) and minutes since sunrise."""
    import swisseph as swe

    sidm = {"lahiri": swe.SIDM_LAHIRI, "true_chitra": swe.SIDM_TRUE_CITRA,
            "kp": swe.SIDM_KRISHNAMURTI, "raman": swe.SIDM_RAMAN,
            "surya_siddhanta": swe.SIDM_SURYASIDDHANTA}[ayanamsha_id]
    swe.set_ephe_path(os.environ.get("SE_EPHE_PATH", ""))
    swe.set_sid_mode(sidm)
    y, m, d = int(dt[:4]), int(dt[5:7]), int(dt[8:10])
    birth_h = int(dt[11:13]) + int(dt[14:16]) / 60.0
    jd0 = swe.julday(y, m, d, 0.0)
    rise_ut = swe.rise_trans(jd0 - tz / 24.0, swe.SUN, swe.CALC_RISE | swe.BIT_HINDU_RISING,
                             (lon, lat, 0.0), 0.0, 0.0, swe.FLG_SWIEPH)[1][0]
    minutes = (birth_h - ((rise_ut - jd0) * 24.0 + tz)) * 60.0
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_TRUEPOS | swe.FLG_NONUT | swe.FLG_NOGDEFL
    sun = swe.calc_ut(rise_ut + extra_sun_hours / 24.0, swe.SUN, flags)[0][0]
    return sun, minutes


def _diff(a, b):
    return ((a - b + 180.0) % 360.0) - 180.0


def _special(dt, lat, lon, tz, aya):
    from pyjhora_adapter import compute_chart
    return compute_chart(inputs=_inputs(dt, lat, lon, tz), ayanamsha_id=aya)["special_lagnas"]


@pytest.mark.parametrize("aya", AYANAMSHAS)
@pytest.mark.parametrize("case", CASES, ids=[c[3].__str__() for c in CASES])
def test_sunrise_lagnas_match_independent_bphs_derivation(case, aya):
    dt, lat, lon, tz = case
    sl = _special(dt, lat, lon, tz, aya)
    sun, minutes = _independent(dt, lat, lon, tz, aya)
    for name, rate in RATES.items():
        expected = (sun + minutes * rate) % 360.0
        assert abs(_diff(sl[name]["longitude_deg"], expected)) < TOL_DEG, (name, case, aya)
    # Vighati: only the Sun-at-sunrise BASE is checked (PyJHora's own rate, not classical)
    assert abs(_diff(sl["vighati_lagna"]["longitude_deg"],
                     (sun + minutes * VIGHATI_RATE) % 360.0)) < TOL_DEG


@pytest.mark.parametrize("case", CASES, ids=[c[3].__str__() for c in CASES])
def test_old_sun_read_tz_hours_after_sunrise_is_gone(case):
    """The retired behaviour (Sun at sunrise + tz hours) must NOT reproduce the output. Its offset
    is |tz| hours of solar motion (>= 0.15 deg for every case here)."""
    dt, lat, lon, tz = case
    sl = _special(dt, lat, lon, tz, "lahiri")
    sun_old, minutes = _independent(dt, lat, lon, tz, "lahiri", extra_sun_hours=tz)
    old = (sun_old + minutes * RATES["hora_lagna"]) % 360.0
    assert abs(_diff(sl["hora_lagna"]["longitude_deg"], old)) > 0.1


def test_module_rates_reproduce_the_bphs_worked_example():
    """BPHS Ch.5 notes: Sun at sunrise 4s 12deg = 132 deg, birth 12 ghatis 30 vighatis after
    sunrise (= 300 min). Text result: Bhava 207, Hora 282, Ghatika 147 (375 mod 360)."""
    from pyjhora_adapter import special_lagnas as sl

    sun, minutes = 132.0, 12.5 * 24.0
    assert (sun + minutes * sl._BHAVA_RATE_DEG_PER_MIN) % 360 == pytest.approx(207.0)
    assert (sun + minutes * sl._HORA_RATE_DEG_PER_MIN) % 360 == pytest.approx(282.0)
    assert (sun + minutes * sl._GHATI_RATE_DEG_PER_MIN) % 360 == pytest.approx(147.0)


def test_output_shape_unchanged():
    sl = _special(*CASES[0], "lahiri")
    for name in ("bhava_lagna", "hora_lagna", "ghati_lagna", "vighati_lagna"):
        assert set(sl[name]) == {"sign", "sign_id", "degree_in_sign", "longitude_deg"}
        assert 0.0 <= sl[name]["longitude_deg"] < 360.0
        assert sl[name]["sign_id"] == int(sl[name]["longitude_deg"] // 30) + 1


def _compute(dt, lat, lon, tz, aya="lahiri"):
    from jhora.panchanga import drik
    from jhora import utils
    from pyjhora_adapter import special_lagnas as sl

    d = drik.Date(int(dt[:4]), int(dt[5:7]), int(dt[8:10]))
    tob = (int(dt[11:13]), int(dt[14:16]), int(dt[17:19]))
    return sl.compute_special_lagnas(utils.julian_day_number(d, tob), d, tob, aya,
                                     lat=lat, lon=lon, tz=tz)


def test_no_pyjhora_attribute_is_ever_reassigned_by_the_adapter():
    """Varnada is a local copy, NOT a swap of ``drik.hora_lagna``: the adapter source contains no
    assignment to any attribute of a PyJHora module (static check)."""
    import ast
    import inspect
    from pyjhora_adapter import special_lagnas as sl

    tree = ast.parse(inspect.getsource(sl))
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        for t in targets:
            assert not (isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                        and t.value.id in {"drik", "charts", "_charts", "utils", "const"}), ast.dump(t)
        assert not (isinstance(node, ast.Call) and getattr(node.func, "id", "") in {"setattr", "delattr"})


def test_drik_hora_lagna_is_identity_unchanged_on_every_exit_path(monkeypatch):
    """(a) normal exit, (b) an Exception inside Varnada, (c) BaseExceptions (KeyboardInterrupt,
    GeneratorExit) propagating out of Varnada: ``drik.hora_lagna`` is the SAME object throughout."""
    from jhora.panchanga import drik
    from pyjhora_adapter import special_lagnas as sl

    original = drik.hora_lagna
    _compute(*CASES[0])
    assert drik.hora_lagna is original

    def boom(exc):
        def f(*a, **k):
            assert drik.hora_lagna is original  # also unchanged from INSIDE the Varnada call
            raise exc
        return f

    monkeypatch.setattr(sl, "_varnada_lagna_bv_raman", boom(RuntimeError("varnada failed")))
    assert "error" in _compute(*CASES[0])["varnada_lagna"]
    assert drik.hora_lagna is original

    for exc in (KeyboardInterrupt(), GeneratorExit(), SystemExit(1)):
        monkeypatch.setattr(sl, "_varnada_lagna_bv_raman", boom(exc))
        with pytest.raises(type(exc)):
            _compute(*CASES[0])
        assert drik.hora_lagna is original


def test_concurrent_caller_of_drik_hora_lagna_sees_the_original_during_compute(monkeypatch):
    """While one thread is inside ``compute_special_lagnas`` (parked in its Varnada step), a second
    thread calling ``drik.hora_lagna`` directly gets the ORIGINAL function and its upstream result."""
    import threading
    from jhora.panchanga import drik
    from jhora import utils
    from pyjhora_adapter import special_lagnas as sl

    dt, lat, lon, tz = CASES[0]
    d = drik.Date(int(dt[:4]), int(dt[5:7]), int(dt[8:10]))
    tob = (11, 0, 0)
    place = drik.Place("subject", lat, lon, tz)
    jd = utils.julian_day_number(d, tob)
    original = drik.hora_lagna
    drik.set_ayanamsa_mode("LAHIRI")
    upstream_result = original(jd, place)

    entered, release = threading.Event(), threading.Event()
    real = sl._varnada_lagna_bv_raman

    def parked(*a, **k):
        entered.set()
        assert release.wait(timeout=30)
        return real(*a, **k)

    monkeypatch.setattr(sl, "_varnada_lagna_bv_raman", parked)
    worker = threading.Thread(target=lambda: sl.compute_special_lagnas(
        jd, d, tob, "lahiri", lat=lat, lon=lon, tz=tz))
    worker.start()
    try:
        assert entered.wait(timeout=30)
        assert drik.hora_lagna is original  # observed from a second thread mid-compute
        seen = {}

        def _read():
            # Swiss Ephemeris keeps its sidereal mode in per-thread state on Linux builds (the CI
            # platform; one process-global state on the macOS wheel), so a fresh thread starts in the
            # library default (Fagan/Bradley) and would return a different longitude regardless of
            # anything compute_special_lagnas did. Select the same mode here so the comparison asks
            # only the question this test is about: is drik.hora_lagna itself left untouched.
            drik.set_ayanamsa_mode("LAHIRI")
            seen.setdefault("v", drik.hora_lagna(jd, place))

        reader = threading.Thread(target=_read)
        reader.start()
        reader.join(timeout=30)
        # the raw upstream function is untouched: it still returns the upstream (offset) value
        assert seen["v"] == upstream_result
    finally:
        release.set()
        worker.join(timeout=60)
    assert drik.hora_lagna is original


def test_varnada_parity_with_upstream_where_hora_signs_agree_and_follows_corrected_hora_otherwise():
    """The local Varnada copy equals upstream ``charts.varnada_lagna`` (method 1, house 1) at every
    sampled instant where upstream's Hora sign equals the corrected one, and follows the CORRECTED
    Hora sign where they differ (and the difference moves Varnada)."""
    from jhora.panchanga import drik
    from jhora.horoscope.chart import charts
    from jhora import utils
    from pyjhora_adapter import special_lagnas as sl

    lat, lon, tz = 23.26, 77.41, 5.5
    place = drik.Place("subject", lat, lon, tz)
    drik.set_ayanamsa_mode("LAHIRI")
    agree = moved = 0
    for day in range(1, 29):
        d = drik.Date(2011, 2, day)
        for second in range(8 * 3600, 20 * 3600, 90):
            tob = (second // 3600, (second % 3600) // 60, second % 60)
            jd = utils.julian_day_number(d, tob)
            ours = sl._varnada_lagna_bv_raman(d, tob, place)
            theirs = charts.varnada_lagna(d, tob, place, house_index=1, varnada_method=1)
            if sl.hora_lagna(jd, place)[0] == drik.hora_lagna(jd, place)[0]:
                assert ours == theirs, (d, tob)
                agree += 1
            elif ours[0] != theirs[0]:
                moved += 1
    assert agree > 5000 and moved > 0, (agree, moved)


def test_writer_rows_carry_corrected_value_and_honest_provenance():
    from ga_writers import ga_sensitive_writer as w
    from pyjhora_adapter import compute_chart

    dt, lat, lon, tz = CASES[0]
    chart = compute_chart(inputs=_inputs(dt, lat, lon, tz), ayanamsha_id="lahiri")
    lagna = float(chart["ascendant"]["longitude_deg"])
    rows = w._build_special_lagnas_rows(chart, {"LAGNA": lagna}, "aaaaaaaa-1111-4222-8333-000000000002",
                                        "lahiri_chitrapaksha", "bbbbbbbb-0000-4000-8000-000000000001",
                                        "t", {})
    by = {(r["fact_subject"], r["fact_key"]): r for r in rows}
    sun, minutes = _independent(dt, lat, lon, tz, "lahiri")
    got = by[("HORA_LAGNA", "longitude_sidereal")]["fact_value_num"]
    assert abs(_diff(got, (sun + minutes * 0.5) % 360.0)) < TOL_DEG
    prov = {s: by[(s, "longitude_sidereal")]["formula_provenance_text"]
            for s in ("BHAVA_LAGNA", "HORA_LAGNA", "GHATI_LAGNA", "VIGHATI_LAGNA")}
    for s in ("BHAVA_LAGNA", "HORA_LAGNA", "GHATI_LAGNA"):
        assert "BPHS Ch.5" in prov[s] and "Ch.11" not in prov[s], s
    assert "BPHS" not in prov["VIGHATI_LAGNA"].replace("not in the BPHS corpus", "")
    assert "NOT classically audited" in prov["VIGHATI_LAGNA"]
