"""BPHS 74 candidate method; literal F1 fixtures, no served admission."""
from dataclasses import replace
from datetime import date
from importlib import import_module
import importlib.util

import pytest

from services.kala_core.clocks.methods import ClockFact
from services.kala_core.overlays.contested import AdapterContext
from services.kala_core.sky import SkyConvention, coverage_of
from services.ka_sudarshana_varsha.candidate import build_candidate

CONVENTION=SkyConvention()
LO,HI=2460676.5,2461041.5


def api():
    name='services.ka_sudarshana_varsha.method'
    assert importlib.util.find_spec(name), 'BPHS 74 candidate judge method missing'
    return import_module(name)


def payload(signs=('Aries','Leo','Sagittarius')):
    facts=tuple(dict(fact_id=s.lower()+'-sign',fact_subject=s,fact_key='sign',fact_value_text=v)
                for s,v in zip(('LAGNA','MOON','SUN'),signs))
    ctx=AdapterContext('chart-a','candidate-1','natal-a',CONVENTION,facts)
    coverage=coverage_of((LO,HI),(LO,HI),backend='swieph',convention_id=CONVENTION.convention_id)
    return build_candidate(ctx=ctx,birth_date=date(2025,1,1),years=(1,),coverage=coverage,year_anchor='civil_birthday')


def influence(graha='Jupiter',nature='benefic',strength=10.,unit='rupas',**changes):
    args=dict(graha=graha,relationship_id='f1-'+graha,source='F1:fixture; BPHS 74.7-16',
              nature=ClockFact(nature,(graha+'-nature',)),
              strength=ClockFact(strength,(graha+'-strength',)),strength_unit=unit)
    args.update(changes)
    return api().Influence(**args)


def snapshot(p=None,**changes):
    p=p or payload()
    planted={0:'Jupiter',4:'Venus',8:'Mercury'}
    houses=tuple(api().HouseEvidence(sign_idx=i,occupants=(influence(planted[i]),) if i in planted else (),aspects=(),lord=None,
                                    occupancy_complete=True,aspects_complete=True) for i in range(12))
    args=dict(chart_id=p.context.chart_id,generation=p.context.generation,
              natal_build_id=p.context.natal_build_id,convention_id=CONVENTION.convention_id,
              at_jd=p.entries[0]['t_in'],houses=houses,source_id='f1-snapshot-1')
    args.update(changes)
    return api().F1Snapshot(**args)


def house_judgment(house,**changes):
    p=payload(); s=snapshot(p,**changes)
    houses=list(s.houses); houses[0]=house
    result=api().evaluate_candidate(p,year=1,evidence=replace(s,houses=tuple(houses)))
    return result['frames'][0]['houses'][0]


def house(occupants=(),aspects=(),lord=None,**changes):
    args=dict(sign_idx=0,occupants=occupants,aspects=aspects,lord=lord,
              occupancy_complete=True,aspects_complete=True)
    args.update(changes)
    return api().HouseEvidence(**args)


def test_three_distinct_frames_can_reach_same_conclusion_for_real_reasons():
    p=payload(); result=api().evaluate_candidate(p,year=1,evidence=snapshot(p))
    assert len(result['frames'])==3
    assert [f['active_sign_idx'] for f in result['frames']]==[0,4,8]
    assert all(len(f['houses'])==12 for f in result['frames'])
    assert all(f['houses'][0]['conclusion']=='favorable' for f in result['frames'])
    assert all(f['houses'][0]['reason']=='benefic_majority' for f in result['frames'])
    assert [f['houses'][0]['relationship_ids'] for f in result['frames']]==[['f1-Jupiter'],['f1-Venus'],['f1-Mercury']]
    assert all(f['coverage']=='partial' for f in result['frames'])
    assert result['method_qualification']=='method_contested' and result['operator_role']=='testimony'
    assert result['admission']=='candidate_only' and result['value'] is None
    assert 'tri_lagna_convergence' not in repr(result) and 'agreement' not in result
    assert p.entries[0]['judgment'] is None  # persisted geometry remains conclusion-free


