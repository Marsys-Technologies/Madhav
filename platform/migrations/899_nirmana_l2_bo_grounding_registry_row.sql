-- 899_nirmana_l2_bo_grounding_registry_row.sql
--
-- NIRMANA v2.1 -- L2 (Bodha). Registers bo_grounding in asset_registry: the
-- third of the three sequenced steps ruled on adjudication #2258 (schema =
-- migration 897; writer = PR #2379; registry/orchestrator wiring = this).
--
-- D-NATIVE-11 (native-ruled 2026-09-07, relayed on #2258): bo_grounding is a
-- SUPPORTING infrastructure writer, NOT a 129th elevation-denominator asset.
-- It registers here (and via @register in the sidecar) so the orchestrator
-- runs it in dependency order and dependents can see it; it is deliberately
-- absent from the frozen 128-asset elevation manifest, produces no terminal
-- capsule, and its correctness is verified as part of the grounding of the
-- assets it serves. The receipt spine accommodates this via SUPPORTING_WRITERS
-- (scripts/generate/nirmana_analysis_layer_pins.py + nirmana-analysis-receipts.ts).
--
-- Volume: one grounding row per fired ga_yoga_firings row + one per
-- bodha_msr_signals row (v1 target_kinds per #2258 ruling (a)), each carrying
-- its source row's own (chart_id, ayanamsha_id). Rehearsed live on the
-- canonical chart 2026-09-07: 63 + 50,104 = 50,167 (PR #2379's own recorded
-- rehearsal, cross-checked twice against independent query paths).
--
-- Integrity check (D-CND-01: no bare count -- every clause is a named
-- invariant that fails on corruption a count cannot see):
--   1. tier vocabulary (redundant with the CHECK constraint, kept so the
--      registry contract stands alone);
--   2. sruti rows carry their earning rule (matched_rule_id) -- a sruti row
--      without evidence is a fabricated citation (D-GROUNDING hard floor);
--   3. no orphan matches: every row resolves to its source row, same chart
--      AND same ayanamsha, per target_kind (polymorphic target_id has no FK
--      by design -- migration 897 -- so this is the detector for it);
--   4+5. completeness where built (guarded per chart_id so an unbuilt chart
--      stays vacuous-green, a PARTIAL build fails): every fired firing and
--      every msr signal of a built chart has EXACTLY ONE match row.
--
-- target_floor = 0 (§N.4: floors are achieved counts, never aspirations --
-- the asset has not been built; the floor is raised to the achieved count
-- after its first verified build).

INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
  storage_type, target_table, count_sql, target_floor,
  expected_volume_formula, expected_volume_inputs, volume_explanation,
  depends_on, scope, is_active, estimated_seconds,
  asset_type, layer_name, layer_index, asset_kind,
  has_writer, writer_timeout_seconds, domain, rung,
  catalog_status, has_substeps, natural_key_partition,
  integrity_check_sql
) VALUES (
  'bo_grounding', 'bodha', 25, 'sruti_yukti_pratyaksa', 'Grounding Tier Matches',
  'D-GROUNDING tier assignment (sruti/yukti/pratyaksa) per D-NATIVE-09: deterministic detector order, first-earned tier wins, evidence stored per row. v1 targets: fired ga_yoga_firings + bodha_msr_signals. SUPPORTING writer per D-NATIVE-11 -- not an elevation-denominator asset.',
  'postgres_table', 'bodha_grounding_matches',
  'SELECT count(*) FROM bodha_grounding_matches WHERE chart_id = $1',
  0,
  'FIRED_YOGA_FIRINGS + MSR_SIGNALS',
  jsonb_build_object(
    'FIRED_YOGA_FIRINGS', 'live count: ga_yoga_firings WHERE fired, per chart (all ayanamshas)',
    'MSR_SIGNALS', 'live count: bodha_msr_signals, per chart (all ayanamshas)',
    'rehearsed_canonical', 50167,
    'rehearsed_breakdown', '63 fired firings + 50,104 msr signals, 2026-09-07, PR #2379 rehearsal',
    'contract_ref', 'platform/python-sidecar/pipeline/orchestrator/writers/bo_grounding.py'
  ),
  'One grounding row per fired ga_yoga_firings row plus one per bodha_msr_signals row (v1 target_kinds, #2258 ruling (a)); both sources are already per-(chart, ayanamsha), so the expected volume is their live per-chart sum at build time -- a derived expectation, not a pinned equality (D-CND-01).',
  ARRAY['ga_yoga','bo_laksana'], 'per_chart', true, 120,
  'data', 'Bodha', 'L2', 'data',
  true, 600, 'chart', 'R2',
  'DRAFT', false, NULL,
  $ICHECK$
SELECT
  NOT EXISTS (
    SELECT 1 FROM bodha_grounding_matches
    WHERE grounding_tier NOT IN ('sruti','yukti','pratyaksa')
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_grounding_matches
    WHERE grounding_tier = 'sruti' AND matched_rule_id IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_grounding_matches g
    WHERE g.target_kind NOT IN ('msr_signal','yoga_dosha_firing')
       OR (g.target_kind = 'msr_signal' AND NOT EXISTS (
             SELECT 1 FROM bodha_msr_signals s
             WHERE s.signal_id::text = g.target_id
               AND s.chart_id = g.chart_id AND s.ayanamsha_id = g.ayanamsha_id))
       OR (g.target_kind = 'yoga_dosha_firing' AND NOT EXISTS (
             SELECT 1 FROM ga_yoga_firings f
             WHERE f.id::text = g.target_id
               AND f.chart_id = g.chart_id AND f.ayanamsha_id = g.ayanamsha_id))
  )
  AND NOT EXISTS (
    SELECT 1 FROM ga_yoga_firings f
    WHERE f.fired
      AND f.chart_id IN (SELECT DISTINCT chart_id FROM bodha_grounding_matches)
      AND (SELECT count(*) FROM bodha_grounding_matches g
            WHERE g.target_kind = 'yoga_dosha_firing' AND g.target_id = f.id::text
              AND g.chart_id = f.chart_id AND g.ayanamsha_id = f.ayanamsha_id) <> 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals s
    WHERE s.chart_id IN (SELECT DISTINCT chart_id FROM bodha_grounding_matches)
      AND (SELECT count(*) FROM bodha_grounding_matches g
            WHERE g.target_kind = 'msr_signal' AND g.target_id = s.signal_id::text
              AND g.chart_id = s.chart_id AND g.ayanamsha_id = s.ayanamsha_id) <> 1
  )
$ICHECK$
)
ON CONFLICT (asset_id) DO UPDATE SET
  layer = EXCLUDED.layer,
  sort_order = EXCLUDED.sort_order,
  sanskrit_name = EXCLUDED.sanskrit_name,
  english_name = EXCLUDED.english_name,
  english_description = EXCLUDED.english_description,
  storage_type = EXCLUDED.storage_type,
  target_table = EXCLUDED.target_table,
  count_sql = EXCLUDED.count_sql,
  expected_volume_formula = EXCLUDED.expected_volume_formula,
  expected_volume_inputs = EXCLUDED.expected_volume_inputs,
  volume_explanation = EXCLUDED.volume_explanation,
  depends_on = EXCLUDED.depends_on,
  scope = EXCLUDED.scope,
  is_active = EXCLUDED.is_active,
  asset_type = EXCLUDED.asset_type,
  layer_name = EXCLUDED.layer_name,
  layer_index = EXCLUDED.layer_index,
  asset_kind = EXCLUDED.asset_kind,
  has_writer = EXCLUDED.has_writer,
  writer_timeout_seconds = EXCLUDED.writer_timeout_seconds,
  domain = EXCLUDED.domain,
  rung = EXCLUDED.rung,
  catalog_status = EXCLUDED.catalog_status,
  has_substeps = EXCLUDED.has_substeps,
  integrity_check_sql = EXCLUDED.integrity_check_sql;
