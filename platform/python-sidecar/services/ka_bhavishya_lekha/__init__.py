"""K6-5 offline mapping verifier; the registrar never depends on repo evidence."""
from __future__ import annotations

import json
from pathlib import Path

from services.kala_core.certification import (
    validate_detector_bindings, validate_fidelity_bindings,
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
        errors.extend(validate_detector_bindings(root, mapping, gates=GATES))
        errors.extend(validate_fidelity_bindings(root, mapping.get('fidelity_tests'), required={
            'tests/l3/kala_db/ka_bhavishya_lekha/test_registrar.py::'
            'test_disconnected_intervals_and_verbatim_statement_survive',
        }))
    except (OSError, ValueError, KeyError, StopIteration, TypeError, AttributeError, SyntaxError) as exc:
        errors.append(f'mapping source unavailable: {exc}')
    return errors
