"""test_a3_earn_cost_grading.py — D6 acceptance cases for `_grade_earn_cost()` (Nikaṣa wave 1,
Lane A, R55 re-specified). The seven test cases D6 item 5 names: failure, zero rows, skip after a
prior timing, probe-green, the legacy ga_* path, the absent column, an unknown NULL.

`_grade_earn_cost()` is a pure function (same discipline as B1's `_grade_build_history`): it takes
a hand-built `attempt`/`baseline` and grades `Earn.build_record` + `Cost.baseline` without touching
a database. It is exercised here rather than live because `asset_throughput.duration_seconds`
(migration 1094) does not exist in this environment — confirmed 2026-09-27 against both production
(`information_schema.columns`) and the nikasha_sandbox proof DB — so `measure()` always calls it
with `instrument_present=False` today; every branch below proves the classifier is CORRECT for the
day migration 1094 lands, not merely that it compiles.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_a3_earn_cost_grading.py -v
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import asset_census as ac  # noqa: E402


def _attempt(**overrides) -> dict:
    base = dict(state="complete", disposition="", reached_completion_write=True,
                duration_seconds=None, rows_written=None, is_legacy_telemetry=False, has_writer=True)
    base.update(overrides)
    return base


# ── Case: the absent column (feature detection; both measurements, not PARTIAL) ──

def test_case_absent_column_grades_no_detector_never_partial():
    earn, cost = ac._grade_earn_cost(attempt=_attempt(duration_seconds=12.0, rows_written=5),
                                      instrument_present=False, baseline=dict(rate=1.0, attempt_id="x", age_days=1))
    assert earn["v"] == ac.NO_DET and cost["v"] == ac.NO_DET
    assert "migration 1094" in earn["measured"] and "migration 1094" in cost["measured"]
    assert ac.PARTIAL not in (earn["v"], cost["v"]), "D6 item 1: neither is PARTIAL — nothing was partly measured"


def test_case_instrument_unreachable_is_a_distinct_reason(monkeypatch):
    """A failed feature-detection query is NO_DETECTOR — instrument unreachable, distinct wording
    from 'absent' (D6 item 1)."""
    monkeypatch.setattr(ac, "scalar", lambda sql: (_ for _ in ()).throw(ac.Unknown("timeout")))
    assert ac.duration_instrument_present() is None
    earn, cost = ac._grade_earn_cost(attempt=None, instrument_present=None, baseline=None)
    assert earn["v"] == ac.NO_DET and "unreachable" in earn["measured"]
    assert cost["v"] == ac.NO_DET and "unreachable" in cost["measured"]


# ── Case: failure (attempt failed before any completion write) ──

def test_case_failure_before_completion_grades_earn_na_cost_by_prior_baseline():
    earn, cost = ac._grade_earn_cost(
        attempt=_attempt(state="error", reached_completion_write=False),
        instrument_present=True, baseline=None)
    assert earn["v"] == ac.NA and "Build.history" in earn["measured"]
    assert cost["v"] == ac.FAIL, "no baseline exists yet — a failure does not create one"


def test_case_failure_does_not_erase_a_prior_cost_baseline():
    earn, cost = ac._grade_earn_cost(
        attempt=_attempt(state="aborted", reached_completion_write=False),
        instrument_present=True, baseline=dict(rate=3.2, attempt_id="attempt-7", age_days=4))
    assert earn["v"] == ac.NA
    assert cost["v"] == ac.PASS, "a failed LATEST attempt must not erase an earlier sanctioned baseline"
    assert "attempt-7" in cost["measured"]


# ── Case: zero rows (a measured rate of 0.0 must PASS, never be suppressed) ──

def test_case_zero_rows_with_finite_duration_grades_pass_with_rate_zero():
    earn, cost = ac._grade_earn_cost(
        attempt=_attempt(duration_seconds=4.5, rows_written=0),
        instrument_present=True, baseline=None)
    assert earn["v"] == ac.PASS
    assert "rate=0.0" in earn["measured"], "a zero-row completion's rate is a real measurement"


# ── Case: skip after a prior timing (healthy non-execution; baseline survives) ──

def test_case_skip_no_delta_grades_na_and_preserves_prior_baseline():
    earn, cost = ac._grade_earn_cost(
        attempt=_attempt(disposition="skip_no_delta"),
        instrument_present=True, baseline=dict(rate=2.0, attempt_id="attempt-3", age_days=10))
    assert earn["v"] == ac.NA and "skip_no_delta" in earn["measured"]
    assert cost["v"] == ac.PASS, "a healthy skip neither erases nor creates a baseline"


# ── Case: probe-green (healthy non-execution, service path) ──

def test_case_probe_green_grades_na():
    earn, cost = ac._grade_earn_cost(
        attempt=_attempt(disposition="probe_green"),
        instrument_present=True, baseline=None)
    assert earn["v"] == ac.NA and "probe_green" in earn["measured"]
    assert cost["v"] == ac.FAIL  # no baseline on record yet — independent of the probe outcome


def test_case_legacy_health_probe_service_no_writer_grades_na():
    """D6 item 3: 'a legacy health-probe service with no registered writer -> N/A', the same
    disposal as a healthy skip, distinct code path (has_writer=False, no disposition set)."""
    earn, _ = ac._grade_earn_cost(
        attempt=_attempt(disposition="", has_writer=False),
        instrument_present=True, baseline=None)
    assert earn["v"] == ac.NA and "no registered writer" in earn["measured"]


# ── Case: the legacy ga_* path (completion write, no duration, R34's residual) ──

def test_case_legacy_telemetry_path_grades_fail():
    earn, _ = ac._grade_earn_cost(
        attempt=_attempt(duration_seconds=None, is_legacy_telemetry=True),
        instrument_present=True, baseline=None)
    assert earn["v"] == ac.FAIL and "_telemetry" in earn["measured"]


# ── Case: an unknown NULL (completion write, no duration, no identified cause) ──

def test_case_unclassified_null_grades_no_detector_never_pass():
    earn, _ = ac._grade_earn_cost(
        attempt=_attempt(duration_seconds=None, is_legacy_telemetry=False),
        instrument_present=True, baseline=None)
    assert earn["v"] == ac.NO_DET and "unclassified" in earn["measured"]
    assert earn["v"] != ac.PASS


# ── Never-attempted asset (no attempt row at all) ──

def test_case_never_attempted_grades_na():
    """This is the LEGITIMATE case — attempt linkage genuinely wired (`attempt_linkage_wired`
    defaults True) and the query genuinely found no attempt row. Distinct from F1 below, where
    `attempt=None` means 'never queried', not 'confirmed absent'."""
    earn, _ = ac._grade_earn_cost(attempt=None, instrument_present=True, baseline=None)
    assert earn["v"] == ac.NA and "Build.exercised" in earn["measured"]


# ── F1 (A_REVIEW.md, Lane A gate REJECT): the unwired path must never read N/A ──

def test_case_instrument_present_attempt_linkage_unwired_grades_no_detector_not_na():
    """F1: `measure()` never queries build_run_assets for a real attempt (that wiring is
    R42-R56, out of scope this lane — see §A-4) — it always calls `_grade_earn_cost` with
    `attempt=None, attempt_linkage_wired=False`. Before this fix, `attempt=None` alone graded
    N/A "never attempted", which is CLOSABLE: the moment migration 1094 lands, every one of the
    ~40 L0 assets that DO have a build history would have its Earn.build_record gap wrongly
    closed on a fact this run never measured. The unwired path must read NO_DETECTOR — never
    N/A — regardless of instrument presence."""
    earn, cost = ac._grade_earn_cost(attempt=None, instrument_present=True, baseline=None,
                                      attempt_linkage_wired=False)
    assert earn["v"] == ac.NO_DET, f"expected NO_DETECTOR, got {earn['v']}: {earn['measured']}"
    assert "attempt linkage not wired" in earn["measured"]
    assert earn["v"] not in ac.CLOSABLE, "NO_DETECTOR must never be a closable verdict"
    assert cost["v"] == ac.NO_DET, "Cost.baseline is equally unwired — same fix, same reason"
    assert "attempt linkage not wired" in cost["measured"]


def test_case_attempt_linkage_unwired_is_the_default_measure_call_shape(monkeypatch):
    """Locks in the actual `measure()` call site shape so this test fails if the call site
    regresses back to the pre-F1 form (attempt=None with no attempt_linkage_wired argument,
    which would silently fall back to the default True and grade N/A again)."""
    import inspect
    src = inspect.getsource(ac.measure)
    assert "attempt_linkage_wired=False" in src, (
        "measure() must pass attempt_linkage_wired=False explicitly — attempt querying (R42-R56) "
        "is not wired at this call site"
    )


def test_emit_gaps_does_not_close_on_the_unwired_no_detector(tmp_path, monkeypatch):
    """F1's closure-side proof: simulate a previously-OPEN Earn.build_record gap, then run
    emit_gaps against exactly the measurement `_grade_earn_cost` now produces for the unwired
    path with the instrument present. The gap must stay OPEN, not close."""
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    ledger = tmp_path / "asset_gaps.jsonl"
    ledger.write_text(
        '{"asset": "bg_x", "gap_id": "bg_x-Earn.build_record", "kind": "gap", '
        '"criterion": "Earn.build_record", "what": "w", "change": "", "detector": "d", '
        '"owner": "asset_census", "gate": "this asset\'s certification", "state": "OPEN", '
        '"ts": "t0"}\n', encoding="utf-8")
    earn, _ = ac._grade_earn_cost(attempt=None, instrument_present=True, baseline=None,
                                   attempt_linkage_wired=False)
    census = dict(layer="L0", assets=[dict(asset_id="bg_x", measurements={"Earn.build_record": earn})])
    added, skipped, closed, reopened = ac.emit_gaps(census)
    assert closed == 0, "the unwired NO_DETECTOR path must never close a gap"
    rows = [json.loads(ln) for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert rows[-1]["state"] == "OPEN"
