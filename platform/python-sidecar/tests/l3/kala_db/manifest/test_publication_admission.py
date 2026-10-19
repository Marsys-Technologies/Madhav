"""K9-23 admission layer (SR-PREBUILD-ALL, SR-BOLD-04, SR-TEARDOWN-AUTHORITY-GATE 2).

Claims, one doctrine-grounded oracle each (the ruling is the source; B.10 -- measured, never a list kept in the code):
  C1  pre admits only assets outside the gochara surface and its dependents, post only inside it
  C2  the dependent set is transitive (ka_vighnakara via ka_sangam) and read from the registry rows
  C3  an unknown, blank, duplicated or empty asset list is refused
  C4  the probe gate stays on: a forcing NIRMANA_FORCE_EXECUTE is refused before any database or orchestrator call
  C5  an admitted rebuild delegates once to publication with the exact run and assets, and a refused one never does
  C6  each layer dry-run runs the real operation, rolls it back and reads the rollback back; dry_run_passed is earned
  C7  a refused layer operation is reported REFUSED with dry_run_passed false and changes nothing
"""
import argparse
import importlib
import json
import uuid
from pathlib import Path

import pytest

from services.kala_core import publication
from tests.l3.kala_db.manifest.test_publication_ops import (  # noqa: F401  (db is a fixture)
    accept, db, independent_digest, prepare, snapshot,
)

ADMISSION = importlib.import_module('services.kala_core.publication_admission')
DRAFT = Path(__file__).resolve().parents[6] / '00_ARCHITECTURE/control/registry_input_draft.json'
PRE = ['ka_yojaka', 'ka_vedha_gochara']
POST = ['ka_gochara', 'ka_gochara_v3_century_materialize', 'ka_gochara_v4_41_candidate', 'ka_gochara_v5',
        'ka_sangam', 'ka_vighnakara', 'ph_muhurta']


@pytest.fixture(scope='module')
def edges():
    # The committed registry reconstruction; the bold04 graph job measured this split on it (pre = ka_yojaka, ka_vedha_gochara).
    return {row['asset_id']: row['depends_on'] for row in json.loads(DRAFT.read_text())}


# ---------------------------------------------------------------- C1, C2, C3: the phase split


@pytest.mark.parametrize('asset', PRE)
def test_pre_admits_and_post_refuses_an_asset_outside_the_gochara_surface(edges, asset):
    assert ADMISSION.phase_refusal(edges, [asset], 'pre') is None
    assert asset in ADMISSION.phase_refusal(edges, [asset], 'post')


@pytest.mark.parametrize('asset', POST)
def test_post_admits_and_pre_refuses_the_gochara_surface_and_its_dependents(edges, asset):
    assert ADMISSION.phase_refusal(edges, [asset], 'post') is None
    assert asset in ADMISSION.phase_refusal(edges, [asset], 'pre')


def test_dependence_is_transitive_and_read_from_the_registry_rows():
    # ka_c reaches the surface only through ka_b; removing the ka_b edge from the rows must move it out of the post set.
    rows = {'ka_gochara_v5': [], 'ka_b': ['ka_gochara_v5'], 'ka_c': ['ka_b'], 'ka_d': []}
    assert ADMISSION.gochara_closure(rows) >= {'ka_b', 'ka_c'} and 'ka_d' not in ADMISSION.gochara_closure(rows)
    assert ADMISSION.phase_refusal(rows, ['ka_c'], 'post') is None
    rows['ka_b'] = []
    assert ADMISSION.phase_refusal(rows, ['ka_c'], 'post') is not None


@pytest.mark.parametrize('assets,phase', [
    (['ka_not_in_registry'], 'pre'), ([], 'pre'), ([''], 'pre'), (['ka_yojaka', 'ka_yojaka'], 'pre'), (['ka_yojaka'], 'both'),
])
def test_unknown_blank_duplicate_empty_assets_and_unknown_phase_are_refused(edges, assets, phase):
    assert ADMISSION.phase_refusal(edges, assets, phase)


# ---------------------------------------------------------------- C4: probe mode


@pytest.mark.parametrize('value,refused', [('1', True), ('true', True), (' YES ', True), ('0', False), ('', False), ('no', False)])
def test_force_execute_is_refused_exactly_when_the_orchestrator_would_force(value, refused):
    # runner.py execute_run: os.environ.get("NIRMANA_FORCE_EXECUTE", "").strip().lower() in ("1", "true", "yes")
    assert bool(ADMISSION.force_refusal({'NIRMANA_FORCE_EXECUTE': value})) is refused
    assert ADMISSION.force_refusal({}) is None


# ---------------------------------------------------------------- C5: the rebuild entry


class Session:
    def __init__(self, conn): self.conn = conn
    def __enter__(self): return self.conn
    def __exit__(self, typ, value, tb):
        if typ: self.conn.rollback()
        else: self.conn.commit()


def registry(db, rows):
    db.execute('CREATE TABLE asset_registry (asset_id text PRIMARY KEY, depends_on text[])')
    for asset, deps in rows.items():
        db.execute('INSERT INTO asset_registry VALUES (%s,%s)', (asset, deps))
    db.commit()


