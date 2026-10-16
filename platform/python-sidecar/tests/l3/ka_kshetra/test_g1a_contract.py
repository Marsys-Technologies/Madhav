"""G1a behavioral oracles: independently recomputed axes and operator roots."""
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


@pytest.mark.parametrize('unavailable', [
    {'null_reason': 'information_unavailable', 'quality_tier': 4},
    {'quality_tier': None},
    {},
])
def test_unavailable_moorti_mask_survives_null_entry_and_wrap(unavailable):
    from services.ka_kshetra.g1_inputs import suppression_primitives
    from services.ka_kshetra import stage5_null as S5
    from services.ka_kshetra.contracts import PromisePrior
    birth = datetime(2001, 1, 1, tzinfo=timezone.utc)
    # Real KA-3b entries use Julian dates, including a leading unavailable span.
    row = dict(graha='Mars', t_in=2451910.5, t_out=2451914.5,
               moorti_name='loha', source_ref='candidate:moorti:Mars:2451910.5',
               **unavailable)
    prims, gaps = suppression_primitives('chart', birth, [], [row], [])
    assert gaps == [{'source_ref': row['source_ref'], 'reason': 'moorti_information_unavailable'}]
    assert len(prims) == 1
    mask = prims[0]
    assert (mask.primitive_kind, mask.polarity, mask.source_table, mask.source_pk) == (
        'input_mask', 'neutral', 'kala_moorti_nirnaya_candidate', row['source_ref'])
    assert mask.envelope == [(0., 0.), (4., 0.)]
    env = S4.EnvelopeIndex([S4.Primitive(p.primitive_kind, p.subject, p.object_ref,
        p.polarity, p.class_label, tuple(p.envelope), p.source_pk,
        p.source_fact_id, p.source_table) for p in prims], 10.)
    ev = S4.FieldEvaluator(event_class='career', lifetime_count=1., promise=PromisePrior(.5),
        clocks=[], ladder={}, envelopes=env, weights={'beta:x7': 99.}, horizon_days=10.)
    empty = S4.FieldEvaluator(event_class='career', lifetime_count=1., promise=PromisePrior(.5),
        clocks=[], ladder={}, envelopes=S4.EnvelopeIndex([], 10.), weights=ev.weights, horizon_days=10.)
    assert {0., 4., 10.} <= set(S5._null_breakpoints(ev))
    shifted = S5.replicate_evaluator(ev, 1.5)
    assert {0., 2.5, 8.5, 10.} <= set(S5._null_breakpoints(shifted))
    for index in (env, shifted.envelopes):
        assert all(p.source_pk == row['source_ref'] and p.source_table == mask.source_table
                   for p in index.supportive)
        for t in (0., 1., 2.5, 4., 8.5, 9.9):
            assert index.covariates_at(t) == {} and index.obstructions_at(t) == {}
    for t in (0., 1., 3., 5., 9.):
        assert ev.ln_lambda(t) == empty.ln_lambda(t) == shifted.ln_lambda(t)
    segments = S5._null_build_segments(shifted)
    assert {0., 2.5, 8.5, 10.} <= {s.t_start for s in segments} | {s.t_end for s in segments}


