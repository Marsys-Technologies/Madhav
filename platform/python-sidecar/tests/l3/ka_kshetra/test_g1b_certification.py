"""Current detector bindings, executable evidence, no fabricated certificate."""
from pathlib import Path
import json
import shutil


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
