-- 842_nirmana_l1_ga_structural_category_ownership_bhava_bala_backfill.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT, third in the 840-859 range (adjudication #2101, L1
-- continuation 5). Closes out D-L1-105 (cycle 86, L1_STATE.md decisions log): while authoring
-- migration 813's `contradiction_pair` conjuncts, a running exclusion-list reconciliation found
-- `fact_category_ownership` missing registry rows for 7 real, migration-796-covered categories
-- (`bhava_bala_positional` / `bhava_bala_directional` / `bhava_bala_temporal` /
-- `bhava_bala_aspectual` / `bhava_bala_occupant` / `bhava_bala_lord` /
-- `bhava_bala_total_extended`) -- confirmed live, each one a real, data-populated `chart_facts`
-- category (60 rows per chart, 180 total across the 3 canonical charts) with ZERO rows in
-- `fact_category_ownership`, owned by no asset at all. D-L1-105 explicitly deferred the fix:
-- "Deliberately did NOT patch `fact_category_ownership` itself -- ... left as an open,
-- correctly-scoped follow-up." This is that follow-up.
--
-- This is also the live mechanism behind two OTHER still-open findings from L1_W2_DECIDE_v1_0.md
-- §3: F-C9 (`ga_structural`'s `count_sql` -- a `JOIN fact_category_ownership` since migration
-- 410 -- omits ~5,157 owned rows because the registry undercounts) and the asset table's own
-- "undercounts self ~5,157" note. Backfilling these 7 rows closes the gap at its root (the
-- registry, not the count_sql text, which already joins the registry correctly per migration
-- 410's design intent) -- `ga_structural`'s served row count should increase by exactly 180
-- (60 x 3 charts) once this lands, no writer or serving-layer change needed.
--
-- Same idempotent `ON CONFLICT (fact_category, owning_asset_id) DO NOTHING` pattern migration
-- 410 established (the table's own seed migration) -- safe to re-run, adds nothing if these 7
-- rows already exist. `count_sql` itself is untouched: migration 410 already pointed it at this
-- registry table, so backfilling the table is the complete fix.

BEGIN;

INSERT INTO fact_category_ownership (fact_category, owning_asset_id) VALUES
    ('bhava_bala_positional', 'ga_structural'),
    ('bhava_bala_directional', 'ga_structural'),
    ('bhava_bala_temporal', 'ga_structural'),
    ('bhava_bala_aspectual', 'ga_structural'),
    ('bhava_bala_occupant', 'ga_structural'),
    ('bhava_bala_lord', 'ga_structural'),
    ('bhava_bala_total_extended', 'ga_structural')
ON CONFLICT (fact_category, owning_asset_id) DO NOTHING;

COMMIT;
