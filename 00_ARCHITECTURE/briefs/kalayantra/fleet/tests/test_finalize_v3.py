"""finalize.sh v3 (relaunch plan v2.7 §12, KU-02): every negative case of the packet, run against the real script.

Every collaborator is a fake that logs its calls (see finalizer_cases.py); the process groups are real and are started, and
only ever signalled, by these tests. Nothing here reads the environment as a whole, touches launchd, docker, a database,
the tracker or /Users/Dev/kalayantra.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import shutil
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finalizer_cases as fc  # noqa: E402
from finalizer_cases import World, SCRIPT, sha256  # noqa: E402

kyaction = fc.kyaction


def gone(pid):
    for _ in range(40):
        probe = kyaction.ps_probe(pid)
        if probe == ('gone',) or (probe and probe[0] == 'alive' and probe[1].startswith('Z')):
            return True
        time.sleep(0.05)
    return False


def ky_verbs(w):
    return [(c['argv'][0], c['argv'][1] if len(c['argv']) > 1 else None, c['stream'], c['lane']) for c in w.calls('ky')]


def publishes(w, item=None):
    rows = [c for c in w.calls('kyverdicts') if c['argv'][0] == 'publish']
    return [c for c in rows if item is None or c['argv'][c['argv'].index('--item') + 1] == item]


def opt(call, name):
    argv = call['argv']
    return argv[argv.index(name) + 1] if name in argv else None


def verdicts(w, item, result='ACCEPTED'):
    return [e for e in w.events(kind='verdict', item=item) if e.get('result') == result]


def done_events(w, item):
    return w.events(kind='item', item=item, state='done')


def kyjob_items(w):
    return [c['item'] for c in w.calls('kyjob')]


def claim_record(w, worker='v1'):
    path = w.run_dir / 'claims' / (worker + '.json')
    return json.loads(path.read_text()) if path.exists() else None


def claim_events(w, item):
    return w.events(kind='claim', item=item)


def reviewer_states(w):
    states = [json.loads(p.read_text()) for p in sorted((w.run_dir / 'jobs').glob('J-*/state.json'))]
    return [s for s in states if s.get('stream') == 'V']


def stream_session(state):
    """The session the reviewer's program reported: the init event of its stream-json output."""
    rows = [json.loads(line) for line in Path(state['stdout_path']).read_text().splitlines()]
    return [r['session_id'] for r in rows if r.get('type') == 'system' and r.get('subtype') == 'init']


def live_job(w, lane='k1', ignore_term=False, deadline_in=-60, seconds=600, **override):
    group = w.start_group(ignore_term=ignore_term, seconds=seconds)
    fields = dict(group)
    fields.pop('proc')
    w.add_job('J-' + lane, worktree=w.wt / lane, phase='live', proc=fields, deadline_in=deadline_in, **override)
    return group


# ───────────────────────────────────────── the accepted path, in full ─────────────────────────────────────────────

def test_accepted_run_records_everything_it_claims():
    with World('accepted') as w:
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        drain, final = w.drain, w.final
        assert drain['result'] == final['result'] == 'ACCEPTED'
        assert drain['schema'] == 'ky.drain_receipt/1' and final['schema'] == 'ky.final_receipt/1'
        assert drain['loops'] == {l: 'stopped' for l in ('dispatcher', 'planner', 'conductor', 'veto')}
        assert [c['argv'] for c in w.calls('kyctl')] == [['stop', l] for l in ('dispatcher', 'planner', 'conductor', 'veto')]
        assert drain['lanes'] == {'k1': 'clean'} and final['lanes'] == {'k1': 'removed'}
        assert not (w.wt / 'k1').exists() and (w.src / '.git').exists()
        assert final['drain_sha256'] == sha256(w.run_dir / 'DRAIN_RECEIPT.json')
        assert final['close_report'] == {'path': str(w.report), 'sha256': sha256(w.report)}
        assert final['absence'] == {'processes': 'absent', 'worktrees': 'absent', 'databases': 'absent'}
        # §12: C-3 on the drain receipt, then the V claim, release and C-4 on the final receipt, all by the S stream
        done3 = done_events(w, 'C-3')
        done4 = done_events(w, 'C-4')
        assert [d['completion']['artifact_digest'] for d in done3] == [sha256(w.run_dir / 'DRAIN_RECEIPT.json')]
        assert [d['completion']['artifact_digest'] for d in done4] == [sha256(w.run_dir / 'FINAL_RECEIPT.json')]
        assert ky_verbs(w) == [('done', 'C-3', 'S', None), ('claim', 'C-4', 'V', 'v1'),
                               ('release', None, 'V', 'v1'), ('done', 'C-4', 'S', None)]
        calls = {(c['argv'][0], c['argv'][1] if len(c['argv']) > 1 else None): c for c in w.calls('ky')}
        assert calls[('done', 'C-3')]['argv'] == ['done', 'C-3', '--artifact-path', str(w.run_dir / 'DRAIN_RECEIPT.json')]
        assert calls[('done', 'C-4')]['argv'] == ['done', 'C-4', '--artifact-path', str(w.run_dir / 'FINAL_RECEIPT.json')]
        assert calls[('claim', 'C-4')]['argv'] == ['claim', 'C-4', '--worker', 'v1', '--lease', '10800']
        assert calls[('claim', 'C-4')]['stream'] == 'V' and calls[('claim', 'C-4')]['lane'] == 'v1'
        assert calls[('release', None)]['lane'] == 'v1'
        # two bounded stream-V reviewers, different identity from the author, outside ordinary dispatch
        jobs = w.calls('kyjob')
        assert [(j['item'], j['stream'], j['kind'], j['max_turns'], j['prompt_has_header'], j['database_url_set']) for j in jobs] == \
            [('C-3', 'V', 'ARTIFACT', 60, True, False), ('C-4', 'V', 'ARTIFACT', 60, True, False)]
        assert [j['slot'] for j in jobs] == ['v1', 'v2']           # C-4 is claimed by v1, so its review is a separate lane
        for call in publishes(w):
            assert opt(call, '--author-id') != opt(call, '--reviewer-id') and opt(call, '--reviewer-id').startswith('J-')
            assert opt(call, '--phase') == 'artifact' and opt(call, '--job-exit') == '0'
            assert '--external-review-path' not in call['argv']
        assert [(v['item'], v['actor']) for v in w.events(kind='verdict')] == [('C-3', 'stream-V:v1'), ('C-4', 'stream-V:v2')]
        assert [c['argv'][0] for c in w.calls('kyboundary')] == ['check', 'release', 'check', 'release']
        # one kyaction record per ky event and per reviewer launch, finalizer / supervisor, all DONE
        actions = w.actions()
        assert len([a for a in actions if a.startswith('FIN-')]) == len(actions) == 6
        assert all(a['state'] == 'DONE' and a['actor']['role'] == 'finalizer' and a['actor']['holder_kind'] == 'supervisor'
                   and a['actor']['controller_id'] for a in actions.values())
        assert sorted(a['kind'] for a in actions.values()).count('reviewer_launch') == 2
        message = (w.run_dir / 'FINAL_MESSAGE.md').read_text()
        assert 'fixture final message' in message and str(w.run_dir / 'FINAL_RECEIPT.json') in message
        assert 'test databases removed' in message and 'preserved' not in message
        assert all((w.pravaha / ('RUNNER_STOP_' + x)).exists() for x in 'ABC')
        for key in ('ts', 'result', 'lanes', 'branches', 'campaign_worktree', 'phase', 'v1', 'pravaha_writers', 'jobs'):
            assert key in drain
        for key in ('ts', 'result', 'lanes', 'branches', 'campaign_worktree', 'phase', 'fleet_processes_remaining',
                    'worktrees_remaining', 'final_review_result'):
            assert key in final
        assert drain['jobs'] == [] and drain['pravaha_writers'].startswith('frozen')


