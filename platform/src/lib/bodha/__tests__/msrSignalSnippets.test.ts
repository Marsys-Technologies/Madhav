import { beforeEach, describe, expect, it, vi } from 'vitest'
const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('server-only', () => ({}))
import { fetchMsrSnippets } from '../msrSignalSnippets'

beforeEach(() => { queryMock.mockReset() })

describe('legacy Consult MSR snippet read owner', () => {
  it('does not query for an empty signal list', async () => {
    expect(await fetchMsrSnippets([])).toEqual(new Map())
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('preserves the signal-ID-only SQL, alias columns, placeholders and original array identity', async () => {
    const ids = ['signal-b', 'signal-a', 'signal-b']
    queryMock.mockResolvedValue({ rows: [
      { signal_id: 'signal-b', name: 'Headline', description: 'Summary' },
      { signal_id: 'signal-a', name: null, description: 'Description only' },
    ] })
    expect(await fetchMsrSnippets(ids)).toEqual(new Map([
      ['signal-b', 'Headline — Summary'], ['signal-a', 'Description only'],
    ]))
    expect(queryMock).toHaveBeenCalledExactlyOnceWith(
      'SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signals WHERE signal_id::text IN ($1, $2, $3)', ids,
    )
    expect(queryMock.mock.calls[0][1]).toBe(ids)
  })

  it.each([
    { name: 'Headline', description: null, expected: 'Headline' },
    { name: '', description: 'Summary', expected: 'Summary' },
    { name: null, description: null, expected: '' },
  ])('retains nullable snippet projection: $expected', async row => {
    queryMock.mockResolvedValue({ rows: [{ signal_id: 'present', name: row.name, description: row.description }] })
    const snippets = await fetchMsrSnippets(['present', 'absent'])
    expect(snippets.get('present')).toBe(row.expected)
    expect(snippets.has('absent')).toBe(false)
  })

  it.each([295, 296])('preserves the existing %i-character truncation boundary', async size => {
    queryMock.mockResolvedValue({ rows: [{ signal_id: 'signal', name: 'x'.repeat(size), description: null }] })
    const result = (await fetchMsrSnippets(['signal'])).get('signal')
    expect(result).toBe(size === 295 ? 'x'.repeat(295) : 'x'.repeat(294) + '…')
  })

  it('preserves last-row Map behavior without inventing missing IDs', async () => {
    queryMock.mockResolvedValue({ rows: [
      { signal_id: 'same', name: 'first', description: null },
      { signal_id: 'same', name: 'last', description: null },
    ] })
    expect(await fetchMsrSnippets(['same', 'absent'])).toEqual(new Map([['same', 'last']]))
  })

  it.each(['rejection', 'synchronous throw'])('retains catch-to-empty-Map for a query %s', async kind => {
    if (kind === 'rejection') queryMock.mockRejectedValue(new Error('synthetic unavailable'))
    else queryMock.mockImplementation(() => { throw new Error('synthetic unavailable') })
    expect(await fetchMsrSnippets(['signal'])).toEqual(new Map())
    expect(queryMock).toHaveBeenCalledOnce()
  })
})
