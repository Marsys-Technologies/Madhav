"""CI_GENERATED_AT must be UTC 'Z' whatever timezone the HEAD commit was made in.

A branch commit made at +05:30 used to stamp generated projections with '+05:30', failing
mcp_catalog_version.test.ts (expects ...Z). Both the ci.yml step and ci_generated.py must normalise."""
import os, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}T[\d:.]+Z$')


def _ist_repo(tmp_path):
    env = {**os.environ, 'GIT_COMMITTER_DATE': '2026-10-16T21:17:30+05:30', 'GIT_AUTHOR_DATE': '2026-10-16T21:17:30+05:30',
           'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@x', 'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@x'}
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', '-C', str(tmp_path), 'commit', '-q', '--allow-empty', '-m', 'ist'], check=True, env=env)
    return tmp_path


def test_ci_generated_py_stamps_utc_z_for_an_ist_commit(tmp_path, monkeypatch):
    repo = _ist_repo(tmp_path)
    src = (ROOT / 'platform/scripts/governance/ci_generated.py').read_text()
    m = re.search(r"subprocess\.run\((\['git', 'show'.*?\]), cwd=ROOT", src)
    assert m, 'ci_generated.py must derive CI_GENERATED_AT with an explicit git show argv'
    argv = eval(m.group(1))  # the literal argv list from the source
    out = subprocess.run(argv, cwd=repo, env={**os.environ, 'TZ': 'UTC'}, capture_output=True, text=True, check=True).stdout.strip()
    assert PATTERN.match(out), out
    assert out == '2026-10-16T15:47:30Z'


def test_ci_yml_projection_step_stamps_utc_z_for_an_ist_commit(tmp_path):
    repo = _ist_repo(tmp_path)
    ci = (ROOT / '.github/workflows/ci.yml').read_text()
    m = re.search(r'CI_GENERATED_AT="\$\((.*?)\)"', ci)
    assert m, 'ci.yml must set CI_GENERATED_AT'
    out = subprocess.run(['bash', '-c', m.group(1)], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
    assert PATTERN.match(out), out
