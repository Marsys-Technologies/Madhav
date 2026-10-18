"""K5-3 suites must remain required and unfiltered, with DB skips fatal."""
from copy import deepcopy
from pathlib import Path
import shlex

import pytest
import yaml

CI = Path(__file__).resolve().parents[5] / '.github/workflows/ci.yml'
SUITES = ('tests/l3/ka_kshetra/test_g2_model.py',
          'tests/l3/ka_kshetra/test_g2_features.py',
          'tests/l3/ka_kshetra/test_g2_ci.py')


def check_required(jobs):
    job = jobs['kala-db-tests']
    assert not job.get('continue-on-error')
    assert runs_in_full_gate(job)
    steps = job['steps']
    selected = [s for s in steps if all(p in str(s.get('run', '')) for p in SUITES)]
    assert len(selected) == 1, 'G2 pure suites need one explicit required selection'
    assert runs_in_full_gate(selected[0]) and not selected[0].get('continue-on-error')
    tokens = shlex.split(selected[0]['run'].replace('\\\n', ' '))
    tokens = tokens[tokens.index('pytest') + 1:]
    assert not any(t in {'-k', '-m', '--collect-only', '||', ';', '|'} for t in tokens)
    assert not any(t.startswith(('--ignore', '--deselect')) for t in tokens)
    db = [s for s in steps if 'pytest tests/l3/kala_db ' in str(s.get('run', ''))]
    assert len(db) == 1, 'retain every existing DB test path'
    assert runs_in_full_gate(db[0]) and not db[0].get('continue-on-error')
    assert str(db[0]['env']['KALA_REQUIRE_DB']) == '1'
    assert db[0]['env']['KALA_ADMIN_DSN'].startswith('postgresql://')


def test_g2_pure_and_guarded_db_suites_run_in_required_ci():
    check_required(_ci_load(CI.read_text())['jobs'])


@pytest.mark.parametrize('mutant', ['pure_missing', 'pure_optional', 'db_missing', 'db_skips'])
def test_ci_coverage_detector_rejects_mutants(mutant):
    jobs = deepcopy(_ci_load(CI.read_text())['jobs'])
    steps = jobs['kala-db-tests']['steps']
    pure = next(s for s in steps if all(p in str(s.get('run', '')) for p in SUITES))
    db = next(s for s in steps if 'pytest tests/l3/kala_db ' in str(s.get('run', '')))
    if mutant == 'pure_missing':
        steps.remove(pure)
    elif mutant == 'pure_optional':
        pure['continue-on-error'] = True
    elif mutant == 'db_missing':
        steps.remove(db)
    else:
        db['env']['KALA_REQUIRE_DB'] = '0'
    with pytest.raises(AssertionError):
        check_required(jobs)

from pathlib import Path as _CiPath
import sys as _ci_sys
_ci_sys.path.insert(0, str(_CiPath(__file__).resolve().parents[5] / 'platform/scripts/governance'))
from ci_discovery import expanded_workflow as _ci_expanded
_ci_sys.path.insert(0, str(_CiPath(__file__).resolve().parents[5] / 'platform/scripts/governance/__tests__'))
from _ci_gate_test_support import runs_in_full_gate

def _ci_load(text):
    import yaml
    data = yaml.safe_load(text)
    data['jobs'] = _ci_expanded(data['jobs'])
    return data
