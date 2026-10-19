"""CI-FLAKE: a relative pytest path in a ci.yml step must resolve from the directory the step has moved to by that line.

Measured 2026-10-18 (merge_group, 'CI — Ganga Quality Gate' 8 failed of 32): five runs lost all four `DB shard n/4` jobs to
`ERROR: file or directory not found: tests/l3/gochara/test_j4ops_*.py` (pytest exit 4). Two PRs each touched the same
A5.3 step; the merge-queue merge put one PR's relative pytest line after the other's `cd ..`, so it ran from platform/ instead
of platform/python-sidecar and matched nothing. Each PR was green alone; only the combination broke, and it surfaced as
four ~8-minute DB jobs instead of one quick line.

Claim (one): every `pytest <relative path or glob>` line in a ci.yml `run:` script names something that exists when resolved
from the working directory in force at that line (step/job `working-directory`, then the script's own top-level `cd <literal>`
lines). Not claimed: paths built from variables or expressions, subshell `( cd ... && ... )` bodies, and `ci_discovery.py`
profiles (they are resolved by that tool and guarded by test_ci_discovery.py).
"""
import glob
import os
from pathlib import Path
import re
import shlex

import yaml

ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / '.github/workflows/ci.yml'

# pytest options that consume the next token as a value, so that token is not a test path
VALUE_OPTIONS = {'-k', '-m', '-p', '-o', '-c', '--deselect', '--ignore', '--ignore-glob', '--basetemp', '--junitxml',
                 '--rootdir', '--tb', '--maxfail', '--durations', '--co', '-n', '--dist'}


def logical_lines(script):
    """The script's lines with backslash continuations joined and comments dropped."""
    joined, pending = [], ''
    for raw in script.splitlines():
        line = pending + raw.strip()
        pending = ''
        if line.endswith('\\'):
            pending = line[:-1].rstrip() + ' '
            continue
        if line and not line.startswith('#'):
            joined.append(line)
    return joined


def pytest_paths(line):
    """Relative, variable-free test paths named by a direct `pytest` call on this line (none for any other line)."""
    if line.startswith('(') or 'ci_discovery.py' in line:
        return []
    try:
        tokens = shlex.split(line, comments=True)
    except ValueError:
        return []
    # `pytest` is a test run only as the command itself or after `-m` (not `pip install pytest`)
    runs = [i for i, t in enumerate(tokens) if t == 'pytest' and (i == 0 or tokens[i - 1] in ('-m', '&&', ';', '||', '|'))]
    after = tokens[runs[0] + 1:] if runs else []
    paths, skip = [], False
    for token in after:
        if skip:
            skip = False
        elif token in VALUE_OPTIONS:
            skip = True
        elif token.startswith('-') or any(c in token for c in '$`{}'):
            continue
        elif token.startswith('/') or '::' in token and not (token.split('::')[0]):
            continue
        else:
            paths.append(token.split('::')[0])
    return paths


def unresolved(workflow_text, root=ROOT):
    """(job, step, line, path, cwd) for every relative pytest path that matches nothing from the cwd in force at its line."""
    problems = []
    for job_id, job in (yaml.safe_load(workflow_text).get('jobs') or {}).items():
        job_dir = ((job.get('defaults') or {}).get('run') or {}).get('working-directory', '.')
        for index, step in enumerate(job.get('steps') or []):
            script = step.get('run')
            if not isinstance(script, str):
                continue
            cwd = step.get('working-directory', job_dir)
            for line in logical_lines(script):
                move = re.fullmatch(r'cd\s+("?)([^\s"$`{}&;|]+)\1', line)
                if move and cwd is not None:
                    cwd = os.path.normpath(os.path.join(cwd, move.group(2)))
                elif re.match(r'cd(\s|$)', line):
                    cwd = None                      # a cd to a variable or with a chain: where we are is no longer known
                if cwd is None:
                    continue
                for path in pytest_paths(line):
                    if not glob.glob(str(Path(root) / cwd / path)):
                        problems.append((job_id, step.get('name') or index, line, path, cwd))
    return problems


def test_every_relative_pytest_path_in_ci_resolves_from_its_own_working_directory():
    assert unresolved(WORKFLOW.read_text()) == []


def test_the_real_workflow_is_actually_examined_not_passed_by_default():
    text = WORKFLOW.read_text()
    line = 'python -m pytest tests/l3/ka_kshetra/compact -q -p no:cacheprovider'
    assert text.count(line) == 1, 'the real direct pytest line this oracle plants into has moved: pick another'
    found = unresolved(text.replace(line, line.replace('compact', 'compact_gone')))
    assert [(path, cwd) for _, _, _, path, cwd in found] == [('tests/l3/ka_kshetra/compact_gone', 'platform/python-sidecar')]


# The merge-queue shape that failed on 2026-10-18, rebuilt around a test family that exists on main (gochara A25 suites).
# Source of the shape: the failing run's A5.3 step — `cd python-sidecar` ... `cd ..` ... mutation check ... pytest line.
QUEUE_STEP = """
jobs:
  db:
    defaults:
      run:
        working-directory: platform
    steps:
      - name: A5.3
        run: |
          cd python-sidecar
          python -m pytest tests/l3/ka_kshetra/compact -q
          cd ..
          python scripts/gochara/mutation_check_verifier_side.py --scratch "$mutation_scratch"
          {last_line}
"""
BROKEN = 'python -B -m pytest tests/l3/gochara/test_a25_*.py -q -rs -p no:cacheprovider'
PINNED = '(cd "$GITHUB_WORKSPACE/platform/python-sidecar" && python -B -m pytest tests/l3/gochara/test_a25_*.py -q -rs -p no:cacheprovider)'
RESTORED = 'cd python-sidecar\n          python -B -m pytest tests/l3/gochara/test_a25_*.py -q -rs -p no:cacheprovider'


def test_the_queue_shape_that_ran_a_sidecar_glob_from_platform_is_reported():
    found = unresolved(QUEUE_STEP.format(last_line=BROKEN))
    assert [(path, cwd) for _, _, _, path, cwd in found] == [('tests/l3/gochara/test_a25_*.py', 'platform')]


def test_a_subshell_pin_or_a_restored_cd_into_the_sidecar_is_accepted():
    assert unresolved(QUEUE_STEP.format(last_line=PINNED)) == []
    assert unresolved(QUEUE_STEP.format(last_line=RESTORED)) == []


def test_a_cd_to_an_unknown_directory_is_not_guessed_at():
    unknown = QUEUE_STEP.format(last_line='cd "$SOMEWHERE"\n          ' + BROKEN)
    assert unresolved(unknown) == []
