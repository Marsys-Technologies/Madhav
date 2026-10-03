"""
special_lagnas.py — Bhava/Hora/Ghati/Vighati/Indu/Sree/Pranapada/Bhrigu-Bindhu/
Kunda/Varnada Lagna.

Who computes what:
  * Bhava / Hora / Ghati / Vighati Lagna: the local ``_special_ascendant`` below, a copy of PyJHora
    4.8.6 ``drik.special_ascendant`` with ONE change (the Sun is read AT sunrise; upstream read it
    ``tz`` hours after sunrise). BPHS Ch.5 vv.2-8 definition; see that function's docstring.
  * Varnada Lagna: the local ``_varnada_lagna_bv_raman``, a copy of PyJHora's BV Raman routine fed by
    the corrected Hora Lagna (no PyJHora attribute is reassigned). The METHOD (BV Raman, 1) is
    upstream's choice and is not audited against the BPHS passage here.
  * Indu / Sree / Pranapada / Bhrigu Bindhu / Kunda Lagna: delegated unchanged to PyJHora
    (jhora.panchanga.drik); not audited here.

M-9 + M-10 fix (R6 1d-sensitive lane, 2026-07-10): the prior ga_sensitive_writer computed
Bhava/Hora/Ghati Lagna and "Pranapada Sphuta" as hand-rolled proxies using the Sun's within-sign
degree as a crude time-since-sunrise stand-in (HL = Lagna + (Sun%30)*2, GL = Lagna + (Sun%30)*12,
BL = 2*Sun - Lagna + 180, Pranapada = Moon + (Lagna-Sun)*4 falsely cited "BPHS"). Those were
non-classical approximations; they were replaced by computations from the real time elapsed since
sunrise at the birth place/moment (see drik.py:1959-2140 for the upstream originals). Indu Lagna,
Sree Lagna, Bhrigu Bindhu Lagna, Kunda Lagna and Varnada Lagna were previously absent entirely
from this writer.
"""
from __future__ import annotations

from functools import partial
from typing import Any

from panchang_engine.swiss_state import serialized_swiss_state

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik
from ._swiss_thread_scope import BACKEND_FAILURE_ERRORS, with_sidereal_mode


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def _to_dict(sign_idx: int, deg: float) -> dict[str, Any]:
    sign_idx = int(sign_idx)
    deg = float(deg)
    return {
        "sign": _names.sign_name(sign_idx),
        "sign_id": sign_idx + 1,
        "degree_in_sign": deg,
        "longitude_deg": sign_idx * 30.0 + deg,
    }


# ── Sunrise-based special ascendants (Bhava / Hora / Ghati / Vighati) ───────────────────
#
# Definition (BPHS Ch.5 "Special Ascendants" vv.2-8, R. Santhanam ed.; corpus chunks
# bphs_pg0061_c01, bphs_pg0062_c01, bphs_pg0063_c01): count the time elapsed from sunrise to
# birth and ADD it, at the lagna's own rate, "to the Sun's longitude as at Sun rise".
#   Bhava  : 5 ghatis (120 min) per sign  -> 30 deg / 120 min = 0.25 deg/min
#   Hora   : 2.5 ghatis (60 min) per sign -> 30 deg /  60 min = 0.50 deg/min
#   Ghatika: 1 ghati (24 min) per sign (vighatis/2 = degrees) -> 30 deg / 24 min = 1.25 deg/min
# Vighati Lagna is NOT in the BPHS corpus chunks: its 15 deg/min rate below is PyJHora's, carried
# unchanged and NOT audited here (B.10 -- only the Sun-at-sunrise base is corrected for it).
_BHAVA_RATE_DEG_PER_MIN = 0.25
_HORA_RATE_DEG_PER_MIN = 0.5
_GHATI_RATE_DEG_PER_MIN = 1.25
_VIGHATI_RATE_DEG_PER_MIN = 15.0  # PyJHora's rate; not found in the BPHS corpus


