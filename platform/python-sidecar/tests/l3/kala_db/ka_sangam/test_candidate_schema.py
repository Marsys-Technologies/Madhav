"""Additive schema, protected routing and candidate partition mutation oracles."""
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb
import pytest
from tests.l3.kala_db.conftest import kala_db_dsn

ROOT=Path(__file__).parents[5]
MIGRATION=ROOT/'migrations/1350_kala_jury_candidate.sql'
CHART=str(uuid4()); CHART2=str(uuid4())
GEN='candidate:fixture:1'
LEGACY_COLUMNS=('convergence_id','chart_id','window_start','window_end','convergence_score',
 'constituent_factors','source_citation','computed_at','signal_id','mode','peak_date',
 'orb_strength','rarity_years','confidence_score','confidence_label','independent_current_count',
 'is_off_dasha_discovery','horizon_tier','domain','confidence_label_relative','tier_basis')


def test_additive_migration_exists_and_is_protected():
    assert MIGRATION.exists(), 'K4 candidate migration absent on base'
    assert MIGRATION.name in (ROOT/'scripts/kala_protected_migrations.txt').read_text().splitlines()


@pytest.fixture(scope='module')
def database(kala_db_dsn):
    assert MIGRATION.exists(), 'K4 candidate migration absent on base'
    with psycopg.connect(kala_db_dsn) as c:
        c.execute('CREATE TABLE charts(id uuid PRIMARY KEY)')
        c.execute('CREATE TABLE kala_layer_candidate(chart_id uuid NOT NULL REFERENCES charts(id), generation text NOT NULL, PRIMARY KEY(chart_id,generation))')
        c.execute('CREATE TABLE kala_layer_head(chart_id uuid PRIMARY KEY,generation text NOT NULL)')
        # The legacy reader projection retains every column from brief.contract.
        c.execute('CREATE TABLE kala_convergence ('+','.join(x+' text' for x in LEGACY_COLUMNS)+')')
        c.execute('INSERT INTO kala_convergence VALUES ('+','.join(['%s']*len(LEGACY_COLUMNS))+')',LEGACY_COLUMNS)
        c.execute('INSERT INTO charts VALUES (%s),(%s)',(CHART,CHART2))
        c.execute('INSERT INTO kala_layer_candidate VALUES (%s,%s),(%s,%s),(%s,%s)',(CHART,GEN,CHART,'candidate:fixture:2',CHART2,GEN))
        c.execute('INSERT INTO kala_layer_head VALUES (%s,%s)',(CHART,'published:legacy'))
        before=c.execute('SELECT row_to_json(x)::text FROM kala_convergence x').fetchall()
        head=c.execute('SELECT * FROM kala_layer_head').fetchall()
        c.execute(MIGRATION.read_text())
        assert c.execute('SELECT row_to_json(x)::text FROM kala_convergence x').fetchall()==before
        assert c.execute('SELECT * FROM kala_layer_head').fetchall()==head
    return kala_db_dsn


@pytest.fixture
def conn(database):
    with psycopg.connect(database) as c:
        yield c
        c.rollback()


def insert(c,**updates):
    values=dict(chart_id=CHART,generation=GEN,event_class='career',assertion_id='jury:1',
      window_start='2026-01-01Z',window_end='2026-02-01Z',subject=Jsonb({'affected_person':'native'}),
      roots=Jsonb({'contact_ids':['contact:1']}),provenance=Jsonb({'rule':'fixture'}),
      coverage=Jsonb({'searched':True}),evidence_graph=Jsonb([{'root_id':'contact:1','role':'corroborates','selected':False}]),
      witness_groups=Jsonb([{'group_id':'G-P','status':'available'}]),witness_signature=Jsonb(['G-P']),
      conditional_null=Jsonb({'estimand':'jury_incremental_agreement','denominator':32,'verdict':'insufficient_evidence','reason':'zero_null_variance'}),
      pipeline_null_reason='whole_pipeline_selector_not_supplied',null_reason='zero_null_variance')
    values.update(updates)
    c.execute('INSERT INTO kala_jury_candidate ('+','.join(values)+') VALUES ('+','.join(['%s']*len(values))+')',tuple(values.values()))


