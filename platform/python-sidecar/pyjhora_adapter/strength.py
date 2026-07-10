"""
strength.py — Shadbala, Vimshopaka Bala, and Ashtakavarga shodhana, delegated
to PyJHora's real classical implementations.

R6 TOTAL ELEVATION, lane 1a-strength (M-1/M-2/M-3 fixes):
  - Shadbala:      jhora.horoscope.chart.strength.shad_bala
                   (sthana = sapthavargaja + ojayugma + kendra + dreshkon + uchcha
                    bala; dig = bhaava-madhya angular distance; kala = nathonnata +
                    paksha + tribhaga + abdadhipathi + masadhipathi + vaaradhipathi +
                    hora + ayana + yuddha bala; cheshta = seeghrochcha kendra;
                    naisargika = fixed BPHS table; drik = Parasari graha drishti
                    matrix, benefic-minus-malefic net, per BPHS Ch.26).
  - Vimshopaka:    jhora.horoscope.chart.charts.vimsopaka_{shadvarga,sapthavarga,
                   dhasavarga,shodhasavarga}_of_planets — real per-varga dignity
                   scoring against the classical amsa-weight tables
                   (const.shadvarga_amsa_vimsopaka etc.), NOT a rescaled shadbala
                   total.
  - Ashtakavarga:  jhora.horoscope.chart.ashtakavarga.get_ashtaka_varga (raw binna
                   bindus from const.ashtaka_varga_dict) + sodhaya_pindas (real
                   trikona shodhana + ekadhipatya shodhana + rasimana/grahamana
                   gunakara multiplication -> raasi/graha/sodhya pinda).

Previously this module was a stub (`compute_strength` returning `{}`); the
build pipeline's `ga_strength_writer.py` hand-rolled all three domains with
heuristic approximations (0-1 six-bucket sthana lookup, linear-distance dig,
day/night-only kala, retro-flag cheshta, min(total/6*20,20) vimsopaka, and an
ashtakavarga "sodhita" that was literally the unreduced raw bindus). See
MARSYS_DEFECT_GAP_REGISTER M-1/M-2/M-3.

Units: shad_bala() returns virupas (0..60 scale per sub-component); this module
converts to RUPA (virupas/60) to match ga_strength_writer's existing `unit:
"rupa"` chart_facts contract, so downstream consumers (bo_laksana.py etc.) that
already expect rupa-scale `graha_shadbala_total` values keep working unchanged.

Note on drik (aspectual) bala: it is SIGNED under the real BPHS formula (net
malefic aspect can drive a planet's drik bala negative) — this is classically
correct, not a defect. Callers must not assume all shadbala sub-components are
non-negative; only the grand total is expected to be positive for a real chart.
"""
from __future__ import annotations

from typing import Any

from ._ayanamsha import resolve_mode
from ._jhora import charts, drik, utils

# PyJHora's const.SUN_TO_SATURN / SUN_TO_KETU planet-index order.
CLASSICAL_PLANETS: list[str] = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
]
NODE_PLANETS: list[str] = ["Rahu", "Ketu"]
ALL_GRAHA_PLANETS: list[str] = CLASSICAL_PLANETS + NODE_PLANETS  # index 0..8


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def _set_ayanamsha(ayanamsha_id: str) -> None:
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)


def compute_shadbala(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, dict[str, float]]:
    """Real BPHS shadbala for the 7 classical grahas (Sun..Saturn).

    Delegates to jhora.horoscope.chart.strength.shad_bala(jd, place), which
    returns [sthana, kaala, dig, cheshta, naisargika, drik, sum_virupas,
    rupas, strength_ratio] each as a 7-element list (Sun..Saturn order).

    Returns {graha_name: {sthana, dig, kala, cheshta, naisargika, drik,
                           total, total_virupas, strength_ratio}} — all
    sub-components and `total` in RUPA (virupas / 60); `total_virupas` kept
    for audit/spot-check convenience.
    """
    from jhora.horoscope.chart import strength as _jhora_strength

    place = _place(lat, lon, tz)
    _set_ayanamsha(ayanamsha_id)

    stb, kb, dgb, cb, nb, dkb, sb_sum, sb_rupa, sb_strength = _jhora_strength.shad_bala(jd_ut, place)

    result: dict[str, dict[str, float]] = {}
    for i, name in enumerate(CLASSICAL_PLANETS):
        result[name] = {
            "sthana": round(stb[i] / 60.0, 4),
            "dig": round(dgb[i] / 60.0, 4),
            "kala": round(kb[i] / 60.0, 4),
            "cheshta": round(cb[i] / 60.0, 4),
            "naisargika": round(nb[i] / 60.0, 4),
            "drik": round(dkb[i] / 60.0, 4),
            "total": round(sb_rupa[i], 4),
            "total_virupas": round(sb_sum[i], 4),
            "strength_ratio": round(sb_strength[i], 4),
        }
    return result


def compute_uchcha_bala(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, float]:
    """Real Uchcha Bala (exaltation-distance strength), in virupas (0..~60),
    for the 7 classical grahas — the specific BPHS input Ishta/Kashta Phala
    is defined against (NOT the full 5-component Sthana Bala, which sums
    uchcha + saptavargaja + ojayugma + kendra + dreshkon bala and can reach
    ~300 virupas). Delegates to
    jhora.horoscope.chart.strength._uchcha_bala on the D1 chart.
    """
    from jhora import const
    from jhora.horoscope.chart import strength as _jhora_strength

    place = _place(lat, lon, tz)
    _set_ayanamsha(ayanamsha_id)

    pp = charts.divisional_chart(jd_ut, place, divisional_chart_factor=1)[:const._pp_count_upto_ketu]
    ub = _jhora_strength._uchcha_bala(pp)
    return {name: round(float(ub[i]), 4) for i, name in enumerate(CLASSICAL_PLANETS)}


