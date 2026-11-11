"""Actual stored grain identity; independent acceptance/publication untouched."""
import json
import hashlib
import pytest
from psycopg.types.json import Jsonb

from test_g1a_candidate_storage import database, data  # noqa: F401
from services.ka_kshetra.g1_manifest import attest_snapshot
from services.ka_kshetra.candidate import CandidateConnection


@pytest.fixture
def attestation(data):
    conn, chart, build = data
    conn.execute("ALTER TABLE kala_layer_candidate ADD COLUMN model_digest text NOT NULL DEFAULT 'model', ADD COLUMN rule_registry_version text NOT NULL DEFAULT 'rules'")
    conn.execute('CREATE TABLE kala_layer_candidate_grain(chart_id uuid,generation text,grain_key text,result_state text,input_vector text,recorded_at timestamptz DEFAULT now(),PRIMARY KEY(chart_id,generation,grain_key))')
    conn.execute("INSERT INTO kala_layer_candidate_grain VALUES(%s,'candidate:g1','judge','rows','j1',now())", (chart,))
    pins = {'weights': 'w', 'corpus': 'c', 'config': {'as_of': '1984-02-05'}}
    def write():
        return attest_snapshot(CandidateConnection(conn, 'candidate:g1'), chart_id=chart,
            generation='candidate:g1', build_id=build, snapshot_id='snapshot',
            content_digest='content', pins=pins)
    return conn, chart, pins, write


@pytest.mark.parametrize('dependency', ['model_digest', 'rule_registry_version', 'conventions', 'pins'])
def test_attestation_binds_each_actual_persisted_dependency(attestation, dependency):
    conn, chart, pins, write = attestation
    original = write()
    # Independent canonical vector, read from persisted operands, not snapshot_vector.
    expected = {'snapshot_id': 'snapshot', 'content_digest': 'content', 'dependencies': {
        'model_digest': 'model', 'rule_registry_version': 'rules', 'conventions': {},
        'upstream_grains': [['judge', 'rows', 'j1']], 'pins': pins.copy()}}
    expected_digest = hashlib.sha256(json.dumps(expected, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    assert original['digest'] == expected_digest
    assert original['dependencies'] == expected['dependencies']
    if dependency == 'pins':
        pins['weights'] = 'new-weights'
    elif dependency == 'conventions':
        conn.execute('UPDATE kala_layer_candidate SET conventions=%s WHERE chart_id=%s AND generation=%s',
                     (Jsonb({'axis': 'birth-relative', 'as_of': '1984-02-05'}), chart, 'candidate:g1'))
    else:
        # Parameterized identifiers are a closed test-owned list above.
        conn.execute(f'UPDATE kala_layer_candidate SET {dependency}=%s WHERE chart_id=%s AND generation=%s',
                     ('changed', chart, 'candidate:g1'))
    changed = write()
    assert changed['digest'] != original['digest']
    stored = conn.execute("SELECT input_vector FROM kala_layer_candidate_grain WHERE chart_id=%s AND generation='candidate:g1' AND grain_key='ka_kshetra:snapshot'", (chart,)).fetchone()[0]
    assert json.loads(stored) == changed


def test_failed_upstream_refuses_attestation_and_preserves_existing_snapshot(attestation):
    conn, chart, pins, write = attestation
    original = write()
    conn.execute("UPDATE kala_layer_candidate_grain SET result_state='failed' WHERE chart_id=%s AND grain_key='judge'", (chart,))
    with pytest.raises(ValueError, match='failed upstream'):
        write()
    stored = conn.execute("SELECT input_vector FROM kala_layer_candidate_grain WHERE chart_id=%s AND grain_key='ka_kshetra:snapshot'", (chart,)).fetchone()[0]
    assert json.loads(stored) == original


def test_snapshot_vector_is_stored_candidate_scoped_and_changes_with_upstream(data):
    conn,chart,build=data
    # The G1a minimal fixture predates the manifest fields. Add their real shape
    # in this rolled-back test transaction; no application migration required.
    conn.execute("ALTER TABLE kala_layer_candidate ADD COLUMN model_digest text NOT NULL DEFAULT 'model', ADD COLUMN rule_registry_version text NOT NULL DEFAULT 'rules'")
    conn.execute('CREATE TABLE kala_layer_candidate_grain(chart_id uuid,generation text,grain_key text,result_state text,input_vector text,recorded_at timestamptz DEFAULT now(),PRIMARY KEY(chart_id,generation,grain_key))')
    conn.execute("INSERT INTO kala_layer_candidate_grain VALUES(%s,'candidate:g1','judge','rows','j1',now())",(chart,))
    scoped=CandidateConnection(conn,'candidate:g1')
    def write():
        return attest_snapshot(scoped,chart_id=chart,generation='candidate:g1',build_id=build,
            snapshot_id='snapshot',content_digest='content',pins={'weights':'w'})
    original=write(); assert write()==original
    stored=conn.execute("SELECT input_vector FROM kala_layer_candidate_grain WHERE chart_id=%s AND grain_key='ka_kshetra:snapshot'",(chart,)).fetchone()[0]
    assert json.loads(stored)==original
    conn.execute("UPDATE kala_layer_candidate_grain SET input_vector='j2' WHERE grain_key='judge'")
    assert write()['digest']!=original['digest']
    assert conn.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s',(chart,)).fetchone()==('candidate:old',)
    conn.execute("UPDATE kala_layer_candidate SET state='published' WHERE chart_id=%s AND generation='candidate:g1'",(chart,))
    with pytest.raises(ValueError,match='building'):
        write()
