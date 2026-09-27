"""
Chart-context staleness (Jātaka Phase-A2, item 2): mi_gunanaka's calibration
LEFT JOIN to mimamsa_predictions must treat a context-staled prediction row
(migration 1122; chart_context_stale_at set) as no match, not as a live
driving_signals source — the ON clause is the only correct place for this
(a WHERE-clause filter would silently drop the calibration row itself).
"""
import inspect
import re

from pipeline.orchestrator.writers import mi_gunanaka


def _run_source() -> str:
    return inspect.getsource(mi_gunanaka.MiGunakaWriter.run)


def test_calibration_join_excludes_context_stale_predictions():
    src = _run_source()
    m = re.search(
        r"LEFT JOIN mimamsa_predictions p ON (.*?)\n\s*\"WHERE",
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
    src = _run_source()
    m = re.search(r"LEFT JOIN mimamsa_predictions p ON (.*?)\n\s*\"WHERE", src, re.S)
    assert m
    assert "lifecycle_status" not in m.group(1)
