"""K3-2 versioned SQL boundary; isolated fixture DB, never production."""
import importlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest
from psycopg.types.json import Jsonb

from tests.l3.kala_db._schema import apply_schema_migration
from tests.l3.ka_vighnakara.test_sealed import CHART,BUILD,GEN,data,clock,export
from tests.l3.kala_db.ka_vighnakara.test_negative_space_storage import database, conn

ROOT=Path(__file__).parents[4]
MIGRATION=ROOT.parent/'migrations/1388_k3_2_sealed_negative_space.sql'


def api():
    assert importlib.util.find_spec('services.ka_vighnakara.sealed_storage'), 'sealed storage missing'
    return importlib.import_module('services.ka_vighnakara.sealed_storage')


def context(conn,tmp_path):
    receipt,expected=export(tmp_path)
    return SimpleNamespace(db_conn=conn,build_id=BUILD,dry_run=False,config=dict(chart_id=CHART,
        negative_space_sealed=dict(receipt=receipt,expected=expected)))


def setup(conn):
    apply_schema_migration(conn,MIGRATION)
    conn.execute('UPDATE kala_layer_candidate SET generation=%s,conventions=%s',(GEN,Jsonb({'negative_space':data()['pins']})))
    conn.execute('''CREATE TABLE chart_dashas (
        dasha_row_id text, chart_id uuid, level_n int, lord_graha text, parent_row_id text,
        start_iso timestamptz,end_iso timestamptz,build_id text,ayanamsha_id text,system_id text,
        verification_pass_status text,applies_to_this_chart_flag bool,
        is_truncated_at_window_start bool,is_truncated_at_window_end bool)''')
    from tests.l3.ka_vighnakara.test_sealed import NATAL,START,END
    conn.execute('''INSERT INTO chart_dashas VALUES ('period:1',%s,1,'Saturn',NULL,%s,%s,%s,
        'lahiri_chitrapaksha','vimshottari','two_pass_verified',true,false,false)''',(CHART,START,END,NATAL))


def test_live_storage_schema_and_repeat_content(conn,tmp_path):
    setup(conn);ctx=context(conn,tmp_path)
    assert api().write_sealed_candidate(ctx)==2
    first=conn.execute('SELECT assertion_id,assertion,roots,release,effective_state FROM kala_obstruction ORDER BY assertion_id').fetchall()
    assert api().write_sealed_candidate(ctx)==2
    assert conn.execute('SELECT assertion_id,assertion,roots,release,effective_state FROM kala_obstruction ORDER BY assertion_id').fetchall()==first
    assert {r[1]['acceptance_scope'] for r in first}=={'sealed_producers'}


def test_writer_dispatch_is_explicit_and_nonfixture(conn,tmp_path):
    setup(conn);ctx=context(conn,tmp_path)
    from pipeline.orchestrator.writers.ka_vighnakara import KaVighnakaraWriter
    assert KaVighnakaraWriter().run(ctx).rows_inserted==2


@pytest.mark.parametrize('mutation',['fixture','published','retained','wrong_chart','wrong_pin','missing_schema'])
def test_refusal_preserves_candidate_and_legacy(conn,tmp_path,mutation):
    setup(conn);ctx=context(conn,tmp_path)
    api().write_sealed_candidate(ctx)
    conn.execute("INSERT INTO kala_obstruction(chart_id,obstruction_type,severity,severity_score,source_citation) VALUES (%s,'malefic_transit','mild',0.5,'legacy')",(CHART,))
    before=conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o ORDER BY id').fetchall()
    if mutation=='fixture': conn.execute("UPDATE kala_layer_candidate SET conventions='{"+'"fixture":true'+"}'")
    elif mutation=='published': conn.execute('INSERT INTO kala_layer_head VALUES (%s,%s)',(CHART,GEN))
    elif mutation=='retained': conn.execute("UPDATE kala_layer_candidate SET state='verified'")
    elif mutation=='wrong_chart': ctx.config['chart_id']='00000000-0000-0000-0000-000000000399'
    elif mutation=='wrong_pin': ctx.config['negative_space_sealed']['expected']['pins']['natal_build_id']='other'
    else: conn.execute('ALTER TABLE kala_obstruction DROP CONSTRAINT kala_obstruction_k3_sealed_check')
    with pytest.raises(ValueError): api().write_sealed_candidate(ctx)
    assert conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o ORDER BY id').fetchall()==before


def test_source_error_preserves_existing_rows(conn,tmp_path):
    setup(conn);ctx=context(conn,tmp_path);api().write_sealed_candidate(ctx)
    before=conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o ORDER BY id').fetchall()
    Path(ctx.config['negative_space_sealed']['receipt']['output_file']).write_text('tail')
    with pytest.raises(ValueError): api().write_sealed_candidate(ctx)
    assert conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o ORDER BY id').fetchall()==before


@pytest.mark.parametrize('mutation',["effective_state='evaluated_silent'", "measurement='measured_lower_rate'",
    "assertion=jsonb_set(assertion,'{acceptance_scope}','\"fixture_only\"')", "severity_score=0.5",
    "roots='{}'", "release='{\"kind\":\"instant\",\"instant\":\"tomorrow\"}'"])
