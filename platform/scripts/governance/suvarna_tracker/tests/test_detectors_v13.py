"""New detector types for plan v1.3 (arch §11.7, built by L.13): prs_merged, main_has_files,
scorecard_pass, migrations_applied, register_rows_state, register_freeze_clean, monitor_check_ok,
deployed_contains, wave_deployed, assets_elevated, registry_coverage, ledger_no_open_gap_on, plus
the family-aware `levels_elevated` (`exclude: family_set`). No network, no real DB: every git/gh/
psql/monitor/suvarna-build call is either a fake (via a wrapped `D._run`) or a real, local,
offline git repo (the same pattern `test_detectors_server.py` already uses for the register).
"""
import hashlib
import json
import os
import subprocess
import time

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


def make_commit_chain(tmp_path, name, n=2):
    """A real, local, offline git repo (no remote configured) with `n` sequential commits on its
    default branch. Returns (repo_path, [sha0, sha1, ..., sha_{n-1}]) oldest first — real commit
    objects the ancestry detectors' `git cat-file` / `git merge-base --is-ancestor` calls can
    resolve without any network access (review pass 2 #5/#7: ancestry, never string equality or a
    substring test)."""
    root = tmp_path / name
    root.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
           "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}
    subprocess.run(["git", "init", "-q"], cwd=str(root), env=env, check=True, capture_output=True)
    shas = []
    for i in range(n):
        (root / f"f{i}.txt").write_text(str(i))
        subprocess.run(["git", "add", "-A"], cwd=str(root), env=env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", f"c{i}"], cwd=str(root), env=env, check=True, capture_output=True)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root), env=env, check=True,
                             capture_output=True, text=True).stdout.strip()
        shas.append(sha)
    return str(root), shas


FULL_FAMILY_ASSETS_KEYS = D.FAMILY_ASSETS_REQUIRED_KEYS


def fam_json(**overrides) -> str:
    """A `FAMILY_ASSETS.json` object carrying every one of CODE-4's required keys (each defaulted
    to an empty list), so a test that only cares about one family's contents does not accidentally
    trip the "missing required key" error on the others. `family_set` auto-computes as the union of
    the other six lists (Track E brief §8's own definition) unless the caller overrides it
    explicitly — so a caller naming only `family_gochara` still gets a `family_set` that contains
    it, matching real `FAMILY_ASSETS.json` content."""
    data = {k: [] for k in FULL_FAMILY_ASSETS_KEYS}
    data.update(overrides)
    if "family_set" not in overrides:
        seen: list[str] = []
        for k in FULL_FAMILY_ASSETS_KEYS:
            if k == "family_set":
                continue
            for a in data.get(k) or []:
                if a not in seen:
                    seen.append(a)
        data["family_set"] = seen
    return json.dumps(data)


def elevation_module_source(elevated_ids) -> str:
    """A minimal, real `asset_elevation_tracker.py` stand-in: `elevated_assets(cfg)` returns exactly
    `elevated_ids`, regardless of `cfg` — enough to exercise the CODE-8 "call the E6.3 function"
    path without needing the real module (which does not exist yet)."""
    ids = ", ".join(repr(a) for a in elevated_ids)
    return f"def elevated_assets(cfg):\n    return {{{ids}}}\n"


def _git(root, *args, env=None):
    base_env = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
               "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com", **(env or {})}
    return subprocess.run(["git", *args], cwd=str(root), env=base_env, check=True,
                          capture_output=True, text=True).stdout.strip()


def make_scorecard_repo(tmp_path, name, tests_obj, generator_content="generator v1\n",
                        generator_path="generator.py", scorecard_path="scorecard.json",
                        corrupt_generator_hash=False, inspector_commit_override=None):
    """A real, local, offline two-commit git repo: commit 1 adds the generator (its sha becomes
    `inspector_commit`), commit 2 adds the scorecard referencing that generator's real sha256 and
    that commit — everything CODE-6 checks (generator hash, inspector_commit ancestry) is exercised
    against real git objects, no faking. Returns the repo path; `ref="HEAD"` is commit 2."""
    root = tmp_path / name
    root.mkdir()
    _git(root, "init", "-q")
    (root / generator_path).parent.mkdir(parents=True, exist_ok=True)
    (root / generator_path).write_text(generator_content)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "generator")
    inspector_commit = _git(root, "rev-parse", "HEAD")
    generator_sha256 = hashlib.sha256(generator_content.encode("utf-8")).hexdigest()
    scorecard = {"generator": generator_path,
                "generator_sha256": "0" * 64 if corrupt_generator_hash else generator_sha256,
                "inspector_commit": inspector_commit_override or inspector_commit,
                "tests": tests_obj}
    (root / scorecard_path).write_text(json.dumps(scorecard))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "scorecard")
    return str(root)


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

