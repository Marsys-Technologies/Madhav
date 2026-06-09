"""
rich_topics.py — Rich panchanga topic computations.

Topics: Sun/Moon dynamics, AngaAttributes, Anandadi Yoga, Vasa family,
5-Panchaka, Shoonya, window-membership, micro-timing.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
import swisseph as swe

from .types import (
    SunMoonDynamics, AnandadiYoga, VasaFamily, PanchakaState,
    ShoonyaState, WindowMembership, MicroTiming, AngaAttributes,
)
from .shastra_tables import (
    ANANDADI_YOGA_NAMES, ANANDADI_AUSPICIOUS,
    AGNI_VASA_TABLE, CHANDRA_VASA_TABLE, RAHU_VASA_TABLE,
    DISHA_SHUL_TABLE, NAKSHATRA_VASA_TABLE, BHADRA_VASA_TABLE,
    PANCHAKA_TYPE_TABLE,
    TITHI_SHOONYA_TABLE, NAKSHATRA_SHOONYA_TABLE,
    SIGN_NAMES, NAKSHATRA_LORDS, NAKSHATRA_DEITIES,
)


# ---------------------------------------------------------------------------
# Tithi type + lord tables
# ---------------------------------------------------------------------------

_TITHI_TYPES = {
    **{t: "Nanda"   for t in [1,  6, 11, 16, 21, 26]},
    **{t: "Bhadra"  for t in [2,  7, 12, 17, 22, 27]},
    **{t: "Jaya"    for t in [3,  8, 13, 18, 23, 28]},
    **{t: "Rikta"   for t in [4,  9, 14, 19, 24, 29]},
    **{t: "Poorna"  for t in [5, 10, 15, 20, 25, 30]},
}

_LORD_SEQ = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
_TITHI_LORDS = {i: _LORD_SEQ[(i - 1) % 7] for i in range(1, 31)}


# ---------------------------------------------------------------------------
# Topic 1 extension: Anga attributes
# ---------------------------------------------------------------------------

def compute_tithi_attrs(tithi_id: int, pct_elapsed: Optional[float] = None) -> AngaAttributes:
    """Return lord, deity and tithi-type for a given tithi_id (1..30)."""
    lord  = _TITHI_LORDS.get(tithi_id, "")
    ttype = _TITHI_TYPES.get(tithi_id, "neutral")
    return AngaAttributes(lord=lord, deity="Chandra", anga_type=ttype, pct_elapsed=pct_elapsed)


def compute_nakshatra_attrs(nak_id: int, pct_elapsed: Optional[float] = None) -> AngaAttributes:
    """Return lord, deity and anga_type for a given nakshatra_id (1..27)."""
    lord  = NAKSHATRA_LORDS[nak_id - 1]
    deity = NAKSHATRA_DEITIES[nak_id - 1]
    return AngaAttributes(lord=lord, deity=deity, anga_type="neutral", pct_elapsed=pct_elapsed)


# ---------------------------------------------------------------------------
# Topic 4: Sun/Moon dynamics
# ---------------------------------------------------------------------------

def compute_sun_moon_dynamics(jd: float) -> SunMoonDynamics:
    """
    Compute Moon illumination and Sun-Moon separation at Julian Day jd.

    Uses swe.pheno_ut for Moon phase data (fractional illumination at index 1).
    Falls back to geometric approximation if pheno_ut is unavailable.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    sun_res,  _ = swe.calc_ut(jd, swe.SUN)
    moon_res, _ = swe.calc_ut(jd, swe.MOON)
    separation = (moon_res[0] - sun_res[0]) % 360

    try:
        moon_attrs, _ = swe.pheno_ut(jd, swe.MOON)
        # pheno_ut returns: [phase_angle, illumination_fraction, ...]
        phase_angle = moon_attrs[0]
        illum_frac  = moon_attrs[1]
    except Exception:
        phase_angle = separation
        illum_frac  = (1.0 - abs(180.0 - separation) / 180.0) * 0.5

    return SunMoonDynamics(
        sun_moon_separation_deg=round(separation, 4),
        moon_illumination_pct=round(max(0.0, min(100.0, illum_frac * 100)), 2),
        moon_phase_angle_deg=round(phase_angle, 4),
    )


# ---------------------------------------------------------------------------
# Topic 10: Anandadi Yoga
# ---------------------------------------------------------------------------

def compute_anandadi_yoga(vara_id: int, nakshatra_id: int) -> AnandadiYoga:
    """
    28-yoga series.  Formula: index = (vara_id + nakshatra_id - 2) % 28
    vara_id: 1=Sun, 2=Mon, ..., 7=Sat
    nakshatra_id: 1..27
    """
    idx = (vara_id + nakshatra_id - 2) % 28
    return AnandadiYoga(
        yoga_name=ANANDADI_YOGA_NAMES[idx],
        yoga_number=idx + 1,
        auspicious=(idx + 1) in ANANDADI_AUSPICIOUS,
    )


# ---------------------------------------------------------------------------
# Topic 11: Vasa family
# ---------------------------------------------------------------------------

