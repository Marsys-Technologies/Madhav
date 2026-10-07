#!/usr/bin/env python3
"""Isolated behavior checks for the bootstrap finalizer; no campaign worktree is touched."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

SCRIPT = Path(__file__).resolve().parents[1] / 'finalize.sh'
BASE = Path(tempfile.gettempdir())
REAL_GIT = shutil.which('git')


def call(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def scenario(kind):
    with tempfile.TemporaryDirectory(prefix=f'B-3b-finalizer-{kind}-', dir=BASE) as temp:
        root = Path(temp)
        for part in ('run/reviews', 'wt', 'bin', 'pravaha_run', 'shim'):
            (root / part).mkdir(parents=True, exist_ok=True)
        repo = root / 'wt/campaign'
        call(REAL_GIT, 'init', '-q', str(repo))
        call(REAL_GIT, 'config', 'user.name', 'Test', cwd=repo)
        call(REAL_GIT, 'config', 'user.email', 'test@example.invalid', cwd=repo)
        (repo / 'tracked.txt').write_text('fixture\n')
        call(REAL_GIT, 'add', 'tracked.txt', cwd=repo)
        call(REAL_GIT, 'commit', '-qm', 'fixture', cwd=repo)
        lane = 'v1' if kind in ('accepted', 'v1_busy') else 'k1'
        call(REAL_GIT, '-C', str(repo), 'worktree', 'add', '--detach', '-q', str(root / 'wt' / lane))
        if kind == 'dirty':
            (root / 'wt/k1/local-change.txt').write_text('must stay\n')
        if kind == 'remove_failure':
            shim = root / 'shim/git'
            shim.write_text(f'''#!/bin/sh
case " $* " in
  *" worktree remove "*) exit 91 ;;
esac
exec {REAL_GIT} "$@"
''')
            shim.chmod(0o755)
        ky = root / 'bin/ky'
        ky.write_text('''#!/usr/bin/env python3
import hashlib, json, os, pathlib, sys
root = pathlib.Path(os.environ['KY_ROOT'])
if len(sys.argv) > 2 and sys.argv[2] == 'C-3':
    digest = hashlib.sha256((root / 'run/DRAIN_RECEIPT.json').read_bytes()).hexdigest()
    (root / 'run/reviews/FINAL_REVIEW.json').write_text(json.dumps({'result': 'ACCEPTED', 'by': 'v1', 'drain_sha256': digest}))
    (root / 'run/FINAL_MESSAGE_DRAFT.md').write_text('fixture final message\\n')
''')
        ky.chmod(0o755)
        lock = None
        if kind in ('busy', 'v1_busy'):
            lock = (root / 'run' / f'{lane}.lock').open('a+')
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        env = dict(os.environ, KY_ROOT=str(root), KY_PRAVAHA_RUN=str(root / 'pravaha_run'),
                   KY_DRAIN_WAIT_MIN='1', KY_FINAL_WAIT_MIN='1', KY_FINAL_POLL_S='0')
        if kind == 'remove_failure':
            env['PATH'] = str(root / 'shim') + os.pathsep + env['PATH']
        result = subprocess.run(['bash', str(SCRIPT)], env=env, capture_output=True, text=True, timeout=20)
        drain = json.loads((root / 'run/DRAIN_RECEIPT.json').read_text())
        final_path = root / 'run/FINAL_RECEIPT.json'
        final = json.loads(final_path.read_text()) if final_path.exists() else None
        if kind in ('busy', 'dirty', 'remove_failure'):
            expected = {'busy': 'busy_kept', 'dirty': 'dirty_kept', 'remove_failure': 'remove_failed'}[kind]
            assert result.returncode != 0 and drain['result'] == 'FAILED' and final is None
            assert drain['lanes']['k1'] == expected and (root / 'wt/k1').exists()
        elif kind == 'v1_busy':
            assert result.returncode != 0 and drain['result'] == 'ACCEPTED'
            assert final['result'] == 'FAILED' and final['lanes']['v1'] == 'busy_kept'
            assert (root / 'wt/v1').exists()
        else:
            assert result.returncode == 0 and drain['result'] == 'ACCEPTED'
            assert final['result'] == 'ACCEPTED' and final['lanes']['v1'] == 'removed'
            assert not (root / 'wt/v1').exists() and (repo / '.git').exists()
        assert (root / 'pravaha_run/RUNNER_STOP_A').exists()
        if lock:
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock.close()
        return {'case': kind, 'rc': result.returncode, 'drain': drain['result'],
                'final': final['result'] if final else None, 'lane_state': drain['lanes'].get(lane) if not final else final['lanes'].get(lane)}


if __name__ == '__main__':
    cases = [scenario(kind) for kind in ('busy', 'dirty', 'remove_failure', 'v1_busy', 'accepted')]
    print(json.dumps(cases, indent=2))
