"""
gochara_v3.mechanisms.w25_kota_chakra — Kota Chakra ring modifier (W2.5).

DORMANT mechanism — NOT wired into engine.py. This module is a candidate
mechanism for the GOCHARA-UTKARSHA Wave 2 campaign. It exists as a standalone
compute unit and registers itself via the YAML entry at:
  services/gochara_v3/mechanisms/registry/w25_kota_chakra.yaml

Admission into the live scoring path requires ablation evidence and a formal
admission ruling (see registry: admission_state: candidate).

Classical basis
---------------
Kota Chakra (Fort Diagram) describes concentric rings of fortification around
a central point. Malefic transits through progressively inner rings of the
Kota represent increasing siege intensity — Stambha (innermost, most powerful)
through Madhya, Pragara, and Bahya (outermost). When malefic planets (primarily
Saturn and Mars) transit the inner rings, adverse-class events are amplified.
The kala_kota_chakra table (built by W0.2) records ring placements but was
never consumed in the v1 gochara scoring path — this mechanism closes that gap.

Reference: Kota Chakra tradition; bg_kota_chakra_rings (ADJUDICATION-9 tier-iii).

Ring intensity mapping (innermost = most powerful)
--------------------------------------------------
  stambha  : 1.30  — siege fully established; innermost ring
  madhya   : 1.15  — middle ring
  pragara  : 1.08  — outer-middle ring
  bahya    : 1.04  — outermost ring; siege barely begun
  none     : 1.00  — not in siege; unit modifier (no effect)

Scope
-----
Only fires for adverse event classes (SIEGE_CLASSES). Gain/neutral event
classes return modifier=1.0 — Kota Chakra amplification is conceptually an
adverse-siege modifier, not a benefic one.

Data dependency
---------------
Requires kota_chakra ring data to be present on the ClassContext. As of this
authoring (W2.5), ClassContext does NOT carry a dedicated kota field — the
kala_kota_chakra table is built by W0.2 but is not yet surfaced in
ClassContext.fetch(). The mechanism degrades gracefully: if no kota data is
found, modifier=1.0 is returned with an honest detail note indicating the
missing data path. This is the same "honest null over fabricated value" doctrine
(§N.6 / §N.7 of CLAUDE.md) applied to mechanism data availability.

I2 compliance: does NOT touch services/gochara_grammar/* or
services/gochara_intensity/* or services/gochara_v3/engine.py.
"""
from __future__ import annotations

import logging
from typing import Optional

from services.gochara_v3.mechanisms import MechanismResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MECHANISM_ID = "w25_kota_chakra"
TOGGLE_KEY = "w25_kota_chakra"

# Ring intensity (innermost = most powerful; bahya = outermost, barely siege).
# Modifier is multiplicative: 1.0 = no effect, 1.30 = 30% amplification.
RING_MODIFIERS: dict[str, float] = {
    "stambha": 1.30,   # innermost — siege fully established
    "madhya": 1.15,    # middle
    "pragara": 1.08,   # outer-middle
    "bahya": 1.04,     # outermost
    "none": 1.00,      # not in siege — unit modifier
}

# Valid ring names (RING_MODIFIERS keys excluding "none").
VALID_RINGS: frozenset[str] = frozenset(RING_MODIFIERS.keys()) - {"none"}

# Only adverse / siege-class event classes fire this mechanism.
# Gain-class and neutral-class events are unaffected by Kota siege.
SIEGE_CLASSES: frozenset[str] = frozenset({
    "illness_acute",
    "chronic_onset",
    "accident",
    "loss",
})

# Classical primary malefics for Kota Chakra siege evaluation.
# (Saturn and Mars are the siege-establishing malefics per tradition.)
KOTA_MALEFICS: frozenset[str] = frozenset({"Saturn", "Mars"})