def test_lone_copy_in_an_empty_directory_runs_to_acceptance():
    with World('lone') as w:
        lone = w.root / 'lonely'
        lone.mkdir()
        copy = lone / 'finalize.sh'
        shutil.copy(SCRIPT, copy)
        rc, out, err = w.finalize(script=copy)
        assert rc == 0 and w.final['result'] == 'ACCEPTED', (out, err)
        assert sorted(p.name for p in lone.iterdir()) == ['finalize.sh']


def test_an_argument_exits_64_before_anything_happens():
    with World('arg') as w:
        rc, out, err = w.finalize(args=('--force',))
        assert rc == 64 and w.drain is None and w.calls() == []


# ───────────────────────────────────────── drain: job groups ──────────────────────────────────────────────────────

UNPROVEN = [
    ('identity_mismatch', dict(process_start='Mon Jan  1 00:00:00 2001')),
    ('start_unreadable', dict(process_start='not a time')),
    ('start_missing', dict(process_start=None)),
    ('pid_pending', dict(pid='pending')),
    ('pgid_one', dict(pgid=1)),
    ('deadline_other_form', dict(deadline='2026-10-12 12:00:00')),
    ('deadline_fraction', dict(deadline='2026-10-12T12:00:00.5Z')),
    ('deadline_offset', dict(deadline='2026-10-12T12:00:00+00:00')),
    ('deadline_missing', dict(deadline=None)),
]


@pytest.mark.parametrize('name,override', UNPROVEN, ids=[n for n, _ in UNPROVEN])
def test_group_of_unknown_identity_is_never_signalled_and_fails_the_drain(name, override):
    with World(name) as w:
        group = live_job(w, **override)
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'FAILED' and w.final is None, (out, err)
        assert w.drain['lanes']['k1'] == 'busy_kept' and (w.wt / 'k1').exists()
        assert w.alive(group), 'a group of unproven identity was signalled'
        assert w.drain['jobs'][0]['result'] == 'busy_kept' and w.drain['jobs'][0]['job_id'] == 'J-k1'
        assert w.calls('kyjob') == [] and w.calls('kyverdicts') == [] and w.calls('ky') == []
        assert not done_events(w, 'C-3')


def test_leader_gone_but_group_alive_is_busy_not_gone():
    with World('orphan') as w:
        proc = subprocess.Popen(['sh', '-c', 'sleep 600 & sleep 0.3'], start_new_session=True, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        start = None
        for _ in range(60):
            ident = kyaction.ps_identity(proc.pid)
            if ident:
                start = ident[1]
                break
            time.sleep(0.02)
        assert start
        w.add_job('J-k1', worktree=w.wt / 'k1', phase='live', pid=proc.pid, pgid=proc.pid, process_start=start)
        proc.wait()
        try:
            rc, out, err = w.finalize()
            assert rc == 1 and w.drain['lanes']['k1'] == 'busy_kept' and w.drain['result'] == 'FAILED', (out, err)
            os.killpg(proc.pid, 0)               # the orphan was left alone: the group still exists
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)       # a group this test started
            except ProcessLookupError:
                pass


def test_group_past_its_deadline_is_terminated_then_the_drain_is_accepted():
    with World('term') as w:
        group = live_job(w)
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        assert not w.alive(group) and gone(group['pid'])
        job = w.drain['jobs'][0]
        assert job['result'] == 'terminated' and job['pid'] == group['pid'] and job['process_start'] == group['process_start']
        assert w.drain['result'] == 'ACCEPTED' and w.final['result'] == 'ACCEPTED'


def test_group_that_ignores_term_is_killed_after_the_grace():
    with World('kill') as w:
        group = live_job(w, ignore_term=True)
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        assert w.drain['jobs'][0]['result'] == 'killed' and gone(group['pid'])
        assert w.final['absence']['processes'] == 'absent'


def test_group_that_ends_inside_its_deadline_is_waited_for_not_signalled():
    with World('wait') as w:
        group = live_job(w, deadline_in=120, seconds=1)
        rc, out, err = w.finalize(KY_DRAIN_WAIT_MIN='0.5')
        assert rc == 0, (out, err)
        assert w.drain['jobs'][0]['result'] == 'exited' and gone(group['pid'])


def test_the_wait_is_capped_by_the_drain_knob():
    with World('cap') as w:
        group = live_job(w, deadline_in=3000)
        started = time.time()
        rc, out, err = w.finalize(KY_DRAIN_WAIT_MIN='0.03')
        assert rc == 0 and time.time() - started < 60, (out, err)
        assert w.drain['jobs'][0]['result'] == 'terminated' and gone(group['pid'])


def test_a_job_whose_state_turns_ended_while_its_group_lives_is_not_called_gone():
    # sweep: the record saying `ended` is not the measurement; gone = leader False AND killpg(pgid, 0) ESRCH
    with World('flip') as w:
        group = live_job(w, deadline_in=3000)
        state = w.run_dir / 'jobs' / 'J-k1' / 'state.json'

        def flip():
            end = time.time() + 30
            while time.time() < end and len(w.calls('kyctl')) < 4:
                time.sleep(0.02)
            doc = json.loads(state.read_text())
            doc.update(phase='ended')
            tmp = state.with_suffix('.tmp')
            tmp.write_text(json.dumps(doc))
            os.replace(tmp, state)

        thread = threading.Thread(target=flip, daemon=True)
        thread.start()
        rc, out, err = w.finalize(KY_DRAIN_WAIT_MIN='0.1')
        thread.join(timeout=30)
        job = w.drain['jobs'][0]
        assert job['result'] != 'ended', 'a group that was alive was called gone because its state said ended'
        assert job['result'] == 'terminated' and not w.alive(group) and gone(group['pid']), (job, out, err)
        assert rc == 0 and w.drain['result'] == 'ACCEPTED' and w.final['absence']['processes'] == 'absent', (out, err)


ENDED_BUT = [('alive', {}, 'alive'), ('identity_unknown', {'process_start': None}, 'unknown'),
             ('pid_pending', {'pid': 'pending', 'pgid': None}, 'unknown')]


@pytest.mark.parametrize('name,override,measured', ENDED_BUT, ids=[n for n, *_ in ENDED_BUT])
def test_a_job_recorded_ended_whose_group_is_not_proven_gone_fails_the_drain(name, override, measured):
    # review r3 B1: the drain measures EVERY recorded group, whatever its phase. A state that says `ended` over a group
    # that is alive, or cannot be measured (KV3-B-KYDJOBS records a launching pid as "pending"), is never signalled,
    # is busy_kept, keeps its worktree and fails the drain: no review, no C-3, no removal
    with World('ended-' + name) as w:
        group = live_job(w, deadline_in=3000)
        state = w.run_dir / 'jobs' / 'J-k1' / 'state.json'
        doc = json.loads(state.read_text())
        doc.update(phase='ended', **override)
        state.write_text(json.dumps(doc))
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert w.alive(group), 'an ended job is never signalled by the finalizer'
        assert w.drain['result'] == 'FAILED' and w.final is None, w.drain
        job = w.drain['jobs'][0]
        assert (job['job_id'], job['phase'], job['result']) == ('J-k1', 'ended', 'busy_kept')
        assert job['reason'] == 'recorded_ended_but_group_%s' % measured
        assert w.drain['lanes'] == {'k1': 'busy_kept'} and (w.wt / 'k1').exists()
        assert w.calls('kyjob') == [] and w.calls('kyverdicts') == [] and w.calls('ky') == [] and w.calls('local_db') == []
        assert not done_events(w, 'C-3') and not w.events(kind='verdict') and not claim_events(w, 'C-4')


