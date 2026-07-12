/**
 * mimamsa_lel_intake.test.ts — BRAHMA-MI-5-1: mimamsa.lel_intake MCP tool (`lel_query`)
 *
 * Rewritten for the KEYSTONE (M6+M7) contract: the tool now delegates to
 * callPlatformPrimitive('lel_query', ...) → /api/mcp/primitives/lel_query, which wraps
 * the L5 capability payload in the standard MCP envelope AND the legacy ToolBundle shape:
 *
 *   { status, envelope: { ok, result: { results: [{ content: "<JSON payload>" }] } } }
 *
 * where the JSON payload (query_life_events.ts) is
 *   { chart_id, events, count, total_matching, filters, provenance }.
 *
 * DEPLOYED DEFECT under test (WP-1.3d / lel_query-deployed-fix / F-L10-021):
 *   The tool previously read envelope.result.events / .total_count — two levels too
 *   shallow and the wrong count key (total_matching) — so it returned a dishonest
 *   { ok:true, events:[], total_count:0 } even though the native has 57 rows, while the
 *   twin `mimamsa_lel_query` (raw envelope pass-through) showed the data. These tests
 *   assert the tool now serves the real 57 for the native and an HONEST empty (ok:true,
 *   events:[], total_count:0) for a chart that genuinely has zero events.
 *
 * BRAHMA-MI-5-1
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock the platform primitive client + authz BEFORE importing the module ─────

const mockCallPlatformPrimitive = vi.fn()
const mockRemoteAuthorize = vi.fn()

vi.mock('../client.js', () => ({
  callPlatformPrimitive: (...args: unknown[]) => mockCallPlatformPrimitive(...args),
}))
vi.mock('../lib/authz.js', () => ({
  remoteAuthorize: (...args: unknown[]) => mockRemoteAuthorize(...args),
}))

// ── Import after mock ─────────────────────────────────────────────────────────

import {
  registerMimamsaLelIntakeTool,
  type LelEvent,
} from '../tools/mimamsa_lel_intake.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Constants / fixtures ────────────────────────────────────────────────────────

const NATIVE_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const SOURCE_CITATION = 'LIFE_EVENT_LOG_v1_2.md (native-disclosed)'

const PRINCIPAL: Principal = { user_uid: 'u-test', key_id: 'k-test', role: 'super_admin' }

function makeEvent(overrides: Partial<LelEvent> = {}): Partial<LelEvent> & Record<string, unknown> {
  return {
    event_id: '550e8400-e29b-41d4-a716-446655440000',
    event_date: '2023-07-15',
    event_type: 'career',
    description: 'Founded Marsys Group (July 2023).',
    domain: 'career/entrepreneurship_founded',
    category: 'career',
    significance: 'major',
    source_citation: SOURCE_CITATION,
    outcome_observed: 'yes',
    ...overrides,
  }
}

/** The L5 capability payload shape (query_life_events.ts handler `content`). */
function makeCapabilityPayload(chartId: string, events: unknown[], totalMatching: number) {
  return {
    chart_id: chartId,
    events,
    count: events.length,
    total_matching: totalMatching,
    filters: { category: null, domain: null, significance: null, start_date: null, end_date: null, limit: 50 },
    provenance: {
      tables: ['life_events'],
      no_leakage_note: 'life_events is a calibration corpus only — must not feed prediction generation.',
      source: 'LIFE_EVENT_LOG (user-authored); served chart-scoped.',
    },
  }
}

/** Wrap a capability payload the way /api/mcp/primitives/[tool] actually does. */
function mockPrimitiveSuccess(chartId: string, events: unknown[], totalMatching: number): void {
  const payload = makeCapabilityPayload(chartId, events, totalMatching)
  mockCallPlatformPrimitive.mockResolvedValueOnce({
    status: 200,
    envelope: {
      ok: true,
      result: {
        tool_bundle_id: 'tb-1',
        tool_name: 'query_life_events',
        results: [{ content: JSON.stringify(payload) }],
      },
    },
  })
}

function mockPrimitiveError(status = 500, message = 'boom'): void {
  mockCallPlatformPrimitive.mockResolvedValueOnce({
    status,
    envelope: { ok: false, error: { class: 'internal', message } },
  })
}

function makeMockServer(): { server: McpServer; toolRegistry: Map<string, unknown> } {
  const toolRegistry = new Map<string, unknown>()
  const server = {
    tool: vi.fn((name: string, _d: string, _s: unknown, handler: unknown) => {
      toolRegistry.set(name, handler)
    }),
  } as unknown as McpServer
  return { server, toolRegistry }
}

async function invokeTool(
  toolRegistry: Map<string, unknown>,
  params: Record<string, unknown>,
): Promise<{ content: { type: string; text: string }[]; isError?: boolean }> {
  const handler = toolRegistry.get('lel_query') as (
    p: Record<string, unknown>,
  ) => Promise<{ content: { type: string; text: string }[]; isError?: boolean }>
  if (!handler) throw new Error('Tool lel_query not registered')
  return handler(params)
}