@serialized_swiss_state
def _special_ascendant(
    jd, place, divisional_chart_factor=1, chart_method=1, lagna_rate_factor=1.0,
    base_rasi=None, count_from_end_of_sign=None, dhasa_progression_correction=0.0,
    ayanamsha_id=None,
):
    """PyJHora 4.8.6 ``drik.special_ascendant`` with its Sun-at-sunrise offset corrected.

    Upstream reads the Sun at ``sunrise(jd, place)[2] + place.timezone / 24``. ``sunrise()[2]`` is
    already a LOCAL julian day and ``charts.divisional_chart`` subtracts the timezone itself, so
    the Sun was evaluated ``tz`` hours AFTER sunrise (about +0.23 deg for IST). Everything else is
    byte-for-byte upstream; only the sunrise JD handed to ``divisional_chart`` differs.

    Inherited from upstream and NOT changed here: sunrise is taken on the birth's own civil date, so
    a birth BEFORE that day's sunrise gets a negative elapsed time rather than the previous day's
    sunrise. Indu / Sree / Varnada (sign-level rules) and Pranapada / Bhrigu Bindhu / Kunda are not
    audited against the corpus in this lane (Indu's kalas 30,16,6,8,10,12,1 match Uttara Kalamrita).

    ``ayanamsha_id`` (``None`` = lahiri, the pipeline default) selects the sidereal mode and pins the
    ``.se1`` path on the CALLING thread INSIDE this function (swisseph keeps both per thread on
    Linux), so a direct or resumed-on-a-new-thread call never computes in whatever mode an earlier
    function left behind.  ``compute_special_lagnas`` passes its own ``ayanamsha_id`` here.
    """
    from jhora import const
    from jhora.horoscope.chart import charts

    with with_sidereal_mode(ayanamsha_id, jd, via_jhora=True):
        _, _, _, time_of_birth_in_hours = drik.jd_to_gregorian(jd)
        srise = drik.sunrise(jd, place)
        time_diff_mins = (time_of_birth_in_hours - srise[0]) * 60
        pp = charts.divisional_chart(
            srise[2], place,  # local sunrise JD as returned: divisional_chart removes the tz itself
            divisional_chart_factor=divisional_chart_factor, chart_method=chart_method,
            base_rasi=base_rasi, count_from_end_of_sign=count_from_end_of_sign,
            dhasa_progression_correction=dhasa_progression_correction,
        )[:const._pp_count_upto_ketu]
        sun_long = pp[1][1][0] * 30 + pp[1][1][1]
        spl_long = (sun_long + time_diff_mins * lagna_rate_factor) % 360
        return drik.dasavarga_from_long(spl_long, divisional_chart_factor)


def _rate_lagna(rate: float):
    def lagna(jd, place, divisional_chart_factor=1, chart_method=1, base_rasi=None,
              count_from_end_of_sign=None, dhasa_progression_correction=0.0, ayanamsha_id=None):
        return _special_ascendant(
            jd, place, divisional_chart_factor=divisional_chart_factor, chart_method=chart_method,
            lagna_rate_factor=rate, base_rasi=base_rasi,
            count_from_end_of_sign=count_from_end_of_sign,
            dhasa_progression_correction=dhasa_progression_correction,
            ayanamsha_id=ayanamsha_id,
        )
    return lagna


bhava_lagna = _rate_lagna(_BHAVA_RATE_DEG_PER_MIN)
hora_lagna = _rate_lagna(_HORA_RATE_DEG_PER_MIN)
ghati_lagna = _rate_lagna(_GHATI_RATE_DEG_PER_MIN)
vighati_lagna = _rate_lagna(_VIGHATI_RATE_DEG_PER_MIN)


