/**
 * Gateway unit tests — unit 3.gateway_pipeline_isolation.
 *
 * Covers AC.1 (search_tools + invoke_tool with authz) and AC.2 (B.11 forced-first).
 */

import { describe, it, expect, beforeEach } from 'vitest'
import {
  searchTools,
  invokeTool,
  registerExecutor,
  __resetRegistryForTests,
  GatewayError,
  B11_FLOOR_TOOL_NAMES,
} from '../index'
import type { DbLike } from '@/lib/auth/authorizeChartAccess'

/** Test DB — owner_id match → 'all', else deny. */
function makeDb(opts: {
  ownerByChart?: Record<string, string | null>
  grants?: Array<{ chart_id: string; principal_id: string; permission: string }>
}): DbLike {
  const owner = opts.ownerByChart ?? {}
  const grants = opts.grants ?? []
  return {
    async query<T>(sql: string, params?: unknown[]) {
      if (/FROM charts WHERE id=\$1/i.test(sql)) {
        const id = String(params?.[0] ?? '')
        const row = id in owner ? { owner_id: owner[id] } : null
        return { rows: row ? ([row] as unknown as T[]) : [] }
      }
      if (/FROM chart_grants/i.test(sql)) {
        const chartId = String(params?.[0] ?? '')
        const principalId = String(params?.[1] ?? '')
        const row = grants.find(
          g => g.chart_id === chartId && g.principal_id === principalId,
        )
        return { rows: row ? ([{ permission: row.permission }] as unknown as T[]) : [] }
      }
      return { rows: [] }
    },
  }
}

describe('gateway.searchTools', () => {
  it('returns the full registered catalog when no filter is given', () => {
    const out = searchTools()
    expect(out.length).toBeGreaterThan(0)
    // every result has the slim shape
    for (const r of out) {
      expect(typeof r.canonical_name).toBe('string')
      expect(typeof r.description).toBe('string')
      expect(typeof r.family).toBe('string')
      expect(typeof r.role).toBe('string')
      expect(typeof r.per_chart).toBe('boolean')
    }
  })

  it('filters by family', () => {
    const chart = searchTools({ family: 'chart' })
    expect(chart.length).toBeGreaterThan(0)
    expect(chart.every(t => t.family === 'chart')).toBe(true)
  })

  it('filters by role', () => {
    const ret = searchTools({ role: 'retrieval' })
    expect(ret.length).toBeGreaterThan(0)
    expect(ret.every(t => t.role === 'retrieval')).toBe(true)
  })

  it('filters by free-text query case-insensitively', () => {
    const out = searchTools({ query: 'CHART_FACTS' })
    expect(out.some(t => t.canonical_name === 'query_chart_facts')).toBe(true)
  })

  it('respects the limit parameter', () => {
    const out = searchTools({ limit: 2 })
    expect(out.length).toBeLessThanOrEqual(2)
  })
})