def test_prs_merged_empty_params_with_no_pinned_by_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "prs_merged", "prs": []}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_prs_merged_empty_params_with_pinned_by_is_error_not_pending(nik, tmp_path):
    """CODE-3/C31 (arch §11.7): a spec deliberately left empty for a later item to pin (`pinned_by`)
    reads `unknown` (`error`), never `pending` — `pending` is reserved for an expected input that
    genuinely does not exist yet, not for a spec nobody has filled in."""
    d = dets(nik, str(tmp_path))
    spec = {"type": "prs_merged", "prs": [], "pinned_by": "L.11"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"
    assert "unknown" in r.detail and "L.11" in r.detail


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


# ---- PR pinning by head ref (review #9/consistency #9) --------------------------------------

def test_prs_merged_resolves_head_refs_via_gh_pr_list(nik, tmp_path, monkeypatch):
    listings = {
        "suvarna/lane/E3.2-build-001": [{"number": 501, "state": "MERGED", "mergedAt": "2026-09-29"}],
        "suvarna/lane/E3.2-build-002": [{"number": 502, "state": "OPEN", "mergedAt": None}],
    }
    view_states = {"501": "MERGED", "502": "OPEN"}

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:3] == ["gh", "pr", "list"]:
            assert cmd[3:5] == ["--state", "all"]
            ref = cmd[cmd.index("--head") + 1]
            assert cmd[-2:] == ["--json", "number,state,mergedAt"]
            return 0, json.dumps(listings[ref])
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": view_states[cmd[3]]})
        raise AssertionError(cmd)

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path))
    spec = {"type": "prs_merged", "prs": [],
            "head_refs": ["suvarna/lane/E3.2-build-001", "suvarna/lane/E3.2-build-002"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "running"
    assert "1/2 merged" in r.detail


def test_prs_merged_head_ref_with_no_pr_yet_is_pending_not_params_not_set(nik, tmp_path, monkeypatch):
    monkeypatch.setattr(D, "_run", lambda cmd, **k: (0, "[]") if cmd[:3] == ["gh", "pr", "list"] else (1, ""))
    d = dets(nik, str(tmp_path))
    spec = {"type": "prs_merged", "prs": [], "head_refs": ["suvarna/lane/not-opened-yet"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"
    assert "not-opened-yet" in r.detail
    assert r.detail != D.PARAMS_NOT_SET


def test_prs_merged_head_ref_gh_list_failure_is_error(nik, tmp_path, monkeypatch):
    monkeypatch.setattr(D, "_run", lambda cmd, **k: (1, "gh: rate limited") if cmd[:3] == ["gh", "pr", "list"] else (1, ""))
    d = dets(nik, str(tmp_path))
    spec = {"type": "prs_merged", "prs": [], "head_refs": ["suvarna/lane/x"]}
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


def test_scorecard_pass_all_pass_verified_generator_and_ancestor_commit_is_done(tmp_path):
    """CODE-6: `tests[T]` is an object with `verdict`; the generator hash and inspector_commit
    ancestry are checked against real git objects, not merely present."""
    repo = make_scorecard_repo(tmp_path, "repo_sc_done", {"T1": {"verdict": "PASS"}, "T2": {"verdict": "PASS"}})
    d = dets(repo, repo)
    spec = {"type": "scorecard_pass", "ref": "HEAD", "path": "scorecard.json", "tests": ["T1", "T2"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0
    assert "generator hash verified" in r.detail and "ancestor" in r.detail


def test_scorecard_pass_missing_generator_fields_is_pending_not_done(tmp_path):
    root = tmp_path / "repo_sc_missing"
    root.mkdir()
    (root / "scorecard.json").write_text(json.dumps({"tests": {"T1": {"verdict": "PASS"}}}))
    _git_init_commit(root)
    d = dets(str(root), str(root))
    spec = {"type": "scorecard_pass", "ref": "HEAD", "path": "scorecard.json", "tests": ["T1"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status != "done"
    assert "generator" in r.detail and "inspector_commit" in r.detail


def test_scorecard_pass_generator_hash_mismatch_is_pending_not_done(tmp_path):
    repo = make_scorecard_repo(tmp_path, "repo_sc_hash_mismatch", {"T1": {"verdict": "PASS"}},
                               corrupt_generator_hash=True)
    d = dets(repo, repo)
    spec = {"type": "scorecard_pass", "ref": "HEAD", "path": "scorecard.json", "tests": ["T1"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status != "done"
    assert "generator_sha256" in r.detail


def test_scorecard_pass_inspector_commit_not_ancestor_is_pending_not_done(tmp_path):
    root = tmp_path / "repo_sc_not_ancestor"
    root.mkdir()
    _git(root, "init", "-q")
    (root / "generator.py").write_text("v1\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "c0")
    default_branch = _git(root, "branch", "--show-current")
    _git(root, "checkout", "-q", "-b", "other")
    (root / "other.txt").write_text("other\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "other-branch-commit")
    other_sha = _git(root, "rev-parse", "HEAD")
    _git(root, "checkout", "-q", default_branch)
    scorecard = {"generator": "generator.py", "generator_sha256": hashlib.sha256(b"v1\n").hexdigest(),
                "inspector_commit": other_sha, "tests": {"T1": {"verdict": "PASS"}}}
    (root / "scorecard.json").write_text(json.dumps(scorecard))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "scorecard")
    d = dets(str(root), str(root))
    spec = {"type": "scorecard_pass", "ref": "HEAD", "path": "scorecard.json", "tests": ["T1"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status != "done"
    assert "not an ancestor" in r.detail


def test_scorecard_pass_pinned_generator_mismatch_is_pending_not_done(tmp_path):
    """B7 (review pass 3): the scorecard names generator.py and hashes it correctly, but the plan
    item's spec pins a *different* generator path — the hash check alone cannot catch this (a
    scorecard trivially satisfies it by naming any committed file with that file's own real hash),
    so the pin comparison must independently catch the mismatch."""
    repo = make_scorecard_repo(tmp_path, "repo_sc_pin_mismatch", {"T1": {"verdict": "PASS"}})
    d = dets(repo, repo)
    spec = {"type": "scorecard_pass", "ref": "HEAD", "path": "scorecard.json", "tests": ["T1"],
            "generator": "platform/scripts/governance/nikasha_scorecard.py"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status != "done"
    assert "pinned generator" in r.detail


def test_scorecard_pass_pinned_generator_match_is_done(tmp_path):
    """The mirror case: the scorecard's own `generator` matches the plan's pin exactly, and every
    other check passes — still `done`."""
    repo = make_scorecard_repo(tmp_path, "repo_sc_pin_match", {"T1": {"verdict": "PASS"}},
                               generator_path="platform/scripts/governance/nikasha_scorecard.py")
    d = dets(repo, repo)
    spec = {"type": "scorecard_pass", "ref": "HEAD", "path": "scorecard.json", "tests": ["T1"],
            "generator": "platform/scripts/governance/nikasha_scorecard.py"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_scorecard_pass_no_pin_in_spec_keeps_old_unpinned_behaviour(tmp_path):
    """A spec with no `generator` key is unaffected by B7 — whichever generator the scorecard names
    itself is still hash-checked, exactly as before."""
    repo = make_scorecard_repo(tmp_path, "repo_sc_no_pin", {"T1": {"verdict": "PASS"}},
                               generator_path="some/other/generator.py")
    d = dets(repo, repo)
    spec = {"type": "scorecard_pass", "ref": "HEAD", "path": "scorecard.json", "tests": ["T1"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_scorecard_pass_failing_test_is_running_not_done(tmp_path):
    repo = make_scorecard_repo(tmp_path, "repo_sc_failing",
                               {"T1": {"verdict": "PASS"}, "T2": {"verdict": "FAIL"}})
    d = dets(repo, repo)
    spec = {"type": "scorecard_pass", "ref": "HEAD", "path": "scorecard.json", "tests": ["T1", "T2"]}
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


# ---- R244-deferred path: DEFERRED counts only with independent verification -----------------
# (R3 in the base REGISTER fixture is DEFERRED — see the module-level fixture above.)

def test_register_rows_state_deferred_unconditional_when_no_deferred_params_given(nik, tmp_path):
    """No `deferred_withholding_entry`/`deferred_pr` params: behaviour is unchanged from before —
    every other generic use of this detector must not regress."""
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_rows_state", "rows": ["R3"], "states": ["CLOSED", "DONE", "DEFERRED"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_register_rows_state_deferred_requires_the_withholding_entry_present(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[0] == "git" and "show" in cmd and "NIKASHA_WITHHOLDING.json" in cmd[-1], 1, "fatal: not on ref"),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_rows_state", "rows": ["R3"], "states": ["CLOSED", "DONE", "DEFERRED"],
            "deferred_withholding_entry": "bo_upaya-Idem.pattern"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"
    assert "withholding entry" in r.detail


def test_register_rows_state_deferred_satisfied_when_withholding_entry_present(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[0] == "git" and "show" in cmd and "NIKASHA_WITHHOLDING.json" in cmd[-1], 0,
         json.dumps(["bo_upaya-Idem.pattern"])),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_rows_state", "rows": ["R3"], "states": ["CLOSED", "DONE", "DEFERRED"],
            "deferred_withholding_entry": "bo_upaya-Idem.pattern"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_register_rows_state_deferred_requires_the_named_fix_pr_merged(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [(lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0, json.dumps({"state": "OPEN"}))])
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_rows_state", "rows": ["R3"], "states": ["CLOSED", "DONE", "DEFERRED"],
            "deferred_pr": 123}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"
    assert "#123" in r.detail and "not merged" in r.detail


def test_register_rows_state_deferred_done_when_the_fix_pr_is_merged(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [(lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0, json.dumps({"state": "MERGED"}))])
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_rows_state", "rows": ["R3"], "states": ["CLOSED", "DONE", "DEFERRED"],
            "deferred_pr": 123}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


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


def test_register_freeze_clean_zero_rows_parsed_is_error_not_done(tmp_path):
    """A register that parses to zero total rows (a layout/format change, or an empty/garbled
    file) must never read `done` on account of "zero BLOCKS_FREEZE rows found" — that is
    indistinguishable from a genuine all-clean register unless some rows actually parsed."""
    root = tmp_path / "nik_zero_rows"
    (root / "00_ARCHITECTURE/briefs/nirmana").mkdir(parents=True)
    (root / "00_ARCHITECTURE/control").mkdir(parents=True)
    reg = "# register\nno rows here — the layout changed\n"
    (root / "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md").write_text(reg)
    (root / "00_ARCHITECTURE/control/asset_gaps.jsonl").write_text(json.dumps({"asset": "_schema"}) + "\n")
    (root / "00_ARCHITECTURE/control/asset_certs.jsonl").write_text(json.dumps({"asset": "_schema"}) + "\n")
    _git_init_commit(root)
    d = dets(str(root), str(tmp_path))
    spec = {"type": "register_freeze_clean", "allow_deferred": []}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"
    assert "zero rows" in r.detail


def test_register_freeze_clean_names_the_resolved_ref_and_commit(nik, tmp_path):
    """"the register was actually read at the pinned ref" must be an auditable fact, not an
    assumption — the resolved commit (short SHA) appears in the detail."""
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_freeze_clean", "allow_deferred": ["R3"]}
    d.poll([spec])
    r = wait_result(d, spec)
    sha = subprocess.run(["git", "-C", nik, "rev-parse", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    assert sha[:12] in r.detail


def test_register_freeze_clean_no_blockers_at_all_is_error_not_done(tmp_path):
    """CODE-7: zero BLOCKS_FREEZE rows found among the parsed rows is itself an error, never
    `done` — indistinguishable from a severity-label or parse miss."""
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
    assert r.status == "error"
    assert "no BLOCKS_FREEZE rows" in r.detail


def test_register_freeze_clean_expect_rows_present_is_unaffected(nik, tmp_path):
    """`expect_rows` naming rows that really are in the register changes nothing about the result —
    it is purely an extra "did the register actually carry these" assertion."""
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_freeze_clean", "allow_deferred": ["R3"], "expect_rows": ["R1", "R2", "R3"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status != "done"  # R1 is still OPEN in the shared `nik` fixture
    assert "R1=OPEN" in r.detail


def test_register_freeze_clean_expect_rows_missing_row_is_error(nik, tmp_path):
    """CODE-7: a row named in `expect_rows` that the register does not actually carry is an error —
    the same "cannot tell a real result from a parse/format miss" hazard as zero blockers found."""
    d = dets(nik, str(tmp_path))
    spec = {"type": "register_freeze_clean", "allow_deferred": [], "expect_rows": ["R1", "R99"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"
    assert "R99" in r.detail


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


def test_monitor_check_ok_warn_status_is_pending_never_done(nik, tmp_path, monkeypatch):
    """B2 (review pass 3): only `ok` ever reads `done` here. A `warn` (e.g. `builder_scope` before
    E7.2 provisioning, monitor.py's own new behaviour) must read `pending`, never `done` on the
    strength of merely not being `block`."""
    report = json.dumps({"overall": "warn", "checks": [
        {"name": "builder_scope", "status": "warn", "detail": "builder identity not provisioned (E7.2)"},
    ]})
    monkeypatch.setattr(D, "_run", lambda *a, **k: (0, report))
    d = dets(nik, str(tmp_path))
    spec = {"type": "monitor_check_ok", "check": "builder_scope"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.status != "done"


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

def test_deployed_contains_empty_params_with_no_pinned_by_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "deployed_contains", "component": "job", "prs": []}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_deployed_contains_empty_params_with_pinned_by_is_error(nik, tmp_path):
    """CODE-3/C31: same rule as prs_merged — a spec left empty with `pinned_by` reads `error`."""
    d = dets(nik, str(tmp_path))
    spec = {"type": "deployed_contains", "component": "job", "prs": [], "pinned_by": "L.11"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"
    assert "unknown" in r.detail and "L.11" in r.detail


def test_deployed_contains_done_when_the_merge_sha_is_an_ancestor_of_the_deployed_tag(tmp_path, monkeypatch):
    """Regression for review #5/#7: the deployed tag's text does NOT contain the merge SHA at all
    (unlike the old substring test) — it is a *different*, later commit that is nonetheless a real
    git descendant of the merge commit, the exact "a later, unrelated deploy" scenario the old
    substring check would fail after. Ancestry must still read `done`."""
    nik = make_nik(tmp_path, name="nik_dc_done")
    repo, shas = make_commit_chain(tmp_path, "repo_dc_done", n=2)
    merge_sha, deployed_sha = shas[0], shas[1]
    build_cmd = D._suvarna_build_cmd()

    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": merge_sha}})),
        (lambda cmd: cmd[:2] == [build_cmd, "--preflight"], 0, json.dumps({"job_image_tag": f"gcr.io/proj/engine:build-{deployed_sha}"})),
    ])
    d = dets(nik, repo)
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0
    assert "ancestry" in r.detail


def test_deployed_contains_pending_when_pr_not_merged(nik, tmp_path, monkeypatch):
    monkeypatch.setattr(D, "_run", lambda cmd, **k: (0, json.dumps({"state": "OPEN"})) if cmd[:3] == ["gh", "pr", "view"] else (1, ""))
    d = dets(nik, str(tmp_path))
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    assert wait_result(d, spec).status == "pending"


def test_deployed_contains_blocked_when_pr_closed_without_merging(nik, tmp_path, monkeypatch):
    """CODE-2: a PR closed without merging is `blocked`, distinct from an `OPEN` PR's `pending`."""
    monkeypatch.setattr(D, "_run", lambda cmd, **k: (0, json.dumps({"state": "CLOSED"})) if cmd[:3] == ["gh", "pr", "view"] else (1, ""))
    d = dets(nik, str(tmp_path))
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked"
    assert "closed without merging" in r.detail


def test_deployed_contains_pending_when_merged_but_the_deploy_is_not_a_descendant(tmp_path, monkeypatch):
    """The merge commit is NEWER than the deployed tag's commit, so it cannot possibly be deployed
    yet (not an ancestor) — must read `pending`, not `error` and not `done`."""
    nik = make_nik(tmp_path, name="nik_dc_pending")
    repo, shas = make_commit_chain(tmp_path, "repo_dc_pending", n=2)
    merge_sha, not_yet_deployed_sha = shas[1], shas[0]  # merge_sha (c1) is NOT an ancestor of c0
    build_cmd = D._suvarna_build_cmd()
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": merge_sha}})),
        (lambda cmd: cmd[:2] == [build_cmd, "--preflight"], 0,
         json.dumps({"job_image_tag": f"gcr.io/proj/engine:build-{not_yet_deployed_sha}"})),
    ])
    d = dets(nik, repo)
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"  # 0 of 1 present yet


def test_deployed_contains_resolves_head_refs_before_the_ancestry_check(tmp_path, monkeypatch):
    nik = make_nik(tmp_path, name="nik_dc_headref")
    repo, shas = make_commit_chain(tmp_path, "repo_dc_headref", n=2)
    merge_sha, deployed_sha = shas[0], shas[1]
    build_cmd = D._suvarna_build_cmd()
    orig = D._run

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:3] == ["gh", "pr", "list"]:
            return 0, json.dumps([{"number": 77, "state": "MERGED", "mergedAt": "x"}])
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": merge_sha}})
        if cmd[:2] == [build_cmd, "--preflight"]:
            return 0, json.dumps({"job_image_tag": f"gcr.io/proj/engine:build-{deployed_sha}"})
        return orig(cmd, cwd=cwd, timeout=timeout, shell=shell, env=env)

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, repo)
    spec = {"type": "deployed_contains", "component": "job", "prs": [], "head_refs": ["suvarna/lane/E3.2-build-001"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_deployed_contains_serving_component_reads_deployed_sha_not_web_sha(tmp_path, monkeypatch):
    """Consistency review #6: the serving component must read `deployed_sha`, never `web_sha`."""
    nik = make_nik(tmp_path, name="nik_dc_serving")
    repo, shas = make_commit_chain(tmp_path, "repo_dc_serving", n=2)
    merge_sha, deployed_sha = shas[0], shas[1]
    build_cmd = D._suvarna_build_cmd()
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": merge_sha}})),
        (lambda cmd: cmd[:2] == [build_cmd, "--preflight"], 0,
         json.dumps({"web_sha": "should-be-ignored", "deployed_sha": deployed_sha})),
    ])
    d = dets(nik, repo)
    spec = {"type": "deployed_contains", "component": "web", "prs": [42]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_deployed_contains_prefers_job_sha_over_job_image_tag(tmp_path, monkeypatch):
    """CODE-1: the running job commit is `job_sha` when the preflight names it — the trailing-SHA
    extraction from `job_image_tag` is only ever the fallback for an older preflight build."""
    nik = make_nik(tmp_path, name="nik_dc_job_sha")
    repo, shas = make_commit_chain(tmp_path, "repo_dc_job_sha", n=2)
    merge_sha, deployed_sha = shas[0], shas[1]
    build_cmd = D._suvarna_build_cmd()
    bogus_sha = "0" * 40  # not a real object in this repo — proves job_sha is read, not the tag
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": merge_sha}})),
        (lambda cmd: cmd[:2] == [build_cmd, "--preflight"], 0,
         json.dumps({"job_sha": deployed_sha, "job_image_tag": f"gcr.io/proj/engine:build-{bogus_sha}"})),
        # a fetch attempt for the bogus SHA must fail quietly (no such remote object) rather than
        # actually contacting a network — if the code wrongly used the tag this surfaces as `error`.
        (lambda cmd: cmd[:4] == ["git", "fetch", "-q", "origin"] and bogus_sha in cmd, 1, "fatal: no such remote ref"),
    ])
    d = dets(nik, repo)
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_deployed_contains_uses_suvarna_build_cmd_setting_not_a_bare_name(tmp_path, monkeypatch):
    nik = make_nik(tmp_path, name="nik_dc_cmd")
    repo, shas = make_commit_chain(tmp_path, "repo_dc_cmd", n=1)
    monkeypatch.setenv("SUVARNA_BUILD_CMD", "/opt/custom/suvarna-build")
    orig = D._run

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": shas[0]}})
        if cmd[0] == "git":
            return orig(cmd, cwd=cwd, timeout=timeout, shell=shell, env=env)
        assert cmd[0] == "/opt/custom/suvarna-build", f"expected the pinned full path, got {cmd}"
        assert cmd[1] == "--preflight" and len(cmd) == 2, "no bare-name lookup, no --json flag"
        return 0, json.dumps({"job_image_tag": f"gcr.io/proj/engine:build-{shas[0]}"})

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, repo)
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_deployed_contains_missing_preflight_script_is_pending_not_error(nik, tmp_path, monkeypatch):
    """CODE-1: a missing suvarna-build script (not provisioned yet, before E7.2) reads `pending`,
    never `error` — an unprovisioned precondition is an expected pre-J1 state."""

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": "a" * 40},
                                  "headRefName": "suvarna/land/B.W0-fold-1"})
        raise FileNotFoundError(f"[Errno 2] No such file or directory: {cmd[0]!r}")

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path))
    spec = {"type": "deployed_contains", "component": "job", "prs": [42]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"
    assert "not provisioned" in r.detail


def test_wave_deployed_missing_preflight_script_is_pending_not_error(tmp_path, monkeypatch):
    nik = make_nik(tmp_path, name="nik_wd_missing_script")
    home = tmp_path / "home"
    landing_dir = home / "evidence" / "B.W0"
    landing_dir.mkdir(parents=True)
    (landing_dir / "LANDING.json").write_text(json.dumps({"pr": 77}))

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": "a" * 40},
                                  "headRefName": "suvarna/land/B.W0-fold-1"})
        raise FileNotFoundError(f"[Errno 2] No such file or directory: {cmd[0]!r}")

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "wave_deployed", "wave": "B.W0"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"
    assert "not provisioned" in r.detail


# ---- git ancestry unit tests (review #5/#7): "Tests with a temp git repo" -------------------

def test_is_ancestor_true_for_a_real_ancestor_commit(tmp_path):
    repo, shas = make_commit_chain(tmp_path, "repo_anc1", n=3)
    d = dets(make_nik(tmp_path, name="nik_anc1"), repo)
    assert d._is_ancestor(shas[0], shas[2]) is True


def test_is_ancestor_false_for_a_non_ancestor_commit(tmp_path):
    repo, shas = make_commit_chain(tmp_path, "repo_anc2", n=3)
    d = dets(make_nik(tmp_path, name="nik_anc2"), repo)
    assert d._is_ancestor(shas[2], shas[0]) is False


def test_is_ancestor_true_when_the_two_shas_are_equal(tmp_path):
    """Covers ROLE_BUILD_OPERATOR's "equal to" wording for a serving deploy's `deployed_sha` — a
    commit is its own ancestor."""
    repo, shas = make_commit_chain(tmp_path, "repo_anc3", n=1)
    d = dets(make_nik(tmp_path, name="nik_anc3"), repo)
    assert d._is_ancestor(shas[0], shas[0]) is True


def test_is_ancestor_raises_for_an_unresolvable_commit(tmp_path):
    repo, shas = make_commit_chain(tmp_path, "repo_anc4", n=1)
    d = dets(make_nik(tmp_path, name="nik_anc4"), repo)
    with pytest.raises(RuntimeError):
        d._is_ancestor("0" * 40, shas[0])


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


def test_wave_deployed_done_when_landing_pr_merged_and_deployed(tmp_path, monkeypatch):
    nik = make_nik(tmp_path, name="nik_wd_done")
    home = tmp_path / "home"
    landing_dir = home / "evidence" / "B.W0"
    landing_dir.mkdir(parents=True)
    (landing_dir / "LANDING.json").write_text(json.dumps({"pr": 77}))
    repo, shas = make_commit_chain(tmp_path, "repo_wd_done", n=2)
    merge_sha, deployed_sha = shas[0], shas[1]
    build_cmd = D._suvarna_build_cmd()
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": merge_sha},
                                                                       "headRefName": "suvarna/land/B.W0-fold-1"})),
        (lambda cmd: cmd[:2] == [build_cmd, "--preflight"], 0,
         json.dumps({"job_image_tag": f"gcr.io/proj/engine:build-{deployed_sha}"})),
    ])
    d = dets(nik, repo, home=str(home))
    spec = {"type": "wave_deployed", "wave": "B.W0"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_wave_deployed_running_when_merged_but_not_yet_a_descendant(tmp_path, monkeypatch):
    nik = make_nik(tmp_path, name="nik_wd_running")
    home = tmp_path / "home"
    landing_dir = home / "evidence" / "B.W1"
    landing_dir.mkdir(parents=True)
    (landing_dir / "LANDING.json").write_text(json.dumps({"pr": 78}))
    repo, shas = make_commit_chain(tmp_path, "repo_wd_running", n=2)
    merge_sha, older_sha = shas[1], shas[0]  # merge_sha (c1) is not an ancestor of c0
    build_cmd = D._suvarna_build_cmd()
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0, json.dumps({"state": "MERGED", "mergeCommit": {"oid": merge_sha},
                                                                       "headRefName": "suvarna/land/B.W1-fold-1"})),
        (lambda cmd: cmd[:2] == [build_cmd, "--preflight"], 0,
         json.dumps({"job_image_tag": f"gcr.io/proj/engine:build-{older_sha}"})),
    ])
    d = dets(nik, repo, home=str(home))
    spec = {"type": "wave_deployed", "wave": "B.W1"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "running" and r.progress == 0.75


# ---- wave_deployed: the head ref must be a Suvarṇa landing branch for this wave (review pass 3,
# below-blocker) --------------------------------------------------------------------------------

def test_wave_deployed_blocks_on_head_ref_from_a_different_wave(tmp_path, monkeypatch):
    nik = make_nik(tmp_path, name="nik_wd_wrong_wave")
    home = tmp_path / "home"
    landing_dir = home / "evidence" / "B.W0"
    landing_dir.mkdir(parents=True)
    (landing_dir / "LANDING.json").write_text(json.dumps({"pr": 90}))
    repo, shas = make_commit_chain(tmp_path, "repo_wd_wrong_wave", n=1)
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0,
         json.dumps({"state": "MERGED", "mergeCommit": {"oid": shas[0]}, "headRefName": "suvarna/land/B.W1-fold-1"})),
    ])
    d = dets(nik, repo, home=str(home))
    spec = {"type": "wave_deployed", "wave": "B.W0"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked"
    assert "not a Suvarṇa landing branch" in r.detail and "B.W1-fold-1" in r.detail


def test_wave_deployed_blocks_on_head_ref_from_a_non_landing_branch(tmp_path, monkeypatch):
    nik = make_nik(tmp_path, name="nik_wd_not_landing")
    home = tmp_path / "home"
    landing_dir = home / "evidence" / "B.W0"
    landing_dir.mkdir(parents=True)
    (landing_dir / "LANDING.json").write_text(json.dumps({"pr": 91}))
    repo, shas = make_commit_chain(tmp_path, "repo_wd_not_landing", n=1)
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0,
         json.dumps({"state": "MERGED", "mergeCommit": {"oid": shas[0]}, "headRefName": "some-random-branch"})),
    ])
    d = dets(nik, repo, home=str(home))
    spec = {"type": "wave_deployed", "wave": "B.W0"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked" and "not a Suvarṇa landing branch" in r.detail


def test_wave_deployed_blocks_on_missing_head_ref(tmp_path, monkeypatch):
    """A merged PR with no `headRefName` at all in the response must never be silently trusted."""
    nik = make_nik(tmp_path, name="nik_wd_missing_head_ref")
    home = tmp_path / "home"
    landing_dir = home / "evidence" / "B.W0"
    landing_dir.mkdir(parents=True)
    (landing_dir / "LANDING.json").write_text(json.dumps({"pr": 92}))
    repo, shas = make_commit_chain(tmp_path, "repo_wd_missing_head_ref", n=1)
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:3] == ["gh", "pr", "view"], 0,
         json.dumps({"state": "MERGED", "mergeCommit": {"oid": shas[0]}})),
    ])
    d = dets(nik, repo, home=str(home))
    spec = {"type": "wave_deployed", "wave": "B.W0"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked" and "not a Suvarṇa landing branch" in r.detail


# ============================================================================================
# assets_elevated
# ============================================================================================

def test_assets_elevated_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": ""}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def _wrap_elevation_and_family(monkeypatch, elevation_source=None, family_json=None):
    """CODE-8: `assets_elevated`/`levels_elevated` first load the E6.3 exact function from
    `origin/main:{ASSET_ELEVATION_TRACKER_REL_PATH}`; only once that's wired do they go on to read
    `FAMILY_ASSETS.json` from the same ref. `elevation_source=None` fakes "not on main yet" (the
    ELEVATION_NOT_WIRED_DETAIL path); `family_json=None` fakes "not on main yet" for the family
    file (only reachable once the elevation module IS wired)."""
    table = [(lambda cmd: cmd[:2] == ["git", "fetch"], 0, "")]
    if elevation_source is not None:
        table.append((lambda cmd: cmd[:2] == ["git", "show"] and D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2],
                      0, elevation_source))
    else:
        table.append((lambda cmd: cmd[:2] == ["git", "show"] and D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2],
                      1, "fatal: not on main"))
    if family_json is not None:
        table.append((lambda cmd: cmd[:2] == ["git", "show"] and "FAMILY_ASSETS.json" in cmd[2], 0, family_json))
    else:
        table.append((lambda cmd: cmd[:2] == ["git", "show"] and "FAMILY_ASSETS.json" in cmd[2],
                      1, "fatal: not on main"))
    wrap_run(monkeypatch, table)


