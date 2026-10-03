"""TI-L0-24 (Track I, L0 INDEX section 8, SS Q11 / CF-10, PROVISIONAL until the J1 review): Build.history counts only
the runs since the last change to the asset's writer.

Before: Build.history graded EVERY build_run_assets row an asset ever had, so a past error (13 L0 assets read PARTIAL
"latest run complete, but N error(s) and M abort(s) on record", seven of them the same 2026-09-04..06
`integrity_check_sql -> False`) could never stop counting: no edit to the asset changes a history record.
SS Q11: Build.history counts only runs since the last change to the asset's writer or registry row; a repaired error
then stops counting.

Implemented here (asset_census.py `writer_change_epoch`, `windowed_history`, `_history_window`, measure()):
  * window start = the committer time of the latest git commit that touched ANY file of the writer's code (the
    registered class and the first-party definitions it delegates to, the census's own R20 delegation scope);
  * the cell is graded from only the runs created at or after the window start (same grader, same states);
  * a window with NO run in it keeps the whole-history verdict, unmoved, with the gap stated: no run since the change is no evidence either way, so
    nothing moves up (an old error predates a change nobody has run) and nothing moves down (and an invented NO_DETECTOR would launder a FAIL into a
    better-ranked cell, CLAUDE.md N.8);
  * the window is not applied, and the verdict is the unchanged full-history one with the reason stated, whenever
    git cannot say (not a work tree, a shallow clone, file untracked or never committed);
  * Build.exercised is untouched (it still reads the whole history).
Honest limit, stated in the verdict text and the registry comment: a change to the asset's REGISTRY ROW is not dated
anywhere (asset_registry has only created_at), so it does not move the window.

Offline: git behaviour on temp repositories, the SQL by a fake psql, the verdicts through the shared measure() harness.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_a_na_causes as na_causes  # noqa: E402

T0 = 1_760_000_000          # 2025-10-09, an arbitrary fixed epoch for commit times


# ───────────────────────────── git: writer_change_epoch ─────────────────────────────

def _git(repo, *args, when=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    if when is not None:
        env.update(GIT_AUTHOR_DATE=f"{when} +0000", GIT_COMMITTER_DATE=f"{when} +0000")
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)


def _commit(repo, name, text, when):
    (repo / name).write_text(text, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-m", f"{name} {when}", when=when)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _commit(r, "a.py", "a = 1\n", T0 + 100)
    _commit(r, "b.py", "b = 1\n", T0 + 200)
    _commit(r, "a.py", "a = 2\n", T0 + 300)
    _commit(r, "other.py", "o = 1\n", T0 + 400)
    return r


def test_epoch_is_the_latest_commit_touching_any_listed_file(repo):
    assert ac.writer_change_epoch(["a.py"], root=repo) == (T0 + 300, None)
    assert ac.writer_change_epoch(["b.py"], root=repo) == (T0 + 200, None)
    assert ac.writer_change_epoch(["a.py", "b.py"], root=repo) == (T0 + 300, None)


def test_a_commit_to_an_unlisted_file_does_not_move_the_epoch(repo):
    assert ac.writer_change_epoch(["a.py"], root=repo)[0] == T0 + 300          # other.py was committed at T0+400


def test_an_untracked_or_missing_file_is_not_dated(repo):
    (repo / "new.py").write_text("n = 1\n", encoding="utf-8")
    for rels in (["new.py"], ["missing.py"], []):
        epoch, why = ac.writer_change_epoch(rels, root=repo)
        assert epoch is None and why, (rels, why)


def test_one_undated_file_makes_the_whole_window_undated(repo):
    """A listed file git cannot date could be the newest change: the window is not guessed from the others."""
    (repo / "new.py").write_text("n = 1\n", encoding="utf-8")
    epoch, why = ac.writer_change_epoch(["a.py", "new.py"], root=repo)
    assert epoch is None and "new.py" in why, (epoch, why)


def test_a_shallow_clone_is_never_dated(repo, tmp_path):
    clone = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{repo}", str(clone)], check=True, capture_output=True)
    epoch, why = ac.writer_change_epoch(["b.py"], root=clone)       # the single grafted commit would date every file the same
    assert epoch is None and "shallow" in why, (epoch, why)


def test_a_directory_that_is_not_a_work_tree_is_not_dated(tmp_path):
    epoch, why = ac.writer_change_epoch(["a.py"], root=tmp_path)
    assert epoch is None and why


# ───────────────────────────── the real writer scope: _history_window ─────────────────────────────

def _repo_is_shallow():
    p = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=ac.ROOT, capture_output=True, text=True)
    return p.stdout.strip() == "true"


def test_history_window_dates_a_real_writer_by_its_repo_relative_scope_files():
    """bg_ontology's registered module and the first-party module it delegates to, as REPO-relative paths (the shape git is asked about; the
    scope's own `rel` is relative to the writers directory and would be 'not tracked')."""
    w = ac._history_window("bg_ontology", ["bg_ontology.py"])
    if _repo_is_shallow():                       # a CI checkout with depth 1: never dated, and it says why
        assert w[0] is None and "shallow" in w[1], w
        return
    epoch, source = w
    assert isinstance(epoch, int) and epoch > 1_700_000_000, w
    assert "platform/python-sidecar/brahmagyan/l0_ontology.py" in source, w          # the delegated module, repo-relative
    rels = [f for f in ("platform/python-sidecar/pipeline/orchestrator/writers/bg_ontology.py",
                        "platform/python-sidecar/brahmagyan/l0_ontology.py")
            if (ac.ROOT / f).is_file()]
    want = int(subprocess.run(["git", "log", "-1", "--format=%ct", "--", *rels], cwd=ac.ROOT, capture_output=True, text=True).stdout.strip())
    assert epoch >= want, (epoch, want)          # the scope may add files the two named here; it can only be as late or later


