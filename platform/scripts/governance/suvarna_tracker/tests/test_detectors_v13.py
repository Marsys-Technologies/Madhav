"""New detector types for plan v1.3 (arch §11.7, built by L.13): prs_merged, main_has_files,
scorecard_pass, migrations_applied, register_rows_state, register_freeze_clean, monitor_check_ok,
deployed_contains, wave_deployed, assets_elevated, registry_coverage, ledger_no_open_gap_on, plus
the family-aware `levels_elevated` (`exclude: family_set`). No network, no real DB: every git/gh/
psql/monitor/suvarna-build call is either a fake (via a wrapped `D._run`) or a real, local,
offline git repo (the same pattern `test_detectors_server.py` already uses for the register).
"""
import json
import os
import subprocess

import pytest

from suvarna_tracker import detectors as D
from suvarna_tracker.server import REPO_ROOT

REGISTER = (
    "# register\n"
    "| # | change | surfaced by | severity | depends_on | effort_h | state |\n"
    "|---|---|---|---|---|---|---|\n"
    "| R1 | a | s | BLOCKS_FREEZE | — | 1 | OPEN |\n"
    "| R2 | b | s | BLOCKS_FREEZE | — | 1 | CLOSED 2026-09-28 |\n"
    "| R3 | c | s | BLOCKS_FREEZE | — | 1 | DEFERRED — see B.U |\n"
    "| R4 | d | s | DEGRADES | — | 1 | OPEN |\n"
)

GAPS = "\n".join([
    json.dumps({"asset": "_schema"}),
    json.dumps({"asset": "clean_a", "gap_id": "g-clean-a", "state": "CLOSED", "kind": "gap", "criterion": "Cost.build_time"}),
    json.dumps({"asset": "with_gap", "gap_id": "g-with-gap", "state": "OPEN", "kind": "gap", "criterion": "Cost.build_time"}),
    json.dumps({"asset": "with_gap2", "gap_id": "g-with-gap2", "state": "OPEN", "kind": "gap", "criterion": "Dens.other"}),
]) + "\n"

CERTS = "\n".join([
    json.dumps({"asset": "_schema"}),
    json.dumps({"asset": "clean_a", "criterion": "X", "verdict": "PASS"}),
]) + "\n"


def _git_init_commit(root) -> None:
    env = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
           "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "seed"]):
        subprocess.run(cmd, cwd=str(root), env=env, check=True, capture_output=True)


def make_nik(tmp_path, name="nik", extra_files: dict | None = None) -> str:
    root = tmp_path / name
    (root / "00_ARCHITECTURE/briefs/nirmana").mkdir(parents=True)
    (root / "00_ARCHITECTURE/control").mkdir(parents=True)
    (root / "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md").write_text(REGISTER)
    (root / "00_ARCHITECTURE/control/asset_gaps.jsonl").write_text(GAPS)
    (root / "00_ARCHITECTURE/control/asset_certs.jsonl").write_text(CERTS)
    for rel, content in (extra_files or {}).items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    _git_init_commit(root)
    return str(root)


@pytest.fixture
def nik(tmp_path):
    return make_nik(tmp_path)


def dets(nik, repo, home=None, pgenv=None):
    return D.Detectors(D.Config(repo=repo, nikasha_root=nik, pgenv=pgenv, home=home or repo))


def wait_result(det, spec, timeout=10):
    import time
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = det.get(spec)
        if r is not None:
            return r
        time.sleep(0.05)
    raise AssertionError("detector never produced a result")


def wrap_run(monkeypatch, table):
    """Intercept specific `D._run` calls (matched by a predicate over argv), falling back to the
    real `_run` for anything unmatched — so a test can fake gh/suvarna-build/a fictitious remote
    while still exercising real, local, offline git against a committed fixture repo."""
    orig = D._run

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        for pred, rc, out in table:
            if pred(cmd):
                return rc, out
        return orig(cmd, cwd=cwd, timeout=timeout, shell=shell, env=env)

    monkeypatch.setattr(D, "_run", fake)


# ============================================================================================
# prs_merged
# ============================================================================================

