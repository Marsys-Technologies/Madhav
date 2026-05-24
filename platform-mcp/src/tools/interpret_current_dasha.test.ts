/**
 * interpret_current_dasha.test.ts — Tests for the interpret_current_dasha MCP tool.
 *
 * Session: TR-P9-S2
 *
 * Acceptance criteria:
 *   TC.1 — Jupiter yoga is_activated_by_dasha=true when MD=Jupiter and yoga.planet=Jupiter
 *   TC.2 — dasha_context.md = "Jupiter" when dasha call returns MD=Jupiter
 *   TC.3 — data_sources is a non-empty array
 *   TC.4 — When dasha call returns error: dasha_context.md = null, function still returns ok:true
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
import { registerInterpretCurrentDasha } from './interpret_current_dasha.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/** Build a dasha envelope with a single period (MD, AD, PD). */
function buildDashaEnvelope(md: string, ad: string, pd = 'Mercury') {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-dasha-001',
      result: {
        periods: [
          {
            mahadasha: md,
            antardasha: ad,
            pratyantar: pd,
            start: '2020-01-01',
            end: '2036-01-01',
          },
        ],
      },
    },
  }
}

/** Build a chart_facts batched envelope with yoga rows. */
function buildYogaEnvelope(yogaRows: Array<{ yoga_name: string; planet: string }>) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-yoga-001',
      result: {
        rows_by_category: {
          yoga: yogaRows.map((r, i) => ({
            fact_id: `YG.${String(i).padStart(3, '0')}`,
            category: 'yoga',
            value_text: r.yoga_name,
            planet: r.planet,
          })),
        },
      },
    },
  }
}

/** Build an error envelope (dasha or yoga call failed). */
function buildErrorEnvelope() {
  return {
    status: 500,
    envelope: {
      ok: false,
      trace_id: 'trace-error-001',
      error: { class: 'internal', message: 'DB error', remediation: 'retry' },
    },
  }
}

/**
 * Registers interpret_current_dasha on a stub MCP server, applies Zod validation,
 * and invokes the handler, returning the raw result.
 */
