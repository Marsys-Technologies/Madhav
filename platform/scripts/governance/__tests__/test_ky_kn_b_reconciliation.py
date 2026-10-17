"""Offline KN-B readiness checks; this suite cannot close a tracker item."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / '00_ARCHITECTURE/briefs/kalayantra/evidence/kn_b_reconcile.py'
spec = importlib.util.spec_from_file_location('kn_b_reconcile', SCRIPT)
kn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kn)

ROLES = ('moorti_nirnaya', 'kota_chakra', 'tithi_pravesha', 'sudarshana_varsha', 'judge_vedha_wiring')


def admitted_fixture(tmp_path):
    # All identifiers, heads and receipts here are synthetic. Never register them.
    rows = [{'id': x, 'depends_on': []} for x in ('D-R8', 'J-0m', 'KA-3a')]
    children = []
    for index, role in enumerate(ROLES):
        item = 'fixture-' + role
        path = ('platform/python-sidecar/services/ka_' + role + '/candidate.py'
                if index < 4 else 'platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py')
        rows.append({'id': item, 'depends_on': ['KA-3a'],
                     'reviewer_rule': 'v_exact_head_then_post_deploy_at_merge_commit',
                     'brief': {'owns': [path]}})
        head = str(index + 1) * 40
        receipt = {'item': item, 'head': head, 'verdict': 'ACCEPTED',
                   'author': 'fixture-builder', 'reviewer': 'fixture-reviewer',
                   'state': 'done', 'merge_sha': 'a' * 40,
                   'readback_required': True, 'readback': {'head': 'a' * 40, 'verdict': 'ACCEPTED'}}
        rp = tmp_path / (item + '.json')
        rp.write_text(json.dumps(receipt))
        children.append({'role': role, 'item': item, 'head': head,
                         'receipt': {'path': str(rp), 'sha256': hashlib.sha256(rp.read_bytes()).hexdigest()}})
    rows += [{'id': 'KA-3b', 'depends_on': ['D-R8', 'J-0m', 'KA-3a'] + [r['item'] for r in children],
              'join': True, 'done_by': 'join'},
             {'id': 'consumer', 'depends_on': ['KA-3b']}]
    evidence = {'baseline_parent_dependencies': ['D-R8', 'J-0m', 'KA-3a'],
                'baseline_downstream_waiters': ['consumer'], 'children': children}
    return {'items': rows}, evidence


def test_complete_independent_children_and_wiring_have_no_offline_gaps(tmp_path):
    model, evidence = admitted_fixture(tmp_path)
    assert kn.reconcile(model, evidence) == []


@pytest.mark.parametrize('family_role', ROLES[:4])
@pytest.mark.parametrize('wiring_path', [
    'platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py',
    'platform/python-sidecar/services/gochara_kernel/overlays.py',
])
def test_family_and_independent_wiring_overlap_reports_gap_and_cli_failure(
        tmp_path, family_role, wiring_path):
    model, evidence = admitted_fixture(tmp_path)
    family_id = 'fixture-' + family_role
    wiring_id = 'fixture-judge_vedha_wiring'
    family = next(row for row in model['items'] if row['id'] == family_id)
    wiring = next(row for row in model['items'] if row['id'] == wiring_id)
    wiring['brief']['owns'] = [wiring_path]
    # The single-owner control differs only by the family claiming this path.
    model_path, evidence_path = tmp_path / 'model.json', tmp_path / 'evidence.json'
    evidence_path.write_text(json.dumps(evidence))
    command = [sys.executable, '-B', str(SCRIPT), '--model', str(model_path),
               '--evidence', str(evidence_path)]
    model_path.write_text(json.dumps(model))
    control = subprocess.run(command, capture_output=True, text=True, check=False)
    assert control.returncode == 0, control.stdout + control.stderr
    assert json.loads(control.stdout)['offline_gaps'] == []

    family['brief']['owns'].append(wiring_path)
    model_path.write_text(json.dumps(model))
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 1, result.stdout + result.stderr
    gaps = json.loads(result.stdout)['offline_gaps']
    assert any('ownership overlap' in gap and wiring_path in gap
               and family_id in gap and wiring_id in gap for gap in gaps)


@pytest.mark.parametrize('role', ROLES)
def test_missing_family_or_wiring_cannot_be_replaced_by_adapter_preacceptance(tmp_path, role):
    model, evidence = admitted_fixture(tmp_path)
    removed = next(c['item'] for c in evidence['children'] if c['role'] == role)
    evidence['children'] = [c for c in evidence['children'] if c['role'] != role]
    model['items'] = [r for r in model['items'] if r['id'] != removed]
    next(r for r in model['items'] if r['id'] == 'KA-3b')['depends_on'].remove(removed)
    assert any(role in gap for gap in kn.reconcile(model, evidence))


def test_duplicate_family_and_reused_child_are_rejected(tmp_path):
    model, evidence = admitted_fixture(tmp_path)
    extra = deepcopy(evidence['children'][0])
    extra['item'] = 'fixture-second-moorti'
    row = deepcopy(model['items'][3]); row['id'] = extra['item']; model['items'].append(row)
    next(r for r in model['items'] if r['id'] == 'KA-3b')['depends_on'].append(extra['item'])
    receipt = json.loads(Path(extra['receipt']['path']).read_text()); receipt['item'] = extra['item']
    path = tmp_path / 'duplicate-family.json'; path.write_text(json.dumps(receipt))
    extra['receipt'] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    evidence['children'].append(extra)
    assert any('duplicate role' in gap for gap in kn.reconcile(model, evidence))
    model, evidence = admitted_fixture(tmp_path)
    evidence['children'][1]['item'] = evidence['children'][0]['item']
    assert any('reused child' in gap for gap in kn.reconcile(model, evidence))


@pytest.mark.parametrize('mutation,reason', [
    ('parent_edge', 'original dependency'), ('downstream_edge', 'downstream'),
    ('child_edge', 'child dependency'), ('cycle', 'cycle'),
    ('duplicate_id', 'duplicate item'), ('unknown_dependency', 'unknown dependency'),
    ('branch_only', 'join'), ('mixed_family', 'ownership'),
    ('missing_item', 'unregistered'), ('carry_forward_cycle', 'cycle'),
])
def test_registration_rejects_lost_edges_cycles_and_branch_only_parent(tmp_path, mutation, reason):
    model, evidence = admitted_fixture(tmp_path)
    parent = next(r for r in model['items'] if r['id'] == 'KA-3b')
    if mutation == 'parent_edge': parent['depends_on'].remove('D-R8')
    elif mutation == 'downstream_edge': model['items'][-1]['depends_on'] = []
    elif mutation == 'child_edge': parent['depends_on'].remove(evidence['children'][0]['item'])
    elif mutation == 'cycle': model['items'][3]['depends_on'].append('KA-3b')
    elif mutation == 'duplicate_id': model['items'].append(deepcopy(model['items'][0]))
    elif mutation == 'unknown_dependency': parent['depends_on'].append('absent')
    elif mutation == 'branch_only': parent.pop('join'); parent.pop('done_by'); parent['detector'] = {'type': 'branch_merged'}
    elif mutation == 'mixed_family': model['items'][3]['brief']['owns'].append('platform/python-sidecar/services/ka_kota_chakra/other.py')
    elif mutation == 'missing_item': model['items'] = [r for r in model['items'] if r['id'] != evidence['children'][0]['item']]
    elif mutation == 'carry_forward_cycle':
        model['items'].append({'id': 'KA3B-N2', 'depends_on': ['KA-3b']})
        parent['depends_on'].append('KA3B-N2')
    assert any(reason in gap for gap in kn.reconcile(model, evidence))


@pytest.mark.parametrize('field,value,reason', [
    ('state', 'ready', 'done'), ('state', 'skipped', 'done'),
    ('verdict', 'REJECTED', 'ACCEPTED'), ('head', 'b' * 40, 'exact head'),
    ('reviewer', 'fixture-builder', 'independent'), ('merge_sha', '', 'merge'),
    ('readback', None, 'readback'),
])
def test_unearned_receipts_cannot_close_parent(tmp_path, field, value, reason):
    model, evidence = admitted_fixture(tmp_path)
    ref = evidence['children'][0]['receipt']
    path = Path(ref['path'])
    receipt = json.loads(path.read_text()); receipt[field] = value
    path.write_text(json.dumps(receipt)); ref['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert any(reason in gap for gap in kn.reconcile(model, evidence))


def test_missing_or_tampered_receipt_is_unavailable(tmp_path):
    model, evidence = admitted_fixture(tmp_path)
    ref = evidence['children'][0]['receipt']
    Path(ref['path']).write_text('{}')
    assert any('digest' in gap for gap in kn.reconcile(model, evidence))
    Path(ref['path']).unlink()
    assert any('missing' in gap for gap in kn.reconcile(model, evidence))


def test_original_builder_absence_is_not_replaced_by_independent_review(tmp_path):
    review = tmp_path / 'review.json'; review.write_text('{"mutations":8}')
    custody = {'original_builder': {'path': str(tmp_path / 'missing-builder/result.json'), 'sha256': None},
               'artifacts': [{'role': 'independent_review', 'path': str(review),
                              'sha256': hashlib.sha256(review.read_bytes()).hexdigest()}]}
    report = kn.inspect_custody(custody)
    assert report['original_builder_available'] is False
    assert report['artifact_errors'] == []
    review.write_text('{"mutations":9}')
    errors = kn.inspect_custody(custody)['artifact_errors']
    assert errors and 'digest' in errors[0]


def test_restored_builder_requires_known_digest_and_original_role(tmp_path):
    builder = tmp_path / 'builder.json'; builder.write_text('{}')
    custody = {'original_builder': {'path': str(builder), 'sha256': None}, 'artifacts': []}
    assert kn.inspect_custody(custody)['original_builder_available'] is False
    custody['original_builder']['sha256'] = hashlib.sha256(builder.read_bytes()).hexdigest()
    assert kn.inspect_custody(custody)['original_builder_available'] is True


def test_real_registration_stays_incomplete_without_inventing_children():
    model = json.loads((ROOT / '00_ARCHITECTURE/control/kalayantra/plan_model.json').read_text())
    evidence = json.loads((ROOT / '00_ARCHITECTURE/briefs/kalayantra/evidence/KN_B_PREBUILD_v1.json').read_text())
    gaps = kn.reconcile(model, evidence)
    # This snapshot intentionally supplies no child-completion receipts.
    assert all(any(role in gap for gap in gaps) for role in ROLES)


def test_unmapped_second_family_or_wiring_dependency_is_not_hidden(tmp_path):
    model, evidence = admitted_fixture(tmp_path)
    for original_index in (3, 7):
        candidate = deepcopy(model)
        extra = deepcopy(candidate['items'][original_index])
        extra['id'] = 'fixture-unmapped-extra'
        candidate['items'].append(extra)
        next(r for r in candidate['items'] if r['id'] == 'KA-3b')['depends_on'].append(extra['id'])
        assert any('unmapped family/wiring' in gap for gap in kn.reconcile(candidate, evidence))


def test_receipt_cannot_waive_model_required_postdeploy_readback(tmp_path):
    model, evidence = admitted_fixture(tmp_path)
    ref = evidence['children'][0]['receipt']; path = Path(ref['path'])
    receipt = json.loads(path.read_text()); receipt['readback_required'] = False; receipt['readback'] = None
    path.write_text(json.dumps(receipt)); ref['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert any('model-required readback' in gap for gap in kn.reconcile(model, evidence))
