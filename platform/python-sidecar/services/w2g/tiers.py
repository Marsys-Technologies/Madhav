"""W2G — the three-tier materialization policy (ADJUDICATION-14).

WHY THIS EXISTS. Design §2.3 assumed a per-chart contact-event count of
"tens of thousands" on the strength of an assumed "1-3x per cycle" crossing
multiplier. W2G's V4 bind-time validation MEASURED it instead and got
**779,595** events — an order of magnitude outside the design's own 10k-100k
band, with the Moon alone accounting for **76.1%** (1,773.36 crossings per
fixed degree across all nine bodies). The multiplier was withdrawn.

ADJUDICATION-14 (ANTARYĀMIN, 2026-08-02, `SHAD_DARSHANA_ADJUDICATIONS_NIGHT5
_v1_0.md`) resolved the overrun by reading design §2.5's multi-rate refinement
correctly rather than by inflating the band:

  * **Tier A — EAGER.** Saturn, Jupiter, Rahu, Ketu and Mars (Mars ruled in).
    Measured 40,293 / 39,476 / 20,963 contact events for the three charts with
    a v1 corpus — INSIDE the original 10k-100k band, unamended. Materialized
    full-span.
  * **Tier B — CONDITIONAL.** Sun, Mercury, Venus. Materialized only inside
    intervals Tier A has already elevated, plus their own stations.
  * **Tier C — LAZY.** The Moon. NEVER materialized full-span; computed on
    demand inside a window the slower layers already elevated, or for an
    election drill-down. This is design §2.5's "exactly how an acharya drills
    down" clause, and it is the clause that makes the ≤15-minute onboarding
    SLO reachable at all.

The tier is a property OF THE BODY, so it lives here as data and is asserted
by tests both ways — `body_tier('Moon') == TIER_LAZY` and
`materialization_policy('Moon').eager is False` — rather than being enforced
by a comment in a caller.

An unknown body raises. There is no default tier, because a default tier would
silently decide the most expensive question in the engine (§N.7 item 6).
"""
from __future__ import annotations

from dataclasses import dataclass

TIER_EAGER = "A_eager"
TIER_CONDITIONAL = "B_conditional"
TIER_LAZY = "C_lazy"

# Body -> tier. The nine `DAILY_BODIES` of `brahmagyan.l0_ephemeris`, all of
# them, so no body can fall through.
BODY_TIERS: dict[str, str] = {
    "Saturn": TIER_EAGER,
    "Jupiter": TIER_EAGER,
    "Rahu": TIER_EAGER,
    "Ketu": TIER_EAGER,
    "Mars": TIER_EAGER,
    "Sun": TIER_CONDITIONAL,
    "Mercury": TIER_CONDITIONAL,
    "Venus": TIER_CONDITIONAL,
    "Moon": TIER_LAZY,
}

# V4's measured share of the 779,595 total, quoted so the tier assignment
# carries its own evidence rather than pointing at a document.
MOON_SHARE_OF_MEASURED_EVENTS = 0.761
V4_MEASURED_CONTACT_EVENTS = 779_595
DESIGN_BAND = (10_000, 100_000)


@dataclass(frozen=True)
class MaterializationPolicy:
    body: str
    tier: str
    eager: bool
    full_span: bool
    conditional_on_elevated_intervals: bool
    reason: str


_POLICY_REASONS = {
    TIER_EAGER: (
        "Tier A (ADJUDICATION-14): measured 20,963-40,293 contact events per "
        "chart across the eager set — inside design §2.3's original "
        "10k-100k band without amending it. Materialized full-span."
    ),
    TIER_CONDITIONAL: (
        "Tier B (ADJUDICATION-14): materialized only inside intervals Tier A "
        "has already elevated, plus this body's own stations. Full-span "
        "materialization is not refused on principle — it is simply not paid "
        "for where nothing slower has elevated the interval."
    ),
    TIER_LAZY: (
        "Tier C (ADJUDICATION-14): the Moon is 76.1% of V4's measured 779,595 "
        "contact events. NEVER materialized full-span; computed on demand "
        "inside an already-elevated window or for an election drill-down "
        "(design §2.5's multi-rate refinement)."
    ),
}


def body_tier(body: str) -> str:
    """The materialization tier for `body`. Raises KeyError for an unknown
    body — see the module docstring on why there is no default."""
    return BODY_TIERS[body]


def materialization_policy(body: str) -> MaterializationPolicy:
    tier = body_tier(body)
    return MaterializationPolicy(
        body=body,
        tier=tier,
        eager=(tier == TIER_EAGER),
        full_span=(tier == TIER_EAGER),
        conditional_on_elevated_intervals=(tier == TIER_CONDITIONAL),
        reason=_POLICY_REASONS[tier],
    )


def eager_bodies() -> tuple[str, ...]:
    return tuple(b for b, t in BODY_TIERS.items() if t == TIER_EAGER)


def lazy_bodies() -> tuple[str, ...]:
    return tuple(b for b, t in BODY_TIERS.items() if t == TIER_LAZY)


__all__ = [
    "BODY_TIERS",
    "DESIGN_BAND",
    "MOON_SHARE_OF_MEASURED_EVENTS",
    "MaterializationPolicy",
    "TIER_CONDITIONAL",
    "TIER_EAGER",
    "TIER_LAZY",
    "V4_MEASURED_CONTACT_EVENTS",
    "body_tier",
    "eager_bodies",
    "lazy_bodies",
    "materialization_policy",
]
