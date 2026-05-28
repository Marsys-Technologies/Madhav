---
status: COMPLETE
unit: 3.tier_excision
wave: 3
title: Excise the tier / disclosure subsystem (depth selector included)
stream: A
worktree: ../MadhavStreamA
blockedBy: [G2_authz_live]
on_red: rollback
---

## Context (self-contained)
With `authorizeChartAccess` live (G2, from 2c), access = **role (super_admin/guest) + chart_grants** only.
The audience-tier system is now redundant overlap (MASTER_PLAN §6-C, audit). Remove it entirely. Note: the
"Deep/Study/Brief" depth selector IS `TierPicker.tsx` mapping to tiers — removing tiers removes it.

## Scope (remove)
- `platform/src/lib/disclosure/` module + `components/disclosure/DisclosureTierBadge.tsx` +
  `components/consume/TierPicker.tsx`.
- `X-MCP-Audience-Tier` header (all sites in `platform-mcp/src/client.ts`); `tier_catalog.ts`; the hard-403
  tier gates in `/api/mcp/health/tools` + `/health/coverage`; `house_rules_variants/public_redacted.md`.
- DB: new migration dropping `mcp_api_keys.audience_tier` (+ relax the 070/117 constraint); relax
  `/api/mcp/keys/validate`.
- The `query_varshphal.ts:87` client-redaction branch.
- **Depth-selector replacement:** when TierPicker is removed, depth is planner-auto-selected by query class
  (no user knob). If the native hasn't confirmed this, default to planner-auto and flag in CONDUCTOR_LOG.

## Acceptance criteria (all automated)
1. Zero tier references (grep `audience_tier|X-MCP-Audience-Tier|TierPicker|disclosure|public_redacted` = none in live code).
2. MCP keys validate without a tier; health routes no longer 403-gate by tier.
3. **Click-through:** chat works with TierPicker removed (no depth-selector regression — mount test).
4. Security posture recorded: every key writes/flags and sees unredacted output (deterministic data — nothing to redact).

## must_not_touch
`chart_facts`/`l25_*` (2a), `platform/src/lib/pipelines/**` (gateway), `platform/src/lib/retrieve/**`,
`platform/src/app/clients/**` (consult_nav owns).

## Commit cadence / rollback
Commits: (1) remove disclosure module + UI + TierPicker, (2) MCP header/tier_catalog/health-gate removal,
(3) migration drop audience_tier. Rollback = revert; the dropped column is the only irreversible step → run it
LAST, after a green post-removal window.
