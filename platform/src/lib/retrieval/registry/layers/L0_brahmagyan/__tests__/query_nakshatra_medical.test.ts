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

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryNakshatraMedicalCapability.scope).toBe('global')
    expect(queryNakshatraMedicalCapability.required_inputs).toEqual([])
  })
})