function register() {
  const { server, toolRegistry } = makeMockServer()
  registerMimamsaLelIntakeTool(server, PRINCIPAL)
  return toolRegistry
}

// ── Tests ──────────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockCallPlatformPrimitive.mockReset()
  mockRemoteAuthorize.mockReset()
  mockRemoteAuthorize.mockResolvedValue(true)
})

describe('lel_query — registration', () => {
  it('registers a tool named lel_query', () => {
    const reg = register()
    expect(reg.has('lel_query')).toBe(true)
  })
})

describe('lel_query — native chart (57 rows): the deployed defect', () => {
  it('serves the real events (NOT dishonest-empty)', async () => {
    const reg = register()
    // Capability caps the page at 50 but reports the full family via total_matching.
    const page = Array.from({ length: 50 }, () => makeEvent())
    mockPrimitiveSuccess(NATIVE_CHART, page, 57)

    const res = await invokeTool(reg, { chart_id: NATIVE_CHART })
    const parsed = JSON.parse(res.content[0].text)

    expect(res.isError).toBeUndefined()
    expect(parsed.ok).toBe(true)
    expect(Array.isArray(parsed.events)).toBe(true)
    expect(parsed.events.length).toBe(50)
    // Honest total reflects the full family, not the page length.
    expect(parsed.total_count).toBe(57)
  })

  it('envelope is honest: total_events matches the served total_count', async () => {
    const reg = register()
    mockPrimitiveSuccess(NATIVE_CHART, [makeEvent()], 57)

    const res = await invokeTool(reg, { chart_id: NATIVE_CHART })
    const parsed = JSON.parse(res.content[0].text)

    expect(parsed.provenance_envelope.total_events).toBe(57)
    expect(parsed.provenance_envelope.source).toBe('mimamsa.lel_intake')
    expect(parsed.provenance_envelope.asset).toBe('MI-5-1')
    expect(parsed.provenance_envelope.b3_compliant).toBe(true)
  })
})

describe('lel_query — genuine zero (Abhinandan): honest-empty is allowed', () => {
  it('returns ok:true with an empty events list and total_count 0', async () => {
    const reg = register()
    mockPrimitiveSuccess(ABHINANDAN_CHART, [], 0)

    const res = await invokeTool(reg, { chart_id: ABHINANDAN_CHART })
    const parsed = JSON.parse(res.content[0].text)

    expect(res.isError).toBeUndefined()
    expect(parsed.ok).toBe(true)
    expect(parsed.events).toEqual([])
    expect(parsed.total_count).toBe(0)
  })
})

describe('lel_query — param mapping', () => {
  it('maps date_from/date_to onto the capability start_date/end_date', async () => {
    const reg = register()
    mockPrimitiveSuccess(NATIVE_CHART, [makeEvent()], 1)

    await invokeTool(reg, {
      chart_id: NATIVE_CHART,
      date_from: '2020-01-01',
      date_to: '2026-12-31',
      domain: 'career',
    })

    const [toolName, args] = mockCallPlatformPrimitive.mock.calls[0]
    expect(toolName).toBe('lel_query')
    expect(args.start_date).toBe('2020-01-01')
    expect(args.end_date).toBe('2026-12-31')
    expect(args.domain).toBe('career')
    expect(args.chart_id).toBe(NATIVE_CHART)
  })
})

describe('lel_query — honesty gate (unparseable payload is NOT laundered to empty)', () => {
  it('surfaces an error when the envelope has no parseable LEL payload', async () => {
    const reg = register()
    mockCallPlatformPrimitive.mockResolvedValueOnce({
      status: 200,
      envelope: { ok: true, result: { tool_bundle_id: 'tb', results: [] } },
    })

    const res = await invokeTool(reg, { chart_id: NATIVE_CHART })
    const parsed = JSON.parse(res.content[0].text)

    expect(res.isError).toBe(true)
    expect(parsed.ok).toBe(false)
  })
})

describe('lel_query — guards + error path', () => {
  it('rejects a missing chart_id', async () => {
    const reg = register()
    const res = await invokeTool(reg, {})
    const parsed = JSON.parse(res.content[0].text)
    expect(res.isError).toBe(true)
    expect(parsed.error).toContain('chart_id')
    expect(mockCallPlatformPrimitive).not.toHaveBeenCalled()
  })

  it('denies when not authorized for the chart', async () => {
    const reg = register()
    mockRemoteAuthorize.mockResolvedValueOnce(false)
    const res = await invokeTool(reg, { chart_id: NATIVE_CHART })
    expect(res.isError).toBe(true)
    expect(mockCallPlatformPrimitive).not.toHaveBeenCalled()
  })

  it('returns isError with provenance_envelope on a primitive error', async () => {
    const reg = register()
    mockPrimitiveError(500, 'db down')
    const res = await invokeTool(reg, { chart_id: NATIVE_CHART })
    const parsed = JSON.parse(res.content[0].text)
    expect(res.isError).toBe(true)
    expect(parsed.ok).toBe(false)
    expect(parsed.provenance_envelope.asset).toBe('MI-5-1')
    expect(parsed.provenance_envelope.no_leakage_note).toContain('calibration')
  })
})
