import { beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryUcdCapability } from '../query_ucd'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('NIR-07 query_ucd index-friendly signalSql & vw_chart_digest contract', () => {
  beforeEach(() => {
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] })
  })

  it('uses computed_salience IS NOT NULL and ORDER BY computed_salience DESC (no NULLS LAST) while keeping FROM vw_chart_digest', async () => {
    await queryUcdCapability.handler({ chart_id: CHART_ID, top_k_signals: 10 }, {})

    const sqls = queryMock.mock.calls.map(([sql]) => String(sql))
    const digestSql = sqls.find((s) => s.includes('FROM vw_chart_digest'))
    const signalSql = sqls.find((s) => s.includes('FROM bodha_msr_signals'))

    expect(digestSql).toBeDefined()
    expect(signalSql).toBeDefined()
    expect(signalSql).toContain('AND computed_salience IS NOT NULL')
    expect(signalSql).toContain('ORDER BY computed_salience DESC')
    expect(signalSql).not.toContain('NULLS LAST')
  })
})
