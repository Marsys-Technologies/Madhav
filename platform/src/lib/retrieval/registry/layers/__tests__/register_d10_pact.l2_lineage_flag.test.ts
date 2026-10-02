/**
 * register_d10_pact.l2_lineage_flag.test.ts — N-91 echo-class disclosure, pact_query wiring.
 *
 * pact_query's fact_id_refs are judgment_query's (L2-echoing) ids plus its own. pact COPIES the
 * lineage flag out of the in-process judgment_query result (no second detector query) into its own
 * judgment_flags, which every non-denied return spreads; the denied_at_promise return spreads
 * judgment_query's flags directly. DB-free (register_d10_pact.test.ts pattern).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => mockQuery(...args) }))

const mockJudgmentHandler = vi.fn()
vi.mock('../register_d9_judgment', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../register_d9_judgment')>()
  return {
    ...actual,
    judgmentQueryCapability: { handler: (...args: unknown[]) => mockJudgmentHandler(...args) },
  }
})

import { pactQueryCapability } from '../register_d10_pact'
import { judgmentFlag } from '../../../envelope'

const SERVED_BUILD_ID = '11111111-1111-4111-8111-111111111111'
function servedReceiptRow() {
  return {
    asset_id: 'ga_structural', partition_key: '__whole_asset__', receipt_version: 'v1',
    receipt_build_id: SERVED_BUILD_ID, rows_build_id: SERVED_BUILD_ID, receipt_state: 'proven',
    freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
    receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build',
    observed_at: '2026-09-07T00:00:00Z',
  }
}

const STALE = judgmentFlag('l2_receipts_predate_l1', 'bo_laksana built against pre-rebuild ga_structural', 'warning')
const FAILED = judgmentFlag('l2_lineage_check_failed', 'permission denied', 'warning')

function judgmentContent(over: Record<string, unknown> = {}) {
  return {
    chart_id: CHART_ID,
    ayanamsha_id: 'lahiri_chitrapaksha',
    about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership', karakas: ['Venus'], operative_varga: 'D9' },
    verdict: { verdict_grade: 'convergent_strong', composite_score: 3.0 },
    receipt: { varga_confirmed: 'D9✓', bhanga_checked: false },
    checklist: {
      bhavesha_condition: { from_lagna: { graha: 'Venus' } },
      timing_hooks: { current: [], mahadasha_windows_by_graha: {} },
    },
    judgment_flags: [],
    fact_id_refs: ['f-1'],
    resolution_chains: {},
    ...over,
  }
}

beforeEach(() => {
  vi.unstubAllGlobals()
  mockQuery.mockReset()
  mockQuery.mockResolvedValueOnce({ rows: [servedReceiptRow()] })
  mockJudgmentHandler.mockReset()
})

type Flag = { code: string } | string
const codesOf = (c: Record<string, unknown>) => (c['judgment_flags'] as Flag[]).map(f => (typeof f === 'string' ? f : f.code))
const lineageQueries = () => mockQuery.mock.calls.filter(([sql]) => String(sql).includes('l1_pins')).length

describe('pact_query — L2 lineage flag copied from judgment_query', () => {
  it('chain stopped at CONFIRMATION (flags spread from pact\'s own list): the stale flag is present exactly once, beside the halt flag', async () => {
    mockJudgmentHandler.mockResolvedValue({ is_error: false, content: judgmentContent({ judgment_flags: [STALE] }) })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-1', fact_value_text: 'debilitated' }] })

    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('denied_at_confirmation')
    const codes = codesOf(content)
    expect(codes.filter(c => c === 'l2_receipts_predate_l1')).toHaveLength(1)
    expect(codes).toContain('pact_halted_at_confirmation')
    // no second detector query: pact never runs the lineage SELECT itself
    expect(lineageQueries()).toBe(0)
  })

  it('chain complete path: the flag is on the returned list (chain_pending_activation return)', async () => {
    mockJudgmentHandler.mockResolvedValue({
      is_error: false,
      content: judgmentContent({
        judgment_flags: [STALE],
        checklist: {
          bhavesha_condition: { from_lagna: { graha: 'Venus' } },
          timing_hooks: { current: [], mahadasha_windows_by_graha: { Venus: [{ start_date: '2099-01-01', end_date: '2119-01-01' }] } },
        },
      }),
    })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-2', fact_value_text: 'exalted' }] })
    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage', as_of_date: '2026-07-08' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('chain_pending_activation')
    expect(codesOf(content)).toContain('l2_receipts_predate_l1')
  })

  it('denied_at_promise (returns judgment_query\'s own flags): the flag is present exactly once, not duplicated', async () => {
    mockJudgmentHandler.mockResolvedValue({
      is_error: false,
      content: judgmentContent({ verdict: { verdict_grade: 'contested', composite_score: -1.5 }, judgment_flags: [STALE] }),
    })
    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['pact_status']).toBe('denied_at_promise')
    expect(codesOf(content).filter(c => c === 'l2_receipts_predate_l1')).toHaveLength(1)
  })

  it('the fail-closed flag (l2_lineage_check_failed) is copied too', async () => {
    mockJudgmentHandler.mockResolvedValue({ is_error: false, content: judgmentContent({ judgment_flags: [FAILED] }) })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-1', fact_value_text: 'debilitated' }] })
    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage' }, undefined)
    expect(codesOf(result.content as Record<string, unknown>)).toContain('l2_lineage_check_failed')
  })

  it('judgment_query clean (no lineage flag): pact does not invent one', async () => {
    mockJudgmentHandler.mockResolvedValue({ is_error: false, content: judgmentContent({ judgment_flags: [judgmentFlag('karaka_unresolved', 'x')] }) })
    mockQuery.mockResolvedValue({ rows: [{ fact_id: 'df-1', fact_value_text: 'debilitated' }] })
    const result = await pactQueryCapability.handler({ chart_id: CHART_ID, domain: 'marriage' }, undefined)
    const codes = codesOf(result.content as Record<string, unknown>)
    expect(codes).not.toContain('l2_receipts_predate_l1')
    expect(codes).not.toContain('l2_lineage_check_failed')
  })
})
