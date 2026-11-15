/** Retirement compatibility contracts; synthetic URIs only, no live chart reads. */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { McpServer, ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js'
import http from 'node:http'
import https from 'node:https'
import { registerChartBundleResource } from '../resources/chart_bundle_resource.js'
import { registerMultiAyanamshaResource } from '../resources/multi_ayanamsha_resource.js'

type Handler = (uri: URL) => Promise<{ contents: Array<{ uri: string; mimeType: string; text: string }> }>
type Metadata = { title: string; description: string; mimeType: string }

function makeMockServer() {
  const entries = new Map<string, { template: ResourceTemplate; metadata: Metadata; handler: Handler }>()
  return {
    resource: vi.fn((name: string, template: ResourceTemplate, metadata: Metadata, handler: Handler) => {
      entries.set(name, { template, metadata, handler })
    }),
    entry(name: string) {
      const entry = entries.get(name)
      if (!entry) throw new Error(`Missing registration: ${name}`)
      return entry
    },
  }
}

const CHART_ID = 'cccccccc-0000-0000-0000-000000000001'
const cases = [
  { name: 'chart-bundle', register: registerChartBundleResource, title: 'Legacy Chart Bundle' },
  { name: 'multi-ayanamsha', register: registerMultiAyanamshaResource, title: 'Legacy Multi-Ayanamsha Status' },
] as const

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() => { throw new Error('Retired resource attempted backend/model/build HTTP') }))
  vi.spyOn(http, 'request').mockImplementation(() => { throw new Error('Unexpected HTTP request') })
  vi.spyOn(https, 'request').mockImplementation(() => { throw new Error('Unexpected HTTPS request') })
  vi.stubEnv('PLATFORM_URL', 'https://must-not-call.invalid')
  vi.stubEnv('MCP_INTERNAL_TOKEN', 'synthetic-unused-token')
})

afterEach(() => {
  expect(fetch).not.toHaveBeenCalled()
  expect(http.request).not.toHaveBeenCalled()
  expect(https.request).not.toHaveBeenCalled()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

describe.each(cases)('$name retirement notice', ({ name, register, title }) => {
  it('retains its registered name, exact template and Markdown MIME with retired discovery metadata', () => {
    const server = makeMockServer()
    register(server as never)
    const { template, metadata } = server.entry(name)
    expect(server.resource).toHaveBeenCalledTimes(1)
    expect(template.uriTemplate.toString()).toBe(`marsys://${name}/{chart_id}`)
    expect(template.listCallback).toBeUndefined()
    expect(metadata).toMatchObject({ title: `${title} (retired)`, mimeType: 'text/markdown' })
    expect(metadata.description).toMatch(/retired/i)
    expect(metadata.description).toContain('Compatibility notice only')
  })

  it('returns one explicit no-data compatibility notice at the original requested URI', async () => {
    const server = makeMockServer()
    register(server as never)
    const uri = new URL(`marsys://${name}/${CHART_ID}`)
    const { contents } = await server.entry(name).handler(uri)
    expect(contents).toHaveLength(1)
    expect(contents[0]).toMatchObject({ uri: uri.href, mimeType: 'text/markdown' })
    const text = contents[0].text
    expect(text).toContain(`# ${title} — retired`)
    expect(text).toContain('retired and unavailable')
    expect(text).toContain('compatibility notice only')
    expect(text).toContain('does not retrieve chart data')
    expect(text).not.toMatch(/not_built|trigger a build|build first|no ayanamshas built|all 5 ayanamshas are built|consensus is partially available|Bundle data not yet loaded/i)
    expect(text).not.toContain('| Ayanamsha |')
    expect(text).not.toContain('divergence_score=')
  })

  it('gives the same static notice for different chart identifiers without measuring their state', async () => {
    const server = makeMockServer()
    register(server as never)
    const handler = server.entry(name).handler
    const first = await handler(new URL(`marsys://${name}/${CHART_ID}`))
    const secondUri = new URL(`marsys://${name}/cccccccc-0000-0000-0000-000000000002`)
    const second = await handler(secondUri)
    expect(second.contents[0].uri).toBe(secondUri.href)
    expect(second.contents[0].text).toBe(first.contents[0].text)
  })

  it('keeps narrower guidance separate from the withdrawn legacy contract', async () => {
    const server = makeMockServer()
    register(server as never)
    const { contents } = await server.entry(name).handler(new URL(`marsys://${name}/${CHART_ID}`))
    const text = contents[0].text
    expect(text).toContain('## Limited alternatives')
    expect(text).toContain('`chart_snapshot`')
    if (name === 'chart-bundle') {
      expect(text).toContain('`marsys://chart-snapshot/{chart_id}`')
      expect(text).toContain('`query_chart_facts`')
      expect(text).toContain('current Panchang')
      expect(text).toContain('do not reproduce the retired five-frame bundle')
      expect(text).toContain('birth Panchanga')
      expect(text).toContain('numeric cross-ayanamsha divergence')
    } else {
      expect(text).toContain('chart-level readiness UI')
      expect(text).toContain('separately labelled identity fact cross-check')
      expect(text).toContain('does not measure per-ayanamsha build progress or consensus')
      expect(text).toContain('do not reproduce the retired status or consensus contract')
    }
  })

  it('lists the retired metadata and dispatches the unchanged URI through the actual SDK in memory', async () => {
    const server = new McpServer({ name: 'retirement-fixture', version: '1.0.0' })
    const client = new Client({ name: 'retirement-fixture-client', version: '1.0.0' })
    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair()
    register(server)
    try {
      await server.connect(serverTransport)
      await client.connect(clientTransport)
      const listed = await client.listResourceTemplates()
      expect(listed.resourceTemplates).toEqual([
        expect.objectContaining({ name, uriTemplate: `marsys://${name}/{chart_id}`, title: `${title} (retired)`, mimeType: 'text/markdown', description: expect.stringContaining('Compatibility notice only') }),
      ])
      const uri = `marsys://${name}/${CHART_ID}`
      const result = await client.readResource({ uri })
      expect(result.contents).toEqual([
        expect.objectContaining({ uri, mimeType: 'text/markdown', text: expect.stringContaining('retired and unavailable') }),
      ])
    } finally {
      await client.close()
      await server.close()
    }
  })
})
