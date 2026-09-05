import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_vastu integrity contract (migration 741, F-A14).
 *
 * ga_vastu's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the four documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and the FORENSIC
 * gate correctly does NOT re-encode the writer's own REMOVED Sun assertion (which its own
 * docstring documents as astrologically incorrect) -- not a live-DB re-run of the contract
 * itself, which was verified and mutation-tested live against production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/741_nirmana_l1_ga_vastu_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 741')
  }
  return migration.slice(start + 4, end)
}

describe('migration 741 — ga_vastu integrity_check_sql', () => {
  it('targets ga_vastu by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_vastu';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all four documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) indication_tier is a single spec-required constant/)
    expect(migration).toMatch(/-- \(b\) direction vocabulary/)
    expect(migration).toMatch(/-- \(c\) direction_impact must equal/)
    expect(migration).toMatch(/-- \(d\) FORENSIC gate/)
  })

  it('does NOT re-encode the writer\'s own removed Sun assertion in the detector SQL', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).not.toMatch(/graha\s*=\s*'Sun'/)
    // The migration's own prose may still explain why it was removed.
    expect(migration).toMatch(/REMOVED as astrologically incorrect/)
  })

  it('FORENSIC gate applies across all five ayanamshas, unlike ga_medical\'s lahiri-only scope', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("chart_id = '482012f1-710e-4a25-994a-93821f5871aa'")
    expect(detectorSql).not.toContain("ayanamsha_id = 'lahiri_chitrapaksha'")
    expect(detectorSql).toContain("graha = 'Saturn' AND direction_impact <> 'strengthened'")
  })

  it('re-derives direction_impact from the writer\'s own threshold formula, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('condition_score < 0.4')
    expect(detectorSql).toContain('condition_score < 0.7')
    expect(migration).toMatch(/compute_direction_impact/)
  })
})
