-- Migration 418: reassign avastha category ownership (BA Phase-3 RULING JL-022).
--
-- The D1 categories graha_avastha_lajjitadi and graha_avastha_sayanadi were
-- written by BOTH ga_structural and ga_condition (dual delete-then-insert on the
-- same fact_category → the wave-parallel lock contention migration 416 papered
-- over with a serializing DAG edge). ga_condition's versions are authoritative
-- (real combustion arc, dignity_d1_from_sign, Phaladeepika ch.13 / BPHS grounding);
-- ga_structural has stopped emitting them (code change, same PR). This migration
-- realigns the J2 category-ownership registry (fact_category_ownership, mig 410 /
-- JL-015) so ga_structural's count_sql JOIN no longer counts rows it no longer
-- writes.
--
-- This also fixes a PRE-EXISTING double-count: ga_condition's count_sql (mig 390)
-- already OR-counts these two categories, while fact_category_ownership still
-- attributed them to ga_structural — so they were counted under BOTH assets. After
-- this migration they are owned+counted only by ga_condition.
--
-- The other four D1 avastha categories (baladi, jagrad, deepta,
-- lifetime_exposure_summary) remain ga_structural-owned: single-writer, never
-- contended. Full ALL-avastha consolidation is a deferred follow-on (JL-022 Opt B).

BEGIN;

UPDATE fact_category_ownership
SET owning_asset_id = 'ga_condition'
WHERE fact_category IN ('graha_avastha_lajjitadi', 'graha_avastha_sayanadi')
  AND owning_asset_id = 'ga_structural';

COMMIT;

-- DOWN:
-- UPDATE fact_category_ownership SET owning_asset_id = 'ga_structural'
-- WHERE fact_category IN ('graha_avastha_lajjitadi', 'graha_avastha_sayanadi');
