"""
gochara_intensity.beta_priors — beta_e, the per-event-class exponential
coefficient in exp(beta_e * X(t)) (BRIEF_D5 §1 G-3 row).

BRIEF_D5 §7 explicitly excludes fitted weights from D-5 ("any FITTED beta --
structural priors only -- D-4b fits, not D-5"). Every value below is a
DISCLOSED STRUCTURAL PRIOR (`calibration_state='structural_prior'`), not a
learned coefficient -- D-4b's hierarchical calibration pass is the only
place these numbers may ever be fitted against outcome data.

Prior-selection reasoning (documented, engineering judgment): X(t)
(`configuration_activity.py`) is an unbounded non-negative sum of
target-weight x orb-strength contributions across up to 9 primitive
families and however many resonance targets a chart/event_class carries;
in practice (per this module's own live-verification run against chart
482012f1, see the G-3 close report) a "quiet" instant has X(t) in the
0.0-1.0 range and a "loud" multi-primitive-multi-target instant reaches
3-6. A flat DEFAULT_BETA = 0.35 keeps exp(beta*X) in a roughly 1x-9x
range across that span -- large enough to matter, not so large that a
single busy instant swamps PROMISE*PERMISSION's own [0,1]x[0,1] bound.
Event classes with a narrower classical "trigger window" doctrine
(point-shaped classes, where a specific exact-degree contact is
classically decisive -- e.g. marriage, career_advancement) get a
slightly higher beta (0.45) so a sharp X(t) spike matters more; classes
whose classical doctrine is itself about a sustained state rather than a
sharp trigger (interval/chain-shaped classes, e.g. major_gain,
spiritual_turn, business_launch) get a slightly lower beta (0.30) so a
single spike matters less than sustained activity across the sweep this
module doesn't itself compute (that's G-4's job) -- a modest, documented
lean toward the vision's own shape-aware framing (BRIEF_D5 §3), not a
per-class fitted value.
"""
from __future__ import annotations

DEFAULT_BETA = 0.35

_POINT_TRIGGER_BETA = 0.45
_SUSTAINED_BETA = 0.30

BETA_STRUCTURAL_PRIORS: dict[str, float] = {
    # point-shaped, sharp-trigger classes
    "marriage": _POINT_TRIGGER_BETA,
    "career_advancement": _POINT_TRIGGER_BETA,
    "career_entry": _POINT_TRIGGER_BETA,
    "achievement_recognition": _POINT_TRIGGER_BETA,
    "childbirth": _POINT_TRIGGER_BETA,
    "property_acquisition": _POINT_TRIGGER_BETA,
    "exam_outcome": _POINT_TRIGGER_BETA,
    "surgery": _POINT_TRIGGER_BETA,
    "travel_event": _POINT_TRIGGER_BETA,
    "romantic_start": _POINT_TRIGGER_BETA,
    "bereavement": _POINT_TRIGGER_BETA,
    "illness_acute": _POINT_TRIGGER_BETA,
    "birth_anchor": _POINT_TRIGGER_BETA,
    # interval-shaped, sustained-state classes
    "major_gain": _SUSTAINED_BETA,
    "major_loss": _SUSTAINED_BETA,
    "career_setback": _SUSTAINED_BETA,
    "chronic_onset": _SUSTAINED_BETA,
    "financial_deception": _SUSTAINED_BETA,
    "psychological_arc": _SUSTAINED_BETA,
    "spiritual_turn": _SUSTAINED_BETA,
    "relocation": _SUSTAINED_BETA,
    "parental_event": _SUSTAINED_BETA,
    # chain-shaped, multi-milestone classes
    "business_launch": _SUSTAINED_BETA,
    "career_change": _SUSTAINED_BETA,
    "education_milestone": _SUSTAINED_BETA,
    "foreign_settlement": _SUSTAINED_BETA,
    "separation": _SUSTAINED_BETA,
}


def beta_for(event_class: str) -> float:
    return BETA_STRUCTURAL_PRIORS.get(event_class, DEFAULT_BETA)


__all__ = ["DEFAULT_BETA", "BETA_STRUCTURAL_PRIORS", "beta_for"]
