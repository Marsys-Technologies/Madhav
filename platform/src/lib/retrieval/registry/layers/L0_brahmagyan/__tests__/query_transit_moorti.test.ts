import { readFileSync } from 'node:fs'
import ts from 'typescript'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryTransitMoortiCapability } from '../query_transit_moorti'

describe('queryTransitMoortiCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 27 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ nakshatra_offset: 1, moorti_name: 'swarna' }] })
    const result = await queryTransitMoortiCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_transit_moorti')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('nakshatra_offset filter is integer-checked and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryTransitMoortiCapability.handler({ nakshatra_offset: 9 }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('nakshatra_offset = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual([9])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryTransitMoortiCapability.handler({ nakshatra_offset: 99 }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('nakshatra_offset=99')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryTransitMoortiCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryTransitMoortiCapability.scope).toBe('global')
    expect(queryTransitMoortiCapability.required_inputs).toEqual([])
  })
})


describe('reference read characterization', () => {
  beforeEach(() => { mockQuery.mockReset() })
  it.each([["absent", {}, {"nakshatra_offset": null, "moorti_name": null}, [], []], ["null", {"nakshatra_offset": null, "moorti_name": null}, {"nakshatra_offset": null, "moorti_name": null}, [], []], ["zero", {"nakshatra_offset": 0}, {"nakshatra_offset": 0, "moorti_name": null}, [0], ["nakshatra_offset = $1"]], ["empty-number", {"nakshatra_offset": ""}, {"nakshatra_offset": 0, "moorti_name": null}, [0], ["nakshatra_offset = $1"]], ["false-number", {"nakshatra_offset": false}, {"nakshatra_offset": 0, "moorti_name": null}, [0], ["nakshatra_offset = $1"]], ["numeric-string", {"nakshatra_offset": "9"}, {"nakshatra_offset": 9, "moorti_name": null}, [9], ["nakshatra_offset = $1"]], ["negative", {"nakshatra_offset": -2}, {"nakshatra_offset": -2, "moorti_name": null}, [-2], ["nakshatra_offset = $1"]], ["fractional", {"nakshatra_offset": 1.5}, {"nakshatra_offset": 1.5, "moorti_name": null}, [], []], ["nan", {"nakshatra_offset": "not-a-number"}, {"nakshatra_offset": NaN, "moorti_name": null}, [], []], ["infinite", {"nakshatra_offset": Infinity}, {"nakshatra_offset": Infinity, "moorti_name": null}, [], []], ["name-only", {"moorti_name": "Swarna"}, {"nakshatra_offset": null, "moorti_name": "Swarna"}, ["Swarna"], ["LOWER(moorti_name) = LOWER($1)"]], ["both", {"nakshatra_offset": "9", "moorti_name": "Swarna"}, {"nakshatra_offset": 9, "moorti_name": "Swarna"}, [9, "Swarna"], ["nakshatra_offset = $1", "LOWER(moorti_name) = LOWER($2)"]], ["empty-name", {"moorti_name": []}, {"nakshatra_offset": null, "moorti_name": ""}, [], []]])('preserves SQL, binds and normalized filters: %s', async (_name, args, filters, params, clauses) => {
    const rows = [{ synthetic_marker: 'reference-row' }]
    mockQuery.mockResolvedValueOnce({ rows })
    const result = await queryTransitMoortiCapability.handler(args as Record<string, unknown>, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toBe(rows)
    expect(content['filters']).toEqual(filters)
    expect(mockQuery.mock.calls[0]).toEqual(["\n      SELECT nakshatra_offset, moorti_name, quality_tier, phala_brief, classical_citation, rule_notes\n      FROM bg_transit_moorti\n      WHERE ${where}\n      ORDER BY nakshatra_offset".replace('${where}', ['1=1', ...(clauses as string[])].join(' AND ')), params])
  })
  it.each(['sync', 'rejection'])('preserves thrown error formatting: %s', async mode => {
    const error = { toString: vi.fn(() => 'synthetic-reference-failure') }
    if (mode === 'sync') mockQuery.mockImplementationOnce(() => { throw error })
    else mockQuery.mockRejectedValueOnce(error)
    expect(await queryTransitMoortiCapability.handler({}, undefined)).toEqual({ content: { error: 'synthetic-reference-failure' }, is_error: true })
    expect(error.toString).toHaveBeenCalledTimes(1)
  })
  it('keeps argument coercion failure outside the query catch', async () => {
    const marker = new Error('synthetic-coercion')
    await expect(queryTransitMoortiCapability.handler({ "nakshatra_offset": { valueOf() { throw marker }, toString() { throw marker } } }, undefined)).rejects.toBe(marker)
    expect(mockQuery).not.toHaveBeenCalled()
  })
  it('keeps concurrent results bound to their own calls', async () => {
    let resolveFirst!: (value: unknown) => void
    let resolveSecond!: (value: unknown) => void
    mockQuery.mockImplementationOnce(() => new Promise(resolve => { resolveFirst = resolve }))
    mockQuery.mockImplementationOnce(() => new Promise(resolve => { resolveSecond = resolve }))
    const first = queryTransitMoortiCapability.handler({}, undefined)
    const second = queryTransitMoortiCapability.handler({}, undefined)
    const rowsFirst = [{ synthetic_marker: 'first' }], rowsSecond = [{ synthetic_marker: 'second' }]
    resolveSecond({ rows: rowsSecond }); resolveFirst({ rows: rowsFirst })
    expect(((await first).content as Record<string, unknown>)['rows']).toBe(rowsFirst)
    expect(((await second).content as Record<string, unknown>)['rows']).toBe(rowsSecond)
    expect(mockQuery).toHaveBeenCalledTimes(2)
  })
})

it('keeps serving SQL at the typed Brahmagyan owner rather than the descriptor', () => {
  const source = readFileSync(new URL('../query_transit_moorti.ts', import.meta.url), 'utf8')
  const file = ts.createSourceFile('query_transit_moorti.ts', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
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
    if (/^\s*SELECT\b/i.test(value) && /\bFROM\s+bg_transit_moorti\b/i.test(value)) localSelects.push(value)
    ts.forEachChild(node, scan)
  }
  scan(methods[0])
  expect(localSelects).toEqual([])
})

it('the typed owner preserves the original driver promise and result', async () => {
  const { queryTransitMoortiReference } = await import('@/lib/brahmagyan/transit_reference_store')
  mockQuery.mockReset()
  const result = { rows: [{ synthetic_marker: 'owned' }] }
  const promise = Promise.resolve(result)
  mockQuery.mockReturnValue(promise)
  const returned = queryTransitMoortiReference({ nakshatraOffset: 9, moortiName: 'Synthetic' })
  expect(returned).toBe(promise)
  expect(await returned).toBe(result)
  expect(mockQuery.mock.calls[0][1]).toEqual([9, 'Synthetic'])
})
