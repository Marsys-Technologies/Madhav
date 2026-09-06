import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — composite_dispositor_strength widening pass
 * (migration 787, F-A14) — eighth migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb; migration 784 added aspect_tajik; migration 785 added
 * graha_yoga_karaka_flag; migration 786 added graha_dispositor_chain (14/57). This adds
 * composite_dispositor_strength, taking coverage to 15/57.
 *
 * composite_dispositor_strength's value is the mean of dignity-strength over the SAME graha's
 * graha_dispositor_chain.chain array (migration 786). dignity_status is never independently
 * persisted (unlike graha_dignity_per_varga's separate, independently-computed scheme, already
 * ruled a genuine vocabulary mismatch in cycle 49), so a full per-member re-derivation is not
 * achievable without reimplementing PyJHora's own dignity tables — disproportionate for one
 * bounded pass, the same judgment already applied to kala_sarpa_per_varga (migration 781).
 * Instead this migration ships three self-consistency/domain/cross-category conjuncts.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 787
 * carries the thirty-nine prior conjuncts (a)-(mm) forward verbatim — including conjuncts (b)/
 * (e)/(f), already genuinely red (tracked) — plus three new conjuncts (nn)-(pp). This textual
 * test verifies the migration's SHAPE — read-only and bind-parameter-free, all forty-two
 * conjuncts survive — not a live-DB re-run of the full combined contract; conjuncts (nn)-(pp)
 * were verified live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/787_nirmana_l1_ga_structural_integrity_contract_compositestrength.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 787')
  }
  return migration.slice(start + 4, end)
}

describe('migration 787 — ga_structural integrity_check_sql (composite_dispositor_strength)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the thirty-nine prior conjuncts (a)-(mm) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(hh\) graha_dispositor_chain's chain\[0\] must equal/,
      /-- \(mm\) terminal cycle-closure/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all three new conjuncts (nn)-(pp)', () => {
    expect(migration).toMatch(
      /-- \(nn\) composite_dispositor_strength\.terminal_strength domain/,
    )
    expect(migration).toMatch(/-- \(oo\) bidirectional row correspondence with graha_dispositor_chain/)
    expect(migration).toMatch(/-- \(pp\) cross-category re-derivation/)
  })

  it('documents why dignity_status was not fully re-derived, citing the cycle-49 vocabulary-mismatch precedent', () => {
    expect(migration).toMatch(/graha_dignity_per_varga.*DIFFERENT.*classify_dignity\(\) scheme/s)
    expect(migration).toMatch(/cycle 49's finding/)
    expect(migration).toMatch(/disproportionate\s*\n?\s*-- scope for one bounded conjunct pass/)
  })

  it('conjunct (nn) restricts the domain to [0.25, 1.0]', () => {
    const detectorSql = extractDetectorSql()
    const nnSection = detectorSql.slice(
      detectorSql.indexOf('-- (nn)'),
      detectorSql.indexOf('-- (oo)'),
    )
    expect(nnSection).toContain('fact_value_num < 0.25 OR fact_value_num > 1.0')
  })

  it('conjunct (oo) checks correspondence in both directions via UNION ALL', () => {
    const detectorSql = extractDetectorSql()
    const ooSection = detectorSql.slice(
      detectorSql.indexOf('-- (oo)'),
      detectorSql.indexOf('-- (pp)'),
    )
    expect(ooSection).toContain('UNION ALL')
  })

  it('conjunct (pp) scales its tolerance by chain length, citing the writer\'s round(mean,4) precision', () => {
    const detectorSql = extractDetectorSql()
    const ppSection = detectorSql.slice(detectorSql.indexOf('-- (pp)'))
    expect(ppSection).toContain("0.0001 * (b.fact_value_jsonb->>'length')::numeric")
    expect(migration).toMatch(/round\(mean, 4\) storage precision/)
  })
})
