-- 845_nirmana_l1_ga_ayurdaya_category_ownership_backfill.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT, sixth in the 840-859 range (adjudication #2101, L1
-- continuation 5). Closes the ownership-registry half of F-E4 (L1_W1_ANALYSIS_BATCH_E.md):
-- `fact_category='ayurdaya'` had NO row in `fact_category_ownership` (confirmed live, cycle
-- 108: 0 rows for this category) -- §N.5's own "L1 authority must be attributable" principle
-- means every category a writer emits should be traceable to its owning asset in this registry,
-- the same GA.1-class registry-disagreement pattern D-L1-105/F-C9 already fixed once for
-- ga_structural (migration 842).
--
-- Unlike ga_structural's count_sql, ga_ayurdaya's count_sql filters on `fact_category='ayurdaya'`
-- directly (not a JOIN against this table) -- so this gap is an attribution/audit-trail defect,
-- not a functional undercount; count_sql itself is untouched here, correctly, since it was
-- never wrong.
--
-- F-E4's second half (a cross-ayanamsha classification band-flip: AMSAYU longevity method
-- classifies madhyayu under most ayanamshas but alpayu under surya_siddhanta_classical, 30.66 vs
-- 36.34 years, near the classical threshold) is a genuine, honest classical-computation
-- divergence, not a defect to fix -- recorded in L1_STATE.md rather than folded into this
-- registry-only migration.

BEGIN;

INSERT INTO fact_category_ownership (fact_category, owning_asset_id) VALUES
    ('ayurdaya', 'ga_ayurdaya')
ON CONFLICT (fact_category, owning_asset_id) DO NOTHING;

COMMIT;
