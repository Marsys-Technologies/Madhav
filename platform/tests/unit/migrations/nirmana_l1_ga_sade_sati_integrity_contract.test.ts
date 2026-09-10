import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_sade_sati integrity contract (migration 748, F-A14).
 *
 * ga_sade_sati's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the three documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and the base
 * intensity lookup table matches the writer's own PHASE_QUARTER_INTENSITY constants -- not a
 * live-DB re-run of the contract itself, which was verified and mutation-tested live against
 * production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/748_nirmana_l1_ga_sade_sati_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 748')
  }
  return migration.slice(start + 4, end)
}

describe('migration 748 — ga_sade_sati integrity_check_sql', () => {
  it('targets ga_sade_sati by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_sade_sati';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all three documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) quarter_intensity_rationale_jsonb's first element/)
    expect(migration).toMatch(/-- \(b\) cycle_start_iso must precede cycle_end_iso/)
    expect(migration).toMatch(/-- \(c\) duration_days must equal/)
  })

  it("matches the writer's own PHASE_QUARTER_INTENSITY base table exactly (12 phase/quarter pairs)", () => {
    const detectorSql = extractDetectorSql()
    const pairs = [
      ["VISHAKHA", 1, "Medium"], ["VISHAKHA", 2, "Low"], ["VISHAKHA", 3, "Low"], ["VISHAKHA", 4, "Medium"],
      ["JANMA", 1, "High"], ["JANMA", 2, "High"], ["JANMA", 3, "High"], ["JANMA", 4, "Medium"],
      ["ANUMUKHA", 1, "Medium"], ["ANUMUKHA", 2, "Low"], ["ANUMUKHA", 3, "Low"], ["ANUMUKHA", 4, "Low"],
    ] as const
    for (const [phase, quarter, expected] of pairs) {
      expect(detectorSql).toContain(`('${phase}',${quarter},'${expected}')`)
    }
  })

  it('re-derives the cycle temporal ordering and duration from stored ISO timestamps, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("s.fact_value_text::timestamptz >= e.fact_value_text::timestamptz")
    expect(detectorSql).toContain('EXTRACT(EPOCH FROM')
  })
})
