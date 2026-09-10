-- 764_bo_cgm_paths_volume_formula.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; F-L2-14 -- expected_volume_formula gap).
-- Transaction ownership belongs to platform/scripts/migrate.ts. Fourth
-- migration of L2's 760-779 range after #2021 (760), #2039 (761), #2041
-- (762), #2044 (763).
--
-- bo_cgm_paths (writers/bo_cgm_paths.py) emits exactly one dispositor-chain
-- row per (graha x ayanamsha) -- GRAHAS=9 x AYANAMSHAS=5 = 45 rows/chart.
-- This is a genuine FIXED TILING, not merely a bound, traced to two
-- unconditional code guarantees:
--
--   1. bo_karanajala's _build_dispositor_edges() iterates every graha in
--      graha_signs (always all 9 for a complete chart) and emits a
--      dispositor edge UNLESS the graha is self-ruling (skipped as "no
--      self-loops", :633-634) -- so every NON-self-ruling graha has
--      exactly one outgoing dispositor edge, and that edge's target is
--      never itself (self-ruling grahas are excluded from emitting one).
--   2. bo_cgm_paths' _build_dispositor_chains() handles the two cases
--      completely: a self-ruling graha emits its own 0-hop row directly
--      via _is_self_ruling() (independent of edges, :173-183); a
--      non-self-ruling graha is GUARANTEED at least one dispositor edge
--      by (1), so its while-loop's first iteration always finds a
--      dispos_edges entry, always advances past depth=0, and always
--      satisfies "len(node_chain) > 1" (:223) -- the only gate for
--      emitting a row. There is no code path where a graha produces zero
--      rows for a complete chart.
--
-- Verified live against all three production charts before landing (C12):
-- all three measure exactly 45 rows (9 x 5), no exceptions -- matching
-- the code guarantee exactly, not coincidentally.

UPDATE asset_registry
   SET expected_volume_formula = 'GRAHAS * AYANAMSHAS',
       expected_volume_inputs = jsonb_build_object(
         'GRAHAS', 9,
         'AYANAMSHAS', 5,
         'grahas_meaning', 'SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN',
         'guarantee', 'every non-self-ruling graha has exactly one outgoing dispositor edge (bo_karanajala._build_dispositor_edges, no self-loops), guaranteeing >=1 hop; every self-ruling graha emits its own 0-hop row directly via _is_self_ruling(). No code path yields zero rows for a graha on a complete chart.',
         'measured', 45,
         'measured_on_charts', jsonb_build_array(
           '482012f1-710e-4a25-994a-93821f5871aa',
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
           'cb73cd3d-9eba-4220-9902-0de91566e980'
         ),
         'contract_ref', 'platform/python-sidecar/pipeline/orchestrator/writers/bo_cgm_paths.py:148-237; bo_karanajala.py:611-681'
       ),
       volume_explanation = '9 grahas x 5 ayanamshas = 45 dispositor-chain rows per chart, '
         || 'exactly one per graha per ayanamsha. Unlike bo_cgm_motifs (genuinely unbounded '
         || 'structural-pattern counts, left NULL), this asset''s per-item cardinality is '
         || 'code-guaranteed: bo_karanajala never skips a non-self-ruling graha''s dispositor '
         || 'edge, and bo_cgm_paths'' self-ruling branch fires unconditionally for the rest -- '
         || 'a count below 45 means an upstream node/edge is missing for a graha; a count above '
         || 'is impossible given the writer''s one-chain-per-graha loop.'
 WHERE asset_id = 'bo_cgm_paths';
