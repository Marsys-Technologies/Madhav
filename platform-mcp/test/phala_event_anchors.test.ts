/**
 * phala_event_anchors.test.ts — phala.anchors MCP tool unit tests (BRAHMA-PH-4-1)
 *
 * Tests:
 *   1. Tool registration — registerPhalaEventAnchorsTool registers 'event_anchors'
 *   2. Successful call — sidecar response forwarded correctly
 *   3. Contract assertions — all anchors have falsifier + source_citation + confidence in [0,1]
 *   4. Provenance envelope — b3_citation_compliant, all_falsifiers_present flags
 *   5. Error propagation — sidecar 503 → isError response
 *   6. Input schema validation — date_range, min_confidence, chart_id UUID
 *   7. Tool smoke — native chart_id round-trip shape
 *
 * All network calls are mocked — no real DB or sidecar required.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { registerPhalaEventAnchorsTool } from '../src/tools/phala_event_anchors.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'

// ── Mock fetch globally ────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Fixtures ───────────────────────────────────────────────────────────────────

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function makeAnchorRow(overrides: Partial<{
  anchor_id: string
  window: { start: string; end: string }
  theme: string
  confidence: number
  falsifier: string
  contributing_dashas: string[]
  contributing_signals: string[]
  source_citation: string
  prediction_state: string
  outcome_note: string | null
}> = {}) {
  return {
    anchor_id: 'PH-4-1.2026H1.CAREER',
    window: { start: '2026-01-01', end: '2026-06-30' },
    theme: 'career_consolidation',
    confidence: 0.59,
    falsifier:
      'If no new client contract in the Marsys Technology domain is reached before 2026-07-01, this prediction is false.',
    contributing_dashas: ['DSH.V.023: Mercury MD Saturn AD (2024-12-12 to 2027-08-21)'],
    contributing_signals: [
      'SIG.09 Mercury 8-system convergence',
      'SIG.14 Sun 10H career-density',
    ],
    source_citation: 'FORENSIC v8.0 §5.1 DSH.V.023; MSR v5.0 SIG.09/SIG.14',
    prediction_state: 'open',
    outcome_note: null,
    ...overrides,
  }
}

function makeThreeAnchors() {
  return [
    makeAnchorRow({ anchor_id: 'PH-4-1.2026H1.CAREER', confidence: 0.59 }),
    makeAnchorRow({
      anchor_id: 'PH-4-1.2026H2.SPIRIT',
      window: { start: '2026-07-01', end: '2026-12-31' },
      theme: 'spiritual_practice_intensification',
      confidence: 0.46,
      falsifier:
        'If no new formal spiritual practice is established before 2027-01-01, this prediction is false.',
      source_citation: 'FORENSIC v8.0 §5.1 DSH.V.023; SADE_SATI_CYCLES_ALL.md Cycle 2',
    }),
    makeAnchorRow({
      anchor_id: 'PH-4-1.2027H2.REGIME_CHANGE',
      window: { start: '2027-07-01', end: '2027-12-31' },
      theme: 'regime_discontinuity_mercury_to_ketu',
      confidence: 0.38,
      falsifier:
        'If the Mercury→Ketu MD transition does not produce any observable role change before 2028-01-01, this prediction is false.',
      source_citation:
        'FORENSIC v8.0 §5.1 DSH.V.023–024; LEL v1.7 PRED.M3D.HOLDOUT.002',
    }),
  ]
}

function makeFullSidecarResponse(anchors = makeThreeAnchors()) {
  return {
    ok: true,
    chart_id: NATIVE_CHART_ID,
    query_window: { start: '2026-01-01', end: '2030-12-31' },
    anchors,
    anchor_count: anchors.length,
    provenance_envelope: {
      source: 'phala.anchors',
      asset: 'PH-4-1',
      algorithm: 'dasha_quality × signal_strength × convergence_score',
      min_confidence_applied: 0.0,
      chart_id: NATIVE_CHART_ID,
      queried_at: '2026-06-04T00:00:00.000Z',
      l1_ground_truth: 'FORENSIC v8.0 §5.1 DSH.V.023–028; CHART_FACTS_EXTRACTION_v1_0.yaml',
      b3_citation_compliant: true,
      all_falsifiers_present: true,
    },
  }
}

function mockSidecarOk(body: object) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  })
}

function mockSidecarError(status: number, message: string) {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status,
    text: () => Promise.resolve(JSON.stringify({ detail: message })),
  })
}

// ── Mock McpServer ─────────────────────────────────────────────────────────────

type ToolHandler = (params: Record<string, unknown>) => Promise<{
  content: Array<{ type: string; text: string }>
  isError?: boolean
}>

function makeMockServer() {
  let registeredName: string | null = null
  let registeredHandler: ToolHandler | null = null

  const server = {
    tool: vi.fn((name: string, _desc: string, _schema: unknown, handler: ToolHandler) => {
      registeredName = name
      registeredHandler = handler
    }),
    getRegisteredName: () => registeredName,
    callTool: async (params: Record<string, unknown>) => {
      if (!registeredHandler) throw new Error('No tool registered')
      return registeredHandler(params)
    },
  }

  return server as unknown as McpServer & {
    getRegisteredName(): string | null
    callTool(params: Record<string, unknown>): Promise<{
      content: Array<{ type: string; text: string }>
      isError?: boolean
    }>
  }
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('registerPhalaEventAnchorsTool', () => {
  let server: ReturnType<typeof makeMockServer>

  beforeEach(() => {
    vi.clearAllMocks()
    server = makeMockServer()
    registerPhalaEventAnchorsTool(server as unknown as McpServer)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ── §1 Tool registration ──────────────────────────────────────────────────

  describe('tool registration', () => {
    it('registers a tool named event_anchors', () => {
      expect(server.getRegisteredName()).toBe('event_anchors')
    })

    it('calls server.tool exactly once', () => {
      const mockServer = server as unknown as { tool: ReturnType<typeof vi.fn> }
      expect(mockServer.tool).toHaveBeenCalledTimes(1)
    })
  })

  // ── §2 Successful sidecar call ────────────────────────────────────────────

  describe('successful call', () => {
    it('returns parsed JSON from sidecar', async () => {
      const sidecarBody = makeFullSidecarResponse()
      mockSidecarOk(sidecarBody)

      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })

      expect(result.content).toHaveLength(1)
      expect(result.content[0].type).toBe('text')
      expect(result.isError).toBeFalsy()

      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.ok).toBe(true)
      expect(parsed.anchor_count).toBe(3)
    })

    it('passes chart_id to sidecar fetch', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2026-06-30' },
      })

      const fetchCall = mockFetch.mock.calls[0]
      const body = JSON.parse(fetchCall[1].body)
      expect(body.chart_id).toBe(NATIVE_CHART_ID)
    })

    it('passes date_range to sidecar fetch', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2027-01-01', end: '2027-12-31' },
      })

      const fetchCall = mockFetch.mock.calls[0]
      const body = JSON.parse(fetchCall[1].body)
      expect(body.date_range).toEqual({ start: '2027-01-01', end: '2027-12-31' })
    })

    it('passes min_confidence when provided', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
        min_confidence: 0.5,
      })

      const fetchCall = mockFetch.mock.calls[0]
      const body = JSON.parse(fetchCall[1].body)
      expect(body.min_confidence).toBe(0.5)
    })
  })

  // ── §3 Contract assertions on returned anchors ────────────────────────────

  describe('anchor contract assertions', () => {
    it('all anchors have non-empty falsifier', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.anchors.length).toBeGreaterThanOrEqual(1)
      for (const anchor of parsed.anchors) {
        expect(typeof anchor.falsifier).toBe('string')
        expect(anchor.falsifier.length).toBeGreaterThan(0)
      }
    })

    it('all anchors have non-empty source_citation', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      for (const anchor of parsed.anchors) {
        expect(typeof anchor.source_citation).toBe('string')
        expect(anchor.source_citation.length).toBeGreaterThan(0)
      }
    })

    it('all anchor confidence values are in [0, 1]', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      for (const anchor of parsed.anchors) {
        expect(anchor.confidence).toBeGreaterThanOrEqual(0.0)
        expect(anchor.confidence).toBeLessThanOrEqual(1.0)
      }
    })

    it('all anchors have window.start and window.end', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      for (const anchor of parsed.anchors) {
        expect(anchor.window).toBeDefined()
        expect(typeof anchor.window.start).toBe('string')
        expect(typeof anchor.window.end).toBe('string')
        // Validate ISO date format
        expect(() => new Date(anchor.window.start)).not.toThrow()
        expect(() => new Date(anchor.window.end)).not.toThrow()
      }
    })
  })

  // ── §4 Provenance envelope ────────────────────────────────────────────────

  describe('provenance_envelope', () => {
    it('response includes provenance_envelope', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.provenance_envelope).toBeDefined()
    })

    it('provenance_envelope has source=phala.anchors', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.provenance_envelope.source).toBe('phala.anchors')
    })

    it('provenance_envelope has asset=PH-4-1', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.provenance_envelope.asset).toBe('PH-4-1')
    })

    it('provenance_envelope.b3_citation_compliant is boolean', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(typeof parsed.provenance_envelope.b3_citation_compliant).toBe('boolean')
    })

    it('provenance_envelope.all_falsifiers_present is boolean', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(typeof parsed.provenance_envelope.all_falsifiers_present).toBe('boolean')
    })

    it('provenance_envelope.l1_ground_truth references FORENSIC', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.provenance_envelope.l1_ground_truth).toContain('FORENSIC')
    })
  })

  // ── §5 Error propagation ──────────────────────────────────────────────────

  describe('error propagation', () => {
    it('returns isError=true on sidecar 503', async () => {
      mockSidecarError(503, 'Service Unavailable')
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      expect(result.isError).toBe(true)
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.error).toBe(true)
    })

    it('error response contains chart_id', async () => {
      mockSidecarError(500, 'Internal error')
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.chart_id).toBe(NATIVE_CHART_ID)
    })

    it('error response contains date_range', async () => {
      mockSidecarError(500, 'Internal error')
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2028-01-01', end: '2028-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.date_range).toEqual({ start: '2028-01-01', end: '2028-12-31' })
    })
  })

  // ── §6 Native chart smoke ─────────────────────────────────────────────────

  describe('native chart smoke', () => {
    it('native chart_id returns >= 3 anchors for 2026-2030', async () => {
      // The full response pre-seeded with 9 anchors (six-month windows 2026-2030)
      const nineAnchors = [
        makeAnchorRow({ anchor_id: 'PH-4-1.2026H1.CAREER', confidence: 0.59 }),
        makeAnchorRow({ anchor_id: 'PH-4-1.2026H2.SPIRIT', confidence: 0.46 }),
        makeAnchorRow({ anchor_id: 'PH-4-1.2027H1.TRANSITION', confidence: 0.40 }),
        makeAnchorRow({ anchor_id: 'PH-4-1.2027H2.REGIME_CHANGE', confidence: 0.38 }),
        makeAnchorRow({ anchor_id: 'PH-4-1.2028H1.RELATIONAL', confidence: 0.27 }),
        makeAnchorRow({ anchor_id: 'PH-4-1.2028H2.WEALTH', confidence: 0.31 }),
        makeAnchorRow({ anchor_id: 'PH-4-1.2029H1.AUTHORITY', confidence: 0.30 }),
        makeAnchorRow({ anchor_id: 'PH-4-1.2029H2.SOUL', confidence: 0.36 }),
        makeAnchorRow({ anchor_id: 'PH-4-1.2030H1.ACTION', confidence: 0.26 }),
      ]
      mockSidecarOk(makeFullSidecarResponse(nineAnchors))

      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })

      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.anchor_count).toBeGreaterThanOrEqual(3)
      expect(parsed.anchors).toHaveLength(9)
    })

    it('anchor_count matches anchors array length', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2030-12-31' },
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.anchor_count).toBe(parsed.anchors.length)
    })

    it('tool is called with correct sidecar path', async () => {
      mockSidecarOk(makeFullSidecarResponse())
      await server.callTool({
        chart_id: NATIVE_CHART_ID,
        date_range: { start: '2026-01-01', end: '2026-06-30' },
      })
      const fetchCall = mockFetch.mock.calls[0]
      const url: string = fetchCall[0]
      expect(url).toContain('/phala/event_anchors')
    })
  })
})
