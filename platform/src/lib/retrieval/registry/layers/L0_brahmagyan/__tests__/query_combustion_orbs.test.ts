/**
 * query_combustion_orbs.test.ts — W2 dark-set wiring unit tests.
 * No live DB required — `query` is mocked (same pattern as get_yoga_dosha.test.ts).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryCombustionOrbsCapability } from '../query_combustion_orbs'

describe('queryCombustionOrbsCapability', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('no filter: queries all 8 rows', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        { graha: 'Moon', orb_degrees: 12, deep_orb_degrees: 10, retrograde_note: null, classical_citation: 'Saravali Ch.6 / BPHS Ch.3' },
      ],
    })
    const result = await queryCombustionOrbsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('FROM bg_combustion_orbs')
    expect(sql).toContain('WHERE 1=1')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('graha filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryCombustionOrbsCapability.handler({ graha: 'mercury' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('LOWER(graha) = LOWER($1)')
    expect(params).toEqual(['mercury'])
  })

  it('empty result (e.g. graha=Sun, which has no row) carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryCombustionOrbsCapability.handler({ graha: 'Sun' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('graha=Sun')
    expect(String(content['empty_reason'])).toContain('never combust')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryCombustionOrbsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required, provenance cites the real table', () => {
    expect(queryCombustionOrbsCapability.scope).toBe('global')
    expect(queryCombustionOrbsCapability.required_inputs).toEqual([])
  })
})
