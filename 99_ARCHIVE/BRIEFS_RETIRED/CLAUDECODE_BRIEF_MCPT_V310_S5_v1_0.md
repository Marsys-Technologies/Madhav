---
artifact: CLAUDECODE_BRIEF_MCPT_V310_S5_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.1.0-S5
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN
branch: feature/mcpt-foundation
depends_on: [v3.1.0-S3, v3.1.0-S4]
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: Operator dashboard at /admin/mcp/health (5 tabs) + alerting subsystem (Phase P5)
migration_number: 077
---

# v3.1.0-S5 — Operator Dashboard at /admin/mcp/health

You are a Claude Code sub-agent on WT-A. Implements perf brief Phase P5: the operator HTML dashboard with five tabs (Tool Health, Data Coverage, Audit Findings, Predictions/Calibration, Sessions) and the alerting subsystem.

Read: `MCP_PERF_SYSTEM_BRIEF_2026-05-22.md §7 (dashboard), §7.6 (alerts)`; parent brief §4 / v3.1.0-S5.

## §1 — Scope

Single HTML page at `/admin/mcp/health`, super_admin-only, five tabs, inline caveat editing, alert configuration, tool-disable toggle. Calibration tab is placeholder until v3.4-P6 lands the calibration MV.

## §2 — Files in scope

```
platform/src/app/admin/mcp/health/page.tsx                               # main page (5 tabs)
platform/src/app/admin/mcp/health/tabs/ToolHealth.tsx
platform/src/app/admin/mcp/health/tabs/DataCoverage.tsx
platform/src/app/admin/mcp/health/tabs/AuditFindings.tsx
platform/src/app/admin/mcp/health/tabs/PredictionsCalibration.tsx        # placeholder for v3.4-P6
platform/src/app/admin/mcp/health/tabs/Sessions.tsx
platform/src/app/admin/mcp/health/components/CaveatEditor.tsx
platform/src/app/admin/mcp/health/components/AlertThresholds.tsx
platform/src/app/admin/mcp/health/components/ToolDisableToggle.tsx
platform/src/lib/alerts/dispatch.ts                                      # Slack + email
platform/supabase/migrations/077_mcp_alerts_config_and_tool_registry.sql # alerts config + tool_registry
platform/test/admin/mcp/health/**                                        # new tests
```

## §3 — Files NOT in scope

```
platform/src/app/api/**                                                  # endpoints all built in S4
platform-mcp/**                                                          # MCP-side complete from S1–S4
```

## §4 — Per-tab spec

Per perf brief §7.1 through §7.5. Tab tables sortable; drill-down modals for findings/sessions; inline caveat editor with dropdown for `caveat_class`; alert thresholds configurable per metric.

## §5 — Alerting

`platform/src/lib/alerts/dispatch.ts` reads `mcp_alerts_config` and dispatches Slack/email when thresholds breach. Defaults per perf brief §7.6.

## §6 — Tool disable toggle

`tool_registry.tool_enabled` boolean. MCP primitives dispatcher (`platform/src/app/api/mcp/primitives/[tool]/route.ts`) checks before executing; returns 503 with `tool_disabled: true` envelope when false.

## §7 — Acceptance criteria (AC.S5.1 through AC.S5.6)

Per parent brief §4 / v3.1.0-S5.

## §8 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN && \
  test -f platform/src/app/admin/mcp/health/page.tsx && \
  test -f platform/src/app/admin/mcp/health/tabs/AuditFindings.tsx && \
  test -f platform/src/lib/alerts/dispatch.ts && \
  test -f platform/supabase/migrations/077_mcp_alerts_config_and_tool_registry.sql && \
  cd platform && npm test -- admin/mcp/health 2>&1 | tail -10
```

## §9 — Sealing artifact

`00_ARCHITECTURE/MCPT_V310_S5_CLOSE.md`. Body: dashboard screenshots (or HTML smoke output), alert-dispatch test evidence, AC table.

---

*End of CLAUDECODE_BRIEF_MCPT_V310_S5_v1_0.md.*
