"""J-5s disabled launcher planning: no transport, one strict verifier contract."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from tests.test_gochara_verification_job_readback import job, task, SHA, DIG


def load():
    path = SCRIPTS / 'prepare_gochara_verifier_launch.py'
    assert path.is_file(), 'the disabled verifier launcher preparation is missing'
    spec = importlib.util.spec_from_file_location('j5s_prepare', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepared_binding_is_disabled_and_pins_full_verification_not_report_or_brief():
    m = load()
    out = m.prepare(job(), reviewed_commit=SHA, image_digest=DIG)
    assert out['schema'] == 'ky.j5s_verifier_launch_preparation/1'
    assert out['enabled'] is False and out['dry_run_passed'] is False
    assert out['status'] == 'PREPARATION_ONLY' and out['production_allocation'] is None
    assert out['runtime_principal'] == 'gochara_verifier'
    assert out['expected_args'] == ['--chart', m.CHART, '--generation', '5.0', '--final-rules']
    expected_digest = hashlib.sha256(json.dumps(job(), sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert out['definition_sha256'] == expected_digest
    assert out['reviewed_commit'] == SHA and out['image_digest'] == DIG
    assert out['argv'] == ['gcloud', 'run', 'jobs', 'execute', 'gochara-verification-job', '--project',
        'madhav-astrology', '--region', 'asia-south1', '--args=--chart,' + m.CHART + ',--generation,5.0,--final-rules',
        '--async', '--format=value(metadata.name)']
    assert {'P06b', 'campaign-coordination', 'backup_restore_verified', 'dry_run_passed',
            'one_build_slot', 'independent_pre_acceptance', 'reviewed_launcher_allocation'} <= set(out['activation_requires'])
    assert out['completion_requires'] == ['executor_receipt', 'executed_resource_readback',
        'full_manifest_all_included_grains_verified', 'approval_bound_seal',
        'independent_readback_sql_same_manifest_execution_run_attempt', 'independent_verdict']


@pytest.mark.parametrize('change', [
    lambda j: task(j).update(serviceAccountName='data-plane-builder-runtime@madhav-astrology.iam.gserviceaccount.com'),
    lambda j: task(j)['containers'][0].update(image='mutable:latest'),
    lambda j: task(j)['containers'][0].update(command=['python', '-m', 'pipeline.orchestrator.main']),
    lambda j: task(j)['containers'][0].update(args=['--report-only']),
    lambda j: task(j)['containers'][0]['env'].append({'name': 'DATABASE_URL', 'value': 'untrusted'}),
    lambda j: task(j).pop('maxRetries'),
])
def test_definition_drift_cannot_be_prepared(change):
    m = load()
    bad = copy.deepcopy(job())
    change(bad)
    with pytest.raises(m.Refused):
        m.prepare(bad, reviewed_commit=SHA, image_digest=DIG)


def test_cli_never_executes_and_rejects_execute_flag(tmp_path):
    load()
    path = tmp_path / 'job.json'
    path.write_text(json.dumps(job()))
    args = [sys.executable, '-B', str(SCRIPTS / 'prepare_gochara_verifier_launch.py'), '--job-file', str(path),
            '--reviewed-commit', SHA, '--image-digest', DIG]
    out = subprocess.run(args, capture_output=True, text=True, check=False)
    assert out.returncode == 0 and json.loads(out.stdout)['enabled'] is False
    out = subprocess.run(args + ['--execute'], capture_output=True, text=True, check=False)
    assert out.returncode == 2 and not out.stdout
