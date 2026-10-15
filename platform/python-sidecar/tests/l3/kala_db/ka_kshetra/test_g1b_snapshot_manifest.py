"""Actual stored grain identity; independent acceptance/publication untouched."""
import json
import pytest

from test_g1a_candidate_storage import database, data  # noqa: F401
from services.ka_kshetra.g1_manifest import attest_snapshot
from services.ka_kshetra.candidate import CandidateConnection


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
