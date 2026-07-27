-- Migration 466: Vidhi registry Ω8 floor-wiring — PARIŚODHANA B2 (Reachability Triangle)
-- Created: 2026-07-28
--
-- Brings the migration-440/462 DB seed (the "third copy" of the Vidhi registry) into lockstep
-- with the canonical source platform/src/lib/vidhi/registry_data.ts after PARIŚODHANA B2's Ω8
-- floor-wiring. Migration 462 seeded the VIDHI-PŪRṆATĀ contents (48 primitives / 11 floors /
-- 230 floor_items). This SURGICAL migration applies ONLY the Ω8 delta on top of it:
--   • 2 NEW primitives — argala_read, dispositor_closure_read (structural sweeps registered in
--     REGENERATED_FLOORS_v1_0.json but previously unwired). Every tool_args category is served by
--     a live tool (get_argala / get_dispositors via ganita_chart_facts_get) — no new computation.
--   • 2 WIDENED primitives — special_lagna_read (full lagna + saham + Upapada set; lagnas filter
--     dropped) and ashtakavarga_scan (full per-varga AV family; definition widened).
--   • 2 RECONCILED primitives — cross_ayanamsha_variation + full_domain_dossier were added to the
--     canonical TS registry AFTER migration 462 (EL-27 / Ω5) but never got their own DB-seed
--     migration; the Ω8 floor re-seed references them and vidhi_floor_items.primitive_id has an FK
--     to vidhi_primitives, so they are upserted here. This brings vidhi_primitives to the full 52.
--   • 7 deepdive floors RE-SEEDED (wholesale per-intent DELETE-then-INSERT of vidhi_floor_items)
--     to carry the Ω8 reachability band — the domain-relevant divisional vargas, the widened AV +
--     special-lagna family scans, the argala + dispositor-closure sweeps, and the cross-ayanamsha
--     agreement axis. The 4 non-deepdive floors (structure_read / panoramic_breadth /
--     retrieval_only / general_synthesis) and the vidhi_intent_floors rows are UNCHANGED.
--
-- Honesty line: every floor item resolves to a live tool OR carries a truthful primitive-level
-- known_gap surfaced in the completeness receipt's `dark` bucket, never faked. argala_read and
-- dispositor_closure_read both carry known_gap NULL (data-backed).
--
-- §N.3 idempotency (mirrors the Python writers exactly):
--   • vidhi_primitives  → ON CONFLICT (primitive_id) DO UPDATE  (L0 global upsert).
--   • vidhi_floor_items → per-intent DELETE-then-INSERT (a floor edit re-numbers item_order, so
--     wholesale replace avoids orphaned rows under stale numbering).
-- Re-runnable: applying twice is a no-op beyond updated_at.
--
-- This migration is DATA on Vidhi-owned tables only. It does NOT touch the FROZEN
-- orchestrator/WriterBase, any L1–L5 writer/table, kala_gochara_windows, build_substep_progress,
-- or any calibration table.
--
-- ROLLBACK (manual): re-apply migration 462 (restores the pre-Ω8 primitive definitions + floor
-- items) and DELETE the two new primitives:
--   BEGIN;
--     DELETE FROM vidhi_floor_items WHERE primitive_id IN ('argala_read','dispositor_closure_read');
--     DELETE FROM vidhi_primitives  WHERE primitive_id IN ('argala_read','dispositor_closure_read');
--     -- then re-run migration 462 to restore special_lagna_read/ashtakavarga_scan + the 7 floors.
--   COMMIT;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — vidhi_primitives: the 2 new + 2 widened + 2 reconciled atoms (ON CONFLICT DO UPDATE) ──

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('argala_read', 1, 'Argala (intervention) + virodha-argala matrix per varga for a house/point — the natal argala_natal_matrix, virodha_argala_natal_matrix, and net_argala_per_varga (intervention structure on the bhāvas). A structural sweep, not a single-fact read.', 'structural', 'ganita_chart_facts_get', '{"chart_id":"{chart_id}","category":"net_argala_per_varga"}'::JSONB,
        'ganita_structural_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('dispositor_closure_read', 1, 'Full dispositor-chain closure: composite_dispositor_strength facts + the convergent- dispositor-chain / dispositor-cycle mechanism classes (the who-ultimately-controls-whom lordship closure across the chart).', 'structural', 'ganita_chart_facts_get', '{"chart_id":"{chart_id}","category":"composite_dispositor_strength"}'::JSONB,
        'bodha_mechanisms_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('special_lagna_read', 1, 'Reads the FULL special-lagna + saham set — 7 special lagnas (Indu, Sree, Ghati, Hora, Bhava, Varnada, Vighati) + 70 sahams + Upapada — with domain salience.', 'structural', 'ganita_special_lagnas_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'ganita_special_lagnas_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('ashtakavarga_scan', 1, 'Full Ashtakavarga family scan (per-varga bindu / bindu-sign / pinda / shodhana / kakshya) per graha/house — not D1-only.', 'structural', 'ganita_chart_facts_get', '{"chart_id":"{chart_id}","category":"ashtakavarga"}'::JSONB,
        'ganita_structural_get', NULL, ARRAY['ashtakavarga_bindu']::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('cross_ayanamsha_variation', 1, 'Cross-ayanamsha agreement for a planet/point: dignity, bhāva-shift, and vargottama deltas computed across the 5 REAL ayanamshas (INVARIANT sentinel excluded), emitting ayanamsha_agreement "n/5" as a confidence field. Full agreement compresses; disagreement surfaces as a rarity signal (EL-56 family-collapse-safe). The planner''s only ayanamsha axis.', 'signal', 'ganita_chart_facts_get', '{"chart_id":"{chart_id}","about":"{point}","ayanamsha_axis":["krishnamurti","lahiri_chitrapaksha","raman","surya_siddhanta_classical","true_chitra"]}'::JSONB,
        'ganita_chart_facts_get(ayanamsha_id={ayanamsha})', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('full_domain_dossier', 1, 'Whole-domain gather-then-compose sweep: pages the domain''s ENTIRE concept slice (all Ω1-inventory concepts) in budget-capped pages via the Ω5 `dossier` engine, structurally withholding every interpretive surface until coverage is 100% accounted (synthesis_gate OPEN). The planner''s guaranteed route to FULL domain coverage — the atom-by-atom floor reads single facts; this reads the whole territory. Call it FIRST; follow `cursor` to exhaustion before composing. Flagship slices: {wealth, career} × the two canonical charts.', 'utility', 'dossier', '{"domain":"{domain}","chart_id":"{chart_id}","budget_kb":24}'::JSONB,
        NULL, NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

-- ── §2 — vidhi_floor_items: re-seed the 7 deepdive floors (per-intent DELETE-then-INSERT) ──

DELETE FROM vidhi_floor_items WHERE intent = 'wealth_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'full_domain_dossier', 1, 'acharya_floor', '{"domain":"wealth"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'bhava_condition', 2, 'acharya_floor', '{"house":2}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'bhavesha_condition', 3, 'acharya_floor', '{"house":2}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'karaka_condition', 4, 'acharya_floor', '{"karaka":"jupiter"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'from_moon_view', 5, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'chalit_cusp_read', 6, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'bhava_bala_scan', 7, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'ashtakavarga_scan', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'sensitive_degree_check', 9, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'divisional_facts', 10, 'acharya_floor', '{"varga":"D2"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'varga_ratification', 11, 'acharya_floor', '{"vargas":["D2","D9","D11"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'karakamsa_read', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'kp_cusp_sublord_read', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'special_lagna_read', 14, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'chara_karaka_read', 15, 'acharya_floor', '{"chara_karaka":"AmK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'dhana_yoga_scan', 16, 'acharya_floor', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'nbry_scan', 17, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'wealth_loss_mechanism_scan', 18, 'acharya_floor', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'sudarshana_agreement_check', 19, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'bhavat_bhavam_check', 20, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'nakshatra_semantics', 21, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'cross_ayanamsha_variation', 22, 'acharya_floor', '{"point":"JUPITER"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'dasha_spine_lord_capability', 23, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'taranga_curve', 24, 'machine_band', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'intervention_synthesis', 25, 'machine_band', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'gochara_activation_read', 26, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'gochara_forecast_read', 27, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'election_read', 28, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'yoga_activation_scan', 29, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'standing_predictions_read', 30, 'machine_band', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'lel_retrodiction', 31, 'machine_band', '{"domain":"wealth"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'contradiction_scan', 32, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'tail_divergence_read', 33, 'machine_band', '{"domain":"wealth"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'mechanism_read', 34, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'statistical_context', 35, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'divisional_facts', 40, 'acharya_floor', '{"varga":"D1"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'divisional_facts', 41, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'divisional_facts', 42, 'acharya_floor', '{"varga":"D11"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'argala_read', 43, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('wealth_deepdive', 'dispositor_closure_read', 44, 'acharya_floor', '{}'::JSONB, false);

DELETE FROM vidhi_floor_items WHERE intent = 'career_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'full_domain_dossier', 1, 'acharya_floor', '{"domain":"career"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'bhava_condition', 2, 'acharya_floor', '{"house":10}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'bhavesha_condition', 3, 'acharya_floor', '{"house":10}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'karaka_condition', 4, 'acharya_floor', '{"karaka":"sun"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'divisional_facts', 5, 'acharya_floor', '{"varga":"D10"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'divisional_facts', 6, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'varga_ratification', 7, 'acharya_floor', '{"vargas":["D1","D9","D10"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'chalit_cusp_read', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'bhava_bala_scan', 9, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'ashtakavarga_scan', 10, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'sensitive_degree_check', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'karakamsa_read', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'kp_cusp_sublord_read', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'sudarshana_agreement_check', 14, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'bhavat_bhavam_check', 15, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'dhana_yoga_scan', 16, 'acharya_floor', '{"domain":"career","family":"raja"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'nakshatra_semantics', 17, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'chara_karaka_read', 18, 'acharya_floor', '{"chara_karaka":"AmK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'dasha_spine_lord_capability', 19, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'taranga_curve', 20, 'machine_band', '{"domain":"career"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'intervention_synthesis', 21, 'machine_band', '{"domain":"career"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'gochara_activation_read', 22, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'gochara_forecast_read', 23, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'election_read', 24, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'yoga_activation_scan', 25, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'standing_predictions_read', 26, 'machine_band', '{"domain":"career"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'lel_retrodiction', 27, 'machine_band', '{"domain":"career"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'contradiction_scan', 28, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'tail_divergence_read', 29, 'machine_band', '{"domain":"career"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'mechanism_read', 30, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'statistical_context', 31, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'divisional_facts', 40, 'acharya_floor', '{"varga":"D1"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'special_lagna_read', 41, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'argala_read', 42, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'dispositor_closure_read', 43, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('career_deepdive', 'cross_ayanamsha_variation', 44, 'acharya_floor', '{"point":"SUN"}'::JSONB, false);

DELETE FROM vidhi_floor_items WHERE intent = 'health_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":6}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhavesha_condition', 2, 'acharya_floor', '{"house":6}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'karaka_condition', 3, 'acharya_floor', '{"karaka":"mars"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'dignity_scan', 4, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'sensitive_degree_check', 5, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'divisional_facts', 6, 'acharya_floor', '{"varga":"D6"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'dosha_scan', 7, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'varga_ratification', 8, 'acharya_floor', '{"vargas":["D1","D6","D9"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'chalit_cusp_read', 9, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhava_bala_scan', 10, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'ashtakavarga_scan', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'karakamsa_read', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'kp_cusp_sublord_read', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'sudarshana_agreement_check', 14, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhavat_bhavam_check', 15, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'ayurdaya_read', 16, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'medical_read', 17, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'bhava_condition', 18, 'acharya_floor', '{"house":8}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'karaka_condition', 19, 'acharya_floor', '{"karaka":"saturn"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'karaka_condition', 20, 'acharya_floor', '{"karaka":"moon"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'dasha_spine_lord_capability', 21, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'taranga_curve', 22, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'remedy_scan', 23, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'gochara_activation_read', 24, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'gochara_forecast_read', 25, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'election_read', 26, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'yoga_activation_scan', 27, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'standing_predictions_read', 28, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'lel_retrodiction', 29, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'contradiction_scan', 30, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'tail_divergence_read', 31, 'machine_band', '{"domain":"health"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'mechanism_read', 32, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'statistical_context', 33, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'divisional_facts', 40, 'acharya_floor', '{"varga":"D1"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'divisional_facts', 41, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'divisional_facts', 42, 'acharya_floor', '{"varga":"D30"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'special_lagna_read', 43, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'argala_read', 44, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'dispositor_closure_read', 45, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'cross_ayanamsha_variation', 46, 'acharya_floor', '{"point":"SATURN"}'::JSONB, false);

DELETE FROM vidhi_floor_items WHERE intent = 'marriage_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":7}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhavesha_condition', 2, 'acharya_floor', '{"house":7}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'karaka_condition', 3, 'acharya_floor', '{"karaka":"venus"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'divisional_facts', 4, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'varga_ratification', 5, 'acharya_floor', '{"vargas":["D1","D9"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'dosha_scan', 6, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'karakamsa_read', 7, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'chalit_cusp_read', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhava_bala_scan', 9, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'ashtakavarga_scan', 10, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'sensitive_degree_check', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'kp_cusp_sublord_read', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'sudarshana_agreement_check', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhavat_bhavam_check', 14, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhava_condition', 15, 'acharya_floor', '{"house":2}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'bhava_condition', 16, 'acharya_floor', '{"house":8}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'chara_karaka_read', 17, 'acharya_floor', '{"chara_karaka":"DK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'upapada_read', 18, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'dasha_spine_lord_capability', 19, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'taranga_curve', 20, 'machine_band', '{"domain":"marriage"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'remedy_scan', 21, 'machine_band', '{"domain":"marriage"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'gochara_activation_read', 22, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'gochara_forecast_read', 23, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'election_read', 24, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'yoga_activation_scan', 25, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'standing_predictions_read', 26, 'machine_band', '{"domain":"marriage"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'lel_retrodiction', 27, 'machine_band', '{"domain":"marriage"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'contradiction_scan', 28, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'tail_divergence_read', 29, 'machine_band', '{"domain":"marriage"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'mechanism_read', 30, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'statistical_context', 31, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'divisional_facts', 40, 'acharya_floor', '{"varga":"D1"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'special_lagna_read', 41, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'argala_read', 42, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'dispositor_closure_read', 43, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('marriage_deepdive', 'cross_ayanamsha_variation', 44, 'acharya_floor', '{"point":"VENUS"}'::JSONB, false);

DELETE FROM vidhi_floor_items WHERE intent = 'spirituality_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":9}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'bhava_condition', 2, 'acharya_floor', '{"house":12}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'bhavesha_condition', 3, 'acharya_floor', '{"house":9}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'bhavesha_condition', 4, 'acharya_floor', '{"house":12}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'karaka_condition', 5, 'acharya_floor', '{"karaka":"jupiter"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'karaka_condition', 6, 'acharya_floor', '{"karaka":"ketu"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'chara_karaka_read', 7, 'acharya_floor', '{"chara_karaka":"AK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'karakamsa_read', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'divisional_facts', 9, 'acharya_floor', '{"varga":"D20"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'varga_ratification', 10, 'acharya_floor', '{"vargas":["D1","D9","D20"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'nakshatra_semantics', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'spiritual_yoga_scan', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'sudarshana_agreement_check', 13, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'dasha_spine_lord_capability', 14, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'intervention_synthesis', 15, 'machine_band', '{"domain":"spirituality"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'gochara_activation_read', 16, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'gochara_forecast_read', 17, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'election_read', 18, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'yoga_activation_scan', 19, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'standing_predictions_read', 20, 'machine_band', '{"domain":"spirituality"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'lel_retrodiction', 21, 'machine_band', '{"domain":"spirituality"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'contradiction_scan', 22, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'tail_divergence_read', 23, 'machine_band', '{"domain":"spirituality"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'mechanism_read', 24, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'statistical_context', 25, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'divisional_facts', 40, 'acharya_floor', '{"varga":"D1"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'divisional_facts', 41, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'ashtakavarga_scan', 42, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'special_lagna_read', 43, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'argala_read', 44, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'dispositor_closure_read', 45, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('spirituality_deepdive', 'cross_ayanamsha_variation', 46, 'acharya_floor', '{"point":"KETU"}'::JSONB, false);

DELETE FROM vidhi_floor_items WHERE intent = 'education_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":4}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhava_condition', 2, 'acharya_floor', '{"house":5}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhava_condition', 3, 'acharya_floor', '{"house":9}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhavesha_condition', 4, 'acharya_floor', '{"house":4}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'bhavesha_condition', 5, 'acharya_floor', '{"house":5}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'karaka_condition', 6, 'acharya_floor', '{"karaka":"mercury"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'karaka_condition', 7, 'acharya_floor', '{"karaka":"jupiter"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'divisional_facts', 8, 'acharya_floor', '{"varga":"D24"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'varga_ratification', 9, 'acharya_floor', '{"vargas":["D1","D9","D24"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'nakshatra_semantics', 10, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'dignity_scan', 11, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'sensitive_degree_check', 12, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'dasha_spine_lord_capability', 13, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'taranga_curve', 14, 'machine_band', '{"domain":"education"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'gochara_activation_read', 15, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'gochara_forecast_read', 16, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'election_read', 17, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'yoga_activation_scan', 18, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'standing_predictions_read', 19, 'machine_band', '{"domain":"education"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'lel_retrodiction', 20, 'machine_band', '{"domain":"education"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'contradiction_scan', 21, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'tail_divergence_read', 22, 'machine_band', '{"domain":"education"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'mechanism_read', 23, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'statistical_context', 24, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'divisional_facts', 40, 'acharya_floor', '{"varga":"D1"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'divisional_facts', 41, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'ashtakavarga_scan', 42, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'special_lagna_read', 43, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'argala_read', 44, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'dispositor_closure_read', 45, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('education_deepdive', 'cross_ayanamsha_variation', 46, 'acharya_floor', '{"point":"MERCURY"}'::JSONB, false);

DELETE FROM vidhi_floor_items WHERE intent = 'progeny_deepdive';
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'bhava_condition', 1, 'acharya_floor', '{"house":5}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'bhava_condition', 2, 'acharya_floor', '{"house":9}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'bhavesha_condition', 3, 'acharya_floor', '{"house":5}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'karaka_condition', 4, 'acharya_floor', '{"karaka":"jupiter"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'chara_karaka_read', 5, 'acharya_floor', '{"chara_karaka":"PuK"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'divisional_facts', 6, 'acharya_floor', '{"varga":"D7"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'varga_ratification', 7, 'acharya_floor', '{"vargas":["D1","D9","D7"]}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'dosha_scan', 8, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'dasha_spine_lord_capability', 9, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'remedy_scan', 10, 'machine_band', '{"domain":"progeny"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'gochara_activation_read', 11, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'gochara_forecast_read', 12, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'election_read', 13, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'yoga_activation_scan', 14, 'machine_band', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'standing_predictions_read', 15, 'machine_band', '{"domain":"progeny"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'lel_retrodiction', 16, 'machine_band', '{"domain":"progeny"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'contradiction_scan', 17, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'tail_divergence_read', 18, 'machine_band', '{"domain":"progeny"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'mechanism_read', 19, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'statistical_context', 20, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'divisional_facts', 40, 'acharya_floor', '{"varga":"D1"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'divisional_facts', 41, 'acharya_floor', '{"varga":"D9"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'ashtakavarga_scan', 42, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'special_lagna_read', 43, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'argala_read', 44, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'dispositor_closure_read', 45, 'acharya_floor', '{}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('progeny_deepdive', 'cross_ayanamsha_variation', 46, 'acharya_floor', '{"point":"JUPITER"}'::JSONB, false);

COMMIT;
