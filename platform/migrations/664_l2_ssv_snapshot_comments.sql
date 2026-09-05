-- 664_l2_ssv_snapshot_comments.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (L2_W2_DECIDE_v1_0.md: N-22 / E10; hard floor §3.5
-- snapshot protection). COMMENT ON TABLE only -- no schema change, no data
-- movement. Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Why this exists
-- --------------------------------------------------------------------------
-- E10's finding: the six `bodha_*__ssv_20260728a` tables carry ZERO
-- self-describing metadata today -- no comment, nothing in the catalogue
-- that says what they are, when they were taken, why they exist, or that
-- they must not be dropped. That is precisely what let an earlier drain
-- script miscount them (E10). W2 ruled RETAIN all 6, DROP none:
--
--   - Provenance: ŚUDDHA-VĀCA Phase D `CTAS` rollback anchors (PR #846).
--   - Restore tested byte-identical.
--   - 4 of 6 already differ materially from live data.
--   - `bodha_msr_signals__ssv_20260728a` is the direct witness for the E3
--     investigation into bo_laksana's floor shortfall.
--
-- Row counts below are measured campaign-wide (all charts in the snapshot,
-- not scoped to the canonical chart) -- verified live before writing this
-- migration, not carried over from an earlier per-chart figure.
--
-- This migration adds ONLY the missing metadata (tag, snapshot date, owning
-- PR, retention stance). It does not touch table contents and it does not
-- change the RETAIN-all-6 disposition -- it makes that disposition legible
-- to the next person (or drain script) who queries the catalogue instead of
-- asking a session.

COMMENT ON TABLE bodha_msr_signals__ssv_20260728a IS
  'NIRMANA snapshot tag=ssv_20260728a, taken 2026-07-28 (SUDDHA-VACA Phase D '
  'CTAS rollback anchor, PR #846). 150,150 rows at snapshot time (campaign-wide, '
  'all charts). Restore-tested byte-identical. RETAIN — the direct data witness '
  'for the bo_laksana E3 floor-shortfall investigation (L2_W1_ANALYSIS_v1_0.md). '
  'Do not drop without a fresh verified snapshot per charter hard floor §3.5.';

COMMENT ON TABLE bodha_cgm_edges__ssv_20260728a IS
  'NIRMANA snapshot tag=ssv_20260728a, taken 2026-07-28 (SUDDHA-VACA Phase D '
  'CTAS rollback anchor, PR #846). 1,687 rows at snapshot time (campaign-wide, '
  'all charts). Restore-tested byte-identical. RETAIN. '
  'Do not drop without a fresh verified snapshot per charter hard floor §3.5.';

COMMENT ON TABLE bodha_cgm_nodes__ssv_20260728a IS
  'NIRMANA snapshot tag=ssv_20260728a, taken 2026-07-28 (SUDDHA-VACA Phase D '
  'CTAS rollback anchor, PR #846). 711 rows at snapshot time (campaign-wide, '
  'all charts). Restore-tested byte-identical. RETAIN. '
  'Do not drop without a fresh verified snapshot per charter hard floor §3.5.';

COMMENT ON TABLE bodha_cdlm_cells__ssv_20260728a IS
  'NIRMANA snapshot tag=ssv_20260728a, taken 2026-07-28 (SUDDHA-VACA Phase D '
  'CTAS rollback anchor, PR #846). 150 rows at snapshot time (campaign-wide, '
  'all charts). Restore-tested byte-identical. RETAIN. '
  'Do not drop without a fresh verified snapshot per charter hard floor §3.5.';

COMMENT ON TABLE bodha_rm_resonances__ssv_20260728a IS
  'NIRMANA snapshot tag=ssv_20260728a, taken 2026-07-28 (SUDDHA-VACA Phase D '
  'CTAS rollback anchor, PR #846). 90 rows at snapshot time (campaign-wide, '
  'all charts). Restore-tested byte-identical. RETAIN. '
  'Do not drop without a fresh verified snapshot per charter hard floor §3.5.';

COMMENT ON TABLE bodha_signal_embeddings__ssv_20260728a IS
  'NIRMANA snapshot tag=ssv_20260728a, taken 2026-07-28 (SUDDHA-VACA Phase D '
  'CTAS rollback anchor, PR #846). 99,498 rows at snapshot time (campaign-wide, '
  'all charts). Restore-tested byte-identical. RETAIN — the largest of the six, '
  '~571 MB of the ~1.2 GB campaign-wide shadow footprint (E10). '
  'Do not drop without a fresh verified snapshot per charter hard floor §3.5.';
