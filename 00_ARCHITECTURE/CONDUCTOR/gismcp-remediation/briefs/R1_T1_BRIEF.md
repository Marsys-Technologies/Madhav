---
session_id: R1-T1
status: PENDING
phase: GISMCP-R1
title: "R1 tests — tier visibility unit + integration tests"
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
branch: fix/gismcp-r1-r2
may_touch:
  - platform-mcp/src/__tests__/**
  - platform-mcp/src/tools/__tests__/**
must_not_touch:
  - platform/src/**
  - platform-mcp/src/server.ts
  - "*.yaml"
  - 00_ARCHITECTURE/**
---

# R1-T1: Tier Visibility Tests

## Context

R1-S1 removed the tier conditional from server.ts. This session authors tests that assert all 40 tools are visible to ALL tiers including `client`.

## Step 1 — Locate existing server registration tests

Read any existing `server.test.ts` or `server.spec.ts` in `platform-mcp/src/__tests__/`. Understand the test pattern (how they mock the API key tier, how they assert tool registration count).

## Step 2 — Author `server_tier_visibility.test.ts`

Create `platform-mcp/src/__tests__/server_tier_visibility.test.ts`.

This file must test:

```typescript
describe('server tool registration — tier visibility', () => {
  it('registers all 40 tools for client tier', async () => {
    // Mock API key with tier = 'client'
    // Call the server registration function or mock server object
    // Assert: server.listTools() returns exactly 40 tools
    // Assert: tool_health, data_coverage, log_prediction, record_outcome, flag_disagreement
    //         are ALL present in the tool list
  })

  it('registers all 40 tools for acharya tier', async () => {
    // Same as above with tier = 'acharya'
    // Assert: tool count = 40
  })

  it('registers all 40 tools for super_admin tier', async () => {
    // Same as above with tier = 'super_admin'
    // Assert: tool count = 40
  })

  it('tool_health tool is present regardless of tier', async () => {
    for (const tier of ['client', 'acharya', 'super_admin']) {
      // Assert tool_health is in the tool list for this tier
    }
  })
})
```

Follow the exact mock/assertion pattern from existing server tests. If the server registration function doesn't support direct testing (it's a side-effectful MCP SDK registration), write the test against the function that builds the server, or use `server.listTools()` on the registered server instance.

## Step 3 — Author integration test for MCP tool discovery endpoint

Create `platform-mcp/src/__tests__/integration/mcp_visibility.integration.test.ts`.

```typescript
// Skipped unless MCP_BASE_URL and MCP_API_KEY_CLIENT are set
describe.skipIf(!process.env.MCP_BASE_URL)('MCP tool visibility — integration', () => {
  it('client tier API key sees all 40 tools', async () => {
    const response = await fetch(`${process.env.MCP_BASE_URL}/tools/list`, {
      headers: { Authorization: `Bearer ${process.env.MCP_API_KEY_CLIENT}` }
    })
    const { tools } = await response.json()
    expect(tools.length).toBe(40)
    const names = tools.map((t: any) => t.name)
    expect(names).toContain('tool_health')
    expect(names).toContain('data_coverage')
    expect(names).toContain('log_prediction')
    expect(names).toContain('record_outcome')
    expect(names).toContain('flag_disagreement')
  })
})
```

## Step 4 — Run all tests

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform-mcp
npx vitest run 2>&1 | tail -20
```

Expected: 0 failures. The new tests pass (unit tests unconditionally; integration test skips if env vars absent).

## Step 5 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
git add platform-mcp/src/__tests__/
git commit -m "test(R1): tier visibility unit + integration tests — all 40 tools for all tiers

Closes R1-T1 per GISMCP_REMEDIATION_PLAN_v1_0 §4"
```

## Acceptance Criteria

1. `test -f platform-mcp/src/__tests__/server_tier_visibility.test.ts`
2. `npx vitest run src/__tests__/server_tier_visibility.test.ts` → 0 failures
3. All 3 tier variants (client, acharya, super_admin) assert 40 tools
4. Integration test file exists and is CI-safe (skips without env var)
