"""
services.ka_sangam.engine — Convergence scoring engine (L3 K4-a).

Implements ratified invariants:
  I-16: convergence_score — multiplicative necessary × saturating supporting
  I-17: orb_strength_score — cos² decay
  I-21: confidence_label — threshold classifier
  I-22: independent_current_count — correlation-discounted evidence counter

Also provides Mode A (daśā-prior soft funnel + transit search) and
Mode B (un-gated long-horizon anomaly sweep, flagged is_off_dasha_discovery=True).

U3 pass-1 (2026-06-22): 6 new supporting currents (C7–C12) added; C13 reserved.
U3 pass-2 (2026-06-22): C13 school_consensus activated (post-U4). All 12 currents now
  live at their original spec weights (sum = 1.0). The 11 pass-1 currents are scaled ×0.90
  to make room for C13=0.10.
  vedha_cancellation (C11) enters the NECESSARY side multiplicatively — not supporting.
  EnrichmentContext carries pre-fetched DB data (ashtakavarga, vedha, tajika,
  school_consensus_by_domain) from the writer.

NEVER calls conn.commit() or conn.rollback() — caller owns the transaction.
NEVER writes to any bodha_* table.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Ratified supporting-factor weights (I-16, sum = 1.0) ──────────────────────
# U3 pass-2 (2026-06-22): 12 currents (C13 school_consensus now live at 0.10).
# Pass-1 weights (11 currents) scaled ×0.90 to make room for C13.
# Tuning bounds from U3 spec §3.1 satisfied for all 12 keys.
# C11 vedha_cancellation is NOT here — it enters the NECESSARY side multiplicatively.

SUPPORTING_WEIGHTS: dict[str, float] = {
    'constituent_lord_transit':     0.180,  # spec 0.18, bound [0.14, 0.24] ✓
    'ashtakavarga_transit_potency': 0.120,  # C7, spec 0.12, bound [0.08, 0.16] ✓
    'cross_dasha_agreement':        0.120,  # spec 0.12, bound [0.09, 0.16] ✓
    'benefic_dristi':               0.100,  # spec 0.10, bound [0.07, 0.13] ✓
    'transit_to_transit':           0.080,  # C9, spec 0.08, bound [0.05, 0.11] ✓
    'panchanga_quality':            0.070,  # spec 0.07, bound [0.05, 0.10] ✓
    'tara_bala':                    0.060,  # spec 0.06, bound [0.04, 0.09] ✓
    'eclipse_proximity':            0.060,  # C8, spec 0.06, bound [0.03, 0.09] ✓
    'nakshatra_subsystem':          0.050,  # spec 0.05, bound [0.03, 0.07] ✓
    'station_retrograde':           0.030,  # C10, spec 0.03, bound [0.01, 0.05] ✓
    'tajika_annual_reinforcement':  0.030,  # C12, spec 0.03, bound [0.01, 0.05] ✓
    'school_consensus':             0.100,  # C13, spec 0.10, bound [0.07, 0.13] ✓
}

# Verify sum ≈ 1.0 at import (hard-fail if someone edits weights carelessly)
_SW_SUM = round(sum(SUPPORTING_WEIGHTS.values()), 6)
assert abs(_SW_SUM - 1.0) < 1e-4, f"SUPPORTING_WEIGHTS must sum to 1.0, got {_SW_SUM}"


# ── EnrichmentContext (U3) ────────────────────────────────────────────────────

class EnrichmentContext:
    """
    Pre-fetched DB data needed by U3 currents (C7, C11, C12, C13).
    Passed in by the ka_sangam writer to avoid passing db_conn into engine.py.

    ashtakavarga_bindu: {planet_name: {sign_number (1-12): bindu_count (0-8)}}
        Sourced from chart_facts (sarvashtakavarga) via ga_strength writer.
        Classical threshold: ≥ 5 bindus = strong; ≤ 3 = weak.
    vedha_rules: list of dicts with keys {graha, transit_to_house, vedha_house}
        Sourced from bg_transit_rules WHERE rule_type='vedha'.
    tajika_year_lords: list of dicts with keys {varsha_year, varshesha, muntha}
        Sourced from l1_tajik_varsha_year_lords for the current chart.
    school_consensus_by_domain: {domain: schools_agreeing (0-7)}
        Sourced from convergence_scores (populated by POST /api/build/school-consensus).
        C13 score = schools_agreeing / 7.0.
    """

    def __init__(
        self,
        ashtakavarga_bindu: Optional[dict[str, dict[int, int]]] = None,
        vedha_rules: Optional[list[dict]] = None,
        tajika_year_lords: Optional[list[dict]] = None,
        school_consensus_by_domain: Optional[dict[str, int]] = None,
    ):
        self.ashtakavarga_bindu = ashtakavarga_bindu or {}
        self.vedha_rules = vedha_rules or []
        self.tajika_year_lords = tajika_year_lords or []
        self.school_consensus_by_domain = school_consensus_by_domain or {}

    @classmethod
    def empty(cls) -> 'EnrichmentContext':
        return cls()


# ── U3 current derivation helpers ─────────────────────────────────────────────

def _c7_ashtakavarga_potency(
    planet: str,
    transit_sign: Optional[int],
    ctx: EnrichmentContext,
) -> float:
    """
    C7: ashtakavarga_transit_potency — does the transit DELIVER?
    Bindus ≥ 5 → strong (→ 1.0 scaled linearly). ≤ 2 → weak (→ 0.0).
    Range: 0.0 (0 bindus) … 1.0 (8 bindus). Formula: bindus / 8.0.
    Classical source: Parāśara, Ashtakavarga adhyāya.
    """
    if not ctx.ashtakavarga_bindu or transit_sign is None:
        return 0.0
    sign_map = ctx.ashtakavarga_bindu.get(planet, {})
    bindus = sign_map.get(transit_sign, 0)
    return min(1.0, bindus / 8.0)


def _c8_eclipse_score(
    planet: str,
    window_start_jd: float,
    window_end_jd: float,
    gochara_service: Any,
    target_lon: float,
    orb: float = 5.0,
) -> float:
    """
    C8: eclipse_proximity — solar/lunar eclipse near the transit trigger point.
    Uses ka_gochara.find_eclipse_proximity over the window.
    Score = max orb-strength across found events; 0.0 if none.
    """
    if gochara_service is None:
        return 0.0
    try:
        events = gochara_service.find_eclipse_proximity(
            node_planet='TrueNode',
            luminary='Sun' if planet not in ('Moon',) else 'Moon',
            orb=orb,
            start_jd=window_start_jd,
            end_jd=window_end_jd,
        )
        if not events:
            return 0.0
        max_score = 0.0
        for ev in events:
            orb_deg = getattr(ev, 'orb_at_event_deg', orb)
            s = orb_strength_score(orb_deg, orb, getattr(ev, 'applying_separating', 'applying'))
            max_score = max(max_score, s)
        return min(1.0, max_score)
    except Exception as exc:
        logger.debug("C8 eclipse_proximity failed: %s", exc)
        return 0.0


def _c9_transit_to_transit_score(
    planet: str,
    window_start_jd: float,
    window_end_jd: float,
    gochara_service: Any,
    outer_planets: Optional[list[str]] = None,
    orb: float = 3.0,
) -> float:
    """
    C9: transit_to_transit — outer-planet mutual aspect/conjunction in window.
    Checks planet vs Jupiter and Saturn (the era-defining cycle pair).
    Score = max orb-strength across found events; 0.0 if none.
    """
    if gochara_service is None:
        return 0.0
    check_against = outer_planets or ['Jupiter', 'Saturn']
    max_score = 0.0
    for partner in check_against:
        if partner == planet:
            continue
        try:
            events = gochara_service.find_transit_to_transit(
                planet_a=planet,
                planet_b=partner,
                aspect_degrees=[0, 60, 90, 120, 180],
                orb=orb,
                start_jd=window_start_jd,
                end_jd=window_end_jd,
            )
            for ev in events:
                orb_deg = getattr(ev, 'orb_at_event_deg', orb)
                s = orb_strength_score(orb_deg, orb, getattr(ev, 'applying_separating', 'applying'))
                max_score = max(max_score, s)
        except Exception as exc:
            logger.debug("C9 transit_to_transit(%s/%s) failed: %s", planet, partner, exc)
    return min(1.0, max_score)


def _c10_station_score(
    planet: str,
    window_start_jd: float,
    window_end_jd: float,
    gochara_service: Any,
) -> float:
    """
    C10: station_retrograde — planet stationing (retro/direct turn) in window.
    Score = 1.0 if any station event found; 0.0 if none. Stationing intensifies.
    """
    if gochara_service is None:
        return 0.0
    try:
        events = gochara_service.find_stations(
            planet=planet,
            start_jd=window_start_jd,
            end_jd=window_end_jd,
        )
        return 1.0 if events else 0.0
    except Exception as exc:
        logger.debug("C10 station(%s) failed: %s", planet, exc)
        return 0.0


def _c11_vedha_factor(
    planet: str,
    transit_house: Optional[int],
    ctx: EnrichmentContext,
) -> float:
    """
    C11: vedha_cancellation — NECESSARY-SIDE modulator (not supporting).
    Returns 0.0 when a vedha rule fully cancels this planet's transit,
    0.5 when the vedha planet is present in the vedha house (partial),
    1.0 (neutral) when no vedha applies (no cancellation).

    Enters necessary_conditions as (1 - 0.0) = 1.0 (no vedha) or lower.
    Classical source: Phaladeepika Ch.26 Gochara Vedha.

    CR-102 (2nd bug, T-6 fix): `bg_transit_rules.graha` is seeded lowercase
    ("saturn", "jupiter", ...; see brahmagyan/l0_transit.py) while callers in
    this module pass capitalized planet names ("Saturn", "Jupiter", ... —
    see `_resolve_transit_planet`). The comparison below is case-normalized
    so a real fetched vedha rule is never missed on case alone. `transit_house`
    itself must ALSO be in the correct house-FROM-MOON reference frame — see
    `_house_from_moon` below and its callers in mode_a_search/mode_b_sweep
    (the CR-102 primary bug: both call sites used to pass the transiting
    planet's raw rasi sign number here instead).
    """
    if not ctx.vedha_rules or transit_house is None:
        return 1.0  # no data → no vedha → neutral (1.0)
    planet_norm = (planet or '').strip().lower()
    for rule in ctx.vedha_rules:
        rule_planet = rule.get('graha') or rule.get('planet')
        to_house = rule.get('transit_to_house') or rule.get('to_house')
        vedha_h = rule.get('vedha_house')
        rule_planet_norm = (rule_planet or '').strip().lower()
        if rule_planet_norm == planet_norm and to_house == transit_house and vedha_h:
            return 0.3  # vedha present → strongly damp
    return 1.0


def _house_from_moon(
    transit_sign_idx_1based: Optional[int],
    moon_sign_idx_0based: Optional[int],
) -> Optional[int]:
    """
    CR-102 fix: classical Chandra Gochara house number (1-12) of a
    transiting sign, counted FROM THE NATAL MOON's sign — the reference
    frame `bg_transit_rules.primary_house` actually encodes (see
    brahmagyan/l0_transit.py: "Jupiter 2nd from Moon" etc.). Returns None
    (caller then falls back to the old, bugged sign-number behavior) when
    either input is unavailable, so this is additive-safe.

    Structurally identical to services.kala_trigger.trigger.house_from_moon
    (T-5's standalone re-derivation) — duplicated here, not imported, to
    avoid a reverse import (kala_trigger already imports from this module).
    """
    if transit_sign_idx_1based is None or moon_sign_idx_0based is None:
        return None
    return ((transit_sign_idx_1based - 1 - moon_sign_idx_0based) % 12) + 1


# ── Nakshatra / tara helpers (C5 nakshatra_subsystem, C_tara_bala) ────────────

# 27 nakshatras in sidereal order (0-indexed, matches pipeline.transit_search.NAKSHATRAS)
_NAKSHATRAS_ORDERED = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)
_NAK_NAME_TO_IDX: dict[str, int] = {n: i for i, n in enumerate(_NAKSHATRAS_ORDERED)}

# CR-87 fix: the module-level native janma-nakshatra constant (formerly
# _NATIVE_JANMA_NAK_IDX = 24, hardcoding Purva Bhadrapada for chart 482012f1)
# has been DELETED — not defaulted. Every function below now REQUIRES the
# caller to supply janma_nakshatra_idx (0-based index into _NAKSHATRAS_ORDERED)
# resolved per-chart from chart_facts (fact_subject='MOON', fact_key='nakshatra').
# A default here would silently reintroduce the CR-87 cross-chart contamination
# bug (every chart's tara-bala scored against Abhisek's janma nakshatra).

# 12 zodiac signs in zodiacal order (used to derive sade-sati signs per-chart).
_ZODIAC_SIGNS_ORDERED = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
_SIGN_NAME_TO_IDX: dict[str, int] = {s: i for i, s in enumerate(_ZODIAC_SIGNS_ORDERED)}


@dataclass(frozen=True)
class NativeChartContext:
    """Per-chart natal context required by tara-bala, sade-sati, and panchanga
    currents (CR-87). Resolved once per writer run from chart_facts /
    birth_params — never hardcoded, never defaulted to another chart's values.
    """
    janma_nakshatra_idx: int   # 0-based index into _NAKSHATRAS_ORDERED
    moon_sign: str             # e.g. "Aquarius"
    sade_sati_signs: tuple     # (12th-from-Moon, Moon sign, 2nd-from-Moon)
    sade_sati_severity: dict   # {sign: severity} keyed by the derived signs above
    location: dict             # {'lat': float, 'lon': float, 'tz_offset_minutes': int}


def derive_sade_sati_signs(moon_sign: str) -> tuple:
    """Derive the 3 sade-sati trigger signs from the natal Moon sign by fixed
    classical rule: the sign before the Moon sign (12th-from-Moon), the Moon
    sign itself, and the sign after (2nd-from-Moon) — zodiacal order.
    CR-87: moon_sign is REQUIRED — no default, no fallback to Aquarius.
    """
    idx = _SIGN_NAME_TO_IDX.get(moon_sign)
    if idx is None:
        raise ValueError(f"derive_sade_sati_signs: unknown moon_sign {moon_sign!r}")
    twelfth = _ZODIAC_SIGNS_ORDERED[(idx - 1) % 12]
    second  = _ZODIAC_SIGNS_ORDERED[(idx + 1) % 12]
    return (twelfth, moon_sign, second)


def derive_sade_sati_severity(sade_sati_signs: tuple) -> dict:
    """Classical doctrine severity weights (0.70 / 1.00 / 0.70) keyed by the
    derived sade-sati signs. The weights are doctrine constants (not natal
    constants) and stay fixed — only the sign keys are per-chart."""
    twelfth, moon_sign, second = sade_sati_signs
    return {twelfth: 0.70, moon_sign: 1.00, second: 0.70}

# Classical Tara Bala scores (1=Janma, 2=Sampat, … 9=Param-Mitra)
# Auspicious: 2, 4, 6, 8, 9.  Malefic: 3, 5, 7.  Mixed: 1.
_TARA_SCORES: dict[int, float] = {
    1: 0.4,  # Janma — mixed/intense
    2: 1.0,  # Sampat — wealth/prosperity
    3: 0.0,  # Vipat — danger
    4: 0.9,  # Kshema — safety/nourishment
    5: 0.1,  # Pratyak — obstacles
    6: 0.8,  # Sadhaka — achievement
    7: 0.0,  # Naidhana — destruction
    8: 0.9,  # Mitra — friends/support
    9: 1.0,  # Param-Mitra — great friend
}


def _tara_score_for_nakshatra(nakshatra_name: str, janma_nakshatra_idx: int) -> float:
    """Return Tara Bala score (0–1) for a nakshatra relative to the chart's
    own janma nakshatra (CR-87: janma_nakshatra_idx is a REQUIRED per-chart
    value — 0-based index into _NAKSHATRAS_ORDERED — never a native default)."""
    idx = _NAK_NAME_TO_IDX.get(nakshatra_name, -1)
    if idx < 0:
        return 0.0
    tara_pos = ((idx - janma_nakshatra_idx) % 9) + 1  # 1–9
    return _TARA_SCORES.get(tara_pos, 0.0)


def _c_nakshatra_subsystem(transit_nakshatra: str, janma_nakshatra_idx: int) -> float:
    """
    C5: nakshatra_subsystem — tara bala of the transit planet's nakshatra
    against THIS CHART's janma nakshatra (CR-87: per-chart, required param).
    Classical source: Parāśara Tara-Bala adhyāya.
    """
    return _tara_score_for_nakshatra(transit_nakshatra, janma_nakshatra_idx)


def _c_tara_bala_for_jd(peak_jd: float, janma_nakshatra_idx: int) -> float:
    """
    C_tara_bala: tara bala of the Moon's nakshatra at peak_jd relative to
    THIS CHART's janma nakshatra (CR-87: per-chart, required param).
    Requires pyswisseph.
    """
    try:
        import swisseph as swe
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        moon_pos, _ = swe.calc_ut(peak_jd, swe.MOON, swe.FLG_SIDEREAL)
        lon = moon_pos[0] % 360.0
        nak_idx = int(lon / (360.0 / 27.0)) % 27
        return _tara_score_for_nakshatra(_NAKSHATRAS_ORDERED[nak_idx], janma_nakshatra_idx)
    except Exception as exc:
        logger.debug("_c_tara_bala_for_jd failed at jd=%.1f: %s", peak_jd, exc)
        return 0.0


# ── C4: benefic_dristi helper ─────────────────────────────────────────────────

def _c_benefic_dristi(
    target_lon: float,
    w_jd_start: float,
    w_jd_end: float,
    gochara_service: Any,
    orb: float = 5.0,
) -> float:
    """
    C4: benefic_dristi — Jupiter or Venus aspecting the activation longitude
    within the window.  Classical: benefic dṛṣṭi bestows full grace on the
    aspected point; trines and conjunctions are strongest.

    Score = max( orb_strength × aspect_weight ) across Jupiter + Venus events.
    """
    if gochara_service is None:
        return 0.0
    # Classical aspect weights for benefic planets:
    #   conjunction 1.0, trine 1.0, sextile 0.7, opposition 0.5, square 0.2
    _ASP_WEIGHT: dict[int, float] = {0: 1.0, 60: 0.7, 90: 0.2, 120: 1.0, 180: 0.5}
    max_score = 0.0
    for benefic in ('Jupiter', 'Venus'):
        try:
            events = gochara_service.find_aspects(
                transit_planet=benefic,
                target_lon=target_lon,
                aspect_degrees=[0, 60, 90, 120, 180],
                orb=orb,
                start_jd=w_jd_start,
                end_jd=w_jd_end,
            )
            for ev in events:
                orb_deg = getattr(ev, 'orb_at_event_deg', orb)
                base = orb_strength_score(
                    orb_deg, orb, getattr(ev, 'applying_separating', 'applying')
                )
                asp = int(round(abs(float((ev.extra or {}).get('aspect_deg', 0)))))
                asp_weight = _ASP_WEIGHT.get(asp, 0.5)
                max_score = max(max_score, base * asp_weight)
        except Exception as exc:
            logger.debug("_c_benefic_dristi(%s) failed: %s", benefic, exc)
    return min(1.0, max_score)


# ── C6: cross_dasha_agreement helper ─────────────────────────────────────────

def _c_cross_dasha_agreement(peak_date: Any, eligible_windows: list) -> float:
    """
    C6: cross_dasha_agreement — how many dasha systems agree at peak_date.

    Uses the cross_dasha_agreement.count on EligibleWindow (already computed
    by KaDashaKalaService across 7 dasha systems).
    Score = max(count across overlapping windows) / 7.0, capped at 1.0.
    Mode B callers pass empty list → 0.0 (correct: no dasha prior in mode B).
    """
    if not eligible_windows:
        return 0.0
    best = 0
    for ew in eligible_windows:
        if ew.start_date <= peak_date <= ew.end_date:
            agreement = getattr(ew, 'cross_dasha_agreement', None)
            count = agreement.count if agreement is not None else 0
            best = max(best, count)
    return min(1.0, best / 7.0)


# ── C_panchanga_quality helper ────────────────────────────────────────────────

def _c_panchanga_quality(
    peak_date: Any,
    muhurta_service: Any,
    native_location: Optional[dict],
) -> float:
    """
    C_panchanga: muhurta score for peak_date at native's birth location.
    Returns 0.0 if muhurta_service is None or location is unavailable.
    Score normalized from 0-100 service scale to 0-1.
    """
    if muhurta_service is None or native_location is None:
        return 0.0
    try:
        raw = muhurta_service.score(peak_date, native_location, event='general')
        return min(1.0, max(0.0, float(raw) / 100.0))
    except Exception as exc:
        logger.debug("_c_panchanga_quality failed for %s: %s", peak_date, exc)
        return 0.0


def _c13_school_consensus_score(
    signature_class: str,
    ctx: EnrichmentContext,
) -> float:
    """
    C13: school_consensus (U3 pass-2, post-U4) — 7-school inter-tradition agreement.
    Score = schools_agreeing / 7.0.  Floor 0.0, ceiling 1.0.
    Domain inference: signature_class → domain (e.g. 'CAREER_PEAK' → 'CAREER').
    Sourced from convergence_scores.schools_agreeing (populated by school-consensus build).
    Returns 0.0 when school_consensus_by_domain is empty (pre-U4 safe default).
    """
    if not ctx.school_consensus_by_domain:
        return 0.0
    # Map signature_class prefix to domain
    domain: Optional[str] = None
    for prefix, mapped in (
        ('CAREER', 'CAREER'),
        ('HEALTH', 'HEALTH'),
        ('RELATIONSHIP', 'RELATIONSHIP'),
        ('SPIRITUAL', 'SPIRITUAL'),
        ('PSYCHOLOGICAL', 'PSYCHOLOGICAL'),
    ):
        if signature_class.upper().startswith(prefix):
            domain = mapped
            break
    if domain is None:
        return 0.0
    n_of_7 = ctx.school_consensus_by_domain.get(domain, 0)
    return min(1.0, max(0.0, n_of_7 / 7.0))


def _c12_tajika_score(
    window_start: date,
    domain_lord: Optional[str],
    ctx: EnrichmentContext,
) -> float:
    """
    C12: tajika_annual_reinforcement — varṣa chart varṣeśa/muntha agrees with window.
    Returns 1.0 if the year-lord for this window's year matches the domain's lord,
    0.5 if muntha matches, 0.0 otherwise.
    Source: l1_tajik_varsha_year_lords.
    """
    if not ctx.tajika_year_lords or domain_lord is None:
        return 0.0
    year = window_start.year
    for row in ctx.tajika_year_lords:
        row_year = row.get('varsha_year')
        if row_year != year:
            continue
        varshesha = row.get('varshesha') or row.get('varshesha_by_tajik_classical')
        muntha = row.get('muntha')
        if varshesha == domain_lord:
            return 1.0
        if muntha == domain_lord:
            return 0.5
    return 0.0


# ── I-16: convergence_score ───────────────────────────────────────────────────

def convergence_score(
    necessary_conditions: list[float],
    supporting_scores: dict[str, float],
) -> float:
    """
    RATIFIED I-16: score = Π(necessary) × saturating_sum(supporting)

    necessary: list of scores in [0,1]; multiplicative veto — if any ≈ 0 the
               product collapses to ≈ 0.
               Includes vedha_factor (C11) when vedha applies.
    supporting: dict keyed by SUPPORTING_WEIGHTS keys, values in [0,1];
                saturating combination = 1 - Π(1 - w_i * s_i).

    Result clamped to [0, 1].
    """
    # Clamp inputs
    nec = [max(0.0, min(1.0, v)) for v in necessary_conditions]
    sup = {k: max(0.0, min(1.0, v)) for k, v in supporting_scores.items()}

    # Necessary: multiplicative (empty list → 1.0 neutral)
    necessary_product = 1.0
    for v in nec:
        necessary_product *= v

    # Supporting: saturating sum 1 - Π(1 - w_i * s_i)
    sat_product = 1.0
    for key, weight in SUPPORTING_WEIGHTS.items():
        s_i = sup.get(key, 0.0)
        sat_product *= (1.0 - weight * s_i)
    supporting_sat = 1.0 - sat_product

    result = necessary_product * supporting_sat
    return max(0.0, min(1.0, result))


# ── I-17: orb_strength_score ─────────────────────────────────────────────────

def orb_strength_score(
    orb_deg: float,
    max_orb_deg: float,
    applying_separating: str,
) -> float:
    """
    RATIFIED I-17: cos²((orb/max_orb) × π/2)

    Full (1.0) at exact (0°), 0 at max_orb boundary.
    applying  × 1.0 (no penalty)
    separating × 0.7

    Result clamped to [0, 1].
    """
    if max_orb_deg <= 0.0:
        return 1.0

    orb_clamped = max(0.0, min(max_orb_deg, orb_deg))
    ratio = orb_clamped / max_orb_deg
    base = math.cos(ratio * math.pi / 2.0) ** 2

    multiplier = 1.0 if applying_separating == 'applying' else 0.7
    result = base * multiplier
    return max(0.0, min(1.0, result))


# ── I-21: confidence_label ────────────────────────────────────────────────────

def confidence_label(score: float) -> str:
    """
    RATIFIED I-21:
      >= 0.75 → 'high'
      >= 0.45 → 'moderate'
      else    → 'speculative'
    """
    if score >= 0.75:
        return 'high'
    if score >= 0.45:
        return 'moderate'
    return 'speculative'


# ── JL-014 (BA Phase 2.5 J5): relative_confidence_labels ─────────────────────
#
# I-21's absolute thresholds (0.75/0.45) were ratified against an assumed
# convergence_score scale that this chart's actual scores never reach (observed
# range ~0.04-0.16 for the native chart) — every row collapses to 'speculative'
# under confidence_label(), a degenerate/non-discriminating tier. Per JL-014,
# recalibrating I-21's absolute thresholds or ka_sangam's constituent-factor
# weights is explicitly DEFERRED to P5A (needs a multi-chart side-by-side
# review, not a one-chart fix). This is an INTERIM, purely additive tier
# computed on a within-chart percentile basis — it does not touch or replace
# confidence_label()/I-21.

def relative_confidence_labels(scores: list[float]) -> list[str]:
    """
    Within-chart percentile tier — NOT calibrated against any absolute scale.
    Top 20% of this batch's scores -> 'high'; next 30% -> 'moderate'; rest ->
    'speculative'. Ties share the same label (rank by score, not position).
    An empty or single-element/all-equal batch cannot be discriminated by
    percentile — everything gets 'moderate' (neutral, not a guess at rank).
    """
    n = len(scores)
    if n == 0:
        return []
    if n == 1 or len(set(scores)) == 1:
        return ['moderate'] * n

    sorted_scores = sorted(scores, reverse=True)

    def _percentile_rank(s: float) -> float:
        # Fraction of the batch this score is >= to (1.0 = the top score).
        rank = sum(1 for x in sorted_scores if x <= s)
        return rank / n

    labels = []
    for s in scores:
        pct = _percentile_rank(s)
        if pct >= 0.80:
            labels.append('high')
        elif pct >= 0.50:
            labels.append('moderate')
        else:
            labels.append('speculative')
    return labels


# ── I-22: independent_current_count ──────────────────────────────────────────

def independent_current_count(currents: dict[str, Any]) -> int:
    """
    RATIFIED I-22: discount correlated evidence.

    Coupling rules (original + U3 extensions):
      - dasha + nakshatra_overlay → coupled (count as ~1, not 2)
      - transit + dasha → independent
      - panchanga + transit → moderate coupling (~0.5 instead of 1.0)
      - ashtakavarga coupled to constituent_lord_transit (same transit → ~1, not 2)
      - eclipse + transit_to_transit → independent (sky-level events)
      - school_consensus → independent (cross-method)
      - station_retrograde → independent
      - tajika → independent (different time system)

    currents: dict with boolean/truthy values for factor keys.
    Returns int >= 1 (always at least 1 if any evidence present).
    """
    has_dasha     = bool(currents.get('dasha'))
    has_nak_ovl   = bool(currents.get('nakshatra_overlay'))
    has_transit   = bool(currents.get('transit'))
    has_panchanga = bool(currents.get('panchanga'))
    has_dristi    = bool(currents.get('benefic_dristi'))
    has_cross     = bool(currents.get('cross_dasha_agreement'))
    # U3 new currents
    has_ashtak    = bool(currents.get('ashtakavarga_transit_potency'))
    has_eclipse   = bool(currents.get('eclipse_proximity'))
    has_t2t       = bool(currents.get('transit_to_transit'))
    has_station   = bool(currents.get('station_retrograde'))
    has_tajika    = bool(currents.get('tajika_annual_reinforcement'))
    has_school    = bool(currents.get('school_consensus'))

    count: float = 0.0

    # dasha + nakshatra_overlay are coupled — count together as 1
    if has_dasha and has_nak_ovl:
        count += 1.0
    elif has_dasha:
        count += 1.0
    elif has_nak_ovl:
        count += 1.0

    # transit is independent of dasha
    if has_transit:
        count += 1.0

    # panchanga + transit moderate coupling → add 0.5 instead of 1.0
    if has_panchanga:
        if has_transit:
            count += 0.5
        else:
            count += 1.0

    # benefic dristi and cross-dasha are independent
    if has_dristi:
        count += 1.0
    if has_cross:
        count += 1.0

    # C7 ashtakavarga: coupled to constituent_lord_transit (same transit)
    # Add 0.5 when transit present (same planet), 1.0 if only ashtakavarga
    if has_ashtak:
        if has_transit:
            count += 0.5
        else:
            count += 1.0

    # C8 eclipse: independent (rare sky-level event)
    if has_eclipse:
        count += 1.0

    # C9 transit_to_transit: independent (outer-planet cycle is distinct from natal transit)
    if has_t2t:
        count += 1.0

    # C10 station: independent (temporal intensification)
    if has_station:
        count += 1.0

    # C12 tajika: independent (annual chart from different framework)
    if has_tajika:
        count += 1.0

    # C13 school_consensus: independent (cross-method triangulation)
    if has_school:
        count += 1.0

    any_present = (has_dasha or has_nak_ovl or has_transit or has_panchanga or
                   has_dristi or has_cross or has_ashtak or has_eclipse or
                   has_t2t or has_station or has_tajika or has_school)
    result = max(1, round(count)) if any_present else 1
    return result


# ── CF.L3.4: Planet synodic/sidereal rarity lookup ───────────────────────────

# Approximate sidereal (synodic for inner) orbital periods in years.
# Rarity_years for a given aspect ≈ period / (360 / aspect_deg), clamped to
# the sidereal period for 0° (conjunction) and half-period for 180°.
_PLANET_PERIOD_YR: dict[str, float] = {
    'Sun':     1.00,
    'Moon':    0.08,   # ~1 month
    'Mercury': 0.24,
    'Venus':   0.62,
    'Mars':    1.88,
    'Jupiter': 11.86,
    'Saturn':  29.46,
    'Uranus':  84.01,
    'Neptune': 164.79,
    'Pluto':   247.92,
    'Rahu':    18.61,
    'Ketu':    18.61,
    'TrueNode': 18.61,
    'MeanNode': 18.61,
}

# Inline confidence gate: I-21 moderate floor (orb_strength_score ≥ 0.45 required).
# Applied per-event inside the transit scan loops so sub-threshold events are
# discarded as found and never accumulate in RAM (prevents Moon/Mercury explosion).
HIGH_CONFIDENCE_ORB_THRESHOLD: float = 0.45


def _rarity_years(planet: str, aspect_deg: float) -> float:
    """
    CF.L3.4 fix: compute approximate rarity of a transit event from the
    planet's sidereal period and the aspect degree.

    Approach: for a transit planet with period P years, a given aspect_deg
    recurs roughly every P × |aspect_deg| / 360 years (minimum 1 year for
    fast movers). Conjunctions (0°) and oppositions (180°) use half the
    period so that a Saturn opposition (≈14.7yr) is distinguished from a
    Saturn conjunction (≈29.5yr).
    """
    period = _PLANET_PERIOD_YR.get(planet, 12.0)
    if aspect_deg <= 0.0:
        aspect_deg = 360.0
    # fraction of orbit between recurrences
    fraction = aspect_deg / 360.0
    rarity = period * fraction
    # never report less than 0.5 yr or more than the full sidereal period
    return round(max(0.5, min(rarity, period)), 2)


def _resolve_transit_planet(predicate: dict) -> Optional[str]:
    """
    Per-signature transit planet resolver (design §4.6).
    Returns the graha to scan for this predicate, or None when no sky scan applies.

    DOSHA              → Saturn  (malefic_transit_over_afflicted_point)
    YOGA               → Jupiter (benefic_transit_to_kendra_trikona)
    DIGNITY            → the signal's own graha (graha_activation;
                         writer populates via predicate['graha_name'])
    DISPOSITOR_RELATIONAL → the house lord (lord_transits_other_bhava;
                         writer populates via predicate['dispositor_lord'])
    SUBSYSTEM          → None  (subsystem_trigger: no transit scan)
    """
    sig_class = (predicate.get('signature_class') or '').upper()
    if 'SUBSYSTEM' in sig_class:
        return None
    if 'DOSHA' in sig_class:
        return 'Saturn'
    if 'YOGA' in sig_class:
        return 'Jupiter'
    if 'DIGNITY' in sig_class:
        return predicate.get('graha_name') or None
    if 'DISPOSITOR_RELATIONAL' in sig_class:
        return predicate.get('dispositor_lord') or None
    return None


# ── JD ↔ date helpers ────────────────────────────────────────────────────────

def _jd_to_date(jd: float) -> date:
    """Convert Julian day number to Python date using swisseph."""
    try:
        import swisseph as swe
        y, m, d, _ = swe.revjul(jd)
        return date(int(y), int(m), int(d))
    except Exception:
        # Fallback: rough conversion (J2000 = 2000-01-01 = JD 2451545.0)
        days_from_j2000 = jd - 2451545.0
        from datetime import timedelta
        dt = date(2000, 1, 1) + timedelta(days=int(days_from_j2000))
        return dt


def _date_to_jd(d: date) -> float:
    """Convert Python date to Julian date number."""
    try:
        import swisseph as swe
        return swe.julday(d.year, d.month, d.day, 0.0)
    except Exception:
        # Fallback
        days_from_j2000 = (d - date(2000, 1, 1)).days
        return 2451545.0 + days_from_j2000


# ── Mode A: daśā-prior soft funnel → transit search ──────────────────────────

def mode_a_search(
    predicate: dict,
    horizon_start_jd: float,
    horizon_end_jd: float,
    dasha_kala_service: Any,
    gochara_service: Any,
    muhurta_service: Any,
    chart_id: str,
    janma_nakshatra_idx: int,
    enrichment_context: Optional[EnrichmentContext] = None,
    native_location: Optional[dict] = None,
    moon_sign: Optional[str] = None,
) -> list[dict]:
    """
    Mode A: daśā-eligibility soft prior → transit search INSIDE eligible survivors.

    moon_sign (CR-102, T-6 fix): this chart's natal Moon sign name (e.g.
    "Aquarius"), used to compute the C11 vedha filter's `transit_house` in
    the correct house-FROM-MOON reference frame. Optional only for backward
    compatibility with pre-fix callers/tests — when omitted, the C11 vedha
    check falls back to the OLD (bugged, CR-102) sign-number behavior rather
    than silently producing a wrong-but-confident house number.

    CR-87: janma_nakshatra_idx is REQUIRED (0-based index into
    _NAKSHATRAS_ORDERED) — this chart's own Moon nakshatra, resolved by the
    caller from chart_facts. No native default; never falls back to another
    chart's value.

    1. Ask dasha_kala_service (or predicate) for eligible dasha windows.
    2. For each eligible window, use find_aspect_events from transit_search to
       find transit events matching the predicate's transit_trigger.
    3. Score each hit with convergence_score + orb_strength.
       U3: adds C7–C12 currents; C11 vedha enters the necessary side.
    4. Return ranked windows.

    Returns list of window dicts with fields:
      mode, window_start, window_end, peak_date, convergence_score,
      orb_strength, constituent_factors, source_citation, is_off_dasha_discovery
    """
    from pipeline.transit_search import find_aspect_events

    ctx = enrichment_context or EnrichmentContext.empty()
    windows: list[dict] = []
    moon_sign_idx = _SIGN_NAME_TO_IDX.get(moon_sign) if moon_sign else None

    # Extract predicate fields
    dasha_rule   = predicate.get('dasha_eligibility_rule_jsonb', {}) or {}
    transit_trig = predicate.get('transit_trigger_jsonb', {}) or {}
    sig_class    = predicate.get('signature_class', 'UNKNOWN')
    signal_id    = predicate.get('signal_id')
    dignity_score = float(predicate.get('dignity_score', 0.5))
    ayanamsha_id  = predicate.get('ayanamsha_id') or 'lahiri'
    # Domain lord for C12 (tajika): the primary significator for this signature
    domain_lord   = predicate.get('domain_lord') or (
        list(dasha_rule.get('constituent_lords', []) or [])[:1] or [None]
    )[0]

    # CF.L3.6: real dasha prior — query KaDashaKalaService if provided.
    # Fall back to the static eligibility_score from the predicate JSONB when
    # the service is None (preserves old behavior for tests / dry-run).
    static_dasha_score = float(dasha_rule.get('eligibility_score', 0.5))
    eligible_windows: list[Any] = []  # EligibleWindow list from service
    if dasha_kala_service is not None:
        target_lords = set(dasha_rule.get('constituent_lords', []))
        if target_lords:
            try:
                from datetime import timedelta
                h_start = _jd_to_date(horizon_start_jd)
                h_end   = _jd_to_date(horizon_end_jd)
                result = dasha_kala_service.query(
                    chart_id=chart_id,
                    ayanamsha_id=ayanamsha_id,
                    target_lords=target_lords,
                    related_lords=set(),
                    date_start=h_start,
                    date_end=h_end,
                    max_level=3,
                )
                eligible_windows = result.windows
                logger.debug(
                    "mode_a_search: dasha query returned %d eligible windows for lords=%s",
                    len(eligible_windows), sorted(target_lords),
                )
            except Exception as exc:
                logger.warning("mode_a_search: dasha_kala_service.query failed: %s", exc)

    def _dasha_score_for_date(peak_date: Any) -> float:
        """Return max eligibility_score of any dasha window overlapping peak_date."""
        if not eligible_windows:
            return static_dasha_score
        best = 0.0
        for ew in eligible_windows:
            if ew.start_date <= peak_date <= ew.end_date:
                best = max(best, ew.eligibility_score)
        return best if best > 0.0 else static_dasha_score

    # Transit trigger params — per-signature resolver (§4.6); no hardcoded fallback
    planet = _resolve_transit_planet(predicate)
    if planet is None:
        return windows  # SUBSYSTEM or unresolvable: skip sky scan entirely
    target_lon   = float(transit_trig.get('target_longitude_deg', 0.0))
    aspect_degs  = transit_trig.get('aspect_degrees', [0, 60, 90, 120, 180])
    orb_deg      = float(transit_trig.get('orb_deg', 5.0))

    try:
        import swisseph as swe
        events = find_aspect_events(
            swe=swe,
            transit_planet=planet,
            target_longitude_deg=target_lon,
            aspect_degrees=aspect_degs,
            orb_deg=orb_deg,
            start_jd=horizon_start_jd,
            end_jd=horizon_end_jd,
        )
    except Exception as exc:
        logger.warning("mode_a_search: transit search failed: %s", exc)
        events = []

    for ev in events:
        orb_s = orb_strength_score(
            ev.orb_at_event_deg, orb_deg, ev.applying_separating
        )
        if orb_s < HIGH_CONFIDENCE_ORB_THRESHOLD:
            continue  # discard sub-threshold events as found — never accumulate in RAM
        peak_dt = _jd_to_date(ev.event_jd)

        # CF.L3.6: real per-event dasha score
        dasha_score = _dasha_score_for_date(peak_dt)

        # CF.L3.4: real rarity from planet period + aspect
        aspect_used = float(ev.extra.get('aspect_deg', 0))
        rarity = _rarity_years(planet, aspect_used)

        # ── U3 C7–C12 current values ────────────────────────────────────────
        # Window JD bounds for gochara calls
        try:
            from datetime import timedelta as _td
            ws = peak_dt - _td(days=15)
            we = peak_dt + _td(days=15)
            w_jd_start = _date_to_jd(ws)
            w_jd_end   = _date_to_jd(we)
        except Exception:
            ws = we = peak_dt
            w_jd_start = w_jd_end = _date_to_jd(peak_dt)

        transit_sign = int(ev.exact_longitude_deg // 30) + 1 if hasattr(ev, 'exact_longitude_deg') else None

        c7  = _c7_ashtakavarga_potency(planet, transit_sign, ctx)
        c8  = _c8_eclipse_score(planet, w_jd_start, w_jd_end, gochara_service, target_lon, orb_deg)
        c9  = _c9_transit_to_transit_score(planet, w_jd_start, w_jd_end, gochara_service)
        c10 = _c10_station_score(planet, w_jd_start, w_jd_end, gochara_service)
        # C11 vedha: NECESSARY side, not supporting.
        # CR-102 fix: transit_house must be house-FROM-MOON, not the raw rasi
        # sign number (see _house_from_moon docstring). Falls back to the old
        # (bugged) sign-number behavior only when moon_sign wasn't supplied.
        transit_house = _house_from_moon(transit_sign, moon_sign_idx)
        if transit_house is None:
            transit_house = transit_sign
        vedha_factor  = _c11_vedha_factor(planet, transit_house, ctx)
        c12 = _c12_tajika_score(ws, domain_lord, ctx)
        c13 = _c13_school_consensus_score(sig_class, ctx)

        # ── Newly wired currents (formerly 0.0) ──────────────────────────────
        c_cross   = _c_cross_dasha_agreement(peak_dt, eligible_windows)
        c_dristi  = _c_benefic_dristi(target_lon, w_jd_start, w_jd_end, gochara_service)
        c_pancha  = _c_panchanga_quality(peak_dt, muhurta_service, native_location)
        c_tara    = _c_tara_bala_for_jd(ev.event_jd, janma_nakshatra_idx)
        c_nak     = _c_nakshatra_subsystem(ev.nakshatra, janma_nakshatra_idx)

        # Necessary conditions: dignity × orb × vedha_factor (1.0 = no vedha)
        necessary = [dignity_score, orb_s, vedha_factor]
        supporting = {
            'constituent_lord_transit':    float(dasha_score),
            'ashtakavarga_transit_potency': c7,
            'cross_dasha_agreement':        c_cross,
            'benefic_dristi':               c_dristi,
            'transit_to_transit':           c9,
            'panchanga_quality':            c_pancha,
            'tara_bala':                    c_tara,
            'eclipse_proximity':            c8,
            'nakshatra_subsystem':          c_nak,
            'station_retrograde':           c10,
            'tajika_annual_reinforcement':  c12,
            'school_consensus':             c13,
        }
        cscore = convergence_score(necessary, supporting)

        windows.append({
            'mode': 'A',
            'window_start': ws,
            'window_end': we,
            'peak_date': peak_dt,
            'convergence_score': round(cscore, 4),
            'orb_strength': round(orb_s, 4),
            'rarity_years': rarity,
            'constituent_factors': {
                'planet': planet,
                'aspect_deg': aspect_used,
                'sign': ev.sign,
                'nakshatra': ev.nakshatra,
                'applying_separating': ev.applying_separating,
                'dasha_score': dasha_score,
                'dignity_score': dignity_score,
                'signature_class': sig_class,
                # U3 per-current breakdown (§3.5 — explainability)
                'c7_ashtakavarga_potency': round(c7, 4),
                'c8_eclipse_proximity': round(c8, 4),
                'c9_transit_to_transit': round(c9, 4),
                'c10_station_retrograde': round(c10, 4),
                'c11_vedha_factor': round(vedha_factor, 4),
                'c12_tajika_reinforcement': round(c12, 4),
                'c13_school_consensus': round(c13, 4),
                # Newly wired currents
                'c_cross_dasha_agreement': round(c_cross, 4),
                'c_benefic_dristi': round(c_dristi, 4),
                'c_panchanga_quality': round(c_pancha, 4),
                'c_tara_bala': round(c_tara, 4),
                'c_nakshatra_subsystem': round(c_nak, 4),
            },
            'source_citation': (
                f"mode_a/{sig_class}/{planet}@{ev.exact_longitude_deg:.1f}°"
                f"/{ev.event_datetime_ist[:10]}"
            ),
            'is_off_dasha_discovery': False,
            'signal_id': signal_id,
        })

    # Sort by convergence_score desc
    windows.sort(key=lambda w: w['convergence_score'], reverse=True)
    return windows


# ── Mode B: un-gated anomaly sweep ───────────────────────────────────────────

def mode_b_sweep(
    signal_id: Any,
    predicate: dict,
    horizon_start_jd: float,
    horizon_end_jd: float,
    gochara_service: Any,
    janma_nakshatra_idx: int,
    magnitude_threshold: float = 0.6,
    enrichment_context: Optional[EnrichmentContext] = None,
    muhurta_service: Any = None,
    native_location: Optional[dict] = None,
    moon_sign: Optional[str] = None,
) -> list[dict]:
    """
    Mode B: un-gated long-horizon anomaly sweep.

    moon_sign (CR-102, T-6 fix): see mode_a_search's docstring — same
    house-from-Moon reference-frame fix for the C11 vedha filter.

    Sweeps the full horizon for transit events matching the predicate's
    transit_trigger, WITHOUT filtering by dasha eligibility. Any window whose
    orb_strength × dignity_score >= magnitude_threshold is returned as an
    off-daśā discovery.

    CR-87: janma_nakshatra_idx is REQUIRED (0-based index into
    _NAKSHATRAS_ORDERED) — this chart's own Moon nakshatra, resolved by the
    caller from chart_facts. No native default; never falls back to another
    chart's value.

    Returns windows with is_off_dasha_discovery=True and mode='B'.
    """
    from pipeline.transit_search import search_long_horizon

    ctx = enrichment_context or EnrichmentContext.empty()
    windows: list[dict] = []
    moon_sign_idx = _SIGN_NAME_TO_IDX.get(moon_sign) if moon_sign else None

    transit_trig  = predicate.get('transit_trigger_jsonb', {}) or {}
    sig_class     = predicate.get('signature_class', 'UNKNOWN')
    dignity_score = float(predicate.get('dignity_score', 0.5))
    domain_lord   = predicate.get('domain_lord') or None

    planet = _resolve_transit_planet(predicate)
    if planet is None:
        return windows  # SUBSYSTEM or unresolvable: skip sky scan entirely
    target_lon   = float(transit_trig.get('target_longitude_deg', 0.0))
    aspect_degs  = transit_trig.get('aspect_degrees', [0, 60, 90, 120, 180])
    orb_deg      = float(transit_trig.get('orb_deg', 5.0))

    try:
        import swisseph as swe
        events = search_long_horizon(
            swe=swe,
            transit_planet=planet,
            target_longitude_deg=target_lon,
            aspect_degrees=aspect_degs,
            orb_deg=orb_deg,
            start_jd=horizon_start_jd,
            end_jd=horizon_end_jd,
        )
    except Exception as exc:
        logger.warning("mode_b_sweep: transit search failed: %s", exc)
        events = []

    for ev in events:
        orb_s = orb_strength_score(
            ev.orb_at_event_deg, orb_deg, ev.applying_separating
        )
        if orb_s < HIGH_CONFIDENCE_ORB_THRESHOLD:
            continue  # discard sub-threshold events as found — never accumulate in RAM
        magnitude = dignity_score * orb_s
        if magnitude < magnitude_threshold:
            continue

        peak_dt = _jd_to_date(ev.event_jd)
        aspect_used = float(ev.extra.get('aspect_deg', 0))
        rarity = _rarity_years(planet, aspect_used)

        try:
            from datetime import timedelta as _td
            ws = peak_dt - _td(days=15)
            we = peak_dt + _td(days=15)
            w_jd_start = _date_to_jd(ws)
            w_jd_end   = _date_to_jd(we)
        except Exception:
            ws = we = peak_dt
            w_jd_start = w_jd_end = _date_to_jd(peak_dt)

        transit_sign = int(ev.exact_longitude_deg // 30) + 1 if hasattr(ev, 'exact_longitude_deg') else None

        c7  = _c7_ashtakavarga_potency(planet, transit_sign, ctx)
        c8  = _c8_eclipse_score(planet, w_jd_start, w_jd_end, gochara_service, target_lon, orb_deg)
        c9  = _c9_transit_to_transit_score(planet, w_jd_start, w_jd_end, gochara_service)
        c10 = _c10_station_score(planet, w_jd_start, w_jd_end, gochara_service)
        # CR-102 fix (see mode_a_search's identical fix + _house_from_moon docstring).
        transit_house = _house_from_moon(transit_sign, moon_sign_idx)
        if transit_house is None:
            transit_house = transit_sign
        vedha_factor = _c11_vedha_factor(planet, transit_house, ctx)
        c12 = _c12_tajika_score(ws, domain_lord, ctx)
        c13 = _c13_school_consensus_score(sig_class, ctx)

        # Newly wired currents (mode B: cross_dasha = 0.0 — no dasha prior in un-gated sweep)
        c_dristi = _c_benefic_dristi(target_lon, w_jd_start, w_jd_end, gochara_service)
        c_pancha = _c_panchanga_quality(peak_dt, muhurta_service, native_location)
        c_tara   = _c_tara_bala_for_jd(ev.event_jd, janma_nakshatra_idx)
        c_nak    = _c_nakshatra_subsystem(ev.nakshatra, janma_nakshatra_idx)

        necessary = [dignity_score, orb_s, vedha_factor]
        supporting = {
            'constituent_lord_transit':    0.0,   # mode B has no dasha prior
            'ashtakavarga_transit_potency': c7,
            'cross_dasha_agreement':        0.0,  # no dasha context in mode B
            'benefic_dristi':               c_dristi,
            'transit_to_transit':           c9,
            'panchanga_quality':            c_pancha,
            'tara_bala':                    c_tara,
            'eclipse_proximity':            c8,
            'nakshatra_subsystem':          c_nak,
            'station_retrograde':           c10,
            'tajika_annual_reinforcement':  c12,
            'school_consensus':             c13,
        }
        cscore = convergence_score(necessary, supporting)

        windows.append({
            'mode': 'B',
            'window_start': ws,
            'window_end': we,
            'peak_date': peak_dt,
            'convergence_score': round(cscore, 4),
            'orb_strength': round(orb_s, 4),
            'rarity_years': rarity,
            'constituent_factors': {
                'planet': planet,
                'aspect_deg': aspect_used,
                'sign': ev.sign,
                'nakshatra': ev.nakshatra,
                'applying_separating': ev.applying_separating,
                'dignity_score': dignity_score,
                'magnitude': round(magnitude, 4),
                'signature_class': sig_class,
                'c7_ashtakavarga_potency': round(c7, 4),
                'c8_eclipse_proximity': round(c8, 4),
                'c9_transit_to_transit': round(c9, 4),
                'c10_station_retrograde': round(c10, 4),
                'c11_vedha_factor': round(vedha_factor, 4),
                'c12_tajika_reinforcement': round(c12, 4),
                'c13_school_consensus': round(c13, 4),
                'c_benefic_dristi': round(c_dristi, 4),
                'c_panchanga_quality': round(c_pancha, 4),
                'c_tara_bala': round(c_tara, 4),
                'c_nakshatra_subsystem': round(c_nak, 4),
            },
            'source_citation': (
                f"mode_b/{sig_class}/{planet}@{ev.exact_longitude_deg:.1f}°"
                f"/{ev.event_datetime_ist[:10]}"
            ),
            'is_off_dasha_discovery': True,
            'signal_id': signal_id,
        })

    windows.sort(key=lambda w: w['convergence_score'], reverse=True)
    return windows


# ── Mode C: SUBSYSTEM period-based activation ─────────────────────────────────

# CR-87 fix: _SADE_SATI_SIGNS / _SADE_SATI_SEVERITY (formerly hardcoded to
# Capricorn/Aquarius/Pisces for chart 482012f1's Aquarius Moon) DELETED — not
# defaulted. mode_c_subsystem_period() now REQUIRES moon_sign and derives the
# trigger signs + severity map per-chart via derive_sade_sati_signs() /
# derive_sade_sati_severity() above.

# Medical/āyur: malefic (Saturn or Mars) transiting the 6th/8th from Aries lagna
# NOTE (CR-87 scope note): _AYUR_SIGNS_* and _VASTU_SIGNS below are ALSO
# hardcoded lagna-relative constants (Aries lagna) and share the same bug
# class, but deriving them per-chart is explicitly OUT OF SCOPE for this hotfix
# (LANE0_CR87_HOTFIX.md §2.1: "Janma-nakshatra, sade-sati, and location are the
# mandatory three"). Filed as a residual — not fixed in this lane.
_AYUR_SIGNS_SATURN = ('Virgo', 'Scorpio')          # 6th and 8th from Aries
_AYUR_SIGNS_MARS   = ('Virgo', 'Scorpio', 'Libra') # 6th, 8th, 7th for Mars

# Vāstu directional: Sun in dusthāna signs or Saturn in lagna
_VASTU_SIGNS = ('Virgo', 'Scorpio', 'Pisces')  # 6th, 8th, 12th from lagna


def mode_c_subsystem_period(
    predicate: dict,
    horizon_start_jd: float,
    horizon_end_jd: float,
    gochara_service: Any,
    moon_sign: str,
    enrichment_context: Optional[EnrichmentContext] = None,
) -> list[dict]:
    """
    Mode C: SUBSYSTEM period-based activation (§T7 template).

    Finds when the relevant planetary condition (e.g. Saturn entering sade-sati
    signs, Mars entering āyur-stress signs) is active over the horizon.
    Returns one window per ingress, spanning the sign-transit period.

    SUBSYSTEM predicates have no point-based transit_trigger — they activate on
    sign-level transit periods rather than longitude-to-longitude aspects.
    is_off_dasha_discovery = False (subsystem periods are dasha-independent by design).

    CR-87: moon_sign is REQUIRED — this chart's own natal Moon sign, resolved
    by the caller from chart_facts. Sade-sati trigger signs + severity are
    derived from it per-chart; no default, no fallback to Aquarius.
    """
    ctx = enrichment_context or EnrichmentContext.empty()
    transit_trig = predicate.get('transit_trigger_jsonb', {}) or {}
    sig_class     = predicate.get('signature_class', 'UNKNOWN')
    dignity_score = float(predicate.get('dignity_score', 0.5))
    signal_id     = predicate.get('signal_id')
    subsystem     = (transit_trig.get('subsystem') or sig_class).lower()

    if gochara_service is None:
        return []

    sade_sati_signs    = derive_sade_sati_signs(moon_sign)
    sade_sati_severity = derive_sade_sati_severity(sade_sati_signs)

    # Determine trigger planet + target signs + per-sign severity
    if any(kw in subsystem for kw in ('sade', 'sati', 'saturn', 'dosha', 'yoga')):
        trigger_planet = 'Saturn'
        trigger_signs  = sade_sati_signs
        severity_map   = sade_sati_severity
    elif any(kw in subsystem for kw in ('medical', 'ayur', 'health', 'mars')):
        trigger_planet = 'Mars'
        trigger_signs  = _AYUR_SIGNS_MARS
        severity_map   = {s: 0.85 for s in _AYUR_SIGNS_MARS}
    else:
        # Generic subsystem: Saturn in major dusthāna signs
        trigger_planet = 'Saturn'
        trigger_signs  = sade_sati_signs
        severity_map   = sade_sati_severity

    # Approx sign-transit duration (sidereal period / 12 signs)
    period_days = _PLANET_PERIOD_YR.get(trigger_planet, 1.0) * 365.25 / 12.0

    windows: list[dict] = []
    for sign in trigger_signs:
        try:
            ingresses = gochara_service.find_ingresses(
                planet=trigger_planet,
                target_sign=sign,
                start_jd=horizon_start_jd,
                end_jd=horizon_end_jd,
            )
            for ingress_ev in ingresses:
                ws = _jd_to_date(ingress_ev.event_jd)
                we = _jd_to_date(ingress_ev.event_jd + period_days)
                severity = severity_map.get(sign, 0.70)
                cscore   = round(dignity_score * severity, 4)
                windows.append({
                    'mode': 'C',
                    'window_start': ws,
                    'window_end':   we,
                    'peak_date':    ws,
                    'convergence_score': cscore,
                    'orb_strength': 1.0,
                    'rarity_years': _rarity_years(trigger_planet, 30.0),
                    'constituent_factors': {
                        'planet': trigger_planet,
                        'sign': sign,
                        'subsystem': subsystem,
                        'dignity_score': dignity_score,
                        'severity_score': severity,
                        'signature_class': sig_class,
                        'mode': 'C',
                    },
                    'source_citation': (
                        f"mode_c/{sig_class}/{trigger_planet}@{sign}/{ws}"
                    ),
                    'is_off_dasha_discovery': False,
                    'signal_id': signal_id,
                })
        except Exception as exc:
            logger.debug("mode_c_subsystem: %s/%s/%s failed: %s", subsystem, trigger_planet, sign, exc)

    windows.sort(key=lambda w: w['convergence_score'], reverse=True)
    return windows


# ── Mode D: Sarva-Ashtakavarga bindhu convergence sub-mode ───────────────────

# Classical threshold: transit through a sign with SAV ≥ 28 bindhu = strong
# activation window (Phaladeepika Ch.26; BPHS Ch.66 Gochara-Ashtakavarga).
# SAV per sign ranges 0-56 (7 classical planets × 8 bindus each); 28 = midpoint.
_SAV_STRONG_THRESHOLD: int = 28

# Sign names indexed 1–12 (Aries … Pisces)
_SIGN_NAMES: dict[int, str] = {
    1: 'Aries', 2: 'Taurus', 3: 'Gemini', 4: 'Cancer',
    5: 'Leo', 6: 'Virgo', 7: 'Libra', 8: 'Scorpio',
    9: 'Sagittarius', 10: 'Capricorn', 11: 'Aquarius', 12: 'Pisces',
}

# Planets to scan for AV-bindhu activation windows (slow-moving have more timing weight)
_AV_SCAN_PLANETS: tuple[str, ...] = ('Jupiter', 'Saturn', 'Mars')


def mode_d_av_bindhu(
    predicate: dict,
    horizon_start_jd: float,
    horizon_end_jd: float,
    gochara_service: Any,
    enrichment_context: Optional[EnrichmentContext] = None,
    sav_threshold: int = _SAV_STRONG_THRESHOLD,
) -> list[dict]:
    """
    Mode D: Sarva-Ashtakavarga (SAV) bindhu convergence sub-mode.

    Classical basis: Phaladeepika Ch.26 + BPHS Ch.66.  A planet transiting a
    sign with SAV ≥ threshold bindhu (default 28) is a strong activation window.
    Only Jupiter, Saturn, and Mars are scanned — fast planets (Sun/Moon/Mercury/
    Venus) produce too many events to be meaningful timing discriminants.

    Algorithm:
      1. Read SAV per sign from EnrichmentContext.ashtakavarga_bindu['SARVA'].
      2. For each sign with SAV ≥ threshold, find planet ingresses (via
         gochara_service.find_ingresses) in the horizon for each scan planet.
      3. Emit one window per ingress, spanning the planet's sign-transit duration.
      4. Convergence score = (sav / 56.0) × dignity_score.  Orb_strength = 1.0
         (sign-level: no angular orb — the window is the full sign transit).

    Returns windows with mode='D' and is_off_dasha_discovery=False.
    Requires gochara_service; returns [] if unavailable.
    """
    if gochara_service is None:
        return []
    ctx = enrichment_context or EnrichmentContext.empty()

    # SARVA bindhu map: {sign_number: sav_count}
    sarva_map: dict[int, int] = ctx.ashtakavarga_bindu.get('SARVA', {})
    if not sarva_map:
        logger.debug("mode_d_av_bindhu: no SARVA data in EnrichmentContext — skipping")
        return []

    sig_class     = predicate.get('signature_class', 'UNKNOWN')
    dignity_score = float(predicate.get('dignity_score', 0.5))
    signal_id     = predicate.get('signal_id')

    # Strong signs: SAV >= threshold
    strong_signs: list[tuple[int, int]] = [
        (sign_num, sav)
        for sign_num, sav in sarva_map.items()
        if sav >= sav_threshold
    ]
    if not strong_signs:
        logger.debug("mode_d_av_bindhu: no signs meet SAV >= %d threshold", sav_threshold)
        return []

    windows: list[dict] = []
    for planet in _AV_SCAN_PLANETS:
        period_days = _PLANET_PERIOD_YR.get(planet, 12.0) * 365.25 / 12.0
        for sign_num, sav in strong_signs:
            sign_name = _SIGN_NAMES.get(sign_num, f'Sign{sign_num}')
            try:
                ingresses = gochara_service.find_ingresses(
                    planet=planet,
                    target_sign=sign_name,
                    start_jd=horizon_start_jd,
                    end_jd=horizon_end_jd,
                )
            except Exception as exc:
                logger.debug("mode_d_av_bindhu: find_ingresses(%s, %s) failed: %s",
                             planet, sign_name, exc)
                ingresses = []

            for ingress_ev in ingresses:
                ws = _jd_to_date(ingress_ev.event_jd)
                we = _jd_to_date(ingress_ev.event_jd + period_days)
                # Score: SAV fraction × dignity  (SAV max = 56 for 7 classical planets)
                sav_score  = min(1.0, sav / 56.0)
                cscore     = round(dignity_score * sav_score, 4)
                rarity     = _rarity_years(planet, 30.0)   # sign-ingress ≈ 30° transit

                windows.append({
                    'mode': 'D',
                    'window_start': ws,
                    'window_end':   we,
                    'peak_date':    ws,
                    'convergence_score': cscore,
                    'orb_strength': 1.0,   # sign-level: no angular orb
                    'rarity_years': rarity,
                    'constituent_factors': {
                        'planet': planet,
                        'sign': sign_name,
                        'sign_num': sign_num,
                        'sav_bindhu': sav,
                        'sav_threshold': sav_threshold,
                        'sav_score': round(sav_score, 4),
                        'dignity_score': dignity_score,
                        'signature_class': sig_class,
                        'mode': 'D',
                    },
                    'source_citation': (
                        f"mode_d/av_bindhu/{planet}@{sign_name}/SAV={sav}/{ws}"
                    ),
                    'is_off_dasha_discovery': False,
                    'signal_id': signal_id,
                })

    windows.sort(key=lambda w: w['convergence_score'], reverse=True)
    return windows


__all__ = [
    'SUPPORTING_WEIGHTS',
    'HIGH_CONFIDENCE_ORB_THRESHOLD',
    'EnrichmentContext',
    'convergence_score',
    'orb_strength_score',
    'confidence_label',
    'independent_current_count',
    'mode_a_search',
    'mode_b_sweep',
    'mode_c_subsystem_period',
    'mode_d_av_bindhu',
    '_jd_to_date',
    '_date_to_jd',
    '_rarity_years',
    '_PLANET_PERIOD_YR',
    '_resolve_transit_planet',
    '_SAV_STRONG_THRESHOLD',
    '_AV_SCAN_PLANETS',
    '_SIGN_NAMES',
]
