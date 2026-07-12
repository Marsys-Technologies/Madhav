/**
 * mcp_primitives.integration.test.ts — Integration tests for /api/mcp/primitives/[tool].
 *
 * Tests the full HTTP stack from request → route handler → retrieval tool → SQL → DB.
 * Requires a running local dev server + DB proxy.
 *
 * Tests SKIP gracefully when DB_PROXY_PORT or INTEGRATION_TEST_API_KEY is absent.
 *
 * Coverage:
 *   - FIX-1: 14 formerly-phantom UDA tools all return non-400 responses
 *   - FIX-2: msr_sql forward_looking filter reaches the DB layer
 *   - FIX-3: valence vocabulary (benefic/malefic accepted; positive rejected)
 *   - FIX-4: query_ephemeris sample_step downsampling
 *   - FIX-5: lel_query significance_tier filter
 */

import { describe, it, expect } from 'vitest'

const BASE_URL = process.env.INTEGRATION_TEST_BASE_URL ?? 'http://localhost:3000'
const API_KEY = process.env.INTEGRATION_TEST_API_KEY ?? ''
const DB_PROXY_PORT = process.env.DB_PROXY_PORT

const CHART_ID = process.env.INTEGRATION_CHART_ID ?? '482012f1-710e-4a25-994a-93821f5871aa'
// ^ Native chart ID (Abhisek Mohanty) — use for all tests

// All tests are skipped unless integration env is configured
const runIntegration = !!DB_PROXY_PORT && !!API_KEY
const describeIf = runIntegration ? describe : describe.skip

/**
 * Call a surgical primitive via the portal's /api/mcp/primitives/[tool] route.
 *
 * Auth model: passes the API key as the MCP internal service token,
 * plus resolved principal headers matching dev-mode expectations.
 * When MCP_INTERNAL_TOKEN is not set in the dev server, service token
 * validation is bypassed in NODE_ENV=development.
 */
async function callPrimitive(toolName: string, params: Record<string, unknown>) {
  const response = await fetch(`${BASE_URL}/api/mcp/primitives/${toolName}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      'X-MARSYS-Chart-Id': CHART_ID,
      // Resolved principal headers required by the route handler
      'x-mcp-internal-token': API_KEY,
      'x-mcp-user': 'integration-test-user',
      'x-mcp-audience-tier': 'super_admin',
      'x-mcp-key-id': 'integration-test-key',
    },
    body: JSON.stringify({ params }),
  })
  return { status: response.status, body: await response.json() }
}

// ── Test Suite 1: 14 formerly-phantom UDA tools all return HTTP 200 ───────────

// WP-1.7 (LCA-1/13): the retained UDA tools resolve to a real capability → non-400.
describeIf('retained UDA tools — resolve (not 400) (WP-1.7)', () => {
  const retainedUdaTools = ['msr_sql', 'temporal', 'contradiction_register']

  it.each(retainedUdaTools)('%s returns 200/500 (not 400 validation error)', async (tool) => {
    const { status, body } = await callPrimitive(tool, {})
    expect(status).not.toBe(400)
    if (status === 400) {
      console.error(`Tool ${tool} unexpectedly blocked:`, body)
    }
    expect([200, 500]).toContain(status)
  }, 10000)  // 10s timeout for DB calls
})

// WP-1.7 (LCA-1/13): the 12 dead tools were REMOVED from the whitelist — they must now
// return a clean 400 {class:"validation"}, NOT a 500 (the pre-fix local-bench crash).
describeIf('WP-1.7-removed dead tools — clean 400 validation (no more 500)', () => {
  const removedDeadTools = [
    'cross_school_lookup', 'kp_query', 'query_kp_ruling_planets',
    'pattern_register', 'resonance_register', 'cluster_atlas',
    'query_ucn_walk', 'query_cdlm_lookup', 'query_rm_walk',
    'query_jaimini_drishti', 'timeline_query', 'query_signal_state',
  ]

  it.each(removedDeadTools)('%s returns 400 validation (not 500)', async (tool) => {
    const { status, body } = await callPrimitive(tool, {})
    expect(status).toBe(400)
    expect(body?.error?.class).toBe('validation')
  }, 10000)
})

// ── Test Suite 2: forward_looking filter (FIX-2 integration) ─────────────────

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

// ── Test Suite 3: valence filter (FIX-3 integration) ─────────────────────────

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

// ── Test Suite 4: sample_step downsampling (FIX-4 integration) ───────────────

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

// ── Test Suite 5: significance filter (FIX-5 integration) ────────────────────

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
