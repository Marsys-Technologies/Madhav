import { describe, it, expect } from 'vitest'
import { EXPLICIT_CLEAR_OPS, deriveDeleteSqlFromCountSql } from '@/lib/cockpit/assetClearSpec'

/**
 * ga_fact_identity: migration 1262 registered the Fact Identity Index (public.chart_fact_identity) with
 * has_writer=false, so its Clear was an explicit null (no build could restore a deleted index).
 * Migration 1333 gives it a REGISTERED WRITER (ga_fact_identity, runs after every chart_facts writer), so the
 * index is a rebuildable cache like any other writer output and its Clear is a real, chart-scoped DELETE.
 * CLEAR_SPEC_MISSING (strict correction policy) would otherwise throw for a writer asset with a null spec.
 */

// The exact count_sql migration 1262 registers for the asset (1333 leaves it unchanged).
const GA_FACT_IDENTITY_COUNT_SQL = 'SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1'

describe('EXPLICIT_CLEAR_OPS — ga_fact_identity has a real chart-scoped spec (it has a writer since migration 1333)', () => {
  it('has an entry, and it is no longer null', () => {
    expect('ga_fact_identity' in EXPLICIT_CLEAR_OPS).toBe(true)
    expect(EXPLICIT_CLEAR_OPS['ga_fact_identity']).not.toBeNull()
  })

  it('is exactly one DELETE, scoped to the chart, single table, no JOIN', () => {
    expect(EXPLICIT_CLEAR_OPS['ga_fact_identity']).toEqual([{ sql: 'DELETE FROM chart_fact_identity WHERE chart_id = $1' }])
  })

  it('equals the statement the registered count_sql would derive (no silent drift between the two)', () => {
    expect(deriveDeleteSqlFromCountSql(GA_FACT_IDENTITY_COUNT_SQL)).toBe(EXPLICIT_CLEAR_OPS['ga_fact_identity']![0].sql)
  })

  it('no OTHER asset’s clear op touches chart_fact_identity directly or through a guard cascade', () => {
    for (const [assetId, ops] of Object.entries(EXPLICIT_CLEAR_OPS)) {
      if (assetId === 'ga_fact_identity') continue
      for (const op of ops ?? []) {
        expect(op.sql, `${assetId}: ${op.sql}`).not.toMatch(/chart_fact_identity/i)
        for (const c of op.guard?.cascade ?? []) {
          expect(c, `${assetId} cascade: ${c}`).not.toMatch(/chart_fact_identity/i)
        }
      }
    }
  })
})
