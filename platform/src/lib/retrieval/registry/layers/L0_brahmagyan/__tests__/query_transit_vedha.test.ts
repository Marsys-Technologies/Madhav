import { readFileSync } from 'node:fs'
import ts from 'typescript'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryTransitVedhaCapability } from '../query_transit_vedha'

describe('queryTransitVedhaCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 33 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ primary_graha: 'sun', primary_transit_house: 3 }] })
    const result = await queryTransitVedhaCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_transit_vedha')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('primary_graha + primary_transit_house filters are param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryTransitVedhaCapability.handler({ primary_graha: 'Sun', primary_transit_house: 3 }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('LOWER(primary_graha) = LOWER($1)')
    expect(sql).toContain('primary_transit_house = $2')
    expect(params).toEqual(['Sun', 3])
  })

  it('empty result carries an honest empty_reason and the governance-anomaly note', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryTransitVedhaCapability.handler({ primary_graha: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('primary_graha=nope')
    expect(String(content['governance_note'])).toContain('no CREATE TABLE migration')
  })

  // PK-R-9 IR-3: bg_transit_vedha is RETIRED-IN-PLACE / non-authoritative --
  // bg_transit_rules is the authoritative vedha-pair corpus. This serving
  // surface stays LIVE (not retired/unwired); the governance_note must name
  // the authority, the 4 Venus disagreements, and the 8 missing rows as an
  // open L0 reconciliation item.
  it('governance_note names bg_transit_rules as authoritative, the 4 Venus disagreements, and the 8 missing rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryTransitVedhaCapability.handler({}, undefined)
    const note = String((result.content as Record<string, unknown>)['governance_note'])

    expect(note).toContain('RETIRED-IN-PLACE')
    expect(note).toContain('non-authoritative')
    expect(note).toContain('bg_transit_rules')
    expect(note.toLowerCase()).toContain('authoritative')

    // 4 Venus disagreements: 4->3v10, 5->11v9, 8->9v1, 9->5v2
    expect(note).toContain('4')
    expect(note).toContain('10')
    expect(note).toContain('9')
    expect(note).toContain('11')
    expect(note).toContain('1')
    expect(note).toContain('5')
    expect(note).toContain('2')
    expect(note.toLowerCase()).toContain('venus')

    // 8 missing rows: Rahu 3/6/11, Ketu 3/6/11, Venus 11/12
    expect(note.toLowerCase()).toContain('rahu')
    expect(note.toLowerCase()).toContain('ketu')
    expect(note).toContain('12')
    expect(note.toLowerCase()).toContain('missing')

    // Open reconciliation, serving surface stays live (not retired/unwired)
    expect(note.toLowerCase()).toContain('reconciliation')
    expect(note.toLowerCase()).toContain('live')
  })

  it('capability itself is still registered/callable (serving surface not retired)', () => {
    expect(typeof queryTransitVedhaCapability.handler).toBe('function')
    expect(queryTransitVedhaCapability.uri).toBe('marsys://tool/L0/query_transit_vedha')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryTransitVedhaCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryTransitVedhaCapability.scope).toBe('global')
    expect(queryTransitVedhaCapability.required_inputs).toEqual([])
  })
})


