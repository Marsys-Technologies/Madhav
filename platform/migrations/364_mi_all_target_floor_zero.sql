-- Migration 364: set target_floor = 0 for all remaining mi_* assets
--
-- L5 Mīmāṃsā is in STRUCTURAL mode — every writer can legitimately return
-- 0 rows until empirical calibration data accrues (by design, per L5 seal
-- L5_SEAL_AND_SHIP_REPORT_v1_0.md). Without target_floor = 0, the
-- orchestrator keeps state = 'dormant' for any per-chart writer that writes
-- 0 rows, which causes DEP-ASSERT cascade failures for all downstream assets.
--
-- mi_pramana (Calibration) is the immediate root of the current cascade:
-- it writes 0 rows in stub mode → mi_gunanaka DEP-ASSERTs →
-- mi_adhilepa / mi_pariksha / mi_sambandha / mi_darshana / mi_seva blocked.
--
-- Setting target_floor = 0 on ALL remaining mi_* assets:
--   • mi_pramana   — Calibration stub (writes 0 until outcome data accrues)
--   • mi_gunanaka  — Score Multipliers (depends on mi_pramana data)
--   • mi_adhilepa  — Overlay (depends on calibration)
--   • mi_pariksha  — QA evaluation (depends on calibration)
--   • mi_sambandha — Manifestation grammar (depends on calibration)
--   • mi_darshana  — Insight surface (depends on calibration)
--   • mi_seva      — Service verifier (depends on upstream)
--   • mi_abhilekha — Service handler (writes 0 to build tables by design)
--   • mi_bhavisya  — Predictions (wrote 800 rows; target_floor=0 is harmless)
--   • mi_kula      — Cultural context (wrote 15 rows; target_floor=0 is harmless)
--   • mi_vistara   — Global summary (chart_id IS NULL → always lit; harmless)
--
-- mi_jivanaghatana is excluded — already set to 0 in migration 363.
--
-- cf. asset_runner.py: zero_rows_is_complete = (chart_id is None) or (target_floor == 0)

UPDATE asset_registry
SET target_floor = 0
WHERE asset_id LIKE 'mi_%'
  AND asset_id != 'mi_jivanaghatana'
  AND target_floor IS NULL;
