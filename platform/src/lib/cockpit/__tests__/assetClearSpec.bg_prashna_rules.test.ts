import { describe, it, expect, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

vi.mock('server-only', () => ({}))

import { EXPLICIT_CLEAR_OPS, deriveDeleteSqlFromCountSql } from '@/lib/cockpit/assetClearSpec'
import { invalidateAssets } from '@/lib/build/assetInvalidation'
import type { Queryable, RegistryEntryWithScope } from '@/lib/build/runPreparation'

/**
 * bg_prashna_rules: a GLOBAL L0 static-reference writer that seeds FIVE tables. Migration 1357 sets its registry
 * target_table to the ONE table its declaration names (bg_prashna_tajik_yogas). With target_table set, the generic
 * fallback (api/cockpit/clear/execute/route.ts, build/assetInvalidation.ts operatorStatements) would resolve to
 * `DELETE FROM bg_prashna_tajik_yogas` only and leave the other four tables populated. The explicit entry clears
 * all five together, so the set can never be left inconsistent.
 */
const FIVE = [
  'bg_prashna_lagna_methods',
  'bg_prashna_tajik_yogas',
  'bg_prashna_significators',
  'bg_prashna_fructification_rules',
  'bg_prashna_special_techniques',
]
// The registered count_sql (scripts/seed/asset_registry_seed.ts) sums exactly the same five tables.
const COUNT_SQL =
  'SELECT (SELECT COUNT(*) FROM bg_prashna_lagna_methods) + (SELECT COUNT(*) FROM bg_prashna_tajik_yogas) + (SELECT COUNT(*) FROM bg_prashna_significators) + (SELECT COUNT(*) FROM bg_prashna_fructification_rules) + (SELECT COUNT(*) FROM bg_prashna_special_techniques) AS count'

const WRITER = join(__dirname, '..', '..', '..', '..', 'python-sidecar', 'brahmagyan', 'l0_prashna.py')

const tablesOf = (ops: Array<{ sql: string }>) => ops.map((op) => op.sql.match(/^DELETE FROM (\w+)$/)?.[1])

describe('EXPLICIT_CLEAR_OPS — bg_prashna_rules clears all five of its tables', () => {
  it('has a non-null entry', () => {
    expect('bg_prashna_rules' in EXPLICIT_CLEAR_OPS).toBe(true)
    expect(EXPLICIT_CLEAR_OPS['bg_prashna_rules']).not.toBeNull()
  })

  it('deletes exactly the five tables, unscoped (global tables carry no chart_id), no JOIN, no guard', () => {
    const ops = EXPLICIT_CLEAR_OPS['bg_prashna_rules']!
    expect(tablesOf(ops)).toEqual(FIVE)
    for (const op of ops) {
      expect(op.sql).not.toContain('$1')
      expect(op.sql).not.toMatch(/\bJOIN\b/i)
      expect(op.sql).not.toMatch(/\bWHERE\b/i)
      expect(op.guard).toBeUndefined()
    }
  })

  it('covers exactly the tables the writer seeds (l0_prashna.py INSERT targets) and the registered count_sql sums', () => {
    const src = readFileSync(WRITER, 'utf8')
    const written = [...src.matchAll(/INSERT INTO (bg_prashna_\w+)/g)].map((m) => m[1])
    expect([...new Set(written)].sort()).toEqual([...FIVE].sort())
    const counted = [...COUNT_SQL.matchAll(/FROM (bg_prashna_\w+)/g)].map((m) => m[1])
    expect(counted.sort()).toEqual([...FIVE].sort())
  })

  it('is load-bearing: the summed count_sql derives no DELETE, and the single-table fallback would clear only 1 of 5', () => {
    expect(deriveDeleteSqlFromCountSql(COUNT_SQL)).toBeNull()
    // what the generic target_table fallback emits for a global asset once migration 1357 sets target_table
    const fallback = `DELETE FROM bg_prashna_tajik_yogas`
    expect(EXPLICIT_CLEAR_OPS['bg_prashna_rules']!.map((o) => o.sql)).not.toEqual([fallback])
    expect(EXPLICIT_CLEAR_OPS['bg_prashna_rules']!.map((o) => o.sql)).toContain(fallback)
  })
})

function recorder() {
  const calls: Array<{ sql: string; params: unknown[] }> = []
  const db: Queryable = {
    query: vi.fn(async (sql: string, params: unknown[] = []) => {
      calls.push({ sql, params })
      return { rows: [], rowCount: 0 }
    }) as unknown as Queryable['query'],
  }
  return { db, calls }
}

describe('invalidateAssets (operator policy, the force_l0 path that can reach a global asset)', () => {
  const prashna = {
    asset_id: 'bg_prashna_rules', layer: 'brahmagyan', depends_on: [], estimated_seconds: 1, scope: 'global', has_writer: true,
    target_table: 'bg_prashna_tajik_yogas', count_sql: COUNT_SQL, natural_key_partition: null,
    asset_kind: 'data', asset_type: 'data', health_probe: null,
  } as unknown as RegistryEntryWithScope

  it('with target_table set (migration 1357) it issues the five DELETEs in one savepoint, not the single-table fallback', async () => {
    const { db, calls } = recorder()
    const result = await invalidateAssets({ db, chartId: 'c-1', assets: [prashna], policy: 'operator-best-effort' })
    expect(result.clearedAssetIds).toEqual(['bg_prashna_rules'])
    expect(calls.map((c) => c.sql)).toEqual([
      'SAVEPOINT cb_0',
      ...FIVE.map((t) => `DELETE FROM ${t}`),
      'RELEASE SAVEPOINT cb_0',
    ])
    for (const c of calls) expect(c.params).toEqual([])
  })

  it('if one of the five DELETEs fails the whole asset rolls back to its savepoint (no half-cleared set)', async () => {
    const calls: string[] = []
    const db = {
      query: vi.fn(async (sql: string) => {
        calls.push(sql)
        if (/DELETE FROM bg_prashna_significators/.test(sql)) throw new Error('boom')
        return { rows: [], rowCount: 0 }
      }),
    } as unknown as Queryable
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const result = await invalidateAssets({ db, chartId: 'c-1', assets: [prashna], policy: 'operator-best-effort' })
    warn.mockRestore()
    expect(result.failedAssetIds).toEqual(['bg_prashna_rules'])
    expect(result.clearedAssetIds).toEqual([])
    expect(calls.slice(-2)).toEqual(['ROLLBACK TO SAVEPOINT cb_0', 'RELEASE SAVEPOINT cb_0'])
  })
})
