-- 723_bo_arudha_volume_formula.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; F-L2-14 -- expected_volume_formula gap).
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- 660_nirmana_l2_registry_accuracy.sql gave six assets a real
-- expected_volume_formula and deliberately left bo_bimba/bo_karanajala NULL
-- (their true volume needs an L2-W5 rebuild to derive). bo_arudha was left
-- untouched by that migration -- not addressed either way. Per
-- 710_bo_arudha_integrity_check.sql's own analysis
-- (bodha_writers/arudha_emitter.py), bo_arudha's row count per
-- (chart_id, ayanamsha_id) is NOT a fixed tiling like bo_drishti's: it is
--   FIXED_ROWS_PER_AYANAMSHA (3: one AL_bhava_relation + two ARUDHA_A{2,11}
--   tenancy rows, unconditional once the AL fact exists)
--   + a genuinely data-dependent AL_conjunction count in [0, GRAHA_COUNT=9]
--     (one row per graha actually sharing AL's house that build).
--
-- Rather than force a false point estimate (C12: a WRONG formula is worse
-- than a NULL one), this expresses the real, independently-verifiable BOUND:
-- per-ayanamsha rows fall in [3, 12], so per-chart rows (5 ayanamshas) fall
-- in [15, 60]. This is the same invariant class 710's own integrity check
-- already enforces (invariant #3: conjunction count <= 9) -- not a new
-- claim, a registry-level restatement of it.
--
-- Measured live across all three production charts before landing (C12:
-- never a formula that has yet to be checked against real data):
--   482012f1-... (canonical): 5 rows/ayanamsha x 5 ayanamshas = 25 (2 conjunctions/ayanamsha)
--   1c826d5a-...            : 4-5 rows/ayanamsha (24 total; one ayanamsha at 1 conjunction)
--   cb73cd3d-...            : 4 rows/ayanamsha x 5 ayanamshas = 20 (1 conjunction/ayanamsha)
-- All three fall inside the [15, 60] bound; none has hit either edge, which
-- is expected -- 0 or 9 simultaneous AL conjunctions is a rare chart, not a
-- build defect indicator on its own.

UPDATE asset_registry
   SET expected_volume_formula =
         'AYANAMSHAS * FIXED_ROWS_PER_AYANAMSHA <= ROWS <= AYANAMSHAS * (FIXED_ROWS_PER_AYANAMSHA + GRAHA_COUNT)',
       expected_volume_inputs = jsonb_build_object(
         'AYANAMSHAS', 5,
         'FIXED_ROWS_PER_AYANAMSHA', 3,
         'GRAHA_COUNT', 9,
         'fixed_rows_meaning', 'arudha:AL_bhava_relation (1) + arudha:ARUDHA_A2_tenancy + arudha:ARUDHA_A11_tenancy (2), unconditional once AL exists',
         'variable_rows_meaning', 'arudha:AL_conjunction:<GRAHA> -- one per graha actually sharing AL''s house, data-dependent',
         'bound_per_chart', jsonb_build_object('min', 15, 'max', 60),
         'measured_rows_by_chart', jsonb_build_object(
           '482012f1-710e-4a25-994a-93821f5871aa', 25,
           '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 24,
           'cb73cd3d-9eba-4220-9902-0de91566e980', 20
         ),
         'contract_ref', 'platform/python-sidecar/bodha_writers/arudha_emitter.py:214-310'
       ),
       volume_explanation = 'Not a fixed tiling like bo_drishti''s: 3 rows per ayanamsha are '
         || 'unconditional (AL_bhava_relation + two ARUDHA_A{2,11}_tenancy rows), and 0-9 more '
         || 'depend on how many of the 9 grahas actually conjunct the Arudha Lagna''s house that '
         || 'build -- genuine chart data, not a build defect. Expressed as the real bound this '
         || 'implies ([15, 60] per chart) rather than a guessed point estimate, matching the '
         || 'conjunction-count <= 9 invariant 710_bo_arudha_integrity_check.sql already enforces. '
         || 'A count outside the bound is unambiguously a defect; a count inside it is merely '
         || 'unverified without also checking the fixed-row tiling (which the integrity check does).'
 WHERE asset_id = 'bo_arudha';
