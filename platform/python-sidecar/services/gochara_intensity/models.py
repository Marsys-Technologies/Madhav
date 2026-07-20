"""
gochara_intensity.models — shared dataclasses for the G-3 intensity engine.

BRIEF_D5 §1 G-3 row / §10 promise-ledger:

    lambda_e(t | chart) = PROMISE * PERMISSION * exp(beta_e * X(t)) - suppression

Every disclosed weight/coefficient in this package carries an explicit
`calibration_state` of `"structural_prior"` -- BRIEF_D5 §7 explicitly
excludes D-4b's fitted-weight work from D-5 ("any FITTED beta -- structural
priors only -- D-4b fits, not D-5"). `IntensityResult.calibration_state`
mechanically enforces this at construction time (mirrors G-2's
`CitationDisciplineError` mechanical-enforcement pattern in
`gochara_grammar.models`) so a result can never silently present a number as
calibrated when it is, in fact, an undisclosed structural prior.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

VALID_TEMPORAL_SHAPES = ("point", "interval", "chain")
VALID_CALIBRATION_STATES = ("structural_prior", "empirically_calibrated")


class CalibrationDisclosureError(ValueError):
    """Raised when an IntensityResult (or a sub-component breakdown dict) is
    constructed without an explicit `calibration_state` disclosure on every
    weight/coefficient it reports. D-5 ships ONLY `structural_prior` values
    (BRIEF_D5 §7 exclusion: fitted weights are D-4b's job) -- this exception
    makes "never silently present a number as calibrated" a mechanical
    guarantee, not a convention callers must remember to honor.
    """


@dataclass
class SystemContribution:
    """One DR-14 timing-system's contribution to PERMISSION at a given t.

    `system_id` is one of PERMISSION's disclosed generator names (see
    `permission.py`'s `SYSTEM_WEIGHTS`); `active` is whether this
    independent generator's window is judged open at t; `weight` is its
    disclosed structural-prior contribution weight (NOT learned -- D-4b's
    job); `detail` carries system-specific evidence (dasha lord, phase name,
    event_jd of the fired primitive, etc.).
    """

    system_id: str
    active: bool
    weight: float
    calibration_state: str = "structural_prior"
    detail: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.calibration_state not in VALID_CALIBRATION_STATES:
            raise ValueError(f"calibration_state must be one of {VALID_CALIBRATION_STATES}")


@dataclass
class IntensityResult:
    """One computed lambda_e(t | chart) value for one event_class at one
    instant (point-shaped classes) or one point along an interval/chain
    sweep (interval/chain-shaped classes -- see `engine.compute_lambda_e_series`
    for the shape-aware multi-point caller, per BRIEF_D5 §3's binding
    shape-aware output semantics -- G-3 itself never asserts more temporal
    precision than an event-class's shape supports; that discipline is
    enforced by ALWAYS reporting `temporal_shape` alongside the value and by
    `engine.compute_lambda_e_series` being the only path that produces
    interval/chain output, never a bare single point dressed up as one).
    """

    chart_id: str
    event_class: str
    temporal_shape: str

    t_jd: float
    t_datetime_ist: Optional[str]

    # ── the four PROMISE x PERMISSION x exp(beta*X) - suppression terms ──
    promise: float
    promise_detail: dict

    permission: float
    permission_detail: dict  # {"systems": [SystemContribution...], "systems_active": [...],
                              #  "systems_considered": [...], "calibration_state": "structural_prior"}

    x_t: float
    x_t_detail: dict

    beta_e: float
    beta_e_calibration_state: str
    exp_term: float

    suppression: float
    suppression_detail: dict

    # ── assembled outputs ──
    raw_lambda: float          # PROMISE * PERMISSION * exp_term - suppression, UNSIGNED magnitude
    valence: str                # 'gain'|'loss'|'neutral'|'mixed' (brahma_event_ontology evidence_requirements)
    is_adverse: bool
    signed_lambda: float        # raw_lambda * (-1 if is_adverse else +1), per D-2 doctrine (BRIEF_D5 §1 G-3 row)

    calibration_state: str = "structural_prior"
    notes: list = field(default_factory=list)
    source: str = "live"  # 'live' | 'fixture' -- honesty marker, never silently blurred

    def __post_init__(self) -> None:
        if self.temporal_shape not in VALID_TEMPORAL_SHAPES:
            raise ValueError(f"temporal_shape must be one of {VALID_TEMPORAL_SHAPES}, got {self.temporal_shape!r}")
        if self.calibration_state not in VALID_CALIBRATION_STATES:
            raise CalibrationDisclosureError(
                f"IntensityResult calibration_state must be one of {VALID_CALIBRATION_STATES}, "
                f"got {self.calibration_state!r} -- D-5 ships structural priors only (BRIEF_D5 §7)."
            )
        if "calibration_state" not in self.permission_detail:
            raise CalibrationDisclosureError(
                "IntensityResult.permission_detail missing 'calibration_state' -- every PERMISSION "
                "per-system weight must disclose structural_prior (DR-14 plurality, BRIEF_D5 §7)."
            )
        if self.beta_e_calibration_state not in VALID_CALIBRATION_STATES:
            raise CalibrationDisclosureError(
                "IntensityResult.beta_e_calibration_state missing/invalid -- beta_e is a disclosed "
                "structural prior until D-4b fits it (BRIEF_D5 §7 exclusion)."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "event_class": self.event_class,
            "temporal_shape": self.temporal_shape,
            "t_jd": self.t_jd,
            "t_datetime_ist": self.t_datetime_ist,
            "promise": self.promise,
            "promise_detail": self.promise_detail,
            "permission": self.permission,
            "permission_detail": self.permission_detail,
            "x_t": self.x_t,
            "x_t_detail": self.x_t_detail,
            "beta_e": self.beta_e,
            "beta_e_calibration_state": self.beta_e_calibration_state,
            "exp_term": self.exp_term,
            "suppression": self.suppression,
            "suppression_detail": self.suppression_detail,
            "raw_lambda": self.raw_lambda,
            "valence": self.valence,
            "is_adverse": self.is_adverse,
            "signed_lambda": self.signed_lambda,
            "calibration_state": self.calibration_state,
            "notes": self.notes,
            "source": self.source,
        }


__all__ = [
    "VALID_TEMPORAL_SHAPES",
    "VALID_CALIBRATION_STATES",
    "CalibrationDisclosureError",
    "SystemContribution",
    "IntensityResult",
]
