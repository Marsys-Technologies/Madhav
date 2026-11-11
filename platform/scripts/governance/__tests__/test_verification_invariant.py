"""The standing watchdog must propagate measured failures and missing coverage."""

import contextlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = "platform/scripts/audit/verification_invariant.py"
WORKFLOW = ROOT / ".github/workflows/verification-invariant.yml"


@pytest.fixture
def watchdog(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", [SCRIPT])
    monkeypatch.setattr(sys, "path", list(sys.path))
    main = runpy.run_path(str(ROOT / SCRIPT))["main"]
    return main, main.__globals__


def verdict(status):
    return {"check": "detector_liveness", "table": "-", "status": status, "detail": "fixture"}


def workflow_step(exit_code):
    workflow = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["invariant"]["steps"]
    run = next(step["run"] for step in steps if step.get("name") == "Run the invariant")
    python_stub = '''
python() {
    [ "$#" = 1 ] && [ "$1" = "$WATCHDOG_SCRIPT" ] || return 99
    return "$WATCHDOG_EXIT"
}
'''
    return subprocess.run(
        ["/bin/bash", "-c", python_stub + run],
        env={"PATH": os.defpath, "WATCHDOG_SCRIPT": SCRIPT, "WATCHDOG_EXIT": str(exit_code)},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(("status", "expected"), [("FAIL", 1), ("PASS", 3)])
def test_no_database_preserves_measured_liveness_and_incomplete_coverage(
    watchdog, monkeypatch, capsys, status, expected
):
    main, namespace = watchdog
    monkeypatch.setitem(namespace, "check_detector_liveness", lambda results: results.append(verdict(status)))

    cli_status = main()
    cli_output = capsys.readouterr()
    assert json.loads(cli_output.out) == {"results": [verdict(status)]}
    assert "QUARANTINED" in cli_output.err

    step = workflow_step(cli_status)
    assert (cli_status, step.returncode) == (expected, expected)
    assert ("::warning::" in step.stdout) == (expected == 3)
    if expected == 3:
        assert "INCOMPLETE" in step.stdout


@pytest.fixture
def fixture_database(watchdog, monkeypatch):
    _, namespace = watchdog
    monkeypatch.setenv("DATABASE_URL", "isolated-test-dsn")

    def connect(dsn):
        assert dsn == "isolated-test-dsn"
        return contextlib.nullcontext(SimpleNamespace(cursor=contextlib.nullcontext))

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=connect))
    monkeypatch.setitem(namespace, "tier_report", lambda cur: {"fixture_table": {"verified": 2}})


@pytest.mark.parametrize(("data_status", "detector_status", "expected"), [
    ("PASS", "PASS", 0), ("FAIL", "PASS", 1), ("PASS", "FAIL", 1),
])
def test_full_watchdog_preserves_data_and_detector_failures(
    watchdog, fixture_database, monkeypatch, capsys, data_status, detector_status, expected
):
    main, namespace = watchdog
    data_result = {"check": "claim_vs_evidence", "table": "fixture_table", "status": data_status, "detail": "fixture"}
    monkeypatch.setitem(namespace, "check_claim_vs_evidence", lambda cur, results: results.append(data_result))
    monkeypatch.setitem(namespace, "check_vocabulary_conformance", lambda cur, results: None)
    monkeypatch.setitem(namespace, "check_detector_liveness", lambda results: results.append(verdict(detector_status)))

    cli_status = main()
    cli_output = capsys.readouterr()
    payload, _, _ = cli_output.out.partition("\n\n=== verification invariant ===")
    assert json.loads(payload)["results"] == [data_result, verdict(detector_status)]
    assert (cli_status, workflow_step(cli_status).returncode) == (expected, expected)


def test_connection_error_still_propagates(watchdog, fixture_database, monkeypatch):
    main, _ = watchdog

    def connection_error(dsn):
        raise OSError("fixture database unavailable")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=connection_error))
    with pytest.raises(OSError, match="fixture database unavailable"):
        main()
    assert workflow_step(1).returncode == 1


def test_report_with_data_remains_counts_only(watchdog, fixture_database, monkeypatch, capsys):
    main, namespace = watchdog
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--report"])

    def unexpected_check(*args):
        pytest.fail("counts-only report must not run watchdog checks")

    for check in ("check_claim_vs_evidence", "check_vocabulary_conformance", "check_detector_liveness"):
        monkeypatch.setitem(namespace, check, unexpected_check)

    assert main() == 0
    assert json.loads(capsys.readouterr().out) == {"tier_report": {"fixture_table": {"verified": 2}}}


def test_report_without_data_preserves_diagnostic(watchdog, monkeypatch, capsys):
    main, namespace = watchdog
    monkeypatch.setattr(sys, "argv", [SCRIPT, "--report"])
    monkeypatch.setitem(namespace, "check_detector_liveness", lambda results: results.append(verdict("FAIL")))

    assert main() == 3
    assert json.loads(capsys.readouterr().out) == {"results": [verdict("FAIL")]}
