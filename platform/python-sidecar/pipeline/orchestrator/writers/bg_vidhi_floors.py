"""
bg_vidhi_floors writer — D-2 Lane V-1 (Vidhi registry + compiler).

Populates `vidhi_intent_floors` + `vidhi_floor_items` (migration 440) with the
per-intent-class acharya floor + machine band. Content mirrors
`platform/src/lib/vidhi/registry_data.ts` (VIDHI_INTENT_FLOORS).

PARIŚODHANA B2: the floor literals below were regenerated from the canonical TS registry
(11 floors / 286 fully-expanded floor_items, incl. the Ω8 reachability band and the
`hard_floor` §N.6 density signal now carried per item) and are held in lockstep with it by
a CI DRIFT GATE (platform/scripts/census/check_vidhi_registry_parity.mjs, which deep-compares
this writer's `--dump-json` output against dump_vidhi_registry.ts). The gate, not hand-
discipline, keeps the copies in sync.

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

try:
    from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
except ImportError:  # PARIŚODHANA B2: standalone `--dump-json` (parity gate) — no orchestrator on path.
    # Minimal stand-ins so the module loads + the writer class defines when run as a script for the
    # parity gate (see bg_vidhi_primitives.py for the full rationale). Under the orchestrator the real
    # import always succeeds; the FROZEN WriterBase contract (§N.2) is unchanged.
    def register(_asset_id):  # type: ignore[misc]
        def _wrap(cls):
            return cls
        return _wrap

    class WriterBase:  # type: ignore[no-redef]
        pass

    ContextSpec = object  # type: ignore[assignment,misc]
    WriterResult = object  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# Each floor: (intent, version, cr27_coverage, notes, items)
# Each item: (primitive_id, order, band, args_override, hard_floor)
WEALTH_DEEPDIVE_ITEMS = [
    ('full_domain_dossier', 1, 'acharya_floor', {'domain': 'wealth'}, True),
    ('bhava_condition', 2, 'acharya_floor', {'house': 2}, False),
    ('bhavesha_condition', 3, 'acharya_floor', {'house': 2}, False),
    ('karaka_condition', 4, 'acharya_floor', {'karaka': 'jupiter'}, False),
    ('from_moon_view', 5, 'acharya_floor', {}, False),
    ('chalit_cusp_read', 6, 'acharya_floor', {}, False),
    ('bhava_bala_scan', 7, 'acharya_floor', {}, False),
    ('ashtakavarga_scan', 8, 'acharya_floor', {}, False),
    ('sensitive_degree_check', 9, 'acharya_floor', {}, False),
    ('divisional_facts', 10, 'acharya_floor', {'varga': 'D2'}, False),
    ('varga_ratification', 11, 'acharya_floor', {'vargas': ['D2', 'D9', 'D11']}, False),
    ('karakamsa_read', 12, 'acharya_floor', {}, False),
    ('kp_cusp_sublord_read', 13, 'acharya_floor', {}, False),
    ('special_lagna_read', 14, 'acharya_floor', {}, False),
    ('chara_karaka_read', 15, 'acharya_floor', {'chara_karaka': 'AmK'}, False),
    ('dhana_yoga_scan', 16, 'acharya_floor', {'domain': 'wealth'}, False),
    ('nbry_scan', 17, 'acharya_floor', {}, False),
    ('wealth_loss_mechanism_scan', 18, 'acharya_floor', {'domain': 'wealth'}, False),
    ('sudarshana_agreement_check', 19, 'acharya_floor', {}, False),
    ('bhavat_bhavam_check', 20, 'acharya_floor', {}, False),
    ('nakshatra_semantics', 21, 'acharya_floor', {}, False),
    ('cross_ayanamsha_variation', 22, 'acharya_floor', {'point': 'JUPITER'}, False),
    ('dasha_spine_lord_capability', 23, 'machine_band', {}, False),
    ('taranga_curve', 24, 'machine_band', {'domain': 'wealth'}, False),
    ('intervention_synthesis', 25, 'machine_band', {'domain': 'wealth'}, False),
    ('gochara_activation_read', 26, 'machine_band', {}, False),
    ('gochara_forecast_read', 27, 'machine_band', {}, False),
    ('election_read', 28, 'machine_band', {}, False),
    ('yoga_activation_scan', 29, 'machine_band', {}, False),
    ('standing_predictions_read', 30, 'machine_band', {'domain': 'wealth'}, False),
    ('lel_retrodiction', 31, 'machine_band', {'domain': 'wealth'}, False),
    ('contradiction_scan', 32, 'machine_band', {}, True),
    ('tail_divergence_read', 33, 'machine_band', {'domain': 'wealth'}, True),
    ('mechanism_read', 34, 'machine_band', {}, True),
    ('statistical_context', 35, 'machine_band', {}, True),
    ('now_read', 36, 'machine_band', {}, True),
    ('ahead_read', 37, 'machine_band', {'domain': 'wealth'}, True),
    ('priority_read', 38, 'machine_band', {}, True),
    ('divisional_facts', 40, 'acharya_floor', {'varga': 'D1'}, False),
    ('divisional_facts', 41, 'acharya_floor', {'varga': 'D9'}, False),
    ('divisional_facts', 42, 'acharya_floor', {'varga': 'D11'}, False),
    ('argala_read', 43, 'acharya_floor', {}, False),
    ('dispositor_closure_read', 44, 'acharya_floor', {}, False),
]

CAREER_DEEPDIVE_ITEMS = [
    ('full_domain_dossier', 1, 'acharya_floor', {'domain': 'career'}, True),
    ('bhava_condition', 2, 'acharya_floor', {'house': 10}, False),
    ('bhavesha_condition', 3, 'acharya_floor', {'house': 10}, False),
    ('karaka_condition', 4, 'acharya_floor', {'karaka': 'sun'}, False),
    ('divisional_facts', 5, 'acharya_floor', {'varga': 'D10'}, False),
    ('divisional_facts', 6, 'acharya_floor', {'varga': 'D9'}, False),
    ('varga_ratification', 7, 'acharya_floor', {'vargas': ['D1', 'D9', 'D10']}, False),
    ('chalit_cusp_read', 8, 'acharya_floor', {}, False),
    ('bhava_bala_scan', 9, 'acharya_floor', {}, False),
    ('ashtakavarga_scan', 10, 'acharya_floor', {}, False),
    ('sensitive_degree_check', 11, 'acharya_floor', {}, False),
    ('karakamsa_read', 12, 'acharya_floor', {}, False),
    ('kp_cusp_sublord_read', 13, 'acharya_floor', {}, False),
    ('sudarshana_agreement_check', 14, 'acharya_floor', {}, False),
    ('bhavat_bhavam_check', 15, 'acharya_floor', {}, False),
    ('dhana_yoga_scan', 16, 'acharya_floor', {'domain': 'career', 'family': 'raja'}, False),
    ('nakshatra_semantics', 17, 'acharya_floor', {}, False),
    ('chara_karaka_read', 18, 'acharya_floor', {'chara_karaka': 'AmK'}, False),
    ('dasha_spine_lord_capability', 19, 'machine_band', {}, False),
    ('taranga_curve', 20, 'machine_band', {'domain': 'career'}, False),
    ('intervention_synthesis', 21, 'machine_band', {'domain': 'career'}, False),
    ('gochara_activation_read', 22, 'machine_band', {}, False),
    ('gochara_forecast_read', 23, 'machine_band', {}, False),
    ('election_read', 24, 'machine_band', {}, False),
    ('yoga_activation_scan', 25, 'machine_band', {}, False),
    ('standing_predictions_read', 26, 'machine_band', {'domain': 'career'}, False),
    ('lel_retrodiction', 27, 'machine_band', {'domain': 'career'}, False),
    ('contradiction_scan', 28, 'machine_band', {}, True),
    ('tail_divergence_read', 29, 'machine_band', {'domain': 'career'}, True),
    ('mechanism_read', 30, 'machine_band', {}, True),
    ('statistical_context', 31, 'machine_band', {}, True),
    ('now_read', 32, 'machine_band', {}, True),
    ('ahead_read', 33, 'machine_band', {'domain': 'career'}, True),
    ('priority_read', 34, 'machine_band', {}, True),
    ('divisional_facts', 40, 'acharya_floor', {'varga': 'D1'}, False),
    ('special_lagna_read', 41, 'acharya_floor', {}, False),
    ('argala_read', 42, 'acharya_floor', {}, False),
    ('dispositor_closure_read', 43, 'acharya_floor', {}, False),
    ('cross_ayanamsha_variation', 44, 'acharya_floor', {'point': 'SUN'}, False),
]

HEALTH_DEEPDIVE_ITEMS = [
    ('bhava_condition', 1, 'acharya_floor', {'house': 6}, False),
    ('bhavesha_condition', 2, 'acharya_floor', {'house': 6}, False),
    ('karaka_condition', 3, 'acharya_floor', {'karaka': 'mars'}, False),
    ('dignity_scan', 4, 'acharya_floor', {}, False),
    ('sensitive_degree_check', 5, 'acharya_floor', {}, False),
    ('divisional_facts', 6, 'acharya_floor', {'varga': 'D6'}, False),
    ('dosha_scan', 7, 'acharya_floor', {}, False),
    ('varga_ratification', 8, 'acharya_floor', {'vargas': ['D1', 'D6', 'D9']}, False),
    ('chalit_cusp_read', 9, 'acharya_floor', {}, False),
    ('bhava_bala_scan', 10, 'acharya_floor', {}, False),
    ('ashtakavarga_scan', 11, 'acharya_floor', {}, False),
    ('karakamsa_read', 12, 'acharya_floor', {}, False),
    ('kp_cusp_sublord_read', 13, 'acharya_floor', {}, False),
    ('sudarshana_agreement_check', 14, 'acharya_floor', {}, False),
    ('bhavat_bhavam_check', 15, 'acharya_floor', {}, False),
    ('ayurdaya_read', 16, 'acharya_floor', {}, False),
    ('medical_read', 17, 'acharya_floor', {}, False),
    ('bhava_condition', 18, 'acharya_floor', {'house': 8}, False),
    ('karaka_condition', 19, 'acharya_floor', {'karaka': 'saturn'}, False),
    ('karaka_condition', 20, 'acharya_floor', {'karaka': 'moon'}, False),
    ('dasha_spine_lord_capability', 21, 'machine_band', {}, False),
    ('taranga_curve', 22, 'machine_band', {'domain': 'health'}, False),
    ('remedy_scan', 23, 'machine_band', {'domain': 'health'}, False),
    ('gochara_activation_read', 24, 'machine_band', {}, False),
    ('gochara_forecast_read', 25, 'machine_band', {}, False),
    ('election_read', 26, 'machine_band', {}, False),
    ('yoga_activation_scan', 27, 'machine_band', {}, False),
    ('standing_predictions_read', 28, 'machine_band', {'domain': 'health'}, False),
    ('lel_retrodiction', 29, 'machine_band', {'domain': 'health'}, False),
    ('contradiction_scan', 30, 'machine_band', {}, True),
    ('tail_divergence_read', 31, 'machine_band', {'domain': 'health'}, True),
    ('mechanism_read', 32, 'machine_band', {}, True),
    ('statistical_context', 33, 'machine_band', {}, True),
    ('now_read', 34, 'machine_band', {}, True),
    ('ahead_read', 35, 'machine_band', {'domain': 'health'}, True),
    ('priority_read', 36, 'machine_band', {}, True),
    ('divisional_facts', 40, 'acharya_floor', {'varga': 'D1'}, False),
    ('divisional_facts', 41, 'acharya_floor', {'varga': 'D9'}, False),
    ('divisional_facts', 42, 'acharya_floor', {'varga': 'D30'}, False),
    ('special_lagna_read', 43, 'acharya_floor', {}, False),
    ('argala_read', 44, 'acharya_floor', {}, False),
    ('dispositor_closure_read', 45, 'acharya_floor', {}, False),
    ('cross_ayanamsha_variation', 46, 'acharya_floor', {'point': 'SATURN'}, False),
]

MARRIAGE_DEEPDIVE_ITEMS = [
    ('bhava_condition', 1, 'acharya_floor', {'house': 7}, False),
    ('bhavesha_condition', 2, 'acharya_floor', {'house': 7}, False),
    ('karaka_condition', 3, 'acharya_floor', {'karaka': 'venus'}, False),
    ('divisional_facts', 4, 'acharya_floor', {'varga': 'D9'}, False),
    ('varga_ratification', 5, 'acharya_floor', {'vargas': ['D1', 'D9']}, False),
    ('dosha_scan', 6, 'acharya_floor', {}, False),
    ('karakamsa_read', 7, 'acharya_floor', {}, False),
    ('chalit_cusp_read', 8, 'acharya_floor', {}, False),
    ('bhava_bala_scan', 9, 'acharya_floor', {}, False),
    ('ashtakavarga_scan', 10, 'acharya_floor', {}, False),
    ('sensitive_degree_check', 11, 'acharya_floor', {}, False),
    ('kp_cusp_sublord_read', 12, 'acharya_floor', {}, False),
    ('sudarshana_agreement_check', 13, 'acharya_floor', {}, False),
    ('bhavat_bhavam_check', 14, 'acharya_floor', {}, False),
    ('bhava_condition', 15, 'acharya_floor', {'house': 2}, False),
    ('bhava_condition', 16, 'acharya_floor', {'house': 8}, False),
    ('chara_karaka_read', 17, 'acharya_floor', {'chara_karaka': 'DK'}, False),
    ('upapada_read', 18, 'acharya_floor', {}, False),
    ('dasha_spine_lord_capability', 19, 'machine_band', {}, False),
    ('taranga_curve', 20, 'machine_band', {'domain': 'marriage'}, False),
    ('remedy_scan', 21, 'machine_band', {'domain': 'marriage'}, False),
    ('gochara_activation_read', 22, 'machine_band', {}, False),
    ('gochara_forecast_read', 23, 'machine_band', {}, False),
    ('election_read', 24, 'machine_band', {}, False),
    ('yoga_activation_scan', 25, 'machine_band', {}, False),
    ('standing_predictions_read', 26, 'machine_band', {'domain': 'marriage'}, False),
    ('lel_retrodiction', 27, 'machine_band', {'domain': 'marriage'}, False),
    ('contradiction_scan', 28, 'machine_band', {}, True),
    ('tail_divergence_read', 29, 'machine_band', {'domain': 'marriage'}, True),
    ('mechanism_read', 30, 'machine_band', {}, True),
    ('statistical_context', 31, 'machine_band', {}, True),
    ('now_read', 32, 'machine_band', {}, True),
    ('ahead_read', 33, 'machine_band', {'domain': 'marriage'}, True),
    ('priority_read', 34, 'machine_band', {}, True),
    ('divisional_facts', 40, 'acharya_floor', {'varga': 'D1'}, False),
    ('special_lagna_read', 41, 'acharya_floor', {}, False),
    ('argala_read', 42, 'acharya_floor', {}, False),
    ('dispositor_closure_read', 43, 'acharya_floor', {}, False),
    ('cross_ayanamsha_variation', 44, 'acharya_floor', {'point': 'VENUS'}, False),
]

SPIRITUALITY_DEEPDIVE_ITEMS = [
    ('bhava_condition', 1, 'acharya_floor', {'house': 9}, False),
    ('bhava_condition', 2, 'acharya_floor', {'house': 12}, False),
    ('bhavesha_condition', 3, 'acharya_floor', {'house': 9}, False),
    ('bhavesha_condition', 4, 'acharya_floor', {'house': 12}, False),
    ('karaka_condition', 5, 'acharya_floor', {'karaka': 'jupiter'}, False),
    ('karaka_condition', 6, 'acharya_floor', {'karaka': 'ketu'}, False),
    ('chara_karaka_read', 7, 'acharya_floor', {'chara_karaka': 'AK'}, False),
    ('karakamsa_read', 8, 'acharya_floor', {}, False),
    ('divisional_facts', 9, 'acharya_floor', {'varga': 'D20'}, False),
    ('varga_ratification', 10, 'acharya_floor', {'vargas': ['D1', 'D9', 'D20']}, False),
    ('nakshatra_semantics', 11, 'acharya_floor', {}, False),
    ('spiritual_yoga_scan', 12, 'acharya_floor', {}, False),
    ('sudarshana_agreement_check', 13, 'acharya_floor', {}, False),
    ('dasha_spine_lord_capability', 14, 'machine_band', {}, False),
    ('intervention_synthesis', 15, 'machine_band', {'domain': 'spirituality'}, False),
    ('gochara_activation_read', 16, 'machine_band', {}, False),
    ('gochara_forecast_read', 17, 'machine_band', {}, False),
    ('election_read', 18, 'machine_band', {}, False),
    ('yoga_activation_scan', 19, 'machine_band', {}, False),
    ('standing_predictions_read', 20, 'machine_band', {'domain': 'spirituality'}, False),
    ('lel_retrodiction', 21, 'machine_band', {'domain': 'spirituality'}, False),
    ('contradiction_scan', 22, 'machine_band', {}, True),
    ('tail_divergence_read', 23, 'machine_band', {'domain': 'spirituality'}, True),
    ('mechanism_read', 24, 'machine_band', {}, True),
    ('statistical_context', 25, 'machine_band', {}, True),
    ('now_read', 26, 'machine_band', {}, True),
    ('ahead_read', 27, 'machine_band', {'domain': 'spirituality'}, True),
    ('priority_read', 28, 'machine_band', {}, True),
    ('divisional_facts', 40, 'acharya_floor', {'varga': 'D1'}, False),
    ('divisional_facts', 41, 'acharya_floor', {'varga': 'D9'}, False),
    ('ashtakavarga_scan', 42, 'acharya_floor', {}, False),
    ('special_lagna_read', 43, 'acharya_floor', {}, False),
    ('argala_read', 44, 'acharya_floor', {}, False),
    ('dispositor_closure_read', 45, 'acharya_floor', {}, False),
    ('cross_ayanamsha_variation', 46, 'acharya_floor', {'point': 'KETU'}, False),
]

EDUCATION_DEEPDIVE_ITEMS = [
    ('bhava_condition', 1, 'acharya_floor', {'house': 4}, False),
    ('bhava_condition', 2, 'acharya_floor', {'house': 5}, False),
    ('bhava_condition', 3, 'acharya_floor', {'house': 9}, False),
    ('bhavesha_condition', 4, 'acharya_floor', {'house': 4}, False),
    ('bhavesha_condition', 5, 'acharya_floor', {'house': 5}, False),
    ('karaka_condition', 6, 'acharya_floor', {'karaka': 'mercury'}, False),
    ('karaka_condition', 7, 'acharya_floor', {'karaka': 'jupiter'}, False),
    ('divisional_facts', 8, 'acharya_floor', {'varga': 'D24'}, False),
    ('varga_ratification', 9, 'acharya_floor', {'vargas': ['D1', 'D9', 'D24']}, False),
    ('nakshatra_semantics', 10, 'acharya_floor', {}, False),
    ('dignity_scan', 11, 'acharya_floor', {}, False),
    ('sensitive_degree_check', 12, 'acharya_floor', {}, False),
    ('dasha_spine_lord_capability', 13, 'machine_band', {}, False),
    ('taranga_curve', 14, 'machine_band', {'domain': 'education'}, False),
    ('gochara_activation_read', 15, 'machine_band', {}, False),
    ('gochara_forecast_read', 16, 'machine_band', {}, False),
    ('election_read', 17, 'machine_band', {}, False),
    ('yoga_activation_scan', 18, 'machine_band', {}, False),
    ('standing_predictions_read', 19, 'machine_band', {'domain': 'education'}, False),
    ('lel_retrodiction', 20, 'machine_band', {'domain': 'education'}, False),
    ('contradiction_scan', 21, 'machine_band', {}, True),
    ('tail_divergence_read', 22, 'machine_band', {'domain': 'education'}, True),
    ('mechanism_read', 23, 'machine_band', {}, True),
    ('statistical_context', 24, 'machine_band', {}, True),
    ('now_read', 25, 'machine_band', {}, True),
    ('ahead_read', 26, 'machine_band', {'domain': 'education'}, True),
    ('priority_read', 27, 'machine_band', {}, True),
    ('divisional_facts', 40, 'acharya_floor', {'varga': 'D1'}, False),
    ('divisional_facts', 41, 'acharya_floor', {'varga': 'D9'}, False),
    ('ashtakavarga_scan', 42, 'acharya_floor', {}, False),
    ('special_lagna_read', 43, 'acharya_floor', {}, False),
    ('argala_read', 44, 'acharya_floor', {}, False),
    ('dispositor_closure_read', 45, 'acharya_floor', {}, False),
    ('cross_ayanamsha_variation', 46, 'acharya_floor', {'point': 'MERCURY'}, False),
]

PROGENY_DEEPDIVE_ITEMS = [
    ('bhava_condition', 1, 'acharya_floor', {'house': 5}, False),
    ('bhava_condition', 2, 'acharya_floor', {'house': 9}, False),
    ('bhavesha_condition', 3, 'acharya_floor', {'house': 5}, False),
    ('karaka_condition', 4, 'acharya_floor', {'karaka': 'jupiter'}, False),
    ('chara_karaka_read', 5, 'acharya_floor', {'chara_karaka': 'PuK'}, False),
    ('divisional_facts', 6, 'acharya_floor', {'varga': 'D7'}, False),
    ('varga_ratification', 7, 'acharya_floor', {'vargas': ['D1', 'D9', 'D7']}, False),
    ('dosha_scan', 8, 'acharya_floor', {}, False),
    ('dasha_spine_lord_capability', 9, 'machine_band', {}, False),
    ('remedy_scan', 10, 'machine_band', {'domain': 'progeny'}, False),
    ('gochara_activation_read', 11, 'machine_band', {}, False),
    ('gochara_forecast_read', 12, 'machine_band', {}, False),
    ('election_read', 13, 'machine_band', {}, False),
    ('yoga_activation_scan', 14, 'machine_band', {}, False),
    ('standing_predictions_read', 15, 'machine_band', {'domain': 'progeny'}, False),
    ('lel_retrodiction', 16, 'machine_band', {'domain': 'progeny'}, False),
    ('contradiction_scan', 17, 'machine_band', {}, True),
    ('tail_divergence_read', 18, 'machine_band', {'domain': 'progeny'}, True),
    ('mechanism_read', 19, 'machine_band', {}, True),
    ('statistical_context', 20, 'machine_band', {}, True),
    ('now_read', 21, 'machine_band', {}, True),
    ('ahead_read', 22, 'machine_band', {'domain': 'progeny'}, True),
    ('priority_read', 23, 'machine_band', {}, True),
    ('divisional_facts', 40, 'acharya_floor', {'varga': 'D1'}, False),
    ('divisional_facts', 41, 'acharya_floor', {'varga': 'D9'}, False),
    ('ashtakavarga_scan', 42, 'acharya_floor', {}, False),
    ('special_lagna_read', 43, 'acharya_floor', {}, False),
    ('argala_read', 44, 'acharya_floor', {}, False),
    ('dispositor_closure_read', 45, 'acharya_floor', {}, False),
    ('cross_ayanamsha_variation', 46, 'acharya_floor', {'point': 'JUPITER'}, False),
]

STRUCTURE_READ_ITEMS = [
    ("positions_snapshot", 1, "acharya_floor", {}, False),
    ("dignity_scan", 2, "acharya_floor", {}, False),
    ("shadbala_rank", 3, "acharya_floor", {}, False),
    ("chalit_cusp_read", 4, "acharya_floor", {}, False),
    ("bhava_bala_scan", 5, "acharya_floor", {}, False),
    ("cross_ayanamsha_variation", 6, "acharya_floor", {"point": "LAGNA"}, False),
]

PANORAMIC_BREADTH_ITEMS = [
    ("positions_snapshot", 1, "acharya_floor", {}, False),
    ("shadbala_rank", 2, "acharya_floor", {}, False),
    ("nakshatra_semantics", 3, "acharya_floor", {}, False),
    ("arudha_read", 4, "acharya_floor", {}, False),
    ("mechanism_read", 5, "acharya_floor", {}, False),
    ("contradiction_scan", 6, "machine_band", {}, False),
    ("statistical_context", 7, "machine_band", {}, False),
    ("dasha_spine_lord_capability", 8, "machine_band", {}, False),
]

RETRIEVAL_ONLY_ITEMS = [
    ("positions_snapshot", 1, "acharya_floor", {}, False),
]

GENERAL_SYNTHESIS_ITEMS = [
    ('chart_digest_read', 1, 'acharya_floor', {}, True),
    ('positions_snapshot', 2, 'acharya_floor', {}, False),
    ('dignity_scan', 3, 'acharya_floor', {}, False),
    ('shadbala_rank', 4, 'acharya_floor', {}, False),
    ('bhava_bala_scan', 5, 'acharya_floor', {}, False),
    ('bhava_condition', 6, 'acharya_floor', {'house': 1}, False),
    ('bhavat_bhavam_check', 7, 'acharya_floor', {}, False),
    ('sensitive_degree_check', 8, 'acharya_floor', {}, False),
    ('chara_karaka_read', 9, 'acharya_floor', {'chara_karaka': 'AK'}, False),
    ('karakamsa_read', 10, 'acharya_floor', {}, False),
    ('arudha_read', 11, 'acharya_floor', {}, False),
    ('upapada_read', 12, 'acharya_floor', {}, False),
    ('yoga_firings_read', 13, 'acharya_floor', {}, False),
    ('divisional_facts', 14, 'acharya_floor', {'varga': 'D9'}, False),
    ('divisional_facts', 15, 'acharya_floor', {'varga': 'D2'}, False),
    ('divisional_facts', 16, 'acharya_floor', {'varga': 'D10'}, False),
    ('divisional_facts', 17, 'acharya_floor', {'varga': 'D7'}, False),
    ('divisional_facts', 18, 'acharya_floor', {'varga': 'D20'}, False),
    ('dasha_spine_lord_capability', 19, 'machine_band', {}, False),
    ('gochara_activation_read', 20, 'machine_band', {}, False),
    ('gochara_forecast_read', 21, 'machine_band', {}, False),
    ('election_read', 22, 'machine_band', {}, False),
    ('yoga_activation_scan', 23, 'machine_band', {}, False),
    ('standing_predictions_read', 24, 'machine_band', {'domain': 'general'}, False),
    ('lel_retrodiction', 25, 'machine_band', {'domain': 'general'}, False),
    ('contradiction_scan', 26, 'machine_band', {}, True),
    ('tail_divergence_read', 27, 'machine_band', {'domain': 'general'}, True),
    ('mechanism_read', 28, 'machine_band', {}, True),
    ('statistical_context', 29, 'machine_band', {}, True),
    ('now_read', 30, 'machine_band', {}, True),
    ('ahead_read', 31, 'machine_band', {'domain': 'general'}, True),
    ('priority_read', 32, 'machine_band', {}, True),
]

# ── ṢAḌ-DARŚANA W5 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W5) — the three kala-routing floors.
# Transcribed verbatim from platform/src/lib/vidhi/registry_data.ts by the vidhi-registry
# parity gate's own dump (scripts/census/dump_vidhi_registry.ts) — never hand-retyped
# independently of the TS source.
UNDERTAKING_ELECTION_ITEMS = [
    ('elect_read', 1, 'acharya_floor', {}, True),
    ('chart_digest_read', 2, 'acharya_floor', {}, True),
    ('positions_snapshot', 3, 'acharya_floor', {}, False),
    ('dignity_scan', 4, 'acharya_floor', {}, False),
    ('shadbala_rank', 5, 'acharya_floor', {}, False),
    ('bhava_bala_scan', 6, 'acharya_floor', {}, False),
    ('bhava_condition', 7, 'acharya_floor', {'house': 1}, False),
    ('bhavat_bhavam_check', 8, 'acharya_floor', {}, False),
    ('sensitive_degree_check', 9, 'acharya_floor', {}, False),
    ('chara_karaka_read', 10, 'acharya_floor', {'chara_karaka': 'AK'}, False),
    ('karakamsa_read', 11, 'acharya_floor', {}, False),
    ('arudha_read', 12, 'acharya_floor', {}, False),
    ('upapada_read', 13, 'acharya_floor', {}, False),
    ('yoga_firings_read', 14, 'acharya_floor', {}, False),
    ('divisional_facts', 15, 'acharya_floor', {'varga': 'D9'}, False),
    ('divisional_facts', 16, 'acharya_floor', {'varga': 'D2'}, False),
    ('divisional_facts', 17, 'acharya_floor', {'varga': 'D10'}, False),
    ('divisional_facts', 18, 'acharya_floor', {'varga': 'D7'}, False),
    ('divisional_facts', 19, 'acharya_floor', {'varga': 'D20'}, False),
    ('dasha_spine_lord_capability', 20, 'machine_band', {}, False),
    ('gochara_activation_read', 21, 'machine_band', {}, False),
    ('gochara_forecast_read', 22, 'machine_band', {}, False),
    ('election_read', 23, 'machine_band', {}, False),
    ('yoga_activation_scan', 24, 'machine_band', {}, False),
    ('standing_predictions_read', 25, 'machine_band', {'domain': 'general'}, False),
    ('lel_retrodiction', 26, 'machine_band', {'domain': 'general'}, False),
    ('contradiction_scan', 27, 'machine_band', {}, True),
    ('tail_divergence_read', 28, 'machine_band', {'domain': 'general'}, True),
    ('mechanism_read', 29, 'machine_band', {}, True),
    ('statistical_context', 30, 'machine_band', {}, True),
    ('now_read', 31, 'machine_band', {}, True),
    ('ahead_read', 32, 'machine_band', {'domain': 'general'}, True),
    ('priority_read', 33, 'machine_band', {}, True),
]

BIOGRAPHY_NARRATIVE_ITEMS = [
    ('story_read', 1, 'acharya_floor', {}, True),
    ('chart_digest_read', 2, 'acharya_floor', {}, True),
    ('positions_snapshot', 3, 'acharya_floor', {}, False),
    ('dignity_scan', 4, 'acharya_floor', {}, False),
    ('shadbala_rank', 5, 'acharya_floor', {}, False),
    ('bhava_bala_scan', 6, 'acharya_floor', {}, False),
    ('bhava_condition', 7, 'acharya_floor', {'house': 1}, False),
    ('bhavat_bhavam_check', 8, 'acharya_floor', {}, False),
    ('sensitive_degree_check', 9, 'acharya_floor', {}, False),
    ('chara_karaka_read', 10, 'acharya_floor', {'chara_karaka': 'AK'}, False),
    ('karakamsa_read', 11, 'acharya_floor', {}, False),
    ('arudha_read', 12, 'acharya_floor', {}, False),
    ('upapada_read', 13, 'acharya_floor', {}, False),
    ('yoga_firings_read', 14, 'acharya_floor', {}, False),
    ('divisional_facts', 15, 'acharya_floor', {'varga': 'D9'}, False),
    ('divisional_facts', 16, 'acharya_floor', {'varga': 'D2'}, False),
    ('divisional_facts', 17, 'acharya_floor', {'varga': 'D10'}, False),
    ('divisional_facts', 18, 'acharya_floor', {'varga': 'D7'}, False),
    ('divisional_facts', 19, 'acharya_floor', {'varga': 'D20'}, False),
    ('dasha_spine_lord_capability', 20, 'machine_band', {}, False),
    ('gochara_activation_read', 21, 'machine_band', {}, False),
    ('gochara_forecast_read', 22, 'machine_band', {}, False),
    ('election_read', 23, 'machine_band', {}, False),
    ('yoga_activation_scan', 24, 'machine_band', {}, False),
    ('standing_predictions_read', 25, 'machine_band', {'domain': 'general'}, False),
    ('lel_retrodiction', 26, 'machine_band', {'domain': 'general'}, False),
    ('contradiction_scan', 27, 'machine_band', {}, True),
    ('tail_divergence_read', 28, 'machine_band', {'domain': 'general'}, True),
    ('mechanism_read', 29, 'machine_band', {}, True),
    ('statistical_context', 30, 'machine_band', {}, True),
    ('now_read', 31, 'machine_band', {}, True),
    ('ahead_read', 32, 'machine_band', {'domain': 'general'}, True),
    ('priority_read', 33, 'machine_band', {}, True),
]

RITUAL_YAJNA_ITEMS = [
    ('ritual_read', 1, 'acharya_floor', {}, True),
    ('chart_digest_read', 2, 'acharya_floor', {}, True),
    ('positions_snapshot', 3, 'acharya_floor', {}, False),
    ('dignity_scan', 4, 'acharya_floor', {}, False),
    ('shadbala_rank', 5, 'acharya_floor', {}, False),
    ('bhava_bala_scan', 6, 'acharya_floor', {}, False),
    ('bhava_condition', 7, 'acharya_floor', {'house': 1}, False),
    ('bhavat_bhavam_check', 8, 'acharya_floor', {}, False),
    ('sensitive_degree_check', 9, 'acharya_floor', {}, False),
    ('chara_karaka_read', 10, 'acharya_floor', {'chara_karaka': 'AK'}, False),
    ('karakamsa_read', 11, 'acharya_floor', {}, False),
    ('arudha_read', 12, 'acharya_floor', {}, False),
    ('upapada_read', 13, 'acharya_floor', {}, False),
    ('yoga_firings_read', 14, 'acharya_floor', {}, False),
    ('divisional_facts', 15, 'acharya_floor', {'varga': 'D9'}, False),
    ('divisional_facts', 16, 'acharya_floor', {'varga': 'D2'}, False),
    ('divisional_facts', 17, 'acharya_floor', {'varga': 'D10'}, False),
    ('divisional_facts', 18, 'acharya_floor', {'varga': 'D7'}, False),
    ('divisional_facts', 19, 'acharya_floor', {'varga': 'D20'}, False),
    ('dasha_spine_lord_capability', 20, 'machine_band', {}, False),
    ('gochara_activation_read', 21, 'machine_band', {}, False),
    ('gochara_forecast_read', 22, 'machine_band', {}, False),
    ('election_read', 23, 'machine_band', {}, False),
    ('yoga_activation_scan', 24, 'machine_band', {}, False),
    ('standing_predictions_read', 25, 'machine_band', {'domain': 'general'}, False),
    ('lel_retrodiction', 26, 'machine_band', {'domain': 'general'}, False),
    ('contradiction_scan', 27, 'machine_band', {}, True),
    ('tail_divergence_read', 28, 'machine_band', {'domain': 'general'}, True),
    ('mechanism_read', 29, 'machine_band', {}, True),
    ('statistical_context', 30, 'machine_band', {}, True),
    ('now_read', 31, 'machine_band', {}, True),
    ('ahead_read', 32, 'machine_band', {'domain': 'general'}, True),
    ('priority_read', 33, 'machine_band', {}, True),
]

FLOORS = [
    ("wealth_deepdive", 1, ["CR-27a", "CR-27b", "CR-27c", "CR-27d", "CR-36"], "Flagship floor — worked example per DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3; §G master acceptance target.", WEALTH_DEEPDIVE_ITEMS),
    ("career_deepdive", 1, ["CR-27c", "CR-27d"], "D10/D9 multi-varga per CR-62’s wealth {D1,D2,D9,D11} / career {D1,D9,D10} map (design §12 lord-placement join).", CAREER_DEEPDIVE_ITEMS),
    ("health_deepdive", 1, ["CR-27b"], None, HEALTH_DEEPDIVE_ITEMS),
    ("marriage_deepdive", 1, ["CR-27b"], None, MARRIAGE_DEEPDIVE_ITEMS),
    ("spirituality_deepdive", 1, [], "VIDHI-PŪRṆATĀ P-2 [MANDATORY] — mokṣa-domain floor (brief §2 P-2 / §A). H9+H12 + lords, Jupiter(guru)+Ketu(mokṣa) kārakas, AK+karakāṃśa (from-karakāṃśa 12th derived answerer-side), D20, D1/D9/D20 ratification. Jaimini spiritual-yoga scan is DARK (CR-130 — family key absent).", SPIRITUALITY_DEEPDIVE_ITEMS),
    ("education_deepdive", 1, [], "VIDHI-PŪRṆATĀ P-2 [CANDIDATE] — D24-backed education floor (brief §A). H4+H5+H9 + 4th/5th lords, Mercury(buddhi)+Jupiter(jñāna) kārakas, D24 + D1/D9/D24 ratification. education-scoped taraṅga_curve inherits CR-66 (phala domain anchors zero) — dark, not faked.", EDUCATION_DEEPDIVE_ITEMS),
    ("progeny_deepdive", 1, [], "VIDHI-PŪRṆATĀ P-2 [CANDIDATE] — D7-backed progeny floor (brief §A). Spine off H5 + Jupiter (putra-kāraka) + PuK REGARDLESS of the D7 spouse_karya label quirk (P-0 (e): L1 chart_divisionals writer mislabel, must_not_touch; D7 is corroboration only). H5(+H9 5th-from-5th), D7, D1/D9/D7 ratification.", PROGENY_DEEPDIVE_ITEMS),
    ("structure_read", 1, [], "Narrow/structure depth — the \"show me my D1\" canonical example; no machine band (deliberate).", STRUCTURE_READ_ITEMS),
    ("panoramic_breadth", 1, ["CR-27a", "CR-27c", "CR-27d"], "The \"unleash my financial potential\"-shaped wide sweep — domain-agnostic breadth, not depth.", PANORAMIC_BREADTH_ITEMS),
    ("retrieval_only", 1, [], None, RETRIEVAL_ONLY_ITEMS),
    ("general_synthesis", 1, ["CR-27a"], None, GENERAL_SYNTHESIS_ITEMS),
    ('undertaking_election', 1, [], 'ṢAḌ-DARŚANA W5 — "when should I…?" routing floor. Headlined by elect_read (Mode-3 ACTIVITY ELECTION: act-time slate + paired preparatory rite, served as one answer per the Mode-3 routing rule, Elevation §8) over the Pūrṇa-Ādhāra structural minimum.', UNDERTAKING_ELECTION_ITEMS),
    ('biography_narrative', 1, [], 'ṢAḌ-DARŚANA W5 — "what has my life been?" routing floor. Headlined by story_read (the daśā-chaptered developmental narrative) over the Pūrṇa-Ādhāra structural minimum.', BIOGRAPHY_NARRATIVE_ITEMS),
    ('ritual_yajna', 1, [], 'ṢAḌ-DARŚANA W5 — ritual/yajña/vrata routing floor. Headlined by ritual_read (YAJÑA-SETU Modes 1–2 ONLY — Mode 3 redirects to elect_read, never passes through, per the Mode-3 routing rule) over the Pūrṇa-Ādhāra structural minimum.', RITUAL_YAJNA_ITEMS),
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
                for (primitive_id, order, band, args_override, hard_floor) in items:
                    cur.execute(
                        """
                        INSERT INTO vidhi_floor_items
                          (intent, primitive_id, item_order, band, args_override, hard_floor)
                        VALUES (%s, %s, %s, %s, %s::JSONB, %s)
                        """,
                        (intent, primitive_id, order, band, _to_jsonb(args_override), hard_floor),
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


def _dump_json() -> None:
    """--dump-json: emit the floors half of the canonical-normalized Vidhi registry for the parity
    gate (platform/scripts/census/check_vidhi_registry_parity.mjs). No DB needed — prints FLOORS as
    JSON in the SAME shape as platform/scripts/census/dump_vidhi_registry.ts's `floors` array
    (floors in registry order; items sorted by order; keys sorted for a stable byte form)."""
    import json as _json
    floors = []
    for (intent, version, cr27_coverage, notes, items) in FLOORS:
        floor_items = [
            {
                "primitive_id": primitive_id,
                "order": order,
                "band": band,
                "args_override": args_override,
                "hard_floor": hard_floor,
            }
            for (primitive_id, order, band, args_override, hard_floor) in items
        ]
        floor_items.sort(key=lambda it: it["order"])
        floors.append({
            "intent": intent,
            "version": version,
            "cr27_coverage": list(cr27_coverage),
            "notes": notes,
            "floor_items": floor_items,
        })
    print(_json.dumps({"floors": floors}, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    import sys
    if '--dump-json' in sys.argv:
        _dump_json()
    else:
        raise SystemExit(
            "bg_vidhi_floors.py is an orchestrator writer; run it via the orchestrator. "
            "The only standalone entrypoint is `--dump-json` (used by the vidhi registry parity gate)."
        )