def compute_vimsopaka(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, dict[str, float]]:
    """Real BPHS Vimshopaka Bala across the 4 classical varga groupings.

    Delegates to jhora.horoscope.chart.charts.vimsopaka_{shadvarga,
    sapthavarga,dhasavarga,shodhasavarga}_of_planets, which score each
    planet's dignity (own/exalted/moolatrikona/friend/neutral/enemy) in every
    varga of that grouping, weighted by the classical amsa tables
    (const.shadvarga_amsa_vimsopaka etc., each summing to 20), NOT a rescaled
    shadbala total.

    Returns {graha_name: {shadvarga, saptavarga, dasavarga, shodasavarga}},
    each score on the classical 0..20 scale. Covers all 9 grahas — Vimshopaka
    Bala (unlike Shadbala) IS classically defined for Rahu/Ketu.
    """
    place = _place(lat, lon, tz)
    _set_ayanamsha(ayanamsha_id)

    shadvarga = charts.vimsopaka_shadvarga_of_planets(jd_ut, place)
    saptavarga = charts.vimsopaka_sapthavarga_of_planets(jd_ut, place)
    dasavarga = charts.vimsopaka_dhasavarga_of_planets(jd_ut, place)
    shodasavarga = charts.vimsopaka_shodhasavarga_of_planets(jd_ut, place)

    result: dict[str, dict[str, float]] = {}
    for i, name in enumerate(ALL_GRAHA_PLANETS):
        result[name] = {
            "shadvarga": round(float(shadvarga[i][2]), 4),
            "saptavarga": round(float(saptavarga[i][2]), 4),
            "dasavarga": round(float(dasavarga[i][2]), 4),
            "shodasavarga": round(float(shodasavarga[i][2]), 4),
        }
    return result


def compute_ashtakavarga_shodhana(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    """Real BPHS Ashtakavarga: raw (binna) bindus, sarvashtakavarga, and full
    shodhana (trikona sodhana + ekadhipatya sodhana + rasimana/grahamana
    gunakara multiplication -> raasi/graha/sodhya pinda).

    Delegates to jhora.horoscope.chart.ashtakavarga.get_ashtaka_varga (uses
    const.ashtaka_varga_dict, the classical per-planet benefic-house table)
    and .sodhaya_pindas (trikona_sodhana -> ekadhipatya_sodhana ->
    rasimana/grahamana-weighted pinda). The D1 chart driving both is
    jhora.horoscope.chart.charts.rasi_chart(jd_ut, place) — mean-node-patched
    at the pyjhora_adapter._jhora import boundary, so it is consistent with
    every other position fact this project stores.

    Returns:
      {
        "bindus": {graha_name: [12 raw bindus]} plus "SARVA": [12 sums]
                  (sum over houses == 337, the classical Parashara constant),
        "pinda": {graha_name: {"raasi": int, "graha": int, "sodhya": int}},
      }
    `sodhya` = raasi + graha (the final trikona+ekadhipatya-reduced,
    gunakara-multiplied pinda total); `graha` is the graha-pinda sub-component.
    """
    from jhora.horoscope.chart import ashtakavarga as _jhora_av

    place = _place(lat, lon, tz)
    _set_ayanamsha(ayanamsha_id)

    pp = charts.rasi_chart(jd_ut, place)
    chart_1d = utils.get_house_planet_list_from_planet_positions(pp)

    binna, samudhaya, _prastara = _jhora_av.get_ashtaka_varga(chart_1d)

    # IMPORTANT: extract the RAW bindus before calling sodhaya_pindas below.
    # PyJHora's _trikona_sodhana/_ekadhipatya_sodhana do `bav = binna[:]`
    # (a SHALLOW copy — the outer list is new but the 12 inner per-house
    # lists are the SAME objects as `binna`'s), then mutate `bav[p][r] -= ...`
    # in place. That mutates `binna`'s own rows too. Reading `binna` after
    # calling sodhaya_pindas would silently return shodhana-reduced bindus
    # mislabeled as "raw" — copy them out first, deeply, before shodhana runs.
    bindus: dict[str, list[int]] = {}
    for i, name in enumerate(CLASSICAL_PLANETS):
        bindus[name] = [int(v) for v in binna[i]]
    bindus["SARVA"] = [int(v) for v in samudhaya]

    raasi_p, graha_p, sodhya_p = _jhora_av.sodhaya_pindas(binna, chart_1d)

    pinda: dict[str, dict[str, int]] = {}
    for i, name in enumerate(CLASSICAL_PLANETS):
        pinda[name] = {
            "raasi": int(raasi_p[i]),
            "graha": int(graha_p[i]),
            "sodhya": int(sodhya_p[i]),
        }
    return {"bindus": bindus, "pinda": pinda}


def compute_strength(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    """Convenience bundle of all three domains (kept for any external callers
    of the old stub signature — previously returned `{}` unconditionally)."""
    return {
        "shadbala": compute_shadbala(jd_ut, ayanamsha_id, lat=lat, lon=lon, tz=tz),
        "vimsopaka": compute_vimsopaka(jd_ut, ayanamsha_id, lat=lat, lon=lon, tz=tz),
        "ashtakavarga": compute_ashtakavarga_shodhana(jd_ut, ayanamsha_id, lat=lat, lon=lon, tz=tz),
    }
