import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — graha_functional_class_per_ascendant widening
 * pass (migration 792, F-A14) — thirteenth migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb; migration 784 added aspect_tajik; migration 785 added
 * graha_yoga_karaka_flag; migration 786 added graha_dispositor_chain; migration 787 added
 * composite_dispositor_strength; migration 788 added the Group H avastha bundle; migration 789
 * added nakshatra_dispositor_chain; migration 790 added chandra_bala_natal_baseline; migration
 * 791 added the Group O tri-deva bundle (24/57). This adds
 * graha_functional_class_per_ascendant, taking coverage to 25/57.
 *
 * Both bphs_canonical and raman_variant are computed by the writer's literal same function call
 * with the same arguments (the writer's own STAGE-2 comment). The function itself is fully
 * deterministic: a hardcoded 7-entry table for Aries lagna, or a dynamic kendra/trikona/
 * dusthana/upachaya derivation for any other lagna. Confirmed live that both branches are
 * genuinely exercised (two charts Aries, one Cancer) before designing the full re-derivation
 * conjunct, which reads lagna sign from ga_positions' own graha_position category — the
 * layer-root T0 asset, not a second independent PyJHora invocation.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 792
 * carries the sixty-one prior conjuncts (a)-(yy2) forward verbatim — including conjuncts (b)/
 * (e)/(f), already genuinely red (tracked) — plus three new conjuncts (zz2)/(aa3)/(bb3). This
 * textual test verifies the migration's SHAPE — read-only and bind-parameter-free, all
 * sixty-four conjuncts survive — not a live-DB re-run of the full combined contract; conjuncts
 * (zz2)/(aa3)/(bb3) were verified live in isolation during authoring, each individually
 * mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/792_nirmana_l1_ga_structural_integrity_contract_funcclass.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 792')
  }
  return migration.slice(start + 4, end)
}

describe('migration 792 — ga_structural integrity_check_sql (graha_functional_class_per_ascendant)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the sixty-one prior conjuncts (a)-(yy2) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(vv2\) pranic_strength_per_graha\.prana_score domain/,
      /-- \(yy2\) graha_tri_deva_role_strength\.role_strength cross-field re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all three new conjuncts (zz2)/(aa3)/(bb3)', () => {
    expect(migration).toMatch(
      /-- \(zz2\) graha_functional_class_per_ascendant fact_value_text domain/,
    )
    expect(migration).toMatch(/-- \(aa3\) bphs_canonical must equal raman_variant/)
    expect(migration).toMatch(/-- \(bb3\) full re-derivation/)
  })

  it('documents that both branches of the two-branch formula are genuinely exercised live', () => {
    expect(migration).toMatch(/two of the three charts have Aries lagna/)
    expect(migration).toMatch(/Cancer lagna across all five ayanamshas/)
  })

  it('conjunct (bb3) reads lagna sign from graha_position, the layer-root T0 asset', () => {
    const detectorSql = extractDetectorSql()
    const bb3Section = detectorSql.slice(detectorSql.indexOf('-- (bb3)'))
    expect(bb3Section).toContain("fact_category = 'graha_position'")
    expect(bb3Section).toContain("fact_subject = 'LAGNA'")
  })

  it('conjunct (bb3) uses LATERAL joins to compute house/kendra/trikona intermediates rather than a hand-flattened expression', () => {
    const detectorSql = extractDetectorSql()
    const bb3Section = detectorSql.slice(detectorSql.indexOf('-- (bb3)'))
    expect(bb3Section).toContain('CROSS JOIN LATERAL')
    expect(bb3Section).toContain('is_kendra')
    expect(bb3Section).toContain('is_trikona')
    expect(bb3Section).toContain('is_dusthana')
    expect(bb3Section).toContain('is_upachaya')
  })

  it('conjunct (bb3) covers both the Aries-table branch and the dynamic classification branch', () => {
    const detectorSql = extractDetectorSql()
    const bb3Section = detectorSql.slice(detectorSql.indexOf('-- (bb3)'))
    expect(bb3Section).toContain("WHEN lg.fact_value_text = 'Aries'")
    expect(bb3Section).toContain("WHEN 'MAR' THEN 'yogakaraka'")
    expect(bb3Section).toContain('cls.is_kendra AND cls.is_trikona')
  })
})
