-- Migration 1072 — E5 station-loop episodes with child contact intervals

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
