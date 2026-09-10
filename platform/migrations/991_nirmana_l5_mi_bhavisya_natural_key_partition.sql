-- 991_nirmana_l5_mi_bhavisya_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L5 (Mimamsa). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 990 (mi_bhavisya output_digest_spec) -- see that
-- migration's header for the full verified account: sole-writer
-- co-writer investigation across both tables this writer touches, the
-- deliberate SUBSET scope (only mimamsa_manifestation_sets specced --
-- mimamsa_predictions carries a real, live-verified non-determinism
-- defect in its driving_signals field, flagged on #1770, not fixed here,
-- per the #2502 subset-declaration ruling), and the live duplicate/NULL-
-- key check (0 duplicate groups, 0 NULLs on mimamsa_manifestation_sets
-- across both populated charts). Declared per the DEP-ASSERT precedent
-- (880/908/909/910/927/930/939-940/.../986-987/988-989):
-- natural_key_partition being NULL reads as freshness_state='unknown'
-- (reason 'partition_undeclared') regardless of writer exclusivity or
-- build success. This partition declaration covers the same 1 component
-- as migration 990's spec -- it does NOT claim coverage of the excluded
-- sibling table.

UPDATE asset_registry
   SET natural_key_partition = 'mimamsa_manifestation_sets (chart_id, prediction_id, channel_id) -- MiBhavisyaWriter (@register(''mi_bhavisya'')) is the confirmed sole live BUILD-TIME writer of this table (grepped tree-wide for INSERT/UPDATE/DELETE across pipeline/orchestrator/writers/*.py and brahmagyan/, excluding this writer''s own file and tests/: mi_sambandha.py and mi_pramana.py both only read it via SELECT, neither is a writer). The key matches the table''s own live PRIMARY KEY exactly. The writer''s own idempotent DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s before the insert pass means exactly the current run''s row set exists per chart_id at any point in time, fed by an explicitly ORDER BY anchor_id SELECT with one row emitted per anchor (no top-N cut, no aggregation) so the SET of rows produced is independent of fetch order and same-run PK collision cannot occur either. Live-verified 0 duplicate (chart_id, prediction_id, channel_id) groups and 0 NULL keys across 139+56 live rows spanning both populated charts (canonical 482012f1, 1c826d5a). Surrogate/non-owned column excluded from the digest value columns: frozen_at (wall-clock write-time artifact -- this writer stamps every row in a run with one shared emitted_at/frozen_at value, so it differs every rebuild regardless of underlying chart-fact content; same exclusion class as created_at used throughout this campaign). DELIBERATELY NOT COVERED by this partition declaration: mimamsa_predictions (its driving_signals field is populated, per prediction, from either a per-domain or chart-wide top-5-by-computed_salience pick over an ORDER BY computed_salience DESC-but-untied bodha_msr_signals query -- live-verified REAL ties at the top-5 cutoff in 9 of 10 domains checked on the canonical chart itself, including one domain, relationship, where the entire 14-row candidate set shares one tied salience value spanning rank 1-14 -- which signal_ids land in the frozen top-5 is therefore not guaranteed stable across rebuilds; flagged on #1770 for a future writer fix -- e.g. a secondary ORDER BY tiebreak key such as signal_id -- not fabricated over here per SS N.8. Separately, and not itself a blocker for this table since it never actually executes: brahmagyan/mimamsa/prediction_ledger.py''s log_prediction API route (live-mounted at POST /api/brahma/mimamsa/log_prediction) targets column names that do not exist on the live mimamsa_predictions schema (prediction_text/confidence/falsifier/source_citation/predicted_at vs the real outcome_claim/confidence_band/falsifier_jsonb/source_pramana_id/emitted_at) -- any call would raise psycopg.errors.UndefinedColumn, the same disconnected-legacy-schema pattern brahmagyan/mimamsa/outcome.py''s own inline comment already documents for its sibling calibration path; flagged on #1770 as a separate schema-drift/broken-endpoint defect.'
 WHERE asset_id = 'mi_bhavisya'
   AND natural_key_partition IS NULL;
