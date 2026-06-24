---
artifact: MCPT_V310_CLOSE.md
canonical_id: MCPT_V310_CLOSE
status: CLOSED
version: 1.0
authored_by: Claude Code sub-agent (Sonnet 4.6)
authored_on: 2026-05-22
project: MCP Transformation
phase: v3.1.0 Foundation
session_id: v3.1.0-S6
worktree: A (MadhavMCPT-FDN)
branch: feature/mcpt-foundation
parent_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md
parent_plan: 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md
changelog:
  - v1.0 (2026-05-22, v3.1.0-S6): Foundation phase sealed. All 6 sub-sessions
      (S1–S6) CLOSED with full AC evidence. feature/mcpt-foundation merged to
      feature/mcpt-final. MARSYS_FLAG_MCP_V3_ENABLED default flipped to true.
      Mirrors MP.1 + MP.2 updated to adapted parity.
---

# MCPT v3.1.0 Foundation — Phase Close Artifact

This document seals the v3.1.0 Foundation phase of the MCP Transformation workstream. All 6 sub-sessions (S1 through S6) are CLOSED. The `feature/mcpt-foundation` branch has been merged into `feature/mcpt-final` as the first worktree to complete its wave contribution.

---

## §1 — Per-Sub-Phase Acceptance Criteria Evidence

### v3.1.0-S1 — Code-Level Fixes

| AC | Item | Result |
|---|---|---|
| AC.S1.1 | F.1 vector_search placeholder-query fix | PASS |
| AC.S1.2 | F.2 msr_sql params.domain + LIMIT fix | PASS |
| AC.S1.3 | F.3 enum-derived description for query_chart_facts | PASS |
| AC.S1.4 | F.4 MCP_INTERNAL_TOKEN from Secret Manager in cloudbuild.yaml | PASS |
| AC.S1.5 | F.5 60s SHA-256-keyed in-memory Bearer token cache | PASS |
| AC.S1.6 | F.7 token-budget allocation call removed from MCP execute path | PASS |

Commits: 9ac54011 (F.1), 2edf825f (F.2), 5af0c7fe (F.3), c50e210f (F.4), 8c48fd44 (F.5), 504b7a05 (F.7).

Close artifact: `00_ARCHITECTURE/MCPT_V310_S1_CLOSE.md`.

### v3.1.0-S2 — Bundles + SSE Streaming

| AC | Item | Result |
|---|---|---|
| AC.S2.1 | `holistic_bundle` MCP tool registered + delegates to executeHolisticBundle | PASS |
| AC.S2.2 | `multi_school_bundle` MCP tool registered + delegates to executeMultiSchoolBundle | PASS |
| AC.S2.3 | Both bundles: parallel `Promise.allSettled` with per-sub-tool 8s timeouts | PASS |
| AC.S2.4 | Error isolation: failed sub-tool recorded in `bundle_entries[].error` | PASS |
| AC.S2.5 | Bundle cache: SHA-256 key = bundleName + queryText + compositionParams + tier + chartId | PASS |
| AC.S2.6 | SSE endpoint `/api/mcp/bundles/[name]/route.ts` streams lifecycle events | PASS |
| AC.S2.7 | Migration 072 (`mcp_bundle_cache`): cache_key PK, envelope_json JSONB, expires_at, expiry index | PASS |
| AC.S2.8 | 25 vitest tests pass (cache:6, holistic_bundle:7, multi_school_bundle:6, SSE:6) | PASS |

Merge commit: 61a6ebf1. Close artifact: `00_ARCHITECTURE/MCPT_V310_S2_CLOSE.md`.

### v3.1.0-S3 — 5 MCP Resources + Tier-Variant House-Rules

| AC | Item | Result |
|---|---|---|
| AC.S3.1 | 5 resources registered: marsys://chart-overview, marsys://house-rules, marsys://active-dashas, marsys://capabilities, marsys://chart-snapshot | PASS |
| AC.S3.2 | `marsys://house-rules` returns tier-conditioned content: super_admin / acharya / client | PASS |
| AC.S3.3 | All 3 house-rules variants authored with PPL, B.11, cite-allowlist, school commitments | PASS |
| AC.S3.4 | `marsys://chart-snapshot` returns FORENSIC-grounded birth + D1 + topSignals JSON | PASS |
| AC.S3.5 | `marsys://capabilities` returns live tool list + tier permissions | PASS |
| AC.S3.6 | Tool descriptions regenerated via description_builder | PASS |

Merge commit: 6ce019f3. Close artifact: `00_ARCHITECTURE/MCPT_V310_S3_CLOSE.md`.

### v3.1.0-S4 — Perf System (P0–P4) + Nightly Audit

