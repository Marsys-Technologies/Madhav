"""W5W6-READINESS WP2 (brief 02): the K9 cancel / teardown kinds are enabled -- one doctrine-grounded oracle per distinct production claim, each with ONE planted
reversion that fails (root CLAUDE.md §N.8: a signal is measured by a detector that can read false).

  C3  a rebuild run publishes nothing to Pub/Sub and its [event] lines still reach stderr (source: events.py emit(): ``PUBSUB_DISABLED`` or no ``PUBSUB_TOPIC`` prints,
      otherwise publishes; the two-source stall / re-projection gates read the log source) -- real and dry-run entries, environment restored
  C4a teardown removes EVERY candidate-keyed row of a terminal run's generation, including the resonance writer's ``kala_f1_*`` candidate tables (no foreign key to the candidate;
      relationship_storage.store_projection / migration 1342), and never another run's rows, another chart's rows or the head (SR-K9-PUBLISHABLE D8)
  C4b ``gochara_resonance_map`` carries the generation (migration 1404) and the resonance writer writes its candidate's partition: a candidate teardown removes exactly the
      rows of (chart, candidate generation) and every SERVED row is byte-identical before and after (SR-K9-RESONANCE-MAP; sealed rule: served rows survive a failed candidate)
  C4c the failed-run receipt records the resonance rows removed (count) and the writer run id (N.7.6: an honest report, not a silent pass)
  C5a a cancel on a running run sets the stop request and the run loop starts nothing further: the run ends ``stopped`` at an asset boundary
      (runner.py check_signals / execute_dag / execute_run -> mark_run_state 'stopped')
  C5b the honest limit: an asset already in flight is NOT interrupted (execute_dag drains it), so a cancel acts only between assets
"""
import json
import sys
import time
import types
import uuid

import psycopg.rows
import pytest

from pipeline.orchestrator import runner
from services.kala_core import publication, rebuild_control
from tests.l3.kala_db.manifest.test_k9_publication_hardening import BOTH, noisy_delegate, verdict
from tests.l3.kala_db.manifest.test_publication_admission import ADMISSION, registry, wired  # noqa: F401  (wired, db are fixtures)
from tests.l3.kala_db.manifest.test_publication_ops import db, prepare  # noqa: F401
from tests.l3.kala_db.manifest.test_rebuild_control import CHART, ctl, make_run  # noqa: F401  (ctl is a fixture)

PLAN = ('ka_yojaka', 'ka_gochara_resonance')
OTHER_CHART = str(uuid.uuid4())


# ---------------------------------------------------------------- C3: the rebuild publishes nothing to Pub/Sub


class FakePublisher:
    published: list = []

    def topic_path(self, project, topic): return f'projects/{project}/topics/{topic}'

    def publish(self, topic, data, **attrs):
        FakePublisher.published.append((topic, data, attrs))
        return types.SimpleNamespace(add_done_callback=lambda cb: None)


def install_fake_pubsub(monkeypatch):
    FakePublisher.published = []
    google, cloud, pubsub = types.ModuleType('google'), types.ModuleType('google.cloud'), types.ModuleType('google.cloud.pubsub_v1')
    pubsub.PublisherClient = FakePublisher
    cloud.pubsub_v1, google.cloud = pubsub, cloud
    for name, module in (('google', google), ('google.cloud', cloud), ('google.cloud.pubsub_v1', pubsub)):
        monkeypatch.setitem(sys.modules, name, module)


def c3(module, wired, monkeypatch, capsys, operation):
    install_fake_pubsub(monkeypatch)
    monkeypatch.setenv('PUBSUB_TOPIC', 'fake-topic')
    monkeypatch.delenv('PUBSUB_DISABLED', raising=False)      # the launcher does not set it: the entry must
    registry(wired, {'ga_positions': [], 'ka_yojaka': ['ga_positions']})
    c = prepare(wired, writers=('ka_yojaka',), chart=publication.CANONICAL_CHART)
    monkeypatch.setattr(publication, 'main', noisy_delegate(c))
    code = module.main([operation, '--run-id', c.build_id, '--assets', 'ka_yojaka'])
    err = capsys.readouterr().err
    assert code == 0
    assert FakePublisher.published == [], f'{len(FakePublisher.published)} event(s) were published to Pub/Sub'
    assert err.count('[event] ') == 2                          # the evidence the two-source gates read
    assert not module.os.environ.get('PUBSUB_DISABLED')         # restored: the entry does not leave the variable set (events.py reads it by truthiness)