def test_legacy_columns_rows_and_published_head_byte_compatible(conn):
    before=conn.execute('SELECT row_to_json(x)::text FROM kala_convergence x').fetchall()
    head=conn.execute('SELECT * FROM kala_layer_head').fetchall()
    conn.execute(MIGRATION.read_text())
    insert(conn)
    assert conn.execute('SELECT row_to_json(x)::text FROM kala_convergence x').fetchall()==before
    assert conn.execute('SELECT * FROM kala_layer_head').fetchall()==head
    assert tuple(x[0] for x in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name='kala_convergence' ORDER BY ordinal_position"))==LEGACY_COLUMNS


def test_partition_identity_includes_chart_generation_and_class(conn):
    insert(conn);insert(conn,generation='candidate:fixture:2');insert(conn,event_class='family');insert(conn,chart_id=CHART2)
    assert conn.execute('SELECT count(*) FROM kala_jury_candidate').fetchone()[0]==4
    with pytest.raises(psycopg.errors.UniqueViolation):
        insert(conn)


def test_scoped_replacement_and_rollback_reapply_leave_other_partitions(conn):
    insert(conn);insert(conn,event_class='family');insert(conn,generation='candidate:fixture:2');insert(conn,chart_id=CHART2)
    before=conn.execute('SELECT chart_id,generation,event_class,assertion_id FROM kala_jury_candidate ORDER BY 1,2,3,4').fetchall()
    with conn.transaction():
        conn.execute('SAVEPOINT oracle')
        conn.execute('DELETE FROM kala_jury_candidate WHERE chart_id=%s AND generation=%s AND event_class=%s',(CHART,GEN,'career'))
        insert(conn)
        assert conn.execute('SELECT chart_id,generation,event_class,assertion_id FROM kala_jury_candidate ORDER BY 1,2,3,4').fetchall()==before
        conn.execute('ROLLBACK TO SAVEPOINT oracle')
    conn.execute(MIGRATION.read_text())
    assert conn.execute('SELECT chart_id,generation,event_class,assertion_id FROM kala_jury_candidate ORDER BY 1,2,3,4').fetchall()==before


@pytest.mark.parametrize('changes',[
    {'generation':'published:legacy'}, {'window_end':'2026-01-01Z'},
    {'roots':Jsonb({}),'null_reason':None}, {'witness_signature':Jsonb(['G-UNKNOWN'])},
    {'conditional_null':Jsonb({'estimand':'whole_pipeline_selection','denominator':32,'verdict':'fail'})},
    {'conditional_null':Jsonb({'estimand':'jury_incremental_agreement','denominator':0,'verdict':'fail'})},
    {'conditional_null':Jsonb({'estimand':'jury_incremental_agreement','denominator':32})},
    {'conditional_null':Jsonb({'estimand':'jury_incremental_agreement','verdict':'fail'})},
    {'conditional_null':Jsonb({'estimand':'jury_incremental_agreement','denominator':32,'verdict':'pass','reason':'zero_null_variance'})},
    {'null_reason':None},
    {'witness_signature':Jsonb(['G-A'])},
    {'pipeline_null_reason':None},
    {'pipeline_null':Jsonb({'estimand':'jury_incremental_agreement'}),'pipeline_null_reason':None},
])
def test_invalid_candidate_or_null_estimand_is_rejected(conn,changes):
    with pytest.raises(psycopg.errors.CheckViolation):
        insert(conn,**changes)


def test_candidate_must_belong_to_registered_generation(conn):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        insert(conn,generation='candidate:not_registered')


def test_half_open_segment_and_contest_payload_checks(conn):
    insert(conn)
    conn.execute("INSERT INTO kala_jury_candidate_segment VALUES (%s,%s,'career','jury:1','2026-01-01Z','2026-01-02Z','[\"G-P\"]','{\"G-P\":[\"contact:1\"]}')",(CHART,GEN))
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("INSERT INTO kala_jury_candidate_segment VALUES (%s,%s,'career','jury:1','2026-01-02Z','2026-01-02Z','[\"G-P\"]','{}')",(CHART,GEN))