def test_prs_merged_empty_params_is_pending_not_error(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "prs_merged", "prs": [], "pinned_by": "L.11"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_prs_merged_all_merged_is_done(nik, tmp_path, monkeypatch):
    def gh(cmd):
        return cmd[:3] == ["gh", "pr", "view"]
    wrap_run(monkeypatch, [(gh, 0, json.dumps({"state": "MERGED", "mergedAt": "2026-09-29"}))])
    d = dets(nik, str(tmp_path))
    spec = {"type": "prs_merged", "prs": [1, 2]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_prs_merged_mixed_states_is_blocked_with_detail(nik, tmp_path, monkeypatch):
    states = {"1": "MERGED", "2": "OPEN", "3": "CLOSED"}
    orig = D._run

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": states[cmd[3]]})
        return orig(cmd, cwd=cwd, timeout=timeout, shell=shell, env=env)

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path))
    spec = {"type": "prs_merged", "prs": [1, 2, 3]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked"
    assert "1/3 merged" in r.detail and "closed without merging: [3]" in r.detail


def test_prs_merged_gh_failure_is_error(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [(lambda cmd: cmd[:3] == ["gh", "pr", "view"], 1, "gh: not found")])
    d = dets(nik, str(tmp_path))
    spec = {"type": "prs_merged", "prs": [9]}
    d.poll([spec])
    assert wait_result(d, spec).status == "error"


# ============================================================================================
# main_has_files
# ============================================================================================

def test_main_has_files_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_has_files", "paths": []}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_main_has_files_all_present_is_done(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:3] == ["git", "cat-file", "-e"], 0, ""),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_has_files", "paths": ["a.py", "b.py"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_main_has_files_partial_is_running_with_missing_named(nik, tmp_path, monkeypatch):
    present = {"a.py"}

    def catfile(cmd):
        return cmd[:3] == ["git", "cat-file", "-e"]

    orig = D._run

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:2] == ["git", "fetch"]:
            return 0, ""
        if catfile(cmd):
            path = cmd[3].split(":", 1)[1]
            return (0, "") if path in present else (1, "")
        return orig(cmd, cwd=cwd, timeout=timeout, shell=shell, env=env)

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_has_files", "paths": ["a.py", "b.py", "c.py"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "running"
    assert abs(r.progress - 1 / 3) < 1e-9
    assert "b.py" in r.detail and "c.py" in r.detail


# ============================================================================================
# scorecard_pass
# ============================================================================================

def test_scorecard_pass_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "scorecard_pass", "ref": "origin/main", "path": "", "tests": ["T1"]}
    d.poll([spec])
    assert wait_result(d, spec).status == "pending"


def test_scorecard_pass_not_yet_on_ref_is_pending(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"], 1, "fatal: path not in ref"),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "scorecard_pass", "ref": "origin/main", "path": "x.json", "tests": ["T1"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "not yet at" in r.detail


def test_scorecard_pass_all_pass_with_inspector_commit_is_done(nik, tmp_path, monkeypatch):
    scorecard = json.dumps({"tests": {"T1": "PASS", "T2": "PASS"}, "inspector_commit": "abc123"})
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"], 0, scorecard),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "scorecard_pass", "ref": "origin/main", "path": "x.json", "tests": ["T1", "T2"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and "abc123" in r.detail


def test_scorecard_pass_missing_inspector_commit_never_shows_done(nik, tmp_path, monkeypatch):
    scorecard = json.dumps({"tests": {"T1": "PASS"}})
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"], 0, scorecard),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "scorecard_pass", "ref": "origin/main", "path": "x.json", "tests": ["T1"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status != "done" and "no inspector commit" in r.detail


def test_scorecard_pass_failing_test_is_running_not_done(nik, tmp_path, monkeypatch):
    scorecard = json.dumps({"tests": {"T1": "PASS", "T2": "FAIL"}, "inspector_commit": "abc123"})
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"], 0, scorecard),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "scorecard_pass", "ref": "origin/main", "path": "x.json", "tests": ["T1", "T2"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "running" and "T2" in r.detail


# ============================================================================================
# migrations_applied
# ============================================================================================

def test_migrations_applied_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "migrations_applied", "numbers": []}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_migrations_applied_without_credential_file_is_error_not_done(nik, tmp_path):
    d = dets(nik, str(tmp_path))  # pgenv=None
    spec = {"type": "migrations_applied", "numbers": [1094]}
    d.poll([spec])
    assert wait_result(d, spec).status == "error"


def test_migrations_applied_partial(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, "1094_foo.sql\n")])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "migrations_applied", "numbers": [1094, 1095]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "running" and r.progress == 0.5
    assert "1095" in r.detail


def test_migrations_applied_all_present_is_done(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, "1094_foo.sql\n1095_bar.sql\n")])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "migrations_applied", "numbers": [1094, 1095]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


# ============================================================================================
# register_rows_state
# ============================================================================================

