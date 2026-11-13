import { readFileSync } from 'node:fs'
import ts from 'typescript'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryTransitEngineCapability } from '../query_transit_engine'

describe('queryTransitEngineCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 9 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ graha: 'moon', avg_daily_motion_deg: 13.176 }] })
    const result = await queryTransitEngineCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_transit_engine')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('graha filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryTransitEngineCapability.handler({ graha: 'Rahu' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('LOWER(graha) = LOWER($1)')
    expect(mockQuery.mock.calls[0][1]).toEqual(['Rahu'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryTransitEngineCapability.handler({ graha: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('graha=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryTransitEngineCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryTransitEngineCapability.scope).toBe('global')
    expect(queryTransitEngineCapability.required_inputs).toEqual([])
  })
})


describe('reference read characterization', () => {
  beforeEach(() => { mockQuery.mockReset() })
  it.each([["absent", {}, {"graha": null}, [], []], ["null", {"graha": null}, {"graha": null}, [], []], ["empty", {"graha": ""}, {"graha": null}, [], []], ["false", {"graha": false}, {"graha": null}, [], []], ["zero", {"graha": 0}, {"graha": null}, [], []], ["empty-array", {"graha": []}, {"graha": ""}, [], []], ["graha", {"graha": "Rahu"}, {"graha": "Rahu"}, ["Rahu"], ["LOWER(graha) = LOWER($1)"]], ["whitespace", {"graha": " Moon "}, {"graha": " Moon "}, [" Moon "], ["LOWER(graha) = LOWER($1)"]], ["numeric", {"graha": 2}, {"graha": "2"}, ["2"], ["LOWER(graha) = LOWER($1)"]]])('preserves SQL, binds and normalized filters: %s', async (_name, args, filters, params, clauses) => {
    const rows = [{ synthetic_marker: 'reference-row' }]
    mockQuery.mockResolvedValueOnce({ rows })
    const result = await queryTransitEngineCapability.handler(args as Record<string, unknown>, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toBe(rows)
    expect(content['filters']).toEqual(filters)
    expect(mockQuery.mock.calls[0]).toEqual(["\n      SELECT graha, avg_daily_motion_deg, zodiac_period_days, sign_residence_days, classical_citation\n      FROM bg_transit_engine\n      WHERE ${where}\n      ORDER BY graha".replace('${where}', ['1=1', ...(clauses as string[])].join(' AND ')), params])
  })
  it.each(['sync', 'rejection'])('preserves thrown error formatting: %s', async mode => {
    const error = { toString: vi.fn(() => 'synthetic-reference-failure') }
    if (mode === 'sync') mockQuery.mockImplementationOnce(() => { throw error })
    else mockQuery.mockRejectedValueOnce(error)
    expect(await queryTransitEngineCapability.handler({}, undefined)).toEqual({ content: { error: 'synthetic-reference-failure' }, is_error: true })
    expect(error.toString).toHaveBeenCalledTimes(1)
  })
  it('keeps argument coercion failure outside the query catch', async () => {
    const marker = new Error('synthetic-coercion')
    await expect(queryTransitEngineCapability.handler({ "graha": { valueOf() { throw marker }, toString() { throw marker } } }, undefined)).rejects.toBe(marker)
    expect(mockQuery).not.toHaveBeenCalled()
  })
  it('keeps concurrent results bound to their own calls', async () => {
    let resolveFirst!: (value: unknown) => void
    let resolveSecond!: (value: unknown) => void
    mockQuery.mockImplementationOnce(() => new Promise(resolve => { resolveFirst = resolve }))
    mockQuery.mockImplementationOnce(() => new Promise(resolve => { resolveSecond = resolve }))
    const first = queryTransitEngineCapability.handler({}, undefined)
    const second = queryTransitEngineCapability.handler({}, undefined)
    const rowsFirst = [{ synthetic_marker: 'first' }], rowsSecond = [{ synthetic_marker: 'second' }]
    resolveSecond({ rows: rowsSecond }); resolveFirst({ rows: rowsFirst })
    expect(((await first).content as Record<string, unknown>)['rows']).toBe(rowsFirst)
    expect(((await second).content as Record<string, unknown>)['rows']).toBe(rowsSecond)
    expect(mockQuery).toHaveBeenCalledTimes(2)
  })
})

it('keeps serving SQL at the typed Brahmagyan owner rather than the descriptor', () => {
  const source = readFileSync(new URL('../query_transit_engine.ts', import.meta.url), 'utf8')
  const file = ts.createSourceFile('query_transit_engine.ts', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
  const rawAdapterImports = file.statements.filter((node) => ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier) && node.moduleSpecifier.text === '@/lib/db/client')
  expect(rawAdapterImports).toEqual([])
  const methods: ts.MethodDeclaration[] = []
  const visit = (node: ts.Node) => {
    if (ts.isMethodDeclaration(node) && node.name.getText(file) === 'handler') methods.push(node)
    ts.forEachChild(node, visit)
  }
  visit(file)
  expect(methods).toHaveLength(1)
  const localSelects: string[] = []
  const scan = (node: ts.Node) => {
    const value = ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node) ? node.text : ts.isTemplateExpression(node) ? node.head.text + node.templateSpans.map((span) => span.literal.text).join('') : ''
    if (/^\s*SELECT\b/i.test(value) && /\bFROM\s+bg_transit_engine\b/i.test(value)) localSelects.push(value)
    ts.forEachChild(node, scan)
  }
  scan(methods[0])
  expect(localSelects).toEqual([])
})

it('the typed owner preserves the original driver promise and result', async () => {
  const { queryTransitEngineReference } = await import('@/lib/brahmagyan/transit_reference_store')
  mockQuery.mockReset()
  const result = { rows: [{ synthetic_marker: 'owned' }] }
  const promise = Promise.resolve(result)
  mockQuery.mockReturnValue(promise)
  const returned = queryTransitEngineReference({ graha: 'Synthetic' })
  expect(returned).toBe(promise)
  expect(await returned).toBe(result)
  expect(mockQuery.mock.calls[0][1]).toEqual(['Synthetic'])
})
