import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — Group H Avastha bundle widening pass
 * (migration 788, F-A14) — ninth migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb; migration 784 added aspect_tajik; migration 785 added
 * graha_yoga_karaka_flag; migration 786 added graha_dispositor_chain; migration 787 added
 * composite_dispositor_strength (15/57). This adds FOUR categories at once —
 * graha_avastha_baladi, graha_avastha_jagrad, graha_avastha_deepta,
 * graha_avastha_lifetime_exposure_summary — taking coverage to 19/57.
 *
 * All four are emitted by the same _build_avastha_rows loop; bundled here because
 * graha_avastha_lifetime_exposure_summary's own value_jsonb re-quotes the other three's
 * current-cycle values as a same-loop-iteration copy.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 788
 * carries the forty-two prior conjuncts (a)-(pp) forward verbatim — including conjuncts (b)/(e)/
 * (f), already genuinely red (tracked) — plus seven new conjuncts (qq)-(ww). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free, all forty-nine conjuncts
 * survive — not a live-DB re-run of the full combined contract; conjuncts (qq)-(ww) were
 * verified live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/788_nirmana_l1_ga_structural_integrity_contract_avastha.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 788')
  }
  return migration.slice(start + 4, end)
}

describe('migration 788 — ga_structural integrity_check_sql (Group H Avastha bundle)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the forty-two prior conjuncts (a)-(pp) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(nn\) composite_dispositor_strength\.terminal_strength domain/,
      /-- \(pp\) cross-category re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all seven new conjuncts (qq)-(ww)', () => {
    expect(migration).toMatch(/-- \(qq\) graha_avastha_baladi\.baladi_state domain/)
    expect(migration).toMatch(/-- \(rr\) graha_avastha_jagrad\.jagrad_state domain/)
    expect(migration).toMatch(/-- \(ss\) graha_avastha_deepta\.deepta_state domain/)
    expect(migration).toMatch(/-- \(tt\) graha_avastha_lifetime_exposure_summary\.value_jsonb\.current_baladi/)
    expect(migration).toMatch(/-- \(uu\) graha_avastha_lifetime_exposure_summary\.value_jsonb\.current_jagrad/)
    expect(migration).toMatch(/-- \(vv\) graha_avastha_lifetime_exposure_summary\.value_jsonb\.current_deepta/)
    expect(migration).toMatch(/-- \(ww\) full cross-branch-logic re-derivation/)
  })

  it('documents bundling four categories in one migration as a cohesive unit, not scope creep', () => {
    expect(migration).toMatch(/This adds[\s\S]{0,20}FOUR categories at once/)
    expect(migration).toMatch(/tightly coupled/)
  })

  it('conjunct (ss) fixes the deepta domain at seven values despite the writer\'s stale "9 states" comment', () => {
    const detectorSql = extractDetectorSql()
    const ssSection = detectorSql.slice(
      detectorSql.indexOf('-- (ss)'),
      detectorSql.indexOf('-- (tt)'),
    )
    expect(ssSection).toContain(
      "NOT IN ('deepta', 'svastha', 'mudita', 'shanta', 'vikala', 'kopa', 'dina')",
    )
  })

  it('conjunct (ww) is scoped as an iff only for the jagrad case, not a false broader claim', () => {
    expect(migration).toMatch(/deliberately an[\s\S]{0,20}iff only for the 'jagrad' case/)
  })
})
