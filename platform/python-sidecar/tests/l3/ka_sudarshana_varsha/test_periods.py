"""ALGO 3.16: a wrong divisor, frame policy or lineage must fail here."""
from importlib import import_module
import importlib.util

import pytest


def clocks():
    name = 'services.kala_core.clocks.sudarshana'
    assert importlib.util.find_spec(name), 'candidate Sudarshana F2 construction is missing'
    return import_module(name)


def rows(**changes):
    args = dict(chart_id='chart-a', generation='candidate-1', natal_build_id='natal-a',
                convention_id='lahiri-pin', varsha_year=2, t_in=1000., t_out=1366.,
                natal_signs={'lagna':0, 'moon':4, 'sun':8},
                frame_fact_ids={'lagna':'lagna-sign', 'moon':'moon-sign', 'sun':'sun-sign'},
                year_anchor='civil_birthday')
    args.update(changes)
    return clocks().period_rows(**args)


def test_all_four_depths_partition_and_preserve_classical_nominal_durations():
    result = rows()
    assert len(result) == 5655  # 3 * (1 + 12 + 144 + 1728)
    root = next(r for r in result if r['frame']=='lagna' and r['level_n']==1)
    assert (root['sign_idx'], root['t_in'], root['t_out']) == (1,1000.,1366.)
    months = [r for r in result if r['parent_period_id']==root['period_id']]
    assert len(months)==12
    assert [r['sign_idx'] for r in months]==[1,2,3,4,5,6,7,8,9,10,11,0]
    assert months[0]['t_out']==1030.5
    by_id={r['period_id']:r for r in result}
    for parent in result:
        children=[by_id[c] for c in parent['child_period_ids']]
        if not children: continue
        assert len(children)==12
        assert children[0]['t_in']==parent['t_in'] and children[-1]['t_out']==parent['t_out']
        assert all(a['t_out']==b['t_in'] for a,b in zip(children,children[1:]))
        assert all(c['t_in']<c['t_out'] for c in children)
    nominal={r['level_n']:r['nominal_days'] for r in result}
    assert nominal=={1:360.,2:30.,3:2.5,4:5/24}
    assert all(r['applicability_tags']==['annual'] and r['source']=='BPHS 74.21-23' for r in result)
    assert all(r['year_anchor']=='civil_birthday' and r['anchor_source_status']=='declared_convention' for r in result)
    assert all(r['fact_ids'] and 'tri_lagna_convergence' not in r for r in result)
    clocks().validate_f2_row(result)


@pytest.mark.parametrize('natal',[
    {'lagna':2,'moon':2,'sun':8}, {'lagna':2,'moon':4,'sun':2},
    {'lagna':2,'moon':4,'sun':4}, {'lagna':2,'moon':2,'sun':2},
])
def test_any_coincident_pair_emits_only_birth_chart_periods(natal):
    result=rows(natal_signs=natal)
    assert len(result)==1885
    assert {r['frame'] for r in result}=={'birth_chart'}
    assert {r['coincident_frame_policy'] for r in result}=={'birth_chart_only'}
    assert result[0]['sign_idx']==3
    assert set(result[0]['fact_ids'])=={'lagna-sign','moon-sign','sun-sign'}


def test_active_sign_repeats_after_twelve_years_with_distinct_period_identities():
    a=rows(varsha_year=1)
    b=rows(varsha_year=13)
    assert [(r['frame'],r['sign_idx']) for r in a]==[(r['frame'],r['sign_idx']) for r in b]
    assert not {r['period_id'] for r in a} & {r['period_id'] for r in b}


@pytest.mark.parametrize('changes',[
    {'t_out':1000.}, {'t_in':float('nan')}, {'natal_signs':{'lagna':12,'moon':4,'sun':8}},
    {'natal_signs':{'lagna':True,'moon':4,'sun':8}}, {'varsha_year':0},
    {'frame_fact_ids':{'lagna':'','moon':'m','sun':'s'}}, {'year_anchor':'solar_return'},
    {'generation':'published'}, {'natal_build_id':''},
])
def test_invalid_or_unpinned_inputs_are_refused(changes):
    with pytest.raises(ValueError): rows(**changes)
