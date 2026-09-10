import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_strength shadbala integrity contract (migration 655, F-A14).
 *
 * ga_strength's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- scope is honestly declared (graha_shadbala_total only,
 * not all 26 fact_categories ga_strength writes), the contract is read-only and bind-parameter-
 * free per the real elevation-pipeline validator, and it does not silently re-encode F-C1 (a
 * finding the authoritative W2 DECIDE record already rules serving-side / L2-owned, not this
 * writer's) as if it were ga_strength's own defect -- not a live-DB re-run of the contract
 * itself, which was verified and mutation-tested live against production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/655_nirmana_l1_ga_strength_shadbala_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 655')
  }
  return migration.slice(start + 4, end)
}

describe('migration 655 — ga_strength graha_shadbala_total integrity_check_sql', () => {
  it('targets ga_strength by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_strength';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all three documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) the writer's own formula/)
    expect(migration).toMatch(/-- \(b\) required_rupa's ayanamsha-independence/)
    expect(migration).toMatch(/-- \(c\) range guard/)
  })

  it('declares its scope honestly — graha_shadbala_total only, 25 other categories NOT covered', () => {
    expect(migration).toMatch(/26 distinct fact_categories/)
    expect(migration).toMatch(/25 categories are NOT covered here/)
  })

  it('does NOT re-encode F-C1 as this writer\'s own defect — cites the W2 ruling and the L2 file', () => {
    expect(migration).toMatch(/rebuild_only/)
    expect(migration).toMatch(/serving-side/)
    expect(migration).toMatch(/layers\/L2_bodha\//)
    // Never assert anything about deriveShadbalaWeakestGraha or a "weakest graha" selection in
    // the DETECTOR SQL itself — that logic belongs to L2's query_ucd.ts, not this contract. The
    // migration's own prose header may still name the function to explain the F-C1 context.
    expect(extractDetectorSql()).not.toMatch(/deriveShadbalaWeakestGraha/)
    expect(extractDetectorSql()).not.toMatch(/MIN\(/i)
  })

  it('joins required_rupa on the INVARIANT pseudo-ayanamsha, not the row\'s own ayanamsha_id', () => {
    // The mutation-caught mistake this migration's header documents: a same-ayanamsha join
    // produces 105 false mismatches because required_rupa is stored once per chart under
    // ayanamsha_id='INVARIANT', not once per ayanamsha.
    expect(migration).toMatch(/req\.ayanamsha_id = 'INVARIANT'/)
    expect(migration).not.toMatch(/req\.ayanamsha_id = r\.ayanamsha_id/)
  })
})
