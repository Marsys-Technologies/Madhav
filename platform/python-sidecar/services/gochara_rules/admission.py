"""P2/P3/P4 admission evaluation (GOCHARA_DESIGN_SPECS_v1_4 §2.2, S-03,
R3-S02).

P3: P3_admit(agent, class) := (∃h∈H: contact(agent,h)) ∨ (∃ℓ∈L(H):
contact(agent,ℓ)) — the union reading; the conjunction reading is rejected
(S-03). contact(agent, house_span h) := residence ∨ aspect;
contact(agent, house_lord ℓ) := conjunction(agent, ℓ_natal) ∨ aspect.

P4 — ONE rule (R3-S02), obeyed identically by O-RP-2 and O-RP-3:
infl(g) := (∃h∈H: contact(g,h)) ∨ (∃ℓ∈L(H): contact(g,ℓ)) with contact =
occupation ∨ aspect ∨ conjunction-within-orb as in P3; then
P4_admit(class) := infl(Jupiter) ∧ infl(Saturn) — union within an agent,
AND across agents; the two agents need not share one target.

P2 adverse residence (D-RQ5 shape): Saturn/Sun/Mars/Jupiter in 12/8/1 from
the Moon is evidence FOR the adverse classes and never attaches to gain
classes; Sade-Sati (12th-from-Moon) is testimony-only with zero score effect
(S-04, O-RP-5b).

Aspect geometry reuses the kernel's pinned SPECIAL_DRISHTI_DEG (oracles
constants.aspect_offsets: universal 7th = 180; Mars 90/210; Jupiter 120/240;
Saturn 60/270; nodes cast nothing — N-14). The P4 admission orb is 5°,
pinned in the O-RP-3 fixture.
"""
from __future__ import annotations

from ..gochara_kernel.convention import SPECIAL_DRISHTI_DEG
from .frames import Frame, sign_of
from .predicates import ADMITTED, EXCLUDED, UNQUALIFIED
from .registry import signature_houses, signature_lords

P4_ADMISSION_ORB_DEG = 5.0  # pinned in the O-RP-3 fixture

ADVERSE_RESIDENCE_BODIES = frozenset({"Saturn", "Sun", "Mars", "Jupiter"})
ADVERSE_RESIDENCE_HOUSES = frozenset({12, 8, 1})


def _delta(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def aspect_points(agent: str, lam: float) -> list[float]:
    """Aspect points cast from λ: (λ + offset) mod 360 per the pinned
    SPECIAL_DRISHTI_DEG (§6.2 inv 6 forward count; nodes cast nothing)."""
    return [(lam + off) % 360.0 for off in SPECIAL_DRISHTI_DEG.get(agent, [])]


def contact_house(agent: str, agent_lam: float, house_sign: str) -> bool:
    """contact(agent, house_span h) := residence(agent, h) ∨ aspect(agent, h)."""
    if sign_of(agent_lam) == house_sign:
        return True
    return any(sign_of(p) == house_sign for p in aspect_points(agent, agent_lam))


def contact_lord(agent: str, agent_lam: float, lord: str, chart: dict,
                 orb_deg: float = P4_ADMISSION_ORB_DEG) -> bool:
    """contact(agent, house_lord ℓ) := conjunction-within-orb ∨ aspect on the
    lord's natal position."""
    natal_lam = chart["natal"].get(lord)
    if natal_lam is None:
        return False
    if _delta(agent_lam, natal_lam) <= orb_deg:
        return True
    return any(_delta(p, natal_lam) <= orb_deg
               for p in aspect_points(agent, agent_lam))


def infl(agent: str, agent_lam: float, event_class: str, chart: dict,
         H: frozenset[str] | None = None,
         L: frozenset[str] | None = None) -> str:
    """infl(g) := (∃h∈H: contact(g,h)) ∨ (∃ℓ∈L(H): contact(g,ℓ)).
    H unknown (None) ⇒ `unqualified`, never false (§2.2 inv 2)."""
    if H is None:
        H = signature_houses(event_class, chart)
    if H is None:
        return UNQUALIFIED
    if L is None:
        L = signature_lords(event_class, chart)
    for h in H:
        if contact_house(agent, agent_lam, h):
            return ADMITTED
    for lord in (L or ()):
        if contact_lord(agent, agent_lam, lord, chart):
            return ADMITTED
    return EXCLUDED


def p3_admit(agent: str, agent_lam: float, event_class: str,
             chart: dict) -> str:
    """P3_admit(agent, class) — the S-03 union over house and lord."""
    return infl(agent, agent_lam, event_class, chart)


def p4_admit(jupiter_lam: float, saturn_lam: float, event_class: str,
             chart: dict, H: frozenset[str] | None = None,
             L: frozenset[str] | None = None) -> str:
    """P4_admit(class) := infl(Jupiter) ∧ infl(Saturn) — the ONE rule
    (R3-S02). AND across agents, union within an agent; the agents need not
    share one target. An unqualified agent ⇒ unqualified admission."""
    ij = infl("Jupiter", jupiter_lam, event_class, chart, H=H, L=L)
    isat = infl("Saturn", saturn_lam, event_class, chart, H=H, L=L)
    if ij == UNQUALIFIED or isat == UNQUALIFIED:
        return UNQUALIFIED
    if ij == ADMITTED and isat == ADMITTED:
        return ADMITTED
    return EXCLUDED


def p2_adverse_residence(agent: str, agent_lam: float, chart: dict) -> int | None:
    """The agent's house from the natal Moon if it is an adverse residence
    (Saturn/Sun/Mars/Jupiter in 12/8/1 — D-RQ5 shape), else None. Evidence
    FOR the adverse classes; NEVER attaches to gain classes; never to a
    relative's event (frame is always the native's Moon here)."""
    if agent not in ADVERSE_RESIDENCE_BODIES:
        return None
    from .frames import house_of
    h = house_of(agent_lam, Frame("moon"), chart)
    return h if h in ADVERSE_RESIDENCE_HOUSES else None


def p2_adverse_edge(agent: str, agent_lam: float, event_class: str,
                    chart: dict) -> dict | None:
    """The scored adverse-residence edge for a class, or None.

    Direction: adverse residence is evidence FOR adverse classes (D-RQ5
    shape) and attaches NOTHING to gain classes (O-RP-5a)."""
    from .registry import CLASS_BY_NAME
    house = p2_adverse_residence(agent, agent_lam, chart)
    if house is None:
        return None
    if CLASS_BY_NAME[event_class]["polarity"] != "adverse":
        return None
    return {"agent": agent, "house_from_moon": house, "class": event_class,
            "direction": "adverse", "channel": "evidence_for_occurrence",
            "operator_role": "scored", "provenance": "verse_cited"}


def sade_sati_row(agent: str, agent_lam: float, chart: dict) -> dict | None:
    """Sade-Sati phase-1 (12th-from-Moon) TESTIMONY row (O-RP-5b): exists as
    operator_role = testimony on adverse-eligible classes with ZERO score
    effect; never attaches to gain classes (childbirth carries no edge)."""
    from .frames import house_of
    if agent != "Saturn":
        return None
    if house_of(agent_lam, Frame("moon"), chart) != 12:
        return None
    return {"agent": agent, "house_from_moon": 12, "phase": 1,
            "operator_role": "testimony", "ruling_ref": "D-PADMIT",
            "score_effect": 0.0}
