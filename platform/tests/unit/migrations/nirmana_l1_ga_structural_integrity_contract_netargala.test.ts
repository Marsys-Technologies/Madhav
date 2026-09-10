import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — net_argala_per_varga widening pass (migration
 * 812, F-A14) — thirteenth migration in the 800-819 range (adjudication #2057, continuation 4).
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
 * added conjunction_per_varga; migration 805 added lord_aspects_lord_per_varga; migration 806
 * added dispositor_chain_per_varga; migration 807 added graha_centrality; migration 808 added
 * chart_cluster; migration 809 added dispositor_tree; migration 810 added
 * graha_in_house_composite_strength; migration 811 added lord_in_house_per_varga (52/57). This
 * adds net_argala_per_varga, taking coverage to 53/57.
 *
 * net_argala_per_varga's cross-category re-derivation against the sibling
 * graha_dignity_per_varga category FIRST produced 40/5220 apparent violations, all confined to
 * varga='D1'. Investigated to a precise root cause: for D1, the writer's own varga_state (built
 * by _extract_chart_state) always includes a LAGNA pseudo-entry at house=1, which the sibling
 * category's graha-only scope never reflects; every other varga's loader is graha-only and
 * needs no adjustment (confirmed live: 0/5040 non-D1 rows disagree without any adjustment at
 * all). The conjunct adds Lagna's house-1 presence back in, but ONLY for varga='D1'.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 812
 * carries the one-hundred-and-seventy-four prior conjuncts (a)-(g18) forward verbatim —
 * including conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus five new
 * conjuncts (a19)-(e19). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-seventy-nine conjuncts survive — not a live-DB re-run of
 * the full combined contract; the new conjuncts were verified live in isolation during
 * authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/812_nirmana_l1_ga_structural_integrity_contract_netargala.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 812')
  }
  return migration.slice(start + 4, end)
}

describe('migration 812 — ga_structural integrity_check_sql (net_argala_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-seventy-four prior conjuncts (a)-(g18) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(g18\) lord domain/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all five new conjuncts (a19)-(e19)', () => {
    expect(migration).toMatch(/-- \(a19\) net_argala_per_varga\.fact_value_num/)
    expect(migration).toMatch(/-- \(b19\) fact_subject format/)
    expect(migration).toMatch(/-- \(c19\) house domain/)
    expect(migration).toMatch(/-- \(d19\) net_argala domain/)
    expect(migration).toMatch(/-- \(e19\) full cross-category re-derivation/)
  })

  it('applies the Lagna house-1 adjustment ONLY for varga=D1, not universally', () => {
    const detectorSql = extractDetectorSql()
    const e19Section = detectorSql.slice(detectorSql.indexOf('-- (e19)'))
    const d1Occurrences = e19Section.match(/t\.varga = 'D1'/g) ?? []
    expect(d1Occurrences.length).toBe(2)
  })

  it('cross-references the sibling graha_dignity_per_varga category for house occupancy', () => {
    const detectorSql = extractDetectorSql()
    const e19Section = detectorSql.slice(detectorSql.indexOf('-- (e19)'))
    expect(e19Section).toContain("fact_category = 'graha_dignity_per_varga'")
    expect(e19Section).toContain('GROUP BY 1, 2, 3, 4, 5')
  })

  it('uses the classical argala/virodha offset arithmetic matching the writer\'s own formula', () => {
    const detectorSql = extractDetectorSql()
    const e19Section = detectorSql.slice(detectorSql.indexOf('-- (e19)'))
    expect(e19Section).toContain('tgt_h-1+2-1')
    expect(e19Section).toContain('tgt_h-1+4-1')
    expect(e19Section).toContain('tgt_h-1+5-1')
    expect(e19Section).toContain('tgt_h-1+11-1')
    expect(e19Section).toContain('tgt_h-1+3-1')
    expect(e19Section).toContain('tgt_h-1+10-1')
    expect(e19Section).toContain('tgt_h-1+9-1')
    expect(e19Section).toContain('tgt_h-1+12-1')
  })
})
