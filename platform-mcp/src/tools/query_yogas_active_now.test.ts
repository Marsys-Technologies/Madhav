/**
 * query_yogas_active_now.test.ts — Unit tests for the query_yogas_active_now MCP tool.
 *
 * TR-P6-S2 AC: all 8 tests must pass.
 * Mocks callPlatformPrimitive to verify yoga classification, dasha matching,
 * filter application, and error/empty handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive BEFORE importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryYogasActiveNow } from './query_yogas_active_now.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build a chart_facts yoga envelope with the given yoga rows.
 * Uses the direct rows_by_category shape (no ToolBundle wrapping).
 */
function buildYogaEnvelope(yogaRows: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-yoga-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true },
      result: {
        rows_by_category: {
          yoga: yogaRows,
        },
      },
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    },
  }
}

/**
 * Build a dasha periods envelope with the given periods array.
 * Uses the direct periods shape (as returned by query_dasha_periods).
 */
function buildDashaEnvelope(periods: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-dasha-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true },
      result: {
        periods,
      },
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    },
  }
}

function buildErrorEnvelope() {
  return {
    status: 500,
    envelope: {
      ok: false,
      trace_id: 'trace-fail-001',
      error: { class: 'internal', message: 'DB error', remediation: 'retry' },
    },
  }
}

/**
 * Invoke the query_yogas_active_now handler directly via a stub McpServer.
 */
async function callQueryYogasActiveNow(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      _schema: unknown,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
    },
  } as unknown as McpServer

  registerQueryYogasActiveNow(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_yogas_active_now handler was not registered')
  return capturedHandler(args)
}

/**
 * Parse the MCP content text envelope and return the first content item as JSON.
 */
function parseResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Sample data ───────────────────────────────────────────────────────────────

const JUPITER_YOGA_ROW = {
  fact_id: 'YG.001',
  category: 'yoga',
  yoga_name: 'Hamsa Yoga',
  planet: 'Jupiter',
}

const SATURN_YOGA_ROW = {
  fact_id: 'YG.002',
  category: 'yoga',
  yoga_name: 'Shasha Yoga',
  planet: 'Saturn',
}

