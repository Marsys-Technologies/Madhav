"""K6-5 step oracle: active/current evidence, never a production certificate.

K8 contract: KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:321.
Registrar scope: control/kalayantra/plan_model.json:4159-4183.
"""
import json
from pathlib import Path
import shutil

import pytest

from services import ka_bhavishya_lekha as service

ROOT = Path(__file__).resolve().parents[5]
MAPPING = Path('platform/python-sidecar/services/ka_bhavishya_lekha/certification_mapping.json')
REGISTRY = Path('platform/scripts/governance/asset_census.py')


def certification_mapping_oracle(root):
    validate = getattr(service, 'validate_certification_mapping', None)
    assert callable(validate), 'K6-5 production certification mapping validator missing'
    assert validate(root) == []


def test_committed_certification_mapping_is_current_and_unmeasured():
    certification_mapping_oracle(ROOT)


@pytest.fixture
def evidence_copy(tmp_path):
    mapping = json.loads((ROOT / MAPPING).read_text())
    paths = [MAPPING, REGISTRY]
    paths += [Path('platform/python-sidecar') / ref.split('::')[0]
              for ref in mapping['fidelity_tests']]
    for path in paths:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    return tmp_path


@pytest.mark.parametrize('mutation', [
    'archived_gates', 'deleted_mapping', 'missing_idem_revision',
    'nonexistent_fidelity_test', 'unearned_production_certificate',
    'missing_production_certification', 'stale_registry', 'false_no_detector',
])
def test_oracle_rejects_mutated_mapping_copy(evidence_copy, mutation):
    certification_mapping_oracle(evidence_copy)
    path = evidence_copy / MAPPING
    mapping = json.loads(path.read_text())
    if mutation == 'archived_gates':
        mapping['archived_gates'] = mapping.pop('gates')
    elif mutation == 'deleted_mapping':
        path.unlink()
    elif mutation == 'missing_idem_revision':
        mapping['gates']['Idem']['revisions'].pop('Idem.pattern')
    elif mutation == 'nonexistent_fidelity_test':
        mapping['fidelity_tests'][0] = mapping['fidelity_tests'][0].split('::')[0] + '::test_nonexistent'
    elif mutation == 'unearned_production_certificate':
        mapping['production_certification'] = 'PASS'
    elif mutation == 'missing_production_certification':
        mapping.pop('production_certification')
    elif mutation == 'stale_registry':
        mapping['registry_revision'] = 0
    elif mutation == 'false_no_detector':
        mapping['gates']['Carr']['detector_none'] = []
    if mutation != 'deleted_mapping':
        path.write_text(json.dumps(mapping))
    with pytest.raises(AssertionError):
        certification_mapping_oracle(evidence_copy)
