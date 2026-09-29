"""hq commit lock (arch §12.12) — L.13: two Conductor passes must never race the `suvarna/hq`
worktree's git index; a commit call must refuse anything but an explicit, named-path commit."""
import fcntl
import os
import subprocess
import sys
import threading
import time

import pytest

from suvarna_tracker import hq_commit as HQ


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


@pytest.fixture
def hq(tmp_path):
    root = tmp_path / "hq"
    root.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
           "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}
    subprocess.run(["git", "init", "-q"], cwd=str(root), env=env, check=True, capture_output=True)
    (root / "tracked.txt").write_text("one\n")
    (root / "other.txt").write_text("one\n")
    subprocess.run(["git", "add", "-A"], cwd=str(root), env=env, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=str(root), env=env, check=True, capture_output=True)
    return root


@pytest.fixture
def home(tmp_path):
    return tmp_path / "home"


# ---- only-mode refusals: no lock taken, no git invoked ----------------------------------------

def test_refuses_empty_paths_before_taking_the_lock_or_invoking_git(hq, home):
    rc = HQ.commit(str(hq), [], "msg", str(home))
    assert rc == HQ.EX_USAGE
    assert not os.path.exists(HQ.lock_path(str(home)))  # never even created


@pytest.mark.parametrize("bad_path", ["-A", "--all", "-a", "."])
def test_refuses_dash_a_and_whole_tree_paths(hq, home, bad_path, capsys):
    rc = HQ.commit(str(hq), ["tracked.txt", bad_path], "msg", str(home))
    assert rc == HQ.EX_USAGE
    assert bad_path in capsys.readouterr().err
    assert not os.path.exists(HQ.lock_path(str(home)))


# ---- the happy path: explicit tracked paths only, no git add step -----------------------------

def test_commits_explicit_tracked_paths(hq, home):
    (hq / "tracked.txt").write_text("two\n")
    rc = HQ.commit(str(hq), ["tracked.txt"], "advance tracked.txt", str(home))
    assert rc == 0
    log = _git("log", "--oneline", "-1", cwd=str(hq)).stdout
    assert "advance tracked.txt" in log
    assert _git("status", "--short", cwd=str(hq)).stdout.strip() == ""  # nothing left dirty


def test_never_runs_git_add_an_untracked_path_is_gits_own_refusal(hq, home):
    """§12.12's own wording is `git commit -- <paths>` only — no separate `add` step. Proof: an
    untracked file named in --paths is refused by git itself ('did not match any file(s) known to
    git'), and nothing is committed at all (not even a tracked path in the same call)."""
    (hq / "tracked.txt").write_text("two\n")
    (hq / "brand_new.txt").write_text("new\n")
    before = _git("rev-parse", "HEAD", cwd=str(hq)).stdout
    rc = HQ.commit(str(hq), ["tracked.txt", "brand_new.txt"], "msg", str(home))
    assert rc != 0
    after = _git("rev-parse", "HEAD", cwd=str(hq)).stdout
    assert before == after  # no commit happened
    assert not _git("log", "--all", "--oneline", "-1", "--grep=msg", cwd=str(hq)).stdout


def test_lock_is_released_after_a_successful_commit(hq, home):
    (hq / "tracked.txt").write_text("two\n")
    HQ.commit(str(hq), ["tracked.txt"], "msg", str(home))
    lp = HQ.lock_path(str(home))
    assert os.path.exists(lp)
    fd = os.open(lp, os.O_RDWR)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # would raise if still held
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)


def test_lock_is_released_after_gits_own_refusal_too(hq, home):
    """A failing git commit (e.g. the untracked-path case) must not leave the lock held."""
    (hq / "brand_new.txt").write_text("new\n")
    HQ.commit(str(hq), ["brand_new.txt"], "msg", str(home))
    lp = HQ.lock_path(str(home))
    fd = os.open(lp, os.O_RDWR)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)


# ---- serialization: a second commit waits for the first to release --------------------------

def test_second_commit_waits_for_the_lock_then_proceeds(hq, home):
    lp = HQ.lock_path(str(home))
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    fd = os.open(lp, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)

    def release_later():
        time.sleep(0.5)
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

    threading.Thread(target=release_later, daemon=True).start()
    (hq / "tracked.txt").write_text("two\n")
    t0 = time.time()
    rc = HQ.commit(str(hq), ["tracked.txt"], "waited", str(home), wait=5)
    elapsed = time.time() - t0
    assert rc == 0
    assert elapsed >= 0.3, "should have waited for the concurrent holder to release"


def test_lock_timeout_when_the_holder_never_releases(hq, home):
    lp = HQ.lock_path(str(home))
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    fd = os.open(lp, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        (hq / "tracked.txt").write_text("two\n")
        t0 = time.time()
        rc = HQ.commit(str(hq), ["tracked.txt"], "msg", str(home), wait=0.3)
        elapsed = time.time() - t0
        assert rc == HQ.EX_LOCK_TIMEOUT
        assert elapsed < 2.0
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_two_concurrent_real_processes_only_one_races_ahead_the_other_still_succeeds(hq, home):
    """End-to-end with real subprocesses (no filesystem race), mirroring the census lock's own
    two-process test: both commits eventually succeed because the lock serializes them rather than
    rejecting the second outright (unlike the census lock's fail-fast contract)."""
    (hq / "tracked.txt").write_text("two\n")
    (hq / "other.txt").write_text("two\n")
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../governance
    env = dict(os.environ)
    procs = [
        subprocess.Popen([sys.executable, "-m", "suvarna_tracker.hq_commit", "--home", str(home),
                          "--hq", str(hq), "--message", f"concurrent-{name}", "--paths", path, "--wait", "10"],
                         cwd=here, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for name, path in (("a", "tracked.txt"), ("b", "other.txt"))
    ]
    rcs = [p.wait(timeout=15) for p in procs]
    assert rcs == [0, 0]
    log = _git("log", "--oneline", "-3", cwd=str(hq)).stdout
    assert "concurrent-a" in log and "concurrent-b" in log


# ---- CLI ---------------------------------------------------------------------------------------

def test_cli_requires_message():
    with pytest.raises(SystemExit):
        HQ.build_arg_parser().parse_args(["--paths", "x"])


def test_cli_main_returns_gits_exit_code(hq, home):
    (hq / "tracked.txt").write_text("two\n")
    rc = HQ.main(["--home", str(home), "--hq", str(hq), "--message", "via cli", "--paths", "tracked.txt"])
    assert rc == 0
    assert "via cli" in _git("log", "--oneline", "-1", cwd=str(hq)).stdout
