-- 023_signal_states.sql
-- Authored by: M3-W2-B2-YOGINI-TRANSIT (2026-05-01)
--
-- Date-indexed signal lit/dormant/ripening surface (M3-B deliverable per
-- PHASE_M3_PLAN_v1_0.md §3.2). Populated by
-- platform/scripts/temporal/signal_activator.py for a given (chart_id, query_date)
-- pair: the activator joins the active Vimshottari dasha row at query_date with
-- the transit state from compute_transits.get_transit_states() and emits one
-- row per MSR signal whose state is decidable.
--
-- Schema design notes:
--   - state is constrained to {'lit','dormant','ripening'} (PHASE_M3_PLAN §3.2,
--     deliverable #4). 'lit' = currently active; 'ripening' = approaching
--     activation within ~30 days or in next sub-period; 'dormant' = otherwise.
--   - confidence is a soft annotation; v1 of signal_activator emits a flat 0.6.
--     Future iterations may calibrate per-signal.
--   - dasha_system is the dasha that drove the activation decision (e.g.
--     'vimshottari'); included in UNIQUE so the same signal can be lit under
--     Vimshottari and dormant under Yogini on the same date without collision.
--   - ayanamsha is recorded for audit trail; project default is 'lahiri' per
--     M3-W2-B1 close fix.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS + UNIQUE constraint allows re-running.

BEGIN;

CREATE TABLE IF NOT EXISTS signal_states (
  id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id      TEXT         NOT NULL,
  signal_id     TEXT         NOT NULL,
  query_date    DATE         NOT NULL,
  state         TEXT         NOT NULL CHECK (state IN ('lit','dormant','ripening')),
  confidence    NUMERIC,
  dasha_system  TEXT,
  computed_by   TEXT         NOT NULL DEFAULT 'signal_activator',
  ayanamsha     TEXT         NOT NULL DEFAULT 'lahiri',
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  UNIQUE (chart_id, signal_id, query_date, dasha_system)
);

CREATE INDEX IF NOT EXISTS idx_signal_states_chart_date
  ON signal_states(chart_id, query_date);
CREATE INDEX IF NOT EXISTS idx_signal_states_chart_signal
  ON signal_states(chart_id, signal_id, query_date);

COMMIT;
