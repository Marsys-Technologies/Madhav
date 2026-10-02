"""three_field_valence (GOCHARA_DESIGN_SPECS_v1_4 §3).

evidence_for_occurrence / evidence_against_occurrence answer "will this class
of thing occur?"; outcome_valence_for_native answers "is that occurrence good
for the native?" Occurrence contested ≠ outcome mixed: high evidence both
ways is reported as both fields standing, never cancelled to neutral and
never relabelled `mixed`. `unqualified` is the honest state when operands are
unresolved (ADK-0026) — never a favourable-sounding default (O-TV-1's E5
regression guard).
"""
from __future__ import annotations

from dataclasses import dataclass

from .registry import CLASS_BY_NAME

VALENCE_STATES = frozenset({"favourable", "adverse", "mixed", "unqualified"})


@dataclass
class Valence:
    evidence_for_occurrence: float
    evidence_against_occurrence: float
    occurrence: str  # "contested" | "plain" | "unqualified"
    outcome_valence_for_native: str
    # No rule in the spec or registry computes severity, so it is None
    # whenever no severity rule supplies one (i.e. always, today) — never a
    # fabricated 0.0. Always None for an unqualified window.
    severity: float | None = None
    unresolved_operand: str | None = None


def compute_valence(event_class: str, evidence_for: float,
                    evidence_against: float,
                    unresolved_operand: str | None = None) -> Valence:
    """§3: the three fields are independent; no arithmetic nets evidence_for
    against evidence_against. Valence derives from class polarity plus rule
    content at evaluation time, never copied class-blind from the rule row."""
    cls = CLASS_BY_NAME[event_class]
    if unresolved_operand is not None:
        return Valence(evidence_for, evidence_against, "unqualified",
                       "unqualified", unresolved_operand=unresolved_operand)
    occurrence = ("contested" if evidence_for > 0 and evidence_against > 0
                  else "plain")
    # Class-relative polarity (#11/#12): the outcome verdict is the class's
    # own polarity for the native. `mixed` is a valence verdict deriving from
    # class polarity plus rule content — no cited rule content here produces
    # it, so it is never emitted by default (S-03).
    if cls["polarity"] == "adverse":
        outcome = "adverse"
    elif cls["polarity"] in ("gain", "non-adverse"):
        outcome = "favourable"
    else:  # anchor — birth_anchor enters no endpoint (protocol §2)
        outcome = "unqualified"
    return Valence(evidence_for, evidence_against, occurrence, outcome)