# Unit result constants for the common fast-paths.
_UNIT_MODIFIER = 1.0
_DETAIL_NOT_SIEGE_CLASS = (
    "w25_kota_chakra: event_class not in SIEGE_CLASSES — Kota modifier not applicable "
    "for non-adverse event classes; returning unit modifier."
)
_DETAIL_DISABLED = (
    "w25_kota_chakra: mechanism disabled via toggle — returning unit modifier."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute(
    context,
    t_jd: float,
    *,
    enabled: bool = True,
) -> MechanismResult:
    """Compute the Kota Chakra ring modifier for the given context + JD.

    Parameters
    ----------
    context : ClassContext
        Pre-fetched immutable context. No DB access occurs here.
    t_jd : float
        Julian Day of the evaluation point (used for future transit-position
        lookup once kota data lands in ClassContext; currently unused).
    enabled : bool
        When False, returns a unit modifier immediately (mechanism toggled off).
        Controlled by TOGGLE_KEY in the admission registry.

    Returns
    -------
    MechanismResult
        modifier in [1.0, 1.30] for siege-class events with kota data.
        modifier == 1.0 (unit) for:
          - mechanism disabled
          - event_class not in SIEGE_CLASSES
          - no kota data available in context (honest degrade)
    """
    # Fast-path: mechanism disabled.
    if not enabled:
        return MechanismResult(
            mechanism_id=MECHANISM_ID,
            modifier=_UNIT_MODIFIER,
            enabled=False,
            detail=_DETAIL_DISABLED,
        )

    # Fast-path: non-siege event class — Kota amplification not applicable.
    event_class = getattr(context, "event_class", None)
    if event_class not in SIEGE_CLASSES:
        return MechanismResult(
            mechanism_id=MECHANISM_ID,
            modifier=_UNIT_MODIFIER,
            enabled=False,
            detail=_DETAIL_NOT_SIEGE_CLASS,
        )

    # Attempt to read kota_chakra data from context.
    # ClassContext does not yet carry a dedicated kota field (W0.2 builds
    # kala_kota_chakra but it is not surfaced in ClassContext.fetch() as of W2.5).
    # We probe several plausible field names defensively.
    kota_data = _extract_kota_data(context)

    if kota_data is None:
        # Honest degrade: no kota data available. Return unit modifier with
        # an explicit detail note pointing to the missing data path.
        return MechanismResult(
            mechanism_id=MECHANISM_ID,
            modifier=_UNIT_MODIFIER,
            enabled=False,
            detail=(
                "w25_kota_chakra: kota_data not in ClassContext; W0.2 builds "
                "kala_kota_chakra but it is not yet surfaced in ClassContext.fetch(). "
                "Returning unit modifier until context carries kota ring data."
            ),
        )

    # Determine the innermost ring occupied by any KOTA_MALEFIC.
    ring = _determine_ring(kota_data)
    modifier = RING_MODIFIERS.get(ring, _UNIT_MODIFIER)

    detail = (
        f"w25_kota_chakra: event_class={event_class!r}, ring={ring!r}, "
        f"modifier={modifier:.2f}. "
        f"Kota Chakra siege ring for malefic transit "
        f"(Saturn/Mars); innermost ring = stambha (1.30), outermost = bahya (1.04)."
    )

    logger.debug("[w25_kota_chakra] %s", detail)

    return MechanismResult(
        mechanism_id=MECHANISM_ID,
        modifier=modifier,
        enabled=True,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_kota_data(context) -> Optional[dict]:
    """Probe ClassContext for kota_chakra ring data.

    Returns a dict if found, None if no kota data is present.
    The dict is expected to carry ring placements keyed by graha name or
    a 'ring' key directly (format TBD once W0.2 → ClassContext wiring lands).

    Probe order:
    1. context.kota_chakra_data  — dedicated field (future)
    2. context.kota_rings        — alternate field name (future)
    3. Any field named 'kota'    — generic fallback

    All probes are defensive (AttributeError / TypeError → None).
    """
    for attr in ("kota_chakra_data", "kota_rings", "kota"):
        try:
            val = getattr(context, attr, None)
        except Exception:  # noqa: BLE001
            continue
        if val is not None and isinstance(val, dict):
            return val
    return None


def _determine_ring(kota_data: dict) -> str:
    """Determine the innermost Kota ring occupied by a primary malefic.

    Traverses RING_MODIFIERS keys in innermost→outermost order and returns
    the first ring name found in kota_data for any KOTA_MALEFIC graha.

    Falls back to 'none' if no malefic occupies a known ring.

    kota_data format (expected, TBD once W0.2 → ClassContext lands):
      {
        "Saturn": "stambha",
        "Mars": "bahya",
        ...
      }
    or alternatively:
      {
        "ring": "stambha",   # if the data is already per-class
        ...
      }
    """
    # Priority order: innermost rings first.
    ring_priority = ("stambha", "madhya", "pragara", "bahya")

    # Build a map of ring → True if any KOTA_MALEFIC is there.
    occupied: dict[str, bool] = {}
    for graha, ring_val in kota_data.items():
        if graha in KOTA_MALEFICS and isinstance(ring_val, str):
            r = ring_val.lower()
            if r in VALID_RINGS:
                occupied[r] = True

    # If the dict has a top-level "ring" key (pre-aggregated), use it.
    if not occupied and "ring" in kota_data:
        ring_val = kota_data["ring"]
        if isinstance(ring_val, str) and ring_val.lower() in VALID_RINGS:
            return ring_val.lower()

    # Return the innermost occupied ring, or "none".
    for ring in ring_priority:
        if occupied.get(ring):
            return ring
    return "none"


__all__ = [
    "MECHANISM_ID",
    "TOGGLE_KEY",
    "RING_MODIFIERS",
    "SIEGE_CLASSES",
    "KOTA_MALEFICS",
    "compute",
]
