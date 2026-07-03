---
canonical_id: CLAUDECODE_BRIEF_MCP_M2_CHART_SELECTION
version: 1.0
status: READY-FOR-EXECUTION — M2 chart selection (the "like the portal" experience)
created: 2026-06-30
author: Cowork (planning) — detail-pass for the autonomous swarm
parent_charter: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (PHASE M2)
depends_on: M1 (getEntitledCharts + resolveMcpPrincipal)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4
verification_basis: live code, read 2026-06-30
hard_constraints:
  - show NAMES not raw UUIDs (provider-spec: resolve UUIDs→human-meaningful)
  - every per-chart op still entitlement-gated (M0); selection is convenience, NOT a bypass
  - VITEST; chart-agnostic gate green
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — MCP M2: CHART SELECTION

> Today the LLM must pass a raw `chart_id` UUID to every tool. M2 gives the portal-like experience: list your
> entitled charts by name, pick one, and have it carry forward. Three parts, parallelizable. Selection NEVER
> weakens entitlement — every call still hits the M0 gate; selection just supplies the chart_id ergonomically.

## §1 — M2.1 `list_my_charts` tool
A new MCP tool (chart-AGNOSTIC at the param level — takes no chart_id; it's "my charts"). Consumes
`getEntitledCharts(principal.uid, principal.role, db)` from M1. Returns, per chart: `display_name`
(`COALESCE(preferred_name, subject_name, name)`), a stable `chart_id`, and optionally a 0-indexed label so the
LLM can say "chart 1" (Anthropic guidance: prefer names / 0-indexed over raw UUIDs). Output through the uniform
MCP envelope (outputSchema + structuredContent + text fallback — see M8's envelope; if M8 envelope not yet
built, ship text+structuredContent here and retrofit). NO raw-UUID-only output.

## §2 — M2.2 `select_chart` / active-chart mechanism
Because the server is stateless today (`sessionIdGenerator: undefined`), "active chart" needs somewhere to
live. Two-tier:
- **Param-carried (works now, stateless):** every per-chart tool keeps accepting `chart_id`; `select_chart`
  validates the chosen chart is entitled (calls `authorizeChartAccess`, deny→error) and returns it as the
  canonical id the client should pass forward. This works without session state.
- **Session-recorded (lands with M3):** once M3's session store exists, `select_chart` also persists the active
  chart per (user × session) so subsequent calls can omit chart_id. **M2 builds the param-carried path; the
  session-persisted path is wired in M3.** Flag this dependency; do not build a bespoke store in M2.

## §3 — M2.3 Charts as MCP resources
Expose the entitled chart set as MCP resources so compatible clients (Claude Desktop) render a native
chart-picker. Use a resource template `marsys://chart/{chart_id}` listing entitled charts (names) — and
entitlement-gate the per-chart resource read exactly like a tool (M0 gate). NOTE the M0 finding: the existing
`marsys://chart-snapshot` resource was a hidden per-chart leak — ensure M2's chart resources are gated and
name-resolving, and that chart-snapshot was parametrized+gated (or removed) in M0. Reuse `registerResources()`
(now live, `server.ts:149`).

## §4 — Acceptance criteria
- `list_my_charts` returns only the caller's entitled charts, by display name (+ stable id / 0-indexed),
  never an unscoped list, never raw-UUID-only. Verified: user A's list ⊆ A's entitlement; super_admin sees all.
- `select_chart` validates entitlement (deny on unentitled) and returns the canonical chart_id; param-carried
  selection works statelessly; the session-persist hook is stubbed for M3.
- Chart resources are entitlement-gated and name-resolving; no resource serves an unentitled or native-default
  chart to a stranger.
- All three parts went through the uniform envelope; Vitest; chart-agnostic gate green; retrieval FROZEN.

## §5 — VERIFICATION PHASE (mandatory; phase NOT done until ALL pass — independent Auditor)
**V1 — Build gate:** `platform-mcp` + `platform` both `npm run build` exit 0; `typecheck-mcp` CI green.
**V2 — Tests:** `list_my_charts` (returns entitled set by name, never raw-UUID-only, never unscoped),
`select_chart` (validates entitlement, deny on unentitled, returns canonical id) — Vitest green; no native name.
**V3 — Deploy + revision match:** deployed amjis-mcp revision SHA == merged SHA.
**V4 — Behavioral proof on PROD (≥2 users × ≥2 charts; guest key for deny):**
  - guest A → `list_my_charts` returns ONLY A's entitled charts, by display_name (`COALESCE(preferred_name,
    subject_name, name)`), with stable id; B's charts absent; output is NOT raw-UUID-only.
  - guest A → `select_chart(<chart A owns>)` → success returns canonical chart_id; `select_chart(<B's chart>)`
    → AUTHZ_DENIED.
  - chart resources: a per-chart resource read for an UNENTITLED chart → denied (regression-guards the M0
    chart-snapshot hidden-leak class); entitled read → 200.
  - super_admin → `list_my_charts` == all charts.
**V5 — Invariants:** retrieval untouched (git diff zero in lib/retrieval); entitlement still enforced per call
(selection is convenience, NOT a bypass — prove a selected-then-called unentitled chart still denies);
chart-agnostic gate green.
**On ANY V-failure:** remediation loop (charter §4); no advance until V1–V5 pass.

*End of CLAUDECODE_BRIEF_MCP_M2_CHART_SELECTION v1.0. Next: M3 adds the session store that makes select_chart sticky.*