def test_assets_elevated_error_before_e63_function_wired(nik, tmp_path, monkeypatch):
    """CODE-8: until `asset_elevation_tracker.py` is on main and loadable, this reads `error`
    (`ELEVATION_NOT_WIRED_DETAIL`), never the retired certification/gap-ledger proxy."""
    _wrap_elevation_and_family(monkeypatch, elevation_source=None, family_json=fam_json(family_gochara=["clean_a"]))
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": "family_gochara"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error" and r.detail == D.ELEVATION_NOT_WIRED_DETAIL


def test_assets_elevated_before_family_assets_json_lands_is_pending(nik, tmp_path, monkeypatch):
    _wrap_elevation_and_family(monkeypatch, elevation_source=elevation_module_source(["clean_a"]), family_json=None)
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": "family_gochara"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "FAMILY_ASSETS.json" in r.detail


def test_assets_elevated_missing_required_family_key_is_error(nik, tmp_path, monkeypatch):
    """CODE-4: a FAMILY_ASSETS.json missing one of Track E brief §8's required keys is malformed,
    never silently read as if that family's list were empty."""
    fam = json.dumps({"family_gochara": ["clean_a"]})  # missing the other six required keys
    _wrap_elevation_and_family(monkeypatch, elevation_source=elevation_module_source(["clean_a"]), family_json=fam)
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": "family_gochara"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"
    assert "missing required key" in r.detail


