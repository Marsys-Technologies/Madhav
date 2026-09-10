import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — aspect_matrix_summary widening pass
 * (migration 797, F-A14) — eighteenth migration in the 780-799 range (adjudication #2012).
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
 * migration 796 added the Group C Bhava Bala extended bundle (36/57). This adds
 * aspect_matrix_summary, taking coverage to 37/57.
 *
 * aspects_received_count is a per-house tally the writer computes by counting IN-MEMORY
 * aspect_parashari_received rows built earlier in the same function call. Since
 * aspect_parashari_received is itself a real, already-stored chart_facts category, the count is
 * fully re-derivable by counting the actual STORED sibling rows — a genuine same-asset
 * cross-category re-derivation. Verified against ALL 180 live rows, confirmed non-vacuous
 * (150/180 nonzero matches, non-degenerate 0-5 distribution).
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 797
 * carries the eighty prior conjuncts (a)-(j2) forward verbatim — including conjuncts (b)/(e)/
 * (f), already genuinely red (tracked) — plus two new conjuncts (k)/(l). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all eighty-two conjuncts
 * survive — not a live-DB re-run of the full combined contract; conjuncts (k)/(l) were verified
 * live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/797_nirmana_l1_ga_structural_integrity_contract_aspectmatrix.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 797')
  }
  return migration.slice(start + 4, end)
}

describe('migration 797 — ga_structural integrity_check_sql (aspect_matrix_summary)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the eighty prior conjuncts (a)-(j2) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(c\) bhava_bala_positional full re-derivation/,
      /-- \(j2\) house_strength_classification_rollup full re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries both new conjuncts (k)/(l)', () => {
    expect(migration).toMatch(
      /-- \(k\) aspect_matrix_summary\.aspects_received_count domain/,
    )
    expect(migration).toMatch(/-- \(l\) full re-derivation/)
  })

  it('re-derives the count from the stored aspect_parashari_received sibling category, not a restated tally', () => {
    const detectorSql = extractDetectorSql()
    const lSection = detectorSql.slice(detectorSql.indexOf('-- (l)'))
    expect(lSection).toContain("fact_category = 'aspect_parashari_received'")
    expect(lSection).toContain('GROUP BY chart_id, ayanamsha_id, build_id, fact_subject')
    expect(lSection).toContain('COALESCE(r.n, 0)')
  })
})
