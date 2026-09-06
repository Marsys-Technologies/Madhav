import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — lord_aspects_lord_per_varga widening pass
 * (migration 805, F-A14) — sixth migration in the 800-819 range (adjudication #2057,
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
 * chart_center_of_gravity; migration 801 added karakatva_strength_per_significance; migration
 * 802 added aspect_received_by_special_point; migration 803 added aspect_jaimini; migration 804
 * added conjunction_per_varga (45/57). This adds lord_aspects_lord_per_varga, taking coverage to
 * 46/57.
 *
 * lord_aspects_lord_per_varga stores, for every ordered pair of house-lords (lord_A, lord_B)
 * where lord_A's classical Parashari aspect lands on lord_B's own house-in-varga, one row. Like
 * migrations 793/802, this category is FULLY SELF-CONTAINED: value_jsonb already stores {varga,
 * lord_a, lord_a_house, lord_b, lord_b_house, aspect_offset, strength} — everything needed to
 * re-verify the row's own geometry and classical aspect membership without any cross-category or
 * cross-asset join. Since SIGN_LORDS maps only to the seven classical grahas, lord_a/lord_b are
 * confirmed live to never include Rahu/Ketu — a narrower domain than migration 802's
 * aspecting_graha, which does include the nodes.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 805
 * carries the one-hundred-and-twenty-five prior conjuncts (a)-(h11) forward verbatim —
 * including conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus eight new
 * conjuncts (a12)-(h12). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-thirty-three conjuncts survive — not a live-DB re-run of
 * the full combined contract; the new conjuncts were verified live in isolation during
 * authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/805_nirmana_l1_ga_structural_integrity_contract_lordaspectslord.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 805')
  }
  return migration.slice(start + 4, end)
}

describe('migration 805 — ga_structural integrity_check_sql (lord_aspects_lord_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-twenty-five prior conjuncts (a)-(h11) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(h11\) house cross-reference, non-D1/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all eight new conjuncts (a12)-(h12)', () => {
    expect(migration).toMatch(/-- \(a12\) lord_aspects_lord_per_varga\.fact_value_num domain/)
    expect(migration).toMatch(/-- \(b12\) fact_value_num must equal value_jsonb\.strength/)
    expect(migration).toMatch(/-- \(c12\) no self-aspect/)
    expect(migration).toMatch(/-- \(d12\) \(lord_a, aspect_offset\) classical validity/)
    expect(migration).toMatch(/-- \(e12\) lord_a\/lord_b domain/)
    expect(migration).toMatch(/-- \(f12\) target_house full re-derivation/)
    expect(migration).toMatch(/-- \(g12\) fact_key format self-consistency/)
    expect(migration).toMatch(/-- \(h12\) fact_subject format self-consistency/)
  })

  it('re-derives target_house purely from the row\'s own stored jsonb fields, no cross-category join', () => {
    const detectorSql = extractDetectorSql()
    const f12Section = detectorSql.slice(
      detectorSql.indexOf('-- (f12)'),
      detectorSql.indexOf('-- (g12)'),
    )
    expect(f12Section).not.toContain('JOIN chart_facts')
    expect(f12Section).toContain("fact_value_jsonb->>'lord_a_house'")
    expect(f12Section).toContain("fact_value_jsonb->>'aspect_offset'")
  })

  it('excludes Rahu/Ketu from the lord domain SQL clause, unlike migration 802\'s aspecting_graha', () => {
    const detectorSql = extractDetectorSql()
    const e12Section = detectorSql.slice(
      detectorSql.indexOf('-- (e12)'),
      detectorSql.indexOf('-- (f12)'),
    )
    expect(e12Section).toContain("'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'")
    const sqlBody = e12Section.slice(e12Section.indexOf('AND NOT EXISTS'))
    expect(sqlBody).not.toContain('Rahu')
  })

  it('checks the classical Parashari offset table hardcoded per lord', () => {
    const detectorSql = extractDetectorSql()
    const d12Section = detectorSql.slice(
      detectorSql.indexOf('-- (d12)'),
      detectorSql.indexOf('-- (e12)'),
    )
    expect(d12Section).toContain('(4, 7, 8)')
    expect(d12Section).toContain('(5, 7, 9)')
    expect(d12Section).toContain('(3, 7, 10)')
  })
})
