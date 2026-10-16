"""Bounded K-CERT artifact: real detector, immutable evidence, existing guard.

No live tracker events, remote service, database or production certification.
The package is a review input; only an independent artifact verdict can accept it.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

import pytest

GOV = Path(__file__).resolve().parents[1]
ROOT = GOV.parents[2]
sys.path.insert(0, str(GOV))

import asset_census as ac
from pravaha_tracker.completion import CompletionError, guarded_done_event
from pravaha_tracker.detectors import Detectors
from pravaha_tracker.state import build_snapshot

PACKAGE = ROOT / '00_ARCHITECTURE/briefs/kalayantra/evidence/kcert'
MODEL = ROOT / '00_ARCHITECTURE/control/kalayantra/plan_model.json'
ASSET = 'bg_gochara_citation_resolution'


@pytest.fixture
def binding():
    if not (PACKAGE / 'BINDING.json').is_file():
        return None
    return json.loads((PACKAGE / 'BINDING.json').read_text())


@pytest.fixture
def model():
    return json.loads(MODEL.read_text())


def item(model):
    return next(row for row in model['items'] if row['id'] == 'K-CERT')


def test_exact_assessment_and_executing_evidence_are_digest_bound(binding):
    assert binding is not None, 'K-CERT requires a digest-bound assessment package'
    assert binding['schema'] == 'ky.kcert_artifact/1'
    assert binding['item'] == 'K-CERT'
    assert binding['acceptance'] == 'pending_independent_artifact_digest_review'
    assert binding['assessment']['sha256'] == 'c2ef88286b21e6fd3a412bcc2033c266bad23dd8574bc6f64c12c56e3fbfa522'
    assert binding['evidence_anchor']['sha256'] == '47f7dff0585d4335d3d66807ece3f4f03df7b0466f3c4e246ed9903ece22af61'
    for record in [binding['assessment'], binding['evidence_anchor'], *binding['evidence']]:
        assert hashlib.sha256((PACKAGE / record['path']).read_bytes()).hexdigest() == record['sha256']
    original_hashes = json.loads((PACKAGE / binding['evidence_anchor']['path']).read_text())
    assert original_hashes['REVIEW.md']['sha256'] == binding['assessment']['sha256']
    for record in binding['evidence']:
        assert original_hashes[Path(record['path']).name]['sha256'] == record['sha256']
    assert binding['assessment_job'].endswith('/X-20261015T095803Z-kcert-assess')
    declaration = json.loads((GOV / 'asset_declarations.json').read_text())['assets'][ASSET]
    declaration_bytes = json.dumps(declaration, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    assert hashlib.sha256(declaration_bytes).hexdigest() == binding['declaration_entry_sha256']
    assert {r['path'] for r in binding['evidence']} >= {
        'evidence/source-pin.json', 'evidence/test-runs.json',
        'evidence/baseline.scanner.json', 'evidence/negative-selection.scanner.json',
        'evidence/negative-selection.patch', 'evidence/negative-selection.vitest.log',
        'evidence/db-catalog-scanner.json', 'evidence/db.test-run.json',
    }
    runs = json.loads((PACKAGE / 'evidence/test-runs.json').read_text())
    by_label = {r['label']: r for r in runs}
    assert by_label['baseline.vitest']['exit'] == by_label['baseline.scanner']['exit'] == 0
    assert by_label['negative-selection.vitest']['exit'] != 0
    assert by_label['negative-selection.scanner']['exit'] != 0
    baseline = json.loads((PACKAGE / 'evidence/baseline.scanner.json').read_text())
    negative = json.loads((PACKAGE / 'evidence/negative-selection.scanner.json').read_text())
    assert baseline['with_custodian_declaration']['grade']['v'] == 'PASS'
    assert baseline['without_declaration']['grade']['v'] != 'PASS'
    assert negative['with_custodian_declaration']['grade']['v'] != 'PASS'
    assert 'no tier column in its served select' in json.dumps(negative['with_custodian_declaration']['grade'])


@pytest.mark.parametrize('body,expected', [
    (None, 'pending'), ('', 'pending'),
    ('**K-CERT: NOT MET — bounded structural Dens.served.**', 'pending'),
    ('**K-CERT-2: MET — bounded structural Dens.served.**', 'pending'),
    ('**OTHER: MET — bounded structural Dens.served.**', 'pending'),
    ('**K-CERT: MET — production certified.**', 'pending'),
    ('quotation: **K-CERT: MET — bounded structural Dens.served.**', 'pending'),
    ('**K-CERT: MET — bounded structural Dens.served.**', 'done'),
])
def test_real_file_detector_requires_the_explicit_bounded_verdict(model, tmp_path, body, expected):
    path = tmp_path / 'assessment.md'
    if body is not None:
        path.write_text(body)
    # Call the synchronous detector directly; do not create its polling pool.
    result = Detectors.d_file_contains(None, {**item(model)['detector'], 'path': str(path)})
    assert result.status == expected


def test_pinned_assessment_matches_the_declared_detector(model, binding):
    spec = {**item(model)['detector'], 'path': str(PACKAGE / binding['assessment']['path'])}
    assert Detectors.d_file_contains(None, spec).status == 'done'


def completion_fixture(model, binding):
    # Use the actual declaration and prerequisites. Only their eligibility is
    # simulated; this is never an observation of live campaign completion.
    row = deepcopy(item(model))
    local = {**model, 'items': [row, *[{'id': dep, 'owner': 'S', 'track': row['track'], 'title': dep}
                                      for dep in row['depends_on']]]}
    events = [{'kind': 'item', 'item': dep, 'state': 'done', 'actor': 'stream-S:fixture',
               'guarded': True, 'ts': '2026-10-15T00:00:00Z'}
              for dep in row['depends_on']]
    verdict = {'kind': 'verdict', 'item': 'K-CERT', 'actor': 'stream-V:independent-fixture',
               'head': None, 'artifact_digest': binding['assessment']['sha256'],
               'phase': 'artifact', 'result': 'ACCEPTED', 'ts': '2026-10-16T00:00:00Z'}
    proof = {'type': 'artifact', 'artifact_digest': binding['assessment']['sha256']}
    return local, events, verdict, proof


def test_existing_guard_accepts_only_independent_exact_digest_after_dependencies(model, binding, tmp_path):
    local, events, verdict, proof = completion_fixture(model, binding)
    event = guarded_done_event(local, [*events, verdict], 'K-CERT', 'stream-K:fixture',
                               {'status': 'done'}, proof)
    assert event['completion']['artifact_digest'] == binding['assessment']['sha256']
    assert event['guarded'] is True
    changed = tmp_path / 'changed-assessment.md'
    changed.write_bytes((PACKAGE / binding['assessment']['path']).read_bytes() + b'\nChanged after review.\n')
    changed_digest = hashlib.sha256(changed.read_bytes()).hexdigest()
    assert Detectors.d_file_contains(None, {**item(model)['detector'], 'path': str(changed)}).status == 'done'
    for bad_events, bad_proof, detector in [
        (events, proof, {'status': 'done'}),  # file presence / MET alone
        ([*events, {**verdict, 'result': 'REJECTED'}], proof, {'status': 'done'}),
        ([*events, {**verdict, 'actor': 'stream-K:fixture'}], proof, {'status': 'done'}),
        ([*events, {**verdict, 'phase': 'pre_merge'}], proof, {'status': 'done'}),
        ([*events, verdict], {**proof, 'artifact_digest': '0' * 64}, {'status': 'done'}),
        ([*events, verdict], {**proof, 'artifact_digest': changed_digest}, {'status': 'done'}),
        ([*events, verdict], proof, {'status': 'pending'}),
        ([verdict], proof, {'status': 'done'}),
    ]:
        with pytest.raises(CompletionError):
            guarded_done_event(local, bad_events, 'K-CERT', 'stream-K:fixture', detector, bad_proof)


def test_retirement_is_limited_to_structural_prerequisite(model, binding):
    row = item(model)
    assert row['owner'] == row['producer'] == 'K'
    assert row['completion_kind'] == 'artifact'
    assert row['reviewer_rule'] == 'v_artifact_digest_reviewer_not_author'
    assert row['depends_on'] == ['B-7', 'K0-SV', 'J-4d-pr3145']
    assert binding['decision']['id'] == 'SR-A2-11'
    assert 'never migrated' in binding['decision']['record']['title']
    schema = next(r for r in model['items'] if r['id'] == 'KV3-SCHEMA-1')
    decision = 'D-KCERT-EXISTING-STATUS-20261015'
    assert schema['requires_outcome'] == {decision: 'approved'}
    assert schema['triage']['class'] == 'retired'
    snapshot = build_snapshot(model, [{'kind': 'decision', 'actor': 'steward',
        'decision': decision, 'state': 'decided', 'outcome': 'refused',
        'detail': 'SR-A2-11 fixture only', 'ts': '2026-10-16T00:00:00Z'}], {}, {}, {})
    status = next(r['status'] for track in snapshot['tracks'] for r in track['items']
                  if r['id'] == schema['id'])
    assert status == 'not_applicable'  # Retirement never claims a delivered migration.
    assert binding['scope'] == 'bounded structural Dens.served from stored citation-resolution status'
    assert binding['excluded_claims'] == ['new migration', 'computed-value verification',
                                          'prose verification', 'production certification',
                                          'K-CERT-2 completion', 'live tracker completion']


def test_current_source_earns_real_density_scanner_pass(monkeypatch):
    """Removing status from the served SELECT must make this baseline fail."""
    monkeypatch.setattr(ac, 'ROOT', ROOT)
    declaration = json.loads((GOV / 'asset_declarations.json').read_text())['assets'][ASSET]
    ddl = (ROOT / 'platform/supabase/migrations/565_bg_gochara_citation_resolution.sql').read_text()
    body = ddl.split('CREATE TABLE IF NOT EXISTS bg_gochara_citation_resolution (', 1)[1].split('\n);', 1)[0]
    columns = re.findall(r'^\s*(\w+)\s+(?:TEXT|TIMESTAMPTZ)\b', body, re.M | re.I)
    assert 'status' in columns and 'verification_pass_status' not in columns
    assert ac.density_tier_measure_problem(declaration, ASSET, columns) is None
    cap = ac.capability_scan(ac.CAPS_ROOTS, [ASSET], columns={ASSET: columns},
                             outside_roots=ac.DENS_OUTSIDE_ROOTS,
                             tier_declared={ASSET: [r['column'] for r in declaration['density_tier_columns']]})
    assert ac._grade_dens(cap, ASSET)['v'] == 'PASS'
