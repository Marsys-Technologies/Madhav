-- Migration 1096 — vw_asset_downstream_dependents: a DAG-derived count of transitive
-- downstream dependents, as a VIEW (Nirmāṇa engine packet B2 — "the DAG-derived
-- downstream count", formerly titled "Blocking radius, recorded")
--
-- Before-measurement: 00_ARCHITECTURE/briefs/nirmana/engine/measurements/
-- B2_before_20260926T173944Z.json. Review (C-1 correction pass):
-- 00_ARCHITECTURE/briefs/nirmana/engine/reviews/B2_review_20260926T202916Z.md.
-- Read both for the full account; this header restates only what a future reader
-- of this migration needs.
--
-- WHAT THIS IS: for asset A, the size of the reverse-transitive-closure of the
-- asset_registry.depends_on DAG rooted at A, RESTRICTED TO is_active = true
-- assets on BOTH sides of the closure — i.e. how many OTHER active assets would
-- need a rebuild if A's data changed. Proven, by an independent Python BFS over
-- the same edge list, to agree exactly with this recursive CTE on all 129 assets
-- when neither is filtered (measurement, above) — and, after the C-1 fix below,
-- proven again to agree with platform/src/lib/build/plan.ts's REAL
-- computeDownstreamClosure() over the SAME is_active-filtered population
-- production actually feeds it (test: vw_asset_downstream_dependents.db.test.ts).
--
-- C-1 (review, BLOCKED the first version of this migration from ever applying):
-- the FIRST version of this view filtered nothing, while
-- platform/src/app/api/cockpit/runs/route.ts (and stats/route.ts's own asset
-- list) load the registry with `WHERE is_active = true` — 127 of 129 rows. Two
-- inactive rows (`ka_gochara_v3_century_materialize`, is_active=false,
-- CURRENT; `ka_gochara_sweep`, is_active=false, RETIRED) are themselves leaves
-- (nothing depends on them) but DO depend on other, active assets — so an
-- unfiltered view counted them as "downstream dependents" of their own active
-- ancestors, inflating 13 assets' counts by 1 or 2, and flipping three genuinely
-- active, CURRENT, live assets (`bg_sky_calendar`, `ka_kota_chakra`,
-- `ka_tithi_pravesha`) from a real 0 ("no downstream impact") to a fabricated 1
-- — a CATEGORY change, not a rounding error, on the exact line this packet
-- tested for honesty. `ga_positions` (the headline figure) moved 79 -> 80 for
-- the same reason. The view's own stated purpose ("how many assets would need a
-- REBUILD") makes the fix's semantics obvious: an inactive asset is never
-- rebuilt by anything, so it can neither BE a rebuild target (excluded from the
-- outer asset list) NOR make some OTHER asset look like a rebuild target on its
-- account (excluded from the edge set that feeds the closure). Both filters
-- below close this — `edges` only originates from active rows (mirrors
-- plan.ts's `registry` array, which is populated by the SAME `is_active = true`
-- query and therefore never iterates an inactive row's `depends_on` at all,
-- so an inactive asset can never seed further reachability either); the outer
-- SELECT only reports active assets (mirrors that an inactive asset is never a
-- valid seed/root for plan.ts's traversal either, being absent from its
-- registry array in the first place).
--
-- WHAT THIS IS NOT, and why the name says so: the before-measurement's own
-- cross-check against 717 historical build runs found this static DAG figure does
-- NOT predict which failures actually cascade hardest in practice (driven by
-- incident FREQUENCY, an operational fact this DAG cannot see, not by graph SHAPE).
-- The sharpest example: ga_dashas has the 2nd-largest transitive radius of the named
-- hub set (61) yet ranks LAST in observed cascade citations; ph_nimitta, smallest in
-- that set (17), ranks 2nd. "Blocking radius" was therefore NOT used as this view's
-- name — that phrase is already load-bearing elsewhere in this repo
-- (00_ARCHITECTURE/briefs/nirmana/BUILD_FAILURE_TRIAGE_2026-09-26_v1_0.md line 85)
-- for the OBSERVED/empirical quantity, a different and incompatible number. This
-- view is named for exactly what it structurally is: a DAG-derived count of
-- transitive downstream dependents, and an UPPER BOUND on what COULD be affected —
-- never a prediction of what HAS been or WILL be affected. Every consumer of this
-- view must carry that caveat forward in the surface itself, not only in a doc
-- (see the sole consumer, platform/src/app/api/cockpit/stats/route.ts, and
-- AssetRow.tsx's rendering of it).
--
-- WHY A VIEW, NOT A COLUMN OR A TABLE: asset_registry rows ARE asset rows (the
-- nirmana_registry_receipt_invalidation trigger already treats that table as
-- authored/structural data, never a place to accrete a derived, driftable number).
-- A new build-state table would be schema-permitted but would need a NEW
-- ancestor-walking invalidation trigger that does not exist today — the existing
-- nirmana_registry_receipt_invalidation trigger marks ONLY the single row whose own
-- depends_on just changed, never the graph of ancestors whose derived counts also
-- changed elsewhere in the tree. A view has nothing to go stale: it recomputes the
-- closure from the LIVE depends_on column on every read, so there is no drift
-- detector to build, own, or forget (§N.8 — a stored value here would be exactly
-- the "detector checks a proxy, not the claim" failure mode this campaign exists to
-- remove). 13 existing vw_*/mv_* views already establish this on-demand-derivation
-- precedent (e.g. vw_chart_digest); none of them cache a scalar that could disagree
-- with its source, and this view follows the same discipline.
--
-- REUSE, NOT REINVENTION: platform/src/lib/build/plan.ts already computes this exact
-- closure in-memory (transitiveDownstream(), ~lines 215-232 / exported as
-- computeDownstreamClosure) for rebuild-scoping. This view is the SQL-side sibling
-- of that same closure definition (same "seed → repeated frontier expansion via
-- depends_on" logic, expressed as a recursive CTE instead of a JS while-loop) so a
-- DB-side reader (the stats route, which cannot cheaply hold the whole registry
-- in-process for every poll) gets the identical answer computeDownstreamClosure
-- would give, without a second, divergent algorithm — the C-1 fix above is exactly
-- what makes that true over the POPULATION production actually uses, not only over
-- an idealized full registry. The test suite proves this view THREE ways: (1) a
-- fresh, independent JS BFS in the test file itself (not a call into plan.ts, so it
-- falsifies rather than assumes the SQL); (2) a direct call into the REAL, exported
-- computeDownstreamClosure() from plan.ts, over the real production registry export
-- (asset_id/depends_on/is_active), read-only, so the "reuse plan.ts" instruction is
-- honoured as a cross-check rather than skipped; (3) the migration's own idempotent
-- re-application. See platform/tests/integration/vw_asset_downstream_dependents.db.test.ts.
--
-- CONSUMER (exactly one, per the packet's own "don't build an unconsumed number"
-- rule): platform/src/app/api/cockpit/stats/route.ts reads this view once per poll
-- (registry-wide, not per-asset — a single query) and surfaces
-- `downstream_dependent_count` on AssetStats; AssetRow.tsx renders it, captioned as
-- an upper bound, only next to a genuine (non-cascade) asset failure.
--
-- HONESTY AT ZERO/ABSENT: the LEFT JOIN below means every asset_registry row gets a
-- row in this view, and count(DISTINCT ...) over a NULL-only join group evaluates to
-- 0, not NULL — a leaf asset with no dependents reads as a real, present 0 ("no
-- downstream impact"), never as an absent row a caller could mistake for "not
-- computed". Absence (this view not existing yet in an environment the migration
-- hasn't reached) is handled entirely on the read side, by
-- platform/src/lib/db/viewPresence.ts's viewPresent() probe — the same
-- process-lifetime-cached, graceful-degradation pattern migration 1095 established
-- for blocked_by_asset_id — so a pre-migration environment reads `null` (not
-- computed), never a fabricated 0 standing in for "not measured".
--
-- Idempotency: CREATE OR REPLACE VIEW; the GRANT below is guarded by
-- has_table_privilege so re-running this migration changes nothing the second time.
--
-- Numbered max+1 scanned across BOTH platform/migrations/ and
-- platform/supabase/migrations/ at execution time (max found: 1095,
-- platform/supabase/migrations/1095_build_run_assets_blocked_dependency.sql;
-- platform/migrations/ max was 1070). migration_number_guard.ts names
-- platform/supabase/migrations/ as "the active sequence -- all new migrations go
-- here", matching where 1092-1095 landed.

CREATE OR REPLACE VIEW vw_asset_downstream_dependents AS
WITH RECURSIVE edges AS (
  -- C-1: filtered to is_active=true assets only, on the SOURCE (dependent) side —
  -- an inactive asset's own depends_on relationships never propagate into anyone
  -- else's closure, mirroring plan.ts's registry array (populated by the same
  -- `is_active = true` query), which never iterates an inactive row either.
  SELECT asset_id AS dependent, unnest(depends_on) AS upstream
  FROM asset_registry
  WHERE is_active = true
),
closure AS (
  SELECT dependent, upstream FROM edges
  UNION
  SELECT c.dependent, e.upstream
  FROM closure c
  JOIN edges e ON e.dependent = c.upstream
)
SELECT
  ar.asset_id,
  count(DISTINCT c.dependent) AS downstream_dependent_count
FROM asset_registry ar
LEFT JOIN closure c ON c.upstream = ar.asset_id
-- C-1: the outer asset list is ALSO filtered to is_active=true, so an inactive
-- asset never gets a row here at all -- it is never a valid rebuild target,
-- mirroring that it is never a valid seed for plan.ts's traversal either
-- (absent from that function's own registry array from the first query).
WHERE ar.is_active = true
GROUP BY ar.asset_id;

COMMENT ON VIEW vw_asset_downstream_dependents IS
  'Packet B2 (C-1-corrected). Per active asset, the size of the reverse-transitive-'
  'closure of asset_registry.depends_on RESTRICTED TO is_active=true assets on both '
  'sides -- how many OTHER active assets depend on this one, directly or '
  'transitively, i.e. how many would need a REBUILD. An UPPER BOUND on what a '
  'failure of this asset COULD affect, never a prediction of what an actual failure '
  'HAS affected or WILL affect (the before-measurement found this static figure '
  'does not predict observed cascade ranking -- that is driven by incident '
  'frequency, not graph shape). Deliberately NOT named "blocking radius": that '
  'phrase already names a different, empirical quantity in '
  '00_ARCHITECTURE/briefs/nirmana/BUILD_FAILURE_TRIAGE_2026-09-26_v1_0.md. '
  'Matches platform/src/lib/build/plan.ts''s computeDownstreamClosure() over the '
  'SAME is_active-filtered population production actually feeds it -- an inactive '
  'asset is never a rebuild target and can never make another asset falsely look '
  'like one either (review B2_review_20260926T202916Z.md C-1). A VIEW, not a '
  'stored column/table, because it has nothing to go stale: it reads the live '
  'depends_on graph on every query. See migration 1096''s own header for the full '
  'account.';

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN
    RAISE EXCEPTION 'migration 1096 requires amjis_app (the app''s own DB role, used pervasively elsewhere -- e.g. migration 638) to already exist';
  END IF;

  IF NOT has_table_privilege('amjis_app', 'public.vw_asset_downstream_dependents', 'SELECT') THEN
    EXECUTE format(
      'GRANT SELECT ON TABLE %I.%I TO amjis_app',
      current_schema(),
      'vw_asset_downstream_dependents'
    );
  END IF;
END $$;
