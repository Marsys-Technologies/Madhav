"""KA-3a independent literals plus the judge oracle; missing/simplified sweeps fail."""
from copy import deepcopy
from datetime import datetime, timezone
from importlib import import_module
import json
from pathlib import Path

import pytest

from services.gochara_rules.vedha_derive import NODES_UNDECIDED, derive_vedha as _derive_vedha, pairs_from_rows
from services.kala_core.sky.coverage import coverage_of

# SR-OD1 C1: this asset's sweep has not adopted ND-NODE-VEDHA (a node in the vedha house obstructs); its cross-check derivation keeps
# the pre-ruling reading until the asset is re-elevated, so every oracle call below asks for it by name
def derive_vedha(*a, **k):
    return _derive_vedha(*a, nodes=NODES_UNDECIDED, **k)

ROWS = json.loads((Path(__file__).parents[1] / 'gochara_rules/fixtures/l0_vedha_rows_2026_10_02.json').read_text())
A, B, C, D = [f'2025-01-{day:02d}T00:00:00+00:00' for day in (1, 3, 5, 7)]
BODIES = ('Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu')


def api():
    # Missing implementation is an assertion failure during the red phase.
    from importlib.util import find_spec
    assert find_spec('services.kala_core.overlays') is not None, 'KA-3a overlays missing'
    return import_module('services.kala_core.overlays')


def residence():
    return {g: [(2, A, D)] for g in BODIES}


def test_house_partition_literal_precedence_and_independent_oracle():
    r = residence()
    r['Mars'] = [(7, B, C), (2, C, D)]  # Aquarius Moon: vedha house 9 = Libra (7)
    r['Rahu'] = [(7, A, D)]
    r['Saturn'] = [(7, A, D)]  # Sun exception, must never appear
    result = api().house_intervals('Sun', 3, (A, D), moon_sign=11, residence=r, pairs=pairs_from_rows(ROWS))
    assert [(x['t_in'], x['t_out'], x['state'], x['reason']) for x in result] == [
        (A, B, 'unqualified', 'obstructor_residence_unknown'),
        (B, C, 'active', None), (C, D, 'unqualified', 'node_obstruction_undecided')]
    assert result == derive_vedha('Sun', 3, (A, D), moon_sign=11, residence=r, pairs=pairs_from_rows(ROWS))['segments']
    assert result[0]['reasons'] == ['obstructor_residence_unknown', 'node_obstruction_undecided']
    assert result[1]['obstructors'] == ['Mars']


@pytest.mark.parametrize('primary,house,scope', [('Sun', 3, 'excluding_on_demand_moon_obstruction'), ('Mercury', 2, None)])
def test_moon_excluded_and_inactivity_scope(primary, house, scope):
    r = residence()
    r['Moon'] = [(7, A, D)]
    got = api().house_intervals(primary, house, (A,D), moon_sign=11, residence=r, pairs=pairs_from_rows(ROWS))
    assert [s['state'] for s in got] == ['inactive']
    assert got[0]['scope'] == scope


def test_each_node_gap_and_cited_obstruction_overrides_all_unknowns():
    for g in BODIES:
        r = residence(); r[g] = []
        got = api().house_intervals('Sun', 3, (A,D), moon_sign=11, residence=r, pairs=pairs_from_rows(ROWS))
        if g in ('Sun', 'Saturn'):
            assert got[0]['state'] == 'inactive'
        else:
            assert got[0]['state'] == 'unqualified'
            assert got[0]['reason'] == ('node_residence_unknown' if g in ('Rahu','Ketu') else 'obstructor_residence_unknown')
        r['Venus'] = [(7,A,D)]
        assert api().house_intervals('Sun',3,(A,D),moon_sign=11,residence=r,pairs=pairs_from_rows(ROWS))[0]['state'] == 'active'


