-- 995_nirmana_l5_mi_pramana_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L5 (Mimamsa). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 994 (mi_pramana output_digest_spec) -- see that
-- migration's header for the full verified account: sole-writer co-writer
-- investigation across both tables this writer touches, the non-determinism
-- analysis (no top-N cut, no fetch-order-dependent dedup or first-row pick
-- anywhere in the writer, unlike the prior 3 partial specs this campaign),
-- and the live duplicate/NULL-key check (0 duplicate groups, 0 NULLs on
-- both tables, canonical chart 482012f1 -- the only chart with data for
-- this writer so far). Declared per the DEP-ASSERT precedent
-- (880/908/909/910/927/930/939-940/.../988-989/990-991):
-- natural_key_partition being NULL reads as freshness_state='unknown'
-- (reason 'partition_undeclared') regardless of writer exclusivity or
-- build success. This partition declaration covers BOTH tables this
-- writer owns -- full coverage, not a subset.

UPDATE asset_registry
   SET natural_key_partition = 'mimamsa_calibration (chart_id, match_id) + mimamsa_reliability (chart_id, stratum_key, predicted_prob_bin) -- MiPramanaWriter (@register(''mi_pramana'')) is the confirmed sole live BUILD-TIME writer of both tables (grepped tree-wide for INSERT/UPDATE/DELETE across pipeline/orchestrator/writers/*.py, brahmagyan/, services/, and all TS consumers, excluding this writer''s own file and tests/: 0 hits against either table outside mi_pramana.py; mi_gunanaka.py writes a DIFFERENT table, mimamsa_calibration_snapshot). Both keys match the tables'' own live PRIMARY KEYs exactly. mimamsa_calibration''s row set is the full cross-product of (prediction, event) pairs whose event_date falls within the prediction''s observation_window, fed by two unbounded chart-scoped SELECTs with no top-N cut or dedup -- content-set independent of fetch order, keyed by match_id = prediction_id concatenated with event_id, a deterministic composite of the two source PKs. Every column value is a pure function of the matched row''s own data; the one stub scorer (_score_manifestation) returns a hardcoded constant regardless of its inputs, and the one currently-empty lookup (_load_base_rates, honest-null per A-F-24/#1738) returns {} deterministically -- neither is a source of drift. mimamsa_reliability aggregates the FULL mimamsa_calibration row set per chart into fixed probability-decile bins (Decimal-based indexing, confirmed the A-F-34 float-floor bug this same file previously fixed is absent from the current source) via order-independent sum/count over full bin membership -- no top-N cut, no first-row pick. Both tables'' DELETE-then-insert-per-chart idempotency (writer''s own `DELETE FROM ... WHERE chart_id = %s` before each insert pass) means exactly the current run''s row set exists per chart_id at any point in time. Live-verified 0 duplicate-key groups and 0 NULL keys on both tables across all populated charts (canonical 482012f1: 57 calibration rows, 6 reliability rows; 1c826d5a: 0 rows in either table, not yet built for this writer). Surrogate/non-owned columns excluded from the digest value columns: mimamsa_calibration.scored_at, mimamsa_reliability.computed_at -- both plain wall-clock DEFAULT now() write-time timestamps, same exclusion class as created_at used throughout this campaign. Unlike the prior 3 specs this campaign (bo_cdlm_summary, mi_adhilepa, mi_bhavisya, all partial under the #2502 subset-declaration ruling), this partition declaration covers the writer''s FULL table scope -- no exclusion was needed, no live non-determinism defect was found in either table.'
 WHERE asset_id = 'mi_pramana'
   AND natural_key_partition IS NULL;
