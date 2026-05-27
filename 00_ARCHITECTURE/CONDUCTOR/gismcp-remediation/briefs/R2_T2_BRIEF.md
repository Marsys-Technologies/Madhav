---
session_id: R2-T2
status: PENDING
phase: GISMCP-R2
title: "MCP smoke tests + full vitest baseline + Stream 1 seal"
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
branch: fix/gismcp-r1-r2
may_touch:
  - platform/src/__tests__/integration/mcp_stub_engines.integration.test.ts
  - 00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM1_COMPLETE.md
must_not_touch:
  - platform/src/lib/retrieve/**
  - platform-mcp/src/server.ts
  - supabase/**
  - "*.yaml"
---

# R2-T2: MCP Smoke Tests + Stream 1 Seal

## Step 1 — Full vitest runs (both packages)

```bash
echo "=== platform vitest ==="
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform
npx vitest run 2>&1 | tail -20

echo "=== platform-mcp vitest ==="
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform-mcp
npx vitest run 2>&1 | tail -20
```

Expected: 0 failures in both. If any failures are NEW (not pre-existing), fix before proceeding. Compare against the known pre-existing failures baseline in `KNOWN_PRE_EXISTING_FAILURES.md`.

## Step 2 — Author MCP smoke integration test

Create `platform/src/__tests__/integration/mcp_stub_engines.integration.test.ts`:

```typescript
/**
 * MCP Smoke Test — 4 Stub Engines via Platform Endpoint
 * Skipped unless SMOKE_SESSION_COOKIE + SMOKE_BASE_URL are set.
 */
const SKIP = !process.env.SMOKE_SESSION_COOKIE || !process.env.SMOKE_BASE_URL

const callPrimitive = async (tool: string, payload: Record<string, unknown>) => {
  const res = await fetch(
    `${process.env.SMOKE_BASE_URL}/api/mcp/primitives/${tool}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Cookie: `__session=${process.env.SMOKE_SESSION_COOKIE}`,
      },
      body: JSON.stringify(payload),
    }
  )
  return { status: res.status, body: await res.json() }
}

describe.skipIf(SKIP)('MCP stub engines — smoke via /api/mcp/primitives', () => {
  it('query_tara_balam returns 200 with valid payload', async () => {
    const { status, body } = await callPrimitive('query_tara_balam', {
      start_date: '2026-05-26',
      end_date: '2026-05-26',
    })
    expect(status).toBe(200)
    expect(body.ok).toBe(true)
    expect(body.result).toBeDefined()
  })

  it('query_chandra_balam returns 200 with valid payload', async () => {
    const { status, body } = await callPrimitive('query_chandra_balam', {
      start_date: '2026-05-26',
      end_date: '2026-05-26',
    })
    expect(status).toBe(200)
    expect(body.ok).toBe(true)
  })

  it('jaimini_chara_dasha returns 200 with empty payload', async () => {
    const { status, body } = await callPrimitive('jaimini_chara_dasha', {})
    expect(status).toBe(200)
    expect(body.ok).toBe(true)
    expect(body.result.current_mahadasha).toBeDefined()
  })

  it('jaimini_chara_dasha_full returns 200 and 12 mahadashas', async () => {
    const { status, body } = await callPrimitive('jaimini_chara_dasha_full', {})
    expect(status).toBe(200)
    expect(body.ok).toBe(true)
    expect(body.result.full_sequence.length).toBe(12)
  })

  it('none of the 4 stub engines returns 500', async () => {
    // Regression guard: previously these were 500 (no engine)
    for (const tool of [
      'query_tara_balam',
      'query_chandra_balam',
      'jaimini_chara_dasha',
      'jaimini_chara_dasha_full',
    ]) {
      const { status } = await callPrimitive(tool, { start_date: '2026-05-26', end_date: '2026-05-26' })
      expect(status, `${tool} should not 500`).not.toBe(500)
    }
  })
})
```

## Step 3 — Commit the smoke test

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
git add platform/src/__tests__/integration/mcp_stub_engines.integration.test.ts
git commit -m "test(R2): MCP smoke tests for 4 stub engines — verify 200 via /api/mcp/primitives

Closes R2-T2 (smoke) per GISMCP_REMEDIATION_PLAN_v1_0 §4"
```

## Step 4 — Author STREAM1_COMPLETE.md seal

Create `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM1_COMPLETE.md`:

```markdown
---
stream: 1
status: COMPLETE
date: 2026-05-26
sessions_completed: [R1-S1, R1-T1, R2-S1, R2-S2, R2-T1, R2-T2]
fixes_shipped:
  R1: "server.ts tier gating removed — all 40 tools unconditional"
  R2: "4 stub retrieval engines implemented — query_tara_balam, query_chandra_balam, jaimini_chara_dasha, jaimini_chara_dasha_full"
test_summary:
  platform_vitest: 0 failures
  platform_mcp_vitest: 0 failures
  integration_tests: PASS (with DB_PROXY_PORT=5433)
  smoke_tests: CI-safe (skip without SMOKE_SESSION_COOKIE)
deploy_required:
  amjis_web: true    # new retrieve tools
  amjis_mcp: true    # server.ts de-gating
branch: fix/gismcp-r1-r2
---
```

## Step 5 — Final commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
git add 00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM1_COMPLETE.md
git commit -m "seal(Stream1): GISMCP R1+R2 complete — 40 tools visible, 4 engines implemented"
```

## Acceptance Criteria

1. `platform vitest` → 0 failures
2. `platform-mcp vitest` → 0 failures
3. `test -f platform/src/__tests__/integration/mcp_stub_engines.integration.test.ts`
4. `test -f 00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM1_COMPLETE.md`
5. STREAM1_COMPLETE.md contains `status: COMPLETE`
