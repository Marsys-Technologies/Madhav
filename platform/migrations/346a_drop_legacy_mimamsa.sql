-- Migration 346a: drop brahma-era mimamsa tables that conflict with L5 writer schema
--
-- Context: brahma_mimamsa_*.sql migrations (applied 2026-06-22, ids 191-196) created early-design
-- versions of these tables with incompatible schemas.  Migrations 347-355 recreate them with the
-- production L5 Mīmāṃsā schema.  All tables have 0 rows — no data loss.
--
-- Does NOT touch tables already correctly created by 345/346:
--   mimamsa_event_provenance, mimamsa_signal_families, mimamsa_negative_controls.
--
-- Safe to re-apply (IF EXISTS, no CASCADE needed — no views depend on these tables).

DROP TABLE IF EXISTS mimamsa_predictions;
DROP TABLE IF EXISTS mimamsa_calibration;
DROP TABLE IF EXISTS mimamsa_multipliers;
DROP TABLE IF EXISTS mimamsa_qa_eval;
DROP TABLE IF EXISTS mimamsa_export_log;
DROP TABLE IF EXISTS mimamsa_export_log_staging;
