-- Migration 454: kala_activation period-window cardinality (CR-109, D-4a Lane A-0)
-- Created: 2026-07-19
--
-- CR-109 (served activation-window coverage gap): ka_kalasutra now inserts one
-- kala_activation row PER matched in-life dasha period for a predicate (see
-- services/ka_temporal/date_resolver.py's `period_windows` addition), not one
-- collapsed row per (chart_id, signal_id, ayanamsha_id). The pre-existing
-- UNIQUE INDEX idx_kala_activation_chart_signal_ayan on exactly that triple
-- blocks this (confirmed live: UniqueViolation during the D-4a A-0 rebuild of
-- chart 482012f1's ka_kalasutra asset). Widen the natural key to include
-- activation_start so multiple period-window rows per signal are representable,
-- while still guarding against a genuine accidental double-insert of the exact
-- same period within one build (same chart+signal+ayanamsha+start is still
-- rejected). NULL activation_start rows (the "nothing resolves" fallback) stay
-- distinct from each other under standard Postgres NULL-distinct unique-index
-- semantics, same as before.
--
-- Idempotency: delete-then-insert per chart (ka_kalasutra.py) is unaffected —
-- this only widens what can coexist WITHIN one chart's row set, it does not
-- change the delete-then-insert discipline itself (§N.3).

BEGIN;

DROP INDEX IF EXISTS idx_kala_activation_chart_signal_ayan;

CREATE UNIQUE INDEX IF NOT EXISTS idx_kala_activation_chart_signal_ayan_start
  ON kala_activation (chart_id, signal_id, ayanamsha_id, activation_start);

COMMIT;
