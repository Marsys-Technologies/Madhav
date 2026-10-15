"""Offline K8 evidence; never awards a production certificate."""
import json
from pathlib import Path
from services.kala_core.certification import validate_detector_bindings, validate_fidelity_bindings

MAPPING_PATH = Path('platform/python-sidecar/services/ka_kshetra/certification_mapping.json')
GATES = frozenset({'Build','Idem','Earn','Vocab','Ldgr','Dens','Narr','Null','Carr'})
FIDELITY = {'tests/l3/ka_kshetra/test_g1b_insights.py::test_normalized_promise_absence_is_typed_model_silence',
            'tests/l3/ka_kshetra/test_g1b_manifest.py::test_complete_dependency_digest_is_recomputed_for_each_mutation'}


def validate_mapping(root):
    try:
        mapping=json.loads((root/MAPPING_PATH).read_text())
        errors=[]
        required={'version','registry_revision','asset','kind','carriage','ldgr_source','vocab_alias',
                  'prose_fields','fidelity_tests','null_convention','produced_tables',
                  'density_tier_columns','semantic_fingerprint','writer_digest','disposition',
                  'production_certification','gates'}
        if not required <= mapping.keys(): errors.append('incomplete K8 mapping')
        if mapping.get('asset')!='ka_kshetra' or mapping.get('kind')!='data': errors.append('wrong identity')
        if mapping.get('production_certification') is not None: errors.append('unearned certificate')
        errors.extend(validate_detector_bindings(root,mapping,gates=GATES))
        errors.extend(validate_fidelity_bindings(root,mapping.get('fidelity_tests'),required=FIDELITY))
        return errors
    except (OSError,ValueError,TypeError,KeyError,StopIteration,SyntaxError,AttributeError) as exc:
        return ['mapping unavailable: '+str(exc)]
