"""Real guarded-suite staging/readback, with an injected launcher; never cloud."""
import importlib.util
import json
from pathlib import Path

import psycopg
import psycopg.rows
import pytest

from ._smalltest_executor_evidence import executor_bound_smalltest  # noqa: F401
from .test_a55_replace_chain import template  # noqa: F401
from .test_c37_dispatch_real_db import dtemplate, dw  # noqa: F401


def test_real_staged_run_is_launched_once_and_receipted(dw, tmp_path, monkeypatch, capsys):
    path = Path(__file__).resolve().parents[5] / "00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py"
    spec = importlib.util.spec_from_file_location("w4_bridge", path)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    import dispatch_v5_small_test_job as dispatch
    monkeypatch.setenv("DATABASE_URL", dw.dsn)
    calls = []
    result = bridge.run(["--run", "one_class_full", "--classes", "marriage"], dispatcher=dispatch,
                        connect=lambda: psycopg.connect(dw.dsn, row_factory=psycopg.rows.dict_row), claim_dir=tmp_path,
                        launcher=lambda run_id, timeout_s: calls.append(run_id) or "brahma-build-pipeline-job-fixture01")
    stored = dw.conn.execute("SELECT id, state, plan_manifest_digest FROM build_runs").fetchall()
    assert len(stored) == 1 and str(stored[0][0]) == calls[0] == result["run_id"]
    assert stored[0][1:] == ("planned", result["plan_manifest_digest"])
    assert json.loads(capsys.readouterr().out)["execution_name"] == "brahma-build-pipeline-job-fixture01"
    assert json.loads((tmp_path / (result["run_id"] + ".json")).read_text()) == result


def test_measuring_staging_dry_run_is_refused_without_writes(dw, capsys, monkeypatch):
    import dispatch_v5_small_test_job as dispatch
    monkeypatch.setenv("DATABASE_URL", dw.dsn)
    path = Path(__file__).resolve().parents[5] / "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"
    surface = json.loads(path.read_text())["ops"]["measuring_dispatch"]["staging_dry_run"]
    # PR #3507 / P01 deliberately disables measuring through the small-test path.
    with pytest.raises(SystemExit) as refused:
        dispatch.main(surface["fixed_args"])
    assert refused.value.code == 2
    streams = capsys.readouterr()
    assert streams.out == ""
    assert "measuring phase is disabled" in streams.err
    assert dw.conn.execute("SELECT count(*) FROM build_runs").fetchone()[0] == 0
    assert dw.conn.execute("SELECT count(*) FROM build_run_assets").fetchone()[0] == 0
