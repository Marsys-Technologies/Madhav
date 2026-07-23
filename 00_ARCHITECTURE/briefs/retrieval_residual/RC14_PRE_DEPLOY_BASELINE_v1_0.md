---
artifact: RC14_PRE_DEPLOY_BASELINE_v1_0.md
canonical_id: RC14_PRE_DEPLOY_BASELINE
version: 1.0
status: CURRENT
governed_by: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §I
captured_by: Claude Code (Sonnet 5), RC-14 conductor session
captured_at: 2026-07-23T07:2x UTC (immediately before merging/deploying PR #726)
---

# RC-14 pre-deploy probe re-snapshot

Per brief §I ("re-snapshot the probe baseline" before a batched deploy), this is a
targeted re-snapshot immediately before RC-14's breaking deploy (PR #726, merge
commit `7a0954b4`), captured against the live `mcp__marsys-jis-direct__*` connector
— the state RC-14 is about to change. This supplements, not replaces, the original
W0 baseline (`retrieval_impl/BASELINE_PROBES.md`, 2026-07-19, 37 calls) — that
baseline predates the entire retrieval campaign and RC-01..RC-13; this snapshot is
scoped specifically to the names RC-14 is about to remove/rename, so the post-deploy
live verification has a precise "before" to diff against.

## Pre-deploy state (captured live, this session, before merge)

| Call | Result | Notes |
|---|---|---|
| `list_my_charts` | `ok:true`, 4 charts returned | **Being renamed to `catalog_charts_list`** — confirmed working under the OLD name pre-deploy |
| `select_chart(482012f1)` | `ok:true`, `provenance_stamp` returned | **Being renamed to `catalog_chart_select`** — confirmed working under the OLD name pre-deploy |
| `ganita_dashas_get(482012f1)` | 89 dasha rows, `total:89`, trimmed to 44 | Canonical name, unaffected by RC-14 — confirms the underlying data/serving layer is healthy and unrelated to the deploy, useful as a control |

## What RC-14 changes (for the post-deploy diff)

- 43 legacy MCP tool names (per `canonical_faces.json`'s `deprecated_aliases`) will
  become unresolvable. Pre-deploy: these currently work (per `main`'s prior state,
  confirmed by this campaign's own earlier live traces — e.g. RC-01's use of
  `list_my_charts` above).
- `list_my_charts` → `catalog_charts_list`, `select_chart` → `catalog_chart_select`,
  `recall_session` → `session_recall`, `list_my_sessions` → `session_list`,
  `holistic_bundle_chart_facts` → `bodha_bundle_get`, `kala_temporal_bundle` →
  `kala_bundle_get`.
- `RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED` flips to `true` by default; `query_spine_bundle`
  becomes reachable (was 404 pre-deploy).
- `COMPILER_VERSION` bumps 1.0.0→2.0.0, changing the vidhi capability-version hash so
  `notifications/tools/list_changed` fires for connected clients presenting a stale
  version.

Post-deploy live verification (this campaign's own DONE bar for RC-14) is recorded
separately in `RESIDUAL_CLOSURE_FINAL_REPORT.md`'s RC-14 section once captured.
