import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { ASSETS } from '../seed/asset_registry_seed'

/**
 * B1 / Part A — Kāla pre-elevation Phase 1.1.
 *
 * `asset_registry.ka_gochara.target_table` is a STRUCTURAL declaration of which
 * relation the writer produces, and the seed file owns it: the upsert's
 * `ON CONFLICT` clause sets `target_table = EXCLUDED.target_table`
 * (asset_registry_seed.ts, the DO UPDATE block), unlike `count_sql`/`depends_on`
 * /`target_floor`, which are pinned to `asset_registry.<col>` and are therefore
 * migration-governed. That asymmetry is why a DB-only correction of this one
 * column would be silently reverted by the next `runSeed()` — the mechanical
 * reason the W0 disposition recorded `ka_gochara` as "seed target mismatch HELD"
 * rather than simply fixing it, and the reason the fix lands in the seed and a
 * migration together.
 *
 * This test is the detector that keeps them together. It does not restate the
 * table name from prose or from the registry — it reads the WRITER's own
 * `TABLE = "..."` constant out of the Python source and requires the seed row to
 * agree with it. A constant can drift from its source; a reference cannot
 * (CLAUDE.md §N.7 item 3).
 *
 * Why this is not cosmetic: `ka_gochara.py`'s module docstring records a NATIVE
 * RULING ("native ruling point 2") that this writer's only DELETE/SELECT/INSERT
 * target is `kala_gochara_windows_v2` and that it must never name
 * `kala_gochara_windows` — the protected corpus. A registry row declaring the
 * protected table as this asset's output is the exact claim the ruling forbids,
 * and it is the row a future clear-spec or tooling change would read.
 */
const WRITER_PATH = path.resolve(
  __dirname,
  '../../python-sidecar/pipeline/orchestrator/writers/ka_gochara.py'
)

function writerTableConstant(): string {
  const src = readFileSync(WRITER_PATH, 'utf8')
  const m = src.match(/^TABLE\s*=\s*"([a-z0-9_]+)"/m)
  if (!m) throw new Error(`could not find a TABLE = "..." constant in ${WRITER_PATH}`)
  return m[1]
}

describe('ka_gochara registry/writer target parity (B1 Part A)', () => {
  it('the writer names kala_gochara_windows_v2 as its only output relation', () => {
    // Anchors the other assertion: if the writer is ever repointed, this fails
    // first and the repoint is a deliberate, reviewed change rather than a
    // silent one that drags the seed along with it.
    expect(writerTableConstant()).toBe('kala_gochara_windows_v2')
  })

  it('the seed row target_table equals the writer TABLE constant', () => {
    const seedRow = ASSETS.find(a => a.asset_id === 'ka_gochara')
    expect(seedRow, 'ka_gochara must have a seed row').toBeDefined()
    expect(seedRow!.target_table).toBe(writerTableConstant())
  })

  it('the seed row never declares the protected v1 corpus table as its output', () => {
    const seedRow = ASSETS.find(a => a.asset_id === 'ka_gochara')
    expect(seedRow!.target_table).not.toBe('kala_gochara_windows')
  })

  it('the seed count_sql also reads the writer\'s own relation, not the protected one', () => {
    // count_sql is migration-governed on an EXISTING row, so the live DB value is
    // authoritative there (measured 2026-09-22: `... FROM kala_gochara_windows_v2
    // ... generation='2.0'`, which matches the writer exactly). But a brand-new
    // row takes the seed literal verbatim, so a stale literal here is a loaded
    // gun rather than a harmless comment: transformed by
    // `deriveDeleteSqlFromCountSql` it would become
    // `DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='3.0'`
    // — the century materializer's protected production rows.
    const seedRow = ASSETS.find(a => a.asset_id === 'ka_gochara')
    expect(seedRow!.count_sql).toContain('kala_gochara_windows_v2')
    expect(seedRow!.count_sql).not.toMatch(/FROM\s+kala_gochara_windows\s/i)
  })

  it('the RETIRED sweep row stays retired and keeps pointing at the protected corpus', () => {
    // Nothing in this fix may un-retire the sweep or repoint it. `is_active:false`
    // is what the Clear-route filter keys on (Part B), and its target_table/
    // count_sql must keep naming the protected corpus so the row remains an
    // honest tombstone of where that data lives.
    const sweep = ASSETS.find(a => a.asset_id === 'ka_gochara_sweep')
    expect(sweep, 'ka_gochara_sweep must keep a seed row').toBeDefined()
    expect(sweep!.is_active).toBe(false)
    expect(sweep!.catalog_status).toBe('RETIRED')
    expect(sweep!.target_table).toBe('kala_gochara_windows')
    expect(sweep!.count_sql).toContain("generation='v1'")
  })
})
