-- Migration 455: kala_activation period-window cardinality, v2 (CR-109 follow-up, D-4a Lane A-0)
-- Created: 2026-07-19
--
-- Supersedes an earlier draft of this same migration (also numbered 455, guard-
-- reviewed but never applied to prod — replaced in place before merge, so no
-- numbering gap and no ledger entry to reconcile). That draft widened
-- kala_activation's unique index from migration 454's
-- (chart_id, signal_id, ayanamsha_id, activation_start) to additionally include
-- activation_end, fixing the MD/first-AD-shared-start collision (confirmed live
-- on chart 482012f1: a Vimshottari mahadasha and its own first-nested
-- antardasha structurally share a start date — not a bug). Migration-guard
-- review of that draft found a second, more consequential collision path in the
-- CONVERGENCE-refined
-- branch of resolve_activation_windows (services/ka_temporal/date_resolver.py,
-- the `p_win_start = _clip(max(p_start, p_peak - half))` / `p_win_end = min(p_end,
-- p_peak + half)` lines), an AD nested inside its own MD can clip to the EXACT
-- SAME [peak-half, peak+half] window as its parent MD whenever the peak sits
-- comfortably inside both periods' bounds (not near an edge) — this is the
-- TYPICAL case for a convergence-anchored signal, not a rare coincidence, so
-- 455's (chart_id, signal_id, ayanamsha_id, activation_start, activation_end)
-- key is insufficient: two rows with different graha/level/proximity can share
-- identical clipped start+end.
--
-- Fix (per guard recommendation): key on something already guaranteed unique
-- per emitted row by construction — ka_kalasutra.py's source_citation embeds a
-- per-signal ordinal (`period={idx}`, idx = enumerate() position in
-- windows.period_windows) alongside the signal_id, so it can never collide
-- across two period-window rows of the SAME (chart_id, signal_id, ayanamsha_id)
-- regardless of how activation_start/end happen to clip.

BEGIN;

-- Drops migration 454's index (the only one of the prior attempts actually
-- applied to prod). IF EXISTS also covers idx_kala_activation_chart_signal_ayan_span
-- in case an earlier draft of this file was ever applied anywhere (it was not,
-- in this repo's prod, but the guard is idempotent regardless).
DROP INDEX IF EXISTS idx_kala_activation_chart_signal_ayan_start;
DROP INDEX IF EXISTS idx_kala_activation_chart_signal_ayan_span;

CREATE UNIQUE INDEX IF NOT EXISTS idx_kala_activation_chart_signal_ayan_citation
  ON kala_activation (chart_id, signal_id, ayanamsha_id, source_citation);

COMMIT;
