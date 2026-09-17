import { beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock, embedTextMock } = vi.hoisted(() => ({ queryMock: vi.fn(), embedTextMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('@/lib/embeddings/embedText', () => ({ embedText: embedTextMock }))

import { queryClassicalTextsCapability } from '../query_classical_texts'

const corpusRows = Array.from({ length: 5 }, (_, index) => ({
  id: `row-${index + 1}`,
  text_id: 'BPHS',
  chunk_id: `chunk-${index + 1}`,
  verse_ref: `1.${index + 1}`,
  chapter: 1,
  verse_start: index + 1,
  content_en: `verse ${index + 1}`,
  content_sa: null,
  content_summary: null,
  source_citation: 'BPHS',
  tradition_school: null,
  topics: [],
  vector_score: null,
  keyword_score: 0.5,
}))

describe('query_classical_texts pagination', () => {
  beforeEach(() => {
    queryMock.mockReset()
    embedTextMock.mockReset()
    embedTextMock.mockResolvedValue(null)
    queryMock.mockImplementation((_sql: string, params: unknown[]) => {
      const limit = params.at(-2) as number
      const offset = params.at(-1) as number
      return Promise.resolve({ rows: corpusRows.slice(offset, offset + limit) })
    })
  })

  it.each([
    { label: 'first', offset: 0, expected: ['row-1', 'row-2'], more: true, next: 2 },
    { label: 'middle', offset: 2, expected: ['row-3', 'row-4'], more: true, next: 4 },
    { label: 'final', offset: 4, expected: ['row-5'], more: false, next: null },
    { label: 'empty', offset: 5, expected: [], more: false, next: null },
  ])('returns the truthful $label hybrid page', async ({ offset, expected, more, next }) => {
    const result = await queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 2, offset }, undefined)
    const content = result.content as Record<string, unknown>
    expect((content['citations'] as Array<{ chunk_id: string }>).map((row) => row.chunk_id.replace('chunk', 'row'))).toEqual(expected)
    expect(content['more_available']).toBe(more)
    expect(content['next_offset']).toBe(next)
    expect(content['total_scope']).toBe('page')
  })

  it.each([
    { label: 'first', offset: 0, expected: ['row-1', 'row-2'], more: true, next: 2 },
    { label: 'middle', offset: 2, expected: ['row-3', 'row-4'], more: true, next: 4 },
    { label: 'final', offset: 4, expected: ['row-5'], more: false, next: null },
    { label: 'empty', offset: 5, expected: [], more: false, next: null },
  ])('returns the truthful $label legacy page', async ({ offset, expected, more, next }) => {
    const result = await queryClassicalTextsCapability.handler({ limit: 2, offset }, undefined)
    const content = result.content as Record<string, unknown>
    expect((content['rows'] as Array<{ id: string }>).map((row) => row.id)).toEqual(expected)
    expect(content['more_available']).toBe(more)
    expect(content['next_offset']).toBe(next)
    expect(content['total_scope']).toBe('page')
  })

  it('normalizes fractional, invalid, and nonfinite hybrid and legacy pagination before SQL', async () => {
    await queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 0.5, offset: 1.9 }, undefined)
    let params = queryMock.mock.calls[0]?.[1] as unknown[]
    expect(params.slice(-2)).toEqual([6, 1])

    queryMock.mockClear()
    await queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 'invalid', offset: 'invalid' }, undefined)
    params = queryMock.mock.calls[0]?.[1] as unknown[]
    expect(params.slice(-2)).toEqual([6, 0])

    queryMock.mockClear()
    await queryClassicalTextsCapability.handler({ keyword: 'dasha', limit: Number.POSITIVE_INFINITY, offset: Number.POSITIVE_INFINITY }, undefined)
    params = queryMock.mock.calls[0]?.[1] as unknown[]
    expect(params.slice(0, 2)).toEqual([21, 0])
  })

  it('uses stable unique SQL ordering for hybrid and legacy lists', async () => {
    await queryClassicalTextsCapability.handler({ query_text: 'dasha', top_k: 2 }, undefined)
    expect(String(queryMock.mock.calls[0]?.[0])).toContain('chunk_id ASC,\n          id ASC')

    queryMock.mockClear()
    await queryClassicalTextsCapability.handler({ limit: 2 }, undefined)
    expect(String(queryMock.mock.calls[0]?.[0])).toContain('chunk_id ASC, id ASC LIMIT $1 OFFSET $2')
  })
})
