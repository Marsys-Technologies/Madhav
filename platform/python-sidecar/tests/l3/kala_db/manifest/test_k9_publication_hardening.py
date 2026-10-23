"""SR-K9-PUBLISHABLE (D1, D4, D5, D8) -- one doctrine-grounded oracle per distinct production claim, each with ONE planted reversion that fails.

Source of each claim: the ruling SR-K9-PUBLISHABLE (DECISIONS_SURROGATE.jsonl) and the K9 rehearsal K9_REHEARSAL.md §7. The reversion of a claim is a copy of
the production module with that claim's line reverted (``mutated``); the oracle passes on the real module and fails on the copy (root CLAUDE.md §N.8).

  D1a the rebuild kind needs no --phase: ONE run over a plan on both sides of the gochara flip is admitted and delegated exactly as given
  D1b the --phase argument no longer exists (the split code path is gone, not merely optional)
  D1c an unknown asset is refused by the registry check and nothing is delegated
  D4  publication's refusal names the writer(s) lacking a grain (K9_REHEARSAL D4: "the refusal does not name ka_yojaka")
  D5a the rebuild's stdout is ONE JSON document carrying the admission block (probe_mode / force_execute) even when the orchestrator prints [event] lines
  D5b those lines are kept as evidence on stderr, not discarded
  D5c a delegate that printed no result document is reported FAILED with a non-zero exit, never as a pass
  D8a a FAILED run's teardown restores the stale/error rows the run itself wrote (events.state_change audit trail), real staleness / terminal-error writers
  D8b it leaves alone a row the run did not write (stale before the run, or changed since by someone else)
  D8c only a FAILED run restores: a completed run's teardown leaves its (legitimate) stale flips
  D8d a role that cannot read the audit trail refuses before anything is deleted (N.7.6: an honest refusal, not a guess)
  D8e the real kind commits and reads the restored states back from the database
  D8f the executor table enables the teardown pair on the admission module (W5W6 WP2, shard K9-4b, ruling S-1); signed-only is X1 of test_executor_mechanical_production.py
"""
import contextlib
import importlib.util
import io
import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from services.kala_core import publication, rebuild_control
from tests.l3.kala_db.manifest.test_publication_admission import ADMISSION, registry, run, wired  # noqa: F401  (wired, db are fixtures)
from tests.l3.kala_db.manifest.test_publication_ops import accept, db, prepare, snapshot  # noqa: F401
from tests.l3.kala_db.manifest.test_rebuild_control import CHART, asset_state_tables, make_run

REPO = Path(__file__).resolve().parents[6]
OPS = REPO / '00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json'


def mutated(module, tmp_path, old, new):
    """A copy of ``module`` with ONE line reverted (the planted reversion)."""
    source = Path(module.__file__).read_text()
    assert source.count(old) == 1, f'reversion anchor is not unique: {old!r}'
    path = tmp_path / ('mutated_' + Path(module.__file__).name)
    path.write_text(source.replace(old, new))
    spec = importlib.util.spec_from_file_location('mutated_' + module.__name__.replace('.', '_'), path)
    copy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(copy)
    return copy


def cli(module, argv, capsys):
    """(exit code, stdout document, stderr); an argparse refusal is an AssertionError of the oracle, never a crash of the harness."""
    try:
        code = module.main(argv)
    except SystemExit as exc:
        raise AssertionError(f'argument parser refused {argv}: {exc.code}')
    captured = capsys.readouterr()
    return code, json.loads(captured.out), captured.err


REAL, REVERTED = False, True
BOTH = pytest.mark.parametrize('reverted', [REAL, REVERTED], ids=['real', 'planted_reversion'])


def verdict(reverted, oracle, module, tmp_path, old, new, *args):
    """The oracle passes on the real module (``reverted`` False) and fails, by its own assertion, on the copy with the claim's line reverted."""
    if not reverted:
        return oracle(module, *args)
    with pytest.raises(AssertionError):
        oracle(mutated(module, tmp_path, old, new), *args)


# ---------------------------------------------------------------- D1: single-phase rebuild


MIXED = 'ka_yojaka,ka_gochara,ka_sangam,ka_vighnakara'        # pre-flip, gochara and its dependents together: the K9 in-scope shape
REGISTRY = {'ga_positions': [], 'ka_yojaka': ['ga_positions'], 'ka_gochara': ['ka_yojaka'], 'ka_sangam': ['ka_gochara'], 'ka_vighnakara': ['ka_sangam']}


