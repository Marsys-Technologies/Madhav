-- Migration 453: register bo_vargottama_dhana (Vargottama amplification + Dhana-axis MSR classes, CR-36, D-2 Lane V-5)
-- Created: 2026-07-16
--
-- bo_vargottama_dhana is a new L2 Bodha writer: pure derivation over
-- existing L1 vargottama_per_varga / graha_position facts (no new
-- astronomical compute). Emits TWO signal_type_classes into the shared
-- bodha_msr_signals table:
--   - vargottama_amplification: one row per graha confirmed vargottama in
--     D9 (fires only when true — an amplification class never emits a
--     vacuous non-event).
--   - dhana_axis: one row per dhana-axis house (2nd, 11th) — occupant
--     grahas + classical sign-lord placement. Always 2 rows/ayanamsha
--     (houses always exist), independent of whether either is tenanted.
--
-- Target: dhana_axis guarantees 2 rows/ayanamsha x 5 = 10 deterministically;
-- vargottama_amplification is chart-dependent (>=1 confirmed on 482012f1
-- lahiri: Mercury). Conservative combined floor = 10 (aspirational per
-- CLAUDE.md §N.4 — never fabricated to hit a number).
--
-- Depends on ga_vargas (vargottama_per_varga facts) and ga_positions
-- (graha/Lagna house+sign facts).
--
-- Salience: vargottama_amplification class_prior=1.15, dhana_axis
-- class_prior=1.05 — both ratified DIS.019/DR-6.
--
-- Idempotent: ON CONFLICT DO UPDATE, safe to re-apply.

BEGIN;

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, target_table, count_sql,
  target_floor, depends_on, scope, has_writer, created_at
) VALUES (
  'bo_vargottama_dhana', 'bodha', 23,
  'vargottama_dhana_aksa', 'Vargottama Amplification + Dhana Axis',
  'Cross-frame (D1/D9) vargottama confirmation and complete 2nd/11th-house (dhana/labha) tenancy analysis — pure L2 derivation over existing ga_vargas/ga_positions facts; emits vargottama_amplification + dhana_axis MSR signals',
  'postgres_table', 'bodha_msr_signals',
  'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = ANY(ARRAY[''vargottama_amplification'', ''dhana_axis''])',
  10, ARRAY['ga_vargas', 'ga_positions'], 'per_chart', true, NOW()
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
