/**
 * mimamsa_lel_intake.test.ts — BRAHMA-MI-5-1: mimamsa.lel_intake MCP tool tests
 *
 * Tests the lel_query MCP tool registration and response structure.
 * No live sidecar required — fetch is mocked.
 *
 * Contract assertions:
 *   - registerMimamsaLelIntakeTool registers tool named 'lel_query'
 *   - lel_query returns events array with provenance_envelope
 *   - provenance_envelope has source = 'mimamsa.lel_intake', asset = 'MI-5-1'
 *   - provenance_envelope has no_leakage_note and b3_compliant = true
 *   - all source_citations are non-empty (B.3 mandate)
 *   - convergence_score values in [0.0, 1.0] range when non-null
 *   - error path returns isError: true with provenance_envelope
 *
 * BRAHMA-MI-5-1
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── Mock fetch before importing module ────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Import after mock ─────────────────────────────────────────────────────────

import {
  registerMimamsaLelIntakeTool,
  type LelEvent,
  type LelQueryResult,
  type LelProvenanceEnvelope,
} from '../tools/mimamsa_lel_intake.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'

// ── Constants ─────────────────────────────────────────────────────────────────

const SOURCE_CITATION = 'LIFE_EVENT_LOG_v1_2.md (native-disclosed)'

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Build a minimal LelEvent fixture. */
function makeEvent(overrides: Partial<LelEvent> = {}): LelEvent {
  return {
    event_id: '550e8400-e29b-41d4-a716-446655440000',
    event_date: '2023-07-15',
    event_type: 'career',
    description: 'Founded Marsys Group (July 2023).',
    domain: 'career/entrepreneurship_founded',
    outcome_observed: 'yes',
    dasha_active: 'Mercury',
    antardasha_active: 'Jupiter',
    key_transits: ['Saturn transit Aquarius = 11H from Lagna'],
    convergence_score: 1.0,
    source_citation: SOURCE_CITATION,
    ...overrides,
  }
}

/** Build a minimal provenance envelope fixture. */
function makeProvenanceEnvelope(overrides: Partial<LelProvenanceEnvelope> = {}): LelProvenanceEnvelope {
  return {
    source: 'mimamsa.lel_intake',
    asset: 'MI-5-1',
    lel_version: 'LIFE_EVENT_LOG_v1_2.md v1.7',
    total_events: 57,
    confidence: 0.89,
    source_citation: SOURCE_CITATION,
    no_leakage_note: 'life_events is calibration corpus only — must not feed prediction generation',
    b3_compliant: true,
    queried_at: '2026-06-04T00:00:00.000Z',
    ...overrides,
  }
}

/** Build a full LelQueryResult fixture. */
function makeLelQueryResult(
  events: LelEvent[] = [makeEvent()],
  totalCount = 57,
): LelQueryResult {
  return {
    ok: true,
    events,
    total_count: totalCount,
    filter_applied: {
      domain: null,
      date_from: null,
      date_to: null,
      limit: 100,
    },
    provenance_envelope: makeProvenanceEnvelope(),
  }
}

/** Mock fetch to return a successful sidecar response. */
function mockSuccessfulFetch(result: LelQueryResult): void {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => result,
    text: async () => '',
    status: 200,
  })
}

/** Mock fetch to return a sidecar error. */
function mockFailedFetch(status = 500, message = 'Internal Server Error'): void {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status,
    text: async () => message,
    json: async () => ({ error: message }),
  })
}

/** Capture registered tools from McpServer mock. */
function makeMockServer(): { server: McpServer; toolRegistry: Map<string, unknown> } {
  const toolRegistry = new Map<string, unknown>()
  const server = {
    tool: vi.fn((name: string, _description: string, _schema: unknown, handler: unknown) => {
      toolRegistry.set(name, handler)
    }),
  } as unknown as McpServer
  return { server, toolRegistry }
}

