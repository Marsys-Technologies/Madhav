import { readFileSync } from 'node:fs'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryFormulaConstantsCapability } from '../query_formula_constants'

describe('queryFormulaConstantsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 18 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ constant_id: 'c1', class: 'classical' }] })
    const result = await queryFormulaConstantsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM brahma_formula_constants')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('class filter is exact and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryFormulaConstantsCapability.handler({ class: 'native_judgment' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('class = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual(['native_judgment'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryFormulaConstantsCapability.handler({ constant_id: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('constant_id=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryFormulaConstantsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryFormulaConstantsCapability.scope).toBe('global')
    expect(queryFormulaConstantsCapability.required_inputs).toEqual([])
  })

  it.each([{"args": {}, "params": [], "filters": {"constant_id": null, "class": null}, "where": "1=1"}, {"args": {"constant_id": "id", "class": "engineering"}, "params": ["id", "engineering"], "filters": {"constant_id": "id", "class": "engineering"}, "where": "1=1 AND constant_id = $1 AND class = $2"}, {"args": {"constant_id": 0, "class": false}, "params": [], "filters": {"constant_id": null, "class": null}, "where": "1=1"}, {"args": {"constant_id": 42, "class": true}, "params": ["42", "true"], "filters": {"constant_id": "42", "class": "true"}, "where": "1=1 AND constant_id = $1 AND class = $2"}, {"args": {"constant_id": [], "class": ["a", "b"]}, "params": ["a,b"], "filters": {"constant_id": "", "class": "a,b"}, "where": "1=1 AND class = $1"}, {"args": {"constant_id": "id' OR 1=1 --", "class": ""}, "params": ["id' OR 1=1 --"], "filters": {"constant_id": "id' OR 1=1 --", "class": null}, "where": "1=1 AND constant_id = $1"}, {"args": {"constant_id": null, "class": null}, "params": [], "filters": {"constant_id": null, "class": null}, "where": "1=1"}])('preserves exact SQL/bind/filter semantics for $args', async ({ args, params, filters, where }) => {
    const rows = Object.freeze([{ synthetic: 'reference-row' }])
    mockQuery.mockResolvedValueOnce({ rows })
    const result = await queryFormulaConstantsCapability.handler(args, undefined)
    expect(mockQuery.mock.calls).toEqual([[`
      SELECT constant_id, value_jsonb, class, consumer_assets, citation_or_ratification,
             calibratable, bounds, version
      FROM brahma_formula_constants
      WHERE ${where}
      ORDER BY constant_id`, params]])
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
    const result = await queryFormulaConstantsCapability.handler({}, undefined)
    expect((result.content as Record<string, unknown>).rows).toBe(rows)
    expect(reads).toBe(3)
  })

  it('keeps argument-coercion failure outside the DB-error envelope', async () => {
    const failure = new Error('synthetic coercion')
    const value = { toString() { throw failure } }
    await expect(queryFormulaConstantsCapability.handler({ constant_id: value }, undefined)).rejects.toBe(failure)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('preserves the caught DB error string without wrapping', async () => {
    const failure = { toString: () => 'synthetic DB failure' }
    mockQuery.mockRejectedValueOnce(failure)
    await expect(queryFormulaConstantsCapability.handler({}, undefined)).resolves.toEqual({
      content: { error: 'synthetic DB failure' }, is_error: true,
    })
  })

  it('keeps the reference SQL in its Brahmagyan owner', () => {
    const facade = readFileSync(new URL('../query_formula_constants.ts', import.meta.url), 'utf8')
    expect(facade).not.toContain('@/lib/db/client')
    expect(facade).not.toContain('FROM brahma_formula_constants')
    expect(facade).toContain('queryFormulaConstantsReference')
  })
})
