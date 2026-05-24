/**
 * get_shadbala_full.test.ts — Unit tests for the get_shadbala_full MCP tool.
 *
 * TR-P6-S3 acceptance criteria:
 *   AC.1 — Mock 3 Jupiter rows (sthana=30, dig=20, kala=10).
 *           Verify sthana_bala=30, dig_bala=20, kala_bala=10, total_virupa=60.
 *   AC.2 — total_rupa = total_virupa / 60 = 1.0.
 *   AC.3 — is_sufficient is boolean.
 *   AC.4 — planets filter: mock has Sun+Jupiter rows; only Jupiter in output.
 *   AC.5 — source_rows_used equals total number of shadbala rows.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive BEFORE importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerGetShadbalaFull, MINIMUM_RUPAS } from './get_shadbala_full.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build an envelope where chart_facts returns rows_by_category.shadbala directly on result.
 */
function buildShadbalaEnvelope(shadbalaRows: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-shadbala-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        rows_by_category: {
          shadbala: shadbalaRows,
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

function buildErrorEnvelope() {
  return {
    status: 500,
    envelope: {
      ok: false,
      trace_id: 'trace-fail-shadbala',
      error: { class: 'internal', message: 'DB error', remediation: 'retry' },
    },
  }
}

async function callGetShadbalaFull(
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

  registerGetShadbalaFull(stubServer, () => principal)

  if (!capturedHandler) throw new Error('get_shadbala_full handler was not registered')
  return capturedHandler(args)
}

function parseToolResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('get_shadbala_full (TR-P6-S3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── AC.1: 3 Jupiter rows → sthana=30, dig=20, kala=10, total=60 ───────────

  it('AC.1 — Jupiter rows: sthana_bala=30, dig_bala=20, kala_bala=10, total_virupa=60', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 30 },
      { planet: 'Jupiter', component_name: 'dig_bala', value_num: 20 },
      { planet: 'Jupiter', component_name: 'kala_bala', value_num: 10 },
    ]))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)

    expect(parsed['ok']).toBe(true)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(shadbala['Jupiter']).toBeDefined()
    expect(shadbala['Jupiter']['sthana_bala']).toBe(30)
    expect(shadbala['Jupiter']['dig_bala']).toBe(20)
    expect(shadbala['Jupiter']['kala_bala']).toBe(10)
    expect(shadbala['Jupiter']['total_virupa']).toBe(60)
  })

  it('AC.1 — unclassified component names are ignored (total reflects only known groups)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 30 },
      { planet: 'Jupiter', component_name: 'unknown_component', value_num: 999 },
    ]))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    // unknown_component should not be added to any group
    expect(shadbala['Jupiter']['sthana_bala']).toBe(30)
    expect(shadbala['Jupiter']['total_virupa']).toBe(30) // only sthana_bala counted
  })

  // ── AC.2: total_rupa = total_virupa / 60 ──────────────────────────────────

  it('AC.2 — total_rupa = total_virupa / 60 = 1.0 when total_virupa=60', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 30 },
      { planet: 'Jupiter', component_name: 'dig_bala', value_num: 20 },
      { planet: 'Jupiter', component_name: 'kala_bala', value_num: 10 },
    ]))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(shadbala['Jupiter']['total_rupa']).toBeCloseTo(1.0)
  })

  it('AC.2 — total_rupa is total_virupa / 60 (general)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Saturn', component_name: 'sthana_bala', value_num: 180 },
      { planet: 'Saturn', component_name: 'kala_bala', value_num: 120 },
    ]))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    const totalVirupa = shadbala['Saturn']['total_virupa'] as number
    const totalRupa = shadbala['Saturn']['total_rupa'] as number
    expect(totalRupa).toBeCloseTo(totalVirupa / 60)
  })

  // ── AC.3: is_sufficient is boolean ────────────────────────────────────────

  it('AC.3 — is_sufficient is a boolean', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 30 },
    ]))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(typeof shadbala['Jupiter']['is_sufficient']).toBe('boolean')
  })

  it('AC.3 — is_sufficient=true when total_rupa >= minimum (Jupiter: 390 virupa = 6.5 rupa)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    // Jupiter minimum = 6.5 rupa = 390 virupa
    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 390 },
    ]))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(shadbala['Jupiter']['is_sufficient']).toBe(true)
  })

  it('AC.3 — is_sufficient=false when total_rupa < minimum (Jupiter: 60 virupa = 1.0 rupa < 6.5)', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 60 },
    ]))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(shadbala['Jupiter']['is_sufficient']).toBe(false)
  })

  // ── AC.4: planets filter — only Jupiter in output when Sun also in rows ────

  it('AC.4 — planets: ["Jupiter"] filter excludes Sun rows', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    // Mock has both Sun and Jupiter rows
    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Sun', component_name: 'sthana_bala', value_num: 100 },
      { planet: 'Sun', component_name: 'dig_bala', value_num: 50 },
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 30 },
      { planet: 'Jupiter', component_name: 'dig_bala', value_num: 20 },
    ]))

    const result = await callGetShadbalaFull({ planets: ['Jupiter'] })
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    // Only Jupiter should be in the output
    expect(Object.keys(shadbala)).toContain('Jupiter')
    expect(Object.keys(shadbala)).not.toContain('Sun')
  })

  it('AC.4 — planets filter preserves correct sums for filtered planet', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Sun', component_name: 'sthana_bala', value_num: 999 },
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 30 },
      { planet: 'Jupiter', component_name: 'dig_bala', value_num: 20 },
      { planet: 'Jupiter', component_name: 'kala_bala', value_num: 10 },
    ]))

    const result = await callGetShadbalaFull({ planets: ['Jupiter'] })
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(shadbala['Jupiter']['sthana_bala']).toBe(30)
    expect(shadbala['Jupiter']['dig_bala']).toBe(20)
    expect(shadbala['Jupiter']['kala_bala']).toBe(10)
    expect(shadbala['Jupiter']['total_virupa']).toBe(60)
  })

  it('AC.4 — no planets filter returns all 7 classical planets in shadbala output', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    // Provide rows for all 7 classical planets
    const allPlanetRows = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].map(
      (planet) => ({ planet, component_name: 'sthana_bala', value_num: 60 })
    )
    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope(allPlanetRows))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    const keys = Object.keys(shadbala)
    expect(keys).toContain('Sun')
    expect(keys).toContain('Moon')
    expect(keys).toContain('Mars')
    expect(keys).toContain('Mercury')
    expect(keys).toContain('Jupiter')
    expect(keys).toContain('Venus')
    expect(keys).toContain('Saturn')
  })

  // ── AC.5: source_rows_used = total shadbala rows ──────────────────────────

  it('AC.5 — source_rows_used equals total number of shadbala rows', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    const rows = [
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 30 },
      { planet: 'Jupiter', component_name: 'dig_bala', value_num: 20 },
      { planet: 'Jupiter', component_name: 'kala_bala', value_num: 10 },
    ]
    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope(rows))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)

    expect(parsed['source_rows_used']).toBe(3)
  })

  it('AC.5 — source_rows_used is 0 when no shadbala rows', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([]))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)

    expect(parsed['source_rows_used']).toBe(0)
  })

  it('AC.5 — source_rows_used counts ALL rows, including those excluded by planets filter', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    // 4 rows total in the raw response
    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Sun', component_name: 'sthana_bala', value_num: 100 },
      { planet: 'Sun', component_name: 'dig_bala', value_num: 50 },
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 30 },
      { planet: 'Jupiter', component_name: 'dig_bala', value_num: 20 },
    ]))

    const result = await callGetShadbalaFull({ planets: ['Jupiter'] })
    const parsed = parseToolResult(result)

    // source_rows_used = total rows fetched from DB, not just filtered rows
    expect(parsed['source_rows_used']).toBe(4)
  })

  // ── Component classification regex tests ────────────────────────────────────

  it('component classification — naisargika prefix matches naisargika_bala group', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Venus', component_name: 'naisargika_strength', value_num: 45 },
    ]))

    const result = await callGetShadbalaFull({ planets: ['Venus'] })
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(shadbala['Venus']['naisargika_bala']).toBe(45)
  })

  it('component classification — drishti prefix matches drig_bala group', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Mars', component_name: 'drishti_bala', value_num: 15 },
    ]))

    const result = await callGetShadbalaFull({ planets: ['Mars'] })
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(shadbala['Mars']['drig_bala']).toBe(15)
  })

  it('component classification — cheshta matches cheshta_bala group', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Saturn', component_name: 'cheshta_bala', value_num: 25 },
    ]))

    const result = await callGetShadbalaFull({ planets: ['Saturn'] })
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(shadbala['Saturn']['cheshta_bala']).toBe(25)
  })

  // ── minimum_required_rupa is correct ─────────────────────────────────────

  it('minimum_required_rupa values match classical specs', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    const allPlanetRows = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].map(
      (planet) => ({ planet, component_name: 'sthana_bala', value_num: 0 })
    )
    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope(allPlanetRows))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)
    const shadbala = parsed['shadbala'] as Record<string, Record<string, unknown>>

    expect(shadbala['Sun']['minimum_required_rupa']).toBe(MINIMUM_RUPAS['Sun'])
    expect(shadbala['Moon']['minimum_required_rupa']).toBe(MINIMUM_RUPAS['Moon'])
    expect(shadbala['Mars']['minimum_required_rupa']).toBe(MINIMUM_RUPAS['Mars'])
    expect(shadbala['Mercury']['minimum_required_rupa']).toBe(MINIMUM_RUPAS['Mercury'])
    expect(shadbala['Jupiter']['minimum_required_rupa']).toBe(MINIMUM_RUPAS['Jupiter'])
    expect(shadbala['Venus']['minimum_required_rupa']).toBe(MINIMUM_RUPAS['Venus'])
    expect(shadbala['Saturn']['minimum_required_rupa']).toBe(MINIMUM_RUPAS['Saturn'])
  })

  // ── Error handling ─────────────────────────────────────────────────────────

  it('returns error result when primitive call fails', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValueOnce(buildErrorEnvelope())

    const result = await callGetShadbalaFull({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // ── ok result shape ────────────────────────────────────────────────────────

  it('returns ok: true in successful response', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)

    mockCall.mockResolvedValueOnce(buildShadbalaEnvelope([
      { planet: 'Jupiter', component_name: 'sthana_bala', value_num: 60 },
    ]))

    const result = await callGetShadbalaFull({})
    const parsed = parseToolResult(result)

    expect(parsed['ok']).toBe(true)
  })
})