| AC | Item | Result |
|---|---|---|
| AC.S4.1 | Migration 073: `tool_execution_log` extensions (6 heuristic columns + partial index) | PASS |
| AC.S4.2 | Migration 074: `mcp_audit_findings` + `audit_job_runs` | PASS |
| AC.S4.3 | Migration 075: `mcp_predictions` extensions + `mcp_prediction_outcomes` | PASS |
| AC.S4.4 | Migration 076: `data_source_expected` + `tool_caveats` | PASS |
| AC.S4.5 | `tool_health` MCP tool registered (super_admin + acharya only) | PASS |
| AC.S4.6 | `data_coverage` MCP tool registered (super_admin + acharya only) | PASS |
| AC.S4.7 | Nightly audit job (`audit_nightly.ts`): 6 regex-only heuristic checks, no LLM calls | PASS |
| AC.S4.8 | `get_trace` enriched with audit findings | PASS |
| AC.S4.9 | 48 perf tests PASS (platform) + 75 tests PASS (platform-mcp) | PASS |

Merge commit: 7f5dd13f. Close artifact: `00_ARCHITECTURE/MCPT_V310_S4_CLOSE.md`.

### v3.1.0-S5 — Operator Dashboard + Alerting

| AC | Item | Result |
|---|---|---|
| AC.S5.1 | `page.tsx` at `/admin/mcp/health` | PASS |
| AC.S5.2 | 5 tabs: ToolHealth, DataCoverage, AuditFindings, PredictionsCalibration, Sessions | PASS |
| AC.S5.3 | `dispatch.ts`: reads `mcp_alerts_config`, dispatches Slack + email | PASS |
| AC.S5.4 | Migration 077: `mcp_alerts_config` + `tool_registry` (seeded: 5 alert defaults + 20 tools) | PASS |
| AC.S5.5 | Tool-disable check wired in primitives dispatcher; 503 on disabled tool | PASS |
| AC.S5.6 | 33 tests pass (`dispatch.test.ts` 18, `tool_registry.test.ts` 8, `dashboard_components.test.tsx` 7) | PASS |

Merge commit: 369d789a. Close artifact: `00_ARCHITECTURE/MCPT_V310_S5_CLOSE.md`.

### v3.1.0-S6 — Foundation Sealing (this session)

| AC | Item | Result |
|---|---|---|
| AC.S6.1 | House-rules variants finalized (no corrections required from S3/S4 audit findings) | PASS |
| AC.S6.2 | `MARSYS_FLAG_MCP_V3_ENABLED` added to `feature_flags.ts`; default `true` | PASS |
| AC.S6.3 | `MCPT_V310_CLOSE.md` authored with per-phase AC evidence table | PASS |
| AC.S6.4 | `CANONICAL_ARTIFACTS_v1_0.md §1` — MCPT_V310_CLOSE artifact registered | PASS |
| AC.S6.5 | `CAPABILITY_MANIFEST.json` — v3.1.0 MCP server entries added | PASS |
| AC.S6.6 | `CLAUDE.md §E` — MCP Transformation workstream entry updated | PASS |
| AC.S6.7 | `SESSION_LOG.md` — v3.1.0-S6 entry appended | PASS |
| AC.S6.8 | `CURRENT_STATE_v1_0.md` — state pointer updated | PASS |
| AC.S6.9 | `.geminirules` + `.gemini/project_state.md` — MP.1/MP.2 adapted parity updates | PASS |
| AC.S6.10 | `feature/mcpt-foundation` merged to `feature/mcpt-final` | PASS |

---

## §2 — Migration Number Audit (072–077 — MCPT foundation range)

The MCPT foundation phase reserved migrations 072–079. Six migrations landed in the 072–077 range:

| Number | Filename | Sub-session | Schema object |
|---|---|---|---|
| 072 | `072_mcp_bundle_cache.sql` | S2 | `mcp_bundle_cache` (content-addressable 5-min cache) |
| 073 | `073_perf_log_extensions.sql` | S4 | `tool_execution_log` extensions (6 heuristic columns) |
| 074 | `074_audit_findings.sql` | S4 | `mcp_audit_findings` + `audit_job_runs` |
| 075 | `075_prediction_outcomes.sql` | S4 | `mcp_prediction_outcomes` + `mcp_predictions` brier_score |
| 076 | `076_data_source_expected_and_caveats.sql` | S4 | `data_source_expected` + `tool_caveats` |
| 077 | `077_mcp_alerts_config_and_tool_registry.sql` | S5 | `mcp_alerts_config` + `tool_registry` |

Range 078–079 remains available for v3.2+ phases.

