-- 724_bo_special_lagna_volume_formula.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; F-L2-14 -- expected_volume_formula gap).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- 660_nirmana_l2_registry_accuracy.sql gave six assets a real
-- expected_volume_formula (bo_samskara/bo_drishti/bo_cdlm_summary/
-- bo_chart_gestalt/bo_samvada/bo_pramana_mapa) and 723 added a seventh
-- (bo_arudha, as a derived bound rather than a point estimate). This adds
-- bo_special_lagna: a straightforward fixed tiling, distinct in kind from
-- bo_arudha's genuinely data-dependent count.
--
-- bodha_writers/special_lagna_emitter.py emits exactly one 'special_lagna'
-- signal per (lagna_key x ayanamsha), for the four canonical special lagnas
-- CR-76 names (Indu/Sree/Ghati/Hora) -- LAGNAS=4, AYANAMSHAS=5. Each row is
-- technically conditional on its L1 house_d1 fact existing
-- (build_signal_row returns None otherwise, special_lagna_emitter.py:77-78)
-- -- same conditional-emission shape as bo_arudha's fixed rows -- but unlike
-- bo_arudha there is no further data-dependent branching once the lagna
-- fact exists: no variable per-row multiplier. This asset's own M-14 check
-- (668_bo_special_lagna_integrity_check.sql) already encodes this as a hard
-- tiling invariant (HAVING count(*) != 4 fails the whole check), not a soft
-- bound -- this migration restates that same claim at the registry level,
-- consistent with it rather than a second guess.
--
-- Measured live across all three production charts before landing (C12:
-- never a formula that has yet to be checked against real data): every one
-- of the 15 (chart x ayanamsha) combinations across the three charts is
-- exactly 4 -- no chart has ever hit fewer, i.e. no lagna fact has ever been
-- observed missing in production. LAGNAS * AYANAMSHAS = 20 rows/chart in
-- all three cases.

UPDATE asset_registry
   SET expected_volume_formula = 'LAGNAS * AYANAMSHAS',
       expected_volume_inputs = jsonb_build_object(
         'LAGNAS', 4,
         'AYANAMSHAS', 5,
         'lagnas_meaning', 'INDU_LAGNA, SREE_LAGNA, GHATI_LAGNA, HORA_LAGNA -- the four CR-76-named special lagnas',
         'conditional_on', 'each row requires its L1 special_lagna house_d1 fact to exist (special_lagna_emitter.py:77-78); none has ever been missing in production',
         'measured', 20,
         'measured_on_charts', jsonb_build_array(
           '482012f1-710e-4a25-994a-93821f5871aa',
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
           'cb73cd3d-9eba-4220-9902-0de91566e980'
         ),
         'contract_ref', 'platform/python-sidecar/bodha_writers/special_lagna_emitter.py:45-78'
       ),
       volume_explanation = '4 special lagnas x 5 ayanamshas = 20 signals per chart. Each row is '
         || 'technically conditional on its own L1 house_d1 fact existing, but unlike bo_arudha '
         || 'there is no further data-dependent branching once that fact exists -- so in practice '
         || 'this is a real tiling, matching the asset''s own M-14 integrity check '
         || '(668_bo_special_lagna_integrity_check.sql, which fails HARD on any count != 4 per '
         || 'chart x ayanamsha, not a soft bound). A count below 20 '
         || 'means an L1 special_lagna fact is missing for that chart; a count above is impossible '
         || 'given the writer''s fixed 4-key loop.'
 WHERE asset_id = 'bo_special_lagna';
