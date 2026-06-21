# L0 Stale-Timestamp Fix — the 20 L0 globals (paste into Claude Code / Antigravity)

**Context:** The prior cockpit-stats fix (migration 312 + route `WHERE chart_id=$1 OR chart_id IS NULL`)
RESOLVED: the L1 `"there is no parameter $1"` error (gone), the 3 NULL floors (set: bg_reference 1485 /
bg_ontology 623 / bg_nakshatra 2857), the ga_condition combined count_sql, and the L1 per-chart stale states.
BUT the report's "0 stale across all layers" is NOT what the live endpoint returns. Verified via
`/api/cockpit/stats?chartId=482012f1`:

**20 L0 assets show `build_state_stale=true`** — EVERY `bg_*` data asset. Per-asset detail: each has
`state="lit"`, correct `actual_rows`, BUT **`last_built_at=null`**. Examples: bg_ephemeris (825,084 rows, lit,
lb=null), bg_texts (10,651, lit, lb=null), bg_reference/bg_ontology/bg_nakshatra/bg_dignity_reference/
bg_transit_engine/bg_nakshatra_medical — all lit, all lb=null.

**Root cause (precise):** the cockpit derives `build_state_stale` from `last_built_at` (null timestamp →
stale). Migration 312 updated `state='lit'` and fixed the L1 per-chart assets, but did NOT populate
`last_built_at` on the L0 GLOBAL `asset_throughput` records. Separately, the route change (`… OR chart_id IS
NULL`) means the cockpit now SUCCESSFULLY READS those global throughput rows for the first time — previously
the `WHERE chart_id=$1` query silently missed them. So the route fix made all 20 global records VISIBLE, and
they all carry a null `last_built_at` → 20 stale where before only ~3 showed. The fix surfaced the problem
rather than completing it.

**This is NOT a data problem** — every asset is `lit` with correct rows. It is purely the missing build
timestamp on the global throughput records.

---

## FIX — populate `last_built_at` on the L0 global asset_throughput records (migration 313)

For every L0 global asset (scope=global / `chart_id IS NULL` throughput row) whose `last_built_at` is null but
`state='lit'` and rows>0: set `last_built_at`.
- **Preferred:** set it to the actual last build time if recoverable (e.g. from a build_runs / build_run_assets
  record, or the max(updated_at) on the underlying data table). This is the truthful timestamp.
- **Acceptable fallback:** if no real build time is recoverable, stamp `now()` — the data IS current and lit;
  the timestamp was simply never written. Document in the migration comment that this is a backfill stamp.

```sql
-- migration 313 (number ABOVE main's max — confirm; L1 went to 312)
UPDATE asset_throughput
SET last_built_at = COALESCE(last_built_at, <real-build-time-or-now()>)
WHERE chart_id IS NULL                       -- global L0 records
  AND state = 'lit'
  AND last_built_at IS NULL;
```
Confirm the WHERE matches the global records via `IS NULL` (not `= %s`) — the global-record-matching trap.
Apply surgically to PROD + ledger-reconcile (`_migrations_applied`, correct SHA). No seed change (throughput is
runtime state, not seed). If the cockpit's `build_state_stale` derivation ALSO checks a freshness window
(last_built_at older than N), confirm `now()` clears it; if it checks against an upstream-hash/content-hash
(the bg_nakshatra DEFER-005 class), note that separately — but the immediate null-timestamp fix is the lever.

---

## VERIFY — via the ENDPOINT, all layers (the standing rail)

After migration 313, hit the actual cockpit data path and assert clean:
1. `GET /api/cockpit/stats?chartId=482012f1` →
   - `build_state_stale=true` count = **0** (was 20). Every L0 `bg_*` data asset: stale=false, last_built_at
     non-null.
   - L1 `ga_*`: still lit, non-null rows, no error (don't regress the param-binding fix).
   - Services (bg_ephemeris_engine, bg_panchanga, ga_pyjhora_engine) correctly have null rows — that is fine
     (health pill, not a bar); do NOT "fix" them.
   - Only acceptable remaining error: `bo_samskara` ("column chart_id does not exist") — KNOWN L2 Bodha schema
     issue, OUT OF SCOPE here (log it for the L2 work, do not fix in this brief).
2. Load `/clients/482012f1/nirmana`, expand Brahma Jñāna + Gaṇita: all bars filled, **zero "build-state stale"
   badges**, no red, no empty bars. Screenshot to confirm.
3. CI green; merge-verify; migration 313 ledger-reconciled on prod.

**Standing rail (already recorded, re-affirm):** "0 stale / cockpit green" is only TRUE when
`/api/cockpit/stats?chartId=…` returns it — NOT when a report asserts it. The two diverge; the endpoint is the
user's truth. Every cockpit-fix claim must paste the endpoint JSON (stale-count=0, error-count=0-except-known-L2)
as evidence.

Report back: the stats-endpoint JSON summary (stale count, error count) + the cockpit screenshot.
