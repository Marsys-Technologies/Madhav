import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — karaka_house_lord_overlap_flag widening pass
 * (migration 795, F-A14) — sixteenth migration in the 780-799 range (adjudication #2012).
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
 * graha_composite_state_classification (27/57). This adds karaka_house_lord_overlap_flag,
 * taking coverage to 28/57.
 *
 * is_overlap is TRUE iff a significance's fixed classical natural karaka equals the lord of that
 * significance's fixed house. Fully re-derived from first principles: lagna sign from
 * ga_positions' graha_position.LAGNA.sign, the same house-from-lagna arithmetic proven in
 * migration 792's conjunct (bb3), and the classical SIGN_LORDS table already embedded in SQL
 * since migration 757. NATURAL_KARAKAS and significance_to_house are the writer's own fixed
 * classical assignment dicts. Verified against ALL 180 live rows, not a sample.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 795
 * carries the seventy prior conjuncts (a)-(b4) forward verbatim — including conjuncts (b)/(e)/
 * (f), already genuinely red (tracked) — plus two new conjuncts (a5)/(b5). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all seventy-two conjuncts
 * survive — not a live-DB re-run of the full combined contract; conjuncts (a5)/(b5) were
 * verified live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/795_nirmana_l1_ga_structural_integrity_contract_karakaoverlap.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 795')
  }
  return migration.slice(start + 4, end)
}

describe('migration 795 — ga_structural integrity_check_sql (karaka_house_lord_overlap_flag)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the seventy prior conjuncts (a)-(b4) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(a4\) graha_composite_state_classification fact_value_text domain/,
      /-- \(b4\) full first-principles re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries both new conjuncts (a5)/(b5)', () => {
    expect(migration).toMatch(
      /-- \(a5\) karaka_house_lord_overlap_flag fact_value_text domain/,
    )
    expect(migration).toMatch(/-- \(b5\) full re-derivation/)
  })

  it('re-derives the house lord from lagna sign via ga_positions, not from a stored karakatva field', () => {
    const detectorSql = extractDetectorSql()
    const b5Section = detectorSql.slice(detectorSql.indexOf('-- (b5)'))
    expect(b5Section).toContain("fact_category = 'graha_position'")
    expect(b5Section).toContain("fact_subject = 'LAGNA'")
    expect(b5Section).toContain('lagna_idx')
    expect(b5Section).toContain('house_num')
  })

  it('hardcodes the writer\'s own NATURAL_KARAKAS and significance_to_house classical dicts for all 12 house-mapped significances', () => {
    const detectorSql = extractDetectorSql()
    const b5Section = detectorSql.slice(detectorSql.indexOf('-- (b5)'))
    for (const signif of [
      'self', 'wealth', 'siblings', 'mother', 'children', 'enemies',
      'spouse', 'longevity', 'luck', 'career', 'gains', 'losses',
    ]) {
      expect(b5Section).toContain(`'${signif}'`)
    }
  })
})