def delegating(calls, c):
    def delegate(argv):
        calls.append(argv)
        print(json.dumps({'status': 'BUILD_COMPLETED', 'run_id': c.build_id}))
        return 0
    return delegate


def d1a(module, wired, monkeypatch, capsys):
    registry(wired, REGISTRY)
    wired.execute('CREATE TABLE kala_convergence (convergence_id bigserial PRIMARY KEY, generation text)')      # ka_sangam is in the plan: 1405 applied
    wired.commit()
    c = prepare(wired, writers=tuple(MIXED.split(',')))
    calls = []
    monkeypatch.setattr(publication, 'main', delegating(calls, c))
    code, out, _ = cli(module, ['rebuild', '--run-id', c.build_id, '--assets', MIXED], capsys)
    assert code == 0 and calls == [['rebuild', '--run-id', c.build_id, '--assets', MIXED]] and out['status'] == 'BUILD_COMPLETED'
    assert 'phase' not in out['admission']


def d1b(module, capsys):
    for operation in ('rebuild', 'rebuild-dryrun'):
        try:
            module.main([operation, '--run-id', str(uuid.uuid4()), '--assets', 'ka_yojaka', '--phase', 'pre'])
        except SystemExit:
            capsys.readouterr()
            continue
        raise AssertionError(f'{operation} still accepts --phase')


def d1c(module, wired, monkeypatch, capsys):
    registry(wired, REGISTRY)
    c = prepare(wired, writers=('ka_yojaka',))
    def delegated(argv):
        raise AssertionError('a refused rebuild must not be delegated')
    monkeypatch.setattr(publication, 'main', delegated)
    code, out, _ = cli(module, ['rebuild', '--run-id', c.build_id, '--assets', 'ka_yojaka,ka_nowhere'], capsys)
    assert code == 2 and out['status'] == 'REFUSED' and 'ka_nowhere' in out['reason']


PHASE_REQUIRED = ("p.add_argument('--assets', required=True)\n", "p.add_argument('--assets', required=True)\n            p.add_argument('--phase', required=True)\n")
PHASE_OPTIONAL = ("p.add_argument('--assets', required=True)\n", "p.add_argument('--assets', required=True)\n            p.add_argument('--phase')\n")
NO_REGISTRY_CHECK = ("unknown = [a for a in assets if a not in edges]", "unknown = []")


@BOTH
def test_d1a_a_plan_on_both_sides_of_the_flip_is_admitted_without_a_phase(wired, monkeypatch, capsys, tmp_path, reverted):
    # reversion: the kind demands --phase again (the withdrawn SR-BOLD-04 split's argument)
    verdict(reverted, d1a, ADMISSION, tmp_path, *PHASE_REQUIRED, wired, monkeypatch, capsys)


@BOTH
def test_d1b_the_phase_argument_is_gone(capsys, tmp_path, reverted):
    # reversion: --phase accepted again, optionally
    verdict(reverted, d1b, ADMISSION, tmp_path, *PHASE_OPTIONAL, capsys)


@BOTH
def test_d1c_an_unknown_asset_is_refused_by_the_registry_check(wired, monkeypatch, capsys, tmp_path, reverted):
    # reversion: the registry membership check is dropped
    verdict(reverted, d1c, ADMISSION, tmp_path, *NO_REGISTRY_CHECK, wired, monkeypatch, capsys)


# ---------------------------------------------------------------- D4: the refusal names the writer


def d4(module, db):
    c = prepare(db)                                                   # ka_yojaka and ka_sangam, one grain each
    db.execute("DELETE FROM kala_layer_candidate_grain WHERE grain_key = 'ka_sangam:inputs'")
    accept(db, c)
    before = snapshot(db)
    with pytest.raises(ValueError) as raised:
        module.publish(db, run_id=c.build_id, generation=c.generation, expected_head=None)
    message = str(raised.value)
    assert 'ka_sangam' in message and 'ka_yojaka' not in message.split('writers lacking a grain:')[-1].split(';')[0]
    assert 'ka_sangam:inputs' in message and snapshot(db) == before


