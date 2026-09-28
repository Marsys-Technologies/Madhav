"""
Chart-context staleness (Jātaka Phase-A2, item 2): `lel_query`'s LEFT JOIN to
event_chart_state_index must treat a context-staled row (migration 1122;
chart_context_stale_at set — the only writer of this table is a manual CLI
seed, never the automated build DAG, so a correction can never rebuild it,
only mark it) as no match, not as current dasha/transit context. The ON
clause is the only correct place: a WHERE-clause filter would drop the
life_events row itself, which must always be served (life_events is never
context-staled — it carries no derived chart-context data of its own).
"""
import inspect
import re

from brahmagyan.mimamsa import lel_intake


def _query_source() -> str:
    return inspect.getsource(lel_intake.lel_query)


def test_join_excludes_context_stale_event_chart_state_rows():
    src = _query_source()
    m = re.search(
        r"LEFT JOIN event_chart_state_index cs\s*\n\s*ON (.*?)\n\s*\{where_clause\}",
        src,
        re.S,
    )
    assert m, "expected the LEFT JOIN event_chart_state_index ON clause"
    on_clause = m.group(1)
    assert "chart_context_stale_at" in on_clause, (
        "a context-staled dasha/transit row must not be joined in as if "
        "current — the ON clause (not WHERE) keeps the life_events row itself"
    )
    assert "IS NULL" in on_clause


def test_life_events_row_is_never_filtered_by_the_staleness_join():
    # The LEFT JOIN shape itself (not INNER JOIN) is what keeps a life_events
    # row served even when its dasha/transit context is stale or absent.
    src = _query_source()
    assert "LEFT JOIN event_chart_state_index" in src
    assert "INNER JOIN event_chart_state_index" not in src