def test_assets_elevated_done_when_every_asset_in_the_set_is_elevated(nik, tmp_path, monkeypatch):
    fam = fam_json(family_gochara=["clean_a"])
    _wrap_elevation_and_family(monkeypatch, elevation_source=elevation_module_source(["clean_a"]), family_json=fam)
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": "family_gochara"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_assets_elevated_pending_when_the_set_asset_is_not_elevated(nik, tmp_path, monkeypatch):
    fam = fam_json(family_sangam=["with_gap"])
    _wrap_elevation_and_family(monkeypatch, elevation_source=elevation_module_source(["clean_a"]), family_json=fam)
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


def _wrap_registry_coverage_report(monkeypatch, report_text):
    """CODE-5: the report is read from `origin/main` (arch §11.7's table), the same discipline
    `_family_assets()` uses — not the Nikaṣa register/ledger ref."""
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["git", "fetch"], 0, ""),
        (lambda cmd: cmd[:2] == ["git", "show"] and D.REGISTRY_COVERAGE_REL_PATH in cmd[2], 0, report_text),
    ])


def test_registry_coverage_report_missing_a_required_key_is_error_not_pending(nik, tmp_path, monkeypatch):
    """CODE-5: an absent required key (`registry_revision`, `inspector_commit`, `covered_cells`,
    `uncovered_required_criteria`) is an error, never `pending` — an absent key is not evidence of
    coverage, and a `pending` reading would let a malformed/partial report look like "just not
    measured yet" instead of "broken"."""
    report = json.dumps({"covered_cells": 900})
    _wrap_registry_coverage_report(monkeypatch, report)
    d = dets(nik, str(tmp_path))
    spec = {"type": "registry_coverage"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"
    assert "missing required key" in r.detail
    assert "registry_revision" in r.detail and "inspector_commit" in r.detail


def test_registry_coverage_uncovered_criteria_is_not_done(nik, tmp_path, monkeypatch):
    report = json.dumps({"registry_revision": 7, "inspector_commit": "abc123",
                         "uncovered_required_criteria": ["Gate.L2.foo"], "covered_cells": 900})
    _wrap_registry_coverage_report(monkeypatch, report)
    d = dets(nik, str(tmp_path))
    spec = {"type": "registry_coverage"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status != "done" and "Gate.L2.foo" in r.detail


def test_registry_coverage_fully_covered_is_done(nik, tmp_path, monkeypatch):
    report = json.dumps({"registry_revision": 7, "inspector_commit": "abc123",
                         "uncovered_required_criteria": [], "covered_cells": 1143})
    _wrap_registry_coverage_report(monkeypatch, report)
    d = dets(nik, str(tmp_path))
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


def test_levels_elevated_error_before_e63_function_wired(nik, tmp_path, monkeypatch):
    """CODE-8: `levels_elevated` reads `error` (`ELEVATION_NOT_WIRED_DETAIL`) until the E6.3 exact
    function is on main and loadable — never the retired certification/gap-ledger proxy, and never
    even reaching the DAG-levels/database step."""
    _wrap_elevation_and_family(monkeypatch, elevation_source=None, family_json=None)
    d = dets(nik, str(tmp_path))
    spec = {"type": "levels_elevated", "levels": [0, 0]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error" and r.detail == D.ELEVATION_NOT_WIRED_DETAIL


def test_levels_elevated_without_exclude_is_unchanged(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    rows = _fake_registry_rows([("clean_a", "L1", "")])
    _wrap_elevation_and_family(monkeypatch, elevation_source=elevation_module_source(["clean_a"]))
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows)])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "levels_elevated", "levels": [0, 0]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and "excluded" not in r.detail


def test_levels_elevated_exclude_family_set_pending_before_family_assets_json_lands(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    rows = _fake_registry_rows([("clean_a", "L1", "")])
    _wrap_elevation_and_family(monkeypatch, elevation_source=elevation_module_source(["clean_a"]), family_json=None)
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows)])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "levels_elevated", "levels": [0, 0], "exclude": "family_set"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "FAMILY_ASSETS.json" in r.detail


