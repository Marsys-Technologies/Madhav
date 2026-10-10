"""Jury wrapper over K4-1; roots and admissions precede shared preparation."""
from dataclasses import dataclass, replace
from typing import Callable, Iterable
from services.kala_core.measure import (
    DEFAULT_NON_IDENTITY_SHIFTS, Draw, Experiment, Interval, NullResult, Segment,
    Witness, evaluate_experiment, intersect_intervals, jury_agreement, prepare_draws,
)
from .evidence import Node, RootUse, Use, corroboration, evidence_graph
from .groups import Group


@dataclass(frozen=True)
class WholePipelineSelector:
    # Must rerun selection on each draw, not return the conditional statistic.
    conditioning: str
    input_refs: tuple[str,...]
    statistic: Callable[[Draw],float]

    def __post_init__(self):
        if not self.conditioning or not self.input_refs or not all(self.input_refs):
            raise ValueError('pipeline selection requires conditioning and input provenance')


@dataclass(frozen=True)
class Agreement:
    segments: tuple[Segment,...]
    witness_signature: tuple[str,...]
    conditional: NullResult
    pipeline: NullResult | None
    pipeline_reason: str | None
    groups: tuple[Group,...]
    evidence: tuple[RootUse,...]


def agreement(horizon: Interval, nodes: Iterable[Node], uses: Iterable[Use],
              groups: Iterable[Group], *, alpha: float, exchangeable: bool,
              non_identity_shifts: int=DEFAULT_NON_IDENTITY_SHIFTS,
              pipeline_selector: WholePipelineSelector | None=None) -> Agreement:
    nodes=tuple(nodes)
    groups=tuple(sorted(set(groups),key=lambda g:g.group_id)); uses=tuple(uses)
    roster={g.group_id:g for g in groups}
    if len(roster)!=len(groups) or 'G-P' not in roster:
        raise ValueError('unique declared groups including the judge anchor required')
    # Conditions/selectors remain in the graph even when their school is not
    # admitted as a witness. Otherwise filtering would erase selection ancestry.
    uses=tuple(replace(u,ancestry=u.ancestry | roster[u.group_id].ancestry,
        role='explains' if u.role=='corroborates' and (roster[u.group_id].status!='available' or 'corroborates' not in roster[u.group_id].roles) else u.role)
        if u.group_id in roster else replace(u,role='explains') if u.role=='corroborates' else u for u in uses)
    supports=corroboration(nodes,uses)
    eligible=[s for s in supports if s.group_id in roster and roster[s.group_id].status=='available'
              and 'corroborates' in roster[s.group_id].roles]
    # Allocate a root once, deterministically, judge first. Different roles,
    # stages and group aliases cannot manufacture another increment.
    owner={}
    for s in sorted(eligible,key=lambda s:(s.group_id!='G-P',s.group_id,sorted(s.roots))):
        for root in s.roots:
            owner.setdefault(root,s.group_id)
    by_group={}
    for s in eligible:
        g=roster[s.group_id]
        if any(owner[r]==s.group_id for r in s.roots):
            by_group.setdefault(s.group_id,[]).extend(intersect_intervals((s.interval,),g.coverage,horizon))
    witnesses=tuple(Witness(name,tuple(intervals)) for name,intervals in sorted(by_group.items()) if intervals)
    signature=tuple(w.witness_id for w in witnesses)
    # The selected judge window is the fixed conditioning interval, not a
    # corroborating root. Losing its credit must not erase anchor exposure.
    selected_anchor=tuple(i for u in uses if u.group_id=='G-P' and u.role=='selects'
        and roster['G-P'].status=='available' for i in intersect_intervals((u.interval,),roster['G-P'].coverage,horizon))
    if 'G-P' in signature:
        witnesses=tuple(Witness(w.witness_id,w.intervals+selected_anchor) if w.witness_id=='G-P' else w for w in witnesses)
    else:
        witnesses=(*witnesses,Witness('G-P',selected_anchor))
    preparation=prepare_draws(horizon,witnesses,anchor_id='G-P',non_identity_shifts=non_identity_shifts,exchangeable=exchangeable)
    conditional=jury_agreement(preparation,alpha=alpha)
    pipeline=None; reason='whole_pipeline_selector_not_supplied'
    if pipeline_selector:
        # Same shared shift schedule, but the judge is shifted too. A synthetic
        # fixed horizon is only preparation's anchor, never a scored witness.
        pipeline_preparation=prepare_draws(horizon,(*witnesses,Witness('__selection_horizon__',(horizon,))),
            anchor_id='__selection_horizon__',non_identity_shifts=non_identity_shifts,exchangeable=exchangeable)
        def statistic(draw):
            clean=Draw(draw.offset,tuple(Segment(s.interval,s.support-{'__selection_horizon__'}) for s in draw.segments))
            return pipeline_selector.statistic(clean)
        pipeline=evaluate_experiment(pipeline_preparation,Experiment('whole_pipeline_selection',pipeline_selector.conditioning),statistic,alpha=alpha)
        reason=None
    return Agreement(preparation.observation.segments,signature,conditional,pipeline,reason,groups,evidence_graph(nodes,uses))
