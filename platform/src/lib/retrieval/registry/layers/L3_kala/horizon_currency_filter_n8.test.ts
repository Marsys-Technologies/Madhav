/**
 * horizon_currency_filter_n8.test.ts — NIRMĀṆA L3-W3, finding M7.
 * ==========================================================================
 * REGRESSION GUARD for a §N.8 defect found in L3-W1: the three horizon-scanning
 * L3 capabilities (kota_chakra / moorti_nirnaya / vedha_gochara) cap their result
 * at MAX_LIMIT with no cursor, and `kala_now_get` filtered the returned page for
 * `is_current` AFTERWARDS. On a chart with more rows than the cap, current rows
 * were therefore unreachable — and `now.ts` then attached a coverage sentence
 * asserting a *classical absence* ("no vedha ... is currently active — honest
 * empty (the classically normal state on most days)") whose real cause was
 * pagination. No code path could make that sentence read false.
 *
 * Measured on the canonical chart at the time of the fix (live production):
 *   kota_chakra   9 rows genuinely current,  4 reachable through the capped page
 *                 (Moon, Rahu, Saturn, Sun, Venus lost — Saturn was in durgantara,
 *                  the most classically load-bearing Kota reading there is)
 *   moorti        8 current,  7 reachable
 *   vedha_gochara 1 current,  0 reachable
 *
 * The fix: `current_only` pushes the currency predicate into SQL, ahead of the
 * cap, and every response carries an explicit `truncated` flag so a consumer can
 * never report a capped result as a substantive absence.
 *
 * THESE TESTS FAIL WITHOUT THE FIX — the first asserts a WHERE clause that did
 * not exist, the second asserts a response field that did not exist. §N.8: a
 * guard nothing can prove fires is not a guard.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// vi.mock is hoisted above imports, so the factory may not close over a module-scope const.
// vi.hoisted gives the mock a home that is initialised before the hoisted factory runs.
const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryKotaChakraCapability }    from './query_kota_chakra'
import { queryMoortiNirnayaCapability } from './query_moorti_nirnaya'
import { queryVedhaGocharaCapability }  from './query_vedha_gochara'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const AS_OF = '2026-09-05'

/** Row query resolves to `rows`; the COUNT(*) query resolves to `total`. */
function primeDb(rows: Array<Record<string, unknown>>, total: number) {
  mockQuery.mockReset()
  mockQuery.mockImplementation(async (sql: string) =>
    /COUNT\(\*\)/i.test(sql) ? { rows: [{ total: String(total) }] } : { rows },
  )
}

/** Every SQL string the handler issued (row query + count query). */
function issuedSql(): string[] {
  return mockQuery.mock.calls.map((c) => String(c[0]))
}

const CAPS = [
  { name: 'query_kota_chakra',    cap: queryKotaChakraCapability },
  { name: 'query_moorti_nirnaya', cap: queryMoortiNirnayaCapability },
  { name: 'query_vedha_gochara',  cap: queryVedhaGocharaCapability },
] as const

describe('L3 horizon capabilities — currency filter runs in SQL, before the row cap (M7, §N.8)', () => {
  beforeEach(() => mockQuery.mockReset())

  for (const { name, cap } of CAPS) {
    it(`${name}: current_only pushes the window predicate into the WHERE clause`, async () => {
      primeDb([], 0)
      await cap.handler!({ chart_id: CHART, as_of: AS_OF, current_only: true }, undefined)

      const sqls = issuedSql()
      expect(sqls.length).toBeGreaterThan(0)
      // The predicate must appear in BOTH the row query and the count query: if the count
      // ignored it, `truncated` would compare a filtered page against an unfiltered total
      // and report truncation that is not real.
      for (const sql of sqls) {
        expect(sql).toMatch(/window_start\s*<=\s*\$\d+::date\s+AND\s+window_end\s*>=\s*\$\d+::date/)
      }
    })

    it(`${name}: without current_only the predicate is NOT added (existing callers unchanged)`, async () => {
      primeDb([], 0)
      await cap.handler!({ chart_id: CHART, as_of: AS_OF }, undefined)

      // `is_current` is still computed as a SELECT-list expression; what must be absent is the
      // WHERE-clause restriction. Check the count query, which has no SELECT-list expression.
      const countSql = issuedSql().find((s) => /COUNT\(\*\)/i.test(s))!
      expect(countSql).toBeDefined()
      expect(countSql).not.toMatch(/window_start\s*<=/)
    })

    it(`${name}: reports \`truncated\` so a capped page is never readable as an absence`, async () => {
      // One row returned, but the table holds more matches than the page — i.e. truncated.
      primeDb([{ graha: 'Saturn' }], 99)
      const res = await cap.handler!({ chart_id: CHART, as_of: AS_OF, current_only: true }, undefined)
      const content = (res as { content: Record<string, unknown> }).content

      expect(content['truncated']).toBe(true)
      expect(content['total_matching']).toBe(99)

      // And the honest case: nothing dropped.
      primeDb([{ graha: 'Saturn' }], 1)
      const res2 = await cap.handler!({ chart_id: CHART, as_of: AS_OF, current_only: true }, undefined)
      const content2 = (res2 as { content: Record<string, unknown> }).content
      expect(content2['truncated']).toBe(false)
    })

    it(`${name}: declares current_only in its input schema`, () => {
      expect(cap.input_schema).toHaveProperty('current_only')
    })
  }
})
