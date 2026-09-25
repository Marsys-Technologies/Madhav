-- Migration 1093 — E5 station-loop episodes with child contact intervals
-- RENUMBERED 1072 -> 1093 on 2026-09-25 (native decision 15), with its sibling 1071 -> 1092. The
-- Gochara branch claimed 1072 for a different migration; neither file was applied, so the remedy is
-- a renumber to max+1 across BOTH migration directories rather than a disclosed exception.
-- The SQL body is unchanged; only the number and this note moved.

ALTER TABLE kala_convergence
    ADD COLUMN IF NOT EXISTS is_episode BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS episode_uuid UUID,
    ADD COLUMN IF NOT EXISTS episode_children JSONB,
    ADD COLUMN IF NOT EXISTS episode_hull JSONB,
    ADD COLUMN IF NOT EXISTS perfected BOOLEAN;

COMMENT ON COLUMN kala_convergence.is_episode IS
    'E5: true when this row is a station-loop episode (aggregate) rather than a single contact.';

COMMENT ON COLUMN kala_convergence.episode_uuid IS
    'E5: deterministic identifier for the episode; survives rebuilds when membership is unchanged.';

COMMENT ON COLUMN kala_convergence.episode_children IS
    'E5: JSONB list of child contact intervals and metadata retained from the grouped contacts.';

COMMENT ON COLUMN kala_convergence.episode_hull IS
    'E5: search envelope {window_start, window_end} spanning the unioned child intervals.';

COMMENT ON COLUMN kala_convergence.perfected IS
    'E5: true when the episode is bounded by a complete retrograde->direct station loop; false for horizon-truncated loops or episodes containing only approached-never-perfected contacts.';
