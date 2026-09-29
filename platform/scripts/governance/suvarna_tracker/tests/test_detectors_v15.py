"""v1.5 plan-set additions (Astra review fold, N-28/N-29): evidence_verified, ci_job_passed,
elevated_interface_ok — required once plan_model.json's v1.5 fold referenced these three detector
types with no registered `d_<type>` method. No network beyond fakes; no real gh/git calls."""
import json
import os

import pytest

from suvarna_tracker import detectors as D

from test_detectors_v13 import dets, elevation_module_source, make_nik, wait_result, wrap_run


@pytest.fixture
def nik(tmp_path):
    return make_nik(tmp_path)


# ============================================================================================
# evidence_verified
# ============================================================================================

def test_evidence_verified_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "evidence_verified", "path": "", "expect": {}}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_evidence_verified_no_file_yet_is_pending(nik, tmp_path):
    home = tmp_path / "home"
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "launch/NS_VERIFY.json", "expect": {"NS.1": "PASS"}}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "no evidence file yet" in r.detail


def _write_evidence(home, rel_path, data):
    full = os.path.join(str(home), "evidence", rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return full


def test_evidence_verified_matching_expect_is_done(nik, tmp_path):
    home = tmp_path / "home"
    _write_evidence(home, "launch/NS_VERIFY.json", {"NS.1": "PASS"})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "launch/NS_VERIFY.json", "expect": {"NS.1": "PASS"}}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_evidence_verified_mismatched_value_is_pending_never_done(nik, tmp_path):
    home = tmp_path / "home"
    _write_evidence(home, "launch/NS_VERIFY.json", {"NS.1": "FAIL"})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "launch/NS_VERIFY.json", "expect": {"NS.1": "PASS"}}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "NS.1" in r.detail


def test_evidence_verified_boolean_false_expect_requires_exact_false(nik, tmp_path):
    """F3.GUARD's own shape: {"refusal_path_present": false} — a present-but-true value, or the
    key simply missing, must never be read as satisfying 'false' by omission."""
    home = tmp_path / "home"
    _write_evidence(home, "F3/GUARD.json", {"refusal_path_present": True})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "F3/GUARD.json", "expect": {"refusal_path_present": False}}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"

    _write_evidence(home, "F3/GUARD.json", {"refusal_path_present": False})
    d2 = dets(nik, str(tmp_path), home=str(home))
    spec2 = {"type": "evidence_verified", "path": "F3/GUARD.json", "expect": {"refusal_path_present": False}}
    d2.poll([spec2])
    r2 = wait_result(d2, spec2)
    assert r2.status == "done"


def test_evidence_verified_missing_required_key_is_pending(nik, tmp_path):
    home = tmp_path / "home"
    _write_evidence(home, "E5.6/REHEARSAL.json", {"result": "PASS"})  # no 'cases' key
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "E5.6/REHEARSAL.json", "expect": {"result": "PASS"}, "required": ["cases"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "cases" in r.detail


def test_evidence_verified_required_key_present_is_done(nik, tmp_path):
    home = tmp_path / "home"
    _write_evidence(home, "E5.6/REHEARSAL.json", {"result": "PASS", "cases": ["c1", "c2"]})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "E5.6/REHEARSAL.json", "expect": {"result": "PASS"}, "required": ["cases"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_evidence_verified_commit_pin_mismatch_is_pending(nik, tmp_path):
    home = tmp_path / "home"
    _write_evidence(home, "launch/LG1_GATE_EVAL.json", {"result": "PASS", "control_commit": "deadbeef"})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "launch/LG1_GATE_EVAL.json", "expect": {"result": "PASS"},
           "commit_key": "control_commit", "commit": "cafef00d"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "control_commit" in r.detail


def test_evidence_verified_commit_pin_match_is_done(nik, tmp_path):
    home = tmp_path / "home"
    _write_evidence(home, "launch/LG1_GATE_EVAL.json", {"result": "PASS", "control_commit": "deadbeef"})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "launch/LG1_GATE_EVAL.json", "expect": {"result": "PASS"},
           "commit_key": "control_commit", "commit": "deadbeef"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_evidence_verified_empty_commit_pin_is_skipped_not_checked(nik, tmp_path):
    """The real LG.* items ship with `"commit": ""` (not yet pinned) — this must not itself block
    the item on an empty pin; it just skips that one check."""
    home = tmp_path / "home"
    _write_evidence(home, "launch/LG1_GATE_EVAL.json", {"result": "PASS"})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "launch/LG1_GATE_EVAL.json", "expect": {"result": "PASS"},
           "commit_key": "control_commit", "commit": ""}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done"


def test_evidence_verified_stale_past_max_age_is_pending(nik, tmp_path):
    home = tmp_path / "home"
    full = _write_evidence(home, "launch/NS_VERIFY.json", {"NS.1": "PASS"})
    old = os.path.getmtime(full) - 3600 * 100
    os.utime(full, (old, old))
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "launch/NS_VERIFY.json", "expect": {"NS.1": "PASS"}, "max_age_hours": 48}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "old" in r.detail


