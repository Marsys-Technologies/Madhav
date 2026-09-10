"""
W3.0 — Nodal Drishti: Rahu/Ketu 5th/7th/9th aspect modifier for gochara transits.

CANDIDATE mechanism — wired into engine.py under _W30_NODAL_DRISHTI_ENABLED toggle.

Classical rule (later tradition)
---------------------------------
Rahu and Ketu are said to cast special aspects to the 5th, 7th, and 9th signs from
their transit position. This rule is attested in later tradition — specifically in
later Parashari commentaries such as Phaladeepika (Mantresvara, c. 16th century) and
the sub-commentary traditions on BPHS, but is NOT found in the original Brihat
Parashara Hora Shastra (BPHS) text itself. Classical sources that discuss this:

  - Phaladeepika (Mantresvara) — nodal special aspects discussed in transit chapters
  - Saravali (Kalyana Varma) — Rahu/Ketu transit effects, implying aspect reach
  - Later Parashari sub-commentaries (regional traditions, 17th–19th century)

The original BPHS does not enumerate 5/7/9 special aspects for Rahu and Ketu. Any
application of this rule should acknowledge this textual gap; the "later tradition"
phrase used throughout this module reflects that honest uncertainty.

Mechanism design
----------------
At evaluation JD, compute Rahu's transit sign using Swiss Ephemeris `swe.calc_ut`
with `MEAN_NODE` (Rahu) and sidereal flag. Ketu is always exactly opposite (180°).

Aspected signs (0-based, 0=Aries):
  From Rahu:  5th = (rahu_sign + 4) % 12
              7th = (rahu_sign + 6) % 12  [= ketu_sign]
              9th = (rahu_sign + 8) % 12
  From Ketu:  5th = (ketu_sign + 4) % 12
              7th = (ketu_sign + 6) % 12  [= rahu_sign]
              9th = (ketu_sign + 8) % 12

For each resonance target whose natal sign is in the aspected set, a contribution
modifier is drawn from ASPECT_MODIFIERS. The final modifier is the geometric mean
of all target contributions (or 1.0 when no targets are aspected).

Effect:
  5th/9th aspect (trine analog): modifier_contribution = 1.05 (slight amplification)
  7th aspect (full opposition):  modifier_contribution = 0.95 (slight suppression)

Honest skip conditions (returns modifier=1.0, skipped=True):
  - mechanism disabled via toggle
  - natal_facts is None (cannot determine target natal signs)
  - swe.calc_ut raises an exception
  - no resonance targets have sign data

I2 compliance: this module does NOT import from or modify any file in
services/gochara_grammar/ or services/gochara_intensity/.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.gochara_v3.context import ClassContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Identity constants
# ---------------------------------------------------------------------------
MECHANISM_ID: str = "w30_nodal_drishti"
TOGGLE_KEY: str = "w30_nodal_drishti"

# ---------------------------------------------------------------------------
# Sign names (0-based: 0=Aries, 11=Pisces) — canonical Parashari order
# ---------------------------------------------------------------------------
SIGN_NAMES: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Sign name → 0-based index lookup (reverse of SIGN_NAMES)
_SIGN_TO_INDEX: dict[str, int] = {name: idx for idx, name in enumerate(SIGN_NAMES)}

# ---------------------------------------------------------------------------
# Aspect tables
# ---------------------------------------------------------------------------
# 0-based offsets for 5th (offset 4), 7th (offset 6), 9th (offset 8) signs.
# "5th sign from X" means sign at (X + 4) % 12 in 0-based indexing.
ASPECT_OFFSETS: tuple[int, ...] = (4, 6, 8)

# Multiplicative modifier per aspect type (later-tradition calibration).
# Trine analogs (5th/9th) → slight amplification; opposition (7th) → slight suppression.
ASPECT_MODIFIERS: dict[int, float] = {
    4: 1.05,   # 5th aspect — trine analog (later tradition): amplify
    6: 0.95,   # 7th aspect — full opposition: suppress
    8: 1.05,   # 9th aspect — trine analog (later tradition): amplify
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MechanismResult:
    """Result returned by w30_nodal_drishti.compute().

    modifier:
        Multiplicative factor on transit intensity (applied to the lambda_v3
        formula term). 1.0 = neutral passthrough. Always > 0.
    aspected_sign_indices:
        Tuple of 0-based sign indices that are aspected by Rahu or Ketu at t_jd.
        Empty tuple when skipped or no aspects computable.
    rahu_sign:
        0-based sign index of Rahu's transit position at t_jd. None when skipped.
    ketu_sign:
        0-based sign index of Ketu's transit position at t_jd. None when skipped.
        Always (rahu_sign + 6) % 12 when not None.
    skipped:
        True when the mechanism produced no adjustment (disabled, no data, or
        swe failure). modifier is 1.0 in this case.
    skip_reason:
        Human-readable explanation when skipped is True. None otherwise.
    mechanism_id:
        Always MECHANISM_ID — for auditing which mechanism produced this result.
    """
    modifier: float
    aspected_sign_indices: tuple[int, ...]
    rahu_sign: Optional[int]
    ketu_sign: Optional[int]
    skipped: bool
    skip_reason: Optional[str]
    mechanism_id: str = MECHANISM_ID


# ---------------------------------------------------------------------------
# Helpers (pure, no I/O)
# ---------------------------------------------------------------------------
def _longitude_to_sign_index(lon_deg: float) -> int:
    """Convert a sidereal longitude (0–360°) to a 0-based sign index (0–11).

    sign_index = floor(lon_deg / 30) % 12
    Aries = 0, Taurus = 1, …, Pisces = 11.
    """
    return int(lon_deg / 30.0) % 12


def _compute_aspected_signs(rahu_sign: int) -> frozenset[int]:
    """Return the set of 0-based sign indices aspected by Rahu and Ketu.

    Ketu is always (rahu_sign + 6) % 12.
    Each body casts aspects to its 5th (offset 4), 7th (offset 6), and 9th
    (offset 8) signs per later-tradition Parashari commentaries.
    """
    ketu_sign = (rahu_sign + 6) % 12
    aspected: set[int] = set()
    for base in (rahu_sign, ketu_sign):
        for offset in ASPECT_OFFSETS:
            aspected.add((base + offset) % 12)
    return frozenset(aspected)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def compute(
    context: "ClassContext",
    t_jd: float,
    *,
    swe,
    enabled: bool = True,
) -> MechanismResult:
    """Compute the W3.0 nodal drishti modifier for a transit at Julian day t_jd.

    Parameters
    ----------
    context:
        Pre-fetched ClassContext. context.resonance_targets supplies the natal
        sign data for each target. context.natal_facts is checked for presence
        (honest skip if absent).
    t_jd:
        Julian Day of the transit evaluation point. Used to call swe.calc_ut
        for Rahu's current position.
    swe:
        Swiss Ephemeris module (or compatible mock). Called as:
            swe.calc_ut(t_jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
        Rahu longitude is result[0][0].
    enabled:
        Toggle: when False the mechanism is a no-op (returns modifier=1.0).

    Returns
    -------
    MechanismResult with modifier, aspected_sign_indices, rahu_sign, ketu_sign,
    skipped, skip_reason.

    Notes
    -----
    The 5/7/9 special aspects for Rahu and Ketu are from later tradition —
    specifically later Parashari commentaries — and are NOT in the original
    Brihat Parashara Hora Shastra text. This rule is applied here as a
    candidate mechanism with explicit "later tradition" acknowledgement.
    """
    if not enabled:
        return MechanismResult(
            modifier=1.0,
            aspected_sign_indices=(),
            rahu_sign=None,
            ketu_sign=None,
            skipped=True,
            skip_reason="mechanism disabled via toggle",
        )

    # --- natal_facts presence check ---
    natal_facts = context.natal_facts
    if natal_facts is None:
        return MechanismResult(
            modifier=1.0,
            aspected_sign_indices=(),
            rahu_sign=None,
            ketu_sign=None,
            skipped=True,
            skip_reason="natal_facts not available in context",
        )

    # --- Rahu transit position via Swiss Ephemeris ---
    try:
        result, _ = swe.calc_ut(t_jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
        rahu_lon_deg = result[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[w30_nodal_drishti] chart_id=%s t_jd=%.4f: swe.calc_ut failed: %s; skipping.",
            context.chart_id,
            t_jd,
            exc,
        )
        return MechanismResult(
            modifier=1.0,
            aspected_sign_indices=(),
            rahu_sign=None,
            ketu_sign=None,
            skipped=True,
            skip_reason=f"swe.calc_ut failed: {exc}",
        )

    rahu_sign = _longitude_to_sign_index(rahu_lon_deg)
    ketu_sign = (rahu_sign + 6) % 12

    aspected_signs = _compute_aspected_signs(rahu_sign)

    # --- Gather target contributions ---
    contributions: list[float] = []
    for target in context.resonance_targets:
        target_sign_name: Optional[str] = getattr(target, "target_sign", None)
        if target_sign_name is None:
            continue
        target_sign_idx = _SIGN_TO_INDEX.get(target_sign_name)
        if target_sign_idx is None:
            logger.debug(
                "[w30_nodal_drishti] Unknown sign name %r for target %r; skipping target.",
                target_sign_name,
                getattr(target, "target_ref", "<unknown>"),
            )
            continue
        if target_sign_idx not in aspected_signs:
            continue

        # Determine which aspect offset applies (prefer Rahu, then Ketu)
        contribution_modifier: Optional[float] = None
        for base_sign in (rahu_sign, ketu_sign):
            for offset in ASPECT_OFFSETS:
                if (base_sign + offset) % 12 == target_sign_idx:
                    contribution_modifier = ASPECT_MODIFIERS[offset]
                    break
            if contribution_modifier is not None:
                break

        if contribution_modifier is not None:
            contributions.append(contribution_modifier)

    # --- Compute final modifier ---
    if not contributions:
        # No targets are in aspected signs: mechanism ran but had no effect.
        modifier = 1.0
    else:
        # Geometric mean of all target contributions.
        log_sum = sum(math.log(c) for c in contributions)
        modifier = math.exp(log_sum / len(contributions))

    logger.debug(
        "[w30_nodal_drishti] chart_id=%s t_jd=%.4f: rahu_sign=%d(%s) ketu_sign=%d(%s) "
        "aspected=%r targets_fired=%d modifier=%.6f",
        context.chart_id,
        t_jd,
        rahu_sign,
        SIGN_NAMES[rahu_sign],
        ketu_sign,
        SIGN_NAMES[ketu_sign],
        sorted(aspected_signs),
        len(contributions),
        modifier,
    )

    return MechanismResult(
        modifier=modifier,
        aspected_sign_indices=tuple(sorted(aspected_signs)),
        rahu_sign=rahu_sign,
        ketu_sign=ketu_sign,
        skipped=False,
        skip_reason=None,
    )


__all__ = [
    "MECHANISM_ID",
    "TOGGLE_KEY",
    "SIGN_NAMES",
    "ASPECT_OFFSETS",
    "ASPECT_MODIFIERS",
    "MechanismResult",
    "compute",
]
