import { readFileSync } from 'node:fs'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryVicharaConstantsCapability } from '../query_vichara_constants'

describe('queryVicharaConstantsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 7 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ constant_key: 'ratification_step' }] })
    const result = await queryVicharaConstantsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM brahma_vichara_constants')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('constant_key filter is exact and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryVicharaConstantsCapability.handler({ constant_key: 'ratification_clamp' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('constant_key = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual(['ratification_clamp'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryVicharaConstantsCapability.handler({ constant_key: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('constant_key=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryVicharaConstantsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryVicharaConstantsCapability.scope).toBe('global')
    expect(queryVicharaConstantsCapability.required_inputs).toEqual([])
  })

  it.each([{"args": {}, "params": [], "filters": {"constant_key": null}, "where": "1=1"}, {"args": {"constant_key": 0}, "params": [], "filters": {"constant_key": null}, "where": "1=1"}, {"args": {"constant_key": false}, "params": [], "filters": {"constant_key": null}, "where": "1=1"}, {"args": {"constant_key": []}, "params": [], "filters": {"constant_key": ""}, "where": "1=1"}, {"args": {"constant_key": ["a", "b"]}, "params": ["a,b"], "filters": {"constant_key": "a,b"}, "where": "1=1 AND constant_key = $1"}, {"args": {"constant_key": "k' OR 1=1 --"}, "params": ["k' OR 1=1 --"], "filters": {"constant_key": "k' OR 1=1 --"}, "where": "1=1 AND constant_key = $1"}, {"args": {"constant_key": true}, "params": ["true"], "filters": {"constant_key": "true"}, "where": "1=1 AND constant_key = $1"}])('preserves exact SQL/bind/filter semantics for $args', async ({ args, params, filters, where }) => {
    const rows = Object.freeze([{ synthetic: 'reference-row' }])
    mockQuery.mockResolvedValueOnce({ rows })
    const result = await queryVicharaConstantsCapability.handler(args, undefined)
    expect(mockQuery.mock.calls).toEqual([[`
      SELECT constant_key, value_jsonb, citation, version, updated_at
      FROM brahma_vichara_constants
      WHERE ${where}
      ORDER BY constant_key`, params]])
    const content = result.content as Record<string, unknown>
    expect(content.rows).toBe(rows)
    expect(content.count).toBe(1)
    expect(content.filters).toEqual(filters)
    expect(content).not.toHaveProperty('empty_reason')
    expect(result.is_error).toBe(false)
  })

  it('preserves query-result row access and array identity', async () => {
    const rows = [{ synthetic: 'opaque-row' }]
    let reads = 0
    mockQuery.mockResolvedValueOnce({ get rows() { reads += 1; return rows } })
    const result = await queryVicharaConstantsCapability.handler({}, undefined)
    expect((result.content as Record<string, unknown>).rows).toBe(rows)
    expect(reads).toBe(3)
  })

  it('keeps argument-coercion failure outside the DB-error envelope', async () => {
    const failure = new Error('synthetic coercion')
    const value = { toString() { throw failure } }
    await expect(queryVicharaConstantsCapability.handler({ constant_key: value }, undefined)).rejects.toBe(failure)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('preserves the caught DB error string without wrapping', async () => {
    const failure = { toString: () => 'synthetic DB failure' }
    mockQuery.mockRejectedValueOnce(failure)
    await expect(queryVicharaConstantsCapability.handler({}, undefined)).resolves.toEqual({
      content: { error: 'synthetic DB failure' }, is_error: true,
    })
  })

  it('keeps the reference SQL in its Brahmagyan owner', () => {
    const facade = readFileSync(new URL('../query_vichara_constants.ts', import.meta.url), 'utf8')
    expect(facade).not.toContain('@/lib/db/client')
    expect(facade).not.toContain('FROM brahma_vichara_constants')
    expect(facade).toContain('queryVicharaConstantsReference')
  })
})