def test_a_job_recorded_ended_whose_group_is_measured_gone_does_not_hold_the_drain():
    # the other half of B1's detector: the same record over a group that IS gone is not busy, and is not listed
    with World('ended-gone') as w:
        group = live_job(w, deadline_in=3000, seconds=1)
        state = w.run_dir / 'jobs' / 'J-k1' / 'state.json'
        doc = json.loads(state.read_text())
        doc.update(phase='ended')
        state.write_text(json.dumps(doc))
        assert gone(group['pid'])
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        assert w.drain['jobs'] == [] and w.drain['lanes'] == {'k1': 'clean'} and w.final['lanes'] == {'k1': 'removed'}


def test_an_ended_record_over_a_live_group_that_appears_after_the_drain_keeps_its_worktree():
    # review r3 B1, the step-6 busy set: the removal measures every recorded group too, whatever its phase
    with World('ended-late') as w:
        w.flag('reviewer_ended_straggler_C-3')
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'ACCEPTED', (out, err)
        assert w.final['result'] == 'FAILED' and w.final['failed_step'] == 'final_receipt'
        assert w.final['lanes'] == {'k1': 'busy_kept'} and (w.wt / 'k1' / '.git').exists()
        assert w.final['absence']['processes'] == 'survivor'
        assert not claim_events(w, 'C-4') and not done_events(w, 'C-4')


def test_a_job_whose_ancestry_cannot_be_read_is_never_signalled():
    # review r3 N4 (sweep): is_self_or_ancestor() answers None when the process tree is unreadable; unknown is not
    # "not ours", so nothing is signalled and the job is busy_kept
    with World('ancestry') as w:
        w.patch_kyaction('def is_self_or_ancestor(pid):\n    return None\n')
        group = live_job(w)
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'FAILED' and w.final is None, (out, err)
        assert w.alive(group), 'a group was signalled although its relation to the finalizer was unknown'
        job = w.drain['jobs'][0]
        assert job['result'] == 'busy_kept' and job['reason'] == 'own_process_tree_or_unknown'
        assert w.calls('kyjob') == [] and w.calls('ky') == []


def test_a_job_directory_without_a_state_is_unknown_not_nothing():
    # sweep: a directory under run/jobs that holds something but no state.json is a job this script cannot read
    with World('nostate') as w:
        odd = w.run_dir / 'jobs' / 'J-odd'
        odd.mkdir()
        (odd / 'state.json.tmp.4242').write_text('{"job_id": "J-odd", "phase": "live", "pid": 1')
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'FAILED' and w.final is None, (out, err)
        assert {'path': str(odd), 'problem': 'job_directory_without_state'} in w.drain['problems']
        assert w.calls('kyjob') == [] and w.calls('ky') == [] and (w.wt / 'k1').exists()


def test_an_empty_job_directory_records_no_job():
    with World('emptyjob') as w:
        (w.run_dir / 'jobs' / 'J-empty').mkdir()
        rc, out, err = w.finalize()
        assert rc == 0 and w.drain['problems'] == [], (out, err)


def test_a_loop_not_confirmed_stopped_fails_the_drain_even_with_no_job_alive():
    # review r3 N1: dropping the loops from the drain's acceptance survived the suite
    with World('loop-idle') as w:
        w.flag('kyctl_fail_planner')
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'FAILED' and w.final is None, (out, err)
        assert w.drain['loops']['planner'] == 'not_stopped' and w.drain['jobs'] == [] and w.drain['lanes'] == {'k1': 'clean'}
        assert w.calls('kyjob') == [] and w.calls('ky') == [] and (w.wt / 'k1').exists()


def test_a_loop_that_cannot_be_confirmed_stopped_blocks_every_signal():
    with World('loop') as w:
        group = live_job(w)
        w.flag('kyctl_fail_dispatcher')
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'FAILED' and w.final is None
        assert w.drain['loops']['dispatcher'] == 'not_stopped' and w.drain['loops']['veto'] == 'stopped'
        assert w.alive(group) and w.drain['jobs'][0]['result'] == 'busy_kept'
        assert w.calls('kyjob') == [] and w.calls('ky') == []


def test_an_unreadable_job_state_fails_the_drain():
    with World('garbage') as w:
        (w.run_dir / 'jobs' / 'J-bad').mkdir()
        (w.run_dir / 'jobs' / 'J-bad' / 'state.json').write_text('{not json')
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'FAILED' and w.drain['problems'] and w.final is None


# ───────────────────────────────────────── drain: worktrees ───────────────────────────────────────────────────────

@pytest.mark.parametrize('how,state', [('make_dirty', 'dirty_kept'), ('make_unpushed', 'unpushed_kept')])
def test_dirty_or_unpushed_work_fails_the_drain_and_is_kept(how, state):
    with World(how) as w:
        getattr(w, how)('k1')
        before = sorted(p.name for p in (w.wt / 'k1').iterdir())
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'FAILED' and w.final is None
        assert w.drain['lanes'] == {'k1': state} and sorted(p.name for p in (w.wt / 'k1').iterdir()) == before
        assert w.calls('kyjob') == [] and w.calls('ky') == [] and w.calls('local_db') == []


def test_a_recorded_worktree_path_that_exists_without_git_metadata_is_not_absent():
    # sweep: `absent` is the path not existing, not its `.git` not existing
    with World('plain', lanes=()) as w:
        plain = w.wt / 'k9'
        plain.mkdir()
        (plain / 'notes.txt').write_text('work of unknown state\n')
        w.add_job('J-k9', worktree=plain)
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'FAILED' and w.final is None, (out, err)
        assert w.drain['lanes'] == {'k9': 'dirty_kept'} and (plain / 'notes.txt').exists()
        assert w.calls('kyjob') == [] and w.calls('ky') == [] and not done_events(w, 'C-3')


def test_work_written_while_the_review_runs_is_kept_by_the_removal():
    with World('late') as w:
        w.flag('reviewer_dirties_C-3')
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'ACCEPTED' and w.final['result'] == 'FAILED', (out, err)
        assert w.final['lanes'] == {'k1': 'dirty_kept'} and (w.wt / 'k1' / 'late-work.txt').exists()
        assert w.final['failed_step'] == 'final_receipt' and w.final['absence']['worktrees'] == 'survivor'
        assert not done_events(w, 'C-4') and kyjob_items(w) == ['C-3']


def test_the_source_repository_is_never_removed_even_when_a_job_names_it():
    with World('source') as w:
        w.add_job('J-src', worktree=w.src)
        rc, out, err = w.finalize()
        assert rc == 0 and (w.src / '.git').exists() and 'source' not in w.drain['lanes']


def test_a_campaign_checkout_under_the_ky_root_is_never_removed():
    with World('campaign') as w:
        camp = w.add_worktree('campaign')
        w.add_job('J-camp', worktree=camp)
        rc, out, err = w.finalize()
        assert rc == 0 and camp.exists() and 'campaign' not in w.final['lanes']


# ───────────────────────────────────────── review: no verdict ─────────────────────────────────────────────────────

REVIEW_FAILURES = [
    ('mutate_receipt', 'reviewer_mutate_receipt_%s', False),
    ('tamper_stream', 'reviewer_tamper_stream_%s', False),
    ('wrong_slot', 'reviewer_wrong_slot_%s', False),
    ('wrong_job', 'reviewer_wrong_job_%s', False),
    ('exit1', 'reviewer_exit1_%s', False),
    ('no_result', 'reviewer_no_result_%s', False),
    ('reject', 'reviewer_reject_%s', True),
]


