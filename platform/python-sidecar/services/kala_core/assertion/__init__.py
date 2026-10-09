"""Shared assertion envelope. K0a lands the negative-space payload first.

References carry L1 identities, never copies of their measured values. This
module performs no astrology and imports no downstream scoring engine.
"""
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.kala_core.vocab import EvidenceRole, OperatorRole

Ref = Annotated[str, Field(min_length=1, pattern=r"\S")]


class Typed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Subject(Typed):
    event_class: Ref
    affected_person: Ref
    objects: tuple[Ref, ...]


class PeriodAnchor(Typed):
    system: Ref
    MD: Ref
    AD: Ref
    PD: Ref | None = None
    applicability: Literal["applicable", "inapplicable", "unknown"]


class Interval(Typed):
    t0: datetime
    t1: datetime

    @model_validator(mode="after")
    def half_open(self):
        if self.t0.tzinfo is None or self.t1.tzinfo is None or self.t0 >= self.t1:
            raise ValueError("interval must be aware and nonempty [t0,t1)")
        return self


class Resolution(Typed):
    computation: Ref
    source_licensed: Ref
    empirically_supported: Ref | None


class Roots(Typed):
    contact_ids: tuple[Ref, ...]
    record_ids: tuple[Ref, ...]
    fact_ids: tuple[Ref, ...]

    @model_validator(mode="after")
    def sourced(self):
        if not (self.contact_ids or self.record_ids or self.fact_ids):
            raise ValueError("at least one source id is required")
        return self


class Source(Typed):
    text: Ref
    locator: Ref


class Precision(Typed):
    method: Ref
    delta_lambda: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None
    delta_t: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None


class Release(Typed):
    kind: Literal["instant", "conditional", "unknown"]
    instant: datetime | None = None
    predicate_ref: Ref | None = None

    @model_validator(mode="after")
    def qualified_release(self):
        if (self.kind == "instant") != (self.instant is not None):
            raise ValueError("instant release requires an instant only")
        if (self.kind == "conditional") != (self.predicate_ref is not None):
            raise ValueError("conditional release requires a predicate only")
        if self.instant is not None and self.instant.tzinfo is None:
            raise ValueError("release instant must be timezone aware")
        return self


class NegativeSpacePayload(Typed):
    kind: Literal["negative_space"]
    exposure: Literal["in_risk_set", "outside_risk_set"]
    knowledge: Literal["evaluated", "unavailable", "method_inapplicable"]
    rule_conclusion: Literal["obstruction_present", "silent", "not_evaluated"]
    defeat_state: Literal["in_force", "cancelled", "qualified", "not_evaluated"]
    effective_state: Literal["outside_risk_set", "method_inapplicable", "information_unavailable",
                             "evaluated_silent", "obstruction_active", "obstruction_cancelled",
                             "obstruction_qualified", "measured_lower_rate"]
    measurement: Literal["not_measured_here"]
    what: Ref
    by_what: Ref
    release: Release

    @staticmethod
    def state_from_axes(exposure, knowledge, conclusion, defeat):
        if exposure == "outside_risk_set": return "outside_risk_set"
        if knowledge == "unavailable": return "information_unavailable"
        if knowledge == "method_inapplicable": return "method_inapplicable"
        if conclusion == "silent": return "evaluated_silent"
        if conclusion == "obstruction_present":
            return {"in_force": "obstruction_active", "cancelled": "obstruction_cancelled",
                    "qualified": "obstruction_qualified"}.get(defeat)
        return None

    @classmethod
    def from_judge_fixture(cls, axes):
        """Derive effective state from a fixture judge's un-netted axes."""
        if not isinstance(axes, dict) or "effective_state" in axes:
            raise ValueError("fixture judge must carry raw axes, not a downstream state")
        state = cls.state_from_axes(axes.get("exposure"), axes.get("knowledge"),
                                    axes.get("rule_conclusion"), axes.get("defeat_state"))
        return cls.model_validate({**axes, "effective_state": state})

    @model_validator(mode="after")
    def effective_conclusion(self):
        # Precedence preserves unknown/silent/cancelled independently of any
        # legacy numeric override. A lower rate cannot be inferred here.
        expected = self.state_from_axes(self.exposure, self.knowledge, self.rule_conclusion, self.defeat_state)
        if self.effective_state != expected:
            raise ValueError("effective_state disagrees with the five axes")
        return self


class AssertionEnvelope(Typed):
    assertion_id: Ref
    chart_id: UUID
    generation: Ref
    stage: Literal["judge", "negative_space", "jury", "forecaster"]
    method: Ref
    rule_version: Ref
    subject: Subject
    frame: Ref
    period_anchor: PeriodAnchor
    interval: Interval
    grain: Literal["year", "era", "month", "week", "day"]
    resolution: Resolution
    role: EvidenceRole
    roots: Roots
    derivation_parents: tuple[Ref, ...] = Field(min_length=1)
    used_for_selection: tuple[Ref, ...]
    source: Source
    provenance: Literal["verse_cited", "uncited_extension"]
    operator_role: OperatorRole
    null_reason: Literal["outside_risk_set", "method_inapplicable", "information_unavailable",
                         "evaluated_silent", "release_unknown"] | None
    coverage_ref: Ref
    precision: Precision
    input_vector_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class Assertion(AssertionEnvelope):
    """K0a's typed negative-space assertion; later stages extend the envelope."""
    stage: Literal["negative_space"]
    payload: NegativeSpacePayload


def increment_allowed(assertion: Assertion, root: str, already_counted: set[str]) -> int:
    """Root identity survives duplicate rows and relocation between stages."""
    roots = (*assertion.roots.record_ids, *assertion.roots.contact_ids, *assertion.roots.fact_ids)
    return int(assertion.operator_role == OperatorRole.SCORED and assertion.role != EvidenceRole.SELECTS and root in roots
               and root not in assertion.used_for_selection and root not in already_counted)
