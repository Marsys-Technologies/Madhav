"""Controller registration: real result/schema/lifecycle readers, external observations faked.

Dropping any head/PR/path/claim check must permit a bad fixture and fail its test.
"""
import copy
import json
import os
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(FLEET))
import kyd_jobs as J
import kyd_kinds_build as B

HEAD = '26806eeaa8478875ccd675bf9310ce58119af824'
BASE = '8' * 40
OTHER = 'f' * 40
ITEM = 'KV3-B-OPS-CONTRACT'
BRANCH = 'kalayantra/kv3-b-ops-contract'
PATH = 'fleet/operation_adapters.py'


class FinishCtx:
    def __init__(self, tmp):
        self.root = str(tmp / 'root')
        self.run = str(tmp / 'run')
        self.repo = str(tmp / 'repo')
        self.fleet = str(FLEET)
        self.scratch = str(tmp / 'scratch')
        self.controller_id = 'controller-fixture'
        self.priority = [ITEM]
        self.next = {'running': [], 'ready': [{'id': ITEM, 'owner': 'K', 'status': 'ready',
                                              'completion_kind': 'code'}], 'blocked': []}
        self.ledger = []
        self.calls = []
        self.remote = HEAD
        self.changed = PATH + '\0'
        self.pr_value = {'number': 3485, 'head': HEAD, 'state': 'OPEN', 'base': 'main',
                         'files': [PATH], 'checks': {'CI': {'status': 'SUCCESS', 'run_id': 1, 'attempt': 1}}}
        self.ky_exit = 0
        self.observe_event = True
        self.publication = 0
        self.route = 0
        for p in (self.run, self.repo, self.scratch):
            Path(p).mkdir()
        packets = Path(self.repo, B.PACKETS)
        packets.mkdir(parents=True)
        self.packet = packets / ('PACKET_' + ITEM + '_v1.md')
        self.packet.write_text('```json\n' + json.dumps({'id': ITEM, 'd1_paths': [PATH],
                                                       'build_tier': 'opus', 'max_loops': 3}) + '\n```\n')

    def events(self, item):
        return copy.deepcopy(self.ledger)

    def pr(self, item):
        return copy.deepcopy(self.pr_value)

    def accepted(self, item):
        return None

    def verify(self, item, step):
        return False

    def journal(self, event, text):
        self.calls.append(('journal', event, text))

    def sh(self, argv, env=None, cwd=None, timeout=120):
        self.calls.append(('sh', argv))
        if 'ls-remote' in argv:
            return 0, self.remote + '\trefs/heads/' + BRANCH + '\n', ''
        if 'diff' in argv and argv[0] == 'git':
            return 0, self.changed, ''
        if 'merge-base' in argv:
            return 0, BASE + '\n', ''
        if 'kyroute.py' in ' '.join(argv):
            return self.route, '{}', ''
        if 'kyboundary.sh' in ' '.join(argv):
            return 0, '', ''
        if 'kyverdicts.py' in ' '.join(argv):
            return self.publication, '', ''
        raise AssertionError(argv)

    def ky(self, *args, stream=None, lane=None):
        self.calls.append(('ky', list(args), stream, lane))
        assert args[0] in ('review', 'block', 'release')
        claim_path = Path(self.run, 'claims', lane + '.json')
        claim = json.loads(claim_path.read_text())
        assert claim['state'] in ('acquired', 'renewed'), 'registration must precede release'
        if args[0] == 'release':
            claim['state'] = 'released'
            claim_path.write_text(json.dumps(claim))
            self.ledger.append(claim)
            return 0, json.dumps(claim), ''
        assert list(args[:2]) == [args[0], ITEM]
        assert args[2] == '--detail'
        if self.observe_event:
            self.ledger.append({'kind': 'item', 'item': ITEM, 'actor': 'stream-' + stream + ':' + lane,
                                'state': 'review' if args[0] == 'review' else 'blocked', 'detail': args[3]})
        return self.ky_exit, '', ''

    def act(self, action_id, kind, inputs, target, effect, observer):
        self.calls.append(('act', action_id))
        return effect()


