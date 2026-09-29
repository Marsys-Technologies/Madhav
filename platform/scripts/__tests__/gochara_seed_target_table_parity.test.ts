import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { ASSETS } from '../seed/asset_registry_seed'

/**
 * ka_gochara registry identity parity — WP10 re-pin (migration 1091).
 *
 * `asset_registry.ka_gochara.target_table` is the CATALOG declaration of the
 * production surface this asset is counted and cleared against, and the seed
 * file owns it: the upsert's `ON CONFLICT` clause sets
 * `target_table = EXCLUDED.target_table` (asset_registry_seed.ts, the DO UPDATE
 * block), unlike `count_sql`/`depends_on`/`target_floor`, which are pinned to
 * `asset_registry.<col>` and are therefore migration-governed. That asymmetry
 * is why a DB-only re-pin of this one column would be silently reverted by the
 * next `runSeed()` — the seed literal must carry the same identity the live
 * registry carries, or it becomes the revert vector.
 *
 * The live identity is migration 1091's (WP10 step 5, applied 2026-09-24 under
 * PRODUCTION_TRANCHE_1, native-authorised): target_table='kala_gochara_windows',
 * count_sql scoped to generation='4.0', with integrity conjunct (j) requiring
 * target_table = the relation count_sql reads. This test is the standing
 * detector that the seed row agrees and that conjunct (j)'s invariant can never
 * silently reopen.
 *
 * The '4.0' windows for ka_gochara are written by the WP10 cutover scripts, not
 * by the writer module: `scripts/kala_gochara_cutover/step06_candidate_build.py`
 * writes the contacts/coverage ledger and `step06b_windows_projection.py`
 * projects `kala_gochara_windows` under generation '4.0' (its
 * `GENERATION_DEFAULT = "4.0"`), per the WP10 design where the '4.0' authority
 * names ka_gochara (step07_flip_gates.py). This test reads that generation out
 * of the projection writer's own source rather than restating it from prose —
 * a constant can drift from its source; a reference cannot (CLAUDE.md §N.7
 * item 3).
 *
 * Separate, unchanged concern: the writer MODULE `writers/ka_gochara.py` keeps
 * its native-ruled identity (TABLE = "kala_gochara_windows_v2",
 * generation='2.0'; its module docstring records the ruling that no code path
 * of that module ever names kala_gochara_windows). The first test below pins
 * that too, so the two identities — writer-module output vs registry/catalog
 * row — can never be conflated by a future edit dragging one along with the
 * other.
 */
const WRITER_PATH = path.resolve(
  __dirname,
  '../../python-sidecar/pipeline/orchestrator/writers/ka_gochara.py'
)
const CUTOVER_PROJECTION_WRITER_PATH = path.resolve(
  __dirname,
  '../../python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py'
)

function writerTableConstant(): string {
  const src = readFileSync(WRITER_PATH, 'utf8')
  const m = src.match(/^TABLE\s*=\s*"([a-z0-9_]+)"/m)
  if (!m) throw new Error(`could not find a TABLE = "..." constant in ${WRITER_PATH}`)
  return m[1]
}

function cutoverGenerationConstant(): string {
  const src = readFileSync(CUTOVER_PROJECTION_WRITER_PATH, 'utf8')
  const m = src.match(/^GENERATION_DEFAULT\s*=\s*"([0-9.]+)"/m)
  if (!m) {
    throw new Error(
      `could not find a GENERATION_DEFAULT = "..." constant in ${CUTOVER_PROJECTION_WRITER_PATH}`
    )
  }
  return m[1]
}

function countSqlRelation(countSql: string): string {
  const m = countSql.match(/FROM\s+([a-z0-9_]+)/i)
  if (!m) throw new Error(`could not parse a FROM relation out of count_sql: ${countSql}`)
  return m[1]
}

describe('ka_gochara registry identity parity (WP10 re-pin, migration 1091)', () => {
  it('the writer MODULE still names kala_gochara_windows_v2 as its only output relation', () => {
    // The native ruling recorded in ka_gochara.py's module docstring is
    // unchanged: that module writes generation='2.0' to its own _v2 relation
    // and never names kala_gochara_windows. This pin anchors the separation —
    // if the module is ever repointed, this fails first and the repoint is a
    // deliberate, reviewed change.
    expect(writerTableConstant()).toBe('kala_gochara_windows_v2')
  })

  it('the cutover projection writer emits the generation the seed count_sql counts', () => {
    // The '4.0' windows the registry row counts are produced by
    // step06b_windows_projection.py (GENERATION_DEFAULT). Bind the seed's
    // generation literal to that source constant so a '4.1' republish cannot
    // leave the seed pointing at a retired generation.
    const seedRow = ASSETS.find(a => a.asset_id === 'ka_gochara')
    expect(seedRow, 'ka_gochara must have a seed row').toBeDefined()
    expect(cutoverGenerationConstant()).toBe('4.0')
    expect(seedRow!.count_sql).toContain(`generation='${cutoverGenerationConstant()}'`)
  })

  it('the seed row carries the 1091 registry identity (kala_gochara_windows, generation 4.0)', () => {
    const seedRow = ASSETS.find(a => a.asset_id === 'ka_gochara')
    expect(seedRow, 'ka_gochara must have a seed row').toBeDefined()
    expect(seedRow!.target_table).toBe('kala_gochara_windows')
    expect(seedRow!.count_sql).toMatch(/FROM\s+kala_gochara_windows\s/i)
  })

  it('conjunct (j): target_table IS the relation count_sql reads — a mismatch can never pass', () => {
    // 1091's integrity conjunct (j) pins target_table = count_sql relation for
    // the live row; this is the seed-side half of that invariant. Derived from
    // the row itself (never restated), and demonstrated on a synthetic
    // mismatch so the assertion is proven to be able to fail (§N.8: a check
    // that cannot read false is not a signal).
    const seedRow = ASSETS.find(a => a.asset_id === 'ka_gochara')
    expect(seedRow, 'ka_gochara must have a seed row').toBeDefined()
    expect(countSqlRelation(seedRow!.count_sql!)).toBe(seedRow!.target_table)

    // Negative control: the pre-1091 pair (target kala_gochara_windows against
    // a _v2 count) violates the invariant — the exact mismatch 1091 exists to
    // close must NOT satisfy this test's equality.
    const mismatched = countSqlRelation(
      "SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'"
    )
    expect(mismatched).toBe('kala_gochara_windows_v2')
    expect(mismatched === 'kala_gochara_windows').toBe(false)
    expect(seedRow!.target_table).not.toBe(mismatched)
  })

  it('the RETIRED sweep row stays retired and keeps pointing at the protected corpus', () => {
    // Nothing in this re-pin may un-retire the sweep or repoint it.
    // `is_active:false` is what the Clear-route filter keys on, and its
    // target_table/count_sql must keep naming the v1 corpus so the row remains
    // an honest tombstone of where that data lives.
    const sweep = ASSETS.find(a => a.asset_id === 'ka_gochara_sweep')
    expect(sweep, 'ka_gochara_sweep must keep a seed row').toBeDefined()
    expect(sweep!.is_active).toBe(false)
    expect(sweep!.catalog_status).toBe('RETIRED')
    expect(sweep!.target_table).toBe('kala_gochara_windows')
    expect(sweep!.count_sql).toContain("generation='v1'")
  })
})
