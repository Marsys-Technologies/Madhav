"""K6-N2: validate private projection evidence, never award certification.

These files are preparation mappings. Legacy serving declarations and the K0a
assertion-slice mapping retain their distinct scopes. CI discovers this directory.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from services.kala_core.certification import (
    validate_detector_bindings, validate_fidelity_bindings,
)
from tests.l3.kala_db.ka_kalasutra.test_read_models import (
    ASSETS, CHART, GEN, WRITERS, ctx, db, planted,
)

ROOT = Path(__file__).resolve().parents[6]
SIDECAR = Path('platform/python-sidecar')
CONTRACT = SIDECAR / 'pipeline/orchestrator/writers/k6_candidate_contract.json'
PLAN = Path('00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md')
GATES = {'Build', 'Idem', 'Earn', 'Vocab', 'Ldgr', 'Dens', 'Narr', 'Null', 'Carr'}
DB_TEST = 'tests/l3/kala_db/ka_kalasutra/test_read_models.py::'
SPECS = {
    'ka_kalasutra': ('services/ka_kalasutra/certification_mapping.json',
        'kala_activation_candidate', 'kala_activation',
        'query_temporal_activation.ts:287', {
            DB_TEST + 'test_shared_contact_identity',
            DB_TEST + 'test_unsearched_interval_survives',
            DB_TEST + 'test_pd_testimony_is_never_scored',
            DB_TEST + 'test_ladder_has_no_eight_match_cap'}),
    'ka_jivana_parva': ('services/ka_jivana_parva/certification_mapping.json',
        'kala_jivana_parva_candidate', 'kala_jivana_parva',
        'query_life_arc.ts:159', {
            DB_TEST + 'test_ad_names_its_own_lord',
            DB_TEST + 'test_same_mechanism_condition_change_is_attributable',
            DB_TEST + 'test_lel_selection_circularity_guard'}),
    'ka_kala_darshana': ('services/kala_core/assertion/k6_certification_mapping.json',
        'kala_darshana_candidate', 'kala_darshana',
        'query_temporal_view.ts:87', {
            DB_TEST + 'test_darshana_retains_cancelled_negative_space_and_separate_valence',
            DB_TEST + 'test_missing_negative_mapping_stays_unavailable',
            DB_TEST + 'test_forecaster_zero_is_retained_separately',
            DB_TEST + 'test_coverage_gap_is_visible_without_judge',
            DB_TEST + 'test_no_top_750_truncation'}),
}


def mapping_oracle(root, asset, mapping):
    path, table, legacy, reader, fidelity = SPECS[asset]
    assert mapping['version'] == 'K6-123/K8-K6/v1'
    assert mapping['asset'] == asset
    assert mapping['scope'] == 'private_fixture_projection_only'
    assert mapping['production_certification'] is None
    assert mapping['k8_k6_complete'] is False
    assert mapping['produced_tables'] == [table]
    assert mapping['legacy_serving']['table'] == legacy
    assert mapping['legacy_serving']['evidence'].endswith(reader)
    source, line = mapping['legacy_serving']['evidence'].rsplit(':', 1)
    assert f'FROM {legacy}' in (root / source).read_text().splitlines()[int(line)-1]
    assert mapping['carriage']['nature'] == 'derivation'
    assert mapping['carriage']['served_surface'] == 'private candidate; no live serving claim'
    assert mapping['ldgr_source']['column'] == f'{table}.payload'
    assert mapping['ldgr_source']['payload_paths'] == {
        'ka_kalasutra': ['mechanism.provenance', 'judge.provenance', 'contact.provenance', 'context.provenance'],
        'ka_jivana_parva': ['period.provenance', 'judge[].provenance', 'jury[].provenance',
                            'negative_space[].provenance', 'lel[].provenance'],
        'ka_kala_darshana': ['judge.provenance', 'negative_space.provenance', 'jury[].provenance',
                             'forecaster[].provenance', 'context.provenance'],
    }[asset]
    assert mapping['provenance_columns'] == ['payload', 'upstream_refs']
    assert mapping['density_tier_columns'] == {table: 'tier'}
    assert mapping['stored_tiers'] == (['fixture_only'] if asset == 'ka_jivana_parva'
                                      else ['contextual', 'testimony', 'fixture_only'])
    assert mapping['live_tier_select'] is None
    assert mapping['prose_none'] is None  # copied dossier/source text can exist
    assert mapping['prose_fields'] is None  # full payload prose inventory unmeasured
    assert mapping['null_convention']['coverage'] == 'incomplete/absent requires reason'
    assert mapping['null_convention']['missing_negative_space'] == {
        'ka_kalasutra': 'not_consumed', 'ka_jivana_parva': 'empty_array',
        'ka_kala_darshana': 'information_unavailable',
    }[asset]
    assert mapping['semantic_fingerprint']['oracles'] == '; '.join(sorted(fidelity))
    assert mapping['semantic_fingerprint']['measured'] is False
    assert mapping['disposition'] == 'built, waiting on gate; private fixtures only'
    assert not validate_detector_bindings(root, mapping, gates=GATES)
    assert not validate_fidelity_bindings(root, mapping['fidelity_tests'], required=fidelity)
    for gate, evidence in mapping['gates'].items():
        assert evidence['verdict'] == ('NO_DETECTOR' if gate == 'Carr' else 'UNMEASURED')
        assert 'fixture' in evidence['expected_reading']
        assert 'PASS' not in evidence['expected_reading']
    fingerprint = mapping['semantic_fingerprint']
    assert fingerprint['inputs'] and fingerprint['outputs']
    assert mapping['fidelity_tests'] == sorted(fidelity)
    contract = json.loads((root / CONTRACT).read_text())
    assert contract['certification_mappings'][asset] == str(SIDECAR / path)
    assert table in contract['outputs']


@pytest.mark.parametrize('asset', SPECS)
def test_private_read_model_mapping_is_current_complete_and_unmeasured(asset):
    path = ROOT / SIDECAR / SPECS[asset][0]
    mapping_oracle(ROOT, asset, json.loads(path.read_text()))


@pytest.mark.parametrize('asset', SPECS)
def test_mapping_evidence_matches_private_sql_output(db, asset):
    """Read stored SQL results; declarations alone cannot establish provenance/tier."""
    path, table, *_ = SPECS[asset]
    mapping = json.loads((ROOT / SIDECAR / path).read_text())
    stored_tiers = set()
    for testimony in (False, True):
        value = planted()
        value['negative_space'] = []
        if testimony:
            value['windows'][0].update(operator_role='testimony', period_anchor=dict(
                system='vimshottari', level=3, lord='Mars', period_id='CODEX-PD-judge',
                no_prerequisite=False))
        WRITERS[ASSETS.index(asset)]().run(ctx(db, value))
        rows = db.execute(f'SELECT tier,payload,upstream_refs FROM {table} '
                          'WHERE chart_id=%s AND generation=%s', (CHART, GEN)).fetchall()
        assert rows
        for tier, payload, upstream in rows:
            stored_tiers.add(tier)
            assert upstream == value['upstream_refs']
            assert payload['acceptance_scope'] == 'fixture_only'
            embedded = [payload[key] for key in ('mechanism', 'period', 'context') if key in payload]
            judge = payload.get('judge')
            embedded += judge if isinstance(judge, list) else [judge] if judge else []
            assert embedded
            assert all(row['provenance'] == {
                'acceptance_scope': 'fixture_only', 'source_id': 'CODEX-input',
            } for row in embedded)
            if asset == 'ka_kala_darshana' and isinstance(judge, dict):
                assert payload['effective_state'] == mapping['null_convention']['missing_negative_space']
                assert payload['null_reason'] == 'negative_space_mapping_missing'
            elif asset == 'ka_jivana_parva':
                assert payload['negative_space'] == []
    assert stored_tiers == set(mapping['stored_tiers'])


@pytest.mark.parametrize('asset', SPECS)
@pytest.mark.parametrize('mutation', [
    'stale_revision', 'missing_gate', 'missing_criterion', 'legacy_output',
    'production_certificate', 'k8_complete', 'missing_provenance', 'invented_tier',
    'missing_null', 'empty_fingerprint', 'wrong_fidelity', 'unearned_gate',
    'wrong_none', 'missing_digest', 'unearned_no_prose', 'live_tier_claim',
])
def test_mapping_oracle_rejects_lost_or_unearned_evidence(asset, mutation):
    mapping = deepcopy(json.loads((ROOT / SIDECAR / SPECS[asset][0]).read_text()))
    if mutation == 'stale_revision':
        mapping['registry_revision'] -= 1
    elif mutation == 'missing_gate':
        del mapping['gates']['Null']
    elif mutation == 'missing_criterion':
        del mapping['gates']['Build']['revisions']['Build.contract']
    elif mutation == 'legacy_output':
        mapping['produced_tables'] = [SPECS[asset][2]]
    elif mutation == 'production_certificate':
        mapping['production_certification'] = 'PASS'
    elif mutation == 'k8_complete':
        mapping['k8_k6_complete'] = True
    elif mutation == 'missing_provenance':
        mapping['provenance_columns'] = []
    elif mutation == 'invented_tier':
        mapping['stored_tiers'] = ['verified']
    elif mutation == 'missing_null':
        del mapping['null_convention']['missing_negative_space']
    elif mutation == 'empty_fingerprint':
        mapping['semantic_fingerprint'] = {}
    elif mutation == 'wrong_fidelity':
        mapping['fidelity_tests'] = [DB_TEST + 'test_shared_contact_identity']
        mapping['semantic_fingerprint']['oracles'] = '; '.join(mapping['fidelity_tests'])
    elif mutation == 'unearned_gate':
        mapping['gates']['Dens']['verdict'] = 'PASS'
    elif mutation == 'wrong_none':
        mapping['gates']['Carr']['detector_none'] = []
    elif mutation == 'missing_digest':
        mapping['writer_digest'] = 'nonexistent'
    elif mutation == 'unearned_no_prose':
        mapping['prose_none'] = True
    elif mutation == 'live_tier_claim':
        mapping['live_tier_select'] = 'tier'
    with pytest.raises((AssertionError, KeyError)):
        mapping_oracle(ROOT, asset, mapping)


def test_plan_and_old_assertion_mapping_keep_acceptance_scopes_separate():
    plan = (ROOT / PLAN).read_text()
    assert 'K6-N2' in plan and 'registrar validation alone cannot complete K8-K6' in plan
    for path, *_ in SPECS.values():
        assert path in plan
    old = json.loads((ROOT / SIDECAR / 'services/kala_core/assertion/certification_mapping.json').read_text())
    assert old['version'] == 'K0a-4/v1' and old['registry_revision'] == 26
    assert old['scope'] == 'Implemented K0a manifest, obstruction axes and Darshana candidate columns; rehearsal evidence only.'
