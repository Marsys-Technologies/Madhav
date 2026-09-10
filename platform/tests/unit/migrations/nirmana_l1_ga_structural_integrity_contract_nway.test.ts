import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — nway_config_per_varga widening pass (migration
 * 780, F-A14) — first migration in the new 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga (7/57). This adds nway_config_per_varga, taking coverage to 8/57.
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 780
 * carries the twelve prior conjuncts (a)-(l) forward verbatim — including conjuncts (b)/(e)/(f),
 * already genuinely red (tracked since migrations 745/756/757) — plus three new conjuncts
 * (m)/(n)/(o). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all fifteen conjuncts survive — not a live-DB re-run of the full combined
 * contract (which cannot currently read true because of (b)/(e)/(f)); conjuncts (m)/(n)/(o) were
 * verified live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/780_nirmana_l1_ga_structural_integrity_contract_nway.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 780')
  }
  return migration.slice(start + 4, end)
}

describe('migration 780 — ga_structural integrity_check_sql (nway_config_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the twelve prior conjuncts (a)-(l) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(j\) graha_yuddha_per_varga\.orb_deg .* must be <= 1\.0/,
      /-- \(l\) graha_yuddha_per_varga\.orb_deg \(varga != 'D1'/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all three new conjuncts (m)/(n)/(o)', () => {
    expect(migration).toMatch(/-- \(m\) nway_config_per_varga\.stellium's fact_value_num/)
    expect(migration).toMatch(/-- \(n\) fact_value_num must equal the length of the value_jsonb\.grahas array/)
    expect(migration).toMatch(/-- \(o\) every graha named in value_jsonb\.grahas \(varga != 'D1'/)
  })

  it('documents the D1 exclusion for (o) as the fourth occurrence of the recognized shape', () => {
    expect(migration).toMatch(/1\/764 violations, on D1/)
    expect(migration).toMatch(/the fourth _per_varga category to hit this exact shape/)
  })

  it('conjunct (m) checks the stellium threshold directly against fact_value_num', () => {
    const detectorSql = extractDetectorSql()
    const mSection = detectorSql.slice(
      detectorSql.indexOf('-- (m)'),
      detectorSql.indexOf('-- (n)'),
    )
    expect(mSection).toContain('fact_value_num < 3')
  })

  it('conjunct (o) joins on every graha in the array via jsonb_array_elements_text, not just the first', () => {
    const detectorSql = extractDetectorSql()
    const oSection = detectorSql.slice(detectorSql.indexOf('-- (o)'))
    expect(oSection).toContain('jsonb_array_elements_text')
    expect(oSection).toContain("gp.fact_key = 'sign'")
    expect(oSection).toContain("split_part(a.fact_subject, '_', 1) <> 'D1'")
  })
})
