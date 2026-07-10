"""
jaimini_chara.py — Jaimini Chara Dasha engine for MARSYS-JIS.

Implements standard Jaimini Chara Dasha computation (K.N. Rao's standard
restatement of the Jaimini Sutram / Upadesa Sutras rule, the same rule
implemented as the L1 authority in ga_writers/ga_dashas_writer.py
::_compute_dynamic_chara_params — CLAUDE.md §N.5, L1 is the authority over
L2+ derivations; this sidecar engine must never diverge from it):
  - 12 rashis serve as dasha lords.
  - Period for each rashi R = forward sign-count from R to R's lord's
    CURRENTLY OCCUPIED rashi (1-12 years; if the lord occupies its own sign,
    the count is 12).
  - Cycle total = sum of the 12 per-rashi counts. This is chart-dependent
    (NOT a fixed 120 — a prior version of this file used a degree-based
    30-minus-longitude formula that is not the classical rule and does not
    match ga_dashas; M-8 fix removed it).
  - Start rashi determined by Lagna (ascendant sign at birth).
  - Sub-periods (antar dasha) subdivide each rashi's period proportionally
    to the actual cycle total (not a hardcoded 120).

M-8 fix (hard-fail, no fallback): this engine REQUIRES the chart's real
sidereal planetary longitudes and lagna longitude. There is no
NATIVE_FALLBACK_LONGITUDES table — a prior version silently substituted
values that were wrong even for the native (Sun 322.61 Aquarius vs. FORENSIC
truth Capricorn; Lagna 51.28 Taurus vs. FORENSIC truth Aries) for every
caller, native or not. Per canonical-or-floor doctrine: callers must supply
real longitudes (from chart_facts) or the call raises — it never serves a
substitute chart's numbers labeled as this chart's dasha.

References: Jaimini Sutram, Upadesa Sutras §Chara Dasha computation;
K.N. Rao, "Jaimini's Upadesa Sutras" (chara dasha length = sign-count rule).
Session: TR-P7-S2. M-8 fix: MARSYS_DEFECT_GAP_REGISTER_v2_0.md.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Dict, Any, Optional

# ── Constants ──────────────────────────────────────────────────────────────────

DAYS_PER_YEAR = 365.25

# 12 rashis in zodiac order (1-indexed).
RASHIS = [
    "Aries",       # 1  (odd)
    "Taurus",      # 2  (even)
    "Gemini",      # 3  (odd)
    "Cancer",      # 4  (even)
    "Leo",         # 5  (odd)
    "Virgo",       # 6  (even)
    "Libra",       # 7  (odd)
    "Scorpio",     # 8  (even)
    "Sagittarius", # 9  (odd)
    "Capricorn",   # 10 (even)
    "Aquarius",    # 11 (odd)
    "Pisces",      # 12 (even)
]

# 0-indexed: True = odd rashi, False = even rashi
RASHI_ODD = [i % 2 == 0 for i in range(12)]  # index 0 = Aries (odd), 1 = Taurus (even)...

# Sign lords for each rashi (Parasara rulership; Rahu/Ketu as co-lords of Scorpio/Aquarius
# are not used for primary Chara Dasha computation — use Mars for Scorpio, Saturn for Aquarius).
SIGN_LORDS = {
    "Aries":       "Mars",
    "Taurus":      "Venus",
    "Gemini":      "Mercury",
    "Cancer":      "Moon",
    "Leo":         "Sun",
    "Virgo":       "Mercury",
    "Libra":       "Venus",
    "Scorpio":     "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn":   "Saturn",
    "Aquarius":    "Saturn",
    "Pisces":      "Jupiter",
}

# Grahas whose sign-lordship the Rao formula walks (Rahu/Ketu excluded — same
# 7-classical-graha school as ga_dashas_writer._compute_dynamic_chara_params).
_CLASSICAL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


# ── Core algorithm ─────────────────────────────────────────────────────────────

def _rashi_index_from_longitude(longitude: float) -> int:
    """Return 0-based rashi index (0=Aries, 11=Pisces) from ecliptic longitude."""
    return int(longitude / 30.0) % 12


def compute_chara_dasha_years(planet_longitudes: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
    """
    Compute Chara Dasha period lengths for all 12 rashis via the classical
    K.N. Rao sign-count rule (see module docstring). This is the SAME rule as
    ga_writers/ga_dashas_writer.py::_compute_dynamic_chara_params — L1 is the
    authority (CLAUDE.md §N.5); this engine must not diverge.

    Args:
        planet_longitudes: dict of planet_name → sidereal longitude (0–360),
            REQUIRED for the 7 classical grahas (Sun, Moon, Mars, Mercury,
            Jupiter, Venus, Saturn). No default — M-8 fix removed the
            NATIVE_FALLBACK_LONGITUDES table, which served wrong values
            (even for the native) to every caller.

    Raises:
        ValueError: if planet_longitudes is falsy or missing a required lord.
            Canonical-or-floor doctrine: a missing longitude is a hard-fail,
            never a computable substitute.

    Returns:
        List of 12 dicts: [{rashi, rashi_index, years, sign_lord, lord_rashi},
        ...] in zodiac order (Aries through Pisces). Total years is
        chart-dependent (NOT a fixed 120 — see module docstring).
    """
    if not planet_longitudes:
        raise ValueError(
            "[jaimini_chara] planet_longitudes is required — there is no "
            "native-chart fallback (M-8 fix). Supply this chart's real "
            f"sidereal longitudes for {_CLASSICAL_GRAHAS}."
        )

    periods: List[Dict[str, Any]] = []

    for idx, rashi in enumerate(RASHIS):
        lord = SIGN_LORDS[rashi]
        if lord not in planet_longitudes:
            raise ValueError(
                f"[jaimini_chara] planet_longitudes missing lord={lord!r} "
                f"(needed to derive the period for rashi={rashi!r}). "
                "Refusing to fabricate a period length."
            )
        lord_rashi_idx = _rashi_index_from_longitude(planet_longitudes[lord])
        steps = (lord_rashi_idx - idx) % 12
        years = 12 if steps == 0 else steps

        periods.append({
            "rashi": rashi,
            "rashi_index": idx,
            "years": years,
            "sign_lord": lord,
            "lord_rashi": RASHIS[lord_rashi_idx],
            "is_odd_rashi": RASHI_ODD[idx],
        })

    return periods


def compute_lagna_rashi_index(lagna_longitude: Optional[float]) -> int:
    """
    Return the 0-based rashi index of the chart's ascendant.

    Args:
        lagna_longitude: sidereal longitude (0-360) of the ascendant,
            REQUIRED. No default — M-8 fix removed NATIVE_LAGNA_RASHI_INDEX,
            which was wrong even for the native (Taurus vs. FORENSIC truth
            Aries) and was served to every caller regardless of chart.

    Raises:
        ValueError: if lagna_longitude is None.
    """
    if lagna_longitude is None:
        raise ValueError(
            "[jaimini_chara] lagna_longitude is required — there is no "
            "native-chart fallback (M-8 fix). Supply this chart's real "
            "sidereal ascendant longitude."
        )
    return _rashi_index_from_longitude(lagna_longitude)


def build_full_chara_dasha(
    birth_date: date,
    planet_longitudes: Dict[str, float],
    lagna_longitude: float,
) -> List[Dict[str, Any]]:
    """
    Build the complete Chara Dasha timeline anchored to birth_date.

    Args:
        birth_date: The chart's birth date.
        planet_longitudes: dict of this chart's real sidereal longitudes,
            REQUIRED (M-8 fix — no native-chart fallback; see
            compute_chara_dasha_years).
        lagna_longitude: this chart's real sidereal ascendant longitude,
            REQUIRED (M-8 fix — see compute_lagna_rashi_index).

    Returns:
        List of 12 dicts with rashi, years, start_date, end_date, and
        sub_periods (list of 12 antar dasha entries).
    """
    rashi_periods = compute_chara_dasha_years(planet_longitudes)
    lagna_idx = compute_lagna_rashi_index(lagna_longitude)
    cycle_total_years = sum(p["years"] for p in rashi_periods)

    # Reorder: start from lagna rashi, proceed in zodiac order.
    ordered = rashi_periods[lagna_idx:] + rashi_periods[:lagna_idx]

    result: List[Dict[str, Any]] = []
    current_start = birth_date

    for period in ordered:
        years = period["years"]
        days = int(round(years * DAYS_PER_YEAR))
        current_end = current_start + timedelta(days=days - 1)

        # Build antar dasha (sub-periods): 12 rashis subdivide the main period
        # in the same forward order starting from the main dasha rashi.
        antar_periods = _build_antar_dasha(
            current_start, current_end, period["rashi_index"], rashi_periods, cycle_total_years,
        )

        result.append({
            "rashi": period["rashi"],
            "sign_lord": period["sign_lord"],
            "years": years,
            "start_date": current_start.isoformat(),
            "end_date": current_end.isoformat(),
            "is_odd_rashi": period["is_odd_rashi"],
            "antar_dasha": antar_periods,
        })

        current_start = current_end + timedelta(days=1)

    return result


def _build_antar_dasha(
    md_start: date,
    md_end: date,
    md_rashi_index: int,
    rashi_periods: List[Dict[str, Any]],
    cycle_total_years: float,
) -> List[Dict[str, Any]]:
    """
    Build 12 antar dasha periods within a given maha dasha period.

    Each antar dasha (AD) is proportional: AD_days = (AD_years / cycle_total_years)
    * MD_days, where cycle_total_years is the ACTUAL sum of this chart's 12
    rashi periods (chart-dependent — not a fixed 120; M-8 fix). The 12 rashis
    cycle starting from the MD rashi in zodiac forward order.
    """
    md_total_days = (md_end - md_start).days + 1
    # Reorder rashi_periods starting from MD rashi
    ordered = rashi_periods[md_rashi_index:] + rashi_periods[:md_rashi_index]

    result: List[Dict[str, Any]] = []
    current_start = md_start

    for i, antar in enumerate(ordered):
        ad_years = antar["years"]
        # Proportional allocation
        if i < len(ordered) - 1:
            ad_days = int(round((ad_years / cycle_total_years) * md_total_days))
        else:
            # Last AD absorbs any rounding residual
            ad_days = (md_end - current_start).days + 1

        ad_end = current_start + timedelta(days=max(ad_days - 1, 0))
        # Clamp to MD boundary
        if ad_end > md_end:
            ad_end = md_end

        result.append({
            "rashi": antar["rashi"],
            "sign_lord": antar["sign_lord"],
            "years_proportion": round(ad_years / cycle_total_years, 4),
            "start_date": current_start.isoformat(),
            "end_date": ad_end.isoformat(),
        })

        current_start = ad_end + timedelta(days=1)
        if current_start > md_end:
            break

    return result


def get_active_dasha(
    full_periods: List[Dict[str, Any]],
    query_date: date,
) -> Dict[str, Any]:
    """
    Return the active maha dasha and antar dasha for a given query date.

    Args:
        full_periods: output of build_full_chara_dasha()
        query_date: the date to look up.

    Returns:
        dict with keys: active_rashi_dasha, active_antar_dasha.
        If query_date is outside the (chart-dependent) full cycle, returns the last/first period.
    """
    active_md = None
    for period in full_periods:
        start = date.fromisoformat(period["start_date"])
        end = date.fromisoformat(period["end_date"])
        if start <= query_date <= end:
            active_md = period
            break

    # Fallback: before birth → first; after cycle → last
    if active_md is None:
        if full_periods:
            active_md = full_periods[-1]
        else:
            return {"active_rashi_dasha": None, "active_antar_dasha": None}

    # Find active antar dasha
    active_ad = None
    for ad in active_md.get("antar_dasha", []):
        ad_start = date.fromisoformat(ad["start_date"])
        ad_end = date.fromisoformat(ad["end_date"])
        if ad_start <= query_date <= ad_end:
            active_ad = ad
            break

    if active_ad is None and active_md.get("antar_dasha"):
        active_ad = active_md["antar_dasha"][-1]

    return {
        "active_rashi_dasha": {
            "rashi": active_md["rashi"],
            "sign_lord": active_md["sign_lord"],
            "start_date": active_md["start_date"],
            "end_date": active_md["end_date"],
        },
        "active_antar_dasha": {
            "rashi": active_ad["rashi"] if active_ad else None,
            "sign_lord": active_ad["sign_lord"] if active_ad else None,
            "start_date": active_ad["start_date"] if active_ad else None,
            "end_date": active_ad["end_date"] if active_ad else None,
        } if active_ad else None,
    }