@pytest.mark.parametrize('name,flag,publishes_rejection', REVIEW_FAILURES, ids=[r[0] for r in REVIEW_FAILURES])
def test_drain_review_failures_publish_no_acceptance_and_complete_nothing(name, flag, publishes_rejection):
    with World('dr-' + name) as w:
        w.flag(flag % 'C-3')
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert w.drain['result'] == 'ACCEPTED'
        assert w.final['result'] == 'FAILED' and w.final['failed_step'] == 'drain_review' and w.final['reason']
        assert not verdicts(w, 'C-3') and not done_events(w, 'C-3') and not done_events(w, 'C-4')
        assert (w.wt / 'k1').exists(), 'nothing is removed before C-3'
        assert w.calls('local_db') == [] and 'claim' not in [v for v, *_ in ky_verbs(w)]
        assert bool(publishes(w, 'C-3')) == publishes_rejection
        if publishes_rejection:
            assert len(verdicts(w, 'C-3', 'REJECTED')) == 1


@pytest.mark.parametrize('name,flag,publishes_rejection', REVIEW_FAILURES, ids=[r[0] for r in REVIEW_FAILURES])
def test_close_review_failures_publish_no_acceptance_and_complete_nothing(name, flag, publishes_rejection):
    with World('cl-' + name) as w:
        w.flag(flag % 'C-4')
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert len(done_events(w, 'C-3')) == 1 and not done_events(w, 'C-4') and not verdicts(w, 'C-4')
        assert w.final['result'] == 'FAILED' and w.final['failed_step'] == 'close_review'
        assert bool(publishes(w, 'C-4')) == publishes_rejection
        assert ('release', None, 'V', 'v1') in ky_verbs(w), 'the V claim is released when the review does not accept'
        assert claim_record(w)['state'] == 'released' and claim_events(w, 'C-4')[-1]['state'] == 'released'


@pytest.mark.parametrize('code', ['1', '3'])
def test_boundary_violated_or_unknown_publishes_nothing(code):
    with World('boundary' + code) as w:
        w.flag('boundary_exit', code)
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'drain_review'
        assert publishes(w) == [] and not w.events(kind='verdict')
        assert all(c['argv'][0] in ('check', 'release') for c in w.calls('kyboundary'))


def test_snapshot_failure_launches_no_reviewer():
    with World('snap') as w:
        w.flag('snapshot_fail')
        rc, out, err = w.finalize()
        assert rc == 1 and w.calls('kyjob') == [] and w.final['failed_step'] == 'drain_review'


def test_publisher_refusal_stops_without_completion():
    with World('refuse') as w:
        w.flag('publish_refuse')
        rc, out, err = w.finalize()
        assert rc == 1 and not w.events(kind='verdict') and not done_events(w, 'C-3')


@pytest.mark.parametrize('item,step', [('C-3', 'drain_review'), ('C-4', 'close_review')])
def test_a_reviewer_under_the_authors_session_is_not_independent(item, step):
    # B1 (r2): the session is MEASURED from the init event of the reviewer's stream-json output; here it is the author's
    with World('indep-session-' + item) as w:
        w.flag('reviewer_session_' + item, 'sess-author')
        rc, out, err = w.finalize(KY_SESSION_ID='sess-author')
        assert rc == 1, (out, err)
        assert w.final['result'] == 'FAILED' and w.final['failed_step'] == step
        assert 'reviewer_not_independent' in w.final['reason'], w.final['reason']
        assert publishes(w, item) == [] and not w.events(kind='verdict', item=item) and not done_events(w, item)
        assert not done_events(w, 'C-4')


def test_a_reviewer_under_its_own_session_is_independent():
    with World('indep-own') as w:
        w.flag('reviewer_session_C-3', 'sess-reviewer-1')
        w.flag('reviewer_session_C-4', 'sess-reviewer-2')
        rc, out, err = w.finalize(KY_SESSION_ID='sess-author')
        assert rc == 0, (out, err)
        assert len(verdicts(w, 'C-3')) == 1 and len(verdicts(w, 'C-4')) == 1
        # finalize.sh is the state writer: what it measured from the stream is what the job state records
        first, second = reviewer_states(w)
        assert (first['provider_session_id'], second['provider_session_id']) == ('sess-reviewer-1', 'sess-reviewer-2')
        assert stream_session(first) == ['sess-reviewer-1'] and stream_session(second) == ['sess-reviewer-2']


def test_a_default_run_records_the_session_each_reviewer_stream_reported():
    with World('indep-measured') as w:
        assert w.finalize()[0] == 0
        first, second = reviewer_states(w)
        for state in (first, second):
            assert stream_session(state) == [state['provider_session_id']] and state['provider_session_id']
        assert first['provider_session_id'] != second['provider_session_id']


UNMEASURED = ['reviewer_no_stream_%s', 'reviewer_stream_without_init_%s', 'reviewer_init_without_session_%s',
              'reviewer_two_sessions_%s', 'reviewer_session_in_state_only_%s']
UNMEASURED_CASES = [(f, 'C-3', 'drain_review') for f in UNMEASURED] + [(UNMEASURED[0], 'C-4', 'close_review'),
                                                                        (UNMEASURED[4], 'C-4', 'close_review')]


@pytest.mark.parametrize('flag,item,step', UNMEASURED_CASES, ids=[(f % i) for f, i, _ in UNMEASURED_CASES])
def test_a_reviewer_whose_session_cannot_be_measured_gets_no_verdict(flag, item, step):
    # B1 (r2): no stream, no init event, an init event without a session, init events that disagree, or a session
    # that exists only in the job state (which kyjob.sh never writes): unknown is not independent
    with World('indep-unmeasured') as w:
        w.flag(flag % item)
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert w.final['result'] == 'FAILED' and w.final['failed_step'] == step
        assert 'reviewer_not_independent(provider_session_unmeasured' in w.final['reason'], w.final['reason']
        assert publishes(w, item) == [] and not w.events(kind='verdict', item=item) and not done_events(w, item)
        assert not done_events(w, 'C-4')
        state = [s for s in reviewer_states(w) if s['item'] == item][0]
        assert state['provider_session_id'] is None, 'an unmeasured session is recorded as null, never as a value'


@pytest.mark.parametrize('item,step', [('C-3', 'drain_review'), ('C-4', 'close_review')])
def test_a_reviewer_under_the_session_of_another_recorded_job_is_not_independent(item, step):
    # the reviewer resumed the session of a job whose work the receipt covers: measured against run/jobs/*/state.json
    with World('indep-other-job') as w:
        w.add_job('J-builder', provider_session_id='sess-builder-9')
        w.flag('reviewer_session_' + item, 'sess-builder-9')
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert w.final['failed_step'] == step and 'provider_session_is_another_jobs' in w.final['reason'], w.final['reason']
        assert publishes(w, item) == [] and not w.events(kind='verdict', item=item) and not done_events(w, item)


def test_the_close_reviewer_under_the_drain_reviewers_session_is_not_independent():
    with World('indep-same-twice') as w:
        w.flag('reviewer_session_C-3', 'sess-reviewer-1')
        w.flag('reviewer_session_C-4', 'sess-reviewer-1')
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'close_review', (out, err)
        assert 'provider_session_is_another_jobs' in w.final['reason'], w.final['reason']
        assert len(verdicts(w, 'C-3')) == 1 and publishes(w, 'C-4') == [] and not done_events(w, 'C-4')


# the proposal is bound to the digest; the boundary evidence is this job's; the verdict is the tracker's event
BOUND = ['reviewer_other_digest_%s', 'reviewer_no_digest_%s']


@pytest.mark.parametrize('flag', BOUND, ids=['other_digest', 'no_digest'])
@pytest.mark.parametrize('item,step', [('C-3', 'drain_review'), ('C-4', 'close_review')])
def test_an_acceptance_proposed_for_another_digest_or_for_none_is_not_published(flag, item, step):
    # sweep: plan §12 "accepts its exact digest" — a model-written ACCEPTED that names no digest, or another, accepts nothing
    with World('bound') as w:
        w.flag(flag % item)
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == step, (out, err, w.final)
        assert 'reviewer_verdict_not_on_this_digest' in w.final['reason'], w.final['reason']
        assert publishes(w, item) == [] and not w.events(kind='verdict', item=item) and not done_events(w, item)


