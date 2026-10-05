"""G1 (REBUILD_AND_UPSTREAM_SEQUENCING_v1_0): a SEALED generation is never re-checked
against upstream drift — once L1 facts or the pinned daśā rows change under it, the
seal keeps certifying inputs that no longer exist. This module is the read-only check
that closes the gap: for one (chart, generation) it recomputes the snapshot's digests
from the LIVE rows with the database's own functions (the same ones the builder used,
so the check cannot disagree with the seal about the digest definition) and reports,
per component, whether the stored value still holds.

The check is pure read: no locks, no writes, no seal side effects. It never rebuilds
or invalidates anything — it answers "is this generation's pinned input identity still
the live one?", for a sealed generation (the G1 case) and for a candidate alike.
"""
from __future__ import annotations

import json as _json
from typing import Any


class SnapshotMissingError(RuntimeError):
    """No input snapshot for (chart, generation) — there is nothing to check (the
    manifest/snapshot substeps have not run for this generation)."""


def sealed_generation_staleness(conn: Any, chart_id: str, generation: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT convention_id, input_generation_vector, consumed_fact_ids,"
        "       consumed_dasha_row_ids, av_declarations,"
        "       l1_facts_digest, dasha_digest, input_digest"
        " FROM public.ka_gochara_search_input_snapshot"
        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if row is None:
        raise SnapshotMissingError(
            f"no ka_gochara_search_input_snapshot for (chart {chart_id}, generation {generation})")
    convention_id, vector, fact_ids, dasha_ids, av, stored_l1, stored_dd, stored_input = row
    vec_json = vector if isinstance(vector, str) else _json.dumps(vector)
    live_l1 = conn.execute(
        "SELECT public.ka_gochara_search_l1_facts_digest(%s::uuid, %s::text[])",
        (chart_id, list(fact_ids))).fetchone()[0]
    live_dd = conn.execute(
        "SELECT public.ka_gochara_search_dasha_digest(%s::uuid, %s::uuid[])",
        (chart_id, [str(d) for d in dasha_ids])).fetchone()[0]
    live_input = conn.execute(
        "SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])",
        (convention_id, vec_json, live_l1, live_dd, list(av))).fetchone()[0]
    sealed = bool(conn.execute(
        "SELECT EXISTS (SELECT 1 FROM public.ka_gochara_generation_seal"
        " WHERE chart_id = %s AND generation = %s)", (chart_id, generation)).fetchone()[0])
    components = {
        "l1_facts": {"stored": stored_l1, "live": live_l1, "same": live_l1 == stored_l1},
        "dasha": {"stored": stored_dd, "live": live_dd, "same": live_dd == stored_dd},
        "input": {"stored": stored_input, "live": live_input, "same": live_input == stored_input},
    }
    return {
        "chart_id": str(chart_id),
        "generation": generation,
        "sealed": sealed,
        "components": components,
        "drifted_components": sorted(k for k, v in components.items() if not v["same"]),
        "drifted": any(not v["same"] for v in components.values()),
    }


__all__ = ["SnapshotMissingError", "sealed_generation_staleness"]
