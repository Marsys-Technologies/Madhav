"""A5 D-33: generated overlays are bound to their source and never hide tampering."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[4]
TOOL = ROOT / 'platform/scripts/governance/ci_generated.py'


def module():
    spec = importlib.util.spec_from_file_location('ci_generated', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_overlay_checks_source_sha_and_every_generated_byte(tmp_path):
    mod = module()
    generated = tmp_path / 'platform/src/generated/example.json'
    generated.parent.mkdir(parents=True)
    generated.write_text('{"value":1}\n')
    manifest = mod.manifest(tmp_path, 'a' * 40, ['platform/src/generated/example.json'])
    assert mod.verify(tmp_path, manifest, 'a' * 40) == []
    assert mod.verify(tmp_path, manifest, 'b' * 40)
    generated.write_text('{"value":2}\n')
    assert mod.verify(tmp_path, manifest, 'a' * 40)
    generated.unlink()
    assert mod.verify(tmp_path, manifest, 'a' * 40)


def test_overlay_refuses_path_escape_and_missing_or_empty_manifests(tmp_path):
    mod = module()
    for bad in ({}, {'schema':'ci.generated/1','source_sha':'a'*40,'files':{}},
                {'schema':'ci.generated/1','source_sha':'a'*40,'files':{'../escape':'bad'}}):
        assert mod.verify(tmp_path, bad, 'a' * 40)


def test_changed_generated_outputs_cannot_be_silently_repaired():
    mod = module()
    assert mod.changed_outputs(['platform/src/generated/capability_estate_census.json'])
    assert mod.changed_outputs(['platform/python-sidecar/services/gochara_kernel/implementation_digest.lock.json'])
    assert mod.changed_outputs(['platform/src/generated/handmade.ts'])
    assert not mod.changed_outputs(['platform/src/generated/__tests__/new.test.ts', 'platform/src/real_source.ts'])
    assert not mod.changed_outputs(['platform/src/generated/nirmana-analysis-layer-pins.json', 'platform/src/generated/harvest/e2_db_truth.json'])


def test_overlay_is_required_by_every_ci_checkout_consumer_and_production_build():
    import yaml
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    assert 'generated-artifacts' in jobs
    for key, job in jobs.items():
        if key in ('changes', 'generated-artifacts'):
            continue
        steps = job.get('steps', [])
        if any(step.get('uses', '').startswith('actions/checkout@') for step in steps):
            assert 'generated-artifacts' in str(job.get('needs'))
            assert any(step.get('uses') == './.github/actions/restore-generated' for step in steps), key
    deploy = yaml.safe_load((ROOT / '.github/workflows/deploy.yml').read_text())['jobs']
    for key, job in deploy.items():
        if key.startswith('deploy-'):
            restore = [step for step in job['steps'] if step.get('uses') == './.github/actions/restore-generated']
            assert len(restore) == 1, key
            assert restore[0]['with']['sha'] == '${{ env.DEPLOY_SHA }}'
            assert restore[0].get('if') == "${{ hashFiles('platform/scripts/governance/ci_generated.py') != '' }}"


def test_dirty_local_generation_cannot_be_used_as_a_reviewed_ci_artifact(tmp_path):
    mod = module()
    generated = tmp_path / 'platform/src/generated/example.json'
    generated.parent.mkdir(parents=True)
    generated.write_text('{}\n')
    doc = {**mod.manifest(tmp_path, 'a' * 40, ['platform/src/generated/example.json']), 'test_only': True}
    assert mod.verify(tmp_path, doc, 'a' * 40)


def test_emergency_deploy_never_contacts_the_artifact_service():
    """Execute workflow/action conditions and real lookup bodies with an offline API."""
    import json
    import subprocess
    import yaml
    payload = {
        'jobs': yaml.safe_load((ROOT / '.github/workflows/deploy.yml').read_text())['jobs'],
        'action': yaml.safe_load((ROOT / '.github/actions/restore-generated/action.yml').read_text()),
    }
    script = r'''
const fs = require('node:fs');
const {jobs, action} = JSON.parse(fs.readFileSync(0, 'utf8'));
function evaluate(value, github, inputs, present = true) {
  if (typeof value !== 'string' || !value.startsWith('${{')) return value;
  return new Function('github', 'inputs', 'hashFiles', 'steps', 'env',
    'return (' + value.slice(3, -2).replace(/steps\.generated-ci/g, 'steps["generated-ci"]') + ')')(github, inputs, () => present ? 'hash' : '',
      {'generated-ci': {outputs: {run_id: ''}}}, {DEPLOY_SHA: 'fixture'});
}
(async () => {
  for (const [name, job] of Object.entries(jobs).filter(([name]) => name.startsWith('deploy-'))) {
    for (const scenario of ['never-ran', 'missing', 'expired', 'unavailable', 'retained']) {
      const event = {event_name: 'workflow_dispatch', event: {workflow_run: {}}};
      const inputs = {ci_gate: 'EMERGENCY-OVERRIDE-CI-NOT-GREEN'};
      let calls = 0;
      const api = {rest: {actions: {listWorkflowRuns() {}, listWorkflowRunArtifacts: async () => {
        calls++; if (scenario === 'unavailable') throw Error('artifact service down');
        return {data: {artifacts: scenario === 'missing' ? [] : [{name: 'ci-generated', expired: scenario === 'expired'}]}};
      }}}, paginate: async () => {
        calls++; if (scenario === 'unavailable') throw Error('artifact service down');
        return scenario === 'never-ran' ? [] : [{id: 1, head_sha: 'fixture'}];
      }};
      for (const step of job.steps.filter(s => s.id === 'generated-ci')) {
        if (evaluate(step.if, event, inputs)) {
          await new (Object.getPrototypeOf(async function(){}).constructor)('github', 'context', 'core', step.with.script)(api,
            {repo: {owner: 'fixture', repo: 'fixture'}}, {setOutput() {}});
        }
      }
      if (calls) throw Error(name + ': emergency contacted artifact service: ' + scenario);
      const restore = job.steps.find(s => s.uses === './.github/actions/restore-generated');
      if (!restore || !evaluate(restore.if, event, inputs)) throw Error(name + ': no emergency generated outputs');
      const actionInputs = Object.fromEntries(Object.entries(restore.with).map(([key, value]) => [key, String(evaluate(value, event, inputs))]));
      const selected = action.runs.steps.filter(s => !s.if || evaluate(s.if, event, actionInputs));
      if (selected.some(s => (s.uses || '').startsWith('actions/download-artifact@'))) throw Error(name + ': emergency downloads artifact');
      if (!selected.some(s => (s.run || '').includes('ci_generated.py generate'))) throw Error(name + ': emergency never regenerates');
      if (!selected.some(s => (s.run || '').includes('ci_generated.py verify'))) throw Error(name + ': emergency never verifies');
      if (evaluate(restore.if, event, inputs, false)) throw Error(name + ': pre-cutover fallback lost');
      // Normal manual/automatic deploys still restore the retained source-bound artifact.
      for (const normalEvent of [{event_name: 'workflow_dispatch', event: {workflow_run: {}}},
                                 {event_name: 'workflow_run', event: {workflow_run: {id: 1}}}]) {
        const normalInputs = {ci_gate: 'require-ci-green'};
        const values = Object.fromEntries(Object.entries(restore.with).map(([key, value]) => [key, String(evaluate(value, normalEvent, normalInputs))]));
        if (!action.runs.steps.some(s => (s.uses || '').startsWith('actions/download-artifact@') && (!s.if || evaluate(s.if, normalEvent, values))))
          throw Error(name + ': normal artifact restore lost');
      }
    }
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
'''
    proc = subprocess.run(['node', '-e', script], input=json.dumps(payload), text=True,
                          capture_output=True, cwd=ROOT, timeout=30)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize('fail_mode', ['', 'generate', 'verify'])
def test_emergency_generation_shell_verifies_sha_and_propagates_mismatch(tmp_path, fail_mode):
    """Run the action's real bash; replace only the expensive compiler boundary."""
    import json
    import os
    import subprocess
    import yaml
    action = yaml.safe_load((ROOT / '.github/actions/restore-generated/action.yml').read_text())
    shell = next((s['run'] for s in action['runs']['steps']
                  if 'ci_generated.py generate' in s.get('run', '')), None)
    assert shell, 'emergency regeneration missing'
    compiler = tmp_path / 'platform/scripts/governance/ci_generated.py'
    compiler.parent.mkdir(parents=True)
    compiler.write_text('''import json, os, sys
from pathlib import Path
with Path(os.environ['CALLS']).open('a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')
sys.exit(9 if sys.argv[1] == os.environ['FAIL_MODE'] else 0)
''')
    calls = tmp_path / 'calls.jsonl'
    proc = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', shell], cwd=tmp_path,
                          env={**os.environ, 'EXPECTED_SHA': 'a' * 40, 'RUNNER_TEMP': str(tmp_path),
                               'CALLS': str(calls), 'FAIL_MODE': fail_mode}, capture_output=True, text=True, timeout=30)
    assert proc.returncode == (9 if fail_mode else 0), proc.stdout + proc.stderr
    commands = [json.loads(line) for line in calls.read_text().splitlines()]
    assert commands[0][0] == 'generate'
    if fail_mode != 'generate':
        assert commands[1][0] == 'verify'
        assert commands[1][commands[1].index('--sha') + 1] == 'a' * 40
        assert '--allow-dirty-test' not in commands[1]
