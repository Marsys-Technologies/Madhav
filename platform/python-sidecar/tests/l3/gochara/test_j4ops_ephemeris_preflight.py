"""Real pinned corpus, exact legacy inline preflight; no auxiliary stand-ins.

No DB connection or whole shell execution: the shell's /tmp/remote build chain
is deliberately not invoked. The subprocess executes the exact preflight block.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from .conftest import EPHE_PATH, requires_swieph, SE1_CHECKSUMS

SHELL = Path(__file__).resolve().parents[3] / 'scripts/kala_gochara_cutover/century_run_4_1.sh'


def run_preflight(corpus):
    block = SHELL.read_text().split("python - <<'PYEOF'\n", 1)[1].split('\nPYEOF', 1)[0]
    return subprocess.run([sys.executable, '-B', '-c', block], capture_output=True, text=True,
                          env=dict(os.environ, EPHE_PATH_ENV=str(corpus)), check=False)


@pytest.fixture
def corpus(tmp_path):
    for name in SE1_CHECKSUMS:
        shutil.copyfile(Path(EPHE_PATH) / name, tmp_path / name)
    assert not (tmp_path / 'sefstars.txt').exists()
    assert not (tmp_path / 'seleapsec.txt').exists()
    return tmp_path


@requires_swieph
def test_exact_preflight_accepts_pinned_planetary_corpus_without_unused_auxiliaries(corpus):
    result = run_preflight(corpus)
    assert result.returncode == 0, result.stderr
    assert '3 .se1 sha256 pins match' in result.stdout
    assert 'horizon endpoints and J2000' in result.stdout


@requires_swieph
@pytest.mark.parametrize('name', sorted(SE1_CHECKSUMS))
@pytest.mark.parametrize('mutation', ('missing', 'changed'))
def test_exact_preflight_refuses_any_missing_or_changed_pinned_file(corpus, name, mutation):
    path = corpus / name
    if mutation == 'missing':
        path.unlink()
    else:
        with path.open('ab') as stream:
            stream.write(b'negative-test-corruption')
    result = run_preflight(corpus)
    assert result.returncode != 0
    assert name in result.stderr
    assert 'OK:' not in result.stdout


@requires_swieph
def test_true_node_probe_detects_real_lunar_fallback_after_hash_check(corpus):
    block = SHELL.read_text().split("python - <<'PYEOF'\n", 1)[1].split('\nPYEOF', 1)[0]
    # Race-like loss of the genuine copied lunar file AFTER hashing. No fake
    # coordinates/retflags: the real Swiss library must detect its own fallback.
    block = block.replace('swe.set_ephe_path(EPHE)',
                          'swe.set_ephe_path(EPHE)\nos.unlink(os.path.join(EPHE, "semo_18.se1"))\nswe.close()\nswe.set_ephe_path(EPHE)')
    result = subprocess.run([sys.executable, '-B', '-c', block], capture_output=True, text=True,
                            env=dict(os.environ, EPHE_PATH_ENV=str(corpus)), check=False)
    assert result.returncode != 0
    assert 'True node computed via fallback backend' in result.stderr
    assert 'OK:' not in result.stdout


@requires_swieph
def test_exact_preflight_observes_each_endpoint_and_true_node_in_real_calculations(corpus):
    import json
    import swisseph as swe
    block = SHELL.read_text().split("python - <<'PYEOF'\n", 1)[1].split('\nPYEOF', 1)[0]
    # Instrument only: every calculation still calls the actual Swiss function.
    instrumentation = '''
observed_calls = []
real_calc_ut = swe.calc_ut
def observed_calc_ut(jd, body, flags):
    observed_calls.append([jd, body])
    return real_calc_ut(jd, body, flags)
swe.calc_ut = observed_calc_ut
'''
    block = block.replace('import swisseph as swe', 'import swisseph as swe\n' + instrumentation)
    block += '\nimport json\nprint(json.dumps(observed_calls))\n'
    result = subprocess.run([sys.executable, '-B', '-c', block], capture_output=True, text=True,
                            env=dict(os.environ, EPHE_PATH_ENV=str(corpus)), check=False)
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout.splitlines()[-1])
    expected = [[jd, body] for jd in (swe.julday(1998, 1, 1, 0.0), swe.julday(2000, 1, 1, 12.0),
                                     swe.julday(2026, 4, 18, 0.0))
                for body in (swe.SUN, swe.TRUE_NODE, swe.SATURN)]
    assert observed == expected
