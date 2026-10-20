"""K9 rebuild control: cancel and teardown kinds (SR-PREBUILD-ALL, SR-TEARDOWN-AUTHORITY-GATE 2 and 3).

Claims, one oracle each (sources: runner.check_signals / cockpit stop route for the stop signal; teardown_gate.py rules 2-3 and
absence() of the K9-4 pack for the teardown; 1330 migration for the candidate tables):
  R1  cancel records the stop REQUEST on a running or paused run and stops a planned one; the state is the database's, never a presumed CANCELLED
  R2  cancel is refused for a terminal run, and a repeated request keeps the first request time
  R3  both operations are scoped to the canonical chart and to an explicit Kāla rebuild plan
  R4  teardown deletes the candidate, its grains, its verification and every table that references it (read from the catalog), and only that run's rows
  R5  teardown is refused for a non-terminal run, a published candidate, the head generation, a run without a candidate and a candidate whose previous head is gone
  R6  a dependent whose key is not (chart_id, generation), or that is referenced by another table, is refused and nothing is deleted
  R7  each dry run changes nothing, passes only when its write was observed and rolled back, and reports a refusal as not passed
  R8  the real kinds commit and read the outcome back from the database; a refusal exits 2 and changes nothing
"""
import json
import uuid
from datetime import timezone
from pathlib import Path

import pytest

from services.kala_core import publication, rebuild_control
from tests.l3.kala_db.manifest.test_publication_admission import (  # noqa: F401  (wired, db are fixtures)
    ADMISSION, canonical_candidate, run, wired,
)
from tests.l3.kala_db.manifest.test_publication_ops import accept, db, prepare, snapshot  # noqa: F401

CHART = publication.CANONICAL_CHART


AUDIT_MIGRATION = Path(__file__).resolve().parents[5] / 'supabase/migrations/586_f152_asset_throughput_state_audit.sql'


def asset_state_tables(conn):
    """The orchestrator's asset_throughput and its REAL audit trail (migration 586: the table and the AFTER UPDATE OF state trigger)."""
    conn.execute('ALTER TABLE build_runs ADD COLUMN started_at timestamptz, ADD COLUMN ended_at timestamptz')
    conn.execute('CREATE TABLE asset_throughput (chart_id uuid, asset_id text NOT NULL, state text NOT NULL, last_error text, last_built_at timestamptz)')
    conn.execute('CREATE UNIQUE INDEX ON asset_throughput (chart_id, asset_id) WHERE chart_id IS NOT NULL')
    conn.execute(AUDIT_MIGRATION.read_text())
    conn.commit()


@pytest.fixture
def ctl(db):
    db.execute('ALTER TABLE build_runs ADD COLUMN stop_requested_at timestamptz')
    asset_state_tables(db)
    db.execute('CREATE TABLE ka_dep_candidate (chart_id uuid NOT NULL, generation text NOT NULL, v int NOT NULL, '
               'FOREIGN KEY (chart_id, generation) REFERENCES kala_layer_candidate (chart_id, generation))')
    db.commit()
    return db


@pytest.fixture
def wired_ctl(ctl, wired):
    return wired


def make_run(conn, state, *, chart=CHART, generation='g', action='rebuild', plan=('ka_yojaka', 'ka_sangam')):
    """A canonical-chart candidate with its build run, in the given run state."""
    c = prepare(conn, generation, chart=chart)
    conn.execute('UPDATE build_runs SET state = %s, action = %s, plan = %s::jsonb WHERE id = %s',
                 (state, action, json.dumps(list(plan)), c.build_id))
    conn.execute('INSERT INTO ka_dep_candidate VALUES (%s, %s, 1), (%s, %s, 2)', (chart, generation, chart, generation))
    conn.commit()
    return c


def state_of(conn, run_id):
    return conn.execute('SELECT state, stop_requested_at FROM build_runs WHERE id = %s', (run_id,)).fetchone()


# ---------------------------------------------------------------- R1, R2: cancel


@pytest.mark.parametrize('state', ['running', 'paused'])
def test_cancel_records_the_stop_request_and_does_not_invent_a_terminal_state(ctl, state):
    c = make_run(ctl, state)
    result = rebuild_control.cancel(ctl, run_id=c.build_id)
    assert result['status'] == 'CANCEL_REQUESTED' and result['state_before'] == state
    got_state, requested = state_of(ctl, c.build_id)
    assert requested is not None                          # runner.check_signals stops a run whose stop_requested_at is set
    assert got_state == state and result['state_after'] == state and result['terminal'] is False   # the runner, not this call, terminalises it


def test_cancel_stops_a_planned_run_at_once(ctl):
    c = make_run(ctl, 'planned')
    result = rebuild_control.cancel(ctl, run_id=c.build_id)
    assert state_of(ctl, c.build_id)[0] == 'stopped' and result['terminal'] is True      # cockpit stop route: planned -> stopped


