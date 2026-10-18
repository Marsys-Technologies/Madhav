#!/usr/bin/env python3
"""SR-A6-GCW: shared deployment catalog and prospective merge-queue guard.

No Git mutations, SQL connections or workflow dispatches in this module.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

import yaml

DEPLOY = '.github/workflows/deploy.yml'
SCHEDULE = '00_ARCHITECTURE/briefs/kalayantra/fleet/protected_window_schedule.json'
COORD = '00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md'
MIGRATION_DIRS = ('platform/migrations', 'platform/supabase/migrations')
FILENAME = re.compile(r'^\d+_[A-Za-z0-9_]+\.sql$')
SAFE_ID = re.compile(r'^[A-Za-z0-9_.-]{1,80}$')


def number(filename):
    match = re.match(r'^(\d+)', filename)
    if not match:
        raise ValueError(f'unnumbered migration: {filename}')
    return int(match[1]), filename


class GitSource:
    """Read-only snapshots. Supervisor must refresh origin refs before each tick."""
    def __init__(self, repo):
        self.repo = Path(repo)

    def git(self, *args, optional=False):
        result = subprocess.run(['git', *args], cwd=self.repo, text=True, capture_output=True,
                                env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}, timeout=30)
        if result.returncode:
            if optional:
                return None
            raise ValueError(f'git {args[0]} could not read required snapshot')
        return result.stdout

    def head(self):
        head = self.git('rev-parse', '--verify', 'origin/main^{commit}').strip()
        if not re.fullmatch(r'[0-9a-f]{40}', head):
            raise ValueError('origin/main is not a full commit SHA')
        return head

    def text(self, path, ref):
        result = self.git('show', f'{ref}:{path}', optional=True)
        if result is None:
            raise FileNotFoundError(f'{ref}:{path}')
        return result

    def files(self, ref):
        return self.git('ls-tree', '-r', '--name-only', ref, '--', *MIGRATION_DIRS).splitlines()

    def added(self, base):
        # Direct base..HEAD, NOT merge-base(origin/main, HEAD): queue/base refs may advance.
        return self.git('diff', '--name-only', '--diff-filter=A', base, 'HEAD', '--', *MIGRATION_DIRS).splitlines()


class WorkingSource(GitSource):
    """Admission reads the PR checkout; dispatch reads immutable GitSource only."""
    def text(self, path, ref):
        if ref == 'HEAD':
            return (self.repo / path).read_text()
        return super().text(path, ref)


def catalog(source, ref):
    """Derive ALL schema windows from deploy's input/env/selection declarations.

    Parse, never execute PR-supplied shell. Unknown shapes fail closed, requiring
    an explicit parser/test update alongside any new deployment selection form.
    """
    workflow = yaml.safe_load(source.text(DEPLOY, ref))
    inputs = workflow.get('on', workflow.get(True, {}))['workflow_dispatch']['inputs']
    windows = {name for name in inputs if name.endswith('_schema_migration')}
    steps = [step for job in workflow['jobs'].values() for step in job.get('steps', [])
             if step.get('name') == 'Apply exact protected public-schema migrations']
    if len(steps) != 1 or not windows:
        raise ValueError('protected window selection step is missing or ambiguous')
    step = steps[0]
    env = {}
    for var, value in step['env'].items():
        match = re.fullmatch(r'\$\{\{\s*inputs\.([a-z0-9_]+)\s*\}\}', value)
        if match and match[1] in windows:
            env[var] = match[1]
    blocks = re.findall(r'^if \[ "\$(\w+)" = "true" \]; then\n(.*?)^fi\s*$', step['run'], re.M | re.S)
    result = {}
    seen = set()
    for var, body in blocks:
        if var not in env:
            raise ValueError(f'unknown protected window selection variable: {var}')
        name = env[var]
        names = re.findall(r'^\s*migrations\+=\(([0-9]+_[A-Za-z0-9_]+\.sql)\)\s*$', body, re.M)
        listing = re.search(r'^\s*kala_list=([A-Za-z0-9_./-]+)\s*$', body, re.M)
        appends = [line.strip() for line in body.splitlines() if 'migrations+=' in line and not line.lstrip().startswith('#')]
        allowed = {f'migrations+=({item})' for item in names}
        if listing:
            allowed.add('migrations+=("$kala_file")')
        if any(line not in allowed for line in appends):
            raise ValueError(f'unrecognized protected window selection: {name}')
        if listing:
            path = PurePosixPath(listing[1])
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('unsafe protected window list path')
            for line in source.text(str(path), ref).splitlines():
                item = line.split('#', 1)[0].strip()
                if item:
                    names.append(item)
        if not names or any(not FILENAME.fullmatch(n) for n in names):
            raise ValueError(f'empty or unrecognized protected window selection: {name}')
        if name in result or seen.intersection(names) or len(names) != len(set(names)):
            raise ValueError(f'duplicate protected window selection: {name}')
        result[name] = sorted(names, key=number)
        seen.update(names)
    if set(result) != windows:
        raise ValueError(f'protected window inputs have no selection: {sorted(windows - set(result))}')
    files = {Path(path).name for path in source.files(ref)}
    if seen - files:
        raise ValueError(f'protected window references missing migrations: {sorted(seen - files)}')
    return result


def schedule_rows(source, ref):
    try:
        data = json.loads(source.text(SCHEDULE, ref))
    except FileNotFoundError:
        return []  # Prospective guard: history before the scheduling format is valid.
    if data.get('schema') != 'ky.protected_window_schedule/1' or not isinstance(data.get('windows'), list):
        raise ValueError('invalid protected window schedule schema')
    return data['windows']


def guard(source, base):
    current = catalog(source, 'HEAD')
    prior = catalog(source, base)
    additions = {Path(path).name for path in source.added(base)}
    old_pairs = {(name, item) for name, items in prior.items() for item in items}
    expected = {(name, item) for name, items in current.items() for item in items
                if item in additions or (name, item) not in old_pairs}
    previous_rows = schedule_rows(source, base)
    rows = schedule_rows(source, 'HEAD')
    errors = []
    for row in previous_rows:
        if row not in rows:
            errors.append('schedule commitment removed or changed; schedule records are append-only')
    # A runner-only classification must not make an added migration invisible to
    # the deployment catalog (the original incident crossed exactly this seam).
    runner = source.text('platform/scripts/migrate.ts', 'HEAD')
    public_set = re.search(r'PROTECTED_PUBLIC_SCHEMA_MIGRATIONS\s*=\s*new Set\(\[([\s\S]*?)\]\)', runner)
    metering = re.search(r"AI_METERING_PROTECTED_PUBLIC_SCHEMA_MIGRATION\s*=\s*'([^']+\.sql)'", runner)
    if not public_set or not metering:
        raise ValueError('cannot parse protected public-schema runner declarations')
    runner_names = set(re.findall(r"'([^']+\.sql)'", public_set[1])) | {metering[1]}
    catalog_names = {item for items in current.values() for item in items}
    for migration in sorted(runner_names - catalog_names, key=number):
        errors.append(f'{migration}: protected runner declaration has no deployment window')
    valid = set()
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'migration', 'window_input', 'lease'}:
            errors.append('schedule row must name exactly migration, window_input and lease')
            continue
        migration, window, lease = row['migration'], row['window_input'], row['lease']
        if not all(isinstance(x, str) for x in (migration, window, lease)):
            errors.append('schedule fields must be strings')
            continue
        pair = (window, migration)
        if pair in seen:
            errors.append(f'duplicate schedule for {migration}')
        seen.add(pair)
        if window not in current or migration not in current[window]:
            errors.append(f'schedule {migration}: wrong protected window {window}')
        elif not SAFE_ID.fullmatch(lease) or lease.upper() in {'TODO', 'TBD', 'NONE', 'UNKNOWN'}:
            errors.append(f'schedule {migration}: missing or placeholder lease')
        elif row not in previous_rows:
            valid.add(pair)
    for window, migration in sorted(expected - valid, key=lambda pair: number(pair[1])):
        errors.append(f'{migration}: add a new schedule record for {window} with the lease to use in this PR')
    return errors


def event_base(source, explicit=None):
    if explicit:
        return explicit
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    if event_path:
        event = json.loads(Path(event_path).read_text())
        kind = os.environ.get('GITHUB_EVENT_NAME')
        if kind == 'pull_request':
            base = event['pull_request']['base']['sha']
        elif kind == 'merge_group':
            base = event['merge_group']['base_sha']
        elif kind == 'push':
            base = event['before']
        elif kind == 'workflow_dispatch':
            return source.git('merge-base', 'origin/main', 'HEAD').strip()
        else:
            raise ValueError('protected window guard needs --base for this event')
        if not re.fullmatch(r'[0-9a-f]{40}', base) or base == '0' * 40:
            raise ValueError('invalid or missing event base SHA')
        return base
    return source.git('merge-base', 'origin/main', 'HEAD').strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['guard'])
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument('--base')
    args = parser.parse_args(argv)
    source = WorkingSource(args.repo)
    try:
        errors = guard(source, event_base(source, args.base))
        for error in errors:
            print(f'FAIL protected-window schedule: {error}', file=sys.stderr)
        if not errors:
            print('PASS protected-window schedule: every new protected migration has a window and lease')
        return int(bool(errors))
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError, yaml.YAMLError) as exc:
        print(f'FAIL protected-window schedule: {exc}', file=sys.stderr)
        return 5


if __name__ == '__main__':
    sys.exit(main())
