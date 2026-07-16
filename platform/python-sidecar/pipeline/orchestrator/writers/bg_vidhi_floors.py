"""
bg_vidhi_floors writer — D-2 Lane V-1 (Vidhi registry + compiler).

Populates `vidhi_intent_floors` + `vidhi_floor_items` (migration 440) with the
per-intent-class acharya floor + machine band. Content mirrors
`platform/src/lib/vidhi/registry_data.ts` (VIDHI_INTENT_FLOORS) — see that
file's header for the sync note.

floor(wealth_deepdive) matches DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3's worked
example verbatim for its 14 named atoms, and is extended (items 15+) to satisfy
every §B0.4 mandatory-surface tag and all four CR-27 improvisation instances
plus the CR-36 buried-evidence specimen from a single floor.

Depends on bg_vidhi_primitives (FK: vidhi_floor_items.primitive_id).

§N.3: L0 idempotency — delete-then-insert per intent (global table, but floor
CONTENT is versioned/replaced wholesale per intent rather than upserted
row-by-row, since item_order re-numbering on a floor edit would otherwise
leave orphaned rows under the old numbering).
§N.2: Frozen orchestrator contract — run(ctx) → WriterResult, never commits.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult

logger = logging.getLogger(__name__)

# Each floor: (intent, version, cr27_coverage, notes, items)
# Each item: (primitive_id, order, band, args_override)

WEALTH_DEEPDIVE_ITEMS = [
    ("bhava_condition", 1, "acharya_floor", {"house": 2}),
    ("bhavesha_condition", 2, "acharya_floor", {"house": 2}),
    ("karaka_condition", 3, "acharya_floor", {"karaka": "jupiter"}),
    ("from_moon_view", 4, "acharya_floor", {}),
    ("chalit_cusp_read", 5, "acharya_floor", {}),
    ("bhava_bala_scan", 6, "acharya_floor", {}),
    ("ashtakavarga_scan", 7, "acharya_floor", {}),
    ("sensitive_degree_check", 8, "acharya_floor", {}),
    ("divisional_facts", 9, "acharya_floor", {"varga": "D2"}),
    ("varga_ratification", 10, "acharya_floor", {"vargas": ["D2", "D9", "D11"]}),
    ("karakamsa_read", 11, "acharya_floor", {}),
    ("kp_cusp_sublord_read", 12, "acharya_floor", {}),
    ("special_lagna_read", 13, "acharya_floor", {"lagnas": ["indu", "sree"]}),
    ("chara_karaka_read", 14, "acharya_floor", {"chara_karaka": "AmK"}),
    ("dhana_yoga_scan", 15, "acharya_floor", {"domain": "wealth"}),
    ("nbry_scan", 16, "acharya_floor", {}),
    ("wealth_loss_mechanism_scan", 17, "acharya_floor", {"domain": "wealth"}),
    ("sudarshana_agreement_check", 18, "acharya_floor", {}),
    ("bhavat_bhavam_check", 19, "acharya_floor", {}),
    ("nakshatra_semantics", 20, "acharya_floor", {}),
    ("mechanism_read", 21, "acharya_floor", {}),
    ("dasha_spine_lord_capability", 22, "machine_band", {}),
    ("taranga_curve", 23, "machine_band", {"domain": "wealth"}),
    ("lel_retrodiction", 24, "machine_band", {"domain": "wealth"}),
    ("statistical_context", 25, "machine_band", {}),
    ("intervention_synthesis", 26, "machine_band", {}),
]

CAREER_DEEPDIVE_ITEMS = [
    ("bhava_condition", 1, "acharya_floor", {"house": 10}),
    ("bhavesha_condition", 2, "acharya_floor", {"house": 10}),
    ("karaka_condition", 3, "acharya_floor", {"karaka": "sun"}),
    ("divisional_facts", 4, "acharya_floor", {"varga": "D10"}),
    ("divisional_facts", 5, "acharya_floor", {"varga": "D9"}),
    ("varga_ratification", 6, "acharya_floor", {"vargas": ["D1", "D9", "D10"]}),
    ("dhana_yoga_scan", 7, "acharya_floor", {"domain": "career", "family": "raja"}),
    ("nakshatra_semantics", 8, "acharya_floor", {}),
    ("mechanism_read", 9, "acharya_floor", {}),
    ("dasha_spine_lord_capability", 10, "machine_band", {}),
    ("taranga_curve", 11, "machine_band", {"domain": "career"}),
    ("intervention_synthesis", 12, "machine_band", {}),
]

HEALTH_DEEPDIVE_ITEMS = [
    ("bhava_condition", 1, "acharya_floor", {"house": 6}),
    ("bhavesha_condition", 2, "acharya_floor", {"house": 6}),
    ("karaka_condition", 3, "acharya_floor", {"karaka": "mars"}),
    ("dignity_scan", 4, "acharya_floor", {}),
    ("sensitive_degree_check", 5, "acharya_floor", {}),
    ("divisional_facts", 6, "acharya_floor", {"varga": "D6"}),
    ("dosha_scan", 7, "acharya_floor", {}),
    ("dasha_spine_lord_capability", 8, "machine_band", {}),
    ("taranga_curve", 9, "machine_band", {"domain": "health"}),
    ("remedy_scan", 10, "machine_band", {"domain": "health"}),
]

MARRIAGE_DEEPDIVE_ITEMS = [
    ("bhava_condition", 1, "acharya_floor", {"house": 7}),
    ("bhavesha_condition", 2, "acharya_floor", {"house": 7}),
    ("karaka_condition", 3, "acharya_floor", {"karaka": "venus"}),
    ("divisional_facts", 4, "acharya_floor", {"varga": "D9"}),
    ("varga_ratification", 5, "acharya_floor", {"vargas": ["D1", "D9"]}),
    ("dosha_scan", 6, "acharya_floor", {}),
    ("karakamsa_read", 7, "acharya_floor", {}),
    ("dasha_spine_lord_capability", 8, "machine_band", {}),
    ("remedy_scan", 9, "machine_band", {"domain": "marriage"}),
]

STRUCTURE_READ_ITEMS = [
    ("positions_snapshot", 1, "acharya_floor", {}),
    ("dignity_scan", 2, "acharya_floor", {}),
    ("shadbala_rank", 3, "acharya_floor", {}),
    ("chalit_cusp_read", 4, "acharya_floor", {}),
    ("bhava_bala_scan", 5, "acharya_floor", {}),
]

PANORAMIC_BREADTH_ITEMS = [
    ("positions_snapshot", 1, "acharya_floor", {}),
    ("shadbala_rank", 2, "acharya_floor", {}),
    ("nakshatra_semantics", 3, "acharya_floor", {}),
    ("arudha_read", 4, "acharya_floor", {}),
    ("mechanism_read", 5, "acharya_floor", {}),
    ("contradiction_scan", 6, "machine_band", {}),
    ("statistical_context", 7, "machine_band", {}),
    ("dasha_spine_lord_capability", 8, "machine_band", {}),
]

RETRIEVAL_ONLY_ITEMS = [
    ("positions_snapshot", 1, "acharya_floor", {}),
]

GENERAL_SYNTHESIS_ITEMS = [
    ("bhava_condition", 1, "acharya_floor", {"house": 1}),
    ("shadbala_rank", 2, "acharya_floor", {}),
    ("mechanism_read", 3, "acharya_floor", {}),
    ("dasha_spine_lord_capability", 4, "machine_band", {}),
    ("contradiction_scan", 5, "machine_band", {}),
    ("intervention_synthesis", 6, "machine_band", {}),
]

FLOORS = [
    ("wealth_deepdive", 1, ["CR-27a", "CR-27b", "CR-27c", "CR-27d", "CR-36"],
     "Flagship floor — worked example per DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3; "
     "§G master acceptance target.",
     WEALTH_DEEPDIVE_ITEMS),
    ("career_deepdive", 1, ["CR-27c", "CR-27d"],
     "D10/D9 multi-varga per CR-62's wealth {D1,D2,D9,D11} / career {D1,D9,D10} map.",
     CAREER_DEEPDIVE_ITEMS),
    ("health_deepdive", 1, ["CR-27b"], None, HEALTH_DEEPDIVE_ITEMS),
    ("marriage_deepdive", 1, ["CR-27b"], None, MARRIAGE_DEEPDIVE_ITEMS),
    ("structure_read", 1, [],
     "Narrow/structure depth — the 'show me my D1' canonical example; no machine band.",
     STRUCTURE_READ_ITEMS),
    ("panoramic_breadth", 1, ["CR-27a", "CR-27c", "CR-27d"],
     "The 'unleash my financial potential'-shaped wide sweep — domain-agnostic breadth.",
     PANORAMIC_BREADTH_ITEMS),
    ("retrieval_only", 1, [], None, RETRIEVAL_ONLY_ITEMS),
    ("general_synthesis", 1, ["CR-27a"], None, GENERAL_SYNTHESIS_ITEMS),
]


@register('bg_vidhi_floors')
class VidhiFloorsWriter(WriterBase):
    asset_id = 'bg_vidhi_floors'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        total_items = sum(len(items) for (*_h, items) in FLOORS)

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=total_items,
                duration_seconds=time.time() - t0,
                notes=f"dry_run — would replace {len(FLOORS)} floors / {total_items} floor_items",
            )

        with ctx.db_conn.cursor() as cur:
            items_written = 0
            for (intent, version, cr27_coverage, notes, items) in FLOORS:
                cur.execute(
                    """
                    INSERT INTO vidhi_intent_floors (intent, version, cr27_coverage, notes, updated_at)
                    VALUES (%s, %s, %s, %s, now())
                    ON CONFLICT (intent) DO UPDATE SET
                        version       = EXCLUDED.version,
                        cr27_coverage = EXCLUDED.cr27_coverage,
                        notes         = EXCLUDED.notes,
                        updated_at    = now()
                    """,
                    (intent, version, cr27_coverage, notes),
                )
                # §N.3 delete-then-insert scoped to this intent's floor_items — a floor
                # edit (re-ordering, adding/removing atoms) never leaves orphaned rows
                # under stale item_order numbering.
                cur.execute("DELETE FROM vidhi_floor_items WHERE intent = %s", (intent,))
                for (primitive_id, order, band, args_override) in items:
                    cur.execute(
                        """
                        INSERT INTO vidhi_floor_items
                          (intent, primitive_id, item_order, band, args_override)
                        VALUES (%s, %s, %s, %s, %s::JSONB)
                        """,
                        (intent, primitive_id, order, band, _to_jsonb(args_override)),
                    )
                    items_written += 1

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=items_written,
            duration_seconds=time.time() - t0,
            notes=f"vidhi_intent_floors: {len(FLOORS)} intents; vidhi_floor_items: {items_written} rows",
        )


def _to_jsonb(d: dict) -> str:
    import json
    return json.dumps(d)
