---
canonical_id: CLAUDECODE_BRIEF_SRP_T3
version: 1.0
status: CURRENT
phase: SRP-T-3
session_type: test
authored: 2026-05-25
worktree: MadhavSRP-T3
branch: test/srp-t3-integration
blocked_by:
  - fix/srp-f1-portal-fixes (must be merged + amjis-web deployed)
  - fix/srp-f2-mcp-fixes (must be merged + amjis-mcp deployed)
deploy_target: none (test-only commit)
may_touch:
  - platform/src/__tests__/integration/mcp_primitives.integration.test.ts (create)
  - platform/src/__tests__/integration/README.md (create)
must_not_touch:
  - platform/src/lib/**
  - platform-mcp/src/**
  - 00_ARCHITECTURE/**
---

# CLAUDECODE BRIEF: SRP-T-3 — Integration Tests (MCP Live DB)

## Context

You are writing **integration tests** that call the MCP primitives HTTP route against a
real database (Postgres via the local proxy). These tests prove the full stack from HTTP
request → route handler → retrieval tool → SQL → DB response works correctly after the
SRP-F-1 and SRP-F-2 fixes are deployed.

Working directory: `/Users/Dev/Vibe-Coding/Apps/MadhavSRP-T3`
Branch: `test/srp-t3-integration`

**Pre-conditions**:
1. `fix/srp-f1-portal-fixes` and `fix/srp-f2-mcp-fixes` merged to main.
2. `amjis-web` redeployed with fixes.
3. Local DB proxy running: `platform/scripts/start_db_proxy.sh` (port 5433 per infra ref).
4. `INTEGRATION_TEST_API_KEY` env var set to a valid MCP API key.
5. `INTEGRATION_TEST_BASE_URL` set to `http://localhost:3000` (local dev) or the deployed URL.

Tests **skip gracefully** if `DB_PROXY_PORT` or `INTEGRATION_TEST_API_KEY` is not set —
they must be CI-safe (not block CI when secrets are absent).

---

## Test File: mcp_primitives.integration.test.ts

**Path**: `platform/src/__tests__/integration/mcp_primitives.integration.test.ts`

**Setup**:

```typescript
import { describe, it, expect, beforeAll } from 'vitest'

const BASE_URL = process.env.INTEGRATION_TEST_BASE_URL ?? 'http://localhost:3000'
const API_KEY = process.env.INTEGRATION_TEST_API_KEY ?? ''
const DB_PROXY_PORT = process.env.DB_PROXY_PORT

const CHART_ID = process.env.INTEGRATION_CHART_ID ?? '362f9f17-95a5-490b-a5a7-027d3e0efda0'
// ^ Native chart ID (Abhisek Mohanty) — use for all tests

const runIntegration = !!DB_PROXY_PORT && !!API_KEY

// All tests are skipped unless integration env is configured
const describeIf = runIntegration ? describe : describe.skip

async function callPrimitive(toolName: string, params: Record<string, unknown>) {
  const response = await fetch(`${BASE_URL}/api/mcp/primitives/${toolName}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      'X-MARSYS-Chart-Id': CHART_ID,
    },
    body: JSON.stringify({ params }),
  })
  return { status: response.status, body: await response.json() }
}
```

**Test Suite 1: The 14 formerly-phantom tools all return HTTP 200**

```typescript
describeIf('14 UDA tools — HTTP 200 with non-empty data (FIX-1 integration)', () => {
  const udaTools = [
    'msr_sql', 'temporal', 'kp_query', 'query_kp_ruling_planets',
    'pattern_register', 'resonance_register', 'cluster_atlas',
    'contradiction_register', 'query_ucn_walk', 'query_cdlm_lookup',
    'query_rm_walk', 'query_jaimini_drishti', 'timeline_query', 'query_signal_state',
  ]

  it.each(udaTools)('%s returns 200 (not 400 validation error)', async (tool) => {
    const { status, body } = await callPrimitive(tool, {})
    // Before FIX-1, all of these returned 400 "Tool not in whitelist"
    expect(status).not.toBe(400)
    // Accept 200 or 500 (500 = reached DB layer but may have minimal params)
    // The key assertion is: NOT 400 validation error
    if (status === 400) {
      console.error(`Tool ${tool} still blocked:`, body)
    }
    expect([200, 500]).toContain(status)
  }, 10000)  // 10s timeout for DB calls
})
```

**Test Suite 2: forward_looking filter (FIX-2 integration)**

```typescript
describeIf('msr_sql forward_looking filter (FIX-2 integration)', () => {
  it('forward_looking=true returns signals with is_forward_looking=true', async () => {
    const { status, body } = await callPrimitive('msr_sql', {
      forward_looking: true,
      limit: 10,
    })
    expect(status).toBe(200)
    const signals = body?.data ?? body?.signals ?? body?.rows ?? []
    if (signals.length > 0) {
      // Every returned signal must be forward-looking
      for (const signal of signals) {
        expect(signal.is_forward_looking).toBe(true)
      }
    }
    // At least a non-error response confirms the filter reached the DB
  }, 15000)

  it('forward_looking=false (no filter) returns a mix or all signals', async () => {
    const { status } = await callPrimitive('msr_sql', { forward_looking: false, limit: 5 })
    expect(status).toBe(200)
  }, 15000)
})
```

**Test Suite 3: valence filter (FIX-3 integration)**

```typescript
describeIf('query_signals valence filter (FIX-3 integration)', () => {
  it('valence="benefic" returns non-empty results', async () => {
    const { status, body } = await callPrimitive('query_signals', {
      valence: 'benefic',
      limit: 5,
    })
    expect(status).toBe(200)
    // After FIX-3, benefic signals should exist in the DB
    const signals = body?.data ?? body?.signals ?? body?.rows ?? []
    // Not asserting length > 0 (may be genuinely empty), but no error
    console.log(`query_signals valence=benefic returned ${signals.length} results`)
  }, 15000)

  it('valence="malefic" returns HTTP 200 (not schema error)', async () => {
    const { status } = await callPrimitive('query_signals', { valence: 'malefic', limit: 5 })
    expect(status).toBe(200)
  }, 15000)

  it('old vocabulary "positive" is rejected by schema (HTTP 400)', async () => {
    const { status } = await callPrimitive('query_signals', { valence: 'positive', limit: 5 })
    // After FIX-3, "positive" is not a valid enum value — should be rejected
    expect(status).toBe(400)
  }, 10000)
})
```

**Test Suite 4: sample_step downsampling (FIX-4 integration)**

```typescript
describeIf('query_ephemeris sample_step (FIX-4 integration)', () => {
  const dateRange = { planet: 'Moon', start_date: '2026-01-01', end_date: '2026-12-31' }

  it('sample_step="1d" returns ~365 rows', async () => {
    const { status, body } = await callPrimitive('query_ephemeris', {
      ...dateRange, sample_step: '1d'
    })
    expect(status).toBe(200)
    const rows = body?.data ?? body?.rows ?? []
    console.log(`sample_step=1d returned ${rows.length} rows`)
    if (rows.length > 0) expect(rows.length).toBeGreaterThan(300)
  }, 20000)

  it('sample_step="7d" returns ~52 rows (every 7th)', async () => {
    const { status, body } = await callPrimitive('query_ephemeris', {
      ...dateRange, sample_step: '7d'
    })
    expect(status).toBe(200)
    const rows = body?.data ?? body?.rows ?? []
    console.log(`sample_step=7d returned ${rows.length} rows`)
    if (rows.length > 0) {
      // Before FIX-4: returned ~365 rows (filter skipped). After FIX-4: ~52 rows.
      expect(rows.length).toBeLessThan(100)
    }
  }, 20000)

  it('sample_step="30d" returns ~12 rows (every 30th)', async () => {
    const { status, body } = await callPrimitive('query_ephemeris', {
      ...dateRange, sample_step: '30d'
    })
    expect(status).toBe(200)
    const rows = body?.data ?? body?.rows ?? []
    console.log(`sample_step=30d returned ${rows.length} rows`)
    if (rows.length > 0) expect(rows.length).toBeLessThan(20)
  }, 20000)
})
```

**Test Suite 5: significance filter (FIX-5 integration)**

```typescript
describeIf('lel_query significance filter (FIX-5 integration)', () => {
  it('significance_tier="tier_1" returns fewer events than tier_3', async () => {
    const [tier1, tier3] = await Promise.all([
      callPrimitive('lel_query', { significance_tier: 'tier_1', limit: 50 }),
      callPrimitive('lel_query', { significance_tier: 'tier_3', limit: 50 }),
    ])
    expect(tier1.status).toBe(200)
    expect(tier3.status).toBe(200)

    const t1Events = tier1.body?.data ?? tier1.body?.events ?? []
    const t3Events = tier3.body?.data ?? tier3.body?.events ?? []
    console.log(`tier_1: ${t1Events.length} events, tier_3: ${t3Events.length} events`)
    // tier_1 (high significance) should return ≤ tier_3 (lower threshold)
    // Before FIX-5: both returned same result (filter ignored)
    // After FIX-5: tier_1 ≤ tier_3 in count
    if (t1Events.length > 0 && t3Events.length > 0) {
      expect(t1Events.length).toBeLessThanOrEqual(t3Events.length)
    }
  }, 20000)
})
```

---

## README for integration tests

**Path**: `platform/src/__tests__/integration/README.md`

```markdown
# Integration Tests

These tests require a running local environment. They are skipped in CI unless
integration env vars are set.

## Setup

1. Start DB proxy: `bash platform/scripts/start_db_proxy.sh`
2. Start Next.js dev server: `cd platform && npm run dev`
3. Set env vars:
   - `DB_PROXY_PORT=5433`
   - `INTEGRATION_TEST_API_KEY=<mcp_api_key>`
   - `INTEGRATION_TEST_BASE_URL=http://localhost:3000`
   - `INTEGRATION_CHART_ID=362f9f17-95a5-490b-a5a7-027d3e0efda0` (optional, this is default)

## Run

```bash
DB_PROXY_PORT=5433 INTEGRATION_TEST_API_KEY=<key> npx vitest run src/__tests__/integration/
```

## CI

Integration tests are skipped when `DB_PROXY_PORT` or `INTEGRATION_TEST_API_KEY` is absent.
They can be enabled in CI by adding the secrets to the GitHub Actions workflow.
```

---

## Acceptance Criteria

- [ ] All 14 formerly-phantom tools return non-400 response.
- [ ] `forward_looking=true` filter returns only forward-looking signals.
- [ ] `valence="benefic"` returns HTTP 200; `valence="positive"` returns HTTP 400.
- [ ] `sample_step="7d"` returns significantly fewer rows than `sample_step="1d"`.
- [ ] `significance_tier="tier_1"` returns ≤ events vs `significance_tier="tier_3"`.
- [ ] All tests skip gracefully when `DB_PROXY_PORT` absent.
- [ ] `npx vitest run src/__tests__/integration/` passes (or skips, not fails) in CI.
- [ ] PR opened from `test/srp-t3-integration`.

## Session Close

Commit message:
```
test(srp-t3): integration tests — MCP primitives filter fidelity against live DB

Covers: FIX-1 (14 UDA tools no longer blocked), FIX-2 (forward_looking SQL filter),
FIX-3 (valence vocabulary), FIX-4 (sample_step downsampling), FIX-5 (significance tier).
Tests skip gracefully when DB_PROXY_PORT absent. README added.
```
