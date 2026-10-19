"""G12's full baseline runs once; a detected mutant stops before expensive work.

Use real pytest subprocesses and the real mutation classifier. The synthetic
suite counts executions instead of asserting a machine-dependent time limit.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def test_a_caught_mutant_does_not_repeat_the_expensive_baseline_work(tmp_path, monkeypatch):
    platform = Path(__file__).resolve().parents[4]
    script = platform / "scripts/gochara/mutation_check_1305.py"
    spec = importlib.util.spec_from_file_location("g12_execution_test", script)
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    counter = tmp_path / "executions.txt"
    suite = tmp_path / "test_synthetic_g12.py"
    # Deliberately put the expensive test FIRST in source order: the runner
    # must prioritize the other assertions without dropping this baseline test.
    suite.write_text(f'''from pathlib import Path
import time
MUTANT = False

def test_every_runnable_substep_after_the_snapshot_runs_with_live_L1_gone_not_only_inventory_and_coverage():
    time.sleep(0.05)  # a measurable cost, independent of machine speed
    counter = Path({str(counter)!r})
    counter.write_text(str(int(counter.read_text()) + 1) if counter.exists() else "1")

def test_detector():
    assert not MUTANT
''')
    original = suite.read_text()
    monkeypatch.setattr(harness, "TEST", str(suite))
    monkeypatch.setattr(harness, "MUTATIONS", [
        ("synthetic guard", str(suite), "MUTANT = False", "MUTANT = True"),
    ])
    monkeypatch.setattr(sys, "argv", [str(script)])
    monkeypatch.chdir(platform)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    assert harness.main() == 0  # clean full baseline and an assertion-classified catch
    assert suite.read_text() == original  # the harness restores the mutation
    assert counter.read_text() == "1", "the caught mutant repeated expensive baseline work"


def test_a_non_assertion_before_the_detector_does_not_hide_the_assertion(tmp_path, monkeypatch):
    platform = Path(__file__).resolve().parents[4]
    script = platform / "scripts/gochara/mutation_check_1305.py"
    spec = importlib.util.spec_from_file_location("g12_non_assertion_test", script)
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    marker = tmp_path / "unneeded"
    suite = tmp_path / "test_infrastructure_before_detector.py"
    suite.write_text(f'''from pathlib import Path

def test_infrastructure():
    raise ValueError("not a detecting assertion")

def test_detector():
    assert False, "the detecting assertion"

def test_unneeded():
    Path({str(marker)!r}).write_text("ran")
''')
    monkeypatch.chdir(platform)
    monkeypatch.setattr(harness, "TEST", str(suite))
    code, out, xml = harness._run(("--g12-stop-on-assertion",), timings={
        "test_infrastructure": 0, "test_detector": 1, "test_unneeded": 2,
    })
    assert harness.classify(code, out, xml) == "CAUGHT"
    assert "not a detecting assertion" in xml
    assert "the detecting assertion" in xml
    assert not marker.exists(), "work continued after the detecting assertion"
