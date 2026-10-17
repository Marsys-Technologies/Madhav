"""Review custody resolves source locators and declares historical scope excursions."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CORRECTIONS = ROOT / '00_ARCHITECTURE/briefs/kalayantra/evidence/nb_kala/scope_corrections.json'
CONCEPT = '00_ARCHITECTURE/briefs/l3_families/KALA_PIPELINE_CONCEPT_NOTE_v1_1.md'


def test_k1_k6_authoritative_locator_resolves_to_the_preserved_source():
    items = json.loads((ROOT / '00_ARCHITECTURE/control/kalayantra/plan_model.json').read_text())['items']
    item = next(item for item in items if item['id'] == 'K5-G1b')
    locators = [locator for locator in item['brief']['spec'] if 'KALA_PIPELINE_CONCEPT_NOTE' in locator]
    assert locators and all(locator.startswith(CONCEPT + ' ') for locator in locators)
    assert (ROOT / CONCEPT).is_file(), 'authoritative concept note must be retained in the governed tree'
    receipt = json.loads((CORRECTIONS.parent / 'concept_note_source.json').read_text())
    assert receipt['path'] == CONCEPT
    assert receipt['source_commit'] == 'fbbbb94148ff91434e731f0f28a5a1bae5df09c0'
    assert hashlib.sha256((ROOT / CONCEPT).read_bytes()).hexdigest() == receipt['sha256']


def test_historical_scope_corrections_cover_every_accepted_excursion():
    assert CORRECTIONS.is_file(), 'read-only original results need a governed additive correction'
    records = json.loads(CORRECTIONS.read_text())['corrections']
    expected = {
        'JGT-NB-01-R1': {'platform/python-sidecar/tests/l3/kala_db/test_gochara_materializer_timeout.py'},
        'K64-NB-02-R01': {'platform/python-sidecar/tests/l3/kala_db/ka_taranga/test_monthly.py',
            'platform/src/generated/nirmana-writer-digests.json',
            'platform/src/generated/capability_estate_census.json'},
    }
    assert {r['finding'] for r in records} == set(expected)
    for record in records:
        assert record['original_out_of_owns'] == []
        assert len(record['original_result_sha256']) == 64
        assert record['source_job'] in record['original_result']
        excursions = {row['path']: row['why'] for row in record['out_of_owns']}
        assert set(excursions) == expected[record['finding']]
        assert all(reason.strip() for reason in excursions.values())
        assert set(excursions) == set(record['changed_paths']) - set(record['child_owned_changed_paths'])
        assert record['rewrites_historical_result'] is False


def test_followups_are_registered_without_completing_their_parents():
    items = {item['id']: item for item in json.loads(
        (ROOT / '00_ARCHITECTURE/control/kalayantra/plan_model.json').read_text())['items']}
    sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
    from pravaha_tracker.server import check_model
    plan = json.loads((ROOT / '00_ARCHITECTURE/control/kalayantra/plan_model.json').read_text())
    assert check_model(plan) == []
    parents = {'JGT-NB-01-R1':'JGT-NB-01', 'K64-NB-02-R01':'K64-NB-02',
        'K5-G1A-NB-01':'K5-G1a', 'KCERT-NB-01':'K-CERT',
        'K5G1B-ORACLES-NB01':'K5-G1b', 'K5G1B-ORACLES-NB02':'K5-G1b',
        'K5G1B-ORACLES-NB03':'K5-G1b', 'K9-23-N2-NB':'K9-23-N2'}
    for finding, parent in parents.items():
        assert finding in items, finding
        child = items[finding]
        assert child['depends_on'] == [parent]
        assert child['track'] == items[parent]['track']
        assert finding not in items[parent]['depends_on']
        assert child['mandatory'] is True and child['completion_kind'] == 'code'
        assert child['detector'] == {'type':'branch_merged', 'ref':'origin/kalayantra/nb-kala'}
        assert child['reviewer_rule'] == 'v_exact_head_then_deploy_containment'
        assert 'status' not in child and 'steps' not in child
        assert finding in items['JOIN-ALL']['depends_on']


def test_bounded_parent_dependencies_are_exact_and_executor_operations_stay_disabled():
    receipt = CORRECTIONS.parent / 'source_imports.json'
    assert receipt.is_file(), 'accepted parent dependency imports need exact source-byte receipts'
    sources = json.loads(receipt.read_text())['sources']
    assert {row['path'] for row in sources} == {
        'platform/python-sidecar/services/kala_core/publication.py',
        'platform-mcp/src/tools/retrieval/register_gochara_windows_kcert_assessment.test.ts'}
    for row in sources:
        assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256']
        assert len(row['source_commit']) == 40 and row['byte_exact'] is True
    ops = json.loads((ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json').read_text())['ops']
    for name in ('orchestrator_rebuild_dryrun','orchestrator_rebuild','layer_verify','layer_publish','layer_rollback'):
        assert ops[name]['enabled'] is False