describe('gateway.invokeTool — error gates', () => {
  beforeEach(() => __resetRegistryForTests())

  it('throws UNKNOWN_TOOL when canonical_name is not in the contract registry', async () => {
    await expect(
      invokeTool({
        name: 'does_not_exist',
        params: {},
        ctx: { principal: { uid: 'u1', role: 'guest' } },
      }),
    ).rejects.toMatchObject({ code: 'UNKNOWN_TOOL' })
  })

  it('throws INVALID_PARAMS when params fail the Zod schema', async () => {
    registerExecutor('query_chart_facts', async () => ({ rows: [] }))
    await expect(
      invokeTool({
        name: 'query_chart_facts',
        params: { /* missing required chart_id */ },
        ctx: {
          principal: { uid: 'u1', role: 'super_admin' },
          b11FloorSatisfied: true,
        },
      }),
    ).rejects.toMatchObject({ code: 'INVALID_PARAMS' })
  })

  it('throws CHART_REQUIRED when a per_chart tool has no chart_id anywhere', async () => {
    // We need to bypass the Zod schema chart_id requirement to hit
    // CHART_REQUIRED — use a non-per-chart contract whose own schema is
    // permissive, but mark the contract per_chart at the gateway level
    // is impossible without mutating contracts. Instead, prove CHART_REQUIRED
    // via the integration with the per_chart contract: when chart_id field is
    // present but empty string the Zod schema still parses, and the gateway
    // path should reject. Let's exercise that.
    registerExecutor('query_chart_facts', async () => ({ rows: [] }))
    await expect(
      invokeTool({
        name: 'query_chart_facts',
        params: { chart_id: '' },
        ctx: {
          principal: { uid: 'u1', role: 'super_admin' },
          b11FloorSatisfied: true,
        },
      }),
    ).rejects.toMatchObject({ code: 'CHART_REQUIRED' })
  })

  it('throws AUTHZ_DENIED when the principal cannot access the chart', async () => {
    registerExecutor('query_chart_facts', async () => ({ rows: [] }))
    const db = makeDb({ ownerByChart: { 'chart-X': 'someone-else' } })
    await expect(
      invokeTool({
        name: 'query_chart_facts',
        params: { chart_id: 'chart-X' },
        ctx: {
          principal: { uid: 'u1', role: 'guest' },
          db,
          b11FloorSatisfied: true,
        },
      }),
    ).rejects.toMatchObject({ code: 'AUTHZ_DENIED' })
  })

  it('throws NO_EXECUTOR when a contract is registered but no executor is wired', async () => {
    // do NOT registerExecutor for query_chart_facts
    const db = makeDb({ ownerByChart: { 'chart-OK': 'u1' } })
    await expect(
      invokeTool({
        name: 'query_chart_facts',
        params: { chart_id: 'chart-OK' },
        ctx: {
          principal: { uid: 'u1', role: 'guest' },
          db,
          b11FloorSatisfied: true,
        },
      }),
    ).rejects.toMatchObject({ code: 'NO_EXECUTOR' })
  })
})

describe('gateway.invokeTool — B.11 forced-first', () => {
  beforeEach(() => __resetRegistryForTests())

  it('REJECTS a non-floor tool when b11FloorSatisfied is false (AC.2)', async () => {
    registerExecutor('query_chart_facts', async () => ({ rows: [] }))
    const db = makeDb({ ownerByChart: { 'chart-OK': 'u1' } })

    // query_chart_facts IS in the floor set, so pick a contract that is NOT.
    // From the current catalog: kp_query is not in B11_FLOOR_TOOL_NAMES.
    expect(B11_FLOOR_TOOL_NAMES.has('kp_query')).toBe(false)

    registerExecutor('kp_query', async () => ({ rows: [] }))

    await expect(
      invokeTool({
        name: 'kp_query',
        params: {
          chart_id: 'chart-OK',
          planet: 'Sun',
          stars: ['Krittika'],
          subs: [],
        },
        ctx: {
          principal: { uid: 'u1', role: 'guest' },
          db,
          // b11FloorSatisfied intentionally NOT set
        },
      }),
    ).rejects.toMatchObject({ code: 'B11_FLOOR_MISSING' })
  })

  it('ALLOWS a floor tool to run BEFORE b11FloorSatisfied is set', async () => {
    // query_chart_facts is in the floor set (predictive floor includes it).
    expect(B11_FLOOR_TOOL_NAMES.has('query_chart_facts')).toBe(true)
    const db = makeDb({ ownerByChart: { 'chart-OK': 'u1' } })
    registerExecutor('query_chart_facts', async () => ({ rows: ['fact'] }))

    const r = await invokeTool({
      name: 'query_chart_facts',
      params: { chart_id: 'chart-OK', category: 'planet' },
      ctx: {
        principal: { uid: 'u1', role: 'guest' },
        db,
        // b11FloorSatisfied NOT set — floor tools are exempt
      },
    })
    expect(r.ok).toBe(true)
    expect(r.resolved.chartId).toBe('chart-OK')
  })

  it('ALLOWS a non-floor tool once b11FloorSatisfied is true', async () => {
    registerExecutor('kp_query', async () => ({ rows: ['kp'] }))
    const db = makeDb({ ownerByChart: { 'chart-OK': 'u1' } })

    const r = await invokeTool({
      name: 'kp_query',
      params: {
        chart_id: 'chart-OK',
        planet: 'Sun',
        stars: ['Krittika'],
        subs: [],
      },
      ctx: {
        principal: { uid: 'u1', role: 'guest' },
        db,
        b11FloorSatisfied: true,
      },
    })
    expect(r.ok).toBe(true)
  })
})

