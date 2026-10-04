/**
 * compose_large_n — N-91 L2 lineage flag. Its v3 envelope's grounding.fact_ids come from the
 * derivation ledger (L2-derived ids); without the flag the reading_contract would print "grounded
 * in N resolvable L1 fact reference(s)" over possibly stale ids. composeLargeN and the detector's
 * flag are mocked; the envelope assembly is real.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const composeMock = vi.fn()
vi.mock('../instrument', () => ({ composeLargeN: (...a: unknown[]) => composeMock(...a) }))
const lineageMock = vi.fn()
vi.mock('../../provenance/l2_lineage', () => ({ resolveL2LineageFlag: (...a: unknown[]) => lineageMock(...a) }))

import { synthComposeLargeNCapability } from '../capability'
import { judgmentFlag } from '../../envelope'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const answer = {
  contract: { primary_domain: 'marriage' },
  families: [{ total_in_family: 10 }],
  budget: { total_signal_rows_served: 4, total_signal_rows_cap: 60 },
  derivation_ledger: [{ fact_ids: ['f1', 'f2', 'f3'] }, { fact_ids: ['f3', 'f4'] }],
}
const STALE = judgmentFlag('l2_receipts_predate_l1', '2 L2 asset(s) (bo_a, bo_b) were built before 1 L1 asset(s) were rebuilt; cited fact_ids may not resolve until L2 is rebuilt.', 'warning')

beforeEach(() => { composeMock.mockReset(); lineageMock.mockReset(); composeMock.mockResolvedValue(answer) })

async function run(format: 'v3' | 'legacy') {
  const r = await synthComposeLargeNCapability.handler({ chart_id: CHART, question: 'q', response_format: format }, undefined)
  expect(r.is_error).toBe(false)
  return r.content as Record<string, unknown>
}

describe('compose_large_n — L2 lineage flag', () => {
  it('flag unset: v3 reading_contract carries the unchanged "grounded in N resolvable" sentence (N = distinct ledger ids)', async () => {
    lineageMock.mockResolvedValue({ result: { state: 'current' }, flag: null })
    const env = await run('v3')
    expect(lineageMock).toHaveBeenCalledWith(CHART)
    expect(String(env['reading_contract'])).toMatch(/grounded in 4 resolvable L1 fact reference\(s\)/)
    expect(String(env['reading_contract'])).not.toContain('NOT yet anchored')
    expect(env['judgment_flags']).toEqual([])
  })

  it('stale flag: carried in judgment_flags and the reading_contract takes the NOT-anchored branch with the cause', async () => {
    lineageMock.mockResolvedValue({ result: { state: 'stale' }, flag: STALE })
    const env = await run('v3')
    expect(env['judgment_flags']).toEqual([STALE])
    const rc = String(env['reading_contract'])
    expect(rc).toContain('NOT yet anchored')
    expect(rc).toMatch(/Cause: the L2 receipts behind these fact_ids predate/)
    expect(rc).not.toMatch(/grounded in \d+ resolvable/)
  })

  it('legacy format has no reading_contract/grounding sentence (the legacy wire shape ignores v3-only fields), so it makes no echo claim', async () => {
    lineageMock.mockResolvedValue({ result: { state: 'stale' }, flag: STALE })
    const env = await run('legacy')
    expect(env['reading_contract']).toBeUndefined()
  })
})
