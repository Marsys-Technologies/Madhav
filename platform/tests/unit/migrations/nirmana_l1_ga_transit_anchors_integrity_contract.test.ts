import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_transit_anchors integrity contract (migration 749, F-A14).
 *
 * ga_transit_anchors's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This
 * textual test verifies the migration's SHAPE -- the two documented conjuncts survive, the
 * contract is read-only and bind-parameter-free per the real elevation-pipeline validator, and no
 * FORENSIC sign assertion was re-introduced (the exact F-D22 landmine this asset already had
 * fixed) -- not a live-DB re-run of the contract itself, which was verified and mutation-tested
 * live against production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/749_nirmana_l1_ga_transit_anchors_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 749')
  }
  return migration.slice(start + 4, end)
}

describe('migration 749 — ga_transit_anchors integrity_check_sql', () => {
  it('targets ga_transit_anchors by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_transit_anchors';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries both documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) natal_degree_absolute must equal/)
    expect(migration).toMatch(/-- \(b\) natal_house_from_moon must equal/)
  })

  it('does not re-introduce a FORENSIC sign assertion — the exact F-D22 landmine already fixed', () => {
    expect(migration).toMatch(/No FORENSIC gate re-encoded here/)
    const detectorSql = extractDetectorSql()
    expect(detectorSql).not.toMatch(/natal_sign\s*=\s*'/i)
    expect(detectorSql).not.toContain('482012f1-710e-4a25-994a-93821f5871aa')
  })

  it('re-derives natal_degree_absolute from graha_position.longitude_sidereal, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("f.fact_category = 'graha_position' AND f.fact_key = 'longitude_sidereal'")
    expect(detectorSql).toContain("WHEN 'rahu' THEN 'RAH_MEAN' WHEN 'ketu' THEN 'KET_MEAN'")
  })

  it('re-derives natal_house_from_moon from the Moon row via a real sign-number mapping', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("m.graha = 'moon'")
    expect(detectorSql).toContain('(((sn_p.num - sn_m.num) % 12 + 12) % 12) + 1')
  })
})