def test_register_rows_state_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_rows_state", "rows": [], "states": []}
    d.poll([spec])
    assert wait_result(d, spec).status == "pending"


def test_register_rows_state_partial(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_rows_state", "rows": ["R1", "R2"], "states": ["CLOSED", "DONE", "DEFERRED"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "running" and r.progress == 0.5
    assert "R1=OPEN" in r.detail


def test_register_rows_state_all_in_allowed_states_is_done(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_rows_state", "rows": ["R2", "R3"], "states": ["CLOSED", "DONE", "DEFERRED"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_register_rows_state_unknown_row_is_error(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_rows_state", "rows": ["R999"], "states": ["CLOSED"]}
    d.poll([spec])
    assert wait_result(d, spec).status == "error"


# ============================================================================================
# register_freeze_clean
# ============================================================================================

def test_register_freeze_clean_open_blocker_is_not_done(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_freeze_clean", "allow_deferred": ["R3"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status != "done"
    assert "R1=OPEN" in r.detail
    assert "R3=DEFERRED" not in r.detail  # R3 is excused by allow_deferred


def test_register_freeze_clean_allow_deferred_excuses_the_named_row(nik, tmp_path):
    """With R1 (the only non-excused blocker) also closed, and R3 excused via allow_deferred, the
    gate reads done. Build a register where every BLOCKS_FREEZE row is CLOSED/DONE except one
    DEFERRED, excused."""
    root = tmp_path / "nik_freeze_clean"
    (root / "00_ARCHITECTURE/briefs/nirmana").mkdir(parents=True)
    (root / "00_ARCHITECTURE/control").mkdir(parents=True)
    reg = (
        "# register\n"
        "| # | change | surfaced by | severity | depends_on | effort_h | state |\n"
        "|---|---|---|---|---|---|---|\n"
        "| R1 | a | s | BLOCKS_FREEZE | — | 1 | CLOSED |\n"
        "| R2 | b | s | BLOCKS_FREEZE | — | 1 | DONE |\n"
        "| R3 | c | s | BLOCKS_FREEZE | — | 1 | DEFERRED |\n"
    )
    (root / "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md").write_text(reg)
    (root / "00_ARCHITECTURE/control/asset_gaps.jsonl").write_text(json.dumps({"asset": "_schema"}) + "\n")
    (root / "00_ARCHITECTURE/control/asset_certs.jsonl").write_text(json.dumps({"asset": "_schema"}) + "\n")
    _git_init_commit(root)
    d = dets(str(root), str(tmp_path))
    spec = {"type": "register_freeze_clean", "allow_deferred": ["R3"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_register_freeze_clean_no_blockers_at_all_is_done(tmp_path):
    root = tmp_path / "nik_no_blockers"
    (root / "00_ARCHITECTURE/briefs/nirmana").mkdir(parents=True)
    (root / "00_ARCHITECTURE/control").mkdir(parents=True)
    reg = (
        "# register\n"
        "| # | change | surfaced by | severity | depends_on | effort_h | state |\n"
        "|---|---|---|---|---|---|---|\n"
        "| R1 | a | s | DEGRADES | — | 1 | OPEN |\n"
    )
    (root / "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md").write_text(reg)
    (root / "00_ARCHITECTURE/control/asset_gaps.jsonl").write_text(json.dumps({"asset": "_schema"}) + "\n")
    (root / "00_ARCHITECTURE/control/asset_certs.jsonl").write_text(json.dumps({"asset": "_schema"}) + "\n")
    _git_init_commit(root)
    d = dets(str(root), str(tmp_path))
    spec = {"type": "register_freeze_clean", "allow_deferred": []}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done"


# ============================================================================================
# monitor_check_ok
# ============================================================================================

def test_monitor_check_ok_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "monitor_check_ok", "check": ""}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_monitor_check_ok_reads_the_named_check(nik, tmp_path, monkeypatch):
    report = json.dumps({"overall": "ok", "checks": [
        {"name": "credential_readonly", "status": "ok", "detail": "no write path"},
        {"name": "builder_scope", "status": "block", "detail": "grants wrong"},
    ]})

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        assert cmd[1:4] == ["-m", "suvarna_tracker.monitor", "--once"]
        return 0, report

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path))
    ok_spec = {"type": "monitor_check_ok", "check": "credential_readonly"}
    block_spec = {"type": "monitor_check_ok", "check": "builder_scope"}
    d.poll([ok_spec, block_spec])
    r_ok = wait_result(d, ok_spec)
    r_block = wait_result(d, block_spec)
    assert r_ok.status == "done" and r_ok.progress == 1.0
    assert r_block.status == "blocked"


def test_monitor_check_ok_unknown_check_name_is_error(nik, tmp_path, monkeypatch):
    report = json.dumps({"overall": "ok", "checks": [{"name": "db_proxy", "status": "ok", "detail": "up"}]})
    monkeypatch.setattr(D, "_run", lambda *a, **k: (0, report))
    d = dets(nik, str(tmp_path))
    spec = {"type": "monitor_check_ok", "check": "no_such_check"}
    d.poll([spec])
    assert wait_result(d, spec).status == "error"


# ============================================================================================
# deployed_contains
# ============================================================================================

def test_deployed_contains_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "deployed_contains", "component": "job", "prs": [], "pinned_by": "L.11"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_deployed_contains_done_when_the_merge_sha_is_in_the_tag(nik, tmp_path, monkeypatch):
    sha = "abcdef1234567890"

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": sha}})
        if cmd[:2] == ["suvarna-build", "--preflight"]:
            return 0, json.dumps({"job_image_tag": f"job-{sha[:12]}-prod"})
        raise AssertionError(f"unexpected command {cmd}")

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path))
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_deployed_contains_pending_when_pr_not_merged(nik, tmp_path, monkeypatch):
    monkeypatch.setattr(D, "_run", lambda cmd, **k: (0, json.dumps({"state": "OPEN"})) if cmd[:3] == ["gh", "pr", "view"] else (1, ""))
    d = dets(nik, str(tmp_path))
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    assert wait_result(d, spec).status == "pending"


