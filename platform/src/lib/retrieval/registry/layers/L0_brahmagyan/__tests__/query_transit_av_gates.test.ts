import { readFileSync } from 'node:fs'
import ts from 'typescript'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryTransitAvGatesCapability } from '../query_transit_av_gates'

describe('queryTransitAvGatesCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 8 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ gate_kind: 'kakshya', graha: 'jupiter' }] })
    const result = await queryTransitAvGatesCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_transit_av_gates')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('gate_kind + graha filters are param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryTransitAvGatesCapability.handler({ gate_kind: 'sav_threshold', graha: 'Venus' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('gate_kind = $1')
    expect(sql).toContain('LOWER(graha) = LOWER($2)')
    expect(params).toEqual(['sav_threshold', 'Venus'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryTransitAvGatesCapability.handler({ gate_kind: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('gate_kind=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryTransitAvGatesCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryTransitAvGatesCapability.scope).toBe('global')
    expect(queryTransitAvGatesCapability.required_inputs).toEqual([])
  })
})


describe('reference read characterization', () => {
  beforeEach(() => { mockQuery.mockReset() })
  it.each([["absent", {}, {"gate_kind": null, "graha": null}, [], []], ["null", {"gate_kind": null, "graha": null}, {"gate_kind": null, "graha": null}, [], []], ["empty", {"gate_kind": "", "graha": ""}, {"gate_kind": null, "graha": null}, [], []], ["falsy", {"gate_kind": 0, "graha": false}, {"gate_kind": null, "graha": null}, [], []], ["empty-array", {"gate_kind": [], "graha": []}, {"gate_kind": "", "graha": ""}, [], []], ["gate-only", {"gate_kind": "sav_threshold"}, {"gate_kind": "sav_threshold", "graha": null}, ["sav_threshold"], ["gate_kind = $1"]], ["graha-only", {"graha": "Venus"}, {"gate_kind": null, "graha": "Venus"}, ["Venus"], ["LOWER(graha) = LOWER($1)"]], ["both", {"gate_kind": "sav_threshold", "graha": "Venus"}, {"gate_kind": "sav_threshold", "graha": "Venus"}, ["sav_threshold", "Venus"], ["gate_kind = $1", "LOWER(graha) = LOWER($2)"]], ["whitespace", {"gate_kind": "  ", "graha": " Moon "}, {"gate_kind": "  ", "graha": " Moon "}, ["  ", " Moon "], ["gate_kind = $1", "LOWER(graha) = LOWER($2)"]], ["numeric", {"gate_kind": 3, "graha": 7}, {"gate_kind": "3", "graha": "7"}, ["3", "7"], ["gate_kind = $1", "LOWER(graha) = LOWER($2)"]]])('preserves SQL, binds and normalized filters: %s', async (_name, args, filters, params, clauses) => {
    const rows = [{ synthetic_marker: 'reference-row' }]
    mockQuery.mockResolvedValueOnce({ rows })
    const result = await queryTransitAvGatesCapability.handler(args as Record<string, unknown>, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toBe(rows)
    expect(content['filters']).toEqual(filters)
    expect(mockQuery.mock.calls[0]).toEqual(["\n      SELECT gate_kind, graha, house_from_moon, kakshya_lord, min_av_score, min_sav_score,\n             effect, classical_citation, rule_notes\n      FROM bg_transit_av_gates\n      WHERE ${where}\n      ORDER BY gate_kind, graha, house_from_moon".replace('${where}', ['1=1', ...(clauses as string[])].join(' AND ')), params])
  })
  it.each(['sync', 'rejection'])('preserves thrown error formatting: %s', async mode => {
    const error = { toString: vi.fn(() => 'synthetic-reference-failure') }
    if (mode === 'sync') mockQuery.mockImplementationOnce(() => { throw error })
    else mockQuery.mockRejectedValueOnce(error)
    expect(await queryTransitAvGatesCapability.handler({}, undefined)).toEqual({ content: { error: 'synthetic-reference-failure' }, is_error: true })
    expect(error.toString).toHaveBeenCalledTimes(1)
  })
  it('keeps argument coercion failure outside the query catch', async () => {
    const marker = new Error('synthetic-coercion')
    await expect(queryTransitAvGatesCapability.handler({ "gate_kind": { valueOf() { throw marker }, toString() { throw marker } } }, undefined)).rejects.toBe(marker)
    expect(mockQuery).not.toHaveBeenCalled()
  })
  it('keeps concurrent results bound to their own calls', async () => {
    let resolveFirst!: (value: unknown) => void
    let resolveSecond!: (value: unknown) => void
    mockQuery.mockImplementationOnce(() => new Promise(resolve => { resolveFirst = resolve }))
    mockQuery.mockImplementationOnce(() => new Promise(resolve => { resolveSecond = resolve }))
    const first = queryTransitAvGatesCapability.handler({}, undefined)
    const second = queryTransitAvGatesCapability.handler({}, undefined)
    const rowsFirst = [{ synthetic_marker: 'first' }], rowsSecond = [{ synthetic_marker: 'second' }]
    resolveSecond({ rows: rowsSecond }); resolveFirst({ rows: rowsFirst })
    expect(((await first).content as Record<string, unknown>)['rows']).toBe(rowsFirst)
    expect(((await second).content as Record<string, unknown>)['rows']).toBe(rowsSecond)
    expect(mockQuery).toHaveBeenCalledTimes(2)
  })
})

it('keeps serving SQL at the typed Brahmagyan owner rather than the descriptor', () => {
  const source = readFileSync(new URL('../query_transit_av_gates.ts', import.meta.url), 'utf8')
  const file = ts.createSourceFile('query_transit_av_gates.ts', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
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
    if (/^\s*SELECT\b/i.test(value) && /\bFROM\s+bg_transit_av_gates\b/i.test(value)) localSelects.push(value)
    ts.forEachChild(node, scan)
  }
  scan(methods[0])
  expect(localSelects).toEqual([])
})

it('the typed owner preserves the original driver promise and result', async () => {
  const { queryTransitAvGatesReference } = await import('@/lib/brahmagyan/transit_reference_store')
  mockQuery.mockReset()
  const result = { rows: [{ synthetic_marker: 'owned' }] }
  const promise = Promise.resolve(result)
  mockQuery.mockReturnValue(promise)
  const returned = queryTransitAvGatesReference({ gateKind: 'synthetic-gate', graha: 'Synthetic' })
  expect(returned).toBe(promise)
  expect(await returned).toBe(result)
  expect(mockQuery.mock.calls[0][1]).toEqual(['synthetic-gate', 'Synthetic'])
})