def compute_vasa_family(tithi_id: int, vara_id: int, nakshatra_id: int) -> VasaFamily:
    """
    Compute all six Vasa attributes from tithi, vara, and nakshatra.
    All lookups use the shastra_tables dictionaries.
    """
    return VasaFamily(
        agni_vasa=AGNI_VASA_TABLE[tithi_id],
        chandra_vasa=CHANDRA_VASA_TABLE.get(tithi_id, "East"),
        rahu_vasa=RAHU_VASA_TABLE[vara_id],
        disha_vasa=DISHA_SHUL_TABLE[vara_id],
        nakshatra_vasa=NAKSHATRA_VASA_TABLE.get(nakshatra_id, "North"),
        bhadra_vasa=BHADRA_VASA_TABLE.get(tithi_id, "Madhya"),
    )


# ---------------------------------------------------------------------------
# Topic 12: 5-Panchaka
# ---------------------------------------------------------------------------

def compute_panchaka(nakshatra_id: int) -> PanchakaState:
    """
    Panchaka active when nakshatra is one of the five Panchaka nakshatras
    (23 Dhanistha through 27 Revati per PANCHAKA_TYPE_TABLE).
    """
    if nakshatra_id in PANCHAKA_TYPE_TABLE:
        return PanchakaState(active=True, panchaka_type=PANCHAKA_TYPE_TABLE[nakshatra_id])
    return PanchakaState(active=False, panchaka_type=None)


# ---------------------------------------------------------------------------
# Topic 15: Shoonya
# ---------------------------------------------------------------------------

def compute_shoonya(tithi_id: int, nakshatra_id: int) -> ShoonyaState:
    """
    Return the shoonya (void / inauspicious sign) for the given tithi and nakshatra.
    sign_id is 1-indexed (Mesha=1); sign_name uses SIGN_NAMES (0-indexed list).
    """
    t_sign = TITHI_SHOONYA_TABLE.get(tithi_id)
    n_sign = NAKSHATRA_SHOONYA_TABLE.get(nakshatra_id)
    return ShoonyaState(
        tithi_shoonya_sign_id=t_sign,
        tithi_shoonya_sign_name=SIGN_NAMES[t_sign - 1] if t_sign else None,
        nakshatra_shoonya_sign_id=n_sign,
        nakshatra_shoonya_sign_name=SIGN_NAMES[n_sign - 1] if n_sign else None,
    )


# ---------------------------------------------------------------------------
# Topic 19: Window-membership (Instant-only)
# ---------------------------------------------------------------------------

def compute_window_membership(
    instant_utc: datetime,
    inauspicious: list,
    auspicious: list,
    choghadiya_all,
    hora_all: list,
) -> WindowMembership:
    """
    Determine which timing windows the given instant falls inside.

    choghadiya_all may be a dict {"day": [...], "night": [...]} or a flat list.
    All datetime comparisons are UTC-aware; naive datetimes are treated as UTC.
    """

    def _tz(dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    inst = _tz(instant_utc)

    def _active(windows: list) -> list:
        result = []
        for w in windows:
            s, e = _tz(w.start_utc), _tz(w.end_utc)
            if s <= inst < e:
                result.append(w.label)
        return result

    def _next(windows: list) -> Optional[float]:
        soonest = None
        for w in windows:
            s = _tz(w.start_utc)
            if s > inst:
                diff = (s - inst).total_seconds()
                if soonest is None or diff < soonest:
                    soonest = diff
        return soonest

    def _current_slot(windows: list) -> Optional[str]:
        for w in windows:
            s, e = _tz(w.start_utc), _tz(w.end_utc)
            if s <= inst < e:
                return w.label
        return None

    # Normalise choghadiya to a flat list
    if isinstance(choghadiya_all, dict):
        choghadiya_flat: list = (
            choghadiya_all.get("day", []) + choghadiya_all.get("night", [])
        )
    else:
        choghadiya_flat = list(choghadiya_all) if choghadiya_all else []

    return WindowMembership(
        inauspicious_active=_active(inauspicious),
        auspicious_active=_active(auspicious),
        choghadiya_slot=_current_slot(choghadiya_flat),
        hora_planet=_current_slot(hora_all),
        seconds_to_next_inauspicious=_next(inauspicious),
        seconds_to_next_auspicious=_next(auspicious),
        seconds_to_next_choghadiya=_next(choghadiya_flat),
        seconds_to_next_hora=_next(hora_all),
    )


# ---------------------------------------------------------------------------
# Topic 20: Micro-timing (Instant-only)
# ---------------------------------------------------------------------------

def compute_micro_timing(instant_utc: datetime, sunrise_utc: datetime) -> MicroTiming:
    """
    Compute ghati/vighati from sunrise, muhurta-of-day, and Pranapada sign.

    Ghatika scale:
      1 ghatika   = 24 min = 1 440 s
      1 vighati   = 24 s   (1/60 of a ghatika)
      1 muhurta   = 2 ghatikas = 48 min  → 30 muhurtas per day
    Pranapada:
      Advances 1 sign every 5 ghatikas from Aries (sign_id=1) at sunrise.
    """

    def _tz(dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    elapsed_s = max(0.0, (_tz(instant_utc) - _tz(sunrise_utc)).total_seconds())
    ghati   = elapsed_s / 1440.0
    vighati = (ghati - int(ghati)) * 60.0
    muhurta = min(int(ghati / 2) + 1, 30)
    pranapada_idx = int(ghati / 5) % 12

    return MicroTiming(
        ghati_from_sunrise=round(ghati, 4),
        vighati_from_sunrise=round(vighati, 4),
        muhurta_of_day=muhurta,
        pranapada_sign_id=pranapada_idx + 1,
        pranapada_sign_name=SIGN_NAMES[pranapada_idx],
    )
