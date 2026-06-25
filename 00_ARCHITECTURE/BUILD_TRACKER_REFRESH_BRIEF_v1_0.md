---
artifact: BUILD_TRACKER_REFRESH_BRIEF_v1_0.md
canonical_id: BUILD_TRACKER_REFRESH_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: BUILD_TRACKER_HARDENING_MASTER_v1_0.md
purpose: Make the Nirmāṇa tracker show DB TRUTH — fix the stale-display class at its structural root.
audience: Claude Code (Antigravity)
---

# Refresh Hardening — "the tracker never lies"

## §0 — The bug, precisely (from the code audit)
`platform/src/app/api/cockpit/stats/route.ts` → `fetchAllCounts`:
- For each asset, if `asset_throughput.rows_written` is non-null, it returns THAT as the count and
  skips the live `count_sql` entirely (perf shortcut, lines ~121-136).
- `deriveState` then returns `lit` whenever `actual_rows > 0`.

`platform/src/app/api/cockpit/clear/execute/route.ts` resets throughput to
`state='dormant', last_built_at=NULL, ...` but **does NOT null `rows_written`**.

⇒ After a clear, `rows_written` still holds the pre-clear count, stats returns it, `deriveState`
says `lit`. The tracker shows a fully-built layer over an empty DB. Same failure shape after a
partial build that errored mid-way (rows_written from a prior run survives).

## §1 — The fix (two parts; both small, both central)

**Part A — clear must invalidate the cached count.** In `clear/execute/route.ts`, the
`UPDATE asset_throughput SET state='dormant', ...` for cleared assets MUST also set
`rows_written = NULL`. Add `rows_written = NULL` to that SET clause (the one keyed by
`chart_id=$1 AND asset_id = ANY($2::text[])`). This makes the stats route fall through to live
`count_sql` for cleared assets, which reads 0 from the now-empty DB.

**Part B — defensive stats guard (belt + suspenders).** In `stats/route.ts` `fetchAllCounts`, the
`rows_written` shortcut should NOT be trusted when the throughput state contradicts it. Change the
shortcut condition so it is taken ONLY when the throughput state is `lit` or `building`. When state
is `dormant`/`stale`/`error`, ignore `rows_written` and fall through to the live `count_sql`. This
makes the displayed count self-correcting even if some other writer forgets to null rows_written.
Concretely, the guard at line ~122 (`if (tp != null && tp.rows_written != null)`) becomes
`if (tp != null && tp.rows_written != null && (tp.state === 'lit' || tp.state === 'building'))`.
(Service assets are already short-circuited above — unaffected.)

Keep the existing live-count fallback path and its error handling unchanged.

## §2 — Tests to add/extend (vitest, in `stats/__tests__`)
- dormant + non-null rows_written ⇒ stats calls count_sql (NOT the shortcut), returns live 0.
- lit + non-null rows_written ⇒ shortcut taken, returns rows_written (perf preserved).
- building + rows_written ⇒ shortcut taken (live build progress shown).
- error state ⇒ falls through to count_sql / error path.
Mock the throughput map + a stub count_sql; assert which path executed.

## §3 — End-to-end proof (Chrome MCP + DB :5433, on 1c826d5a ONLY)
PASTE TO CLAUDE CODE:
```
Goal: prove the Nirmāṇa tracker shows DB truth after a clear (stale-display fix, parent
BUILD_TRACKER_HARDENING_MASTER_v1_0.md §2 F1). Chart: Abhinandan Mohanty
1c826d5a-41cb-4450-b4dc-59d440e5f75a (SAFE non-native). NEVER touch native 482012f1.
Data plane = prod via Cloud SQL proxy :5433. Chrome is read-tier → use mcp__Claude_in_Chrome__* for
all UI actions. Dev server on localhost:3000 must serve the fix commit (or restart it).

IMPLEMENT first (then prove):
  1. clear/execute/route.ts: add `rows_written = NULL` to the cleared-assets asset_throughput UPDATE.
  2. stats/route.ts fetchAllCounts: gate the rows_written shortcut on
     (tp.state === 'lit' || tp.state === 'building'); else fall through to live count_sql.
  3. Add the 4 vitest cases in §2. Run `cd platform && npm run typecheck && npm test -- stats` green.

PROVE (UI + DB must agree):
  PRE (DB): record per-asset rows for one ga_ asset that is currently lit on 1c826d5a, e.g.
    SELECT count(*) FROM chart_dashas WHERE chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a';
    and the asset_throughput row: SELECT state, rows_written FROM asset_throughput
      WHERE chart_id='1c826d5a-...' AND asset_id='ga_dashas';
  STEP A: open http://localhost:3000/clients/1c826d5a-41cb-4450-b4dc-59d440e5f75a/nirmana,
    screenshot the Gaṇita layer, record the displayed count for that asset.
  STEP B: clear that ONE asset via the UI (asset-scope clear). Capture /api/cockpit/clear/execute
    network response (failed_tables MUST be empty).
  STEP C: WITHOUT a manual refresh trick, re-read /api/cockpit/stats (or click the tracker Refresh)
    and screenshot. The asset must now read 0 / NOT BUILT.
  STEP D (DB arbiter): re-run the PRE queries. DB rows == 0 AND asset_throughput.rows_written IS NULL
    AND state='dormant'.
  ACCEPTANCE: STEP C display == STEP D DB (both 0). If display still shows the old count while DB=0,
    the fix is incomplete — STOP and report which of Part A / Part B did not take.

Deliver: the vitest result, the BEFORE/AFTER DB rows + throughput, the clear/execute response, the
two screenshots (pre-clear count, post-clear 0), and a PASS/FAIL. STOP and report.
```

## §4 — Done when
Tracker display equals DB reality for a freshly-cleared asset with zero manual cache-busting, vitest
green, and the same guard demonstrably also corrects a stale `rows_written` left by a prior run.
