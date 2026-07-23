-- Migration 463: Vidhi registry seed — VIDHI-PŪRṆATĀ Opus-Gate follow-up (2 deltas)
-- Created: 2026-07-23
--
-- Follows migration 462 (VIDHI-PŪRṆATĀ base seed). The independent Opus Gate returned FAIL on
-- exactly two issues; this migration carries the DB-seed ("third copy") side of the two
-- canonical-registry fixes into lockstep with platform/src/lib/vidhi/registry_data.ts:
--
--   FAIL-1 (F9 reconciled) — dhana_yoga_scan.known_gap: 'CR-56' → NULL. The house-lord
--     dhana/raja yoga family IS confirmed firing live via ganita_yoga_firings_get
--     (dhana_yoga_house_lords), verified by P-0's probe AND the yoga_firings_read primitive
--     (same underlying tool, known_gap NULL). CR-56 is now CLOSED (stale register drift); the
--     registry-completeness test asserts no primitive cites a CLOSED CR, so the column must
--     flip to NULL here too. Same stale-correction precedent as CR-54 / CR-59.
--
--   FAIL-2 (F4 health floor Moon) — health_deepdive gains karaka_condition{karaka:moon}
--     (mind / mental-health kāraka) at order 20, per STATIC_VIDHI_AUDIT_v1_0.md F4 + brief §2
--     P-3's health floor. Moon is data-backed (the karaka_condition primitive already routes
--     mars/saturn/jupiter live in this floor). The machine band + elevation tail renumber by
--     +1 (dasha_spine → 21 … statistical_context → 32); the whole health floor is therefore
--     re-seeded via the per-intent DELETE-then-INSERT (natural key = intent), matching 462.
--
-- §N.3 idempotency (mirrors migration 462 + the Python writers exactly):
--   • vidhi_primitives   → ON CONFLICT (primitive_id) DO UPDATE  (L0 global upsert).
--   • vidhi_floor_items  → per-intent DELETE-then-INSERT (a floor edit re-numbers item_order,
--     so wholesale replace of the health_deepdive floor avoids orphaned rows).
-- Re-runnable: applying twice is a no-op beyond updated_at.
--
-- This migration is DATA-ONLY on Vidhi-owned tables. It does NOT touch the FROZEN
-- orchestrator/WriterBase, any L1–L5 writer/table, or any calibration table. The hard_floor
-- column already exists (added additively by migration 462).
--
-- ROLLBACK (manual):
--   BEGIN;
--   -- Restore dhana_yoga_scan.known_gap = 'CR-56' and re-run migration 462's health_deepdive
--   -- floor block (orders 1..31, no Moon item).
--   COMMIT;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── FAIL-1 — vidhi_primitives: flip dhana_yoga_scan.known_gap to NULL (CR-56 reconciled) ──
INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('dhana_yoga_scan', 1, 'Scans the house-lord yoga family for the domain (dhana / raja / Budha-Āditya / Sarasvatī / Lakṣmī).', 'doctrine', 'ganita_yoga_firings_get', '{"chart_id":"{chart_id}","domain":"{domain}","family":"house_lord"}'::JSONB,
        'ganita_yogas_get', NULL, ARRAY[]::TEXT[], ARRAY['CR-27c']::TEXT[], now())
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

-- ── FAIL-2 — vidhi_floor_items: re-seed health_deepdive with the Moon karaka item (order 20) ──
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
-- FAIL-2: the new Moon (mind / mental-health) kāraka floor item — data-backed, known_gap NULL.
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
VALUES ('health_deepdive', 'standing_predictions_read', 27, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'lel_retrodiction', 28, 'machine_band', '{"domain":"health"}'::JSONB, false);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'contradiction_scan', 29, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'tail_divergence_read', 30, 'machine_band', '{"domain":"health"}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'mechanism_read', 31, 'machine_band', '{}'::JSONB, true);
INSERT INTO vidhi_floor_items (intent, primitive_id, item_order, band, args_override, hard_floor)
VALUES ('health_deepdive', 'statistical_context', 32, 'machine_band', '{}'::JSONB, true);

COMMIT;
