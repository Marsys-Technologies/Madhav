import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/tools/classical_text_search', () => ({ classical_text_search: vi.fn() }))

import { query } from '@/lib/db/client'
import * as reads from '../classical_text_reads'
import * as tools from '@/lib/tools/classical_text_tools'
import { classical_text_search } from '@/lib/tools/classical_text_search'

const mockQuery = vi.mocked(query)
const mockSearch = vi.mocked(classical_text_search)

beforeEach(() => {
  mockQuery.mockReset()
  mockSearch.mockReset()
})

describe('Brahmagyan classical-reference read boundary', () => {
  it('preserves the legacy facade function identities', () => {
    expect(tools.read_chapter).toBe(reads.read_chapter)
    expect(tools.list_classical_texts).toBe(reads.list_classical_texts)
    expect(tools.read_classical_text_by_ref).toBe(reads.read_classical_text_by_ref)
  })

  it('retains chapter binds, row identity and null row-count fallback', async () => {
    const rows = [{ chunk_id: 'fixture-chunk', verse_ref: null, content_en: 'synthetic', content_sa: null }]
    mockQuery.mockResolvedValue({ rows, rowCount: null } as never)
    const result = await tools.read_chapter({ text_id: 'fixture-α', chapter: 3 })
    expect(mockQuery).toHaveBeenCalledTimes(1)
    expect(mockQuery.mock.calls[0]![1]).toEqual(['fixture-α', 3, 50])
    expect(mockQuery.mock.calls[0]![0]).toContain('ORDER BY verse_start, chunk_id')
    expect(result.chunks).toBe(rows)
    expect(result).toEqual({ text_id: 'fixture-α', chapter: 3, chunks: rows, total: 0 })
  })

  it.each([[250, 100], [-2, -2], [Number.NaN, Number.NaN]])('retains the existing chapter limit mapping for %s', async (limit, expected) => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 } as never)
    await reads.read_chapter({ text_id: 'fixture-text', chapter: 1, limit })
    expect(mockQuery.mock.calls[0]![1]).toEqual(['fixture-text', 1, expected])
  })

  it('preserves list order, nullable fields and existing count parsing', async () => {
    mockQuery.mockResolvedValue({
      rows: [
        { text_id: 'fixture-b', title_en: 'Synthetic B', author: null, school: null, tradition: null, chunk_count: '12', source_url: null, license: null },
        { text_id: 'fixture-a', title_en: 'Synthetic A', author: 'fixture-author', school: 'fixture-school', tradition: 'fixture-tradition', chunk_count: null, source_url: 'fixture-source', license: 'fixture-license' },
      ],
      rowCount: 2,
    } as never)
    expect(await tools.list_classical_texts()).toEqual({
      texts: [
        { text_id: 'fixture-b', title: 'Synthetic B', author: null, school: null, tradition: null, chunk_count: 12, source_url: null, license: null },
        { text_id: 'fixture-a', title: 'Synthetic A', author: 'fixture-author', school: 'fixture-school', tradition: 'fixture-tradition', chunk_count: 0, source_url: 'fixture-source', license: 'fixture-license' },
      ],
      total: 2,
    })
    expect(mockQuery.mock.calls[0]).toHaveLength(1)
    expect(mockQuery.mock.calls[0]![0]).toContain('ORDER BY t.text_id')
  })

  it('retains the complete missing-reference shape', async () => {
    mockQuery.mockResolvedValue({ rows: [] } as never)
    expect(await tools.read_classical_text_by_ref({ text_id: 'fixture-text', verse_ref: 'fixture-ref' })).toEqual({
      chunk_id: null, text_id: 'fixture-text', verse_ref: 'fixture-ref', content_en: null,
      content_sa: null, chapter: null, source_citation: null, found: false,
    })
    expect(mockQuery.mock.calls[0]![1]).toEqual(['fixture-text', 'fixture-ref'])
  })

  it('returns only the first matched reference without a new fallback or coercion', async () => {
    const row = { chunk_id: 'fixture-chunk', text_id: 'stored-text', verse_ref: 'stored-ref', content_en: 'synthetic', content_sa: null, chapter: 4, source_citation: null }
    mockQuery.mockResolvedValue({ rows: [row, { ...row, chunk_id: 'ignored-row' }] } as never)
    expect(await reads.read_classical_text_by_ref({ text_id: 'fixture-text', verse_ref: 'fixture-ref' })).toEqual({ ...row, found: true })
  })

  it('preserves school mapping order and duplicates while excluding empty values', async () => {
    mockQuery.mockResolvedValue({ rows: [{ tradition_school: 'fixture-b' }, { tradition_school: '' }, { tradition_school: 'fixture-b' }, { tradition_school: 'fixture-a' }] } as never)
    expect(await reads.readClassicalTextSchools(['fixture-α', 'fixture-b'])).toEqual(['fixture-b', 'fixture-b', 'fixture-a'])
    expect(mockQuery.mock.calls[0]![1]).toEqual([['fixture-α', 'fixture-b']])
  })

  it('does not read schools when no text filter is supplied', async () => {
    const results = [{ text_key: 'fixture-other' }]
    mockSearch.mockResolvedValue({ results, total: 1 } as never)
    expect(await tools.find_verses_about({ topic: 'fixture-topic' })).toEqual({ results, total: 1, topic: 'fixture-topic' })
    expect(mockQuery).not.toHaveBeenCalled()
    expect(mockSearch).toHaveBeenCalledWith({ query: 'fixture-topic', schools: undefined, limit: 10 })
  })

  it('reads schools before search and preserves text-id postfiltering', async () => {
    const events: string[] = []
    mockQuery.mockImplementation(async () => {
      events.push('schools')
      return { rows: [{ tradition_school: 'fixture-school' }] } as never
    })
    mockSearch.mockImplementation(async () => {
      events.push('search')
      return { results: [{ text_key: 'fixture-text' }, { text_key: 'other-text' }], total: 2 } as never
    })
    expect(await tools.find_verses_about({ topic: 'fixture-topic', text_ids: ['fixture-text'], top_k: 7 })).toEqual({ results: [{ text_key: 'fixture-text' }], total: 1, topic: 'fixture-topic' })
    expect(events).toEqual(['schools', 'search'])
    expect(mockSearch).toHaveBeenCalledWith({ query: 'fixture-topic', schools: ['fixture-school'], limit: 7 })
  })

  it('keeps an empty school mapping undefined rather than inventing a filter', async () => {
    mockQuery.mockResolvedValue({ rows: [] } as never)
    mockSearch.mockResolvedValue({ results: [], total: 0 } as never)
    await tools.find_verses_about({ topic: 'fixture-topic', text_ids: ['fixture-text'] })
    expect(mockSearch).toHaveBeenCalledWith({ query: 'fixture-topic', schools: undefined, limit: 10 })
  })

  it.each([new Error('synthetic failure'), undefined, null, 0, 'synthetic rejection'])('propagates the original query rejection without wrapping: %s', async failure => {
    mockQuery.mockRejectedValue(failure)
    await expect(reads.read_chapter({ text_id: 'fixture-text', chapter: 1 })).rejects.toBe(failure)
    mockQuery.mockRejectedValue(failure)
    await expect(reads.list_classical_texts()).rejects.toBe(failure)
    mockQuery.mockRejectedValue(failure)
    await expect(reads.read_classical_text_by_ref({ text_id: 'fixture-text', verse_ref: 'fixture-ref' })).rejects.toBe(failure)
    mockQuery.mockRejectedValue(failure)
    await expect(tools.find_verses_about({ topic: 'fixture-topic', text_ids: ['fixture-text'] })).rejects.toBe(failure)
    expect(mockSearch).not.toHaveBeenCalled()
  })
})
