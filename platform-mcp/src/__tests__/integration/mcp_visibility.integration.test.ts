/**
 * mcp_visibility.integration.test.ts — R1-T1 integration
 * Skipped unless MCP_BASE_URL + MCP_API_KEY_CLIENT are set.
 * Verifies the /mcp tools/list endpoint returns all 40 tools for client tier.
 */

import { describe, it, expect } from 'vitest'

const SKIP = !process.env['MCP_BASE_URL'] || !process.env['MCP_API_KEY_CLIENT']

describe.skipIf(SKIP)('MCP tool visibility — integration (R1 de-gating)', () => {
  it('client tier API key sees all 40 tools', async () => {
    const response = await fetch(`${process.env['MCP_BASE_URL']}/mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env['MCP_API_KEY_CLIENT']}`,
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/list',
        params: {},
      }),
      signal: AbortSignal.timeout(15_000),
    })
    const json = await response.json() as {
      result?: { tools?: Array<{ name: string }> }
    }
    const tools = json.result?.tools ?? []
    expect(tools.length).toBe(40)
    const names = tools.map(t => t.name)
    expect(names).toContain('tool_health')
    expect(names).toContain('data_coverage')
    expect(names).toContain('log_prediction')
    expect(names).toContain('record_outcome')
    expect(names).toContain('flag_disagreement')
  })
})
