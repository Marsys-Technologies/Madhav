/**
 * phala_outlook.test.ts — phala.outlook MCP tool unit tests (BRAHMA-PH-4-5)
 *
 * Acceptance criteria:
 *   AC1 — all 4 subsystems present in response
 *   AC2 — summary_confidence in [0.0, 1.0]
 *   AC3 — tool smoke: native chart returns valid structure
 *
 * Test sections:
 *   §1 Tool registration — registerPhalaOutlookTool registers 'phala_outlook'
 *   §2 AC1 — all 4 subsystems present: anchors, mitigations, rectification, auspicious_windows
 *   §3 AC2 — summary_confidence in [0.0, 1.0]
 *   §4 Provenance envelope — source, asset, layers, computed_at
 *   §5 Error propagation — sidecar 503 → isError response
 *   §6 AC3 tool smoke — native chart_id round-trip shape
 *   §7 Input schema validation — chart_id UUID, horizon_months range
 *
 * All network calls mocked — no real DB or sidecar required.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { registerPhalaOutlookTool } from '../src/tools/phala_outlook.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'

// ── Mock fetch globally ────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Fixtures ───────────────────────────────────────────────────────────────────

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

function makeAnchorRow(confidence = 0.59) {
  return {
    anchor_id: 'PH-4-1.2026H1.CAREER',
    window: { start: '2026-01-01', end: '2026-06-30' },
    theme: 'career_consolidation',
    confidence,
    falsifier: 'If no new contract before 2026-07-01, this prediction is false.',
    contributing_dashas: ['DSH.V.023: Mercury MD Saturn AD'],
    contributing_signals: ['SIG.09 Mercury 8-system convergence'],
    source_citation: 'FORENSIC v8.0 §5.1 DSH.V.023; MSR v5.0 SIG.09',
    prediction_state: 'open',
    outcome_note: null,
  }
}

function makeMitigationRow() {
  return {
    anchor_id: 'PH-4-1.2026H1.CAREER',
    theme: 'career',
    mitigation_type: 'mantra',
    mitigation_text: 'Recite the beej mantra of the 10th lord daily.',
    source_l0_rule_id: 'BPHS-CAREER-MANTRA',
    source_citation: 'BPHS.3.6-8',
    l2_remediation_hub_id: null,
    asset_version: '1.0',
    computed_at: '2026-06-04T00:00:00+00:00',
  }
}

function makeRectification() {
  return {
    chart_id: NATIVE_CHART_ID,
    best_candidate_time: '10:44',
    confidence: 0.68,
    train_score: 0.71,
    test_score: 0.64,
    candidate_count: 61,
    source_citation: 'FORENSIC v8.0 §5.1 + LEL v1.7',
  }
}

function makeAuspiciousWindow() {
  return {
    date: '2026-06-10',
    tithi: 'Dvitiya',
    vara: 'Budhavara',
    moon_nakshatra: 'Rohini',
    yoga: 'Siddhi',
    karana: 'Bava',
    auspicious_metadata: {},
    top_windows: [
      { type: 'amrit_kalam', start_time: '08:00', end_time: '09:30', score: 0.9 },
    ],
    source: 'panchanga_daily / phala.outlook-PH-4-4',
  }
}

function makeFullOutlookResponse(
  opts: {
    anchors?: ReturnType<typeof makeAnchorRow>[]
    mitigations?: ReturnType<typeof makeMitigationRow>[]
    rectification?: ReturnType<typeof makeRectification>
    auspicious_windows?: ReturnType<typeof makeAuspiciousWindow>[]
    summary_confidence?: number
  } = {}
) {
  const anchors = opts.anchors ?? [makeAnchorRow(0.59), makeAnchorRow(0.46)]
  const summaryConf = opts.summary_confidence ?? (
    anchors.length > 0
      ? anchors.reduce((s, a) => s + a.confidence, 0) / anchors.length
      : 0.0
  )

  return {
    ok: true,
    chart_id: NATIVE_CHART_ID,
    horizon_months: 12,
    query_window: { start: '2026-06-04', end: '2026-12-04' },
    anchors,
    mitigations: opts.mitigations ?? [makeMitigationRow()],
    rectification: opts.rectification ?? makeRectification(),
    auspicious_windows: opts.auspicious_windows ?? [makeAuspiciousWindow()],
    summary_confidence: summaryConf,
    provenance_envelope: {
      source: 'phala.outlook',
      asset: 'PH-4-5',
      asset_version: '1.0',
      layers: ['PH-4-1', 'PH-4-2', 'PH-4-3', 'PH-4-4'],
      layer_provenances: {
        'PH-4-1': { source: 'phala.anchors' },
        'PH-4-2': { source: 'phala.mitigation' },
        'PH-4-3': { source: 'phala.rectification' },
        'PH-4-4': { source: 'panchanga_daily' },
      },
      chart_id: NATIVE_CHART_ID,
      horizon_months: 12,
      date_range: { start: '2026-06-04', end: '2026-12-04' },
      summary_confidence_algorithm: 'mean(anchor.confidence) across all returned anchors',
      computed_at: '2026-06-04T00:00:00.000Z',
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

describe('registerPhalaOutlookTool', () => {
  let server: ReturnType<typeof makeMockServer>

  beforeEach(() => {
    vi.clearAllMocks()
    server = makeMockServer()
    registerPhalaOutlookTool(server as unknown as McpServer)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ── §1 Tool registration ──────────────────────────────────────────────────

  describe('tool registration', () => {
    it('registers a tool named phala_outlook', () => {
      expect(server.getRegisteredName()).toBe('phala_outlook')
    })

    it('calls server.tool exactly once', () => {
      const mockServer = server as unknown as { tool: ReturnType<typeof vi.fn> }
      expect(mockServer.tool).toHaveBeenCalledTimes(1)
    })
  })

  // ── §2 AC1 — all 4 subsystems present ────────────────────────────────────

  describe('AC1 — all 4 subsystems present', () => {
    it('response contains anchors key', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed).toHaveProperty('anchors')
    })

    it('response contains mitigations key', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed).toHaveProperty('mitigations')
    })

    it('response contains rectification key', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed).toHaveProperty('rectification')
    })

    it('response contains auspicious_windows key', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed).toHaveProperty('auspicious_windows')
    })

    it('all 4 subsystem keys present simultaneously', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      const required = ['anchors', 'mitigations', 'rectification', 'auspicious_windows']
      for (const key of required) {
        expect(parsed).toHaveProperty(key)
      }
    })

    it('anchors is an array', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(Array.isArray(parsed.anchors)).toBe(true)
    })

    it('mitigations is an array', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(Array.isArray(parsed.mitigations)).toBe(true)
    })

    it('auspicious_windows is an array', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(Array.isArray(parsed.auspicious_windows)).toBe(true)
    })

    it('rectification is an object', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(typeof parsed.rectification).toBe('object')
      expect(parsed.rectification).not.toBeNull()
    })
  })

  // ── §3 AC2 — summary_confidence in [0.0, 1.0] ────────────────────────────

  describe('AC2 — summary_confidence in [0.0, 1.0]', () => {
    it('summary_confidence is present in response', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed).toHaveProperty('summary_confidence')
    })

    it('summary_confidence is a number', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(typeof parsed.summary_confidence).toBe('number')
    })

    it('summary_confidence >= 0.0', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.summary_confidence).toBeGreaterThanOrEqual(0.0)
    })

    it('summary_confidence <= 1.0', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.summary_confidence).toBeLessThanOrEqual(1.0)
    })

    it('summary_confidence is 0.0 when anchors is empty', async () => {
      mockSidecarOk(makeFullOutlookResponse({ anchors: [], summary_confidence: 0.0 }))
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.summary_confidence).toBe(0.0)
    })

    it('summary_confidence matches mean of anchor confidences', async () => {
      const anchors = [makeAnchorRow(0.59), makeAnchorRow(0.46)]
      const expected = (0.59 + 0.46) / 2
      mockSidecarOk(makeFullOutlookResponse({ anchors, summary_confidence: expected }))
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.summary_confidence).toBeCloseTo(expected, 3)
    })
  })

  // ── §4 Provenance envelope ────────────────────────────────────────────────

  describe('provenance_envelope', () => {
    it('response includes provenance_envelope', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.provenance_envelope).toBeDefined()
    })

    it('provenance_envelope.source is "phala.outlook"', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.provenance_envelope.source).toBe('phala.outlook')
    })

    it('provenance_envelope.asset is "PH-4-5"', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.provenance_envelope.asset).toBe('PH-4-5')
    })

    it('provenance_envelope.layers contains all 4 sub-system IDs', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      const layers = parsed.provenance_envelope.layers
      for (const id of ['PH-4-1', 'PH-4-2', 'PH-4-3', 'PH-4-4']) {
        expect(layers).toContain(id)
      }
    })

    it('provenance_envelope.computed_at is a string', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(typeof parsed.provenance_envelope.computed_at).toBe('string')
      expect(parsed.provenance_envelope.computed_at.length).toBeGreaterThan(0)
    })

    it('provenance_envelope.layer_provenances has all 4 keys', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      const lp = parsed.provenance_envelope.layer_provenances
      for (const id of ['PH-4-1', 'PH-4-2', 'PH-4-3', 'PH-4-4']) {
        expect(lp).toHaveProperty(id)
      }
    })
  })

  // ── §5 Error propagation ──────────────────────────────────────────────────

  describe('error propagation', () => {
    it('returns isError=true on sidecar 503', async () => {
      mockSidecarError(503, 'Service Unavailable')
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      expect(result.isError).toBe(true)
    })

    it('error response contains error=true', async () => {
      mockSidecarError(503, 'Service Unavailable')
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.error).toBe(true)
    })

    it('error response contains chart_id', async () => {
      mockSidecarError(500, 'Internal error')
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.chart_id).toBe(NATIVE_CHART_ID)
    })

    it('error response contains horizon_months', async () => {
      mockSidecarError(500, 'Internal error')
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 6,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.horizon_months).toBe(6)
    })

    it('error response contains tool=phala_outlook', async () => {
      mockSidecarError(500, 'Internal error')
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.tool).toBe('phala_outlook')
    })
  })

  // ── §6 AC3 — Tool smoke: native chart round-trip ──────────────────────────

  describe('AC3 — tool smoke (native chart)', () => {
    it('native chart returns ok=true', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      expect(result.isError).toBeFalsy()
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.ok).toBe(true)
    })

    it('native chart response has chart_id echoed correctly', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const parsed = JSON.parse(result.content[0].text)
      expect(parsed.chart_id).toBe(NATIVE_CHART_ID)
    })

    it('sidecar is called at /api/compute/phala/outlook', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const fetchCall = mockFetch.mock.calls[0]
      const url: string = fetchCall[0]
      expect(url).toContain('/phala/outlook')
    })

    it('chart_id is passed to sidecar in request body', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      const fetchCall = mockFetch.mock.calls[0]
      const body = JSON.parse(fetchCall[1].body)
      expect(body.chart_id).toBe(NATIVE_CHART_ID)
    })

    it('horizon_months is passed to sidecar in request body', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 6,
      })
      const fetchCall = mockFetch.mock.calls[0]
      const body = JSON.parse(fetchCall[1].body)
      expect(body.horizon_months).toBe(6)
    })

    it('min_confidence is passed to sidecar when provided', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
        min_confidence: 0.45,
      })
      const fetchCall = mockFetch.mock.calls[0]
      const body = JSON.parse(fetchCall[1].body)
      expect(body.min_confidence).toBe(0.45)
    })

    it('response content is a single text element', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 12,
      })
      expect(result.content).toHaveLength(1)
      expect(result.content[0].type).toBe('text')
    })
  })

  // ── §7 Input schema validation ────────────────────────────────────────────

  describe('input schema validation', () => {
    it('rejects invalid chart_id (not UUID)', async () => {
      await expect(
        server.callTool({
          chart_id: 'not-a-uuid',
          horizon_months: 12,
        })
      ).rejects.toThrow()
    })

    it('rejects horizon_months = 0', async () => {
      await expect(
        server.callTool({
          chart_id: NATIVE_CHART_ID,
          horizon_months: 0,
        })
      ).rejects.toThrow()
    })

    it('rejects horizon_months > 120', async () => {
      await expect(
        server.callTool({
          chart_id: NATIVE_CHART_ID,
          horizon_months: 121,
        })
      ).rejects.toThrow()
    })

    it('rejects min_confidence < 0', async () => {
      await expect(
        server.callTool({
          chart_id: NATIVE_CHART_ID,
          horizon_months: 12,
          min_confidence: -0.1,
        })
      ).rejects.toThrow()
    })

    it('rejects min_confidence > 1', async () => {
      await expect(
        server.callTool({
          chart_id: NATIVE_CHART_ID,
          horizon_months: 12,
          min_confidence: 1.5,
        })
      ).rejects.toThrow()
    })

    it('accepts horizon_months = 1 (boundary)', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 1,
      })
      expect(result.isError).toBeFalsy()
    })

    it('accepts horizon_months = 120 (boundary)', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      const result = await server.callTool({
        chart_id: NATIVE_CHART_ID,
        horizon_months: 120,
      })
      expect(result.isError).toBeFalsy()
    })

    it('defaults horizon_months to 12 when omitted', async () => {
      mockSidecarOk(makeFullOutlookResponse())
      await server.callTool({
        chart_id: NATIVE_CHART_ID,
      })
      const fetchCall = mockFetch.mock.calls[0]
      const body = JSON.parse(fetchCall[1].body)
      expect(body.horizon_months).toBe(12)
    })
  })
})
