"""
Chart-context staleness (Jātaka Phase-A3, item 2): mi_bhara's `fetch_open_predictions`
feeds field-skill scoring — a "current calibration" read of
`brahma_prospective_ledger`. A prediction a correction has marked
chart_context_stale_at (migration 1123) was filed under former birth
details and must not enter that scoring.
"""
import inspect
import re

from services.mi_bhara import db as mi_bhara_db


def _fetch_source() -> str:
    return inspect.getsource(mi_bhara_db.fetch_open_predictions)


def test_excludes_context_stale_predictions():
    src = _fetch_source()
    m = re.search(
        r"FROM brahma_prospective_ledger(.*?)ORDER BY",
        src,
        re.S,
    )
    assert m, "expected the brahma_prospective_ledger WHERE clause"
    where_clause = m.group(1)
    assert "chart_context_stale_at" in where_clause, (
        "a chart-context-stale prediction must not feed mi_bhara's field-skill "
        "scoring as if it reflected the chart's current birth details"
    )
    assert "IS NULL" in where_clause


def test_never_touches_lifecycle_status_or_rewrites_the_row():
    src = _fetch_source()
    assert "SET " not in src
    assert re.search(r"lifecycle_status\s*=\s*'open'", src)
