"""Real PostgreSQL chart/generation isolation and schema drift fingerprint oracles."""
from copy import deepcopy
from pathlib import Path
import json
import sys

import psycopg
import pytest

ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'platform/scripts/governance'))
A='00000000-0000-0000-0000-000000000001'
B='00000000-0000-0000-0000-000000000002'


@pytest.fixture
def db(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn) as conn:
        conn.execute('CREATE TABLE asset_registry(asset_id text PRIMARY KEY, depends_on text[])')
        conn.execute("INSERT INTO asset_registry VALUES ('ka_sangam', ARRAY['ka_yojaka'])")
        conn.execute('''CREATE TABLE kala_jury_candidate (
          chart_id uuid NOT NULL,generation text NOT NULL,event_class text NOT NULL,
          assertion_id text NOT NULL,payload jsonb, build_id text,
          PRIMARY KEY(chart_id,generation,event_class,assertion_id))''')
        conn.execute('''INSERT INTO kala_jury_candidate VALUES
          (%s,'candidate:one','career','same','{"value":1}','build1'),
          (%s,'candidate:two','career','same','{"value":2}','build2'),
          (%s,'candidate:one','career','same','{"value":3}','build3')''',(A,A,B))
        conn.commit()
        yield conn
        conn.execute('DROP TABLE kala_jury_candidate,asset_registry')
        conn.commit()


def decl():
    doc=json.loads((ROOT/'platform/scripts/governance/asset_declarations.json').read_text())
    value=deepcopy(doc['assets']['ka_sangam']['fingerprint'])
    value['tables']=value['tables'][:1]
    return value


def measure(conn,fp=None,chart=A):
    import kala_fingerprint_declarations as mod
    with conn.transaction():
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        return mod.fingerprint_asset(conn,'ka_sangam',decl() if fp is None else fp,chart)


def test_all_retained_generations_and_identity_are_hashed_but_other_charts_are_isolated(db):
    first=measure(db)
    assert first['coverage']=='partial' and first['production_certification'] is None
    assert first['tables']['kala_jury_candidate']['rows']==2
    db.execute("UPDATE kala_jury_candidate SET payload='{}' WHERE chart_id=%s",(B,)); db.commit()
    assert measure(db)==first
    db.execute("UPDATE kala_jury_candidate SET payload='{}' WHERE chart_id=%s AND generation='candidate:two'",(A,)); db.commit()
    assert measure(db)['sha256']!=first['sha256']
    semantic=measure(db)
    db.execute("UPDATE kala_jury_candidate SET build_id='changed' WHERE chart_id=%s",(A,)); db.commit()
    assert measure(db)['sha256']!=semantic['sha256']
    identity=measure(db)
    db.execute("UPDATE kala_jury_candidate SET generation='candidate:renamed' WHERE chart_id=%s AND generation='candidate:one'",(A,)); db.commit()
    assert measure(db)['sha256']!=identity['sha256']
    renamed=measure(db)
    db.execute("DELETE FROM kala_jury_candidate WHERE chart_id=%s AND generation='candidate:two'",(A,)); db.commit()
    assert measure(db)['sha256']!=renamed['sha256']


def test_new_columns_move_the_hash_and_schema_pin_and_registry_changes_move_registry_pin(db):
    first=measure(db)
    db.execute('ALTER TABLE kala_jury_candidate ADD COLUMN new_semantic text'); db.commit()
    second=measure(db)
    assert second['schema_sha256']!=first['schema_sha256']
    assert second['sha256']!=first['sha256']
    db.execute("UPDATE asset_registry SET depends_on=ARRAY['ka_yojaka','ga_dashas']"); db.commit()
    third=measure(db)
    assert third['registry_sha256']!=second['registry_sha256']
    assert third['sha256']==second['sha256']


def test_fingerprint_refuses_writable_transactions_and_bad_live_schema(db):
    import kala_fingerprint_declarations as mod
    with pytest.raises(ValueError,match='read.only'):
        mod.fingerprint_asset(db,'ka_sangam',decl(),A)
    db.rollback()
    db.execute('ALTER TABLE kala_jury_candidate DROP CONSTRAINT kala_jury_candidate_pkey'); db.commit()
    with pytest.raises(ValueError,match='key'):
        measure(db)


def test_measurement_receipt_binds_the_generated_writer_inventory_and_criterion_definition(db):
    import asset_census as ac
    import hashlib
    result=measure(db)
    path=ROOT/'platform/src/generated/nirmana-writer-digests.json'
    inventory=json.loads(path.read_text())
    assert result['writer_digest']==inventory['writers']['ka_sangam']
    assert result['inventory_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert result['criterion_sha256']==ac.registry_fingerprint()


def test_permuting_storage_order_keeps_the_same_semantic_fingerprint(db):
    first=measure(db)
    values=db.execute('SELECT chart_id,generation,event_class,assertion_id,payload::text,build_id FROM kala_jury_candidate').fetchall()
    db.execute('DELETE FROM kala_jury_candidate')
    for row in reversed(values):
        db.execute('INSERT INTO kala_jury_candidate VALUES (%s,%s,%s,%s,%s,%s)',row)
    db.commit()
    assert measure(db)==first
