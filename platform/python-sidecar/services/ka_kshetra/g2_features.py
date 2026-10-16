"""G2 projections of the admitted F1 graph; no scalar promise or strength default."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence

from services.kala_core.promise import EffectiveState, MechanismRoute, PromiseGraph
from services.kala_core.promise.relationships import Relationship, Role
from services.ka_kshetra.g2_model import EventModel, InputValue, RouteCell, _operand


@dataclass(frozen=True)
class FeatureSpec:
    key: str
    kind: str
    mechanism_ids: tuple[str, ...]
    role: str | None = None
    rule_id: str | None = None


def extract_features(
    graph: PromiseGraph, relationships: Sequence[Relationship], specs: Sequence[FeatureSpec],
    available_fact_ids: Sequence[str], *, complete: bool,
    dominance: Mapping[str, InputValue] | None = None,
) -> dict[str, InputValue]:
    """Project role counts, cancellation indicators and rule-local comparisons.

    (I) INTERPRETATION: counts describe admitted formations independently of
    effective cancellation. An unresolved conclusion is not an inactive
    cancellation. F1 currently supplies no universal dominance number: only an
    explicit grounded rule-local operand can fill that term.
    ``complete`` is the upstream evaluated-coverage assertion, not row presence.
    """
    facts = set(available_fact_ids)
    result: dict[str, InputValue] = {}
    for spec in specs:
        if not spec.key or spec.key in result or not spec.mechanism_ids:
            raise ValueError('feature needs a unique key and route mechanism identities')
        if spec.kind not in {'admitted_count', 'effective_cancellation', 'rule_local_dominance'}:
            raise ValueError('feature kind must be typed')
        if spec.kind == 'admitted_count' and spec.role not in {r.value for r in Role}:
            raise ValueError('count must declare an F1 role')
        if spec.kind == 'rule_local_dominance' and not spec.rule_id:
            raise ValueError('dominance must name its local rule')
        source = f'F1:{spec.kind}:' + ','.join(sorted(spec.mechanism_ids))
        missing = InputValue(None, 'information_unavailable', source, ())
        result[spec.key] = missing
        if not complete:
            continue
        mechanisms = [graph.mechanisms.get(mid) for mid in spec.mechanism_ids]
        if any(m is None or m.route is not MechanismRoute.ADMITTED
               or not m.fact_ids or not set(m.fact_ids) <= facts for m in mechanisms):
            continue
        classes = {m.event_class_id for m in mechanisms}
        if len(classes) != 1:
            raise ValueError('a route cannot mix event classes')
        refs = set(f for m in mechanisms for f in m.fact_ids)
        if spec.kind == 'admitted_count':
            edges = [e for e in relationships if e.mechanism_id in spec.mechanism_ids
                     and e.role == spec.role]
            if any(e.resolution_state != 'resolved' or e.event_class_id not in classes
                   or not e.provenance or not e.rule_id for e in edges):
                continue
            result[spec.key] = InputValue(float(len({e.mechanism_id for e in edges})),
                'evaluated', source + ':' + ','.join(sorted(
                    {f'{e.edge_id}|{e.rule_id}|{e.provenance}' for e in edges})), tuple(sorted(refs)))
        elif spec.kind == 'effective_cancellation':
            conclusions = [c for c in graph.conclusions.values()
                           if c.mechanism_id in spec.mechanism_ids]
            if {c.mechanism_id for c in conclusions} != set(spec.mechanism_ids):
                continue
            states = [graph.effective_result(c.conclusion_id, facts) for c in conclusions]
            if any(s.state not in {EffectiveState.IN_FORCE, EffectiveState.DEFEATED} for s in states):
                continue
            refs.update(f for c in conclusions for f in c.fact_ids)
            refs.update(f for d in graph.defeats if d.conclusion_id in {c.conclusion_id for c in conclusions}
                        for f in d.fact_ids if f in facts)
            evidence = sorted({c.conclusion_id for c in conclusions}
                              | {d for s in states for d in s.defeat_ids}
                              | {d.defeat_id or d.rule_id for d in graph.defeats
                                 if d.conclusion_id in {c.conclusion_id for c in conclusions}})
            result[spec.key] = InputValue(float(any(s.state is EffectiveState.DEFEATED for s in states)),
                'evaluated', source + ':' + ','.join(evidence), tuple(sorted(refs)))
        else:
            operand = (dominance or {}).get(spec.rule_id)
            if operand is not None and _operand(operand) and operand.fact_ids and set(operand.fact_ids) <= facts:
                result[spec.key] = operand
    return result


def assemble_cells(
    model: EventModel, cells: Mapping[str, tuple[RouteCell, ...]],
    feature_specs: Mapping[str, tuple[FeatureSpec, ...]], graph: PromiseGraph,
    relationships: Sequence[Relationship], available_fact_ids: Sequence[str], *,
    complete: bool, dominance: Mapping[str, InputValue] | None = None,
) -> dict[str, tuple[RouteCell, ...]]:
    """Bind graph features into every original knot cell without shadow values."""
    route_ids = {r.route_id for r in model.routes}
    if set(cells) != route_ids or set(feature_specs) != route_ids:
        raise ValueError('each route must declare its graph feature mapping, even if empty')
    assembled = {}
    for route in model.routes:
        specs = feature_specs[route.route_id]
        if any(not set(s.mechanism_ids) <= set(route.mechanism_ids) for s in specs):
            raise ValueError('feature mechanisms must belong to this route')
        if any(graph.mechanisms[mid].event_class_id != model.event_class
               for mid in route.mechanism_ids if mid in graph.mechanisms):
            raise ValueError('route graph event class differs from the model class')
        features = extract_features(graph, relationships, specs, available_fact_ids,
                                    complete=complete, dominance=dominance)
        if any(set(cell.terms) & features.keys() for cell in cells[route.route_id]):
            raise ValueError('caller terms may not shadow F1 features')
        assembled[route.route_id] = tuple(replace(cell, terms=dict(cell.terms) | features)
                                          for cell in cells[route.route_id])
    return assembled