def test_deployed_contains_running_when_merged_but_not_yet_deployed(nik, tmp_path, monkeypatch):
    sha = "1112223334445556"

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": sha}})
        if cmd[:2] == ["suvarna-build", "--preflight"]:
            return 0, json.dumps({"job_image_tag": "job-oldsha-prod"})
        raise AssertionError(cmd)

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path))
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"  # 0 of 1 present yet


# ============================================================================================
# wave_deployed
# ============================================================================================

def test_wave_deployed_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "wave_deployed", "wave": ""}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_wave_deployed_no_landing_record_yet_is_pending(nik, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "wave_deployed", "wave": "B.W0"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "LANDING.json" in r.detail


def test_wave_deployed_done_when_landing_pr_merged_and_deployed(nik, tmp_path, monkeypatch):
    home = tmp_path / "home"
    landing_dir = home / "evidence" / "B.W0"
    landing_dir.mkdir(parents=True)
    (landing_dir / "LANDING.json").write_text(json.dumps({"pr": 77}))
    sha = "deadbeefcafefeed"

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": sha}})
        if cmd[:2] == ["suvarna-build", "--preflight"]:
            return 0, json.dumps({"job_image_tag": f"job-{sha[:12]}-prod"})
        raise AssertionError(cmd)

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "wave_deployed", "wave": "B.W0"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


# ============================================================================================
# assets_elevated
# ============================================================================================

def test_assets_elevated_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": ""}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_assets_elevated_before_family_assets_json_lands_is_pending(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and "FAMILY_ASSETS.json" in cmd[2], 1, "fatal: not on main"),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": "family_gochara"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "FAMILY_ASSETS.json" in r.detail


def test_assets_elevated_done_when_every_asset_in_the_set_is_elevated(nik, tmp_path, monkeypatch):
    fam = json.dumps({"family_gochara": ["clean_a"]})
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and "FAMILY_ASSETS.json" in cmd[2], 0, fam),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": "family_gochara"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0  # clean_a: PASS cert, no open gap (real nik fixture)


def test_assets_elevated_pending_when_the_set_asset_is_not_elevated(nik, tmp_path, monkeypatch):
    fam = json.dumps({"family_sangam": ["with_gap"]})
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and "FAMILY_ASSETS.json" in cmd[2], 0, fam),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": "family_sangam"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.progress == 0.0


# ============================================================================================
# registry_coverage
# ============================================================================================

def test_registry_coverage_report_not_yet_on_ref_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "registry_coverage"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "not yet" in r.detail