@pytest.mark.parametrize('state', ['completed', 'stopped', 'failed'])
def test_cancel_of_a_terminal_run_is_refused_and_changes_nothing(ctl, state):
    c = make_run(ctl, state)
    before = state_of(ctl, c.build_id)
    with pytest.raises(ValueError, match='only a planned, running or paused'):
        rebuild_control.cancel(ctl, run_id=c.build_id)
    assert state_of(ctl, c.build_id) == before


def test_a_repeated_cancel_keeps_the_first_request_time(ctl):
    c = make_run(ctl, 'running')
    rebuild_control.cancel(ctl, run_id=c.build_id)
    ctl.execute("UPDATE build_runs SET stop_requested_at = '2026-01-01T00:00:00+00:00' WHERE id = %s", (c.build_id,))
    rebuild_control.cancel(ctl, run_id=c.build_id)
    assert state_of(ctl, c.build_id)[1].astimezone(timezone.utc).isoformat() == '2026-01-01T00:00:00+00:00'


# ---------------------------------------------------------------- R3: scope


@pytest.mark.parametrize('operation', ['cancel', 'teardown'])
@pytest.mark.parametrize('case', ['other_chart', 'not_rebuild', 'not_kala_plan', 'issued_forecast', 'absent'])
def test_both_operations_are_refused_outside_the_canonical_kala_rebuild_scope(ctl, operation, case):
    state = 'running' if operation == 'cancel' else 'failed'
    if case == 'other_chart':
        c = make_run(ctl, state, chart=str(uuid.uuid4()))
    elif case == 'absent':
        c = argparse_run(str(uuid.uuid4()))
    else:
        plan = {'not_kala_plan': ('ka_yojaka', 'ga_positions'), 'issued_forecast': ('ka_yojaka', 'ka_bhavishya_lekha')}.get(case, ('ka_yojaka',))
        c = make_run(ctl, state, action='build' if case == 'not_rebuild' else 'rebuild', plan=plan)
    before = snapshot(ctl)
    reason = {'other_chart': 'canonical-chart scoped', 'absent': 'build run is absent', 'not_rebuild': 'explicit Kāla rebuild plan',
              'not_kala_plan': 'explicit Kāla rebuild plan', 'issued_forecast': 'issued forecasts'}[case]
    with pytest.raises(ValueError, match=reason):            # the refusal named for its own cause, not a later filter that happens to match nothing
        getattr(rebuild_control, operation)(ctl, run_id=c.build_id)
    assert snapshot(ctl) == before


def argparse_run(run_id):
    import argparse
    return argparse.Namespace(build_id=run_id)


# ---------------------------------------------------------------- R4: teardown deletes exactly the run's candidate


def rows(conn, generation):
    q = lambda t: conn.execute(f'SELECT count(*) FROM {t} WHERE generation = %s', (generation,)).fetchone()[0]
    return {t: q(t) for t in ('kala_layer_candidate', 'kala_layer_candidate_grain', 'kala_layer_verification', 'ka_dep_candidate')}


def test_teardown_deletes_the_candidate_and_everything_that_references_it_and_nothing_else(ctl):
    keep = make_run(ctl, 'completed', generation='keep')
    accept(ctl, keep)
    gone = make_run(ctl, 'failed', generation='gone')
    accept(ctl, gone)                                         # a verified, never published candidate is torn down with its receipt
    ctl.commit()
    assert rows(ctl, 'gone') == {'kala_layer_candidate': 1, 'kala_layer_candidate_grain': 2, 'kala_layer_verification': 1, 'ka_dep_candidate': 2}
    kept = rows(ctl, 'keep')
    result = rebuild_control.teardown(ctl, run_id=gone.build_id)
    assert result['status'] == 'TORN_DOWN' and result['generation'] == 'gone'
    assert result['deleted'] == {'kala_layer_candidate': 1, 'kala_layer_candidate_grain': 2, 'kala_layer_verification': 1, 'ka_dep_candidate': 2}
    assert rows(ctl, 'gone') == {k: 0 for k in kept}          # K9-4 pack absence(): zero rows of the run in every scope table
    assert rows(ctl, 'keep') == kept                           # another run's candidate is untouched


def test_teardown_keeps_the_published_head_and_its_retained_previous_generation(ctl):
    a = canonical_candidate(ctl, 'a')
    publication.publish(ctl, run_id=a.build_id, generation='a', expected_head=None)
    b = canonical_candidate(ctl, 'b')
    ctl.execute("UPDATE build_runs SET state = 'failed' WHERE id = %s", (b.build_id,))
    ctl.commit()
    result = rebuild_control.teardown(ctl, run_id=b.build_id)
    assert result['head_generation'] == 'a' and result['retained_previous_present'] is True
    assert ctl.execute('SELECT generation FROM kala_layer_head').fetchone() == ('a',)
    assert ctl.execute("SELECT state FROM kala_layer_candidate WHERE generation = 'a'").fetchone() == ('published',)