def write_job(ctx, job_id='J-20261013T103505Z-b1', kind='BUILD', outcome=None):
    job = dict.fromkeys(J.LAUNCH_KEYS + J.LIFECYCLE_KEYS)
    job.update(schema='ky.job/1', job_id=job_id, item=ITEM, kind=kind, stream='K', slot='b1',
               branch=BRANCH, base_sha=BASE, worktree=ctx.repo, packet_path=str(ctx.packet),
               phase='terminating' if outcome is None else 'ended', outcome=outcome,
               failure_fp='no_post_action' if outcome else None, model='opus', loop=1, max_loops=3,
               controller_id=ctx.controller_id, exit_code=0, claim_id='claim-live',
               key='BUILD.' + ITEM + '.fc6c3173b3cf', evidence_fp='a' * 64, locks=[],
               checkpoint={'collected': '2026-10-13T11:04:50Z', 'steps': {'exited': '2026-10-13T11:04:50Z'}},
               job_scratch=str(Path(ctx.scratch, job_id)))
    Path(job['job_scratch']).mkdir()
    directory = Path(ctx.run, 'jobs', job_id)
    directory.mkdir(parents=True)
    (directory / 'state.json').write_text(json.dumps(job))
    result = {'schema': 'ky.job_result/1', 'job_id': job_id, 'item': ITEM, 'status': 'done',
              'branch': BRANCH, 'head_sha': HEAD, 'pr_number': 3485, 'tests': [],
              'blocked_reason': None, 'notes': 'Request review registration for the new head.'}
    Path(job['job_scratch'], 'result.json').write_text(json.dumps(result))
    claim = {'kind': 'claim', 'item': ITEM, 'worker_id': 'b1', 'claim_id': job['claim_id'],
             'state': 'acquired', 'actor': 'stream-K:b1'}
    ctx.ledger.append(claim)
    Path(ctx.run, 'claims').mkdir(exist_ok=True)
    Path(ctx.run, 'claims', 'b1.json').write_text(json.dumps(claim))
    return job, result


def write_result(job, result):
    Path(job['job_scratch'], 'result.json').write_text(json.dumps(result))


def registrations(ctx):
    return [e for e in ctx.ledger if e.get('kind') == 'item' and e.get('state') == 'review']


@pytest.mark.parametrize('kind', ['BUILD', 'REWORK'])
def test_done_without_lane_event_is_registered_by_controller(tmp_path, kind):
    ctx = FinishCtx(tmp_path)
    job, _ = write_job(ctx, kind=kind)
    result = B.finish(ctx, job)
    assert result['outcome'] == 'done'
    assert registrations(ctx) == [{'kind': 'item', 'item': ITEM, 'actor': 'stream-K:b1',
                                   'state': 'review', 'detail': 'PR #3485 @ ' + HEAD}]
    assert ('ky', ['review', ITEM, '--detail', 'PR #3485 @ ' + HEAD], 'K', 'b1') in ctx.calls
    stored = J.load(ctx)[0]
    assert stored['head'] == HEAD and stored['pr'] == 3485
    assert stored['result_path'] == str(Path(job['job_scratch'], 'result.json'))
    # A controller restart sees the registration and never writes it twice.
    assert B.finish(ctx, J.load(ctx)[0])['outcome'] == 'done'
    assert len(registrations(ctx)) == 1


@pytest.mark.parametrize('bad, fingerprint', [
    ('wrong_origin', 'review_origin_head_mismatch'), ('missing_pr', 'review_pr_missing'),
    ('pr_head', 'review_pr_head_mismatch'), ('pr_number', 'review_pr_number_mismatch'),
    ('closed_pr', 'review_pr_not_open'), ('outside_scope', 'review_paths_outside_scope'),
    ('scope_unknown', 'review_scope_unknown'), ('wrong_branch', 'review_branch_mismatch'),
    ('notes_array', 'job_result_invalid'), ('wrong_job', 'job_result_invalid'),
    ('missing_head', 'review_identity_missing'), ('released_claim', 'claim_not_held'),
    ('missing_claim', 'claim_not_held'), ('symlink_result', 'job_result_invalid'),
    ('no_readback', 'review_event_not_observed'),
])
def test_unverifiable_done_never_registers(tmp_path, bad, fingerprint):
    ctx = FinishCtx(tmp_path)
    job, doc = write_job(ctx)
    if bad == 'wrong_origin': ctx.remote = OTHER
    if bad == 'missing_pr': ctx.pr_value = None
    if bad == 'pr_head': ctx.pr_value['head'] = OTHER
    if bad == 'pr_number': ctx.pr_value['number'] = 99
    if bad == 'closed_pr': ctx.pr_value['state'] = 'CLOSED'
    if bad == 'outside_scope': ctx.changed = 'platform/migrations/unauthorised.sql\0'
    if bad == 'scope_unknown': ctx.packet.write_text('```json\n{}\n```\n')
    if bad == 'wrong_branch': doc['branch'] = 'kalayantra/other'
    if bad == 'notes_array': doc['notes'] = ['legacy malformed notes']
    if bad == 'wrong_job': doc['job_id'] = 'J-other'
    if bad == 'missing_head': doc.update(head_sha=None, pr_number=None)
    if bad == 'released_claim':
        p = Path(ctx.run, 'claims', 'b1.json')
        d = json.loads(p.read_text()); d['state'] = 'released'; p.write_text(json.dumps(d))
    if bad == 'missing_claim': Path(ctx.run, 'claims', 'b1.json').unlink()
    if bad == 'no_readback': ctx.observe_event = False
    write_result(job, doc)
    if bad == 'symlink_result':
        p = Path(job['job_scratch'], 'result.json'); p.rename(p.with_name('other.json'))
        p.symlink_to(p.with_name('other.json'))
    result = B.finish(ctx, job)
    assert result['outcome'] == 'interrupted'
    assert result['failure_fp'] == fingerprint
    assert registrations(ctx) == []
    if bad != 'no_readback': assert not any(c[0] == 'ky' for c in ctx.calls)


