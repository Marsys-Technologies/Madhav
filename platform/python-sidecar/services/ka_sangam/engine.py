"""
services.ka_sangam.engine — Convergence scoring engine (L3 K4-a).

Implements ratified invariants:
  I-16: convergence_score — multiplicative necessary × saturating supporting
  I-17: orb_strength_score — cos² decay
  I-21: confidence_label — threshold classifier
  I-22: independent_current_count — correlation-discounted evidence counter

Also provides Mode A (daśā-prior soft funnel + transit search) and
Mode B (un-gated long-horizon anomaly sweep, flagged is_off_dasha_discovery=True).

U3 enrichment (2026-06-22): 6 new supporting currents (C7–C12) added; C13 school_consensus
  reserved (weight slot 0.10) pending U4. Weights re-normalized to 1.0 without C13.
  vedha_cancellation (C11) enters the NECESSARY side multiplicatively — not supporting.
  EnrichmentContext carries pre-fetched DB data (ashtakavarga, vedha, tajika) from the writer.

NEVER calls conn.commit() or conn.rollback() — caller owns the transaction.
NEVER writes to any bodha_* table.
"""
from __future__ import annotations

import logging
import math
from datetime import date
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Ratified supporting-factor weights (I-16, sum = 1.0) ──────────────────────
# U3 pass-1: 11 currents (C13 school_consensus reserved weight = 0.10 pending U4;
#   remaining 11 re-normalized to 1.0). Tuning bounds from U3 spec §3.1 satisfied.
# C11 vedha_cancellation is NOT here — it enters the NECESSARY side multiplicatively.

SUPPORTING_WEIGHTS: dict[str, float] = {
    'constituent_lord_transit':    0.200,   # was 0.30; re-normed without C13
    'ashtakavarga_transit_potency': 0.133,  # C7 NEW: "does the transit deliver?"
    'cross_dasha_agreement':        0.133,  # was 0.18 (U1 surfaced; U3 re-normed)
    'benefic_dristi':               0.111,  # was 0.20
    'transit_to_transit':           0.089,  # C9 NEW: outer-planet cycles
    'panchanga_quality':            0.078,  # was 0.12
    'tara_bala':                    0.067,  # was 0.12
    'eclipse_proximity':            0.067,  # C8 NEW: eclipse on sensitive point
    'nakshatra_subsystem':          0.056,  # was 0.08
    'station_retrograde':           0.033,  # C10 NEW: planet stationing on trigger
    'tajika_annual_reinforcement':  0.033,  # C12 NEW: annual chart varṣeśa/muntha
    # C13 school_consensus: weight 0.10 reserved; activates in U3 pass-2 (post-U4)
}

# Verify sum ≈ 1.0 at import (hard-fail if someone edits weights carelessly)
_SW_SUM = round(sum(SUPPORTING_WEIGHTS.values()), 6)
assert abs(_SW_SUM - 1.0) < 1e-4, f"SUPPORTING_WEIGHTS must sum to 1.0, got {_SW_SUM}"


# ── EnrichmentContext (U3) ────────────────────────────────────────────────────

