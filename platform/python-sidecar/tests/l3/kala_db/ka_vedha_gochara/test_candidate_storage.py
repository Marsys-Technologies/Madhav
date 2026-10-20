"""Real PostgreSQL constraints and transactions; losing a guard fails these."""
from dataclasses import replace
from datetime import datetime
from importlib import import_module
from types import SimpleNamespace

import psycopg
import pytest
from psycopg.types.json import Jsonb

from tests.l3.kala_db.ka_vedha_gochara.conftest import CHART, NATAL, BUILD, MIGRATION
from tests.l3.ka_vedha_gochara.test_overlays import bundle, residence, A, B, C, D


def store(conn, value=None, build=BUILD):
    return import_module('services.ka_vedha_gochara.storage').replace_candidate(
        SimpleNamespace(db_conn=conn, build_id=build,config={'chart_id':CHART},dry_run=False), value or bundle())


def snapshot(conn,table):
    return conn.execute(f'SELECT to_jsonb(t) FROM {table} t ORDER BY to_jsonb(t)::text').fetchall()


def active_bundle():
    r=residence(); r['Sun']=[(1,A,D)]; r['Mars']=[(7,B,C),(2,C,D)]
    return bundle(residence=r)


def test_replacement_twice_empty_header_legacy_and_other_generations_unchanged(conn):
    legacy=snapshot(conn,'kala_vedha_gochara')
    rows=active_bundle()
    assert store(conn,rows)>0
    first=snapshot(conn,'kala_vedha_gochara_interval')
    assert store(conn,rows)>0 and snapshot(conn,'kala_vedha_gochara_interval')==first
    assert snapshot(conn,'kala_vedha_gochara')==legacy
    # Empty replacement on a new input vector requires a new candidate.
    conn.execute("UPDATE kala_layer_candidate_grain SET input_vector='changed'")
    with pytest.raises(ValueError,match='input|stale'):
        store(conn,bundle())
    assert snapshot(conn,'kala_vedha_gochara_interval')==first
    conn.execute("DELETE FROM kala_layer_candidate_grain")
    assert store(conn,bundle())==0
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_candidate').fetchone()[0]==3
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_interval').fetchone()[0]==0
    assert snapshot(conn,'kala_vedha_gochara')==legacy
    assert conn.execute('SELECT count(*) FROM kala_layer_candidate_grain').fetchone()[0]==3
    conn.execute(MIGRATION.read_text().replace('public.',conn.execute('SELECT quote_ident(current_schema())').fetchone()[0]+'.'))
    assert snapshot(conn,'kala_vedha_gochara')==legacy


@pytest.mark.parametrize('state',['complete','verified','published','rejected'])
def test_nonbuilding_candidate_refused_before_any_delete(conn,state):
    store(conn,active_bundle()); prior=snapshot(conn,'kala_vedha_gochara_interval')
    conn.execute('UPDATE kala_layer_candidate SET state=%s',(state,))
    with pytest.raises(ValueError,match='building|mutable'):
        store(conn)
    assert snapshot(conn,'kala_vedha_gochara_interval')==prior


@pytest.mark.parametrize('failure',['head','build','chart','natal','fact','ayanamsha'])
def test_wrong_pins_or_published_head_refused(conn,failure):
    val=bundle()
    if failure=='head': conn.execute("INSERT INTO kala_layer_head VALUES (%s,'candidate-1')",(CHART,))
    if failure=='natal': conn.execute("UPDATE kala_layer_candidate SET conventions='{}'")
    if failure=='fact': conn.execute("UPDATE chart_facts SET fact_value_num=301")
    if failure=='ayanamsha': conn.execute("UPDATE chart_facts SET ayanamsha_id='wrong'")
    if failure=='chart': conn.execute('UPDATE build_runs SET chart_id=%s WHERE id=%s',(NATAL,BUILD))
    with pytest.raises((ValueError,LookupError)):
        store(conn,val,build=NATAL if failure=='build' else BUILD)
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_candidate').fetchone()[0]==0