def test_blocked_result_is_registered_by_controller(tmp_path):
    ctx = FinishCtx(tmp_path)
    job, doc = write_job(ctx)
    doc.update(status='blocked', blocked_reason='missing prerequisite')
    write_result(job, doc)
    assert B.finish(ctx, job)['outcome'] == 'blocked'
    assert ctx.ledger[-1]['state'] == 'blocked' and ctx.ledger[-1]['detail'] == 'missing prerequisite'
    assert not any(c[0] == 'sh' for c in ctx.calls)


def test_old_lane_written_registration_is_accepted_unchanged(tmp_path):
    ctx = FinishCtx(tmp_path)
    job, _ = write_job(ctx)
    Path(job['job_scratch'], 'result.json').unlink()
    ctx.ledger.append({'kind': 'item', 'item': ITEM, 'state': 'review', 'actor': 'stream-K:b1',
                       'detail': 'PR #3485 @ ' + HEAD})
    assert B.finish(ctx, job)['outcome'] == 'done'
    assert ctx.calls == []


@pytest.mark.parametrize('status', ['ready', 'running'])
def test_recovery_reclaims_registers_without_launch_and_clears_only_matching_failure(tmp_path, monkeypatch, status):
    ctx = FinishCtx(tmp_path)
    old, _ = write_job(ctx, outcome='interrupted')
    row = ctx.next['ready'][0]; row['status'] = status
    if status == 'running': ctx.next = {'running': [row], 'ready': [], 'blocked': []}
    Path(ctx.run, 'jobs', 'failures.json').write_text(json.dumps({ITEM: {
        'no_post_action': {'count': 2, 'evidence_fp': old['evidence_fp'], 'last_job': old['job_id']},
        'other_failure': {'count': 1, 'evidence_fp': 'b' * 64, 'last_job': 'J-other'}}}))
    monkeypatch.setattr(J, '_process', lambda job: 'gone')
    intent = next(i for i in B.intents(ctx) if i['kind'] == 'BUILD')
    assert intent['runner'] == 'script' and intent['claim'] == 'K'
    assert not J.attempts(ctx, intent)['blocked']
    new, _ = write_job(ctx, 'J-20261013T120000Z-b1')
    new.update(key=intent['key'], evidence_fp=intent['evidence_fp'], phase='prepared')
    J._save(ctx, new)
    assert B.start(ctx, new)['outcome'] == 'done'
    assert len(registrations(ctx)) == 1
    assert not any('kyjob.sh' in str(c) for c in ctx.calls)
    table = json.loads(Path(ctx.run, 'jobs', 'failures.json').read_text())
    assert 'no_post_action' not in table[ITEM] and table[ITEM]['other_failure']['count'] == 1
    ctx.next = {'running': [dict(row, status='review')], 'ready': [], 'blocked': []}
    assert [(i['kind'], i['head']) for i in B.intents(ctx)] == [('VERIFY', HEAD)]


@pytest.mark.parametrize('bad', ['invalid_result', 'head_changed', 'survivors', 'wrong_failure', 'blocked_result'])
def test_recovery_never_reuses_unverifiable_or_live_work(tmp_path, monkeypatch, bad):
    ctx = FinishCtx(tmp_path)
    old, doc = write_job(ctx, outcome='interrupted')
    if bad == 'invalid_result': doc['notes'] = []
    if bad == 'head_changed': ctx.pr_value['head'] = OTHER
    if bad == 'wrong_failure': old['failure_fp'] = 'quota'; J._save(ctx, old)
    if bad == 'blocked_result': doc.update(status='blocked', blocked_reason='hold')
    write_result(old, doc)
    monkeypatch.setattr(J, '_process', lambda job: 'survivors' if bad == 'survivors' else 'gone')
    assert B.intents(ctx) == []
    assert registrations(ctx) == []


