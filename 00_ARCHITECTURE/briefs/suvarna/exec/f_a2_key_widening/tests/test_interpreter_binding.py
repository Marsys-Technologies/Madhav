"""The interpreter and driver are bound into the dry-run evidence digest, and --apply / --rollback refuse BY THEMSELVES when they differ.

Runtime record = sys.executable, the full sys.version, psycopg.__version__, the libpq version (psycopg.pq.version()). Three layers:
  (a) it is part of the evidence digest (run_leg), so a different runtime never reproduces the dry run's digest;
  (b) interpreter_precheck, before any connection and before the credential is fetched: a matching dry run's outcome.json is compared field by
      field; any difference = exit 92 with check `interpreter_differs_from_dry_run`; a missing field = exit 92 `dry_run_evidence_lacks_interpreter_record`
      ("cannot compare"); the same runtime proceeds;
  (c) with no dry-run evidence to read (copied from another host) only (a) remains: the apply is refused by evidence_digest_matches_expected, rolled back.
Simulated by patching sys.executable / sys.version / psycopg.__version__ / psycopg.pq.version in the test (the executor reads them at call time)."""
from __future__ import annotations

import json
import pathlib
import shutil
import sys

import psycopg
import pytest

import conftest as cf


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return cf.Runner(cluster, mod, db, tmp_path)


def no_connect():
    pytest.fail("connected: an interpreter refusal must come BEFORE the credential is fetched")


def outcome_of(tmp_path, prefix):
    return json.loads(next(iter(sorted((tmp_path / "ev").glob(prefix + "_*/outcome.json")))).read_text())


def dry_run(runner):
    code, res = runner.run("dry-run")
    assert code == 0
    return res


def apply_args(runner, digest):
    return runner.args("apply", expect_evidence=digest)


def patch_runtime(monkeypatch, which):
    if which == "executable":
        monkeypatch.setattr(sys, "executable", "/opt/other/python3.11")
    elif which == "version":
        monkeypatch.setattr(sys, "version", sys.version + " [PATCH-LEVEL-DIFFERS]")
    elif which == "psycopg":
        monkeypatch.setattr(psycopg, "__version__", "0.0.1")
    elif which == "libpq":
        monkeypatch.setattr(psycopg.pq, "version", lambda: 1)


KEYS = {"executable": "python_executable", "version": "python_version", "psycopg": "psycopg_version", "libpq": "libpq_version"}


@pytest.mark.parametrize("which", list(KEYS))
def test_apply_under_a_different_runtime_refuses_by_itself_before_connecting(runner, mod, monkeypatch, tmp_path, which):
    before = runner.state()
    digest = dry_run(runner)["evidence_digest"]
    patch_runtime(monkeypatch, which)
    with pytest.raises(SystemExit) as ei:
        mod.execute(apply_args(runner, digest), no_connect, writer_runner=cf.writer_runner(mod))
    assert ei.value.code == mod.EXIT_INTERPRETER == 92
    o = outcome_of(tmp_path, "apply")
    assert o["status"] == "failed" and o["failed_checks"] == ["interpreter_differs_from_dry_run"]
    monkeypatch.undo()
    assert runner.state() == before                                   # nothing was even attempted


def test_the_refusal_message_names_both_values(runner, mod, monkeypatch, capsys):
    digest = dry_run(runner)["evidence_digest"]
    patch_runtime(monkeypatch, "executable")
    with pytest.raises(SystemExit):
        mod.execute(apply_args(runner, digest), no_connect, writer_runner=cf.writer_runner(mod))
    err = capsys.readouterr().err
    assert "REFUSED (interpreter)" in err and "python_executable" in err and "/opt/other/python3.11" in err and "SAME interpreter" in err


def test_the_same_runtime_proceeds_and_commits(runner):
    code, res = runner.run("apply")                                   # Runner.run performs the matching dry run first, same process
    assert code == 0 and res["status"] == "COMMITTED"
    assert any("interpreter check: 1 dry run(s)" in ln for ln in res["log"])
    assert res["runtime"]["python_executable"] == sys.executable


def test_the_same_runtime_proceeds_for_the_rollback_too(runner):
    assert runner.run("apply")[0] == 0
    code, res = runner.run("rollback")
    assert code == 0 and res["status"] == "COMMITTED"


def test_the_rollback_under_a_different_runtime_refuses_too(runner, mod, monkeypatch):
    assert runner.run("apply")[0] == 0
    _, d = runner.execute(runner.args("rollback-dry-run"))
    patch_runtime(monkeypatch, "version")
    with pytest.raises(SystemExit) as ei:
        mod.execute(runner.args("rollback", expect_evidence=d["evidence_digest"]), no_connect, writer_runner=cf.writer_runner(mod))
    assert ei.value.code == 92


@pytest.mark.parametrize("drop", list(KEYS.values()))
def test_a_dry_run_record_lacking_a_field_cannot_be_compared_and_refuses(runner, mod, tmp_path, drop):
    """The old format (no interpreter fields, or a SIGKILL between the two renames) = cannot compare = REFUSED."""
    before = runner.state()
    res = dry_run(runner)
    f = pathlib.Path(res["outcome_file"])
    body = json.loads(f.read_text())
    del body[drop]
    f.write_text(json.dumps(body))
    with pytest.raises(SystemExit) as ei:
        mod.execute(apply_args(runner, res["evidence_digest"]), no_connect, writer_runner=cf.writer_runner(mod))
    assert ei.value.code == 92
    assert outcome_of(tmp_path, "apply")["failed_checks"] == ["dry_run_evidence_lacks_interpreter_record"]
    assert runner.state() == before


