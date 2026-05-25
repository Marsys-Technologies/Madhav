/**
 * mcp_stub_engines.integration.test.ts — R2-T2 smoke integration test.
 *
 * Verifies the 4 previously-stubbed MCP primitive retrieval engines are
 * correctly registered in the portal's RETRIEVAL_TOOLS and resolvable by
 * the primitives dispatcher (getTool). These were the Class B stubs that
 * caused 500 errors on MCP primitive calls before GISMCP Remediation R2.
 *
 * Tests always run (no external dependency required) because they verify
 * the registry state, not live retrieval results.
 *
 * Skipped live-endpoint tests (require MCP_BASE_URL + MCP_API_KEY_CLIENT):
 *   - Smoke each MCP tool call returning ok: true (not 500).
 *
 * GISMCP Remediation R2-T2.
 */

import { describe, it, expect, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/storage', () => ({ getStorageClient: vi.fn() }))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))

import { getTool, RETRIEVAL_TOOLS } from '../../lib/retrieve/index'

// ── Registry smoke (always runs) ─────────────────────────────────────────────

describe('R2 stub engine registry smoke (R2-T2)', () => {
  const R2_TOOLS = [
    'query_tara_balam',
    'query_chandra_balam',
    'jaimini_chara_dasha',
    'jaimini_chara_dasha_full',
  ] as const

  for (const toolName of R2_TOOLS) {
    it(`getTool('${toolName}') resolves (was stub before R2)`, () => {
      const resolved = getTool(toolName)
      expect(resolved, `${toolName} not found in RETRIEVAL_TOOLS — stub not wired`).toBeDefined()
      expect(resolved!.name).toBe(toolName)
      expect(typeof resolved!.retrieve).toBe('function')
    })
  }

  it('all 4 R2 tools are in RETRIEVAL_TOOLS array', () => {
    const names = RETRIEVAL_TOOLS.map(t => t.name)
    for (const toolName of R2_TOOLS) {
      expect(names, `${toolName} missing from RETRIEVAL_TOOLS`).toContain(toolName)
    }
  })

  it('no duplicate entries for R2 tool names', () => {
    const names = RETRIEVAL_TOOLS.map(t => t.name)
    for (const toolName of R2_TOOLS) {
      const count = names.filter(n => n === toolName).length
      expect(count, `${toolName} has ${count} entries (expected 1)`).toBe(1)
    }
  })

  it('query_tara_balam and tara_balam_for_native are both registered (distinct tools)', () => {
    expect(getTool('query_tara_balam')).toBeDefined()
    expect(getTool('tara_balam_for_native')).toBeDefined()
    expect(getTool('query_tara_balam')!.name).not.toBe(getTool('tara_balam_for_native')!.name)
  })

  it('query_chandra_balam and chandra_balam_for_native are both registered (distinct tools)', () => {
    expect(getTool('query_chandra_balam')).toBeDefined()
    expect(getTool('chandra_balam_for_native')).toBeDefined()
    expect(getTool('query_chandra_balam')!.name).not.toBe(getTool('chandra_balam_for_native')!.name)
  })
})

// ── Live MCP endpoint smoke (skip without env vars) ───────────────────────────

const SKIP_LIVE = !process.env['MCP_BASE_URL'] || !process.env['MCP_API_KEY_CLIENT']

describe.skipIf(SKIP_LIVE)('R2 MCP live endpoint smoke (R2-T2)', () => {
  const callMcpTool = async (toolName: string, args: Record<string, unknown>) => {
    const res = await fetch(`${process.env['MCP_BASE_URL']}/mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env['MCP_API_KEY_CLIENT']}`,
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/call',
        params: { name: toolName, arguments: args },
      }),
      signal: AbortSignal.timeout(20_000),
    })
    return res.json() as Promise<{
      result?: { content?: Array<{ text: string }> }
      error?: { message: string }
    }>
  }

  it('tara_balam_for_native({date:"1984-02-05"}) returns ok:true (not 500)', async () => {
    const response = await callMcpTool('tara_balam_for_native', { date: '1984-02-05' })
    expect(response.error).toBeUndefined()
    const text = response.result?.content?.[0]?.text ?? '{}'
    const parsed = JSON.parse(text) as { ok?: boolean }
    expect(parsed.ok).toBe(true)
  }, 25_000)

  it('chandra_balam_for_native({date:"1984-02-05"}) returns ok:true (not 500)', async () => {
    const response = await callMcpTool('chandra_balam_for_native', { date: '1984-02-05' })
    expect(response.error).toBeUndefined()
    const text = response.result?.content?.[0]?.text ?? '{}'
    const parsed = JSON.parse(text) as { ok?: boolean }
    expect(parsed.ok).toBe(true)
  }, 25_000)
})