@BOTH
def test_d4_the_refusal_names_the_writer_lacking_a_grain(db, tmp_path, reverted):
    # reversion: the generic message of publication.py before this change
    verdict(reverted, d4, publication, tmp_path, "raise CandidateNotPublishable(_grain_refusal(absent,unplanned,failed))",
            "raise CandidateNotPublishable('candidate has absent, unplanned or failed grains')", db)


@pytest.mark.parametrize('defect,expected', [('failed', 'failed grains: ka_sangam:inputs'), ('unplanned', 'unplanned grains: ka_sangam:unplanned')])
def test_d4_failed_and_unplanned_grains_are_named_with_their_keys(db, defect, expected):
    c = prepare(db)
    if defect == 'failed':
        db.execute("UPDATE kala_layer_candidate_grain SET result_state='failed' WHERE grain_key='ka_sangam:inputs'")
    else:
        from services.kala_core.manifest import attest_grain
        attest_grain(db, c, grain_key='ka_sangam:unplanned', result_state='rows', input_vector='extra')
    accept(db, c)
    with pytest.raises(ValueError, match=expected):
        publication.publish(db, run_id=c.build_id, generation=c.generation, expected_head=None)


# ---------------------------------------------------------------- D5: one JSON document, events on stderr


def noisy_delegate(c, *, result=True):
    """What the real rebuild prints: the orchestrator's own [event] lines (events.emit_event with Pub/Sub off) and then the result."""
    def delegate(argv):
        from pipeline.orchestrator import events
        print('import-time banner from a writer')
        events.emit_event({'type': 'asset.state_change', 'asset_id': 'ka_yojaka', 'from_state': 'queued', 'to_state': 'building'})
        events.emit_event({'type': 'asset.state_change', 'asset_id': 'ka_yojaka', 'from_state': 'building', 'to_state': 'lit'})
        if result:
            print(json.dumps({'status': 'BUILD_COMPLETED', 'run_id': c.build_id}, sort_keys=True))
        return 0
    return delegate


def d5(module, wired, monkeypatch, capsys, operation, flag):
    monkeypatch.setenv('PUBSUB_DISABLED', '1')
    registry(wired, {'ga_positions': [], 'ka_yojaka': ['ga_positions']})
    c = prepare(wired, writers=('ka_yojaka',), chart=publication.CANONICAL_CHART)
    monkeypatch.setattr(publication, 'main', noisy_delegate(c))
    code = module.main([operation, '--run-id', c.build_id, '--assets', 'ka_yojaka', *flag])
    out = capsys.readouterr()
    assert code == 0
    document = json.loads(out.out)                                    # stdout is exactly ONE document: the receipt parser (json.loads of the output) reads it
    assert document['status'] == 'BUILD_COMPLETED'
    forced = bool(flag)
    assert document['admission'] == {'assets': ['ka_yojaka'], 'probe_mode': 'force_execute' if forced else 'delta_skip_gate', 'force_execute': forced}
    return out.err


EVENTS_NOT_PARSED = ("        if isinstance(document, dict):\n            return document, lines[:index] + lines[index + 1:]",
                     "        if isinstance(document, dict) and len(lines) == 1:\n            return document, []")
EVENTS_DROPPED = ("        if rest:\n            print('\\n'.join(rest), file=sys.stderr)", "        if False:\n            pass")


@BOTH
@pytest.mark.parametrize('operation,flag', [('rebuild', ['--force-execute']), ('rebuild', []), ('rebuild-dryrun', [])])
def test_d5a_the_receipt_output_is_one_document_with_the_admission_block(wired, monkeypatch, capsys, tmp_path, operation, flag, reverted):
    # reversion: the result is only recognised when it is the whole captured text (the pre-change parse), so event lines hide it
    verdict(reverted, d5, ADMISSION, tmp_path, *EVENTS_NOT_PARSED, wired, monkeypatch, capsys, operation, flag)


def d5b(module, wired, monkeypatch, capsys):
    stderr = d5(module, wired, monkeypatch, capsys, 'rebuild', ['--force-execute'])
    assert stderr.count('[event] ') == 2 and 'import-time banner from a writer' in stderr


@BOTH
def test_d5b_the_orchestrator_events_are_kept_as_evidence_on_stderr(wired, monkeypatch, capsys, tmp_path, reverted):
    # reversion: the non-result lines are discarded
    verdict(reverted, d5b, ADMISSION, tmp_path, *EVENTS_DROPPED, wired, monkeypatch, capsys)


