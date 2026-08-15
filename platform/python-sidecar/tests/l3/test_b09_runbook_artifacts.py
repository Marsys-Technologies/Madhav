"""test_b09_runbook_artifacts.py — B-09 golden tests for EKV E-03 gochara rebuild artifacts.

TDD gate: all 8 tests must FAIL before the 3 artifact files are written.
After artifacts are written, all 8 must PASS.

Tests verify existence and key content of:
  - platform/scripts/dispatch_ekv_e03_gochara_canary_482012f1.py
  - platform/scripts/dispatch_ekv_e03_gochara_full_482012f1.py
  - platform/scripts/EKV_E03_GOCHARA_REBUILD_RUNBOOK.md
"""
from __future__ import annotations

import pathlib

# Resolve paths relative to this test file's location:
#   tests/l3/test_b09_runbook_artifacts.py
#   → python-sidecar/
#   → platform/
#   → repo root / platform/scripts/
_SCRIPTS_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "scripts"

CANARY_SCRIPT = _SCRIPTS_DIR / "dispatch_ekv_e03_gochara_canary_482012f1.py"
FULL_SCRIPT = _SCRIPTS_DIR / "dispatch_ekv_e03_gochara_full_482012f1.py"
RUNBOOK = _SCRIPTS_DIR / "EKV_E03_GOCHARA_REBUILD_RUNBOOK.md"


def test_canary_script_exists():
    assert CANARY_SCRIPT.exists(), f"Canary dispatch script not found: {CANARY_SCRIPT}"


def test_full_script_exists():
    assert FULL_SCRIPT.exists(), f"Full dispatch script not found: {FULL_SCRIPT}"


def test_runbook_exists():
    assert RUNBOOK.exists(), f"Runbook not found: {RUNBOOK}"


def test_canary_script_has_chart_id():
    contents = CANARY_SCRIPT.read_text()
    assert "482012f1" in contents, "Canary script must reference chart_id '482012f1'"


def test_runbook_has_stall_rule():
    contents = RUNBOOK.read_text()
    assert "35" in contents, "Runbook must document the 35-min stall watch rule"


def test_runbook_has_f52_canary():
    contents = RUNBOOK.read_text()
    assert "F-52" in contents, "Runbook must reference F-52 canary assertion"


def test_triggered_by_canary_distinguishable():
    contents = CANARY_SCRIPT.read_text()
    assert "ekv-e03-gochara-canary" in contents, (
        "Canary script must use triggered_by containing 'ekv-e03-gochara-canary'"
    )


def test_triggered_by_full_distinguishable():
    contents = FULL_SCRIPT.read_text()
    assert "ekv-e03-gochara-full" in contents, (
        "Full dispatch script must use triggered_by containing 'ekv-e03-gochara-full'"
    )