def test_verify_registration_head_change_never_publishes(tmp_path):
    ctx = FinishCtx(tmp_path)
    job, _ = write_job(ctx)
    ctx.ledger.append({'kind': 'item', 'item': ITEM, 'state': 'review', 'actor': 'stream-K:b1',
                       'detail': 'PR #3485 @ ' + OTHER})
    job.update(kind='VERIFY', slot='v1', head=HEAD, verdict_phase='pre_merge',
               result_path=str(Path(job['job_scratch'], 'result.json')))
    result = B.finish(ctx, job)
    assert result['outcome'] == 'failed' and result['failure_fp'] == 'registration_changed'
    assert not any('publish' in c[1] for c in ctx.calls if c[0] == 'sh')


def test_a_lost_cli_reply_with_observed_registration_is_done(tmp_path):
    ctx = FinishCtx(tmp_path)
    job, _ = write_job(ctx)
    ctx.ky_exit = None
    assert B.finish(ctx, job)['outcome'] == 'done'
    assert len(registrations(ctx)) == 1


def test_controller_registration_survives_restart_before_failure_clear(tmp_path, monkeypatch):
    ctx = FinishCtx(tmp_path)
    old, doc = write_job(ctx, outcome='interrupted')
    new, _ = write_job(ctx, 'J-20261013T120000Z-b1')
    table = {ITEM: {'no_post_action': {'count': 2, 'evidence_fp': old['evidence_fp'], 'last_job': old['job_id']}}}
    Path(ctx.run, 'jobs', 'failures.json').write_text(json.dumps(table))
    real_clear = J.clear_review_failure
    monkeypatch.setattr(J, 'clear_review_failure', lambda ctx, job: None)
    assert B._register_result(ctx, new, doc, source=old)['outcome'] == 'done'
    monkeypatch.setattr(J, 'clear_review_failure', real_clear)
    fresh = next(j for j in J.load(ctx) if j['job_id'] == new['job_id'])
    assert B.finish(ctx, fresh)['outcome'] == 'done'
    assert len(registrations(ctx)) == 1
    assert J._step_result(ctx, fresh, {'outcome': 'done'}) is True
    assert 'no_post_action' not in json.loads(Path(ctx.run, 'jobs', 'failures.json').read_text())[ITEM]


@pytest.mark.parametrize('kind', ['VERIFY', 'ARTIFACT'])
def test_verifier_card_proposal_is_passed_to_controller_publisher(tmp_path, kind):
    ctx = FinishCtx(tmp_path)
    job, doc = write_job(ctx)
    artifact = Path(ctx.scratch, 'receipt.md')
    artifact.write_text('exact artifact bytes')
    import hashlib
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    event = {'kind': 'item', 'item': ITEM, 'state': 'review', 'actor': 'stream-K:b1',
             'detail': 'PR #3485 @ ' + HEAD}
    if kind == 'ARTIFACT':
        event.update(detail='sha256 ' + digest, evidence=str(artifact))
    ctx.ledger.append(event)
    job.update(kind=kind, slot='v1', head=HEAD if kind == 'VERIFY' else None, digest=digest,
               verdict_phase='pre_merge' if kind == 'VERIFY' else 'artifact',
               result_path=str(Path(job['job_scratch'], 'result.json')))
    doc.update(head_sha=None, pr_number=None,
               proposed_verdict={'verdict': 'ACCEPTED', 'head': HEAD if kind == 'VERIFY' else None, 'findings': []})
    write_result(job, doc)
    assert J.read_result(job) == doc
    assert B.finish(ctx, job)['outcome'] == 'done'
    command = next(c[1] for c in ctx.calls if c[0] == 'sh' and 'publish' in c[1])
    assert command[command.index('--result') + 1] == job['result_path']
    assert command[command.index('--author-id') + 1] == 'stream-K:b1'
    assert command[command.index('--reviewer-id') + 1] == 'stream-V:v1'
    assert not any(c[0] == 'ky' for c in ctx.calls), 'verifier never writes tracker state itself'


def test_recovery_requires_claim_event_before_any_tracker_write(tmp_path):
    ctx = FinishCtx(tmp_path)
    job, doc = write_job(ctx)
    ctx.ledger = []
    result = B._register_result(ctx, job, doc)
    assert result['outcome'] == 'interrupted' and result['failure_fp'] == 'no_claim_event'
    assert registrations(ctx) == []
    assert not any(c[0] == 'ky' for c in ctx.calls)
