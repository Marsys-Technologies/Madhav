# Gate II.5 — Trace UI Visual Smoke Screenshots

Captured: 2026-05-13 (CROSS_GATE_VISUAL_SMOKE session)
QUERY_ID: `57fb6f82-135a-4fcf-b6d5-078b8d1a9a9a` (interpretive, 18 trace steps, audit_events row present)
Playwright run: 7/7 PASS

## Screenshots

| File | Content | Reviewer checklist |
|---|---|---|
| `drawer_full.png` | Full trace modal at 1440×900 | Three-column layout: lifecycle graph, step detail, health rail |
| `planning_container.png` | Planning sub-rows (classify, compose_bundle, plan_per_tool) | All 3 sub-rows visible; D9 alignment confirmed |
| `planner_compose_bundle.png` | PlannerDetail with compose_bundle focused | compose_bundle data rendered (not "did not fire") |
| `planner_plan_per_tool.png` | PlannerDetail with plan_per_tool focused | plan_per_tool data rendered; tool_count, planner_active, latency_ms visible |
| `retrieval_container.png` | Retrieval sub-rows (21 tools) | 21 rows present; unfired tools dimmed |
| `checkpoints_expanded.png` | Checkpoint group | Checkpoint stages visible |
| `audit_detail.png` | AuditDetail panel with real audit_events JOIN data | audit_event_id shows real UUID (not "—"); validator_verdict PASS; D11 columns "—" with tooltip (FU.2 pending) |
| `banner.png` | QueryHeaderStrip | Query metadata rendered |

## Bug Fixed in This Session

`TracePage` (`src/app/admin/trace/[query_id]/page.tsx`) accessed `params.query_id` synchronously. In Next.js 15, `params` is a Promise — the fix makes the component `async` and awaits params. Without this fix, `TraceModal` received `queryId = undefined`, causing all API calls to hit `/api/admin/trace/undefined` which returned placeholder audit data and empty planner sections.

## Re-run Command

```
SMOKE_SESSION_COOKIE=<firebase_session_cookie> \
SMOKE_QUERY_ID=57fb6f82-135a-4fcf-b6d5-078b8d1a9a9a \
npx playwright test tests/e2e/gate_ii_trace_smoke.spec.ts --reporter=list --workers=1
```
