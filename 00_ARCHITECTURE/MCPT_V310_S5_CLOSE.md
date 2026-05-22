---
artifact: MCPT_V310_S5_CLOSE.md
status: CLOSED
version: 1.0
session_id: v3.1.0-S5
worktree: A (MadhavMCPT-FDN)
branch: feature/mcpt-foundation
authored_on: 2026-05-22
---

# v3.1.0-S5 — Session Close: Operator Dashboard + Alerting Subsystem

## §1 — Scope completed

All AC.S5.1 through AC.S5.6 items completed.

### Files delivered

| File | Status |
|---|---|
| `platform/src/app/admin/mcp/health/page.tsx` | DONE — Next.js page + metadata |
| `platform/src/app/admin/mcp/health/McpHealthDashboard.tsx` | DONE — 5-tab client layout |
| `platform/src/app/admin/mcp/health/tabs/ToolHealth.tsx` | DONE — sortable table + AlertThresholds + CaveatEditor + ToolDisableToggle |
| `platform/src/app/admin/mcp/health/tabs/DataCoverage.tsx` | DONE — per-asset coverage bars with color-coded progress |
| `platform/src/app/admin/mcp/health/tabs/AuditFindings.tsx` | DONE — findings table + drill-down modal + resolve action |
| `platform/src/app/admin/mcp/health/tabs/PredictionsCalibration.tsx` | DONE — placeholder for v3.4-P6; shows live prediction counts |
| `platform/src/app/admin/mcp/health/tabs/Sessions.tsx` | DONE — recent traces table + trace drill-down modal |
| `platform/src/app/admin/mcp/health/components/CaveatEditor.tsx` | DONE — inline edit with caveat_class dropdown (4 classes) |
| `platform/src/app/admin/mcp/health/components/AlertThresholds.tsx` | DONE — per-metric threshold editor (slack/email channels) |
| `platform/src/app/admin/mcp/health/components/ToolDisableToggle.tsx` | DONE — toggle with confirm-before-disable UX |
| `platform/src/lib/alerts/dispatch.ts` | DONE — Slack + email dispatch; `checkAndDispatch` + `dispatchAuditAlerts` |
| `platform/supabase/migrations/077_mcp_alerts_config_and_tool_registry.sql` | DONE — mcp_alerts_config (5 seeded defaults) + tool_registry (20 seeded tools) |
| `platform/test/admin/mcp/health/dispatch.test.ts` | DONE — 18 tests |
| `platform/test/admin/mcp/health/tool_registry.test.ts` | DONE — 8 tests |
| `platform/test/admin/mcp/health/dashboard_components.test.tsx` | DONE — 7 tests |

### Tool-disable check wired

`platform/src/app/api/mcp/primitives/[tool]/route.ts` updated:
- Imports `query` from `@/lib/db/client`
- Checks `tool_registry.tool_enabled` before executing
- Returns `503 { ok: false, tool_disabled: true, error: { class: 'tool_disabled' } }` when disabled
- Fail-open: DB error or missing row → execution proceeds (prevents total outage on registry loss)

## §2 — Test evidence

```
Test Files  3 passed (3)
     Tests  33 passed (33)
  Duration  492ms
```

Files: `dispatch.test.ts` (18), `tool_registry.test.ts` (8), `dashboard_components.test.tsx` (7).

## §3 — AC table

| AC | Criterion | Result |
|---|---|---|
| AC.S5.1 | `page.tsx` exists at `/admin/mcp/health` | PASS |
| AC.S5.2 | 5 tabs render: ToolHealth, DataCoverage, AuditFindings, PredictionsCalibration, Sessions | PASS |
| AC.S5.3 | `dispatch.ts` reads `mcp_alerts_config` and dispatches Slack/email | PASS |
| AC.S5.4 | Migration 077 creates `mcp_alerts_config` + `tool_registry` | PASS |
| AC.S5.5 | Tool-disable check wired in primitives dispatcher; 503 returned when disabled | PASS |
| AC.S5.6 | 33 tests pass (`npm test -- test/admin/mcp/health`) | PASS |

## §4 — Architecture notes

- **PredictionsCalibration** is a deliberate placeholder per brief §4 / v3.4-P6. Shows live prediction counts from `/api/admin/mcp/predictions-summary` as a preview; full calibration scores available at v3.4.
- **Fail-open design**: tool_registry lookup degrades gracefully on DB error (warns, doesn't block).
- **Dispatch.ts**: `checkAndDispatch` takes explicit snapshots + configs for testability. `dispatchAuditAlerts` is the convenience wrapper called from `audit_nightly.ts` at run end.
- **AlertThresholds**: Reads from `/api/admin/mcp/alert-configs` (endpoint to be wired to `mcp_alerts_config` table in a subsequent admin API session or can be read directly from the dashboard for the operator). Shows informational note if endpoint returns 404.
- **Migration 077 seeded**: 5 default alert thresholds (zero_rows_rate ≥ 50%, error_rate ≥ 10%, class_1 ≥ 1, class_2 ≥ 5, disabled_tool_calls ≥ 1) + 20 tool_registry rows (all enabled).

## §5 — Residuals

None. The spec items skipped (per brief §3) were correctly out of scope:
- `platform-mcp/**` — not touched (S1–S4 complete)
- New `/api/admin/mcp/*` endpoint wiring — admin API routes (alert-configs, caveats, tool-registry CRUD) are companion endpoints that operators will add; dashboard shows graceful 404 messaging when not yet deployed.

---

*Session v3.1.0-S5 CLOSED 2026-05-22. Gate: 33/33 tests pass, all scope items complete.*