describe('gateway.invokeTool — happy path + authz chokepoint', () => {
  beforeEach(() => __resetRegistryForTests())

  it('calls the executor and echoes resolved chart + ayanamsha + permission', async () => {
    let seenChart: string | undefined
    let seenAyanamsha: string | undefined
    registerExecutor('query_chart_facts', async (_params, ctx) => {
      seenChart = ctx.chartId
      seenAyanamsha = ctx.ayanamshaId
      return { rows: ['ok'] }
    })
    const db = makeDb({ ownerByChart: { 'chart-OK': 'u1' } })

    const r = await invokeTool({
      name: 'query_chart_facts',
      params: { chart_id: 'chart-OK' },
      ctx: {
        principal: { uid: 'u1', role: 'guest' },
        db,
        b11FloorSatisfied: true,
        ayanamshaId: 'true_chitra',
      },
    })

    expect(r.ok).toBe(true)
    expect(r.data).toEqual({ rows: ['ok'] })
    expect(r.resolved.chartId).toBe('chart-OK')
    expect(r.resolved.ayanamshaId).toBe('true_chitra')
    expect(r.resolved.permission).toBe('all')
    expect(seenChart).toBe('chart-OK')
    expect(seenAyanamsha).toBe('true_chitra')
  })

  it('super_admin always passes authz', async () => {
    registerExecutor('query_chart_facts', async () => ({ rows: ['admin'] }))
    const db = makeDb({ ownerByChart: { 'chart-OK': 'someone-else' } })

    const r = await invokeTool({
      name: 'query_chart_facts',
      params: { chart_id: 'chart-OK' },
      ctx: {
        principal: { uid: 'admin', role: 'super_admin' },
        db,
        b11FloorSatisfied: true,
      },
    })
    expect(r.resolved.permission).toBe('all')
  })

  it("chart_grants 'view' permission permits the call (read-only surface)", async () => {
    registerExecutor('query_chart_facts', async () => ({ rows: ['view'] }))
    const db = makeDb({
      ownerByChart: { 'chart-OK': 'owner-other' },
      grants: [{ chart_id: 'chart-OK', principal_id: 'u1', permission: 'view' }],
    })
    const r = await invokeTool({
      name: 'query_chart_facts',
      params: { chart_id: 'chart-OK' },
      ctx: {
        principal: { uid: 'u1', role: 'guest' },
        db,
        b11FloorSatisfied: true,
      },
    })
    expect(r.resolved.permission).toBe('view')
  })

  it('non-per-chart tool (read_classical_text) skips chart authz', async () => {
    registerExecutor('read_classical_text', async () => ({
      verses: [{ id: 'bphs-1', text: '...' }],
    }))
    const r = await invokeTool({
      name: 'read_classical_text',
      params: { text_id: 'bphs', limit: 10 },
      ctx: {
        principal: { uid: 'anyone', role: 'guest' },
        // no chartId, no db — non-per-chart tool path
        b11FloorSatisfied: true,
      },
    })
    expect(r.ok).toBe(true)
    expect(r.resolved.chartId).toBeNull()
    expect(r.resolved.permission).toBeNull()
  })

  it('prefers ctx.chartId over params.chart_id when both are present', async () => {
    let seen: string | undefined
    registerExecutor('query_chart_facts', async (_p, ctx) => {
      seen = ctx.chartId
      return { rows: [] }
    })
    const db = makeDb({ ownerByChart: { 'chart-CTX': 'u1' } })

    await invokeTool({
      name: 'query_chart_facts',
      params: { chart_id: 'chart-PARAMS' },
      ctx: {
        principal: { uid: 'u1', role: 'guest' },
        chartId: 'chart-CTX',
        db,
        b11FloorSatisfied: true,
      },
    })
    expect(seen).toBe('chart-CTX')
  })
})

describe('GatewayError', () => {
  it('carries code + meta + name', () => {
    const e = new GatewayError('UNKNOWN_TOOL', 'msg', { name: 'x' })
    expect(e.code).toBe('UNKNOWN_TOOL')
    expect(e.meta).toEqual({ name: 'x' })
    expect(e.name).toBe('GatewayError')
  })
})