def test_history_window_without_writer_files_is_none():
    assert ac._history_window("bg_ontology", []) is None
    assert ac._history_window("bg_ontology", None) is None


# ───────────────────────────── SQL: windowed_history ─────────────────────────────

def _fake_psql(rows, seen):
    def fake(sql, sep="\x1f", timeout=None):
        seen.append(sql)
        return [list(r) for r in rows]
    return fake


def test_windowed_history_sql_bounds_every_asset_by_its_own_epoch_and_tallies_the_rest(monkeypatch):
    seen = []
    rows = [["bg_a", "layer", "complete", "build", "2026-10-01", "", "t"],
            ["bg_a", "layer", "complete", "build", "2026-10-02", "", "t"]]
    monkeypatch.setattr(ac, "psql", _fake_psql(rows, seen))
    out = ac.windowed_history("bg_", {"bg_a": T0 + 5, "bg_b": T0 + 9})
    sql = seen[0]
    assert "FROM build_run_assets a JOIN build_runs r ON r.id=a.run_id" in sql
    assert f"WHEN 'bg_a' THEN to_timestamp({T0 + 5})" in sql and f"WHEN 'bg_b' THEN to_timestamp({T0 + 9})" in sql, sql
    assert "r.created_at >= CASE a.asset_id" in sql, sql
    assert "ORDER BY a.asset_id, r.created_at, a.run_id" in sql, sql
    assert set(out) == {"bg_a"} and out["bg_a"]["complete"] == 2 and out["bg_a"]["error"] == 0   # bg_b: no row in its window
    assert out["bg_a"]["executed"] == 2


def test_windowed_history_with_no_windows_reads_nothing(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "psql", _fake_psql([], seen))
    assert ac.windowed_history("bg_", {}) == {} and seen == []


def test_windowed_history_refuses_a_malformed_epoch(monkeypatch):
    monkeypatch.setattr(ac, "psql", _fake_psql([], []))
    with pytest.raises((ValueError, TypeError)):
        ac.windowed_history("bg_", {"bg_a": "1; DROP TABLE x"})


