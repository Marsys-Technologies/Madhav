-- 729_bo_nakshatra_semantic_volume_formula.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; F-L2-14 -- expected_volume_formula gap).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Seventh and last asset in the F-L2-14 sweep under L2's 710-729 migration
-- range (this is migration 729 -- the final number in the range; a further
-- pin allocation is needed before any more L2-owned migrations can ship).
--
-- bodha_writers/nakshatra_semantic_emitter.py + bo_nakshatra_semantic.py
-- emit exactly one 'nakshatra_semantic' signal per (graha x ayanamsha) for
-- all 9 GRAHAS (bo_nakshatra_semantic.py:83, "for graha_code in GRAHAS") --
-- the docstring's "9 grahas + Lagna" describes what facts are READ (Lagna's
-- position is used as a reference input), not a separate emitted row; only
-- the 9 grahas get their own signal. GRAHAS=9 x AYANAMSHAS=5 = 45
-- rows/chart. This asset's own M-14 check already treats this as a hard
-- tiling invariant (HAVING count(*) != 9 per chart x ayanamsha fails
-- outright, not a soft bound) -- this migration restates that same claim
-- at the registry level, the same pattern as bo_sudarshana (725) and
-- bo_special_lagna (724).
--
-- Measured live across all three production charts before landing (C12:
-- never a formula that has yet to be checked against real data): all three
-- charts measure exactly 45, no exceptions.

UPDATE asset_registry
   SET expected_volume_formula = 'GRAHAS * AYANAMSHAS',
       expected_volume_inputs = jsonb_build_object(
         'GRAHAS', 9,
         'AYANAMSHAS', 5,
         'grahas_meaning', 'SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN -- Lagna is a read-only reference input, not a separate emitted row',
         'conditional_on', 'each row requires the graha''s own L1 position/nakshatra facts (bo_nakshatra_semantic.py:80-107); none has ever been missing in production',
         'measured', 45,
         'measured_on_charts', jsonb_build_array(
           '482012f1-710e-4a25-994a-93821f5871aa',
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
           'cb73cd3d-9eba-4220-9902-0de91566e980'
         ),
         'contract_ref', 'platform/python-sidecar/pipeline/orchestrator/writers/bo_nakshatra_semantic.py:80-107'
       ),
       volume_explanation = '9 grahas x 5 ayanamshas = 45 signals per chart. Each row is '
         || 'technically conditional on the graha''s own L1 position/nakshatra facts, but none has '
         || 'ever been missing in production, and the asset''s own M-14 check already fails HARD '
         || 'on any count != 9 per chart x ayanamsha, not a soft bound. A count below 45 means an '
         || 'L1 fact is missing for that chart; a count above is impossible given the writer''s '
         || 'fixed 9-graha loop.'
 WHERE asset_id = 'bo_nakshatra_semantic';
