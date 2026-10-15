"""K5-2b storage/lifecycle proof; guarded suite owns its throwaway database."""
from pathlib import Path
from types import SimpleNamespace
import json
import uuid

import psycopg
from psycopg.rows import dict_row
import pytest

from services.ka_kshetra.writer import KaKshetraWriter
from tests.l3.ka_kshetra.test_compact_field import source_rows

ROOT = Path(__file__).resolve().parents[6]
MIGRATION = ROOT / 'platform/migrations/1391_k5_2b_compact_field.sql'
CHART, BUILD = str(uuid.uuid4()), str(uuid.uuid4())
GEN = 'candidate:compact-fixture'


@pytest.fixture(scope='module')
def schema(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn) as conn:
        conn.execute((ROOT / 'platform/migrations/1330_kala_layer_manifest_candidates.sql')
                     .read_text().split('-- A separately dispatched verifier')[0])
        conn.execute('CREATE TABLE build_runs(id uuid PRIMARY KEY, chart_id uuid NOT NULL)')
        core=(ROOT / 'platform/supabase/migrations/492_kala_field_core.sql').read_text()
        conn.execute('CREATE TABLE IF NOT EXISTS kala_field (' + core.split('CREATE TABLE IF NOT EXISTS kala_field (')[1].split('\n);',1)[0] + '\n);')
        # Exact upstream 1385 strategy: LIKE constraints, separate generation-keyed uniqueness.
        conn.execute('CREATE TABLE kala_field_candidate (LIKE kala_field INCLUDING DEFAULTS INCLUDING CONSTRAINTS)')
        conn.execute('ALTER TABLE kala_field_candidate ADD COLUMN generation text NOT NULL')
        conn.execute('CREATE UNIQUE INDEX candidate_key ON kala_field_candidate(generation,chart_id,event_class,segment_index)')
        conn.execute('CREATE TABLE kala_field_snapshots_candidate (' + core.split('CREATE TABLE IF NOT EXISTS kala_field_snapshots (')[1].split('\n);',1)[0] + '\n);')
        conn.execute('ALTER TABLE kala_field_snapshots_candidate ADD COLUMN generation text NOT NULL')
        assert MIGRATION.is_file(), 'compact candidate migration must exist'
        conn.execute(MIGRATION.read_text())
        conn.execute(MIGRATION.read_text())  # idempotent migration retry
    yield isolated_kala_db_dsn


@pytest.fixture
def stored(schema):
    with psycopg.connect(schema, row_factory=dict_row) as conn:
        conn.execute('INSERT INTO build_runs VALUES (%s,%s)',(BUILD,CHART))
        conn.execute('''INSERT INTO kala_layer_candidate
            (chart_id,generation,build_id,model_digest,rule_registry_version,conventions)
            VALUES (%s,%s,%s,'fixture','fixture','{}')''',(CHART,GEN,BUILD))
        conn.execute("INSERT INTO kala_layer_head(chart_id,generation) VALUES (%s,'retained:v1')",(CHART,))
        conn.execute('''INSERT INTO kala_field_snapshots_candidate
            (chart_id,generation,field_snapshot_id,field_content_hash,weights_version,x_schema_version,
             corpus_pin,config_pin,horizon_days,event_classes) VALUES
            (%s,%s,'fixture-v1','finalized-fixture','classical','x1','fixture','{}',6.,ARRAY['career_change'])''',(CHART,GEN))
        for row in source_rows():
            row.update(chart_id=CHART,event_class='career_change',generation=GEN,
                       lambda_start=__import__('math').exp(row['alpha']),lambda_end=1.,
                       promise_term=1.,clock_term_start=0.,modifier_term_start=1.,
                       suppression_term_start=1.,signed_obstruction_start=0.)
            columns=tuple(row)
            conn.execute('INSERT INTO kala_field_candidate (' + ','.join(columns) + ') VALUES (' + ','.join(['%s']*len(columns))+')',list(row.values()))
        # Legacy row shares chart/key: it must survive the candidate build byte-for-byte.
        conn.execute('''INSERT INTO kala_field SELECT id,chart_id,event_class,segment_index,
            t_start,t_end,alpha,gamma,lambda_start,lambda_end,integral_days,promise_term,
            clock_term_start,modifier_term_start,suppression_term_start,signed_obstruction_start,
            refinement_depth,refinement_exhausted,refinement_residual,weights_version,
            x_schema_version,field_snapshot_id,computed_at FROM kala_field_candidate''')
        try: yield conn
        finally: conn.rollback()


