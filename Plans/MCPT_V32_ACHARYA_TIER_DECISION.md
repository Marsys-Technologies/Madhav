# MCPT v3.2 — acharya Tier Decision

## Decision: Path A — Add acharya to DB constraint

### Current state

- `mcp_api_keys.audience_tier` column type: `text NOT NULL CHECK (audience_tier IN ('client', 'super_admin'))`
  - NOT a Postgres named enum type — uses a text column with CHECK constraint.
  - Migration 070 (`platform/supabase/migrations/070_mcp_api_keys.sql`) introduced it with only `client` + `super_admin`.
- Code references to 'acharya': see audit table below.
- `data_coverage.ts:55` and `tool_health.ts:53` gate on `'client' || 'public_redacted'` (pass-through for all other tiers including 'acharya') — these are correct by intent but produce undefined behavior if 'acharya' is never in the DB, because the CHECK constraint would reject key creation with `audience_tier = 'acharya'`.
- `platform/src/app/api/mcp/health/tools/route.ts:40` and `coverage/route.ts:36` have the same `'client' || 'public_redacted'` gate — correct by intent, same undefined-behavior gap.

### Acharya references audit

| File | Line | Reference type |
|---|---|---|
| `platform-mcp/src/server.ts` | 91 | Comment: "Client/acharya callers must use…" |
| `platform-mcp/src/tools/tool_health.ts` | 5, 24, 57 | Tier-gate comment + tierNote + error message |
| `platform-mcp/src/tools/data_coverage.ts` | 6, 26, 59 | Tier-gate comment + tierNote + error message |
| `platform-mcp/src/tools/description_builder.ts` | 39 | JSDoc example string |
| `platform-mcp/src/tools/flag_disagreement.ts` | 71 | tierNote: "acharya/client tier = 403" |
| `platform-mcp/src/tools/read_classical_text.ts` | 16 | Access control comment: all tiers including acharya |
| `platform-mcp/src/resources/chart_overview.ts` | 5 | Comment: "super_admin/acharya ~3k tokens" |
| `platform-mcp/src/resources/capabilities.ts` | 7, 104, 105, 175, 176 | Capability table tier references |
| `platform-mcp/src/resources/index.ts` | 38 | Comment: "admin/acharya" |
| `platform-mcp/src/resources/house_rules_variants/acharya.md` | 1-68 | Full acharya house-rules variant (exists) |
| `platform-mcp/src/resources/house_rules.ts` | 29, 46, 54 | validTiers list, loadVariant('acharya'), default comment |
| `platform-mcp/src/resources/house_rules_variants/super_admin.md` | 98, 105 | Description of acharya tier |
| `platform/src/app/api/mcp/health/tools/route.ts` | 4, 45 | Comment + error message |
| `platform/src/app/api/mcp/health/coverage/route.ts` | 4, 43 | Comment + error message |
| `platform/src/app/api/mcp/execute/route.ts` | 120 | TypeScript union type `'acharya_reviewer'` (variant spelling — see note) |

**Note on `execute/route.ts:120`:** This file uses `'acharya_reviewer'` (not `'acharya'`). This is a separate old legacy type annotation in the `LegacyQueryPlan` interface (the pipeline planner path, not the MCP server path). It does not affect MCP key authentication; the MCP principal flow reads `audience_tier` from the DB via `mcp_api_keys`. This discrepancy is pre-existing and out of scope for this migration.

### Rationale for Path A

1. **CLAUDE.md §M (quality standard)** explicitly names the "independent senior Jyotish acharya reviewing this corpus" use case as a first-class accuracy-review scenario. The acharya tier is architecturally intended, not a future concept.
2. **house_rules_variants/acharya.md already exists** — the MCP server already serves a dedicated acharya house-rules document. Refusing to issue acharya keys due to a DB constraint is an inconsistency.
3. **tool_health + data_coverage are gated for acharya** — the code already assumes acharya can call these tools; without this migration, a key with `audience_tier = 'acharya'` cannot be created, so the gate is never reachable.
4. **Low risk:** The fix is a DROP/ADD of a CHECK constraint on a small table (mcp_api_keys). No enum type exists; no cascade; idempotent guard included.

### Implementation

- Migration 117: Drop old CHECK constraint on `mcp_api_keys.audience_tier`, add new CHECK including `'acharya'`.
- No code changes required: `data_coverage.ts` and `tool_health.ts` already use the `client || public_redacted` gate pattern which correctly allows acharya through. The logic is already correct — the DB was the only blocker.

### Rollback

If Path A is wrong: Re-apply migration 117 in reverse (drop constraint with acharya, add constraint without acharya, then revoke/delete any existing acharya keys). Trivially reversible since no rows with `audience_tier = 'acharya'` exist yet.

Reversing is simpler than a Postgres named enum removal would have been.
