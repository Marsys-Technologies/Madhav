"""
houses.py — Lagna (ascendant) + 12 whole-sign houses.

Whole-sign is the default house system for this instrument: house 1 = the sign
the Lagna falls in,
houses 2..12 follow in zodiacal order.
"""
from __future__ import annotations

from typing import Any

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def compute_ascendant(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    # jd_ut MUST be a LOCAL-time Julian Day (utils.julian_day_number(date, local_tob)).
    # Passing a UTC-based JD (swe.julday with UT hours) gives a ~9-sign error for IST
    # births because drik.ascendant does its own UT conversion using the Place timezone.
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = _place(lat, lon, tz)
    asc = drik.ascendant(jd_ut, place)
    # ascendant -> [sign_idx, deg_in_sign, nak_idx, pada]
    sign_idx = int(asc[0])
    deg_in_sign = float(asc[1])
    full_long = sign_idx * 30.0 + deg_in_sign
    nak = int(asc[2]) if len(asc) > 2 else 0
    pada = int(asc[3]) if len(asc) > 3 else 0
    return {
        "longitude_deg": full_long,
        "degree_in_sign": deg_in_sign,
        "sign": _names.sign_name(sign_idx),
        "sign_id": sign_idx + 1,  # 1-based per L2.5 contract
        "sign_lord": _names.sign_lord(sign_idx),
        "nakshatra": _names.nakshatra_name(nak) if nak else None,
        "nakshatra_id": nak,
        "pada": pada,
    }


def compute_midheaven(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    """
    D-9 fix (R6 1d-sensitive lane, 2026-07-10): real MC (Midheaven) from
    Swiss Ephemeris, replacing the previous `Lagna + 270°` computable
    substitute (a non-canonical approximation banned by canonical-or-floor —
    true MC diverges from Lagna+270 by several degrees at this birth
    latitude/longitude).

    Mirrors drik.ascendant() exactly (drik.py:1667-1684) but reads
    ascmc[1] (MC) instead of ascmc[0] (Asc) from the same swe.houses_ex()
    call, using the same ayanamsha/sidereal flags so MC and Lagna are
    computed from the identical ephemeris state.
    """
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = _place(lat, lon, tz)
    _, plat, plon, ptz = place
    jd_utc = jd_ut - (ptz / 24.0)
    swe = drik.swe
    if drik.const._TROPICAL_MODE:
        flags = swe.FLG_SWIEPH
    else:
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | drik._rise_flags
    ascmc = swe.houses_ex(jd_utc, plat, plon, flags=flags)[1]
    nirayana_mc = drik.utils.norm360(ascmc[1])
    sign_idx = int(nirayana_mc / 30.0)
    deg_in_sign = nirayana_mc - sign_idx * 30.0
    nak_no, pada, _ = drik.nakshatra_pada(nirayana_mc)
    return {
        "longitude_deg": nirayana_mc,
        "degree_in_sign": deg_in_sign,
        "sign": _names.sign_name(sign_idx),
        "sign_id": sign_idx + 1,
        "sign_lord": _names.sign_lord(sign_idx),
        "nakshatra": _names.nakshatra_name(nak_no) if nak_no else None,
        "nakshatra_id": nak_no,
        "pada": pada,
    }


def compute_houses(ascendant: dict[str, Any]) -> list[dict[str, Any]]:
    """12 whole-sign houses starting from the Lagna sign."""
    # ascendant['sign_id'] is 1-based; convert to 0-based for arithmetic.
    asc_sign0 = int(ascendant["sign_id"]) - 1
    houses: list[dict[str, Any]] = []
    for h in range(12):
        sign_idx = (asc_sign0 + h) % 12
        houses.append({
            "house_number": h + 1,
            "house_num": h + 1,  # alias for l25_builder
            "sign": _names.sign_name(sign_idx),
            "sign_id": sign_idx + 1,  # 1-based per L2.5 contract
            "sign_lord": _names.sign_lord(sign_idx),
        })
    return houses


# ── Bhāva-chalit (real astronomical cusps) ────────────────────────────────────
# DR-2 doctrine: whole-sign (compute_houses / house_d1) STAYS PRIMARY and is NOT
# touched. This is a FULL SECOND DATA LAYER, purely additive: real Sripati (Indian
# bhava-chalita) + Placidus (KP/Western) cusps computed natively by PyJHora, used
# for chalit-frame context and sandhi (junction) detection in synthesis.

SANDHI_ORB_DEG_DEFAULT = 3.0  # Binder-adjudicated ACCEPT (BRIEF_D1_5B §B)


def _arc_sep(a: float, b: float) -> float:
    """Smallest angular separation (deg, 0..180) between two longitudes."""
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def _mid_point(a: float, b: float) -> float:
    """Midpoint along the forward arc a -> b (mod 360). Mirrors PyJHora."""
    return (a + ((b - a) % 360.0) / 2.0) % 360.0


def _forward_arc_contains(long_deg: float, start: float, end: float) -> bool:
    """True if long_deg lies on the forward arc [start, end) (mod 360)."""
    span = (end - start) % 360.0
    off = (long_deg - start) % 360.0
    return off < span


def compute_bhava_chalit(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
    grahas: list[dict[str, Any]] | None = None,
    sandhi_orb_deg: float = SANDHI_ORB_DEG_DEFAULT,
) -> dict[str, Any]:
    """
    Real bhāva-chalit cusps (ADDITIVE second data layer; DR-2 — whole-sign stays
    primary). Two house systems computed natively by PyJHora:

      * Sripati (Indian bhāva-chalita): ``drik.bhaava_madhya_sripathi`` returns 12
        bhāva-madhyas (house centres); bhāva boundaries (sandhis) are the midpoints
        of adjacent madhyas. A graha's chalit bhāva is the arc [start, end) it is in.
      * Placidus (KP/Western): ``drik.bhaava_madhya_swe(house_code='P')`` returns the
        12 house-cusp boundaries (cusp[0] = ascendant). Surfaced for KP cuspal use.

    jd_ut MUST be a LOCAL-time Julian Day (utils.julian_day_number(date, local_tob)),
    exactly as ``compute_ascendant`` requires — a UTC-based JD gives a ~9-sign error
    for IST births (see the caveat at compute_ascendant, houses.py:29-31). ``compute.py``
    already builds jd_ut this way and passes it straight through.

    ``grahas`` (optional): list of graha dicts carrying ``name``, ``longitude_deg``
    and the whole-sign ``house`` (int). When provided, per-graha chalit assignment,
    cusp distances and sandhi flags are computed; divergence between whole-sign and
    chalit house is one of the two sandhi triggers.

    Returns a dict::

        {
          "sandhi_orb_deg": 3.0,
          "sripati":  {"madhyas": [12 floats],
                       "cusps":   [{house, start, madhya, end}, ... 12]},
          "placidus": {"cusp_boundaries": [12 floats],   # cusp[h] = KP cusp of house h+1
                       "cusps":   [{house, start, madhya, end}, ... 12]},
          "graha_chalit": {GRAHA_NAME: {chalit_house, whole_sign_house,
                                        dist_to_madhya_deg, dist_to_nearest_boundary_deg,
                                        nearest_boundary, sandhi_flag,
                                        sandhi_reasons: [...]}}
        }
    """
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = _place(lat, lon, tz)

    # --- Sripati (Indian bhāva-chalita) madhyas + derived boundaries ---
    sri_madhyas = [float(x) % 360.0 for x in drik.bhaava_madhya_sripathi(jd_ut, place)]
    # sandhi[h] = boundary between house h and house h+1 = midpoint(madhya[h], madhya[h+1]).
    # House h therefore starts at sandhi[h-1] and ends at sandhi[h].
    sri_sandhi = [_mid_point(sri_madhyas[h], sri_madhyas[(h + 1) % 12]) for h in range(12)]
    sripati_cusps: list[dict[str, Any]] = []
    for h in range(12):
        start = sri_sandhi[(h - 1) % 12]
        end = sri_sandhi[h]
        sripati_cusps.append({
            "house": h + 1,
            "start": start,
            "madhya": sri_madhyas[h],
            "end": end,
        })

    # --- Placidus (KP/Western) cusp boundaries ---
    plac_bounds = [float(x) % 360.0 for x in drik.bhaava_madhya_swe(jd_ut, place, house_code="P")]
    placidus_cusps: list[dict[str, Any]] = []
    for h in range(12):
        start = plac_bounds[h]
        end = plac_bounds[(h + 1) % 12]
        placidus_cusps.append({
            "house": h + 1,
            "start": start,
            "madhya": _mid_point(start, end),
            "end": end,
        })

    # --- Per-graha chalit assignment (Sripati is the primary chalit frame) ---
    graha_chalit: dict[str, Any] = {}
    for g in (grahas or []):
        name = g.get("name")
        if not name:
            continue
        lon_deg = g.get("longitude_deg")
        if lon_deg is None:
            continue
        lon_deg = float(lon_deg) % 360.0

        chalit_house = None
        for h in range(12):
            start = sri_sandhi[(h - 1) % 12]
            end = sri_sandhi[h]
            if _forward_arc_contains(lon_deg, start, end):
                chalit_house = h + 1
                break
        if chalit_house is None:  # numerical fallback (should not happen)
            chalit_house = 1

        hidx = chalit_house - 1
        b_start = sri_sandhi[(hidx - 1) % 12]
        b_end = sri_sandhi[hidx]
        dist_start = _arc_sep(lon_deg, b_start)
        dist_end = _arc_sep(lon_deg, b_end)
        if dist_start <= dist_end:
            nearest_boundary, dist_boundary = "start", dist_start
        else:
            nearest_boundary, dist_boundary = "end", dist_end
        dist_madhya = _arc_sep(lon_deg, sri_madhyas[hidx])

        whole_sign_house = g.get("house")
        whole_sign_house = int(whole_sign_house) if whole_sign_house is not None else None

        sandhi_reasons: list[str] = []
        if dist_boundary <= sandhi_orb_deg:
            sandhi_reasons.append("within_boundary_orb")
        if whole_sign_house is not None and whole_sign_house != chalit_house:
            sandhi_reasons.append("wholesign_chalit_divergence")

        graha_chalit[name] = {
            "chalit_house": chalit_house,
            "whole_sign_house": whole_sign_house,
            "dist_to_madhya_deg": dist_madhya,
            "dist_to_nearest_boundary_deg": dist_boundary,
            "nearest_boundary": nearest_boundary,
            "sandhi_flag": bool(sandhi_reasons),
            "sandhi_reasons": sandhi_reasons,
        }

    return {
        "sandhi_orb_deg": sandhi_orb_deg,
        "sripati": {"madhyas": sri_madhyas, "cusps": sripati_cusps},
        "placidus": {"cusp_boundaries": plac_bounds, "cusps": placidus_cusps},
        "graha_chalit": graha_chalit,
    }
