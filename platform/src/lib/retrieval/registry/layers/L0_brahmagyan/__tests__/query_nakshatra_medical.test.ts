import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryNakshatraMedicalCapability } from '../query_nakshatra_medical'

describe('queryNakshatraMedicalCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 27 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ nakshatra_name: 'Ashwini', nakshatra_number: 1 }] })
    const result = await queryNakshatraMedicalCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_nakshatra_medical')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('nakshatra_number filter is integer-checked and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryNakshatraMedicalCapability.handler({ nakshatra_number: 25 }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('nakshatra_number = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual([25])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryNakshatraMedicalCapability.handler({ nakshatra_name: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('nakshatra_name=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryNakshatraMedicalCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  // ── spelling tolerance (SS N-471): L1 now writes Moola / Mrigasira / Dhanishtha, the L0 medical seed
  //    (brahmagyan/l0_medical.py) still stores Mula / Mrigashira / Dhanishtha. Either must find the row.
  describe('name filter is spelling-tolerant', () => {
    const SEED = [
      { nakshatra_name: 'Mrigashira', nakshatra_number: 5 },
      { nakshatra_name: 'Mula', nakshatra_number: 19 },
      { nakshatra_name: 'Dhanishtha', nakshatra_number: 23 },
      { nakshatra_name: 'Rohini', nakshatra_number: 4 },
    ]
    // Emulates the SQL `LOWER(nakshatra_name) = ANY($1::text[])` against the seed spellings.
    function emulateDb(_sql: string, params: unknown[]) {
      const names = Array.isArray(params[0]) ? (params[0] as string[]) : []
      return Promise.resolve({ rows: SEED.filter(r => names.includes(r.nakshatra_name.toLowerCase())) })
    }

    it.each([
      [5, 'Mrigasira'], [5, 'Mrigashira'], [5, 'MRIGASIRA'],
      [19, 'Moola'], [19, 'Mula'], [19, ' moola '],
      [23, 'Dhanishtha'], [23, 'Dhanishta'],
    ])('no. %i found from "%s"', async (num, name) => {
      mockQuery.mockImplementationOnce(emulateDb)
      const result = await queryNakshatraMedicalCapability.handler({ nakshatra_name: name }, undefined)
      const content = result.content as Record<string, unknown>
      expect(result.is_error).toBe(false)
      expect(content['count']).toBe(1)
      expect((content['rows'] as Array<Record<string, unknown>>)[0]!['nakshatra_number']).toBe(num)
      expect(content['empty_reason']).toBeUndefined()
    })

    it('binds the equivalent spellings as ONE array parameter (no interpolation of the input)', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] })
      await queryNakshatraMedicalCapability.handler({ nakshatra_name: "Moola'; DROP TABLE x;--" }, undefined)
      mockQuery.mockResolvedValueOnce({ rows: [] })
      await queryNakshatraMedicalCapability.handler({ nakshatra_name: 'Moola' }, undefined)
      const [sqlBad, paramsBad] = mockQuery.mock.calls[0] as [string, unknown[]]
      expect(sqlBad).not.toContain('DROP')
      expect(paramsBad).toEqual([["moola'; drop table x;--"]])   // unresolved input passes through, bound
      const [sql, params] = mockQuery.mock.calls[1] as [string, unknown[]]
      expect(sql).toContain('LOWER(nakshatra_name) = ANY($1::text[])')
      expect(params).toEqual([['moola', 'mula']])
    })

    it('unknown name still returns the honest empty_reason (response shape unchanged)', async () => {
      mockQuery.mockImplementationOnce(emulateDb)
      const result = await queryNakshatraMedicalCapability.handler({ nakshatra_name: 'nope' }, undefined)
      const content = result.content as Record<string, unknown>
      expect(content['count']).toBe(0)
      expect(content['filters']).toEqual({ nakshatra_name: 'nope', nakshatra_number: null })
      expect(String(content['empty_reason'])).toContain('nakshatra_name=nope')
    })

    it('name + number filters keep their parameter order', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] })
      await queryNakshatraMedicalCapability.handler({ nakshatra_name: 'Mula', nakshatra_number: 19 }, undefined)
      const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]
      expect(sql).toContain('ANY($1::text[])')
      expect(sql).toContain('nakshatra_number = $2')
      expect(params).toEqual([['moola', 'mula'], 19])
    })
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryNakshatraMedicalCapability.scope).toBe('global')
    expect(queryNakshatraMedicalCapability.required_inputs).toEqual([])
  })
})
