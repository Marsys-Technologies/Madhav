"""executor_standards.py: launch marker verification + outcome.json (no network, no database)."""
import hashlib
import json
import os
import shutil
import stat
import sys
import time

import pytest

from gate_v2_helpers import GATE_DIR, staged, world  # noqa: F401

sys.path.insert(0, str(GATE_DIR))
import executor_standards as es  # noqa: E402

PLAN = "a" * 64
DIGEST = "b" * 64


@pytest.fixture()
def gdir(tmp_path):
    d = tmp_path / "gate"
    d.mkdir()
    for f in ("prerun_gate.py", "run_gated.sh", "executor_standards.py"):
        shutil.copy(GATE_DIR / f, d / f)
    return d


def marker(gdir, **kw):
    return es.make_marker(str(gdir / "prerun_gate.py"), str(gdir / "run_gated.sh"), **kw)


# ------------------------------------------------------------ launch marker
def test_a_fresh_marker_verifies(gdir):
    assert es.verify_marker(marker(gdir), gate_dir=str(gdir)) == (True, "ok")


def test_marker_shape_is_documented_and_unique_per_launch(gdir):
    m1, m2 = marker(gdir), marker(gdir)
    p = m1.split(".")
    assert len(p) == 6 and p[0] == "v1" and len(p[1]) == len(p[2]) == len(p[5]) == 64 and len(p[4]) == 32
    assert m1 != m2                                                          # nonce
    fp = es.fingerprint(str(gdir))
    assert p[1] == fp["gate_sha256"] and p[2] == fp["run_gated_sha256"]


@pytest.mark.parametrize("bad,reason", [
    (None, "no_marker"), ("", "no_marker"), ("garbage", "malformed_marker"), ("v1.a.b.c.d.e", "malformed_marker"),
    ("v2." + "0." * 4 + "0", "malformed_marker"),
])
def test_missing_or_malformed_marker_is_refused(gdir, bad, reason):
    assert es.verify_marker(bad, gate_dir=str(gdir)) == (False, reason)


def test_a_forged_check_is_refused(gdir):
    p = marker(gdir).split(".")
    p[5] = "0" * 64
    assert es.verify_marker(".".join(p), gate_dir=str(gdir)) == (False, "marker_check_mismatch")


def test_a_marker_for_an_edited_gate_file_is_refused(gdir):
    m = marker(gdir)
    (gdir / "prerun_gate.py").write_text((gdir / "prerun_gate.py").read_text() + "\n# edited\n")
    assert es.verify_marker(m, gate_dir=str(gdir)) == (False, "gate_sha_differs_from_live_gate_file")


def test_a_marker_for_an_edited_launcher_is_refused(gdir):
    m = marker(gdir)
    (gdir / "run_gated.sh").write_text((gdir / "run_gated.sh").read_text() + "\n# edited\n")
    assert es.verify_marker(m, gate_dir=str(gdir)) == (False, "launcher_sha_differs_from_live_run_gated")


def test_shas_pinned_in_the_plan_must_match(gdir):
    m, fp = marker(gdir), es.fingerprint(str(gdir))
    assert es.verify_marker(m, str(gdir), fp["gate_sha256"], fp["run_gated_sha256"])[0]
    assert es.verify_marker(m, str(gdir), "0" * 64, None) == (False, "gate_sha_differs_from_plan")
    assert es.verify_marker(m, str(gdir), None, "0" * 64) == (False, "launcher_sha_differs_from_plan")


def test_stale_and_future_markers_are_refused(gdir):
    now = time.time()
    assert es.verify_marker(marker(gdir, now=now - 7 * 3600), gate_dir=str(gdir)) == (False, "marker_stale")
    assert es.verify_marker(marker(gdir, now=now - 5 * 3600), gate_dir=str(gdir))[0]
    assert es.verify_marker(marker(gdir, now=now + 3600), gate_dir=str(gdir)) == (False, "marker_from_the_future")


def test_require_gate_launch_exits_93_without_a_marker_and_returns_the_fingerprint_with_one(gdir, capsys):
    with pytest.raises(SystemExit) as e:
        es.require_gate_launch({}, gate_dir=str(gdir))
    assert e.value.code == 93 and "REFUSED" in capsys.readouterr().err
    fp = es.require_gate_launch({es.MARKER_ENV: marker(gdir)}, gate_dir=str(gdir))
    assert fp == es.fingerprint(str(gdir))


def test_the_refusal_message_never_echoes_the_marker(gdir, capsys):
    m = marker(gdir)[:-3] + "bad"
    with pytest.raises(SystemExit):
        es.require_gate_launch({es.MARKER_ENV: m}, gate_dir=str(gdir))
    assert m not in capsys.readouterr().err


def test_gate_shas_are_part_of_the_plan_hash(gdir):
    fp = es.fingerprint(str(gdir))
    h = es.bind_gate_into_plan_hash(PLAN, fp)
    assert len(h) == 64 and h != PLAN
    (gdir / "prerun_gate.py").write_text("# other gate\n")
    assert es.bind_gate_into_plan_hash(PLAN, es.fingerprint(str(gdir))) != h


