"""KA-4b preparation mapping oracle; production certification remains unearned.

Authority: plan_model.json KA-4b.certification_mapping; packet §6 N1–N5.
SR-A4-01 permits pre-build; L0-M admission and consumer acceptance remain owed.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT, is_verified
from services.kala_core.certification import (
    REGISTRY_PATH, validate_detector_bindings, validate_fidelity_bindings,
)

ROOT = Path(__file__).resolve().parents[5]
SIDECAR = Path('platform/python-sidecar')
MAPPING = SIDECAR / 'services/ka_muhurta_seva/certification_mapping.json'
EVAL = 'services/ka_muhurta_seva/parihara_eval.py'
ROUTE = 'routers/parihara_evaluate.py'
UNIT = 'tests/l3/ka_muhurta_seva/'
DB = 'tests/l3/kala_db/ka_muhurta_seva/test_parihara_db.py::'
GATES = frozenset({'Build', 'Idem', 'Earn', 'Vocab', 'Ldgr', 'Dens', 'Narr', 'Null', 'Carr'})

# Independent requirements: (real detector, exact tests, epistemic limitation).
# Changing the mapping cannot shrink this inventory or substitute an unrelated test.
CLAIMS = {
    'cited_cancellation': (EVAL + '::evaluate_candidate', [
        UNIT + 'test_parihara_eval.py::test_marriage_cited_cancellation_and_exact_metadata',
    ], 'Synthetic sky and typed rules; not admitted production cancellation.'),
    'undertaking_scope': (EVAL + '::scopes_for', [
        UNIT + 'test_parihara_eval.py::test_exact_scope_map_no_natal_or_muhurta_fallback',
        UNIT + 'test_parihara_eval.py::test_business_excludes_marriage_only_rule',
    ], 'Explicit undertaking map only; no event-class inference.'),
    'recursive_predicates': (EVAL + '::_predicate', [
        UNIT + 'test_parihara_eval.py::test_recursive_grammar',
    ], 'Allowlisted grammar; no prose-to-predicate extraction.'),
    'unknown_is_unassessed': (EVAL + '::_term_value', [
        UNIT + 'test_parihara_eval.py::test_unknowns_never_cancel_or_earn_residual',
    ], 'Undefined strength, agents and predicates remain unknown.'),
    'sample_changes': (EVAL + '::_predicate', [
        UNIT + 'test_parihara_eval.py::test_three_sample_term_changes_do_not_clear_even_when_any_of_stays_true',
        UNIT + 'test_mars_v88_readings.py::test_mars_v88_changing_combustion_cannot_become_agreement',
    ], 'Start/mid/end samples detect observed changes; no continuity or interval splitting proof.'),
    'coordinate_frame': (EVAL + '::_term_value', [
        UNIT + 'test_parihara_eval.py::test_independent_frame_goldens',
    ], 'Planted frame goldens; no second independent sky engine.'),
    'combustion': (EVAL + '::_term_value', [
        UNIT + 'test_parihara_eval.py::test_combustion_reads_l0_orbs_and_short_arc',
    ], 'Boundary goldens use existing L0 orbs; no new classical authority.'),
    'sky_identity': (EVAL + '::_valid_sky', [
        UNIT + 'test_parihara_eval.py::test_coverage_requires_real_backend_body_and_each_instant',
    ], 'Coverage and instant/backend checks, not independent ephemeris verification.'),
    'v88_conflict': (EVAL + '::_dosha', [
        UNIT + 'test_parihara_eval.py::test_v88_disagreement_retains_both_citations_and_blocks_unrelated_cancellation',
        UNIT + 'test_parihara_eval.py::test_source_pair_unknown_is_not_treated_as_agreement',
        UNIT + 'test_parihara_eval.py::test_other_verses_in_the_same_chunk_do_not_count_as_v88_readings',
        UNIT + 'test_parihara_verse_locator.py::test_v88_conflict_uses_explicit_locator_not_display_citation',
        UNIT + 'test_parihara_verse_locator.py::test_display_v88_and_shared_chunk_cannot_override_cross_verse_locators',
        UNIT + 'test_parihara_verse_locator.py::test_verse_88_still_requires_the_exact_source_reading_pair',
        UNIT + 'test_parihara_verse_locator.py::test_explicit_v88_unknown_reading_does_not_earn_agreement',
    ], 'Synthetic reducer outcomes only; real kartari agents and source reading remain unqualified.'),
    'mars_v88_readings': (EVAL + '::_dosha', [
        UNIT + 'test_mars_v88_readings.py::test_mars_v88_readings_are_evaluated_and_cited_separately',
        UNIT + 'test_mars_v88_readings.py::test_mars_v88_preserves_literal_preparation_reading',
        DB + 'test_mars_v88_disagreement_survives_read_only_source_roundtrip',
    ], 'Synthetic controls and guarded fixture roundtrip preserve literal and reconstructed readings; neither translation is selected and no L0-M admission is asserted.'),
    'source_locator': (EVAL + '::_rule', [
        UNIT + 'test_parihara_verse_locator.py::test_invalid_or_missing_verse_locator_cannot_earn_a_rule_verdict',
        UNIT + 'test_parihara_verse_locator.py::test_display_citation_is_preserved_alongside_explicit_locator',
        UNIT + 'test_parihara_verse_locator.py::test_missing_locator_cannot_bypass_a_potential_reading_conflict',
        UNIT + 'test_parihara_eval.py::test_unsourced_never_cancelled_cannot_earn_a_verdict',
    ], 'Positive typed verse and exact reading pair; display citation is preserved, not parsed.'),
    'state_reduction': (EVAL + '::_dosha', [
        UNIT + 'test_parihara_eval.py::test_state_reduction',
        UNIT + 'test_parihara_eval.py::test_never_cancelled_overrides_applies',
    ], 'Explicit applies/does_not_apply/unknown rule states; no ranking or subtraction.'),
    'source_text_fidelity': (UNIT + 'test_parihara_eval.py::test_source_fixtures_resolve_verbatim_not_from_memory', [
        UNIT + 'test_parihara_eval.py::test_source_fixtures_resolve_verbatim_not_from_memory',
    ], 'Fixture quotation fidelity only; does not select either v.88 reading or admit L0-M rows.'),
    'fact_carriage': (EVAL + '::_sample', [
        UNIT + 'test_parihara_eval.py::test_real_swiss_facts_roundtrip_without_recomputing_source_values',
    ], 'Real Swiss relay fidelity and house calculation; same backend is not a second pass.'),
    'ephemeris_gap': (EVAL + '::_sample', [
        UNIT + 'test_parihara_eval.py::test_missing_ephemeris_files_never_fall_back_to_moshier',
    ], 'Absent pinned corpus yields sky_coverage_gap; no stand-in.'),
    'request_validation': (ROUTE + '::PariharaRequest', [
        UNIT + 'test_parihara_evaluate.py::test_invalid_inputs_refused_before_db',
        UNIT + 'test_parihara_evaluate.py::test_valid_request_roundtrips_caller_and_reference_origin',
    ], 'HTTP contract and disclosed origin; consumer adapters are not exercised.'),
    'authentication': ('main.py::verify_api_key', [
        UNIT + 'test_parihara_evaluate.py::test_main_mount_refuses_missing_or_wrong_key_before_db',
    ], 'Actual guarded mount AST in a local app; no deployed authentication claim.'),
    'source_unavailable': (ROUTE + '::parihara_evaluate', [
        UNIT + 'test_parihara_evaluate.py::test_schema_or_db_error_refuses_instead_of_empty_residual',
        DB + 'test_missing_typed_schema_is_loud_not_no_rules',
    ], 'Absent typed schema refuses; schema admission and production readback remain owed.'),
    'scoped_sql': (EVAL + '::load_rules', [
        DB + 'test_scoped_read_only_source_roundtrip_and_unknown_readings',
    ], 'Guarded disposable database with fixture rows; no production database proof.'),
    'read_only_connection': (ROUTE + '::_connect', [
        DB + 'test_real_route_connection_is_read_only',
    ], 'Real read-only transaction in a guarded disposable database.'),
}
UNMEASURED = {
    'interval_continuity': 'Three samples do not prove continuity or split candidate boundaries.',
    'l0_m_admission': 'Accepted typed L0-M rows, doctrine qualification and coordinated reseal remain prerequisites.',
    'elect_consumer_integration': 'Election registry/alias, budget, legacy shape and served prose integration remain unmeasured.',
    'production_readback': 'No production build, deployment containment or independent certification receipt is asserted.',
}
# The shared service contract has established ranking fields. Explicit N/A
# readings keep this evaluator honest without changing/forking that validator.
CONTRACT = {
    'version': 'KA-4b/certification_mapping/v1',
    'status': 'PREBUILD_SR_A4_01',
    'item': 'KA-4b',
    'asset_id': 'ka_muhurta_seva',
    'kind': 'service',
    'scope': 'Scoped parihara evaluator preparation only; completion recorded after L0-M.',
    'carriage': {'nature': 'computation',
                 'served_call': 'platform/python-sidecar/routers/parihara_evaluate.py:72',
                 'served_surface': 'POST /api/compute/parihara_evaluate (prepared route; no ELECT integration)'},
    'ldgr_source': None,
    'vocab_alias': None,
    'prose_fields': None,
    'produced_tables': [],
    'density_tier_columns': None,
    'writer_digest_entry': 'platform/src/generated/nirmana-writer-digests.json#/writers/ka_muhurta_seva',
    'semantic_fingerprint': {
        'contract_version': 'parihara_evaluate/1',
        'axes': ['undertaking_scope', 'typed_predicate', 'start_mid_end_samples'],
        'dominance': 'Not applicable: no composite score or ranking.',
        'front': 'Explicit per-dosha states and by_rules; no Pareto front.',
        'ordering': 'Input dosha order deduplicated; rules ordered by target, cancellation_index, id.',
        'live_jury_binding': 'Not applicable; L0-M source admission and ELECT consumer binding unadmitted.',
        'fixed_weights': False,
    },
    'null_convention': 'Unknown predicates, source locators, scope and sky coverage preserve named unassessed reasons; no invented clearance.',
    'disposition': 'Preparation evidence only; no whole-asset, census, consumer or production PASS.',
    'production_certification': None,
    'completion_after': 'L0-M',
    'interpretations': [
        '(I) INTERPRETATION I1: single-pass tiers describe bounded fixture/relay evidence only; all live, consumer and interval-continuity claims remain null.',
        '(I) INTERPRETATION I2: use the unchanged shared K8 service contract fields with explicit no-ranking/not-applicable readings; registry gate verdicts remain UNMEASURED or NO_DETECTOR.',
    ],
}
FINGERPRINT_PATHS = {
    SIDECAR / EVAL, SIDECAR / ROUTE, SIDECAR / 'main.py',
    SIDECAR / UNIT / 'conftest.py', SIDECAR / UNIT / 'parihara_predicates.json',
    SIDECAR / 'tests/l3/kala_db/conftest.py',
    SIDECAR / 'tests/l3/_disposable_db_guard.py',
    Path('platform/scripts/corpus/data/muhurta_chintamani_translations.json'),
    SIDECAR / 'services/kala_core/sky/ephemeris.py',
    SIDECAR / 'brahmagyan/verification_vocab.py',
    SIDECAR / 'services/kala_core/certification.py', REGISTRY_PATH,
} | {SIDECAR / ref.split('::')[0] for _, refs, _ in CLAIMS.values() for ref in refs}


def certification_mapping_oracle(root: Path):
    """Unchanged positive oracle over real mapping data, including copy mutations."""
    mapping = json.loads((root / MAPPING).read_text())
    assert set(mapping) == set(CONTRACT) | {'registry_revision', 'gates', 'claims', 'unmeasured', 'hashes'}
    for field, expected in CONTRACT.items():
        assert mapping[field] == expected, field
    # Shared grouped validation checks revisions/NONE. Pin expected readings too:
    # fixture evidence is never permission to invent a census verdict.
    assert set(mapping['gates']) == GATES
    for gate, evidence in mapping['gates'].items():
        assert set(evidence) == {'revisions', 'expected_reading', 'detector_none', 'detector_dependency'}
        none = evidence['detector_none']
        expected = ('NO_DETECTOR: ' + ', '.join(sorted(none)) + '; ' if none else '')
        expected += 'UNMEASURED: offline evaluator preparation only; no census or production PASS.'
        assert evidence['expected_reading'] == expected, gate
        assert evidence['detector_dependency'] == ('Current registry has no detector; later implementation required.' if none else None)
    assert set(mapping['claims']) == set(CLAIMS)
    for name, (detector, tests, limitation) in CLAIMS.items():
        claim = mapping['claims'][name]
        assert set(claim) == {'detector', 'source', 'tests', 'tier', 'limitation'}
        assert claim['detector'] == detector, name
        assert claim['tests'] == tests, name
        assert claim['limitation'] == limitation, name
        assert claim['tier'] == UNVERIFIED_DEFAULT and not is_verified(claim['tier']), name
        assert validate_fidelity_bindings(root, claim['tests'], required=tests) == [], name
        file, symbol = detector.split('::')
        tree = ast.parse((root / SIDECAR / file).read_text())
        node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == symbol)
        assert claim['source'] == f'{SIDECAR / file}:{node.lineno}', name
    assert mapping['unmeasured'] == {
        name: {'detector': None, 'tests': [], 'tier': None, 'reason': reason}
        for name, reason in UNMEASURED.items()
    }
    assert set(mapping['hashes']) == {str(p) for p in FINGERPRINT_PATHS}
    for file, digest in mapping['hashes'].items():
        assert hashlib.sha256((root / file).read_bytes()).hexdigest() == digest, file
    assert validate_detector_bindings(root, mapping, gates=GATES) == []


def test_committed_certification_mapping_is_current_and_unmeasured():
    certification_mapping_oracle(ROOT)


@pytest.fixture
def evidence_copy(tmp_path):
    for path in FINGERPRINT_PATHS | {MAPPING, Path('platform/src/generated/nirmana-writer-digests.json')}:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    return tmp_path


@pytest.mark.parametrize('mutation', [
    'deleted_mapping', 'deleted_claim', 'valid_wrong_test', 'unearned_tier',
    'null_tier', 'stale_revision', 'wrong_hash', 'no_detector_claim',
    'unearned_production', 'dropped_unknown', 'false_census_pass',
])
def test_oracle_rejects_mutated_mapping_copy(evidence_copy, mutation):
    certification_mapping_oracle(evidence_copy)
    path = evidence_copy / MAPPING
    data = json.loads(path.read_text())
    if mutation == 'deleted_mapping':
        path.unlink()
    elif mutation == 'deleted_claim':
        data['claims'].pop('undertaking_scope')
    elif mutation == 'valid_wrong_test':
        data['claims']['undertaking_scope']['tests'] = data['claims']['cited_cancellation']['tests']
    elif mutation == 'unearned_tier':
        from brahmagyan.verification_vocab import TWO_PASS_VERIFIED
        data['claims']['fact_carriage']['tier'] = TWO_PASS_VERIFIED
    elif mutation == 'null_tier':
        data['claims']['scoped_sql']['tier'] = None
    elif mutation == 'stale_revision':
        data['registry_revision'] = 0
    elif mutation == 'wrong_hash':
        data['hashes'][str(SIDECAR / EVAL)] = '0' * 64
    elif mutation == 'no_detector_claim':
        data['claims']['sky_identity']['detector'] = None
    elif mutation == 'unearned_production':
        data['production_certification'] = 'PASS'
    elif mutation == 'dropped_unknown':
        data['unmeasured'].pop('l0_m_admission')
    elif mutation == 'false_census_pass':
        data['gates']['Earn']['expected_reading'] = 'PASS'
    if mutation != 'deleted_mapping':
        path.write_text(json.dumps(data))
    with pytest.raises((AssertionError, FileNotFoundError)):
        certification_mapping_oracle(evidence_copy)


def test_mapping_runs_in_mandatory_governance_and_evaluator_ci():
    """Omitting this oracle from mandatory CI must be observable."""
    import yaml
    jobs = _ci_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    shard = jobs['governance-gates-py-sidecar-shard']
    runs = [step.get('run', '') for step in shard['steps']]
    assert any('tests/l3/test_certification_validation.py' in run
               and 'tests/l3/ka_muhurta_seva/test_certification_mapping.py' in run
               for run in runs)
    assert not shard.get('continue-on-error')
    aggregate = jobs['governance-gates']
    assert 'full-suite' in aggregate['needs']
    assert 'governance-gates-py-sidecar-shard' in jobs['full-suite']['needs']
    assert 'always()' in aggregate['if']
    assert not aggregate.get('continue-on-error')
    assert any('tests/l3/ka_muhurta_seva -q' in step.get('run', '')
               for step in jobs['kala-db-tests']['steps'])

from pathlib import Path as _CiPath
import sys as _ci_sys
_ci_sys.path.insert(0, str(_CiPath(__file__).resolve().parents[5] / 'platform/scripts/governance'))
from ci_discovery import expanded_workflow as _ci_expanded

def _ci_load(text):
    import yaml
    data = yaml.safe_load(text)
    data['jobs'] = _ci_expanded(data['jobs'])
    return data
