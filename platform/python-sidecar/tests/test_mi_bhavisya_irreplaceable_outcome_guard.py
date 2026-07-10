"""
R6 fix: mi_bhavisya.py's idempotent per-chart delete-then-insert previously deleted
ALL mimamsa_predictions rows unconditionally on every rebuild -- including rows whose
lifecycle_status has moved to 'confirmed'/'denied'/'partial', which carry a real,
native-verified outcome written exclusively by mi_abhilekha's journal-answer sync.
That is IRREPLACEABLE data (JL-020 classification) and must never be destroyed by a
routine rebuild of this writer. The delete must scope to lifecycle_status IN
('pending', 'due') -- only this writer's own still-forecasting, rebuildable rows.
"""
import inspect
import re

from pipeline.orchestrator.writers import mi_bhavisya


def _run_source() -> str:
    return inspect.getsource(mi_bhavisya.MiBhavisyaWriter.run)


def test_predictions_delete_is_scoped_to_pending_or_due_only():
    src = _run_source()
    m = re.search(
        r'DELETE FROM mimamsa_predictions WHERE chart_id = %s(.*?)"', src
    )
    assert m, "expected an unconditional-looking DELETE FROM mimamsa_predictions statement to scope"
    assert "lifecycle_status" in m.group(1), (
        "mimamsa_predictions delete must be scoped by lifecycle_status -- an unscoped "
        "per-chart delete destroys confirmed/denied/partial rows (real recorded native "
        "outcomes) alongside pending forecasts"
    )
    assert "'pending'" in m.group(1) and "'due'" in m.group(1), (
        "must preserve exactly the non-forecasting statuses ('confirmed'/'denied'/'partial'); "
        "only 'pending'/'due' rows are this writer's own rebuildable output"
    )


def test_predictions_delete_does_not_reference_the_dropped_outcome_observed_column():
    # outcome_observed/brier_score belonged to the v1.0 table dropped by migration 346a and
    # recreated with a different schema by 347_mimamsa_bhavisya.sql -- never resurrect it.
    src = _run_source()
    assert "outcome_observed" not in src
    assert "brier_score" not in src


def test_manifestation_sets_delete_remains_unconditional():
    # mimamsa_manifestation_sets carries no outcome-tracking column -- it is fully
    # rebuildable, unconditional per-chart delete is correct and must not regress.
    src = _run_source()
    assert re.search(
        r"DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s\s*[,)\"']", src
    ), "mimamsa_manifestation_sets delete should remain a plain per-chart delete"
