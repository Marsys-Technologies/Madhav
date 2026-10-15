#!/usr/bin/env python3
"""Isolated behaviour checks for finalize.sh v3; no campaign worktree, tracker, launchd, docker or database is touched.

The world built here is a throwaway KY_ROOT: a real git source repository with a bare origin, real item worktrees, real
process groups started by the test, and FAKE collaborators (ky, kyctl.sh, kyjob.sh, kyboundary.sh, kyverdicts.py,
local_db.sh) that log every call to calls.jsonl and take their behaviour from flag files under behavior/. The five cases
below are the v1.2 finalizer's cases moved onto v3 inputs (job states and a live process group replace lane flocks);
test_finalize_v3.py imports World for the rest.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

FLEET = Path(__file__).resolve().parents[1]
SCRIPT = FLEET / 'finalize.sh'
REAL_GIT = shutil.which('git')
sys.path.insert(0, str(FLEET))
import kyaction  # noqa: E402  (the real module: identities in the fixtures are measured the way finalize.sh measures them)


def base_dir():
    """Scratch for the fixtures: $JOB_SCRATCH when it is an absolute directory, else the temporary directory."""
    scratch = os.environ.get('JOB_SCRATCH', '')
    if scratch.startswith('/') and os.path.isdir(scratch):
        base = Path(scratch) / 'finalize-tests'
        base.mkdir(exist_ok=True)
        return base
    return Path(tempfile.gettempdir())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args, cwd=None):
    subprocess.run([REAL_GIT, *args], cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


FAKE_TOOLS = r'''
import glob, hashlib, json, os, signal, subprocess, sys, time, uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kyaction  # noqa: E402  (copied next to this file by World._fakes)

RUN = Path(os.environ['KY_RUN'])
ROOT = RUN.parent
BEH = ROOT / 'behavior'


def flag(name):
    return (BEH / name).exists()


def take(name):
    path = BEH / name
    if path.exists():
        path.unlink()
        return True
    return False


def text(name, default=''):
    path = BEH / name
    return path.read_text().strip() if path.exists() else default


def log(tool, argv, **extra):
    with open(ROOT / 'calls.jsonl', 'a') as handle:
        handle.write(json.dumps(dict({'tool': tool, 'argv': list(argv)}, **extra)) + '\n')


def events():
    out = []
    try:
        lines = (RUN / 'EVENTS.jsonl').read_text().splitlines()
    except OSError:
        return out
    for line in lines:                 # as the tracker's reader (claims.py _read): a line events.py validate() refuses is skipped
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get('actor') and (row.get('state') != 'done' or row.get('kind') != 'item' or row.get('evidence')):
            out.append(row)
    return out


def latest_verdict(item, digest):
    """verdicts.py accepted_verdict: the LATEST artifact verdict at this identity decides."""
    return next((e for e in reversed(events()) if e.get('kind') == 'verdict' and e.get('item') == item
                 and e.get('phase') == 'artifact' and e.get('artifact_digest') == digest), None)


def append(event):
    with open(RUN / 'EVENTS.jsonl', 'a') as handle:
        handle.write(json.dumps(event) + '\n')


def opt(argv, name):
    return argv[argv.index(name) + 1] if name in argv else None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc(t=None):
    return time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime(time.time() if t is None else t))


def latest_claim(item):
    return next((e for e in reversed(events()) if e.get('kind') == 'claim' and e.get('item') == item), None)


def record_claim(event):
    """As the tracker does (claims.py _record): claims/<worker>.json is the latest claim event, KEPT after a release."""
    (RUN / 'claims').mkdir(exist_ok=True)
    (RUN / 'claims' / (event['worker_id'] + '.json')).write_text(json.dumps(event, indent=2) + '\n')


def ky(argv):
    log('ky', argv, stream=os.environ.get('KY_STREAM'), lane=os.environ.get('KY_LANE'))
    verb = argv[0] if argv else ''
    if verb == 'claim':
        item, worker, lease = argv[1], opt(argv, '--worker'), int(opt(argv, '--lease') or 5400)
        if flag('ky_claim_fail'):
            print('refused: fake claim refusal', file=sys.stderr)
            return 2
        if any(e.get('kind') == 'item' and e.get('item') == item and e.get('state') == 'done' for e in events()):
            print('refused: item is not claimable: done', file=sys.stderr)       # claims.py: a done item is never claimable
            return 2
        last = latest_claim(item)
        if last and last['state'] in ('acquired', 'renewed') and time.time() < kyaction.parse_utc(last['expires_at']):
            print('refused: item is claimed by %s until %s' % (last['worker_id'], last['expires_at']), file=sys.stderr)
            return 2
        claim = {'kind': 'claim', 'actor': 'stream-%s:%s' % (os.environ.get('KY_STREAM'), worker), 'item': item,
                 'state': text('ky_claim_records_state', 'acquired'), 'worker_id': worker,
                 'claim_id': hashlib.sha256(os.urandom(16)).hexdigest()[:32], 'lease_s': lease,
                 'expires_at': utc(time.time() + (-5 if flag('ky_claim_already_expired') else lease)), 'ts': utc(),
                 'branch': None, 'head': None, 'step': None}
        append(claim)
        record_claim(dict(claim, claim_id='0' * 32) if flag('ky_claim_record_differs') else claim)
        return 0
    if verb == 'release':
        worker = os.environ.get('KY_LANE', '')
        try:
            current = json.loads((RUN / 'claims' / (worker + '.json')).read_text())
        except (OSError, ValueError):
            print('refused: no claim record for this worker', file=sys.stderr)
            return 2
        last = latest_claim(current.get('item'))
        if flag('ky_release_fail') or not last or last.get('claim_id') != current.get('claim_id') \
                or last.get('worker_id') != worker or last['state'] not in ('acquired', 'renewed'):
            print('refused: claim is not active for this worker', file=sys.stderr)
            return 2
        if flag('ky_release_noop'):
            return 0                                   # exits 0, records nothing: the claim is still held
        released = dict(last, state='released', ts=utc())
        append(released)
        record_claim(released)
        return 0
    if verb == 'done':
        item, path = argv[1], opt(argv, '--artifact-path')
        declared = RUN / {'C-3': 'DRAIN_RECEIPT.json', 'C-4': 'FINAL_RECEIPT.json'}.get(item, 'none')
        if os.environ.get('KY_STREAM') != 'S' or not path or os.path.realpath(path) != os.path.realpath(declared):
            print('refused: artifact path is not the declared detector', file=sys.stderr)
            return 2
        if flag('ky_done_fail_' + item):
            print('refused: fake guarded refusal', file=sys.stderr)
            return 2
        if any(e.get('kind') == 'item' and e.get('item') == item and e.get('state') == 'done' for e in events()):
            print('refused: item is already done', file=sys.stderr)
            return 2
        digest = sha(path)
        verdict = latest_verdict(item, digest)
        if not verdict or verdict.get('result') != 'ACCEPTED':
            print('refused: independent artifact verdict is missing', file=sys.stderr)
            return 2
        if take('crash_before_done_' + item):
            os.killpg(os.getpgrp(), signal.SIGKILL)
        # the event completion.py guarded_done_event returns for typed artifact evidence (cli.py cmd_guarded_done)
        append({'kind': 'item', 'actor': 'stream-S', 'item': item, 'state': 'done', 'guarded': True,
                'evidence': 'artifact sha256 %s; verdict %s' % (digest, verdict['ts']),
                'completion': {'type': 'artifact', 'artifact_digest': digest, 'path': os.path.realpath(path)},
                'detail': 'guarded completion: dependencies, steps, detector and independent acceptance verified', 'ts': utc()})
        if take('crash_after_done_' + item):
            os.killpg(os.getpgrp(), signal.SIGKILL)
        return 0
    return 64


def kyctl(argv):
    log('kyctl', argv)
    return 1 if len(argv) > 1 and flag('kyctl_fail_' + argv[1]) else 0


def kyboundary(argv):
    verb, job = argv[0], argv[1]
    log('kyboundary', argv)
    released = ROOT / 'boundary_released' / job
    if verb == 'check':
        # KV3-B-KYBOUNDARY: one JSON object {job_id, mechanism, head_unchanged, status_clean, tracked_hashes_unchanged,
        # mechanism_intact, result}; exit 0 intact, 1 violated, 3 unknown (anything unobservable: a released view is)
        code = 3 if released.exists() else int(text('boundary_exit', '0'))
        if flag('boundary_not_object'):
            print(json.dumps(['intact']))
            return 0
        seen = code == 0
        print(json.dumps({'job_id': 'J-other' if flag('boundary_other_job') else job, 'mechanism': 'fake',
                          'head_unchanged': seen, 'status_clean': seen, 'tracked_hashes_unchanged': seen,
                          'mechanism_intact': seen, 'result': {0: 'intact', 1: 'violated'}.get(code, 'unknown')}))
        return code
    if verb == 'release':
        if flag('boundary_release_fail'):
            return 1
        released.parent.mkdir(exist_ok=True)
        released.write_text('1')
        return 0
    return 64


def local_db(argv):
    log('local_db', argv)
    session = argv[2]
    mode = text('db_mode', 'removed')
    handover = RUN / 'local_db' / 'container.json'      # KV3-B-LOCALDB: {owner, storage, from}, gone once its owner's close removes the container
    try:
        if json.loads(handover.read_text()).get('owner') == session and not flag('db_keep_handover'):
            handover.unlink()
    except (OSError, ValueError, AttributeError):
        pass
    dropped = 0
    if (BEH / 'db_present').exists():
        (BEH / 'db_present').unlink()
        dropped = 1
    if mode != 'stale_ready':
        for path in glob.glob(str(RUN / 'local_db' / '*.json')):
            try:
                if json.loads(Path(path).read_text()).get('session_id') == session:
                    os.unlink(path)
            except (OSError, ValueError):
                pass
    if mode == 'exit1':
        print('close session=%s reason=unmarked_database' % session)
        return 1
    if mode == 'wrong_mount':
        print('ky_v1 STALE: mount source outside the session root')
        return 1
    if mode == 'ownership_conflict':
        print('close session=%s reason=foreign_database' % session)
        return 1
    if mode == 'no_token':
        print('close session=%s dropped=%d' % (session, dropped))
        return 0
    if mode == 'other_session_line':
        print('close session=%s-other dropped=0 container=removed' % session)
        return 0
    if mode == 'tokens_on_two_lines':
        print('close session=%s dropped=%d\ncontainer=removed' % (session, dropped))
        return 0
    container = {'stale_ready': 'removed', 'stop_without_removal': 'stopped'}.get(mode, mode)
    print('close session=%s dropped=%d container=%s' % (session, dropped, container))
    return 0


def kyverdicts(argv):
    verb = argv[0]
    log('kyverdicts', argv)
    if verb == 'snapshot':
        if flag('snapshot_fail'):
            return 1
        Path(opt(argv, '--out')).write_text(json.dumps({'head': None, 'status_porcelain': '', 'tracked_sha256': 'f' * 64}))
        return 0
    if verb != 'publish':
        return 64
    job, item, digest = opt(argv, '--job-id'), opt(argv, '--item'), opt(argv, '--artifact-digest')
    reasons = []
    if opt(argv, '--job-exit') != '0':
        reasons.append('job_exit')
    try:
        result = json.loads(Path(opt(argv, '--result')).read_text())
        if (result.get('schema') != 'ky.job_result/1' or result.get('status') != 'done'
                or (result.get('proposed_verdict') or {}).get('verdict') not in ('ACCEPTED', 'REJECTED')):
            reasons.append('result_invalid')
        proposed = (result.get('proposed_verdict') or {}).get('verdict')
    except (OSError, ValueError, TypeError):
        reasons.append('result_unreadable')
        proposed = None
    if opt(argv, '--author-id') == opt(argv, '--reviewer-id'):
        reasons.append('not_independent')
    if not Path(opt(argv, '--snapshot') or '/nonexistent').exists():
        reasons.append('snapshot_missing')
    if sha(opt(argv, '--artifact-path')) != digest:
        reasons.append('artifact_changed')
    try:
        if json.loads(Path(opt(argv, '--boundary')).read_text()).get('result') != 'intact':
            reasons.append('boundary')
    except (OSError, ValueError):
        reasons.append('boundary_unreadable')
    if '--external-review-path' in argv and sha(opt(argv, '--external-review-path')) != opt(argv, '--external-review-sha256'):
        reasons.append('external_review_sha')
    if flag('publish_refuse'):
        reasons.append('fake_refusal')
    if reasons:
        print(json.dumps({'published': False, 'result': None, 'reasons': reasons, 'action_id': 'VERDICT-' + job}))
        return 1
    if flag('publish_answers_without_event'):
        print(json.dumps({'published': True, 'result': proposed, 'reasons': [], 'action_id': 'VERDICT-' + job}))
        return 0
    if flag('publish_answer_not_object'):
        print(json.dumps([True]))
        return 0
    if not any(e.get('kind') == 'verdict' and str(e.get('detail', '')).startswith('job %s;' % job) for e in events()):
        # `ky verdict` (cli.py write): a key without a value is not written, so an artifact verdict has no `head`
        event = {'kind': 'verdict', 'actor': 'stream-V:' + opt(argv, '--vslot'), 'item': item, 'phase': 'artifact',
                 'artifact_digest': digest, 'result': proposed, 'ts': utc(),
                 'detail': 'job %s; fake' % ('J-other' if flag('publish_as_other_job') else job)}
        if '--external-review-path' in argv:
            event['external_review'] = {'path': opt(argv, '--external-review-path'), 'sha256': opt(argv, '--external-review-sha256')}
        append(event)
    print(json.dumps({'published': True, 'result': proposed, 'reasons': [], 'action_id': 'VERDICT-' + job}))
    return 0


def kyjob(argv):
    job = argv[0]
    state_path = RUN / 'jobs' / job / 'state.json'
    state = json.loads(state_path.read_text())
    scratch = Path(state['job_scratch'])
    item = state['item']
    log('kyjob', argv, item=item, stream=state['stream'], slot=state['slot'], cwd=os.getcwd(),
        max_turns=state['max_turns'], deadline=state['deadline'], kind=state['kind'],
        prompt_has_header='--- job header ---' in Path(state['prompt_path']).read_text(),
        database_url_set='DATABASE_URL' in os.environ, own_pgid=os.getpgrp(), own_pid=os.getpid())
    receipt = RUN / ('DRAIN_RECEIPT.json' if item == 'C-3' else 'FINAL_RECEIPT.json')
    reviewed = sha(receipt)
    # kyjob.sh writes no state (KV3-B-KYJOB): what a real run leaves of its identity is the init event of the program's
    # stream-json output, redirected to stdout_path. The session is a fresh one unless a flag names it.
    session = text('reviewer_session_' + item) or str(uuid.uuid4())
    init = {'type': 'system', 'subtype': 'init', 'cwd': os.getcwd(), 'session_id': session, 'tools': [], 'model': state['model']}
    stream = [init, {'type': 'assistant', 'session_id': session, 'message': {'content': []}}]
    if flag('reviewer_no_stream_' + item) or flag('reviewer_session_in_state_only_' + item):
        stream = None
    elif flag('reviewer_stream_without_init_' + item):
        stream = [{'type': 'result', 'subtype': 'success', 'session_id': session}]
    elif flag('reviewer_two_sessions_' + item):
        stream.append(dict(init, session_id=str(uuid.uuid4())))
    elif flag('reviewer_init_without_session_' + item):
        stream = [{'type': 'system', 'subtype': 'init', 'cwd': os.getcwd()}]
    if stream is not None:
        Path(state['stdout_path']).write_text(''.join(json.dumps(row) + '\n' for row in stream))
    if flag('reviewer_hang_' + item):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        time.sleep(600)
    if flag('reviewer_exit1_' + item):
        return 1
    if flag('reviewer_leaves_child_' + item):
        child = subprocess.Popen(['sleep', '600'])
        (ROOT / 'child.pid').write_text(str(child.pid))
    if flag('reviewer_straggler_' + item):
        proc = subprocess.Popen(['sleep', '600'], start_new_session=True)
        start = subprocess.run(['ps', '-o', 'lstart=', '-p', str(proc.pid)], capture_output=True, text=True).stdout.strip()
        other = RUN / 'jobs' / 'J-straggler'
        other.mkdir(parents=True, exist_ok=True)
        (other / 'state.json').write_text(json.dumps({
            'job_id': 'J-straggler', 'item': 'K-1', 'slot': 'b1', 'worktree': None, 'phase': 'live', 'pid': proc.pid,
            'pgid': proc.pid, 'process_start': start, 'deadline': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() + 3000))}))
        (ROOT / 'straggler.pid').write_text(str(proc.pid))
    if flag('reviewer_ended_straggler_' + item):         # a record that says `ended` over a group that is alive
        proc = subprocess.Popen(['sleep', '600'], start_new_session=True)
        start = subprocess.run(['ps', '-o', 'lstart=', '-p', str(proc.pid)], capture_output=True, text=True).stdout.strip()
        other = RUN / 'jobs' / 'J-late'
        other.mkdir(parents=True, exist_ok=True)
        (other / 'state.json').write_text(json.dumps({
            'job_id': 'J-late', 'item': 'K-1', 'slot': 'b1', 'worktree': str(ROOT / 'wt' / 'k1'), 'phase': 'ended',
            'pid': proc.pid, 'pgid': proc.pid, 'process_start': start,
            'deadline': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() + 3000))}))
        (ROOT / 'straggler.pid').write_text(str(proc.pid))
    if flag('reviewer_adds_db_' + item):
        (BEH / 'db_present').write_text('1')
    if flag('reviewer_recreates_worktree_' + item):
        (ROOT / 'wt' / 'k1').mkdir(exist_ok=True)
    if flag('reviewer_wrong_slot_' + item):
        state['slot'] = 'x9'
        state_path.write_text(json.dumps(state))
    if flag('reviewer_slow_' + item):
        time.sleep(2)
    if flag('reviewer_dirties_' + item):
        (ROOT / 'wt' / 'k1' / 'late-work.txt').write_text('written while the review ran\n')
    if flag('reviewer_mutate_receipt_' + item):
        receipt.write_text(receipt.read_text() + ' ')
    if flag('reviewer_tamper_stream_' + item):
        state['stream'] = 'S'
        state_path.write_text(json.dumps(state))
    if flag('reviewer_session_in_state_only_' + item):   # a model that edits its own job state: no stream evidence behind it
        state['provider_session_id'] = str(uuid.uuid4())
        state_path.write_text(json.dumps(state))
    if flag('reviewer_is_author_process_' + item):       # a model that edits its job state to name the finalizer's process
        parent = os.getppid()
        start = subprocess.run(['ps', '-o', 'lstart=', '-p', str(parent)], capture_output=True, text=True).stdout.strip()
        state.update(pid=parent, pgid=os.getpgid(parent), process_start=start)
        state_path.write_text(json.dumps(state))
    verdict = 'REJECTED' if flag('reviewer_reject_' + item) else 'ACCEPTED'
    result = {'schema': 'ky.job_result/1', 'job_id': 'J-other' if flag('reviewer_wrong_job_' + item) else job,
              'item': item, 'status': 'done', 'branch': None, 'head_sha': None, 'pr_number': None, 'tests': [],
              'blocked_reason': None, 'notes': 'fake', 'proposed_verdict': {'verdict': verdict, 'artifact_digest': reviewed, 'blocking': []}}
    if flag('reviewer_other_digest_' + item):
        result['proposed_verdict']['artifact_digest'] = 'e' * 64
    if flag('reviewer_no_digest_' + item):
        del result['proposed_verdict']['artifact_digest']
    if not flag('reviewer_no_result_' + item):
        (scratch / 'result.json').write_text(json.dumps(result))
    return 0


if __name__ == '__main__':
    tool = sys.argv[1]
    sys.exit({'ky': ky, 'kyctl': kyctl, 'kyboundary': kyboundary, 'local_db': local_db,
              'kyverdicts': kyverdicts, 'kyjob': kyjob}[tool](sys.argv[2:]))
'''


class World:
    """A throwaway KY_ROOT. Use as a context manager; teardown stops only the process groups this world started."""

    def __init__(self, kind='world', vslots=('v1', 'v2'), lanes=('k1',), final_wait_min='0.1', grace='0.5'):
        self._tmp = tempfile.TemporaryDirectory(prefix='B-FIN-%s-' % kind, dir=base_dir())
        self.root = Path(self._tmp.name).resolve()
        self.vslots = ' '.join(vslots)
        self.knobs = {'KY_DRAIN_WAIT_MIN': '0.05', 'KY_FINAL_WAIT_MIN': final_wait_min, 'KY_FINAL_POLL_S': '0.05',
                      'KY_TERM_GRACE_S': grace}
        self.run_dir, self.fleet, self.bin = self.root / 'run', self.root / 'fleet', self.root / 'bin'
        self.wt, self.beh, self.scratch = self.root / 'wt', self.root / 'behavior', self.root / 'scratch'
        self.pravaha, self.shim = self.root / 'pravaha_run', self.root / 'shim'
        self.src, self.origin = self.root / 'source', self.root / 'origin.git'
        for part in (self.run_dir / 'jobs', self.run_dir / 'actions', self.run_dir / 'local_db', self.fleet, self.bin,
                     self.wt, self.beh, self.scratch / 'jobs', self.pravaha, self.shim):
            part.mkdir(parents=True, exist_ok=True)
        self.procs = []
        self._git_source()
        self._fakes()
        self.lanes = {}
        for lane in lanes:
            self.add_worktree(lane)
            self.add_job('J-%s' % lane, worktree=self.wt / lane)
        report = self.root / 'close_report.md'
        report.write_text('close report fixture\n')
        self.report = report
        self.append_event({'kind': 'item', 'actor': 'stream-S', 'item': 'C-1', 'state': 'done', 'guarded': True,
                           'evidence': 'artifact sha256 %s; verdict fixture' % sha256(report),
                           'completion': {'type': 'artifact', 'artifact_digest': sha256(report), 'path': str(report)},
                           'detail': 'guarded completion: dependencies, steps, detector and independent acceptance verified',
                           'ts': '2026-10-12T00:00:00+00:00'})
        (self.run_dir / 'FINAL_MESSAGE_DRAFT.md').write_text('fixture final message\n')

    # ── construction ──────────────────────────────────────────────────────────────────────────────────────────────
    def _git_source(self):
        git('init', '-q', '-b', 'main', str(self.src))
        git('config', 'user.name', 'Test', cwd=self.src)
        git('config', 'user.email', 'test@example.invalid', cwd=self.src)
        (self.src / 'tracked.txt').write_text('fixture\n')
        git('add', 'tracked.txt', cwd=self.src)
        git('commit', '-qm', 'fixture', cwd=self.src)
        git('init', '-q', '--bare', str(self.origin))
        git('remote', 'add', 'origin', str(self.origin), cwd=self.src)
        git('push', '-q', 'origin', 'main', cwd=self.src)

    def _fakes(self):
        shutil.copy(FLEET / 'kyaction.py', self.fleet / 'kyaction.py')
        (self.fleet / 'fake_tools.py').write_text(FAKE_TOOLS)
        for name, tool in (('kyctl.sh', 'kyctl'), ('kyjob.sh', 'kyjob'), ('kyboundary.sh', 'kyboundary'),
                           ('local_db.sh', 'local_db')):
            (self.fleet / name).write_text('#!/usr/bin/env bash\nexec python3 "$(dirname "$0")/fake_tools.py" %s "$@"\n' % tool)
        (self.fleet / 'kyverdicts.py').write_text(
            'import sys\nsys.path.insert(0, __import__("os").path.dirname(__file__))\nimport fake_tools\n'
            'sys.exit(fake_tools.kyverdicts(sys.argv[1:]))\n')
        (self.fleet / 'mcp.none.json').write_text('{"mcpServers":{}}\n')
        ky = self.bin / 'ky'
        ky.write_text('#!/usr/bin/env bash\nexec python3 "%s" ky "$@"\n' % (self.fleet / 'fake_tools.py'))
        ky.chmod(0o755)

    # ── fixtures ──────────────────────────────────────────────────────────────────────────────────────────────────
    def add_worktree(self, name):
        git('-C', str(self.src), 'worktree', 'add', '-q', '--detach', str(self.wt / name))
        self.lanes[name] = self.wt / name
        return self.wt / name

    def make_dirty(self, name):
        (self.wt / name / 'local-change.txt').write_text('must stay\n')

    def make_unpushed(self, name):
        path = self.wt / name
        git('config', 'user.name', 'Test', cwd=path)
        git('config', 'user.email', 'test@example.invalid', cwd=path)
        (path / 'unpushed.txt').write_text('work\n')
        git('add', 'unpushed.txt', cwd=path)
        git('commit', '-qm', 'unpushed work', cwd=path)

    def start_group(self, ignore_term=False, seconds=600):
        """A real process group (its own session) started by this test: {pid, pgid, process_start}."""
        code = 'import signal, time\n%stime.sleep(%d)\n' % ('signal.signal(signal.SIGTERM, signal.SIG_IGN)\n' if ignore_term else '', seconds)
        proc = subprocess.Popen([sys.executable, '-c', code], start_new_session=True, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        threading.Thread(target=proc.wait, daemon=True).start()     # reap at once: a killed leader is gone, not a zombie
        for _ in range(100):
            ident = kyaction.ps_identity(proc.pid)
            if ident:
                break
            time.sleep(0.05)
        self.procs.append((proc.pid, ident[1]))
        return {'pid': proc.pid, 'pgid': proc.pid, 'process_start': ident[1], 'proc': proc}

    def add_job(self, job_id, worktree=None, phase='ended', proc=None, deadline_in=-60, **override):
        state = {'schema': 'ky.job/1', 'job_id': job_id, 'key': job_id, 'item': 'K-1', 'kind': 'BUILD', 'role': 'builder',
                 'stream': 'K', 'slot': 'b1', 'worktree': str(worktree) if worktree else None, 'phase': phase,
                 'pid': proc['pid'] if proc else None, 'pgid': proc['pgid'] if proc else None,
                 'process_start': proc['process_start'] if proc else None,
                 'deadline': kyaction.utc(time.time() + deadline_in), 'exit_code': None, 'outcome': None}
        state.update(override)
        path = self.run_dir / 'jobs' / job_id
        path.mkdir(parents=True, exist_ok=True)
        (path / 'state.json').write_text(json.dumps(state))
        return path / 'state.json'

    def add_db_receipt(self, slot='v1', session='sess-1'):
        (self.run_dir / 'local_db' / (slot + '.json')).write_text(json.dumps(
            {'schema': 'ky.slot_db/1', 'slot': slot, 'result': 'READY', 'session_id': session}))

    def add_handover(self, owner, came_from):
        """The record KV3-B-LOCALDB's `close` leaves when the container passes to a remaining session."""
        (self.run_dir / 'local_db' / 'container.json').write_text(json.dumps(
            {'owner': owner, 'storage': str(self.scratch / 'db' / came_from), 'from': came_from}))

    def patch_kyaction(self, source):
        """Append to the world's copy of kyaction.py (a fault the real module answers only when ps cannot be asked)."""
        with open(self.fleet / 'kyaction.py', 'a') as handle:
            handle.write('\n\n' + source)

    def flag(self, name, content='1'):
        (self.beh / name).write_text(content)

    def append_event(self, event):
        with open(self.run_dir / 'EVENTS.jsonl', 'a') as handle:
            handle.write(json.dumps(event) + '\n')

    # ── running ───────────────────────────────────────────────────────────────────────────────────────────────────
    def env(self, **extra):
        env = {k: os.environ[k] for k in ('PATH', 'HOME', 'USER', 'LANG', 'TMPDIR') if k in os.environ}
        env.update(KY_ROOT=str(self.root), KY_RUN=str(self.run_dir), KY_FLEET=str(self.fleet),
                   KY_SCRATCH=str(self.scratch), KY_SOURCE_REPO=str(self.src), KY_PRAVAHA_RUN=str(self.pravaha),
                   KY_VERIFIER_SLOTS=self.vslots, KY_GIT=REAL_GIT, CLAUDE_BIN='/nonexistent/claude')
        env.update(self.knobs)
        env.update(extra)
        return env

    def finalize(self, script=None, args=(), timeout=120, **extra_env):
        """Run finalize.sh as the executor does: bash <script>, cwd = KY_ROOT, own session. → (rc, stdout, stderr)."""
        proc = subprocess.Popen(['bash', str(script or SCRIPT), *args], cwd=self.root, env=self.env(**extra_env),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)       # a group this test started
            out, err = proc.communicate()
            raise AssertionError('finalize.sh timed out\n%s\n%s' % (out[-2000:], err[-2000:]))
        self.last = (proc.returncode, out, err)
        return self.last

    def start_finalize(self, **extra_env):
        """finalize.sh left running (own session): the caller kills its group to simulate a crash."""
        return subprocess.Popen(['bash', str(SCRIPT)], cwd=self.root, env=self.env(**extra_env), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, start_new_session=True)

    # ── reading ───────────────────────────────────────────────────────────────────────────────────────────────────
    def json(self, name):
        path = self.run_dir / name
        return json.loads(path.read_text()) if path.exists() else None

    @property
    def drain(self):
        return self.json('DRAIN_RECEIPT.json')

    @property
    def final(self):
        return self.json('FINAL_RECEIPT.json')

    def calls(self, tool=None):
        path = self.root / 'calls.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        return [r for r in rows if tool is None or r['tool'] == tool]

    def events(self, kind=None, item=None, state=None):
        path = self.run_dir / 'EVENTS.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        return [e for e in rows if (kind is None or e.get('kind') == kind) and (item is None or e.get('item') == item)
                and (state is None or e.get('state') == state)]

    def alive(self, proc):
        return kyaction.process_matches(proc['pid'], proc['process_start']) is True

    def actions(self):
        return {p.stem: json.loads(p.read_text()) for p in sorted((self.run_dir / 'actions').glob('*.json'))}

    # ── teardown ──────────────────────────────────────────────────────────────────────────────────────────────────
    def _reap_known(self):
        pids = [(p, s) for p, s in self.procs]
        for name in ('straggler.pid', 'child.pid'):
            path = self.root / name
            if path.exists():
                try:
                    pids.append((int(path.read_text()), None))
                except ValueError:
                    pass
        for pid, start in pids:
            if start is None or kyaction.process_matches(pid, start) is True:      # only what this test started
                for sig in (signal.SIGKILL,):
                    try:
                        os.killpg(pid, sig) if start is not None else os.kill(pid, sig)
                    except (ProcessLookupError, PermissionError):
                        pass

    def close(self):
        self._reap_known()
        git('-C', str(self.src), 'worktree', 'prune')
        self._tmp.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def scenario(kind):
    with World(kind, lanes=()) as w:
        w.add_worktree('k1')
        drain_ok = None
        live = None
        if kind == 'busy':
            # a live group whose recorded start identity does not match: never signalled, never "gone" -> busy_kept
            live = w.start_group()
            w.add_job('J-k1', worktree=w.wt / 'k1', phase='live', proc=dict(live, process_start='Mon Jan  1 00:00:00 2001'))
        else:
            w.add_job('J-k1', worktree=w.wt / 'k1')
        if kind == 'dirty':
            w.make_dirty('k1')
        if kind == 'remove_failure':
            shim = w.shim / 'git'
            shim.write_text('#!/bin/sh\ncase " $* " in\n  *" worktree remove "*) exit 91 ;;\nesac\nexec %s "$@"\n' % REAL_GIT)
            shim.chmod(0o755)
        if kind == 'v1_busy':
            w.flag('reviewer_straggler_C-4')
        extra = {'KY_GIT': str(w.shim / 'git')} if kind == 'remove_failure' else {}
        rc, out, err = w.finalize(**extra)
        drain, final = w.drain, w.final
        assert drain is not None, (out, err)
        if kind in ('busy', 'dirty', 'remove_failure'):
            expected = {'busy': 'busy_kept', 'dirty': 'dirty_kept', 'remove_failure': 'remove_failed'}[kind]
            if kind == 'remove_failure':
                assert rc != 0 and drain['result'] == 'ACCEPTED' and final['result'] == 'FAILED', (rc, out, err)
                assert final['lanes']['k1'] == expected and (w.wt / 'k1').exists()
            else:
                assert rc != 0 and drain['result'] == 'FAILED' and final is None, (rc, out, err)
                assert drain['lanes']['k1'] == expected and (w.wt / 'k1').exists()
            if kind == 'busy':
                assert w.alive(live), 'a process of unproven identity was signalled'
        elif kind == 'v1_busy':
            assert rc != 0 and drain['result'] == 'ACCEPTED', (rc, out, err)
            assert final['result'] == 'FAILED' and final['absence']['processes'] == 'survivor', final
            assert not [e for e in w.events(kind='verdict', item='C-4')] and not w.events(kind='item', item='C-4', state='done')
        else:
            assert rc == 0 and drain['result'] == 'ACCEPTED', (rc, out, err)
            assert final['result'] == 'ACCEPTED' and final['lanes']['k1'] == 'removed', final
            assert not (w.wt / 'k1').exists() and (w.src / '.git').exists()
        assert (w.pravaha / 'RUNNER_STOP_A').exists()
        return {'case': kind, 'rc': rc, 'drain': drain['result'], 'final': final['result'] if final else None,
                'lane_state': (final or drain)['lanes'].get('k1')}


if __name__ == '__main__':
    from concurrent.futures import ThreadPoolExecutor
    kinds = ('busy', 'dirty', 'remove_failure', 'v1_busy', 'accepted')
    with ThreadPoolExecutor(max_workers=len(kinds)) as pool:          # five isolated worlds: nothing is shared between them
        cases = list(pool.map(scenario, kinds))
    print(json.dumps(cases, indent=2))
