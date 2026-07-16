-- Migration 451: register bo_arudha (Jaimini Arudha MSR class, CR-61, D-2 Lane V-5)
-- Created: 2026-07-16
--
-- bo_arudha is a new L2 Bodha writer: pure derivation over existing L1
-- arudha_pada / graha_position facts (no new astronomical compute). Emits
-- one `arudha` bodha_msr_signals row per: AL-bhava relation (always),
-- AL-conjunction per graha sharing AL's house (chart-dependent), and A2/A11
-- (dhana/labha arudha) tenancy (always, one row each).
--
-- Target: on chart 482012f1 (lahiri) this is 1 (AL relation) + 2 (Jupiter
-- and Venus both conjunct AL in H9) + 2 (A2/A11 tenancy) = 5 per ayanamsha;
-- conservative floor of 3/ayanamsha x 5 ayanamshas = 15 (aspirational per
-- CLAUDE.md §N.4 — floors are never a gate, the achieved count post-build
-- is what stands; AL-conjunction count varies per ayanamsha).
--
-- Depends on ga_structural (arudha_pada facts) and ga_positions (graha
-- house placements).
--
-- Salience: class_prior=1.10, subsystem='jaimini' — ratified DIS.019/DR-6.
--
-- Idempotent: ON CONFLICT DO UPDATE, safe to re-apply.

BEGIN;

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name,
  english_description, storage_type, target_table, count_sql,
  target_floor, depends_on, scope, has_writer, created_at
) VALUES (
  'bo_arudha', 'bodha', 21,
  'arudha_pada', 'Jaimini Arudha (Perception Layer)',
  'Arudha Lagna bhava-relation, AL conjunctions, and A2/A11 (dhana/labha arudha) tenancy — pure L2 derivation over existing ga_structural/ga_positions facts; emits arudha MSR signals',
  'postgres_table', 'bodha_msr_signals',
  'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1 AND signal_type_class = ''arudha''',
  15, ARRAY['ga_structural', 'ga_positions'], 'per_chart', true, NOW()
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