@pytest.mark.parametrize('signs',[
    ('Aries','Aries','Leo'), ('Aries','Leo','Aries'), ('Aries','Leo','Leo'), ('Aries','Aries','Aries'),
])
def test_coincident_frames_are_judged_once_from_birth_chart(signs):
    p=payload(signs); result=api().evaluate_candidate(p,year=1,evidence=snapshot(p))
    assert len(result['frames'])==1 and result['frames'][0]['frame']=='birth_chart'
    assert result['frames'][0]['active_sign_idx']==0
    assert len(result['periods'])==1885
    assert {r['frame'] for r in result['periods']}=={'birth_chart'}


@pytest.mark.parametrize('occupants,expected,reason',[
    (('b','b','m'),'favorable','benefic_majority'),
    (('b','m','m'),'unfavorable','malefic_majority'),
])
def test_counts_decide_before_strength(occupants,expected,reason):
    bodies=('Jupiter','Venus','Saturn')
    refs=tuple(influence(g,'benefic' if n=='b' else 'malefic',1000. if n=='m' else 1.)
               for g,n in zip(bodies,occupants))
    result=house_judgment(house(occupants=refs))
    assert (result['conclusion'],result['reason'])==(expected,reason)
    assert set(result['fact_ids']) >= {'Jupiter-nature','Venus-nature','Saturn-nature','lagna-sign'}


@pytest.mark.parametrize('a,b,expected',[(20.,10.,'favorable'),(10.,20.,'unfavorable'),(10.,10.,'mixed')])
def test_equal_counts_use_referenced_like_unit_strength(a,b,expected):
    result=house_judgment(house(occupants=(influence(strength=a),influence('Saturn','malefic',b))))
    assert result['conclusion']==expected and result['reason']=='strength_tie_break'
    assert set(result['fact_ids']) >= {'Jupiter-strength','Saturn-strength'}
    assert result['strength_reduction']=='sum_like_unit_f1_strength'


def test_missing_or_incommensurable_strength_never_guesses_a_tie():
    for strength,unit in [(None,'rupas'),(20.,'virupas')]:
        result=house_judgment(house(occupants=(influence(),influence('Saturn','malefic',strength,unit))))
        assert result['conclusion'] is None and result['null_reason']=='strength_unavailable'
    with pytest.raises(ValueError):
        house_judgment(house(occupants=(influence(),influence('Saturn','malefic',float('nan')))))


def test_occupants_then_aspects_then_lord_with_no_silent_fallback():
    jupiter=influence(); saturn=influence('Saturn','malefic')
    assert house_judgment(house(occupants=(jupiter,),aspects=(saturn,)))['conclusion']=='favorable'
    assert house_judgment(house(aspects=(saturn,),lord=jupiter))['conclusion']=='unfavorable'
    result=house_judgment(house(lord=jupiter))
    assert result['conclusion']=='favorable' and result['basis']=='lord'
    for h in (house(), house(aspects=(jupiter,),occupancy_complete=False),
              house(lord=jupiter,aspects_complete=False),
              house(occupants=(influence(nature=None),))):
        assert house_judgment(h)['conclusion'] is None


def test_sun_first_house_exception_is_frame_relative():
    p=payload(); s=snapshot(p)
    houses=list(s.houses)
    houses[0]=house(occupants=(influence('Sun','malefic'),))
    result=api().evaluate_candidate(p,year=1,evidence=replace(s,houses=tuple(houses)))
    lagna,moon=result['frames'][:2]
    assert lagna['houses'][0]['conclusion']=='favorable'
    assert moon['houses'][0]['conclusion']=='favorable'
    assert moon['houses'][8]['conclusion']=='unfavorable'