def test_timezone_nonfinite_overlapping_spans_refused():
    for spans in ([(2,D,A)], [(2,A,C),(3,B,D)], [(True,A,D)], [(2,'2025-01-01',D)]):
        r = residence(); r['Mars'] = spans
        with pytest.raises(ValueError):
            api().house_intervals('Sun',3,(A,D),moon_sign=11,residence=r,pairs=pairs_from_rows(ROWS))


def bundle(**kw):
    args = dict(chart_id='00000000-0000-0000-0000-000000000001', generation='candidate-1',
        ayanamsha_id='lahiri_chitrapaksha', natal_build_id='00000000-0000-0000-0000-000000000002',
        janma_fact={'fact_id':'moon-ref','fact_value_num':300.0},
        coverage=coverage_of((2460676.5,2460682.5),(2460676.5,2460682.5), backend='swieph',convention_id='test'),
        residence={**residence(), 'Mercury':[(11,A,D)], 'Venus':[(5,A,D)], 'Jupiter':[(11,A,D)]}, pairs_rows=ROWS, nakshatra_residence={}, latta_rules=[], enrichment=None)
    args.update(kw)
    return import_module('services.ka_vedha_gochara.candidate').build_candidate_payload(**args)


def test_zero_intervals_preserve_three_headers_and_honest_disclosures():
    api()
    got = bundle()
    assert got.intervals == ()
    headers = {r['vedha_kind']: r for r in got.headers}
    assert set(headers) == {'house_vedha','latta','sarvatobhadra'}
    assert headers['house_vedha']['coverage']['search_state'] == 'searched'
    assert headers['house_vedha']['payload']['viparita'] == {'applied':False,'reason':'not applied — no served source'}
    assert headers['sarvatobhadra']['null_reason'] == 'information_unavailable'
    assert headers['sarvatobhadra']['method_qualification'] is None
    assert headers['latta']['payload']['ketu_gap'] == 'information_unavailable'
    assert headers['latta']['payload']['enrichment']['null_reason'] == 'information_unavailable'


def test_coverage_outside_horizon_is_unsearched_and_fingerprint_tracks_inputs():
    api()
    cov = coverage_of((2460000.5,2460006.5),(2460676.5,2460682.5),backend='swieph',convention_id='test')
    got = bundle(coverage=cov)
    assert got.intervals == ()
    assert got.headers[0]['coverage']['search_state'] == 'unsearched'
    assert got.headers[0]['coverage']['gaps'] == [[2460000.5,2460006.5]]
    one = bundle(); changed = residence(); changed['Mars'] = []
    assert one.headers[0]['upstream_fingerprint'] != bundle(residence=changed).headers[0]['upstream_fingerprint']
    assert one.headers[0]['upstream_fingerprint'] != bundle(natal_build_id='different').headers[0]['upstream_fingerprint']


def test_sourced_latta_and_enrichment_never_apply_severity():
    api()
    rule={'graha':'Sun','count_from_graha':12,'direction':'forward','source_citation':'Phaladeepika PG339', 'verse_ref':'Adh.XXVI PG338-339 Sloka 42-44'}
    enrichment={'passage':'Literal supplied passage from the source.', 'locator':'phaladeepika:PG340:C1', 'verses':'XXVI.47-48'}
    got=bundle(latta_rules=[rule],nakshatra_residence={'Sun':[(12,A,D)]},enrichment=enrichment)
    assert len(got.intervals)==1  # natal longitude 300 -> nakshatra 23, 12+11=23
    row=got.intervals[0]
    assert row['vedha_kind']=='latta' and row['source_qualification']=='verse_cited'
    assert row['detail']['source_nakshatra']==12 and row['detail']['target_nakshatra']==23
    h=next(r for r in got.headers if r['vedha_kind']=='latta')
    assert h['payload']['enrichment']['applied_to_computation'] is False
    assert h['payload']['enrichment']['passage']==enrichment['passage']
    assert 'concurrent_latta_count' not in json.dumps(h)
    with pytest.raises(ValueError):
        bundle(latta_rules=[{**rule,'graha':'Ketu'}])