# ---------------------------------------------------------------- R5: teardown refusals (teardown_gate rules 2 and 3)


@pytest.mark.parametrize('state', ['planned', 'running', 'paused'])
def test_teardown_of_a_run_that_is_not_terminal_is_refused(ctl, state):
    c = make_run(ctl, state)
    before = snapshot(ctl)
    with pytest.raises(ValueError, match='not terminal'):
        rebuild_control.teardown(ctl, run_id=c.build_id)
    assert snapshot(ctl) == before


def test_teardown_of_a_published_candidate_is_refused(ctl):
    a = canonical_candidate(ctl, 'a')
    publication.publish(ctl, run_id=a.build_id, generation='a', expected_head=None)
    ctl.execute("UPDATE build_runs SET state = 'completed' WHERE id = %s", (a.build_id,))
    ctl.commit()
    before = snapshot(ctl)
    with pytest.raises(ValueError, match='never torn down'):
        rebuild_control.teardown(ctl, run_id=a.build_id)
    assert snapshot(ctl) == before


def test_teardown_of_the_head_generation_is_refused_even_when_the_candidate_row_is_not_marked_published(ctl):
    c = make_run(ctl, 'failed', generation='h')
    ctl.execute('INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s, %s)', (CHART, 'h'))
    ctl.commit()
    before = snapshot(ctl)
    with pytest.raises(ValueError, match='never torn down'):
        rebuild_control.teardown(ctl, run_id=c.build_id)
    assert snapshot(ctl) == before


def test_teardown_of_a_run_without_a_candidate_is_refused(ctl):
    c = make_run(ctl, 'failed')
    ctl.execute('DELETE FROM ka_dep_candidate')
    ctl.execute('DELETE FROM kala_layer_candidate_grain')
    ctl.execute('DELETE FROM kala_layer_candidate')
    ctl.commit()
    with pytest.raises(ValueError, match='nothing to tear down'):
        rebuild_control.teardown(ctl, run_id=c.build_id)


def test_teardown_is_refused_when_the_retained_previous_generation_is_gone(ctl):
    a = canonical_candidate(ctl, 'a')
    publication.publish(ctl, run_id=a.build_id, generation='a', expected_head=None)
    b = make_run(ctl, 'failed', generation='b')
    ctl.execute("UPDATE kala_layer_candidate SET expected_head_generation = 'a' WHERE generation = 'b'")
    ctl.execute("UPDATE kala_layer_candidate SET state = 'building' WHERE generation = 'a'")      # 'a' is no longer a retained published generation
    ctl.commit()
    before = snapshot(ctl)
    with pytest.raises(ValueError, match='retained previous generation'):
        rebuild_control.teardown(ctl, run_id=b.build_id)
    assert snapshot(ctl) == before


# ---------------------------------------------------------------- R6: dependents the teardown cannot cover


def test_a_dependent_with_another_key_shape_is_refused_and_nothing_is_deleted(ctl):
    ctl.execute('CREATE TABLE ka_by_build (build_id uuid NOT NULL, FOREIGN KEY (build_id) REFERENCES kala_layer_candidate (build_id))')
    c = make_run(ctl, 'failed')
    ctl.execute('INSERT INTO ka_by_build VALUES (%s)', (c.build_id,))
    ctl.commit()
    before = snapshot(ctl)
    with pytest.raises(ValueError, match='only .chart_id, generation. can be torn down'):
        rebuild_control.teardown(ctl, run_id=c.build_id)
    assert snapshot(ctl) == before and ctl.execute('SELECT count(*) FROM ka_dep_candidate').fetchone()[0] == 2


def test_a_dependent_that_is_itself_referenced_is_refused_and_nothing_is_deleted(ctl):
    ctl.execute('ALTER TABLE ka_dep_candidate ADD COLUMN id serial PRIMARY KEY')
    ctl.execute('CREATE TABLE ka_grandchild (dep_id int NOT NULL REFERENCES ka_dep_candidate (id))')
    c = make_run(ctl, 'failed')
    ctl.execute('INSERT INTO ka_grandchild SELECT id FROM ka_dep_candidate LIMIT 1')
    ctl.commit()
    before = snapshot(ctl)
    with pytest.raises(ValueError, match='itself referenced'):
        rebuild_control.teardown(ctl, run_id=c.build_id)
    assert snapshot(ctl) == before and ctl.execute('SELECT count(*) FROM ka_dep_candidate').fetchone()[0] == 2