def test_levels_elevated_exclude_family_set_missing_required_key_is_error(nik, tmp_path, monkeypatch):
    fam = json.dumps({"family_gochara": ["with_gap"]})  # missing the other six required keys
    _wrap_elevation_and_family(monkeypatch, elevation_source=elevation_module_source(["clean_a"]), family_json=fam)
    d = dets(nik, str(tmp_path))
    spec = {"type": "levels_elevated", "levels": [0, 0], "exclude": "family_set"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"
    assert "missing required key" in r.detail


def test_levels_elevated_exclude_family_set_drops_family_and_reader_assets(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    # clean_a: elevated, non-family. with_gap: has an open gap, but is excluded as a family asset —
    # so its non-elevation must never keep the wave from reading done.
    rows = _fake_registry_rows([("clean_a", "L1", ""), ("with_gap", "L3", "")])
    fam = fam_json(family_gochara=["with_gap"])
    _wrap_elevation_and_family(monkeypatch, elevation_source=elevation_module_source(["clean_a"]), family_json=fam)
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows)])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "levels_elevated", "levels": [0, 0], "exclude": "family_set"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0
    assert "1 family/reader asset(s) excluded" in r.detail


# ============================================================================================
# FAMILY_ASSETS.json path: configurable via SUVARNA_FAMILY_ASSETS_PATH (consistency review #7)
# ============================================================================================

