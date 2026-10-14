"""K0A-R2: two real connections interleaved between validation and head CAS."""
from pathlib import Path
import hashlib
import json
import uuid

import psycopg
from psycopg import sql
import pytest

from services.kala_core.manifest import (
    CandidateNotPublishable, attest_grain, open_candidate, publish_candidate,
)


@pytest.fixture
def publication_connections(kala_db_dsn):
    schema = "k0a_publication_" + uuid.uuid4().hex
    with psycopg.connect(kala_db_dsn) as publisher, psycopg.connect(kala_db_dsn) as contender:
        publisher.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            for conn in (publisher, contender):
                conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            migration = (Path(__file__).resolve().parents[5]
                         / "migrations/1330_kala_layer_manifest_candidates.sql").read_text()
            tables = migration.split("-- A separately dispatched verifier", 1)[0]
            publisher.execute(tables.replace("public.", ""))
            publisher.commit()
            contender.commit()
            yield publisher, contender
        finally:
            contender.rollback()
            publisher.rollback()
            publisher.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            publisher.commit()


def prepared_candidate(conn):
    candidate = open_candidate(
        conn, chart_id=str(uuid.uuid4()), generation="candidate-a", build_id=str(uuid.uuid4()),
        model_digest="fixture", rule_registry_version="fixture", conventions={"fixture": True},
    )
    attest_grain(conn, candidate, grain_key="writer", result_state="rows", input_vector="A")
    digest = hashlib.sha256(json.dumps([("writer", "A")], separators=(",", ":")).encode()).hexdigest()
    conn.execute(
        "INSERT INTO kala_layer_verification "
        "(chart_id, generation, verifier_principal, result, detail) "
        "VALUES (%s, %s, 'verifier_principal', 'accepted', %s::jsonb)",
        (candidate.chart_id, candidate.generation, json.dumps({"input_digest": digest})),
    )
    conn.commit()
    return candidate


def test_competing_attestation_between_validation_and_cas_cannot_invalidate_publication(publication_connections):
    publisher, contender = publication_connections
    candidate = prepared_candidate(publisher)

    class InterleavedPublisher:
        mutation_blocked = False

        def execute(self, query, params=()):
            if query.startswith(("INSERT INTO kala_layer_head", "UPDATE kala_layer_head")):
                # No worker/thread is needed: lock_timeout observes whether the
                # second connection can mutate evidence while publication holds it.
                try:
                    with contender.transaction():
                        contender.execute("SET LOCAL lock_timeout = '100ms'")
                        attest_grain(contender, candidate, grain_key="writer",
                                     result_state="failed", input_vector="B")
                except psycopg.errors.LockNotAvailable:
                    self.mutation_blocked = True
                assert self.mutation_blocked, "evidence changed after validation and before head CAS"
            return publisher.execute(query, params)

    interleaved = InterleavedPublisher()
    with publisher.transaction():
        publish_candidate(interleaved, candidate, expected_grains=("writer",))
    assert interleaved.mutation_blocked
    with contender.transaction():
        with pytest.raises(CandidateNotPublishable, match="building"):
            attest_grain(contender, candidate, grain_key="writer", result_state="failed", input_vector="B")
    assert publisher.execute("SELECT state FROM kala_layer_candidate").fetchone() == ("published",)
    assert publisher.execute("SELECT result_state, input_vector FROM kala_layer_candidate_grain").fetchone() == ("rows", "A")
    assert publisher.execute("SELECT generation FROM kala_layer_head").fetchone() == (candidate.generation,)


def test_mutation_that_wins_the_lock_makes_publication_refuse(publication_connections):
    publisher, contender = publication_connections
    candidate = prepared_candidate(publisher)
    with contender.transaction():
        attest_grain(contender, candidate, grain_key="writer", result_state="failed", input_vector="B")
        with pytest.raises(psycopg.errors.LockNotAvailable):
            with publisher.transaction():
                publisher.execute("SET LOCAL lock_timeout = '100ms'")
                publish_candidate(publisher, candidate, expected_grains=("writer",))
    with pytest.raises(CandidateNotPublishable, match="writer"):
        publish_candidate(publisher, candidate, expected_grains=("writer",))
    assert publisher.execute("SELECT generation FROM kala_layer_head").fetchall() == []


@pytest.mark.parametrize('lock_winner', ['publication', 'attestation'])
def test_lifecycle_lock_is_shared_across_processes(publication_connections, kala_db_dsn, lock_winner):
    """A process-local mutex cannot satisfy the publication/evidence contract."""
    import subprocess
    import sys
    from psycopg.conninfo import make_conninfo

    publisher, contender = publication_connections
    candidate = prepared_candidate(publisher)
    schema = publisher.execute('SELECT current_schema()').fetchone()[0]
    publisher.commit()
    child_code = '''
import json, os, psycopg
from services.kala_core.manifest import Candidate, CandidateNotPublishable, attest_grain, publish_candidate
candidate = Candidate(**json.loads(os.environ['K0A_CANDIDATE']))
with psycopg.connect(os.environ['K0A_DSN']) as conn:
    conn.execute("SET LOCAL lock_timeout = '150ms'")
    try:
        if os.environ['K0A_ACTION'] == 'attest':
            attest_grain(conn, candidate, grain_key='writer', result_state='failed', input_vector='B')
        else:
            publish_candidate(conn, candidate, expected_grains=('writer',))
    except psycopg.errors.LockNotAvailable:
        conn.rollback()
        print('blocked')
    except CandidateNotPublishable:
        conn.rollback()
        print('refused')
    else:
        print('succeeded')
'''
    dsn = make_conninfo(kala_db_dsn, options=f'-c search_path={schema}')

    def child(action):
        run = subprocess.run(
            [sys.executable, '-B', '-c', child_code],
            cwd=Path(__file__).resolve().parents[4],
            env={'K0A_DSN': dsn, 'K0A_ACTION': action, 'PYTHONDONTWRITEBYTECODE': '1',
                 'K0A_CANDIDATE': json.dumps({
                     'chart_id': candidate.chart_id, 'generation': candidate.generation,
                     'build_id': candidate.build_id,
                     'expected_head_generation': candidate.expected_head_generation,
                 })},
            capture_output=True, text=True, timeout=5,
        )
        assert run.returncode == 0, run.stderr
        return run.stdout.strip()

    if lock_winner == 'publication':
        with publisher.transaction():
            publish_candidate(publisher, candidate, expected_grains=('writer',))
            assert child('attest') == 'blocked'
        assert child('attest') == 'refused'
        assert publisher.execute('SELECT state FROM kala_layer_candidate').fetchall() == [('published',)]
        assert publisher.execute('SELECT result_state, input_vector FROM kala_layer_candidate_grain').fetchall() == [('rows', 'A')]
        assert publisher.execute('SELECT generation FROM kala_layer_head').fetchall() == [(candidate.generation,)]
    else:
        with contender.transaction():
            attest_grain(contender, candidate, grain_key='writer', result_state='failed', input_vector='B')
            assert child('publish') == 'blocked'
        assert child('publish') == 'refused'
        assert publisher.execute('SELECT generation FROM kala_layer_head').fetchall() == []
        assert publisher.execute('SELECT result_state, input_vector FROM kala_layer_candidate_grain').fetchall() == [('failed', 'B')]