def context(conn, **updates):
    ctx=SimpleNamespace(db_conn=conn,build_id=BUILD,dry_run=False,
        config={'chart_id':CHART,'birth_params':{'datetime_iso':'2000-01-01T12:00:00+00:00'},'kshetra_compact_candidate':GEN})
    for k,v in updates.items():setattr(ctx,k,v)
    return ctx


def run(conn, **updates):
    writer=KaKshetraWriter();ctx=context(conn,**updates)
    steps=writer.plan_substeps(ctx)
    return [writer.run_substep(ctx,step) for step in steps]


def test_real_dispatch_replaces_only_candidate_class_and_records_counts(stored):
    before=stored.execute('SELECT to_jsonb(kala_field) AS row FROM kala_field ORDER BY id').fetchall()
    assert sum(r.rows_inserted for r in run(stored)) == 3
    assert sum(r.rows_inserted for r in run(stored)) == 3
    rows=stored.execute('SELECT * FROM kala_field_compact ORDER BY segment_index').fetchall()
    assert len(rows)==3
    assert all(r['risk_mask'] is None and r['risk_mask_reason']=='risk_set_not_specified' for r in rows)
    assert [(r['alpha'],r['gamma'],r['integral_days']) for r in rows] == [
        (r['alpha'],r['gamma'],r['integral_days']) for r in source_rows()]
    assert stored.execute('SELECT to_jsonb(kala_field) AS row FROM kala_field ORDER BY id').fetchall()==before
    assert stored.execute('SELECT generation FROM kala_layer_head').fetchone()['generation']=='retained:v1'
    grain=stored.execute("SELECT * FROM kala_layer_candidate_grain WHERE grain_key='ka_kshetra:compact:career_change'").fetchone()
    assert grain['result_state']=='rows' and len(grain['input_vector'])==64
    assert stored.execute('SELECT count(*) AS n FROM kala_field_candidate').fetchone()['n']==3


def test_dry_run_is_read_only_and_stale_source_requires_new_candidate(stored):
    run(stored,dry_run=True)
    assert stored.execute('SELECT count(*) AS n FROM kala_field_compact').fetchone()['n']==0
    run(stored)
    stored.execute('UPDATE kala_field_candidate SET alpha=alpha+0.125,integral_days=integral_days*exp(0.125)')
    with pytest.raises(ValueError,match='input.*changed'):
        run(stored)
    assert stored.execute('SELECT DISTINCT weights_version FROM kala_field_compact').fetchone()['weights_version']=='classical'


@pytest.mark.parametrize('mutation', ['wrong_build','published','head','no_source'])
def test_refuses_wrong_build_published_or_incomplete_source_before_write(stored,mutation):
    ctx=context(stored)
    if mutation=='wrong_build':ctx.build_id=str(uuid.uuid4())
    if mutation=='published':stored.execute("UPDATE kala_layer_candidate SET state='published'")
    if mutation=='head':stored.execute('UPDATE kala_layer_head SET generation=%s',(GEN,))
    if mutation=='no_source':stored.execute('DELETE FROM kala_field_candidate')
    writer=KaKshetraWriter()
    with pytest.raises((ValueError,RuntimeError)):
        steps=writer.plan_substeps(ctx)
        for step in steps:writer.run_substep(ctx,step)
    assert stored.execute('SELECT count(*) AS n FROM kala_field_compact').fetchone()['n']==0