def test_sampled_candidate_dispatch_runs_the_pinned_nonidentity_experiment(monkeypatch):
    from services.ka_kshetra import writer as W, stage5_null as S5
    from services.ka_kshetra.contracts import PromisePrior
    from .fake_db import FakeConn, FakeCtx
    from .fixtures import build_tables, CHART_ID, EVENT_CLASS
    monkeypatch.setattr(W, 'HORIZON_DAYS', 10.)
    monkeypatch.setattr(W.KaKshetraWriter, '_optional_stage_plugins', lambda *a: [])
    conn = FakeConn(build_tables())
    ctx = FakeCtx(conn, CHART_ID)
    writer = W.KaKshetraWriter()
    steps = writer.plan_substeps(ctx)
    assert writer._pins.config_pin['segment_engine'] == 'sampled'
    ev = S4.FieldEvaluator(event_class=EVENT_CLASS, lifetime_count=1., promise=PromisePrior(.5),
        clocks=[], ladder={}, envelopes=S4.EnvelopeIndex([
            primitive('contact_moon_ref', [(2.31, 0.), (2.37, 1.), (2.43, 0.)])], 10.),
        weights={'beta:x1': 2.}, horizon_days=10., extra_breakpoints=(4.13,))
    acc = S5.NullAccumulator(replicates=S5.DEFAULT_REPLICATES, horizon_days=10.)
    cctx = SimpleNamespace(evaluator=ev, null_accumulator=acc,
        temporal_shape='punctual', baseline_is_synthetic=False)
    monkeypatch.setattr(writer, '_class_context', lambda *a: cctx)
    # Stage 5 must read the committed observation; store the real reference segments.
    conn.tables['kala_field'] = [dict(chart_id=CHART_ID, event_class=EVENT_CLASS,
        segment_index=i, **vars(s)) for i, s in enumerate(ev.build_segments())]
    shifts, partitions = [], []
    real_replicate, real_build = S5.replicate_evaluator, S5._null_build_segments
    def replicate(field, delta):
        shifts.append(delta)
        return real_replicate(field, delta)
    def build(field):
        actual = real_build(field)
        reference = field.build_segments()
        assert actual == reference
        partitions.append(tuple(field.breakpoints()))
        return actual
    monkeypatch.setattr(S5, 'replicate_evaluator', replicate)
    monkeypatch.setattr(S5, '_null_build_segments', build)
    blocks = [s for s in steps if s.key.startswith('stage5:')]
    assert len(blocks) == 64
    for step in blocks[:-1]:
        writer.run_substep(ctx, step)
    finalize = next(s for s in steps if s.key.startswith('stage5finalize:'))
    with pytest.raises(S4.UpstreamStageIncomplete, match='1008/1023'):
        writer.run_substep(ctx, finalize)
    writer.run_substep(ctx, blocks[-1])
    assert shifts == [r * (10. / 1024) for r in range(1, 1024)]
    assert S5.shift_grid(10., S5.DEFAULT_REPLICATES) == shifts
    assert all(0. < delta < 10. for delta in shifts)
    assert len(partitions) == 1023 and all(4.13 in p for p in partitions)
    result = acc.finalize()
    assert result.replicates == 1024 and result.shift_count == 1023
    assert result.shift_grid_step == 10. / 1024
    assert result.resolution == 1. / 1024
    assert all(len(stats) == 1023 for stats in result.max_stats.values())
    assert S5.null_p([0.] * 1023, 1.) == result.resolution
    assert S5.null_p([1.] * 1023, 1.) == 1.
    writer.run_substep(ctx, finalize)
    assert len(conn.tables['kala_field_null']) == 10
    assert all(r['replicates'] == 1024 and len(r['null_max_stats']) == 1023
               and r['shift_grid_step'] == 10. / 1024 for r in conn.tables['kala_field_null'])
    assert conn.tables['kala_field_windows'], 'the real peak must exercise persisted window resolution'
    assert all(r['null_R'] == 1024 and r['null_resolution'] == 1. / 1024
               and r['null_p'] >= r['null_resolution'] for r in conn.tables['kala_field_windows'])


@pytest.mark.parametrize('replicates', [8, 1024])
def test_sampled_experiment_provenance_is_derived_from_execution_config(monkeypatch, replicates):
    from services.ka_kshetra import writer as W, stage5_null as S5
    from .fake_db import FakeConn, FakeCtx
    from .fixtures import build_tables, CHART_ID
    monkeypatch.setattr(S5, 'DEFAULT_REPLICATES', replicates)
    monkeypatch.setattr(W.KaKshetraWriter, '_optional_stage_plugins', lambda *a: [])
    writer = W.KaKshetraWriter()
    writer.plan_substeps(FakeCtx(FakeConn(build_tables()), CHART_ID))
    config = writer._pins.config_pin
    assert config['null_replicates'] == replicates
    assert config['null_experiment'] == {
        'replicates': replicates, 'shift_count': replicates - 1,
        'denominator': replicates, 'resolution': 1. / replicates,
        'shift_grid_step': W.HORIZON_DAYS / replicates,
        'schedule': 'delta_r=r*H/R; r=1..R-1; observation counted once',
    }
    assert f'{replicates - 1} non-identity shifts + observation' in config['constant_provenance']['null']
    assert f'denominator={replicates}' in config['constant_provenance']['null']


def test_lagna_contact_target_inherits_the_real_pinned_L1_key():
    class Conn:
        def execute(self,sql,params): self.sql=sql;return self
        def fetchone(self): return {'fact_value_num':39.2} if "fact_key = 'longitude_sidereal'" in self.sql else None
    conn=Conn()
    assert S0.fetch_natal_longitude(conn,'chart','natal_lagna','LAGNA')==39.2
    assert "fact_category = 'graha_position'" in conn.sql
    assert 'ORDER BY fact_id' in conn.sql