@pytest.fixture
def wired(db, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'guarded-local-publication-fixture')
    monkeypatch.delenv('NIRMANA_FORCE_EXECUTE', raising=False)
    monkeypatch.setattr(ADMISSION.psycopg, 'connect', lambda *a, **k: Session(db))
    yield db
    db.rollback()
    db.read_only = False


def run(argv, capsys):
    code = ADMISSION.main(argv)
    return code, json.loads(capsys.readouterr().out)


def test_admitted_rebuild_delegates_once_with_the_exact_run_and_assets(wired, monkeypatch, capsys):
    registry(wired, {'ga_positions': [], 'ka_gochara': ['ga_positions'], 'ka_sangam': ['ka_gochara']})
    c = prepare(wired, writers=('ka_gochara', 'ka_sangam'))
    calls = []
    def delegate(argv):
        calls.append(argv)
        print(json.dumps({'status': 'BUILD_COMPLETED', 'run_id': c.build_id}))
        return 0
    monkeypatch.setattr(publication, 'main', delegate)
    code, out = run(['rebuild', '--run-id', c.build_id, '--assets', 'ka_gochara,ka_sangam', '--phase', 'post'], capsys)
    assert code == 0 and calls == [['rebuild', '--run-id', c.build_id, '--assets', 'ka_gochara,ka_sangam']]
    assert out['status'] == 'BUILD_COMPLETED'
    assert out['admission'] == {'phase': 'post', 'assets': ['ka_gochara', 'ka_sangam'],
                                'probe_mode': 'delta_skip_gate', 'force_execute': False}


def test_phase_violation_is_refused_and_nothing_is_delegated(wired, monkeypatch, capsys):
    registry(wired, {'ga_positions': [], 'ka_gochara': ['ga_positions'], 'ka_sangam': ['ka_gochara']})
    c = prepare(wired, writers=('ka_gochara', 'ka_sangam'))
    monkeypatch.setattr(publication, 'main', lambda argv: pytest.fail('a refused rebuild must not be delegated'))
    code, out = run(['rebuild', '--run-id', c.build_id, '--assets', 'ka_gochara,ka_sangam', '--phase', 'pre'], capsys)
    assert code == 2 and out['status'] == 'REFUSED' and 'ka_gochara' in out['reason']


@pytest.mark.parametrize('operation', ['rebuild', 'rebuild-dryrun'])
def test_forcing_environment_is_refused_before_any_connection(operation, monkeypatch, capsys):
    monkeypatch.setenv('DATABASE_URL', 'never-used')
    monkeypatch.setenv('NIRMANA_FORCE_EXECUTE', '1')
    monkeypatch.setattr(ADMISSION.psycopg, 'connect', lambda *a, **k: pytest.fail('refusal precedes any connection'))
    monkeypatch.setattr(publication, 'main', lambda argv: pytest.fail('refusal precedes delegation'))
    code, out = run([operation, '--run-id', str(uuid.uuid4()), '--assets', 'ka_yojaka', '--phase', 'pre'], capsys)
    assert code == 2 and out['status'] == 'REFUSED' and 'NIRMANA_FORCE_EXECUTE' in out['reason']


def test_rebuild_dryrun_stays_plan_only_through_the_admission_layer(wired, monkeypatch, capsys):
    registry(wired, {'ga_positions': [], 'ka_yojaka': ['ga_positions']})
    c = prepare(wired, writers=('ka_yojaka',), chart=publication.CANONICAL_CHART)
    from pipeline.orchestrator import runner
    monkeypatch.setattr(runner, 'execute_run', lambda run_id: pytest.fail('a dry run never executes the orchestrator'))
    code, out = run(['rebuild-dryrun', '--run-id', c.build_id, '--assets', 'ka_yojaka', '--phase', 'pre'], capsys)
    assert code == 0 and out['status'] == 'PLAN_ONLY' and out['dry_run_passed'] is None
    assert out['admission']['phase'] == 'pre'
    wired.read_only = False


def test_phase_and_database_url_are_required(monkeypatch, capsys):
    with pytest.raises(SystemExit):
        ADMISSION.main(['rebuild', '--run-id', str(uuid.uuid4()), '--assets', 'ka_yojaka'])
    capsys.readouterr()
    monkeypatch.delenv('DATABASE_URL', raising=False)
    code, out = run(['rebuild', '--run-id', str(uuid.uuid4()), '--assets', 'ka_yojaka', '--phase', 'pre'], capsys)
    assert code == 2 and out['status'] == 'REFUSED'


# ---------------------------------------------------------------- C6, C7: the layer rehearsals


def canonical_candidate(db, generation, *, chart=publication.CANONICAL_CHART, accepted=True):
    c = prepare(db, generation, chart=chart)
    if accepted:
        accept(db, c)
        db.commit()
    return c