**Pre-existing collision note (non-blocking):** Numbers 070 and 071 each have two files in `platform/supabase/migrations/` — a collision inherited from the branch before MCPT work began:
- `070_mcp_api_keys.sql` (MCP v1 workstream, PR #127) and `070_capability_tool_registry.sql` (M5 Coverage Campaign, PR #120 / COV-S9)
- `071_mcp_predictions_disagreements.sql` (MCP v1) and `071_sade_sati_cycles.sql` (M5 Coverage, PR #122 / COV-S10)

This collision is present on `main` as well (confirmed by `git ls-tree main platform/supabase/migrations/`). It predates the MCPT project and is not introduced or worsened by MCPT work. Supabase migration tooling uses the full filename as the key (not just the numeric prefix), so both are applied independently. Resolution is a governance task for a subsequent hygiene session — tracked as a residual below.

---

## §3 — House-Rules Finalization

Review of S3/S4 audit findings produced no corrections to the tier-conditioned house-rules content. All three variants (`super_admin.md`, `acharya.md`, `client.md`) are accepted as-authored in S3. Key invariants verified:

- All three variants contain: cite-allowlist contract, B.11 floor, PPL discipline, school-commitment precedence order (Parashara primary → Jaimini → KP → Tajaka).
- `super_admin.md`: full audit commentary, operator-side audit subsystem description, per-tier output template.
- `acharya.md`: full analysis template without internal audit commentary.
- `client.md`: compact ≤800 token template, Sanskrit glossing mandate, Parashara-primary with Jaimini/KP/Tajaka surfaced only when clearly relevant.
- No `public_redacted.md` changes required (that variant is correctly minimal).

---

## §4 — Residual Risks

| ID | Description | Severity | Resolution |
|---|---|---|---|
| RES.S6.1 | Migration 070/071 filename collision (pre-existing on `main`, not introduced by MCPT) | LOW | Track in subsequent governance hygiene session; Supabase uses full filename key so both apply independently |
| RES.S6.2 | `MARSYS_FLAG_MCP_V3_ENABLED` is a code-level flag only — no deploy.yml build-arg added (server-side only; sidecar-scoped) | INFO | Correct by design: this is a server-side flag; no build-arg needed |
| RES.S6.3 | PredictionsCalibration tab is a placeholder per brief §4/v3.4-P6 | KNOWN | Full calibration scores land at v3.4 |
| RES.S6.4 | `/api/admin/mcp/*` companion endpoints (alert-configs, caveats, tool-registry CRUD) not yet wired | LOW | Dashboard shows graceful 404 messaging; companion endpoints are operator-add tasks |
| RES.S6.5 | F.6 (shared.ts synthesis-prompt template touch) out of scope — per brief §3 | DEFERRED | Explicitly excluded from v3.1.0; not a v3.1.0 gap |

---

## §5 — v3.2 Entry Conditions

v3.2 Classical Grounding (WT-B/C/D) may begin when:

1. This sealing artifact (`MCPT_V310_CLOSE.md`) exists and status is `CLOSED`. ✓ (this file)
2. `feature/mcpt-foundation` has been merged to `feature/mcpt-final` (WT-A wave contribution complete). ✓ (this session)
3. Source data populated in `00_ARCHITECTURE/SOURCE_DATA/` per master plan §6:
   - `bphs_chapters.json` (BPHS chapter-by-chapter index)
   - `jaimini_sutram.md` (Jaimini Sutras text)
   - `kp_reader_1_6.md` (KP Reader volumes 1–6 extracted)
   - `tajaka_neelakanthi.md` (Tajaka Neelakanthi text)
4. v3.2-S1 (WT-B: BPHS indexing) depends only on items 1–3 above — no other MCPT phase dependency.
5. v3.2-S2/S3 are parallel-safe with v3.2-S1; v3.2-S4 depends on S1+S2; v3.2-S5 depends on S3+S4.

---

## §6 — Red-Team Scheduling Note

Per `MCP_TRANSFORMATION_PLAN §1` and `MACRO_PLAN v2.0 §IS.8`, the MCP Transformation red-team discharges at v3.4-S2 (the final phase). v3.1.0–v3.3 do not require individual red-team passes. The v3.4-S2 red-team covers:
- All 21 tools for class-1 (data fabrication), class-2 (tier bypass), class-3 (B.11 skip) findings.
- MSR signal-grounding: target ≥95% of 573 signals with explicit FORENSIC/LEL citations (from current 419 ungrounded).
- Calibration MV: prediction accuracy + Brier score computation from mcp_prediction_outcomes.

---

## §7 — Mirror Propagation Evidence

Per `GOVERNANCE_INTEGRITY_PROTOCOL §K` and mirror pairs MP.1 (CLAUDE.md ↔ .geminirules) and MP.2 (CLAUDE.md §E ↔ .gemini/project_state.md):

- **MP.1 (.geminirules):** MCP Transformation workstream entry updated in §E — status from ACTIVE (pending Wave 0 kickoff) to "ACTIVE — v3.1.0 foundation CLOSED (2026-05-22), v3.2 classical grounding next". Semantic parity maintained; Gemini-side §E is a compact summary, not a byte-duplicate.
- **MP.2 (.gemini/project_state.md):** Concurrent workstream state pointer updated to reflect v3.1.0 CLOSED and MCPT v3.2 as next wave. Current active sub-phase pointer unchanged (M5 / MCP Transformation active per project architecture).

Both mirrors are adapted parity (not byte-identical) per declared MP.1/MP.2 asymmetries in `CANONICAL_ARTIFACTS_v1_0.md §2`.

---

*Authored at v3.1.0-S6 close, 2026-05-22. MCP Transformation v3.1.0 Foundation phase CLOSED. feature/mcpt-foundation → feature/mcpt-final merge complete. v3.2 entry conditions satisfied pending source data.*