def d5c(module, wired, monkeypatch, capsys):
    registry(wired, {'ga_positions': [], 'ka_yojaka': ['ga_positions']})
    c = prepare(wired, writers=('ka_yojaka',), chart=publication.CANONICAL_CHART)
    monkeypatch.setenv('PUBSUB_DISABLED', '1')
    monkeypatch.setattr(publication, 'main', noisy_delegate(c, result=False))
    code, out, _ = cli(module, ['rebuild', '--run-id', c.build_id, '--assets', 'ka_yojaka'], capsys)
    assert out['status'] == 'FAILED' and 'no JSON result' in out['reason'] and code != 0 and 'admission' not in out


@BOTH
def test_d5c_a_delegate_without_a_result_document_is_failed_not_passed(wired, monkeypatch, capsys, tmp_path, reverted):
    # reversion: the exit status of the silent delegate (0) is passed through
    verdict(reverted, d5c, ADMISSION, tmp_path, "        return code or 3\n", "        return code\n", wired, monkeypatch, capsys)


# ---------------------------------------------------------------- D8: the failed run's asset states


RUN_ASSETS = ['ka_yojaka', 'ka_sangam']
DOWNSTREAM = [{'asset_id': 'ka_yojaka', 'depends_on': []}, {'asset_id': 'ka_sangam', 'depends_on': ['ka_yojaka']},
              {'asset_id': 'ka_kshetra', 'depends_on': ['ka_yojaka']}, {'asset_id': 'mi_bhara', 'depends_on': ['ka_yojaka']},
              {'asset_id': 'ka_old_stale', 'depends_on': ['ka_yojaka']}, {'asset_id': 'ka_hand_edited', 'depends_on': []},
              {'asset_id': 'ka_edited_after', 'depends_on': ['ka_yojaka']}]
BEFORE = {'ka_yojaka': 'lit', 'ka_sangam': 'lit', 'ka_kshetra': 'lit', 'mi_bhara': 'service_ok', 'ka_old_stale': 'stale',
          'ka_hand_edited': 'lit', 'ka_edited_after': 'lit'}


def states(conn):
    return dict(conn.execute('SELECT asset_id, state FROM asset_throughput WHERE chart_id = %s', (CHART,)).fetchall())


def failed_run(conn, state='failed'):
    """A run that left the real writers' marks: staleness.propagate_downstream_staleness (lit/service_ok -> stale) and
    runner._mark_asset_error_terminal (the failing asset -> error), written over a connection that carries the orchestrator's GUC (db.connect)."""
    from pipeline.orchestrator import runner, staleness
    c = make_run(conn, state)
    asset_state_tables_ready = conn.execute("SELECT to_regclass('build_run_assets')").fetchone()[0]
    if asset_state_tables_ready is None:
        conn.execute('CREATE TABLE build_run_assets (run_id uuid, asset_id text, state text, error text, ended_at timestamptz, disposition text, '
                     'blocked_by_asset_id text, output_changed boolean)')
    conn.execute('INSERT INTO build_run_assets (run_id, asset_id, state) VALUES (%s, %s, %s), (%s, %s, %s)',
                 (c.build_id, 'ka_yojaka', 'complete', c.build_id, 'ka_sangam', 'queued'))
    for asset, st in BEFORE.items():
        conn.execute('INSERT INTO asset_throughput (chart_id, asset_id, state) VALUES (%s, %s, %s)', (CHART, asset, st))
    conn.execute("UPDATE build_runs SET started_at = now() - interval '1 hour', ended_at = now() + interval '1 hour' WHERE id = %s", (c.build_id,))
    conn.commit()
    conn.execute("SET marsys.triggered_by = 'asset_runner'")
    cur = conn.cursor()
    cur.execute("UPDATE asset_throughput SET state = 'building' WHERE chart_id = %s AND asset_id = 'ka_sangam'", (CHART,))
    with contextlib.redirect_stdout(io.StringIO()):                    # the orchestrator's own [event] lines are not this fixture's output
        staleness.propagate_downstream_staleness(conn, cur, CHART, 'ka_yojaka', set(RUN_ASSETS), DOWNSTREAM, lambda event: None, c.build_id)
        runner._mark_asset_error_terminal(conn, cur, c.build_id, CHART, 'ka_sangam', 'writer raised')
    conn.commit()
    # what the run did not write: a hand edit inside the window (no orchestrator GUC), and a change made after the run's last write
    conn.execute("RESET marsys.triggered_by")
    conn.execute("UPDATE asset_throughput SET state = 'stale' WHERE chart_id = %s AND asset_id = 'ka_hand_edited'", (CHART,))
    conn.execute("UPDATE asset_throughput SET state = 'error' WHERE chart_id = %s AND asset_id = 'ka_edited_after'", (CHART,))
    conn.commit()
    return c


