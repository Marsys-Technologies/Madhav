/**
 * query_transit_event.test.ts — Regression tests for the query_transit_event MCP tool.
 *
 * Tests the event_type schema fix (C6 bug):
 *   The MCP input schema did not expose event_type, so callers couldn't send it
 *   and the engine received undefined — triggering "Unknown event_type undefined".
 *   Fix: event_type is now a required enum in the Zod schema.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryTransitEvent } from './query_transit_event.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildTransitEventEnvelope(events: unknown[]) {
  // The engine returns a ToolBundle; results is an array of ToolBundleResult
  const toolBundle = {
    tool_bundle_id: 'transit-bundle-id',
    tool_name: 'query_transit_event',
    tool_version: '1.0.0',
    invocation_params: {},
    results: events.map(e => ({
      content: JSON.stringify(e),
      source_canonical_id: 'EPHEMERIS_DAILY',
      source_version: '1.0',
      confidence: 1.0,
      significance: 0.9,
    })),
    served_from_cache: false,
    latency_ms: 12,
    result_hash: 'sha256:transit-test',
    schema_version: '1.0',
  }

  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-transit-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: toolBundle,
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
 * Extract and call the registered handler from the stub server.
 * Returns the raw MCP tool result.
 */
async function callQueryTransitEvent(
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

  registerQueryTransitEvent(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_transit_event handler was not registered')

  // Simulate Zod validation (as MCP SDK would do it)
  // Build a schema object from the registered shape and validate
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)

  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    // Return the ZodError so tests can assert on it
    return { zodError: parseResult.error, isZodError: true }
  }

  // If Zod passes, call the handler with validated data
  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_transit_event — event_type schema fix (C6)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.4: calling without event_type must return a Zod validation error
  it('AC.4 — calling without event_type produces a Zod validation error, not "Unknown event_type undefined"', async () => {
    const result = await callQueryTransitEvent({
      planet: 'Saturn',
      target: 'Aquarius',
      date_range: { start: '2024-01-01', end: '2025-12-31' },
      // event_type deliberately omitted
    })

    expect((result as { isZodError: boolean }).isZodError).toBe(true)
    const zodError = (result as { zodError: z.ZodError }).zodError
    expect(zodError).toBeDefined()

    // The error must mention event_type (required field missing)
    const issues = zodError.issues
    const hasEventTypeIssue = issues.some(
      (issue) => issue.path.includes('event_type') || issue.message.toLowerCase().includes('required')
    )
    expect(hasEventTypeIssue).toBe(true)
  })

  it('rejects invalid event_type values with a Zod enum error', async () => {
    const result = await callQueryTransitEvent({
      event_type: 'station_retrograde',  // not in the enum; engine uses 'station'
      planet: 'Saturn',
      date_range: { start: '2024-01-01', end: '2025-12-31' },
    })

    expect((result as { isZodError: boolean }).isZodError).toBe(true)
    const zodError = (result as { zodError: z.ZodError }).zodError
    const issues = zodError.issues
    // Zod v4 uses 'invalid_value' for enum failures; Zod v3 uses 'invalid_enum_value'.
    const hasEnumIssue = issues.some(
      (issue) => issue.code === 'invalid_value' || issue.code === 'invalid_enum_value'
    )
    expect(hasEnumIssue).toBe(true)
  })

  // AC.4 (second half): calling with a valid event_type reaches the engine
  it('calling with valid event_type=ingress reaches callPlatformPrimitive', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(
      buildTransitEventEnvelope([
        { event_type: 'ingress', date: '2025-03-29', planet: 'saturn', sign: 'Aquarius' },
      ])
    )

    const result = await callQueryTransitEvent({
      event_type: 'ingress',
      planet: 'Saturn',
      target: 'Aquarius',
      date_range: { start: '2024-01-01', end: '2026-12-31' },
    })

    // Should not be a Zod error
    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()

    // callPlatformPrimitive must have been called with event_type forwarded
    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCallPlatformPrimitive.mock.calls[0]
    expect(toolName).toBe('query_transit_event')
    expect((params as Record<string, unknown>)['event_type']).toBe('ingress')
  })

  it('forwards event_type=station to the engine correctly', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(
      buildTransitEventEnvelope([
        { event_type: 'station', planet: 'saturn', retrograde_start: '2024-06-29' },
      ])
    )

    await callQueryTransitEvent({
      event_type: 'station',
      planet: 'Saturn',
      date_range: { start: '2024-01-01', end: '2024-12-31' },
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['event_type']).toBe('station')
    expect(params['planet']).toBe('Saturn')
  })

  it('forwards event_type=conjunction with planet_a and planet_b', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildTransitEventEnvelope([]))

    await callQueryTransitEvent({
      event_type: 'conjunction',
      planet_a: 'Jupiter',
      planet_b: 'Saturn',
      date_range: { start: '2024-01-01', end: '2026-12-31' },
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['event_type']).toBe('conjunction')
    expect(params['planet_a']).toBe('Jupiter')
    expect(params['planet_b']).toBe('Saturn')
  })

  it('maps date_range.start/end to start_date/end_date for the engine', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildTransitEventEnvelope([]))

    await callQueryTransitEvent({
      event_type: 'ingress',
      planet: 'Jupiter',
      date_range: { start: '2025-01-01', end: '2025-12-31' },
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['start_date']).toBe('2025-01-01')
    expect(params['end_date']).toBe('2025-12-31')
    // date_range object itself should NOT be passed to engine (it uses flat start_date/end_date)
    expect(params['date_range']).toBeUndefined()
  })

  it('returns error when primitive call fails', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue({
      status: 500,
      envelope: {
        ok: false,
        trace_id: 'fail-001',
        error: { class: 'internal', message: 'DB error' },
      },
    })

    const result = await callQueryTransitEvent({
      event_type: 'ingress',
      planet: 'Mars',
      date_range: { start: '2025-01-01', end: '2025-12-31' },
    })

    expect((result as { isError?: boolean }).isError).toBe(true)
  })
})
