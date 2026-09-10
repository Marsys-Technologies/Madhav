/**
 * NIRMĀṆA L5 W3-3 — `qa_fail_count` must count the writer's REAL failure vocabulary.
 * ==================================================================================
 * The defect: `query_calibration.ts` computed `qa_fail_count` as
 * `qaResult.rows.filter(r => r.status === 'FAIL').length` — EXACT equality against a
 * column that is not a two-value enum. `mi_pariksha.py` emits six distinct literals, and
 * the bare string `'FAIL'` is only one of them (the `degenerate_distribution` substep,
 * mi_pariksha.py:623). The control-window substep (mi_pariksha.py:335) emits
 * `'FAIL_event_too_close'`.
 *
 * Live production at the time of the fix (canonical chart 482012f1, 2026-09-05):
 *
 *   SELECT status, count(*) FROM mimamsa_qa_eval
 *    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' GROUP BY status;
 *     control_baseline      92
 *     FAIL_event_too_close  61
 *     structural_proxy      10
 *     not_implemented        4
 *     pass                   1
 *
 *   -- old rule vs. new rule over the SAME 168 rows:
 *     count(*) FILTER (WHERE status = 'FAIL')            -> 0
 *     count(*) FILTER (WHERE upper(status) LIKE 'FAIL%') -> 61
 *
 * So `qa_summary.fail_count` reported 0 while 61 FAIL-prefixed rows sat inside the
 * `qa_results` array the SAME response returned. These tests pin the widened rule AND its
 * disclosure — §N.6 item 4: a widened match that is not reported is just a different
 * silent number.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryCalibrationCapability, isQaFailStatus } from '../query_calibration'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/** The exact live status distribution above, as rows. */
const LIVE_QA_ROWS = [
  ...Array.from({ length: 92 }, (_, i) => ({ check_id: `ctrl_${i}`, status: 'control_baseline' })),
  ...Array.from({ length: 61 }, (_, i) => ({ check_id: `ctrl_close_${i}`, status: 'FAIL_event_too_close' })),
  ...Array.from({ length: 10 }, (_, i) => ({ check_id: `abl_${i}`, status: 'structural_proxy' })),
  ...Array.from({ length: 4 }, (_, i) => ({ check_id: `neg_${i}`, status: 'not_implemented' })),
  { check_id: 'degen', status: 'pass' },
]

function installDb(qaRows: Array<Record<string, unknown>>) {
  queryMock.mockReset()
  queryMock.mockImplementation(async (sql: string) => {
    if (String(sql).includes('FROM mimamsa_qa_eval')) return { rows: qaRows }
    return { rows: [] }
  })
}

type Content = {
  qa_summary: {
    total: number
    fail_count: number
    fail_match_rule: string
    fail_statuses: string[]
    status_counts: Record<string, number>
    unrun_check_statuses: string[]
  }
  empty_reason?: string
}

async function run(qaRows: Array<Record<string, unknown>>): Promise<Content> {
  installDb(qaRows)
  const result = await queryCalibrationCapability.handler({ chart_id: CHART_ID }, undefined)
  expect(result.is_error).toBe(false)
  return result.content as Content
}

describe('query_calibration — qa_fail_count over the real mi_pariksha status vocabulary', () => {
  beforeEach(() => queryMock.mockReset())

  it('counts FAIL_event_too_close (the old exact-equality rule scored these 0)', async () => {
    const content = await run(LIVE_QA_ROWS)
    expect(content.qa_summary.total).toBe(168)
    expect(content.qa_summary.fail_count).toBe(61)
    // The precise regression: the old rule's answer on this exact input.
    expect(LIVE_QA_ROWS.filter(r => r.status === 'FAIL')).toHaveLength(0)
  })

  it('still counts the bare "FAIL" literal the degenerate_distribution substep emits', async () => {
    const content = await run([
      { check_id: 'degen', status: 'FAIL' },
      { check_id: 'ctrl', status: 'control_baseline' },
    ])
    expect(content.qa_summary.fail_count).toBe(1)
    expect(content.qa_summary.fail_statuses).toEqual(['FAIL'])
  })

  it('does NOT count pass / control_baseline / structural_proxy / not_implemented as failures', async () => {
    const content = await run([
      { check_id: 'a', status: 'pass' },
      { check_id: 'b', status: 'control_baseline' },
      { check_id: 'c', status: 'structural_proxy' },
      { check_id: 'd', status: 'not_implemented' },
    ])
    expect(content.qa_summary.fail_count).toBe(0)
    expect(content.qa_summary.fail_statuses).toEqual([])
  })

  it('DISCLOSES the widened rule, the statuses it matched, and the full histogram (§N.6 item 4)', async () => {
    const content = await run(LIVE_QA_ROWS)
    expect(content.qa_summary.fail_match_rule).toMatch(/prefix 'FAIL'/)
    expect(content.qa_summary.fail_statuses).toEqual(['FAIL_event_too_close'])
    expect(content.qa_summary.status_counts).toEqual({
      control_baseline: 92,
      FAIL_event_too_close: 61,
      structural_proxy: 10,
      not_implemented: 4,
      pass: 1,
    })
    // The count is re-derivable by the caller from the disclosed histogram alone.
    const rederived = content.qa_summary.fail_statuses
      .reduce((n, s) => n + content.qa_summary.status_counts[s], 0)
    expect(rederived).toBe(content.qa_summary.fail_count)
  })

  it('names the tiers that are neither pass nor failure, so "0 failures" cannot read as "all checked" (§N.8)', async () => {
    const content = await run(LIVE_QA_ROWS)
    expect(content.qa_summary.unrun_check_statuses).toEqual(['not_implemented', 'structural_proxy'])
  })

  it('reports an honest empty_reason naming the empty sections rather than a hollow envelope (§N.6 item 3)', async () => {
    const content = await run([])
    expect(content.empty_reason).toMatch(/verdict_distribution/)
    expect(content.empty_reason).toMatch(/qa_results/)
    expect(content.qa_summary.total).toBe(0)
    expect(content.qa_summary.fail_count).toBe(0)
  })

  it('isQaFailStatus is case-insensitive on the prefix and rejects non-strings', () => {
    expect(isQaFailStatus('FAIL')).toBe(true)
    expect(isQaFailStatus('FAIL_event_too_close')).toBe(true)
    expect(isQaFailStatus('  fail_something ')).toBe(true)
    expect(isQaFailStatus('pass')).toBe(false)
    expect(isQaFailStatus('control_baseline')).toBe(false)
    expect(isQaFailStatus(null)).toBe(false)
    expect(isQaFailStatus(undefined)).toBe(false)
  })
})
