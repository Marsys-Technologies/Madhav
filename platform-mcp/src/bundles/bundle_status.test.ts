/**
 * bundle_status.test.ts — ŚODHANA T2 (MC-002).
 * Pure threshold tests for computeBundleHealth. Anti-vacuous: asserts the exact
 * boundary at which `ok:true` becomes structurally impossible.
 */
import { describe, it, expect } from 'vitest'
import { computeBundleHealth, DEGRADED_ERROR_RATIO } from './bundle_status.js'

describe('computeBundleHealth — MC-002', () => {
  it('0 errored → ok / ok:true', () => {
    expect(computeBundleHealth(0, 8)).toEqual({ status: 'ok', ok: true })
  })

  it('minority errored (<50%) → partial / ok:true', () => {
    expect(computeBundleHealth(3, 8)).toEqual({ status: 'partial', ok: true }) // 37.5%
    expect(computeBundleHealth(1, 8)).toEqual({ status: 'partial', ok: true })
  })

  it('exactly 50% errored → degraded / ok:false (majority threshold is inclusive)', () => {
    expect(computeBundleHealth(4, 8)).toEqual({ status: 'degraded', ok: false })
  })

  it('majority errored (>50%) → degraded / ok:false', () => {
    expect(computeBundleHealth(5, 8)).toEqual({ status: 'degraded', ok: false }) // the live MC-002 case
    expect(computeBundleHealth(8, 8)).toEqual({ status: 'degraded', ok: false })
  })

  it('empty bundle (nothing ran) → degraded / ok:false, never a hollow ok', () => {
    expect(computeBundleHealth(0, 0)).toEqual({ status: 'degraded', ok: false })
  })

  it('ok is ALWAYS derived from status (never true when degraded)', () => {
    for (let total = 1; total <= 12; total++) {
      for (let err = 0; err <= total; err++) {
        const h = computeBundleHealth(err, total)
        expect(h.ok).toBe(h.status !== 'degraded')
        if (err / total >= DEGRADED_ERROR_RATIO) expect(h.ok).toBe(false)
      }
    }
  })
})
