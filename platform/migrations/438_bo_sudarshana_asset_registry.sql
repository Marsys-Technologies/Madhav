-- Migration 438: register bo_sudarshana (Sudarśana Chakra, CR-100, D-1.5b Lane B-3)
-- Created: 2026-07-15
--
-- bo_sudarshana is a new L2 Bodha writer: pure derivation over existing L1
-- graha_position sign facts (no new astronomical compute). For each of the 9
-- grahas it computes the tri-frame house assignment (house-from-Lagna,
-- house-from-Chandra, house-from-Sūrya) and emits one bodha_msr_signals row
-- per (graha x ayanamsha) in the new `sudarshana_agreement` signal class
-- (DIS.016 / DR-3 ratified: class_prior=1.15, subsystem=structural).
--
-- Target: 9 grahas x 5 canonical ayanamshas = 45 signals once fully built.
-- Depends only on ga_positions (the sole L1 fact source it reads).
--
-- Idempotent: ON CONFLICT DO UPDATE, safe to re-apply.

BEGIN;

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, target_table, count_sql,
  target_floor, depends_on, scope, has_writer, created_at
) VALUES (
  'bo_sudarshana', 'bodha', 19,
  'sudarshana_chakra', 'Sudarśana Chakra',
  'Tri-frame (Lagna/Chandra/Sūrya) house assignment per graha — pure L2 derivation over existing ga_positions facts; emits sudarshana_agreement MSR signals (confirmed-in-3-frames amplifies, contradicted flags)',
  'postgres_table', 'bodha_msr_signals',
  'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = ''sudarshana_agreement''',
  45, ARRAY['ga_positions'], 'per_chart', true, NOW()
)
ON CONFLICT (asset_id) DO UPDATE SET
  layer                = EXCLUDED.layer,
  sanskrit_name         = EXCLUDED.sanskrit_name,
  english_name          = EXCLUDED.english_name,
  english_description   = EXCLUDED.english_description,
  storage_type          = EXCLUDED.storage_type,
  target_table          = EXCLUDED.target_table,
  count_sql             = EXCLUDED.count_sql,
  target_floor          = EXCLUDED.target_floor,
  depends_on            = EXCLUDED.depends_on,
  scope                 = EXCLUDED.scope,
  has_writer            = true;

COMMIT;