def test_family_assets_default_path_matches_the_plan_model_and_track_e_brief(tmp_path, monkeypatch):
    nik = make_nik(tmp_path, name="nik_fa_default")
    fam = fam_json(family_gochara=["clean_a"])
    elevation_src = elevation_module_source(["clean_a"])
    seen = {}

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:2] == ["git", "fetch"]:
            return 0, ""
        if cmd[:2] == ["git", "show"]:
            if D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2]:
                return 0, elevation_src
            seen["path"] = cmd[2]
            return 0, fam
        raise AssertionError(cmd)

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": "family_gochara"}
    d.poll([spec])
    wait_result(d, spec)
    assert seen["path"] == "origin/main:00_ARCHITECTURE/control/FAMILY_ASSETS.json"


def test_family_assets_path_overridden_by_env_setting(tmp_path, monkeypatch):
    monkeypatch.setenv("SUVARNA_FAMILY_ASSETS_PATH", "00_ARCHITECTURE/control/custom/FAMILY_ASSETS.json")
    nik = make_nik(tmp_path, name="nik_fa_custom")
    fam = fam_json(family_gochara=["clean_a"])
    elevation_src = elevation_module_source(["clean_a"])
    seen = {}

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:2] == ["git", "fetch"]:
            return 0, ""
        if cmd[:2] == ["git", "show"]:
            if D.ASSET_ELEVATION_TRACKER_REL_PATH in cmd[2]:
                return 0, elevation_src
            seen["path"] = cmd[2]
            return 0, fam
        raise AssertionError(cmd)

    monkeypatch.setattr(D, "_run", fake)
    d = dets(nik, str(tmp_path))
    spec = {"type": "assets_elevated", "set": "family_gochara"}
    d.poll([spec])
    wait_result(d, spec)
    assert seen["path"] == "origin/main:00_ARCHITECTURE/control/custom/FAMILY_ASSETS.json"


# ============================================================================================
# evidence_recent — replaces the builder_scope Monitor check (Track E brief §8 E7.3), which
# cannot run as suvarna_reader: D6 withholds chart_grants.permission and profiles from that
# login (review pass 2 finding 3 / substance #14).
# ============================================================================================

