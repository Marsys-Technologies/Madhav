-- 725_bo_sudarshana_volume_formula.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; F-L2-14 -- expected_volume_formula gap).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Third asset in the F-L2-14 sweep (660_nirmana_l2_registry_accuracy.sql
-- fixed six; 723_bo_arudha_volume_formula.sql and
-- 724_bo_special_lagna_volume_formula.sql added two more this campaign).
--
-- bodha_writers/sudarshana_emitter.py emits exactly one 'sudarshana_agreement'
-- signal per (graha x ayanamsha) -- GRAHAS=9 x AYANAMSHAS=5 = 45 rows/chart.
-- The writer (bo_sudarshana.py:105-157) skips an entire ayanamsha if its
-- Lagna/Moon/Sun sign facts are missing, and skips an individual graha if
-- its own position fact is missing -- technically conditional, same shape
-- as bo_special_lagna's tiling -- but these are foundational L1 facts that
-- exist for any chart that has completed L1 at all, so in practice this is
-- a real tiling. This asset's own M-14 check (667_bo_sudarshana_integrity_
-- check.sql) already treats it as a hard invariant (HAVING count(*) != 9
-- per chart x ayanamsha fails outright, not a soft bound) -- this migration
-- restates that same claim at the registry level.
--
-- Measured live across all three production charts before landing (C12:
-- never a formula that has yet to be checked against real data): all three
-- charts measure exactly 45 rows (9 x 5), no exceptions.

UPDATE asset_registry
   SET expected_volume_formula = 'GRAHAS * AYANAMSHAS',
       expected_volume_inputs = jsonb_build_object(
         'GRAHAS', 9,
         'AYANAMSHAS', 5,
         'grahas_meaning', 'SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN',
         'conditional_on', 'each row requires the graha''s own L1 position fact plus Lagna/Moon/Sun sign facts for that ayanamsha (sudarshana_emitter.py + bo_sudarshana.py:105-157); none has ever been missing in production',
         'measured', 45,
         'measured_on_charts', jsonb_build_array(
           '482012f1-710e-4a25-994a-93821f5871aa',
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
           'cb73cd3d-9eba-4220-9902-0de91566e980'
         ),
         'contract_ref', 'platform/python-sidecar/bodha_writers/sudarshana_emitter.py:57,198-260'
       ),
       volume_explanation = '9 grahas x 5 ayanamshas = 45 signals per chart, one per graha''s '
         || 'tri-frame (Lagna/Chandra/Surya) Sudarshana result. Each row is technically '
         || 'conditional on foundational L1 position/sign facts, but none has ever been missing '
         || 'in production, and the asset''s own M-14 check '
         || '(667_bo_sudarshana_integrity_check.sql) already fails HARD on any count != 9 per '
         || 'chart x ayanamsha, not a soft bound. A count below 45 means an L1 position or sign '
         || 'fact is missing for that chart; a count above is impossible given the writer''s '
         || 'fixed 9-graha loop.'
 WHERE asset_id = 'bo_sudarshana';
