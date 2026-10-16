"""K5-3 additive candidate persistence on the suite's guarded isolated database."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import uuid

import psycopg
from psycopg.types.json import Jsonb
import pytest

from services.kala_core.manifest import open_candidate
from services.ka_kshetra.g2_candidate import write_candidate
from services.ka_kshetra.g2_model import model_digest
from tests.l3.ka_kshetra.test_g2_model import model, risk, cells, value

ROOT = Path(__file__).resolve().parents[5]
MIGRATION = ROOT / 'migrations/1387_k5_g2_candidate_field.sql'


@pytest.fixture(scope='module')
def database(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as c:
        # Real prerequisite DDL; only its unrelated verifier role grants are omitted.
        base = (ROOT / 'migrations/1330_kala_layer_manifest_candidates.sql').read_text()
        c.execute(base.split('-- A separately dispatched verifier')[0])
        c.execute('CREATE TABLE kala_field(chart_id uuid, generation text, payload jsonb)')
        c.execute("INSERT INTO kala_field VALUES (%s,'legacy',%s)",
                  (str(uuid.uuid4()), Jsonb({'legacy': 'retained byte-for-byte'})))
        c.execute(MIGRATION.read_text())
        c.execute(MIGRATION.read_text())
    return isolated_kala_db_dsn


@pytest.fixture
def conn(database):
    with psycopg.connect(database) as c:
        yield c
        c.rollback()


def candidate(c, m=None, chart_id=None, generation=None):
    m = m or model()
    ca = open_candidate(c, chart_id=chart_id or str(uuid.uuid4()),
        generation=generation or 'candidate:g2:' + uuid.uuid4().hex,
        build_id=str(uuid.uuid4()), model_digest='fixture:layer-model',
        rule_registry_version='fixture:rules', conventions={
            'kshetra_g2': {'model_digests': {m.event_class: model_digest(m)},
                           'source_pin': 'fixture:upstream-source-pin', 'as_of_jd': 100.,
                           'prebuild_only': True}})
    ctx = SimpleNamespace(db_conn=c, build_id=ca.build_id,
                          config={'chart_id': ca.chart_id}, dry_run=False)
    return ca, ctx


def write(ctx, **kw):
    args = dict(model=model(), risk=risk(), cells=cells(), source_pin='fixture:upstream-source-pin')
    return write_candidate(ctx, **(args | kw))


def test_idempotent_candidate_write_preserves_legacy_published_head_and_other_partitions(conn):
    ca, ctx = candidate(conn)
    other, other_ctx = candidate(conn, chart_id=ca.chart_id)
    second, second_ctx = candidate(conn)
    conn.execute('INSERT INTO kala_layer_head(chart_id,generation) VALUES (%s,%s)',
                 (ca.chart_id, 'published:retained'))
    legacy = conn.execute('SELECT row_to_json(f)::text FROM kala_field f').fetchall()
    heads = conn.execute('SELECT row_to_json(h)::text FROM kala_layer_head h').fetchall()
    write(other_ctx); write(second_ctx)
    preserved = conn.execute('SELECT row_to_json(f)::text FROM kala_kshetra_g2_candidate f ORDER BY chart_id,generation').fetchall()
    assert write(ctx) == 1
    first = conn.execute('SELECT row_to_json(f)::text FROM kala_kshetra_g2_candidate f WHERE generation=%s', (ca.generation,)).fetchone()
    assert write(ctx) == 1
    assert conn.execute('SELECT row_to_json(f)::text FROM kala_kshetra_g2_candidate f WHERE generation=%s', (ca.generation,)).fetchone() == first
    assert conn.execute('SELECT row_to_json(f)::text FROM kala_kshetra_g2_candidate f WHERE generation<>%s ORDER BY chart_id,generation', (ca.generation,)).fetchall() == preserved
    assert conn.execute('SELECT row_to_json(f)::text FROM kala_field f').fetchall() == legacy
    assert conn.execute('SELECT row_to_json(h)::text FROM kala_layer_head h').fetchall() == heads


@pytest.mark.parametrize('mutation', ['state', 'head', 'build', 'source', 'model'])
def test_wrong_owner_or_pin_is_refused_before_replacement(conn, mutation):
    ca, ctx = candidate(conn)
    write(ctx)
    before = conn.execute('SELECT payload FROM kala_kshetra_g2_candidate').fetchall()
    kwargs = {}
    if mutation == 'state':
        conn.execute("UPDATE kala_layer_candidate SET state='published' WHERE generation=%s", (ca.generation,))
    elif mutation == 'head':
        conn.execute('INSERT INTO kala_layer_head VALUES (%s,%s,now())', (ca.chart_id, ca.generation))
    elif mutation == 'build':
        ctx.build_id = str(uuid.uuid4())
    elif mutation == 'source':
        kwargs['source_pin'] = 'changed'
    else:
        kwargs['model'] = replace(model(), model_id='changed')
    with pytest.raises((ValueError, LookupError)):
        write(ctx, **kwargs)
    assert conn.execute('SELECT payload FROM kala_kshetra_g2_candidate').fetchall() == before


def test_changed_input_requires_new_generation_and_caller_rollback_works(conn):
    ca, ctx = candidate(conn)
    write(ctx)
    before = conn.execute('SELECT payload FROM kala_kshetra_g2_candidate').fetchall()
    altered = {'r1': tuple(replace(x, terms={'count': value(99)}) for x in cells()['r1'])}
    with pytest.raises(ValueError, match='input'):
        write(ctx, cells=altered)
    assert conn.execute('SELECT payload FROM kala_kshetra_g2_candidate').fetchall() == before
    conn.rollback()
    assert conn.execute('SELECT count(*) FROM kala_kshetra_g2_candidate').fetchone() == (0,)


def test_dry_run_does_not_write_and_missing_candidate_never_falls_back(conn):
    ca, ctx = candidate(conn)
    ctx.dry_run = True
    assert write(ctx) == 0
    assert conn.execute('SELECT count(*) FROM kala_kshetra_g2_candidate').fetchone() == (0,)
    ctx.dry_run = False
    ctx.config['chart_id'] = str(uuid.uuid4())
    with pytest.raises(ValueError, match='chart'):
        write(ctx)


def test_direct_sql_cannot_mutate_published_or_unowned_partition(conn):
    ca, ctx = candidate(conn)
    write(ctx)
    conn.execute("UPDATE kala_layer_candidate SET state='published' WHERE generation=%s", (ca.generation,))
    for query, params in [
        ('DELETE FROM kala_kshetra_g2_candidate WHERE generation=%s', (ca.generation,)),
        ("UPDATE kala_kshetra_g2_candidate SET payload='{}'::jsonb WHERE generation=%s", (ca.generation,)),
    ]:
        with pytest.raises(psycopg.Error):
            with conn.transaction():
                conn.execute(query, params)
    assert conn.execute('SELECT count(*) FROM kala_kshetra_g2_candidate').fetchone() == (1,)


def test_migration_is_protected_additive_and_not_a_writer_activation():
    assert MIGRATION.name in (ROOT / 'scripts/kala_protected_migrations.txt').read_text().splitlines()
    text = MIGRATION.read_text().lower()
    assert 'update public.asset_registry' not in text
    assert 'kala_layer_head' in text
    assert 'prebuild_only' in text


def test_graph_features_reach_persisted_field_with_fact_and_rule_provenance(conn):
    from services.ka_kshetra.g2_candidate import write_graph_candidate
    from services.ka_kshetra.g2_features import FeatureSpec
    from tests.l3.ka_kshetra.test_g2_features import graph, edge
    ca, ctx = candidate(conn)
    raw = {'r1': tuple(replace(c, terms={}) for c in cells()['r1'])}
    assert write_graph_candidate(ctx, model=model(), risk=risk(), cells=raw,
        source_pin='fixture:upstream-source-pin', graph=graph(), relationships=(edge(),),
        available_fact_ids=('f1',), complete=True,
        feature_specs={'r1': (FeatureSpec('count', 'admitted_count', ('m1',), role='lord'),)}) == 1
    payload = conn.execute('SELECT payload FROM kala_kshetra_g2_candidate WHERE generation=%s', (ca.generation,)).fetchone()[0]
    operand = payload['inputs']['cells']['r1'][0]['terms']['count']
    assert operand['fact_ids'] == ['f1']
    assert operand['value'] == 1
    assert 'm1' in operand['source']
    assert payload['field']['integrated_hazard'] > 0
    assert payload['null_statistics'] is None


def test_input_ledger_includes_every_suppression_and_calibration_source(conn):
    from services.ka_kshetra.g2_model import Suppression
    from tests.l3.ka_kshetra.test_g2_model import calibration
    ca, ctx = candidate(conn)
    receipt = calibration(model())
    write(ctx, suppressions=(Suppression('s1','r1','reduced_intensity',value(.5)),), calibration=receipt)
    payload = conn.execute('SELECT payload FROM kala_kshetra_g2_candidate WHERE generation=%s', (ca.generation,)).fetchone()[0]
    assert payload['inputs']['suppressions'][0]['operand']['source'] == 'fixture:declared-input'
    assert payload['inputs']['calibration']['evaluation_id'] == receipt.evaluation_id


def test_manifest_cutoff_must_be_finite_and_not_a_boolean(conn):
    ca, ctx = candidate(conn)
    conn.execute("UPDATE kala_layer_candidate SET conventions=jsonb_set(conventions,'{kshetra_g2,as_of_jd}','true') WHERE generation=%s", (ca.generation,))
    with pytest.raises(ValueError, match='pin'):
        write(ctx)


@pytest.mark.parametrize('bad_pin', ['source', 'model'])
def test_sql_insert_must_match_manifest_source_and_model(conn, bad_pin):
    ca, ctx = candidate(conn)
    write(ctx)
    row = list(conn.execute('SELECT chart_id,generation,build_id,event_class,model_digest,input_digest,payload FROM kala_kshetra_g2_candidate WHERE generation=%s', (ca.generation,)).fetchone())
    payload = row[-1]
    if bad_pin == 'source':
        payload['source_pin'] = 'different-source'
    else:
        row[4] = '0'*64
        payload['field']['model_digest'] = row[4]
    row[-1] = Jsonb(payload)
    with pytest.raises(psycopg.Error):
        with conn.transaction():
            conn.execute('DELETE FROM kala_kshetra_g2_candidate WHERE generation=%s', (ca.generation,))
            conn.execute('INSERT INTO kala_kshetra_g2_candidate (chart_id,generation,build_id,event_class,model_digest,input_digest,payload) VALUES (%s,%s,%s,%s,%s,%s,%s)', row)
    assert conn.execute('SELECT count(*) FROM kala_kshetra_g2_candidate WHERE generation=%s', (ca.generation,)).fetchone() == (1,)


@pytest.mark.parametrize('state', ['building', 'published'])
def test_truncate_cannot_erase_candidate_or_published_rows(conn, state):
    ca, ctx = candidate(conn)
    write(ctx)
    conn.execute('UPDATE kala_layer_candidate SET state=%s WHERE generation=%s', (state, ca.generation))
    with pytest.raises(psycopg.Error):
        with conn.transaction():
            conn.execute('TRUNCATE kala_kshetra_g2_candidate')
    assert conn.execute('SELECT count(*) FROM kala_kshetra_g2_candidate').fetchone() == (1,)