def test_sql_overlap_reverse_infinity_wrong_parent_and_qualifications_rejected(conn):
    store(conn,active_bundle())
    row=conn.execute("SELECT to_jsonb(t) FROM kala_vedha_gochara_interval t WHERE graha='Sun' ORDER BY t_in LIMIT 1").fetchone()[0]
    def insert(r):
        keys=list(r)
        conn.execute('INSERT INTO kala_vedha_gochara_interval ('+','.join(keys)+') VALUES ('+','.join(['%s']*len(keys))+')',
                     [Jsonb(v) if k=='detail' else v for k,v in r.items()])
    for mutate in (lambda r:r.update(t_out=r['t_in']),lambda r:r.update(t_in='-infinity',graha='Jupiter'),
                   lambda r:r.update(t_in='2025-01-01T12:00Z'),lambda r:r.update(generation='wrong'),
                   lambda r:r.update(state='cancelled_vipareeta'),lambda r:r.update(detail={'primary_house':0,'vedha_house':9})):
        bad=dict(row); mutate(bad)
        with pytest.raises(psycopg.Error), conn.transaction(): insert(bad)


def test_db_trigger_refuses_direct_mutation_after_publication(conn):
    store(conn,active_bundle())
    conn.execute("UPDATE kala_layer_candidate SET state='published'")
    with pytest.raises(psycopg.Error), conn.transaction():
        conn.execute('DELETE FROM kala_vedha_gochara_interval')


def test_update_cannot_create_overlap_when_graha_and_start_change(conn):
    store(conn,active_bundle())
    row=conn.execute("SELECT to_jsonb(t) FROM kala_vedha_gochara_interval t WHERE graha='Sun' ORDER BY t_in LIMIT 1").fetchone()[0]
    conn.execute('DELETE FROM kala_vedha_gochara_interval')
    # Distinct primary keys can share a start. Only the old Sun row may be
    # excluded when moving it to Mars [B,C), inside the existing Mars [A,D).
    for graha,end in [('Sun',B),('Mars',D)]:
        value={**row,'graha':graha,'t_in':A,'t_out':end}
        keys=list(value)
        conn.execute('INSERT INTO kala_vedha_gochara_interval ('+','.join(keys)+') VALUES ('+','.join(['%s']*len(keys))+')',
            [Jsonb(v) if k=='detail' else v for k,v in value.items()])
    before=snapshot(conn,'kala_vedha_gochara_interval')
    with pytest.raises(psycopg.errors.RaiseException,match='overlapping intervals'),conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_interval SET graha='Mars',t_in=%s,t_out=%s WHERE graha='Sun'",(B,C))
    assert snapshot(conn,'kala_vedha_gochara_interval')==before
    # The same identity change is valid when the other row only touches B.
    conn.execute("UPDATE kala_vedha_gochara_interval SET t_out=%s WHERE graha='Mars'",(B,))
    conn.execute("UPDATE kala_vedha_gochara_interval SET graha='Mars',t_in=%s,t_out=%s WHERE graha='Sun'",(B,C))
    assert conn.execute("SELECT graha,t_in,t_out FROM kala_vedha_gochara_interval ORDER BY t_in").fetchall()==[
        ('Mars',datetime.fromisoformat(A),datetime.fromisoformat(B)),
        ('Mars',datetime.fromisoformat(B),datetime.fromisoformat(C))]


@pytest.mark.parametrize('start',[A,B])
def test_update_excludes_its_own_interval_with_unchanged_or_changed_start(conn,start):
    store(conn,active_bundle())
    conn.execute("DELETE FROM kala_vedha_gochara_interval WHERE graha<>'Sun' OR t_in<>%s",(B,))
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_interval').fetchone()[0]==1
    conn.execute('UPDATE kala_vedha_gochara_interval SET t_in=%s,t_out=%s',(start,D))
    assert conn.execute('SELECT t_in=%s,t_out=%s FROM kala_vedha_gochara_interval',(start,D)).fetchone()==(True,True)