class EnrichmentContext:
    """
    Pre-fetched DB data needed by the new U3 currents (C7, C11, C12).
    Passed in by the ka_sangam writer to avoid passing db_conn into engine.py.

    ashtakavarga_bindu: {planet_name: {sign_number (1-12): bindu_count (0-8)}}
        Sourced from chart_facts (sarvashtakavarga) via ga_strength writer.
        Classical threshold: ≥ 5 bindus = strong; ≤ 3 = weak.
    vedha_rules: list of dicts with keys {planet, transit_to_house, vedha_house}
        Sourced from bg_transit_rules WHERE rule_type='vedha'.
    tajika_year_lords: list of dicts with keys {varsha_year, varshesha, muntha}
        Sourced from l1_tajik_varsha_year_lords for the current chart.
    """

    def __init__(
        self,
        ashtakavarga_bindu: Optional[dict[str, dict[int, int]]] = None,
        vedha_rules: Optional[list[dict]] = None,
        tajika_year_lords: Optional[list[dict]] = None,
    ):
        self.ashtakavarga_bindu = ashtakavarga_bindu or {}
        self.vedha_rules = vedha_rules or []
        self.tajika_year_lords = tajika_year_lords or []

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
    """
    if not ctx.vedha_rules or transit_house is None:
        return 1.0  # no data → no vedha → neutral (1.0)
    for rule in ctx.vedha_rules:
        rule_planet = rule.get('graha') or rule.get('planet')
        to_house = rule.get('transit_to_house') or rule.get('to_house')
        vedha_h = rule.get('vedha_house')
        if rule_planet == planet and to_house == transit_house and vedha_h:
            return 0.3  # vedha present → strongly damp
    return 1.0


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
    enrichment_context: Optional[EnrichmentContext] = None,
) -> list[dict]:
    """
    Mode A: daśā-eligibility soft prior → transit search INSIDE eligible survivors.

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

    # Transit trigger params
    planet       = transit_trig.get('planet', 'Jupiter')
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
        # C11 vedha: NECESSARY side, not supporting
        transit_house = transit_sign  # house ≈ sign for transits in this model
        vedha_factor  = _c11_vedha_factor(planet, transit_house, ctx)
        c12 = _c12_tajika_score(ws, domain_lord, ctx)

        # Necessary conditions: dignity × orb × vedha_factor (1.0 = no vedha)
        necessary = [dignity_score, orb_s, vedha_factor]
        supporting = {
            'constituent_lord_transit':    float(dasha_score),
            'ashtakavarga_transit_potency': c7,
            'cross_dasha_agreement':        0.0,   # wire later from U1 at ph_nimitta level
            'benefic_dristi':               0.0,
            'transit_to_transit':           c9,
            'panchanga_quality':            0.0,
            'tara_bala':                    0.0,
            'eclipse_proximity':            c8,
            'nakshatra_subsystem':          0.0,
            'station_retrograde':           c10,
            'tajika_annual_reinforcement':  c12,
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
    magnitude_threshold: float = 0.6,
    enrichment_context: Optional[EnrichmentContext] = None,
) -> list[dict]:
    """
    Mode B: un-gated long-horizon anomaly sweep.

    Sweeps the full horizon for transit events matching the predicate's
    transit_trigger, WITHOUT filtering by dasha eligibility. Any window whose
    orb_strength × dignity_score >= magnitude_threshold is returned as an
    off-daśā discovery.

    Returns windows with is_off_dasha_discovery=True and mode='B'.
    """
    from pipeline.transit_search import search_long_horizon

    ctx = enrichment_context or EnrichmentContext.empty()
    windows: list[dict] = []

    transit_trig  = predicate.get('transit_trigger_jsonb', {}) or {}
    sig_class     = predicate.get('signature_class', 'UNKNOWN')
    dignity_score = float(predicate.get('dignity_score', 0.5))
    domain_lord   = predicate.get('domain_lord') or None

    planet       = transit_trig.get('planet', 'Jupiter')
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
        vedha_factor = _c11_vedha_factor(planet, transit_sign, ctx)
        c12 = _c12_tajika_score(ws, domain_lord, ctx)

        necessary = [dignity_score, orb_s, vedha_factor]
        supporting = {
            'constituent_lord_transit':    0.0,   # mode B has no dasha prior
            'ashtakavarga_transit_potency': c7,
            'cross_dasha_agreement':        0.0,
            'benefic_dristi':               0.0,
            'transit_to_transit':           c9,
            'panchanga_quality':            0.0,
            'tara_bala':                    0.0,
            'eclipse_proximity':            c8,
            'nakshatra_subsystem':          0.0,
            'station_retrograde':           c10,
            'tajika_annual_reinforcement':  c12,
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


__all__ = [
    'SUPPORTING_WEIGHTS',
    'EnrichmentContext',
    'convergence_score',
    'orb_strength_score',
    'confidence_label',
    'independent_current_count',
    'mode_a_search',
    'mode_b_sweep',
    '_jd_to_date',
    '_date_to_jd',
    '_rarity_years',
    '_PLANET_PERIOD_YR',
]