@BOTH
@pytest.mark.parametrize('operation', ['rebuild', 'rebuild-dryrun'])
def test_c3_a_rebuild_run_publishes_nothing_to_pubsub_and_keeps_its_event_lines(wired, monkeypatch, capsys, tmp_path, operation, reverted):
    # reversion: the entry does not set PUBSUB_DISABLED for the run
    verdict(reverted, c3, ADMISSION, tmp_path, 'redirect_stdout(captured), pubsub_disabled(), (', 'redirect_stdout(captured), (', wired, monkeypatch, capsys, operation)


def test_c3_an_ambient_pubsub_disabled_is_restored_after_the_run(wired, monkeypatch, capsys):
    registry(wired, {'ga_positions': [], 'ka_yojaka': ['ga_positions']})
    c = prepare(wired, writers=('ka_yojaka',), chart=publication.CANONICAL_CHART)
    monkeypatch.setattr(publication, 'main', noisy_delegate(c))
    monkeypatch.setenv('PUBSUB_DISABLED', '0')
    assert ADMISSION.main(['rebuild-dryrun', '--run-id', c.build_id, '--assets', 'ka_yojaka']) == 0
    capsys.readouterr()
    assert ADMISSION.os.environ['PUBSUB_DISABLED'] == '0'


# ---------------------------------------------------------------- C4: teardown covers the whole candidate of the plan


@pytest.fixture
def plan_tables(ctl):
    """The write targets of the closed K9 plan that carry the candidate generation without a foreign key to kala_layer_candidate, as migrations 243/1339/1342 and 459+1404 define them."""
    ctl.execute("CREATE TABLE kala_activation_predicates (id serial PRIMARY KEY, chart_id uuid NOT NULL, generation text NOT NULL DEFAULT 'legacy')")
    ctl.execute('CREATE TABLE kala_f1_target_object (chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, generation text NOT NULL, object_id text NOT NULL, '
                'PRIMARY KEY (chart_id, ayanamsha_id, generation, object_id))')
    ctl.execute('CREATE TABLE kala_f1_relationship (chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, generation text NOT NULL, edge_id text NOT NULL, object_id text, '
                'PRIMARY KEY (chart_id, ayanamsha_id, generation, edge_id), '
                'FOREIGN KEY (chart_id, ayanamsha_id, generation, object_id) REFERENCES kala_f1_target_object (chart_id, ayanamsha_id, generation, object_id))')
    ctl.execute("CREATE TABLE gochara_resonance_map (id serial PRIMARY KEY, chart_id uuid NOT NULL, generation text NOT NULL DEFAULT 'legacy', event_class text NOT NULL, "
                "computed_at timestamptz NOT NULL DEFAULT clock_timestamp())")
    ctl.commit()
    return ctl


def seed(conn, chart, generation):
    conn.execute('INSERT INTO kala_activation_predicates (chart_id, generation) VALUES (%s, %s), (%s, %s)', (chart, generation, chart, generation))
    conn.execute("INSERT INTO gochara_resonance_map (chart_id, generation, event_class) VALUES (%s, %s, 'career'), (%s, %s, 'wealth')", (chart, generation, chart, generation))
    for ayanamsha in ('lahiri', 'raman'):
        conn.execute('INSERT INTO kala_f1_target_object VALUES (%s, %s, %s, %s)', (chart, ayanamsha, generation, 'graha:sun'))
        for edge in ('e1', 'e2'):
            conn.execute('INSERT INTO kala_f1_relationship VALUES (%s, %s, %s, %s, %s)', (chart, ayanamsha, generation, f'{ayanamsha}:{edge}', 'graha:sun'))
    conn.commit()


