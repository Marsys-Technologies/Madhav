"""K6-5 offline mapping verifier; the registrar never depends on repo evidence."""
from __future__ import annotations

import json
from pathlib import Path

from services.kala_core.certification import (
    REGISTRY_PATH, read_detector_registry, test_reference_exists,
)

MAPPING_PATH = Path('platform/python-sidecar/services/ka_bhavishya_lekha/certification_mapping.json')
GATES = frozenset({'Build', 'Idem', 'Earn', 'Vocab', 'Ldgr', 'Dens', 'Narr', 'Null', 'Carr'})


def validate_certification_mapping(root: Path) -> list[str]:
    """Refuse missing/stale K8 declarations and unearned production certification.

    (I) INTERPRETATION I1: K8's version-specific detector mapping is current
    only when every criterion in its nine active gates matches the registry.
    This validates evidence bindings, not the census verdicts or live admission.
    """
    errors = []
    try:
        mapping = json.loads((root / MAPPING_PATH).read_text())
        required = {'version', 'registry_revision', 'asset', 'kind', 'carriage',
                    'ldgr_source', 'vocab_alias', 'prose_fields', 'fidelity_tests',
                    'null_convention', 'produced_tables', 'density_tier_columns',
                    'semantic_fingerprint', 'writer_digest', 'disposition',
                    'production_certification', 'gates'}
        if not required <= mapping.keys():
            errors.append('missing K8 mapping declarations')
        if mapping.get('asset') != 'ka_bhavishya_lekha' or mapping.get('kind') != 'data':
            errors.append('wrong registrar identity/kind')
        if 'production_certification' not in mapping or mapping['production_certification'] is not None:
            errors.append('production certification must be explicitly null')
        revision, criteria = read_detector_registry(root / REGISTRY_PATH)
        if mapping.get('registry_revision') != revision:
            errors.append('stale detector registry revision')
        gates = mapping.get('gates', {})
        if set(gates) != GATES:
            errors.append('nine active gates required')
        for gate in GATES:
            evidence = gates.get(gate, {})
            expected = {key: value['revision'] for key, value in criteria.items()
                        if key.split('.')[0] == gate}
            if not expected or evidence.get('revisions') != expected:
                errors.append(f'missing/stale detector binding: {gate}')
            if not evidence.get('expected_reading'):
                errors.append(f'missing expected reading: {gate}')
            none = {key for key in expected if criteria[key]['detector'] == 'NONE'}
            if set(evidence.get('detector_none', [])) != none:
                errors.append(f'wrong NO_DETECTOR binding: {gate}')
            if none and ('NO_DETECTOR' not in evidence.get('expected_reading', '')
                         or not evidence.get('detector_dependency')):
                errors.append(f'missing NO_DETECTOR dependency: {gate}')
        if not mapping.get('fidelity_tests'):
            errors.append('fidelity evidence required')
        for reference in mapping.get('fidelity_tests', []):
            if not test_reference_exists(root / 'platform/python-sidecar', reference):
                errors.append(f'missing fidelity test: {reference}')
    except (OSError, ValueError, KeyError, StopIteration, TypeError, AttributeError, SyntaxError) as exc:
        errors.append(f'mapping source unavailable: {exc}')
    return errors
