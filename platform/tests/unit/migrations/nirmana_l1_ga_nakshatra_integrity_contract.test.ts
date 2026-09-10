import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_nakshatra integrity contract (migration 742, F-A14).
 *
 * ga_nakshatra's integrity_check_sql was NULL (unearned count(*)>0 fallback, §N.8). This textual
 * test verifies the migration's SHAPE -- the four documented conjuncts survive, the contract is
 * read-only and bind-parameter-free per the real elevation-pipeline validator, and the
 * verification-status honesty conjunct's four-pair allowlist matches the writer's actual two real
 * detectors (the second-pass nakshatra/pada re-derivation and the KP significator emitter's own
 * two_pass_verdict) -- not a live-DB re-run of the contract itself, which was verified and
 * mutation-tested live against production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/742_nirmana_l1_ga_nakshatra_integrity_contract.sql'),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 742')
  }
  return migration.slice(start + 4, end)
}

describe('migration 742 — ga_nakshatra integrity_check_sql', () => {
  it('targets ga_nakshatra by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_nakshatra';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries all four documented conjuncts', () => {
    expect(migration).toMatch(/-- \(a\) FORENSIC gate/)
    expect(migration).toMatch(/-- \(b\) verification_pass_status honesty/)
    expect(migration).toMatch(/-- \(c\) nakshatra_id_ref must equal/)
    expect(migration).toMatch(/-- \(d\) cross-ayanamsha sentinel internal consistency/)
  })

  it('FORENSIC gate targets Moon nakshatra_id_ref=25 (Purva Bhadrapada) on the canonical chart, all ayanamshas', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("chart_id = '482012f1-710e-4a25-994a-93821f5871aa'")
    expect(detectorSql).toContain("fact_subject = 'MOON'")
    expect(detectorSql).toContain("fact_key = 'nakshatra_id_ref' AND fact_value_num <> 25")
    expect(detectorSql).not.toMatch(/ayanamsha_id\s*=\s*'lahiri_chitrapaksha'/)
  })

  it("verification-status allowlist matches the writer's exact two real detectors (4 pairs)", () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("(fact_category = 'graha_nakshatra_join' AND fact_key = 'nakshatra_id_ref')")
    expect(detectorSql).toContain("(fact_category = 'graha_pada_join' AND fact_key = 'pada_number_ref')")
    expect(detectorSql).toContain("(fact_category = 'kp_planet_significations' AND fact_key = 'star_lord')")
    expect(detectorSql).toContain("(fact_category = 'kp_planet_significations' AND fact_key = 'sub_lord')")
    expect(detectorSql).toContain("verification_pass_status IN ('two_pass_verified', 'divergent_flagged')")
  })

  it('re-derives nakshatra_id_ref from longitude_sidereal via the 27-fold division formula, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain('360.0/27.0')
    expect(detectorSql).toContain("fact_category = 'graha_position' AND p.fact_key = 'longitude_sidereal'")
  })

  it('cross-ayanamsha sentinel conjunct requires the unanimous "5/5" sibling', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("fact_key = 'stable_nakshatra_id'")
    expect(detectorSql).toContain("fact_key = 'nak_5ay_consistency'")
    expect(detectorSql).toContain("c.fact_value_text = '5/5'")
  })
})
