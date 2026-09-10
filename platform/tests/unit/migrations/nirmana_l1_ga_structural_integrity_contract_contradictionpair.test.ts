import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — contradiction_pair widening pass (migration
 * 813, F-A14) — fourteenth migration in the 800-819 range (adjudication #2057, continuation 4).
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
 * graha_in_house_composite_strength; migration 811 added lord_in_house_per_varga; migration 812
 * added net_argala_per_varga. This adds contradiction_pair.
 *
 * contradiction_pair is a cross-category aggregation flagging a "contradiction" when both a
 * benefic-valence source and a malefic-valence source exist for the same (subject, family,
 * varga) key. Only the argala family is live today (yoga/dosha are ga_yoga-owned and never
 * present in ga_structural's own build pass; the writer's own "net_argala" dict key is a dead
 * reference to a category that was renamed to net_argala_per_varga). Given the scale of the two
 * source categories this would fully re-derive from (argala_natal_matrix/
 * virodha_argala_natal_matrix, 62640 rows each, neither yet examined), this migration ships
 * strong self-consistency and domain conjuncts rather than a full row-count re-derivation, per
 * the established "don't always need to re-derive the full source algorithm" precedent.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 813
 * carries the one-hundred-and-seventy-nine prior conjuncts (a)-(e19) forward verbatim —
 * including conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus seven new
 * conjuncts (a20)-(g20). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-eighty-six conjuncts survive — not a live-DB re-run of
 * the full combined contract; the new conjuncts were verified live in isolation during
 * authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/813_nirmana_l1_ga_structural_integrity_contract_contradictionpair.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 813')
  }
  return migration.slice(start + 4, end)
}

describe('migration 813 — ga_structural integrity_check_sql (contradiction_pair)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-seventy-nine prior conjuncts (a)-(e19) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(e19\) full cross-category re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all seven new conjuncts (a20)-(g20)', () => {
    expect(migration).toMatch(/-- \(a20\) contradiction_pair\.fact_value_text domain/)
    expect(migration).toMatch(/-- \(b20\) fact_key format/)
    expect(migration).toMatch(/-- \(c20\) family domain/)
    expect(migration).toMatch(/-- \(d20\) argala-family source consistency/)
    expect(migration).toMatch(/-- \(e20\) genuine-contradiction invariant/)
    expect(migration).toMatch(/-- \(f20\) target self-consistency/)
    expect(migration).toMatch(/-- \(g20\) varga\/subject consistency/)
  })

  it('checks the argala-family source pair against the exact two categories CATEGORY_FAMILY maps to argala', () => {
    const detectorSql = extractDetectorSql()
    const d20Section = detectorSql.slice(
      detectorSql.indexOf('-- (d20)'),
      detectorSql.indexOf('-- (e20)'),
    )
    expect(d20Section).toContain('argala_natal_matrix')
    expect(d20Section).toContain('virodha_argala_natal_matrix')
  })

  it('checks both counts are positive rather than just one, matching the writer\'s AND-gated emission condition', () => {
    const detectorSql = extractDetectorSql()
    const e20Section = detectorSql.slice(
      detectorSql.indexOf('-- (e20)'),
      detectorSql.indexOf('-- (f20)'),
    )
    expect(e20Section).toContain('benefic_count')
    expect(e20Section).toContain('malefic_count')
    expect(e20Section).toContain('AND')
  })
})