def test_dispatch_unbound_is_inert(conn):
    # A build with no candidate bound stays inert. A BOUND build (BUILD) is no
    # longer inert since SR-K9-PUBLISHABLE D2: see test_k9_dispatch_provider.py.
    from services.ka_vedha_gochara.writer import KaVedhaGocharaWriter
    before=snapshot(conn,'kala_vedha_gochara')
    for build in (NATAL,):
        ctx=SimpleNamespace(db_conn=conn,build_id=build,config={'chart_id':CHART},dry_run=False)
        result=KaVedhaGocharaWriter().run(ctx)
        assert result.rows_inserted==0
    assert snapshot(conn,'kala_vedha_gochara')==before
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_candidate').fetchone()[0]==0


@pytest.mark.parametrize('source',['pairs','latta','enrichment'])
def test_changed_or_fabricated_source_refused_before_replacement(conn,source):
    val=bundle()
    if source=='pairs':
        conn.execute("UPDATE bg_transit_rules SET classical_citation='changed authority' WHERE graha='sun'")
    elif source=='latta':
        conn.execute("INSERT INTO bg_phaladeepika_latta VALUES ('Sun',12,'forward','citation','verse')")
    else:
        from tests.l3.ka_vedha_gochara.test_overlays import api
        api()
        val=bundle(enrichment={'passage':'invented','locator':'missing','verses':'XXVI.47-48'})
    with pytest.raises(ValueError,match='source|authority|passage'):
        store(conn,val)
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_candidate').fetchone()[0]==0


@pytest.mark.parametrize('patch',["method_qualification=NULL,null_reason=NULL", "coverage='{}'", "payload='{}'", "upstream_fingerprint='{}'"])
def test_sql_refuses_unearned_null_method_or_missing_coverage_contract(conn,patch):
    store(conn)
    with pytest.raises(psycopg.Error),conn.transaction():
        conn.execute('UPDATE kala_vedha_gochara_candidate SET '+patch)


def test_db_failure_rolls_back_children_and_header_with_caller_savepoint(conn):
    val=active_bundle(); store(conn,val)
    before=snapshot(conn,'kala_vedha_gochara_interval')
    bad=replace(val,intervals=tuple({**r,'state':'invented'} for r in val.intervals))
    with pytest.raises(psycopg.Error),conn.transaction():
        store(conn,bad)
    assert snapshot(conn,'kala_vedha_gochara_interval')==before


def test_two_generations_coexist_without_rewriting_first(conn):
    from tests.l3.ka_vedha_gochara.test_overlays import bundle
    from psycopg.types.json import Jsonb
    store(conn,active_bundle())
    first=snapshot(conn,'kala_vedha_gochara_interval')
    build2='00000000-0000-0000-0000-000000000004'
    conn.execute('INSERT INTO build_runs VALUES (%s,%s)',(build2,CHART))
    conn.execute("INSERT INTO kala_layer_candidate SELECT chart_id,'candidate-2',%s,state,conventions FROM kala_layer_candidate WHERE generation='candidate-1'",(build2,))
    store(conn,bundle(generation='candidate-2'),build=build2)
    assert snapshot(conn,'kala_vedha_gochara_interval')==first
    assert conn.execute('SELECT generation,count(*) FROM kala_vedha_gochara_candidate GROUP BY generation ORDER BY generation').fetchall()==[
        ('candidate-1',3),('candidate-2',3)]


def test_verbatim_enrichment_checked_against_actual_fixture_source(conn):
    source={'passage':'Planted source text for exact equality verification.', 'locator':'phaladeepika_pg0340_c01','verses':'XXVI.47-48'}
    conn.execute("INSERT INTO classical_text_chunks VALUES (%s,'phaladeepika',26,47,48,%s)",(source['locator'],source['passage']))
    store(conn,bundle(enrichment=source))
    assert conn.execute("SELECT payload->'enrichment'->>'passage',payload->'enrichment'->'applied_to_computation' FROM kala_vedha_gochara_candidate WHERE vedha_kind='latta'").fetchone()==(source['passage'],False)


