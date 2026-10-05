"""AM-5 search-inventory persistence over migration 1206 (PR #2867 — shapes NOT frozen
until the Codex verdict; this module is the single place that knows them).

Lock protocol (draft §AM-5 item 7): every transaction here takes the chart family key
FIRST (`ka_gochara_lock_chart`, done by the caller exactly like every chart-serving
substep), then `ka_gochara_lock_global_shared()` before reading any rule seal. Nothing here
commits, rolls back or closes the connection (FROZEN orchestrator contract).

Digests are NOT computed in Python here: the builder asks the DATABASE's own functions
(`ka_gochara_search_*_digest`) and the finalisation UPDATE is refused unless they equal the
recomputation — so the builder cannot disagree with the seal check. The independent
verifier (inventory_verifier.py) is the code that derives the same digest WITHOUT these
functions.

Replacement (AM-3 / AM-5 item 8): a candidate rebuild deletes the dependent chain in FK
order — verification → intervals → obligations → pins → header [→ snapshot] — then inserts
afresh. A SEALED generation is refused up front (the DB refuses too).
"""
from __future__ import annotations

import json as _json
from datetime import datetime
from typing import Any, Sequence

from .inventory import ClassInventory, DashaRow
from .record_store import SealedGenerationError

# The builder deletes ONLY the tables it owns. The verification row
# (ka_gochara_search_inventory_verification) is the verifier's: the builder holds NO privilege
# on it (1206 §7, ND-ROLES option A), so listing it here would fail 'permission denied' at the
# replace-prelude. A rebuild still invalidates a stale verification — the FK to the header is
# ON DELETE CASCADE (PC-4 e4d31c9ef), so deleting the header removes it.
_CLASS_TABLES_DELETE_ORDER = (
    "ka_gochara_search_interval",
    "ka_gochara_search_obligation",
    "ka_gochara_search_path_pin",
    "ka_gochara_search_inventory",
)


class SnapshotUnboundError(RuntimeError):
    """The generation has no manifest row, so the snapshot's input vector has nothing to
    be bound to (AM-5 item 0b) — the `manifest` substep must run first."""


def _range(lo: datetime, hi: datetime) -> str:
    return f"[{lo.isoformat()},{hi.isoformat()})"


