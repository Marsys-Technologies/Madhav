-- M0-T20 — asset_registry.has_substeps repair. Authorized by DECISIONS.jsonl D-24 (G9).
-- Truth source: independent AST re-derivation of @register'd WriterBase subclasses
--   (00_ARCHITECTURE/control/snapshots/<ts>_has_substeps/independent_ast_derivation.py),
--   rule: HEAVY iff the class OVERRIDES BOTH plan_substeps AND run_substep, excluding
--   WriterBase's own defaults. Measured: 12 false negatives, 0 false positives.
-- Touches the has_substeps column ONLY. No DDL. No other table. No build dispatched.
BEGIN;

UPDATE asset_registry SET has_substeps = true
WHERE asset_id IN (
  'bg_muhurta_lattice',   -- writers/bg_muhurta_lattice.py:530   BgMuhurtaLatticeWriter
  'bo_laksana',           -- writers/bo_laksana.py:2975          BoLaksanaWriter
  'bo_samskara',          -- writers/bo_samskara.py:190          BoSamskaraWriter
  'ga_ayurdaya',          -- writers/ga_ayurdaya.py:22           GaAyurdayaWriter
  'ga_nakshatra',         -- writers/ga_nakshatra.py:389         NakshatraWriter
  'ga_sensitive',         -- writers/ga_sensitive.py:14          GaSensitiveWriter
  'ga_sensitive_degree',  -- writers/ga_sensitive_degree.py:22   GaSensitiveDegreeWriter
  'ga_structural',        -- writers/ga_structural.py:12         GaStructuralWriter
  'ka_sangam',            -- writers/ka_sangam.py:225            KaSangamWriter
  'mi_darshana',          -- writers/mi_darshana.py:170          MiDarshanaWriter
  'mi_pariksha',          -- writers/mi_pariksha.py:91           MiParikshaWriter
  'mi_pramana'            -- writers/mi_pramana.py:250           MiPramanaWriter
) AND has_substeps IS DISTINCT FROM true;
-- EXPECTED: UPDATE 12  (rollback and stop if it is any other number)

-- bg_reference and bo_laksana_rerank are DELIBERATELY ABSENT: the plan's figure of 14
-- includes them; the source refutes both (bg_reference is a 51-line LIGHT writer with no
-- plan_substeps at all; bo_laksana_rerank shares writers/bo_laksana.py with the HEAVY
-- BoLaksanaWriter and is itself LIGHT). Adding them to reach 14 would be H6.

COMMIT;
