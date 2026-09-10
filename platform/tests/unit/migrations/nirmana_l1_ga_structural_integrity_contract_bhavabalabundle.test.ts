import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_structural integrity contract — Group C "Bhava Bala extended" bundle widening
 * pass (migration 796, F-A14) — seventeenth migration in the 780-799 range (adjudication
 * #2012). Bundles EIGHT categories in one migration, the arc's largest bundle jump yet (after
 * migration 788's 4-category Group H bundle and migration 791's 3-category Group O bundle):
 * bhava_bala_positional, bhava_bala_directional, bhava_bala_temporal, bhava_bala_aspectual,
 * bhava_bala_occupant, bhava_bala_lord, bhava_bala_total_extended, and
 * house_strength_classification_rollup — taking coverage from 28/57 to 36/57.
 *
 * All eight are emitted by the SAME per-house loop in `_build_bhava_bala_extended_rows`, with a
 * genuine cross-field dependency chain: total_extended is the mean of the six sub-scores, and
 * house_strength_classification_rollup is a threshold function of total_extended. Three
 * sub-scores (positional/directional/temporal) are pure functions of house number alone — fully
 * re-derived with zero cross-reference risk; the other three (aspectual/occupant/lord) get
 * domain-bound conjuncts derived from the writer's own formula structure. Verified against ALL
 * 180 live rows per category, not a sample.
 *
 * integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so migration 796
 * carries the seventy-two prior conjuncts (a)-(b5) forward verbatim — including conjuncts (b)/
 * (e)/(f), already genuinely red (tracked) — plus eight new conjuncts (c)/(d)/(e2)/(f2)/(g2)/
 * (h2)/(i2)/(j2). This textual test verifies the migration's SHAPE — read-only and
 * bind-parameter-free, all eighty conjuncts survive — not a live-DB re-run of the full combined
 * contract; the new conjuncts were verified live in isolation during authoring, each
 * individually mutation-tested.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/796_nirmana_l1_ga_structural_integrity_contract_bhavabalabundle.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 796')
  }
  return migration.slice(start + 4, end)
}

describe('migration 796 — ga_structural integrity_check_sql (Group C Bhava Bala extended bundle)', () => {
  it('targets ga_structural by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_structural';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the seventy-two prior conjuncts (a)-(b5) verbatim, including the still-red (b)/(e)/(f)', () => {
    for (const marker of [
      /-- \(a\) amplification_factor domain/,
      /-- \(b\) F-A15: amplification_factor must agree/,
      /-- \(e\) F-A17: vargottama_per_varga\.is_vargottama/,
      /-- \(f\) F-157: parivartana_per_varga\.mutual_exchange must never pair/,
      /-- \(a5\) karaka_house_lord_overlap_flag fact_value_text domain/,
      /-- \(b5\) full re-derivation/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all eight new conjuncts spanning the bundle', () => {
    expect(migration).toMatch(/-- \(c\) bhava_bala_positional full re-derivation/)
    expect(migration).toMatch(/-- \(d\) bhava_bala_directional full re-derivation/)
    expect(migration).toMatch(/-- \(e2\) bhava_bala_temporal full re-derivation/)
    expect(migration).toMatch(/-- \(f2\) bhava_bala_aspectual domain/)
    expect(migration).toMatch(/-- \(g2\) bhava_bala_occupant domain/)
    expect(migration).toMatch(/-- \(h2\) bhava_bala_lord domain/)
    expect(migration).toMatch(/-- \(i2\) bhava_bala_total_extended self-consistency/)
    expect(migration).toMatch(/-- \(j2\) house_strength_classification_rollup full re-derivation/)
  })

  it('re-derives positional/directional/temporal as pure functions of house number, no chart-data join', () => {
    const detectorSql = extractDetectorSql()
    const cSection = detectorSql.slice(
      detectorSql.indexOf('-- (c) bhava_bala_positional'),
      detectorSql.indexOf('-- (f2)'),
    )
    expect(cSection).not.toContain('JOIN chart_facts')
    expect(cSection).toContain("substring(fact_subject from 7)")
  })

  it('re-derives total_extended as the mean of all six sibling sub-score categories', () => {
    const detectorSql = extractDetectorSql()
    const i2Section = detectorSql.slice(
      detectorSql.indexOf('-- (i2)'),
      detectorSql.indexOf('-- (j2)'),
    )
    for (const sib of [
      'bhava_bala_positional', 'bhava_bala_directional', 'bhava_bala_temporal',
      'bhava_bala_aspectual', 'bhava_bala_occupant', 'bhava_bala_lord',
    ]) {
      expect(i2Section).toContain(sib)
    }
    expect(i2Section).toContain('/ 6.0')
  })

  it('re-derives the classification threshold from the sibling total_extended category', () => {
    const detectorSql = extractDetectorSql()
    const j2Section = detectorSql.slice(detectorSql.indexOf('-- (j2)'))
    expect(j2Section).toContain('bhava_bala_total_extended')
    expect(j2Section).toContain("'strong'")
    expect(j2Section).toContain("'normal'")
    expect(j2Section).toContain("'weak'")
  })
})
