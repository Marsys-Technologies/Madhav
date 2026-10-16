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


def test_overlay_is_required_by_every_ci_checkout_consumer():
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


def test_kcert_sidecar_checks_verified_inventory_before_running_required_tests():
    """KCERT2-R1-N01: repair the generation boundary without losing either gate."""
    import yaml
    import ci_discovery

    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    job = jobs['governance-gates-py-sidecar-shard']
    assert 'generated-artifacts' in str(job.get('needs'))
    steps = job['steps']
    checkout = next(i for i, step in enumerate(steps)
                    if step.get('uses', '').startswith('actions/checkout@'))
    assert steps[checkout + 1]['uses'] == './.github/actions/restore-generated'
    run = next(step['run'] for step in steps if '--ci-shard' in step.get('run', ''))
    expanded = ci_discovery.expanded_workflow_text(run)
    guard = 'python -m pipeline.orchestrator.provenance_inventory --check'
    assert guard in expanded
    assert expanded.index(guard) < expanded.index('python -m pytest tests/')
    assert (ROOT / 'platform/python-sidecar/tests/l3/kala_db/test_k_cert_citation_resolution.py').is_file()
    producer = '\n'.join(step.get('run', '') for step in jobs['generated-artifacts']['steps'])
    assert 'ci_generated.py generate --destination' in producer
    action = (ROOT / '.github/actions/restore-generated/action.yml').read_text()
    assert 'ci_generated.py verify' in action
    assert '--allow-dirty-test' not in action


def test_dirty_local_generation_cannot_be_used_as_a_reviewed_ci_artifact(tmp_path):
    mod = module()
    generated = tmp_path / 'platform/src/generated/example.json'
    generated.parent.mkdir(parents=True)
    generated.write_text('{}\n')
    doc = {**mod.manifest(tmp_path, 'a' * 40, ['platform/src/generated/example.json']), 'test_only': True}
    assert mod.verify(tmp_path, doc, 'a' * 40)