TABLES = ('kala_layer_candidate', 'ka_dep_candidate', 'kala_activation_predicates', 'kala_f1_target_object', 'kala_f1_relationship', 'gochara_resonance_map')


def held(conn, chart, generation):
    return {t: conn.execute(f'SELECT count(*) FROM {t} WHERE chart_id = %s AND generation = %s', (chart, generation)).fetchone()[0] for t in TABLES}


def world(conn, plan=PLAN):
    """Run A (failed, torn down), a later run B of the same chart, and a run of another chart that reuses A's generation name; the resonance table also holds the chart's served ('legacy') rows."""
    a = make_run(conn, 'failed', generation='a', plan=plan)
    b = make_run(conn, 'completed', generation='b', plan=plan)
    other = make_run(conn, 'completed', generation='a', chart=OTHER_CHART, plan=plan)
    for chart, generation in ((CHART, 'a'), (CHART, 'b'), (OTHER_CHART, 'a')):
        seed(conn, chart, generation)
    conn.execute("INSERT INTO gochara_resonance_map (chart_id, event_class) VALUES (%s, 'career'), (%s, 'wealth'), (%s, 'health')", (CHART, CHART, CHART))
    conn.commit()
    return a, b, other


def served_state(conn, chart=CHART, generation='a'):
    """Every column (id and computed_at included) of every resonance row that is NOT the torn-down run's: the byte-level state of everything else."""
    return conn.execute('SELECT md5(coalesce(string_agg(t::text, $$|$$ ORDER BY id), $$$$)), count(*) FROM gochara_resonance_map t '
                        'WHERE NOT (chart_id = %s AND generation = %s)', (chart, generation)).fetchone()


def c4a(module, conn):
    a, _b, _other = world(conn)
    assert module.census(conn, a.build_id) == {'kala_layer_candidate': 1, 'ka_dep_candidate': 2, 'kala_activation_predicates': 2,
                                               'kala_f1_target_object': 2, 'kala_f1_relationship': 4, 'gochara_resonance_map': 2, 'kala_layer_candidate_grain': 2, 'kala_layer_verification': 0}
    kept_b, kept_other = held(conn, CHART, 'b'), held(conn, OTHER_CHART, 'a')
    head = conn.execute('SELECT chart_id, generation FROM kala_layer_head ORDER BY chart_id').fetchall()
    result = module.teardown(conn, run_id=a.build_id)
    assert result['status'] == 'TORN_DOWN' and result['generation'] == 'a'
    assert held(conn, CHART, 'a') == {t: 0 for t in TABLES}, 'candidate rows of the torn-down run remain'
    assert held(conn, CHART, 'b') == kept_b and held(conn, OTHER_CHART, 'a') == kept_other      # a later run's rows and another chart's rows are untouched
    assert conn.execute('SELECT chart_id, generation FROM kala_layer_head ORDER BY chart_id').fetchall() == head
    assert result['deleted']['kala_f1_relationship'] == 4 and result['deleted']['kala_f1_target_object'] == 2 and result['deleted']['kala_activation_predicates'] == 2
    assert result['deleted']['gochara_resonance_map'] == 2


@BOTH
def test_c4a_teardown_removes_every_candidate_row_of_the_run_and_only_those(plan_tables, tmp_path, reverted):
    # reversion: the resonance writer's candidate tables are dropped from the census (the pre-change list)
    verdict(reverted, c4a, rebuild_control, tmp_path,
            "UNLINKED_CANDIDATE_TABLES = ('kala_activation_predicates', 'kala_f1_relationship', 'kala_f1_target_object')", "UNLINKED_CANDIDATE_TABLES = ('kala_activation_predicates',)", plan_tables)


def c4b(module, conn):
    a, _b, _other = world(conn)
    before = served_state(conn)
    assert before[1] == 2 + 2 + 3        # run b's rows, the other chart's same-named generation, the chart's served ('legacy') rows
    result = module.teardown(conn, run_id=a.build_id)
    assert result['deleted']['gochara_resonance_map'] == 2
    assert conn.execute('SELECT count(*) FROM gochara_resonance_map WHERE chart_id = %s AND generation = %s', (CHART, 'a')).fetchone()[0] == 0
    assert served_state(conn) == before, 'a candidate teardown changed a row that is not the run\'s own (served rows must be byte-identical)'


