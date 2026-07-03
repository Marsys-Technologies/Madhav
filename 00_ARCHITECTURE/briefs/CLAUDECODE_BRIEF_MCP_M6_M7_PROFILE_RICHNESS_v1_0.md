---
canonical_id: CLAUDECODE_BRIEF_MCP_M6_M7_PROFILE_RICHNESS
version: 1.0
status: READY-FOR-EXECUTION — M6 per-model declared profile, M7 resources+prompts, + keystone migration
created: 2026-06-30
author: Cowork (planning) — detail-pass for the autonomous swarm
parent_charter: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (PHASES M6 + M7 + keystone)
depends_on: M1 (principal); consumes LIVE retrieval seams (surface-spec, response_format, resources, prompts)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4 (MCP consumes; does not redefine)
verification_basis: live code + RETRIEVAL_TO_MCP_HANDOFF, read 2026-06-30
hard_constraints:
  - CONSUME getMcpSurfaceSpec + response_format; do NOT re-derive MARO or re-implement retrieval
  - any missing capability is REQUESTED from retrieval (§4), never solved with local SQL
  - tool names snake_case no '-'; VITEST; chart-agnostic green
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — MCP M6 (declared profile) + M7 (richness) + KEYSTONE migration

> These three turn "the LLM can access data" into "the LLM gets the RIGHT shape of data and the high-value
> insight surfaces" — the "superlative insights" half of the goal. Almost all of it is EXPOSING already-live
> retrieval seams, not building. The keystone migration (remaining sidecar-direct tools → registry) is folded
> here since it's the same "consume the registry" move.

## §1 — Ground truth (live seams to consume — already built retrieval-side)
- `getMcpSurfaceSpec(family)` published: route `/api/mcp/surface-spec` + `callPlatformSurfaceSpec`
  (`platform-mcp/src/client.ts:348`). MARO profiles MEASURED v1.1.0.
- `response_format: minimal|standard|detailed` live in `platform/src/lib/mcp/bundle_adapters.ts`.
- Reasoning-unit tools live: `assess_marriage/career/health/wealth` + `yoga_activation_by_dasha`
  (`platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`).
- `registerResources()` CALLED (`server.ts:149`): 9 resources + 3 prompts (`orient_chart`, `assess_domain`,
  `find_active_yogas`).
- Keystone substantially landed: `registry_bridge.ts` exposes 12 registry-served tools. Remaining bypassers:
  the sidecar-direct phala_*, bo_2-8 holistic_bundle, kala_temporal_bundle, mimamsa_* callers.

