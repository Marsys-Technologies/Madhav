/**
 * R5.1 C2 item 5 (lel_training_matched=0 corroboration honesty) — regression test.
 *
 * Fixture rows below are VERBATIM real values read live from prod (Cloud SQL Auth Proxy,
 * 2026-07-09) for the two canonical charts:
 *   - native (482012f1-…): lel_event_count=57, calibration_state='calibrated',
 *     lel_training_events=36, lel_training_matched=0 — the exact "0 that looks like a
 *     failure but isn't" case the brief names.
 *   - Abhinandan (1c826d5a-…): lel_event_count=0, calibration_state='structural',
 *     lel_training_events=0, lel_training_matched=null — the genuinely-nothing-to-report
 *     case, which must read distinctly from the native's "0 matches out of a real subset".
 *
 * Asserts the handler's `lel_match_explanation` block surfaces BOTH numbers (lel_event_count
 * vs lel_training_matched) together, explains the leakage-firewall reason they differ, and
 * never lets one silently stand in for the other.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()

vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryRectificationCapability } from '../query_phala_calibration'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

describe('query_rectification — lel_match_explanation (R5.1 C2 item 5)', () => {
  beforeEach(() => {
    queryMock.mockReset()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('native chart: surfaces lel_event_count=57 AND lel_training_matched=0 together with an explanation, never one silently substituting for the other', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] }) // candidates query (not needed for this assertion)
      .mockResolvedValueOnce({
        rows: [{
          judgment_flags: {
            calibration: 'calibrated',
            calibration_state: 'calibrated',
            rectification_basis: 'lel_fit',
            lel_event_count: 57,
            load_bearing: true,
          },
          confidence_label: 'unresolved',
          best_offset_minutes: 0,
          best_lel_fit_score: null,
          confidence_low: null,
          confidence_high: null,
          win_margin: null,
          lel_training_events: 36,
          lel_training_matched: 0,
          leakage_firewall_note: '[basis=lel_fit] LEAKAGE-FIREWALL: 36 training events (all pre-2020-01-01, exact/month-exact, none from LEL v1.7 M5-A-S1 enrichment). Post-2020 + enrichment events held out for out-of-sample validation.',
          competing_candidates: [],
        }],
      })

    const result = await queryRectificationCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { lel_match_explanation: Record<string, unknown>; calibration_state: string }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    expect(result.content.calibration_state).toBe('calibrated')

    const explanation = result.content.lel_match_explanation
    expect(explanation.corroboration_available).toBe(true)
    // The full corroboration count (drives calibration_state) must still be visible.
    expect(explanation.lel_event_count).toBe(57)
    // The separate training-subset match count must ALSO be visible, not hidden behind the 57.
    expect(explanation.lel_training_events).toBe(36)
    expect(explanation.lel_training_matched).toBe(0)
    // The explanation text must mention both numbers so a reader cannot conflate them.
    expect(String(explanation.explanation)).toContain('57')
    expect(String(explanation.explanation)).toContain('36')
    expect(String(explanation.explanation)).toContain('0')
    expect(String(explanation.match_criterion)).toContain('dasha')
    expect(explanation.leakage_firewall_note).toContain('LEAKAGE-FIREWALL')
  })

  it('Abhinandan chart (structural, no rectification run): explanation reads as "no LEL corroboration to report" — never conflated with a denial or a training-match failure', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] }) // candidates query
      .mockResolvedValueOnce({ rows: [] }) // no phala_rectification_best row at all

    const result = await queryRectificationCapability.handler({ chart_id: ABHINANDAN_CHART_ID }, undefined) as {
      content: { lel_match_explanation: Record<string, unknown>; calibration_state: string | null }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    expect(result.content.calibration_state).toBeNull()
    expect(result.content.lel_match_explanation.corroboration_available).toBe(false)
    expect(String(result.content.lel_match_explanation.note)).toMatch(/structural|no rectification/i)
  })

  it('a chart WITH a best row but genuinely zero LEL events (structural, load_bearing false) reports lel_event_count=0 honestly, distinct from the native\'s calibrated-but-zero-training-match case', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({
        rows: [{
          judgment_flags: {
            calibration: 'structural',
            calibration_state: 'structural',
            rectification_basis: 'structural_no_lel',
            lel_event_count: 0,
            load_bearing: false,
          },
          confidence_label: 'unresolved',
          best_offset_minutes: 0,
          best_lel_fit_score: null,
          confidence_low: null,
          confidence_high: null,
          win_margin: null,
          lel_training_events: 0,
          lel_training_matched: null,
          leakage_firewall_note: '[basis=structural_no_lel] LEAKAGE-FIREWALL: 0 training events (all pre-2020-01-01, exact/month-exact, none from LEL v1.7 M5-A-S1 enrichment). Post-2020 + enrichment events held out for out-of-sample validation.',
          competing_candidates: [],
        }],
      })

    const result = await queryRectificationCapability.handler({ chart_id: ABHINANDAN_CHART_ID }, undefined) as {
      content: { lel_match_explanation: Record<string, unknown> }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    expect(result.content.lel_match_explanation.corroboration_available).toBe(true)
    expect(result.content.lel_match_explanation.lel_event_count).toBe(0)
    expect(result.content.lel_match_explanation.lel_training_matched).toBeNull()
  })
})