@pytest.mark.parametrize('operation',['UPDATE','DELETE','identity','TRUNCATE'])
def test_database_guard_retains_published_coefficients_even_for_direct_sql(stored,operation):
    run(stored)
    stored.execute("UPDATE kala_layer_candidate SET state='published'")
    statements={'UPDATE':"UPDATE kala_field_compact SET alpha=0",
                'DELETE':'DELETE FROM kala_field_compact',
                'identity':"UPDATE kala_field_compact SET generation='other'",
                'TRUNCATE':'TRUNCATE kala_field_compact'}
    with pytest.raises(psycopg.Error):
        with stored.transaction():stored.execute(statements[operation])
    assert stored.execute('SELECT count(*) AS n FROM kala_field_compact').fetchone()['n']==3


@pytest.mark.parametrize('mutation',['no_snapshot','unfinalized','short_horizon'])
def test_requires_finalized_source_snapshot_and_complete_horizon(stored,mutation):
    if mutation=='no_snapshot':stored.execute('DELETE FROM kala_field_snapshots_candidate')
    if mutation=='unfinalized':stored.execute('UPDATE kala_field_snapshots_candidate SET field_content_hash=NULL')
    if mutation=='short_horizon':stored.execute('DELETE FROM kala_field_candidate WHERE segment_index=2')
    with pytest.raises((ValueError,RuntimeError)):
        run(stored)
    assert stored.execute('SELECT count(*) AS n FROM kala_field_compact').fetchone()['n']==0


def test_class_replay_keeps_another_class_and_another_generation(stored):
    run(stored)
    # A second building generation for the same chart must survive too.
    build2 = str(uuid.uuid4())
    stored.execute('INSERT INTO build_runs VALUES (%s,%s)',(build2,CHART))
    stored.execute("""INSERT INTO kala_layer_candidate
        (chart_id,generation,build_id,model_digest,rule_registry_version,conventions)
        VALUES (%s,'candidate:sibling',%s,'fixture','fixture','{}')""",(CHART,build2))
    stored.execute("""INSERT INTO kala_field_compact
        SELECT chart_id,'candidate:sibling',%s,event_class,segment_index,t_start,t_end,
        alpha,gamma,integral_days,refinement_depth,refinement_exhausted,refinement_residual,
        field_snapshot_id,weights_version,x_schema_version,risk_mask,risk_mask_reason
        FROM kala_field_compact""",(build2,))
    stored.execute("""INSERT INTO kala_field_compact
        SELECT chart_id,generation,build_id,'other_class',segment_index,t_start,t_end,
        alpha,gamma,integral_days,refinement_depth,refinement_exhausted,refinement_residual,
        field_snapshot_id,weights_version,x_schema_version,risk_mask,risk_mask_reason
        FROM kala_field_compact WHERE generation=%s""",(GEN,))
    before=stored.execute("""SELECT to_jsonb(kala_field_compact) AS row FROM kala_field_compact
        WHERE generation<>%s OR event_class<>'career_change' ORDER BY generation,event_class,segment_index""",(GEN,)).fetchall()
    run(stored)
    after=stored.execute("""SELECT to_jsonb(kala_field_compact) AS row FROM kala_field_compact
        WHERE generation<>%s OR event_class<>'career_change' ORDER BY generation,event_class,segment_index""",(GEN,)).fetchall()
    assert after==before and len(after)==6


def test_published_identity_cannot_escape_into_another_building_candidate(stored):
    run(stored)
    stored.execute("UPDATE kala_layer_candidate SET state='published'")
    build2 = str(uuid.uuid4())
    stored.execute('INSERT INTO build_runs VALUES (%s,%s)',(build2,CHART))
    stored.execute("""INSERT INTO kala_layer_candidate
        (chart_id,generation,build_id,model_digest,rule_registry_version,conventions)
        VALUES (%s,'candidate:escape',%s,'fixture','fixture','{}')""",(CHART,build2))
    # NEW alone would look mutable. The guard must inspect identity before the
    # candidate-state check, so a published row cannot be moved out of its head.
    with pytest.raises(psycopg.Error,match='identity'):
        with stored.transaction():
            stored.execute("UPDATE kala_field_compact SET generation='candidate:escape',build_id=%s",(build2,))
    assert stored.execute('SELECT count(*) AS n FROM kala_field_compact WHERE generation=%s',(GEN,)).fetchone()['n']==3
    assert stored.execute("SELECT count(*) AS n FROM kala_field_compact WHERE generation='candidate:escape'").fetchone()['n']==0
