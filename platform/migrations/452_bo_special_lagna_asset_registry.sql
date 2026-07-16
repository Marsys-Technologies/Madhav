-- Migration 452: register bo_special_lagna (special-lagna domain-salience MSR class, CR-76, D-2 Lane V-5)
-- Created: 2026-07-16
--
-- bo_special_lagna is a new L2 Bodha writer: pure derivation over existing
-- L1 special_lagna facts (no new astronomical compute). Emits one
-- `special_lagna` bodha_msr_signals row per (Indu/Sree/Ghati/Hora Lagna x
-- ayanamsha), each carrying domain_salience so it ranks correctly WITHIN
-- its classically-assigned domain despite the chart-wide 0.90 class-prior
-- discount (DIS.019/DR-6).
--
-- Target: 4 lagnas x 5 canonical ayanamshas = 20 signals once fully built.
-- Depends on ga_sensitive (special_lagna facts).
--
-- Salience: class_prior=0.90, subsystem='special_lagna' — ratified DIS.019/DR-6.
--
-- Idempotent: ON CONFLICT DO UPDATE, safe to re-apply.

BEGIN;

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, target_table, count_sql,
  target_floor, depends_on, scope, has_writer, created_at
) VALUES (
  'bo_special_lagna', 'bodha', 22,
  'visesha_lagna', 'Special Lagna (Indu/Sree/Ghati/Hora)',
  'Domain-scoped corroboration from the four canonical special/upapada lagnas (Indu, Sree, Ghati, Hora) — pure L2 derivation over existing ga_sensitive facts; emits special_lagna MSR signals with per-signal domain_salience',
  'postgres_table', 'bodha_msr_signals',
  'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = ''special_lagna''',
  20, ARRAY['ga_sensitive'], 'per_chart', true, NOW()
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
