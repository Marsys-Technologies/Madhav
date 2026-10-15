"""Production evidence mutations must fail through both shared-validator callers."""
import copy
import json
from pathlib import Path
import shutil

import pytest

from services import ka_bhavishya_lekha as registrar
from services import ka_tulana as tulana

ROOT = Path(__file__).resolve().parents[4]
VIEWS = ['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain']
VIEW_ROOT = 'platform/src/lib/retrieval/registry/layers/L3_kala/'


@pytest.mark.parametrize('view', VIEWS)
@pytest.mark.parametrize('pointer', [
    'platform/python-sidecar/services/ka_tulana/__init__.py:1',
    VIEW_ROOT + 'view_common.ts:1',
    VIEW_ROOT + 'view_common.ts:99999',
])
def test_tier_pointer_must_resolve_stored_tier_select(monkeypatch, view, pointer):
    mapping = copy.deepcopy(tulana.CERTIFICATION_MAPPING)
    mapping['views'][view]['tier_select'] = pointer
    monkeypatch.setattr(tulana, 'CERTIFICATION_MAPPING', mapping)
    assert tulana.validate_certification_mapping(ROOT), 'non-SELECT tier evidence accepted'


@pytest.mark.parametrize('view', VIEWS)
def test_production_module_is_not_fidelity_evidence(monkeypatch, view):
    mapping = copy.deepcopy(tulana.CERTIFICATION_MAPPING)
    mapping['views'][view]['fidelity_tests'] = [VIEW_ROOT + 'view_now.ts']
    monkeypatch.setattr(tulana, 'CERTIFICATION_MAPPING', mapping)
    assert tulana.validate_certification_mapping(ROOT), 'non-test fidelity evidence accepted'


@pytest.mark.parametrize('golden', [
    VIEW_ROOT + '__tests__/f131_priority_ranking_glossary.test.ts',
    'platform-mcp/src/tools/kala_views/f171_disclosure_receipt_regression.test.ts',
])
def test_priority_requires_each_specialized_golden(monkeypatch, golden):
    mapping = copy.deepcopy(tulana.CERTIFICATION_MAPPING)
    mapping['views']['priority']['fidelity_tests'].remove(golden)
    monkeypatch.setattr(tulana, 'CERTIFICATION_MAPPING', mapping)
    assert tulana.validate_certification_mapping(ROOT), 'specialized PRIORITY golden lost'


@pytest.mark.parametrize('criterion', [
    'Build.contract', 'Idem.pattern', 'Dens.served', 'Narr.agree',
    'Narr.checkable', 'Narr.fidelity_test', 'Narr.lint', 'Null.schema_default',
    'Null.blank_rows', 'Carr.D1', 'Carr.D2', 'Carr.D3', 'Earn.service_state',
])
def test_global_mapping_cannot_delete_required_detector(monkeypatch, criterion):
    mapping = copy.deepcopy(tulana.CERTIFICATION_MAPPING)
    mapping['detectors'].pop(criterion)
    monkeypatch.setattr(tulana, 'CERTIFICATION_MAPPING', mapping)
    assert tulana.validate_certification_mapping(ROOT), 'required detector silently lost'


@pytest.fixture
def registrar_copy(tmp_path):
    mapping = json.loads((ROOT / registrar.MAPPING_PATH).read_text())
    paths = [registrar.MAPPING_PATH, Path('platform/scripts/governance/asset_census.py')]
    paths += [Path('platform/python-sidecar') / ref.split('::')[0]
              for ref in mapping['fidelity_tests']]
    # A real but unrelated pytest node is not the registrar's verbatim oracle.
    paths.append(Path('platform/python-sidecar/tests/l3/test_ka_tulana.py'))
    for path in paths:
        dest = tmp_path / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, dest)
    assert registrar.validate_certification_mapping(tmp_path) == []
    return tmp_path, mapping


def test_registrar_requires_verbatim_fidelity_binding(registrar_copy):
    root, mapping = registrar_copy
    mapping['fidelity_tests'] = ['tests/l3/test_ka_tulana.py::test_OpenElapsed']
    (root / registrar.MAPPING_PATH).write_text(json.dumps(mapping))
    assert registrar.validate_certification_mapping(root), 'unrelated real pytest node accepted'


def test_registrar_still_requires_all_gate_detectors(registrar_copy):
    root, mapping = registrar_copy
    mapping['gates']['Build']['revisions'].pop('Build.contract')
    (root / registrar.MAPPING_PATH).write_text(json.dumps(mapping))
    assert registrar.validate_certification_mapping(root), 'registrar detector silently lost'


def test_both_current_mappings_validate_without_awarding_certification():
    assert tulana.validate_certification_mapping(ROOT) == []
    assert registrar.validate_certification_mapping(ROOT) == []
