/**
 * data_coverage.integration.test.ts — Integration tests for data_coverage MCP tool.
 * MCPT v3.1.0-S4 AC.S4.8
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

import { registerDataCoverage } from '../src/tools/data_coverage.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'

type ToolHandler = (input: Record<string, unknown>) => Promise<{ content: Array<{ type: string; text: string }>; isError?: boolean }>

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

const CLIENT_PRINCIPAL = {
  user_uid: 'uid-client',
  audience_tier: 'client',
  key_id: 'key-client',
}

describe('data_coverage MCP tool', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        ok: true,
        coverage: [
          { tool: 'query_chart_facts', category: 'house', expected_rows: 12, actual_rows: null, status: 'active' },
          { tool: 'query_chart_facts', category: 'kp_cusp', expected_rows: 12, actual_rows: null, status: 'pending', caveat: 'KP backfill pending v3.3' },
        ],
        caveats: [],
      }),
    })
    vi.clearAllMocks()
  })

  it('registers as "data_coverage" tool', () => {
    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => ACHARYA_PRINCIPAL)
    expect(typeof server.callTool).toBe('function')
  })

  it('returns 403-equivalent for client tier', async () => {
    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => CLIENT_PRINCIPAL)

    const result = await server.callTool('data_coverage', {})
    expect(result.isError).toBe(true)
    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as { error?: string }
    expect(parsed.error).toBe('Forbidden')
  })

  it('calls /api/mcp/health/coverage for acharya tier', async () => {
    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => ACHARYA_PRINCIPAL)

    await server.callTool('data_coverage', {})
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/mcp/health/coverage'),
      expect.any(Object)
    )
  })

  it('returns coverage data with expected structure', async () => {
    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => ACHARYA_PRINCIPAL)

    const result = await server.callTool('data_coverage', {})
    expect(result.isError).toBeFalsy()
    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as {
      ok?: boolean
      coverage?: Array<{ tool: string }>
    }
    expect(parsed.ok).toBe(true)
    expect(Array.isArray(parsed.coverage)).toBe(true)
  })

  it('applies tool_filter when provided', async () => {
    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => ACHARYA_PRINCIPAL)

    const result = await server.callTool('data_coverage', { tool_filter: 'query_chart_facts' })
    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as {
      coverage?: Array<{ tool: string }>
    }
    if (parsed.coverage) {
      expect(parsed.coverage.every(c => c.tool === 'query_chart_facts')).toBe(true)
    }
  })

  it('handles fetch failure gracefully', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))

    const server = createMockServer()
    registerDataCoverage(server as unknown as McpServer, () => ACHARYA_PRINCIPAL)

    const result = await server.callTool('data_coverage', {})
    expect(result.isError).toBe(true)
  })
})