class InventoryStore:
    def __init__(self, conn: Any):
        self.conn = conn

    # ── locks, seal, registry ────────────────────────────────────────────

    def lock_global_shared(self) -> None:
        self.conn.execute("SELECT public.ka_gochara_lock_global_shared()")

    def _refuse_if_sealed(self, chart_id: str, generation: str, what: str) -> None:
        row = self.conn.execute(
            "SELECT public.ka_gochara_generation_is_sealed(%s::uuid, %s)",
            (chart_id, generation)).fetchone()
        if row and row[0]:
            raise SealedGenerationError(
                f"{what}: (chart {chart_id}, generation {generation}) is SEALED — a changed "
                "search is a new generation")

    def sealed_rule_paths(self) -> list[tuple[str, str]]:
        """The registry's sealed (path_id, rule_version) set — read under the global
        SHARED key so it cannot change under this transaction (1154:479–490)."""
        self.lock_global_shared()
        rows = self.conn.execute(
            "SELECT path_id, rule_version FROM public.ka_gochara_rule_path_seal"
            " ORDER BY path_id, rule_version").fetchall()
        return [(r[0], r[1]) for r in rows]

    def manifest_vector(self, chart_id: str, generation: str) -> dict | None:
        row = self.conn.execute(
            "SELECT input_generation_vector FROM public.kala_gochara_publication"
            " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
        if row is None:
            return None
        v = row[0]
        return v if isinstance(v, dict) else _json.loads(v)

    # ── replacement ──────────────────────────────────────────────────────

    def delete_class_inventory(self, chart_id: str, generation: str,
                               event_class: str) -> dict[str, int]:
        self._refuse_if_sealed(chart_id, generation, f"inventory {event_class}")
        out = {}
        for table in _CLASS_TABLES_DELETE_ORDER:
            out[table] = self.conn.execute(
                f"DELETE FROM public.{table} WHERE chart_id = %s AND generation = %s"
                " AND event_class = %s", (chart_id, generation, event_class)).rowcount
        return out

    def delete_generation_inventory(self, chart_id: str, generation: str) -> dict[str, int]:
        """Every class's chain, then the snapshot (a changed snapshot is a different
        generation, or a dependency-ordered delete of every dependent row — item 0d)."""
        self._refuse_if_sealed(chart_id, generation, "search inventory")
        out = {}
        for table in _CLASS_TABLES_DELETE_ORDER:
            out[table] = self.conn.execute(
                f"DELETE FROM public.{table} WHERE chart_id = %s AND generation = %s",
                (chart_id, generation)).rowcount
        out["ka_gochara_search_input_snapshot"] = self.conn.execute(
            "DELETE FROM public.ka_gochara_search_input_snapshot"
            " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).rowcount
        return out

    # ── snapshot (item 0) ────────────────────────────────────────────────

    def snapshot_copy_available(self) -> bool:
        """Does the APPLIED schema give the snapshot a COPY of what it consumed (migration 1305, G12 route 1)? Read, never assumed: without it the
        snapshot is the LEGACY shape (ids and whole-row digests) and is NOT self-contained — it dangles after any later L1 rebuild — which the
        build notes name and the seal path refuses."""
        row = self.conn.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public'"
            " AND table_name = 'ka_gochara_search_input_snapshot'"
            " AND column_name IN ('consumed_fact_rows', 'consumed_dasha_rows', 'l1_facts_metadata_digest', 'dasha_metadata_digest')").fetchone()
        return int(row[0]) == 4

    def insert_snapshot(self, *, chart_id: str, generation: str, convention_id: str,
                        consumed_fact_ids: Sequence[str],
                        consumed_dasha_row_ids: Sequence[str],
                        av_declaration_keys: Sequence[str] = ()) -> str:
        """The ONE immutable input identity of the generation. Its vector is the
        manifest's (read, never invented); the digests come from the database's own
        functions over the live rows; the insert trigger recomputes `input_digest`.

        With migration 1305 the snapshot stores a COPY of the consumed L1 rows (`consumed_fact_rows`, `consumed_dasha_rows`: {key, content,
        metadata}) and `l1_facts_digest` / `dasha_digest` are the IDENTITY digests of that copy (content columns only), so the generation
        stays self-contained and verifiable after any later L1 rebuild; the ids stay as provenance. Without it, the legacy shape is written."""
        vector = self.manifest_vector(chart_id, generation)
        if vector is None:
            raise SnapshotUnboundError(
                f"no kala_gochara_publication manifest for (chart {chart_id}, generation "
                f"{generation}): run the manifest substep before the snapshot")
        facts = sorted(set(map(str, consumed_fact_ids)))
        dashas = sorted(set(map(str, consumed_dasha_row_ids)))
        av = sorted(self.conn.execute(
            "SELECT public.ka_gochara_search_av_entry(k) FROM unnest(%s::text[]) k",
            (list(av_declaration_keys),)).fetchall()) if av_declaration_keys else []
        av = [r[0] for r in av]
        vec_json = _json.dumps(vector)
        if self.snapshot_copy_available():
            facts_copy = _json.dumps(self.conn.execute(
                "SELECT public.ka_gochara_search_facts_copy(%s::uuid, %s::text[], true)", (chart_id, facts)).fetchone()[0])
            dashas_copy = _json.dumps(self.conn.execute(
                "SELECT public.ka_gochara_search_dasha_copy(%s::uuid, %s::uuid[])", (chart_id, dashas)).fetchone()[0])

            def _digest(copy: str, block: str) -> str:
                return self.conn.execute("SELECT public.ka_gochara_search_copy_digest(%s::jsonb, %s)", (copy, block)).fetchone()[0]
            l1, dd = _digest(facts_copy, "content"), _digest(dashas_copy, "content")
            l1m, ddm = _digest(facts_copy, "metadata"), _digest(dashas_copy, "metadata")
            digest = self.conn.execute(
                "SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])",
                (convention_id, vec_json, l1, dd, av)).fetchone()[0]
            self.conn.execute(
                "INSERT INTO public.ka_gochara_search_input_snapshot"
                " (chart_id, generation, convention_id, input_generation_vector,"
                "  consumed_fact_ids, consumed_dasha_row_ids, av_declarations,"
                "  l1_facts_digest, dasha_digest, input_digest,"
                "  consumed_fact_rows, consumed_dasha_rows, l1_facts_metadata_digest, dasha_metadata_digest)"
                " VALUES (%s,%s,%s,%s::jsonb,%s,%s::uuid[],%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s)",
                (chart_id, generation, convention_id, vec_json, facts, dashas, av, l1, dd, digest,
                 facts_copy, dashas_copy, l1m, ddm))
            return digest
        # LEGACY shape (no migration 1305): 1206's live-input digests keyed by (chart, id)
        l1 = self.conn.execute(
            "SELECT public.ka_gochara_search_l1_facts_digest(%s::uuid, %s::text[])",
            (chart_id, facts)).fetchone()[0]
        dd = self.conn.execute(
            "SELECT public.ka_gochara_search_dasha_digest(%s::uuid, %s::uuid[])",
            (chart_id, dashas)).fetchone()[0]
        digest = self.conn.execute(
            "SELECT public.ka_gochara_search_input_digest(%s, %s::jsonb, %s, %s, %s::text[])",
            (convention_id, vec_json, l1, dd, av)).fetchone()[0]
        self.conn.execute(
            "INSERT INTO public.ka_gochara_search_input_snapshot"
            " (chart_id, generation, convention_id, input_generation_vector,"
            "  consumed_fact_ids, consumed_dasha_row_ids, av_declarations,"
            "  l1_facts_digest, dasha_digest, input_digest)"
            " VALUES (%s,%s,%s,%s::jsonb,%s,%s::uuid[],%s,%s,%s,%s)",
            (chart_id, generation, convention_id, vec_json, facts, dashas, av, l1, dd, digest))
        return digest

    def consumed_dasha_rows(self, chart_id: str, generation: str) -> list[DashaRow]:
        """The pinned daśā rows the snapshot CONSUMED (the inventory is cut at exactly the rows the snapshot's digest covers, never a fresh read).
        With 1305 they come from the snapshot's own COPY (so they exist after any later L1 rebuild); a legacy snapshot is read by id."""
        copy = None
        if self.snapshot_copy_available():
            r = self.conn.execute(
                "SELECT consumed_dasha_rows FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s",
                (chart_id, generation)).fetchone()
            copy = r[0] if r else None
        if copy is not None:
            from datetime import timezone as _tz
            rows = sorted(copy, key=lambda e: (int(e["key"]["level_n"]), e["key"]["start_iso"]))
            return [DashaRow(str(e["metadata"]["dasha_row_id"]), int(e["key"]["level_n"]), str(e["content"]["lord_graha"]).lower(),
                             datetime.fromisoformat(e["key"]["start_iso"]).astimezone(_tz.utc),
                             datetime.fromisoformat(e["content"]["end_iso"]).astimezone(_tz.utc)) for e in rows]
        rows = self.conn.execute(
            "SELECT d.dasha_row_id::text, d.level_n, d.lord_graha, d.start_iso, d.end_iso"
            " FROM public.chart_dashas d"
            " JOIN public.ka_gochara_search_input_snapshot s"
            "   ON d.chart_id = s.chart_id AND d.dasha_row_id = ANY (s.consumed_dasha_row_ids)"
            " WHERE s.chart_id = %s AND s.generation = %s ORDER BY d.level_n, d.start_iso",
            (chart_id, generation)).fetchall()
        return [DashaRow(r[0], int(r[1]), str(r[2]).lower(), r[3], r[4]) for r in rows]

    def moon_scope_available(self) -> bool:
        """Does the APPLIED schema account a Moon-resolved period-role interval (1232)? The state is
        in `kgsiv_state_ck` AND the derived-domain function exists. Read, never assumed."""
        row = self.conn.execute(
            "SELECT to_regprocedure('public.ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)')"
            " IS NOT NULL AND EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = 'kgsiv_state_ck'"
            " AND c.conrelid = 'public.ka_gochara_search_interval'::regclass"
            " AND pg_get_constraintdef(c.oid) LIKE '%excluded_moon_tier%')").fetchone()
        return bool(row[0])

    def snapshot_input_digest(self, chart_id: str, generation: str) -> str | None:
        row = self.conn.execute(
            "SELECT input_digest FROM public.ka_gochara_search_input_snapshot"
            " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
        return row[0] if row else None

    # ── one class's chain ────────────────────────────────────────────────

    def write_class_inventory(self, *, chart_id: str, generation: str,
                              plan: ClassInventory, input_digest: str) -> dict[str, Any]:
        """Replace the class's chain, insert header → pins → obligations → intervals,
        then the one-shot FINALISATION (digests from the DB's functions — equal to the
        seal's recomputation by construction). Returns the finalised digests."""
        self.delete_class_inventory(chart_id, generation, plan.event_class)
        self.lock_global_shared()     # pins/obligations read the rule seal (chart → global SHARED)
        cls = plan.event_class
        self.conn.execute(
            "INSERT INTO public.ka_gochara_search_inventory"
            " (chart_id, generation, event_class, horizon, input_digest)"
            " VALUES (%s,%s,%s,%s::tstzrange,%s)",
            (chart_id, generation, cls, _range(*plan.horizon), input_digest))
        for pin in plan.pins:
            self.conn.execute(
                "INSERT INTO public.ka_gochara_search_path_pin"
                " (chart_id, generation, event_class, path_id, rule_version, disposition,"
                "  exclusion_reason, ruling_ref, basis, committed_ob_ids)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::uuid[])",
                (chart_id, generation, cls, pin.path_id, pin.rule_version, pin.disposition,
                 pin.exclusion_reason, pin.ruling_ref, pin.basis,
                 [str(i) for i in pin.committed_ob_ids]))
            for o in pin.obligations:
                self.conn.execute(
                    "INSERT INTO public.ka_gochara_search_obligation"
                    " (chart_id, generation, event_class, ob_id, path_id, rule_version,"
                    "  agent, relation, object_role, target, frame, person, canonical_bytes)"
                    " VALUES (%s,%s,%s,%s::uuid,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (chart_id, generation, cls, str(o.ob_id), o.path_id, o.rule_version,
                     o.agent, o.relation, o.object_role, o.target, o.frame, o.person,
                     o.canonical_bytes))
        for iv in plan.intervals:
            self.conn.execute(
                "INSERT INTO public.ka_gochara_search_interval"
                " (chart_id, generation, event_class, ob_id, search_range, state, detail,"
                "  input_digest)"
                " VALUES (%s,%s,%s,%s::uuid,%s::tstzrange,%s,%s::jsonb,%s)",
                (chart_id, generation, cls, str(iv.ob_id), _range(iv.start, iv.end),
                 iv.state, None if iv.detail is None else _json.dumps(iv.detail),
                 input_digest))
        inv, led = self.conn.execute(
            "SELECT public.ka_gochara_search_inventory_digest(%s::uuid,%s,%s),"
            "       public.ka_gochara_search_ledger_digest(%s::uuid,%s,%s)",
            (chart_id, generation, cls, chart_id, generation, cls)).fetchone()
        self.conn.execute(
            "UPDATE public.ka_gochara_search_inventory SET inventory_digest = %s,"
            " ledger_digest = %s, finalized_at = now()"
            " WHERE chart_id = %s AND generation = %s AND event_class = %s",
            (inv, led, chart_id, generation, cls))
        return {"inventory_digest": inv, "ledger_digest": led,
                "obligations": len(plan.obligations),
                "pins": len(plan.pins), "intervals": len(plan.intervals)}

    def finalised_class_facts(self, chart_id: str, generation: str,
                              event_class: str) -> dict[str, Any] | None:
        """What the class's coverage partition must equal (partition_overclaims):
        the inventory horizon and the obligations' distinct relations."""
        row = self.conn.execute(
            "SELECT lower(horizon), upper(horizon), inventory_digest"
            " FROM public.ka_gochara_search_inventory"
            " WHERE chart_id = %s AND generation = %s AND event_class = %s",
            (chart_id, generation, event_class)).fetchone()
        if row is None:
            return None
        rels = [r[0] for r in self.conn.execute(
            "SELECT DISTINCT relation FROM public.ka_gochara_search_obligation"
            " WHERE chart_id = %s AND generation = %s AND event_class = %s ORDER BY 1",
            (chart_id, generation, event_class)).fetchall()]
        counts = self.conn.execute(
            "SELECT count(*),"
            " count(*) FILTER (WHERE EXISTS (SELECT 1 FROM public.ka_gochara_search_interval v"
            "   WHERE (v.chart_id,v.generation,v.event_class,v.ob_id) ="
            "         (o.chart_id,o.generation,o.event_class,o.ob_id)"
            "     AND v.state = 'missing_inputs'))"
            " FROM public.ka_gochara_search_obligation o"
            " WHERE o.chart_id = %s AND o.generation = %s AND o.event_class = %s",
            (chart_id, generation, event_class)).fetchone()
        moon = self.conn.execute(
            "SELECT count(*) FROM public.ka_gochara_search_interval v WHERE v.chart_id = %s"
            " AND v.generation = %s AND v.event_class = %s AND v.state = 'excluded_moon_tier'",
            (chart_id, generation, event_class)).fetchone()[0]
        return {"horizon": (row[0], row[1]), "inventory_digest": row[2],
                "relations": rels, "obligations": counts[0], "missing_inputs": counts[1],
                "moon_excluded_intervals": moon}


__all__ = ["InventoryStore", "SnapshotUnboundError"]
