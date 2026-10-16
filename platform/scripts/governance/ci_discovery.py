#!/usr/bin/env python3
"""Runtime CI test discovery. Profiles retain fixture environments; files are never enumerated in ci.yml.

A profile owns filename families, not a frozen list. New ordinary sidecar and web tests also
run through the existing whole-directory jobs. New template-backed Gochara DB suites fall
into the general A5.3 DB context unless a dedicated measured shard already owns their family.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PROFILES = Path(__file__).with_name('ci_test_suites.json')
# Historical group totals from the original workflow comment, not per-file measurements.
SLOW_GROUP_ESTIMATES = (374, 270, 357)
# (I) INTERPRETATION: a newly marked file gets a 100-second scheduling estimate;
# existing files keep their original legs. Actual CI duration remains the authority.
NEW_SLOW_ESTIMATE = 100
# Preserve the existing measured partition; new marked files go to the lightest leg.
SLOW_LEGS = {
    'test_lambda_v3_bounded.py': 1, 'test_mr23_w12_adverse_window_golden.py': 1,
    'test_direction_restored.py': 2, 'test_graded_suppression.py': 2,
    'test_v1_parity.py': 3, 'test_lambda_decomposition.py': 3, 'test_w2g_arc_substrate.py': 3,
}
SLOW_MARK = re.compile(r'pytestmark\s*=\s*pytest\.mark\.slow_real_ephemeris|@pytest\.mark\.slow_real_ephemeris')
DB_MARKERS = ('import template', '_runner_world', 'create_am5_database', 'GOCHARA_A53_ADMIN_DSN',
              'GOCHARA_A53_REQUIRE_DB', 'import test_a53_inventory', 'from .test_a53_',
              'from . import test_a53_', 'from .test_a55_')


def profiles():
    return json.loads(PROFILES.read_text())['suites']


def discover(root: Path, profile: dict) -> list[str]:
    cwd = root / profile['cwd']
    selected = set()
    for pattern in profile['include']:
        if not any(c in pattern for c in '*?['):
            raise ValueError(f'file allowlist is forbidden: {pattern}')
        for path in cwd.glob(pattern):
            if path.is_file() and not any(part in ('node_modules', '__pycache__', '.next') for part in path.parts):
                rel = path.relative_to(cwd).as_posix()
                if any(fnmatch.fnmatchcase(rel, p) for p in profile.get('exclude', [])):
                    continue
                selected.add(rel)
    if profile.get('discover_db'):
        # Dedicated measured contexts keep ownership; otherwise a new real-DB suite
        # joins the general required DB step rather than silently self-skipping.
        claimed = [pattern for key, other in profiles().items()
                   if (key.startswith('gochara-a55-') or key.startswith('db-integration-tests-'))
                   and not other.get('discover_db') and other['engine'] == 'pytest'
                   and other['cwd'] == profile['cwd'] for pattern in other['include']]
        for path in (cwd / 'tests/l3/gochara').rglob('test_*.py'):
            rel = path.relative_to(cwd).as_posix()
            if any(marker in path.read_text() for marker in DB_MARKERS) and not any(fnmatch.fnmatchcase(rel, pat) for pat in claimed):
                selected.add(rel)
    directories = profile.get('directories', [])
    if any(not (cwd / directory).is_dir() for directory in directories):
        raise ValueError('missing discovery directory')
    if not selected and not directories:
        raise ValueError('empty discovery profile; refusing to run an unintended whole-repository suite')
    # Keep directory collection native: preloading every nested conftest by passing
    # its files separately can change pytest fixture/import scope.
    return list(directories) + sorted(selected)


def slow_files(root: Path, leg: int | None = None) -> list[str]:
    cwd = root / 'platform/python-sidecar'
    files = sorted(p.relative_to(cwd).as_posix() for p in (cwd / 'services/gochara_v3/tests').rglob('test_*.py')
                   if SLOW_MARK.search(p.read_text()))
    if leg is None:
        return files
    shards = [[], [], []]
    loads = list(SLOW_GROUP_ESTIMATES)
    for path in files:
        name = Path(path).name
        if name in SLOW_LEGS:
            i = SLOW_LEGS[name] - 1
            shards[i].append(path)
    for path in sorted(p for p in files if Path(p).name not in SLOW_LEGS):
        i = min(range(3), key=lambda i: (loads[i], i))
        shards[i].append(path)
        loads[i] += NEW_SLOW_ESTIMATE
    if sorted(sum(shards, [])) != files or any(not s for s in shards):
        raise ValueError('slow shard partition is incomplete or empty')
    return sorted(shards[leg - 1])


def workflow_problems(text: str) -> list[str]:
    import yaml
    jobs = yaml.safe_load(text).get('jobs', {})
    problems = []
    for name, job in jobs.items():
        steps = job.get('steps', [])
        checkouts = [i for i, step in enumerate(steps)
                     if step.get('uses', '').startswith('actions/checkout@')]
        # Discover consumers from the actual workflow, including jobs merged later.
        # Only classification and the overlay producer intentionally read raw source.
        if checkouts and name not in ('changes', 'generated-artifacts'):
            needs = job.get('needs', [])
            needs = [needs] if isinstance(needs, str) else needs
            if 'generated-artifacts' not in needs:
                problems.append(f'{name}: checkout consumer needs generated-artifacts')
            for index in checkouts:
                restore = steps[index + 1] if index + 1 < len(steps) else {}
                if restore.get('uses') != './.github/actions/restore-generated' or 'if' in restore:
                    problems.append(f'{name}: checkout must immediately restore generated outputs unconditionally')
        for step in steps:
            for line in str(step.get('run', '')).replace('\\\n', ' ').splitlines():
                if line.lstrip().startswith('#'):
                    continue
                if re.search(r'\b(?:pytest|vitest)\b', line):
                    skip_value = False
                    for token in line.split():
                        if skip_value:
                            skip_value = False
                            continue
                        if token in ('--deselect', '--ignore', '--ignore-glob'):
                            skip_value = True
                            continue
                        value = token.strip('\'"')
                        if value.startswith('-'):
                            continue  # existing --ignore/--deselect are exclusion policy, not allowlists
                        if re.search(r'(?:^|/)[^/ ]+(?:\.py|\.(?:test|spec)\.[jt]sx?)(?:::.*)?$', value) and not any(c in value for c in '*?$'):
                            problems.append(f'{name}: explicit test path {value}; use a discovery profile or directory')
    # Matrices must not become a second file allowlist either.
    if re.search(r'\bshard_files\s*:', text):
        problems.append('explicit shard_files matrix; use marker discovery')
    return problems


def run(root: Path, profile: dict, args: list[str]) -> int:
    files = discover(root, profile)
    command = ([sys.executable, '-m', 'pytest'] if profile['engine'] == 'pytest'
               else ['npx', '--no-install', 'vitest', 'run', '--no-cache'])
    quarantine = profile.get('quarantine', {})
    if quarantine and (profile['engine'] != 'vitest' or any(len(reason.strip()) < 12 for reason in quarantine.values()) or any(any(c in path for c in '*?[') for path in quarantine)):
        raise ValueError('quarantine requires Vitest paths and reviewable reasons')
    exclusions = [arg for path in quarantine for arg in ('--exclude', path)]
    if profile.get('workers'):
        exclusions += ['--minWorkers=1', f"--maxWorkers={profile['workers']}"]
    if profile.get('test_timeout_ms'):
        exclusions += [f"--testTimeout={profile['test_timeout_ms']}"]
    return subprocess.call([*command, *files, *exclusions, *args], cwd=root / profile['cwd'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['run', 'pytest', 'vitest', 'files', 'guard', 'slow'])
    ap.add_argument('suite', nargs='?')
    ap.add_argument('args', nargs=argparse.REMAINDER)
    ns = ap.parse_args()
    if ns.mode == 'guard':
        problems = workflow_problems((ROOT / '.github/workflows/ci.yml').read_text())
        print('\n'.join(problems) if problems else 'CI test discovery governance: current')
        return bool(problems)
    if ns.mode == 'slow':
        files = slow_files(ROOT, int(ns.suite.removeprefix('slow-')))
        args = ns.args[1:] if ns.args[:1] == ['--'] else ns.args
        return subprocess.call([sys.executable, '-m', 'pytest', *files, *args], cwd=ROOT / 'platform/python-sidecar')
    profile = profiles()[ns.suite]
    if ns.mode == 'files':
        print('\n'.join(discover(ROOT, profile)))
        return 0
    args = ns.args[1:] if ns.args[:1] == ['--'] else ns.args
    # D-29: a shared PR DB context runs only its changed discovery profiles.
    # Apply before shard selection (#3618); full events leave this env unset.
    if 'CI_PR_DB_PROFILES' in os.environ and os.environ['CI_PR_DB_PROFILES']:
        selected = json.loads(os.environ['CI_PR_DB_PROFILES'])
        if not isinstance(selected, list) or not all(isinstance(p, str) for p in selected):
            raise ValueError('invalid PR DB profile selection')
        if ns.suite not in selected:
            print(f'PR DB profile {ns.suite}: unchanged, skipped by design')
            return 0
    return run(ROOT, profile, args)


def expanded_workflow(jobs: dict, root: Path = ROOT) -> dict:
    """Resolve runtime selections for governance detectors and their in-memory mutations.

    Only substitutes actual discovery invocations; environment, ordering, conditionals,
    flags and shell failure handling remain the workflow's own. Directory selectors stay
    directories so detectors can check the owning boundary as well as individual files.
    """
    import copy
    result = copy.deepcopy(jobs)
    for job in result.values():
        for step in job.get('steps', []):
            if 'run' in step:
                step['run'] = expanded_workflow_text(step['run'], root)
    return result


def expanded_workflow_text(text: str, root: Path = ROOT) -> str:
    """Resolve only command selectors, preserving comments, step order and shell flags."""
    specs = profiles()
    expression = re.compile(r'python(?: -B)? "\$GITHUB_WORKSPACE/platform/scripts/governance/ci_discovery.py" (?:run|pytest|vitest) ([\w-]+) --')
    def expand(match):
        profile = specs[match[1]]
        files = discover(root, profile)
        directories = [p.removesuffix('/**/test_*.py') for p in profile['include'] if p.endswith('/**/test_*.py')]
        remaining = [f for f in files if not any(f.startswith(d + '/') for d in directories)]
        exe = 'python -m pytest' if profile['engine'] == 'pytest' else 'npx vitest run'
        return exe + ' ' + ' '.join(directories + remaining)
    return expression.sub(expand, text)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError) as exc:
        print(f'CI discovery failed: {exc}', file=sys.stderr)
        sys.exit(4)