def test_live_schema_rejects_forged_axes(conn,tmp_path,mutation):
    setup(conn);api().write_sealed_candidate(context(conn,tmp_path))
    with pytest.raises((psycopg.errors.CheckViolation,psycopg.errors.InvalidDatetimeFormat)):
        conn.execute('UPDATE kala_obstruction SET '+mutation+" WHERE effective_state='obstruction_in_force'")


def test_migration_repeat_and_served_legacy_bytes(conn,tmp_path):
    conn.execute("INSERT INTO kala_obstruction(chart_id,obstruction_type,severity,severity_score,source_citation) VALUES (%s,'malefic_transit','mild',0.5,'legacy')",(CHART,))
    before=conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o WHERE generation IS NULL ORDER BY id').fetchall()
    setup(conn);api().write_sealed_candidate(context(conn,tmp_path))
    apply_schema_migration(conn,MIGRATION)
    assert conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o WHERE generation IS NULL ORDER BY id').fetchall()==before


def test_dry_run_requires_no_database():
    assert api().write_sealed_candidate(SimpleNamespace(dry_run=True))==0


def test_real_f2_reader_boundaries_and_inapplicability(conn):
    conn.execute('''CREATE TABLE chart_dashas (
        dasha_row_id text, chart_id uuid, level_n int, lord_graha text, parent_row_id text,
        start_iso timestamptz,end_iso timestamptz,build_id text,ayanamsha_id text,system_id text,
        verification_pass_status text,applies_to_this_chart_flag bool,
        is_truncated_at_window_start bool,is_truncated_at_window_end bool)''')
    from tests.l3.ka_vighnakara.test_sealed import NATAL,START,MID,END
    for ident,a,b,applicable in [('MD:1',START,MID,True),('MD:2',MID,END,False)]:
        conn.execute('INSERT INTO chart_dashas VALUES (%s,%s,1,\'Saturn\',NULL,%s,%s,%s,\'lahiri_chitrapaksha\',\'vimshottari\',\'two_pass_verified\',%s,false,false)',
            (ident,CHART,a,b,NATAL,applicable))
    rows=api().read_clock_spans(conn,data())
    assert [r['applicability'] for r in rows]==['applicable','method_inapplicable']
    assert [r['period_ids'] for r in rows]==[{'MD':'MD:1'},{'MD':'MD:2'}]


def test_f2_gap_is_a_scoped_unavailable_span(conn,tmp_path):
    setup(conn)
    from tests.l3.ka_vighnakara.test_sealed import MID
    conn.execute('UPDATE chart_dashas SET end_iso=%s',(MID,))
    assert api().write_sealed_candidate(context(conn,tmp_path))==2
    states=conn.execute('SELECT effective_state,null_reason FROM kala_obstruction ORDER BY interval_start').fetchall()
    assert states==[('obstruction_in_force',None),('information_unavailable','coverage_gap')]


@pytest.mark.parametrize('mutation',["assertion=jsonb_set(assertion,'{protections}','[]')",
    "assertion=jsonb_set(assertion,'{protections,0,target_assertion_id}','\"wrong\"')",
    "assertion=jsonb_set(assertion,'{protections,0,fact_ids}','[]')"])
def test_live_cancelled_sql_requires_targeted_source_conclusion_evidence(conn,tmp_path,mutation):
    setup(conn)
    from tests.l3.ka_vighnakara.test_sealed import with_protection
    receipt,expected=export(tmp_path,with_protection())
    ctx=context(conn,tmp_path)
    # context() re-exports the base case; keep the protected full artifact.
    receipt,expected=export(tmp_path,with_protection())
    ctx.config['negative_space_sealed']=dict(receipt=receipt,expected=expected)
    assert api().write_sealed_candidate(ctx)==2
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute('UPDATE kala_obstruction SET '+mutation+" WHERE effective_state='obstruction_cancelled'")


def test_database_rejects_duplicate_sealed_assertion_identity(conn,tmp_path):
    setup(conn);api().write_sealed_candidate(context(conn,tmp_path))
    cursor=conn.execute('SELECT * FROM kala_obstruction WHERE generation=%s',(GEN,))
    from psycopg import sql
    columns=sql.SQL(',').join(sql.Identifier(c.name) for c in cursor.description if c.name!='id')
    with pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute(sql.SQL('INSERT INTO kala_obstruction ({}) SELECT {} FROM kala_obstruction WHERE generation=%s').format(columns,columns),(GEN,))


def test_complete_export_receipt_and_independent_inventory_survive_storage(conn,tmp_path):
    setup(conn);ctx=context(conn,tmp_path)
    api().write_sealed_candidate(ctx)
    payload=conn.execute('SELECT assertion FROM kala_obstruction ORDER BY id LIMIT 1').fetchone()[0]
    assert payload['provenance']['export_receipt']==ctx.config['negative_space_sealed']['receipt']
    import hashlib,json
    expected=ctx.config['negative_space_sealed']['expected']
    keys=json.dumps(expected['keys'],sort_keys=True,separators=(',',':')).encode()
    assert payload['provenance']['independent_inventory']==dict(row_count=expected['row_count'],
        counts={kind:len(values) for kind,values in expected['keys'].items()},
        keys_sha256=hashlib.sha256(keys).hexdigest())
    assert 'keys' not in payload['provenance']['independent_inventory']