def test_windowed_history_keeps_the_seven_field_read_guard(monkeypatch):
    monkeypatch.setattr(ac, "psql", _fake_psql([["bg_a", "t"]], []))
    with pytest.raises(ac.Unknown, match="did not parse into the 7 selected fields"):
        ac.windowed_history("bg_", {"bg_a": T0})


def test_the_full_history_read_is_unchanged(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "psql", lambda sql, sep="\x1f", timeout=None: (seen.append(sql), [])[1])
    monkeypatch.setattr(ac, "scalar", lambda sql: "0")
    ac.build_history("bg_", ["bg_a"])
    assert "to_timestamp" not in seen[0] and "CASE" not in seen[0], seen[0]


# ───────────────────────────── verdicts through measure() ─────────────────────────────

def _h(complete=0, error=0, aborted=0, last_state="complete", blocked=0, runs=None, sample_error=""):
    return dict(runs=runs if runs is not None else complete + error + aborted, executed=complete + error + aborted,
                states={}, error=error, blocked=blocked, aborted=aborted, complete=complete, skipped=0,
                last_state=last_state, last_disposition="build" if last_state == "complete" else "", last_when="2026-10-02",
                sample_error=sample_error, sample_error_when="2026-09-05" if sample_error else "", sample_blocked="",
                executed_scopes={"layer"}, last_executed_when="2026-10-02", scopes={"layer"})


FULL_OLD_ERROR = _h(complete=3, error=2, sample_error="post-write integrity check failed: integrity_check_sql -> False")
WINDOW = (T0 + 300, "a.py")                  # the writer last changed at T0+300


def _history_cell(monkeypatch, tmp_path, *, full, windowed, window=WINDOW, windowed_exc=None):
    reg = {"x": na_causes._reg_row("x", has_writer=True)}
    na_causes._stub_layer(monkeypatch, tmp_path, reg, registered={"x": ["x.py"]}, hist={"x": full})
    monkeypatch.setattr(ac, "_history_window", lambda aid, files: window)

    def fake_windowed(prefix, since):
        if windowed_exc:
            raise windowed_exc
        assert since == ({"x": window[0]} if window and window[0] is not None else {}), since
        return {"x": windowed} if windowed is not None else {}
    monkeypatch.setattr(ac, "windowed_history", fake_windowed)
    census = ac.measure("L0")
    return next(a for a in census["assets"] if a["asset_id"] == "x")["measurements"]


def test_without_the_window_the_old_error_still_reads_partial():
    """Control: the grader on the whole history, exactly as before the change."""
    assert ac._grade_build_history(FULL_OLD_ERROR)["v"] == ac.PARTIAL


def test_an_error_before_the_last_writer_change_stops_counting(monkeypatch, tmp_path):
    """The key test: errors predate the writer change, every run since is clean -> PASS, and the text says why."""
    m = _history_cell(monkeypatch, tmp_path, full=FULL_OLD_ERROR, windowed=_h(complete=2))
    cell = m["Build.history"]
    assert cell["v"] == ac.PASS, cell
    assert "since the last writer change" in cell["measured"] and "2 complete" in cell["measured"], cell
    assert "registry row" in cell["measured"], cell                       # the undated half is stated, not hidden
    assert "3 earlier build_run_assets row(s)" in cell["measured"], cell  # 5 rows in all, 2 since the change


def test_an_error_after_the_last_writer_change_still_counts(monkeypatch, tmp_path):
    m = _history_cell(monkeypatch, tmp_path, full=FULL_OLD_ERROR, windowed=_h(complete=1, error=1, sample_error="boom"))
    assert m["Build.history"]["v"] == ac.PARTIAL, m["Build.history"]


def test_a_failed_latest_run_inside_the_window_still_fails(monkeypatch, tmp_path):
    m = _history_cell(monkeypatch, tmp_path, full=FULL_OLD_ERROR,
                      windowed=_h(error=1, last_state="error", sample_error="boom"))
    assert m["Build.history"]["v"] == ac.FAIL, m["Build.history"]


