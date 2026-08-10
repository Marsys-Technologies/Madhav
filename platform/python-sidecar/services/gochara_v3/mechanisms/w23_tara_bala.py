"""
W2.3 — Tara bala: 9-cycle nakshatra quality modifier for gochara transits vs natal Moon.

CANDIDATE mechanism — NOT wired into engine.py. Togglable dormant module.

Background
----------
The v1 primitive `nakshatra_ingress_tara` (primitives.py:558) is wired-but-dead:
its call site (configuration_activity.py ~line 67) never passes
`natal_moon_nakshatra_id`, so the Tara-quality dict in each sentence's `detail`
is never populated. This module activates the same classical rule INDEPENDENTLY
of the v1 primitive, sourcing natal Moon nakshatra from ClassContext.natal_facts
(pre-fetched by v3 context, zero extra DB round-trips).

Classical rule
--------------
Nava Tara Chakra (9-Tara cycle): for any transit nakshatra, count forward from
the natal Moon's nakshatra (both 1-based, 1–27) in steps of 1, cycling modulo
27, and then modulo 9 to get the Tara position (1–9). Each Tara has a quality
and a multiplicative modifier on the transit's overall intensity.

Tara positions (1-based, cycle repeats every 9):
  1 Janma       — mixed    → 1.00
  2 Sampat      — good     → 1.15
  3 Vipat       — bad      → 0.75
  4 Kshema      — good     → 1.10
  5 Pratyak     — bad      → 0.80
  6 Sadhana     — good     → 1.05
  7 Naidhana    — bad      → 0.70
  8 Mitra       — good     → 1.15
  9 Paramamitra — very good → 1.20

Formula:
  position = ((transit_nak_index - natal_moon_nak_index) % 27) % 9 + 1
  (both indexes 1-based; the outer %27 handles the full 27-nak cycle;
   the inner %9 maps into the repeating 9-Tara cycle.)

Derivation of transit body nakshatra from longitude:
  nakshatra_index (1-based) = int(longitude_deg / (360.0/27)) + 1
  clamped to [1, 27].

Classical citations:
  - Muhurta Chintamani — Tara bala chapter
  - BPHS — nakshatra transit quality (Tara Chakra)

Admission state: candidate (not yet ablation-evidenced; toggle_key controls
whether the engine applies this modifier when it is eventually wired).

I2 compliance: this module does NOT import from or modify any file in
services/gochara_grammar/ or services/gochara_intensity/.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.gochara_v3.context import ClassContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Toggle key (engine checks context feature flags — off by default until wired)
# ---------------------------------------------------------------------------
MECHANISM_ID: str = "w23_tara_bala"
TOGGLE_KEY: str = "w23_tara_bala"

# ---------------------------------------------------------------------------
# 9-Tara cycle tables (1-based; position 1–9)
# ---------------------------------------------------------------------------
TARA_QUALITY: dict[int, str] = {
    1: "janma",
    2: "sampat",
    3: "vipat",
    4: "kshema",
    5: "pratyak",
    6: "sadhana",
    7: "naidhana",
    8: "mitra",
    9: "paramamitra",
}

# Multiplicative modifier on transit intensity per Tara position.
# Values in (0, 2]: < 1.0 damps, > 1.0 amplifies, 1.0 neutral.
TARA_MODIFIERS: dict[str, float] = {
    "janma":       1.00,
    "sampat":      1.15,
    "vipat":       0.75,
    "kshema":      1.10,
    "pratyak":     0.80,
    "sadhana":     1.05,
    "naidhana":    0.70,
    "mitra":       1.15,
    "paramamitra": 1.20,
}

# Nakshatra arc width (degrees per nakshatra, exact)
_NAK_ARC_DEG: float = 360.0 / 27.0


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MechanismResult:
    """Result returned by a candidate mechanism's compute() call.

    modifier: multiplicative factor to apply to the transit intensity.
              1.0 = neutral (passthrough). Always > 0.
    tara_name: name of the Tara position (e.g. "sampat", "naidhana").
               None when the mechanism is disabled or no natal Moon available.
    tara_position: integer 1–9 (Tara cycle position). None same conditions.
    skipped: True when the mechanism produced no adjustment (disabled, no data,
             or natal Moon nakshatra unavailable). modifier is 1.0 in this case.
    skip_reason: human-readable explanation when skipped is True.
    mechanism_id: always MECHANISM_ID — for auditing which mechanism produced this.
    """
    modifier: float
    tara_name: Optional[str]
    tara_position: Optional[int]
    skipped: bool
    skip_reason: Optional[str]
    mechanism_id: str = MECHANISM_ID


# ---------------------------------------------------------------------------
# Core computation (pure function — no I/O, no DB)
# ---------------------------------------------------------------------------
def compute_tara(
    transit_nak_index: int,
    natal_moon_nak_index: int,
) -> tuple[str, float]:
    """Return (tara_name, modifier). Both indexes are 1-based (1–27).

    Formula:
        position = ((transit - natal) % 27) % 9 + 1

    The outer %27 normalises the forward count within the 27-nakshatra wheel.
    The inner %9 maps into the repeating 9-Tara cycle.
    Position is always in [1, 9].
    """
    position = ((transit_nak_index - natal_moon_nak_index) % 27) % 9 + 1
    tara = TARA_QUALITY[position]
    modifier = TARA_MODIFIERS[tara]
    return tara, modifier


def _longitude_to_nakshatra_index(longitude_deg: float) -> int:
    """Convert a sidereal longitude (0–360°) to a 1-based nakshatra index (1–27).

    nakshatra_index = floor(longitude / (360/27)) + 1, clamped [1, 27].
    """
    idx = int(longitude_deg / _NAK_ARC_DEG) + 1
    return max(1, min(27, idx))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def compute(
    context: "ClassContext",
    t_jd: float,
    *,
    enabled: bool = True,
    transit_body_longitude_deg: Optional[float] = None,
) -> MechanismResult:
    """Compute the Tara bala modifier for a transit at Julian day t_jd.

    Parameters
    ----------
    context:
        The pre-fetched ClassContext. natal_facts.graha_longitudes["Moon"]
        supplies the natal Moon sidereal longitude used to derive the Moon's
        natal nakshatra index.
    t_jd:
        Julian Day of the transit evaluation point (informational; not used
        in the nakshatra computation — that uses transit_body_longitude_deg).
    enabled:
        Toggle: when False the mechanism is a no-op (returns modifier=1.0).
    transit_body_longitude_deg:
        Sidereal longitude of the transiting body at t_jd. When None the
        mechanism logs a warning and returns modifier=1.0 (honest skip).
        In production the engine will supply this from the pre-computed
        per-JD planet position vector (zero extra ephemeris calls needed
        since positions are already evaluated as part of X(t)).

    Returns
    -------
    MechanismResult with modifier, tara_name, tara_position, skipped, skip_reason.
    """
    if not enabled:
        return MechanismResult(
            modifier=1.0,
            tara_name=None,
            tara_position=None,
            skipped=True,
            skip_reason="mechanism disabled via toggle",
        )

    # --- Natal Moon nakshatra from pre-fetched context ---
    natal_facts = context.natal_facts
    if natal_facts is None:
        return MechanismResult(
            modifier=1.0,
            tara_name=None,
            tara_position=None,
            skipped=True,
            skip_reason="natal_facts not available in context",
        )

    moon_lon = natal_facts.graha_longitudes.get("Moon")
    if moon_lon is None:
        logger.debug(
            "[w23_tara_bala] chart_id=%s: Moon longitude absent from natal_facts; skipping.",
            context.chart_id,
        )
        return MechanismResult(
            modifier=1.0,
            tara_name=None,
            tara_position=None,
            skipped=True,
            skip_reason="Moon longitude absent from natal_facts.graha_longitudes",
        )

    natal_moon_nak = _longitude_to_nakshatra_index(moon_lon)

    # --- Transit body nakshatra ---
    if transit_body_longitude_deg is None:
        logger.debug(
            "[w23_tara_bala] chart_id=%s t_jd=%.4f: transit_body_longitude_deg not supplied; skipping.",
            context.chart_id,
            t_jd,
        )
        return MechanismResult(
            modifier=1.0,
            tara_name=None,
            tara_position=None,
            skipped=True,
            skip_reason="transit_body_longitude_deg not supplied",
        )

    transit_nak = _longitude_to_nakshatra_index(transit_body_longitude_deg)

    # --- Tara computation ---
    tara_name, modifier = compute_tara(transit_nak, natal_moon_nak)
    position = ((transit_nak - natal_moon_nak) % 27) % 9 + 1

    logger.debug(
        "[w23_tara_bala] chart_id=%s t_jd=%.4f: natal_moon_nak=%d transit_nak=%d "
        "tara_pos=%d tara=%s modifier=%.3f",
        context.chart_id,
        t_jd,
        natal_moon_nak,
        transit_nak,
        position,
        tara_name,
        modifier,
    )

    return MechanismResult(
        modifier=modifier,
        tara_name=tara_name,
        tara_position=position,
        skipped=False,
        skip_reason=None,
    )


__all__ = [
    "MECHANISM_ID",
    "TOGGLE_KEY",
    "TARA_QUALITY",
    "TARA_MODIFIERS",
    "MechanismResult",
    "compute_tara",
    "compute",
]
