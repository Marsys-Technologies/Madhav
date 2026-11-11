"""No workflow may download this project's own images back out of Artifact Registry (owner-approved cost fix, 2026-10-23).

deploy.yml's pipeline-job verify steps pulled the ~3.7 GB image they had just pushed: 615 GiB of billed egress in 30 days. Each test
below plants ONE reversion in an in-memory workflow (never in the repo) and expects the check to FAIL it; the live-repo tests pin the
shape deploy.yml actually ships, so removing `load: true` or `--pull=never` fails CI before it can cost anything.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / 'platform/scripts/governance/check_registry_pull_guard.py'
_spec = importlib.util.spec_from_file_location('check_registry_pull_guard', SCRIPT)
guard = importlib.util.module_from_spec(_spec)
sys.modules['check_registry_pull_guard'] = guard
_spec.loader.exec_module(guard)

IMAGE = 'asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:${{ env.DEPLOY_SHA }}'


def workflow(run: str = 'echo hi', job_extra: str = '') -> dict:
    text = (f"name: planted\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n{job_extra}    steps:\n"
            f"      - name: planted step\n        run: |\n{textwrap.indent(run, '          ')}\n")
    return yaml.safe_load(text)


def codes(doc) -> list[str]:
    return [v['code'] for v in guard.check_document('planted.yml', doc)]


def test_the_repository_workflows_pass_the_guard():
    assert guard.check_directory(ROOT / '.github/workflows') == []


def test_deploy_keeps_the_pipeline_image_local_and_never_pulls_it():
    doc = yaml.safe_load((ROOT / '.github/workflows/deploy.yml').read_text())
    steps = doc['jobs']['deploy-pipeline-job']['steps']
    build = next(s for s in steps if s.get('name') == 'Build and push pipeline job image')
    assert build['with'].get('load') is True, 'without load: true the verify steps must download the image again'
    assert build['with'].get('push') is True
    runs = [s['run'] for s in steps if 'brahma-pipeline' in s.get('run', '') and 'docker run' in s.get('run', '')]
    assert len(runs) >= 2
    for run in runs:
        for line in guard._logical_lines(run):
            if 'docker run' in line:
                assert '--pull=never' in line


def test_docker_run_without_pull_never_fails():
    assert codes(workflow(f'docker run --rm --entrypoint python \\\n  {IMAGE} \\\n  -c "print(1)"')) == ['REGISTRY_RUN_PULLS']


def test_docker_run_with_pull_never_passes():
    assert codes(workflow(f'docker run --rm --pull=never --entrypoint python \\\n  {IMAGE} -c "print(1)"')) == []
    assert codes(workflow(f'docker run --rm --pull never {IMAGE} true')) == []


def test_docker_pull_and_create_fail():
    assert codes(workflow(f'docker pull {IMAGE}')) == ['REGISTRY_PULL']
    assert codes(workflow(f'docker image pull {IMAGE}')) == ['REGISTRY_PULL']
    assert codes(workflow(f'docker create {IMAGE}')) == ['REGISTRY_RUN_PULLS']
    assert codes(workflow(f'docker container run --rm {IMAGE} true')) == ['REGISTRY_RUN_PULLS']


def test_legacy_gcr_host_is_the_same_registry():
    assert codes(workflow('docker run --rm gcr.io/madhav-astrology/amjis-web:latest true')) == ['REGISTRY_RUN_PULLS']


def test_chained_command_is_checked_per_command():
    assert codes(workflow(f'echo start && docker run --rm {IMAGE} true')) == ['REGISTRY_RUN_PULLS']


def test_job_container_and_service_from_the_registry_fail():
    container = f"    container: {IMAGE}\n"
    service = f"    services:\n      db:\n        image: {IMAGE}\n"
    assert codes(workflow(job_extra=container)) == ['REGISTRY_CONTAINER']
    assert codes(workflow(job_extra=service)) == ['REGISTRY_CONTAINER']


def test_other_images_and_cloud_run_deploys_are_not_flagged():
    assert codes(workflow('docker run --rm postgres:16 true')) == []
    assert codes(workflow('docker run --rm amjis-sidecar:pr-check python -c "1"')) == []
    assert codes(workflow(f'gcloud run jobs update brahma-build-pipeline-job --image={IMAGE}')) == []
    assert codes(workflow(f'# docker run {IMAGE}')) == []


def test_cli_exit_codes(tmp_path):
    (tmp_path / 'bad.yml').write_text(yaml.safe_dump(workflow(f'docker pull {IMAGE}')))
    bad = subprocess.run([sys.executable, str(SCRIPT), '--workflows', str(tmp_path)], capture_output=True, text=True)
    assert bad.returncode == 1 and 'REGISTRY_PULL' in bad.stdout
    good = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert good.returncode == 0, good.stdout
    missing = subprocess.run([sys.executable, str(SCRIPT), '--workflows', str(tmp_path / 'nope')], capture_output=True, text=True)
    assert missing.returncode == 2
