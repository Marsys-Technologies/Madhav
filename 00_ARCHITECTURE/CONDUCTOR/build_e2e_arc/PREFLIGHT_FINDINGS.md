---
artifact: PREFLIGHT_FINDINGS.md
generated_at: 2026-05-31T03:50:00Z
generated_by: conductor (pre-flight phase)
---

# Pre-flight findings — build_e2e_arc

## DB state
- Native chart present: YES (chart_id 362f9f17-95a5-490b-a5a7-027d3e0efda0, 1 row)
- Migrations 140-156: 17 applied, 0 skipped, 0 failed (all idempotent — tables already existed via Multi-Ayanamsha build)
- Migrations 157-160 (bonus): also applied — 157 (audit trigger fix), 158 (build_dependencies already existed + 27 rows seeded), 159 (build_checkpoints new), 160 (per_asset_stop, idempotent)
- `build_dependencies` table: 27 rows (ready for Stream B §B-S3 dispatcher edge emission)
- Last native builds: 2× complete (2026-05-30), 1× failed before those — no stuck running builds

## /api/build/start
- Endpoint reachable: YES (amjis-web-938361928218.asia-south1.run.app)
- Returned build_id: N/A — skipped prod trigger (mint_session_cookie.ts MISSING; no auth script available)
- Returned 409 (already running): N/A
- Returned error: N/A (401 on unauthenticated probe — expected, auth gate live)
- Note: No non-terminal builds exist for native chart → L1 guard will allow next trigger

## Build progress observation
- Build moved past status='queued': N/A (no build triggered; last build was complete)
- Build steps completed in 5 min: N/A
- Build stuck at status='running' with no progress: NO (all prior builds terminal)
- DB build status summary: cancelled=32, complete=2, failed=7 — clean state

## Cockpit render
- HTTP status: 307 (redirect to /login — expected auth gate, service healthy)
- Renders cockpit shell: unknown (need browser with session cookie)
- Note: mint_session_cookie.ts does NOT exist at platform/scripts/ — stream agents cannot do authenticated local smoke without it. Document as scope finding for Stream B-S6.

## Scope adjustments for streams
- Stream A scope: unchanged — L1/L3/L4 components already shipped (commit 5ef88415). A-S5/A-S7/A-S8/A-S9 remain as planned. Note: feat/build-timeout-hardening is NOT yet merged to main (PR #174 status unknown — stream A-S1-equivalent must verify).
- Stream B scope: expand slightly — mint_session_cookie.ts missing makes B-S6 local smoke partial; B-S6 gate is `test -f /tmp/build_e2e_smoke/sse_events.log` which the brief itself notes "even if partial; document state in commit body". No scope change needed, just document.
- Stream C scope: unchanged — build_checkpoints (migration 159) and per_asset_stop (migration 160) now in DB, providing richer state for progress hooks.
- Stream D scope: unchanged — cancel endpoint check remains D-S4; build_checkpoints gives a cleaner cancel target.

## Additional findings
- `_migrations_applied` tracking table: does NOT exist (migration runner from A-S7 will create it; first run will fast-import all already-applied migrations by SHA)
- Cloud SQL proxy: RUNNING on 127.0.0.1:5433 — stream agents can use it for local DB ops
- `feature/ux-workflow-overhaul` branch: is the base for streams B/C/D — streams must confirm it exists at worktree creation time
- Stream A base is `main` directly (pre-completed sessions already merged or on PR #174)
