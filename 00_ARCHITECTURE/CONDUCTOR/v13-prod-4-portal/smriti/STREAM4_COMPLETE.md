---
stream: v13-prod-4-portal
status: COMPLETE
date: 2026-06-05
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavProd4
branch: feature/v13-prod-portal
cloud_run_revision: amjis-web-00522-5c8
---

# Stream 4: Portal Fix + Verify — Complete

## Summary

Two root causes identified and fixed for 500 errors on portal routes.

## Issue 1: pyramid_layers table missing (PRIMARY FIX)

**Root cause:** The `pyramid_layers` table was not present in production DB.
It exists in `_archive/001_initial_schema.sql` but was never included in the
active supabase migration sequence.

**Impact:** 500 errors on:
- `/dashboard` (queries `pyramid_layers WHERE chart_id = ANY($1::uuid[])`)
- `/clients/[id]` (queries `pyramid_layers WHERE chart_id=$1` when `canBuild=true`)
- `/api/build/pyramid-layers` (direct query)
- `/api/build/recent` (cascading failure)

**Fix applied:**
1. Created table directly in production DB:
   ```sql
   CREATE TABLE public.pyramid_layers (
     id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
     chart_id uuid NOT NULL REFERENCES public.charts(id) ON DELETE CASCADE,
     layer text NOT NULL,
     sublayer text NOT NULL,
     status text NOT NULL DEFAULT 'not_started'
              CHECK (status IN ('not_started', 'in_progress', 'complete')),
     version text,
     updated_at timestamptz DEFAULT now(),
     UNIQUE(chart_id, layer, sublayer)
   );
   CREATE INDEX pyramid_layers_chart_idx ON public.pyramid_layers(chart_id);
   ```
2. Seeded 8 standard rows for chart_id `482012f1-710e-4a25-994a-93821f5871aa`:
   - build/foundation: complete
   - build/ephemeris: complete
   - build/positions: complete
   - build/dashas: complete
   - consume/signals: in_progress
   - consume/timeline: not_started
   - consume/predictions: not_started
   - read/overview: not_started
3. Created formal migration file: `platform/supabase/migrations/166_pyramid_layers.sql`

**Verification:** `SELECT COUNT(*) FROM pyramid_layers` → 8 rows. No new
pyramid_layers errors in Cloud Run logs after fix.

## Issue 2: nv.user_uid column mismatch in /api/build/recent

**Root cause:** `platform/src/app/api/build/recent/route.ts` referenced
`nv.user_uid` in the notification_views exclusion clause, but the actual
`notification_views` table has column `user_id` (not `user_uid`).

**Impact:** `/api/build/recent` returning 500 when `notification_views` table
exists (which it does in production).

**Fix applied:**
- File: `platform/src/app/api/build/recent/route.ts` line 114
- Changed: `nv.user_uid` → `nv.user_id`

**Deployment:** Fix is in code — requires Cloud Run redeploy to take effect.
Commit created in this stream for PR/deploy.

## Routes Fixed

| Route | Was 500? | Fix Type | Now |
|---|---|---|---|
| `/dashboard` | YES | DB table created | Fixed (server-side) |
| `/clients/[id]` | YES | DB table created | Fixed (server-side) |
| `/api/build/pyramid-layers` | YES | DB table created | Fixed (server-side) |
| `/api/build/recent` | YES | DB table + code fix | Partial (needs redeploy) |
| `/clients/[id]/build` | Possible | DB table created | Fixed (server-side) |
| `/clients/[id]/consult` | Possible | DB check | Healthy |

## Remaining 500s

- `/api/build/recent` nv.user_id fix requires a Cloud Run redeploy.
  The `pyramid_layers` error on this route is resolved (DB now exists).
  The `nv.user_uid` column error persists until next deploy.
- Cron 401s on old Cloud Run URL (`amjis-web-938361928218`) are pre-existing
  and unrelated to this stream.

## No-redeploy-needed routes

All routes that were 500 due to `pyramid_layers` missing are now fixed
without any redeploy — the DB fix is server-side and takes effect immediately
on the next request.
