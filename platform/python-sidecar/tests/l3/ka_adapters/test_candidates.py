"""KA-3b: wrong epoch, fabricated qualification and authored scoring must fail."""
from datetime import date, datetime, timezone
from importlib import import_module
from pathlib import Path

import pytest

from services.gochara_kernel.arcs import build_arc_index
from services.kala_core.sky import SkyConvention, coverage_of, ephemeris_at, boundary_events
from services.gochara_rules.nature import agent_nature

CHART='00000000-0000-0000-0000-000000000001'
NATAL='00000000-0000-0000-0000-000000000002'
BUILD='00000000-0000-0000-0000-000000000003'
CONVENTION=SkyConvention()
LO=2460676.5
HI=LO+90
EPHE='/Users/Dev/kalayantra/ephe'
FAMILIES=('moorti_nirnaya','kota_chakra','tithi_pravesha','sudarshana_varsha')
MOORTI=[{'nakshatra_offset':k,'moorti_name':f'source-{k}', 'quality_tier':1,'phala_brief':'verbatim', 'classical_citation':'legacy reference'} for k in range(1,28)]
RINGS=[{'ring_name':('stambha' if k<=3 else 'bahya'), 'ring_position':k,'table_version':'v01','citation':'legacy extension'} for k in range(1,28)]


def api(family):
    import importlib.util
    name=f'services.ka_{family}.candidate'
    assert importlib.util.find_spec(name), f'{family} candidate adapter missing'
    return import_module(name)


def context(**changes):
    m=api('moorti_nirnaya')
    common=dict(chart_id=CHART,generation='candidate-1',natal_build_id=NATAL,convention=CONVENTION,
                facts=({'fact_id':'moon-ref','fact_subject':'MOON','fact_key':'longitude_sidereal', 'fact_value_num':300.0},))
    common.update(changes)
    return m.AdapterContext(**common)


def cov(lo=LO,hi=HI,source=(LO,HI)):
    return coverage_of((lo,hi),source,backend='swieph',convention_id=CONVENTION.convention_id)


@pytest.fixture(scope='module')
def indexes():
    import os
    path=os.environ.get('SE_EPHE_PATH',EPHE)
    out={}
    jds=[LO+k for k in range(91)]
    for body in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'):
        lons=[]
        for jd in jds:
            answer=ephemeris_at(jd,CONVENTION,bodies=(body,),ephe_path=path)
            assert answer.available, 'pinned Swiss corpus required'
            lons.append(answer.values[0].position(body).longitude_deg)
        out[body]=build_arc_index(body,jds,lons)
    return out


def moorti(indexes,**changes):
    args=dict(ctx=context(),indexes={'Sun':indexes['Sun']},horizon=(LO,HI),moorti_rows=MOORTI)
    args.update(changes)
    return api('moorti_nirnaya').build_candidate(**args)


def test_moorti_ingress_roots_and_moon_share_exact_sky_epoch(indexes):
    p=moorti(indexes)
    roots=boundary_events(indexes['Sun'],'Sun',['sign_ingress'],(LO,HI),CONVENTION.convention_id).values
    observed=[r for r in p.entries if r['ingress_jd'] is not None]
    assert observed and [r['ingress_jd'] for r in observed]==[r.jd for r in roots]
    for row in observed:
        moon=ephemeris_at(row['ingress_jd'],CONVENTION,bodies=('Moon',)).values[0]
        nak=int(moon.position('Moon').longitude_deg/(360/27))
        offset=(nak-22)%27+1
        assert row['moon_evaluated_jd']==row['ingress_jd']
        assert row['moon_nakshatra_idx']==nak and row['nakshatra_offset']==offset
        assert row['moorti_name']==f'source-{offset}'
        assert row['source_status']=='uncited_legacy'
        assert row['method_id']=='moorti_nakshatra_27'
        assert row['epoch_correction']=='sky_UT_instant; legacy epoch preserved separately'
    assert p.method_qualification=='method_contested' and p.operator_role=='testimony'
    assert p.entries[0]['moorti_name'] is None  # clipped residence is not an ingress


def test_moorti_missing_source_is_not_guessed(indexes):
    p=moorti(indexes,moorti_rows=[])
    assert p.null_reason=='information_unavailable' and not p.entries


