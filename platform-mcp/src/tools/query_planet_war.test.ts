/**
 * query_planet_war.test.ts — Unit tests for the query_planet_war MCP tool.
 *
 * TR-P8-S1 acceptance criteria:
 *   T1 — Returns array for any valid date_range.
 *   T2 — Mock: Mars at 45.3°, Venus at 45.0° on "2026-06-15" → 1 war, 0.3° orb.
 *   T3 — Winner determined correctly (higher declination wins).
 *   T4 — 360° wrap: planet at 359° and planet at 0.5° → detected as war (1.5° apart → NOT war; boundary test at 359° vs 0° = 1° IS war).
 *   T5 — Planets filter: only requested planets checked.
 *   T6 — classical_interpretation is non-empty string matching winner.
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
  registerQueryPlanetWar,
  detectPlanetWars,
  determineWinner,
  buildWarInterpretation,
  angularSep,
  type WarEvent,
} from './query_planet_war.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildEphemerisEnvelope(positions: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-eph-war-001',
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

async function callQueryPlanetWar(
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

  registerQueryPlanetWar(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_planet_war handler was not registered')

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

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_planet_war (TR-P8-S1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── T1: Returns array for any valid date_range ─────────────────────────────

  it('T1 — Returns an array (war_events field) for any valid date_range', async () => {
    // Positions far apart — no war
    const noWarPositions = [
      { date: '2026-04-01', planet: 'Mars', longitude: 45.0 },
      { date: '2026-04-01', planet: 'Venus', longitude: 120.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(noWarPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-04-01', to: '2026-04-30' },
    })
    const parsed = parseToolResult(result)

    expect(parsed['ok']).toBe(true)
    expect(Array.isArray(parsed['war_events'])).toBe(true)
    expect(typeof parsed['total_wars']).toBe('number')
  })

  it('T1 — No-war positions returns empty war_events', async () => {
    const noWarPositions = [
      { date: '2026-04-01', planet: 'Mars', longitude: 45.0 },
      { date: '2026-04-01', planet: 'Venus', longitude: 120.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(noWarPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-04-01', to: '2026-04-30' },
    })
    const parsed = parseToolResult(result)

    expect(parsed['war_events']).toEqual([])
    expect(parsed['total_wars']).toBe(0)
  })

  // ── T2: Mars 45.3°, Venus 45.0° → 1 war with 0.3° orb ───────────────────

  it('T2 — Mars at 45.3°, Venus at 45.0° on 2026-06-15 → 1 war detected', async () => {
    const warPositions = [
      { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: 12.5, speed: 0.6 },
      { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 10.0, speed: 1.1 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(events.length).toBe(1)
    expect(events[0].date).toBe('2026-06-15')
  })

  it('T2 — War event has degree ≈ 0.3 (Mars 45.3 vs Venus 45.0)', async () => {
    const warPositions = [
      { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: 12.5, speed: 0.6 },
      { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 10.0, speed: 1.1 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(events.length).toBe(1)
    expect(events[0].degree).toBeCloseTo(0.3, 5)
  })

  it('T2 — War event reports planet_1 and planet_2', async () => {
    const warPositions = [
      { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: 12.5, speed: 0.6 },
      { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 10.0, speed: 1.1 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    const planets = [events[0].planet_1, events[0].planet_2].sort()
    expect(planets).toEqual(['Mars', 'Venus'])
  })

  // ── T3: Winner determined by higher declination ────────────────────────────

  it('T3 — Winner is the planet with higher absolute declination (Mars > Venus)', async () => {
    // Mars declination 12.5°, Venus 10.0° → Mars wins
    const warPositions = [
      { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: 12.5, speed: 0.6 },
      { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 10.0, speed: 1.1 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(events[0].winner).toBe('Mars')
    expect(events[0].loser).toBe('Venus')
  })

  it('T3 — Winner is the planet with higher declination (Venus > Mars)', async () => {
    // Venus declination 20.0°, Mars 8.0° → Venus wins
    const warPositions = [
      { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: 8.0, speed: 0.6 },
      { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 20.0, speed: 0.5 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(events[0].winner).toBe('Venus')
    expect(events[0].loser).toBe('Mars')
  })

  it('T3 — When declination unavailable, higher speed wins', async () => {
    // No declination; Mars speed=1.5, Venus speed=0.5 → Mars wins
    const warPositions = [
      { date: '2026-06-15', planet: 'Mars', longitude: 45.3, speed: 1.5 },
      { date: '2026-06-15', planet: 'Venus', longitude: 45.0, speed: 0.5 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(events[0].winner).toBe('Mars')
  })

  // ── T4: 360° wrap handling ─────────────────────────────────────────────────

  it('T4 — 360° wrap: planet at 359.0° and 0.5° → separation is 1.5°, NOT a war', async () => {
    // 359° and 0.5° → min(358.5, 1.5) = 1.5° > 1° → not a war
    const wrapPositions = [
      { date: '2026-07-01', planet: 'Mars', longitude: 359.0 },
      { date: '2026-07-01', planet: 'Venus', longitude: 0.5 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(wrapPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-07-01', to: '2026-07-31' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)

    expect(parsed['total_wars']).toBe(0)
  })

  it('T4 — 360° wrap: planet at 359.5° and 0.0° → separation is 0.5°, IS a war', async () => {
    // 359.5° and 0.0° → min(359.5, 0.5) = 0.5° ≤ 1° → war
    const wrapWarPositions = [
      { date: '2026-07-01', planet: 'Mars', longitude: 359.5, declination: 10.0 },
      { date: '2026-07-01', planet: 'Venus', longitude: 0.0, declination: 5.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(wrapWarPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-07-01', to: '2026-07-31' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(events.length).toBe(1)
    expect(events[0].degree).toBeCloseTo(0.5, 5)
  })

  it('T4 — 360° wrap: boundary exactly at 1° (359° and 0°) → detected as war', async () => {
    // 359° and 0° → |359-0|=359 → min(359, 1)=1° ≤ 1° → war
    const boundaryPositions = [
      { date: '2026-07-01', planet: 'Mars', longitude: 359.0, declination: 10.0 },
      { date: '2026-07-01', planet: 'Venus', longitude: 0.0, declination: 5.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(boundaryPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-07-01', to: '2026-07-31' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(events.length).toBe(1)
    expect(events[0].degree).toBeCloseTo(1.0, 5)
  })

  // ── T5: Planet filter ──────────────────────────────────────────────────────

  it('T5 — planets filter: only specified planets are checked', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope([]),
    )

    await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Mars', 'Venus'],
    })

    expect(vi.mocked(callPlatformPrimitive)).toHaveBeenCalledWith(
      'query_ephemeris',
      expect.objectContaining({
        planets: ['Mars', 'Venus'],
      }),
      expect.any(Object),
    )
  })

  it('T5 — planets_checked in response matches requested planets', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope([]),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Jupiter', 'Saturn'],
    })
    const parsed = parseToolResult(result)

    expect(parsed['planets_checked']).toEqual(['Jupiter', 'Saturn'])
  })

  // ── T6: classical_interpretation matches winner ────────────────────────────

  it('T6 — classical_interpretation is non-empty string', async () => {
    const warPositions = [
      { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: 12.5 },
      { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 10.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(typeof events[0].classical_interpretation).toBe('string')
    expect(events[0].classical_interpretation.length).toBeGreaterThan(0)
  })

  it('T6 — classical_interpretation mentions winner planet', async () => {
    const warPositions = [
      { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: 12.5 },
      { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 10.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-06-01', to: '2026-06-30' },
      planets: ['Mars', 'Venus'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]
    const winner = events[0].winner

    expect(events[0].classical_interpretation).toContain(winner)
  })

  it('T6 — Jupiter wins → interpretation mentions wisdom/dharma', async () => {
    const warPositions = [
      { date: '2026-08-01', planet: 'Jupiter', longitude: 90.5, declination: 22.0 },
      { date: '2026-08-01', planet: 'Saturn', longitude: 90.0, declination: 15.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-08-01', to: '2026-08-31' },
      planets: ['Jupiter', 'Saturn'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(events[0].winner).toBe('Jupiter')
    expect(events[0].classical_interpretation).toContain('wisdom')
  })

  it('T6 — Saturn wins → interpretation mentions delays/karma', async () => {
    const warPositions = [
      { date: '2026-08-01', planet: 'Jupiter', longitude: 90.5, declination: 10.0 },
      { date: '2026-08-01', planet: 'Saturn', longitude: 90.0, declination: 22.0 },
    ]

    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(
      buildEphemerisEnvelope(warPositions),
    )

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-08-01', to: '2026-08-31' },
      planets: ['Jupiter', 'Saturn'],
    })
    const parsed = parseToolResult(result)
    const events = parsed['war_events'] as WarEvent[]

    expect(events[0].winner).toBe('Saturn')
    expect(events[0].classical_interpretation).toContain('delays')
  })

  // ── Ephemeris error ────────────────────────────────────────────────────────

  it('Ephemeris error → tool returns isError result', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValueOnce(buildErrorEnvelope())

    const result = await callQueryPlanetWar({
      date_range: { from: '2026-01-01', to: '2026-12-31' },
    })

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // ── Unit: angularSep helper ────────────────────────────────────────────────

  it('Unit — angularSep(45.3, 45.0) = 0.3', () => {
    expect(angularSep(45.3, 45.0)).toBeCloseTo(0.3, 5)
  })

  it('Unit — angularSep(359.0, 0.5) = 1.5 (wrap)', () => {
    expect(angularSep(359.0, 0.5)).toBeCloseTo(1.5, 5)
  })

  it('Unit — angularSep(359.5, 0.0) = 0.5 (wrap)', () => {
    expect(angularSep(359.5, 0.0)).toBeCloseTo(0.5, 5)
  })

  it('Unit — angularSep(0, 180) = 180', () => {
    expect(angularSep(0, 180)).toBeCloseTo(180, 5)
  })

  it('Unit — angularSep(181, 0) = 179', () => {
    expect(angularSep(181, 0)).toBeCloseTo(179, 5)
  })

  // ── Unit: determineWinner helper ──────────────────────────────────────────

  it('Unit — determineWinner: higher declination wins', () => {
    const p1 = { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: 12.5 }
    const p2 = { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 8.0 }
    const { winner, loser } = determineWinner(p1, p2)
    expect(winner).toBe('Mars')
    expect(loser).toBe('Venus')
  })

  it('Unit — determineWinner: negative declination uses absolute value', () => {
    const p1 = { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: -15.0 }
    const p2 = { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 8.0 }
    const { winner } = determineWinner(p1, p2)
    expect(winner).toBe('Mars')  // |−15| > |8|
  })

  it('Unit — determineWinner: speed tiebreaker when dec equal', () => {
    const p1 = { date: '2026-06-15', planet: 'Mercury', longitude: 45.3, declination: 10.0, speed: 1.8 }
    const p2 = { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 10.0, speed: 0.9 }
    const { winner } = determineWinner(p1, p2)
    expect(winner).toBe('Mercury')
  })

  // ── Unit: buildWarInterpretation helper ───────────────────────────────────

  it('Unit — buildWarInterpretation(Mars, Venus) mentions aggression', () => {
    const interp = buildWarInterpretation('Mars', 'Venus')
    expect(interp).toContain('aggression')
  })

  it('Unit — buildWarInterpretation(Venus, Mars) mentions artistic', () => {
    const interp = buildWarInterpretation('Venus', 'Mars')
    expect(interp).toContain('artistic')
  })

  it('Unit — buildWarInterpretation(Saturn, Mercury) mentions delays', () => {
    const interp = buildWarInterpretation('Saturn', 'Mercury')
    expect(interp).toContain('delays')
  })

  it('Unit — buildWarInterpretation(Mercury, Saturn) mentions intellect', () => {
    const interp = buildWarInterpretation('Mercury', 'Saturn')
    expect(interp).toContain('intellect')
  })

  it('Unit — buildWarInterpretation(Jupiter, Mars) mentions wisdom', () => {
    const interp = buildWarInterpretation('Jupiter', 'Mars')
    expect(interp).toContain('wisdom')
  })

  // ── Unit: detectPlanetWars helper ─────────────────────────────────────────

  it('Unit — detectPlanetWars: Mars 45.3 vs Venus 45.0 → 1 event', () => {
    const byDate = new Map()
    byDate.set('2026-06-15', new Map([
      ['mars', { date: '2026-06-15', planet: 'Mars', longitude: 45.3, declination: 12.5 }],
      ['venus', { date: '2026-06-15', planet: 'Venus', longitude: 45.0, declination: 10.0 }],
    ]))

    const events = detectPlanetWars(byDate, ['Mars', 'Venus'])
    expect(events.length).toBe(1)
    expect(events[0].degree).toBeCloseTo(0.3, 5)
  })

  it('Unit — detectPlanetWars: planets 2° apart → no war', () => {
    const byDate = new Map()
    byDate.set('2026-06-15', new Map([
      ['mars', { date: '2026-06-15', planet: 'Mars', longitude: 47.0 }],
      ['venus', { date: '2026-06-15', planet: 'Venus', longitude: 45.0 }],
    ]))

    const events = detectPlanetWars(byDate, ['Mars', 'Venus'])
    expect(events.length).toBe(0)
  })

  it('Unit — detectPlanetWars: wrap 359.5 vs 0.0 → war detected', () => {
    const byDate = new Map()
    byDate.set('2026-07-01', new Map([
      ['mars', { date: '2026-07-01', planet: 'Mars', longitude: 359.5, declination: 10.0 }],
      ['venus', { date: '2026-07-01', planet: 'Venus', longitude: 0.0, declination: 5.0 }],
    ]))

    const events = detectPlanetWars(byDate, ['Mars', 'Venus'])
    expect(events.length).toBe(1)
    expect(events[0].degree).toBeCloseTo(0.5, 5)
  })
})
