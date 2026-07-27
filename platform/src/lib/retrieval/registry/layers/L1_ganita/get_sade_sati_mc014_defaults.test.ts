/**
 * get_sade_sati_mc014_defaults.test.ts — ŚODHANA T3 (MC-014 defaults sweep).
 *
 * get_sade_sati serves 15 Saturn-period categories spanning a chart's full historical +
 * future sweep (~1950-2100) by default — MC-014 measured ~1,259 rows for one chart with no
 * "current phase" default. Default (`all` omitted or false) now filters to periods whose own
 * start/end date pair overlaps a window around "now"; `all:true` restores the full sweep
 * (never removed — B.10, just no longer the default). A period-family category with no
 * start/end date pair of its own (flags/overlays keyed off a parent cycle) is always kept,
 * regardless of the flag — the filter only drops what it can positively confirm is outside
 * the window.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

async function getCapabilityHandler() {
  await import('../../catalog')
  const { getCapability } = await import('../../index')
  const cap = getCapability('marsys://tool/L1/get_sade_sati')
  if (!cap) throw new Error('get_sade_sati capability not registered')
  return cap.handler as (args: Record<string, unknown>, ctx?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
}

function periodRow(overrides: Record<string, unknown>): Record<string, unknown> {
  return {
    fact_id: 'fid', fact_category: 'janma_shani_period', fact_subject: 'SUBJ', ayanamsha_id: 'lahiri_chitrapaksha',
    fact_key: 'k', fact_value_num: null, fact_value_text: null, fact_value_jsonb: null,
    unit: null, verification_pass_status: 'pass', citation_ref: 'c',
    ...overrides,
  }
}

function makeRows(): Record<string, unknown>[] {
  const now = new Date()
  const isoYearsFromNow = (years: number) => new Date(now.getTime() + years * 365.25 * 24 * 60 * 60 * 1000).toISOString()
  return [
    // CURRENT period — well inside the window, must survive.
    periodRow({ fact_category: 'janma_shani_period', fact_subject: 'CURRENT', fact_key: 'period_start_iso', fact_value_text: isoYearsFromNow(-1) }),
    periodRow({ fact_category: 'janma_shani_period', fact_subject: 'CURRENT', fact_key: 'period_end_iso', fact_value_text: isoYearsFromNow(1) }),
    // FAR-FUTURE period — outside the window (e.g. year ~2090), must be dropped by default.
    periodRow({ fact_category: 'janma_shani_period', fact_subject: 'FAR_FUTURE', fact_key: 'period_start_iso', fact_value_text: isoYearsFromNow(60) }),
    periodRow({ fact_category: 'janma_shani_period', fact_subject: 'FAR_FUTURE', fact_key: 'period_end_iso', fact_value_text: isoYearsFromNow(61) }),
    // FAR-PAST period — outside the window (e.g. year ~1955), must be dropped by default.
    periodRow({ fact_category: 'janma_shani_period', fact_subject: 'FAR_PAST', fact_key: 'period_start_iso', fact_value_text: isoYearsFromNow(-70) }),
    periodRow({ fact_category: 'janma_shani_period', fact_subject: 'FAR_PAST', fact_key: 'period_end_iso', fact_value_text: isoYearsFromNow(-69) }),
    // Undated flag category (no *_start_iso/*_end_iso pair) — always kept, filter can't
    // evaluate it, never silently dropped (B.10).
    periodRow({ fact_category: 'sade_sati_cancellation_check', fact_subject: 'CYCLE_1', fact_key: 'cancellation_active_flag', fact_value_text: 'false' }),
  ]
}

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockResolvedValue({ rows: makeRows() })
})

describe('get_sade_sati — MC-014 current+adjacent-window default', () => {
  it('default (all omitted): drops far-past/far-future dated periods, keeps current + undated rows', async () => {
    const handler = await getCapabilityHandler()
    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha' })

    expect(res.is_error).toBeFalsy()
    const rows = res.content['rows'] as Record<string, unknown>[]
    const subjects = new Set(rows.map(r => r['fact_subject']))
    expect(subjects.has('CURRENT')).toBe(true)
    expect(subjects.has('CYCLE_1')).toBe(true) // undated flag row — always kept
    expect(subjects.has('FAR_FUTURE')).toBe(false)
    expect(subjects.has('FAR_PAST')).toBe(false)
    expect(res.content['periods_dropped_outside_window']).toBe(2) // FAR_FUTURE + FAR_PAST
    expect(res.content['window_filter_applied']).toBe(true)
  })

  it('all:true restores the full historical+future sweep (never deleted, just not the default)', async () => {
    const handler = await getCapabilityHandler()
    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', all: true })

    const rows = res.content['rows'] as Record<string, unknown>[]
    const subjects = new Set(rows.map(r => r['fact_subject']))
    expect(subjects.has('CURRENT')).toBe(true)
    expect(subjects.has('FAR_FUTURE')).toBe(true)
    expect(subjects.has('FAR_PAST')).toBe(true)
    expect(subjects.has('CYCLE_1')).toBe(true)
    expect(res.content['all']).toBe(true)
  })
})
