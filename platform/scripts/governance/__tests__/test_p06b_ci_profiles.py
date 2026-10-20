"""P06b must run in the existing required contexts without workflow file allowlists."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT=Path(__file__).resolve().parents[4]
SCRIPT=ROOT/'platform/scripts/gochara/ci_p06b.py'


def test_p06b_profile_guard_is_current():
    result=subprocess.run([sys.executable,str(SCRIPT),'--check'],capture_output=True,text=True)
    assert result.returncode==0, result.stdout+result.stderr
    assert result.stdout.strip()=='current'


def test_new_test_families_are_discovered_and_empty_families_refuse(tmp_path):
    assert SCRIPT.is_file(), 'P06b CI profile consumer is missing'
    spec=importlib.util.spec_from_file_location('ci_p06b',SCRIPT)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    config=ROOT/'platform/scripts/governance/ci_test_suites.json'
    destination=tmp_path/config.relative_to(ROOT)
    destination.parent.mkdir(parents=True);destination.write_text(config.read_text())
    with pytest.raises(ValueError,match='empty'):
        module.discover(tmp_path,'p06b-python')
    side=tmp_path/'platform/python-sidecar/tests/l3/gochara';side.mkdir(parents=True)
    for name in ('test_p06b_future.py','test_near_miss_future.py'):
        (side/name).write_text('def test_future(): pass\n')
    assert set(module.discover(tmp_path,'p06b-python')[2]) == {
        'tests/l3/gochara/test_p06b_future.py','tests/l3/gochara/test_near_miss_future.py'}
    data=json.loads(destination.read_text());data['suites']['p06b-python']['include']=['tests/l3/gochara/test_p06b_future.py']
    destination.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='glob'):
        module.discover(tmp_path,'p06b-python')


def test_both_profiles_run_in_required_contexts_with_real_db_and_ephemeris():
    jobs=yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())['jobs']
    found={}
    for name,job in jobs.items():
        for step in job.get('steps',[]):
            run=step.get('run','')
            for suite,engine in (('p06b-python','pytest'),('p06b-typescript','vitest')):
                if f'ci_discovery.py" {engine} {suite} --' in run:
                    assert not job.get('continue-on-error') and not step.get('continue-on-error')
                    assert name in ('unit-db-tests','db-integration-tests')
                    assert suite in step['if'], 'the light-PR gate must select the step by its own profile'
                    found[suite]=(step,run)
    assert set(found)=={'p06b-python','p06b-typescript'}
    step,run=found['p06b-python']
    assert step['env']['GOCHARA_A53_REQUIRE_DB']=='1'
    assert 'GOCHARA_SE1_REQUIRE=1' in run and 'SE_EPHE_PATH=' in run
