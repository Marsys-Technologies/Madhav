import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_sade_sati integrity contract — Dhaiya widening pass (migration 752, F-A14).
 *
 * Migration 748 shipped a bounded first pass (sade_sati_cycle, sade_sati_phase_quarter —
 * 2/15 categories). integrity_check_sql is a single UPDATE ... SET column, not additive SQL, so
 * migration 752 carries the FULL replacement value: 748's three original conjuncts (a)/(b)/(c)
 * verbatim, plus four new conjuncts (d)/(e)/(f)/(g) covering the four Dhaiya-family categories
 * (dhaiya_period, kantaka_shani_period, ashtama_shani_period, ardha_ashtama_shani_period —
 * Saturn's 4H/8H transits from natal Moon), taking coverage to 6/15 categories. This textual
 * test verifies the migration's SHAPE — read-only and bind-parameter-free per the real
 * elevation-pipeline validator, all seven conjuncts survive — not a live-DB re-run of the
 * contract itself, which was verified and mutation-tested live against production during
 * authoring.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/752_nirmana_l1_ga_sade_sati_integrity_contract_dhaiya.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 752')
  }
  return migration.slice(start + 4, end)
}

describe('migration 752 — ga_sade_sati integrity_check_sql (Dhaiya widening)', () => {
  it('targets ga_sade_sati by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_sade_sati';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries migration 748\'s three original conjuncts verbatim (full-replacement column, not additive)', () => {
    expect(migration).toMatch(/-- \(a\) quarter_intensity_rationale_jsonb's first element/)
    expect(migration).toMatch(/-- \(b\) cycle_start_iso must precede cycle_end_iso/)
    expect(migration).toMatch(/-- \(c\) duration_days must equal the actual day-span between cycle_start_iso/)
  })

  it('carries all four new Dhaiya-family conjuncts', () => {
    expect(migration).toMatch(/-- \(d\) dhaiya_period\.period_start_iso must precede period_end_iso/)
    expect(migration).toMatch(/-- \(e\) dhaiya_period\.duration_days must equal the actual day-span/)
    expect(migration).toMatch(/-- \(f\) kantaka_shani_period \/ ashtama_shani_period \/ ardha_ashtama_shani_period's/)
    expect(migration).toMatch(/-- \(g\) kantaka_shani_period \/ ashtama_shani_period's duration_days and saturn_sign/)
  })

  it("re-derives dhaiya_period's temporal ordering and duration from stored ISO timestamps, not a restated literal", () => {
    const detectorSql = extractDetectorSql()
    const dhaiyaSection = detectorSql.slice(detectorSql.indexOf("fact_category = 'dhaiya_period'"))
    expect(dhaiyaSection).toContain("s.fact_value_text::timestamptz >= e.fact_value_text::timestamptz")
    expect(dhaiyaSection).toContain('EXTRACT(EPOCH FROM')
  })

  it('cross-checks kantaka/ashtama/ardha_ashtama against dhaiya_period by VALUE equality, never a bare count', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("c.fact_category IN ('kantaka_shani_period', 'ashtama_shani_period', 'ardha_ashtama_shani_period')")
    expect(detectorSql).toContain('c.fact_value_text <> d.fact_value_text')
    expect(detectorSql).toContain("c.fact_category IN ('kantaka_shani_period', 'ashtama_shani_period')")
  })

  it('scopes the duration_days/saturn_sign cross-check away from ardha_ashtama_shani_period (which stores neither field)', () => {
    const detectorSql = extractDetectorSql()
    const gPredicates = detectorSql
      .slice(detectorSql.lastIndexOf("-- (g)"))
      .match(/c\.fact_category IN \([^)]+\)/g)
    expect(gPredicates).not.toBeNull()
    for (const predicate of gPredicates ?? []) {
      expect(predicate).not.toContain('ardha_ashtama_shani_period')
    }
  })
})
