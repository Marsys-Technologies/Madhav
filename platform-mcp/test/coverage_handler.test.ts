/**
 * coverage_handler.test.ts — Tests for coverage + tool_health handler behaviour
 * through the data_coverage and tool_health MCP tools.
 *
 * Validates Phase 7c: graceful empty-table fallback and real-data path.
 *
 * MCPT v3.2 Phase 7c
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

import { registerDataCoverage } from '../src/tools/data_coverage.js'
import { registerToolHealth } from '../src/tools/tool_health.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'

// ── Shared helpers ────────────────────────────────────────────────────────────

type ToolHandler = (
  input: Record<string, unknown>
) => Promise<{ content: Array<{ type: string; text: string }>; isError?: boolean }>

function createMockServer() {
  const tools: Record<string, { handler: ToolHandler }> = {}
  return {
    tool: (name: string, _desc: string, _schema: unknown, handler: ToolHandler) => {
      tools[name] = { handler }
    },
    callTool: (name: string, input: Record<string, unknown>) => {
      const tool = tools[name]
      if (!tool) throw new Error(`Tool ${name} not registered`)
      return tool.handler(input)
    },
  }
}

const ACHARYA_PRINCIPAL = {
  user_uid: 'uid-acharya',
  audience_tier: 'acharya',
  key_id: 'key-acharya',
}

const SUPER_ADMIN_PRINCIPAL = {
  user_uid: 'uid-super',
  audience_tier: 'super_admin',
  key_id: 'key-super',
}

// ── data_coverage handler tests ───────────────────────────────────────────────

describe('data_coverage: coverage handler Phase 7c', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns ok:true with empty coverage array and seeding note when table is empty', async () => {
    // Simulate the platform handler returning "not yet seeded" graceful response
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ok: true,
          generated_at: new Date().toISOString(),
          tier: 'acharya',
          coverage: [],
          caveats: [],
          note: 'data_source_expected table not yet seeded — run Phase 7a seed load',
        }),
    })

    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => ACHARYA_PRINCIPAL)

    const result = await server.callTool('data_coverage', {})
    expect(result.isError).toBeFalsy()

    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as {
      ok?: boolean
      coverage?: unknown[]
      note?: string
    }
    expect(parsed.ok).toBe(true)
    expect(Array.isArray(parsed.coverage)).toBe(true)
    expect(parsed.coverage).toHaveLength(0)
    expect(parsed.note).toContain('not yet seeded')
  })

  it('returns actual_rows and status when table is populated', async () => {
    // Simulate the platform handler returning real DB rows
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ok: true,
          generated_at: new Date().toISOString(),
          tier: 'acharya',
          coverage: [
            {
              tool: 'query_chart_facts',
              category: 'house',
              expected_rows: 12,
              actual_rows: 12,
              last_updated_at: '2026-05-23T02:00:00Z',
              backfill_phase: 'v3.1.0-S1',
              status: 'ok',
            },
            {
              tool: 'query_chart_facts',
              category: 'kp_cusp',
              expected_rows: 12,
              actual_rows: 0,
              last_updated_at: '2026-05-23T02:00:00Z',
              backfill_phase: 'v3.3',
              status: 'low',
            },
            {
              tool: 'query_signals',
              category: 'msr_corpus',
              expected_rows: 573,
              actual_rows: 573,
              last_updated_at: '2026-05-23T02:00:00Z',
              backfill_phase: 'v3.1.0-S1',
              status: 'ok',
            },
          ],
          caveats: [
            { tool: 'query_chart_facts', caveat: 'KP backfill pending v3.3', severity: 'warn' },
          ],
        }),
    })

    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => ACHARYA_PRINCIPAL)

    const result = await server.callTool('data_coverage', {})
    expect(result.isError).toBeFalsy()

    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as {
      ok?: boolean
      coverage?: Array<{
        tool: string
        category: string
        actual_rows: number
        expected_rows: number
        status: string
        last_updated_at?: string
      }>
      caveats?: unknown[]
    }

    expect(parsed.ok).toBe(true)
    expect(Array.isArray(parsed.coverage)).toBe(true)
    expect(parsed.coverage).toHaveLength(3)

    // Verify actual_rows is present (not null)
    const houseRow = parsed.coverage?.find(c => c.category === 'house')
    expect(houseRow).toBeDefined()
    expect(houseRow?.actual_rows).toBe(12)
    expect(houseRow?.status).toBe('ok')
    expect(houseRow?.last_updated_at).toBe('2026-05-23T02:00:00Z')

    // Verify low-status row for un-backfilled category
    const kpRow = parsed.coverage?.find(c => c.category === 'kp_cusp')
    expect(kpRow).toBeDefined()
    expect(kpRow?.actual_rows).toBe(0)
    expect(kpRow?.status).toBe('low')

    // Verify caveats present
    expect(Array.isArray(parsed.caveats)).toBe(true)
    expect(parsed.caveats).toHaveLength(1)
  })

  it('status is ok when actual_rows >= expected_rows', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ok: true,
          coverage: [
            {
              tool: 'query_panchanga',
              category: 'panchanga_daily',
              expected_rows: 73414,
              actual_rows: 73414,
              last_updated_at: '2026-05-23T02:00:00Z',
              status: 'ok',
            },
          ],
          caveats: [],
        }),
    })

    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => ACHARYA_PRINCIPAL)

    const result = await server.callTool('data_coverage', {})
    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as {
      coverage?: Array<{ status: string }>
    }
    expect(parsed.coverage?.[0]?.status).toBe('ok')
  })

  it('status is low when actual_rows < expected_rows', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ok: true,
          coverage: [
            {
              tool: 'query_chart_facts',
              category: 'shadbala',
              expected_rows: 9,
              actual_rows: 3,
              last_updated_at: '2026-05-23T02:00:00Z',
              status: 'low',
            },
          ],
          caveats: [],
        }),
    })

    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => ACHARYA_PRINCIPAL)

    const result = await server.callTool('data_coverage', {})
    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as {
      coverage?: Array<{ status: string; actual_rows: number }>
    }
    expect(parsed.coverage?.[0]?.status).toBe('low')
    expect(parsed.coverage?.[0]?.actual_rows).toBe(3)
  })
})

// ── tool_health handler tests ─────────────────────────────────────────────────

describe('tool_health: Phase 7c graceful MV fallback', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns ok:true with null metrics and note when MVs are not populated', async () => {
    // Simulate platform returning the graceful "MVs not yet available" response
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ok: true,
          generated_at: new Date().toISOString(),
          lookback_hours: 24,
          tier: 'super_admin',
          mv_available: false,
          tools: [
            {
              tool_name: 'holistic_bundle',
              call_count_24h: null,
              error_rate: null,
              avg_latency_ms: null,
              audit_finding_count: null,
              last_call_at: null,
              caveats: [],
            },
          ],
          note: 'audit MVs not yet populated — apply migration 082 and Phase 7b nightly audit job',
        }),
    })

    const server = createMockServer()
    registerToolHealth(server as unknown as McpServer, () => SUPER_ADMIN_PRINCIPAL)

    const result = await server.callTool('tool_health', {})
    expect(result.isError).toBeFalsy()

    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as {
      ok?: boolean
      mv_available?: boolean
      tools?: Array<{ tool_name: string; call_count_24h: number | null }>
      note?: string
    }
    expect(parsed.ok).toBe(true)
    expect(parsed.mv_available).toBe(false)
    expect(parsed.note).toContain('audit MVs not yet populated')
    expect(Array.isArray(parsed.tools)).toBe(true)
    const bundle = parsed.tools?.find(t => t.tool_name === 'holistic_bundle')
    expect(bundle).toBeDefined()
    expect(bundle?.call_count_24h).toBeNull()
  })

  it('returns real call_count_24h and error_rate when MVs are populated', async () => {
    // Simulate platform returning real MV data
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ok: true,
          generated_at: new Date().toISOString(),
          lookback_hours: 24,
          tier: 'super_admin',
          mv_available: true,
          tools: [
            {
              tool_name: 'holistic_bundle',
              call_count_24h: 42,
              error_rate: 0.05,
              avg_latency_ms: 320,
              audit_finding_count: 1,
              last_call_at: '2026-05-23T10:00:00Z',
              caveats: [],
            },
            {
              tool_name: 'query_chart_facts',
              call_count_24h: 18,
              error_rate: 0.0,
              avg_latency_ms: 85,
              audit_finding_count: 0,
              last_call_at: '2026-05-23T09:30:00Z',
              caveats: [],
            },
          ],
        }),
    })

    const server = createMockServer()
    registerToolHealth(server as unknown as McpServer, () => SUPER_ADMIN_PRINCIPAL)

    const result = await server.callTool('tool_health', {})
    expect(result.isError).toBeFalsy()

    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as {
      ok?: boolean
      mv_available?: boolean
      tools?: Array<{
        tool_name: string
        call_count_24h: number | null
        error_rate: number | null
        avg_latency_ms: number | null
        audit_finding_count: number | null
      }>
    }
    expect(parsed.ok).toBe(true)
    expect(parsed.mv_available).toBe(true)

    const bundle = parsed.tools?.find(t => t.tool_name === 'holistic_bundle')
    expect(bundle).toBeDefined()
    expect(bundle?.call_count_24h).toBe(42)
    expect(bundle?.error_rate).toBe(0.05)
    expect(bundle?.avg_latency_ms).toBe(320)
    expect(bundle?.audit_finding_count).toBe(1)
  })

  it('does not return data_note fallback about pending migrations', async () => {
    // Verify the old data_note sentinel is gone — handler must not emit it
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ok: true,
          tools: [],
          mv_available: false,
        }),
    })

    const server = createMockServer()
    registerToolHealth(server as unknown as McpServer, () => SUPER_ADMIN_PRINCIPAL)

    const result = await server.callTool('tool_health', {})
    const text = result.content[0]?.text ?? ''
    expect(text).not.toContain('Apply migrations 073-076')
    expect(text).not.toContain('data_note')
  })
})
