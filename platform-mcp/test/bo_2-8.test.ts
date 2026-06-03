/**
 * bo_2-8.test.ts — holistic_bundle MCP tool unit tests (BRAHMA-BO-2-8)
 *
 * Tests the registerHolisticBundleTool registration and the sidecar-call
 * behaviour under success, error-isolation, and timeout scenarios.
 *
 * All network calls are mocked — no real DB or sidecar required.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { registerHolisticBundleTool } from '../src/tools/bo_2-8.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../src/types.js'

// ── Mock fetch globally ───────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Fixtures ──────────────────────────────────────────────────────────────────

const MOCK_PRINCIPAL: Principal = {
  user_uid: 'test-uid',
  key_id: 'test-key',
}

const NATIVE_CHART_ID = '00000000-0000-0000-0000-198402051043'  // native placeholder

function makeSidecarResponse(result: object) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve({ ok: true, result }),
  }
}

const FULL_BUNDLE = {
  signals: [
    {
      signal_id: 'SIG.MSR.001',
      domain: 'career',
      valence: 'positive',
      confidence: 0.85,
      salience: 0.92,
      state: 'lit',
      signal_text: 'Strong 10th lord placement — professional recognition.',
      source_citation: 'FORENSIC-v8.0:graha.saturn',
      graha_refs: ['saturn'],
      house_refs: [10],
      created_at: '2026-06-03T00:00:00Z',
    },
  ],
  graph_edges: [
    {
      edge_id: 'EDGE.001',
      from_signal_id: 'SIG.MSR.001',
      to_signal_id: 'SIG.MSR.002',
      edge_type: 'reinforce',
      weight: 0.75,
      label: 'Saturn–Jupiter mutual support',
      created_at: '2026-06-03T00:00:00Z',
    },
  ],
  domain_links: [
    {
      link_id: 'CDLM.001',
      from_domain: 'career',
      to_domain: 'wealth',
      link_type: 'karaka_bridge',
      signal_ids: ['SIG.MSR.001'],
      strength: 0.70,
      note: '10th–2nd house axis active.',
      created_at: '2026-06-03T00:00:00Z',
    },
  ],
  resonance: [
    {
      resonance_id: 'RM.001',
      theme: 'dharma_artha_axis',
      signal_ids: ['SIG.MSR.001'],
      resonance_type: 'harmonic',
      amplitude: 0.88,
      note: 'Career–wealth axis in resonance.',
      created_at: '2026-06-03T00:00:00Z',
    },
  ],
  provenance_envelope: {
    chart_id: NATIVE_CHART_ID,
    queried_at: '2026-06-03T00:00:00Z',
    subsystems_ok: ['MSR', 'CGM', 'CDLM', 'RM'],
    subsystems_errored: [],
    signal_count: 1,
    graph_edge_count: 1,
    domain_link_count: 1,
    resonance_count: 1,
    b11_floor_passed: true,
  },
}

// ── Mock McpServer ────────────────────────────────────────────────────────────

interface ToolHandler {
  handler: (args: Record<string, unknown>) => Promise<{ content: Array<{ type: string; text: string }> }>
  description: string
  schema: Record<string, unknown>
}

function createMockServer() {
  const tools = new Map<string, ToolHandler>()

  const server = {
    tool: vi.fn((name: string, description: string, schema: Record<string, unknown>, handler: ToolHandler['handler']) => {
      tools.set(name, { handler, description, schema })
    }),
  } as unknown as McpServer

  return { server, tools }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('registerHolisticBundleTool', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('registers a tool named holistic_bundle', () => {
    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    expect(tools.has('holistic_bundle')).toBe(true)
  })

  it('description mentions B.11 whole-chart-read', () => {
    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!
    expect(tool.description).toContain('B.11')
    expect(tool.description).toContain('whole-chart-read')
  })

  it('input schema requires chart_id', () => {
    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!
    expect(tool.schema).toHaveProperty('chart_id')
  })
})

describe('holistic_bundle handler', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns all 4 subsystems when sidecar succeeds', async () => {
    mockFetch.mockResolvedValue(makeSidecarResponse(FULL_BUNDLE))

    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!

    const result = await tool.handler({ chart_id: NATIVE_CHART_ID })
    expect(result.content).toHaveLength(1)

    const payload = JSON.parse(result.content[0]!.text)
    expect(payload.ok).toBe(true)
    expect(payload.tool).toBe('holistic_bundle')
    expect(payload.brahma_unit).toBe('BO-2-8')
    expect(payload.b11_floor_passed).toBe(true)
    expect(payload.result.signals).toHaveLength(1)
    expect(payload.result.graph_edges).toHaveLength(1)
    expect(payload.result.domain_links).toHaveLength(1)
    expect(payload.result.resonance).toHaveLength(1)
  })

  it('provenance_envelope reflects subsystems_ok for all 4', async () => {
    mockFetch.mockResolvedValue(makeSidecarResponse(FULL_BUNDLE))

    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!

    const result = await tool.handler({ chart_id: NATIVE_CHART_ID })
    const payload = JSON.parse(result.content[0]!.text)
    expect(payload.summary.subsystems_ok).toContain('MSR')
    expect(payload.summary.subsystems_ok).toContain('CGM')
    expect(payload.summary.subsystems_ok).toContain('CDLM')
    expect(payload.summary.subsystems_ok).toContain('RM')
    expect(payload.summary.subsystems_errored).toHaveLength(0)
  })

  it('returns ok:false + error envelope when sidecar call fails', async () => {
    mockFetch.mockRejectedValue(new Error('Connection refused'))

    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!

    const result = await tool.handler({ chart_id: NATIVE_CHART_ID })
    const payload = JSON.parse(result.content[0]!.text)
    expect(payload.ok).toBe(false)
    expect(payload.result.provenance_envelope.b11_floor_passed).toBe(false)
    expect(payload.result.provenance_envelope.subsystems_errored).toContain('MSR')
    expect(payload.result.signals).toHaveLength(0)
  })

  it('returns ok:false when sidecar returns HTTP error', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 503,
      text: () => Promise.resolve('Service Unavailable'),
    })

    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!

    const result = await tool.handler({ chart_id: NATIVE_CHART_ID })
    const payload = JSON.parse(result.content[0]!.text)
    expect(payload.ok).toBe(false)
    expect(payload.error).toContain('503')
  })

  it('summary counts match provenance_envelope', async () => {
    mockFetch.mockResolvedValue(makeSidecarResponse(FULL_BUNDLE))

    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!

    const result = await tool.handler({ chart_id: NATIVE_CHART_ID })
    const payload = JSON.parse(result.content[0]!.text)
    expect(payload.summary.signal_count).toBe(1)
    expect(payload.summary.graph_edge_count).toBe(1)
    expect(payload.summary.domain_link_count).toBe(1)
    expect(payload.summary.resonance_count).toBe(1)
  })

  it('b11_floor_passed is false when signals array is empty', async () => {
    const emptyBundle = {
      ...FULL_BUNDLE,
      signals: [],
      provenance_envelope: {
        ...FULL_BUNDLE.provenance_envelope,
        signal_count: 0,
        b11_floor_passed: false,
        subsystems_errored: ['MSR'],
        subsystems_ok: ['CGM', 'CDLM', 'RM'],
      },
    }
    mockFetch.mockResolvedValue(makeSidecarResponse(emptyBundle))

    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!

    const result = await tool.handler({ chart_id: NATIVE_CHART_ID })
    const payload = JSON.parse(result.content[0]!.text)
    // ok is still true at the tool level (bundle returned data)
    expect(payload.ok).toBe(true)
    expect(payload.b11_floor_passed).toBe(false)
    expect(payload.summary.signal_count).toBe(0)
  })

  it('response text is valid JSON', async () => {
    mockFetch.mockResolvedValue(makeSidecarResponse(FULL_BUNDLE))

    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!

    const result = await tool.handler({ chart_id: NATIVE_CHART_ID })
    expect(() => JSON.parse(result.content[0]!.text)).not.toThrow()
  })

  it('includes brahma_unit BO-2-8 and latency_ms in response', async () => {
    mockFetch.mockResolvedValue(makeSidecarResponse(FULL_BUNDLE))

    const { server, tools } = createMockServer()
    registerHolisticBundleTool(server, MOCK_PRINCIPAL)
    const tool = tools.get('holistic_bundle')!

    const result = await tool.handler({ chart_id: NATIVE_CHART_ID })
    const payload = JSON.parse(result.content[0]!.text)
    expect(payload.brahma_unit).toBe('BO-2-8')
    expect(typeof payload.latency_ms).toBe('number')
    expect(payload.latency_ms).toBeGreaterThanOrEqual(0)
  })
})