@serialized_swiss_state
def _varnada_lagna_bv_raman(dob, tob, place, ayanamsha_id=None):
    """BV Raman Varnada Lagna of the Lagna itself (``varnada_method=1``, ``house_index=1``).

    A line-for-line copy of PyJHora 4.8.6 ``charts._varnada_lagna_bv_raman`` for those arguments,
    except that its Hora Lagna SIGN comes from this module's corrected ``hora_lagna`` instead of
    ``drik.hora_lagna`` (which carries the Sun-at-sunrise offset). It is a copy, NOT a swap of
    ``drik.hora_lagna``: no PyJHora attribute is ever reassigned, so no other caller in the process
    can observe a changed function. ``test_special_lagna_sunrise_sun`` pins parity with upstream
    wherever the two Hora signs agree. Returns ``(varnada_sign_index_0_11, lagna_degree_in_sign)``.

    ``ayanamsha_id`` (``None`` = lahiri) selects the sidereal mode and pins the ``.se1`` path on the
    CALLING thread inside this function (see ``_special_ascendant``).
    """
    from jhora import const, utils
    from jhora.horoscope.chart import charts

    jd_at_dob = utils.julian_day_number(dob, tob)
    with with_sidereal_mode(ayanamsha_id, jd_at_dob, via_jhora=True):
        planet_positions = charts.divisional_chart(jd_at_dob, place)
        lagna = planet_positions[0][1][0] % 12
        asc_long = planet_positions[0][1][1]
        lagna_is_odd = lagna in const.odd_signs
        count1 = (utils.count_rasis(0, lagna, direction=1) if lagna_is_odd
                  else utils.count_rasis(11, lagna, direction=-1))
        hora_sign, _ = hora_lagna(jd_at_dob, place, ayanamsha_id=ayanamsha_id)
        hora_sign = hora_sign % 12
        hora_is_odd = hora_sign in const.odd_signs
        count2 = (utils.count_rasis(0, hora_sign, direction=1) if hora_is_odd
                  else utils.count_rasis(11, hora_sign, direction=-1))
        count = ((count1 + count2) % 12 if hora_is_odd == lagna_is_odd
                 else (max(count1, count2) - min(count1, count2)) % 12)
        varnada = (utils.count_rasis(1, count, direction=1) if lagna_is_odd
                   else utils.count_rasis(12, count, direction=-1))
        return varnada - 1, asc_long


@serialized_swiss_state
def compute_special_lagnas(
    jd_ut: float,
    dob: Any,
    tob: tuple[int, int, int],
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    """
    Returns a dict of {name: {sign, sign_id, degree_in_sign, longitude_deg}}
    for: bhava_lagna, hora_lagna, ghati_lagna, vighati_lagna, indu_lagna,
    sree_lagna, pranapada_lagna, bhrigu_bindhu_lagna, kunda_lagna,
    varnada_lagna. On a COMPUTATION failure for any single lagna, that entry carries
    {"error": ...} rather than aborting the whole batch. An ephemeris-BACKEND failure
    (``SwissBackendError`` / ``OutOfCorpusRangeError`` / ``WindowUncheckedError``) is NOT such a
    failure: it propagates and fails the caller (the infrastructure cannot compute at all).
    """
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = _place(lat, lon, tz)

    out: dict[str, Any] = {}

    # jd-only special ascendants (drik.py:1959-1988, 2107-2281)
    _jd_only = [
        ("bhava_lagna", partial(bhava_lagna, ayanamsha_id=ayanamsha_id)),
        ("hora_lagna", partial(hora_lagna, ayanamsha_id=ayanamsha_id)),
        ("ghati_lagna", partial(ghati_lagna, ayanamsha_id=ayanamsha_id)),
        ("vighati_lagna", partial(vighati_lagna, ayanamsha_id=ayanamsha_id)),
        ("indu_lagna", drik.indu_lagna),
        ("sree_lagna", drik.sree_lagna),
        ("pranapada_lagna", drik.pranapada_lagna),
        ("bhrigu_bindhu_lagna", drik.bhrigu_bindhu_lagna),
        ("kunda_lagna", drik.kunda_lagna),
    ]
    for name, fn in _jd_only:
        try:
            sign_idx, deg = fn(jd_ut, place)
            out[name] = _to_dict(sign_idx, deg)
        except BACKEND_FAILURE_ERRORS:
            # Infrastructure failure (no .se1 backend / out-of-corpus JD / unchecked window), not
            # "this lagna is undefined": fail the build, never an {"error"} entry that ga_sensitive
            # would turn into a FLOORED row (SS ruling 2026-10-03).
            raise
        except Exception as exc:  # noqa: BLE001
            out[name] = {"error": f"{name} failed: {exc!r}"}

    # Varnada Lagna needs (dob, tob, place) not jd (charts.py:1749) — BV Raman
    # method (varnada_method=1), house_index=1 (Varnada of the Lagna itself).
    try:
        sign_idx, deg = _varnada_lagna_bv_raman(dob, tob, place, ayanamsha_id=ayanamsha_id)
        out["varnada_lagna"] = _to_dict(sign_idx, deg)
    except BACKEND_FAILURE_ERRORS:
        raise  # infrastructure failure, not "undefined": see the loop above
    except Exception as exc:  # noqa: BLE001
        out["varnada_lagna"] = {"error": f"varnada_lagna failed: {exc!r}"}

    return out
