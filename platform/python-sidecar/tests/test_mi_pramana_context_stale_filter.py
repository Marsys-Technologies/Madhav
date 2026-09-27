"""
Chart-context staleness (Jātaka Phase-A2, item 2): mi_pramana's own
`mimamsa_predictions` read is the calibration substep's input — a prediction
row context-staled by a birth-details correction (migration 1122;
`chart_context_stale_at` set) must not feed current-chart calibration.
`chart_context_stale_at`/`chart_context_stale_reason`/
`chart_context_superseded_by_run_id` are orthogonal metadata (never
lifecycle_status/outcome) — this filter reads that metadata, it never
rewrites it or any prediction's lifecycle/outcome value.
"""
import inspect
import re

from pipeline.orchestrator.writers import mi_pramana


def _match_source() -> str:
    return inspect.getsource(mi_pramana.MiPramanaWriter._substep_match)


def test_predictions_read_excludes_context_stale_rows():
    src = _match_source()
    m = re.search(
        r'"SELECT \* FROM mimamsa_predictions WHERE chart_id = %s(.*?)"',
        src,
        re.S,
    )
    assert m, "expected mi_pramana's mimamsa_predictions SELECT to be scoped"
    assert "chart_context_stale_at" in m.group(1), (
        "the calibration match substep must exclude rows a correction has "
        "marked context-stale — otherwise a birth-details correction leaves "
        "calibration silently computed against former-chart predictions"
    )
    assert "IS NULL" in m.group(1)


def test_predictions_read_never_touches_lifecycle_status_or_outcome():
    # The staleness filter is orthogonal metadata read, never a rewrite of the
    # prediction's own lifecycle/outcome fields.
    src = _match_source()
    m = re.search(
        r'"SELECT \* FROM mimamsa_predictions WHERE chart_id = %s(.*?)"',
        src,
        re.S,
    )
    assert m
    assert "lifecycle_status" not in m.group(1)
    assert "SET " not in m.group(1)
