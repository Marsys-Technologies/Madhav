/**
 * query_eclipse_transits.test.ts — Unit tests for the query_eclipse_transits MCP tool.
 *
 * TR-P8-S1 acceptance criteria:
 *   T1 — Returns an array (empty or non-empty) for any valid date_range.
 *   T2 — eclipse_type filter "solar" returns only solar eclipses (mock data).
 *   T3 — eclipse_type filter "lunar" returns only lunar eclipses (mock data).
 *   T4 — Each result has date, eclipse_type, degree, sign.
 *   T5 — natal_sensitive_points=true flags eclipse near natal_moon.
 *   T6 — Sidecar not running: uses vi.mock to mock sidecar call (no real HTTP).
 *   T7 — Empty ephemeris positions → eclipses is [] and total_eclipses is 0.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive BEFORE importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import {
  registerQueryEclipseTransits,
  detectEclipses,
  type EclipseEvent,
} from './query_eclipse_transits.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build a ToolBundle-style envelope wrapping ephemeris positions.
 * Positions is an array of {date, planet, longitude} objects.
 */
function buildEphemerisEnvelope(positions: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-eph-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true },
      result: {
        results: [
          {
            content: JSON.stringify({ positions }),
            source_canonical_id: 'EPHEMERIS',
            confidence: 1.0,
          },
        ],
      },
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
 * Registers query_eclipse_transits on a stub McpServer and invokes handler.
 */
async function callQueryEclipseTransits(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
  applyZodValidation = false,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null
  let capturedSchema: Record<string, unknown> | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      schema: Record<string, unknown>,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
      capturedSchema = schema
    },
  } as unknown as McpServer

  registerQueryEclipseTransits(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_eclipse_transits handler was not registered')

  if (applyZodValidation) {
    const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
    const zodSchema = z.object(schemaShape)
    const parseResult = zodSchema.safeParse(args)
    if (!parseResult.success) {
      return { zodError: parseResult.error, isZodError: true }
    }
    return capturedHandler(parseResult.data as Record<string, unknown>)
  }

  return capturedHandler(args)
}

function parseToolResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Mock ephemeris data with a solar eclipse ──────────────────────────────────
//
// Solar eclipse conditions:
//   Sun at 45.0°, Moon at 44.5° → separation = 0.5° ≤ 1°
//   Rahu at 50.0° → Moon–Rahu = 5.5° ≤ 12°
//
// Lunar eclipse conditions (different date):
//   Sun at 10.0°, Moon at 191.0° → opposition sep = |181.0 - 180| = 1.0° ≤ 1°
//   Rahu at 196.0° → Moon–Rahu = 5.0° ≤ 12°

const SOLAR_ECLIPSE_DATE = '2026-03-15'
const LUNAR_ECLIPSE_DATE = '2026-09-07'

const SOLAR_ECLIPSE_POSITIONS = [
  { date: SOLAR_ECLIPSE_DATE, planet: 'Sun', longitude: 45.0 },
  { date: SOLAR_ECLIPSE_DATE, planet: 'Moon', longitude: 44.5 },
  { date: SOLAR_ECLIPSE_DATE, planet: 'Rahu', longitude: 50.0 },
  { date: SOLAR_ECLIPSE_DATE, planet: 'Ketu', longitude: 230.0 },
]

const LUNAR_ECLIPSE_POSITIONS = [
  { date: LUNAR_ECLIPSE_DATE, planet: 'Sun', longitude: 10.0 },
  { date: LUNAR_ECLIPSE_DATE, planet: 'Moon', longitude: 191.0 },
  { date: LUNAR_ECLIPSE_DATE, planet: 'Rahu', longitude: 196.0 },
  { date: LUNAR_ECLIPSE_DATE, planet: 'Ketu', longitude: 16.0 },
]

const BOTH_ECLIPSE_POSITIONS = [...SOLAR_ECLIPSE_POSITIONS, ...LUNAR_ECLIPSE_POSITIONS]

