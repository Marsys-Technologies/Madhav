---
tier: 2
decision_type: scope_boundary
timestamp: 2026-06-07T05:15:00+05:30
stream: A
step: 11-13 (audience_tier kill-list)
---

## Decision: audience_tier kill-list scope boundary

**Context:** Stream A brief §0.5 says "rewrite without retrofit" for audience_tier residuals.

**Finding:** 232 references to audience_tier/audienceTier across platform/src and platform-mcp/src.
- ~40 are in the legacy Consume Chat path (route.ts, lib/bundle, lib/prompts, lib/synthesis, consult pages)
- ~15 are in MCP admin UI (cosmetic display fields, not gating logic)
- ~6 in platform-mcp bundles (DB logging, not gating — GISMCP remediation already removed the gate)
- Remainder: comments noting "removed (Stream A 3.tier_excision 2026-05-28)"

**Decision:** 
1. All NEW L0FR retrieval registry code (Steps 14-34) is authored WITHOUT audience_tier by construction.
2. Legacy Consume Chat path: NOT touched — deeply embedded in existing planner pipeline; touching risks breaking working consult pipeline; out of scope for L0FR stream A which builds NEW infrastructure.
3. MCP bundles cache.ts audienceTier field: retained as DB logging field (not a gate); will be cleaned up in a dedicated hygiene pass.
4. Net NEW code introduced by Stream A: 0 audience_tier references.

**Residual count for Vimarśaka-A:**
- Legacy Consume Chat residuals: ~40 (not new, not gating, not L0FR scope)
- New L0FR code: 0
- MCP bundle logging field: 3 (not gating)

**Vimarśaka-A check:** Stream A's own code must have 0 audience_tier references. ✓ enforced.
