"""G1a behavioral oracles: independently recomputed axes and operator roots.

Rule locators (no JH-parity oracle, CLAUDE.md §N.4):
* ALGO = 00_ARCHITECTURE/briefs/l3_families/
  KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md:300–308 (§3.13): uncited legacy
  mūrti has no admitted numeric bridge; D-PADMIT permits testimony only.
* ALGO :442–454 (§3.20): G1 formula, pinned axis/rarity, complete operator
  partition; 1023 nonidentity shifts + observation. Statistics and seeded
  coefficients are engineering conventions, never classical probabilities.
* PLAN = 00_ARCHITECTURE/briefs/l3_families/
  KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:282–285 (§6.2 items 4–5):
  scenario/risk-mask edges and shift seams survive every representation.
Classical vedha inputs trace to Phaladīpikā XXVI 3–8 via ALGO §3.12;
these consumer tests inherit supplied intervals, never re-judge a transit.
"""
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import hashlib
import json
import math

import pytest

from services.ka_kshetra import stage0_kinematics as S0, stage1_symbolization as S1
from services.ka_kshetra import stage4_field as S4, integrator


def test_birth_axis_across_epochs_offsets_and_fractional_days():
    from services.ka_kshetra.g1_inputs import birth_instant, field_days
    for iso, offset in [('1984-02-05T10:43:00', 5.5), ('2034-08-23T09:12:30', -4),
                        ('1952-01-01T00:00:00+09:00', 0)]:
        config = {'birth_params': {'datetime_iso': iso, 'tz_offset_hours': offset}}
        expected = datetime.fromisoformat(iso)
        if expected.tzinfo is None:
            expected = expected.replace(tzinfo=timezone(timedelta(hours=offset)))
        birth = birth_instant(config)
        assert birth == expected.astimezone(timezone.utc)
        sample = expected + timedelta(days=147, seconds=12345)
        assert field_days(sample, birth) == pytest.approx(147 + 12345 / 86400)
        assert field_days(birth, birth) == 0


def test_stage0_production_series_is_birth_relative(monkeypatch):
    from services.ka_kshetra.g1_inputs import birth_instant
    birth = birth_instant({'birth_params': {'datetime_iso': '1984-02-05T10:43:00', 'tz_offset_hours': 5.5}})
    class Conn:
        def cursor(self): return self
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def execute(self, *a): return self
        def fetchall(self): return [(birth.date(), 20., 0., 1.), (birth.date()+timedelta(days=1),21.,0.,1.)]
    monkeypatch.setattr(S0, '_sidereal_offset_series', lambda jds, ayan: [0.]*len(jds))
    result = S0.fetch_ephemeris_series(Conn(), 'Sun', birth.date(), birth.date()+timedelta(days=1), origin=birth)
    # ephemeris_daily is measured at noon UT, not at local birth midnight.
    assert result['t_days'][0] == pytest.approx((12*3600-5*3600-13*60)/86400)


def test_as_of_required_and_normalized():
    from services.ka_kshetra.g1_inputs import pinned_as_of
    with pytest.raises(ValueError, match='as_of'):
        pinned_as_of({})
    with pytest.raises(ValueError, match='offset'):
        pinned_as_of({'as_of':'2020-01-01T00:00:00'})
    assert pinned_as_of({'as_of':'2020-01-01T05:30:00+05:30'}) == datetime(2020,1,1,tzinfo=timezone.utc)


