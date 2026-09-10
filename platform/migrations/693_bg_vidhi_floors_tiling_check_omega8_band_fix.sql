-- 693_bg_vidhi_floors_tiling_check_omega8_band_fix.sql
--
-- NIRMANA L0-W4 CONFORM (C12 wave-1 defect investigation): bg_vidhi_floors'
-- integrity_check_sql tiling assertion (`lo<>1 OR hi<>n OR distinct_orders<>n`)
-- treats any gap in an intent's item_order sequence as a violation. That is
-- the WRONG invariant -- C12 "correct the check" path (same class as the
-- bg_gochara_arcs stale-pin rewrite and migration 692's bg_doshas fix),
-- verified against the canonical source of truth before writing.
--
-- Root cause: the writer (bg_vidhi_floors.py, mirrored 1:1 by a CI drift
-- gate against the canonical `platform/src/lib/vidhi/registry_data.ts`)
-- deliberately reserves item_order 40+ as a fixed "Omega-8 reachability
-- band" appended to each _deepdive floor's own item list -- see
-- registry_data.ts's `omega8Band({ from: 40, ... })` calls and their
-- PARIŚODHANA B2 comments. Each floor's own item count varies (27-43
-- items), so the jump from e.g. order 38 straight to order 40 is an
-- intentional, documented, versioned design -- not an unnumbered edit
-- artifact. `hi<>n` (max item_order must equal item count) assumes
-- gapless 1..n numbering that was never the actual contract; it is
-- currently reproduced identically in BOTH the Python writer and its TS
-- mirror, so a future correctly-dispatched build would trip this same
-- false positive forever.
--
-- Verified live (read-only): all 7 `_deepdive` intents currently present
-- fail today's check on `hi<>n` alone (e.g. wealth_deepdive: n=40,
-- hi=44 -- the correct Omega-8-band shape); with `hi<>n` dropped, the
-- tiling NOT EXISTS clause returns 0 rows against current production
-- data. The two invariants that actually matter -- `lo=1` (sequences
-- start at 1) and `distinct_orders=n` (no duplicate order values, i.e.
-- real uniqueness) -- are both already satisfied and remain enforced.
--
-- This migration does NOT make bg_vidhi_floors' full integrity_check_sql
-- pass today -- the asset is separately, genuinely incomplete live
-- (11/14 intents, 286/409 items; `catalog_status='DRAFT'`), which the
-- count(*)=14 / count(*)=409 conditions correctly continue to catch.
-- That gap is a real dispatch/governance question (tracked in
-- L0_STATE.md), not a check bug, and is out of scope for this migration.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
   SET integrity_check_sql = $check$
SELECT
  (SELECT count(*) = 14 FROM vidhi_intent_floors)
  AND (SELECT count(*) = 409 FROM vidhi_floor_items)
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT intent,count(*) AS n,min(item_order) AS lo,max(item_order) AS hi,
             count(DISTINCT item_order) AS distinct_orders
      FROM vidhi_floor_items GROUP BY intent
    ) grouped
    WHERE lo<>1 OR distinct_orders<>n
  )
  AND NOT EXISTS (
    SELECT 1 FROM vidhi_floor_items item
    LEFT JOIN vidhi_intent_floors floor USING(intent)
    LEFT JOIN vidhi_primitives primitive USING(primitive_id)
    WHERE floor.intent IS NULL OR primitive.primitive_id IS NULL
  )
$check$
 WHERE asset_id = 'bg_vidhi_floors';

-- Forward reversal (safe at any time -- additive value correction, not a
-- schema change): re-run with `hi<>n` restored in the tiling WHERE clause.
