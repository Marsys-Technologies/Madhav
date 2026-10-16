"""K8-K3 semantic evidence bindings are current; no live verdict is awarded."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[5]
MAPPING=Path('platform/python-sidecar/services/ka_vighnakara/certification_mapping.json')


def validator(root=ROOT):
    from services.ka_vighnakara import sealed
    validate=getattr(sealed,'validate_certification_mapping',None)
    assert callable(validate), 'K3-2 mapping validator missing'
    return validate(root)


def test_mapping_current_and_production_unmeasured():
    assert validator()==[]


@pytest.mark.parametrize('mutation',['stale_registry','earned_pass','deleted','wrong_asset','missing_gate','no_detector','missing_golden'])
def test_mapping_mutations_refuse(tmp_path,mutation):
    mapping=json.loads((ROOT/MAPPING).read_text())
    # Only read-only evidence copies; no git repo or commands in the fixture.
    import shutil
    files=[MAPPING,Path('platform/scripts/governance/asset_census.py')]
    files += [Path('platform/python-sidecar')/ref.split('::')[0] for ref in mapping['fidelity_tests']]
    for path in files:
        target=tmp_path/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    path=tmp_path/MAPPING
    if mutation=='stale_registry': mapping['registry_revision']=0
    elif mutation=='earned_pass': mapping['production_certification']='PASS'
    elif mutation=='wrong_asset': mapping['asset']='ka_yojaka'
    elif mutation=='missing_gate': mapping['gates'].pop('Idem')
    elif mutation=='no_detector': mapping['gates']['Carr']['detector_none']=[]
    elif mutation=='missing_golden': mapping['fidelity_tests']=['tests/l3/ka_vighnakara/test_sealed.py::test_nonexistent']
    if mutation=='deleted': path.unlink()
    else: path.write_text(json.dumps(mapping))
    assert validator(tmp_path)


def test_sealed_sql_suite_is_a_required_governance_dependency():
    import yaml
    jobs=yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())['jobs']
    assert 'k3-sealed-db-tests' in jobs['governance-gates']['needs']
    job=jobs['k3-sealed-db-tests']
    commands='\n'.join(step.get('run','') for step in job['steps'])
    assert 'tests/l3/ka_vighnakara tests/l3/kala_db/ka_vighnakara' in commands
    assert job['env']['KALA_REQUIRE_DB']=='1'
    assert 'postgres' in job['services']
    old_commands='\n'.join(step.get('run','') for step in jobs['kala-db-tests']['steps'])
    assert 'tests/l3/kala_db tests/l3/ka_bhavishya_lekha/test_certification_mapping.py' in old_commands
    gate_commands='\n'.join(step.get('run','') for step in jobs['governance-gates']['steps'])
    assert 'K3_RESULT' in gate_commands and 'DOCS_ONLY' in gate_commands
