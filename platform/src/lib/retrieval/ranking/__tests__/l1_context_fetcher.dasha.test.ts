import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { fetchL1Context } from '../l1_context_fetcher'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const AS_OF = '2026-11-21'

describe('NIR-07 fetchL1Context chart_dashas schema & cd_temporal_lookup_idx query', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('queries real columns (level_n, lord_graha) with system_id = vimshottari and maps current_md_lord / current_ad_lord', async () => {
    mockQuery.mockImplementation(async (sql: string) => {
      if (sql.includes('FROM chart_facts')) return { rows: [] }
      if (sql.includes('FROM chart_dashas')) {
        return {
          rows: [
            { level_n: 1, lord_graha: 'SUN' },
            { level_n: 2, lord_graha: 'MOON' },
          ],
        }
      }
      return { rows: [] }
    })

    const ctx = await fetchL1Context(CHART_ID, AYANAMSHA, AS_OF)
    const dashaCall = mockQuery.mock.calls.find(([sql]) => String(sql).includes('FROM chart_dashas'))
    expect(dashaCall).toBeDefined()
    const sql = String(dashaCall![0])
    expect(sql).toContain('SELECT level_n, lord_graha')
    expect(sql).toContain("system_id = 'vimshottari'")
    expect(sql).toContain('level_n IN (1, 2)')
    expect(sql).toContain('ORDER BY level_n ASC')
    expect(sql).not.toMatch(/\bSELECT\s+level\b|\bdasha_lord\b/)
    expect(dashaCall![1]).toEqual([CHART_ID, AYANAMSHA, AS_OF])

    expect(ctx.current_md_lord).toBe('SU')
    expect(ctx.current_ad_lord).toBe('MO')
  })
})
