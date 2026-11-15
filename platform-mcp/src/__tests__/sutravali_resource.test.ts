import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { registerSutravaliResources } from '../resources/sutravali_resource.js'

const principal = { user_uid: 'fixture-user', key_id: 'fixture-key', role: 'client' } as Principal
type Read = (uri: URL, vars: Record<string, string | string[]>) => Promise<{ contents: { uri: string; mimeType: string; text: string }[] }>
function callbacks() {
  const reads = new Map<string, Read>()
  const server = { resource: vi.fn((name: string, _template: unknown, read: Read) => { reads.set(name, read) }) }
  registerSutravaliResources(server as unknown as McpServer, principal)
  return reads
}
function success(rules: unknown[]) { return { ok: true, content: { is_error: false, content: { rules } } } }
let fetchMock: ReturnType<typeof vi.fn>
beforeEach(() => { fetchMock = vi.fn(async () => ({ ok: true, json: async () => success([]) })); vi.stubGlobal('fetch', fetchMock) })
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('Sutravali canonical resources', () => {
  it('uses the real registration principal and exact planet 500 request, preserving URI and empty success', async () => {
    const timeout = vi.spyOn(AbortSignal, 'timeout')
    const uri = new URL('marsys://resource/sutravali/all-by-planet/Saturn')
    const result = await callbacks().get('sutravali-by-planet')!(uri, { planet: ['Saturn', 'Moon'] })
    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toMatch(/\/api\/retrieval\/capability$/)
    expect(init.method).toBe('POST')
    expect(init.headers).toMatchObject({ 'Content-Type': 'application/json', 'X-MCP-User': principal.user_uid, 'X-MCP-Key-Id': principal.key_id })
    expect(init.headers).toHaveProperty('X-MCP-Internal-Token')
    expect(init.headers).not.toHaveProperty('Cookie')
    expect(JSON.parse(String(init.body))).toEqual({ uri: 'marsys://tool/L0/query_sutravali_rules_for_planet', args: { planet: 'Saturn', limit: 500 } })
    expect(timeout).toHaveBeenCalledWith(20_000)
    expect(result).toEqual({ contents: [{ uri: uri.href, mimeType: 'text/markdown', text: '# Sūtravali Rules — Planet: Saturn\n\nNo rules found for this query.' }] })
  })

  it.each(['02trailing', '2.9', ' 2', '+2'])('retains parseInt house spelling %j and raw display label', async (raw) => {
    const uri = new URL('marsys://resource/sutravali/all-by-house/2')
    const result = await callbacks().get('sutravali-by-house')!(uri, { n: [raw, '8'] })
    expect(JSON.parse(String(fetchMock.mock.calls[0]![1].body))).toEqual({ uri: 'marsys://tool/L0/query_sutravali_rules', args: { house: 2, limit: 500 } })
    expect(result.contents[0]!.text).toContain(`House: ${raw}`)
  })

  it.each(['1', '12'])('admits boundary house %s with the same 500-row request', async raw => {
    await callbacks().get('sutravali-by-house')!(new URL(`marsys://resource/sutravali/all-by-house/${raw}`), { n: raw })
    expect(JSON.parse(String(fetchMock.mock.calls[0]![1].body))).toEqual({ uri: 'marsys://tool/L0/query_sutravali_rules', args: { house: parseInt(raw, 10), limit: 500 } })
  })

  it.each(['0', '13', '-1', 'NaN', '', undefined])('rejects out-of-range house %j before the RPC', async (n) => {
    const result = await callbacks().get('sutravali-by-house')!(new URL('marsys://resource/sutravali/all-by-house/bad'), { n } as Record<string, string>)
    expect(fetchMock).not.toHaveBeenCalled()
    expect(result.contents[0]!.text).toContain('No data available')
    expect(result.contents[0]!.text).not.toContain('No rules found')
  })

  it('preserves all 500 rows, returned order, and exact Markdown formatter fields', async () => {
    const rows = Array.from({ length: 500 }, (_, i) => ({ rule_id: `fixture-${i}`, text_id: `text-${i}`, verse_ref: `${500-i}`, antecedent: { planet: 'Saturn' }, predicate: { house: 2 }, prediction: { result: 'fixture' }, confidence: i === 0 ? 0 : 0.5 }))
    fetchMock.mockResolvedValue({ ok: true, json: async () => success(rows) })
    const result = await callbacks().get('sutravali-by-house')!(new URL('marsys://resource/sutravali/all-by-house/2'), { n: '2' })
    const text = result.contents[0]!.text
    const expected = ['# Sūtravali Rules — House: 2', '**Count:** 500', '', ...rows.flatMap(row => [`## ${row.text_id} ${row.verse_ref}`, `**Antecedent:** ${JSON.stringify(row.antecedent)}`, `**Predicate:** ${JSON.stringify(row.predicate)}`, `**Prediction:** ${JSON.stringify(row.prediction)}`, `**Confidence:** ${row.confidence}`, ''])].join('\n')
    expect(text).toBe(expected)
  })

  it('retains rule-id prefix fallback without inventing absent fields', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => success([{ rule_id: '123456789-abcd', confidence: null }]) })
    const result = await callbacks().get('sutravali-by-planet')!(new URL('marsys://resource/sutravali/all-by-planet/Moon'), { planet: 'Moon' })
    expect(result.contents[0]!.text).toBe('# Sūtravali Rules — Planet: Moon\n**Count:** 1\n\n## 12345678\n')
  })

  it.each([
    { ok: false, error: 'fixture error' },
    { ok: true, content: { is_error: true, content: { rules: [] } } },
    { ok: true, content: { content: { rules: [] } } },
    { ok: true, content: { is_error: false, content: {} } },
    { ok: true, content: { is_error: false, content: { rules: [null] } } },
    { ok: true, content: { is_error: false, content: { rules: [[]] } } },
    { ok: true, content: { is_error: false, content: { rules: [1] } } },
    { ok: true, content: { is_error: false, content: { rules: 'bad' } } },
    null,
  ])('does not turn error/malformed envelopes into empty success: %j', async body => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => body })
    const result = await callbacks().get('sutravali-by-planet')!(new URL('marsys://resource/sutravali/all-by-planet/Sun'), { planet: 'Sun' })
    expect(result.contents[0]!.text).toContain('No data available')
    expect(result.contents[0]!.text).not.toContain('No rules found')
  })

  it.each(['http', 'transport', 'json'])('keeps %s failure distinct from successful empty', async kind => {
    if (kind === 'http') fetchMock.mockResolvedValue({ ok: false, status: 403, text: async () => 'denied' })
    if (kind === 'transport') fetchMock.mockRejectedValue(new Error('fixture transport'))
    if (kind === 'json') fetchMock.mockResolvedValue({ ok: true, json: async () => { throw new Error('fixture json') } })
    const result = await callbacks().get('sutravali-by-house')!(new URL('marsys://resource/sutravali/all-by-house/1'), { n: '1' })
    expect(result.contents[0]!.text).toContain('No data available')
    expect(result.contents[0]!.text).not.toContain('No rules found')
  })
})
