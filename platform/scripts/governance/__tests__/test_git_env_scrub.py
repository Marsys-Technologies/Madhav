"""A test process started with GIT_DIR & co exported must not let a fixture's git act on that repository (2026-10-17 02:09Z incident: `git init --bare` re-initialised the shared repo).

Throwaway repositories only: GIT_DIR is only ever pointed at a repository this file created under tmp_path.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import textwrap

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import git_env_scrub as g  # noqa: E402


def _clean_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in g.REPO_LOCATING_VARS and k != "PYTEST_CURRENT_TEST"}


def test_scrubbed_drops_every_repository_locating_variable_and_nothing_else():
    # `git rev-parse --local-env-vars` is git's own list of the variables that locate a repository (GIT_NAMESPACE is not in it: it picks the ref namespace, still repository-scoped)
    own = set(subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True, text=True, check=True, env=_clean_env()).stdout.split())
    locating = {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"}
    assert locating <= own
    assert set(g.REPO_LOCATING_VARS) == locating | {"GIT_NAMESPACE"}
    env = {name: "/x" for name in g.REPO_LOCATING_VARS} | {"GIT_CEILING_DIRECTORIES": "/c", "GIT_AUTHOR_NAME": "a", "PATH": "/bin"}
    assert g.scrubbed(env) == {"GIT_CEILING_DIRECTORIES": "/c", "GIT_AUTHOR_NAME": "a", "PATH": "/bin"}


def test_a_conftest_that_installs_the_cloud_guard_also_protects_a_repository_named_by_git_dir(tmp_path):
    """The incident on a throwaway repository: GIT_DIR names a linked worktree's gitdir and a fixture's plain `git init` flipped the whole repository to core.bare=true."""
    git = lambda *a, **kw: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True, text=True, env=_clean_env(), **kw).stdout.strip()
    victim = tmp_path / "victim"
    git("init", "-q", "-b", "main", str(victim))
    git("-C", str(victim), "commit", "-q", "--allow-empty", "-m", "x")
    git("-C", str(victim), "worktree", "add", "-q", str(tmp_path / "linked"), "-b", "linked")
    linked_gitdir = next((victim / ".git" / "worktrees").iterdir())
    bare = lambda: git("--git-dir", str(victim / ".git"), "config", "--bool", "core.bare")
    assert bare() == "false"
    run = tmp_path / "run"
    run.mkdir()
    (run / "conftest.py").write_text(textwrap.dedent(f"""
        import sys
        sys.path.insert(0, {str(HERE.parent)!r})
        from no_real_cloud_pytest import *   # noqa
    """))
    (run / "test_x.py").write_text(textwrap.dedent("""
        import subprocess
        def test_fixture_style_init(tmp_path):
            subprocess.run(["git", "init", "-q", str(tmp_path / "repo")], check=True, capture_output=True)  # inherits the environment, as a fixture does
    """))
    env = _clean_env() | {"GIT_DIR": str(linked_gitdir)}
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(run / "test_x.py")], capture_output=True, text=True, env=env, cwd=run)
    assert r.returncode == 0, r.stdout + r.stderr
    assert bare() == "false"