@pytest.fixture
def stale_world(db):
    db.execute('ALTER TABLE build_runs ADD COLUMN stop_requested_at timestamptz')
    db.execute('CREATE TABLE ka_dep_candidate (chart_id uuid NOT NULL, generation text NOT NULL, v int NOT NULL, '
               'FOREIGN KEY (chart_id, generation) REFERENCES kala_layer_candidate (chart_id, generation))')
    asset_state_tables(db)
    return db


def d8a(module, conn):
    c = failed_run(conn)
    marked = states(conn)
    assert marked['ka_sangam'] == 'error' and marked['ka_kshetra'] == 'stale' and marked['mi_bhara'] == 'stale', 'premise: the real writers left their marks'
    result = module.teardown(conn, run_id=c.build_id)
    after = states(conn)
    assert (after['ka_kshetra'], after['mi_bhara'], after['ka_sangam']) == ('lit', 'service_ok', 'lit')       # back to what each held before the run
    assert conn.execute("SELECT last_error FROM asset_throughput WHERE asset_id = 'ka_sangam'").fetchone() == (None,)
    assert after['ka_yojaka'] == 'lit'                                                                          # the run's own successful asset is untouched
    assert sorted(r['asset_id'] for r in result['asset_states_restored']) == ['ka_kshetra', 'ka_sangam', 'mi_bhara']
    assert conn.execute('SELECT count(*) FROM kala_layer_candidate WHERE build_id = %s', (c.build_id,)).fetchone() == (0,)


def d8b(module, conn):
    c = failed_run(conn)
    module.teardown(conn, run_id=c.build_id)
    after = states(conn)
    assert after['ka_old_stale'] == 'stale'            # stale before the run: the run did not write it
    assert after['ka_hand_edited'] == 'stale'          # changed inside the window by something other than the orchestrator
    assert after['ka_edited_after'] == 'error'         # the run wrote stale, someone changed it to error afterwards: not ours to reset


def d8c(module, conn):
    c = failed_run(conn, state='completed')
    before = states(conn)
    result = module.teardown(conn, run_id=c.build_id)
    assert states(conn) == before and result['asset_states_restored'] == []


@BOTH
def test_d8a_a_failed_runs_stale_and_error_rows_are_restored(stale_world, tmp_path, reverted):
    # reversion: the teardown restores nothing
    verdict(reverted, d8a, rebuild_control, tmp_path, "    restored = restore_asset_states(conn, to_restore, chart_id)\n", "    restored = []\n", stale_world)


@BOTH
def test_d8b_a_row_changed_since_the_runs_last_write_is_left_alone(stale_world, tmp_path, reverted):
    # reversion: the restore does not compare the row's current state with the run's last orchestrator write
    verdict(reverted, d8b, rebuild_control, tmp_path, "t.state = ANY(%(written)s) AND t.state = span.last_new AND", "t.state = ANY(%(written)s) AND", stale_world)


def d8b_hand_edit(module, conn):
    c = failed_run(conn)
    module.teardown(conn, run_id=c.build_id)
    assert states(conn)['ka_hand_edited'] == 'stale'


@BOTH
def test_d8b_a_hand_edit_inside_the_window_is_not_the_orchestrators(stale_world, tmp_path, reverted):
    # reversion: the audit rows of any writer count, not only those of the orchestrator's connection (marsys.triggered_by)
    verdict(reverted, d8b_hand_edit, rebuild_control, tmp_path, "a.chart_id = %(chart)s AND a.triggered_by = %(by)s",
            "a.chart_id = %(chart)s AND (%(by)s::text IS NOT NULL)", stale_world)


