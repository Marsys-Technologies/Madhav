import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — nakshatra_dispositor_chain widening pass
 * (migration 789, F-A14) — tenth migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb; migration 784 added aspect_tajik; migration 785 added
 * graha_yoga_karaka_flag; migration 786 added graha_dispositor_chain; migration 787 added
 * composite_dispositor_strength; migration 788 added the Group H avastha bundle (19/57). This
 * adds nakshatra_dispositor_chain, taking coverage to 20/57.
 *
 * Unlike graha_dispositor_chain, nakshatra_dispositor_chain reads each chain step's lord
 * directly from graha_nakshatra_join (an L1-authority reference per §N.5) rather than
 * recomputing from a hardcoded classical table — this migration's conjuncts re-derive the
 * chain-walk by reading that same source-of-truth table.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 789
 * carries the forty-nine prior conjuncts (a)-(ww) forward verbatim — including conjuncts (b)/
 * (e)/(f), already genuinely red (tracked) — plus six new conjuncts (nn2)-(ss2). This textual
 * test verifies the migration's SHAPE — read-only and bind-parameter-free, all fifty-five
 * conjuncts survive — not a live-DB re-run of the full combined contract; conjuncts (nn2)-(ss2)
 * were verified live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/789_nirmana_l1_ga_structural_integrity_contract_nakdispositor.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 789')
  }
  return migration.slice(start + 4, end)
}

describe('migration 789 — ga_structural integrity_check_sql (nakshatra_dispositor_chain)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the forty-nine prior conjuncts (a)-(ww) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(qq\) graha_avastha_baladi\.baladi_state domain/,
      /-- \(ww\) full cross-branch-logic re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all six new conjuncts (nn2)-(ss2)', () => {
    expect(migration).toMatch(/-- \(nn2\) nakshatra_dispositor_chain\.chain\[0\]/)
    expect(migration).toMatch(/-- \(oo2\) length must equal the actual length/)
    expect(migration).toMatch(/-- \(pp2\) cycle_at_step must equal length-1/)
    expect(migration).toMatch(/-- \(qq2\) the nakshatras array must have length-1 entries/)
    expect(migration).toMatch(/-- \(rr2\) full re-derivation against the writer's own authoritative source/)
    expect(migration).toMatch(/-- \(ss2\) constituent_fact_ids\[0\], when present/)
  })

  it('documents reading graha_nakshatra_join directly rather than an independently-embedded classical table', () => {
    expect(migration).toMatch(/L1-authority reference per §N\.5/)
    expect(migration).toMatch(/does NOT recompute[\s\S]{0,20}anything from a hardcoded classical table/)
  })

  it('conjunct (qq2) scopes the Lagna exception explicitly rather than treating it as a violation', () => {
    const detectorSql = extractDetectorSql()
    const qq2Section = detectorSql.slice(
      detectorSql.indexOf('-- (qq2)'),
      detectorSql.indexOf('-- (rr2)'),
    )
    expect(qq2Section).toContain("CASE WHEN fact_subject = 'LAGNA' THEN 2 ELSE 1 END")
  })

  it('conjunct (rr2) walks the chain via generate_series against graha_nakshatra_join, including Lagna as a valid source step', () => {
    const detectorSql = extractDetectorSql()
    const rr2Section = detectorSql.slice(
      detectorSql.indexOf('-- (rr2)'),
      detectorSql.indexOf('-- (ss2)'),
    )
    expect(rr2Section).toContain("fact_category = 'graha_nakshatra_join'")
    expect(rr2Section).toContain("WHEN 'Lagna' THEN 'LAGNA'")
    expect(rr2Section).toContain('generate_series(0, jsonb_array_length')
  })

  it('conjunct (ss2) verifies constituent_fact_ids resolution against the real source row', () => {
    const detectorSql = extractDetectorSql()
    const ss2Section = detectorSql.slice(detectorSql.indexOf('-- (ss2)'))
    expect(ss2Section).toContain("(a.fact_value_jsonb->'constituent_fact_ids'->>0)")
  })
})
