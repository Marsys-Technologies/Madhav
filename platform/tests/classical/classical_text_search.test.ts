import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

// Shared state that the mock factory can close over
let _mockToken = 'mock-token'
let _mockVertexResponse: unknown = null

const mockFetch = vi.fn()
global.fetch = mockFetch

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => mockQuery(...args),
}))

vi.mock('google-auth-library', () => ({
  GoogleAuth: class {
    async getClient() {
      return {
        getAccessToken: async () => ({ token: _mockToken }),
      }
    }
  },
}))

const MOCK_EMBEDDING = Array.from({ length: 768 }, (_, i) => i * 0.001)

function makeDbRow(overrides: Record<string, unknown> = {}) {
  return {
    chunk_id: 'chunk-uuid-1',
    text_key: 'bphs',
    title: 'Brihat Parashara Hora Shastra',
    author: 'Parashara',
    tradition: 'parashari',
    chapter: '7',
    verse_range: '7.1-7.5',
    content: 'Rahu in the 7th house causes disruption in partnerships.',
    attribution_baseline_confidence: 0.85,
    distance: 0.12,
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  _mockToken = 'mock-token'
  process.env.GCP_PROJECT = 'test-project'
  process.env.VERTEX_AI_LOCATION = 'us-central1'

  _mockVertexResponse = { predictions: [{ embeddings: { values: MOCK_EMBEDDING } }] }
  mockFetch.mockImplementation(async () => ({
    ok: true,
    json: async () => _mockVertexResponse,
    text: async () => JSON.stringify(_mockVertexResponse),
  }))
  mockQuery.mockResolvedValue({ rows: [makeDbRow()], rowCount: 1 })
})

import { classical_text_search } from '@/lib/tools/classical_text_search'

describe('classical_text_search', () => {
  it('returns results with similarity = 1 - distance', async () => {
    const result = await classical_text_search({ query: 'Rahu in 7th house' })
    expect(result.results).toHaveLength(1)
    expect(result.results[0].similarity).toBeCloseTo(1 - 0.12, 5)
    expect(result.results[0].text_key).toBe('bphs')
  })

  it('returns query_embedding_dim = 768', async () => {
    const result = await classical_text_search({ query: 'saturn dasha' })
    expect(result.query_embedding_dim).toBe(768)
  })

  it('passes school filter into SQL when schools provided', async () => {
    await classical_text_search({ query: 'saturn', schools: ['parashari', 'jaimini'] })
    const [sql, params] = mockQuery.mock.calls[0]
    expect(sql).toContain('ct.school = ANY')
    expect(params).toContainEqual(['parashari', 'jaimini'])
  })

  it('passes tier_max filter into SQL when provided', async () => {
    await classical_text_search({ query: 'saturn', tier_max: 2 })
    const [sql, params] = mockQuery.mock.calls[0]
    expect(sql).toContain('ct.tier <=')
    expect(params).toContain(2)
  })

  it('respects limit cap at 20', async () => {
    await classical_text_search({ query: 'saturn', limit: 100 })
    const [, params] = mockQuery.mock.calls[0]
    expect(params[1]).toBe(20)
  })

  it('uses text-embedding-004 model in Vertex AI endpoint', async () => {
    await classical_text_search({ query: 'moon placement' })
    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('text-embedding-004')
  })

  it('sends RETRIEVAL_QUERY task_type to Vertex AI', async () => {
    await classical_text_search({ query: 'moon placement' })
    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body.instances[0].task_type).toBe('RETRIEVAL_QUERY')
  })

  it('throws when Vertex AI returns wrong embedding dimension', async () => {
    _mockVertexResponse = { predictions: [{ embeddings: { values: [0.1, 0.2] } }] }
    await expect(
      classical_text_search({ query: 'test' })
    ).rejects.toThrow(/unexpected embedding shape/)
  })

  it('throws when GCP_PROJECT env var is not set', async () => {
    delete process.env.GCP_PROJECT
    await expect(
      classical_text_search({ query: 'test' })
    ).rejects.toThrow(/GCP_PROJECT/)
  })

  it('throws when Vertex AI returns non-ok response', async () => {
    mockFetch.mockImplementationOnce(async () => ({
      ok: false,
      status: 500,
      text: async () => 'Internal Server Error',
    }))
    await expect(
      classical_text_search({ query: 'test' })
    ).rejects.toThrow(/500/)
  })
})
