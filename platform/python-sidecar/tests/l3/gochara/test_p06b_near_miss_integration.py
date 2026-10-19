"""Ruling 18 §8: measured near-miss verification, never a pin-only PASS."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from services.gochara_kernel import near_miss_verifier as nv
from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import seal_brief as sb
from .test_near_miss_verifier import _derive, parabola, TC
from ._p06_prerequisite import classify, require_p06

MIGRATIONS = Path(__file__).resolve().parents[4] / 'migrations'
MIGRATION = '1381_gochara_near_miss_seal_integration.sql'


@pytest.mark.parametrize('body', ['sun', 'moon', 'rahu', 'ketu'])
def test_stationless_rootless_curve_is_refused_even_with_positive_clearance(body):
    rows = _derive(parabola(0.5, 0.01), body=body)
    assert rows and all(r['state'] == 'unresolved' and r['reason'] == 'stationless_rootless_stretch' for r in rows)


def test_precision_evidence_names_each_false_claim():
    row = dict(solver_method='swiss_refined_extremum', delta_t=7e-6,
               precision_regime='swiss_golden_section_tol_1e-05d')
    assert nv.precision_problems(row) == []
    for key, value, refusal in [
        ('solver_method', 'arc_index_extremum', 'near_miss_solver_method'),
        ('precision_regime', 'guessed', 'near_miss_precision_regime'),
        ('delta_t', None, 'near_miss_delta_t'), ('delta_t', float('nan'), 'near_miss_delta_t'),
        ('delta_t', -1, 'near_miss_delta_t'), ('delta_t', 1.0, 'near_miss_delta_t'),
    ]:
        assert any(p.startswith(refusal) for p in nv.precision_problems({**row, key: value}))


def test_manifest_layer_pin_is_versioned_without_changing_legacy_preimages():
    from .test_a53_input_vector import _mutate
    inp = _mutate("base")
    old = iv.assemble_vector(inp)
    assert 'near_miss_layer_version' not in old
    new = iv.assemble_vector({**inp, 'near_miss_layer_version': 1})
    assert new == {**old, 'near_miss_layer_version': 1}
    for bad in (True, 0, 2, '1'):
        with pytest.raises(iv.InputDrift, match='near_miss_layer_version'):
            iv.assemble_vector({**inp, 'near_miss_layer_version': bad})


def test_pin_alone_is_unverified_and_all_null_identity_stays_vacuous():
    assert sb.near_miss_layer_status({}) == 'stored_uncovered'
    assert sb.near_miss_layer_status({'near_miss_layer_version': 1}) == 'unverified'
    assert sb.near_miss_layer_status({'near_miss_layer_version': 1}, {'status': 'VERIFIED', 'digest': 'a'*64}) == 'verified'


def test_ephemeris_object_comparison_checks_real_clearance_and_missing_rows():
    # Jupiter's December 2003 loop: actual pinned Swiss, no analytic position seam.
    from .conftest import assert_real_ephemeris, EPHE_PATH
    from services.gochara_kernel.knots import calc_sidereal_lon
    assert_real_ephemeris()
    def at(body, t):
        lon, flag = calc_sidereal_lon(body.title(), t.timestamp()/86400 + 2440587.5, EPHE_PATH)
        assert flag & 2
        return lon
    lo, hi = nv.utc(2003, 11, 1), nv.utc(2004, 3, 1)
    found = nv.derive_near_misses(at, 'jupiter', [145.39, 85.39, 25.39], lo, hi, orb_deg=1.0)
    want = [r for r in found if r['state'] == 'near_miss']
    assert len(want) == 1
    assert want[0]['clearance_deg'] == pytest.approx(0.396, abs=.002)
    assert any(p.startswith('near_miss_missing') for p in nv.compare_sets(found, [], junction_source=([], False),
        expected_orb_deg=1.0, expected_object_id='jupiter-test'))


def test_new_migration_is_protected_and_every_apply_has_its_own_readback():
    root = Path(__file__).resolve().parents[5]
    assert MIGRATION in (root/'platform/scripts/kala_protected_migrations.txt').read_text()
    for n in ('1305', '1306', '1308', '1381'):
        assert list((root/'platform/scripts/gochara').glob(f'readback_{n}_*.sql'))
    deploy = (root/'.github/workflows/deploy.yml').read_text()
    assert 'readback_1381_near_miss_seal.sql' in deploy


def test_p06_landing_gate_skips_only_when_p06_is_wholly_absent_and_refuses_a_half_landed_p06():
    """The gate that lets the P06-dependent tests wait for P06 reads false on a partial landing (P06B_PREBUILD_v1_0 landing order)."""
    names = ('migration 1305', 'migration 1306', 'migration 1308', 'module near_miss', 'helper apply_1305')
    assert classify(dict.fromkeys(names, False)) == 'absent'
    assert classify(dict.fromkeys(names, True)) == 'complete'
    for i in range(len(names)):
        assert classify({n: n == names[i] for n in names}) == 'partial'
        assert classify({n: n != names[i] for n in names}) == 'partial'


@pytest.fixture()
def chain():
    require_p06()
    import psycopg
    from .test_a53_inventory import create_am5_database, drop_am5_database, _boot
    admin, name, dsn = create_am5_database('p06b', apply_1305=True)
    conn = psycopg.connect(dsn, autocommit=True)
    try:
        conn.execute((MIGRATIONS.parent/'scripts/gochara/readback_1305_snapshot_copy.sql').read_text())
        for filename in ('1306_gochara_expected_class_census.sql', '1308_gochara_near_miss_storage.sql'):
            with conn.transaction():
                conn.execute((MIGRATIONS/filename).read_text())
                conn.execute('INSERT INTO _migrations_applied(filename) VALUES (%s)', (filename,))
            number=filename.split('_')[0]
            script=next((MIGRATIONS.parent/'scripts/gochara').glob(f'readback_{number}_*.sql'))
            conn.execute(script.read_text())
        _boot(conn, '5.0')
        yield conn
    finally:
        conn.close()
        drop_am5_database(admin, name)


def _apply(conn):
    with conn.transaction():
        conn.execute((MIGRATIONS/MIGRATION).read_text())
        conn.execute('INSERT INTO _migrations_applied(filename) VALUES (%s)', (MIGRATION,))
    conn.execute((MIGRATIONS.parent/'scripts/gochara/readback_1381_near_miss_seal.sql').read_text())


def test_stacked_chain_preserves_legacy_digest_and_carries_exact_old_function_bodies(chain):
    from .test_a53_inventory import CHART_ID
    c = chain
    old = {n: c.execute('SELECT pg_get_functiondef(%s::regprocedure)', (f'public.{n}(uuid,text)',)).fetchone()[0]
           for n in ('ka_gochara_candidate_gate_violations', 'ka_gochara_brief_state_digest')}
    def digest():
        return c.execute('SELECT ka_gochara_brief_state_digest(%s,%s)', (CHART_ID, '5.0')).fetchone()[0]
    before = digest()
    _apply(c)
    assert digest() == before  # FB-26: table additions do not change an old generation's bytes.
    for n in old:
        new = c.execute('SELECT pg_get_functiondef(%s::regprocedure)', (f'public.{n}(uuid,text)',)).fetchone()[0]
        # FB-20: the real pg_get_functiondef is literally the old body plus its own block.
        import re
        if n.endswith('candidate_gate_violations'):
            block="\n  UNION ALL\n  SELECT '*'::text,NULL::text,NULL::text,n.violation,n.detail\n  FROM public.ka_gochara_near_miss_violations(p_chart,p_generation) n"
            assert new.replace(block,'') == old[n]
        else:
            assert re.sub(r'  -- P06b begin:.*?  -- P06b end\n','',new,flags=re.S) == old[n]



def test_wrong_predecessor_definition_refuses_before_any_ddl(chain):
    import psycopg
    c = chain
    c.execute("COMMENT ON FUNCTION ka_gochara_candidate_gate_violations(uuid,text) IS 'irrelevant comment'")
    # Change prosrc while preserving the result type: functiondef pin must see it.
    c.execute("CREATE OR REPLACE FUNCTION ka_gochara_candidate_gate_violations(p_chart uuid,p_generation text) "
              "RETURNS TABLE(event_class text,path_id text,rule_version text,violation text,detail text) "
              "LANGUAGE sql STABLE AS $$ SELECT NULL::text,NULL::text,NULL::text,NULL::text,NULL::text WHERE false $$")
    with pytest.raises(psycopg.Error, match='predecessor'):
        _apply(c)
    assert c.execute("SELECT to_regclass('public.ka_gochara_near_miss_verification')").fetchone()[0] is None


def test_sql_gate_requires_measurement_and_stale_digest_never_seals(chain):
    import json
    import psycopg
    from .test_a53_inventory import CHART_ID
    c = chain
    _apply(c)
    with c.transaction():
        c.execute('SELECT ka_gochara_lock_chart(%s)', (CHART_ID,))
        c.execute("UPDATE kala_gochara_publication SET input_generation_vector = input_generation_vector || "
                  "'{\"near_miss_layer_version\":1}'::jsonb WHERE chart_id=%s AND generation='5.0'", (CHART_ID,))
    def names():
        return [r[0] for r in c.execute("SELECT violation FROM ka_gochara_candidate_gate_violations(%s,%s) WHERE violation LIKE 'near_miss_%%'", (CHART_ID, '5.0'))]
    assert 'near_miss_verification_missing' in names()
    # No point obligations: a real ephemeris stage can certify the empty object census.
    from .conftest import EPHE_PATH
    from services.gochara_kernel import verification_job as vj
    with c.transaction():
        vj.take_locks(c, CHART_ID)
        preview = nv.verify_generation(c, chart_id=CHART_ID, generation='5.0', ephe_path=EPHE_PATH, persist=False)
        assert preview['status'] == 'VERIFIED'
        assert c.execute('SELECT count(*) FROM ka_gochara_near_miss_verification').fetchone()[0] == 0
    with c.transaction():
        vj.take_locks(c, CHART_ID)
        result = nv.verify_generation(c, chart_id=CHART_ID, generation='5.0', ephe_path=EPHE_PATH, persist=True)
    assert result['status'] == 'VERIFIED' and result['objects'] == 0
    assert names() == []
    assert c.execute('SELECT near_miss_digest FROM ka_gochara_near_miss_verification').fetchone()[0] == result['digest']
    # Positive near-miss seal contract on the ACTUAL table: current measured evidence
    # passes this additive guard and reaches the existing publication guard. It does
    # not bypass publication/approval or claim an empty fixture is a FINAL generation.
    with pytest.raises(psycopg.Error, match='not a published manifest'):
        with c.transaction():
            vj.take_locks(c, CHART_ID)
            c.execute("INSERT INTO ka_gochara_generation_seal(chart_id,generation,manifest_id) "
                      "SELECT chart_id,generation,manifest_id FROM kala_gochara_publication WHERE chart_id=%s", (CHART_ID,))
    # The stacked brief hash must bind near-miss rows that 1240 never read.
    from services.gochara_kernel.near_miss import NearMissObject, NearMissStore
    sky=c.execute('SELECT sky_convention_id FROM ka_gochara_convention_bridge').fetchone()[0]
    with c.transaction(force_rollback=True):
        vj.take_locks(c, CHART_ID)
        before=c.execute('SELECT ka_gochara_brief_state_digest(%s,%s)',(CHART_ID,'5.0')).fetchone()[0]
        obj=NearMissObject('jupiter','aspect','point:265.39','orb_drishti_slow:1.000000',sky)
        NearMissStore(c)._ensure_object(obj)
        c.execute("INSERT INTO ka_gochara_near_miss_search(chart_id,generation,near_miss_object_id,layer_version,searched_complete,horizon,near_miss_count) "
                  "SELECT chart_id,generation,%s,1,true,horizon,0 FROM kala_gochara_publication",(obj.uuid,))
        after=c.execute('SELECT ka_gochara_brief_state_digest(%s,%s)',(CHART_ID,'5.0')).fetchone()[0]
        assert before != after, 'brief digest omitted newly stored near-miss search'
        c.execute("UPDATE kala_gochara_publication SET input_generation_vector=input_generation_vector-'near_miss_layer_version'")
        assert 'near_miss_layer_unpinned' in names()
    # Changing the horizon moves the measured near-miss digest even on an empty census.
    with c.transaction():
        c.execute('SELECT ka_gochara_lock_chart(%s)', (CHART_ID,))
        c.execute("UPDATE kala_gochara_publication SET horizon=tstzrange('2025-01-01','2025-04-01','[)') WHERE chart_id=%s", (CHART_ID,))
    assert 'near_miss_verification_stale' in names()
    # The new trigger is additive on the actual seal surface, independently of Python adapters.
    with pytest.raises(psycopg.Error, match='near_miss_verification_stale'):
        with c.transaction():
            c.execute("SELECT ka_gochara_lock_chart(%s)", (CHART_ID,))
            c.execute("INSERT INTO ka_gochara_generation_seal(chart_id,generation,manifest_id) "
                      "SELECT chart_id,generation,manifest_id FROM kala_gochara_publication WHERE chart_id=%s", (CHART_ID,))


@pytest.fixture()
def real_jupiter_candidate(chain):
    """A real Jupiter near miss, created by the builder, checked only by the independent stage."""
    import uuid
    from services.gochara_kernel import inventory as inv, near_miss as builder
    from services.gochara_kernel import verification_job as vj
    from services.gochara_kernel.inventory_store import InventoryStore
    from services.gochara_kernel.substrate import production_arc_index
    from .test_a53_inventory import CHART_ID, FACT_IDS, PINNED_BUILD
    from .test_d1_near_miss_storage import EXTRA_DASHA, NEAR
    from .conftest import EPHE_PATH, assert_real_ephemeris
    assert_real_ephemeris()
    c=chain
    _apply(c)
    sky=c.execute('SELECT sky_convention_id FROM ka_gochara_convention_bridge').fetchone()[0]
    with c.transaction():
        vj.take_locks(c,CHART_ID)
        c.execute("UPDATE kala_gochara_publication SET horizon=tstzrange(%s,%s,'[)'),input_generation_vector="
                  "input_generation_vector || jsonb_build_object('near_miss_layer_version',1,'sky_convention',jsonb_build_object('id',%s::text))",
                  (*NEAR,sky))
        c.execute('DELETE FROM chart_dashas')
        for i,level,parent,lord,start,end in EXTRA_DASHA:
            c.execute("INSERT INTO chart_dashas(dasha_row_id,chart_id,ayanamsha_id,system_id,level_n,parent_row_id,lord_graha,"
                      "start_iso,end_iso,build_id,verification_pass_status) VALUES(%s,%s,'lahiri_chitrapaksha','vimshottari',%s,%s,%s,%s,%s,%s,'two_pass_verified')",
                      (str(uuid.UUID(int=i)),CHART_ID,level,None if parent is None else str(uuid.UUID(int=parent)),lord,start,end,PINNED_BUILD))
        store=InventoryStore(c)
        inp=store.insert_snapshot(chart_id=CHART_ID,generation='5.0',convention_id=sky,consumed_fact_ids=FACT_IDS,
                                  consumed_dasha_row_ids=[str(uuid.UUID(int=r[0])) for r in EXTRA_DASHA])
        ob=inv.Obligation('marriage','P3','1.0.0','jupiter','aspect','natal_planet','point:265.39','natal','native')
        plan=inv.ClassInventory('marriage',NEAR,(inv.PinPlan('P3','1.0.0','included',(ob,)),),
                                (inv.IntervalPlan(ob.ob_id,*NEAR,inv.STATE_COMPLETE),))
        store.write_class_inventory(chart_id=CHART_ID,generation='5.0',plan=plan,input_digest=inp)
        # Populate real pinned sky source identities, including verified-empty junctions.
        from pipeline.orchestrator.writers import ContextSpec, SubStep, ka_gochara_v5 as writer
        ctx=ContextSpec(asset_id=writer.ASSET_ID,build_id='p06b-sky',db_conn=c,dry_run=False,
                        config={'chart_id':CHART_ID,'horizon':NEAR,'ephe_path':EPHE_PATH})
        writer.GocharaV5Writer().run_substep(ctx,SubStep(key='body:Jupiter',label='Jupiter'))
        obj=builder.NearMissObject('jupiter','aspect','point:265.39','orb_drishti_slow:1.000000',sky)
        found=builder.solve_object_near_misses(obj=obj,index=production_arc_index('Jupiter',EPHE_PATH),orb_deg=1,
                                              horizon=NEAR,position_at=nv._ephemeris_position(EPHE_PATH))
        assert len(found)==1
        builder.NearMissStore(c).write_object(chart_id=CHART_ID,generation='5.0',obj=obj,horizon=NEAR,
            near_misses=found,dasha_rows=store.consumed_dasha_rows(CHART_ID,'5.0'))
    with c.transaction():
        vj.take_locks(c,CHART_ID)
        result=nv.verify_generation(c,chart_id=CHART_ID,generation='5.0',ephe_path=EPHE_PATH,persist=True)
    assert result['objects']==1 and result['status']=='VERIFIED'
    assert c.execute('SELECT count(*) FROM ka_gochara_near_miss_violations(%s,%s)',(CHART_ID,'5.0')).fetchone()[0]==0
    assert sb.near_miss_evidence(c,CHART_ID,'5.0',{'near_miss_layer_version':1})['digest']==result['digest']
    return c, result


def test_real_stored_object_stage_rederives_full_domain_ordinals_junction_and_precision(real_jupiter_candidate):
    from services.gochara_kernel import verification_job as vj
    from .test_a53_inventory import CHART_ID
    from .conftest import EPHE_PATH
    c, result = real_jupiter_candidate
    # Change each stored claim under a rolled-back corruption transaction. No trigger is disabled.
    # The insert-only discipline permits DELETE+INSERT only before seal.
    import psycopg
    for field,value,refusal in [('solver_method','arc_index_extremum','near_miss_solver_method'),
                                ('precision_regime','unverified','near_miss_precision_regime'),
                                ('delta_t',1.0,'near_miss_delta_t'),
                                ('clearance_deg',.2,'near_miss_clearance_mismatch'),
                                ('ordinal',99,'near_miss_ordinal_mismatch'),
                                ('junction',psycopg.types.json.Jsonb({'contains_junction':False}),'near_miss_junction_mismatch')]:
        with c.transaction(force_rollback=True):
            vj.take_locks(c,CHART_ID)
            c.execute('CREATE TEMP TABLE corrupt_nm AS SELECT * FROM ka_gochara_near_miss')
            c.execute('DELETE FROM ka_gochara_near_miss')
            c.execute(psycopg.sql.SQL('UPDATE corrupt_nm SET {}=%s').format(psycopg.sql.Identifier(field)),(value,))
            if field=='clearance_deg':
                c.execute('UPDATE corrupt_nm SET proximity=1-clearance_deg/orb_deg')
            c.execute('INSERT INTO ka_gochara_near_miss SELECT * FROM corrupt_nm')
            with pytest.raises(nv.NearMissError,match=refusal):
                nv.verify_generation(c,chart_id=CHART_ID,generation='5.0',ephe_path=EPHE_PATH,persist=True)


def test_job_near_miss_disagreement_prevents_class_persistence(monkeypatch):
    from contextlib import nullcontext
    from services.gochara_kernel import verification_job as vj
    class C:
        def transaction(self):
            return nullcontext()
    monkeypatch.setattr(vj,'take_locks',lambda *a:None)
    monkeypatch.setattr(vj,'check_preconditions',lambda *a,**kw:{'classes':['marriage']})
    monkeypatch.setattr(vj,'precondition_fingerprint',lambda *a:'same')
    def disagree(*a,**kw):
        raise nv.NearMissError('near_miss_missing: independent detector')
    monkeypatch.setattr(nv,'verify_generation',disagree)
    def forbidden(*a,**kw):
        pytest.fail('class verification wrote after near-miss disagreement')
    monkeypatch.setattr(vj,'verify_class',forbidden)
    with pytest.raises(vj.VerificationDisagrees,match='near_miss_missing'):
        vj.run(C(),chart_id='fixture',position_at=None,ephe_path='unused',modules={'known':()},
               configured_selection_for=lambda c:{},path_rulings={},h_unknown={},moon_scope_domain=False,
               factor_rows_for=lambda *a:[],drishti_bound=False,vedha_bound=False,enforce_identity=False)


def test_independent_input_verifier_names_an_unsupported_layer_pin(monkeypatch):
    # The component is a closed vocabulary check, exercised through the full existing verifier.
    # The frozen vector provides literal data; every unrelated detector is held at its own matching value.
    from services.gochara_kernel import input_vector_verifier as ivv
    from .test_a53_input_vector import _mutate
    v=iv.assemble_vector(_mutate('base'))
    v['near_miss_layer_version']=2
    monkeypatch.setattr(ivv,'sql_sky_convention_digest',lambda *a:v['sky_convention']['content_digest'])
    monkeypatch.setattr(ivv,'sql_l0_digest',lambda *a:next(iter(v['l0'].values())))
    monkeypatch.setattr(ivv,'module_digests',lambda *a:v['implementation'])
    # Other drift may also be reported; the claim under test must be independently refused by name.
    from .conftest import EPHE_PATH
    with pytest.raises(RuntimeError,match='near_miss_layer_version'):
        ivv.verify_inputs(None,v,ephe_path=EPHE_PATH,modules={'pinned':()})


@pytest.mark.parametrize('version,required',[('1.0.0',False),('1.2.0',True)])
def test_final_rules_grain_requires_layer_pin_even_before_search_rows_exist(chain,version,required):
    from services.gochara_kernel import inventory as inv, verification_job as vj
    from services.gochara_kernel.inventory_store import InventoryStore
    from .test_a53_inventory import CHART_ID, FACT_IDS, DASHA_IDS, H0, H1
    from .conftest import EPHE_PATH
    from services.gochara_kernel import rule_registry
    c=chain
    _apply(c)
    with rule_registry.rule_profile(final_rules=True):   # main made the final (1.2.0) rules opt-in: a record on P3@1.2.0 needs that sealed row
        rule_registry.RuleRegistryStore(c).seed()
    sky=c.execute('SELECT sky_convention_id FROM ka_gochara_convention_bridge').fetchone()[0]
    with c.transaction():
        vj.take_locks(c,CHART_ID)
        store=InventoryStore(c)
        inp=store.insert_snapshot(chart_id=CHART_ID,generation='5.0',convention_id=sky,
                                  consumed_fact_ids=FACT_IDS,consumed_dasha_row_ids=DASHA_IDS)
        ob=inv.Obligation('marriage','P3',version,'jupiter','aspect','natal_planet','point:265.39','natal','native')
        plan=inv.ClassInventory('marriage',(H0,H1),(inv.PinPlan('P3',version,'included',(ob,)),),
                                (inv.IntervalPlan(ob.ob_id,H0,H1,inv.STATE_COMPLETE),))
        store.write_class_inventory(chart_id=CHART_ID,generation='5.0',plan=plan,input_digest=inp)
    names=[r[0] for r in c.execute('SELECT violation FROM ka_gochara_near_miss_violations(%s,%s)',(CHART_ID,'5.0'))]
    assert ('near_miss_layer_unpinned' in names) is required
    if required:
        with pytest.raises(nv.NearMissError,match='near_miss_layer_unpinned'):
            nv.verify_generation(c,chart_id=CHART_ID,generation='5.0',ephe_path=EPHE_PATH)


def test_junction_source_rederives_the_copied_md_ad_boundary_with_its_identity(chain):
    c=chain
    sky=c.execute('SELECT sky_convention_id FROM ka_gochara_convention_bridge').fetchone()[0]
    a,b,boundary=nv.utc(2004,1,1),nv.utc(2004,1,25),nv.utc(2004,1,10)
    rows=[{'level':1,'start':nv.utc(2003,6,1),'end':nv.utc(2004,6,1),'id':'md'},
          {'level':2,'start':nv.utc(2003,6,1),'end':boundary,'id':'ad1'},
          {'level':2,'start':boundary,'end':nv.utc(2004,6,1),'id':'ad2'}]
    from .conftest import EPHE_PATH
    junction,complete=nv._junction(c,{'convention_id':sky,'body':'jupiter'},{'t_in':a,'t_out':b},(a,b),rows,nv._ephemeris_position(EPHE_PATH))
    assert junction['dasha_boundary']=={'state':'complete','events':[{'level':'AD','t':boundary.isoformat(),'dasha_row_id':'ad1','row_edge':'end'}]}
    assert junction['contains_junction'] is True
    assert complete is False  # no sky-event substrate was built: unknown, never a verified empty.


@pytest.mark.parametrize('agent',['moon','period_lord:md'])
def test_stored_non_moon_census_requires_only_concrete_included_point_objects(chain,agent):
    from services.gochara_kernel import inventory as inv, verification_job as vj
    from services.gochara_kernel.inventory_store import InventoryStore
    from .test_a53_inventory import CHART_ID, FACT_IDS, DASHA_IDS, H0, H1
    from .conftest import EPHE_PATH
    c=chain
    _apply(c)
    sky=c.execute('SELECT sky_convention_id FROM ka_gochara_convention_bridge').fetchone()[0]
    with c.transaction():
        vj.take_locks(c,CHART_ID)
        c.execute("UPDATE kala_gochara_publication SET input_generation_vector=input_generation_vector || '{\"near_miss_layer_version\":1}'::jsonb")
        store=InventoryStore(c)
        inp=store.insert_snapshot(chart_id=CHART_ID,generation='5.0',convention_id=sky,consumed_fact_ids=FACT_IDS,consumed_dasha_row_ids=DASHA_IDS)
        ob=inv.Obligation('marriage','P3','1.0.0',agent,'conjunction','natal_planet','point:265.39','natal','native')
        plan=inv.ClassInventory('marriage',(H0,H1),(inv.PinPlan('P3','1.0.0','included',(ob,)),),
                                (inv.IntervalPlan(ob.ob_id,H0,H1,inv.STATE_COMPLETE),))
        store.write_class_inventory(chart_id=CHART_ID,generation='5.0',plan=plan,input_digest=inp)
        names=[r[0] for r in c.execute('SELECT violation FROM ka_gochara_near_miss_violations(%s,%s)',(CHART_ID,'5.0'))]
        assert 'near_miss_unsearched' not in names
        result=nv.verify_generation(c,chart_id=CHART_ID,generation='5.0',ephe_path=EPHE_PATH,persist=False)
        assert result['status']=='VERIFIED' and result['objects']==0


@pytest.mark.parametrize('pinned,refusal',[(False,'near_miss_layer_unpinned'),(True,'near_miss_unsearched')])
def test_an_orphan_occurrence_is_never_attested_as_an_empty_layer(chain,pinned,refusal):
    from services.gochara_kernel import near_miss as builder, verification_job as vj
    from .test_a53_inventory import CHART_ID
    from .conftest import EPHE_PATH
    c=chain
    _apply(c)
    sky=c.execute('SELECT sky_convention_id FROM ka_gochara_convention_bridge').fetchone()[0]
    with c.transaction():
        vj.take_locks(c,CHART_ID)
        if pinned:
            c.execute("UPDATE kala_gochara_publication SET input_generation_vector=input_generation_vector || '{\"near_miss_layer_version\":1}'::jsonb")
        obj=builder.NearMissObject('jupiter','aspect','point:265.39','orb_drishti_slow:1.000000',sky)
        builder.NearMissStore(c)._ensure_object(obj)
        # Deliberate invalid fixture: a stored occurrence with no search/coverage row.
        c.execute("INSERT INTO ka_gochara_near_miss(chart_id,generation,near_miss_id,near_miss_object_id,ordinal,level_deg,t_in,t_out,t_closest,"
            "closest_state,clearance_deg,orb_deg,proximity,junction,junction_complete,coverage,solver_method,delta_t,precision_regime) "
            "VALUES(%s,'5.0',%s,%s,1,145.39,'2025-01-01','2025-01-02','2025-01-01 12:00','placed',.3,1,.7,"
            "'{\"contains_junction\":null}',false,'{}','swiss_refined_extremum',.000007,'swiss_golden_section_tol_1e-05d')",
            (CHART_ID,builder.near_miss_id(obj,1),obj.uuid))
        with pytest.raises(nv.NearMissError,match=refusal):
            nv.verify_generation(c,chart_id=CHART_ID,generation='5.0',ephe_path=EPHE_PATH,persist=False)


def test_runtime_vector_pins_installed_layer_and_replays_the_original_pin(chain):
    from .conftest import EPHE_PATH, assert_real_ephemeris
    from services.gochara_kernel.rule_registry import bound_path_refs
    assert_real_ephemeris()
    c=chain
    sky=c.execute('SELECT sky_convention_id FROM ka_gochara_convention_bridge').fetchone()[0]
    kw=dict(sky_convention_id=sky,ephe_path=EPHE_PATH,path_refs=bound_path_refs(),rulings=[],scored_classes=['marriage'])
    vector=iv.build_input_vector(c,**kw)
    assert vector['near_miss_layer_version']==1
    legacy=iv.build_input_vector(c,**kw,near_miss_layer_version=None)
    assert legacy=={k:v for k,v in vector.items() if k!='near_miss_layer_version'}
    iv.verify_live(c,vector,**{k:v for k,v in kw.items() if k!='path_refs'},path_refs=kw['path_refs'])
    iv.verify_replay(c,legacy,kw['path_refs'],**{k:v for k,v in kw.items() if k!='path_refs'})


def test_a_stationless_contact_root_outside_the_domain_is_followed_not_called_a_near_miss(chain):
    from services.gochara_kernel import inventory as inv, near_miss as builder, verification_job as vj
    from services.gochara_kernel.inventory_store import InventoryStore
    from .test_a53_inventory import CHART_ID, FACT_IDS
    from .conftest import EPHE_PATH
    c=chain
    _apply(c)
    sky=c.execute('SELECT sky_convention_id FROM ka_gochara_convention_bridge').fetchone()[0]
    horizon=(nv.utc(1998,1,1),nv.utc(1998,1,5))
    at=nv._ephemeris_position(EPHE_PATH)
    target=f'point:{(at("sun",horizon[0])-.5)%360:.6f}'
    with c.transaction():
        vj.take_locks(c,CHART_ID)
        c.execute("UPDATE kala_gochara_publication SET horizon=tstzrange(%s,%s,'[)'),input_generation_vector=input_generation_vector || "
                  "jsonb_build_object('near_miss_layer_version',1,'sky_convention',jsonb_build_object('id',%s::text))",(*horizon,sky))
        c.execute("UPDATE chart_dashas SET start_iso=start_iso-interval '27 years',end_iso=end_iso-interval '27 years'")
        ids=[r[0] for r in c.execute('SELECT dasha_row_id FROM chart_dashas WHERE start_iso<%s AND end_iso>%s',(horizon[1],horizon[0]))]
        store=InventoryStore(c)
        inp=store.insert_snapshot(chart_id=CHART_ID,generation='5.0',convention_id=sky,consumed_fact_ids=FACT_IDS,consumed_dasha_row_ids=ids)
        ob=inv.Obligation('marriage','P3','1.0.0','sun','conjunction','natal_planet',target,'natal','native')
        store.write_class_inventory(chart_id=CHART_ID,generation='5.0',input_digest=inp,plan=inv.ClassInventory('marriage',horizon,
            (inv.PinPlan('P3','1.0.0','included',(ob,)),),(inv.IntervalPlan(ob.ob_id,*horizon,inv.STATE_COMPLETE),)))
        obj=builder.NearMissObject('sun','conjunction',target,'orb_conj_slow:1.000000',sky)
        builder.NearMissStore(c).write_object(chart_id=CHART_ID,generation='5.0',obj=obj,horizon=horizon,near_misses=[],dasha_rows=[])
        result=nv.verify_generation(c,chart_id=CHART_ID,generation='5.0',ephe_path=EPHE_PATH,persist=False)
        assert result['status']=='VERIFIED' and result['objects']==1


def test_new_verification_table_preserves_builder_verifier_sealer_separation():
    require_p06()
    import psycopg
    from .test_a53_inventory import create_am5_database, drop_am5_database
    admin,name,dsn=create_am5_database('p06bacl',faithful=True,apply_1305=True)
    c=psycopg.connect(dsn,autocommit=True)
    try:
        for filename in ('1306_gochara_expected_class_census.sql','1308_gochara_near_miss_storage.sql'):
            with c.transaction():
                c.execute((MIGRATIONS/filename).read_text())
                c.execute('INSERT INTO _migrations_applied(filename) VALUES (%s)',(filename,))
        _apply(c)
        for role,expected in [('data_plane_builder',(True,False,False,False)),
                              ('gochara_verifier',(True,True,True,False)),
                              ('gochara_sealer',(True,False,False,False))]:
            got=tuple(c.execute("SELECT has_table_privilege(%s,'public.ka_gochara_near_miss_verification',%s)",(role,priv)).fetchone()[0]
                      for priv in ('SELECT','INSERT','DELETE','UPDATE'))
            assert got==expected,(role,got)
    finally:
        c.close()
        drop_am5_database(admin,name)


def test_pinned_junction_source_changes_move_the_near_miss_digest(chain):
    """A staleness injection, not a claim that the injected event is physical."""
    import uuid
    from services.gochara_kernel import near_miss as builder, verification_job as vj
    from services.gochara_kernel.substrate import physical_object_id, boundary_target
    from services.gochara_kernel.record_store import RecordStore
    from .test_a53_inventory import CHART_ID
    c=chain
    _apply(c)
    sky=c.execute('SELECT sky_convention_id FROM ka_gochara_convention_bridge').fetchone()[0]
    with c.transaction():
        vj.take_locks(c,CHART_ID)
        obj=builder.NearMissObject('jupiter','aspect','point:265.39','orb_drishti_slow:1.000000',sky)
        builder.NearMissStore(c)._ensure_object(obj)
        c.execute("INSERT INTO ka_gochara_near_miss(chart_id,generation,near_miss_id,near_miss_object_id,ordinal,level_deg,t_in,t_out,t_closest,"
            "closest_state,clearance_deg,orb_deg,proximity,junction,junction_complete,coverage,solver_method,delta_t,precision_regime) "
            "VALUES(%s,'5.0',%s,%s,1,145.39,'2025-01-01','2025-01-02','2025-01-01 12:00','placed',.3,1,.7,"
            "'{\"contains_junction\":null}',false,'{}','swiss_refined_extremum',.000007,'swiss_golden_section_tol_1e-05d')",
            (CHART_ID,builder.near_miss_id(obj,1),obj.uuid))
        before=c.execute('SELECT ka_gochara_near_miss_digest(%s,%s)',(CHART_ID,'5.0')).fetchone()[0]
        po=physical_object_id(body='jupiter',relation_kind='sign_ingress',canonical_target=boundary_target(150),convention_id=sky)
        RecordStore(c).ensure_object(po)
        c.execute("INSERT INTO ka_gochara_sky_event(event_id,physical_object_id,convention_id,body,event_kind,occurrence_ordinal,t_exact,"
                  "longitude,solver_method,delta_lambda,delta_t,precision_regime,coverage) VALUES(%s,%s,%s,'jupiter','sign_ingress',1,"
                  "'2025-01-01 12:00',150,'swiss_refined',.00027,1,'fixture','{\"truncated\":false}')",(uuid.uuid4(),po.uuid,sky))
        after=c.execute('SELECT ka_gochara_near_miss_digest(%s,%s)',(CHART_ID,'5.0')).fetchone()[0]
        assert after != before,'junction source mutation left the near-miss attestation usable'


def test_operator_entry_reports_a_generation_stage_disagreement_as_disagree(monkeypatch,capsys):
    import json
    import psycopg
    from pipeline.orchestrator import verification_job as entry
    from services.gochara_kernel import verification_job as vj
    class C:
        closed=False
        def close(self):
            self.closed=True
    c=C()
    monkeypatch.setenv(entry.ENV_URL,'postgresql://postgres@127.0.0.1:55433/postgres')
    monkeypatch.setattr(psycopg,'connect',lambda *a,**kw:c)
    monkeypatch.setattr(entry,'_build_kwargs',lambda *a:{})
    def disagreement(*a,**kw):
        raise vj.VerificationDisagrees('near_miss','near_miss_missing: independently detected')
    monkeypatch.setattr(vj,'run',disagreement)
    code=entry.main(['--chart','482012f1-710e-4a25-994a-93821f5871aa'])
    out=json.loads(capsys.readouterr().out)
    assert code==vj.EXIT_DISAGREE==3
    assert out['status']=='DISAGREE' and out['stage']=='near_miss'
    assert 'near_miss_missing' in out['detail']
    assert c.closed


@pytest.mark.parametrize('field,value,refusal', [
    pytest.param('near_miss_id', '00000000-0000-4000-8000-000000000001',
                 'near_miss_identity_mismatch', id='P06B-NB-01-occurrence-uuid'),
    pytest.param('level_deg', 0.0, 'near_miss_level_mismatch', id='P06B-NB-02-ray-level'),
])
def test_review_children_refuse_corrupted_claim_without_attesting(real_jupiter_candidate, field, value, refusal):
    """Real Jupiter geometry; only the reviewed claim changes and all row guards stay enabled."""
    import psycopg
    from services.gochara_kernel import verification_job as vj
    from .test_a53_inventory import CHART_ID
    from .conftest import EPHE_PATH
    c, valid = real_jupiter_candidate
    before = c.execute('SELECT to_jsonb(v) FROM ka_gochara_near_miss_verification v').fetchone()[0]
    with c.transaction(force_rollback=True):
        vj.take_locks(c, CHART_ID)
        c.execute('CREATE TEMP TABLE corrupt_claim AS SELECT * FROM ka_gochara_near_miss')
        c.execute('DELETE FROM ka_gochara_near_miss')
        c.execute(psycopg.sql.SQL('UPDATE corrupt_claim SET {}=%s').format(psycopg.sql.Identifier(field)), (value,))
        c.execute('INSERT INTO ka_gochara_near_miss SELECT * FROM corrupt_claim')
        assert c.execute('SELECT ka_gochara_near_miss_digest(%s,%s)', (CHART_ID,'5.0')).fetchone()[0] != valid['digest']
        with pytest.raises(nv.NearMissError, match=refusal):
            nv.verify_generation(c, chart_id=CHART_ID, generation='5.0', ephe_path=EPHE_PATH, persist=True)
        assert c.execute('SELECT to_jsonb(v) FROM ka_gochara_near_miss_verification v').fetchone()[0] == before
    assert sb.near_miss_evidence(c,CHART_ID,'5.0',{'near_miss_layer_version':1})['digest'] == valid['digest']


def test_direct_sql_replay_is_a_named_predecessor_refusal_and_leaves_state_unchanged(chain):
    """NB-03: raw replay is deliberately unsupported; the ledger runner owns replay."""
    import psycopg
    _apply(chain)
    def state():
        return chain.execute("SELECT p.proname, pg_get_functiondef(p.oid) FROM pg_proc p "
            "WHERE p.pronamespace='public'::regnamespace AND p.proname IN "
            "('ka_gochara_brief_state_digest','ka_gochara_candidate_gate_violations',"
            "'ka_gochara_near_miss_digest','ka_gochara_near_miss_violations') ORDER BY 1").fetchall()
    before=state()
    ledger=chain.execute('SELECT filename,sha256 FROM _migrations_applied ORDER BY filename').fetchall()
    with pytest.raises(psycopg.Error,match='predecessor'):
        with chain.transaction():
            chain.execute((MIGRATIONS/MIGRATION).read_text())
    assert state()==before
    assert chain.execute('SELECT filename,sha256 FROM _migrations_applied ORDER BY filename').fetchall()==ledger


def test_all_null_policy_never_claims_endpoint_or_ranking_identity(chain):
    from services.gochara_kernel import verification_job as vj
    from .test_a53_inventory import CHART_ID
    from .conftest import EPHE_PATH
    _apply(chain)
    with chain.transaction():
        vj.take_locks(chain,CHART_ID)
        chain.execute("UPDATE kala_gochara_publication SET input_generation_vector=input_generation_vector || "
            "'{\"near_miss_layer_version\":1,\"result_policy\":\"all_null_candidate/1\"}'::jsonb")
        result=nv.verify_generation(chain,chart_id=CHART_ID,generation='5.0',ephe_path=EPHE_PATH,persist=False)
        assert result['status']=='VERIFIED'  # the measured layer; endpoint identity is a separate claim
        assert result['output_identity']=='vacuous_under_policy'