def test_suppression_adapters_and_effective_states():
    from services.ka_kshetra.g1_inputs import suppression_primitives
    birth=datetime(1984,2,5,tzinfo=timezone.utc)
    stamp=lambda day:(birth+timedelta(days=day)).isoformat()
    vedha=[{'graha':'Saturn','state':'active','t_in':stamp(10),'t_out':stamp(20),
            'vedha_kind':'house_vedha','detail':{'vedha_house':4},'source_ref':'v1'}]
    moorti=[{'graha':'Mars','t_in':2445735.5,'t_out':2445736.5,'moorti_name':'loha','quality_tier':4,'source_ref':'m1'}]
    states=[{'assertion_id':s,'effective_state':s,'interval_start':stamp(11),'interval_end':stamp(12),
             'event_class_id':'career','assertion':{'acceptance_scope':'fixture_only'}} for s in
            ('obstruction_in_force','obstruction_cancelled','obstruction_partly_cancelled','obstruction_contested','information_unavailable')]
    prims,gaps=suppression_primitives('chart',birth,vedha,moorti,states,allow_fixture=True)
    assert {'vedha','moorti_testimony','negative_space'} <= {p.primitive_kind for p in prims}
    active=[p for p in prims if p.primitive_kind=='negative_space']
    assert [p.source_pk for p in active] == ['obstruction_in_force']
    assert {g['reason'] for g in gaps} >= {'obstruction_partly_cancelled','obstruction_contested','information_unavailable'}
    env=S4.EnvelopeIndex([S4.Primitive(p.primitive_kind,p.subject,p.object_ref,p.polarity,p.class_label,
                       tuple(p.envelope),p.source_pk,p.source_fact_id,p.source_table) for p in prims],100)
    assert env.obstructions_at(11.5)
    assert active[0].t_start == 11
    assert active[0].class_label == 'event_class:career'


def primitive(kind, knots, subject='Saturn'):
    return S4.Primitive(kind,subject,None,'neutral',None,tuple(knots))


def test_full_operator_breakpoints_and_shift_seams():
    # The winning Moon contact switches at 3.7; min(Moon,Lagna) at 6.3.
    env=S4.EnvelopeIndex([
        primitive('contact_moon_ref',[(0,0),(10,1)]),
        primitive('contact_moon_ref',[(0,.74),(10,-.26)]),
        primitive('contact_lagna_ref',[(0,.63),(10,.63)])],10)
    points=env.breakpoints()
    assert any(abs(t-3.7)<1e-10 for t in points)
    assert any(abs(t-6.3)<1e-10 for t in points)
    shifted=env.circular_shift(2.1)
    assert {0.,10.} <= set(shifted.breakpoints())
    assert any(abs(t-1.6)<1e-10 for t in shifted.breakpoints())


def test_one_sided_discontinuities_and_reproducible_coefficients():
    def rate(t): return 1. if 3. <= t < 7. else 0.
    segs=integrator.build_segments([0,3,7,10],rate)
    assert [(s.t_start,s.t_end) for s in segs]==[(0,3),(3,7),(7,10)]
    assert [s.alpha for s in segs] == [0,1,0]
    assert all(s.gamma == 0 for s in segs)
    payload=lambda:json.dumps([vars(s) for s in integrator.build_segments([0,3,7,10],rate)],sort_keys=True)
    assert hashlib.sha256(payload().encode()).digest() == hashlib.sha256(payload().encode()).digest()


def test_rarity_uses_canonical_ayanamsha_and_discloses_it():
    from services.ka_kshetra.writer import KaKshetraWriter
    class Conn:
        description=None
        def cursor(self): return self
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def execute(self,sql,params): self.sql=sql; self.params=params
        def fetchall(self):
            return [{'fact_value_num':29.9 if 'lahiri_chitrapaksha' in self.params else 30.1}]
    conn=Conn(); writer=KaKshetraWriter(); writer._chart_id='chart'
    assert writer._natal_lagna_sign(conn)==1
    assert 'ayanamsha_id = %s' in conn.sql
    assert writer.rarity_convention()['ayanamsha_id']=='lahiri_chitrapaksha'


def test_ordinary_build_is_no_write_prebuild_containment():
    from services.ka_kshetra.writer import KaKshetraWriter
    class NoDB:
        def __getattr__(self,name): raise AssertionError('ordinary build touched DB: '+name)
    ctx=SimpleNamespace(config={'chart_id':'chart', 'birth_params':{'datetime_iso':'1984-02-05T10:43:00','tz_offset_hours':5.5}}, db_conn=NoDB(),dry_run=False,build_id='build')
    writer=KaKshetraWriter(); steps=writer.plan_substeps(ctx)
    assert len(steps)==1
    result=writer.run_substep(ctx,steps[0])
    assert result.rows_inserted==0
    assert 'pre-build' in result.notes