@BOTH
def test_c4b_a_candidate_teardown_removes_its_own_resonance_rows_and_leaves_every_other_row_byte_identical(plan_tables, tmp_path, reverted):
    # reversion: the unlinked-table delete is not scoped to the generation (it takes the chart's whole partition set)
    verdict(reverted, c4b, rebuild_control, tmp_path,
            "sql.SQL('DELETE FROM {} WHERE chart_id = %s AND generation = %s')", "sql.SQL('DELETE FROM {} WHERE chart_id = %s AND %s::text IS NOT NULL')", plan_tables)


def c4c(module, conn):
    a, _b, _other = world(conn)
    result = module.teardown(conn, run_id=a.build_id)
    assert result['generation_scoped_writes_removed'] == [{'asset_id': 'ka_gochara_resonance', 'table': 'gochara_resonance_map', 'generation': 'a',
                                                           'rows_deleted': 2, 'writer_run_id': a.build_id}]
    assert result['chart_scoped_writes_left_alone'] == []       # the receipt keeps its shape; no writer's rows are left alone any more


@BOTH
def test_c4c_the_receipt_records_the_rows_removed_and_the_writer_run_id(plan_tables, tmp_path, reverted):
    # reversion: the receipt does not carry the writer's run id
    verdict(reverted, c4c, rebuild_control, tmp_path, "'rows_deleted': deleted[table], 'writer_run_id': run_id}", "'rows_deleted': deleted[table], 'writer_run_id': None}", plan_tables)


def test_c4c_a_plan_without_the_resonance_writer_names_nothing(plan_tables):
    a = make_run(plan_tables, 'failed', generation='a', plan=('ka_yojaka', 'ka_sangam'))
    seed(plan_tables, CHART, 'a')
    assert rebuild_control.teardown(plan_tables, run_id=a.build_id)['generation_scoped_writes_removed'] == []


def test_c4_the_dry_run_counts_the_resonance_candidate_rows_and_changes_nothing(plan_tables, wired, capsys):
    a, _b, _other = world(wired)
    before = held(wired, CHART, 'a')
    code = ADMISSION.main(['teardown-dryrun', '--run-id', a.build_id])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out['dry_run_passed'] is True and out['operation_result']['deleted']['kala_f1_relationship'] == 4
    assert held(wired, CHART, 'a') == before


# ---------------------------------------------------------------- C5: what a cancel does to a running run


def drive(module, conn, run_id, plan, monkeypatch, *, cancel_when, work=0.0):
    """The run loop of runner.execute_run for a stub plan: execute_dag with the runner's own signal check, then the runner's own terminal write."""
    monkeypatch.setattr(runner, '_POLL_INTERVAL', 0.02)
    conn.execute('ALTER TABLE build_runs ADD COLUMN IF NOT EXISTS pause_requested_at timestamptz')
    conn.commit()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)
    started, finished, sent = [], [], []

    def run_fn(asset):
        started.append(asset)
        time.sleep(work)
        finished.append(asset)
        return 'lit'

    def should_stop():
        conn.rollback()
        if not sent and cancel_when(started, finished):
            sent.append(module.cancel(conn, run_id=run_id))
            conn.commit()
        return runner.check_signals(cur, run_id)

    deps = {a: ([plan[i - 1]] if i else []) for i, a in enumerate(plan)}
    failed, terminal = runner.execute_dag(list(plan), deps, run_fn, 1, should_stop=should_stop)
    if terminal == 'stopped':
        runner.mark_run_state(conn, cur, run_id, 'stopped', ended_at=True)      # runner.py execute_run, on terminal == 'stopped'
    state = conn.execute('SELECT state, stop_requested_at, ended_at FROM build_runs WHERE id = %s', (run_id,)).fetchone()
    return started, finished, failed, terminal, sent, state


