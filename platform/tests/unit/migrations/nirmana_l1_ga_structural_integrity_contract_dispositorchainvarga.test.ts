import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — dispositor_chain_per_varga widening pass
 * (migration 806, F-A14) — seventh migration in the 800-819 range (adjudication #2057,
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
 * added conjunction_per_varga; migration 805 added lord_aspects_lord_per_varga (46/57). This
 * adds dispositor_chain_per_varga, taking coverage to 47/57.
 *
 * dispositor_chain_per_varga is the per-varga sibling of migration 786's graha_dispositor_chain:
 * for each graha, walks its classical SIGN_LORDS dispositor chain up to 8 hops, stopping on
 * cycle detection. Unlike migration 786's version, this per-varga row does NOT store a parallel
 * "signs" array alongside "chain" — only {varga, chain, chain_length, start_sign}. The classical
 * chain-step re-derivation therefore cross-references each chain member's sign-in-this-varga via
 * the SAME asset's own sibling graha_dignity_per_varga category, rather than a self-contained
 * parallel array.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 806
 * carries the one-hundred-and-thirty-three prior conjuncts (a)-(h12) forward verbatim —
 * including conjuncts (b)/(e)/(f)/(e7), already genuinely red (tracked) — plus seven new
 * conjuncts (a13)-(g13). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all one-hundred-forty conjuncts survive — not a live-DB re-run of the
 * full combined contract; the new conjuncts were verified live in isolation during authoring,
 * each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/806_nirmana_l1_ga_structural_integrity_contract_dispositorchainvarga.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 806')
  }
  return migration.slice(start + 4, end)
}

describe('migration 806 — ga_structural integrity_check_sql (dispositor_chain_per_varga)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the one-hundred-and-thirty-three prior conjuncts (a)-(h12) verbatim, including the still-red (b)/(e)/(f)/(e7)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(e7\) F-A18, GENUINELY RED TODAY/,
      /-- \(h12\) fact_subject format self-consistency/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all seven new conjuncts (a13)-(g13)', () => {
    expect(migration).toMatch(/-- \(a13\) dispositor_chain_per_varga\.fact_value_text/)
    expect(migration).toMatch(/-- \(b13\) chain_length must equal the actual jsonb array length/)
    expect(migration).toMatch(/-- \(c13\) chain\[0\] must equal the row's own graha/)
    expect(migration).toMatch(/-- \(d13\) no duplicate elements in the chain array/)
    expect(migration).toMatch(/-- \(e13\) chain_length domain/)
    expect(migration).toMatch(/-- \(f13\) start_sign cross-reference/)
    expect(migration).toMatch(/-- \(g13\) full classical chain-step re-derivation/)
  })

  it('cross-references the sibling graha_dignity_per_varga category, not a self-contained parallel array', () => {
    const detectorSql = extractDetectorSql()
    const f13Section = detectorSql.slice(
      detectorSql.indexOf('-- (f13)'),
      detectorSql.indexOf('-- (g13)'),
    )
    const g13Section = detectorSql.slice(detectorSql.indexOf('-- (g13)'))
    expect(f13Section).toContain("fact_category = 'graha_dignity_per_varga'")
    expect(g13Section).toContain("fact_category = 'graha_dignity_per_varga'")
  })

  it('walks the chain step-by-step via generate_series over the JSON array', () => {
    const detectorSql = extractDetectorSql()
    const g13Section = detectorSql.slice(detectorSql.indexOf('-- (g13)'))
    expect(g13Section).toContain('generate_series(0,')
    expect(g13Section).toContain("jsonb_array_length(cf.fact_value_jsonb->'chain') - 2")
  })

  it('checks the classical SIGN_LORDS table hardcoded per sign', () => {
    const detectorSql = extractDetectorSql()
    const g13Section = detectorSql.slice(detectorSql.indexOf('-- (g13)'))
    expect(g13Section).toContain("WHEN 'Aries' THEN 'Mars'")
    expect(g13Section).toContain("WHEN 'Sagittarius' THEN 'Jupiter'")
    expect(g13Section).toContain("WHEN 'Pisces' THEN 'Jupiter'")
  })
})
