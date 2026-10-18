"""K6-N1: the consumer contracts must describe the merged preparation paths."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[6]
REGISTRAR = Path('00_ARCHITECTURE/briefs/l3_families/contracts/REGISTRAR_INPUT_OUTPUT_CONTRACT_v1_0.md')
READ_MODELS = Path('platform/python-sidecar/pipeline/orchestrator/writers/k6_candidate_contract.json')


def registrar_contract(root):
    text = ' '.join((root / REGISTRAR).read_text().split())
    assert 'version: "1.1"' in text
    for required in (
        '`registrar_inputs`', '`registrar_fixture_inputs`',
        'default append-only registrar', 'no SQL', 'no_delivery_inputs',
        '_LegacyKaBhavishyaLekhaWriter', 'historical safety oracles only',
        'jury_reader_generation', 'takes precedence',
        'issued_forecast', 'fixture', 'live', 'phala_anchors',
        'never updates, reclassifies or deletes', 'Idem', 'R-10',
    ):
        assert required in text, f'missing registrar contract: {required}'
    assert 'default writer continues legacy computation' not in text
    assert 'protective read remains required until' not in text


def integrity_contract(root):
    contract = json.loads((root / READ_MODELS).read_text())
    assert contract['contract_version'] == 'k6-123:read-models:v2'
    # The document is versioned separately from the unchanged payload schema.
    assert contract['projection_payload_version'] == 'k6-123:read-models:v1'
    target = contract['integrity_target']
    assert target['scope'] == 'exact_transaction_bound_chart_and_build'
    assert target['settings'] == ['kala.integrity_chart_id', 'kala.integrity_build_id']
    assert target['transaction_local'] is True
    assert target['standalone_requires_explicit_pins'] is True
    assert target['missing_or_mismatched_pins'] == 'false'
    assert target['valid_after_completion'] is True
    assert target['legacy_else_preserved'] is True
    assert 'bind_integrity_target(ctx)' in target['standalone']
    assert 'set_config' in target['standalone']
    assert 'integrity_check_sql scopes the latest build' not in contract['storage']
    assert 'unchanged legacy writer dispatch' in contract['entry']
    assert contract['live_bindings']['state'] == 'information_unavailable'
    assert len(contract['live_bindings']['reasons']) == 6
    assert 'fixture_only' in contract['acceptance_scope']
    assert 'K9-4b' in contract['acceptance_scope']


def test_registrar_contract_matches_default_and_historical_boundaries():
    registrar_contract(ROOT)


def test_read_model_contract_requires_exact_transaction_integrity_pins():
    integrity_contract(ROOT)


@pytest.mark.parametrize('scope', ['latest_build', 'latest_chart_build'])
def test_contract_oracle_rejects_superseded_integrity_target(tmp_path, scope):
    contract = json.loads((ROOT / READ_MODELS).read_text())
    contract['integrity_target']['scope'] = scope
    target = tmp_path / READ_MODELS
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(contract))
    with pytest.raises(AssertionError):
        integrity_contract(tmp_path)


@pytest.mark.parametrize('field,value', [
    ('transaction_local', False), ('standalone_requires_explicit_pins', False),
    ('missing_or_mismatched_pins', 'true'), ('valid_after_completion', False),
    ('legacy_else_preserved', False), ('settings', ['latest_build']),
])
def test_contract_oracle_rejects_lost_integrity_guarantee(tmp_path, field, value):
    contract = json.loads((ROOT / READ_MODELS).read_text())
    contract['integrity_target'][field] = value
    target = tmp_path / READ_MODELS
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(contract))
    with pytest.raises(AssertionError):
        integrity_contract(tmp_path)


def test_contract_oracle_rejects_legacy_default(tmp_path):
    text = (ROOT / REGISTRAR).read_text()
    target = tmp_path / REGISTRAR
    target.parent.mkdir(parents=True)
    target.write_text(text + '\nThe default writer continues legacy computation.\n')
    with pytest.raises(AssertionError):
        registrar_contract(tmp_path)
