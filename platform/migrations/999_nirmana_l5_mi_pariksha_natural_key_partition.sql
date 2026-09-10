-- 999_nirmana_l5_mi_pariksha_natural_key_partition.sql
--
-- NIRMANA v2.5 -- L5 (Mimamsa). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Sibling migration to 998 (mi_pariksha output_digest_spec) -- see that
-- migration's header for the full verified account: co-writer
-- investigation across all 3 tables this writer touches, the
-- non-determinism analysis (mimamsa_qa_eval clean; mimamsa_attribution
-- and mimamsa_discoveries both excluded on live-verified propagated
-- non-determinism), and the live duplicate/NULL-key check (0 duplicate
-- groups, 0 NULLs, canonical chart 482012f1 168 rows + 1c826d5a 6 rows).
-- Declared per the DEP-ASSERT precedent
-- (880/908/909/910/927/930/939-940/.../994-995): natural_key_partition
-- being NULL reads as freshness_state='unknown' (reason
-- 'partition_undeclared') regardless of writer exclusivity or build
-- success. This partition declaration covers ONLY mimamsa_qa_eval --
-- mimamsa_attribution and mimamsa_discoveries remain undeclared pending a
-- writer fix for the driving_signals/top-3-anchor non-determinism flagged
-- on #1770.

UPDATE asset_registry
   SET natural_key_partition = 'mimamsa_qa_eval (chart_id, check_id) -- MiParikshaWriter (@register(''mi_pariksha'')) is the confirmed sole live BUILD-TIME writer of this table (grepped tree-wide for INSERT/UPDATE/DELETE across pipeline/orchestrator/writers/*.py, brahmagyan/, services/, and all TS consumers, excluding this writer''s own file and tests/: brahmagyan/mimamsa/answer_quality.py contains a live INSERT/UPDATE against mimamsa_qa_eval but targets a disconnected legacy schema shape that does not match the live table -- confirmed dead code via \d, same pattern as mi_bhavisya''s log_prediction finding). Key matches the table''s own live PRIMARY KEY exactly. Written by 4 of this writer''s 7 substeps (control_windows, ablation, neg_control, tail_only), each verified deterministic by full source read: fixed per-event control-window offsets; one row per active family_id from order-independent aggregates (marginal_skill honestly stored as 0.0 under status=''structural_proxy'', never a fabricated ''pass''); one row per catalog negative-control (status=''not_implemented'', an honest null per JL-019, not a tautological pass); and a tail-selection substep whose live tie-prone ORDER BY affects only WHICH signals fall in the bottom-30% set, never the persisted values (only the deterministic COUNT of that set is ever written). Live-verified 0 duplicate-key groups and 0 NULL keys across all populated charts. This writer''s other 2 tables (mimamsa_attribution, mimamsa_discoveries) are DELIBERATELY NOT covered here -- mimamsa_attribution propagates a live-verified non-determinism from mimamsa_predictions.driving_signals (the same column that excluded mi_bhavisya, migration 990/991), and mimamsa_discoveries inherits that same defect transitively via its emergent_law substep plus an independent top-3-anchor tie risk in its retrodiction substep -- both flagged on #1770, not fixed this cycle.'
 WHERE asset_id = 'mi_pariksha'
   AND natural_key_partition IS NULL;
