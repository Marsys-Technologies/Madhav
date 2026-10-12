"""Versioned fixture consumer and build-bound class replacement.

PLAN §9 permits planted stage contracts before live producer admission. This
entry consumes evaluated assertions; it computes neither clocks nor doctrine.
Times on the measure axis are UTC Unix seconds, never a civil-date fallback.
The orchestrator owns the transaction, connection and substep commit.
"""
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, model_validator
from psycopg.rows import tuple_row
from psycopg.types.json import Jsonb

from services.kala_core.assertion import AssertionEnvelope, Ref, Typed
from services.kala_core.measure import DEFAULT_NON_IDENTITY_SHIFTS, Interval, intersect_intervals
from .agreement import Agreement, agreement
from .contests import Contest, Opinion, Sequence, _canonical, contests, sequences, turning_points
from .evidence import GROUPS, Node, Use, Support, corroboration, evidence_graph
from .groups import Group, declarations
from .jaimini import MethodOutput, consume

VERSION = 'k4-2aw:class_input:v1'


class ClassInput(Typed):
    contract_version: Literal['k4-2aw:class_input:v1']
    acceptance_scope: Literal['fixture_only']
    anchor: AssertionEnvelope
    upstream_refs: dict[Literal['judge', 'negative_space', 'F1', 'F2'], tuple[Ref, ...]]
    nodes: tuple[Node, ...]
    uses: tuple[Use, ...]
    groups: tuple[Group, ...]
    opinions: tuple[Opinion, ...]
    jaimini: MethodOutput | None
    alpha: Annotated[float, Field(gt=0, lt=1, allow_inf_nan=False)]
    exchangeable: StrictBool
    corpus_admitted: StrictBool = False
    kp_ingested: StrictBool = False
    non_identity_shifts: Annotated[StrictInt, Field(ge=1)] = DEFAULT_NON_IDENTITY_SHIFTS

    @property
    def horizon(self):
        return Interval(self.anchor.interval.t0.timestamp(), self.anchor.interval.t1.timestamp())

    @property
    def event_class(self):
        return self.anchor.subject.event_class

    @model_validator(mode='after')
    def complete_class(self):
        if self.anchor.stage != 'judge' or self.anchor.role != 'selects' or self.anchor.operator_role != 'scored':
            raise ValueError('the class anchor must be a selected judge assertion')
        if not self.anchor.generation.startswith('candidate:') or self.anchor.generation == 'candidate:':
            raise ValueError('private candidate generation required')
        if set(self.upstream_refs) != {'judge', 'negative_space', 'F1', 'F2'} or not all(self.upstream_refs.values()):
            raise ValueError('all evaluated upstream input references must be pinned')
        if {g.group_id for g in self.groups} != GROUPS or len(self.groups) != len(GROUPS):
            raise ValueError('declare each school exactly once')
        source_roots = {r.root_id for r in evidence_graph(self.nodes, self.uses)}
        if any(not o.roots <= source_roots for o in self.opinions):
            raise ValueError('opinion requires an evaluated source root')
        if any(g.group_id == 'G-A' and 'corroborates' in g.roles for g in self.groups):
            raise ValueError('G-A remains testimony')
        if any(u.group_id == 'G-J' for u in self.uses) or any('G-J' in o.groups for o in self.opinions):
            # G-J can only enter through the complete consumer, never caller
            # supplied uses/opinions which bypass its admission checks.
            raise ValueError('G-J testimony requires a complete method output')
        intervals = [u.interval for u in self.uses] + [o.interval for o in self.opinions]
        if any(i.start < self.horizon.start or i.end > self.horizon.end for i in intervals):
            raise ValueError('input outside class horizon')
        if any(o.event_class != self.event_class for o in self.opinions):
            raise ValueError('opinion outside class grain')
        if any(not o.groups <= GROUPS for o in self.opinions):
            raise ValueError('unknown opinion school')
        if self.jaimini and (self.jaimini.event_class != self.event_class or self.jaimini.horizon != self.horizon):
            raise ValueError('complete method output outside class horizon')
        return self


def class_inputs(values):
    result = {}
    for raw in values:
        value = ClassInput.model_validate(raw)
        if value.event_class in result and result[value.event_class] != value:
            raise ValueError('conflicting duplicate class input')
        result[value.event_class] = value
    if not result:
        raise ValueError('declare a class with a typed unavailable result rather than an empty build')
    return result


def joint_turning_points(values):
    """Shared core comparison across the explicitly supplied class roster."""
    opinions = []
    for value in values:
        nodes, uses, roster, class_opinions = _class_evidence(value)
        support = _admitted_support(value.horizon, nodes, uses, roster)
        opinions.extend(_supported_opinions(class_opinions, support))
    return turning_points(opinions, min_classes=2)


