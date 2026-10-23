"""Oracles for the gcloud flag-drift guard (CLAUDE.md §N.8; incident: run 39736105931, 2026-10-22).

The incident: `gcloud run jobs deploy ... --clear-args` — "unrecognized arguments: --clear-args" — passed every CI check because
no check ever compared a workflow's gcloud flags with gcloud's own flag list. Claims, one detector each:

 C1  every gcloud flag the repository's workflows use is in the reference fixture (the production claim; fails at the pre-fix head)
 C2  the detector can read false: a planted unsupported flag in a workflow is reported, whichever way it reaches gcloud
     (inline, bash-array expansion, deploy-cloudrun `flags:`), and an unknown gcloud command is reported rather than skipped
 C3  the reference fixture states the documented fact behind the incident: no `--clear-args` on `run jobs deploy|update`;
     `--args` (the documented reset, "pass an empty string") is on both
 C4  live mode compares against `--help` text: a flag missing from the help is reported; `--[no-]x` in help covers --x and --no-x
 C5  the verification-job definition workflow reaches gcloud with flags that all exist for the command it calls
     (create -> `run jobs deploy`, no args; update -> `run jobs update --args ""`)

Sources for C3 (official reference, retrieved 2026-10-22):
 https://docs.cloud.google.com/sdk/gcloud/reference/run/jobs/deploy and .../run/jobs/update — `--args`: "To reset this field to its
 default, pass an empty string."; neither page lists `--clear-args`.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

GOV = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location('gcloud_flag_drift', GOV / 'gcloud_flag_drift.py')
drift = importlib.util.module_from_spec(spec)
sys.modules['gcloud_flag_drift'] = drift
spec.loader.exec_module(drift)
REFERENCE = drift.load_reference(drift.DEFAULT_REFERENCE)
DEFINITION = '.github/workflows/gochara-verification-job-deploy.yml'


def make_repo(tmp_path, workflow_text, name='w.yml'):
    wf = tmp_path / '.github/workflows'
    wf.mkdir(parents=True)
    (wf / name).write_text(workflow_text)
    return tmp_path


def workflow_with(run):
    body = '\n'.join('          ' + l for l in run.strip('\n').split('\n'))
    return f'name: t\non: workflow_dispatch\njobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n      - name: s\n        run: |\n{body}\n'


def static_problems_for(root):
    used, unknown = drift.uses_by_command(drift.collect_calls(root), REFERENCE)
    return unknown + drift.static_problems(used, REFERENCE)


def test_c1_every_gcloud_flag_in_the_repository_workflows_is_in_the_reference():
    calls = drift.collect_calls(ROOT)
    assert len(calls) >= 30, 'the scanner found suspiciously few gcloud calls; it is not reading the workflows'
    assert static_problems_for(ROOT) == []


def test_c1_cli_exit_code_matches(tmp_path):
    ok = subprocess.run([sys.executable, str(GOV / 'gcloud_flag_drift.py'), 'static', '--root', str(ROOT)], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    bad = make_repo(tmp_path, workflow_with('gcloud run jobs deploy j --clear-args'))
    r = subprocess.run([sys.executable, str(GOV / 'gcloud_flag_drift.py'), 'static', '--root', str(bad)], capture_output=True, text=True)
    assert r.returncode == 1 and '--clear-args' in r.stdout


def test_c2_the_incident_command_is_reported(tmp_path):
    root = make_repo(tmp_path, workflow_with('''
gcloud run jobs deploy "$JOB" \\
  --project p \\
  --clear-args \\
  --quiet
'''))
    problems = static_problems_for(root)
    assert len(problems) == 1 and 'run jobs deploy' in problems[0] and '--clear-args' in problems[0]


def test_c2_flags_reach_gcloud_through_a_bash_array_and_are_still_checked(tmp_path):
    root = make_repo(tmp_path, workflow_with('''
FLAGS=(
  --project p
  --clear-args
  --max-retries 0
)
gcloud run jobs deploy "$JOB" "${FLAGS[@]}"
'''))
    problems = static_problems_for(root)
    assert len(problems) == 1 and '--clear-args' in problems[0]


def test_c2_deploy_cloudrun_flags_input_is_checked_against_run_deploy(tmp_path):
    text = ('name: t\non: workflow_dispatch\njobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n      - name: d\n'
            '        uses: google-github-actions/deploy-cloudrun@v2\n        with:\n          service: s\n          flags: >-\n'
            '            --no-traffic\n            --not-a-real-flag=1\n')
    problems = static_problems_for(make_repo(tmp_path, text))
    assert len(problems) == 1 and '--not-a-real-flag' in problems[0] and 'run deploy' in problems[0]


def test_c2_unknown_gcloud_command_is_reported_not_skipped(tmp_path):
    problems = static_problems_for(make_repo(tmp_path, workflow_with('gcloud frobnicate widgets --quiet')))
    assert len(problems) == 1 and 'not in the reference fixture' in problems[0]


def test_c2_gcloud_inside_command_substitution_and_a_quoted_format_is_found(tmp_path):
    root = make_repo(tmp_path, workflow_with('''
EXEC="$(gcloud run jobs execute "$J" --project p --region r \\
  --args="--a,b" --bogus --async --format='value(metadata.name)')"
'''))
    problems = static_problems_for(root)
    assert len(problems) == 1 and '--bogus' in problems[0]


def test_c3_reference_records_the_documented_args_reset_and_no_clear_args():
    for command in ('run jobs deploy', 'run jobs update'):
        flags = REFERENCE['commands'][command]
        assert '--args' in flags and '--clear-args' not in flags
    assert '--clear-args' not in REFERENCE['commands']['run deploy']
    assert REFERENCE['source']['pages']['run jobs deploy'].startswith('https://docs.cloud.google.com/sdk/gcloud/reference/')
    assert REFERENCE['source']['retrieved'] and REFERENCE['source']['gcloud_version']


HELP_DEPLOY = '''
NAME  gcloud run jobs deploy
    --args=[ARG,...]   Comma-separated arguments.
    --[no-]gpu-zonal-redundancy
    --image=IMAGE
GCLOUD WIDE FLAGS
    --project=PROJECT_ID  --quiet
'''


def test_c4_live_mode_reports_a_flag_missing_from_help_and_accepts_present_ones():
    used = {'run jobs deploy': {'--args': ['a'], '--no-gpu-zonal-redundancy': ['b'], '--project': ['c'], '--clear-args': ['d']}}
    problems = drift.live_problems(used, run_help=lambda command: HELP_DEPLOY)
    assert len(problems) == 1 and '--clear-args' in problems[0]


def test_c4_live_mode_refuses_to_pass_on_empty_help():
    problems = drift.live_problems({'run jobs deploy': {'--args': ['a']}}, run_help=lambda command: 'ERROR: not installed')
    assert len(problems) == 1 and 'cannot verify' in problems[0]


def test_c5_definition_workflow_flags_are_valid_for_the_command_that_carries_them():
    calls = [c for c in drift.collect_calls(ROOT) if c.file == DEFINITION]
    by_command = {drift.resolve_command(c, REFERENCE['commands']): c for c in calls}
    deploy, update = by_command['run jobs deploy'], by_command['run jobs update']
    assert '--args' not in deploy.flags() and '--clear-args' not in deploy.flags()
    assert update.flags().count('--args') == 1 and update.words[update.words.index('--args') + 1] == ''
    # same definition on both paths: every flag but --args is shared
    assert sorted(set(update.flags()) - {'--args'}) == sorted(set(deploy.flags()))
    for call in (deploy, update):
        allowed = set(REFERENCE['commands'][drift.resolve_command(call, REFERENCE['commands'])]) | set(REFERENCE['global_flags'])
        assert set(call.flags()) <= allowed
