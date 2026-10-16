"""J4P-B4-NB1: CLI JSON survives diagnostics emitted during the core call.

Collected by mandatory CI's ``pytest tests/l3/kala_db`` directory selection.
The core double supplies only the report fields the CLI reads: astronomy and
storage are covered by the integration suites. Emitting here, after module
loading, makes the stdout contract independent of import order/copy layout.
Removing either CLI's redirect_stdout must break the corresponding test.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS = Path(__file__).resolve().parents[3] / "scripts/kala_gochara_cutover"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DIAGNOSTIC = "dependency diagnostic emitted during core execution"


def _dependency_diagnostic():
    # Deliberately use the dependency's default stdout, never stderr.
    print(DIAGNOSTIC)


@pytest.mark.parametrize(
    ("script", "core_name"),
    [
        ("step06_enumerate_episodes", "enumerate_core"),
        ("step06b_windows_projection", "project_windows_core"),
    ],
)
def test_cli_json_isolates_core_dependency_stdout(
    script, core_name, monkeypatch, capsys, tmp_path,
):
    spec = importlib.util.spec_from_file_location(script, SCRIPTS / f"{script}.py")
    cli = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, cli)
    spec.loader.exec_module(cli)

    # No database connection or ephemeris substitution: this is the real CLI
    # adapter around a controlled core dependency, not a computation test.
    conn = SimpleNamespace(commit=lambda: None, close=lambda: None)
    monkeypatch.setattr(cli, "connect", lambda *args, **kwargs: conn)
    report = {"writer": script}
    if script == "step06b_windows_projection":
        report.update(contacts_unmapped_no_class=0, contacts_unmapped_relation=0)

    def core_with_noisy_dependency(*args, **kwargs):
        _dependency_diagnostic()
        if script == "step06_enumerate_episodes":
            return [], [], report
        return {"report": report, "delta_report": ""}

    monkeypatch.setattr(cli, core_name, core_with_noisy_dependency)
    argv = ["--chart-id", CHART_ID,
            "--dsn", "postgresql://postgres@127.0.0.1:55433/postgres"]
    if script == "step06_enumerate_episodes":
        episodes_path = tmp_path / "episodes.json"
        coverage_path = tmp_path / "coverage.json"
        argv += ["--episodes-out", str(episodes_path),
                 "--coverage-out", str(coverage_path)]
    else:
        argv += ["--rehearse-synthetic"]

    # Discard any import-time noise: only a core-time diagnostic earns this
    # regression. The entire remaining stdout must be one JSON document.
    capsys.readouterr()
    assert cli.main(argv) == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    expected = {"writer": script}
    if script == "step06b_windows_projection":
        expected.update(contacts_unmapped_no_class=0, contacts_unmapped_relation=0,
                        delta_report_out=None)
    assert parsed == expected
    assert captured.err.splitlines().count(DIAGNOSTIC) == 1
    if script == "step06_enumerate_episodes":
        assert json.loads(episodes_path.read_text()) == []
        assert json.loads(coverage_path.read_text()) == []
