"""
special_lagnas.py — Bhava/Hora/Ghati/Vighati/Indu/Sree/Pranapada/Bhrigu-Bindhu/
Kunda/Varnada Lagna, delegated entirely to PyJHora (jhora.panchanga.drik +
jhora.horoscope.chart.charts).

M-9 + M-10 fix (R6 1d-sensitive lane, 2026-07-10): the prior ga_sensitive_writer
computed Bhava/Hora/Ghati Lagna and "Pranapada Sphuta" as hand-rolled proxies
using the Sun's within-sign degree as a crude time-since-sunrise stand-in
(HL = Lagna + (Sun%30)*2, GL = Lagna + (Sun%30)*12, BL = 2*Sun - Lagna + 180,
Pranapada = Moon + (Lagna-Sun)*4 falsely cited "BPHS"). These are non-classical
approximations. PyJHora computes all of these correctly from the real
time-elapsed-since-sunrise (ghatis) at the birth place/moment via
`drik.special_ascendant()` (Bhava/Hora/Ghati/Vighati Lagna) and
`drik.pranapada_lagna()` (real BPHS Pranapada: ghatis-since-sunrise x4,
+ Sun's sign-category offset 0/120/240 for movable/dual/fixed) — see
drik.py:1959-2140.

Sunrise-based Bhava/Hora/Ghati/Vighati Lagna are computed by the local ``_special_ascendant`` below,
NOT by ``drik.special_ascendant``: PyJHora 4.8.6 reads the Sun ``tz`` hours after sunrise (see its
docstring). Indu Lagna, Sree Lagna, Bhrigu Bindhu Lagna, Kunda Lagna, and Varnada Lagna
were previously absent entirely from this writer; added here via direct
PyJHora delegation per the M-10 fix instruction ("delegate to PyJHora's
implementations rather than in-house approximations").
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from panchang_engine.swiss_state import serialized_swiss_state

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik


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
    """
    from jhora import const
    from jhora.horoscope.chart import charts

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
              count_from_end_of_sign=None, dhasa_progression_correction=0.0):
        return _special_ascendant(
            jd, place, divisional_chart_factor=divisional_chart_factor, chart_method=chart_method,
            lagna_rate_factor=rate, base_rasi=base_rasi,
            count_from_end_of_sign=count_from_end_of_sign,
            dhasa_progression_correction=dhasa_progression_correction,
        )
    return lagna


bhava_lagna = _rate_lagna(_BHAVA_RATE_DEG_PER_MIN)
hora_lagna = _rate_lagna(_HORA_RATE_DEG_PER_MIN)
ghati_lagna = _rate_lagna(_GHATI_RATE_DEG_PER_MIN)
vighati_lagna = _rate_lagna(_VIGHATI_RATE_DEG_PER_MIN)


@contextmanager
def _corrected_hora_lagna_for_varnada() -> Iterator[None]:
    """BV Raman Varnada Lagna derives its Hora Lagna SIGN from ``drik.hora_lagna`` internally.
    Swap in the corrected function for that one call and always restore it. Callers hold the
    process-wide Swiss-state lock (``compute_special_lagnas`` is ``@serialized_swiss_state``)."""
    original = drik.hora_lagna
    drik.hora_lagna = hora_lagna
    try:
        yield
    finally:
        drik.hora_lagna = original


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
    varnada_lagna. On failure for any single lagna, that entry carries
    {"error": ...} rather than aborting the whole batch.
    """
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = _place(lat, lon, tz)

    out: dict[str, Any] = {}

    # jd-only special ascendants (drik.py:1959-1988, 2107-2281)
    _jd_only = [
        ("bhava_lagna", bhava_lagna),
        ("hora_lagna", hora_lagna),
        ("ghati_lagna", ghati_lagna),
        ("vighati_lagna", vighati_lagna),
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
        except Exception as exc:  # noqa: BLE001
            out[name] = {"error": f"{name} failed: {exc!r}"}

    # Varnada Lagna needs (dob, tob, place) not jd (charts.py:1749) — BV Raman
    # method (varnada_method=1), house_index=1 (Varnada of the Lagna itself).
    try:
        from jhora.horoscope.chart import charts as _charts
        with _corrected_hora_lagna_for_varnada():
            sign_idx, deg = _charts.varnada_lagna(dob, tob, place, house_index=1, varnada_method=1)
        out["varnada_lagna"] = _to_dict(sign_idx, deg)
    except Exception as exc:  # noqa: BLE001
        out["varnada_lagna"] = {"error": f"varnada_lagna failed: {exc!r}"}

    return out