def cancel_between_assets(module, ctl, monkeypatch):
    stub = ('ka_a', 'ka_b', 'ka_c')
    c = make_run(ctl, 'running', plan=stub)
    ctl.execute("UPDATE build_runs SET started_at = now() WHERE id = %s", (c.build_id,))
    ctl.commit()
    try:
        started, finished, failed, terminal, sent, state = drive(module, ctl, c.build_id, stub, monkeypatch, cancel_when=lambda s, f: len(f) == 1)
    except Exception as exc:                                  # a reverted cancel() that cannot even record the request is a failed oracle, not a harness crash
        raise AssertionError(f'cancel did not record a stop request: {exc!r}') from exc
    assert sent and sent[0]['status'] == 'CANCEL_REQUESTED' and sent[0]['state_after'] == 'running'      # the request, not a presumed terminal state
    assert started == ['ka_a'] and finished == ['ka_a'] and failed == set()                        # ka_b and ka_c never started
    assert terminal == 'stopped' and state[0] == 'stopped' and state[1] is not None and state[2] is not None


@BOTH
def test_c5a_a_cancel_stops_the_run_at_the_next_asset_boundary(ctl, monkeypatch, tmp_path, reverted):
    # reversion: cancel() does not record the stop request (the UPDATE keeps stop_requested_at as it was)
    verdict(reverted, cancel_between_assets, rebuild_control, tmp_path,
            '"UPDATE build_runs SET stop_requested_at = COALESCE(stop_requested_at, NOW()), "', '"UPDATE build_runs SET stop_requested_at = stop_requested_at, "', ctl, monkeypatch)


def test_c5b_a_cancel_never_interrupts_the_asset_in_flight(ctl, monkeypatch):
    stub = ('ka_a', 'ka_b', 'ka_c')
    c = make_run(ctl, 'running', plan=stub)
    # the stop request lands while ka_a is still working; ka_a runs to its own end and is counted as completed, nothing further starts
    started, finished, failed, terminal, sent, state = drive(rebuild_control, ctl, c.build_id, stub, monkeypatch, cancel_when=lambda s, f: s == ['ka_a'] and not f, work=0.4)
    assert sent and started == ['ka_a'] and finished == ['ka_a'] and failed == set()
    assert terminal == 'stopped' and state[0] == 'stopped'


def test_c5c_the_rebuild_child_of_a_cancelled_run_exits_refused_not_completed(ctl, wired, monkeypatch, capsys):
    """The whole chain for one run on the canonical chart: the executor's rebuild child -> publication.main -> execute_run (the stub plan's run loop) -> a cancel between assets.
    publication.main reads the final state and refuses anything but ``completed`` ("orchestrator did not complete the build"): the receipt of a cancelled rebuild is a refusal, never a pass."""
    stub = ('ka_a', 'ka_b', 'ka_c')
    c = prepare(ctl, 'g', writers=stub, chart=CHART)              # a frozen manifest that matches the plan, as publication._run requires
    ctl.execute("UPDATE build_runs SET state = 'running' WHERE id = %s", (c.build_id,))
    ctl.commit()
    registry(wired, {'ka_a': [], 'ka_b': ['ka_a'], 'ka_c': ['ka_b']})
    outcome = {}

    def execute_run(run_id):
        ctl.rollback()
        ctl.read_only = False                                       # the real run loop has its own connections; this fixture shares one with the read-only admission
        outcome['drive'] = drive(rebuild_control, ctl, run_id, stub, monkeypatch, cancel_when=lambda s, f: len(f) == 1)
        ctl.rollback()

    monkeypatch.setattr(runner, 'execute_run', execute_run)
    code = ADMISSION.main(['rebuild', '--run-id', c.build_id, '--assets', ','.join(stub), '--force-execute'])
    out = json.loads(capsys.readouterr().out)
    assert 'drive' in outcome, (code, out)
    started, finished, failed, terminal, sent, state = outcome['drive']
    assert started == ['ka_a'] and terminal == 'stopped' and state[0] == 'stopped'
    assert code == 2 and out == {'reason': 'orchestrator did not complete the build', 'status': 'REFUSED'}