def test_production_clock_boundaries_share_birth_axis(monkeypatch):
    from services.ka_kshetra import stage3_clocks as S3
    from tests.l3._dasha_projection import emulated_projection
    # This oracle checks the birth axis after loading governed operands.
    monkeypatch.setattr(S3, 'execute_governed_dasha_query', emulated_projection)
    birth=datetime(1984,2,5,5,13,tzinfo=timezone.utc)
    class Conn:
        def execute(self,*a): return self
        def fetchall(self): return [{'dasha_row_id':'d1','level_n':1,'lord_graha':'Jupiter',
            'lord_sign':None,'parent_row_id':None,'start_iso':birth+timedelta(days=100.25),'duration_days':1000}]
    monkeypatch.setattr(S3.U,'fetch_sigma_t_days',lambda *a:(.1,'test'))
    monkeypatch.setattr(S3,'_system_sigma_t',lambda *a,**kw:(.1,'test'))
    rows=S3.compute_boundaries_for_system('chart','vimshottari',Conn(),
        birth_params={'datetime_iso':birth.isoformat(),'tz_offset_hours':5.5})
    assert rows[0].t_boundary==100.25


def test_analytic_path_keeps_kinematic_scenario_mask_edges():
    from services.ka_kshetra.dhara_sweep import assemble_knot_set
    ev=SimpleNamespace(horizon_days=10.,ladder={},envelopes=S4.EnvelopeIndex([],10),
                       extra_breakpoints=(2.37,4.13,6.71))
    assert {2.37,4.13,6.71} <= set(assemble_knot_set(ev))


def test_null_uses_the_full_shifted_reference_partition_and_statistics():
    from services.ka_kshetra import stage5_null as S5
    from services.ka_kshetra.contracts import PromisePrior
    ev=S4.FieldEvaluator(event_class='career',lifetime_count=1,promise=PromisePrior(.5),clocks=[],ladder={},
        envelopes=S4.EnvelopeIndex([primitive('contact_moon_ref',[(2.31,0),(2.37,1),(2.43,0)])],10),
        weights={'beta:x1':2.},horizon_days=10,extra_breakpoints=(4.13,))
    for delta in (0.,1.37,7.61):
        shifted=S5.replicate_evaluator(ev,delta)
        reference=shifted.build_segments()
        actual=S5._null_build_segments(shifted)
        assert [(s.t_start,s.t_end,s.alpha,s.gamma) for s in actual] == [(s.t_start,s.t_end,s.alpha,s.gamma) for s in reference]
        assert integrator.integrate(actual,0,10)==integrator.integrate(reference,0,10)
        assert S5.replicate_stats(ev,delta,10,buckets=(1,3),segments=actual)==S5.replicate_stats(ev,delta,10,buckets=(1,3),segments=reference)
        assert max(integrator.lambda_at(actual,t) for t in shifted.breakpoints()) > math.exp(ev.ln_lambda(0))


def test_candidate_uses_complete_reference_not_uncertified_compact_engine():
    from services.ka_kshetra.writer import _candidate_engine
    assert _candidate_engine() == 'sampled'


def test_numeric_parameters_have_source_locators_and_declared_provenance():
    from pathlib import Path
    from services.ka_kshetra.g1_provenance import numeric_constant_inventory
    rows=numeric_constant_inventory()
    assert {'P_FLOOR','RHO_MAX','DEFAULT_TAU','DEFAULT_MAX_DEPTH','STATION_BAND_BASE_DAYS'} <= {r['name'] for r in rows}
    root=Path(S4.__file__).parents[4]
    for row in rows:
        file,line=row['declaration'].rsplit(':',1)
        assert row['name'] in (root/file).read_text().splitlines()[int(line)-1]
        assert row['provenance']


def test_stage3_dispatch_passes_pinned_as_of_to_quality(monkeypatch):
    from services.ka_kshetra import stage3_clocks as S3
    seen={}
    def applicable(chart,conn,**kwargs): seen.update(kwargs); return []
    monkeypatch.setattr(S3,'applicable_systems',applicable)
    monkeypatch.setattr(S3,'write_clock_rows',lambda *args:0)
    ctx=SimpleNamespace(db_conn=object(),dry_run=False,config={'chart_id':'chart',
        'birth_params':{'datetime_iso':'1984-02-05T10:43:00+05:30'},'as_of':'1994-02-05T00:00:00+00:00'})
    S3.run_substep(ctx,SimpleNamespace(key='stage3:run'))
    assert seen['reference_dt']==datetime(1994,2,5,tzinfo=timezone.utc)


