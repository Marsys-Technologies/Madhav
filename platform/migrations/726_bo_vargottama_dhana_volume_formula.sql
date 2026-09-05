-- 726_bo_vargottama_dhana_volume_formula.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; F-L2-14 -- expected_volume_formula gap).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Fourth asset in the F-L2-14 sweep (660_nirmana_l2_registry_accuracy.sql
-- fixed six; 723/724/725 added bo_arudha, bo_special_lagna, bo_sudarshana
-- this campaign). Second bound-style (not point-estimate) formula after
-- bo_arudha, for the same reason: one of this asset's two signal classes
-- is genuinely data-dependent.
--
-- bodha_writers/vargottama_dhana_emitter.py emits TWO signal_type_classes
-- from one writer (bo_vargottama_dhana.py), sharing this asset's row:
--   - 'dhana_axis': exactly TWO rows per (chart_id, ayanamsha_id) -- one
--     per house (2nd, 11th), unconditional (docstring: "One row per house
--     (2 rows minimum per ayanamsha)"). Confirmed live: 10/10/10 = 2 x 5
--     ayanamshas on all three production charts, no exceptions.
--   - 'vargottama_amplification': ZERO to NINE rows per (chart_id,
--     ayanamsha_id) -- fires ONLY when a graha IS vargottama in D9
--     (docstring: "fires ONLY when true — an amplification signal that
--     never amplifies is not a signal"), genuinely chart-data-dependent,
--     GRAHAS=9 the hard ceiling. This asset's own M-14 check
--     (bo_vargottama_dhana's integrity_check_sql) already enforces this as
--     a hard bound (HAVING count(*) > 9 fails), and in fact one live
--     ayanamsha (chart 482012f1, surya_siddhanta_classical) has ZERO
--     vargottama_amplification rows -- proving the lower bound of 0 is not
--     hypothetical, it is observed in production.
--
-- Combined per-ayanamsha bound: [2, 11] rows; per-chart (5 ayanamshas):
-- [10, 55]. Measured live across all three production charts before
-- landing (C12: never a formula that has yet to be checked against real
-- data): 16 / 14 / 15 total rows respectively -- all inside the bound, and
-- the 482012f1 case (14 = 10 dhana_axis + 4 vargottama, one ayanamsha at 0)
-- demonstrates the lower edge is real, not theoretical.

UPDATE asset_registry
   SET expected_volume_formula =
         'AYANAMSHAS * DHANA_AXIS_FIXED <= ROWS <= AYANAMSHAS * (DHANA_AXIS_FIXED + GRAHA_COUNT)',
       expected_volume_inputs = jsonb_build_object(
         'AYANAMSHAS', 5,
         'DHANA_AXIS_FIXED', 2,
         'GRAHA_COUNT', 9,
         'dhana_axis_meaning', 'exactly 2 rows per ayanamsha (houses 2 and 11), unconditional',
         'vargottama_amplification_meaning', '0-9 rows per ayanamsha -- fires only when a graha is vargottama in D9, genuinely chart-data-dependent',
         'bound_per_chart', jsonb_build_object('min', 10, 'max', 55),
         'measured_rows_by_chart', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', 14,
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 16,
           'cb73cd3d-9eba-4220-9902-0de91566e980', 15
         ),
         'observed_zero_vargottama_ayanamsha', 'chart 482012f1, ayanamsha surya_siddhanta_classical -- confirms the lower bound is real, not hypothetical',
         'contract_ref', 'platform/python-sidecar/bodha_writers/vargottama_dhana_emitter.py:1-33'
       ),
       volume_explanation = 'Two signal classes share this asset: dhana_axis is a real fixed '
         || 'tiling (exactly 2/ayanamsha, houses 2 and 11), while vargottama_amplification fires '
         || 'only when a graha is genuinely vargottama in D9 -- 0 to 9 rows/ayanamsha, chart-data-'
         || 'dependent, not a build defect. Expressed as the real bound this implies ([10, 55] per '
         || 'chart) rather than a guessed point estimate, matching the count > 9 invariant this '
         || 'asset''s own M-14 check already enforces. The observed zero-vargottama ayanamsha '
         || '(482012f1 / surya_siddhanta_classical) confirms the lower edge is a real production '
         || 'case, not a theoretical floor nobody has seen.'
 WHERE asset_id = 'bo_vargottama_dhana';
