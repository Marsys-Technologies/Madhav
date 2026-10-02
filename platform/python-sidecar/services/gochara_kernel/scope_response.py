"""The mandatory coverage-response constructor (AM-14; Codex round 7 [2]).

Every answer the serving layer gives about this generation's stored tier — a POSITIVE answer (windows
found) AND a NO-WINDOW answer — is built here, and every one carries the generation's `stored_scope`
read BACK from the BOUND manifest vector (never a literal, never inferred). A manifest without the scope
REFUSES an unqualified completeness claim: the response says `completeness = "refused"` and names why;
it can never say "complete" about a tier whose scope it cannot state. An on-demand (Moon) answer does not
change the stored scope — it is listed beside it, so a reader sees both what the stored tier excludes and
which on-demand intervals have since been answered.

Serving code must call `coverage_response`; the stored tier's scope is `stored_non_moon`: the Moon is
the on-demand tier (AM-4), excluded from this generation's stored contacts, records and windows.
"""
from __future__ import annotations

import json as _json
from typing import Any, Sequence

SCOPE_STATEMENT = {
    "stored_non_moon": "the stored tier holds no Moon-agent contact, record or window; the Moon is served "
                       "on demand (moon_on_demand coverage), and Moon-resolved period portions are "
                       "accounted as excluded from the stored tier",
}


class ScopeMissing(RuntimeError):
    """The bound manifest does not state a stored scope."""


def bound_stored_scope(conn: Any, chart_id: str, generation: str) -> str:
    """The `stored_scope` of the generation's BOUND manifest vector; ScopeMissing if there is no manifest,
    no scope, or a scope this build does not know how to state."""
    row = conn.execute(
        "SELECT input_generation_vector FROM public.kala_gochara_publication"
        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if row is None:
        raise ScopeMissing(f"generation {generation} has no bound manifest")
    vector = row[0] if isinstance(row[0], dict) else _json.loads(row[0])
    scope = vector.get("stored_scope")
    if not scope:
        raise ScopeMissing(f"the manifest vector of generation {generation} states no stored_scope")
    if scope not in SCOPE_STATEMENT:
        raise ScopeMissing(f"stored_scope {scope!r} is not a scope this build can state")
    return scope


def on_demand_partitions(conn: Any, chart_id: str, generation: str) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT partition_key FROM public.kala_gochara_coverage WHERE chart_id = %s AND generation = %s"
        " AND partition_kind = 'moon_on_demand' ORDER BY partition_key", (chart_id, generation)).fetchall()]


def coverage_response(conn: Any, *, chart_id: str, generation: str, event_class: str,
                      windows: Sequence[Any]) -> dict:
    """The response for one (chart, generation, class): windows (possibly none), the scope, and the
    completeness claim — which is only ever made WITHIN a stated scope."""
    out: dict[str, Any] = {
        "chart_id": chart_id, "generation": generation, "event_class": event_class,
        "windows": list(windows), "window_count": len(windows),
        "on_demand_answered": on_demand_partitions(conn, chart_id, generation),
    }
    try:
        scope = bound_stored_scope(conn, chart_id, generation)
    except ScopeMissing as exc:
        out.update(stored_scope=None, completeness="refused", refusal="stored_scope_missing",
                   refusal_detail=str(exc))
        return out
    out.update(stored_scope=scope, scope_statement=SCOPE_STATEMENT[scope],
               completeness="complete_within_scope")
    return out


__all__ = ["SCOPE_STATEMENT", "ScopeMissing", "bound_stored_scope", "coverage_response",
           "on_demand_partitions"]
