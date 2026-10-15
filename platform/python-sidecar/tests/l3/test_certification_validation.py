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
    paths = [registrar.MAPPING_PATH, Path('platform/scripts/governance/asset_census.py'),
             Path('platform/src/generated/nirmana-writer-digests.json'),
             Path(VIEW_ROOT + 'query_projections.ts')]
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


# Exact production-data mutations from the independent K6-5 re-check,
# prior-review_steps.py:187-189 (X-20261015T173434Z-k6-5-certmap-step).
@pytest.mark.parametrize('field,value', [
    ('writer_digest', 'platform/src/generated/nonexistent.json:absent'),
    ('semantic_fingerprint', {}), ('carriage', {}), ('ldgr_source', {}),
    ('produced_tables', []), ('disposition', ''),
], ids=['writer_digest', 'semantic_fingerprint', 'carriage', 'ldgr_source',
        'produced_tables', 'disposition'])
def test_registrar_rejects_empty_contract_data(registrar_copy, field, value):
    root, mapping = registrar_copy
    mapping[field] = value
    (root / registrar.MAPPING_PATH).write_text(json.dumps(mapping))
    errors = registrar.validate_certification_mapping(root)
    assert any(field in error for error in errors), errors


@pytest.mark.parametrize('reading', ['PASS', 'EARNED', 'UNMEASURED', 'FAIL but PASS earned'])
def test_registrar_idem_reading_cannot_contradict_current_detector(registrar_copy, reading):
    root, mapping = registrar_copy
    mapping['gates']['Idem']['expected_reading'] = reading
    (root / registrar.MAPPING_PATH).write_text(json.dumps(mapping))
    errors = registrar.validate_certification_mapping(root)
    assert any('Idem' in error for error in errors), errors


@pytest.mark.parametrize('field,value', [
    ('writer_digest', ''),
    ('writer_digest', 'platform/src/generated/nirmana-writer-digests.json:absent'),
    ('writer_digest', 'platform/src/generated/nirmana-writer-digests.json:ka_tulana'),
    ('semantic_fingerprint', {'inputs': ' ', 'outputs': 'x', 'oracles': 'x'}),
    ('semantic_fingerprint', 'not an object'),
    ('carriage', {'nature': 'source'}),
    ('carriage', {'nature': 'source', 'served_surface': ' ', 'evidence': 'x:1'}),
    ('ldgr_source', {'column': 'falsifier.provenance', 'state': ' '}),
    ('produced_tables', ['']), ('produced_tables', 'issued_forecast'),
    ('disposition', ' \n'),
])
def test_registrar_rejects_malformed_contract_values(registrar_copy, field, value):
    root, mapping = registrar_copy
    mapping[field] = value
    (root / registrar.MAPPING_PATH).write_text(json.dumps(mapping))
    errors = registrar.validate_certification_mapping(root)
    assert any(field in error for error in errors), errors


# CERTMAP-GAPS-R1: retain every formerly required token while contradicting
# the disposition later in the reading (including the exact review probe).
@pytest.mark.parametrize('reading', [
    'FAIL under the prior Idem.pattern detector; R-10 is resolved. '
    'The current Idem.pattern verdict is PASS and certification is earned.',
    'FAIL under current Idem.pattern detector; R-10. '
    'The current detector now passes.',
    'FAIL under current Idem.pattern detector; R-10.\n'
    'Certification is earned under the current detector.',
    None,
], ids=['review_probe', 'later_passes', 'later_earned', 'append_to_valid'])
def test_registrar_rejects_later_contradictory_idem_claim(registrar_copy, reading):
    root, mapping = registrar_copy
    if reading is None:
        reading = (mapping['gates']['Idem']['expected_reading']
                   + ' The current Idem.pattern verdict is PASS.')
    mapping['gates']['Idem']['expected_reading'] = reading
    (root / registrar.MAPPING_PATH).write_text(json.dumps(mapping))
    errors = registrar.validate_certification_mapping(root)
    assert any('Idem' in error for error in errors), errors
