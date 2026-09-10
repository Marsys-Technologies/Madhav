-- 674_nirmana_l3_n6_ssv_shadow_disposition.sql
--
-- NIRMĀṆA L3 Kāla — mandate item (b): dispositions all Kāla `__ssv_*` tables (finding N6,
-- L3_W2_DECIDE_v1_0.md). Full evidence in L3_W1_ANALYSIS_BATCH_D.md's "Kāla __ssv_* shadow-table
-- disposition" section.
--
-- Provenance: these are `CREATE TABLE ... AS SELECT` rollback snapshots the ŚUDDHA-VĀCA campaign
-- took 2026-07-28 (SUDDHA_VACA_REPORT_v1_0.md §Phase D / §Step-3) before a rebuild it needed a
-- tested-rollback drill for. That rebuild was accepted and the campaign sealed at PŪRṆATĀ
-- (2026-07-31) — the rollback window these snapshots existed for has been closed for weeks.
--
-- Verified before writing this migration (live, this session):
--   - Row counts match the W1 analysis exactly for all 8 tables (no drift since the audit).
--   - Zero FK constraints and zero views reference any of the 8 tables (pg_constraint /
--     pg_depend, both empty).
--   - All 8 have idx_scan NULL (no index — a plain CTAS heap, never a maintained table) and
--     single-digit seq_scan counts (audit reads only, no application traffic).
--   - Repo grep (`__ssv`) confirms the only production reader anywhere is
--     `services/w2g_validations/v5_corpus_readiness.py`, which reads
--     `kala_gochara_windows__ssv_20260728c` specifically (not any of the 7 dropped here), and
--     even there only as non-verdict evidence (`sibling_tables`, not the PASS/FAIL driver).
--
-- 7 of 8 dropped (723.4 MiB reclaimed); `kala_gochara_windows__ssv_20260728c` is DELIBERATELY
-- NOT dropped in this migration: it is the one table with a real (if weak) repo reader, and is
-- cited by ADJUDICATION-6 as the production precedent for the sibling-table generation pattern.
-- Re-evaluate only after v5_corpus_readiness.py's probe is re-pointed — not this campaign's job.
--
-- This is NOT the v1 gochara corpus. `kala_gochara_windows_archive_20260805` (the hard floor's
-- named irreplaceable `ka_gochara_sweep` v1 archive) is a DIFFERENT table, untouched here, and
-- does not match the `__ssv_*` naming pattern this migration targets.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DROP TABLE kala_activation__ssv_20260728b;
DROP TABLE kala_taranga__ssv_20260728b;
DROP TABLE kala_convergence__ssv_20260728b;
DROP TABLE kala_obstruction__ssv_20260728b;
DROP TABLE kala_darshana__ssv_20260728b;
DROP TABLE kala_jivana_parva__ssv_20260728b;
DROP TABLE kala_bhavishya__ssv_20260728b;
