#!/usr/bin/env python3
"""One foreground tick of the generalized protected-window watcher (SR-A6-GCW).

Read-only origin/main snapshot + SQL truth + green CI + a sole live lease.
A supervisor may invoke ticks repeatedly; this program starts no daemon.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import re
from pathlib import Path
import subprocess
import sys

from protected_windows import COORD, GitSource, SAFE_ID, catalog, number, schedule_rows

SQL = ('SELECT COALESCE(json_agg(filename ORDER BY filename), \'[]\'::json) '
       'FROM public._migrations_applied;')
CI = 'CI — Ganga Quality Gate'


def command(executable, *args):
    result = subprocess.run([executable, *args], text=True, capture_output=True, timeout=60)
    if result.returncode:
        # Never echo subprocess stderr: a SQL client might include connection secrets.
        raise ValueError(f'{Path(executable).name} failed with exit {result.returncode}')
    if not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise ValueError(f'{Path(executable).name} returned non-JSON evidence') from exc


def read_applied(readback):
    rows = command(readback, '--no-psqlrc', '--tuples-only', '--no-align', '--set', 'ON_ERROR_STOP=1', '--command', SQL)
    if not isinstance(rows, list) or any(not isinstance(row, str) or not row.endswith('.sql') for row in rows):
        raise ValueError('invalid _migrations_applied readback')
    return set(rows)


def require_lease(source, lease):
    if not SAFE_ID.fullmatch(lease):
        raise ValueError('invalid lease id')
    text = source.text(COORD, 'origin/campaign-coordination')
    section = text.split('## 1.', 1)
    if len(section) != 2:
        raise ValueError('lease table section 1 is missing')
    active = []
    for line in section[1].split('## 2.', 1)[0].splitlines():
        if not line.startswith('|'):
            continue
        cells = [cell.strip().replace('**', '') for cell in line.strip().strip('|').split('|')]
        if len(cells) != 6 or not re.match(r'^ACTIVE(?:\s|$)', cells[5]):
            continue
        try:
            expiry = dt.datetime.strptime(cells[4][:16], '%Y-%m-%d %H:%M').replace(
                tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30)))
        except ValueError as exc:
            raise ValueError('lease has unreadable expiry') from exc
        if expiry > dt.datetime.now(dt.timezone.utc):
            active.append(cells[0])
    if active != [lease]:
        raise ValueError('lease is not the sole unexpired ACTIVE coordination row')


def save(state_path, state):
    # Caller holds the stable sibling lock. fsync intent BEFORE any external mutation.
    temporary = state_path.with_suffix(state_path.suffix + '.new')
    with temporary.open('w') as stream:
        json.dump(state, stream, sort_keys=True, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, state_path)
    descriptor = os.open(state_path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def deploy_runs(gh, head):
    rows = command(gh, 'run', 'list', '--workflow', 'deploy.yml', '--event', 'workflow_dispatch',
                   '--commit', head, '--limit', '100', '--json',
                   'databaseId,headSha,event,status,conclusion')
    if not isinstance(rows, list):
        raise ValueError('invalid workflow run list')
    return [row for row in rows if row.get('headSha') == head and row.get('event') == 'workflow_dispatch']


def reconcile(source, state_path, state, head, gh, readback):
    row = state['heads'][head]
    if row['status'] == 'verified':
        return {'status': 'already_dispatched', 'head': head, 'inputs': row['inputs']}
    require_lease(source, row['lease'])
    if not row.get('run_id'):
        candidates = [run for run in deploy_runs(gh, head) if run['databaseId'] not in row['previous_runs']]
        if len(candidates) != 1:
            # Includes crash-before-dispatch: never guess whether an API request landed.
            return {'status': 'awaiting_run_identity', 'head': head, 'candidates': len(candidates)}
        row['run_id'] = candidates[0]['databaseId']
        save(state_path, state)
    run = command(gh, 'run', 'view', str(row['run_id']), '--json', 'databaseId,headSha,event,status,conclusion')
    if run.get('headSha') != head or run.get('event') != 'workflow_dispatch':
        raise ValueError('dispatched run does not match reserved head')
    if run.get('status') != 'completed':
        return {'status': 'in_progress', 'head': head, 'run_id': row['run_id'], 'inputs': row['inputs']}
    after = read_applied(readback)
    row['after'] = sorted(after)
    row['conclusion'] = run.get('conclusion')
    missing = sorted(set(row['pending']) - after, key=number)
    row['missing'] = missing
    row['status'] = 'verified' if not missing else 'readback_failed'
    save(state_path, state)
    if missing:
        raise ValueError(f'protected window readback failed for run {row["run_id"]}: {missing}; conclusion={run.get("conclusion")}')
    return {'status': 'verified', 'head': head, 'run_id': row['run_id'], 'inputs': row['inputs'],
            'workflow_conclusion': run.get('conclusion')}


def _tick(source, state_path, lease, gh, readback, dry_run):
    head = source.head()
    sets = catalog(source, head)
    before = read_applied(readback)
    state = json.loads(state_path.read_text()) if state_path.exists() else {'schema': 'ky.protected_window_state/1', 'heads': {}}
    if state.get('schema') != 'ky.protected_window_state/1' or not isinstance(state.get('heads'), dict):
        raise ValueError('invalid protected-window state; refusing to forget dispatch history')
    # Recover old-head runs first, even if main advanced or the DB already changed.
    unfinished = [sha for sha, row in state['heads'].items() if row['status'] not in {'verified', 'readback_failed'}]
    if unfinished:
        if dry_run:
            return {'status': 'dry_run', 'unfinished': unfinished}
        return reconcile(source, state_path, state, unfinished[0], gh, readback)
    if head in state['heads']:
        if state['heads'][head]['status'] == 'readback_failed' and not dry_run:
            return reconcile(source, state_path, state, head, gh, readback)
        return {'status': 'already_dispatched', 'head': head, 'inputs': state['heads'][head]['inputs']}
    pending_sets = {name: sorted(set(items) - before, key=number) for name, items in sets.items() if set(items) - before}
    if not pending_sets:
        return {'status': 'all_applied', 'head': head}
    inputs = sorted(pending_sets, key=lambda name: number(pending_sets[name][0]))
    pending = sorted({item for items in pending_sets.values() for item in items}, key=number)
    # The selected windows pass their ENTIRE sets to migrate.ts --only.
    selected = {item for name in inputs for item in sets[name]}
    highest = max(map(number, selected))
    routine_missing = sorted({Path(path).name for path in source.files(head)
                              if Path(path).name.endswith('.sql') and Path(path).name[:1].isdigit()
                              and number(Path(path).name)[0] <= highest[0]} - selected - before, key=number)
    if routine_missing:
        return {'status': 'waiting_predecessors', 'head': head, 'missing': routine_missing}
    runs = command(gh, 'run', 'list', '--workflow', CI, '--commit', head, '--limit', '100', '--json',
                   'databaseId,headSha,headBranch,event,status,conclusion')
    if not isinstance(runs, list):
        raise ValueError('invalid CI run list')
    eligible = [run for run in runs if run.get('headSha') == head and run.get('headBranch') == 'main'
                and run.get('event') == 'push']
    if not eligible or max(eligible, key=lambda run: run['databaseId']).get('status') != 'completed' or max(
            eligible, key=lambda run: run['databaseId']).get('conclusion') != 'success':
        return {'status': 'waiting_ci', 'head': head}
    require_lease(source, lease)
    for row in schedule_rows(source, head):
        if row.get('migration') in pending and row.get('lease') != lease:
            raise ValueError(f'scheduled lease mismatch for {row["migration"]}')
    remote = command(gh, 'api', 'repos/{owner}/{repo}/git/ref/heads/main')
    if remote.get('object', {}).get('sha') != head or source.head() != head:
        return {'status': 'head_changed', 'head': head}
    if dry_run:
        return {'status': 'dry_run', 'head': head, 'inputs': inputs, 'pending': pending}
    previous = [run['databaseId'] for run in deploy_runs(gh, head)]
    # (I) INTERPRETATION: one batch per head, ordered by lowest pending migration.
    # A failed/uncertain intent needs operator reconciliation; never auto-redispatch.
    state['heads'][head] = {'status': 'dispatch_intent', 'lease': lease, 'inputs': inputs,
                            'pending': pending, 'before': sorted(before), 'previous_runs': previous,
                            'created_at': dt.datetime.now(dt.timezone.utc).isoformat()}
    save(state_path, state)
    # Recheck lease immediately before crossing the external mutation boundary.
    require_lease(source, lease)
    # workflow run emits human-readable output, so do not use the JSON command helper.
    args = [gh, 'workflow', 'run', 'deploy.yml', '--ref', 'main', '-f', 'ci_gate=require-ci-green']
    for name in inputs:
        args.extend(['-f', f'{name}=true'])
    result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError('workflow dispatch failed or uncertain; intent retained, inspect before recovery')
    return reconcile(source, state_path, state, head, gh, readback)


def tick(source, state_path, lease, *, gh='gh', readback='psql', dry_run=False):
    state_path = Path(state_path)
    if dry_run:
        return _tick(source, state_path, lease, gh, readback, True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    # flock survives stale lock files and serializes concurrent ticks/restarts.
    with state_path.with_suffix(state_path.suffix + '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _tick(source, state_path, lease, gh, readback, False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--lease-id', required=True)
    parser.add_argument('--gh', default='gh')
    parser.add_argument('--readback', default='psql', help='psql-compatible executable; returns JSON filename array')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        repo, state = args.repo.resolve(), args.state.resolve()
        os.chdir(repo)  # gh resolves {owner}/{repo} and workflow names in this checkout.
        print(json.dumps(tick(GitSource(repo), state, args.lease_id,
                              gh=args.gh, readback=args.readback, dry_run=args.dry_run), sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
        print(f'FAIL protected-window dispatch: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
