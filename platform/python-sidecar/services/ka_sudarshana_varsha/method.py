"""Read-time BPHS 74 candidate judge, outside the sealed Gochara generation.

Consumes explicit F1 house evidence; never invents nature, strength, aspects,
exaltation or varga conditions. F1's effective nature must already account for
BPHS 74.7-9,15-16 (including exaltation and Saptavarga qualifications), with
its L1 fact references and source. Unknown operands remain unknown here.

(I) INTERPRETATION: occupancy takes precedence, aspects apply to empty houses,
and the lord is used only when neither exists (74.11-14). Equal counts compare
sums of referenced strength in one unit; this disclosed reduction can be
replaced at candidate review without changing any published generation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from math import isfinite

from services.kala_core.clocks.methods import ClockFact
from services.kala_core.clocks.sudarshana import FRAMES, period_rows
from services.kala_core.overlays.contested import AdapterPayload, digest
from services.kala_core.sky import kernel_body
from services.kala_core.vocab import SignId


@dataclass(frozen=True)
class Influence:
    """One F1 relation with effective nature and comparable, referenced strength.

    ``nature`` is an upstream assessment, not a new astronomical fact. Its
    references identify the operands of the assessment. A missing assessment
    must carry ClockFact(None, ...), never a natural-benefic default.
    """
    graha: str
    relationship_id: str
    source: str
    nature: ClockFact
    strength: ClockFact
    strength_unit: str | None


@dataclass(frozen=True)
class HouseEvidence:
    sign_idx: int
    occupants: tuple[Influence, ...] = ()
    aspects: tuple[Influence, ...] = ()
    lord: Influence | None = None
    occupancy_complete: bool = False
    aspects_complete: bool = False


@dataclass(frozen=True)
class F1Snapshot:
    chart_id: str
    generation: str
    natal_build_id: str
    convention_id: str
    at_jd: float
    houses: tuple[HouseEvidence, ...]
    source_id: str

    def validate(self):
        if (not all((self.chart_id, self.generation, self.natal_build_id, self.convention_id, self.source_id))
                or not isfinite(self.at_jd) or len(self.houses) != 12
                or {h.sign_idx for h in self.houses} != set(range(12))
                or any(type(h.sign_idx) is not int for h in self.houses)):
            raise ValueError('complete twelve-sign F1 snapshot and explicit source pin required')
        for h in self.houses:
            if type(h.occupancy_complete) is not bool or type(h.aspects_complete) is not bool:
                raise ValueError('F1 absence requires explicit completeness')
            for influences in (h.occupants, h.aspects, (h.lord,) if h.lord else ()):
                bodies = []
                for i in influences:
                    if (not isinstance(i, Influence) or not i.relationship_id or not i.source
                            or not isinstance(i.nature, ClockFact) or not isinstance(i.strength, ClockFact)):
                        raise ValueError('cited, typed F1 influence required')
                    bodies.append(kernel_body(i.graha))
                if len(set(bodies)) != len(bodies):
                    raise ValueError('duplicate F1 influence cannot manufacture a count')
        return self


def _nature(i, house):
    if not i.nature.known or i.nature.value not in ('benefic', 'malefic', 'neutral'):
        return None
    # BPHS 74.7-9 explicitly treats the Sun as auspicious in the first bhava.
    return 'benefic' if kernel_body(i.graha) == 'Sun' and house == 1 else i.nature.value


def _refs(influences, *, strength=False):
    return sorted({str(ref) for i in influences
                   for ref in (*i.nature.fact_ids, *(i.strength.fact_ids if strength else ()))})


def _commencement(h, house):
    """74.24-26 statements remain separate, even when their effects conflict."""
    natures = [_nature(i, house) for i in h.occupants]
    known = h.occupancy_complete and all(n is not None for n in natures)
    benefics = any(n == 'benefic' for n in natures) if known else None
    malefics = any(n == 'malefic' for n in natures) if known else None
    return dict(
        source='BPHS 74.24-26',
        benefic_in_1_4_7_10_5_9_8=(benefics and house in (1,4,7,10,5,9,8)) if known else None,
        benefic_effect=('unfavorable' if house in (6,12) else 'favorable') if benefics else None,
        malefic_in_3_6_11=(malefics and house in (3,6,11)) if known else None,
        node_only_harm=(len(h.occupants)==1 and kernel_body(h.occupants[0].graha) in ('Rahu','Ketu')) if known else None,
        malefic_majority_harm=(natures.count('malefic') > natures.count('benefic')) if known else None,
        relationship_ids=sorted(i.relationship_id for i in h.occupants), fact_ids=_refs(h.occupants),
        null_reason=None if known else 'commencement_occupancy_or_nature_unavailable',
    )


def _judge_house(h, house, frame_refs):
    result = dict(house=house, sign_idx=h.sign_idx, conclusion=None, reason=None,
                  null_reason=None, basis=None, relationship_ids=[], fact_ids=list(frame_refs),
                  source='BPHS 74.7-16', commencement=_commencement(h, house))
    if not h.occupancy_complete:
        result['null_reason'] = 'occupancy_unavailable'
        return result
    if h.occupants:
        influences, basis = h.occupants, 'occupants'
    elif not h.aspects_complete:
        result['null_reason'] = 'aspects_unavailable'
        return result
    elif h.aspects:
        influences, basis = h.aspects, 'aspects'
    elif h.lord:
        influences, basis = (h.lord,), 'lord'
    else:
        result['null_reason'] = 'lord_unavailable'
        return result
    result.update(basis=basis, relationship_ids=sorted(i.relationship_id for i in influences),
                  fact_ids=sorted(set(frame_refs) | set(_refs(influences))),
                  input_sources=sorted({i.source for i in influences}))
    natures = [_nature(i, house) for i in influences]
    if None in natures:
        result['null_reason'] = 'effective_nature_unavailable'
        return result
    benefics = [i for i,n in zip(influences,natures) if n == 'benefic']
    malefics = [i for i,n in zip(influences,natures) if n == 'malefic']
    result.update(benefic_count=len(benefics), malefic_count=len(malefics))
    if len(benefics) != len(malefics):
        positive = len(benefics) > len(malefics)
        result.update(conclusion='favorable' if positive else 'unfavorable',
                      reason='benefic_majority' if positive else 'malefic_majority')
    elif not benefics:
        result.update(conclusion='mixed', reason='neutral_influences')
    else:
        relevant = benefics + malefics
        units = {i.strength_unit for i in relevant}
        def comparable(i):
            value = i.strength.value
            return (i.strength.known and type(value) in (int,float,Decimal) and isfinite(value) and value >= 0)
        if len(units) != 1 or not all(units) or not all(comparable(i) for i in relevant):
            result['null_reason'] = 'strength_unavailable'
            return result
        b = sum(i.strength.value for i in benefics)
        m = sum(i.strength.value for i in malefics)
        result.update(conclusion='favorable' if b > m else 'unfavorable' if m > b else 'mixed',
                      reason='strength_tie_break', strength_reduction='sum_like_unit_f1_strength',
                      strength_unit=next(iter(units)), benefic_strength=b, malefic_strength=m,
                      fact_ids=sorted(set(frame_refs) | set(_refs(relevant,strength=True))))
    return result


def judge_period(period, evidence: F1Snapshot):
    """Judge all twelve bhavas for any nested period at its own commencement."""
    if not isinstance(evidence, F1Snapshot):
        raise TypeError('typed F1Snapshot required')
    evidence.validate()
    for key in ('chart_id','generation','natal_build_id','convention_id'):
        if getattr(evidence,key) != period[key]:
            raise ValueError('F1 evidence does not match candidate/natal/convention pin')
    if evidence.at_jd != period['t_in']:
        raise ValueError('F1 evidence must be evaluated at this period commencement')
    by_sign = {h.sign_idx:h for h in evidence.houses}
    houses = [_judge_house(by_sign[(period['sign_idx']+h-1)%12],h,period['fact_ids']) for h in range(1,13)]
    return dict(period_id=period['period_id'], frame=period['frame'], active_sign_idx=period['sign_idx'],
                houses=houses, f1_source_id=evidence.source_id, f1_fingerprint=digest(asdict(evidence)),
                coverage='complete' if all(h['conclusion'] is not None for h in houses) else 'partial')


def evaluate_candidate(payload: AdapterPayload, *, year, evidence: F1Snapshot):
    """Compute an unadmitted read-time method result from stored KA-3b geometry.

    No dispatch, registered writer, publication update or persisted conclusion.
    Nested periods can be evaluated with ``judge_period`` and their own F1
    snapshots; the annual snapshot never pretends to cover later commencements.
    """
    if not isinstance(payload, AdapterPayload) or payload.family != 'sudarshana_varsha':
        raise ValueError('Sudarshana adapter payload required')
    payload.validate()
    entries = [r for r in payload.entries if r['year'] == year and not r.get('null_reason')]
    if len(entries) != 1 or not payload.context.convention.computable:
        raise ValueError('requested year has no computed candidate coverage')
    ctx = payload.context
    names = [s.value for s in SignId]
    natal, refs = {}, {}
    for frame in FRAMES:
        fact = ctx.fact(frame.upper(),'sign')
        if fact is None or fact.get('fact_value_text') not in names:
            raise ValueError('missing/invalid natal sign fact')
        natal[frame] = names.index(fact['fact_value_text'])
        refs[frame] = fact['fact_id']
    entry = entries[0]
    expected = {f:(n+year-1)%12 for f,n in natal.items()}
    if entry['frames'] != expected or entry['frame_fact_ids'] != refs:
        raise ValueError('adapter frame geometry differs from cited L1 signs')
    periods = period_rows(chart_id=ctx.chart_id, generation=ctx.generation,
                          natal_build_id=ctx.natal_build_id, convention_id=ctx.convention.convention_id,
                          varsha_year=year,t_in=entry['t_in'],t_out=entry['t_out'],
                          natal_signs=natal,frame_fact_ids=refs,year_anchor=entry['year_anchor'])
    return dict(schema='ka_sudarshana_method_candidate/1', chart_id=ctx.chart_id,
                generation=ctx.generation, natal_build_id=ctx.natal_build_id,
                convention_id=ctx.convention.convention_id,
                method_id='sudarshana_bphs74_candidate/1', admission='candidate_only',
                method_qualification=payload.method_qualification, operator_role=payload.operator_role,
                value=None, adapter_fingerprint=payload.upstream_fingerprint['digest'],
                periods=periods, frames=[judge_period(p,evidence) for p in periods if p['level_n']==1])
