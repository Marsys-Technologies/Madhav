-- Migration 172: asset_throughput — rows_written + expected_rows
-- Adds volume tracking columns required by the new run-id orchestrator.
-- Applied: 2026-06-06

ALTER TABLE asset_throughput
  ADD COLUMN IF NOT EXISTS rows_written    INT,
  ADD COLUMN IF NOT EXISTS expected_rows   INT;
