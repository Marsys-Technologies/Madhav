/**
 * calibration_producer — retired-no-op tests.
 *
 * recordCalibrationStamp was RETIRED by PB-3 (SAMĪKṢĀ) lane L-1 (MEMO_PB-3_0): it wrote
 * exclusively to `mcp_predictions`, dropped by migration 471. It is now an inert no-op. These
 * tests assert:
 *   1. It performs NO DB write (10 calls → 0 query invocations).
 *   2. It returns { ok: false }.
 *   3. hashQuery is retained and still produces stable 16-char hex.
 *
 * The DB client is mocked to a spy; asserting the spy is never called is what makes "no DB
 * write" a real, falsifiable check (a live writer would trip it).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn().mockResolvedValue({ rows: [] })
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { hashQuery, recordCalibrationStamp } from '../calibration_producer'

describe('recordCalibrationStamp (RETIRED)', () => {
  beforeEach(() => {
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] })
  })
  afterEach(() => vi.restoreAllMocks())

  it('performs NO DB write (10 calls → 0 query invocations)', async () => {
    for (let i = 0; i < 10; i++) {
      await recordCalibrationStamp({
        chart_id: 'abhisek_mohanty_primary',
        ayanamsha_id: 'jh_true_chitra',
        query_text: `query ${i}`,
        model_id: 'claude-opus-4-7-1m',
      })
    }
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('returns { ok: false } (retired no-op)', async () => {
    const result = await recordCalibrationStamp({
      chart_id: 'abhisek_mohanty_primary',
      ayanamsha_id: 'jh_true_chitra',
      query_text: 'will I move abroad in 2027?',
      model_id: 'claude-opus-4-7-1m',
    })
    expect(result.ok).toBe(false)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('hashQuery produces stable 16-char hex', () => {
    const h1 = hashQuery('hello world')
    const h2 = hashQuery('hello world')
    expect(h1).toBe(h2)
    expect(h1).toMatch(/^[0-9a-f]{16}$/)
  })

  it('different query texts produce different hashes', () => {
    expect(hashQuery('q1')).not.toBe(hashQuery('q2'))
  })
})
