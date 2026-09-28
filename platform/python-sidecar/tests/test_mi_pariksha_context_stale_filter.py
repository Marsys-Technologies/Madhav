"""
Chart-context staleness (Jātaka Phase-A2, item 2): mi_pariksha's attribution
LEFT JOIN to mimamsa_predictions must treat a context-staled prediction row
(migration 1122; chart_context_stale_at set) as no match, not as a live
driving_signals source — same discipline as mi_gunanaka's identical join
shape (the ON clause, not WHERE, keeps the calibration row itself).
"""
import inspect
import re

from pipeline.orchestrator.writers import mi_pariksha


def _attribution_source() -> str:
    return inspect.getsource(mi_pariksha.MiParikshaWriter._substep_attribution)


def test_calibration_join_excludes_context_stale_predictions():
    src = _attribution_source()
    m = re.search(
        r"LEFT JOIN mimamsa_predictions p\s*\"?\s*\"?\s*ON (.*?)\n\s*\"WHERE",
        src,
        re.S,
    )
    assert m, "expected the LEFT JOIN mimamsa_predictions ON clause"
    on_clause = m.group(1)
    assert "chart_context_stale_at" in on_clause, (
        "a context-staled prediction must not be joined in as if current — "
        "the ON clause (not WHERE) is what keeps the calibration row itself"
    )
    assert "IS NULL" in on_clause


def test_join_never_touches_lifecycle_status_or_outcome():
    src = _attribution_source()
    m = re.search(r"LEFT JOIN mimamsa_predictions p\s*\"?\s*\"?\s*ON (.*?)\n\s*\"WHERE", src, re.S)
    assert m
    assert "lifecycle_status" not in m.group(1)