def test_registry_coverage_uncovered_criteria_is_not_done(tmp_path):
    report = json.dumps({"uncovered_required_criteria": ["Gate.L2.foo"], "covered_cells": 900})
    nik2 = make_nik(tmp_path, name="nik_cov_partial", extra_files={D.REGISTRY_COVERAGE_REL_PATH: report})
    d = dets(nik2, str(tmp_path))
    spec = {"type": "registry_coverage"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status != "done" and "Gate.L2.foo" in r.detail


def test_registry_coverage_fully_covered_is_done(tmp_path):
    report = json.dumps({"uncovered_required_criteria": [], "covered_cells": 1143})
    nik2 = make_nik(tmp_path, name="nik_cov_full", extra_files={D.REGISTRY_COVERAGE_REL_PATH: report})
    d = dets(nik2, str(tmp_path))
    spec = {"type": "registry_coverage"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


# ============================================================================================
# ledger_no_open_gap_on
# ============================================================================================

def test_ledger_no_open_gap_on_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "ledger_no_open_gap_on", "criteria_prefixes": []}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_ledger_no_open_gap_on_finds_the_open_matching_row(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "ledger_no_open_gap_on", "criteria_prefixes": ["Cost."]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "g-with-gap" in r.detail  # clean_a's Cost. gap is CLOSED, with_gap's is OPEN


def test_ledger_no_open_gap_on_clean_prefixes_is_done(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "ledger_no_open_gap_on", "criteria_prefixes": ["Count.", "Complete.", "Reach."]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


# ============================================================================================
# levels_elevated: family-aware `exclude: family_set`
# ============================================================================================

@pytest.fixture(autouse=True)
def _reset_dag_cache():
    D._dag_cache.update(at=0.0, levels={}, layer={})
    yield
    D._dag_cache.update(at=0.0, levels={}, layer={})


def _fake_registry_rows(rows):
    """rows: list of (asset_id, layer, deps_csv) -> the psql-shaped tab-separated text dag_levels expects."""
    return "\n".join(f"{a}\t{l}\t{deps}" for a, l, deps in rows) + "\n"


def test_levels_elevated_without_exclude_is_unchanged(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    rows = _fake_registry_rows([("clean_a", "L1", "")])
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows)])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "levels_elevated", "levels": [0, 0]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and "excluded" not in r.detail


def test_levels_elevated_exclude_family_set_pending_before_e63(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    rows = _fake_registry_rows([("clean_a", "L1", "")])
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows),
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and "FAMILY_ASSETS.json" in cmd[2], 1, "fatal: not on main"),
    ])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "levels_elevated", "levels": [0, 0], "exclude": "family_set"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "FAMILY_ASSETS.json" in r.detail


def test_levels_elevated_exclude_family_set_drops_family_and_reader_assets(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    # clean_a: elevated, non-family. with_gap: has an open gap, but is excluded as a family asset —
    # so its non-elevation must never keep the wave from reading done.
    rows = _fake_registry_rows([("clean_a", "L1", ""), ("with_gap", "L3", "")])
    fam = json.dumps({"family_gochara": ["with_gap"]})
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows),
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and "FAMILY_ASSETS.json" in cmd[2], 0, fam),
    ])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "levels_elevated", "levels": [0, 0], "exclude": "family_set"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0
    assert "1 family/reader asset(s) excluded" in r.detail


# ============================================================================================
# Coverage: every detector type the real plan_model.json references is registered
# ============================================================================================

def test_every_detector_type_in_the_real_plan_model_has_a_registered_detector():
    model_path = os.path.join(REPO_ROOT, "00_ARCHITECTURE", "control", "suvarna", "plan_model.json")
    with open(model_path, encoding="utf-8") as f:
        model = json.load(f)
    types = {i["detector"]["type"] for i in model["items"] if i.get("detector")}
    assert types, "expected at least one detector-backed item in the real plan model"
    missing = sorted(t for t in types if not hasattr(D.Detectors, f"d_{t}"))
    assert not missing, f"plan_model.json references detector types with no d_<type> method: {missing}"


def test_new_v13_detector_types_are_all_present_on_the_real_plan_model():
    """Sanity check that the model actually exercises every type L.13 was asked to build, so the
    coverage test above cannot pass by accident on a model that dropped one."""
    model_path = os.path.join(REPO_ROOT, "00_ARCHITECTURE", "control", "suvarna", "plan_model.json")
    with open(model_path, encoding="utf-8") as f:
        model = json.load(f)
    types = {i["detector"]["type"] for i in model["items"] if i.get("detector")}
    expected = {"prs_merged", "main_has_files", "scorecard_pass", "migrations_applied",
                "register_rows_state", "register_freeze_clean", "monitor_check_ok",
                "deployed_contains", "wave_deployed", "assets_elevated", "registry_coverage",
                "ledger_no_open_gap_on"}
    assert expected <= types
