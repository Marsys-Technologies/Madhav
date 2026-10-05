"""test_sb1_build_window_reader.py -- the Build.history window DATING (build_window.py), against scratch git repos only.

No database, no network, no production. Every repository here is a throw-away `git init` under tmp_path; commits carry a
fixed committer date so the expected window start is exact. Each test names the defect it would catch; the MUTANT tests at
the end re-run a scenario with one guard removed (monkeypatched) and assert the defect returns, so a test that could not
fail is itself caught.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import build_window as bw  # noqa: E402

T0 = 1_700_000_000          # arbitrary fixed epoch; commits are spaced by whole days from here
DAY = 86400


def _git(repo, *args, when=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    if when is not None:
        env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = f"{when} +0000"
    p = subprocess.run(["git", "-c", "user.name=x", "-c", "user.email=x@x", "-c", "commit.gpgsign=false", *args],
                       cwd=str(repo), env=env, capture_output=True, text=True)
    assert p.returncode == 0, (args, p.stderr)
    return p.stdout


def _commit(repo, files: dict, day: int, msg="c"):
    for rel, text in files.items():
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg, when=T0 + day * DAY)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "scratch"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    return r


W = "platform/python-sidecar/pipeline/orchestrator/writers/ga_x.py"
MIG = "platform/migrations/100_ga_x.sql"


def _base(repo):
    _commit(repo, {W: "# v1\n", MIG: "INSERT INTO asset_registry (asset_id) VALUES ('ga_x');\n"}, 1)


def test_window_is_the_later_of_code_and_registry_code_later(repo):
    _base(repo)
    _commit(repo, {MIG: "-- ga_x asset_registry\nUPDATE asset_registry SET depends_on='{}' WHERE asset_id='ga_x';\n"}, 5)
    _commit(repo, {W: "# v2\n"}, 9)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert w["ok"] and w["epoch"] == T0 + 9 * DAY and "writer digest" in w["basis"], w
    assert w["code_epoch"] == T0 + 9 * DAY and w["registry_epoch"] == T0 + 5 * DAY


def test_window_is_the_later_of_code_and_registry_registry_later(repo):
    _base(repo)
    _commit(repo, {W: "# v2\n"}, 5)
    _commit(repo, {MIG: "UPDATE asset_registry SET count_sql='select 1' WHERE asset_id='ga_x';\n"}, 9)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert w["ok"] and w["epoch"] == T0 + 9 * DAY and "registry identity" in w["basis"], w


def test_unrelated_commits_do_not_move_the_window(repo):
    _base(repo)
    _commit(repo, {"platform/python-sidecar/pipeline/orchestrator/writers/ga_other.py": "# other\n",
                   "platform/migrations/200_other.sql": "UPDATE asset_registry SET x=1 WHERE asset_id='ga_other';\n"}, 20)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert w["ok"] and w["epoch"] == T0 + 1 * DAY, w


def test_registry_match_is_whole_word_not_a_prefix(repo):
    """ga_dasha must not be dated by a migration that names only ga_dashas."""
    _commit(repo, {W: "# v1\n", "platform/migrations/100.sql": "UPDATE asset_registry SET x=1 WHERE asset_id='ga_dashas';\n"}, 1)
    w = bw.compute_window(bw.WindowReader(repo), "ga_dasha", [W])
    assert not w["ok"] and "names ga_dasha" in w["reason"], w


def test_a_migration_that_names_the_asset_but_not_the_registry_is_not_an_identity_change(repo):
    _commit(repo, {W: "# v1\n", MIG: "INSERT INTO asset_registry (asset_id) VALUES ('ga_x');\n"}, 1)
    _commit(repo, {"platform/migrations/101_grant.sql": "GRANT SELECT ON ga_x_table TO ga_x;\n"}, 30)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert w["ok"] and w["epoch"] == T0 + 1 * DAY, w


SEED = "platform/scripts/seed/asset_registry_seed.ts"


def _seed(a_dep="[]", b_dep="[]"):
    return ("export const ROWS = [\n  {\n    asset_id: 'ga_x',\n    layer: 'ganita',\n    depends_on: " + a_dep +
            ",\n  },\n  {\n    asset_id: 'ga_y',\n    layer: 'ganita',\n    depends_on: " + b_dep + ",\n  },\n]\n")


def test_seed_row_edit_of_this_asset_counts_as_registry_identity(repo):
    _commit(repo, {W: "# v1\n", SEED: _seed()}, 1)
    _commit(repo, {SEED: _seed(a_dep="['ga_y']")}, 7)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert w["ok"] and w["epoch"] == T0 + 7 * DAY, w


def test_seed_edit_of_another_asset_row_does_not_move_this_window(repo):
    """The seed names every asset: a file-level date would reopen every window on any edit (what the first real read showed)."""
    _commit(repo, {W: "# v1\n", SEED: _seed()}, 1)
    _commit(repo, {SEED: _seed(b_dep="['ga_x']")}, 9)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert w["ok"] and w["epoch"] == T0 + 1 * DAY, w
    w = bw.compute_window(bw.WindowReader(repo), "ga_y", [W])
    assert w["ok"] and w["epoch"] == T0 + 9 * DAY, w


# ───────────────────────────── fail closed: every undeterminable case is ok=False with a reason ─────────────────────────────

def test_no_migration_names_the_asset_is_unknown_not_a_window(repo):
    _commit(repo, {W: "# v1\n"}, 1)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert not w["ok"] and "registry identity cannot be dated" in w["reason"], w


def test_empty_code_path_set_is_unknown(repo):
    _base(repo)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [])
    assert not w["ok"] and "no code path set" in w["reason"], w


def test_working_tree_modified_writer_is_unknown(repo):
    _base(repo)
    (repo / W).write_text("# edited, uncommitted\n")
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert not w["ok"] and "not the code on main" in w["reason"], w


def test_staged_but_uncommitted_writer_change_is_unknown(repo):
    _base(repo)
    (repo / W).write_text("# staged\n")
    _git(repo, "add", W)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert not w["ok"] and "not the code on main" in w["reason"], w


def test_untracked_writer_file_is_unknown(repo):
    _base(repo)
    new = "platform/python-sidecar/pipeline/orchestrator/writers/ga_new.py"
    (repo / new).write_text("# untracked\n")
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W, new])
    assert not w["ok"] and "not tracked at the main ref" in w["reason"], w


def test_missing_main_ref_is_unknown(tmp_path):
    r = tmp_path / "other"
    r.mkdir()
    _git(r, "init", "-q", "-b", "trunk")
    _base(r)
    w = bw.compute_window(bw.WindowReader(r), "ga_x", [W])
    assert not w["ok"] and "resolves to a commit" in w["reason"], w


def test_explicit_ref_is_used_alone(tmp_path):
    r = tmp_path / "other"
    r.mkdir()
    _git(r, "init", "-q", "-b", "trunk")
    _base(r)
    w = bw.compute_window(bw.WindowReader(r, ref="trunk"), "ga_x", [W])
    assert w["ok"] and w["ref"] == "trunk", w


def test_shallow_clone_is_unknown(repo, tmp_path):
    _base(repo)
    _commit(repo, {W: "# v2\n"}, 3)
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "-q", "--depth", "1", f"file://{repo}", str(clone))
    w = bw.compute_window(bw.WindowReader(clone, ref="origin/main"), "ga_x", [W])
    assert not w["ok"] and "shallow" in w["reason"], w


def test_origin_main_is_preferred_over_a_stale_local_main(repo, tmp_path):
    """A local checkout behind origin/main must date from origin/main (a later writer change on main is seen)."""
    _base(repo)
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "-q", f"file://{repo}", str(clone))
    _commit(repo, {W: "# v2\n"}, 12)
    _git(clone, "fetch", "-q", "origin")
    w = bw.compute_window(bw.WindowReader(clone), "ga_x", [W])
    # the clone's work tree still holds v1, which differs from origin/main: refused rather than dated from a stale main
    assert not w["ok"] and "not the code on main" in w["reason"], w
    _git(clone, "merge", "-q", "--ff-only", "origin/main")
    w2 = bw.compute_window(bw.WindowReader(clone), "ga_x", [W])
    assert w2["ok"] and w2["epoch"] == T0 + 12 * DAY and w2["ref"] == "origin/main", w2


def test_git_unavailable_is_unknown(repo, monkeypatch):
    _base(repo)

    def boom(*a, **k):
        raise FileNotFoundError("git")
    monkeypatch.setattr(bw.subprocess, "run", boom)
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert not w["ok"] and "could not run" in w["reason"], w


def test_compute_window_never_raises_on_a_bad_repo(tmp_path):
    w = bw.compute_window(bw.WindowReader(tmp_path / "does-not-exist"), "ga_x", [W])
    assert not w["ok"] and w["reason"], w


# ───────────────────────────── mutants: remove one guard, the defect must return ─────────────────────────────

def test_mutant_registry_ignored_reads_an_earlier_window(repo, monkeypatch):
    """If the registry date were dropped, the window would open at the (earlier) code date: a post-contract-change attempt
    would be missed and a pre-change attempt counted."""
    _base(repo)
    _commit(repo, {MIG: "UPDATE asset_registry SET count_sql='select 1' WHERE asset_id='ga_x';\n"}, 9)
    monkeypatch.setattr(bw.WindowReader, "registry_commit", lambda self, aid: (T0 + 1 * DAY, "0" * 40))
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert w["ok"] and w["epoch"] == T0 + 1 * DAY                      # the mutant's wrong answer
    monkeypatch.undo()
    w = bw.compute_window(bw.WindowReader(repo), "ga_x", [W])
    assert w["epoch"] == T0 + 9 * DAY                                  # the real one


def test_mutant_unmodified_check_off_dates_uncommitted_code_as_main(repo, monkeypatch):
    _base(repo)
    (repo / W).write_text("# edited, uncommitted\n")
    monkeypatch.setattr(bw.WindowReader, "tracked_and_unmodified", lambda self, paths: None)
    assert bw.compute_window(bw.WindowReader(repo), "ga_x", [W])["ok"]  # the defect: a window for code that is not main's
    monkeypatch.undo()
    assert not bw.compute_window(bw.WindowReader(repo), "ga_x", [W])["ok"]