def test_an_old_format_dry_run_without_any_interpreter_fields_refuses_with_cannot_compare(runner, mod, capsys):
    res = dry_run(runner)
    f = pathlib.Path(res["outcome_file"])
    body = {k: v for k, v in json.loads(f.read_text()).items() if k not in KEYS.values()}
    f.write_text(json.dumps(body))
    with pytest.raises(SystemExit) as ei:
        mod.execute(apply_args(runner, res["evidence_digest"]), no_connect, writer_runner=cf.writer_runner(mod))
    assert ei.value.code == 92 and "cannot compare" in capsys.readouterr().err


# ---------------------------------------------------------------------------------------------------- (a) the digest binds the runtime
@pytest.mark.parametrize("which", list(KEYS))
def test_the_evidence_digest_differs_under_a_different_runtime(runner, monkeypatch, which):
    d1 = dry_run(runner)["evidence_digest"]
    assert dry_run(runner)["evidence_digest"] == d1                    # deterministic for one runtime
    patch_runtime(monkeypatch, which)
    assert dry_run(runner)["evidence_digest"] != d1


@pytest.mark.parametrize("which", list(KEYS))
def test_with_no_dry_run_evidence_to_read_the_digest_alone_refuses_the_apply(runner, mod, monkeypatch, tmp_path, which):
    """(c): the dry-run folder is not on this host. No early verdict, the transaction runs, evidence_digest_matches_expected fails, ROLLBACK."""
    before = runner.state()
    digest = dry_run(runner)["evidence_digest"]
    for d in (tmp_path / "ev").glob("dry-run_*"):
        shutil.rmtree(d)
    patch_runtime(monkeypatch, which)
    code, res = mod.execute(apply_args(runner, digest), lambda: runner.cl.conn(runner.db, user=cf.ADMIN_USER),
                            gate_tables=cf.L1_TABLES, writer_runner=cf.writer_runner(mod))
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK" and "evidence_digest_matches_expected" in res["failed_checks"]
    assert any("no dry-run evidence for this digest" in ln for ln in res["log"])
    monkeypatch.undo()
    assert runner.state() == before


def test_the_runtime_is_in_result_json_and_outcome_json_of_every_mode(runner):
    res = dry_run(runner)
    rec = json.loads((pathlib.Path(res["evidence_dir"]) / "result.json").read_text())["runtime"]
    o = json.loads(pathlib.Path(res["outcome_file"]).read_text())
    assert rec == {k: o[k] for k in KEYS.values()} and rec["libpq_version"] == psycopg.pq.version()


# ---------------------------------------------------------------------------------------- an unexpected error in the interpreter step
def raising_only_in_the_interpreter_step(real):
    """runtime_record() that raises AttributeError ONLY when add_interpreter_to_outcome calls it (the step after the standard outcome write);
    the precheck, the evidence digest and result.json still get the real record."""
    def fake():
        if sys._getframe(1).f_code.co_name == "add_interpreter_to_outcome":
            raise AttributeError("simulated: no version attribute")
        return real()
    return fake


def test_an_unexpected_error_in_the_interpreter_step_is_a_warning_not_a_crash(mod, tmp_path, monkeypatch):
    es = mod.standards()
    d = tmp_path / "w3"
    monkeypatch.setattr(mod, "runtime_record", raising_only_in_the_interpreter_step(mod.runtime_record))
    with mod.safe_outcome_class(es)(d, str(cf.EXEC_DIR / "d6_dataplane_capture_fa2_exec.py"), "a" * 64,
                                    dict(es.fingerprint(str(cf.GATE_FIXTURE)), under_test=False)) as o:
        result = mod.conclude(o, {}, "applied", "b" * 64)
    assert o.write_error is None and o.interpreter_record_error == "AttributeError"
    body = json.loads((d / "outcome.json").read_text())
    assert body["status"] == "applied" and "python_executable" not in body and not list(d.glob(".outcome.*"))
    assert result["outcome_file"] == o.path
    assert result["warnings"] == ["outcome.json written without the interpreter record (AttributeError); THE COMMIT HAPPENED"]


def test_a_committed_apply_whose_interpreter_step_raises_is_still_recorded_applied(runner, mod, monkeypatch, tmp_path):
    digest = dry_run(runner)["evidence_digest"]
    monkeypatch.setattr(mod, "runtime_record", raising_only_in_the_interpreter_step(mod.runtime_record))
    code, res = runner.execute(apply_args(runner, digest))
    assert code == 0 and res["status"] == "COMMITTED"
    assert res["warnings"] == ["outcome.json written without the interpreter record (AttributeError); THE COMMIT HAPPENED"]
    o = outcome_of(tmp_path, "apply")
    assert o["status"] == "applied" and o["evidence_digest"] == digest and "python_executable" not in o