@pytest.mark.parametrize('flag', ['boundary_other_job', 'boundary_not_object'])
def test_boundary_evidence_of_another_job_or_of_no_recognised_shape_publishes_nothing(flag):
    # sweep: `kyboundary.sh check` exit 0 is evidence only as the object the producer prints, for THIS job
    with World(flag) as w:
        w.flag(flag)
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'drain_review' and 'boundary_' in w.final['reason'], (out, err, w.final)
        assert publishes(w) == [] and not w.events(kind='verdict') and not done_events(w, 'C-3')
        assert [c['argv'][0] for c in w.calls('kyboundary')] == ['check', 'release']


@pytest.mark.parametrize('flag', ['publish_answers_without_event', 'publish_answer_not_object'])
def test_a_publisher_answer_without_the_trackers_verdict_event_is_no_verdict(flag):
    # sweep: `published: true` on stdout is a log line; the backing record is the verdict event in the tracker's log
    with World(flag) as w:
        w.flag(flag)
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'drain_review', (out, err, w.final)
        assert 'verdict_event_not_observed' in w.final['reason'] or 'publish_' in w.final['reason'], w.final['reason']
        assert len(publishes(w, 'C-3')) == 1 and not w.events(kind='verdict')
        assert w.calls('ky') == [], 'no ky done is attempted on a verdict nothing recorded'
        assert (w.wt / 'k1').exists() and w.calls('local_db') == []


def test_a_verdict_event_of_another_job_on_the_same_digest_is_not_this_reviews_verdict():
    # review r3 N2: the latest verdict on (item, digest) counts only when it is THIS job's (detail `job <J>; …`)
    with World('otherjob') as w:
        w.flag('publish_as_other_job')
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'drain_review', (out, err, w.final)
        assert 'verdict_event_not_observed' in w.final['reason'], w.final['reason']
        assert len(verdicts(w, 'C-3')) == 1 and w.calls('ky') == [] and (w.wt / 'k1').exists()


def test_a_later_rejection_of_the_same_digest_revokes_the_acceptance_on_a_rerun():
    # the tracker's rule (verdicts.py accepted_verdict): the LATEST verdict at this identity decides
    with World('revoked') as w:
        w.flag('crash_before_done_C-3')
        assert w.finalize()[0] == -signal.SIGKILL
        accepted = verdicts(w, 'C-3')[0]
        w.append_event(dict(accepted, result='REJECTED', detail='invalidated: fixture'))
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'drain_review', (out, err, w.final)
        assert 'no accepted verdict' in w.final['reason'] and len(publishes(w, 'C-3')) == 1, w.final['reason']
        assert not done_events(w, 'C-3') and (w.wt / 'k1').exists()
        assert [c['argv'][0] for c in w.calls('ky')] == ['done'], 'only the first run reached ky done'


def test_a_reviewer_recording_the_authors_process_as_its_own_is_not_independent():
    with World('indep-process') as w:
        w.flag('reviewer_is_author_process_C-3')
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'drain_review', (out, err)
        assert 'reviewer_not_independent' in w.final['reason'], w.final['reason']
        assert publishes(w) == [] and not w.events(kind='verdict') and not done_events(w, 'C-3')


def test_reviewer_that_hangs_is_killed_at_its_deadline_and_proven_gone():
    with World('hang', final_wait_min='0.05') as w:
        w.flag('reviewer_hang_C-3')
        started = time.time()
        rc, out, err = w.finalize()
        assert rc == 1 and time.time() - started < 60, (out, err)
        job = w.calls('kyjob')[0]
        assert gone(job['own_pid'])
        reviewer = [json.loads(p.read_text()) for p in (w.run_dir / 'jobs').glob('*/state.json')
                    if json.loads(p.read_text()).get('stream') == 'V'][0]
        assert reviewer['phase'] == 'ended' and reviewer['outcome'] == 'timed_out' and reviewer['pgid'] == job['own_pgid']
        assert not w.events(kind='verdict') and w.final['failed_step'] == 'drain_review'


def test_a_child_the_reviewer_leaves_in_its_group_is_reaped_before_the_verdict():
    with World('child') as w:
        w.flag('reviewer_leaves_child_C-3')
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        child = int((w.root / 'child.pid').read_text())
        assert gone(child)


def test_reviewer_state_is_a_complete_stream_v_artifact_job():
    with World('state') as w:
        assert w.finalize()[0] == 0
        states = [json.loads(p.read_text()) for p in sorted((w.run_dir / 'jobs').glob('J-*/state.json'))]
        reviewers = [s for s in states if s.get('stream') == 'V']
        assert len(reviewers) == 2
        for s in reviewers:
            assert (s['schema'], s['kind'], s['role'], s['max_turns'], s['phase'], s['outcome'], s['exit_code']) == \
                ('ky.job/1', 'ARTIFACT', 'reviewer', 60, 'ended', 'done', 0)
            assert kyaction.parse_utc(s['ended_at']) <= kyaction.parse_utc(s['deadline']) + 1
            assert s['slot'] in ('v1', 'v2') and s['worktree'] == str(w.src) and s['controller_id']
            assert all(Path(s[k]).is_absolute() for k in ('job_scratch', 'prompt_path', 'stdout_path', 'stderr_path', 'tmp_path',
                                                           'card_path', 'packet_path', 'mcp_config'))
            assert s['pid'] and s['pgid'] == s['pid']
            prompt = Path(s['prompt_path']).read_bytes()
            assert prompt.startswith(Path(s['card_path']).read_bytes() + Path(s['packet_path']).read_bytes())
        assert reviewers[0]['digest'] == sha256(w.run_dir / 'DRAIN_RECEIPT.json')
        assert reviewers[1]['digest'] == sha256(w.run_dir / 'FINAL_RECEIPT.json')


# ───────────────────────────────────────── the recheck ────────────────────────────────────────────────────────────

def test_anything_present_at_the_recheck_blocks_the_verdict():
    with World('straggler') as w:
        w.flag('reviewer_straggler_C-4')
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain['result'] == 'ACCEPTED' and w.final['result'] == 'FAILED', (out, err)
        assert w.final['absence']['processes'] == 'survivor' and w.final['failed_step'] == 'close_review'
        assert publishes(w, 'C-4') == [] and not done_events(w, 'C-4')
        assert ('release', None, 'V', 'v1') in ky_verbs(w)


def test_a_database_that_appears_during_the_review_blocks_the_verdict():
    with World('dbappears') as w:
        w.flag('reviewer_adds_db_C-4')
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['absence']['databases'] == 'survivor' and publishes(w, 'C-4') == []
        assert not done_events(w, 'C-4')


# ───────────────────────────────────────── KU-02: databases ───────────────────────────────────────────────────────

DB_FAILURES = ['handed_over', 'exit1', 'wrong_mount', 'ownership_conflict', 'stale_ready', 'stop_without_removal', 'no_token']


@pytest.mark.parametrize('mode', DB_FAILURES)
def test_database_not_proven_absent_is_not_accepted(mode):
    with World('db-' + mode) as w:
        w.add_db_receipt('v1', 'sess-1')
        w.flag('db_mode', mode)
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert w.drain['result'] == 'ACCEPTED' and w.final['result'] == 'FAILED' and w.final['failed_step'] == 'final_receipt'
        assert w.final['absence']['databases'] in ('survivor', 'unknown')
        assert kyjob_items(w) == ['C-3'] and not done_events(w, 'C-4') and 'claim' not in [v for v, *_ in ky_verbs(w)]
        assert [c['argv'] for c in w.calls('local_db')][0] == ['close', '--session', 'sess-1']


