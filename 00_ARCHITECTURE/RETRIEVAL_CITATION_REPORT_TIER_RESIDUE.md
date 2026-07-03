---
artifact: RETRIEVAL_CITATION_REPORT_TIER_RESIDUE
canonical_id: RETRIEVAL_CITATION_REPORT_TIER_RESIDUE
version: "1.0"
status: COMPLETE
created: 2026-06-27
session: D0_5_CLEANUP
task: TASK-2 — MCP resource audience_tier residue reverse-citation gate
---

# Reverse-Citation Report: MCP Resource audience_tier Tier Residue

## Scope

Files named in brief §2:
- `platform-mcp/src/resources/house_rules_variants/{client,acharya,super_admin}.md`
- `platform-mcp/src/resources/house_rules.ts`
- `platform-mcp/src/resources/types.ts` (searched; file is `platform-mcp/src/types.ts`)
- `platform-mcp/src/__tests__/server_tier_visibility.test.ts`
- `platform/src/lib/retrieve/types.ts` (note: brief says "lib/retrieve tier removed in D1 convergence, not here")

## Full audience_tier Grep (platform-mcp/src/)

**Query:** `grep -rn "audience_tier"` in `platform-mcp/src/`

| File | Lines | Content |
|---|---|---|
| `src/types.ts` | 64, 102, 112 | Comment-only: `// audience_tier removed (Stream A 3.tier_excision 2026-05-28).` |
| `src/auth.ts` | 104 | Comment-only: `// audience_tier excised (Stream A 3.tier_excision 2026-05-28).` |
| `src/__tests__/server_tier_visibility.test.ts` | 6, 121 | Comment-only references to prior excision history |
| `src/bundles/cache.ts` | 106, 121 | `@deprecated` comment + omit comment — not live access control code |

**Verdict on `platform-mcp/src/` source:** `audience_tier` appears only in historical comments documenting the 2026-05-28 excision. No live access-control or gating logic remains.

## audience_tier in Test Files (platform-mcp/test/)

| File | Lines | Context |
|---|---|---|
| `test/auth_cache.test.ts` | 18, 117 | Test fixtures with `audience_tier` field — testing auth cache behavior |
| `test/routing_eval.test.ts` | 101, 106, 158, 162, 163 | Routing eval tests referencing `audience_tier` in prompt fixtures |
| `test/data_coverage.integration.test.ts` | 32, 38 | Integration test fixtures |
| `test/chart_summary.test.ts` | 37 | Test fixture: `audience_tier: 'super_admin' as const` |
| `test/tool_health.integration.test.ts` | 34, 40 | Integration test fixtures |
| `test/query_chart_facts_batching.test.ts` | 64 | Test fixture |
| `test/bundles/sse_streaming.integration.test.ts` | 32 | Test fixture |
| `test/coverage_handler.test.ts` | 41, 47 | Test fixture |
| `test/accuracy/cross_scenario.test.ts` | 91 | Test fixture |
| `test/bench/run.ts` | 58, 310 | Bench runner fixture |
| `test/bundles/holistic_bundle.test.ts` | 31 | Test fixture |
| `test/bundles/multi_school_bundle.test.ts` | 26 | Test fixture |

**Verdict on test files:** These are in `test/` (legacy test directory, not `src/__tests__/`). They use `audience_tier` as a fixture field on MCP call payloads — the field passes through HTTP to a legacy /api/ route. The brief scopes cleanup to `platform-mcp/src/resources/` files only. D1 convergence handles the broader `platform/src/lib/retrieve/types.ts` tier. The `test/` fixtures are out of scope for D0.5.

## house_rules_variants — Callers

**Query:** `grep -rn "getHouseRulesForTier\|VARIANTS\[tier\]\|loadVariant\|house_rules_variants"` in `platform-mcp/src/`

| File | Caller | Notes |
|---|---|---|
| `src/resources/house_rules.ts` | `loadVariant()` internal, `getHouseRulesForTier()` exported | The only caller of variants; no external caller found in `src/` |
| `src/resources/index.ts` | comment line 47-48 | Reference to loading from `house_rules_variants/{tier}.md` — informational comment |

**External callers of `getHouseRulesForTier`:** Zero found in `platform-mcp/src/` (other than `house_rules.ts` itself).

## server_tier_visibility.test.ts Current State

The test in `src/__tests__/server_tier_visibility.test.ts` was **already migrated** to a no-tier assertion at Stream A 3.tier_excision (2026-05-28):
- `Principal` type has no `audience_tier` (removed at source)
- `makePrincipal()` creates `{ user_uid, key_id }` only — no tier field
- All tests assert 40 tools register for any input (the no-tier invariant)
- The "tier" labels (`client`, `acharya`, `super_admin`) are string labels only — not typed access control

**Verdict:** The test already satisfies "no-tier assertion". The descriptions still mention tier labels. Brief says to "delete/replace with a no-tier assertion" — we will rename the file/description to remove the tier framing while preserving the tool-count parity invariant.

## Actions Planned

1. **house_rules.ts** — Collapse to single universal variant: load `universal.md` only; remove `loadVariant`, `VARIANTS` dict, `getHouseRulesForTier` tier-arg function.
2. **house_rules_variants/** — Create `universal.md` (content = super_admin rules, which are the most complete); delete `client.md`, `acharya.md`, `super_admin.md`.
3. **server_tier_visibility.test.ts** — Already a no-tier test. Rename to `server_tool_registration.test.ts`; strip tier-framing from descriptions; retain 40-tool count + no-duplicate assertions.
4. **No changes to `platform/src/lib/retrieve/types.ts`** — deferred to D1 convergence per brief.

*End RETRIEVAL_CITATION_REPORT_TIER_RESIDUE v1.0.*