def test_a_window_with_no_run_keeps_the_whole_history_verdict(monkeypatch, tmp_path):
    """The writer changed after the last run: nothing has been re-earned, so nothing moves."""
    clean = _h(complete=5)
    m = _history_cell(monkeypatch, tmp_path, full=clean, windowed=None)
    cell = m["Build.history"]
    assert cell["v"] == ac.PASS and "not yet re-earned" in cell["measured"] and "whole-history verdict is kept" in cell["measured"], cell


def test_a_failed_history_is_not_laundered_into_a_better_cell_by_a_writer_change(monkeypatch, tmp_path):
    """FAIL ranks below NO_DETECTOR: reading an empty window as NO_DETECTOR would move a FAIL UP on no evidence."""
    failing = _h(complete=2, error=1, last_state="error", sample_error="boom")
    m = _history_cell(monkeypatch, tmp_path, full=failing, windowed=None)
    assert m["Build.history"]["v"] == ac.FAIL and "not yet re-earned" in m["Build.history"]["measured"], m["Build.history"]


def test_a_partial_history_stays_partial_until_a_run_after_the_change_earns_the_move(monkeypatch, tmp_path):
    m = _history_cell(monkeypatch, tmp_path, full=FULL_OLD_ERROR, windowed=None)
    assert m["Build.history"]["v"] == ac.PARTIAL, m["Build.history"]


def test_an_undated_window_keeps_the_full_history_verdict_and_says_so(monkeypatch, tmp_path):
    m = _history_cell(monkeypatch, tmp_path, full=FULL_OLD_ERROR, windowed=None, window=(None, "repository is shallow"))
    cell = m["Build.history"]
    assert cell["v"] == ac.PARTIAL and "window not applied" in cell["measured"] and "shallow" in cell["measured"], cell


def test_no_files_to_date_keeps_the_full_history_verdict(monkeypatch, tmp_path):
    m = _history_cell(monkeypatch, tmp_path, full=FULL_OLD_ERROR, windowed=None, window=None)
    assert m["Build.history"]["v"] == ac.PARTIAL and "window not applied" not in m["Build.history"]["measured"]


def test_an_unreadable_windowed_history_is_errored_never_a_fallback(monkeypatch, tmp_path):
    m = _history_cell(monkeypatch, tmp_path, full=FULL_OLD_ERROR, windowed=None, windowed_exc=ac.Unknown("proxy down"))
    assert m["Build.history"]["v"] == ac.ERRORED and "proxy down" in m["Build.history"]["measured"], m["Build.history"]


def test_build_exercised_still_reads_the_whole_history(monkeypatch, tmp_path):
    m = _history_cell(monkeypatch, tmp_path, full=FULL_OLD_ERROR, windowed=None)
    assert m["Build.exercised"]["v"] == ac.PASS and "5 executed run(s) of 5" in m["Build.exercised"]["measured"], m["Build.exercised"]


def test_the_window_can_be_switched_off(monkeypatch, tmp_path):
    """The real `_history_window` (not stubbed): with the switch off git is never asked."""
    reg = {"x": na_causes._reg_row("x", has_writer=True)}
    na_causes._stub_layer(monkeypatch, tmp_path, reg, registered={"x": ["x.py"]}, hist={"x": FULL_OLD_ERROR})
    monkeypatch.setattr(ac, "HISTORY_WINDOW_ENABLED", False)

    def boom(*a, **k):
        raise AssertionError("git / the windowed read must not be consulted when the window is off")
    monkeypatch.setattr(ac, "writer_change_epoch", boom)
    monkeypatch.setattr(ac, "windowed_history", boom)
    cell = next(a for a in ac.measure("L0")["assets"] if a["asset_id"] == "x")["measurements"]["Build.history"]
    assert cell["v"] == ac.PARTIAL and "since the last writer change" not in cell["measured"], cell
    assert "window not applied" not in cell["measured"], cell      # switched off is not 'tried and could not date'