@pytest.mark.parametrize('mode', ['other_session_line', 'tokens_on_two_lines'])
def test_a_close_line_that_is_not_this_sessions_report_proves_nothing(mode):
    # sweep: the producer prints ONE line `close session=S dropped=<n> container=<c>`; anything else is unknown
    with World('db-' + mode) as w:
        w.add_db_receipt('v1', 'sess-1')
        w.flag('db_mode', mode)
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert w.final['result'] == 'FAILED' and w.final['failed_step'] == 'final_receipt'
        assert w.final['absence']['databases'] == 'unknown'
        row = w.final['absence_detail']['databases']['sessions'][0]
        assert row['session'] == 'sess-1' and row['exit'] == 0 and row['container'] is None and row['stdout']
        assert kyjob_items(w) == ['C-3'] and not done_events(w, 'C-4')


def test_a_session_name_local_db_accepts_is_closed_under_that_name():
    # BR-09: local_db.sh's session rule is ^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$ (KV3-B-LOCALDB): an underscore is a session
    with World('db-underscore') as w:
        w.add_db_receipt('v1', 'CTL_20261012.a-1')
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        assert [c['argv'][2] for c in w.calls('local_db')] == ['CTL_20261012.a-1'] * 2
        assert w.final['absence']['databases'] == 'absent'


@pytest.mark.parametrize('session', ['sess:1', 'a..b', 'x' * 65])
def test_a_session_name_local_db_would_refuse_is_never_passed_to_it(session):
    with World('db-badname') as w:
        w.add_db_receipt('v1', session)
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['absence']['databases'] != 'absent', (out, err)
        assert w.final['absence_detail']['databases']['unreadable_receipts'] == [str(w.run_dir / 'local_db' / 'v1.json')]
        assert session not in [c['argv'][2] for c in w.calls('local_db')]


def test_receipts_gone_but_a_database_survives_is_still_a_failure():
    with World('norcpt') as w:
        w.flag('db_mode', 'exit1')                            # no run/local_db/*.json at all
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['absence']['databases'] == 'survivor'
        closes = [c['argv'] for c in w.calls('local_db')]
        assert len(closes) == 1 and closes[0][:2] == ['close', '--session'] and closes[0][2]


def test_no_receipts_still_closes_under_the_finalizers_own_session():
    with World('own') as w:
        assert w.finalize()[0] == 0
        closes = [c['argv'] for c in w.calls('local_db')]
        assert [c[:2] for c in closes] == [['close', '--session']] * 2        # removal, then the recheck
        assert w.final['absence']['databases'] == 'absent'


def test_one_close_per_recorded_session():
    with World('sessions') as w:
        w.add_db_receipt('v1', 'sess-b')
        w.add_db_receipt('v2', 'sess-a')
        w.add_db_receipt('b1', 'sess-b')
        assert w.finalize()[0] == 0
        closes = [c['argv'][2] for c in w.calls('local_db')]
        assert closes == ['sess-a', 'sess-b', 'sess-a', 'sess-b']


def test_a_receipt_without_a_session_leaves_the_databases_unknown():
    with World('nosess') as w:
        (w.run_dir / 'local_db' / 'v1.json').write_text(json.dumps({'result': 'READY'}))
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['absence']['databases'] != 'absent' and w.final['failed_step'] == 'final_receipt'
        assert w.final['absence_detail']['databases']['unreadable_receipts'] == [str(w.run_dir / 'local_db' / 'v1.json')]


def test_the_hand_over_record_names_a_session_whose_close_is_owed():
    # BR-09 (KV3-B-LOCALDB): `close` records a hand-over in run/local_db/container.json as {owner, storage, from}. It
    # is not a slot receipt: its owner is a session whose close must run, and the record must be gone afterwards
    with World('handover') as w:
        w.add_db_receipt('v1', 'sess-1')
        w.add_handover(owner='sess-2', came_from='sess-0')
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        assert [c['argv'][2] for c in w.calls('local_db')] == ['sess-1', 'sess-2', 'sess-1', 'sess-2']
        assert w.final['absence']['databases'] == 'absent' and not list((w.run_dir / 'local_db').glob('*.json'))
        assert w.final['absence_detail']['databases']['unreadable_receipts'] == []


def test_a_hand_over_record_that_outlives_its_owners_close_is_a_survivor():
    with World('handover-kept') as w:
        w.add_handover(owner='sess-2', came_from='sess-0')
        w.flag('db_keep_handover')
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'final_receipt' and w.final['absence']['databases'] == 'survivor', (out, err)
        assert [c['argv'][2] for c in w.calls('local_db')] == ['sess-2']
        assert w.final['absence_detail']['databases']['receipts_remaining'] == [str(w.run_dir / 'local_db' / 'container.json')]
        assert not claim_events(w, 'C-4') and not done_events(w, 'C-4')


@pytest.mark.parametrize('record', [{'owner': 5, 'storage': '/x', 'from': 'sess-0'}, {'owner': 'sess:2', 'storage': '/x', 'from': 'a'},
                                    {'owner': 'sess-2'}, ['sess-2']], ids=['owner_type', 'owner_name', 'keys', 'not_object'])
def test_a_hand_over_record_of_no_recognised_shape_leaves_the_databases_unknown(record):
    with World('handover-odd') as w:
        (w.run_dir / 'local_db' / 'container.json').write_text(json.dumps(record))
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'final_receipt' and w.final['absence']['databases'] != 'absent', (out, err)
        assert w.final['absence_detail']['databases']['unreadable_receipts'] == [str(w.run_dir / 'local_db' / 'container.json')]
        assert 'sess:2' not in [c['argv'][2] for c in w.calls('local_db')]


def test_an_incompatible_container_is_preserved_and_reported_not_a_failure():
    with World('incompat') as w:
        w.add_db_receipt('v1', 'sess-1')
        w.flag('db_mode', 'incompatible')
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        assert w.final['absence']['databases'] == 'absent'
        assert 'incompatible' in json.dumps(w.final['absence_detail']['databases'])
        # review r3 N7 (sweep): the message does not say "removed" of a container that was preserved
        message = (w.run_dir / 'FINAL_MESSAGE.md').read_text()
        assert 'incompatible pre-existing container preserved' in message and 'sess-1' in message
        assert w.finalize()[0] == 0 and (w.run_dir / 'FINAL_MESSAGE.md').read_text() == message


# ───────────────────────────────────────── close report, draft, claim ─────────────────────────────────────────────

