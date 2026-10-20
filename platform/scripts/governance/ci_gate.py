#!/usr/bin/env python3
"""D-29 light PR gate: derive DB-profile ownership from ci.yml and discovery.

SR-BOLD-08(a): also decides `run_combination_suites` -- false only on a pull_request that leaves the scoping rules alone
(DB Integration Tests and the Governance Tool Tests shards are then merge_group-only; see PR_DEFERRED_DB_JOBS).

(I) INTERPRETATION: the brief's changed-profile DB exception qualifies its normal
PR heavy-job skip. Source/migration-only PRs use full_gate dispatch.
(I) INTERPRETATION: selection runs the entire affected profile, preserving fixture
and shard coverage, rather than narrowing it to individual changed files.
No committed file list: new test family members inherit their discovery context.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
import posixpath
import re

import ci_changes
import ci_discovery

ROOT = Path(__file__).resolve().parents[3]
# OWNER-CI-SCOPED-QUEUE-20261017: the merge queue selects exactly as a PR does; push/main and
# full_gate dispatch print empty selections because the workflow runs every heavy job there.
SCOPED_EVENTS = ('pull_request', 'merge_group')
# SR-CI-SCOPED-SAFEGUARD (surrogate ruling 2026-10-17): suites that failed "green alone, red combined" run on EVERY
# merge_group whatever paths changed: DB Integration Tests (SAMIKSHA, all shards), the Gochara measuring build, and
# the C38 small-test teardown (base + rounds 2 and 3). Job ids in ci.yml; their profiles come from db_profile_owners.
QUEUE_ALWAYS_JOBS = frozenset({
    'db-integration-tests', 'gochara-a55-measuring-build',
    'gochara-a55-teardown', 'gochara-a55-teardown-round2', 'gochara-a55-teardown-round3',
})
# OWNER-MERGE-GROUP-FULL-20261019 (supersedes the merge_group clause of OWNER-CI-SCOPED-QUEUE-20261017): from now until the
# campaign closes, a merge_group runs the FULL "CI -- Ganga Quality Gate" -- every DB job and profile, unscoped; a pull_request
# stays path-scoped. Reason: two red mains in 24 h (K7 certification; C37 and A5.5f), each from a suite scoped out of the queue.
# THE SINGLE SWITCH: set MERGE_GROUP_FULL = False at campaign close to return the queue to the scoped path (QUEUE_ALWAYS_JOBS).
MERGE_GROUP_FULL = True
# Record of SR-SCOPE-C37 (owner surrogate, 2026-10-19; incident #3715 -- a backup-validity change merged green and turned
# push-main red because C37 was path-scoped out of the queue). That ruling selected the C37 dispatch job and the C38 teardown
# jobs on a merge_group whose diff touched these repo-relative globs; MERGE_GROUP_FULL makes it moot, the list is kept as the
# record of why (re-add as a path-scoped queue rule if the switch is turned off):
#   00_ARCHITECTURE/briefs/kalayantra/fleet/**   platform/scripts/*small_test*   platform/scripts/backup_v5_*
#   platform/scripts/dispatch_v5_*   platform/scripts/teardown_v5_*   platform/scripts/*executor*
#   platform/python-sidecar/tests/l3/gochara/_smalltest_executor*
#   -> jobs gochara-a55-dispatch, gochara-a55-teardown, gochara-a55-teardown-round2, gochara-a55-teardown-round3
# SR-BOLD-08(a) (owner-confirmed 2026-10-18): the same combination-sensitive family is MERGE_GROUP-ONLY. A pull_request does not
# run DB Integration Tests (SAMIKSHA, all shards, even when its diff touches their tests) nor the Governance Tool Tests shards; the
# queue runs both on the PR merged with current main -- the only place "green alone, red combined" can be measured -- and the
# fast/ preflight (SR-PREFLIGHT-FULL) runs them locally before a PR is armed. Their required names still report on the PR:
# `required-db-integration-tests` and `governance-tool-tests` say "deferred to the merge queue" and pass ONLY when `changes`
# proved the deferral (see their steps in ci.yml). Job ids in ci.yml.
PR_DEFERRED_DB_JOBS = frozenset({'db-integration-tests'})
# The scoper cannot vouch for a change to itself: a pull_request whose diff touches the scoping rules, the workflow or the
# discovery that feeds them runs the whole family on the PR (fail-safe). Repo-relative paths, exact match.
SCOPER_PATHS = frozenset({
    '.github/workflows/ci.yml',
    'platform/scripts/governance/ci_gate.py',
    'platform/scripts/governance/ci_changes.py',
    'platform/scripts/governance/ci_discovery.py',
    'platform/scripts/governance/ci_test_suites.json',
})
PROFILE_CALL = re.compile(r'ci_discovery\.py[\"\']?\s+(?:run|pytest|vitest)\s+([\w-]+)\s+--')


def db_profile_owners(jobs: dict) -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for name, job in jobs.items():
        if not job.get('services'):
            continue
        for step in job.get('steps', []):
            for profile in PROFILE_CALL.findall(str(step.get('run', ''))):
                if name not in owners.setdefault(profile, []):
                    owners[profile].append(name)
    return owners


def _test_file(path: str, engine: str) -> bool:
    name = posixpath.basename(path)
    if engine == 'pytest':
        return name.endswith('.py') and (name.startswith('test_') or name.endswith('_test.py'))
    return bool(re.search(r'\.(?:test|spec)\.[jt]sx?$', name))


def _glob_matches(path: str, pattern: str) -> bool:
    def match(parts, patterns):
        if not patterns:
            return not parts
        if patterns[0] == '**':
            return any(match(parts[i:], patterns[1:]) for i in range(len(parts) + 1))
        return bool(parts) and fnmatch.fnmatchcase(parts[0], patterns[0]) and match(parts[1:], patterns[1:])
    return match(path.split('/'), pattern.split('/'))


def _matches(root: Path, spec: dict, paths: list[str], discovered: list[str]) -> bool:
    cwd = root / spec['cwd']
    selected = {posixpath.normpath(f'{spec["cwd"]}/{path}') for path in discovered}
    directories = [posixpath.normpath(f'{spec["cwd"]}/{path}').rstrip('/') + '/'
                   for path in discovered if (cwd / path).is_dir()]
    for path in paths:
        # A profile may also own non-test source paths (repo-root globs): a change to one runs the whole profile.
        if any(_glob_matches(path, pat) for pat in spec.get('path_triggers', [])):
            return True
        if path in selected or (_test_file(path, spec['engine']) and any(path.startswith(d) for d in directories)):
            return True
        # A deleted/renamed-away file is absent from discover(); retain its old
        # family ownership using the same profile patterns (--no-renames diff).
        if not (root / path).exists():
            rel = posixpath.relpath(path, spec['cwd'])
            includes = spec['include']
            if any(_glob_matches(rel, pat) for pat in includes):
                if not any(_glob_matches(rel, pat) for pat in spec.get('exclude', [])):
                    return True
            if _test_file(path, spec['engine']) and any(path.startswith(posixpath.normpath(f'{spec["cwd"]}/{d}').rstrip('/') + '/') for d in spec.get('directories', [])):
                return True
    return False


def combination_suites_run(event: str, paths: list[str]) -> bool:
    """True when the combination-sensitive family runs in THIS event. Only a pull_request defers it, and only when its diff
    is non-empty and touches none of SCOPER_PATHS; every other event (queue, main, dispatch) runs it."""
    return event != 'pull_request' or any(path in SCOPER_PATHS for path in paths)


def merge_group_full(event: str) -> bool:
    """True when this event runs every DB job and profile unscoped: a merge_group while MERGE_GROUP_FULL is on."""
    return MERGE_GROUP_FULL and event == 'merge_group'


def select_db(root: Path, jobs: dict, paths: list[str], always_jobs=frozenset(), deferred_jobs=frozenset(), select_all=False) -> tuple[list[str], list[str]]:
    specs = ci_discovery.profiles()
    selected_jobs: set[str] = set()
    selected_profiles: list[str] = []
    for profile, owners in db_profile_owners(jobs).items():
        spec = specs[profile]
        owners = [owner for owner in owners if owner not in deferred_jobs]
        if not owners:
            continue
        if select_all or any(owner in always_jobs for owner in owners) or _matches(root, spec, paths, ci_discovery.discover(root, spec)):
            selected_profiles.append(profile)
            selected_jobs.update(owners)
    # Accepted #3618 fixture producers are prerequisites, not a second profile list.
    pending = list(selected_jobs)
    while pending:
        job = jobs[pending.pop()]
        needs = job.get('needs', [])
        for name in ([needs] if isinstance(needs, str) else needs):
            if jobs[name].get('services') and name not in selected_jobs:
                selected_jobs.add(name)
                pending.append(name)
    return sorted(selected_jobs), sorted(selected_profiles)


def main(argv=None):
    import yaml
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--event', required=True)
    ap.add_argument('--base', default='HEAD^1')
    ap.add_argument('--head', default='HEAD')
    ns = ap.parse_args(argv)
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    scoped = ns.event in SCOPED_EVENTS
    paths = ci_changes.changed_files(ns.base, ns.head) if scoped else []
    if paths is None or (scoped and not paths):
        raise ValueError('cannot establish the PR/queue diff; refusing a green light gate')
    always = QUEUE_ALWAYS_JOBS if ns.event == 'merge_group' else frozenset()
    run_combination = combination_suites_run(ns.event, paths)
    deferred = frozenset() if run_combination else PR_DEFERRED_DB_JOBS
    selected_jobs, selected_profiles = select_db(ROOT, jobs, paths, always, deferred, merge_group_full(ns.event)) if scoped else ([], [])
    print('db_jobs=' + json.dumps(selected_jobs, separators=(',', ':')))
    print('db_profiles=' + json.dumps(selected_profiles, separators=(',', ':')))
    print('run_combination_suites=' + ('true' if run_combination else 'false'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
