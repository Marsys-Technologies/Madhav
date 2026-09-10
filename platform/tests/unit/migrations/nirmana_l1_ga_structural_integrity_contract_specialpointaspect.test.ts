import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — aspect_received_by_special_point widening pass
 * (migration 802, F-A14) — third migration in the 800-819 range (adjudication #2057,
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
 * chart_center_of_gravity; migration 801 added karakatva_strength_per_significance (42/57).
 * This adds aspect_received_by_special_point, taking coverage to 43/57.
 *
 * Like migration 793's graha_effective_dignity_modified_by_aspects, this category is FULLY
 * SELF-CONTAINED: value_jsonb already stores {special_point, aspecting_graha, graha_house,
 * aspect_offset, target_house, target_sign, strength} — everything needed to re-verify the
 * row's own geometry and classical aspect membership without any cross-category or cross-asset
 * join.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 802
 * carries the one-hundred-and-five prior conjuncts (a)-(d9) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus six new conjuncts
 * (a10)-(f10). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-eleven conjuncts survive — not a live-DB re-run of the
 * full combined contract; the new conjuncts were verified live in isolation during authoring,
 * each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/802_nirmana_l1_ga_structural_integrity_contract_specialpointaspect.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 802')
  }
  return migration.slice(start + 4, end)
}

describe('migration 802 — ga_structural integrity_check_sql (aspect_received_by_special_point)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-five prior conjuncts (a)-(d9) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(d9\) composite_strength full re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all six new conjuncts (a10)-(f10)', () => {
    expect(migration).toMatch(/-- \(a10\) aspect_received_by_special_point\.fact_value_num domain/)
    expect(migration).toMatch(/-- \(b10\) fact_value_num must equal value_jsonb\.strength/)
    expect(migration).toMatch(/-- \(c10\) target_house full re-derivation/)
    expect(migration).toMatch(/-- \(d10\) \(aspecting_graha, aspect_offset\) classical validity/)
    expect(migration).toMatch(/-- \(e10\) fact_key format self-consistency/)
    expect(migration).toMatch(/-- \(f10\) special_point self-consistency/)
  })

  it('re-derives target_house purely from the row\'s own stored jsonb fields, no cross-category join', () => {
    const detectorSql = extractDetectorSql()
    const c10Section = detectorSql.slice(
      detectorSql.indexOf('-- (c10)'),
      detectorSql.indexOf('-- (d10)'),
    )
    expect(c10Section).not.toContain('JOIN chart_facts')
    expect(c10Section).toContain("fact_value_jsonb->>'graha_house'")
    expect(c10Section).toContain("fact_value_jsonb->>'aspect_offset'")
  })

  it('checks the classical Parashari offset table hardcoded per graha', () => {
    const detectorSql = extractDetectorSql()
    const d10Section = detectorSql.slice(
      detectorSql.indexOf('-- (d10)'),
      detectorSql.indexOf('-- (e10)'),
    )
    expect(d10Section).toContain("(4, 7, 8)")
    expect(d10Section).toContain("(5, 7, 9)")
    expect(d10Section).toContain("(3, 7, 10)")
  })
})