def test_per_instant_offset_uses_each_real_jd_across_century():
    from services.kala_core.ayanamsha import sidereal_offset
    m=api()
    jds=(2415020.5,2451544.5)
    got=m.sidereal_samples([(j,30.0) for j in jds], 'lahiri_chitrapaksha')
    assert abs(got[0][1]-got[1][1]) > 1.0
    assert [v for _,v in got] == pytest.approx([(30-sidereal_offset(j))%360 for j in jds],abs=1e-10)


def test_overlapping_unknown_boundary_inside_active_is_preserved_for_oracle_equality():
    r=residence(); r['Mars']=[(7,A,D)]; r['Venus']=[(2,A,B),(2,C,D)]
    got=api().house_intervals('Sun',3,(A,D),moon_sign=11,residence=r,pairs=pairs_from_rows(ROWS))
    assert got==derive_vedha('Sun',3,(A,D),moon_sign=11,residence=r,pairs=pairs_from_rows(ROWS))['segments']
    assert [(s['t_in'],s['t_out']) for s in got]==[(A,B),(B,C),(C,D)]


def test_header_discloses_exact_residence_holes_and_unavailable_not_clean():
    api()
    r=residence(); r['Mars']=[(2,A,B),(2,C,D)]
    got=bundle(residence=r)
    h=got.headers[0]
    assert h['coverage']['residence_gaps']['Mars']==[[B,C]]
    assert h['coverage']['search_state']=='partial'
    assert h['coverage']['complete'] is False
    assert h['null_reason']=='information_unavailable'


def test_sky_initial_position_and_exact_ingress_produce_half_open_residences():
    from types import SimpleNamespace
    from services.kala_core.sky import SkyResult
    from services.kala_core.sky.ephemeris import EphemerisAnswer, BodyPosition
    coverage=coverage_of((2460676.5,2460682.5),(2460676.5,2460682.5),backend='swieph',convention_id='test')
    initial_coverage=coverage_of((2460676.5,2460676.5),(2460676.5,2460682.5),backend='swieph',convention_id='test')
    initial=SkyResult((EphemerisAnswer(2460676.5,'UT','swiss_instant','swieph',0,'flags','mean','lahiri_chitrapaksha',24,'test',
                                     (BodyPosition('Sun',29,1),)),),initial_coverage)
    events=SkyResult((SimpleNamespace(body='Sun',relation='sign_ingress',jd=2460678.5,cell_after=1),),coverage)
    assert api().sky_residences(events,initial,'Sun')==((1,A,B),(2,B,D))
    with pytest.raises(ValueError,match='coverage start'):
        wrong=SkyResult((__import__('dataclasses').replace(initial.values[0],jd=2460677.5),),initial_coverage)
        api().sky_residences(events,wrong,'Sun')


@pytest.mark.parametrize('primary,house',sorted(pairs_from_rows(ROWS)))
def test_every_cited_pair_matches_independent_derivation(primary,house):
    # Planted varied residence/crossing/gap patterns, never a second pair map.
    r={g:[(1,A,B),(7,B,C),(2,C,D)] for g in BODIES}
    r['Mars']=[(7,A,B),(2,C,D)]
    r['Ketu']=[(1,A,C)]
    assert api().house_intervals(primary,house,(A,D),moon_sign=11,residence=r,pairs=pairs_from_rows(ROWS)) == derive_vedha(
        primary,house,(A,D),moon_sign=11,residence=r,pairs=pairs_from_rows(ROWS))['segments']


def test_unbound_dispatch_does_not_require_any_database_schema():
    from types import SimpleNamespace
    from services.ka_vedha_gochara.writer import KaVedhaGocharaWriter
    result=KaVedhaGocharaWriter().run(SimpleNamespace(db_conn=None,build_id=None,config={'chart_id':'test-chart'},dry_run=False))
    assert result.rows_inserted==0
