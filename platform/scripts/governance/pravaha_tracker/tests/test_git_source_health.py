"""PR #3899 (c): the tracker's health 'git' source counts a git call as a failure only when its exit is NOT the answer.

Claims, one oracle each, run against a real throwaway repository (no mocked git; `gh` is stubbed out because it needs the network).
`git merge-base --is-ancestor` exits 1 for "not an ancestor" and `git rev-parse --verify -q` exits 1 for "no such ref" (git-merge-base(1),
git-rev-parse(1)); a fetch of a branch nobody pushed exits 128 "couldn't find remote ref" (the MISSING_REMOTE_REF the detector already maps
to "not yet"). Source: detectors.py `_run` / `SourceMonitor` (the snapshot feeds the operator-visible health).
  1. fetch of a never-pushed branch (exit 128 + MISSING_REMOTE_REF) does not mark git stale
     (reversion: drop `answer_rc=(128,)` from the fetch call in `_fetch`)
  2. `rev-parse --verify -q` exit 1 does not mark git stale (reversion: drop `answer_rc=(1,)` from that call in d_branch_merged)
  3. `merge-base --is-ancestor` exit 1 does not mark git stale (reversion: drop `answer_rc=(1,)` from that call in d_branch_merged)
  4. a REAL fetch failure (exit 128 without the missing-ref marker: the directory is not a git repository) still marks git stale
     (reversion: ignore `answer_text` in `_run`, so every 128 on a fetch is an answer)
  5. a REAL failure on a command whose only answer is exit 1 (128 on `merge-base --is-ancestor`) still marks git stale
     (reversion: in `_run`, test `answer_rc` for truthiness instead of `p.returncode in answer_rc`)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pravaha_tracker import detectors as D

GIT_ID = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]


def _git(*args, cwd):
    subprocess.run(["git", *GIT_ID, *args], cwd=cwd, check=True, capture_output=True, timeout=30)


@pytest.fixture
def repo(tmp_path):
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    _git("init", "-q", "--bare", "-b", "main", str(origin), cwd=tmp_path)
    _git("clone", "-q", str(origin), str(work), cwd=tmp_path)
    _git("checkout", "-q", "-b", "main", cwd=work)
    (work / "a").write_text("a")
    _git("add", "a", cwd=work)
    _git("commit", "-q", "-m", "base", cwd=work)
    _git("push", "-q", "origin", "main", cwd=work)
    _git("checkout", "-q", "-b", "feature", cwd=work)      # local only: not on origin, not an ancestor of origin/main
    (work / "b").write_text("b")
    _git("add", "b", cwd=work)
    _git("commit", "-q", "-m", "feature work", cwd=work)
    return work


@pytest.fixture
def det(repo, monkeypatch):
    real = D._run
    # gh needs the network; its answer is irrelevant here, only the git calls feed the git source
    monkeypatch.setattr(D, "_run", lambda cmd, **kw: (1, "") if cmd[0] == "gh" else real(cmd, **kw))
    detector = D.Detectors(D.Config(str(repo), None, str(repo)))
    yield detector
    detector._pool.shutdown(wait=True)


def _git_source(det):
    return det.sources.snapshot()["git"]


def _branch_merged(det, ref):
    with D.external_context(det.sources):
        return det.d_branch_merged({"type": "branch_merged", "ref": ref})


def test_fetch_of_a_never_pushed_branch_is_an_answer_not_a_git_failure(det):  # claim 1
    result = _branch_merged(det, "origin/kalayantra/never-pushed")
    assert result.status == "pending" and "does not exist on origin yet" in result.detail
    assert _git_source(det)["stale"] is False, _git_source(det)


def test_rev_parse_verify_exit_1_is_an_answer_not_a_git_failure(det):  # claim 2
    result = _branch_merged(det, "no-such-local-branch")
    assert result.status == "pending" and "does not exist yet" in result.detail
    assert _git_source(det)["stale"] is False, _git_source(det)


def test_is_ancestor_exit_1_is_an_answer_not_a_git_failure(det):  # claim 3
    result = _branch_merged(det, "feature")
    assert result.status == "running" and "commits on feature not yet on main" in result.detail
    assert _git_source(det)["stale"] is False, _git_source(det)


def test_a_real_fetch_failure_still_marks_git_stale(tmp_path, monkeypatch):  # claim 4
    not_a_repo = tmp_path / "plain-dir"
    not_a_repo.mkdir()
    detector = D.Detectors(D.Config(str(not_a_repo), None, str(not_a_repo)))
    try:
        with D.external_context(detector.sources), pytest.raises(RuntimeError, match="not a git repository"):
            detector._fetch("main")                         # exit 128, but not "couldn't find remote ref"
        row = detector.sources.snapshot()["git"]
        assert row["stale"] is True and row["error"] == "exit 128", row
    finally:
        detector._pool.shutdown(wait=True)


def test_a_real_failure_on_an_exit_1_answer_command_still_marks_git_stale(tmp_path):  # claim 5
    not_a_repo = tmp_path / "plain-dir"
    not_a_repo.mkdir()
    monitor = D.SourceMonitor()
    with D.external_context(monitor):
        rc, _ = D._run(["git", "merge-base", "--is-ancestor", "a", "b"], cwd=str(not_a_repo), answer_rc=(1,))
    assert rc == 128
    row = monitor.snapshot()["git"]
    assert row["stale"] is True and row["error"] == "exit 128", row
