"""
services.ka_sangam.engine — Convergence scoring engine (L3 K4-a).

Implements ratified invariants:
  I-16: convergence_score — multiplicative necessary × saturating supporting
  I-17: orb_strength_score — cos² decay
  I-21: confidence_label — threshold classifier
  I-22: independent_current_count — correlation-discounted evidence counter

Also provides Mode A (daśā-prior soft funnel + transit search) and
Mode B (un-gated long-horizon anomaly sweep, flagged is_off_dasha_discovery=True).

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

SUPPORTING_WEIGHTS: dict[str, float] = {
    'constituent_lord_transit': 0.30,
    'benefic_dristi':           0.20,
    'cross_dasha_agreement':    0.18,
    'panchanga_quality':        0.12,
    'tara_bala':                0.12,
    'nakshatra_subsystem':      0.08,
}


# ── I-16: convergence_score ───────────────────────────────────────────────────

def convergence_score(
    necessary_conditions: list[float],
    supporting_scores: dict[str, float],
) -> float:
    """
    RATIFIED I-16: score = Π(necessary) × saturating_sum(supporting)

    necessary: list of scores in [0,1]; multiplicative veto — if any ≈ 0 the
               product collapses to ≈ 0.
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

    Coupling rules:
      - dasha + nakshatra_overlay → coupled (count as ~1, not 2)
      - transit + dasha → independent
      - panchanga + transit → moderate (~1.5, rounds to 2 if other factors present)

    currents: dict with boolean/truthy values for factor keys:
      'dasha', 'nakshatra_overlay', 'transit', 'panchanga', 'benefic_dristi',
      'cross_dasha_agreement', etc.

    Returns int >= 1 (always at least 1 if any evidence present).
    """
    has_dasha     = bool(currents.get('dasha'))
    has_nak_ovl   = bool(currents.get('nakshatra_overlay'))
    has_transit   = bool(currents.get('transit'))
    has_panchanga = bool(currents.get('panchanga'))
    has_dristi    = bool(currents.get('benefic_dristi'))
    has_cross     = bool(currents.get('cross_dasha_agreement'))

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

    result = max(1, round(count)) if (has_dasha or has_nak_ovl or has_transit or
                                       has_panchanga or has_dristi or has_cross) else 1
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
    """Convert Python date to Julian day number."""
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
) -> list[dict]:
    """
    Mode A: daśā-eligibility soft prior → transit search INSIDE eligible survivors.

    1. Ask dasha_kala_service (or predicate) for eligible dasha windows.
    2. For each eligible window, use find_aspect_events from transit_search to
       find transit events matching the predicate's transit_trigger.
    3. Score each hit with convergence_score + orb_strength.
    4. Return ranked windows.

    Returns list of window dicts with fields:
      mode, window_start, window_end, peak_date, convergence_score,
      orb_strength, constituent_factors, source_citation, is_off_dasha_discovery
    """
    from pipeline.transit_search import find_aspect_events

    windows: list[dict] = []

    # Extract predicate fields
    dasha_rule   = predicate.get('dasha_eligibility_rule_jsonb', {}) or {}
    transit_trig = predicate.get('transit_trigger_jsonb', {}) or {}
    sig_class    = predicate.get('signature_class', 'UNKNOWN')
    signal_id    = predicate.get('signal_id')
    dignity_score = float(predicate.get('dignity_score', 0.5))
    ayanamsha_id  = predicate.get('ayanamsha_id') or 'lahiri'

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

        necessary = [dignity_score, orb_s]
        supporting = {
            'constituent_lord_transit': float(dasha_score),
            'benefic_dristi': 0.0,
            'cross_dasha_agreement': 0.0,
            'panchanga_quality': 0.0,
            'tara_bala': 0.0,
            'nakshatra_subsystem': 0.0,
        }
        cscore = convergence_score(necessary, supporting)

        # Window = ±15 days around peak
        try:
            from datetime import timedelta
            ws = peak_dt - timedelta(days=15)
            we = peak_dt + timedelta(days=15)
        except Exception:
            ws = peak_dt
            we = peak_dt

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

    windows: list[dict] = []

    transit_trig  = predicate.get('transit_trigger_jsonb', {}) or {}
    sig_class     = predicate.get('signature_class', 'UNKNOWN')
    dignity_score = float(predicate.get('dignity_score', 0.5))

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

        necessary = [dignity_score, orb_s]
        supporting = {
            'constituent_lord_transit': 0.0,
            'benefic_dristi': 0.0,
            'cross_dasha_agreement': 0.0,
            'panchanga_quality': 0.0,
            'tara_bala': 0.0,
            'nakshatra_subsystem': 0.0,
        }
        cscore = convergence_score(necessary, supporting)

        peak_dt = _jd_to_date(ev.event_jd)
        # CF.L3.4: rarity from orbital period
        aspect_used = float(ev.extra.get('aspect_deg', 0))
        rarity = _rarity_years(planet, aspect_used)

        try:
            from datetime import timedelta
            ws = peak_dt - timedelta(days=15)
            we = peak_dt + timedelta(days=15)
        except Exception:
            ws = peak_dt
            we = peak_dt

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