def _roster(value):
    roster = {g.group_id: g for g in value.groups}
    for name, admitted, reason in (('G-T', value.corpus_admitted, 'corpus_not_admitted'),
                                   ('G-K', value.kp_ingested, 'kp_not_ingested')):
        if not admitted:
            roster[name] = replace(roster[name], status='information_unavailable', reason=reason)
    return roster


@dataclass(frozen=True)
class CandidateResult:
    assertion_id: str
    agreement: Agreement
    contests: tuple[Contest, ...]
    sequences: tuple[Sequence, ...]
    support: tuple[Support, ...]


def _class_evidence(value):
    # Explicit upstream selection roots need a selection use even when the
    # anchor's own source roots omit them; otherwise the root graph loses them.
    roots = frozenset((*value.anchor.roots.contact_ids, *value.anchor.roots.record_ids,
                       *value.anchor.roots.fact_ids, *value.anchor.used_for_selection))
    anchor_id = '__selected_judge__'
    if any(n.node_id == anchor_id for n in value.nodes):
        raise ValueError('reserved selection node identity')
    nodes = (*value.nodes, Node(anchor_id, roots, selection_roots=frozenset(value.anchor.used_for_selection)))
    uses = (*value.uses, Use(anchor_id, 'G-P', value.horizon, 'selects'))
    roster = _roster(value)
    opinions = list(value.opinions)
    if value.jaimini is None:
        roster['G-J'] = declarations(value.horizon)[1]
    else:
        method = consume(value.jaimini)
        roster['G-J'] = method.group
        method_nodes, method_uses = method.evidence()
        nodes += method_nodes
        uses += method_uses
        opinions.extend(method.opinions())
    return nodes, uses, roster, opinions


def _admitted_support(horizon, nodes, uses, roster):
    # Match agreement's roles/ancestry admission before using the same root
    # algebra. Keep selectors and conditions so their exclusions cannot vanish.
    admitted_uses = tuple(replace(u, ancestry=u.ancestry | roster[u.group_id].ancestry,
        role='explains' if u.role == 'corroborates' and (roster[u.group_id].status != 'available'
            or 'corroborates' not in roster[u.group_id].roles) else u.role) for u in uses)
    support = {replace(s, interval=i) for s in corroboration(nodes, admitted_uses)
        for i in intersect_intervals((s.interval,), roster[s.group_id].coverage, horizon)}
    return tuple(sorted(support, key=lambda s: (s.group_id, s.interval, sorted(s.roots), sorted(s.ancestry))))


def _supported_opinions(opinions, support):
    """Retain a conclusion only where every declared root/group is supported."""
    admitted = []
    for opinion in _canonical(opinions):
        matching = tuple(s for s in support if s.group_id in opinion.groups and s.roots & opinion.roots
            and s.interval.start < opinion.interval.end and s.interval.end > opinion.interval.start)
        boundaries = sorted({opinion.interval.start, opinion.interval.end,
            *(max(s.interval.start, opinion.interval.start) for s in matching),
            *(min(s.interval.end, opinion.interval.end) for s in matching)})
        for start, end in zip(boundaries, boundaries[1:]):
            by_group = {g: frozenset(r for s in matching if s.group_id == g
                and s.interval.start <= start and s.interval.end >= end
                for r in s.roots & opinion.roots) for g in opinion.groups}
            if all(by_group.values()) and opinion.roots <= frozenset().union(*by_group.values()):
                admitted.append(replace(opinion, interval=Interval(start, end)))
    return _canonical(admitted)


def compute(value: ClassInput) -> CandidateResult:
    nodes, uses, roster, opinions = _class_evidence(value)
    support = _admitted_support(value.horizon, nodes, uses, roster)
    opinions = _supported_opinions(opinions, support)
    measured = agreement(value.horizon, nodes, uses, roster.values(), alpha=value.alpha,
        exchangeable=value.exchangeable, non_identity_shifts=value.non_identity_shifts)
    identity = json.dumps([value.event_class, value.horizon.start, value.horizon.end], separators=(',', ':'))
    return CandidateResult('jury:' + hashlib.sha256(identity.encode()).hexdigest(), measured,
                           contests(opinions), sequences(opinions), support)


