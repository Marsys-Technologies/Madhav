/**
 * DENS-F: bodha_signals_get declares the producer_asset_id input (a z.enum of the six producers) so the MCP SDK does not strip it,
 * and forwards it verbatim to query_signals (the bo_laksana facet is served through this surface too).
 */
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import { registerP1AliasTools } from '../register_p1_aliases.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)
const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }
const PRODUCERS = ['bo_laksana', 'bo_arudha', 'bo_special_lagna', 'bo_sudarshana', 'bo_vargottama_dhana', 'bo_nakshatra_semantic']

describe('bodha_signals_get producer_asset_id', () => {
  let schema: Record<string, z.ZodTypeAny>
  let handler: (p: Record<string, unknown>) => Promise<unknown>
  beforeAll(() => {
    const server = {
      tool: (name: string, _d: string, s: Record<string, z.ZodTypeAny>, h: typeof handler) => {
        if (name === 'bodha_signals_get') { schema = s; handler = h }
      },
    } as unknown as McpServer
    registerP1AliasTools(server, principal)
  })
  beforeEach(() => { mockFetch.mockReset() })

  it('is in the schema as an optional enum of exactly the six producers', () => {
    const f = schema['producer_asset_id']!
    expect(f).toBeDefined()
    expect(f.safeParse(undefined).success).toBe(true)
    for (const p of PRODUCERS) expect(f.safeParse(p).success).toBe(true)
    expect(f.safeParse('bo_unknown').success).toBe(false)
  })

  it('forwards the value to query_signals', async () => {
    mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => ({ ok: true, content: { signals: [] } }), text: async () => '{}' })
    await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', producer_asset_id: 'bo_laksana' })
    const bodies = mockFetch.mock.calls.map(c => String((c[1] as { body?: string } | undefined)?.body ?? ''))
    expect(bodies.some(b => b.includes('"producer_asset_id":"bo_laksana"'))).toBe(true)
  })
})