// A date with no eclipse (planets not near conjunction/opposition with nodes)
const NO_ECLIPSE_POSITIONS = [
  { date: '2026-04-01', planet: 'Sun', longitude: 10.0 },
  { date: '2026-04-01', planet: 'Moon', longitude: 90.0 },
  { date: '2026-04-01', planet: 'Rahu', longitude: 250.0 },
  { date: '2026-04-01', planet: 'Ketu', longitude: 70.0 },
]

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_eclipse_transits (TR-P8-S1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── T1: Returns array for any valid date_range ─────────────────────────────

  it('T1 — Returns an array (eclipses field) for any valid date_range', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(NO_ECLIPSE_POSITIONS),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-04-01', to: '2026-04-30' },
      eclipse_type: 'all',
    })
    const parsed = parseToolResult(result)

    expect(parsed['ok']).toBe(true)
    expect(Array.isArray(parsed['eclipses'])).toBe(true)
    expect(typeof parsed['total_eclipses']).toBe('number')
  })

  it('T1 — Non-eclipse date returns empty eclipses array', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(NO_ECLIPSE_POSITIONS),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-04-01', to: '2026-04-30' },
    })
    const parsed = parseToolResult(result)

    expect(parsed['eclipses']).toEqual([])
    expect(parsed['total_eclipses']).toBe(0)
  })

  // ── T2: eclipse_type filter "solar" returns only solar eclipses ────────────

  it('T2 — eclipse_type "solar" returns only solar eclipses', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(BOTH_ECLIPSE_POSITIONS),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-01-01', to: '2026-12-31' },
      eclipse_type: 'solar',
    })
    const parsed = parseToolResult(result)
    const eclipses = parsed['eclipses'] as EclipseEvent[]

    expect(eclipses.length).toBeGreaterThan(0)
    for (const e of eclipses) {
      expect(e.eclipse_type).toBe('solar')
    }
  })

  it('T2 — eclipse_type "solar" does not return any lunar eclipses', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(BOTH_ECLIPSE_POSITIONS),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-01-01', to: '2026-12-31' },
      eclipse_type: 'solar',
    })
    const parsed = parseToolResult(result)
    const eclipses = parsed['eclipses'] as EclipseEvent[]

    const hasLunar = eclipses.some(e => e.eclipse_type === 'lunar')
    expect(hasLunar).toBe(false)
  })

  // ── T3: eclipse_type filter "lunar" returns only lunar eclipses ────────────

  it('T3 — eclipse_type "lunar" returns only lunar eclipses', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(BOTH_ECLIPSE_POSITIONS),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-01-01', to: '2026-12-31' },
      eclipse_type: 'lunar',
    })
    const parsed = parseToolResult(result)
    const eclipses = parsed['eclipses'] as EclipseEvent[]

    expect(eclipses.length).toBeGreaterThan(0)
    for (const e of eclipses) {
      expect(e.eclipse_type).toBe('lunar')
    }
  })

  // ── T4: Each result has date, eclipse_type, degree, sign ──────────────────

  it('T4 — Each eclipse result has required fields: date, eclipse_type, degree, sign', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(BOTH_ECLIPSE_POSITIONS),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-01-01', to: '2026-12-31' },
      eclipse_type: 'all',
    })
    const parsed = parseToolResult(result)
    const eclipses = parsed['eclipses'] as EclipseEvent[]

    expect(eclipses.length).toBeGreaterThan(0)
    for (const e of eclipses) {
      expect(typeof e.date).toBe('string')
      expect(['solar', 'lunar']).toContain(e.eclipse_type)
      expect(typeof e.degree).toBe('number')
      expect(typeof e.sign).toBe('string')
      expect(e.sign.length).toBeGreaterThan(0)
    }
  })

  it('T4 — Solar eclipse is detected on expected date', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(SOLAR_ECLIPSE_POSITIONS),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-03-01', to: '2026-03-31' },
      eclipse_type: 'solar',
    })
    const parsed = parseToolResult(result)
    const eclipses = parsed['eclipses'] as EclipseEvent[]

    expect(eclipses.length).toBe(1)
    expect(eclipses[0].date).toBe(SOLAR_ECLIPSE_DATE)
    expect(eclipses[0].eclipse_type).toBe('solar')
    // Moon at 44.5° → Taurus (30-60°)
    expect(eclipses[0].sign).toBe('Taurus')
  })

  it('T4 — Lunar eclipse is detected on expected date', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(LUNAR_ECLIPSE_POSITIONS),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-09-01', to: '2026-09-30' },
      eclipse_type: 'lunar',
    })
    const parsed = parseToolResult(result)
    const eclipses = parsed['eclipses'] as EclipseEvent[]

    expect(eclipses.length).toBe(1)
    expect(eclipses[0].date).toBe(LUNAR_ECLIPSE_DATE)
    expect(eclipses[0].eclipse_type).toBe('lunar')
  })

  // ── T5: natal_sensitive_points flags eclipse near natal_moon ──────────────

  it('T5 — natal_sensitive_points=true flags eclipse conjunct natal_moon', async () => {
    // Place Moon at 335.0° (exactly on native natal_moon) with a solar eclipse geometry
    // Sun at 334.5° (Moon-Sun sep = 0.5° ≤ 1°), Rahu at 330.0° (Moon-Rahu = 5° ≤ 12°)
    const natalMoonEclipsePositions = [
      { date: '2026-06-20', planet: 'Sun', longitude: 334.5 },
      { date: '2026-06-20', planet: 'Moon', longitude: 335.0 },
      { date: '2026-06-20', planet: 'Rahu', longitude: 330.0 },
      { date: '2026-06-20', planet: 'Ketu', longitude: 150.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(natalMoonEclipsePositions),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      eclipse_type: 'solar',
      natal_sensitive_points: true,
    })
    const parsed = parseToolResult(result)
    const eclipses = parsed['eclipses'] as EclipseEvent[]

    expect(eclipses.length).toBe(1)
    expect(eclipses[0].conjunct_natal_point).toBe('natal_moon')
    expect(eclipses[0].impact_assessment).toContain('natal moon')
  })

  it('T5 — natal_sensitive_points=false → conjunct_natal_point is null even on natal point', async () => {
    const natalMoonEclipsePositions = [
      { date: '2026-06-20', planet: 'Sun', longitude: 334.5 },
      { date: '2026-06-20', planet: 'Moon', longitude: 335.0 },
      { date: '2026-06-20', planet: 'Rahu', longitude: 330.0 },
      { date: '2026-06-20', planet: 'Ketu', longitude: 150.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(natalMoonEclipsePositions),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      eclipse_type: 'solar',
      natal_sensitive_points: false,
    })
    const parsed = parseToolResult(result)
    const eclipses = parsed['eclipses'] as EclipseEvent[]

    expect(eclipses.length).toBe(1)
    expect(eclipses[0].conjunct_natal_point).toBeNull()
  })

  // ── T6: Sidecar mock — no real HTTP calls ─────────────────────────────────

  it('T6 — callPlatformPrimitive is mocked (no real sidecar HTTP call)', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(NO_ECLIPSE_POSITIONS),
    )

    await callQueryEclipseTransits({
      date_range: { from: '2026-04-01', to: '2026-04-30' },
    })

    // Verify the mock was called with query_ephemeris (not the eclipses sidecar)
    expect(vi.mocked(callPlatformPrimitive)).toHaveBeenCalledTimes(1)
    expect(vi.mocked(callPlatformPrimitive)).toHaveBeenCalledWith(
      'query_ephemeris',
      expect.objectContaining({
        start_date: '2026-04-01',
        end_date: '2026-04-30',
      }),
      expect.any(Object),
    )
  })

  // ── T7: Empty ephemeris positions → eclipses is [] ────────────────────────

  it('T7 — Empty ephemeris positions → eclipses is [] and total_eclipses is 0', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope([]),
    )

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-01-01', to: '2026-12-31' },
    })
    const parsed = parseToolResult(result)

    expect(parsed['eclipses']).toEqual([])
    expect(parsed['total_eclipses']).toBe(0)
  })

  it('T7 — Ephemeris error envelope → tool returns isError result', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(buildErrorEnvelope())

    const result = await callQueryEclipseTransits({
      date_range: { from: '2026-01-01', to: '2026-12-31' },
    })

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // ── Unit: detectEclipses helper ────────────────────────────────────────────

  it('Unit — detectEclipses detects solar from pre-built byDate map', () => {
    const byDate = new Map()
    byDate.set(SOLAR_ECLIPSE_DATE, new Map([
      ['sun', { date: SOLAR_ECLIPSE_DATE, planet: 'Sun', longitude: 45.0 }],
      ['moon', { date: SOLAR_ECLIPSE_DATE, planet: 'Moon', longitude: 44.5 }],
      ['rahu', { date: SOLAR_ECLIPSE_DATE, planet: 'Rahu', longitude: 50.0 }],
      ['ketu', { date: SOLAR_ECLIPSE_DATE, planet: 'Ketu', longitude: 230.0 }],
    ]))

    const events = detectEclipses(byDate, 'all', false)
    expect(events.length).toBe(1)
    expect(events[0].eclipse_type).toBe('solar')
    expect(events[0].date).toBe(SOLAR_ECLIPSE_DATE)
  })

  it('Unit — detectEclipses detects lunar from pre-built byDate map', () => {
    const byDate = new Map()
    byDate.set(LUNAR_ECLIPSE_DATE, new Map([
      ['sun', { date: LUNAR_ECLIPSE_DATE, planet: 'Sun', longitude: 10.0 }],
      ['moon', { date: LUNAR_ECLIPSE_DATE, planet: 'Moon', longitude: 191.0 }],
      ['rahu', { date: LUNAR_ECLIPSE_DATE, planet: 'Rahu', longitude: 196.0 }],
      ['ketu', { date: LUNAR_ECLIPSE_DATE, planet: 'Ketu', longitude: 16.0 }],
    ]))

    const events = detectEclipses(byDate, 'all', false)
    expect(events.length).toBe(1)
    expect(events[0].eclipse_type).toBe('lunar')
  })

  it('Unit — detectEclipses returns [] when no eclipse conditions met', () => {
    const byDate = new Map()
    byDate.set('2026-04-01', new Map([
      ['sun', { date: '2026-04-01', planet: 'Sun', longitude: 10.0 }],
      ['moon', { date: '2026-04-01', planet: 'Moon', longitude: 90.0 }],
      ['rahu', { date: '2026-04-01', planet: 'Rahu', longitude: 250.0 }],
      ['ketu', { date: '2026-04-01', planet: 'Ketu', longitude: 70.0 }],
    ]))

    const events = detectEclipses(byDate, 'all', false)
    expect(events).toEqual([])
  })
})
