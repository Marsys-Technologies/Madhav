"""The standing watchdog must propagate measured failures and missing coverage."""

import contextlib
import json
import os
import runpy
import sqlite3
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


@pytest.mark.parametrize(("level", "status", "unexamined"), [
    (1, "two_pass_verified", 0),
    (4, "two_pass_verified", 0),
    (5, "two_pass_verified", 1),
    (None, "two_pass_verified", 1),
    (None, "single", 0),
])
def test_claim_vs_evidence_counts_only_verified_claims_outside_examined_rows(
    watchdog, monkeypatch, level, status, unexamined
):
    _, namespace = watchdog
    monkeypatch.setitem(namespace, "_tables_with_column", lambda cur: ["chart_dashas", "chart_facts"])

    with contextlib.closing(sqlite3.connect(":memory:")) as connection:
        connection.execute(
            "CREATE TABLE chart_dashas (verification_pass_status TEXT, kp_sublevel INTEGER, "
            "level_n INTEGER, system_id TEXT)"
        )
        connection.execute("INSERT INTO chart_dashas VALUES (?, NULL, ?, 'vimshottari')", (status, level))
        connection.execute("CREATE TABLE chart_facts (verification_pass_status TEXT)")
        connection.executemany(
            "INSERT INTO chart_facts VALUES (?)", [("two_pass_verified",), ("two_pass_verified",), ("single",), (None,)]
        )
        cursor = connection.cursor()

        def execute(sql, params):
            # Adapt PostgreSQL array binding while evaluating the audit predicate unchanged.
            statuses, = params
            placeholders = ", ".join("?" for _ in statuses)
            cursor.execute(sql.replace("= ANY(%s)", f"IN ({placeholders})"), statuses)

        results = []
        namespace["check_claim_vs_evidence"](SimpleNamespace(execute=execute, fetchone=cursor.fetchone), results)

    dashas, facts = results
    assert dashas["table"] == "chart_dashas"
    assert dashas["status"] == ("FAIL" if unexamined else "PASS")
    assert dashas["detail"].startswith(f"{int(status == 'two_pass_verified')} row(s) claim a verified tier; {unexamined} ")
    assert facts["table"] == "chart_facts"
    assert facts["status"] == "INCOMPLETE"
    assert facts["detail"].startswith("2 row(s) claim a verified tier.")
    assert "Examined-row coverage is unknown" in facts["detail"]


def test_no_verified_chart_facts_claims_are_explicit_without_predicate_credit(watchdog, monkeypatch):
    _, namespace = watchdog
    monkeypatch.setitem(namespace, "_tables_with_column", lambda cur: ["chart_facts"])
    queries = []
    cursor = SimpleNamespace(execute=lambda sql, params: queries.append((sql, params)), fetchone=lambda: (0,))
    results = []
    namespace["check_claim_vs_evidence"](cursor, results)
    assert results == [{
        "check": "claim_vs_evidence", "table": "chart_facts", "status": "PASS",
        "detail": "0 row(s) claim a verified tier. No verified claims to assess.",
    }]
    assert queries == [('SELECT count(*) FROM "chart_facts" WHERE verification_pass_status = ANY(%s)',
                        (["two_pass_verified"],))]


def test_divisional_and_undeclared_claim_dispositions_are_unchanged(watchdog, monkeypatch):
    _, namespace = watchdog
    monkeypatch.setitem(namespace, "_tables_with_column", lambda cur: ["chart_divisionals", "fixture_undeclared"])
    counts = iter([(0,), (1,), (1,)])
    cursor = SimpleNamespace(execute=lambda sql, params: None, fetchone=lambda: next(counts))
    results = []
    namespace["check_claim_vs_evidence"](cursor, results)
    assert [(r["table"], r["status"]) for r in results] == [("chart_divisionals", "PASS"), ("fixture_undeclared", "FAIL")]
    assert "(TRUE). Tolerance 0." in results[0]["detail"]
    assert "NO examined-row predicate" in results[1]["detail"]


