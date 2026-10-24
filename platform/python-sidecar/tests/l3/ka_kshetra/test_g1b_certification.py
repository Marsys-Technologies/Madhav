"""Current detector bindings, executable evidence, no fabricated certificate."""
from pathlib import Path
import json
import shutil
import copy
import pytest


@pytest.mark.parametrize('mutation', ['unearned_build', 'missing_manifest_output'])
def test_shared_validator_rejects_unearned_readings_and_incomplete_outputs(mutation):
    from services.kala_core.certification import validate_detector_bindings
    from services.ka_kshetra.g1_certification import MAPPING_PATH, GATES
    root = Path(__file__).resolve().parents[5]
    mapping = json.loads((root / MAPPING_PATH).read_text())
    assert validate_detector_bindings(root, mapping, gates=GATES) == []
    changed = copy.deepcopy(mapping)
    if mutation == 'unearned_build':
        changed['gates']['Build']['expected_reading'] = 'PASS'
    else:
        changed['produced_tables'].remove('kala_layer_candidate_grain')
    assert validate_detector_bindings(root, changed, gates=GATES)


def test_mapping_tracks_all_current_detectors_and_rejects_stale_copy(tmp_path):
    from services.ka_kshetra.g1_certification import validate_mapping, MAPPING_PATH
    root=Path(__file__).resolve().parents[5]
    assert validate_mapping(root)==[]
    mapping=json.loads((root/MAPPING_PATH).read_text())
    assert mapping['production_certification'] is None
    paths=[MAPPING_PATH,Path('platform/scripts/governance/asset_census.py'),
           Path('platform/src/generated/nirmana-writer-digests.json'),
           Path(mapping['carriage']['evidence'].rsplit(':',1)[0])]
    paths += [Path('platform/python-sidecar')/ref.split('::')[0] for ref in mapping['fidelity_tests']]
    for rel in paths:
        target=tmp_path/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/rel,target)
    assert validate_mapping(tmp_path)==[]
    target=tmp_path/MAPPING_PATH
    mapping['registry_revision']=0;target.write_text(json.dumps(mapping))
    assert validate_mapping(tmp_path)


def test_writer_digest_is_the_actual_executable_import_closure():
    from services.ka_kshetra import writer  # register the real writer
    from pipeline.orchestrator.writer_runtime_support import get_writer_source_hash
    root = Path(__file__).resolve().parents[5]
    inventory = json.loads((root / 'platform/src/generated/nirmana-writer-digests.json').read_text())
    assert inventory['writers']['ka_kshetra'] == get_writer_source_hash('ka_kshetra')


def test_output_declaration_includes_every_candidate_stage_and_manifest_grain():
    from services.ka_kshetra.candidate import TABLES
    from services.ka_kshetra.g1_certification import MAPPING_PATH
    root = Path(__file__).resolve().parents[5]
    mapping = json.loads((root / MAPPING_PATH).read_text())
    assert set(mapping['produced_tables']) == {t + '_candidate' for t in TABLES} | {'kala_layer_candidate_grain'}