@BOTH
def test_d8c_only_a_failed_run_restores(stale_world, tmp_path, reverted):
    # reversion: every terminal run restores
    verdict(reverted, d8c, rebuild_control, tmp_path, "if run['state'] == 'failed' else []", "if True else []", stale_world)


def d8d(module, conn):
    c = failed_run(conn)
    role = 'k9_no_audit_' + uuid.uuid4().hex[:8]
    conn.execute(f'CREATE ROLE {role} NOLOGIN')
    schema = conn.execute('SELECT current_schema()').fetchone()[0]
    conn.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO {role}')
    conn.execute(f'GRANT ALL ON ALL TABLES IN SCHEMA "{schema}" TO {role}')
    conn.execute(f'REVOKE ALL ON asset_throughput_state_audit FROM {role}')
    conn.commit()
    before = snapshot(conn), states(conn)
    try:
        conn.execute(f'SET ROLE {role}')
        with pytest.raises(ValueError, match='cannot read the asset state audit trail'):
            module.teardown(conn, run_id=c.build_id)
    except psycopg.Error as exc:                      # the reversion: the audit query itself is refused by the database, later and in the wrong way
        raise AssertionError(f'refused by the database, not by the teardown: {exc}')
    finally:
        conn.rollback()
        conn.execute('RESET ROLE')
        conn.commit()
        conn.execute(f'DROP OWNED BY {role}')
        conn.execute(f'DROP ROLE {role}')
        conn.commit()
    assert (snapshot(conn), states(conn)) == before   # nothing was deleted or restored


@BOTH
def test_d8d_an_unreadable_audit_trail_refuses_before_anything_is_deleted(stale_world, tmp_path, reverted):
    # reversion: the privilege check is dropped
    verdict(reverted, d8d, rebuild_control, tmp_path,
            "if not conn.execute('SELECT has_table_privilege(current_user, %s, %s)', (AUDIT_TABLE, 'SELECT')).fetchone()[0]:", "if False:", stale_world)


def test_d8d_an_absent_audit_trail_refuses_too(stale_world):
    c = failed_run(stale_world)
    stale_world.execute('DROP TABLE asset_throughput_state_audit CASCADE')
    stale_world.commit()
    with pytest.raises(ValueError, match='audit trail is absent'):
        rebuild_control.teardown(stale_world, run_id=c.build_id)


def test_d8e_the_real_kind_commits_and_reads_the_restored_states_back(stale_world, wired, capsys, tmp_path):
    c = failed_run(stale_world)
    code, out, _ = cli(ADMISSION, ['teardown', '--run-id', c.build_id], capsys)
    assert code == 0 and out['status'] == 'TORN_DOWN'
    assert out['readback']['asset_states'] == {'ka_kshetra': 'lit', 'ka_sangam': 'lit', 'mi_bhara': 'service_ok'}
    wired.rollback()
    assert states(wired)['ka_kshetra'] == 'lit' and states(wired)['mi_bhara'] == 'service_ok'      # committed, not merely visible in the open transaction


def test_d8e_the_dry_run_restores_nothing(stale_world, wired, capsys):
    c = failed_run(stale_world)
    before = snapshot(wired), states(wired)
    code, out, _ = cli(ADMISSION, ['teardown-dryrun', '--run-id', c.build_id], capsys)
    assert code == 0 and out['dry_run_passed'] is True and len(out['operation_result']['asset_states_restored']) == 3
    wired.rollback()
    assert (snapshot(wired), states(wired)) == before


@pytest.mark.parametrize('kind', ['orchestrator_rebuild_teardown_dryrun', 'orchestrator_rebuild_teardown'])
def test_d8f_the_teardown_pair_is_enabled_on_the_admission_module(kind):
    # Enabled by W5W6-READINESS WP2 under surrogate ruling S-1 (shard K9-4b.json). The OWNER-AUTH-TEARDOWN-v2 authority covers only ka_gochara_v5 candidate/test rows, so
    # deletion of a K9 rebuild candidate stays behind the signed-only rule (X1 of test_executor_mechanical_production.py), the pack's teardown gate and the database role.
    table = json.loads(OPS.read_text())['ops']
    assert table[kind]['enabled'] is True and table[kind]['script'].endswith('publication_admission.py')
    assert table['orchestrator_rebuild_teardown']['production'] is True and table['orchestrator_rebuild_teardown_dryrun']['production'] is False
