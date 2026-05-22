/**
 * tool_health.integration.test.ts — Integration tests for tool_health MCP tool.
 * MCPT v3.1.0-S4 AC.S4.7
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

import { registerToolHealth } from '../src/tools/tool_health.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'

// ── Mock McpServer ────────────────────────────────────────────────────────────

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

const SUPER_ADMIN_PRINCIPAL = {
  user_uid: 'uid-super',
  audience_tier: 'super_admin',
  key_id: 'key-super',
}

const CLIENT_PRINCIPAL = {
  user_uid: 'uid-client',
  audience_tier: 'client',
  key_id: 'key-client',
}

describe('tool_health MCP tool', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        ok: true,
        generated_at: new Date().toISOString(),
        tools: [],
      }),
    })
    vi.clearAllMocks()
  })

  it('registers as "tool_health" tool', () => {
    const server = createMockServer()
    registerToolHealth(server as unknown as McpServer, () => SUPER_ADMIN_PRINCIPAL)
    expect(typeof server.callTool).toBe('function')
  })

  it('returns 403-equivalent for client tier', async () => {
    const server = createMockServer()
    registerToolHealth(server as unknown as McpServer, () => CLIENT_PRINCIPAL)

    const result = await server.callTool('tool_health', { lookback_hours: 24 })
    expect(result.isError).toBe(true)
    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as { error?: string }
    expect(parsed.error).toBe('Forbidden')
  })

  it('calls platform /api/mcp/health/tools for super_admin', async () => {
    const server = createMockServer()
    registerToolHealth(server as unknown as McpServer, () => SUPER_ADMIN_PRINCIPAL)

    await server.callTool('tool_health', { lookback_hours: 24 })
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/mcp/health/tools'),
      expect.any(Object)
    )
  })

  it('returns ok: true for super_admin on success', async () => {
    const server = createMockServer()
    registerToolHealth(server as unknown as McpServer, () => SUPER_ADMIN_PRINCIPAL)

    const result = await server.callTool('tool_health', { lookback_hours: 24 })
    expect(result.isError).toBeFalsy()
    const parsed = JSON.parse(result.content[0]?.text ?? '{}') as { ok?: boolean }
    expect(parsed.ok).toBe(true)
  })

  it('handles platform fetch failure gracefully', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))

    const server = createMockServer()
    registerToolHealth(server as unknown as McpServer, () => SUPER_ADMIN_PRINCIPAL)

    const result = await server.callTool('tool_health', { lookback_hours: 24 })
    expect(result.isError).toBe(true)
  })
})
