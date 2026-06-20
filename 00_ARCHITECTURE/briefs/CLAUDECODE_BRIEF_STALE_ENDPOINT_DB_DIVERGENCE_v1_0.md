# L0 Stale — Endpoint-vs-DB Divergence DIAGNOSIS (paste into Claude Code / Antigravity)

**STOP stamping timestamps. The fix already "succeeded" against the wrong target. This is a diagnosis brief.**

**Cowork verified via the LIVE cockpit endpoint (browser, authenticated session) AFTER migration 313:**
`GET /api/cockpit/stats?chartId=482012f1` → **still 20 stale, every L0 `bg_*` asset shows
`last_built_at=null`, state=lit.** Identical with AND without the chartId param (so it is NOT a chart-scoped vs
global DISTINCT-ON row collision — ruled out by probing both).

**The contradiction to resolve:** the migration-313 agent reported "all 8 global asset_throughput records
already have non-null last_built_at; UPDATE 0; zero null timestamps across all 41 rows" — measured against the
DB it connected to. **The endpoint returns null for 20 of those same assets.** The DB the agent stamped and the
DB/column the endpoint reads DISAGREE. Do not write another timestamp migration until you find WHY they diverge.

**⚠️ The agent made the exact substitution this whole thread warns against:** "the endpoint requires auth, let me
verify against the database instead." The endpoint is the user's truth; verifying against a DB that disagrees
with the endpoint is how this bug has survived three fix attempts.

---

## DIAGNOSE — find the divergence (read-only first)

Work through these in order; STOP at the first one that explains it:

1. **Same database?** (the localhost-data-plane trap, [[feedback-localhost-codeplane-prod-dataplane]]).
   - What connection string does the running Next.js dev server use for `/api/cockpit/stats`? (env: DATABASE_URL
     / the Cloud SQL proxy target / port 5433?)
   - What connection did the migration-313 apply + the agent's verification query use?
   - If they differ (branch/worktree DB vs the prod DB the dev server reads, or two different proxies) → the
     migration stamped one DB, the endpoint reads another. The `UPDATE 0` was true in the WRONG db. This is the
     branch-vs-prod trap one layer down. FIX: re-apply the timestamp backfill against the SAME database the dev
     server / prod endpoint actually reads, then re-verify via the endpoint.

2. **Same column / same source?** Read the stats route handler (`/api/cockpit/stats`). Find EXACTLY where
   `last_built_at` (and `build_state_stale`) come from:
   - Is it `asset_throughput.last_built_at` directly? Or a JOIN to `build_runs`/`build_run_assets`/another table?
   - Is `build_state_stale` derived from `last_built_at IS NULL`, or from a freshness window, or an
     upstream/content hash (the bg_nakshatra DEFER-005 hash class)?
   - If the route reads `last_built_at` from a DIFFERENT table/column than migration 313 updated → the agent
     fixed the wrong field. FIX: stamp the field the route actually reads.

3. **Same row identity?** For one asset (e.g. bg_ephemeris) run, against the DB THE DEV SERVER READS, the EXACT
   query the route runs (copy it from the handler, bind the same params). Compare its `last_built_at` to what the
   endpoint returns for bg_ephemeris. If the query returns non-null but the endpoint shows null → a mapping/
   serialization bug in the route (field renamed, wrong alias). If the query ALSO returns null → the agent's
   "non-null" reading was against a different DB/row (back to #1).

Output a short diagnosis: which of #1/#2/#3 it is, with the evidence (the connection strings, the route's actual
last_built_at source, the one-asset query result).

---

## FIX (only after diagnosis names the cause)

- If **#1 (wrong DB):** re-apply the `last_built_at` backfill to the database the dev-server/prod endpoint reads;
  ledger-reconcile there.
- If **#2 (wrong column/source):** stamp the field the route actually reads (or fix the route to read the field
  that IS populated); migration + route change as needed.
- If **#3 (route mapping bug):** fix the route's field mapping/alias.

---

## VERIFY — ENDPOINT ONLY, and PASTE THE JSON

Re-run, in the browser/authenticated context (or curl with the dev server's own auth), and PASTE the result:
```
GET /api/cockpit/stats?chartId=482012f1
→ build_state_stale=true count: MUST be 0
→ state=error count: MUST be 0 except bo_samskara (known L2, out of scope)
→ any last_built_at=null on a CURRENT bg_*/ga_* data asset: MUST be 0 (services excepted)
```
A DB query is NOT acceptable evidence this time — the DB is exactly what disagreed with reality. The endpoint
JSON is the only proof. Then screenshot `/clients/482012f1/nirmana` — zero stale badges.

**RAIL (record + obey):** when a report's DB-verification contradicts the endpoint, the ENDPOINT WINS and the
divergence itself is the bug to find — never paper over it with another migration. "Endpoint requires auth" is
not a reason to fall back to the DB; it's a reason to authenticate.

Report back: the diagnosis (#1/#2/#3 + evidence), the fix applied, and the ENDPOINT JSON showing stale=0.
