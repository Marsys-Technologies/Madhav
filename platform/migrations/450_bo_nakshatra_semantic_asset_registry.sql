-- Migration 450: register bo_nakshatra_semantic (Nakshatra-semantic MSR class, CR-26/64, D-2 Lane V-5)
-- Created: 2026-07-16
--
-- bo_nakshatra_semantic is a new L2 Bodha writer: pure derivation over
-- existing L1 graha_position / graha_dispositor_chain / graha_tara_bala
-- facts (no new astronomical compute). For each of the 9 grahas it emits
-- one `nakshatra_semantic` bodha_msr_signals row combining own-star
-- identity, dispositor chain, tara bala, and gandanta/end-degree flagging.
--
-- Target: 9 grahas x 5 canonical ayanamshas = 45 signals once fully built.
-- Depends on ga_positions (position facts) and ga_nakshatra (dispositor
-- chain + tara bala facts).
--
-- Salience: class_prior=1.00, subsystem='nakshatra' — ratified DIS.019/DR-6.
--
-- Idempotent: ON CONFLICT DO UPDATE, safe to re-apply.

BEGIN;

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, target_table, count_sql,
  target_floor, depends_on, scope, has_writer, created_at
) VALUES (
  'bo_nakshatra_semantic', 'bodha', 20,
  'nakshatra_tattva', 'Nakshatra-Semantic Profile',
  'Own-star identity, dispositor chain, tara bala, and gandanta/end-degree flagging per graha — pure L2 derivation over existing ga_positions/ga_nakshatra facts; emits nakshatra_semantic MSR signals',
  'postgres_table', 'bodha_msr_signals',
  'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = ''nakshatra_semantic''',
  45, ARRAY['ga_positions', 'ga_nakshatra'], 'per_chart', true, NOW()
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
