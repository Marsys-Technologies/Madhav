-- 760_bo_upaya_volume_formula.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; F-L2-14 -- expected_volume_formula gap).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- First migration of L2's new 760-779 range (ruled #2005; 710-729 exhausted
-- at migration 729). Continues the F-L2-14 sweep -- eighth asset, same
-- fixed-tiling shape as bo_sudarshana/bo_special_lagna/bo_nakshatra_semantic.
--
-- bo_upaya.py writes one bodha_rm_resonances row per (graha x ayanamsha) --
-- KNOWN_GRAHAS has exactly 9 entries -- GRAHAS=9 x AYANAMSHAS=5 = 45
-- rows/chart. The writer's own loop (line 485, `for graha in KNOWN_GRAHAS`)
-- has internal `continue`/early-return branches on missing L1 facts, but
-- these have never manifested in production: measured live across all
-- three production charts, every one of the 15 (chart_id, ayanamsha_id)
-- combinations is exactly 9, no exceptions. This asset's own M-14 check
-- already encodes the same expectation as a hard natural-key distinctness
-- guard (GROUP BY chart_id, ayanamsha_id, graha HAVING count(*) > 1) --
-- this migration adds the tiling COUNT that guard implies but does not by
-- itself assert.
--
-- Scope note: bo_upaya also writes bodha_rm_remedy_prescriptions (1-3 rows
-- per resonance, already bounded by this asset's own M-14 check's
-- max-3-per-resonance guard) via a SEPARATE registered asset
-- (bo_upaya's "4 RM sibling rollup tables" PR, #1920, still in flight) --
-- out of scope for this migration, which covers only the registered
-- target_table (bodha_rm_resonances).

UPDATE asset_registry
   SET expected_volume_formula = 'GRAHAS * AYANAMSHAS',
       expected_volume_inputs = jsonb_build_object(
         'GRAHAS', 9,
         'AYANAMSHAS', 5,
         'grahas_meaning', 'Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu (bo_upaya.py KNOWN_GRAHAS)',
         'conditional_on', 'each row requires the graha''s own L1 shadbala/bhava_bala facts (bo_upaya.py resonance algorithm); none has ever been missing in production',
         'measured', 45,
         'measured_on_charts', jsonb_build_array(
           '482012f1-710e-4a25-994a-93821f5871aa',
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
           'cb73cd3d-9eba-4220-9902-0de91566e980'
         ),
         'contract_ref', 'platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py:44-51,485'
       ),
       volume_explanation = '9 grahas x 5 ayanamshas = 45 resonance rows per chart. Each row is '
         || 'technically conditional on the graha''s own L1 strength facts, but none has ever been '
         || 'missing in production, and the asset''s own M-14 check already enforces a hard '
         || 'natural-key distinctness guard on (chart_id, ayanamsha_id, graha) -- this migration '
         || 'adds the tiling count that guard implies. A count below 45 means an L1 fact is '
         || 'missing for that chart; a count above is impossible given the writer''s fixed '
         || '9-graha loop. Scope is `bodha_rm_resonances` only -- the sibling '
         || '`bodha_rm_remedy_prescriptions` table belongs to a separately-registered asset.'
 WHERE asset_id = 'bo_upaya';
