"""WP10 flip scripts must load the real ledger without an inherited PYTHONPATH.

The CI rehearsal launches these scripts by absolute path. Pytest's sidecar
import path does not reach those child interpreters (PR #3337).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


CUTOVER = Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover"


@pytest.mark.parametrize("script", ["step07_flip_gates.py", "step08_flip.py"])
def test_standalone_flip_script_can_load_ledger_dependencies(script, tmp_path):
    # -I excludes PYTHONPATH and cwd; the unrelated cwd also prevents an
    # accidental pass from running in python-sidecar. No database is contacted.
    probe = """
import importlib.util
import runpy
import sys

step = runpy.run_path(sys.argv[1])
if '_load_ledger' in step:
    ledger = step['_load_ledger']()
else:
    # Step 7 loads this file inside main, after its substrate queries.
    spec = importlib.util.spec_from_file_location(
        'cutover_step07_ledger',
        step['SIDECAR'] / 'services' / 'gochara_kernel' / 'ledger.py')
    ledger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ledger)
assert ledger.canonical_json({'b': 2, 'a': 1}) == '{"a":1,"b":2}'
print('ledger dependencies loaded')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", probe, str(CUTOVER / script)],
        cwd=tmp_path, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ledger dependencies loaded"
