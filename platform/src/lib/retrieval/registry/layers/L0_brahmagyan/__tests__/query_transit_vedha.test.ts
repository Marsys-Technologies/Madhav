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
