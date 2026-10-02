import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { EXPLICIT_CLEAR_OPS } from '../../src/lib/cockpit/assetClearSpec'
import { ASSETS } from '../seed/asset_registry_seed'

/**
 * ka_gochara registry identity parity — the row describes what its REGISTERED WRITER writes
 * (migration 1230, reverting the target/count/integrity/clear half of migration 1091's WP10 re-pin).
 *
 * `asset_registry.ka_gochara.target_table` is the CATALOG declaration of the surface this asset is
 * counted and cleared against, and the seed file owns it: the upsert's `ON CONFLICT` clause sets
 * `target_table = EXCLUDED.target_table` (asset_registry_seed.ts, the DO UPDATE block), unlike
 * `count_sql`/`depends_on`/`target_floor`, which are pinned to `asset_registry.<col>` and are
 * therefore migration-governed. That asymmetry is why a DB-only re-pin of this one column would be
 * silently reverted by the next `runSeed()` — the seed literal must carry the same identity the live
 * registry carries.
 *
 * The live identity is now migration 1230's: target_table = the writer's TABLE, count_sql scoped to
 * the writer's GENERATION_V2, restored from kala_gochara_cutover_step05_snapshot. 1091 had pointed the
 * row at the '4.0' surface the cutover scripts write; the registered writer never moved there, so the
 * cockpit counted 0 against rows the writer really wrote, the integrity contract read TRUE over an
 * empty '4.0' scope, and a Clear never touched the writer's own rows (CLAUDE.md N.4 / N.8). The 1091
 * pin returns TOGETHER WITH the writer switch at D-FLIP — then this test is re-pointed in the same
 * change.
 *
 * Every constant below is READ OUT OF THE WRITER MODULE'S OWN SOURCE rather than restated from
 * prose — a constant can drift from its source; a reference cannot (CLAUDE.md §N.7 item 3). That is
 * the binding this file adds: the registry row, the explicit Clear spec and the writer cannot drift
 * apart again without this failing first.
 */
const WRITER_PATH = path.resolve(
  __dirname,
  '../../python-sidecar/pipeline/orchestrator/writers/ka_gochara.py'
)

// GENERATION_V2 is defined in the materializer the writer imports (`from services.w2g.materialize
// import ... GENERATION_V2`), not in the writer file itself.
const MATERIALIZE_PATH = path.resolve(
  __dirname,
  '../../python-sidecar/services/w2g/materialize.py'
)
const CONSTANT_SOURCE: Record<string, string> = {
  TABLE: WRITER_PATH,
  BUILD_STATE_TABLE: WRITER_PATH,
  GENERATION_V2: MATERIALIZE_PATH,
}

function writerConstant(name: string): string {
  const file = CONSTANT_SOURCE[name]
  const src = readFileSync(file, 'utf8')
  const m = src.match(new RegExp(`^${name}\\s*=\\s*"([A-Za-z0-9_.]+)"`, 'm'))
  if (!m) throw new Error(`could not find a ${name} = "..." constant in ${file}`)
  return m[1]
}

function countSqlRelation(countSql: string): string {
  const m = countSql.match(/FROM\s+([a-z0-9_]+)/i)
  if (!m) throw new Error(`could not parse a FROM relation out of count_sql: ${countSql}`)
  return m[1]
}

describe('ka_gochara registry identity parity (the row = the registered writer\'s surface, migration 1230)', () => {
  it('the writer MODULE writes kala_gochara_windows_v2 at generation 2.0 (the surface the row must name)', () => {
    expect(writerConstant('TABLE')).toBe('kala_gochara_windows_v2')
    expect(writerConstant('GENERATION_V2')).toBe('2.0')
    expect(writerConstant('BUILD_STATE_TABLE')).toBe('kala_gochara_v2_build_state')
  })

  it('the seed row counts exactly what the writer writes — relation AND generation read from the writer source', () => {
    const seedRow = ASSETS.find(a => a.asset_id === 'ka_gochara')
    expect(seedRow, 'ka_gochara must have a seed row').toBeDefined()
    expect(seedRow!.target_table).toBe(writerConstant('TABLE'))
    expect(countSqlRelation(seedRow!.count_sql!)).toBe(writerConstant('TABLE'))
    expect(seedRow!.count_sql).toContain(`generation='${writerConstant('GENERATION_V2')}'`)
    expect(seedRow!.count_sql).toMatch(/chart_id=\$1/)
  })

  it('conjunct (j) / N.4: target_table IS the relation count_sql reads — a mismatch can never pass', () => {
    // Derived from the row itself (never restated), and demonstrated on a synthetic mismatch so the
    // assertion is proven able to fail (§N.8: a check that cannot read false is not a signal).
    const seedRow = ASSETS.find(a => a.asset_id === 'ka_gochara')
    expect(seedRow, 'ka_gochara must have a seed row').toBeDefined()
    expect(countSqlRelation(seedRow!.count_sql!)).toBe(seedRow!.target_table)

    // Negative control: the 1091 pair (target + count on the '4.0' surface) is NOT what the writer writes.
    const pin1091 = countSqlRelation(
      "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'"
    )
    expect(pin1091).toBe('kala_gochara_windows')
    expect(pin1091).not.toBe(writerConstant('TABLE'))
    expect(seedRow!.target_table).not.toBe(pin1091)
  })

  it("the explicit Clear spec removes exactly the writer's own rows — its relation, its bookkeeping, its generation", () => {
    const ops = EXPLICIT_CLEAR_OPS['ka_gochara']
    expect(ops, 'ka_gochara must have an explicit clear spec').toBeTruthy()
    const generation = writerConstant('GENERATION_V2')
    expect(ops!.map(op => op.sql)).toEqual([
      `DELETE FROM ${writerConstant('TABLE')} WHERE chart_id = $1 AND generation = '${generation}'`,
      `DELETE FROM ${writerConstant('BUILD_STATE_TABLE')} WHERE chart_id = $1 AND generation = '${generation}'`,
    ])
  })

  it('the RETIRED sweep row stays retired and keeps pointing at the protected corpus', () => {
    // Nothing in this revert may un-retire the sweep or repoint it.
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