// Preserve the descriptor's accepted normalization and driver-result boundary.
describe('Vedha reference read-owner compatibility', () => {
  beforeEach(() => { mockQuery.mockReset() })
  const cases = [
    [{}, [], null, null],
    [{ primary_graha: null }, [], null, null],
    [{ primary_graha: '' }, [], null, null],
    [{ primary_graha: 0 }, [], null, null],
    [{ primary_graha: false }, [], null, null],
    [{ primary_graha: [] }, [], '', null],
    [{ primary_graha: ' Mixed ' }, [' Mixed '], ' Mixed ', null],
    [{ primary_transit_house: 0 }, [0], null, 0],
    [{ primary_transit_house: '' }, [0], null, 0],
    [{ primary_transit_house: false }, [0], null, 0],
    [{ primary_transit_house: '2' }, [2], null, 2],
    [{ primary_transit_house: -1 }, [-1], null, -1],
    [{ primary_transit_house: 2.5 }, [], null, 2.5],
    [{ primary_transit_house: 'not-a-number' }, [], null, NaN],
    [{ primary_transit_house: Infinity }, [], null, Infinity],
    [{ primary_graha: 'Synthetic', primary_transit_house: '3' }, ['Synthetic', 3], 'Synthetic', 3],
  ] as const

  it.each(cases)('keeps normalized input and bound parameters for %j', async (args, params, graha, house) => {
    const rows = [{ synthetic: 'row' }]
    mockQuery.mockResolvedValue({ rows })
    const output = await queryTransitVedhaCapability.handler!(args, {})
    const [sql, bindings] = mockQuery.mock.calls[0]
    expect(bindings).toEqual(params)
    expect(sql).toContain('FROM bg_transit_vedha')
    expect(sql).toContain('ORDER BY primary_graha, primary_transit_house')
    expect(sql).toContain('WHERE 1=1')
    if (graha) expect(sql).toContain('LOWER(primary_graha) = LOWER($1)')
    else expect(sql).not.toContain('LOWER(primary_graha)')
    if (house != null && Number.isInteger(house)) expect(sql).toContain(`primary_transit_house = $${graha ? 2 : 1}`)
    else expect(sql).not.toContain('primary_transit_house = $')
    expect(output.content).toMatchObject({ count: 1, filters: { primary_graha: graha, primary_transit_house: house } })
    expect((output.content as { rows: unknown[] }).rows).toBe(rows)
    expect(output.is_error).toBe(false)
  })

  it('keeps synchronous and rejected query failures inside the same error response', async () => {
    for (const synchronous of [false, true]) {
      const failure = { toString: vi.fn(() => 'synthetic query failure') }
      mockQuery.mockReset()
      if (synchronous) mockQuery.mockImplementation(() => { throw failure })
      else mockQuery.mockRejectedValue(failure)
      expect(await queryTransitVedhaCapability.handler!({}, {})).toEqual({ content: { error: 'synthetic query failure' }, is_error: true })
      expect(failure.toString).toHaveBeenCalledTimes(1)
    }
  })

  it('does not move argument conversion into the query error catch', async () => {
    const failure = new Error('synthetic argument conversion')
    await expect(queryTransitVedhaCapability.handler!({ primary_graha: { toString: () => { throw failure } } }, {})).rejects.toBe(failure)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('keeps concurrent filter/result state independent under reversed completion', async () => {
    let first!: (value: { rows: unknown[] }) => void
    let second!: (value: { rows: unknown[] }) => void
    mockQuery.mockImplementationOnce(() => new Promise((resolve) => { first = resolve }))
    mockQuery.mockImplementationOnce(() => new Promise((resolve) => { second = resolve }))
    const a = queryTransitVedhaCapability.handler!({ primary_graha: 'first' }, {})
    const b = queryTransitVedhaCapability.handler!({ primary_graha: 'second' }, {})
    const rowsA = [{ synthetic: 'first' }], rowsB = [{ synthetic: 'second' }]
    second({ rows: rowsB })
    expect((await b).content).toMatchObject({ rows: rowsB, filters: { primary_graha: 'second' } })
    first({ rows: rowsA })
    expect((await a).content).toMatchObject({ rows: rowsA, filters: { primary_graha: 'first' } })
    expect(mockQuery.mock.calls.map((call) => call[1])).toEqual([['first'], ['second']])
  })
})


it('keeps serving SQL at the typed Brahmagyan owner rather than the descriptor', () => {
  const source = readFileSync(new URL('../query_transit_vedha.ts', import.meta.url), 'utf8')
  const file = ts.createSourceFile('query_transit_vedha.ts', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
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
    if (/^\s*SELECT\b/i.test(value) && /\bFROM\s+bg_transit_vedha\b/i.test(value)) localSelects.push(value)
    ts.forEachChild(node, scan)
  }
  scan(methods[0])
  expect(localSelects).toEqual([])
})

it('the typed owner returns the original query promise and result without a wrapper', async () => {
  const { queryTransitVedhaReference } = await import('@/lib/brahmagyan/transit_reference_store')
  mockQuery.mockReset()
  const result = { rows: [{ synthetic: 'owned' }] }
  const promise = Promise.resolve(result)
  mockQuery.mockReturnValue(promise)
  const returned = queryTransitVedhaReference({ primaryGraha: 'Synthetic', primaryHouse: 2 })
  expect(returned).toBe(promise)
  expect(await returned).toBe(result)
  expect(mockQuery.mock.calls[0][1]).toEqual(['Synthetic', 2])
})
