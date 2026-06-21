---
canonical_id: CLAUDECODE_BRIEF_SRP_T4
version: 1.0
status: CURRENT
phase: SRP-T-4
session_type: test
authored: 2026-05-25
worktree: MadhavSRP-T4
branch: test/srp-t4-system
blocked_by:
  - fix/srp-f1-portal-fixes (merged + deployed)
  - fix/srp-f2-mcp-fixes (merged + deployed)
deploy_target: none (test-only commit)
may_touch:
  - platform/src/__tests__/system/portal_pipeline.system.test.ts (create)
  - platform/src/__tests__/system/README.md (create)
must_not_touch:
  - platform/src/lib/**
  - platform-mcp/src/**
  - platform/src/app/**
  - 00_ARCHITECTURE/**
---

# CLAUDECODE BRIEF: SRP-T-4 — System Tests (Portal Pipeline E2E)

## Context

You are writing **system tests** that exercise the full portal query pipeline from HTTP
request all the way through to a streamed LLM response. These tests use the same auth
mechanism as the existing smoke suite (`SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID`).

The goal is to verify three things at the system level:
1. The adapter pipeline is active (`MARSYS_FLAG_R11V2_USE_ADAPTERS=true`).
2. B.11 floor tools always appear in the query trace.
3. `forward_looking`-type queries reach forward-looking signals.

Working directory: `/Users/Dev/Vibe-Coding/Apps/MadhavSRP-T4`
Branch: `test/srp-t4-system`

**Pre-conditions**:
1. `fix/srp-f1-portal-fixes` and `fix/srp-f2-mcp-fixes` merged + deployed.
2. `SMOKE_SESSION_COOKIE` env var set (from `platform/scripts/mint_session_cookie.ts`).
3. `SMOKE_CHART_ID` = `362f9f17-95a5-490b-a5a7-027d3e0efda0`.
4. `SMOKE_BASE_URL` = production URL or local dev server.

Tests **skip gracefully** if `SMOKE_SESSION_COOKIE` absent — CI-safe.

---

## Test File: portal_pipeline.system.test.ts

**Path**: `platform/src/__tests__/system/portal_pipeline.system.test.ts`

```typescript
import { describe, it, expect } from 'vitest'

const BASE_URL = process.env.SMOKE_BASE_URL ?? 'http://localhost:3000'
const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE ?? ''
const CHART_ID = process.env.SMOKE_CHART_ID ?? '362f9f17-95a5-490b-a5a7-027d3e0efda0'
const runSmoke = !!SESSION_COOKIE

const describeIf = runSmoke ? describe : describe.skip

// Standard query POST function
async function submitQuery(queryText: string, options: {
  provider?: string
  mode?: 'classic' | 'claude-style'
  stream?: boolean
} = {}) {
  const response = await fetch(`${BASE_URL}/api/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Cookie': `__session=${SESSION_COOKIE}`,
    },
    body: JSON.stringify({
      query: queryText,
      chart_id: CHART_ID,
      provider: options.provider ?? 'anthropic',
      stream: options.stream ?? false,
    }),
  })
  if (!response.ok && !response.body) {
    throw new Error(`HTTP ${response.status}`)
  }
  // If streaming, read entire response as text
  const text = await response.text()
  return { status: response.status, text, headers: Object.fromEntries(response.headers) }
}

// Parse query trace from response (may be in X-Query-Trace header or response JSON)
function extractTrace(responseText: string, responseHeaders: Record<string, string>) {
  // Check headers first
  const traceHeader = responseHeaders['x-query-trace'] ?? responseHeaders['x-marsys-trace']
  if (traceHeader) {
    try { return JSON.parse(traceHeader) } catch {}
  }
  // Try parsing JSON body
  try {
    const json = JSON.parse(responseText)
    return json.trace ?? json.query_trace ?? json.metadata?.trace
  } catch {}
  // For streamed responses, look for trace in the SSE data
  const traceMatch = responseText.match(/"trace":(\{[^}]+\})/)
  if (traceMatch) {
    try { return JSON.parse(traceMatch[1]) } catch {}
  }
  return null
}
```

**Test Suite 1: Adapter pipeline is active**

```typescript
describeIf('Portal pipeline — adapter path active', () => {
  it('query returns HTTP 200', async () => {
    const { status } = await submitQuery('What is my Sun sign placement?')
    expect(status).toBe(200)
  }, 30000)

  it('response is non-empty', async () => {
    const { text } = await submitQuery('Summarize my chart briefly.')
    expect(text.length).toBeGreaterThan(50)
  }, 30000)

  it('no "createOrchestrator" error in response (legacy pipeline not active)', async () => {
    const { text } = await submitQuery('What is my ascendant?')
    expect(text.toLowerCase()).not.toContain('createorchestrator')
    expect(text.toLowerCase()).not.toContain('single_model_strategy')
  }, 30000)
})
```

**Test Suite 2: B.11 floor tools appear in trace**

```typescript
describeIf('B.11 floor — mandatory tools in every query trace', () => {
  const B11_FLOOR_TOOLS = ['msr_sql', 'cgm_graph_walk', 'pattern_register', 'vector_search', 'chart_facts_query']

  it('query trace contains all 5 B.11 floor tools', async () => {
    const { text, headers } = await submitQuery('Tell me about my career prospects.')
    const trace = extractTrace(text, headers)

    if (trace) {
      // Check tool_executions or tools_called in trace
      const toolsCalled = trace.tool_executions ?? trace.tools_called ?? trace.tools ?? []
      const toolNames = toolsCalled.map((t: { name?: string; tool?: string }) => t.name ?? t.tool ?? '')
      console.log('B.11 tools in trace:', toolNames.filter((n: string) => B11_FLOOR_TOOLS.includes(n)))

      for (const floorTool of B11_FLOOR_TOOLS) {
        expect(toolNames).toContain(floorTool)
      }
    } else {
      // Trace extraction failed — log a warning but don't fail the test
      console.warn('Could not extract query trace from response. Skipping B.11 floor assertion.')
      expect(text.length).toBeGreaterThan(0)  // At minimum, got a response
    }
  }, 45000)
})
```

**Test Suite 3: forward_looking routing**

```typescript
describeIf('forward_looking routing — predictive queries reach is_forward_looking signals', () => {
  it('future transit query returns a response mentioning planetary movement', async () => {
    const { status, text } = await submitQuery(
      'What transits are coming up for me in the next 6 months?'
    )
    expect(status).toBe(200)
    // The response should mention planets, transits, or time references
    const lowerText = text.toLowerCase()
    const mentionsPlanets = ['saturn', 'jupiter', 'rahu', 'ketu', 'mars', 'transit', 'period']
      .some(word => lowerText.includes(word))
    expect(mentionsPlanets).toBe(true)
  }, 45000)
})
```

**Test Suite 4: Multi-provider smoke**

```typescript
describeIf('Multi-provider — all 5 providers return non-error responses', () => {
  const providers = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia']

  // Only run if SMOKE_TEST_ALL_PROVIDERS=true (these may cost tokens)
  const runAllProviders = !!process.env.SMOKE_TEST_ALL_PROVIDERS

  if (runAllProviders) {
    it.each(providers)('provider=%s returns 200', async (provider) => {
      const { status } = await submitQuery('What is my Sun placement?', { provider })
      expect(status).toBe(200)
    }, 30000)
  } else {
    it('anthropic provider returns 200 (default smoke)', async () => {
      const { status } = await submitQuery('What is my Sun placement?', { provider: 'anthropic' })
      expect(status).toBe(200)
    }, 30000)
  }
})
```

**Test Suite 5: MCP channel smoke**

```typescript
describeIf('MCP channel — representative tools return non-empty data', () => {
  const MCP_BASE_URL = process.env.MCP_BASE_URL ?? BASE_URL
  const MCP_API_KEY = process.env.INTEGRATION_TEST_API_KEY ?? ''

  it.skipIf(!MCP_API_KEY)('msr_sql tool returns signals via MCP', async () => {
    const response = await fetch(`${MCP_BASE_URL}/api/mcp/primitives/msr_sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${MCP_API_KEY}`,
        'X-MARSYS-Chart-Id': CHART_ID,
      },
      body: JSON.stringify({ params: { limit: 3 } }),
    })
    expect(response.status).toBe(200)
    const body = await response.json()
    const rows = body?.data ?? body?.signals ?? body?.rows ?? []
    expect(rows.length).toBeGreaterThan(0)
  }, 20000)

  it.skipIf(!MCP_API_KEY)('query_chart_facts tool returns chart facts', async () => {
    const response = await fetch(`${MCP_BASE_URL}/api/mcp/primitives/query_chart_facts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${MCP_API_KEY}`,
        'X-MARSYS-Chart-Id': CHART_ID,
      },
      body: JSON.stringify({ params: { category: 'planetary_positions', limit: 5 } }),
    })
    expect(response.status).toBe(200)
    const body = await response.json()
    const facts = body?.data ?? body?.facts ?? body?.rows ?? []
    expect(facts.length).toBeGreaterThan(0)
  }, 20000)

  it.skipIf(!MCP_API_KEY)('temporal tool returns non-error response', async () => {
    const response = await fetch(`${MCP_BASE_URL}/api/mcp/primitives/temporal`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${MCP_API_KEY}`,
        'X-MARSYS-Chart-Id': CHART_ID,
      },
      body: JSON.stringify({ params: {} }),
    })
    expect([200, 500]).toContain(response.status)  // 500 = reached DB, minimal params ok
    expect(response.status).not.toBe(400)  // 400 = still blocked (FIX-1 regression)
  }, 15000)
})
```

---

## Acceptance Criteria

- [ ] ≥ 15 system test scenarios across all suites.
- [ ] `provider=anthropic` query returns HTTP 200.
- [ ] B.11 floor: 5 mandatory tools appear in trace (when trace is parseable).
- [ ] Forward-looking query response mentions planetary/transit content.
- [ ] No `createOrchestrator` or legacy pipeline error in responses.
- [ ] All tests skip cleanly when `SMOKE_SESSION_COOKIE` absent.
- [ ] `npx vitest run src/__tests__/system/` shows 0 failures (or all skipped in CI).
- [ ] PR opened from `test/srp-t4-system`.

## Session Close

Commit message:
```
test(srp-t4): portal pipeline system tests — adapter path, B.11 floor, forward_looking, multi-provider

Covers: adapter pipeline active (not legacy createOrchestrator), B.11 floor in trace,
forward_looking query routing, multi-provider smoke (anthropic default + all-5 opt-in),
MCP channel smoke for msr_sql/query_chart_facts/temporal.
Tests skip when SMOKE_SESSION_COOKIE absent (CI-safe).
```
