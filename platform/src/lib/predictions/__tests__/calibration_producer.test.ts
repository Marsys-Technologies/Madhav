/**
 * 4.learning_loop — calibration-stamp producer tests.
 *
 * Asserts that:
 *   1. Each call writes a row to mcp_predictions (10 calls -> 10 INSERT attempts).
 *   2. The deterministic stamp shape (chart_id, ayanamsha_id, query_hash,
 *      salience_formula_version, model_id, predicted_at_iso) is bound correctly.
 *   3. DB errors are swallowed (must never break the user's response).
 *   4. The producer is independent of LEL toggle (no LEL_CONTEXT_ENABLED branching).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn().mockResolvedValue({ rows: [] })

vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { hashQuery, recordCalibrationStamp } from '../calibration_producer'

describe('recordCalibrationStamp', () => {
  beforeEach(() => {
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('writes one row per call (10 calls → 10 INSERTs)', async () => {
    for (let i = 0; i < 10; i++) {
      await recordCalibrationStamp({
        chart_id: 'abhisek_mohanty_primary',
        ayanamsha_id: 'jh_true_chitra',
        query_text: `query ${i}`,
        model_id: 'claude-opus-4-7-1m',
      })
    }
    expect(queryMock).toHaveBeenCalledTimes(10)
  })

  it('binds the deterministic stamp into the INSERT', async () => {
    await recordCalibrationStamp({
      chart_id: 'abhisek_mohanty_primary',
      ayanamsha_id: 'jh_true_chitra',
      query_text: 'will I move abroad in 2027?',
      model_id: 'claude-opus-4-7-1m',
      predicted_at_iso: '2026-05-28T14:00:00.000Z',
    })
    expect(queryMock).toHaveBeenCalledOnce()
    const [, params] = queryMock.mock.calls[0] as [string, unknown[]]
    // [prediction_id, logged_at, chart_id, ayanamsha_id, query_hash, formula_version, model_id, predicted_at_iso, caller_context]
    expect(params[2]).toBe('abhisek_mohanty_primary')
    expect(params[3]).toBe('jh_true_chitra')
    expect(params[4]).toBe(hashQuery('will I move abroad in 2027?'))
    expect(params[5]).toBe('v3.0')
    expect(params[6]).toBe('claude-opus-4-7-1m')
    expect(params[7]).toBe('2026-05-28T14:00:00.000Z')
    expect(params[8]).toBe('wave4-calibration-stamp')
  })

  it('returns ok:false on DB error without throwing', async () => {
    queryMock.mockRejectedValueOnce(new Error('connection refused'))
    const result = await recordCalibrationStamp({
      chart_id: 'abhisek_mohanty_primary',
      ayanamsha_id: 'jh_true_chitra',
      query_text: 'q',
      model_id: 'm',
    })
    expect(result.ok).toBe(false)
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

  it('producer never branches on LEL toggle (no env-var read)', async () => {
    process.env['MARSYS_FLAG_LEL_CONTEXT_ENABLED'] = 'false'
    const result = await recordCalibrationStamp({
      chart_id: 'abhisek_mohanty_primary',
      ayanamsha_id: 'jh_true_chitra',
      query_text: 'q',
      model_id: 'm',
    })
    expect(result.ok).toBe(true)
    expect(queryMock).toHaveBeenCalledOnce()
    delete process.env['MARSYS_FLAG_LEL_CONTEXT_ENABLED']
  })
})
