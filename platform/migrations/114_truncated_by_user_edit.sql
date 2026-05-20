-- Y-S5: Stop-and-edit while streaming.
-- Tracks which audit_events entries were truncated by user-initiated stop+edit.
-- Nullable boolean — only populated when R10_EDIT_WHILE_STREAMING fires.
-- Reversible: DROP COLUMN restores original schema.

ALTER TABLE audit_events
  ADD COLUMN IF NOT EXISTS truncated_by_user_edit BOOLEAN DEFAULT FALSE;

-- Down: ALTER TABLE audit_events DROP COLUMN IF EXISTS truncated_by_user_edit;