def bind_candidate(ctx, *, lock: bool) -> str:
    with ctx.db_conn.cursor(row_factory=tuple_row) as cursor:
        suffix = ' FOR UPDATE' if lock else ' FOR SHARE'
        binding = cursor.execute('SELECT chart_id,generation,state,conventions FROM kala_layer_candidate '
                                 'WHERE build_id=%s' + suffix, (str(ctx.build_id),)).fetchone()
        if binding is None or str(binding[0]) != str(ctx.config['chart_id']) or binding[2] != 'building':
            raise ValueError('only the build-bound building candidate may be replaced')
        if binding[3].get('fixture') is not True:
            raise ValueError('jury fixture consumer requires conventions.fixture=true')
        generation = binding[1]
        if not generation.startswith('candidate:') or generation == 'candidate:':
            raise ValueError('private candidate generation required')
        head = cursor.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s FOR SHARE',
                              (str(ctx.config['chart_id']),)).fetchone()
        if head and head[0] == generation:
            raise ValueError('published generation cannot be replaced')
        return generation


def validate_binding(ctx, value, generation):
    if str(value.anchor.chart_id) != str(ctx.config['chart_id']) or value.anchor.generation != generation:
        raise ValueError('input outside build chart or generation')


def _instant(value):
    return datetime.fromtimestamp(value, timezone.utc)


def _null(value):
    if value is None:
        return None
    return {**asdict(value), 'estimand': value.experiment.estimand,
            'conditioning': value.experiment.conditioning}


def _json(value):
    # Canonicalise sets from typed evidence without losing root identities.
    return Jsonb(json.loads(json.dumps(value, default=lambda v: sorted(v) if isinstance(v, (set, frozenset))
                                      else v.isoformat() if isinstance(v, datetime) else str(v))))


def write_candidate(ctx, value: ClassInput, *, joint_points=()) -> int:
    if ctx.dry_run:
        return 0
    generation = bind_candidate(ctx, lock=True)
    validate_binding(ctx, value, generation)
    result = compute(value)  # all computations/validation precede replacement
    measured = result.agreement
    chart = str(value.anchor.chart_id)
    grain = (chart, generation, value.event_class)
    graph = [asdict(r) for r in measured.evidence]
    roots = {'source_ids': sorted({r.root_id for r in measured.evidence})}
    provenance = {'contract_version': VERSION, 'acceptance_scope': 'fixture_only',
        'anchor': value.anchor.model_dump(mode='json'), 'upstream_refs': value.upstream_refs,
        'axis': 'utc_unix_seconds', 'sequences': [asdict(s) for s in result.sequences],
        'turning_points': [asdict(p) for p in joint_points if value.event_class in p.event_classes]}
    with ctx.db_conn.cursor() as cursor:
        # Child-first replacement is restricted to this class. Published and
        # legacy output have no DELETE or INSERT path in this consumer.
        cursor.execute('DELETE FROM kala_jury_candidate_segment WHERE chart_id=%s AND generation=%s AND event_class=%s', grain)
        cursor.execute('DELETE FROM kala_jury_candidate_contest WHERE chart_id=%s AND generation=%s AND event_class=%s', grain)
        cursor.execute('DELETE FROM kala_jury_candidate WHERE chart_id=%s AND generation=%s AND event_class=%s', grain)
        cursor.execute('''INSERT INTO kala_jury_candidate
            (chart_id,generation,event_class,assertion_id,window_start,window_end,subject,roots,
             provenance,coverage,evidence_graph,witness_groups,witness_signature,conditional_effect,
             conditional_null,pipeline_null,pipeline_null_reason,null_reason)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (*grain, result.assertion_id, value.anchor.interval.t0, value.anchor.interval.t1,
             _json(value.anchor.subject.model_dump(mode='json')), _json(roots), _json(provenance),
             _json({'coverage_ref': value.anchor.coverage_ref, 'horizon': asdict(value.horizon)}),
             _json(graph), _json([asdict(g) for g in measured.groups]), _json(measured.witness_signature),
             measured.conditional.effect, _json(_null(measured.conditional)),
             None if measured.pipeline is None else _json(_null(measured.pipeline)),
             measured.pipeline_reason, measured.conditional.reason))
        for segment in measured.segments:
            support_roots = {g: sorted({root for s in result.support if s.group_id == g
                and s.interval.start < segment.interval.end and s.interval.end > segment.interval.start
                for root in s.roots})
                for g in segment.support}
            cursor.execute('INSERT INTO kala_jury_candidate_segment VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                (*grain, result.assertion_id, _instant(segment.interval.start), _instant(segment.interval.end),
                 _json(sorted(segment.support)), _json(support_roots)))
        for contest in result.contests:
            material = json.dumps(asdict(contest), sort_keys=True, default=lambda v: sorted(v))
            cursor.execute('INSERT INTO kala_jury_candidate_contest VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                (*grain, result.assertion_id, hashlib.sha256(material.encode()).hexdigest(),
                 _instant(contest.interval.start), _instant(contest.interval.end),
                 _json([asdict(o) for o in contest.sides])))
    return 1
