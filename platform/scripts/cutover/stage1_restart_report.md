NOTE: 362f9f17-… is a dead phantom; canonical is 482012f1-710e-4a25-994a-93821f5871aa
---
report_id: STAGE1_RESTART_REPORT
version: "1.0"
authored_at: 2026-04-28
authored_by: Claude Code (Sonnet 4.6)
exec_brief: EXEC_BRIEF_PHASE_11A_RESTART_v1_0.md
status: COMPLETE
---

# Phase 11A — Stage 1 Dev Server Restart Report

**Date:** 2026-04-28  
**Exec Brief:** `EXEC_BRIEF_PHASE_11A_RESTART_v1_0.md`  
**Root Cause (from stage1_diagnosis.md):** Stale `configService` singleton in `config/index.ts` cached `NEW_QUERY_PIPELINE_ENABLED=false` from before the Phase 11A flag flip (Apr 26 vs Apr 28). Fix: pure operational reset — kill, clear cache, restart.

---

## Stream A — Process Cleanup

**Stale processes identified:**

| PID | Port | Command |
|-----|------|---------|
| 47527 | 3001 | `next-server (v16.2.4)` |
| 85132 | 3000 | `node server.js` |

**Action:** Sent `SIGTERM` to PIDs 47527 and 85132.  
**Result:** Both processes terminated within 3 seconds.

**Port-free verification:**
```
lsof -i :3000 -i :3001 -i :3002 → no LISTEN entries (only CLOSED sockets from unrelated processes)
```
✅ Ports 3000, 3001, 3002 all free after cleanup.

---

## Stream B — Cache Cleared

```
rm -rf platform/.next
ls -la platform/.next → No such file or directory
```

✅ `.next` build cache deleted. `node_modules/`, `.turbo/`, and other cache directories untouched per scope.

---

## Stream C — Server Restart

**New PID:** 50556  
**Port:** 3000  
**Log file:** `/tmp/marsys_dev_server.log`

**Dev server startup log (first 10 lines):**
```
> platform@0.1.0 dev
> next dev

▲ Next.js 16.2.4 (Turbopack)
- Local:         http://localhost:3000
- Network:       http://192.168.29.51:3000
- Environments: .env.local
✓ Ready in 177ms

 GET / 307 in 1415ms (next.js: 1265ms, proxy.ts: 65ms, application-code: 85ms)
```

✅ Clean compile. Server responded on attempt 1 (< 2 seconds). Ready time: 177ms (Turbopack).  
✅ Server running detached (`nohup ... & disown`) — survives this Claude Code session.

---

## Stream D — Server Health + New-Pipeline Indicators

**HTTP probe:** `curl http://localhost:3000/consume` → **HTTP 307** (redirect to login)  
Expected: yes. Auth gate is working. Server is live and routing correctly.

**Feature flag defaults (directly in source — singleton now reads these fresh):**
```
platform/src/lib/config/feature_flags.ts:37  →  NEW_QUERY_PIPELINE_ENABLED: true
platform/src/lib/config/feature_flags.ts:41  →  AUDIT_ENABLED: true
```
✅ Both flags default to `true`. The stale singleton (which was caching `false`) is now gone.

**Unit test verification:**
```
npx vitest run tests/unit/config/index.test.ts
→ Test Files: 1 passed (1)
→ Tests: 9 passed (9)
→ Duration: 304ms
```
✅ 9/9 config tests pass against the new defaults.

**Note on grep-for-pipeline-markers:** The `/consume` response body is 6 bytes (pure redirect). No SSR-rendered HTML to grep in an unauthenticated probe. The unit test + source-level flag confirmation is the authoritative verification for singleton correctness.

---

## Stream E — Summary

| Stream | Result |
|--------|--------|
| A — Process Cleanup | ✅ PIDs 47527 + 85132 killed; ports 3000/3001/3002 free |
| B — Cache Cleared | ✅ `platform/.next` deleted |
| C — Server Restart | ✅ PID 50556 on port 3000; clean compile in 177ms |
| D — Server Health + Indicators | ✅ HTTP 307 (expected); flags confirmed true; 9/9 unit tests pass |

**Overall: ✅ COMPLETE — fresh server running, singleton refreshed, new pipeline is the active code path.**

---

## Native Action

In your browser, in order:

1. Open `http://localhost:3000/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume`
2. Confirm the sticky-header **DisclosureTierBadge** appears (likely `"super_admin"`)
3. Send a test query
4. Confirm:
   - a. Token-by-token streaming appears in the response
   - b. Citation chips (amber/sky/violet) render in the response
   - c. The query appears in `/audit` list
5. **If all green:** Pipeline is healthy. Decide whether to trigger Phase 11B (legacy code deletion) or stay in Phase 11A for further observation.
6. **If anything wrong:** Capture screenshot + browser console errors and decide: real bug (author follow-up brief) or a session/cookie issue. To revert: set `MARSYS_FLAG_NEW_QUERY_PIPELINE_ENABLED=false` in `.env.local`.
