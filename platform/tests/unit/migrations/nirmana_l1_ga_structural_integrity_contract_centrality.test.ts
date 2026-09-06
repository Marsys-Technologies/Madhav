import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — graha_centrality widening pass (migration 807,
 * F-A14) — eighth migration in the 800-819 range (adjudication #2057, continuation 4).
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
 * added dispositor_chain_per_varga (47/57). This adds graha_centrality, taking coverage to
 * 48/57.
 *
 * graha_centrality computes, per varga, an undirected Parashari aspect-graph degree centrality
 * per graha. The row stores {varga, degree_centrality, connected_to} but not the graha's own
 * house/sign, so the full classical edge re-derivation cross-references the sibling
 * graha_dignity_per_varga category's own house/sign fields for both grahas in every edge. A
 * modulo sign-bug was caught during authoring: SQL's `%` follows the dividend's sign (unlike
 * Python's floor-mod), so the naive offset formula produced 2338 false violations across 11500
 * live edges before being fixed to a safe-wraparound `MOD(diff + 120, 12) + 1` form.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 807
 * carries the one-hundred-and-forty prior conjuncts (a)-(g13) forward verbatim — including
 * conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus six new conjuncts
 * (a14)-(f14). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-forty-six conjuncts survive — not a live-DB re-run of the
 * full combined contract; the new conjuncts were verified live in isolation during authoring,
 * each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/807_nirmana_l1_ga_structural_integrity_contract_centrality.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 807')
  }
  return migration.slice(start + 4, end)
}

describe('migration 807 — ga_structural integrity_check_sql (graha_centrality)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-forty prior conjuncts (a)-(g13) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(g13\) full classical chain-step re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all six new conjuncts (a14)-(f14)', () => {
    expect(migration).toMatch(/-- \(a14\) graha_centrality\.fact_value_num/)
    expect(migration).toMatch(/-- \(b14\) degree_centrality must equal the actual jsonb array length/)
    expect(migration).toMatch(/-- \(c14\) no self in connected_to/)
    expect(migration).toMatch(/-- \(d14\) symmetric mutual invariant/)
    expect(migration).toMatch(/-- \(e14\) degree_centrality domain/)
    expect(migration).toMatch(/-- \(f14\) full classical edge re-derivation/)
  })

  it('uses safe-wraparound modulo arithmetic, not the sign-following SQL % operator', () => {
    const detectorSql = extractDetectorSql()
    const f14Section = detectorSql.slice(detectorSql.indexOf('-- (f14)'))
    expect(f14Section).toContain('MOD(j.h2::int - j.h1::int + 120, 12)')
    expect(f14Section).toContain('MOD(j.h1::int - j.h2::int + 120, 12)')
    expect(f14Section).not.toMatch(/h2::int - j\.h1::int\) % 12/)
  })

  it('cross-references the sibling graha_dignity_per_varga category for both grahas in an edge', () => {
    const detectorSql = extractDetectorSql()
    const f14Section = detectorSql.slice(detectorSql.indexOf('-- (f14)'))
    const occurrences = f14Section.match(/fact_category = 'graha_dignity_per_varga'/g) ?? []
    expect(occurrences.length).toBe(2)
  })

  it('checks the classical Parashari offset table hardcoded per graha', () => {
    const detectorSql = extractDetectorSql()
    const f14Section = detectorSql.slice(detectorSql.indexOf('-- (f14)'))
    expect(f14Section).toContain('ARRAY[4,7,8]')
    expect(f14Section).toContain('ARRAY[5,7,9]')
    expect(f14Section).toContain('ARRAY[3,7,10]')
  })
})
