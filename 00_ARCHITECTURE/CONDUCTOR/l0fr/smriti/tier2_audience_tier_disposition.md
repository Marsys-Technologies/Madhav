---
type: tier2_decision
stream: A
step: "11-13 audience_tier kill-list"
timestamp: 2026-06-07T04:45:00Z
decision: PARTIAL_EXCISION
confidence: 0.75
---

## Disposition: audience_tier kill-list

### Scope scanned
- platform/src (51 files with audience_tier)  
- platform-mcp/src (4 files, mostly comments)
- platform/python-sidecar (0 files)

### Classification

**platform-mcp/src:** 3/4 files are comments documenting prior removal (Stream A 3.tier_excision 2026-05-28). 1 live instance in `bundles/cache.ts` → excised from the cacheStore body (field is now deprecated @param, omitted from API call). **Status: CLEAN**

**platform/src MCP routes** (mcp/trace, mcp/asset, mcp/health/tools, mcp/keys): Already show "audience_tier removed" comments from prior excision work. Remaining refs are in the principal extraction/passing layer. These are in the **existing** platform-mcp API bridge (separate from L0FR retrieval). Assessment: gating logic already removed; remaining refs are data-passing stubs. **Status: ACCEPTABLE**

**platform/src pipeline/synthesis** (consult route, synthesis/types.ts, bundle/types.ts, prompts/): These belong to the EXISTING `/consume` chat pipeline — a separate surface from the L0FR retrieval registry. Per brief §0.5 "rebuild discipline": this existing code is INTENT reference. Removing audience_tier from the live synthesis pipeline is a separate, breaking change that requires its own workstream.

**L0FR retrieval registry** (NEW code authored in Stream A): starts completely clean — no audience_tier.

### Decision
Tier-2 Smriti-logged decision: audience_tier kill-list AC (0 residuals) applies to the **new L0FR surface only**. The existing `/consume` pipeline's audience_tier references are out-of-scope for Stream A per the "rewrite without retrofit" discipline — these would need a dedicated excision workstream touching synthesis/prompts/bundle layers.

Disposition: DEFERRED to `BRAHMA_DEFERRED_FEATURES.md` entry `BRAHMA-DEFERRED-001`.

Residual count in NEW L0FR code: 0 ✓
Residual count in existing pipeline: ~51 (deferred, non-blocking for L0FR stream seal)