def test_evidence_verified_not_a_json_object_is_error(nik, tmp_path):
    home = tmp_path / "home"
    full = os.path.join(str(home), "evidence", "launch", "NS_VERIFY.json")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write("[1, 2, 3]")
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_verified", "path": "launch/NS_VERIFY.json", "expect": {"NS.1": "PASS"}}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"


# ============================================================================================
# ci_job_passed
# ============================================================================================

def test_ci_job_passed_empty_job_is_pinned_by_unknown(nik, tmp_path):
    """Every real item using this detector today ships with `job: ""` — CODE-3's unpinned-spec
    convention applies: `unknown`/error, never a guess at which job to check."""
    d = dets(nik, str(tmp_path))
    spec = {"type": "ci_job_passed", "workflow": ".github/workflows/ci.yml", "job": "",
           "paths": ["a.py"], "pinned_by": "Track E"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error" and "unknown" in r.detail and "Track E" in r.detail


def test_ci_job_passed_paths_not_on_main_is_pending(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:3] == ["git", "cat-file", "-e"], 1, ""),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "ci_job_passed", "workflow": ".github/workflows/ci.yml", "job": "test-e5-1",
           "paths": ["platform/scripts/governance/nikasha_certify.py"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "not yet on main" in r.detail


def test_ci_job_passed_no_run_yet_is_pending(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:3] == ["git", "cat-file", "-e"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "rev-parse"], 0, "a" * 40 + "\n"),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "workflows/ci.yml/runs" in cmd[2], 0,
         json.dumps({"workflow_runs": []})),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "ci_job_passed", "workflow": ".github/workflows/ci.yml", "job": "test-e5-1", "paths": ["a.py"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "no CI run yet" in r.detail


def test_ci_job_passed_run_still_in_progress_is_running(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:3] == ["git", "cat-file", "-e"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "rev-parse"], 0, "a" * 40 + "\n"),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "workflows/ci.yml/runs" in cmd[2], 0,
         json.dumps({"workflow_runs": [{"id": 1, "status": "in_progress"}]})),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "ci_job_passed", "workflow": ".github/workflows/ci.yml", "job": "test-e5-1", "paths": ["a.py"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "running"


def test_ci_job_passed_job_succeeded_is_done(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:3] == ["git", "cat-file", "-e"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "rev-parse"], 0, "a" * 40 + "\n"),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "workflows/ci.yml/runs" in cmd[2], 0,
         json.dumps({"workflow_runs": [{"id": 55, "status": "completed"}]})),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "runs/55/jobs" in cmd[2], 0,
         json.dumps({"jobs": [{"name": "test-e5-1", "conclusion": "success"}]})),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "ci_job_passed", "workflow": ".github/workflows/ci.yml", "job": "test-e5-1", "paths": ["a.py"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_ci_job_passed_job_failed_is_blocked(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:3] == ["git", "cat-file", "-e"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "rev-parse"], 0, "a" * 40 + "\n"),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "workflows/ci.yml/runs" in cmd[2], 0,
         json.dumps({"workflow_runs": [{"id": 55, "status": "completed"}]})),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "runs/55/jobs" in cmd[2], 0,
         json.dumps({"jobs": [{"name": "test-e5-1", "conclusion": "failure"}]})),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "ci_job_passed", "workflow": ".github/workflows/ci.yml", "job": "test-e5-1", "paths": ["a.py"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked"


def test_ci_job_passed_job_name_not_found_is_error(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:3] == ["git", "cat-file", "-e"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "rev-parse"], 0, "a" * 40 + "\n"),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "workflows/ci.yml/runs" in cmd[2], 0,
         json.dumps({"workflow_runs": [{"id": 55, "status": "completed"}]})),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "runs/55/jobs" in cmd[2], 0,
         json.dumps({"jobs": [{"name": "some-other-job", "conclusion": "success"}]})),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "ci_job_passed", "workflow": ".github/workflows/ci.yml", "job": "test-e5-1", "paths": ["a.py"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error" and "test-e5-1" in r.detail


def test_ci_job_passed_gh_failure_is_error(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:3] == ["git", "cat-file", "-e"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "rev-parse"], 0, "a" * 40 + "\n"),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "workflows/ci.yml/runs" in cmd[2], 1, "gh: HTTP 403"),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "ci_job_passed", "workflow": ".github/workflows/ci.yml", "job": "test-e5-1", "paths": ["a.py"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"


# ============================================================================================
# elevated_interface_ok (F7, E6.3t)
# ============================================================================================

def test_elevated_interface_ok_error_before_module_wired(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2],
         1, "fatal: not on main"),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "elevated_interface_ok", "ref": "origin/main"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error" and r.detail == D.ELEVATION_NOT_WIRED_DETAIL


