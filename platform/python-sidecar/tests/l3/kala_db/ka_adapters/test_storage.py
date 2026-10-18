"""Candidate DB operations must refuse wrong pins before DELETE and preserve legacy."""
from dataclasses import replace
from datetime import datetime,timezone
from importlib import import_module
from types import SimpleNamespace

import psycopg
import pytest
from psycopg.types.json import Jsonb

from tests.l3.ka_adapters.test_candidates import (
    CHART,NATAL,BUILD,LO,HI,FAMILIES,RINGS,api,context,cov,moorti,sudarshana,indexes,  # noqa: F401
)
from tests.l3.kala_db.ka_adapters.conftest import MIGRATION


def values(indexes):
    return [moorti(indexes),api('kota_chakra').build_candidate(ctx=context(),indexes=indexes,horizon=(LO,HI),ring_rows=RINGS),
        api('tithi_pravesha').build_candidate(ctx=context(),birth_dt=datetime(1984,2,5,5,13,tzinfo=timezone.utc),years=(42,),coverage=cov(LO,LO+365,source=(LO,LO+365))),sudarshana()]


def store(conn,p,**changes):
    ctx=SimpleNamespace(db_conn=conn,build_id=BUILD,config={'chart_id':CHART,'birth_params':{'datetime_iso':'1984-02-05T10:43:00','tz_offset_hours':5.5}},dry_run=False)
    for k,v in changes.items(): setattr(ctx,k,v)
    return import_module('services.kala_core.overlays.contested_storage').replace_candidate(ctx,p)


def snapshot(conn,table):
    return conn.execute(f'SELECT to_jsonb(t) FROM {table} t ORDER BY to_jsonb(t)::text').fetchall()


def test_all_four_replace_twice_preserve_legacy_other_generation_and_additive_schema(conn,indexes):
    before={f:snapshot(conn,'kala_'+f) for f in FAMILIES}
    for p in values(indexes):
        assert store(conn,p)==len(p.entries)
        first=snapshot(conn,'kala_'+p.family+'_candidate')
        assert store(conn,p)==len(p.entries)
        assert snapshot(conn,'kala_'+p.family+'_candidate')==first
        assert snapshot(conn,'kala_'+p.family)==before[p.family]
    assert conn.execute('SELECT count(*) FROM kala_layer_candidate_grain').fetchone()[0]==4
    # A new building generation can coexist; later mutation of it cannot affect candidate-1.
    conn.execute('INSERT INTO build_runs VALUES (%s,%s)',(CHART,CHART))
    conn.execute("INSERT INTO kala_layer_candidate SELECT chart_id,'candidate-2',%s,state,conventions FROM kala_layer_candidate",(CHART,))
    p=moorti(indexes,ctx=context(generation='candidate-2'))
    assert store(conn,p,build_id=CHART)==len(p.entries)
    assert conn.execute('SELECT count(*) FROM kala_moorti_nirnaya_candidate').fetchone()[0]==2
    conn.execute(MIGRATION.read_text().replace('public.',conn.execute('SELECT quote_ident(current_schema())').fetchone()[0]+'.'))
    for f in FAMILIES: assert snapshot(conn,'kala_'+f)==before[f]


@pytest.mark.parametrize('failure',['chart','build','natal','ayanamsha','fact','source','head','state','vector','tamper'])
def test_bad_inputs_refused_before_replacement(conn,indexes,failure):
    p=moorti(indexes); store(conn,p)
    prior=snapshot(conn,'kala_moorti_nirnaya_candidate')
    if failure=='chart': conn.execute('UPDATE build_runs SET chart_id=%s WHERE id=%s',(NATAL,BUILD))
    if failure=='build': conn.execute('UPDATE kala_layer_candidate SET build_id=%s',(NATAL,))
    if failure=='natal': conn.execute("UPDATE kala_layer_candidate SET conventions='{}'")
    if failure=='ayanamsha': conn.execute("UPDATE chart_facts SET ayanamsha_id='wrong'")
    if failure=='fact': conn.execute("UPDATE chart_facts SET fact_value_num=301 WHERE fact_id='moon-ref'")
    if failure=='source': conn.execute("UPDATE bg_transit_moorti SET phala_brief='changed'")
    if failure=='head': conn.execute("INSERT INTO kala_layer_head VALUES (%s,'candidate-1')",(CHART,))
    if failure=='state': conn.execute("UPDATE kala_layer_candidate SET state='verified'")
    if failure=='vector': conn.execute("UPDATE kala_layer_candidate_grain SET input_vector='changed'")
    if failure=='tamper': p=replace(p,entries=({'score':1},))
    with pytest.raises((ValueError,LookupError)): store(conn,p)
    assert snapshot(conn,'kala_moorti_nirnaya_candidate')==prior