def verifier_role(db):
    from psycopg import sql
    if not db.execute("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='verifier_principal')").fetchone()[0]:
        db.execute('CREATE ROLE verifier_principal NOLOGIN')
    schema = db.execute('SELECT current_schema()').fetchone()[0]
    db.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO verifier_principal').format(sql.Identifier(schema)))
    db.execute('GRANT SELECT ON kala_layer_candidate_grain TO verifier_principal')
    db.execute('GRANT INSERT ON kala_layer_verification TO verifier_principal')
    db.execute('GRANT SELECT(chart_id,generation) ON kala_layer_verification TO verifier_principal')
    migration = Path(__file__).resolve().parents[5] / 'migrations/1390_kala_layer_operation_verifier_reads.sql'
    db.execute(migration.read_text().replace('public.', ''))
    db.commit()


def test_publish_rehearsal_publishes_inside_the_transaction_and_leaves_the_head_untouched(wired, capsys):
    c = canonical_candidate(wired, 'a')
    before = snapshot(wired)
    code, out = run(['publish-dryrun', '--run-id', c.build_id, '--generation', 'a', '--expected-head', 'NONE'], capsys)
    assert code == 0 and out['status'] == 'ROLLED_BACK'
    assert out['write_observed_in_transaction'] is True and out['rollback_confirmed'] is True and out['dry_run_passed'] is True
    assert out['operation_result']['status'] == 'PUBLISHED'
    assert snapshot(wired) == before and wired.execute('SELECT * FROM kala_layer_head').fetchall() == []


def test_rollback_rehearsal_restores_inside_the_transaction_and_leaves_the_head_untouched(wired, capsys):
    a = canonical_candidate(wired, 'a')
    publication.publish(wired, run_id=a.build_id, generation='a', expected_head=None)
    b = canonical_candidate(wired, 'b')
    publication.publish(wired, run_id=b.build_id, generation='b', expected_head='a')
    wired.commit()
    before = snapshot(wired)
    code, out = run(['rollback-dryrun', '--generation', 'a', '--expected-head', 'b'], capsys)
    assert code == 0 and out['dry_run_passed'] is True and out['operation_result']['status'] == 'ROLLED_BACK'
    assert snapshot(wired) == before
    assert wired.execute('SELECT generation FROM kala_layer_head').fetchone() == ('b',)


def test_verify_rehearsal_records_a_receipt_inside_the_transaction_only(wired, capsys):
    c = canonical_candidate(wired, 'a', accepted=False)
    verifier_role(wired)
    digest = independent_digest(c, wired)
    wired.execute('SET ROLE verifier_principal')
    wired.commit()
    try:
        code, out = run(['verify-dryrun', '--run-id', c.build_id, '--generation', 'a',
                         '--independently-derived-digest', digest], capsys)
    finally:
        wired.rollback()
        wired.execute('RESET ROLE')
        wired.commit()                                       # a session-level SET is undone by a later rollback
    assert code == 0 and out['dry_run_passed'] is True and out['operation_result']['status'] == 'INPUT_VERIFICATION_RECORDED'
    assert wired.execute('SELECT * FROM kala_layer_verification').fetchall() == []


def test_a_rehearsal_that_wrote_nothing_does_not_pass(wired, monkeypatch, capsys):
    c = canonical_candidate(wired, 'a')
    monkeypatch.setattr(publication, 'publish', lambda conn, **k: {'status': 'PUBLISHED'})
    code, out = run(['publish-dryrun', '--run-id', c.build_id, '--generation', 'a', '--expected-head', 'NONE'], capsys)
    assert code == 0 and out['write_observed_in_transaction'] is False and out['dry_run_passed'] is False


def test_a_rehearsal_whose_write_survives_the_rollback_does_not_pass(wired, monkeypatch, capsys):
    c = canonical_candidate(wired, 'a')
    real = publication.publish
    def committing(conn, **k):
        result = real(conn, **k)
        conn.commit()                                        # the write escapes the rehearsal's rollback
        return result
    monkeypatch.setattr(publication, 'publish', committing)
    code, out = run(['publish-dryrun', '--run-id', c.build_id, '--generation', 'a', '--expected-head', 'NONE'], capsys)
    assert code == 0 and out['rollback_confirmed'] is False and out['dry_run_passed'] is False


@pytest.mark.parametrize('case', ['absent', 'unverified', 'stale_head', 'other_chart'])
def test_a_refused_layer_operation_is_reported_refused_and_changes_nothing(wired, capsys, case):
    if case == 'other_chart':
        c = canonical_candidate(wired, 'a', chart=str(uuid.uuid4()))
    elif case == 'absent':
        c = argparse.Namespace(build_id=str(uuid.uuid4()))
    else:
        c = canonical_candidate(wired, 'a', accepted=case != 'unverified')
    expected = 'wrong' if case == 'stale_head' else 'NONE'
    before = snapshot(wired)
    code, out = run(['publish-dryrun', '--run-id', c.build_id, '--generation', 'a', '--expected-head', expected], capsys)
    assert code == 2 and out['status'] == 'REFUSED' and out['dry_run_passed'] is False
    assert snapshot(wired) == before
