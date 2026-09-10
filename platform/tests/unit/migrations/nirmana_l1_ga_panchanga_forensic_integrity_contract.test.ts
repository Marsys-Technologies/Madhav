import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_panchanga FORENSIC integrity contract (migration 657, F-A14).
 *
 * ga_panchanga's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- scope is honestly declared (four FORENSIC-anchored
 * categories only, not all 31 this writer emits), the contract is read-only and bind-parameter-
 * free per the real elevation-pipeline validator, and the FORENSIC assertions stay scoped to the
 * canonical chart -- not a live-DB re-run of the contract itself, which was verified and
 * mutation-tested live against production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/657_nirmana_l1_ga_panchanga_forensic_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 657')
  }
  return migration.slice(start + 4, end)
}

describe('migration 657 — ga_panchanga FORENSIC integrity_check_sql', () => {
  it('targets ga_panchanga by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_panchanga';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('declares its scope honestly — 4 of 31 fact_categories, the FORENSIC-anchored ones', () => {
    expect(migration).toMatch(/31 distinct fact_categories/)
    expect(migration).toMatch(/27 categories are NOT covered here/)
  })

  it('asserts all four panchanga FORENSIC anchors, each scoped to the canonical chart', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toMatch(/panchanga_tithi'.*fact_value_text <> 'Shukla Tritiya'/s)
    expect(detectorSql).toMatch(/panchanga_vara'.*fact_value_text <> 'Ravivara'/s)
    expect(detectorSql).toMatch(/panchanga_yoga'.*fact_value_text <> 'Shiva'/s)
    expect(detectorSql).toMatch(/panchanga_karana'.*fact_value_text <> 'Garaja'/s)
    const canonicalChartOccurrences = (detectorSql.match(/482012f1-710e-4a25-994a-93821f5871aa/g) ?? []).length
    expect(canonicalChartOccurrences).toBe(4)
  })

  it('re-derives paksha/number_in_lunar_month from the writer\'s own tithi_num split, not a restated range', () => {
    expect(migration).toMatch(/tithi_num<=15[\s\S]{0,20}Krishna/)
    expect(migration).toMatch(/fact_value_num < 1 OR fact_value_num > 15/)
  })

  it('documents the ayanamsha_id=INVARIANT convention discovered during mutation testing', () => {
    // A first draft assumed a real ayanamsha and matched nothing at all when mutation-testing —
    // the header must record the correction so a future edit doesn't repeat it.
    expect(migration).toMatch(/ayanamsha-independent[\s\S]{0,20}pseudo-value 'INVARIANT'/)
    expect(migration).toMatch(/matched nothing at all/)
  })
})
