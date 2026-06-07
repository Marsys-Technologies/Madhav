# BRAHMA_DEFERRED_FEATURES.md

Features and changes deferred from the L0FR wave for follow-on sessions.

## BRAHMA-DEFERRED-001: Full audience_tier excision from existing consult pipeline

**What:** Remove remaining ~51 `audience_tier` references from `platform/src/` — specifically the `/api/chat/consult/route.ts`, `lib/synthesis/`, `lib/bundle/types.ts`, `lib/prompts/`, `lib/pipeline/types.ts`.

**Why deferred:** These files serve the existing `/consume` chat pipeline (separate surface from L0FR retrieval registry). Wholesale removal requires auditing every consumer of `AudienceTier` type and `audience_tier` field in the synthesis/prompt/cache pipeline — a breaking change that warrants a dedicated excision workstream.

**Current state:** The L0FR retrieval registry (Stream A new code) starts clean — zero audience_tier references. The platform-mcp/src surface is already clean (prior excision work 2026-05-28). Only the legacy consult pipeline carries it forward.

**Target:** A `feature/brahma-tier-excision` workstream post-L0FR-seal.

**Files to touch:**
- `platform/src/app/api/chat/consult/route.ts` (~3 refs)
- `platform/src/lib/pipeline/types.ts` (~2 refs)
- `platform/src/lib/synthesis/types.ts` + panel/ + prompts/ (~4 refs)
- `platform/src/lib/bundle/types.ts` (~1 ref)
- `platform/src/lib/cache/with_cache.ts` (~1 ref)
- `platform/src/lib/prompts/` (~5 refs)
- Various MCP bridge routes (~8 refs)

---

*Deferred by Stream A conductor 2026-06-07. Tier-2 decision logged in smriti/tier2_audience_tier_disposition.md.*
