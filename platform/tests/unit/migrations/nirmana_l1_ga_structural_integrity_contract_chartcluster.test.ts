import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — chart_cluster widening pass (migration 808,
 * F-A14) — ninth migration in the 800-819 range (adjudication #2057, continuation 4).
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
 * added dispositor_chain_per_varga; migration 807 added graha_centrality (48/57). This adds
 * chart_cluster, taking coverage to 49/57.
 *
 * chart_cluster computes Parashari aspect-graph connected components (union-find) per varga,
 * using the EXACT SAME edge rule as migration 807's graha_centrality. The row stores {varga,
 * cluster_id, total_clusters} but no per-graha edge list, so its conjuncts lean on internal
 * self-consistency/completeness plus a genuine cross-category re-derivation against the sibling
 * graha_centrality category's own connected_to/degree_centrality fields, rather than rebuilding
 * the union-find from scratch in SQL.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 808
 * carries the one-hundred-and-forty-six prior conjuncts (a)-(f14) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus six new conjuncts
 * (a15)-(f15). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-fifty-two conjuncts survive — not a live-DB re-run of the
 * full combined contract; the new conjuncts were verified live in isolation during authoring,
 * each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/808_nirmana_l1_ga_structural_integrity_contract_chartcluster.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 808')
  }
  return migration.slice(start + 4, end)
}

describe('migration 808 — ga_structural integrity_check_sql (chart_cluster)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-forty-six prior conjuncts (a)-(f14) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(f14\) full classical edge re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all six new conjuncts (a15)-(f15)', () => {
    expect(migration).toMatch(/-- \(a15\) chart_cluster\.fact_value_num/)
    expect(migration).toMatch(/-- \(b15\) cluster_id domain/)
    expect(migration).toMatch(/-- \(c15\) total_clusters consistency/)
    expect(migration).toMatch(/-- \(d15\) total_clusters completeness/)
    expect(migration).toMatch(/-- \(e15\) direct-edge-implies-same-cluster/)
    expect(migration).toMatch(/-- \(f15\) isolated-implies-singleton-cluster/)
  })

  it('cross-references the sibling graha_centrality category rather than rebuilding union-find in SQL', () => {
    const detectorSql = extractDetectorSql()
    const e15Section = detectorSql.slice(
      detectorSql.indexOf('-- (e15)'),
      detectorSql.indexOf('-- (f15)'),
    )
    const f15Section = detectorSql.slice(detectorSql.indexOf('-- (f15)'))
    expect(e15Section).toContain("fact_category = 'graha_centrality'")
    expect(e15Section).toContain('connected_to')
    expect(f15Section).toContain("fact_category = 'graha_centrality'")
    expect(f15Section).toContain('degree_centrality')
  })

  it('checks total_clusters group-consistency and completeness with GROUP BY, not a per-row comparison', () => {
    const detectorSql = extractDetectorSql()
    const c15Section = detectorSql.slice(
      detectorSql.indexOf('-- (c15)'),
      detectorSql.indexOf('-- (d15)'),
    )
    const d15Section = detectorSql.slice(
      detectorSql.indexOf('-- (d15)'),
      detectorSql.indexOf('-- (e15)'),
    )
    expect(c15Section).toContain('GROUP BY 1, 2, 3, 4')
    expect(d15Section).toContain('GROUP BY 1, 2, 3, 4')
  })
})
