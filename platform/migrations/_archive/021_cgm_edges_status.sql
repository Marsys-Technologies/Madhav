-- 021_cgm_edges_status.sql
-- Adds status + orphan_reason to l25_cgm_edges and its staging mirror.
-- status values: 'valid' | 'orphan' | 'self_loop'
-- Backfills existing rows as 'valid' (pre-migration data is all intra-CGM edges).

ALTER TABLE l25_cgm_edges
  ADD COLUMN IF NOT EXISTS status        TEXT NOT NULL DEFAULT 'valid',
  ADD COLUMN IF NOT EXISTS orphan_reason TEXT;

ALTER TABLE l25_cgm_edges_staging
  ADD COLUMN IF NOT EXISTS status        TEXT NOT NULL DEFAULT 'valid',
  ADD COLUMN IF NOT EXISTS orphan_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_l25_cgm_edges_status ON l25_cgm_edges(status);

UPDATE l25_cgm_edges SET status = 'valid' WHERE status IS NULL OR status = '';
