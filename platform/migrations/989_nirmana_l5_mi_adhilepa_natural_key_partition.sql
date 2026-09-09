-- 989_nirmana_l5_mi_adhilepa_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L5 (Mimamsa). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 988 (mi_adhilepa output_digest_spec) -- see that
-- migration's header for the full verified account: sole-writer
-- co-writer investigation across all 5 tables this writer touches, the
-- deliberate SUBSET scope (only mimamsa_signal_adjustment,
-- mimamsa_fact_adjustment, mimamsa_anchor_adjustment specced --
-- mimamsa_convergence_adjustment and mimamsa_load_bearing each carry a
-- real, live-verified non-determinism defect, flagged on #1770, not fixed
-- here, per the #2502 subset-declaration ruling), and the live
-- duplicate/NULL-key check (0 duplicate groups, 0 NULLs across all three
-- specced tables on both populated charts). Declared per the DEP-ASSERT
-- precedent (880/908/909/910/927/930/939-940/.../984-985/986-987):
-- natural_key_partition being NULL reads as freshness_state='unknown'
-- (reason 'partition_undeclared') regardless of writer exclusivity or
-- build success. This partition declaration covers the same 3 components
-- as migration 988's spec -- it does NOT claim coverage of the two
-- excluded sibling tables.

UPDATE asset_registry
   SET natural_key_partition = 'mimamsa_signal_adjustment, mimamsa_fact_adjustment, mimamsa_anchor_adjustment (chart_id, origin_id, weight_id) each -- MiAdhilepaWriter (@register(''mi_adhilepa'')) is the confirmed sole live BUILD-TIME writer of all 5 tables it touches (grepped tree-wide for INSERT/UPDATE/DELETE across pipeline/orchestrator/writers/*.py, platform/scripts/*.py, and brahmagyan/, excluding this writer''s own file and tests/: mimamsa_signal_adjustment''s other hit is mi_seva.py''s existence-check-only service-handler list, not a co-writer; mimamsa_load_bearing''s other hits are mi_darshana.py''s read-only SELECT and dispatch_nirmana_campaign_wave.py''s blast-radius NO_FK_REFERRERS registry, neither a writer). The key matches each table''s own live PRIMARY KEY exactly. The writer''s own idempotent DELETE FROM <table> WHERE chart_id = %s (shared loop across all 5 sibling tables) before the classification/insert passes means exactly the current run''s row set exists per chart_id at any point in time, and each origin_id yields at most one row per table (single family match per signal/fact/anchor) so same-run PK collision cannot occur either. Non-determinism check on the 3 covered tables: each is fed by a per-row classify-and-match loop with no top-N cut and no aggregation, so the SET of rows produced is independent of the feeding SELECT''s fetch order regardless of ORDER BY presence (mimamsa_fact_adjustment''s feed is additionally explicitly ORDER BY fact_id). Live-verified 0 duplicate (chart_id, origin_id, weight_id) groups and 0 NULL keys across 50104+50171 (signal), 61523+61749 (fact), and 139+56 (anchor) live rows spanning both populated charts (canonical 482012f1, 1c826d5a). Surrogate/non-owned column excluded from the digest value columns: created_at (wall-clock write-time artifact, same exclusion class used throughout this campaign). DELIBERATELY NOT COVERED by this partition declaration: mimamsa_convergence_adjustment (fed by an unordered SELECT convergence_id FROM kala_convergence WHERE chart_id = %s LIMIT 500 with no ORDER BY -- live-verified both populated charts, 1c826d5a at 17,957 rows and cb73cd3d at 2,540 rows, exceed the cutoff, so which 500 land is not guaranteed stable across rebuilds) and mimamsa_load_bearing (top_mults = sorted(applied_multiplier>=1.0 items, key=applied_multiplier, reverse=True)[:5] over an unordered SELECT FROM mimamsa_multipliers -- live-verified real tie on BOTH populated charts between fam_yoga and fam_msr_signal at applied_multiplier=1.4, so which family gets role=''load_bearing'' at rank 0 versus role=''supporting'' at rank 1 is non-deterministic) -- both flagged on #1770 for a future writer fix, not fabricated over here per SS N.8.'
 WHERE asset_id = 'mi_adhilepa'
   AND natural_key_partition IS NULL;
