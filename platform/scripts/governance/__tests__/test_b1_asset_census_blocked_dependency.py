"""test_b1_asset_census_blocked_dependency.py — Packet B1 §N.8 proof for the
governance census surface (the worst offender named in
00_ARCHITECTURE/briefs/nirmana/engine/measurements/B1_before_20260926T173931Z.json §4:
"a chart whose every failure was a downstream consequence is currently graded as if
it had real defects").

`_grade_build_history()` (extracted from measure()'s inline Build.history block) is
the pure decision function under test. It grades one asset's build_run_assets
history dict `h` (as produced by build_history()) into a PASS/PARTIAL/FAIL verdict.

Mutation-checked framing: reverting the fix (i.e. computing `bad = h["error"] +
h["aborted"]` again, with no blocked-aware carve-out) makes every test below that
asserts PASS/PARTIAL fail against a genuinely-cascade-only `h` — they would grade
FAIL/PARTIAL exactly as the pre-fix code did.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_b1_asset_census_blocked_dependency.py -v
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import asset_census  # noqa: E402


def _h(**overrides) -> dict:
    """A build_history()-shaped per-asset dict with every key defaulted to the
    'never touched' value, so each test only names what it actually varies."""
    base = dict(
        runs=0, error=0, aborted=0, complete=0, queued=0, skipped=0, blocked=0,
        last_state="", last_when="", last_disposition="", sample_error="", sample_blocked="",
    )
    base.update(overrides)
    return base


# ── §N.8: the earned signal — a chart with ONLY cascade blocks must not FAIL ────

def test_all_blocked_no_genuine_error_grades_pass_not_fail():
    """The packet's core claim: a chart whose every build_run_assets 'error' row is
    a cascade block (disposition='blocked_dependency') from someone else's failure,
    with zero genuine errors of its own, must grade PASS — not FAIL, not even
    PARTIAL. Pre-fix, `bad = h['error'] + h['aborted']` would count these 3 blocked
    rows as 3 real errors and the last_state=='error' branch would FAIL it outright.
    """
    h = _h(runs=4, complete=1, error=3, blocked=3, aborted=0,
           last_state="error", last_disposition="blocked_dependency", last_when="2026-09-20",
           sample_blocked="BLOCKED: upstream dependency(ies) some_root did not complete in this run; skipped to avoid building on incomplete data")
    verdict = asset_census._grade_build_history(h)
    assert verdict["v"] == asset_census.PASS, (
        f"expected PASS for an all-cascade history, got {verdict['v']}: {verdict['measured']}"
    )
    assert "3 blocked_dependency" in verdict["measured"], (
        "the blocked count must still be surfaced in the measured text (§N.6: count, "
        "never silently drop it), even though it does not fail the grade"
    )


def test_never_completed_all_cascade_grades_partial_not_pass():
    """C-4 (review B1_review_20260926T182200Z.md, §N.8 defect class): an asset that
    has NEVER ONCE completed a build — every single attempt cascade-blocked, none
    of them a genuine error of its own — must NOT grade PASS. 'no genuine error'
    is not the same claim as 'builds successfully', and PASS with complete==0 is a
    green signal with no detector behind the completion claim. Reproduces the
    reviewer's own probe verbatim: _grade_build_history({complete: 0, error: 4,
    blocked: 4, ...}) must no longer return PASS.
    """
    h = _h(runs=4, complete=0, error=4, blocked=4, aborted=0,
           last_state="error", last_disposition="blocked_dependency", last_when="2026-09-20",
           sample_blocked="BLOCKED: upstream dependency(ies) some_root did not complete in this run; skipped to avoid building on incomplete data")
    verdict = asset_census._grade_build_history(h)
    assert verdict["v"] != asset_census.PASS, (
        f"an asset with ZERO completions must never grade PASS, got {verdict['v']}: {verdict['measured']}"
    )
    assert verdict["v"] == asset_census.PARTIAL
    assert "0 complete" in verdict["measured"] or "NEVER" in verdict["measured"]


def test_at_least_one_completion_with_blocked_rows_still_grades_pass():
    """Regression guard for the C-4 fix itself: the guard must trigger ONLY on
    complete==0, not on the mere presence of blocked rows — an asset with at least
    one genuine completion and an all-cascade remainder still grades PASS exactly
    as test_all_blocked_no_genuine_error_grades_pass_not_fail already asserts.
    This test re-affirms the boundary explicitly at complete==1."""
    h = _h(runs=4, complete=1, error=3, blocked=3, aborted=0,
           last_state="error", last_disposition="blocked_dependency", last_when="2026-09-20",
           sample_blocked="BLOCKED: upstream dependency(ies) some_root did not complete in this run; skipped to avoid building on incomplete data")
    verdict = asset_census._grade_build_history(h)
    assert verdict["v"] == asset_census.PASS


def test_genuine_error_still_fails_even_with_blocked_rows_present():
    """A REAL defect must still FAIL the chart even when blocked rows are also
    present — this proves the fix differentiates rather than blanket-suppressing
    every 'error' row (the 'marks nothing blocked' failure mode named in the
    packet's §N.8 requirement: 'a classifier that marks everything blocked is as
    broken as one that marks nothing')."""
    h = _h(runs=5, complete=1, error=4, blocked=3, aborted=0,
           last_state="error", last_disposition="", last_when="2026-09-21",
           sample_error="TIMEOUT: writer exceeded its writer_timeout_seconds budget (600s) — this asset is the failure, not a blocked dependent")
    verdict = asset_census._grade_build_history(h)
    assert verdict["v"] == asset_census.FAIL, (
        f"a genuine (non-blocked_dependency) most-recent-run error must still FAIL, got {verdict['v']}"
    )
    assert "1 error(s)" in verdict["measured"], "genuine_error must be error(4) - blocked(3) = 1, not 4"
    assert "3 blocked_dependency" in verdict["measured"]


def test_older_genuine_error_with_latest_run_blocked_only_grades_partial():
    """Most recent run is a pure cascade block, but an OLDER run in history had a
    real error — must grade PARTIAL (bad>0), not silently PASS and not FAIL purely
    because the latest state happens to be 'error'."""
    h = _h(runs=3, complete=1, error=2, blocked=1, aborted=0,
           last_state="error", last_disposition="blocked_dependency", last_when="2026-09-25",
           sample_error="worker_crash: RuntimeError: boom")
    verdict = asset_census._grade_build_history(h)
    assert verdict["v"] == asset_census.PARTIAL, f"expected PARTIAL, got {verdict['v']}: {verdict['measured']}"
    assert "1 error(s)" in verdict["measured"]  # genuine_error = 2 - 1 = 1


def test_clean_history_with_no_blocked_rows_is_unaffected():
    """A chart with zero errors and zero blocked rows must grade exactly as before
    the fix — this packet must not change behaviour for the unaffected majority."""
    h = _h(runs=6, complete=6, error=0, blocked=0, aborted=0,
           last_state="complete", last_disposition="", last_when="2026-09-24", skipped=2)
    verdict = asset_census._grade_build_history(h)
    assert verdict["v"] == asset_census.PASS
    assert "blocked_dependency" not in verdict["measured"], (
        "a history with zero blocked rows must not mention blocked_dependency at all"
    )


def test_aborted_is_still_a_genuine_failure_trigger_independent_of_blocked():
    """'aborted' (a distinct state from 'error') must remain a FAIL trigger on its
    own — the fix only carves out disposition='blocked_dependency' 'error' rows, it
    must not accidentally soften 'aborted' handling too."""
    h = _h(runs=2, complete=0, error=0, blocked=0, aborted=1,
           last_state="aborted", last_disposition="", last_when="2026-09-22")
    verdict = asset_census._grade_build_history(h)
    assert verdict["v"] == asset_census.FAIL


# ── build_history() itself: the blocked/genuine split is computed correctly ────

def test_build_history_separates_blocked_from_genuine_error(monkeypatch):
    """build_history() must tally disposition='blocked_dependency' rows into
    `blocked` (and NOT let them contaminate `sample_error`), while a genuine error
    row still populates `sample_error`."""
    rows = [
        ["bg_x", "layer", "error", "blocked_dependency", "2026-09-20",
         "BLOCKED: upstream dependency(ies) bg_root did not complete in this run; skipped to avoid building on incomplete data"],
        ["bg_x", "layer", "error", "blocked_dependency", "2026-09-21",
         "BLOCKED: upstream dependency(ies) bg_root did not complete in this run; skipped to avoid building on incomplete data"],
        ["bg_x", "layer", "error", "", "2026-09-22", "TIMEOUT: writer exceeded its writer_timeout_seconds budget (600s)"],
        ["bg_x", "layer", "complete", "", "2026-09-23", ""],
    ]

    def _fake_psql(sql, sep="\x1f"):
        if "build_run_assets" in sql and "build_runs" in sql:
            return rows
        if "asset_throughput" in sql:
            return []
        return []

    def _fake_scalar(sql):
        return "0"

    monkeypatch.setattr(asset_census, "psql", _fake_psql)
    monkeypatch.setattr(asset_census, "scalar", _fake_scalar)

    hist = asset_census.build_history("bg_")
    h = hist["per"]["bg_x"]
    assert h["runs"] == 4
    assert h["error"] == 3          # all three error-state rows, blocked + genuine
    assert h["blocked"] == 2        # only the two disposition='blocked_dependency' rows
    assert h["complete"] == 1
    assert h["sample_error"] == "TIMEOUT: writer exceeded its writer_timeout_seconds budget (600s)", (
        "sample_error must come from the GENUINE (non-blocked) error row, never a "
        "blocked_dependency row's text"
    )
    assert h["sample_blocked"].startswith("BLOCKED:")
    assert h["last_state"] == "complete" and h["last_disposition"] == ""
