import { describe, it, expect } from 'vitest'
import { EXPLICIT_CLEAR_OPS, deriveDeleteSqlFromCountSql } from '@/lib/cockpit/assetClearSpec'

/**
 * ga_fact_identity (migration 1262, PR #3073): the Fact Identity Index
 * (public.chart_fact_identity) has NO producing writer in the build (the hand-run
 * G-IDX script fills it), so a cockpit Clear can destroy it and NO build can restore it.
 * Migration 1262's own CLEAR note: "A manual cockpit Clear at layer/global scope derives
 * `DELETE FROM chart_fact_identity WHERE chart_id = $1` from this count_sql ... not restored by
 * any build." The explicit null below stops the DIRECT delete only
 * (the chart_facts ON DELETE CASCADE is a known residual); it is merged BEFORE 1262 applies, so the
 * entry names an asset that is not (yet) in the registry on purpose.
 */

// The exact count_sql migration 1262 registers for the asset.
const GA_FACT_IDENTITY_COUNT_SQL = 'SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1'

describe('EXPLICIT_CLEAR_OPS — ga_fact_identity is an explicit null', () => {
  it('has an entry, and the entry is null (nothing is cleared)', () => {
    expect('ga_fact_identity' in EXPLICIT_CLEAR_OPS).toBe(true)
    expect(EXPLICIT_CLEAR_OPS['ga_fact_identity']).toBeNull()
  })

  it('the null is load-bearing: without it the registry-derived fallback WOULD directly delete the index', () => {
    expect(deriveDeleteSqlFromCountSql(GA_FACT_IDENTITY_COUNT_SQL)).toBe(
      'DELETE FROM chart_fact_identity WHERE chart_id = $1',
    )
  })

  it('no explicit clear op anywhere directly deletes or updates chart_fact_identity (the chart_facts ON DELETE CASCADE is a known residual, not asserted here)', () => {
    for (const [assetId, ops] of Object.entries(EXPLICIT_CLEAR_OPS)) {
      for (const op of ops ?? []) {
        expect(op.sql, `${assetId}: ${op.sql}`).not.toMatch(/chart_fact_identity/i)
        for (const c of op.guard?.cascade ?? []) {
          expect(c, `${assetId} cascade: ${c}`).not.toMatch(/chart_fact_identity/i)
        }
      }
    }
  })
})