def test_evidence_recent_empty_params_is_pending(nik, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_recent", "path": "", "max_age_hours": 0, "required_keys": []}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_evidence_recent_missing_file_is_pending(nik, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "evidence_recent", "path": "builder/provisioning.json", "max_age_hours": 24,
            "required_keys": ["principal", "grants"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "no evidence file" in r.detail


def test_evidence_recent_missing_required_key_is_pending(tmp_path):
    home = tmp_path / "home"
    ev = home / "evidence" / "builder"
    ev.mkdir(parents=True)
    (ev / "provisioning.json").write_text(json.dumps({"principal": "guest"}))
    d = dets(str(tmp_path), str(tmp_path), home=str(home))
    spec = {"type": "evidence_recent", "path": "builder/provisioning.json", "max_age_hours": 24,
            "required_keys": ["principal", "grants"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "grants" in r.detail


def test_evidence_recent_stale_file_is_pending(tmp_path):
    home = tmp_path / "home"
    ev = home / "evidence" / "builder"
    ev.mkdir(parents=True)
    f = ev / "provisioning.json"
    f.write_text(json.dumps({"principal": "guest", "grants": [{"chart_id": "482012f1", "permission": "build"}]}))
    old = time.time() - 48 * 3600
    os.utime(f, (old, old))
    d = dets(str(tmp_path), str(tmp_path), home=str(home))
    spec = {"type": "evidence_recent", "path": "builder/provisioning.json", "max_age_hours": 24,
            "required_keys": ["principal", "grants"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "old" in r.detail


def test_evidence_recent_fresh_file_with_all_keys_is_done(tmp_path):
    home = tmp_path / "home"
    ev = home / "evidence" / "builder"
    ev.mkdir(parents=True)
    f = ev / "provisioning.json"
    f.write_text(json.dumps({"principal": "guest", "grants": [{"chart_id": "482012f1", "permission": "build"}]}))
    d = dets(str(tmp_path), str(tmp_path), home=str(home))
    spec = {"type": "evidence_recent", "path": "builder/provisioning.json", "max_age_hours": 24,
            "required_keys": ["principal", "grants"]}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_evidence_recent_malformed_json_is_error(tmp_path):
    home = tmp_path / "home"
    ev = home / "evidence" / "builder"
    ev.mkdir(parents=True)
    (ev / "provisioning.json").write_text("not json")
    d = dets(str(tmp_path), str(tmp_path), home=str(home))
    spec = {"type": "evidence_recent", "path": "builder/provisioning.json", "max_age_hours": 24, "required_keys": []}
    d.poll([spec])
    assert wait_result(d, spec).status == "error"


# ============================================================================================
# NIKASHA_REF fetch (CODE-17): a remote-tracking ref (origin/<branch>) is fetched before each read
# ============================================================================================

@pytest.fixture(autouse=True)
def _reset_nikasha_fetch_cache():
    D._nikasha_fetch_cache.update(at=0.0)
    yield
    D._nikasha_fetch_cache.update(at=0.0)


def test_register_text_fetches_the_named_branch_when_ref_is_remote_tracking(nik, tmp_path, monkeypatch):
    monkeypatch.setenv("NIKASHA_REF", "origin/campaign/nikasha-test")
    fetched = []
    orig = D._run

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:2] == ["git", "fetch"]:
            fetched.append(tuple(cmd))
            return 0, ""
        return orig(cmd, cwd=cwd, timeout=timeout, shell=shell, env=env)

    monkeypatch.setattr(D, "_run", fake)
    with pytest.raises(RuntimeError):
        D.register_text(nik)  # the branch doesn't exist in the throwaway fixture repo -> git show fails
    assert fetched and fetched[0] == ("git", "fetch", "-q", "origin", "campaign/nikasha-test")


def test_register_text_never_fetches_for_a_local_ref(nik, tmp_path, monkeypatch):
    monkeypatch.delenv("NIKASHA_REF", raising=False)  # defaults to HEAD
    fetched = []
    orig = D._run

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:2] == ["git", "fetch"]:
            fetched.append(tuple(cmd))
        return orig(cmd, cwd=cwd, timeout=timeout, shell=shell, env=env)

    monkeypatch.setattr(D, "_run", fake)
    D.register_text(nik)
    assert fetched == []


def test_nikasha_fetch_is_ttl_cached_across_reads(nik, tmp_path, monkeypatch):
    monkeypatch.setenv("NIKASHA_REF", "origin/campaign/nikasha-test")
    fetched = []
    orig = D._run

    def fake(cmd, cwd=None, timeout=60, shell=False, env=None):
        if cmd[:2] == ["git", "fetch"]:
            fetched.append(tuple(cmd))
            return 0, ""
        return orig(cmd, cwd=cwd, timeout=timeout, shell=shell, env=env)

    monkeypatch.setattr(D, "_run", fake)
    for _ in range(3):
        try:
            D.register_text(nik)
        except RuntimeError:
            pass
    assert len(fetched) == 1  # only the first call actually fetched; the rest were within the TTL


# ============================================================================================
# fk_no_cascade (CODE-9)
# ============================================================================================

def test_fk_no_cascade_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "fk_no_cascade", "referenced": ""}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_fk_no_cascade_no_rows_is_done(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, "")])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "fk_no_cascade", "referenced": "public.bodha_msr_signals"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0
    assert "bodha_msr_signals" in r.detail


def test_fk_no_cascade_rows_found_is_pending_listing_them(nik, tmp_path, monkeypatch):
    """B7/F3.FK (review pass 3): the query now also selects `confdeltype`, so a real cascade row
    carries a third field naming it."""
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    rows = ("kala_convergence\tkala_convergence_signal_id_fkey\tc\n"
           "kala_darshana\tkala_darshana_signal_id_fkey\tc\n")
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows)])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "fk_no_cascade", "referenced": "public.bodha_msr_signals"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"
    assert "kala_convergence" in r.detail and "2" in r.detail


def test_fk_no_cascade_without_credential_file_is_error(nik, tmp_path):
    d = dets(nik, str(tmp_path))  # pgenv=None
    spec = {"type": "fk_no_cascade", "referenced": "public.bodha_msr_signals"}
    d.poll([spec])
    assert wait_result(d, spec).status == "error"


# ---- fk_no_cascade: restricting (NO ACTION/RESTRICT) foreign keys (review pass 3, below-blocker) --

def test_fk_no_cascade_restricting_fk_is_blocked(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    rows = "kala_convergence\tkala_convergence_signal_id_fkey\tr\n"
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows)])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "fk_no_cascade", "referenced": "public.bodha_msr_signals"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked"
    assert "restrict would refuse the MSR rebuild" in r.detail and "kala_convergence" in r.detail


def test_fk_no_cascade_no_action_fk_is_blocked(nik, tmp_path, monkeypatch):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    rows = "kala_darshana\tkala_darshana_signal_id_fkey\ta\n"
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows)])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "fk_no_cascade", "referenced": "public.bodha_msr_signals"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked" and "restrict would refuse the MSR rebuild" in r.detail


@pytest.mark.parametrize("allow", ["set_null", "no_fk"])
def test_fk_no_cascade_restricting_fk_allowed_by_params_is_done(nik, tmp_path, monkeypatch, allow):
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    rows = "kala_convergence\tkala_convergence_signal_id_fkey\tr\n"
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows)])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "fk_no_cascade", "referenced": "public.bodha_msr_signals", "allow": allow}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0
    assert "allowed by the item's own params" in r.detail