def verdict(status):
    return {"check": "detector_liveness", "table": "-", "status": status, "detail": "fixture"}


def workflow_step(exit_code, database_url=""):
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
        env={"PATH": os.defpath, "WATCHDOG_SCRIPT": SCRIPT, "WATCHDOG_EXIT": str(exit_code),
             "DATABASE_URL": database_url},
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
        assert "DATABASE_URL unavailable; liveness ran, but data checks did not" in step.stdout


@pytest.fixture
def fixture_database(watchdog, monkeypatch):
    _, namespace = watchdog
    monkeypatch.setenv("DATABASE_URL", "isolated-test-dsn")

    def connect(dsn):
        assert dsn == "isolated-test-dsn"
        return contextlib.nullcontext(SimpleNamespace(cursor=contextlib.nullcontext))

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=connect))
    monkeypatch.setitem(namespace, "tier_report", lambda cur: {"fixture_table": {"verified": 2}})


@pytest.mark.parametrize(("data_status", "detector_status", "additional_failure", "expected"), [
    ("PASS", "PASS", None, 0),
    ("FAIL", "PASS", None, 1),
    ("PASS", "FAIL", None, 1),
    ("INCOMPLETE", "PASS", None, 3),
    ("INCOMPLETE", "FAIL", None, 1),
    ("INCOMPLETE", "PASS", "claim_vs_evidence", 1),
    ("INCOMPLETE", "PASS", "vocabulary_conformance", 1),
])
def test_full_watchdog_preserves_data_and_detector_failures(
    watchdog, fixture_database, monkeypatch, capsys, data_status, detector_status, additional_failure, expected
):
    main, namespace = watchdog
    data_result = {"check": "claim_vs_evidence", "table": "chart_facts", "status": data_status, "detail": "fixture"}
    extra = {"check": additional_failure, "table": "fixture_other", "status": "FAIL", "detail": "fixture"}
    claims = [data_result] + ([extra] if additional_failure == "claim_vs_evidence" else [])
    vocabulary = [extra] if additional_failure == "vocabulary_conformance" else []
    monkeypatch.setitem(namespace, "check_claim_vs_evidence", lambda cur, results: results.extend(claims))
    monkeypatch.setitem(namespace, "check_vocabulary_conformance", lambda cur, results: results.extend(vocabulary))
    monkeypatch.setitem(namespace, "check_detector_liveness", lambda results: results.append(verdict(detector_status)))

    cli_status = main()
    cli_output = capsys.readouterr()
    payload, _, summary = cli_output.out.partition("\n\n=== verification invariant ===")
    results = claims + vocabulary + [verdict(detector_status)]
    assert json.loads(payload) == {"tier_report": {"fixture_table": {"verified": 2}}, "results": results}
    assert f"{sum(row['status'] == 'FAIL' for row in results)} FAIL / {len(results)} checks" in summary
    assert ("1 INCOMPLETE" in summary) == (data_status == "INCOMPLETE")
    step = workflow_step(cli_status, database_url="isolated-test-dsn")
    assert (cli_status, step.returncode) == (expected, expected)
    assert "isolated-test-dsn" not in step.stdout
    assert ("::warning::" in step.stdout) == (expected == 3)
    if expected == 3:
        assert "data checks ran, but verified-claim evidence coverage is incomplete" in step.stdout
        assert "DATABASE_URL unavailable" not in step.stdout


def test_with_database_incomplete_wrapper_never_claims_data_checks_were_skipped():
    step = workflow_step(3, database_url="isolated-test-dsn")
    assert step.returncode == 3
    assert "verified-claim evidence coverage is incomplete" in step.stdout
    assert "DATABASE_URL unavailable" not in step.stdout
    assert "isolated-test-dsn" not in step.stdout


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
