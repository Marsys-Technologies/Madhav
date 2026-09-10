import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — Group O Tri-deva bundle widening pass
 * (migration 791, F-A14) — twelfth migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb; migration 784 added aspect_tajik; migration 785 added
 * graha_yoga_karaka_flag; migration 786 added graha_dispositor_chain; migration 787 added
 * composite_dispositor_strength; migration 788 added the Group H avastha bundle; migration 789
 * added nakshatra_dispositor_chain; migration 790 added chandra_bala_natal_baseline (21/57).
 * This adds THREE categories at once — pranic_strength_per_graha,
 * jaimini_tri_deva_role_per_graha, graha_tri_deva_role_strength — taking coverage to 24/57.
 *
 * All three are emitted by the same _build_esoteric_rows loop (Group O); bundled here because
 * graha_tri_deva_role_strength has a genuine, direct cross-field dependency on both siblings.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 791
 * carries the fifty-seven prior conjuncts (a)-(uu2) forward verbatim — including conjuncts (b)/
 * (e)/(f), already genuinely red (tracked) — plus four new conjuncts (vv2)-(yy2). This textual
 * test verifies the migration's SHAPE — read-only and bind-parameter-free, all sixty-one
 * conjuncts survive — not a live-DB re-run of the full combined contract; conjuncts (vv2)-(yy2)
 * were verified live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/791_nirmana_l1_ga_structural_integrity_contract_tridevabundle.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 791')
  }
  return migration.slice(start + 4, end)
}

describe('migration 791 — ga_structural integrity_check_sql (Group O Tri-deva bundle)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the fifty-seven prior conjuncts (a)-(uu2) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(tt2\) chandra_bala_natal_baseline\.classification domain/,
      /-- \(uu2\) chandra_bala_natal_baseline\.classification must equal/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all four new conjuncts (vv2)-(yy2)', () => {
    expect(migration).toMatch(/-- \(vv2\) pranic_strength_per_graha\.prana_score domain/)
    expect(migration).toMatch(/-- \(ww2\) jaimini_tri_deva_role_per_graha\.tri_deva_role domain/)
    expect(migration).toMatch(/-- \(xx2\) jaimini_tri_deva_role_per_graha\.tri_deva_role full re-derivation/)
    expect(migration).toMatch(/-- \(yy2\) graha_tri_deva_role_strength\.role_strength cross-field re-derivation/)
  })

  it('documents bundling three categories as a cohesive unit due to a real cross-field dependency', () => {
    expect(migration).toMatch(/This adds THREE categories at once/)
    expect(migration).toMatch(/genuine, direct cross-field dependency/)
  })

  it('documents the Jupiter dual-membership tie-break confirmed against live data, not assumed', () => {
    expect(migration).toMatch(/BOTH TRI_DEVA_ROLES\["brahma"\] and TRI_DEVA_ROLES\["vishnu"\]/)
    expect(migration).toMatch(/confirmed against all 135 live rows/)
  })

  it('conjunct (xx2) resolves Jupiter to brahma, not vishnu, matching the writer\'s dict-order tie-break', () => {
    const detectorSql = extractDetectorSql()
    const xx2Section = detectorSql.slice(
      detectorSql.indexOf('-- (xx2)'),
      detectorSql.indexOf('-- (yy2)'),
    )
    expect(xx2Section).toContain("WHEN fact_subject IN ('JUP', 'VEN', 'MER') THEN 'brahma'")
    expect(xx2Section).toContain("WHEN fact_subject IN ('SUN', 'MOON') THEN 'vishnu'")
  })

  it('conjunct (yy2) joins both sibling categories to re-derive role_strength', () => {
    const detectorSql = extractDetectorSql()
    const yy2Section = detectorSql.slice(detectorSql.indexOf('-- (yy2)'))
    expect(yy2Section).toContain("fact_category = 'pranic_strength_per_graha'")
    expect(yy2Section).toContain("fact_category = 'jaimini_tri_deva_role_per_graha'")
    expect(yy2Section).toContain("WHEN 'brahma' THEN 1.1 WHEN 'vishnu' THEN 1.2 WHEN 'shiva' THEN 0.9")
  })
})