def test_unavailable_and_cancelled_masks_keep_edges_without_a_scalar():
    from services.ka_kshetra.g1_inputs import suppression_primitives
    birth=datetime(2001,1,1,tzinfo=timezone.utc)
    stamp=lambda d:birth+timedelta(days=d)
    prims,gaps=suppression_primitives('chart',birth,
        [{'graha':'Saturn','state':'unqualified','t_in':stamp(7.4),'t_out':stamp(8.6),'vedha_kind':'house_vedha','source_ref':'v'}],[],
        [{'assertion_id':'cancelled','effective_state':'obstruction_cancelled','interval_start':stamp(23.1),
          'interval_end':stamp(24.3),'event_class_id':'career','assertion':{'acceptance_scope':'fixture_only'}}],allow_fixture=True)
    env=S4.EnvelopeIndex([S4.Primitive(p.primitive_kind,p.subject,p.object_ref,p.polarity,p.class_label,
        tuple(p.envelope),p.source_pk,p.source_fact_id,p.source_table) for p in prims],100)
    assert {7.4,8.6,23.1,24.3} <= set(env.breakpoints())
    assert env.obstructions_at(8)=={} and env.obstructions_at(24)=={}


def test_lagna_contact_target_inherits_the_real_pinned_L1_key():
    class Conn:
        def execute(self,sql,params): self.sql=sql;return self
        def fetchone(self): return {'fact_value_num':39.2} if "fact_key = 'longitude_sidereal'" in self.sql else None
    conn=Conn()
    assert S0.fetch_natal_longitude(conn,'chart','natal_lagna','LAGNA')==39.2
    assert "fact_category = 'graha_position'" in conn.sql
    assert 'ORDER BY fact_id' in conn.sql


@pytest.mark.parametrize('name,tier', [('svarna',1),('rajata',2),('tamra',3),('loha',4)])
def test_moorti_testimony_cannot_change_the_forecast_rate(name, tier):
    """ALGO §3.13: uncited legacy mūrti is testimony, never a scored factor.

    There is no admitted classical numeric bridge. In particular loha does
    not imply u=1 or any other suppression strength (D-PADMIT; §N.4).
    Catches moorti_polarity_numeric_bridge at its field consumer.
    """
    from services.ka_kshetra.g1_inputs import suppression_primitives
    from services.ka_kshetra.contracts import PromisePrior
    birth = datetime(2001,1,1,tzinfo=timezone.utc)
    rows,gaps = suppression_primitives('chart',birth,[],[{
        'graha':'Mars', 't_in':birth+timedelta(days=2.37),
        't_out':birth+timedelta(days=6.71), 'moorti_name':name,
        'quality_tier':tier, 'source_ref':'m1'}],[])
    env = S4.EnvelopeIndex([S4.Primitive(p.primitive_kind,p.subject,p.object_ref,
        p.polarity,p.class_label,tuple(p.envelope)) for p in rows],10)
    ev = S4.FieldEvaluator(event_class='career',lifetime_count=1,
        promise=PromisePrior(.5),clocks=[],ladder={},envelopes=env,
        weights={'rho:default':.75},horizon_days=10)
    # G1 §3.20's product has S=1 for testimony: hand-derived multiplicative
    # identity, not a comparison against another production evaluator.
    assert env.obstructions_at(4) == {}
    assert ev.terms_at(4).suppression_term == 1.
    # W2 §5.1 C-1/C-2: lambda0=1/36525 days, Ptilde=.05+.95*.5=.525.
    # The baseline is per century, independent of this ten-day test horizon;
    # mūrti adds no factor to these seeded engineering operands.
    assert ev.ln_lambda(4) == pytest.approx(math.log(.525/36525), abs=1e-12)
    assert ev.ln_lambda(4) == ev.ln_lambda(1)
    assert any('numeric_bridge_not_admitted' in g['reason'] for g in gaps)


