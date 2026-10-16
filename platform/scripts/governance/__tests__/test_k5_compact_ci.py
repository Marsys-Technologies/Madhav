"""K5-2 stays isolated and its detector tests cannot fall out of required CI."""
import ast
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]


def test_compact_suite_is_explicit_in_mandatory_governance_shard():
    jobs = _ci_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    job = jobs['governance-gates-py-sidecar-shard']
    steps = [step for step in job['steps'] if 'pytest tests/l3/ka_kshetra/compact' in step.get('run', '')]
    assert len(steps) == 1
    assert '-p no:cacheprovider' in steps[0]['run']
    assert not steps[0].get('continue-on-error', False)
    assert not job.get('continue-on-error', False)
    assert 'governance-gates-py-sidecar-shard' in jobs['governance-gates']['needs']
    assert 'SHARDS_RESULT' in jobs['governance-gates']['steps'][0]['run']


def test_no_existing_live_module_imports_compact_trial():
    sidecar = ROOT / 'platform/python-sidecar'
    for directory in ('services', 'pipeline', 'routers'):
        for path in (sidecar / directory).rglob('*.py'):
            if 'tests' in path.parts or 'compact' in path.parts:
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    assert all(not n.name.startswith('services.ka_kshetra.compact') for n in node.names), path
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    assert not module.startswith('services.ka_kshetra.compact'), path
                    if module == 'services.ka_kshetra':
                        assert all(n.name != 'compact' for n in node.names), path

from pathlib import Path as _CiPath
import sys as _ci_sys
_ci_sys.path.insert(0, str(_CiPath(__file__).resolve().parents[4] / 'platform/scripts/governance'))
from ci_discovery import expanded_workflow as _ci_expanded

def _ci_load(text):
    import yaml
    data = yaml.safe_load(text)
    data['jobs'] = _ci_expanded(data['jobs'])
    return data