## §2 — M6 Per-model declared profile
- **M6.1 Declaration mechanism (resolved recommendation): per-key binding + client-hint fallback.** Bind a
  model family to the MCP API key at issuance (the cleanest, since Bearer is the production path and the key
  already maps to a user); accept an optional client-supplied hint header (`x-mcp-model-family`) as override.
  Avoid OAuth-scope (heavier) and config-file (not multi-tenant). Human-Proxy may revise, but per-key is the
  default. Declared → profiled; undeclared (no key binding, no hint) → universal-best.
  **SCHEMA NOTE (verified 2026-06-30):** `mcp_api_keys` has NO model-family column today — only `key_id,
  key_hash, user_uid, scopes[], created_at, last_used_at, revoked_at, label` (`platform/migrations/001_baseline.sql`).
  Per-key binding therefore REQUIRES a forward migration adding `model_family TEXT` (or `model_policy JSONB`),
  plus a `model_family` param threaded through `generateMcpKey` (`platform/src/lib/mcp/auth.ts:164`) and the
  `POST /api/mcp/keys` route (`platform/src/app/api/mcp/keys/route.ts`). Do NOT abuse the `label` column (it's
  human display text, surfaced in the keys list) or `scopes[]` (semantically tool-scoping). Migration number:
  next free across both dirs (≥382/383, cross-dir-checked — coordinate with M3/M5 migration numbers so they
  don't collide).
- **M6.2 Consume the surface spec:** call `callPlatformSurfaceSpec(family)` at tool-registration / list time to
  shape which tools + verbosity the connecting family sees (fat bundles for Gemini, fine-grained for Anthropic,
  strict schema for GPT/DeepSeek). Wire `response_format` through so the family gets terse vs exhaustive shapes.
  Do NOT re-derive any of this — it's measured; consume it.

## §3 — M7 Richness (expose what's live) + KEYSTONE
- **M7.1 Resources:** the 9 registered resources + a chart catalog/vocab/schema resource — expose as MCP
  resources (per-chart ones entitlement-gated per M0; reuse M2's chart resources). The "active chart context"
  resource is the natural multi-user portal surface.
- **M7.2 Prompts:** expose the 3 guided-reading prompts (`orient_chart`, `assess_domain`, `find_active_yogas`)
  as MCP prompts (`server.prompt()` — currently zero). These are the acharya-grade entry points that drive
  "superlative insights."
- **KEYSTONE migration:** migrate the remaining sidecar-direct tools to `callPlatformPrimitive` (the live
  registry path), each under the M0 entitlement gate + the uniform envelope. Surface the reasoning-unit tools
  (`assess_*`, `yoga_activation_by_dasha`) prominently — they are the highest-value insight tools. Any
  capability genuinely missing registry-side → request from the retrieval fork (§4), never local SQL.

## §4 — Acceptance criteria
- Declaration mechanism live (per-key binding + hint override); a declared Claude key gets the Claude-profiled
  surface; undeclared gets universal-best; `response_format` shapes verbosity per family. No MARO re-derivation.
- 9 resources + chart-context resource served live (per-chart gated); 3 guided-reading prompts exposed as MCP
  prompts; reasoning-unit tools surfaced.
- Remaining sidecar-direct tools migrated to the registry path under the entitlement gate; zero MCP-side chart
  SQL remains; any missing capability filed as a request to retrieval, not worked around.
- Naming snake_case no '-'; Vitest; chart-agnostic green; retrieval FROZEN (MCP consumed, never redefined the seam).

## §5 — VERIFICATION PHASE (mandatory; phase NOT done until ALL pass — independent Auditor)
**V1 — Build gate:** both packages build; `typecheck-mcp` CI green.
**V2 — Migration (M6 model_family):** the `model_family` column migration applied; number collision-free
(cross-dir check, coordinate with M3/M5 numbers); `generateMcpKey` + POST /api/mcp/keys accept + persist it;
additive; rollback note.
**V3 — Tests:** declared key → profiled surface; undeclared → universal-best; client-hint override;
`response_format` shapes verbosity; resources + prompts registered; migrated tools route via
callPlatformPrimitive. Vitest green.
**V4 — Deploy + revision match:** deployed revision SHA == merged SHA.
**V5 — Behavioral proof on PROD:**
  - a key bound to model_family=anthropic gets the Anthropic-profiled surface; an undeclared key gets
    universal-best (diff the two tool lists / shapes to prove they differ).
  - `response_format=minimal` vs `detailed` on the same tool returns demonstrably different payload sizes.
  - the 3 guided-reading prompts are listed via prompts/list; the 9 resources via resources/list (per-chart
    resources still entitlement-gated — re-prove a deny).
  - a migrated formerly-sidecar/SQL tool returns real data via the registry path with a valid key (carry the
    M0.5 lesson: prove the internal token is actually SENT, and the call returns data — not just auth-OK).
**V6 — Keystone invariant (the §4 seam):** grep proves ZERO MCP-side chart SQL remains in migrated tools; any
capability that couldn't be migrated is filed as a REQUEST to the retrieval fork (not worked around locally);
`git diff` shows lib/retrieval untouched; MARO consumed via getMcpSurfaceSpec, never re-derived.
**On ANY V-failure:** remediation loop (charter §4); no advance until V1–V6 pass.

*End of CLAUDECODE_BRIEF_MCP_M6_M7_PROFILE_RICHNESS v1.0. Next: M8 harden + prove live.*
