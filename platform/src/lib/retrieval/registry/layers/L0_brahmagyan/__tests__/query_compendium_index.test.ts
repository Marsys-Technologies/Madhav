import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryCompendiumIndexCapability } from '../query_compendium_index'

describe('queryCompendiumIndexCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries with default bound (100) and returns total', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ total: 9538 }] })
      .mockResolvedValueOnce({ rows: [{ index_id: 1, text_id: 'bphs' }] })
    const result = await queryCompendiumIndexCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['total']).toBe(9538)
    const sql = mockQuery.mock.calls[1][0] as string
    expect(sql).toContain('FROM brahma_compendium_index')
    expect(sql).toContain('LIMIT $1')
  })

  it('text_id + chapter_num filters are param-bound', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ total: 0 }] })
      .mockResolvedValueOnce({ rows: [] })
    await queryCompendiumIndexCapability.handler({ text_id: 'bphs', chapter_num: 27 }, undefined)
    const sql = mockQuery.mock.calls[1][0] as string
    const params = mockQuery.mock.calls[1][1] as unknown[]
    expect(sql).toContain('text_id = $1')
    expect(sql).toContain('chapter_num = $2')
    expect(params[0]).toBe('bphs')
    expect(params[1]).toBe(27)
  })

  it('limit is clamped to MAX_LIMIT (100)', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ total: 0 }] })
      .mockResolvedValueOnce({ rows: [] })
    await queryCompendiumIndexCapability.handler({ limit: 9999 }, undefined)
    const params = mockQuery.mock.calls[1][1] as unknown[]
    expect(params[params.length - 1]).toBe(100)
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ total: 0 }] })
      .mockResolvedValueOnce({ rows: [] })
    const result = await queryCompendiumIndexCapability.handler({ text_id: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('text_id=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryCompendiumIndexCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryCompendiumIndexCapability.scope).toBe('global')
    expect(queryCompendiumIndexCapability.required_inputs).toEqual([])
  })
})
