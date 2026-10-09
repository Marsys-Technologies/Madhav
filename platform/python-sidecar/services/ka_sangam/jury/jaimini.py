"""Consume the complete reviewed method; construct neither clock nor rule.

The producer owns class mapping and rāśi-dṛṣṭi geometry. Contacts are directed
records, never expanded with a reverse edge. Cara is an upstream F2 method,
not an alias of the Moon-nakṣatra ladder. A review ref is provenance, not a
local claim of a production verdict. No partial rule can enter agreement.
"""
from dataclasses import dataclass, replace
import hashlib
import json
from services.kala_core.clocks.methods import DashaMethod, dasha_method
from services.kala_core.measure import Interval, intersect_intervals, union_intervals
from .evidence import Node, Support, Use
from .groups import Group, admit, declarations


@dataclass(frozen=True)
class DirectedContact:
    root_id: str
    caster: str
    target: str
    interval: Interval


@dataclass(frozen=True)
class MethodAssertion:
    rule_ref: str
    interval: Interval
    roots: frozenset[str]


@dataclass(frozen=True)
class MethodOutput:
    event_class: str
    horizon: Interval
    clock: DashaMethod
    cara_refs: tuple[str,...]
    rasi_refs: tuple[str,...]
    review_refs: tuple[str,...]
    coverage: tuple[Interval,...]
    contacts: tuple[DirectedContact,...]
    assertions: tuple[MethodAssertion,...]
    complete: bool


@dataclass(frozen=True)
class JaiminiResult:
    group: Group
    output: MethodOutput
    support: tuple[Support,...]

    def evidence(self) -> tuple[tuple[Node,...],tuple[Use,...]]:
        nodes={}; uses=set()
        if self.group.status=='available':
            for a in self.output.assertions:
                material=json.dumps([self.output.event_class,a.rule_ref,sorted(a.roots)],separators=(',',':'))
                key='G-J:'+hashlib.sha256(material.encode()).hexdigest()
                nodes[key]=Node(key,a.roots)
                uses.add(Use(key,'G-J',a.interval,'corroborates',self.group.ancestry))
        return tuple(nodes[k] for k in sorted(nodes)),tuple(sorted(uses,key=lambda u:(u.node_id,u.interval)))

    def directed_contacts(self,caster: str,target: str) -> tuple[Interval,...]:
        return tuple(c.interval for c in self.output.contacts if c.caster==caster and c.target==target) if self.group.status=='available' else ()


def consume(output: MethodOutput) -> JaiminiResult:
    group=declarations(output.horizon)[1]
    reason=None
    if output.clock != dasha_method('chara'):
        reason='wrong_clock'
    elif not output.complete:
        reason='partial_method_output'
    elif not output.event_class or not output.cara_refs or not output.rasi_refs:
        reason='cara_or_rasi_input_missing'
    elif union_intervals(output.coverage,output.horizon)!=(output.horizon,):
        reason='method_coverage_incomplete'
    else:
        refs=frozenset(output.cara_refs+output.rasi_refs)
        contacts={c.root_id for c in output.contacts if c.caster and c.target and c.root_id in output.rasi_refs}
        if any(not a.rule_ref or not a.roots<=refs or not a.roots.intersection(output.cara_refs)
               or not a.roots.intersection(contacts)
               or intersect_intervals((a.interval,),output.coverage,output.horizon)!=(a.interval,)
               or not all(union_intervals((c.interval for c in output.contacts if c.root_id==root),a.interval)==(a.interval,)
                          for root in a.roots.intersection(output.rasi_refs))
               for a in output.assertions):
            reason='partial_or_uncovered_rule'
    if reason:
        return JaiminiResult(replace(group,reason=reason),output,())
    group=admit(group,output.cara_refs+output.rasi_refs,output.coverage,output.review_refs,complete_method=True)
    support=tuple(sorted({Support('G-J',a.interval,a.roots,group.ancestry) for a in output.assertions},
                         key=lambda s:(s.interval,sorted(s.roots)))) if group.status=='available' else ()
    return JaiminiResult(group,output,support)