def test_elevated_interface_ok_calls_the_pinned_interface_and_succeeds(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2],
         0, elevation_module_source(["clean_a", "clean_b"])),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "elevated_interface_ok", "ref": "origin/main"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0
    assert "2 asset id(s)" in r.detail


def test_elevated_interface_ok_blocked_when_module_still_uses_retired_one_arg_signature(nik, tmp_path, monkeypatch):
    """The exact F7 regression this detector exists to catch — E6.3t's pre-fix version could not
    tell a conforming (ref, repo) implementation from a still-retired (cfg) one."""
    legacy_source = "def elevated_assets(cfg):\n    return {'clean_a'}\n"
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2],
         0, legacy_source),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "elevated_interface_ok", "ref": "origin/main"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked" and "(ref, repo)" in r.detail


def test_elevated_interface_ok_blocked_when_return_type_is_not_a_set(nik, tmp_path, monkeypatch):
    bad_source = "def elevated_assets(ref, repo):\n    return ['clean_a']\n"  # a list, not a set
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2],
         0, bad_source),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "elevated_interface_ok", "ref": "origin/main"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked" and "not a set" in r.detail


def test_elevated_interface_ok_error_when_the_function_itself_raises(nik, tmp_path, monkeypatch):
    raising_source = "def elevated_assets(ref, repo):\n    raise RuntimeError('db unavailable')\n"
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2],
         0, raising_source),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "elevated_interface_ok", "ref": "origin/main"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error" and "db unavailable" in r.detail


def test_elevated_interface_ok_defaults_ref_to_elevated_assets_ref(nik, tmp_path, monkeypatch):
    d = dets(nik, str(tmp_path))
    assert D.ELEVATED_ASSETS_REF == "origin/main"
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2],
         0, elevation_module_source(["clean_a"])),
    ])
    spec = {"type": "elevated_interface_ok"}  # no ref at all
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done"


def test_new_detector_types_are_registered_and_have_ttls():
    for typ in ("evidence_verified", "ci_job_passed", "elevated_interface_ok"):
        assert hasattr(D.Detectors, f"d_{typ}")
        assert typ in D.Detectors.TTL