@pytest.mark.parametrize('family',FAMILIES)
def test_sql_refuses_published_mutation_and_truncate(conn,indexes,family):
    p=next(p for p in values(indexes) if p.family==family); store(conn,p)
    table='kala_'+family+'_candidate'
    conn.execute("UPDATE kala_layer_candidate SET state='published'")
    for command in (f'DELETE FROM {table}',f'UPDATE {table} SET payload=payload',f'TRUNCATE {table}'):
        with pytest.raises(psycopg.Error),conn.transaction(): conn.execute(command)


@pytest.mark.parametrize('mutation',["method_qualification='qualified'","operator_role='scored'","coverage='{}'","upstream_fingerprint='{}'","payload='{}'", "generation='other'"])
def test_sql_contract_rejects_false_green_or_identity(conn,indexes,mutation):
    store(conn,moorti(indexes))
    with pytest.raises(psycopg.Error),conn.transaction():
        conn.execute('UPDATE kala_moorti_nirnaya_candidate SET '+mutation)


@pytest.mark.parametrize('family',FAMILIES)
def test_writer_explicit_payload_dispatch_is_candidate_only(conn,indexes,family):
    from pipeline.orchestrator.writers import WRITER_REGISTRY
    import_module('services.ka_'+family+'.writer')
    p=next(p for p in values(indexes) if p.family==family)
    before=snapshot(conn,'kala_'+family)
    ctx=SimpleNamespace(db_conn=conn,build_id=BUILD,config={'chart_id':CHART,'birth_params':{'datetime_iso':'1984-02-05T10:43:00+05:30'},'ka_adapter_payload':p},dry_run=False)
    assert WRITER_REGISTRY['ka_'+family]().run(ctx).rows_inserted==len(p.entries)
    assert snapshot(conn,'kala_'+family)==before
    ctx.dry_run=True
    assert WRITER_REGISTRY['ka_'+family]().run(ctx).rows_inserted==0
    wrong=replace(p,family='moorti_nirnaya' if family!='moorti_nirnaya' else 'kota_chakra')
    ctx.config['ka_adapter_payload']=wrong; ctx.dry_run=False
    with pytest.raises(ValueError): WRITER_REGISTRY['ka_'+family]().run(ctx)


def test_missing_l1_external_spec_storage_and_later_fact_drift(conn,indexes):
    conn.execute("DELETE FROM chart_facts WHERE fact_id='moon-ref'")
    p=moorti(indexes,ctx=context(facts=()))
    assert store(conn,p)==0
    row=conn.execute('SELECT payload FROM kala_moorti_nirnaya_candidate').fetchone()[0]
    assert row['external_computation_required'][0]['fact_key']=='longitude_sidereal'
    conn.execute("INSERT INTO chart_facts VALUES ('new',%s,%s,'lahiri_chitrapaksha','graha_position','MOON','longitude_sidereal',300,NULL)",(CHART,NATAL))
    with pytest.raises(ValueError,match='fact|L1'): store(conn,p)


@pytest.mark.parametrize('family',['tithi_pravesha','sudarshana_varsha'])
def test_annual_payload_must_use_orchestrator_birth_params(conn,indexes,family):
    p=next(p for p in values(indexes) if p.family==family)
    with pytest.raises(ValueError,match='birth'):
        store(conn,p,config={'chart_id':CHART,'birth_params':{'datetime_iso':'1985-02-05T10:43:00','tz_offset_hours':5.5}})
    assert not snapshot(conn,'kala_'+family+'_candidate')


@pytest.mark.parametrize('family',FAMILIES)
@pytest.mark.parametrize('bad',['score','reversed_interval','unqualified_source'])
def test_direct_sql_entries_cannot_invent_judgment_or_source(conn,indexes,family,bad):
    p=next(p for p in values(indexes) if p.family==family); store(conn,p)
    table='kala_'+family+'_candidate'
    row=conn.execute(f'SELECT payload FROM {table}').fetchone()[0]
    entry=row['entries'][-1]
    if bad=='score': entry['score']=1
    if bad=='reversed_interval': entry['t_out']=entry['t_in']
    if bad=='unqualified_source':
        if family=='sudarshana_varsha': entry['judgment']='favorable'
        else: entry['source_status']='verse_cited'
    with pytest.raises(psycopg.Error),conn.transaction():
        conn.execute(f'UPDATE {table} SET payload=%s',(Jsonb(row),))
