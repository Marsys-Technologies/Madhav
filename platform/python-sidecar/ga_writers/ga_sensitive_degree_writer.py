"""
ga_sensitive_degree_writer.py — GA sensitive-degree checks writer (WP-2.5 / LCA-10)
====================================================================================
Asset:  ga_sensitive_degree
Table:  chart_facts   (fact_category = 'sensitive_degree_check')
Grain:  one row per (graha × concept) with degree evidence, per ayanamsha.

Root defect (REMEDIATION_PLAN_v2_0 §5, WP-2.5 / R-47 / LCA-10):
  UNREACHABLE-by-nonexistence — the canon calls for these per-graha sensitive-degree
  facts, but no L1 writer computed them. A Venus spot-check found 7 canonical facets at
  0 rows. This writer computes them, one deterministic classical rule per facet.

Facets computed (each by its CLASSICAL rule, cited — CLAUDE.md §B.10, no invented numbers):

  1. mrityu_bhaga        — fatal-degree proximity. Degree table + tolerances delegated
                           1:1 from PyJHora const.mrityu_bhaga_base_longitudes /
                           const.mrityu_bhaga_tolerances (BPHS / Jataka Parijata mrityu
                           bhaga). Same trusted-delegation discipline as migration 430
                           (bg_shashtiamsha_deities) — real cited data, not hand-recall.
  2. neecha_bhanga       — cancellation of debilitation (Neecha Bhanga Raja Yoga). Reuses
                           ga_yoga_writer.detect_neecha_bhanga (BPHS Ch. on NBRY).
  3. kartari             — papa-/shubha-kartari (hemming): malefics/benefics in the 2nd
                           and 12th bhava FROM the graha (classical kartari yoga).
  4. sarvatobhadra_vedha — natal nakshatra vedha in the Sarvatobhadra Chakra: a graha
                           receiving vedha from another graha's nakshatra (Prasna Marga /
                           SBC vedha geometry — rekha/kona/vithi vedha).
  5. khareshwara         — 22nd drekkana (from Lagna) + 64th navamsa (from Moon), the two
                           classical maraka/trik markers (BPHS; "khara" = 64th navamsa).
  6. pushkara            — pushkara-navamsa (3°20' auspicious arc per sign) + pushkara-bhaga
                           (auspicious degree per sign), delegated from PyJHora
                           const.pushkara_navamsa / const.pushkara_bhagas.
  7. kranti              — declination (kranti/apakrama) of the graha's ecliptic point and
                           rasi-samya (equal-declination) pairs. β (celestial latitude) is
                           not in L1, so β=0 (ecliptic-point kranti) — explicitly flagged.
  8. gandanta            — proximity to the water→fire sandhi (last 3°20' of Cancer/Scorpio/
                           Pisces + first 3°20' of Leo/Sagittarius/Aries = the Ashlesha-Magha
                           / Jyeshtha-Mula / Revati-Ashwini nakshatra junctions).

  9. yogi_system         — MC-029 (Śodhana Builder T6 "YOGI-BINDU"): Yogi/Avayogi/
                           Duplicate-Yogi/Sahayogi, under a SEPARATE fact_category
                           'sensitive_point_yogi' (see build_yogi_points_rows below).
                           Yogi Sphuta = Sun + Moon + 93°20'; Yogi Graha = nakshatra lord
                           of that point (BPHS Ch.20 / Tajik Nilakanthi). Avayogi Sphuta =
                           Yogi Sphuta + 186°40'; Avayogi Graha = its nakshatra lord.
                           Duplicate-Yogi = rasi (sign) lord of the Yogi Sphuta's own sign.
                           Sahayogi = the SAME classical quantity as Duplicate-Yogi under
                           its Tajik Nilakanthi name (cross-checked against PyJHora's own
                           reference implementation — see citations on that function).

B.10 posture: every degree constant here is either (a) delegated from PyJHora's shipped
classical arrays (mrityu bhaga, pushkara) with the array cited, or (b) computed by a
stated deterministic rule (kartari counting, gandanta arc, declination formula). No degree
is hand-recalled. Facets whose L1 inputs are incomplete (kranti β; full 28-nakshatra SBC
vedha table) emit honest evidence rows carrying provenance_status for the W3 jyotish-domain
verifier to adjudicate — never a fabricated fired/not-fired verdict.

Idempotency: L1 delete-then-insert scoped to (chart_id, ayanamsha_id, fact_category) via
ga_writers._idempotency.replace_prior_chart_facts (fact_category='sensitive_degree_check'
for facets 1-8; fact_category='sensitive_point_yogi' for facet 9 — both categories are
present in the combined `rows` list build_ga_sensitive_degree_substep passes to
replace_prior_chart_facts, which scopes its DELETE to every distinct fact_category found
in the rows it's given, so neither category accretes on rebuild — §N.3).
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg.rows

from jhora import const as _jconst
from ga_writers._idempotency import replace_prior_chart_facts

logger = logging.getLogger(__name__)

GA_SENSITIVE_DEGREE_ASSET_ID = "ga_sensitive_degree"
FACT_CATEGORY = "sensitive_degree_check"

# MC-029 (Śodhana Builder T6 "YOGI-BINDU"): Yogi/Avayogi/Duplicate-Yogi/Sahayogi live under
# their OWN fact_category — distinct from the 8 facets above — per the builder's brief §5.
YOGI_CATEGORY = "sensitive_point_yogi"

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "krishnamurti",
    "true_chitra",
    "raman",
    "surya_siddhanta_classical",
]

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# fact_subject codes — must match ga_positions_writer.PLANET_TO_SUBJECT
GRAHA_SUBJECT = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
    "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN", "Lagna": "LAGNA",
}
SUBJECT_GRAHA = {v: k for k, v in GRAHA_SUBJECT.items()}
SEVEN_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
NINE_GRAHAS = SEVEN_GRAHAS + ["Rahu", "Ketu"]

# Natural malefics / benefics for kartari (classical: Sun/Mars/Saturn/Rahu/Ketu papa;
# Jupiter/Venus/waxing-Moon/well-associated-Mercury shubha). BPHS Ch.3 grahaguna.
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
NATURAL_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}

# ── mrityu bhaga (DELEGATED 1:1 from PyJHora const — BPHS / Jataka Parijata) ──────
# const.mrityu_bhaga_base_longitudes: 12 rows (rasi 0..11), each 11 cols in order
#   [Sun, Moon, Mars, Merc, Jup, Ven, Sat, Rahu, Ketu, Mandi, Lagna]
# const.mrityu_bhaga_tolerances: col-index -> tolerance in degrees.
_MB_COL = {"Sun": 0, "Moon": 1, "Mars": 2, "Mercury": 3, "Jupiter": 4,
           "Venus": 5, "Saturn": 6, "Rahu": 7, "Ketu": 8, "Lagna": 10}
MRITYU_BHAGA_CITATION = (
    "BPHS / Jataka Parijata mrityu-bhaga; degrees delegated 1:1 from "
    "PyJHora const.mrityu_bhaga_base_longitudes (rasi×graha) + "
    "const.mrityu_bhaga_tolerances (per-graha orb)."
)


def mrityu_bhaga_degree(graha: str, sign_num: int) -> Optional[float]:
    """Return the classical mrityu-bhaga degree-in-sign for `graha` in rasi `sign_num`
    (0=Aries). None if the graha has no mrityu-bhaga entry."""
    col = _MB_COL.get(graha)
    if col is None or not (0 <= sign_num <= 11):
        return None
    return float(_jconst.mrityu_bhaga_base_longitudes[sign_num][col])


def mrityu_bhaga_tolerance(graha: str) -> float:
    col = _MB_COL.get(graha)
    tol = _jconst.mrityu_bhaga_tolerances
    if graha == "Lagna":
        return float(tol.get("L", 2 / 3))
    return float(tol.get(col, 0.25))


def check_mrityu_bhaga(graha: str, sign_num: int, degree_in_sign: float) -> dict:
    """Fatal-degree check. Fired iff |deg - mrityu_deg| <= tolerance (degrees)."""
    mb = mrityu_bhaga_degree(graha, sign_num)
    if mb is None:
        return {"fired": False, "reason": "no_mrityu_bhaga_entry"}
    tol = mrityu_bhaga_tolerance(graha)
    orb = abs(degree_in_sign - mb)
    return {
        "fired": orb <= tol,
        "mrityu_bhaga_deg": round(mb, 4),
        "graha_deg_in_sign": round(degree_in_sign, 4),
        "orb_deg": round(orb, 4),
        "tolerance_deg": round(tol, 4),
        "sign": SIGNS[sign_num],
    }


# ── pushkara (DELEGATED from PyJHora const — pushkara navamsa/bhaga) ──────────────
PUSHKARA_NAVAMSA_ARC = 30.0 / 9.0  # 3°20' — one navamsa span
PUSHKARA_CITATION = (
    "Classical pushkara-navamsa (3°20' auspicious arc per sign) + pushkara-bhaga "
    "(auspicious degree per sign); values delegated from PyJHora "
    "const.pushkara_navamsa / const.pushkara_bhagas."
)


def check_pushkara(sign_num: int, degree_in_sign: float) -> dict:
    """Pushkara-navamsa: deg within [start, start+3°20'). Pushkara-bhaga: deg == bhaga (±0.5°)."""
    pn_start = float(_jconst.pushkara_navamsa[sign_num])
    pb_deg = float(_jconst.pushkara_bhagas[sign_num])
    in_navamsa = pn_start <= degree_in_sign < (pn_start + PUSHKARA_NAVAMSA_ARC)
    bhaga_orb = abs(degree_in_sign - pb_deg)
    return {
        "fired": bool(in_navamsa or bhaga_orb <= 0.5),
        "in_pushkara_navamsa": bool(in_navamsa),
        "pushkara_navamsa_start_deg": round(pn_start, 4),
        "on_pushkara_bhaga": bool(bhaga_orb <= 0.5),
        "pushkara_bhaga_deg": round(pb_deg, 4),
        "bhaga_orb_deg": round(bhaga_orb, 4),
        "graha_deg_in_sign": round(degree_in_sign, 4),
    }


# ── gandanta (water→fire sandhi; nakshatra-gandanta junctions) ────────────────────
# Water signs Cancer(3), Scorpio(7), Pisces(11); fire signs Leo(4), Sag(8), Aries(0).
# Gandanta = last 3°20' of a water sign + first 3°20' of the following fire sign =
# the Ashlesha–Magha / Jyeshtha–Mula / Revati–Ashwini nakshatra junctions.
GANDANTA_ARC = 30.0 / 9.0  # 3°20'
_WATER_SIGNS = {3, 7, 11}
_FIRE_SIGNS = {4, 8, 0}
GANDANTA_CITATION = (
    "Classical gandanta (BPHS / Sarvartha Chintamani): last 3°20' of a water sign "
    "and first 3°20' of the succeeding fire sign — the Ashlesha-Magha, Jyeshtha-Mula "
    "and Revati-Ashwini nakshatra sandhi."
)


def check_gandanta(sign_num: int, degree_in_sign: float) -> dict:
    """Proximity to nearest gandanta point (junction). Fired iff within a gandanta arc."""
    dist = None
    zone = None
    if sign_num in _WATER_SIGNS and degree_in_sign >= (30.0 - GANDANTA_ARC):
        dist = 30.0 - degree_in_sign          # distance to the sign-end junction
        zone = f"end_of_{SIGNS[sign_num]}"
    elif sign_num in _FIRE_SIGNS and degree_in_sign <= GANDANTA_ARC:
        dist = degree_in_sign                  # distance from the sign-start junction
        zone = f"start_of_{SIGNS[sign_num]}"
    return {
        "fired": dist is not None,
        "gandanta_zone": zone,
        "distance_to_junction_deg": round(dist, 4) if dist is not None else None,
        "gandanta_arc_deg": round(GANDANTA_ARC, 4),
        "graha_deg_in_sign": round(degree_in_sign, 4),
        "sign": SIGNS[sign_num],
    }


# ── kartari (papa / shubha hemming from the graha) ────────────────────────────────
KARTARI_CITATION = (
    "Classical kartari yoga: a graha hemmed by malefics in the 2nd and 12th bhava "
    "from it = papa-kartari; by benefics = shubha-kartari (BPHS grahaguna Ch.3)."
)


def check_kartari(graha: str, house_by_graha: dict[str, int]) -> dict:
    """Malefic/benefic occupancy of the 2nd and 12th house FROM the graha's house."""
    h = house_by_graha.get(graha)
    if not h:
        return {"fired": False, "reason": "graha_house_unknown"}
    h2 = (h % 12) + 1                 # 2nd from graha
    h12 = ((h - 2) % 12) + 1          # 12th from graha
    occ2 = [g for g, gh in house_by_graha.items() if gh == h2 and g not in (graha, "Lagna")]
    occ12 = [g for g, gh in house_by_graha.items() if gh == h12 and g not in (graha, "Lagna")]
    mal2 = [g for g in occ2 if g in NATURAL_MALEFICS]
    mal12 = [g for g in occ12 if g in NATURAL_MALEFICS]
    ben2 = [g for g in occ2 if g in NATURAL_BENEFICS]
    ben12 = [g for g in occ12 if g in NATURAL_BENEFICS]
    papa = bool(mal2 and mal12)
    shubha = bool(ben2 and ben12)
    kind = "papa_kartari" if papa else "shubha_kartari" if shubha else None
    return {
        "fired": bool(papa or shubha),
        "kartari_type": kind,
        "second_house": h2, "twelfth_house": h12,
        "malefics_2nd": mal2, "malefics_12th": mal12,
        "benefics_2nd": ben2, "benefics_12th": ben12,
    }


# ── khareshwara: 22nd drekkana (from Lagna) + 64th navamsa (from Moon) ─────────────
KHARESHWARA_CITATION = (
    "BPHS trik/maraka markers: the 22nd drekkana counted from the Lagna's drekkana and "
    "the 64th navamsa counted from the Moon's navamsa (khareshwara). Their sign-lords "
    "are classical death-inflicting significators."
)


def _drekkana_sign_index(sign_num: int, degree_in_sign: float) -> int:
    """Absolute drekkana ordinal 0..35 from Aries (each drekkana = 10°)."""
    drek_within = int(degree_in_sign // 10.0)  # 0,1,2
    return sign_num * 3 + drek_within


def _navamsa_sign_index(sign_num: int, degree_in_sign: float) -> int:
    """Absolute navamsa ordinal 0..107 from Aries (each navamsa = 3°20')."""
    nav_within = int(degree_in_sign // (30.0 / 9.0))  # 0..8
    return sign_num * 9 + nav_within


def compute_22nd_drekkana(lagna_sign_num: int, lagna_deg: float) -> dict:
    """The rasi holding the 22nd drekkana counted (inclusive) from the Lagna's own
    drekkana — the classical maraka 'twenty-second drekkana' marker (BPHS)."""
    lagna_drek = _drekkana_sign_index(lagna_sign_num, lagna_deg)  # 0..35
    target_drek = (lagna_drek + 21) % 36   # 22nd inclusive of the lagna drekkana as the 1st
    target_sign = (target_drek // 3) % 12
    return {
        "lagna_drekkana_ordinal": lagna_drek,
        "twentysecond_drekkana_ordinal": target_drek,
        "twentysecond_drekkana_sign": SIGNS[target_sign],
        "twentysecond_drekkana_sign_num": target_sign,
    }


def compute_64th_navamsa(moon_sign_num: int, moon_deg: float) -> dict:
    """The rasi holding the 64th navamsa counted (inclusive) from the Moon's navamsa."""
    moon_nav = _navamsa_sign_index(moon_sign_num, moon_deg)  # 0..107
    target_nav = (moon_nav + 63) % 108
    target_sign = (target_nav // 9) % 12
    return {
        "moon_navamsa_ordinal": moon_nav,
        "sixtyfourth_navamsa_ordinal": target_nav,
        "sixtyfourth_navamsa_sign": SIGNS[target_sign],
        "sixtyfourth_navamsa_sign_num": target_sign,
    }


# ── kranti / declination (ecliptic-point; β not in L1) ────────────────────────────
_OBLIQUITY_DEG = 23.436  # mean obliquity of the ecliptic (modern ~23.44°; Surya Siddhanta ~24°)
KRANTI_CITATION = (
    "Kranti (apakrama / declination) of the graha's ecliptic point: "
    "δ = arcsin(sin(ε)·sin(λ_tropical)), ε≈23.44° (spherical astronomy / Surya Siddhanta "
    "kranti). NOTE: graha celestial latitude β is not stored in L1 → β=0 (ecliptic-point "
    "kranti); a β-corrected kranti is a W3 refinement."
)


def compute_kranti(longitude_tropical_deg: float) -> dict:
    lam = math.radians(longitude_tropical_deg % 360.0)
    dec = math.degrees(math.asin(math.sin(math.radians(_OBLIQUITY_DEG)) * math.sin(lam)))
    return {
        "kranti_deg": round(dec, 4),
        "direction": "north" if dec >= 0 else "south",
        "obliquity_deg": _OBLIQUITY_DEG,
        "latitude_assumption": "beta_zero_ecliptic_point",
    }


# ── Yogi / Avayogi / Duplicate-Yogi / Sahayogi ─────────────────────────────────────
# MC-029 (Śodhana Builder T6 "YOGI-BINDU"). Standard classical Tajika/Jyotish construct,
# confirmed absent from every existing L1 serving surface before this pass.
#
# Yogi Sphuta   = Sun + Moon + 93°20' (mod 360°)               — BPHS Ch.20 / Tajik Nilakanthi
# Yogi Graha    = nakshatra LORD of the Yogi Sphuta
# Avayogi Sphuta= Yogi Sphuta + 186°40' (mod 360°)
# Avayogi Graha = nakshatra LORD of the Avayogi Sphuta
# Duplicate-Yogi= rasi (SIGN) lord of the Yogi Sphuta's own sign (NOT the nakshatra lord)
# Sahayogi      = PyJHora's own reference implementation
#                 (jhora/horoscope/chart/sphuta.py, __main__ demo block) computes
#                 `sahayogi_planet = const._house_owners_list[yh]` where `yh` is the Yogi
#                 Sphuta's rasi index — i.e. Sahayogi and Duplicate-Yogi are the SAME
#                 classical quantity under two attested names (Raman's "Duplicate Yogi" vs
#                 Tajik Nilakanthi's "Sahayogi"), not two independent constructs. Both are
#                 served as their own subject rows (not merely aliased) so either name is
#                 independently queryable, per this builder's brief.
YOGI_OFFSET_DEG = 93.0 + 20.0 / 60.0          # 93°20'
AVAYOGI_OFFSET_DEG = 186.0 + 40.0 / 60.0      # 186°40' beyond the Yogi Sphuta

YOGI_NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
YOGI_NAK_SPAN_DEG = 360.0 / 27.0  # 13°20'

# Fallback tables (correct Parashari/vimshottari classics) — used only if the L0 reference
# tables (reference_signs / reference_nakshatra) are unreachable at build time. Mirrors the
# fallback discipline already established in ga_sensitive_writer.py / ga_dashas_writer.py.
_YOGI_FALLBACK_SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                             "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
_YOGI_FALLBACK_NAK_LORDS = (
    ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"] * 3
)

YOGI_POINT_CITATION = (
    "BPHS Ch.20 / Tajik Nilakanthi: Yogi Sphuta = Sun + Moon + 93°20' (mod 360°); Yogi "
    "Graha = nakshatra lord of the Yogi Sphuta. Cross-checked against PyJHora "
    "jhora.horoscope.chart.sphuta.yogi_sphuta (add_yogi_longitude=True adds exactly "
    "93+20/60 degrees to Moon+Sun)."
)
AVAYOGI_POINT_CITATION = (
    "BPHS Ch.20 / Tajik Nilakanthi: Avayogi Sphuta = Yogi Sphuta + 186°40' (mod 360°); "
    "Avayogi Graha = nakshatra lord of the Avayogi Sphuta. Cross-checked against PyJHora "
    "jhora.horoscope.chart.sphuta.avayogi_sphuta (yogi_long + 186+40/60 degrees)."
)
DUPLICATE_YOGI_CITATION = (
    "Classical 'Duplicate Yogi' (Raman, Hindu Predictive Astrology): rasi (sign) lord of "
    "the Yogi Sphuta's own sign — distinct from the Yogi Graha (the NAKSHATRA lord of the "
    "same point). Cross-checked against PyJHora jhora.const._house_owners_list[yogi_rasi]."
)
SAHAYOGI_CITATION = (
    "Tajik Nilakanthi Sahayogi Graha. PyJHora's own reference implementation "
    "(jhora/horoscope/chart/sphuta.py __main__ demo: "
    "'sahayogi_planet = const._house_owners_list[yh]', yh = Yogi Sphuta's rasi) computes "
    "Sahayogi identically to the Duplicate-Yogi construction above: both are the rasi lord "
    "of the Yogi Sphuta's sign. This row is served independently (not merely an alias of "
    "DUPLICATE_YOGI) so the Tajik Nilakanthi name is directly queryable by fact_subject."
)


def _load_yogi_sign_lords(conn: Any) -> list[str]:
    """0-based (Aries=0) sign→lord, from L0 reference_signs. Falls back to Parashari classics
    if the table is unreachable (never fabricates a divergent lordship table)."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("SELECT lord FROM reference_signs ORDER BY sign_id")
            lords = [r[0].capitalize() for r in cur.fetchall()]
        if len(lords) == 12:
            return lords
    except Exception as exc:
        logger.warning("[ga_sensitive_degree][yogi] reference_signs unavailable (%s); "
                       "using Parashari fallback lords", exc)
    return list(_YOGI_FALLBACK_SIGN_LORDS)


def _load_yogi_nakshatra_lords(conn: Any) -> list[str]:
    """0-based (Ashwini=0) nakshatra→vimshottari lord, from the CANONICAL L0
    reference_nakshatra table (28 rows incl. Abhijit; migration 302 deprecated the older
    reference_nakshatras — this reads only the canonical singular table, never the
    deprecated one). Falls back to the standard 9-lord vimshottari cycle if unreachable."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                "SELECT vimshottari_lord FROM reference_nakshatra "
                "WHERE nakshatra_id <= 27 ORDER BY nakshatra_id"
            )
            lords = [r[0].capitalize() for r in cur.fetchall()]
        if len(lords) == 27:
            return lords
    except Exception as exc:
        logger.warning("[ga_sensitive_degree][yogi] reference_nakshatra unavailable (%s); "
                       "using vimshottari-cycle fallback lords", exc)
    return list(_YOGI_FALLBACK_NAK_LORDS)


def _yogi_point_two_pass(sun_long: float, moon_long: float) -> tuple[float, float, bool]:
    """Two INDEPENDENTLY-WRITTEN code paths for the Yogi Sphuta longitude (mirrors the
    ga_tajaka_writer ephemeris_audit_jsonb two-pass discipline):
      Pass A — plain floating-point degree arithmetic.
      Pass B — integer-arcsecond arithmetic (a different representation/rounding path,
               sharing no intermediate float state with Pass A).
    Returns (yogi_deg [Pass A value, the one served], divergence_arcsec, agrees)."""
    yogi_a = (sun_long + moon_long + YOGI_OFFSET_DEG) % 360.0

    sun_asec = round(sun_long * 3600.0)
    moon_asec = round(moon_long * 3600.0)
    offset_asec = round(YOGI_OFFSET_DEG * 3600.0)  # 93*3600 + 20*60 = 335600
    yogi_asec = (sun_asec + moon_asec + offset_asec) % (360 * 3600)
    yogi_b = yogi_asec / 3600.0

    diff = abs(yogi_a - yogi_b)
    diff = min(diff, 360.0 - diff)
    divergence_arcsec = diff * 3600.0
    agrees = divergence_arcsec <= 1.0  # rounding-only tolerance (1 arcsec)
    return yogi_a, divergence_arcsec, agrees


def _avayogi_point_two_pass(yogi_deg: float) -> tuple[float, float, bool]:
    """Same two-pass discipline as `_yogi_point_two_pass`, for Avayogi = Yogi + 186°40'."""
    avayogi_a = (yogi_deg + AVAYOGI_OFFSET_DEG) % 360.0

    yogi_asec = round(yogi_deg * 3600.0)
    offset_asec = round(AVAYOGI_OFFSET_DEG * 3600.0)
    avayogi_asec = (yogi_asec + offset_asec) % (360 * 3600)
    avayogi_b = avayogi_asec / 3600.0

    diff = abs(avayogi_a - avayogi_b)
    diff = min(diff, 360.0 - diff)
    divergence_arcsec = diff * 3600.0
    agrees = divergence_arcsec <= 1.0
    return avayogi_a, divergence_arcsec, agrees


def _yogi_nakshatra_of(long_deg: float, nak_lords: list[str]) -> tuple[str, str, int]:
    """(nakshatra_name, nakshatra_lord, 0-based sign_num) for a Yogi-system longitude."""
    long_norm = long_deg % 360.0
    nak_idx = min(int(long_norm / YOGI_NAK_SPAN_DEG), 26)
    sign_idx = int(long_norm / 30.0) % 12
    return YOGI_NAKSHATRAS[nak_idx], nak_lords[nak_idx], sign_idx


def build_yogi_points_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    positions: dict[str, dict], conn: Any,
) -> list[dict]:
    """MC-029 (Śodhana Builder T6 "YOGI-BINDU"): Yogi / Avayogi / Duplicate-Yogi / Sahayogi.

    L1-authority discipline (§N.5): Sun/Moon longitudes are READ from `positions` (sourced
    from chart_facts by `load_positions`, never recomputed here) — this function only
    derives the Yogi-system points from those already-authoritative longitudes.

    Emits under fact_category=YOGI_CATEGORY ('sensitive_point_yogi'), a category distinct
    from FACT_CATEGORY so it is separately addressable; both categories share this writer's
    (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id) idempotency
    key and are both covered by the single replace_prior_chart_facts() call in
    build_ga_sensitive_degree_substep (§N.3 — no accretion on rebuild).
    """
    sun = positions.get("Sun")
    moon = positions.get("Moon")
    if not sun or not moon:
        logger.warning("[ga_sensitive_degree][yogi] Sun/Moon absent for chart=%s aya=%s; "
                       "skipping", chart_id, ayanamsha_id)
        return []
    sun_long = sun.get("longitude_sidereal")
    moon_long = moon.get("longitude_sidereal")
    if sun_long is None or moon_long is None:
        logger.warning("[ga_sensitive_degree][yogi] Sun/Moon longitude_sidereal missing for "
                       "chart=%s aya=%s; skipping", chart_id, ayanamsha_id)
        return []

    sign_lords = _load_yogi_sign_lords(conn)
    nak_lords = _load_yogi_nakshatra_lords(conn)
    now = datetime.now(timezone.utc)

    yogi_deg, yogi_div_asec, yogi_ok = _yogi_point_two_pass(sun_long, moon_long)
    yogi_nak, yogi_graha, yogi_sign_idx = _yogi_nakshatra_of(yogi_deg, nak_lords)
    yogi_status = "two_pass_verified" if yogi_ok else "divergent_flagged"

    avayogi_deg, avayogi_div_asec, avayogi_ok = _avayogi_point_two_pass(yogi_deg)
    avayogi_nak, avayogi_graha, avayogi_sign_idx = _yogi_nakshatra_of(avayogi_deg, nak_lords)
    avayogi_status = "two_pass_verified" if avayogi_ok else "divergent_flagged"

    # Duplicate-Yogi / Sahayogi two-pass: agree iff (a) the Yogi point itself two-pass
    # verified AND (b) the sign index re-derived from the independent arcsecond pass
    # (recomputed here, not threaded through, to keep this a genuinely independent
    # re-derivation rather than reusing Pass B's own state) matches the degree-pass sign.
    sun_asec = round(sun_long * 3600.0)
    moon_asec = round(moon_long * 3600.0)
    offset_asec = round(YOGI_OFFSET_DEG * 3600.0)
    yogi_asec_b = (sun_asec + moon_asec + offset_asec) % (360 * 3600)
    sign_idx_b = int((yogi_asec_b / 3600.0) / 30.0) % 12
    duplicate_ok = yogi_ok and (sign_idx_b == yogi_sign_idx)
    duplicate_status = "two_pass_verified" if duplicate_ok else "divergent_flagged"
    duplicate_yogi_graha = sign_lords[yogi_sign_idx]

    rows: list[dict] = [
        _row(chart_id, ayanamsha_id, build_id, "YOGI", "point_longitude",
             round(yogi_deg, 6), None,
             {"divergence_arcsec": round(yogi_div_asec, 4), "offset_deg": YOGI_OFFSET_DEG,
              "sun_longitude_sidereal": sun_long, "moon_longitude_sidereal": moon_long},
             YOGI_POINT_CITATION, now, provenance=yogi_status, category=YOGI_CATEGORY),
        _row(chart_id, ayanamsha_id, build_id, "YOGI", "sign",
             None, SIGNS[yogi_sign_idx], None,
             YOGI_POINT_CITATION, now, provenance=yogi_status, category=YOGI_CATEGORY),
        _row(chart_id, ayanamsha_id, build_id, "YOGI", "nakshatra",
             None, yogi_nak, None,
             YOGI_POINT_CITATION, now, provenance=yogi_status, category=YOGI_CATEGORY),
        _row(chart_id, ayanamsha_id, build_id, "YOGI", "assigned_graha",
             None, yogi_graha, None,
             YOGI_POINT_CITATION, now, provenance=yogi_status, category=YOGI_CATEGORY),

        _row(chart_id, ayanamsha_id, build_id, "AVAYOGI", "point_longitude",
             round(avayogi_deg, 6), None,
             {"divergence_arcsec": round(avayogi_div_asec, 4), "offset_deg": AVAYOGI_OFFSET_DEG},
             AVAYOGI_POINT_CITATION, now, provenance=avayogi_status, category=YOGI_CATEGORY),
        _row(chart_id, ayanamsha_id, build_id, "AVAYOGI", "sign",
             None, SIGNS[avayogi_sign_idx], None,
             AVAYOGI_POINT_CITATION, now, provenance=avayogi_status, category=YOGI_CATEGORY),
        _row(chart_id, ayanamsha_id, build_id, "AVAYOGI", "nakshatra",
             None, avayogi_nak, None,
             AVAYOGI_POINT_CITATION, now, provenance=avayogi_status, category=YOGI_CATEGORY),
        _row(chart_id, ayanamsha_id, build_id, "AVAYOGI", "assigned_graha",
             None, avayogi_graha, None,
             AVAYOGI_POINT_CITATION, now, provenance=avayogi_status, category=YOGI_CATEGORY),

        _row(chart_id, ayanamsha_id, build_id, "DUPLICATE_YOGI", "sign",
             None, SIGNS[yogi_sign_idx], None,
             DUPLICATE_YOGI_CITATION, now, provenance=duplicate_status, category=YOGI_CATEGORY),
        _row(chart_id, ayanamsha_id, build_id, "DUPLICATE_YOGI", "assigned_graha",
             None, duplicate_yogi_graha, None,
             DUPLICATE_YOGI_CITATION, now, provenance=duplicate_status, category=YOGI_CATEGORY),

        _row(chart_id, ayanamsha_id, build_id, "SAHAYOGI", "sign",
             None, SIGNS[yogi_sign_idx], None,
             SAHAYOGI_CITATION, now, provenance=duplicate_status, category=YOGI_CATEGORY),
        _row(chart_id, ayanamsha_id, build_id, "SAHAYOGI", "assigned_graha",
             None, duplicate_yogi_graha, None,
             SAHAYOGI_CITATION, now, provenance=duplicate_status, category=YOGI_CATEGORY),
    ]
    return rows


# ── DB helpers ────────────────────────────────────────────────────────────────────

def _fact_id(subject: str, key: str, chart_id: str, ayanamsha_id: str, build_id: str,
             category: str = FACT_CATEGORY) -> str:
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_positions(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, dict]:
    """Read each graha's sign, sign_num, degree_in_sign, longitude_sidereal, house_d1,
    nakshatra, retrograde from chart_facts (L1-authority: never recomputed — §N.5)."""
    out: dict[str, dict] = {}
    with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
        cur.execute(
            """
            SELECT fact_subject, fact_category, fact_key, fact_value_text, fact_value_num
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND fact_category IN ('graha_position', 'graha_sign_attributes')
              AND fact_key IN ('sign','longitude_sidereal','nakshatra','house_d1',
                               'retrograde_flag','sign_num','degree_in_sign')
            """,
            (chart_id, ayanamsha_id),
        )
        for subject, cat, key, vtxt, vnum in cur.fetchall():
            graha = SUBJECT_GRAHA.get(subject)
            if graha is None:
                continue
            rec = out.setdefault(graha, {})
            if key == "sign":
                rec["sign"] = vtxt
            elif key == "sign_num":
                # chart_facts stores sign_num 1-BASED (Aries=1; ga_positions_writer.py:271).
                # Keep the raw DB value here and derive the canonical 0-based sign_num below.
                rec["_sign_num_db_1based"] = int(vnum) if vnum is not None else None
            elif key == "degree_in_sign":
                rec["degree_in_sign"] = float(vnum) if vnum is not None else None
            elif key == "longitude_sidereal":
                rec["longitude_sidereal"] = float(vnum) if vnum is not None else None
            elif key == "nakshatra":
                rec["nakshatra"] = vtxt
            elif key == "house_d1":
                rec["house_d1"] = int(vnum) if vnum is not None else None
            elif key == "retrograde_flag":
                rec["retrograde_flag"] = vtxt
    # Derive a CANONICAL 0-based sign_num (Aries=0) — the contract every facet helper and
    # jhora rasi index expects. Priority: longitude_sidereal (single source of truth, exactly
    # as the ga_structural dosha wiring derives it) → sign name → DB 1-based sign_num - 1.
    for graha, rec in out.items():
        lon = rec.get("longitude_sidereal")
        db_1based = rec.get("_sign_num_db_1based")
        if lon is not None:
            rec["sign_num"] = int(lon // 30) % 12
            if rec.get("degree_in_sign") is None:
                rec["degree_in_sign"] = lon % 30.0
        elif rec.get("sign") in SIGNS:
            rec["sign_num"] = SIGNS.index(rec["sign"])
        elif db_1based is not None:
            rec["sign_num"] = (db_1based - 1) % 12
        else:
            rec["sign_num"] = None
        rec.pop("_sign_num_db_1based", None)
    return out


def _ayanamsha_offset_deg(conn: Any, ayanamsha_id: str) -> Optional[float]:
    """Best-effort ayanamsha degree offset (sidereal→tropical) from chart_facts, if present.
    Returns None when unavailable — kranti then flags tropical longitude unresolved."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                """
                SELECT fact_value_num FROM chart_facts
                WHERE ayanamsha_id = %s AND fact_key = 'ayanamsha_value'
                  AND fact_value_num IS NOT NULL
                LIMIT 1
                """,
                (ayanamsha_id,),
            )
            row = cur.fetchone()
            return float(row[0]) if row else None
    except Exception:
        return None


# ── row builder ────────────────────────────────────────────────────────────────────

def _row(chart_id, ayanamsha_id, build_id, subject, key, num, text, jsonb,
         citation, computed_at, provenance="single", category: str = FACT_CATEGORY) -> dict:
    return {
        "fact_id": _fact_id(subject, key, chart_id, ayanamsha_id, build_id, category),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "fact_category": category,
        "fact_subject": subject,
        "fact_key": key,
        "fact_value_text": text,
        "fact_value_num": num,
        "fact_value_jsonb": json.dumps(jsonb) if jsonb is not None else None,
        "unit": "deg" if num is not None else None,
        "citation_ref": f"WP-2.5/LCA-10/{key}",
        "citation_human": citation,
        "source_calculation": f"ga_sensitive_degree_writer/{key}/{provenance}",
        "verification_pass_status": provenance,
        "engine_version": "ga_sensitive_degree_v1",
        "computed_at": computed_at,
    }


def build_sensitive_degree_rows(
    chart_id: str, build_id: str, ayanamsha_id: str, positions: dict[str, dict],
    ayanamsha_offset_deg: Optional[float] = None,
) -> list[dict]:
    """Pure builder — produce all sensitive_degree_check rows for one (chart × ayanamsha).
    Kept side-effect-free so unit tests can recompute a facet and diff it."""
    now = datetime.now(timezone.utc)
    rows: list[dict] = []
    house_by_graha = {g: rec.get("house_d1") for g, rec in positions.items() if rec.get("house_d1")}

    # canonical neecha-bhanga detector (single source of truth, R6A.1) — best-effort import
    try:
        from ga_writers.ga_yoga_writer import detect_neecha_bhanga  # type: ignore
    except Exception:
        detect_neecha_bhanga = None  # type: ignore

    for graha in NINE_GRAHAS:
        rec = positions.get(graha)
        if not rec:
            continue
        subject = GRAHA_SUBJECT[graha]
        sn = rec.get("sign_num")
        deg = rec.get("degree_in_sign")
        if sn is None or deg is None:
            continue

        # 1. mrityu bhaga
        mb = check_mrityu_bhaga(graha, sn, deg)
        rows.append(_row(chart_id, ayanamsha_id, build_id, subject, "mrityu_bhaga",
                         mb.get("orb_deg"), "fired" if mb["fired"] else "not_fired",
                         mb, MRITYU_BHAGA_CITATION, now))

        # 3. kartari
        kt = check_kartari(graha, house_by_graha)
        rows.append(_row(chart_id, ayanamsha_id, build_id, subject, "kartari",
                         None, kt.get("kartari_type") or "none", kt,
                         KARTARI_CITATION, now))

        # 6. pushkara
        pk = check_pushkara(sn, deg)
        rows.append(_row(chart_id, ayanamsha_id, build_id, subject, "pushkara",
                         pk.get("bhaga_orb_deg"),
                         "pushkara" if pk["fired"] else "not_pushkara", pk,
                         PUSHKARA_CITATION, now))

        # 8. gandanta
        gd = check_gandanta(sn, deg)
        rows.append(_row(chart_id, ayanamsha_id, build_id, subject, "gandanta",
                         gd.get("distance_to_junction_deg"),
                         "gandanta" if gd["fired"] else "not_gandanta", gd,
                         GANDANTA_CITATION, now))

        # 7. kranti (declination) — needs tropical longitude
        lon_sid = rec.get("longitude_sidereal")
        if lon_sid is not None and ayanamsha_offset_deg is not None:
            kr = compute_kranti(lon_sid + ayanamsha_offset_deg)
            rows.append(_row(chart_id, ayanamsha_id, build_id, subject, "kranti",
                             kr["kranti_deg"], kr["direction"], kr, KRANTI_CITATION, now))
        elif lon_sid is not None:
            rows.append(_row(chart_id, ayanamsha_id, build_id, subject, "kranti", None,
                             "ayanamsha_offset_unresolved",
                             {"longitude_sidereal": lon_sid,
                              "note": "tropical longitude unresolvable at build; W3 refinement"},
                             KRANTI_CITATION, now, provenance="pending_w3_verification"))

        # 2. neecha bhanga — only meaningful for the 7 grahas
        if detect_neecha_bhanga is not None and graha in SEVEN_GRAHAS:
            try:
                d1 = {g: {"sign_num": r.get("sign_num"), "house": r.get("house_d1"),
                          "degree_in_sign": r.get("degree_in_sign")}
                      for g, r in positions.items()}
                nb_findings = detect_neecha_bhanga(d1, varga="D1")  # type: ignore
                fired = bool(nb_findings and any(
                    (isinstance(f, dict) and f.get("graha") == graha) for f in nb_findings))
                rows.append(_row(chart_id, ayanamsha_id, build_id, subject, "neecha_bhanga",
                                 None, "cancelled" if fired else "not_applicable_or_intact",
                                 {"detector": "ga_yoga_writer.detect_neecha_bhanga"},
                                 "BPHS Neecha Bhanga Raja Yoga (via ga_yoga_writer detector)",
                                 now))
            except Exception as exc:  # detector shape mismatch → flag, do not fabricate
                rows.append(_row(chart_id, ayanamsha_id, build_id, subject, "neecha_bhanga",
                                 None, "detector_unavailable", {"error": str(exc)[:200]},
                                 "BPHS Neecha Bhanga Raja Yoga", now,
                                 provenance="pending_w3_verification"))

    # 5. khareshwara — chart-level (Lagna + Moon)
    lag = positions.get("Lagna")
    if lag and lag.get("sign_num") is not None and lag.get("degree_in_sign") is not None:
        d22 = compute_22nd_drekkana(lag["sign_num"], lag["degree_in_sign"])
        rows.append(_row(chart_id, ayanamsha_id, build_id, "LAGNA", "khareshwara_22nd_drekkana",
                         None, d22["twentysecond_drekkana_sign"], d22, KHARESHWARA_CITATION, now))
    moon = positions.get("Moon")
    if moon and moon.get("sign_num") is not None and moon.get("degree_in_sign") is not None:
        d64 = compute_64th_navamsa(moon["sign_num"], moon["degree_in_sign"])
        rows.append(_row(chart_id, ayanamsha_id, build_id, "MOON", "khareshwara_64th_navamsa",
                         None, d64["sixtyfourth_navamsa_sign"], d64, KHARESHWARA_CITATION, now))

    # 4. sarvatobhadra_vedha — natal nakshatra occupancy evidence (chart-level).
    # The full 28-nakshatra SBC rekha/kona/vithi vedha table is not in L1; rather than
    # hand-recall it (B.10), emit natal nakshatra occupancy for the W3 jyotish-domain
    # verifier to grade against the SBC geometry.
    nak_occ = {g: rec.get("nakshatra") for g, rec in positions.items() if rec.get("nakshatra")}
    if nak_occ:
        rows.append(_row(chart_id, ayanamsha_id, build_id, "CHART", "sarvatobhadra_vedha",
                         None, "nakshatra_occupancy_recorded", {"nakshatra_by_graha": nak_occ},
                         "Sarvatobhadra Chakra vedha (Prasna Marga): natal nakshatra occupancy "
                         "recorded; full rekha/kona/vithi vedha adjudicated at W3.", now,
                         provenance="pending_w3_verification"))
    return rows


def build_ga_sensitive_degree_substep(
    chart_id: str, build_id: str, ayanamsha_id: str, conn: Any,
) -> int:
    """Build + insert sensitive_degree_check rows for one (chart × ayanamsha).
    Orchestrator owns the transaction — this never commits/closes conn."""
    positions = load_positions(conn, chart_id, ayanamsha_id)
    if not positions:
        logger.warning("[ga_sensitive_degree] no positions for chart=%s aya=%s",
                       chart_id, ayanamsha_id)
        return 0
    offset = _ayanamsha_offset_deg(conn, ayanamsha_id)
    rows = build_sensitive_degree_rows(chart_id, build_id, ayanamsha_id, positions, offset)
    # MC-029 (Śodhana Builder T6): Yogi/Avayogi/Duplicate-Yogi/Sahayogi, under the separate
    # YOGI_CATEGORY fact_category. Appended into the SAME rows list so the single
    # replace_prior_chart_facts() call below scopes its delete-then-insert over BOTH
    # fact_categories present (§N.3 — neither category accretes on rebuild).
    rows.extend(build_yogi_points_rows(chart_id, ayanamsha_id, build_id, positions, conn))
    if not rows:
        return 0
    replace_prior_chart_facts(conn, rows)
    inserted = 0
    for r in rows:
        conn.execute(
            """
            INSERT INTO chart_facts
              (fact_id, chart_id, ayanamsha_id, build_id,
               fact_category, fact_subject, fact_key,
               fact_value_text, fact_value_num, fact_value_jsonb,
               unit, citation_ref, citation_human,
               source_calculation, verification_pass_status,
               engine_version, computed_at)
            VALUES
              (%(fact_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
               %(fact_category)s, %(fact_subject)s, %(fact_key)s,
               %(fact_value_text)s, %(fact_value_num)s, %(fact_value_jsonb)s,
               %(unit)s, %(citation_ref)s, %(citation_human)s,
               %(source_calculation)s, %(verification_pass_status)s,
               %(engine_version)s, %(computed_at)s)
            ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
            WHERE formula_id IS NULL
            DO UPDATE SET
              fact_id         = EXCLUDED.fact_id,
              fact_value_text = EXCLUDED.fact_value_text,
              fact_value_num  = EXCLUDED.fact_value_num,
              fact_value_jsonb= EXCLUDED.fact_value_jsonb,
              citation_human  = EXCLUDED.citation_human,
              computed_at     = EXCLUDED.computed_at
            """,
            r,
        )
        inserted += 1
    logger.info("[ga_sensitive_degree] chart=%s aya=%s inserted %d rows",
                chart_id, ayanamsha_id, inserted)
    return inserted