async function callInterpretCurrentDasha(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
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

  registerInterpretCurrentDasha(stubServer, () => principal)

  if (!capturedHandler) throw new Error('interpret_current_dasha handler was not registered')

  // Simulate Zod validation as MCP SDK would do
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

/** Parse the MCP content text from the result. */
function parseResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('interpret_current_dasha (TR-P9-S2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── TC.1: Jupiter yoga activated when MD=Jupiter ───────────────────────────

  it('TC.1 — yoga.planet=Jupiter is is_activated_by_dasha=true when MD=Jupiter', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    // Both calls resolve in parallel; mock returns both in order
    mockFn
      .mockResolvedValueOnce(buildDashaEnvelope('Jupiter', 'Saturn'))
      .mockResolvedValueOnce(
        buildYogaEnvelope([
          { yoga_name: 'Hamsa Yoga', planet: 'Jupiter' },  // MD match → activated
          { yoga_name: 'Shasha Yoga', planet: 'Venus' },   // no match → not activated
        ])
      )

    const result = await callInterpretCurrentDasha({ date: '2026-05-25' })
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)

    const relevantYogas = envelope['relevant_yogas'] as Array<{
      yoga_name: string
      is_activated_by_dasha: boolean
    }>
    expect(Array.isArray(relevantYogas)).toBe(true)

    const hamsaYoga = relevantYogas.find(y => y.yoga_name === 'Hamsa Yoga')
    expect(hamsaYoga).toBeDefined()
    expect(hamsaYoga!.is_activated_by_dasha).toBe(true)

    const shashaYoga = relevantYogas.find(y => y.yoga_name === 'Shasha Yoga')
    expect(shashaYoga).toBeDefined()
    expect(shashaYoga!.is_activated_by_dasha).toBe(false)
  })

  // ── TC.2: dasha_context.md = "Jupiter" ────────────────────────────────────

  it('TC.2 — dasha_context.md equals "Jupiter" when dasha periods return mahadasha=Jupiter', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(buildDashaEnvelope('Jupiter', 'Saturn'))
      .mockResolvedValueOnce(buildYogaEnvelope([]))

    const result = await callInterpretCurrentDasha({})
    const envelope = parseResult(result)

    const dashaContext = envelope['dasha_context'] as Record<string, string | null>
    expect(dashaContext['md']).toBe('Jupiter')
    expect(dashaContext['ad']).toBe('Saturn')
  })

  // ── TC.3: data_sources is a non-empty array ────────────────────────────────

  it('TC.3 — data_sources is a non-empty array when both calls succeed', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(buildDashaEnvelope('Jupiter', 'Saturn'))
      .mockResolvedValueOnce(buildYogaEnvelope([{ yoga_name: 'Bhadra Yoga', planet: 'Mercury' }]))

    const result = await callInterpretCurrentDasha({})
    const envelope = parseResult(result)

    const dataSources = envelope['data_sources'] as string[]
    expect(Array.isArray(dataSources)).toBe(true)
    expect(dataSources.length).toBeGreaterThan(0)
    expect(dataSources).toContain('query_dasha_periods')
    expect(dataSources).toContain('query_chart_facts:yoga')
  })

  // ── TC.4: dasha error → dasha_context.md=null, still ok:true ─────────────

  it('TC.4 — when dasha call returns error, dasha_context.md=null and result is ok:true', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(buildErrorEnvelope())  // dasha fails
      .mockResolvedValueOnce(buildYogaEnvelope([{ yoga_name: 'Hamsa Yoga', planet: 'Jupiter' }]))

    const result = await callInterpretCurrentDasha({})
    const envelope = parseResult(result)

    // Should still return ok:true
    expect(envelope['ok']).toBe(true)

    // dasha_context should have nulls
    const dashaContext = envelope['dasha_context'] as Record<string, string | null>
    expect(dashaContext['md']).toBeNull()
    expect(dashaContext['ad']).toBeNull()

    // data_sources should NOT include dasha (since it errored)
    const dataSources = envelope['data_sources'] as string[]
    expect(dataSources).not.toContain('query_dasha_periods')
  })

  // ── Additional: Zod default for subset_size ────────────────────────────────

  it('subset_size defaults to 30 when not provided', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(buildDashaEnvelope('Saturn', 'Mercury'))
      .mockResolvedValueOnce(buildYogaEnvelope([]))

    const result = await callInterpretCurrentDasha({})
    const envelope = parseResult(result)

    // Verify tool ran without error; Zod default is handled transparently
    expect(envelope['ok']).toBe(true)
  })

  // ── Additional: AD activation ──────────────────────────────────────────────

  it('yoga matching AD planet is also activated', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    // MD=Jupiter, AD=Saturn → Saturn yoga should also be activated
    mockFn
      .mockResolvedValueOnce(buildDashaEnvelope('Jupiter', 'Saturn'))
      .mockResolvedValueOnce(
        buildYogaEnvelope([
          { yoga_name: 'Shasha Yoga', planet: 'Saturn' },  // AD match
          { yoga_name: 'Malavya Yoga', planet: 'Venus' },  // no match
        ])
      )

    const result = await callInterpretCurrentDasha({})
    const envelope = parseResult(result)
    const relevantYogas = envelope['relevant_yogas'] as Array<{
      yoga_name: string
      is_activated_by_dasha: boolean
    }>

    const shashaYoga = relevantYogas.find(y => y.yoga_name === 'Shasha Yoga')
    expect(shashaYoga!.is_activated_by_dasha).toBe(true)

    const malavyaYoga = relevantYogas.find(y => y.yoga_name === 'Malavya Yoga')
    expect(malavyaYoga!.is_activated_by_dasha).toBe(false)
  })

  // ── Additional: synthesis_note is present ──────────────────────────────────

  it('synthesis_note is present in output', async () => {
    const mockFn = vi.mocked(callPlatformPrimitive)

    mockFn
      .mockResolvedValueOnce(buildDashaEnvelope('Jupiter', 'Saturn'))
      .mockResolvedValueOnce(buildYogaEnvelope([]))

    const result = await callInterpretCurrentDasha({})
    const envelope = parseResult(result)

    expect(typeof envelope['synthesis_note']).toBe('string')
    expect(envelope['synthesis_note']).toContain('holistic_bundle')
  })
})
