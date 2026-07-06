-- Migration 420: raise writer_timeout budgets for ka_sangam + bo_laksana
-- (BA Phase-3 parallel restore, JL-023 follow-up from measured data).
--
-- Evidence: the first parallel rebuild (WORKER_LIMIT=2, run 8d12cde4) failed on a
-- single asset — ka_sangam ran 660s and hit its 600s budget. The watchdog correctly
-- evicted+failed it, which transitively BLOCKED 25 downstream L3/L4/L5 assets. Root
-- cause is purely the budget: ka_sangam takes 373s serial but ~660s under parallel
-- CPU contention on the 2-CPU job (~1.8x inflation) — it would have completed
-- ~60s past its cap. No lock contention, no dual-write, no data error occurred;
-- the rest of the DAG built cleanly in parallel.
--
-- Fix: give ka_sangam generous headroom (1200s) so it survives parallel inflation
-- (and a possible future WORKER_LIMIT increase). bo_laksana was the next-slowest
-- un-bumped asset (359s parallel here, a known heavy percentile pass) — raised to
-- 1200s as forward-insurance against the same ~1.8x inflation at higher worker
-- counts. All other assets stayed well under their 600s default this run.

BEGIN;

UPDATE asset_registry SET writer_timeout_seconds = 1200 WHERE asset_id = 'ka_sangam';
UPDATE asset_registry SET writer_timeout_seconds = 1200 WHERE asset_id = 'bo_laksana';

COMMIT;

-- DOWN:
-- UPDATE asset_registry SET writer_timeout_seconds = 600 WHERE asset_id IN ('ka_sangam','bo_laksana');
