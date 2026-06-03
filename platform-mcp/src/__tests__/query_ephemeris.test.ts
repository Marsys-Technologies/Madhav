/**
 * query_ephemeris.test.ts — Unit tests for brahmagyan.ephemeris MCP tool.
 *
 * Tests 7.1–7.7 per CLAUDECODE_BRIEF_BRAHMA_INFRA_VERIFICATION_v1_0.md §DELIVERABLE 7.
 * [BRAHMA-BG-0-1]
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { registerQueryEphemeris } from '../tools/query_ephemeris.js'
import { MCP_CONTRACT_TOOL_NAMES } from '../contract_bridge.js'

// ── Mock callPlatformPrimitive ────────────────────────────────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'

const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)

// ── Helper types ──────────────────────────────────────────────────────────────

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  content: Array<{ type: string; text: string }>
  isError?: boolean
}>

/**
 * Build a minimal mock McpServer and capture registered tools.
 */
function createMockServerWithCapture() {
  const registered: Map<string, ToolHandler> = new Map()
  const mockServer = {
    tool: (name: string, _desc: string, _schema: unknown, handler: ToolHandler) => {
      registered.push ? null : null // type compat
      registered.set(name, handler)
    },
  } as unknown as McpServer
  return { mockServer, registered }
}

/** Return a simple mock server that only tracks names (for TEST 7.1). */
function createSimpleMockServer() {
  const registeredNames: string[] = []
  return {
    mockServer: {
      tool: (name: string, ..._rest: unknown[]) => { registeredNames.push(name) },
    } as unknown as McpServer,
    registeredNames,
  }
}

const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key' }

// ── TEST 7.1 — Tool registers without throwing ────────────────────────────────

describe('query_ephemeris — registration', () => {
  it('registerQueryEphemeris registers the tool on server without throwing', () => {
    const { mockServer, registeredNames } = createSimpleMockServer()
    registerQueryEphemeris(mockServer, () => TEST_PRINCIPAL)
    expect(registeredNames).toContain('query_ephemeris')
  })
})

// ── TEST 7.2 — Rejects date_range_too_wide ───────────────────────────────────

describe('query_ephemeris — date range validation', () => {
  it('rejects date_range_too_wide (span > 1825 days)', async () => {
    const { mockServer, registered } = createMockServerWithCapture()
    registerQueryEphemeris(mockServer, () => TEST_PRINCIPAL)

    const handler = registered.get('query_ephemeris')!
    expect(handler).toBeDefined()

    const result = await handler({
      date_range: { from: '2020-01-01', to: '2030-01-01' },
      sample_step: '1d',
      return_changes_only: false,
    })

    expect(result.isError).toBe(true)
    const parsed = JSON.parse(result.content[0]?.text ?? '{}')
    expect(parsed.error).toBe('date_range_too_wide')
    // Verify callPlatformPrimitive was never called
    expect(mockCallPlatformPrimitive).not.toHaveBeenCalled()
  })

  it('rejects reversed date range (from > to)', async () => {
    const { mockServer, registered } = createMockServerWithCapture()
    registerQueryEphemeris(mockServer, () => TEST_PRINCIPAL)

    const handler = registered.get('query_ephemeris')!
    const result = await handler({
      date_range: { from: '2025-06-01', to: '2025-01-01' },
      sample_step: '1d',
      return_changes_only: false,
    })

    expect(result.isError).toBe(true)
    const parsed = JSON.parse(result.content[0]?.text ?? '{}')
    expect(parsed.error).toBe('date_range_invalid')
  })
})

// ── TEST 7.4 — FORENSIC ground-truth: native birth date 1984-02-05, Saturn ───

describe('query_ephemeris — FORENSIC ground-truth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('native birth date 1984-02-05 Saturn: sign=Libra, dignity_d1=exalted (FORENSIC v8.0)', async () => {
    // Saturn was in Libra (exalted) at ~27° on 1984-02-05 — FORENSIC_ASTROLOGICAL_DATA_v8_0.md
    mockCallPlatformPrimitive.mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'test-trace-001',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: {
          positions: [{
            date: '1984-02-05',
            planet: 'Saturn',
            sign: 'Libra',
            sign_degree: 27.3,
            nakshatra: 'Vishakha',
            nakshatra_pada: 4,
            retrograde: false,
            speed_deg_per_day: 0.041,
            dignity_d1: 'exalted',
          }]
        },
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    const { mockServer, registered } = createMockServerWithCapture()
    registerQueryEphemeris(mockServer, () => TEST_PRINCIPAL)

    const handler = registered.get('query_ephemeris')!
    const result = await handler({
      planet: 'Saturn',
      date_range: { from: '1984-02-05', to: '1984-02-05' },
      sample_step: '1d',
      return_changes_only: false,
    })

    expect(result.isError).toBeUndefined()
    const parsed = JSON.parse(result.content[0]?.text ?? '{}')
    expect(parsed.ok).toBe(true)
    expect(parsed.result.positions[0].sign).toBe('Libra')
    expect(parsed.result.positions[0].dignity_d1).toBe('exalted')
  })
})

// ── TEST 7.5 — Omitting planet → no planet/planets keys ──────────────────────

describe('query_ephemeris — planet omission', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('omitting planet returns all grahas (callPlatformPrimitive called without planet/planets keys)', async () => {
    mockCallPlatformPrimitive.mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'test-trace-002',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: { positions: [] },
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    const { mockServer, registered } = createMockServerWithCapture()
    registerQueryEphemeris(mockServer, () => TEST_PRINCIPAL)

    const handler = registered.get('query_ephemeris')!
    await handler({
      date_range: { from: '2025-01-01', to: '2025-01-07' },
      sample_step: '1d',
      return_changes_only: false,
    })

    expect(mockCallPlatformPrimitive).toHaveBeenCalledOnce()
    const [_toolName, callParams] = mockCallPlatformPrimitive.mock.calls[0]!
    expect(callParams).not.toHaveProperty('planet')
    expect(callParams).not.toHaveProperty('planets')
  })
})

// ── TEST 7.6 — sample_step '7d' → integer 7 ──────────────────────────────────

describe('query_ephemeris — sample_step conversion', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("sample_step '7d' converts to integer 7 (not string)", async () => {
    mockCallPlatformPrimitive.mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'test-trace-003',
        epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
        result: { positions: [] },
        citations: [],
        plan: null,
        predictions_logged: [],
        synthesis_audit: null,
        suggested_followups: [],
        warnings: [],
      },
    })

    const { mockServer, registered } = createMockServerWithCapture()
    registerQueryEphemeris(mockServer, () => TEST_PRINCIPAL)

    const handler = registered.get('query_ephemeris')!
    await handler({
      date_range: { from: '2025-01-01', to: '2025-06-30' },
      sample_step: '7d',
      return_changes_only: false,
    })

    expect(mockCallPlatformPrimitive).toHaveBeenCalledOnce()
    const [_toolName, callParams] = mockCallPlatformPrimitive.mock.calls[0]!
    expect(callParams['sample_step']).toBe(7)
    expect(typeof callParams['sample_step']).toBe('number')
  })
})

// ── TEST 7.7 — Tool name is in MCP_CONTRACT_TOOL_NAMES ───────────────────────

describe('query_ephemeris — contract bridge', () => {
  it('query_ephemeris is in MCP_CONTRACT_TOOL_NAMES', () => {
    expect(MCP_CONTRACT_TOOL_NAMES).toContain('query_ephemeris')
  })
})
