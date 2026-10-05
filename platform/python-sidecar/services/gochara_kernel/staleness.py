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

    hz = conn.execute("SELECT horizon::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    horizon = (tuple(hz.values())[0] if isinstance(hz, dict) else hz[0]) if hz is not None else None
    if horizon is None:
        return _legacy_staleness(conn, chart_id, generation)         # no bound manifest to take the live population's horizon from

    # EVERY digest is computed INSIDE PostgreSQL over the exact text of the stored copy and of the live population: no Python round trip, so a numeric
    # change that a float cannot carry (12.5 versus 12.5000000000000001) is never erased (Codex round 1, finding 4)
    digests = conn.execute(
        "WITH lf AS (SELECT public.ka_gochara_search_facts_live_population(%s::uuid, %s::jsonb) AS j),"
        "     ld AS (SELECT public.ka_gochara_search_dasha_live_population(%s::uuid, %s::jsonb, %s::tstzrange) AS j)"
        " SELECT public.ka_gochara_search_copy_digest(lf.j, 'content'), public.ka_gochara_search_copy_digest(ld.j, 'content'),"
        "        public.ka_gochara_search_copy_digest(lf.j, 'metadata'), public.ka_gochara_search_copy_digest(ld.j, 'metadata') FROM lf, ld",
        (chart_id, facts_text, chart_id, dashas_text, horizon)).fetchone()
    live_l1, live_dd, live_l1m, live_ddm = tuple(digests.values()) if isinstance(digests, dict) else tuple(digests)
    live_input = conn.execute("SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])",
                              (convention_id, vec_json, live_l1, live_dd, list(av))).fetchone()[0]
    sealed = bool(conn.execute("SELECT EXISTS (SELECT 1 FROM public.ka_gochara_generation_seal WHERE chart_id = %s AND generation = %s)",
                               (chart_id, generation)).fetchone()[0])
    components = {
        "l1_facts": {"stored": stored_l1, "live": live_l1, "same": live_l1 == stored_l1, "kind": "hard"},
        "dasha": {"stored": stored_dd, "live": live_dd, "same": live_dd == stored_dd, "kind": "hard"},
        "input": {"stored": stored_input, "live": live_input, "same": live_input == stored_input, "kind": "hard"},
        "l1_metadata": {"stored": stored_l1m, "live": live_l1m, "same": live_l1m == stored_l1m, "kind": "soft"},
        "dasha_metadata": {"stored": stored_ddm, "live": live_ddm, "same": live_ddm == stored_ddm, "kind": "soft"},
    }
    hard = sorted(k for k, v in components.items() if v["kind"] == "hard" and not v["same"])
    soft = sorted(k for k, v in components.items() if v["kind"] == "soft" and not v["same"])
    changes, total = ([], 0)
    if hard or soft:
        live_facts = conn.execute("SELECT public.ka_gochara_search_facts_live_population(%s::uuid, %s::jsonb)::text", (chart_id, facts_text)).fetchone()[0]
        live_dashas = conn.execute("SELECT public.ka_gochara_search_dasha_live_population(%s::uuid, %s::jsonb, %s::tstzrange)::text", (chart_id, dashas_text, horizon)).fetchone()[0]
        changes, total = _changes(facts_text, dashas_text, live_facts, live_dashas)
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
        "changes": changes,
        "changes_total": total,
        "changes_truncated": total > len(changes),
    }


_HARD_ORDER = {"missing_live": 0, "moved": 0, "content_differs": 0, "extra_live": 0, "metadata_only": 1}


def _changes(facts_text: str, dashas_text: str, live_facts: str, live_dashas: str, limit: int = 40) -> tuple[list[dict[str, Any]], int]:
    """What differs, by name: HARD changes first (a value changed, a row missing or moved, an EXTRA live row), metadata-only changes last; at most `limit`
    are returned and the TOTAL is disclosed so a truncation is never silent. Numerics are compared EXACTLY (Decimal). A daśā row missing at its stored
    start is named MOVED when a live period has the stored ORDINAL path (the index of the period within its parent at every level: cycle-specific, so a
    repeated lord is never mistaken for it), with the start shift in seconds."""
    from datetime import datetime
    from decimal import Decimal
    def parse(t: str) -> list[dict[str, Any]]:
        return _json.loads(t, parse_float=Decimal)
    out: list[dict[str, Any]] = []
    for kind, stored_text, live_text in (("fact", facts_text, live_facts), ("dasha", dashas_text, live_dashas)):
        stored = {_json.dumps(e["key"], sort_keys=True, default=str): e for e in parse(stored_text)}
        live_list = parse(live_text)
        live: dict[str, list[dict[str, Any]]] = {}
        for e in live_list:
            live.setdefault(_json.dumps(e["key"], sort_keys=True, default=str), []).append(e)
        for key, e in sorted(stored.items()):
            hits = live.get(key, [])
            if not hits or hits[0].get("content") is None:
                change: dict[str, Any] = {"kind": kind, "key": e["key"], "change": "missing_live"}
                if kind == "dasha":
                    ordinal = (e.get("content") or {}).get("ordinal_path")
                    cand = [x for xs in live.values() for x in xs
                            if ordinal and (x.get("content") or {}).get("ordinal_path") == ordinal
                            and x["key"]["level_n"] == e["key"]["level_n"] and x["key"]["system_id"] == e["key"]["system_id"]
                            and x["key"]["ayanamsha_id"] == e["key"]["ayanamsha_id"]]
                    if cand:
                        c = cand[0]
                        shift = (datetime.fromisoformat(c["key"]["start_iso"]) - datetime.fromisoformat(e["key"]["start_iso"])).total_seconds()
                        change.update({"change": "moved", "ordinal_path": ordinal, "lord_path": e["content"].get("lord_path"),
                                       "live_start": c["key"]["start_iso"], "start_shift_seconds": shift})
                out.append(change)
            elif len(hits) > 1:
                out.append({"kind": kind, "key": e["key"], "change": "extra_live", "detail": f"{len(hits)} live rows share this key (a conflicting duplicate)"})
            elif hits[0]["content"] != e["content"]:
                out.append({"kind": kind, "key": e["key"], "change": "content_differs",
                            "fields": sorted(k for k in set(e["content"]) | set(hits[0]["content"]) if e["content"].get(k) != hits[0]["content"].get(k))})
            elif hits[0]["metadata"] != e["metadata"]:
                out.append({"kind": kind, "key": e["key"], "change": "metadata_only",
                            "fields": sorted(k for k in set(e["metadata"]) | set(hits[0]["metadata"]) if e["metadata"].get(k) != hits[0]["metadata"].get(k))})
        moved_keys = {_json.dumps(c["key"], sort_keys=True, default=str) for c in out if c["kind"] == kind and c["change"] == "moved"}
        live_by_start = {c.get("live_start") for c in out if c["kind"] == kind and c["change"] == "moved"}
        for key, xs in sorted(live.items()):
            if key not in stored and not any(x["key"]["start_iso"] in live_by_start for x in xs):
                out.append({"kind": kind, "key": xs[0]["key"], "change": "extra_live"})
    out.sort(key=lambda c: (_HARD_ORDER[c["change"]], c["kind"], _json.dumps(c["key"], sort_keys=True, default=str)))
    return out[:limit], len(out)


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
        "changes_total": 0,
        "changes_truncated": False,
    }


__all__ = ["SnapshotMissingError", "sealed_generation_staleness"]