def test_missing_close_report_fails_the_final_receipt():
    with World('noreport') as w:
        rows = [e for e in w.events() if e.get('item') != 'C-1']
        (w.run_dir / 'EVENTS.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in rows))
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['result'] == 'FAILED' and w.final['close_report'] is None
        assert not [c for c in w.calls('ky') if c['argv'][0] == 'claim']


def test_close_report_changed_since_its_completion_fails():
    with World('badreport') as w:
        w.report.write_text('rewritten after C-1\n')
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['result'] == 'FAILED' and w.final['close_report'] is None


def test_missing_final_message_draft_fails_the_final_receipt():
    with World('nodraft') as w:
        (w.run_dir / 'FINAL_MESSAGE_DRAFT.md').unlink()
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['result'] == 'FAILED'


def test_no_v_claim_on_c4_means_no_review_no_verdict_no_completion():
    with World('noclaim') as w:
        w.flag('ky_claim_fail')
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert w.final['result'] == 'FAILED' and w.final['failed_step'] == 'claim_C-4'
        assert kyjob_items(w) == ['C-3'] and publishes(w, 'C-4') == [] and not done_events(w, 'C-4')
        assert [v for v, *_ in ky_verbs(w)] == ['done', 'claim']
        assert not w.events(kind='claim')


def test_a_release_leaves_a_released_record_and_is_observed_as_released():
    # B1: the tracker keeps claims/<worker>.json after a release, rewritten with state released (claims.py _record)
    with World('released') as w:
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        record, events = claim_record(w), claim_events(w, 'C-4')
        assert [e['state'] for e in events] == ['acquired', 'released'] and record == events[-1]
        assert record['item'] == 'C-4' and record['worker_id'] == 'v1' and record['claim_id'] == events[0]['claim_id']
        release = [a for k, a in w.actions().items() if k.startswith('FIN-ky-release-C-4-')]
        assert len(release) == 1 and release[0]['state'] == 'DONE' and release[0]['result']['claim_id'] == record['claim_id']
        assert release[0]['inputs']['claim_id'] == record['claim_id']
        assert len(done_events(w, 'C-4')) == 1


@pytest.mark.parametrize('state', ['expired', 'released'])
def test_a_claim_recorded_as_not_active_is_not_held(state):
    # B1: a claim record that is not acquired/renewed is no claim, whatever item it names
    with World('claim-' + state) as w:
        w.flag('ky_claim_records_state', state)
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert w.final['failed_step'] == 'claim_C-4' and claim_record(w)['state'] == state
        assert kyjob_items(w) == ['C-3'] and publishes(w, 'C-4') == [] and not done_events(w, 'C-4')


@pytest.mark.parametrize('flag,why', [('ky_claim_already_expired', 'lease_expired'),
                                      ('ky_claim_record_differs', 'record_differs_from_event_log')])
def test_an_expired_claim_or_one_whose_record_differs_from_the_log_is_not_held(flag, why):
    # review r2 N1: mutations m6 (lease expiry) and m7 (record agreement) survived; each now has its fixture
    with World(flag) as w:
        w.flag(flag)
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'claim_C-4' and why in w.final['reason'], (out, err, w.final)
        assert kyjob_items(w) == ['C-3'] and publishes(w, 'C-4') == [] and not done_events(w, 'C-4')


def test_an_event_log_that_cannot_be_read_stops_before_anything_is_run_or_written():
    # review r2 N2 (mutation m8): whether C-4 is done cannot be observed
    with World('noevents') as w:
        (w.run_dir / 'EVENTS.jsonl').unlink()
        (w.run_dir / 'EVENTS.jsonl').mkdir()
        rc, out, err = w.finalize()
        assert rc == 1 and w.drain is None and w.final is None, (out, err)
        assert w.calls() == [] and (w.wt / 'k1').exists()


def test_lines_of_the_event_log_that_are_not_events_are_passed_over_as_the_tracker_does():
    # BR-09: claims.py _read skips a line that is not a valid event object; it is neither an event nor a crash
    with World('oddlines') as w:
        with open(w.run_dir / 'EVENTS.jsonl', 'a') as handle:
            handle.write('[]\n"text"\n{torn\n7\nnull\n')
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        assert w.drain['result'] == w.final['result'] == 'ACCEPTED' and 'internal_error' not in json.dumps(w.final)
        assert 'EVENTS.jsonl: 5 lines' in out, 'what was passed over is journalled, not silent'


NOT_TRACKER_EVENTS = [
    ('no_actor', lambda e: {k: v for k, v in e.items() if k != 'actor'}),
    ('no_evidence', lambda e: {k: v for k, v in e.items() if k != 'evidence'}),
    ('ts_not_a_time', lambda e: dict(e, ts='yesterday')),
]


@pytest.mark.parametrize('name,spoil', NOT_TRACKER_EVENTS, ids=[n for n, _ in NOT_TRACKER_EVENTS])
def test_a_done_line_the_trackers_reader_rejects_is_not_a_completion(name, spoil):
    # BR-09: events.py validate() is applied by every tracker reader (claims.py _read, EventLog.refresh): a line
    # without an actor, a done without evidence, or a ts that is no time is malformed to the tracker, so C-1 is NOT done
    with World('c1-' + name) as w:
        rows = w.events()
        assert [e['item'] for e in rows] == ['C-1'] and rows[0]['actor'] and rows[0]['evidence']
        (w.run_dir / 'EVENTS.jsonl').write_text(json.dumps(spoil(rows[0])) + '\n')
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['result'] == 'FAILED' and w.final['close_report'] is None, (out, err, w.final)
        assert 'EVENTS.jsonl: 1 line' in out, 'a line passed over is journalled'
        assert not claim_events(w, 'C-4') and not done_events(w, 'C-4')


def test_a_c4_done_line_the_tracker_rejects_does_not_end_the_finalization():
    with World('c4-forged') as w:
        (w.run_dir / 'FINAL_RECEIPT.json').write_text('{"result": "ACCEPTED"}\n')
        w.append_event({'kind': 'item', 'item': 'C-4', 'state': 'done', 'guarded': True,
                        'completion': {'type': 'artifact', 'artifact_digest': sha256(w.run_dir / 'FINAL_RECEIPT.json'),
                                       'path': str(w.run_dir / 'FINAL_RECEIPT.json')}})
        rc, out, err = w.finalize()
        assert rc == 0, (out, err)
        assert kyjob_items(w) == ['C-3', 'C-4'] and w.final['schema'] == 'ky.final_receipt/1'
        assert [e['completion']['artifact_digest'] for e in done_events(w, 'C-4') if e.get('actor')] == \
            [sha256(w.run_dir / 'FINAL_RECEIPT.json')]


def test_the_fixture_events_are_events_to_the_real_tracker():
    # BR-09: every line the fakes write must be one the real producer's validator (pravaha_tracker/events.py) keeps
    tracker = Path(__file__).resolve().parents[5] / 'platform' / 'scripts' / 'governance'
    sys.path.insert(0, str(tracker))
    try:
        from pravaha_tracker import events as tracker_events
    finally:
        sys.path.remove(str(tracker))
    with World('real-shapes') as w:
        assert w.finalize()[0] == 0
        rows = w.events()
        assert sorted({e['kind'] for e in rows}) == ['claim', 'item', 'verdict'] and len(rows) == 7
        for row in rows:
            tracker_events.validate(row)                       # raises EventError on a line the tracker would skip
        assert 'EVENTS.jsonl:' not in w.last[1]


def test_a_done_record_without_the_trackers_done_event_is_not_a_completion():
    # sweep: a DONE kyaction record is this script's own note; the backing record is the tracker's guarded done event.
    # Here the record of `ky done C-4` says DONE on this very digest and the tracker's log holds no such completion
    with World('record-only') as w:
        assert w.finalize()[0] == 0
        digest = sha256(w.run_dir / 'FINAL_RECEIPT.json')
        assert w.actions()['FIN-ky-done-C-4-' + digest[:12]]['state'] == 'DONE'
        rows = [e for e in w.events() if not (e['kind'] == 'item' and e['item'] == 'C-4')]
        (w.run_dir / 'EVENTS.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in rows))
        done_calls = len([c for c in w.calls('ky') if c['argv'][0] == 'done'])
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert w.final['result'] == 'FAILED' and w.final['failed_step'] == 'done_C-4', w.final
        assert 'record_done_but_not_observed' in w.final['reason'] and not done_events(w, 'C-4')
        assert len([c for c in w.calls('ky') if c['argv'][0] == 'done']) == done_calls, 'nothing is repeated on a guess'


def test_a_release_that_exits_0_but_records_nothing_is_not_a_release():
    with World('release-noop') as w:
        w.flag('ky_release_noop')
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'release_C-4', (out, err)
        assert claim_record(w)['state'] == 'acquired' and not done_events(w, 'C-4')


def test_a_failed_release_stops_before_completion():
    with World('norelease') as w:
        w.flag('ky_release_fail')
        rc, out, err = w.finalize()
        assert rc == 1 and not done_events(w, 'C-4') and w.final['failed_step'] == 'release_C-4'


def test_a_refused_c3_completion_stops_before_any_removal():
    with World('c3refused') as w:
        w.flag('ky_done_fail_C-3')
        rc, out, err = w.finalize()
        assert rc == 1 and (w.wt / 'k1').exists() and w.calls('local_db') == []
        assert w.final['failed_step'] == 'done_C-3'


def test_a_refused_c4_completion_exits_1():
    with World('c4refused') as w:
        w.flag('ky_done_fail_C-4')
        rc, out, err = w.finalize()
        assert rc == 1 and not done_events(w, 'C-4') and w.final['failed_step'] == 'done_C-4'


# ───────────────────────────────────────── external review (a lone verifier slot) ─────────────────────────────────

def test_a_lone_verifier_slot_needs_a_bound_external_review():
    with World('lone-slot', vslots=('v1',)) as w:
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['failed_step'] == 'close_review' and 'external' in w.final['reason']
        assert publishes(w, 'C-4') == [] and not done_events(w, 'C-4')


def test_a_lone_verifier_slot_with_an_external_review_passes_its_digest():
    with World('lone-slot-ext', vslots=('v1',)) as w:
        review = w.root / 'external_review.json'
        review.write_text(json.dumps({'item': 'C-4', 'by': 'someone-else', 'result': 'ACCEPTED'}))
        rc, out, err = w.finalize(KY_C4_EXTERNAL_REVIEW=str(review))
        assert rc == 0, (out, err)
        call = publishes(w, 'C-4')[0]
        assert opt(call, '--external-review-path') == str(review) and opt(call, '--external-review-sha256') == sha256(review)
        assert '--external-review-path' not in publishes(w, 'C-3')[0]['argv']


# ───────────────────────────────────────── crash and re-run ───────────────────────────────────────────────────────

@pytest.mark.parametrize('crash', ['crash_before_done_C-3', 'crash_after_done_C-3', 'crash_before_done_C-4', 'crash_after_done_C-4'])
def test_crash_after_the_verdict_then_rerun_completes_each_event_once(crash):
    with World(crash) as w:
        w.flag(crash)
        rc1, out1, err1 = w.finalize()
        assert rc1 == -signal.SIGKILL, (rc1, out1, err1)
        item = crash[-3:]
        assert len(verdicts(w, item)) == 1
        assert len(done_events(w, item)) == (1 if 'after' in crash else 0)
        rc2, out2, err2 = w.finalize()
        assert rc2 == 0, (out2, err2)
        assert len(done_events(w, 'C-3')) == 1 and len(done_events(w, 'C-4')) == 1
        assert len(verdicts(w, 'C-3')) == 1 and len(verdicts(w, 'C-4')) == 1
        assert kyjob_items(w) == ['C-3', 'C-4'], 'no reviewer is launched twice for one digest'
        done_calls = [c for c in w.calls('ky') if c['argv'][0] == 'done' and c['argv'][1] == item]
        assert len(done_calls) == (1 if 'after' in crash else 2)
        assert w.drain['result'] == w.final['result'] == 'ACCEPTED' and not (w.wt / 'k1').exists()
        assert done_events(w, 'C-3')[0]['completion']['artifact_digest'] == sha256(w.run_dir / 'DRAIN_RECEIPT.json')
        assert done_events(w, 'C-4')[0]['completion']['artifact_digest'] == sha256(w.run_dir / 'FINAL_RECEIPT.json')
        assert all(a['state'] == 'DONE' for a in w.actions().values())
        claims = claim_events(w, 'C-4')
        if crash == 'crash_before_done_C-4':
            assert [e['state'] for e in claims] == ['acquired', 'released', 'acquired', 'released']
            assert claims[0]['claim_id'] != claims[2]['claim_id']
        else:
            assert [e['state'] for e in claims] == ['acquired', 'released']
        assert claim_record(w) == claims[-1]


def test_rerun_after_success_changes_nothing_and_completes_nothing_twice():
    with World('twice') as w:
        assert w.finalize()[0] == 0
        final = (w.run_dir / 'FINAL_RECEIPT.json').read_bytes()
        drain = (w.run_dir / 'DRAIN_RECEIPT.json').read_bytes()
        before = len(w.calls())
        rc, out, err = w.finalize()
        # B2: C-4 is done, so FINAL is bound to its digest: no claim (the tracker refuses one on a done item), no review,
        # no publish, no completion, and the receipt keeps its bytes
        assert rc == 0, (out, err)
        assert (w.run_dir / 'FINAL_RECEIPT.json').read_bytes() == final and (w.run_dir / 'DRAIN_RECEIPT.json').read_bytes() == drain
        assert done_events(w, 'C-4')[0]['completion']['artifact_digest'] == sha256(w.run_dir / 'FINAL_RECEIPT.json')
        assert w.calls()[before:] == [], 'the re-run of a completed finalization called %s' % w.calls()[before:]
        assert len(done_events(w, 'C-3')) == 1 and len(done_events(w, 'C-4')) == 1
        assert len(claim_events(w, 'C-4')) == 2 and kyjob_items(w) == ['C-3', 'C-4']


def test_rerun_after_success_with_the_bound_final_receipt_changed_rewrites_nothing_and_fails():
    with World('twice-changed') as w:
        assert w.finalize()[0] == 0
        path = w.run_dir / 'FINAL_RECEIPT.json'
        path.write_text(path.read_text() + ' ')                  # changed after C-4 was completed on it
        changed = path.read_bytes()
        before = len(w.calls())
        rc, out, err = w.finalize()
        assert rc == 1, (out, err)
        assert path.read_bytes() == changed, 'the receipt C-4 is bound to was rewritten'
        assert w.calls()[before:] == [] and len(done_events(w, 'C-4')) == 1


# ───────────────────────────────────────── receipts are written by rename ─────────────────────────────────────────

def test_receipts_are_complete_json_documents_and_unchanged_rewrites_keep_their_bytes():
    with World('bytes') as w:
        assert w.finalize()[0] == 0
        for name in ('DRAIN_RECEIPT.json', 'FINAL_RECEIPT.json'):
            doc = json.loads((w.run_dir / name).read_text())
            assert isinstance(doc, dict)
        assert not list(w.run_dir.glob('*.tmp*')) and not list(w.run_dir.glob('.*.tmp*'))


def test_a_worktree_recreated_during_the_close_review_blocks_the_verdict():
    with World('recreate') as w:
        w.flag('reviewer_recreates_worktree_C-4')
        rc, out, err = w.finalize()
        assert rc == 1 and w.final['absence']['worktrees'] == 'survivor' and w.final['failed_step'] == 'close_review'
        assert publishes(w, 'C-4') == [] and not done_events(w, 'C-4')


def test_runner_stop_files_that_cannot_be_written_are_unknown_not_frozen():
    with World('nopravaha') as w:
        rc, out, err = w.finalize(KY_PRAVAHA_RUN=str(w.root / 'does-not-exist'))
        assert rc == 0, (out, err)
        assert w.drain['pravaha_writers'].startswith('unknown') and 'frozen' not in w.drain['pravaha_writers']
        assert not (w.root / 'does-not-exist').exists()


def test_crash_during_the_review_then_rerun_leaves_no_reviewer_and_completes_once():
    with World('midreview') as w:
        w.flag('reviewer_slow_C-3')
        proc = w.start_finalize()
        end = time.time() + 30
        while time.time() < end and not w.calls('kyjob'):
            time.sleep(0.05)
        assert w.calls('kyjob'), 'the reviewer never started'
        os.killpg(proc.pid, signal.SIGKILL)            # finalize.sh and its python die; the reviewer has its own group
        proc.communicate()
        rc, out, err = w.finalize(KY_DRAIN_WAIT_MIN='0.5')
        assert rc == 0, (out, err)
        assert len(done_events(w, 'C-3')) == 1 and len(done_events(w, 'C-4')) == 1
        assert len(verdicts(w, 'C-3')) == 1 and len(verdicts(w, 'C-4')) == 1
        assert w.final['absence'] == {'processes': 'absent', 'worktrees': 'absent', 'databases': 'absent'}
        first = w.calls('kyjob')[0]
        assert gone(first['own_pid'])
