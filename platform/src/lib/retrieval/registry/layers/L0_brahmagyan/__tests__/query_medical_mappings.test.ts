import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryMedicalMappingsCapability } from '../query_medical_mappings'

describe('queryMedicalMappingsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 9 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ graha: 'Sun', dosha: ['pitta'] }] })
    const result = await queryMedicalMappingsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_medical_mappings')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('graha filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryMedicalMappingsCapability.handler({ graha: 'Mars' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('LOWER(graha) = LOWER($1)')
    expect(mockQuery.mock.calls[0][1]).toEqual(['Mars'])
  })

  it('empty result carries an honest empty_reason and medical disclaimer', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryMedicalMappingsCapability.handler({ graha: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('graha=nope')
    expect(String(content['disclaimer'])).toContain('NOT a medical diagnostic system')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryMedicalMappingsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryMedicalMappingsCapability.scope).toBe('global')
    expect(queryMedicalMappingsCapability.required_inputs).toEqual([])
  })
})