@pytest.mark.parametrize('patch',["natal_build_id='00000000-0000-0000-0000-000000000003'", "janma_reference_fact_id='wrong'", "ayanamsha_id='wrong'", "generation='legacy'"])
def test_direct_header_mutations_cannot_bypass_natal_or_identity_guard(conn,patch):
    store(conn)
    with pytest.raises(psycopg.Error),conn.transaction():
        conn.execute('UPDATE kala_vedha_gochara_candidate SET '+patch)


def test_writer_keeps_candidate_row_locked_against_concurrent_publication(conn, kala_db_dsn):
    # Fixture setup is committed solely to expose this disposable schema to a
    # second session. Neither the writer nor the provider commits anything.
    conn.commit()
    schema=conn.execute('SELECT current_schema()').fetchone()[0]
    store(conn,active_bundle())
    # ConnectionInfo.dsn omits passwords; reuse the guarded fixture DSN in CI.
    with psycopg.connect(kala_db_dsn) as other:
        other.execute(f'SET search_path TO "{schema}", public')
        other.execute("SET LOCAL lock_timeout='100ms'")
        with pytest.raises(psycopg.errors.LockNotAvailable),other.transaction():
            other.execute("UPDATE kala_layer_candidate SET state='published' WHERE generation='candidate-1'")
        other.rollback()
    conn.rollback()
    with psycopg.connect(kala_db_dsn) as other:
        other.execute(f'SET search_path TO "{schema}", public')
        other.execute("UPDATE kala_layer_candidate SET state='published' WHERE generation='candidate-1'")
    with pytest.raises(ValueError,match='building|mutable'):
        store(conn)


def test_missing_natal_keeps_unavailable_headers_and_exact_external_spec(conn):
    conn.execute("DELETE FROM chart_facts")
    assert store(conn,bundle(janma_fact=None))==0
    rows=conn.execute('SELECT janma_reference_fact_id,null_reason,payload FROM kala_vedha_gochara_candidate').fetchall()
    assert len(rows)==3
    for ref,reason,payload in rows:
        assert ref=='[EXTERNAL_COMPUTATION_REQUIRED]' and reason=='information_unavailable'
        assert payload['external_computation_required']=={'asset':'ga_positions','fact_category':'graha_position',
            'fact_subject':'MOON','fact_key':'longitude_sidereal','chart_id':CHART,'build_id':NATAL,'ayanamsha_id':'lahiri_chitrapaksha'}
    with pytest.raises(psycopg.Error),conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_candidate SET payload=jsonb_set(payload,'{external_computation_required,chart_id}','\"wrong\"')")


def test_missing_natal_header_cannot_parent_a_computed_interval(conn):
    val=active_bundle()
    conn.execute('DELETE FROM chart_facts')
    store(conn,bundle(janma_fact=None))
    row=val.intervals[0]
    keys=list(row)
    with pytest.raises(psycopg.Error),conn.transaction():
        conn.execute('INSERT INTO kala_vedha_gochara_interval ('+','.join(keys)+') VALUES ('+','.join(['%s']*len(keys))+')',
            [Jsonb(v) if k=='detail' else v for k,v in row.items()])


@pytest.mark.parametrize('table',['kala_vedha_gochara_interval','kala_vedha_gochara_candidate'])
def test_truncate_cannot_bypass_retained_generation_guards(conn,table):
    store(conn,active_bundle())
    conn.execute("UPDATE kala_layer_candidate SET state='published'")
    with pytest.raises(psycopg.Error),conn.transaction():
        conn.execute('TRUNCATE '+table+' CASCADE')
