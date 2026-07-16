/**
 * CR-47 fix (D-1.6 S-1) — regression test.
 *
 * phala_rectification's lel_fit_score is flat 0 across all 185 candidates on the native
 * chart (confirmed live 2026-07-16: every one of the top-50 rows had lel_fit_score:0),
 * yet the surface presented `candidates` ORDER BY lel_fit_score DESC with no signal that
 * the ranking is degenerate — a caller reading "row 1 of 185" could wrongly infer it is
 * the best-supported candidate. This asserts the handler now serves an honest
 * `non_discriminating: true` flag (+ explanatory note) whenever the served page's
 * lel_fit_score has zero variance, or the best row's win_margin is ~0 — and that a
 * genuinely-discriminating candidate set (real spread + real win_margin) does NOT get
 * flagged, so the fix doesn't turn into a false-positive-everywhere flag.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()

vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

function routeRectificationQueries(
  candidateRows: Record<string, unknown>[],
  bestRows: Record<string, unknown>[],
  total = String(candidateRows.length),
) {
  return (sql: string) => {
    const s = String(sql)
    if (s.includes('COUNT(*)')) return Promise.resolve({ rows: [{ total }] })
    if (s.includes('FROM phala_rectification_best')) return Promise.resolve({ rows: bestRows })
    return Promise.resolve({ rows: candidateRows })
  }
}

import { queryRectificationCapability } from '../query_phala_calibration'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function flatZeroCandidates(n: number): Record<string, unknown>[] {
  return Array.from({ length: n }, (_, i) => ({
    id: `cand-${i}`,
    candidate_birth_date: '1984-02-05',
    offset_minutes: (i - n / 2) * 5,
    ayanamsha_id: 'lahiri',
    lagna_sign: 'Aries',
    lel_fit_score: 0,
    lel_events_matched: 0,
    lel_events_tested: 36,
    lagna_stable: true,
    scored_date: '2026-07-15',
  }))
}

describe('query_rectification — non_discriminating flag (CR-47)', () => {
  beforeEach(() => {
    queryMock.mockReset()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('flags non_discriminating=true when all served candidates have lel_fit_score=0 (the live 482012f1 case)', async () => {
    queryMock.mockImplementation(
      routeRectificationQueries(
        flatZeroCandidates(50),
        [{
          judgment_flags: { calibration_state: 'calibrated', lel_event_count: 57, load_bearing: true },
          confidence_label: 'unresolved',
          best_offset_minutes: 0,
          best_lel_fit_score: 0,
          confidence_low: -0.2,
          confidence_high: 0.2,
          win_margin: 0,
          lel_training_events: 36,
          lel_training_matched: 0,
          leakage_firewall_note: '[basis=lel_fit] LEAKAGE-FIREWALL: ...',
          competing_candidates: [],
        }],
        '185',
      ),
    )

    const result = await queryRectificationCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: {
        non_discriminating: boolean
        non_discriminating_note?: string
        candidates: unknown[]
      }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    expect(result.content.non_discriminating).toBe(true)
    expect(result.content.non_discriminating_note).toBeTruthy()
    expect(String(result.content.non_discriminating_note)).toMatch(/not discriminating|zero variance/i)
    // The degenerate rows are still served (B.10 — never silently drop data).
    expect(result.content.candidates.length).toBe(50)
  })

  it('does NOT flag non_discriminating when candidates have real score spread and a real win_margin', async () => {
    const candidates = [
      { id: 'a', offset_minutes: 0, lel_fit_score: 0.72, lel_events_matched: 26, lel_events_tested: 36, lagna_stable: true, lagna_sign: 'Aries', ayanamsha_id: 'lahiri', candidate_birth_date: '1984-02-05', scored_date: '2026-07-15' },
      { id: 'b', offset_minutes: 5, lel_fit_score: 0.41, lel_events_matched: 15, lel_events_tested: 36, lagna_stable: true, lagna_sign: 'Aries', ayanamsha_id: 'lahiri', candidate_birth_date: '1984-02-05', scored_date: '2026-07-15' },
      { id: 'c', offset_minutes: -5, lel_fit_score: 0.10, lel_events_matched: 4, lel_events_tested: 36, lagna_stable: true, lagna_sign: 'Aries', ayanamsha_id: 'lahiri', candidate_birth_date: '1984-02-05', scored_date: '2026-07-15' },
    ]
    queryMock.mockImplementation(
      routeRectificationQueries(
        candidates,
        [{
          judgment_flags: { calibration_state: 'calibrated', lel_event_count: 57, load_bearing: true },
          confidence_label: 'resolved',
          best_offset_minutes: 0,
          best_lel_fit_score: 0.72,
          confidence_low: 0.5,
          confidence_high: 0.9,
          win_margin: 0.31,
          lel_training_events: 36,
          lel_training_matched: 26,
          leakage_firewall_note: '[basis=lel_fit] LEAKAGE-FIREWALL: ...',
          competing_candidates: [],
        }],
        '3',
      ),
    )

    const result = await queryRectificationCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { non_discriminating: boolean }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    expect(result.content.non_discriminating).toBe(false)
  })

  it('flags non_discriminating via win_margin ~0 even if the served page happens to have some scores absent', async () => {
    queryMock.mockImplementation(
      routeRectificationQueries(
        [{ id: 'a', offset_minutes: 0, lel_fit_score: null, lagna_stable: true }],
        [{
          judgment_flags: { calibration_state: 'calibrated', lel_event_count: 57, load_bearing: true },
          confidence_label: 'unresolved',
          best_offset_minutes: 0,
          best_lel_fit_score: 0,
          confidence_low: -0.2,
          confidence_high: 0.2,
          win_margin: 0,
          lel_training_events: 36,
          lel_training_matched: 0,
          leakage_firewall_note: '[basis=lel_fit] ...',
          competing_candidates: [],
        }],
        '1',
      ),
    )

    const result = await queryRectificationCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { non_discriminating: boolean }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    expect(result.content.non_discriminating).toBe(true)
  })
})
