"""ALGO3.4 typed interpretation of already evaluated judge/F1/F2 findings.

KYD-134 admits planted consumer fixtures only. No astrology is computed here;
source/field/coverage/locator mappings remain a separate conductor admission.
"""
from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import model_validator
from services.kala_core.assertion import Interval, Ref, Release, Roots, Source, Typed

VERSION = 'k3-negative-space/1.0.0'
Exposure = Literal['in_risk_set', 'outside_risk_set', 'method_inapplicable']
Knowledge = Literal['searched', 'unsearched', 'inputs_missing', 'computation_failed', 'complete']
Conclusion = Literal['none', 'supportive', 'adverse', 'obstructed', 'conditionally_deferred', 'denied']
Defeat = Literal['active', 'excepted', 'cancelled', 'partly_cancelled', 'contested', 'unresolved']
Effective = Literal['outside_risk_set', 'method_inapplicable', 'information_unavailable',
                    'evaluated_silent', 'obstruction_in_force', 'obstruction_cancelled',
                    'obstruction_partly_cancelled', 'obstruction_contested']


class Protection(Typed):
    target_assertion_id: Ref
    kind: Literal['defeats', 'excepts', 'partly_defeats', 'contests']
    fact_ids: tuple[Ref, ...]
    source: Source
    interval: Interval

    @model_validator(mode='after')
    def has_evidence(self):
        if not self.fact_ids:
            raise ValueError('protection requires protecting fact ids')
        return self


class Finding(Typed):
    contract_version: Literal['k3-negative-space/1.0.0']
    assertion_id: Ref
    chart_id: UUID
    generation: Ref
    event_class_id: Ref
    mechanism: Ref
    exposure: Exposure
    knowledge: Knowledge
    rule_conclusion: Conclusion
    defeat_state: Defeat
    measurement: Literal['not_estimated_here']
    judge_state: Literal['active', 'inactive', 'unqualified'] | None
    coverage: Literal['complete', 'incomplete', 'absent']
    binding: Literal['fixture_only', 'unbound']
    interval: Interval
    roots: Roots
    source: Source
    what: Ref | None
    by_what: Ref | None
    protections: tuple[Protection, ...]
    release: Release
    null_reason: Ref | None

    @model_validator(mode='after')
    def pinned(self):
        if not self.generation.startswith('candidate:') or self.generation == 'candidate:':
            raise ValueError('finding must name a private candidate generation')
        if self.binding == 'unbound' and not self.null_reason:
            raise ValueError('unbound input requires a named reason')
        if self.mechanism == 'vedha' and self.judge_state == 'active' and self.rule_conclusion in {'none', 'supportive'}:
            raise ValueError('active vedha cannot carry a silent/supportive conclusion')
        if self.release.instant is not None and self.release.instant < self.interval.t0:
            raise ValueError('release cannot precede the finding interval')
        if self.mechanism == 'vedha' and self.judge_state == 'active' and self.release.kind == 'instant':
            if self.release.instant != self.interval.t1:
                raise ValueError('vedha instant release must equal interval end')
        return self


class NegativeSpace(Typed):
    contract_version: Literal['k3-negative-space/1.0.0']
    assertion_id: Ref
    chart_id: UUID
    generation: Ref
    event_class_id: Ref
    mechanism: Ref
    exposure: Exposure
    knowledge: Knowledge
    rule_conclusion: Conclusion
    defeat_state: Defeat
    measurement: Literal['not_estimated_here']
    effective_state: Effective
    interval: Interval
    roots: Roots
    source: Source
    what: Ref | None
    by_what: Ref | None
    protections: tuple[Protection, ...]
    release: Release
    release_reason: Literal['release_unknown', 'release_conditional'] | None
    null_reason: Ref | None
    acceptance_scope: Literal['fixture_only', 'unbound']


def interpret(finding: Finding) -> NegativeSpace | None:
    """Retain axes and targeted defeating evidence; derive one usable state.

    A coverage hole outranks a planted active/cancelled label. Exceptions do
    not erase the candidate conclusion or turn harm into opposite support.
    """
    if finding.mechanism in {'rikta_tithi', 'daily_gandanta', 'kulika', 'transit_combustion'}:
        return None
    edges = tuple(edge for edge in finding.protections
                  if edge.target_assertion_id == finding.assertion_id
                  and edge.interval.t0 < finding.interval.t1
                  and edge.interval.t1 > finding.interval.t0)
    defeat = finding.defeat_state
    if edges:
        full = [edge for edge in edges if edge.interval.t0 <= finding.interval.t0
                and edge.interval.t1 >= finding.interval.t1]
        if any(edge.kind == 'contests' for edge in edges):
            defeat = 'contested'
        elif any(edge.kind in {'defeats', 'excepts'} for edge in full):
            defeat = 'cancelled'
        else:
            defeat = 'partly_cancelled'
    reason = finding.null_reason
    if finding.binding == 'unbound':
        state = 'information_unavailable'
    elif finding.exposure == 'outside_risk_set':
        state = 'outside_risk_set'
    elif finding.exposure == 'method_inapplicable':
        state = 'method_inapplicable'
    elif finding.coverage != 'complete':
        state, reason = 'information_unavailable', reason or 'judge_coverage_unavailable'
    elif finding.knowledge not in {'complete', 'searched'}:
        state, reason = 'information_unavailable', reason or finding.knowledge
    elif finding.mechanism == 'vedha' and finding.judge_state in {None, 'unqualified'}:
        state, reason = 'information_unavailable', reason or 'judge_vedha_state_unqualified'
    elif defeat == 'unresolved':
        state, reason = 'information_unavailable', reason or 'defeat_unresolved'
    elif finding.rule_conclusion in {'none', 'supportive'}:
        state = 'evaluated_silent'
    elif finding.mechanism == 'vedha' and finding.judge_state == 'inactive':
        state = 'evaluated_silent'
    else:
        state = {'active': 'obstruction_in_force', 'excepted': 'obstruction_cancelled',
                 'cancelled': 'obstruction_cancelled', 'partly_cancelled': 'obstruction_partly_cancelled',
                 'contested': 'obstruction_contested'}[defeat]
    facts = tuple(sorted(set(finding.roots.fact_ids).union(*(set(edge.fact_ids) for edge in edges))))
    roots = finding.roots.model_copy(update={'fact_ids': facts})
    return NegativeSpace(
        **{key: getattr(finding, key) for key in ('contract_version', 'assertion_id', 'chart_id',
           'generation', 'event_class_id', 'mechanism', 'exposure', 'knowledge', 'rule_conclusion',
           'measurement', 'interval', 'source', 'what', 'by_what', 'release')},
        defeat_state=defeat, effective_state=state, roots=roots, protections=edges,
        release_reason={'unknown': 'release_unknown', 'conditional': 'release_conditional'}.get(finding.release.kind),
        null_reason=reason if state == 'information_unavailable' else None,
        acceptance_scope=finding.binding,
    )