def test_fk_no_cascade_restricting_fk_not_allowed_by_unrelated_param_value_is_blocked(nik, tmp_path, monkeypatch):
    """`allow` must be exactly `set_null` or `no_fk` — any other value is not the escape."""
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake\n")
    rows = "kala_convergence\tkala_convergence_signal_id_fkey\tr\n"
    wrap_run(monkeypatch, [(lambda cmd: cmd[:2] == ["bash", "-c"], 0, rows)])
    d = dets(nik, str(tmp_path), pgenv=str(pgenv))
    spec = {"type": "fk_no_cascade", "referenced": "public.bodha_msr_signals", "allow": "restrict"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked"


# ============================================================================================
# acks_from (CODE-10)
# ============================================================================================

def test_acks_from_empty_params_is_pending(nik, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "acks_from", "actors": [], "marker": ""}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_acks_from_no_event_log_yet_is_pending_listing_everyone_missing(nik, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "acks_from", "actors": ["l3-gochara", "l3-sangam"], "marker": "ACK FI-8"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"
    assert "l3-gochara" in r.detail and "l3-sangam" in r.detail


def test_acks_from_partial_acknowledgement_is_running(nik, tmp_path):
    home = tmp_path / "home"
    home.mkdir(parents=True)
    events_path = home / "run" / "EVENTS.jsonl"
    events_path.parent.mkdir(parents=True)
    from suvarna_tracker.events import append
    append(str(events_path), {"kind": "note", "actor": "l3-gochara", "detail": "ACK FI-8: received"})
    append(str(events_path), {"kind": "note", "actor": "l3-sangam", "detail": "not an ack at all"})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "acks_from", "actors": ["l3-gochara", "l3-sangam", "l3-kshetra"], "marker": "ACK FI-8"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "running"
    assert abs(r.progress - 1 / 3) < 1e-9
    assert "l3-sangam" in r.detail and "l3-kshetra" in r.detail
    assert "l3-gochara" not in r.detail.split(";")[-1]  # not listed among the missing


def test_acks_from_all_acknowledged_is_done(nik, tmp_path):
    home = tmp_path / "home"
    home.mkdir(parents=True)
    events_path = home / "run" / "EVENTS.jsonl"
    events_path.parent.mkdir(parents=True)
    from suvarna_tracker.events import append
    for actor in ("l3-gochara", "l3-sangam", "l3-kshetra"):
        append(str(events_path), {"kind": "note", "actor": actor, "detail": "ACK FI-8: received and understood"})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "acks_from", "actors": ["l3-gochara", "l3-sangam", "l3-kshetra"], "marker": "ACK FI-8"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_acks_from_ignores_notes_from_other_actors_and_wrong_marker(nik, tmp_path):
    home = tmp_path / "home"
    home.mkdir(parents=True)
    events_path = home / "run" / "EVENTS.jsonl"
    events_path.parent.mkdir(parents=True)
    from suvarna_tracker.events import append
    append(str(events_path), {"kind": "note", "actor": "l3-gochara", "detail": "ACK FI-9: wrong marker"})
    append(str(events_path), {"kind": "note", "actor": "someone-else", "detail": "ACK FI-8: not a named actor"})
    d = dets(nik, str(tmp_path), home=str(home))
    spec = {"type": "acks_from", "actors": ["l3-gochara"], "marker": "ACK FI-8"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and "l3-gochara" in r.detail


# ============================================================================================
# main_protected (CODE-11)
# ============================================================================================

def test_main_protected_empty_params_is_pending(nik, tmp_path):
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "", "bypass_only": ""}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending" and r.detail == D.PARAMS_NOT_SET


def test_main_protected_ruleset_pull_request_rule_is_done(nik, tmp_path, monkeypatch):
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 1}}]
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, json.dumps(rules)),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0
    assert "native" in r.detail


def test_main_protected_no_rulesets_falls_back_to_classic_protection(nik, tmp_path, monkeypatch):
    protection = {"required_pull_request_reviews": {"required_approving_review_count": 2}}
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, "[]"),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "branches/main/protection" in cmd[2], 0, json.dumps(protection)),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_main_protected_no_protection_at_all_is_error(nik, tmp_path, monkeypatch):
    """CODE-11: 403/404 (or any other failure) on either `gh api` call is `error`, never a silent
    'not protected yet'."""
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, "[]"),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "branches/main/protection" in cmd[2], 1,
         "gh: Branch not protected (HTTP 404)"),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"


def test_main_protected_rulesets_call_403_is_error(nik, tmp_path, monkeypatch):
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 1,
         "gh: HTTP 403: Resource not accessible"),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"


def test_main_protected_ruleset_rule_with_zero_required_reviews_is_pending(nik, tmp_path, monkeypatch):
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 0}}]
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, json.dumps(rules)),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "pending"


# ---- main_protected: bypass actors, checked via the ruleset detail endpoint (item 8) -----------

def test_main_protected_ruleset_with_no_ruleset_id_is_done_unbypass_unchecked(nik, tmp_path, monkeypatch):
    """No `ruleset_id` on the rule (the shape every prior test used): bypass cannot be checked this
    way, so this stays `done`, unchanged — the only regression guard here is that adding the bypass
    check must not turn an already-passing case into a failure."""
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 1}}]
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, json.dumps(rules)),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_main_protected_ruleset_id_with_no_bypass_actors_is_done(nik, tmp_path, monkeypatch):
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 1}, "ruleset_id": 42}]
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, json.dumps(rules)),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rulesets/42" in cmd[2], 0, json.dumps({"bypass_actors": []})),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_main_protected_ruleset_id_with_only_the_native_as_bypass_is_done(nik, tmp_path, monkeypatch):
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 1}, "ruleset_id": 42}]
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, json.dumps(rules)),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rulesets/42" in cmd[2], 0,
         json.dumps({"bypass_actors": [{"actor_type": "User", "actor_id": 7}]})),
        (lambda cmd: cmd[:2] == ["gh", "api"] and cmd[2] == "users/native", 0, json.dumps({"id": 7})),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "done" and r.progress == 1.0


def test_main_protected_ruleset_id_with_an_extra_user_bypass_is_blocked(nik, tmp_path, monkeypatch):
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 1}, "ruleset_id": 42}]
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, json.dumps(rules)),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rulesets/42" in cmd[2], 0,
         json.dumps({"bypass_actors": [{"actor_type": "User", "actor_id": 7},
                                       {"actor_type": "User", "actor_id": 99}]})),
        (lambda cmd: cmd[:2] == ["gh", "api"] and cmd[2] == "users/native", 0, json.dumps({"id": 7})),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked" and "bypass actor(s) beyond native" in r.detail and "99" in r.detail


def test_main_protected_ruleset_id_with_a_non_user_bypass_is_blocked(nik, tmp_path, monkeypatch):
    """A Team/Integration/OrganizationAdmin/RepositoryRole bypass actor is never the native's own
    login, whatever its id — it is always outside `bypass_only`."""
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 1}, "ruleset_id": 42}]
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, json.dumps(rules)),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rulesets/42" in cmd[2], 0,
         json.dumps({"bypass_actors": [{"actor_type": "OrganizationAdmin", "actor_id": 1}]})),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "blocked" and "bypass actor(s) beyond native" in r.detail


def test_main_protected_ruleset_detail_403_is_error(nik, tmp_path, monkeypatch):
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 1}, "ruleset_id": 42}]
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, json.dumps(rules)),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rulesets/42" in cmd[2], 1, "gh: HTTP 403: Resource not accessible"),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"


def test_main_protected_users_lookup_failure_is_error(nik, tmp_path, monkeypatch):
    rules = [{"type": "pull_request", "parameters": {"required_approving_review_count": 1}, "ruleset_id": 42}]
    wrap_run(monkeypatch, [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rules/branches/main" in cmd[2], 0, json.dumps(rules)),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "rulesets/42" in cmd[2], 0,
         json.dumps({"bypass_actors": [{"actor_type": "User", "actor_id": 7}]})),
        (lambda cmd: cmd[:2] == ["gh", "api"] and cmd[2] == "users/native", 1, "gh: HTTP 404: Not Found"),
    ])
    d = dets(nik, str(tmp_path))
    spec = {"type": "main_protected", "branch": "main", "bypass_only": "native"}
    d.poll([spec])
    r = wait_result(d, spec)
    assert r.status == "error"


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


def test_new_v14_detector_types_are_all_present_on_the_real_plan_model():
    """Same sanity check as above, for the three v1.4 additions (review pass 2, §11.7)."""
    model_path = os.path.join(REPO_ROOT, "00_ARCHITECTURE", "control", "suvarna", "plan_model.json")
    with open(model_path, encoding="utf-8") as f:
        model = json.load(f)
    types = {i["detector"]["type"] for i in model["items"] if i.get("detector")}
    assert {"fk_no_cascade", "acks_from", "main_protected"} <= types
