---
artifact: F1_SMOKE_DEFERRED.md
produced_during: CV2-FINAL-CLOSE
produced_on: 2026-05-21
status: DEFERRED
---

# F.1 Chrome MCP Smoke Tests — DEFERRED

## Status

Chrome DevTools MCP unavailable during CV2-FINAL-CLOSE execution. Error:
`The browser is already running for /Users/Dev/.cache/chrome-devtools-mcp/chrome-profile. Use --isolated to run multiple browser instances.`

## Target

Production revision: **amjis-web-00289-jcn** (post-B.1 R8 flags flip).

## Pending Verification Items

### B.2 — R8 Smoke (was SKIP_NO_CHROME_MCP)
- Slash command menu: type `/` in composer, verify menu appears
- Conversation export: open conversation menu, verify Export option
- Token estimate: verify token counter visible in composer chrome

### B.4 — Scroll/Validator Smoke (was SKIP_NO_CHROME_MCP)
- Scroll discipline: scroll up mid-stream, verify no auto-snap-to-bottom
- Validator gates: trigger a query, verify validator gate UI renders

## Operator Action Required

Manually verify the above checks against the production URL with chartId=362f9f17-95a5-490b-a5a7-027d3e0efda0, or re-run CV2-FINAL with Chrome DevTools MCP connected.

## Disposition

F.1 flipped to SKIP_DEFERRED in CLAUDECODE_BRIEF.md. CV2-FINAL arc proceeds to C.1 + C.2.