def test_cli_make_marker_and_fingerprint(gdir):
    import subprocess
    m = subprocess.run([sys.executable, str(gdir / "executor_standards.py"), "make-marker", str(gdir / "prerun_gate.py"), str(gdir / "run_gated.sh")],
                       capture_output=True, text=True).stdout
    assert es.verify_marker(m, gate_dir=str(gdir)) == (True, "ok")
    fp = json.loads(subprocess.run([sys.executable, str(gdir / "executor_standards.py"), "fingerprint", str(gdir)], capture_output=True, text=True).stdout)
    assert fp == es.fingerprint(str(gdir))


# ------------------------------------------------------------ outcome file
@pytest.fixture()
def ex(tmp_path):
    p = tmp_path / "executor.py"
    p.write_text("print('executor')\n")
    return p


def mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def test_outcome_file_fields_and_permissions_for_each_status(tmp_path, ex, gdir):
    fp = es.fingerprint(str(gdir))
    ev = tmp_path / "evidence" / "run1"
    for status, digest, checks in [("dry_run", DIGEST, []), ("applied", DIGEST, []), ("failed", None, ["P5_no_build_in_flight", "E_digest"])]:
        path = es.write_outcome(str(ev), status, str(ex), PLAN, fp, digest, checks, now=1_700_000_000)
        body = json.loads(open(path).read())
        assert body == {"schema": "executor_outcome_v1", "status": status, "utc": "2023-11-14T22:13:20Z",
                        "executor_sha256": hashlib.sha256(ex.read_bytes()).hexdigest(), "plan_hash": PLAN,
                        "gate_sha256": fp["gate_sha256"], "run_gated_sha256": fp["run_gated_sha256"],
                        "evidence_digest": digest, "failed_checks": checks}
        assert mode(path) == 0o600 and mode(ev) == 0o700
    assert [p.name for p in ev.iterdir()] == ["outcome.json"]                # no temp file left behind


def test_an_existing_loose_directory_is_forced_to_0700(tmp_path, ex, gdir):
    ev = tmp_path / "loose"
    ev.mkdir(mode=0o755)
    os.chmod(ev, 0o755)
    es.write_outcome(str(ev), "dry_run", str(ex), PLAN, es.fingerprint(str(gdir)), DIGEST)
    assert mode(ev) == 0o700


@pytest.mark.parametrize("kw", [dict(status="weird"), dict(status="failed", failed_checks=[]), dict(status="applied", failed_checks=["x"]),
                                dict(status="failed", failed_checks=["has space"]), dict(status="dry_run", evidence_digest="short")])
def test_invalid_outcomes_are_rejected(tmp_path, ex, gdir, kw):
    with pytest.raises(ValueError):
        es.write_outcome(str(tmp_path / "ev"), kw.pop("status"), str(ex), PLAN, es.fingerprint(str(gdir)), **kw)


def read(tmp_path, name="ev"):
    return json.loads((tmp_path / name / "outcome.json").read_text())


def test_guard_records_dry_run_and_applied(tmp_path, ex, gdir):
    fp = es.fingerprint(str(gdir))
    with es.outcome_guard(str(tmp_path / "ev"), str(ex), PLAN, fp) as o:
        o.dry_run(DIGEST)
    assert read(tmp_path)["status"] == "dry_run" and read(tmp_path)["evidence_digest"] == DIGEST
    with es.outcome_guard(str(tmp_path / "ev"), str(ex), PLAN, fp) as o:
        o.applied(DIGEST)
    assert read(tmp_path)["status"] == "applied"


def test_guard_writes_failed_for_an_explicit_refusal_an_exception_a_systemexit_and_a_silent_return(tmp_path, ex, gdir):
    fp = es.fingerprint(str(gdir))
    with es.outcome_guard(str(tmp_path / "ev"), str(ex), PLAN, fp) as o:
        o.fail(["P5_no_build_in_flight", "V_verdict_diff"])
    assert read(tmp_path)["failed_checks"] == ["P5_no_build_in_flight", "V_verdict_diff"]
    with pytest.raises(RuntimeError):
        with es.outcome_guard(str(tmp_path / "ev"), str(ex), PLAN, fp):
            raise RuntimeError("boom")
    assert read(tmp_path)["status"] == "failed" and read(tmp_path)["failed_checks"] == ["RuntimeError"]
    with pytest.raises(SystemExit):
        with es.outcome_guard(str(tmp_path / "ev"), str(ex), PLAN, fp):
            raise SystemExit(3)
    assert read(tmp_path)["failed_checks"] == ["exit_3"]
    with es.outcome_guard(str(tmp_path / "ev"), str(ex), PLAN, fp):
        pass
    assert read(tmp_path)["status"] == "failed" and read(tmp_path)["failed_checks"] == ["no_outcome_recorded"]


def test_guard_does_not_overwrite_a_declared_success_when_the_block_raises_afterwards(tmp_path, ex, gdir):
    fp = es.fingerprint(str(gdir))
    with pytest.raises(RuntimeError):
        with es.outcome_guard(str(tmp_path / "ev"), str(ex), PLAN, fp) as o:
            o.applied(DIGEST)
            raise RuntimeError("late")
    assert read(tmp_path)["status"] == "applied"


def test_no_secret_or_environment_is_in_the_outcome(tmp_path, ex, gdir, monkeypatch):
    monkeypatch.setenv("PGPASSWORD", "sekrit")
    es.write_outcome(str(tmp_path / "ev"), "dry_run", str(ex), PLAN, es.fingerprint(str(gdir)), DIGEST)
    assert "sekrit" not in (tmp_path / "ev" / "outcome.json").read_text()
