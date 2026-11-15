/** Mixed resource registration contract; all transport responses are synthetic. */
import { afterEach, expect, it, vi } from 'vitest'
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js'
import { registerResources } from '../resources/index.js'
import type { Principal } from '../types.js'

afterEach(() => { vi.unstubAllGlobals() })
it('registers retired and retained resources together and forwards the actual Principal through SDK reads', async () => {
  const fetchMock = vi.fn(async () => ({ ok: true, json: async () => ({ ok: true, content: { is_error: false, content: { rules: [] } } }) }))
  vi.stubGlobal('fetch', fetchMock)
  const principal: Principal = { user_uid: 'mixed-fixture-user', key_id: 'mixed-fixture-key', role: 'client' }
  const server = new McpServer({ name: 'mixed-resource-fixture', version: '1.0.0' })
  const client = new Client({ name: 'mixed-resource-client', version: '1.0.0' })
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair()
  registerResources(server, principal)
  try {
    await server.connect(serverTransport)
    await client.connect(clientTransport)
    const templates = (await client.listResourceTemplates()).resourceTemplates
    for (const name of ['chart-bundle', 'multi-ayanamsha', 'sutravali-by-planet', 'sutravali-by-house']) {
      expect(templates.filter(entry => entry.name === name)).toHaveLength(1)
    }
    for (const name of ['chart-bundle', 'multi-ayanamsha']) {
      const uri = `marsys://${name}/cccccccc-0000-0000-0000-000000000001`
      const result = await client.readResource({ uri })
      expect(result.contents[0]).toMatchObject({ uri, mimeType: 'text/markdown', text: expect.stringContaining('retired and unavailable') })
    }
    expect(fetchMock).not.toHaveBeenCalled()
    for (const suffix of ['all-by-planet/Saturn', 'all-by-house/02trailing']) {
      const uri = `marsys://resource/sutravali/${suffix}`
      const result = await client.readResource({ uri })
      expect(result.contents[0]).toMatchObject({ uri, mimeType: 'text/markdown', text: expect.stringContaining('No rules found for this query.') })
    }
    expect(fetchMock).toHaveBeenCalledTimes(2)
    for (const [, init] of fetchMock.mock.calls as unknown as [string, RequestInit][]) {
      expect(init.headers).toMatchObject({ 'X-MCP-User': principal.user_uid, 'X-MCP-Key-Id': principal.key_id })
    }
    expect(JSON.parse(String((fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1].body))).toEqual({ uri: 'marsys://tool/L0/query_sutravali_rules_for_planet', args: { planet: 'Saturn', limit: 500 } })
    expect(JSON.parse(String((fetchMock.mock.calls[1] as unknown as [string, RequestInit])[1].body))).toEqual({ uri: 'marsys://tool/L0/query_sutravali_rules', args: { house: 2, limit: 500 } })
  } finally { await client.close(); await server.close() }
})