const CURRENT_DASHA = {
  mahadasha: 'Jupiter',
  antardasha: 'Moon',
  pratyantar: 'Mars',
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_yogas_active_now (TR-P6-S2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── Test 1: Jupiter yoga is active when MD=Jupiter ────────────────────────

  it('T1 — Jupiter yoga has status "active" and dasha_match=true when MD=Jupiter, AD=Moon', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([JUPITER_YOGA_ROW, SATURN_YOGA_ROW]))
      .mockResolvedValueOnce(buildDashaEnvelope([CURRENT_DASHA]))

    const result = await callQueryYogasActiveNow({ date: '2026-05-25' })
    const parsed = parseResult(result)
    expect(parsed.ok).toBe(true)

    const yogas = parsed.yogas as Array<Record<string, unknown>>
    const jupiterYoga = yogas.find(y => y.yoga_name === 'Hamsa Yoga')

    expect(jupiterYoga).toBeDefined()
    expect(jupiterYoga!.status).toBe('active')
    expect(jupiterYoga!.dasha_match).toBe(true)
  })

  // ── Test 2: Saturn yoga is dormant when MD=Jupiter, AD=Moon ───────────────

  it('T2 — Saturn yoga has status "latent" or "dormant" (no match with MD=Jupiter, AD=Moon)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([JUPITER_YOGA_ROW, SATURN_YOGA_ROW]))
      .mockResolvedValueOnce(buildDashaEnvelope([CURRENT_DASHA]))

    const result = await callQueryYogasActiveNow({ date: '2026-05-25' })
    const parsed = parseResult(result)

    const yogas = parsed.yogas as Array<Record<string, unknown>>
    const saturnYoga = yogas.find(y => y.yoga_name === 'Shasha Yoga')

    expect(saturnYoga).toBeDefined()
    // Saturn doesn't match MD=Jupiter or AD=Moon — should be latent (has key_planets) or dormant
    expect(['latent', 'dormant']).toContain(saturnYoga!.status)
    expect(saturnYoga!.dasha_match).toBe(false)
  })

  // ── Test 3: active_count = 1 ──────────────────────────────────────────────

  it('T3 — active_count equals 1 when only Jupiter yoga is active', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([JUPITER_YOGA_ROW, SATURN_YOGA_ROW]))
      .mockResolvedValueOnce(buildDashaEnvelope([CURRENT_DASHA]))

    const result = await callQueryYogasActiveNow({ date: '2026-05-25' })
    const parsed = parseResult(result)

    expect(parsed.active_count).toBe(1)
  })

  // ── Test 4: total_yogas = 2 ───────────────────────────────────────────────

  it('T4 — total_yogas equals 2 when chart_facts returns 2 yoga rows', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([JUPITER_YOGA_ROW, SATURN_YOGA_ROW]))
      .mockResolvedValueOnce(buildDashaEnvelope([CURRENT_DASHA]))

    const result = await callQueryYogasActiveNow({ date: '2026-05-25' })
    const parsed = parseResult(result)

    expect(parsed.total_yogas).toBe(2)
  })

  // ── Test 5: status_filter='active' returns only active yogas ─────────────

  it('T5 — status_filter="active" returns only active yogas in response', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([JUPITER_YOGA_ROW, SATURN_YOGA_ROW]))
      .mockResolvedValueOnce(buildDashaEnvelope([CURRENT_DASHA]))

    const result = await callQueryYogasActiveNow({ date: '2026-05-25', status_filter: 'active' })
    const parsed = parseResult(result)

    const yogas = parsed.yogas as Array<Record<string, unknown>>
    expect(yogas.every(y => y.status === 'active')).toBe(true)
    // total_yogas still reflects all yogas; only yogas array is filtered
    expect(parsed.total_yogas).toBe(2)
    expect(yogas.length).toBeLessThan(2) // at most 1 active
  })

  // ── Test 6: 0 yoga rows — no crash, total_yogas=0 ─────────────────────────

  it('T6 — 0 yoga rows: total_yogas=0, yogas=[], no crash', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([]))
      .mockResolvedValueOnce(buildDashaEnvelope([CURRENT_DASHA]))

    const result = await callQueryYogasActiveNow({ date: '2026-05-25' })
    const parsed = parseResult(result)

    expect(parsed.ok).toBe(true)
    expect(parsed.total_yogas).toBe(0)
    expect(Array.isArray(parsed.yogas)).toBe(true)
    expect((parsed.yogas as unknown[]).length).toBe(0)
  })

  // ── Test 7: dasha call error → dasha_context=null, all yogas dormant ──────

  it('T7 — dasha call returns error: dasha_context=null, all yogas dormant', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    // chart_facts succeeds; dasha returns an error
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([JUPITER_YOGA_ROW, SATURN_YOGA_ROW]))
      .mockResolvedValueOnce(buildErrorEnvelope())

    const result = await callQueryYogasActiveNow({ date: '2026-05-25' })
    const parsed = parseResult(result)

    expect(parsed.ok).toBe(true)
    expect(parsed.dasha_context).toBeNull()

    const yogas = parsed.yogas as Array<Record<string, unknown>>
    expect(yogas.every(y => y.status === 'dormant')).toBe(true)
    expect(yogas.every(y => y.dasha_match === false)).toBe(true)
  })

  // ── Test 8: evaluation_date is passed through / defaults to today ─────────

  it('T8 — evaluation_date echoes the input date when date param is provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([]))
      .mockResolvedValueOnce(buildDashaEnvelope([]))

    const result = await callQueryYogasActiveNow({ date: '2025-01-15' })
    const parsed = parseResult(result)

    expect(parsed.evaluation_date).toBe('2025-01-15')
  })

  it('T8b — evaluation_date is a non-empty string when date param is omitted', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([]))
      .mockResolvedValueOnce(buildDashaEnvelope([]))

    const result = await callQueryYogasActiveNow({})
    const parsed = parseResult(result)

    expect(typeof parsed.evaluation_date).toBe('string')
    expect((parsed.evaluation_date as string).length).toBeGreaterThan(0)
    // Should look like an ISO date (YYYY-MM-DD)
    expect(parsed.evaluation_date).toMatch(/^\d{4}-\d{2}-\d{2}/)
  })

  // ── Additional: planets_involved array field ───────────────────────────────

  it('planets_involved array — extracts multiple key planets from array field', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    const multiPlanetRow = {
      fact_id: 'YG.010',
      category: 'yoga',
      yoga_name: 'Raja Yoga',
      planets_involved: ['Jupiter', 'Moon'],
    }
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([multiPlanetRow]))
      .mockResolvedValueOnce(buildDashaEnvelope([CURRENT_DASHA])) // MD=Jupiter, AD=Moon

    const result = await callQueryYogasActiveNow({ date: '2026-05-25' })
    const parsed = parseResult(result)

    const yogas = parsed.yogas as Array<Record<string, unknown>>
    expect(yogas.length).toBe(1)
    const y = yogas[0]
    // Both Jupiter (MD) and Moon (AD) match — expect active + double-dasha reason
    expect(y.status).toBe('active')
    expect(y.dasha_match).toBe(true)
    const keyPlanets = y.key_planets as string[]
    expect(keyPlanets).toContain('Jupiter')
    expect(keyPlanets).toContain('Moon')
  })

  // ── Additional: dasha_context is populated when dasha succeeds ────────────

  it('dasha_context reflects MD/AD/PD from the dasha response', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall
      .mockResolvedValueOnce(buildYogaEnvelope([JUPITER_YOGA_ROW]))
      .mockResolvedValueOnce(buildDashaEnvelope([CURRENT_DASHA]))

    const result = await callQueryYogasActiveNow({ date: '2026-05-25' })
    const parsed = parseResult(result)

    const ctx = parsed.dasha_context as Record<string, unknown> | null
    expect(ctx).not.toBeNull()
    expect(ctx!.md).toBe('Jupiter')
    expect(ctx!.ad).toBe('Moon')
    expect(ctx!.pd).toBe('Mars')
  })
})
