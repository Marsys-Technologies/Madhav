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


def _has_copy_columns(conn: Any) -> bool:
    n = conn.execute(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'"
        " AND column_name IN ('consumed_fact_rows', 'consumed_dasha_rows', 'l1_facts_metadata_digest', 'dasha_metadata_digest')").fetchone()
    return int(n[0]) == 4


def sealed_generation_staleness(conn: Any, chart_id: str, generation: str) -> dict[str, Any]:
    """Per-component drift of the snapshot against LIVE L1, with two KINDS (G12 route 1, migration 1305):

      HARD  (`l1_facts`, `dasha`, `input`): the IDENTITY digest of the live rows, found by their natural key, differs from the stored one — a VALUE
            changed or a consumed row is gone. `drifted` is true only for these.
      SOFT  (`l1_metadata`, `dasha_metadata`): only ids, build ids, tier, engine version or other metadata differ (an L1 rebuild that re-issued
            them): REPORTED, never blocking, and never a failure to verify the generation, which owns a copy of what it consumed.

    A legacy snapshot (no copy) keeps the 1206 id-and-whole-row check and every component is HARD."""
    if not _has_copy_columns(conn):
        return _legacy_staleness(conn, chart_id, generation)
    row = conn.execute(
        "SELECT convention_id, input_generation_vector, av_declarations, l1_facts_digest, dasha_digest, input_digest,"
        "       l1_facts_metadata_digest, dasha_metadata_digest, consumed_fact_rows::text, consumed_dasha_rows::text"
        " FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if row is None:
        raise SnapshotMissingError(
            f"no ka_gochara_search_input_snapshot for (chart {chart_id}, generation {generation})")
    (convention_id, vector, av, stored_l1, stored_dd, stored_input, stored_l1m, stored_ddm, facts_text, dashas_text) = tuple(
        row.values()) if isinstance(row, dict) else tuple(row)
    if facts_text is None or dashas_text is None:
        return _legacy_staleness(conn, chart_id, generation)         # a snapshot written before 1305
    vec_json = vector if isinstance(vector, str) else _json.dumps(vector)

    def one(sql: str, *params: Any) -> Any:
        return conn.execute(sql, params).fetchone()[0]
    live_facts = _json.dumps(one("SELECT public.ka_gochara_search_facts_live_copy(%s::uuid, %s::jsonb)", chart_id, facts_text))
    live_dashas = _json.dumps(one("SELECT public.ka_gochara_search_dasha_live_copy(%s::uuid, %s::jsonb)", chart_id, dashas_text))

    def digest(copy: str, block: str) -> str:
        return one("SELECT public.ka_gochara_search_copy_digest(%s::jsonb, %s)", copy, block)
    live_l1, live_dd = digest(live_facts, "content"), digest(live_dashas, "content")
    live_l1m, live_ddm = digest(live_facts, "metadata"), digest(live_dashas, "metadata")
    live_input = one("SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])",
                     convention_id, vec_json, live_l1, live_dd, list(av))
    sealed = bool(one("SELECT EXISTS (SELECT 1 FROM public.ka_gochara_generation_seal WHERE chart_id = %s AND generation = %s)",
                      chart_id, generation))
    components = {
        "l1_facts": {"stored": stored_l1, "live": live_l1, "same": live_l1 == stored_l1, "kind": "hard"},
        "dasha": {"stored": stored_dd, "live": live_dd, "same": live_dd == stored_dd, "kind": "hard"},
        "input": {"stored": stored_input, "live": live_input, "same": live_input == stored_input, "kind": "hard"},
        "l1_metadata": {"stored": stored_l1m, "live": live_l1m, "same": live_l1m == stored_l1m, "kind": "soft"},
        "dasha_metadata": {"stored": stored_ddm, "live": live_ddm, "same": live_ddm == stored_ddm, "kind": "soft"},
    }
    hard = sorted(k for k, v in components.items() if v["kind"] == "hard" and not v["same"])
    soft = sorted(k for k, v in components.items() if v["kind"] == "soft" and not v["same"])
    return {
        "chart_id": str(chart_id),
        "generation": generation,
        "sealed": sealed,
        "self_contained": True,
        "components": components,
        "drifted_components": hard,
        "drifted": bool(hard),
        "metadata_drift_components": soft,
        "metadata_only_drift": bool(soft) and not hard,
        "changes": _changes(conn, chart_id, facts_text, dashas_text, live_facts, live_dashas) if (hard or soft) else [],
    }


def _changes(conn: Any, chart_id: str, facts_text: str, dashas_text: str, live_facts: str, live_dashas: str, limit: int = 40) -> list[dict[str, Any]]:
    """What differs, by name (at most `limit`): a fact or daśā row whose content changed or is missing live; for a daśā row missing at its stored start, the
    live period with the same ordinal lord path, if there is one, is named as MOVED with the shift in seconds — never just 'row missing'."""
    out: list[dict[str, Any]] = []
    for kind, stored_text, live_text in (("fact", facts_text, live_facts), ("dasha", dashas_text, live_dashas)):
        stored = {_json.dumps(e["key"], sort_keys=True): e for e in _json.loads(stored_text)}
        live = {_json.dumps(e["key"], sort_keys=True): e for e in _json.loads(live_text)}
        for key, e in sorted(stored.items()):
            lv = live.get(key)
            if lv is None or lv.get("content") is None:
                change: dict[str, Any] = {"kind": kind, "key": e["key"], "change": "missing_live"}
                if kind == "dasha":
                    moved = _moved(conn, chart_id, e)
                    if moved:
                        change.update(moved)
                out.append(change)
            elif lv["content"] != e["content"]:
                out.append({"kind": kind, "key": e["key"], "change": "content_differs",
                            "fields": sorted(k for k in set(e["content"]) | set(lv["content"]) if e["content"].get(k) != lv["content"].get(k))})
            elif lv["metadata"] != e["metadata"]:
                out.append({"kind": kind, "key": e["key"], "change": "metadata_only",
                            "fields": sorted(k for k in set(e["metadata"]) | set(lv["metadata"]) if e["metadata"].get(k) != lv["metadata"].get(k))})
            if len(out) >= limit:
                return out
    return out


def _moved(conn: Any, chart_id: str, element: dict[str, Any]) -> dict[str, Any] | None:
    """The live period with the stored ORDINAL lord path (same level, system, ayanamsha), if any: the boundary moved, the period did not vanish."""
    k, path = element["key"], element["content"].get("lord_path")
    if not path:
        return None
    rows = conn.execute(
        "SELECT d.start_iso, d.end_iso, public.ka_gochara_search_dasha_path(d.chart_id, d.dasha_row_id)"
        " FROM public.chart_dashas d WHERE d.chart_id = %s AND d.ayanamsha_id = %s AND d.system_id = %s AND d.level_n = %s",
        (chart_id, k["ayanamsha_id"], k["system_id"], int(k["level_n"]))).fetchall()
    from datetime import datetime
    stored_start = datetime.fromisoformat(k["start_iso"])
    best = [(abs((r[0] - stored_start).total_seconds()), r) for r in rows if r[2] == path]
    if not best:
        return None
    delta, r = min(best, key=lambda x: x[0])
    return {"change": "moved", "lord_path": path, "live_start": r[0].isoformat(), "live_end": r[1].isoformat(),
            "start_shift_seconds": (r[0] - stored_start).total_seconds()}


def _legacy_staleness(conn: Any, chart_id: str, generation: str) -> dict[str, Any]:
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
        "l1_facts": {"stored": stored_l1, "live": live_l1, "same": live_l1 == stored_l1, "kind": "hard"},
        "dasha": {"stored": stored_dd, "live": live_dd, "same": live_dd == stored_dd, "kind": "hard"},
        "input": {"stored": stored_input, "live": live_input, "same": live_input == stored_input, "kind": "hard"},
    }
    return {
        "chart_id": str(chart_id),
        "generation": generation,
        "sealed": sealed,
        "self_contained": False,
        "components": components,
        "drifted_components": sorted(k for k, v in components.items() if not v["same"]),
        "drifted": any(not v["same"] for v in components.values()),
        "metadata_drift_components": [],
        "metadata_only_drift": False,
        "changes": [],
    }


__all__ = ["SnapshotMissingError", "sealed_generation_staleness"]