# ---------------------------------------------------------------- R7: the dry-run twins


def test_cancel_dryrun_requests_the_stop_inside_the_transaction_and_leaves_the_run_untouched(wired_ctl, capsys):
    c = make_run(wired_ctl, 'running')
    before = state_of(wired_ctl, c.build_id)
    code, out = run(['cancel-dryrun', '--run-id', c.build_id], capsys)
    assert code == 0 and out['status'] == 'ROLLED_BACK' and out['dry_run_passed'] is True
    assert out['write_observed_in_transaction'] is True and out['rollback_confirmed'] is True
    assert out['operation_result']['status'] == 'CANCEL_REQUESTED' and state_of(wired_ctl, c.build_id) == before


def test_teardown_dryrun_deletes_inside_the_transaction_and_every_row_is_back_after_the_rollback(wired_ctl, capsys):
    c = make_run(wired_ctl, 'failed')
    before = snapshot(wired_ctl)
    code, out = run(['teardown-dryrun', '--run-id', c.build_id], capsys)
    assert code == 0 and out['dry_run_passed'] is True and out['operation_result']['status'] == 'TORN_DOWN'
    assert snapshot(wired_ctl) == before and rows(wired_ctl, 'g')['kala_layer_candidate'] == 1
    assert rows(wired_ctl, 'g')['ka_dep_candidate'] == 2


def test_a_teardown_rehearsal_that_deleted_nothing_does_not_pass(wired_ctl, monkeypatch, capsys):
    c = make_run(wired_ctl, 'failed')
    monkeypatch.setattr(rebuild_control, 'teardown', lambda conn, **k: {'status': 'TORN_DOWN'})
    code, out = run(['teardown-dryrun', '--run-id', c.build_id], capsys)
    assert code == 0 and out['write_observed_in_transaction'] is False and out['dry_run_passed'] is False


def test_a_teardown_rehearsal_whose_deletion_survives_the_rollback_does_not_pass(wired_ctl, monkeypatch, capsys):
    c = make_run(wired_ctl, 'failed')
    real = rebuild_control.teardown
    def committing(conn, **k):
        result = real(conn, **k)
        conn.commit()                                          # the deletion escapes the rehearsal's rollback
        return result
    monkeypatch.setattr(rebuild_control, 'teardown', committing)
    code, out = run(['teardown-dryrun', '--run-id', c.build_id], capsys)
    assert code == 0 and out['rollback_confirmed'] is False and out['dry_run_passed'] is False


@pytest.mark.parametrize('operation,state', [('cancel-dryrun', 'completed'), ('teardown-dryrun', 'running')])
def test_a_refused_rehearsal_is_reported_refused_and_not_passed(wired_ctl, capsys, operation, state):
    c = make_run(wired_ctl, state)
    before = snapshot(wired_ctl)
    code, out = run([operation, '--run-id', c.build_id], capsys)
    assert code == 2 and out['status'] == 'REFUSED' and out['dry_run_passed'] is False and snapshot(wired_ctl) == before


# ---------------------------------------------------------------- R8: the real kinds commit and read back


def test_cancel_commits_and_reads_the_state_back(wired_ctl, capsys):
    c = make_run(wired_ctl, 'running')
    code, out = run(['cancel', '--run-id', c.build_id], capsys)
    assert code == 0 and out['status'] == 'CANCEL_REQUESTED'
    assert out['readback']['state'] == 'running' and out['readback']['stop_requested_at'] is not None
    wired_ctl.rollback()
    assert state_of(wired_ctl, c.build_id)[1] is not None     # committed, not merely observed in the open transaction


def test_teardown_commits_and_reads_zero_remaining_rows_back(wired_ctl, capsys):
    c = make_run(wired_ctl, 'failed')
    code, out = run(['teardown', '--run-id', c.build_id], capsys)
    assert code == 0 and out['status'] == 'TORN_DOWN'
    assert out['readback']['remaining_rows'] == {'kala_layer_candidate': 0, 'kala_layer_candidate_grain': 0,
                                                 'kala_layer_verification': 0, 'ka_dep_candidate': 0}
    wired_ctl.rollback()
    assert rows(wired_ctl, 'g')['kala_layer_candidate'] == 0


@pytest.mark.parametrize('operation,state', [('cancel', 'completed'), ('teardown', 'running')])
def test_a_refused_real_operation_exits_2_and_changes_nothing(wired_ctl, capsys, operation, state):
    c = make_run(wired_ctl, state)
    before = snapshot(wired_ctl)
    code, out = run([operation, '--run-id', c.build_id], capsys)
    assert code == 2 and out['status'] == 'REFUSED' and 'readback' not in out
    assert snapshot(wired_ctl) == before