def test_kota_occupancy_shared_nature_and_null_direction(indexes):
    p=api('kota_chakra').build_candidate(ctx=context(),indexes=indexes,horizon=(LO,HI),ring_rows=RINGS)
    assert p.method_qualification=='uncited_extension'
    assert p.entries
    for row in p.entries:
        sky=ephemeris_at(row['t_in'],CONVENTION,bodies=tuple(indexes)).values[0]
        sun=sky.position('Sun').longitude_deg; moon=sky.position('Moon').longitude_deg
        merc=sky.position('Mercury').longitude_deg
        joined=any(int(merc//30)==int(sky.position(g).longitude_deg//30)
                   for g in ('Sun','Mars','Saturn','Rahu','Ketu')) or (
                agent_nature('Moon',sun_lon=sun,moon_lon=moon)=='malefic' and int(merc//30)==int(moon//30))
        expected=agent_nature(row['graha'],sun_lon=sun,moon_lon=moon,joined_to_malefic=joined)
        assert row['nature']==expected
        assert row['direction_of_motion'] is None
        assert row['source_status']=='uncited_extension'
        assert row['ring']==('stambha' if row['count_from_janma']<=3 else 'bahya')
        assert not {'posture','severity','attack','score'} & row.keys()
    # A Moon nature boundary inside a nakshatra residence must become an edge.
    moon_rows=[r for r in p.entries if r['graha']=='Moon']
    assert {'benefic','malefic'} <= {r['nature'] for r in moon_rows}


def test_kota_incomplete_nature_operands_stay_unqualified(indexes):
    p=api('kota_chakra').build_candidate(ctx=context(),indexes={'Mercury':indexes['Mercury']},horizon=(LO,HI),ring_rows=RINGS)
    assert p.entries and {r['nature'] for r in p.entries}=={'unqualified'}


def test_tithi_names_legacy_moon_return_and_exposes_one_coverage():
    p=api('tithi_pravesha').build_candidate(ctx=context(),birth_dt=datetime(1984,2,5,5,13,tzinfo=timezone.utc),
        years=(42,),coverage=cov(LO,LO+365,source=(LO,LO+365)))
    assert p.entries
    row=p.entries[0]
    assert row['method_id']=='moon_longitude_return' and row['source_status']=='uncited_legacy'
    moon=ephemeris_at(row['return_jd'],CONVENTION,bodies=('Moon',)).values[0].position('Moon').longitude_deg
    assert abs((moon-300+180)%360-180)<.01
    assert row['phase_return'] is None
    assert row['annual_object_identity_admitted'] is False
    overlay=import_module('services.kala_core.overlays.contested')
    now=overlay.testimony(p,at=row['return_jd'],view='NOW')
    ahead=overlay.testimony(p,at=row['return_jd'],view='AHEAD')
    assert now==ahead and now['coverage']==p.coverage
    assert now['value'] is None and now['operator_role']=='testimony'


def test_uncovered_tithi_never_uses_anniversary_as_return():
    p=api('tithi_pravesha').build_candidate(ctx=context(),birth_dt=datetime(1984,2,5,tzinfo=timezone.utc),
        years=(42,),coverage=cov(LO,LO+365,source=None))
    assert not p.entries and p.null_reason=='information_unavailable'


def sign_context(**changes):
    facts=tuple({'fact_id':s.lower()+'-sign','fact_subject':s,'fact_key':'sign','fact_value_text':v}
                for s,v in [('LAGNA','Aries'),('MOON','Aries'),('SUN','Capricorn')])
    return context(facts=facts,**changes)


def sudarshana(**changes):
    args=dict(ctx=sign_context(),birth_date=date(1984,2,5),years=(42,54),coverage=cov(LO,LO+5000,source=(LO,LO+5000)),year_anchor='civil_birthday')
    args.update(changes)
    return api('sudarshana_varsha').build_candidate(**args)


def test_sudarshana_frames_period_12_convention_without_judgment():
    p=sudarshana()
    assert len(p.entries)==2
    a,b=p.entries
    assert a['frames']==b['frames']
    assert a['frames']=={'lagna':5,'moon':5,'sun':2}
    assert a['judgment'] is None and a['coincident_frame_policy']=='birth_chart_only'
    assert a['year_anchor']=='civil_birthday' and a['anchor_source_status']=='declared_convention'
    assert 'tri_lagna_convergence' not in a
    assert a['frame_fact_ids']=={'lagna':'lagna-sign','moon':'moon-sign','sun':'sun-sign'}
    with pytest.raises(ValueError,match='anchor|convention'):
        sudarshana(year_anchor='solar_return')


@pytest.mark.parametrize('family',FAMILIES)
def test_missing_l1_fact_is_explicit_unavailable(family,indexes):
    ctx=context(facts=())
    if family=='moorti_nirnaya': p=moorti(indexes,ctx=ctx)
    elif family=='kota_chakra': p=api(family).build_candidate(ctx=ctx,indexes=indexes,horizon=(LO,HI),ring_rows=RINGS)
    elif family=='tithi_pravesha': p=api(family).build_candidate(ctx=ctx,birth_dt=datetime(1984,2,5,tzinfo=timezone.utc),years=(42,),coverage=cov())
    else: p=sudarshana(ctx=ctx)
    assert not p.entries and p.null_reason=='information_unavailable'
    assert p.external_computation_required and p.coverage['search_state']=='unsearched'


@pytest.mark.parametrize('generation',['legacy','published','current','retained',''])
def test_candidate_never_aliases_published_generation(generation):
    with pytest.raises(ValueError,match='candidate|generation'): context(generation=generation)


def test_coverage_fingerprint_and_overlay_identity_refuse_drift(indexes):
    from dataclasses import replace
    p=moorti(indexes)
    changed=moorti(indexes,moorti_rows=[{**r,'phala_brief':'changed'} for r in MOORTI])
    assert p.upstream_fingerprint!=changed.upstream_fingerprint
    overlay=import_module('services.kala_core.overlays.contested')
    for kwargs in ({'chart_id':NATAL},{'generation':'other'},{'fingerprint':'wrong'}):
        with pytest.raises(ValueError,match='identity|fingerprint'): overlay.testimony(p,at=LO+1,**kwargs)
    assert overlay.testimony(p,at=HI)['null_reason']=='information_unavailable'
    # Forged mutable nested output must be caught before it can reach a consumer.
    with pytest.raises(ValueError,match='fingerprint|integrity'):
        overlay.testimony(replace(p,entries=({'score':1},)),at=LO+1)


def test_no_candidate_reader_bypasses_overlays(tmp_path):
    overlay=import_module('services.kala_core.overlays.contested')
    for text in ('SELECT * FROM kala_kota_chakra_candidate',
                 'SELECT * FROM public."kala_kota_chakra_candidate"',
                 'from services.ka_moorti_nirnaya.candidate import build_candidate'):
        path=tmp_path/'bad_consumer.py'; path.write_text(text)
        with pytest.raises(ValueError,match='overlays'): overlay.lint_consumers([path])
    root=Path(__file__).resolve().parents[3]
    paths=[p for base in ('services','pipeline') for p in (root/base).rglob('*.py')
           if not any(f'ka_{f}' in p.parts for f in FAMILIES) and 'overlays' not in p.parts
           and p != root/'services/kala_core/idempotency/__init__.py']
    repo=root.parents[1]
    paths += [p for base in ('platform/src/lib/retrieval','platform-mcp/src')
              for p in (repo/base).rglob('*.ts')]
    overlay.lint_consumers(paths)


def test_partial_sky_coverage_never_claims_complete(indexes):
    p=moorti(indexes,horizon=(LO-10,HI+10))
    assert p.coverage['complete'] is False and p.coverage['search_state']=='partial'
    assert p.coverage['gaps']==((LO-10,LO),(HI,HI+10))
    assert p.null_reason=='information_unavailable'


def test_missing_computation_is_not_reported_fully_searched(indexes):
    from services.kala_core.overlays.contested import testimony
    p=moorti(indexes,moorti_rows=[])
    assert p.coverage['complete'] is False and p.coverage['search_state']=='unsearched'
    clipped=moorti(indexes)
    assert testimony(clipped,at=LO)['null_reason']=='information_unavailable'


def test_noncomputable_convention_does_not_get_swiss_qualification(indexes):
    c=context(convention=SkyConvention(node_model='true'))
    p=moorti(indexes,ctx=c)
    assert not p.entries and p.null_reason=='information_unavailable'
    assert p.coverage['complete'] is False
