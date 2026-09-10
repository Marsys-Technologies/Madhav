import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — karakatva_strength_per_significance widening
 * pass (migration 801, F-A14) — second migration in the 800-819 range (adjudication #2057,
 * continuation 4).
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
 * 791 added the Group O tri-deva bundle; migration 792 added
 * graha_functional_class_per_ascendant; migration 793 added
 * graha_effective_dignity_modified_by_aspects; migration 794 added
 * graha_composite_state_classification; migration 795 added karaka_house_lord_overlap_flag;
 * migration 796 added the Group C Bhava Bala extended bundle; migration 797 added
 * aspect_matrix_summary; migration 798 added the aspect_parashari_given/received bundle;
 * migration 799 added graha_special_state_rollup, discovering F-A18; migration 800 added
 * chart_center_of_gravity (41/57). This adds karakatva_strength_per_significance, taking
 * coverage to 42/57.
 *
 * karakatva_strength_per_significance is emitted by the SAME function as migration 795's
 * karaka_house_lord_overlap_flag (_build_karakatva_rows), but covers all 30
 * KARAKATVA_SIGNIFICANCES (not just the 12 house-mapped ones). natural_karaka re-derives from
 * the writer's own NATURAL_KARAKAS dict (hardcoded as authority); composite_strength re-derives
 * from the natural karaka's own dignity (via migration 794's classical tables, read from
 * graha_position.sign) averaged with its own house-based strength (from
 * graha_position.house_d1) — a genuine two-source cross-field re-derivation.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 801
 * carries the one-hundred-and-one prior conjuncts (a)-(f8) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus four new conjuncts
 * (a9)-(d9). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-five conjuncts survive — not a live-DB re-run of the
 * full combined contract; the new conjuncts were verified live in isolation during authoring,
 * each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/801_nirmana_l1_ga_structural_integrity_contract_karakatvastrength.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 801')
  }
  return migration.slice(start + 4, end)
}

describe('migration 801 — ga_structural integrity_check_sql (karakatva_strength_per_significance)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-one prior conjuncts (a)-(f8) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(f8\) tally-sum invariant/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all four new conjuncts (a9)-(d9)', () => {
    expect(migration).toMatch(/-- \(a9\) karakatva_strength_per_significance\.natural_karaka fact_value_text domain/)
    expect(migration).toMatch(/-- \(b9\) natural_karaka full re-derivation/)
    expect(migration).toMatch(/-- \(c9\) composite_strength domain/)
    expect(migration).toMatch(/-- \(d9\) composite_strength full re-derivation/)
  })

  it('hardcodes the writer\'s own NATURAL_KARAKAS dict for all 30 significances', () => {
    const detectorSql = extractDetectorSql()
    const b9Section = detectorSql.slice(
      detectorSql.indexOf('-- (b9)'),
      detectorSql.indexOf('-- (c9)'),
    )
    for (const signif of [
      'self', 'wealth', 'siblings', 'mother', 'children', 'enemies', 'spouse', 'longevity',
      'luck', 'career', 'gains', 'losses', 'dharma', 'artha', 'kama', 'moksha', 'body',
      'courage', 'intelligence', 'happiness', 'education', 'travel', 'lineage',
      'spiritual_merit', 'obstacles', 'foreign_travel', 'inner_strength', 'creativity',
      'authority', 'liberation',
    ]) {
      expect(b9Section).toContain(`'${signif}'`)
    }
  })

  it('re-derives composite_strength from both the natural karaka\'s own dignity and house, not a restated value', () => {
    const detectorSql = extractDetectorSql()
    const d9Section = detectorSql.slice(detectorSql.indexOf('-- (d9)'))
    expect(d9Section).toContain("fact_category = 'graha_position'")
    expect(d9Section).toContain("fact_key = 'sign'")
    expect(d9Section).toContain("fact_key = 'house_d1'")
    expect(d9Section).toContain('/ 2.0, 4)')
  })
})