@pytest.mark.parametrize('unavailable', [
    {'null_reason':'information_unavailable'}, {'quality_tier':None},
])
def test_unavailable_moorti_retains_mask_edges_without_scoring(unavailable):
    """PLAN §6.2 item 4: unavailable risk masks retain both interval edges.

    ALGO §3.13's missing source cannot establish a scalar, even when the
    interval is known. This is a mask, not a fabricated classical judgment.
    """
    from services.ka_kshetra.g1_inputs import suppression_primitives
    birth = datetime(2001,1,1,tzinfo=timezone.utc)
    rows,gaps = suppression_primitives('chart',birth,[],[{
        'graha':'Mars','t_in':birth+timedelta(days=2.37),
        't_out':birth+timedelta(days=6.71),'source_ref':'m-gap',**unavailable}],[])
    env = S4.EnvelopeIndex([S4.Primitive(p.primitive_kind,p.subject,p.object_ref,
        p.polarity,p.class_label,tuple(p.envelope),p.source_pk,
        p.source_fact_id,p.source_table) for p in rows],10)
    assert {0.,2.37,6.71,10.} <= set(env.breakpoints())
    assert env.obstructions_at(4) == {}
    assert [(p.source_pk,p.source_table) for p in rows] == [('m-gap','kala_moorti_nirnaya_candidate')]
    assert gaps == [{'source_ref':'m-gap','reason':'moorti_information_unavailable'}]


def test_layer0_retains_non_grid_kinematic_scenario_and_mask_edges():
    """PLAN §6.2 item 4 and ALGO §3.20(g): full operator partition.

    Neither a clock nor decade seam implies these three interior edges;
    dropping extra_breakpoints must remove an observable Layer0 knot.
    """
    from services.ka_kshetra.layer0 import assemble_knot_set_with_decade_seams
    ev = SimpleNamespace(horizon_days=10.,ladder={},envelopes=S4.EnvelopeIndex([],10),
                         extra_breakpoints=(2.37,4.13,6.71,-1.,11.,float('nan')))
    assert list(assemble_knot_set_with_decade_seams(ev)) == [
        0.,1.,2.,2.37,3.,4.,4.13,5.,6.,6.71,7.,8.,9.,10.]


def test_sampled_null_uses_1023_nonidentity_shifts_and_observation():
    """ALGO §3.20 and PLAN §6.2 item 5: 1023+1=1024, no identity draw.

    This is the declared G1 engineering surrogate, not a classical odds rule
    or JH-parity oracle. Exercise the default consumer, including stored stats.
    """
    from services.ka_kshetra import stage5_null as S5
    from services.ka_kshetra.contracts import PromisePrior
    shifts = S5.shift_grid(10.,S5.DEFAULT_REPLICATES)
    assert len(shifts) == 1023
    assert shifts == pytest.approx([r*10/1024 for r in range(1,1024)])
    assert all(0 < d < 10 for d in shifts)
    ev = S4.FieldEvaluator(event_class='career',lifetime_count=1,
        promise=PromisePrior(.5),clocks=[],ladder={},
        envelopes=S4.EnvelopeIndex([],10),weights={},horizon_days=10)
    result = S5.run_null(ev,10,buckets=(1,))
    assert len(result.max_stats[1]) == result.replicates == 1023
    assert result.shift_grid_step == 10/1024
    assert S5.null_p(result.max_stats[1],100.) == 1/1024
    assert S5.null_resolution(result.replicates) == 1/1024


def test_production_boundary_oracles_run_in_required_no_skip_ci():
    """§N.8: an optional database job cannot earn a mandatory oracle signal."""
    from pathlib import Path
    import shlex
    import yaml
    root = Path(__file__).resolve().parents[5]
    jobs = yaml.safe_load((root/'.github/workflows/ci.yml').read_text())['jobs']
    required = jobs['governance-gates']
    assert 'k3-sealed-db-tests' in required['needs']
    job = jobs['k3-sealed-db-tests']
    assert job['env']['KALA_REQUIRE_DB'] == '1'
    assert not job.get('continue-on-error')
    step = next(s for s in job['steps'] if s.get('name','').startswith('K5-G1a —'))
    assert not step.get('continue-on-error') and not step.get('if')
    args = shlex.split(step['run'])
    assert {'tests/l3/ka_kshetra/test_g1a_contract.py',
            'tests/l3/ka_kshetra/test_g1a_candidate_sql.py',
            'tests/l3/kala_db/ka_kshetra/test_g1a_candidate_storage.py'} <= set(args)
    assert '-k' not in args and '-m' in args and args[args.index('-m')+1] == 'pytest'
    assert '-p' in args and args[args.index('-p')+1] == 'no:cacheprovider'