def test_commencement_conditions_are_cited_per_house_not_an_aggregate_vote():
    p=payload(); s=snapshot(p)
    result=api().evaluate_candidate(p,year=1,evidence=s)
    houses=result['frames'][0]['houses']
    assert [h['house'] for h in houses if h['commencement']['benefic_in_1_4_7_10_5_9_8']]==[1,5,9]
    assert houses[0]['commencement']['benefic_effect']=='favorable'
    for sign in (5,11):
        modified=list(s.houses)
        modified[sign]=replace(modified[sign],occupants=(influence('Moon'),))
        judged=api().evaluate_candidate(p,year=1,evidence=replace(s,houses=tuple(modified)))
        assert judged['frames'][0]['houses'][sign]['commencement']['benefic_effect']=='unfavorable'
    assert all(h['commencement']['source']=='BPHS 74.24-26' for h in houses)
    node=house_judgment(house(occupants=(influence('Rahu','malefic'),)))
    assert node['commencement']['node_only_harm'] is True
    planted={2:'Mars',5:'Saturn',10:'Sun'}
    s=replace(s,houses=tuple(replace(h,occupants=(influence(planted[h.sign_idx],'malefic'),) if h.sign_idx in planted else ()) for h in s.houses))
    houses=api().evaluate_candidate(p,year=1,evidence=s)['frames'][0]['houses']
    assert [h['house'] for h in houses if h['commencement']['malefic_in_3_6_11']]==[3,6,11]


def test_nested_period_judgment_requires_evidence_at_its_own_commencement():
    p=payload(); s=snapshot(p)
    result=api().evaluate_candidate(p,year=1,evidence=s)
    month=next(r for r in result['periods'] if r['frame']=='lagna' and r['ordinal_path']==[2])
    with pytest.raises(ValueError,match='commencement'):
        api().judge_period(month,s)
    judged=api().judge_period(month,replace(s,at_jd=month['t_in']))
    assert judged['active_sign_idx']==1 and len(judged['houses'])==12


@pytest.mark.parametrize('change',[
    {'chart_id':'other'}, {'generation':'other'}, {'natal_build_id':'other'},
    {'convention_id':'other'}, {'at_jd':LO+1}, {'source_id':''},
])
def test_cross_pin_or_wrong_epoch_f1_is_refused(change):
    p=payload()
    with pytest.raises(ValueError): api().evaluate_candidate(p,year=1,evidence=snapshot(p,**change))


def test_incomplete_coverage_does_not_construct_unsearched_year():
    p=payload()
    with pytest.raises(ValueError,match='year|coverage'):
        api().evaluate_candidate(p,year=2,evidence=snapshot(p))
    with pytest.raises(ValueError,match='integrity|fingerprint'):
        api().evaluate_candidate(replace(p,entries=()),year=1,evidence=snapshot(p))


def test_duplicate_influencers_or_signs_cannot_manufacture_a_majority():
    p=payload(); s=snapshot(p)
    for houses in ((s.houses[0],)*12,
                   (replace(s.houses[0],occupants=(influence(),influence())),*s.houses[1:])):
        with pytest.raises(ValueError): api().evaluate_candidate(p,year=1,evidence=replace(s,houses=houses))


@pytest.mark.parametrize('house_number,expected',[
    (1,True),(2,False),(3,False),(4,True),(5,True),(6,False),
    (7,True),(8,True),(9,True),(10,True),(11,False),(12,False),
])
def test_each_listed_commencement_house_is_measured(house_number,expected):
    p=payload(); s=snapshot(p)
    houses=tuple(replace(h,occupants=(influence(),) if h.sign_idx==house_number-1 else ()) for h in s.houses)
    result=api().evaluate_candidate(p,year=1,evidence=replace(s,houses=houses))
    condition=result['frames'][0]['houses'][house_number-1]['commencement']
    assert condition['benefic_in_1_4_7_10_5_9_8'] is expected
    assert condition['benefic_effect']==('unfavorable' if house_number in (6,12) else 'favorable')


def test_decimal_strength_from_postgres_remains_comparable():
    from decimal import Decimal
    result=house_judgment(house(occupants=(influence(strength=Decimal('11.5')),
                                           influence('Saturn','malefic',Decimal('10.0')))))
    assert result['conclusion']=='favorable' and result['reason']=='strength_tie_break'


def test_unreferenced_nature_is_unknown_even_for_the_sun():
    result=house_judgment(house(occupants=(replace(influence('Sun','malefic'),nature=ClockFact('malefic',())),)))
    assert result['conclusion'] is None
