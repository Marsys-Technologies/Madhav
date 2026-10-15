/**
 * rectification_labels.test.ts — SS N-342 / N-343: query_rectification labels.
 *
 * The candidate list follows the requested ayanamsha (the web bridge injects Lahiri when omitted);
 * the chart-level "best" values are a pooled mean over five ayanamshas and are served with the
 * explicit label "consensus over five ayanamshas". "all" returns the raw list with its own label.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

import { queryRectificationCapability } from '../layers/L4_phala/query_phala_calibration'

type Content = Record<string, unknown>

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockImplementation(async (sql: string) => {
    if (sql.includes('COUNT(*)')) return { rows: [{ total: '37' }] }
    if (sql.includes('phala_rectification_best')) return { rows: [] }
    return { rows: [{ ayanamsha_id: 'lahiri', offset_minutes: 0, lel_fit_score: 0 }] }
  })
})

async function run(args: Record<string, unknown>): Promise<Content> {
  const r = await queryRectificationCapability.handler({ chart_id: 'c1', ...args }, undefined)
  return r.content as Content
}

describe('query_rectification labels', () => {
  it('the pooled best-offset values are labelled "consensus over five ayanamshas"', async () => {
    const c = await run({ ayanamsha_id: 'lahiri_chitrapaksha' })
    expect(c['best_candidate_basis']).toBe('consensus over five ayanamshas')
    expect(String(c['best_candidate_basis_note'])).toContain('not the Lahiri-only reading')
  })

  it('a Lahiri candidate list is labelled Lahiri and queries the stored short code', async () => {
    const c = await run({ ayanamsha_id: 'lahiri_chitrapaksha' })
    expect(c['candidates_basis']).toBe('Lahiri (lahiri_chitrapaksha), the primary reading')
    const listCall = queryMock.mock.calls.find((x) => String(x[0]).includes('FROM phala_rectification') && !String(x[0]).includes('COUNT'))!
    expect(listCall[1]).toContain('lahiri')
  })

  it('another ayanamsha is labelled a cross-check, not the primary reading', async () => {
    const c = await run({ ayanamsha_id: 'krishnamurti' })
    expect(String(c['candidates_basis'])).toContain('cross-check, not the primary reading')
  })

  it('an unfiltered call (the explicit "all" opt-out) says the rows are raw five-ayanamsha rows', async () => {
    const c = await run({})
    expect(String(c['candidates_basis'])).toContain('all five ayanamshas')
  })

  it('the description and schema text name lahiri_chitrapaksha as the default and describe "all"', () => {
    const d = queryRectificationCapability.description
    const s = String((queryRectificationCapability.input_schema as Record<string, { description: string }>)['ayanamsha_id']!.description)
    expect(d).toContain("'lahiri_chitrapaksha'")
    expect(d).toContain('consensus over five ayanamshas')
    expect(s).toContain("default: 'lahiri_chitrapaksha'")
    expect(s).toContain('"all"')
    expect(s).not.toMatch(/omit for all/i)
  })
})
