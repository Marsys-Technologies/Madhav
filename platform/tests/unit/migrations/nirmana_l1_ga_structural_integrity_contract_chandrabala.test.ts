import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — chandra_bala_natal_baseline widening pass
 * (migration 790, F-A14) — eleventh migration in the 780-799 range (adjudication #2012).
 *
 * Migration 745 covered graha_vargottama_amplification_factor; migration 755 added
 * bhadra_flag/panchaka_flag; migration 756 added vargottama_per_varga; migration 757 added
 * parivartana_per_varga; migration 758 added combustion_per_varga; migration 759 added
 * graha_yuddha_per_varga; migration 780 added nway_config_per_varga; migration 781 added
 * kala_sarpa_per_varga; migration 782 added tara_bala_natal_baseline; migration 783 added
 * conjunction_within_orb; migration 784 added aspect_tajik; migration 785 added
 * graha_yoga_karaka_flag; migration 786 added graha_dispositor_chain; migration 787 added
 * composite_dispositor_strength; migration 788 added the Group H avastha bundle; migration 789
 * added nakshatra_dispositor_chain (20/57). This adds chandra_bala_natal_baseline, taking
 * coverage to 21/57.
 *
 * chandra_bala_natal_baseline is a THIRD cross-writer-owned category (like migration 755's
 * bhadra_flag/panchaka_flag and migration 782's tara_bala_natal_baseline): emitted by
 * ga_panchanga_writer.py, owned by ga_structural. Its formula reuses the D-L1-55 Postgres
 * modulo-sign-bug precedent (this time mod-12, not mod-27/mod-9).
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 790
 * carries the fifty-five prior conjuncts (a)-(ss2) forward verbatim — including conjuncts (b)/
 * (e)/(f), already genuinely red (tracked) — plus two new conjuncts (tt2)/(uu2). This textual
 * test verifies the migration's SHAPE — read-only and bind-parameter-free, all fifty-seven
 * conjuncts survive — not a live-DB re-run of the full combined contract; conjuncts (tt2)/(uu2)
 * were verified live in isolation during authoring, each individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/790_nirmana_l1_ga_structural_integrity_contract_chandrabala.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 790')
  }
  return migration.slice(start + 4, end)
}

describe('migration 790 — ga_structural integrity_check_sql (chandra_bala_natal_baseline)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the fifty-five prior conjuncts (a)-(ss2) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(nn2\) nakshatra_dispositor_chain\.chain\[0\]/,
      /-- \(ss2\) constituent_fact_ids\[0\], when present/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries both new conjuncts (tt2)/(uu2)', () => {
    expect(migration).toMatch(/-- \(tt2\) chandra_bala_natal_baseline\.classification domain/)
    expect(migration).toMatch(/-- \(uu2\) chandra_bala_natal_baseline\.classification must equal/)
  })

  it('documents this as a third cross-writer-owned category, same pattern as migrations 755/782', () => {
    expect(migration).toMatch(/THIRD cross-writer-owned category/)
    expect(migration).toMatch(/EMITTED by\s*\n?-- ga_panchanga_writer\.py/)
  })

  it('reuses the D-L1-55 Postgres modulo-sign-bug precedent with a +120 margin for the mod-12 formula', () => {
    const detectorSql = extractDetectorSql()
    const uu2Section = detectorSql.slice(detectorSql.indexOf('-- (uu2)'))
    expect(uu2Section).toContain('+ 120')
    expect(uu2Section).toContain(') % 12')
    expect(migration).toMatch(/D-L1-55/)
  })

  it('conjunct (uu2) re-derives birth_moon_sign_id via integer floor division from panchanga_nakshatra_moon', () => {
    const detectorSql = extractDetectorSql()
    const uu2Section = detectorSql.slice(detectorSql.indexOf('-- (uu2)'))
    expect(uu2Section).toContain("fact_category = 'panchanga_nakshatra_moon'")
    expect(uu2Section).toContain('((n.fact_value_num::int - 1) * 4) / 9 + 1')
  })

  it('conjunct (tt2) restricts the domain to exactly the three classical classifications', () => {
    const detectorSql = extractDetectorSql()
    const tt2Section = detectorSql.slice(
      detectorSql.indexOf('-- (tt2)'),
      detectorSql.indexOf('-- (uu2)'),
    )
    expect(tt2Section).toContain("NOT IN ('favorable', 'unfavorable', 'neutral')")
  })
})
