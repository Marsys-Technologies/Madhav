import { NextRequest } from 'next/server'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { GET } from '../route'

const { query } = vi.hoisted(() => ({ query: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query }))

const token = 'fixture-service-token'
const edgeKey = "Mixed text/Ω + ? % '"
const fixture = {
  text_key: edgeKey,
  title: 'Synthetic summary',
  author: null,
  tradition: 'fixture-tradition',
  school: 'fixture-school',
  tier: 2,
  language_original: 'fixture-language',
  translation_author: null,
  chunk_count: 0,
  attribution_baseline_confidence: 0.625,
}

function request(textKey: string, headers: HeadersInit = { 'x-mcp-internal-token': token }) {
  return new NextRequest(`https://fixture.invalid/api/classical-texts/${encodeURIComponent(textKey)}/summary`, { headers })
}

function assertExactQuery(textKey: string) {
  expect(query).toHaveBeenCalledTimes(1)
  const [statement, args] = query.mock.calls[0]
  expect(statement.replace(/\s+/g, ' ').trim()).toBe(
    'SELECT text_key, title, author, tradition, school, tier, language_original, ' +
    'translation_author, chunk_count, attribution_baseline_confidence FROM classical_texts WHERE text_key = $1 LIMIT 1',
  )
  expect(args).toEqual([textKey])
}

beforeEach(() => {
  query.mockReset()
  vi.stubEnv('MCP_INTERNAL_TOKEN', token)
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.restoreAllMocks()
})

describe('GET classical-text summary', () => {
  it.each([
    ['missing internal token', {}],
    ['wrong internal token', { 'x-mcp-internal-token': 'wrong-service-token' }],
    ['unsupported bearer only', { authorization: `Bearer ${token}` }],
  ] as const)('refuses %s before resolving route params or issuing SQL', async (_name, headers) => {
    const then = vi.fn((resolve: (value: { text_key: string }) => void) => resolve({ text_key: edgeKey }))
    const params = { then } as unknown as Promise<{ text_key: string }>
    const response = await GET(request(edgeKey, headers), { params })
    expect(response.status).toBe(403)
    expect(await response.text()).toBe('{"error":"forbidden"}')
    expect(then).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
  })

  it('fails closed when the service token is unconfigured', async () => {
    vi.stubEnv('MCP_INTERNAL_TOKEN', undefined)
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const then = vi.fn((resolve: (value: { text_key: string }) => void) => resolve({ text_key: edgeKey }))
    const params = { then } as unknown as Promise<{ text_key: string }>
    const response = await GET(request(edgeKey), { params })
    expect(response.status).toBe(403)
    expect(await response.text()).toBe('{"error":"forbidden"}')
    expect(then).not.toHaveBeenCalled()
    expect(query).not.toHaveBeenCalled()
  })

  it('binds an opaque text key once and returns the existing projected row bytes', async () => {
    query.mockResolvedValueOnce({ rows: [fixture] })
    const response = await GET(request(edgeKey), { params: Promise.resolve({ text_key: edgeKey }) })
    expect(response.status).toBe(200)
    expect(await response.text()).toBe(JSON.stringify(fixture))
    assertExactQuery(edgeKey)
  })

  it('returns the existing not_found body for a missing row', async () => {
    const missing = 'fixture-missing'
    query.mockResolvedValueOnce({ rows: [] })
    const response = await GET(request(missing), { params: Promise.resolve({ text_key: missing }) })
    expect(response.status).toBe(404)
    expect(await response.text()).toBe('{"error":"not_found"}')
    assertExactQuery(missing)
  })

  it('leaves database failures to the existing route error handling', async () => {
    const error = new Error('Synthetic query failure')
    query.mockRejectedValueOnce(error)
    await expect(GET(request(edgeKey), { params: Promise.resolve({ text_key: edgeKey }) })).rejects.toBe(error)
    assertExactQuery(edgeKey)
  })
})