/** Invoke a registered tool handler with given params. */
async function invokeTool(
  toolRegistry: Map<string, unknown>,
  toolName: string,
  params: Record<string, unknown> = {}
): Promise<{ content: { type: string; text: string }[]; isError?: boolean }> {
  const handler = toolRegistry.get(toolName) as (
    params: Record<string, unknown>
  ) => Promise<{ content: { type: string; text: string }[]; isError?: boolean }>
  if (!handler) throw new Error(`Tool '${toolName}' not registered`)
  return handler(params)
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('mimamsa.lel_intake — tool registration', () => {
  it('registers tool named lel_query', () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    expect(toolRegistry.has('lel_query')).toBe(true)
  })

  it('server.tool is called exactly once', () => {
    const { server } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    expect((server.tool as ReturnType<typeof vi.fn>).mock.calls.length).toBe(1)
  })

  it('tool name matches contract: lel_query', () => {
    const { server } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    const call = (server.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(call[0]).toBe('lel_query')
  })
})

describe('mimamsa.lel_intake — lel_query success path', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('returns events array from sidecar response', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult([makeEvent(), makeEvent()]))

    const response = await invokeTool(toolRegistry, 'lel_query', {})
    const parsed = JSON.parse(response.content[0].text)

    expect(Array.isArray(parsed.events)).toBe(true)
    expect(parsed.events.length).toBe(2)
  })

  it('returns provenance_envelope with correct source', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.provenance_envelope.source).toBe('mimamsa.lel_intake')
  })

  it('returns provenance_envelope with correct asset MI-5-1', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.provenance_envelope.asset).toBe('MI-5-1')
  })

  it('returns provenance_envelope with total_events = 57', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.provenance_envelope.total_events).toBe(57)
  })

  it('returns provenance_envelope with b3_compliant = true', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.provenance_envelope.b3_compliant).toBe(true)
  })

  it('returns provenance_envelope with no_leakage_note containing "calibration"', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.provenance_envelope.no_leakage_note).toContain('calibration')
  })

  it('all events have non-empty source_citation', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    const events = [
      makeEvent({ source_citation: SOURCE_CITATION }),
      makeEvent({ source_citation: SOURCE_CITATION, event_type: 'health' }),
    ]
    mockSuccessfulFetch(makeLelQueryResult(events))

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    for (const event of parsed.events as LelEvent[]) {
      expect(event.source_citation).toBeTruthy()
      expect(event.source_citation.length).toBeGreaterThan(0)
    }
  })

  it('convergence_score values are in [0.0, 1.0] when non-null', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    const events = [
      makeEvent({ convergence_score: 1.0 }),
      makeEvent({ convergence_score: 0.5 }),
      makeEvent({ convergence_score: 0.0 }),
      makeEvent({ convergence_score: null }),
    ]
    mockSuccessfulFetch(makeLelQueryResult(events, 4))

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    for (const event of parsed.events as LelEvent[]) {
      if (event.convergence_score !== null && event.convergence_score !== undefined) {
        expect(event.convergence_score).toBeGreaterThanOrEqual(0.0)
        expect(event.convergence_score).toBeLessThanOrEqual(1.0)
      }
    }
  })

  it('total_count is included in response', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult([makeEvent()], 57))

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(typeof parsed.total_count).toBe('number')
    expect(parsed.total_count).toBeGreaterThan(0)
  })

  it('filter_applied is included in response', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    const response = await invokeTool(toolRegistry, 'lel_query', { domain: 'career' })
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.filter_applied).toBeDefined()
  })

  it('ok = true on success', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.ok).toBe(true)
  })

  it('calls sidecar with correct path /brahma/mimamsa/lel_query', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    await invokeTool(toolRegistry, 'lel_query', { domain: 'career', limit: 10 })

    const calledUrl: string = mockFetch.mock.calls[0][0]
    expect(calledUrl).toContain('/brahma/mimamsa/lel_query')
  })

  it('sends domain parameter in request body', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    await invokeTool(toolRegistry, 'lel_query', { domain: 'spiritual', limit: 50 })

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string)
    expect(body.domain).toBe('spiritual')
    expect(body.limit).toBe(50)
  })
})

describe('mimamsa.lel_intake — lel_query error path', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('returns isError: true on sidecar HTTP error', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockFailedFetch(500, 'Internal Server Error')

    const response = await invokeTool(toolRegistry, 'lel_query')

    expect(response.isError).toBe(true)
  })

  it('error response contains provenance_envelope', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockFailedFetch(503, 'Service Unavailable')

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.provenance_envelope).toBeDefined()
    expect(parsed.provenance_envelope.source).toBe('mimamsa.lel_intake')
    expect(parsed.provenance_envelope.asset).toBe('MI-5-1')
  })

  it('error response contains ok: false', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockFailedFetch()

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.ok).toBe(false)
  })

  it('error response preserves no_leakage_note', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockFailedFetch()

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.provenance_envelope.no_leakage_note).toContain('calibration')
  })

  it('error response preserves b3_compliant = true', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockFailedFetch()

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.provenance_envelope.b3_compliant).toBe(true)
  })

  it('error response preserves total_events = 57', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockFailedFetch()

    const response = await invokeTool(toolRegistry, 'lel_query')
    const parsed = JSON.parse(response.content[0].text)

    expect(parsed.provenance_envelope.total_events).toBe(57)
  })
})

describe('mimamsa.lel_intake — domain filtering', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('sends null domain when no domain filter provided', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    await invokeTool(toolRegistry, 'lel_query', {})

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string)
    expect(body.domain).toBeNull()
  })

  it('sends date_from null when not provided', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    await invokeTool(toolRegistry, 'lel_query', { domain: 'career' })

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string)
    expect(body.date_from).toBeNull()
    expect(body.date_to).toBeNull()
  })

  it('sends date_from and date_to when provided', async () => {
    const { server, toolRegistry } = makeMockServer()
    registerMimamsaLelIntakeTool(server)
    mockSuccessfulFetch(makeLelQueryResult())

    await invokeTool(toolRegistry, 'lel_query', {
      date_from: '2020-01-01',
      date_to: '2026-12-31',
    })

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string)
    expect(body.date_from).toBe('2020-01-01')
    expect(body.date_to).toBe('2026-12-31')
  })
})
