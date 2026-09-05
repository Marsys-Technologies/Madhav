import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_sade_sati integrity contract — Phase widening pass (migration 753, F-A14).
 *
 * Migration 748 covered sade_sati_cycle/sade_sati_phase_quarter; migration 752 added the Dhaiya
 * family (6/15 categories). integrity_check_sql is a single UPDATE ... SET column, not additive
 * SQL, so migration 753 carries the FULL replacement value: the prior seven conjuncts (a)-(g)
 * verbatim, plus three new conjuncts (h)/(i)/(j) covering sade_sati_phase and the three
 * classically-named sub-phase categories (janma_shani_period, vishakha_shani_period,
 * anumukha_shani_period), taking coverage to 10/15 categories. This textual test verifies the
 * migration's SHAPE — read-only and bind-parameter-free per the real elevation-pipeline
 * validator, all ten conjuncts survive — not a live-DB re-run of the contract itself, which was
 * verified and mutation-tested live against production during authoring.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/753_nirmana_l1_ga_sade_sati_integrity_contract_phase.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 753')
  }
  return migration.slice(start + 4, end)
}

describe('migration 753 — ga_sade_sati integrity_check_sql (Phase widening)', () => {
  it('targets ga_sade_sati by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_sade_sati';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the seven prior conjuncts (a)-(g) verbatim (full-replacement column, not additive)', () => {
    expect(migration).toMatch(/-- \(a\) quarter_intensity_rationale_jsonb's first element/)
    expect(migration).toMatch(/-- \(b\) cycle_start_iso must precede cycle_end_iso/)
    expect(migration).toMatch(/-- \(c\) duration_days must equal the actual day-span between cycle_start_iso/)
    expect(migration).toMatch(/-- \(d\) dhaiya_period\.period_start_iso must precede period_end_iso/)
    expect(migration).toMatch(/-- \(e\) dhaiya_period\.duration_days must equal the actual day-span/)
    expect(migration).toMatch(/-- \(f\) kantaka_shani_period \/ ashtama_shani_period \/ ardha_ashtama_shani_period's/)
    expect(migration).toMatch(/-- \(g\) kantaka_shani_period \/ ashtama_shani_period's duration_days and saturn_sign/)
  })

  it('carries all three new Phase-family conjuncts', () => {
    expect(migration).toMatch(/-- \(h\) sade_sati_phase\.phase_start_iso must precede phase_end_iso/)
    expect(migration).toMatch(/-- \(i\) sade_sati_phase\.duration_days must equal the actual day-span/)
    expect(migration).toMatch(/-- \(j\) janma_shani_period \/ vishakha_shani_period \/ anumukha_shani_period's/)
  })

  it("re-derives sade_sati_phase's temporal ordering and duration from stored ISO timestamps, not a restated literal", () => {
    const detectorSql = extractDetectorSql()
    const phaseSection = detectorSql.slice(detectorSql.indexOf("-- (h) sade_sati_phase"))
    expect(phaseSection).toContain("s.fact_value_text::timestamptz >= e.fact_value_text::timestamptz")
    expect(phaseSection).toContain('EXTRACT(EPOCH FROM')
  })

  it('cross-checks the three classical sub-phase categories against sade_sati_phase by VALUE equality, mapping phase_*/period_* key names', () => {
    const detectorSql = extractDetectorSql()
    expect(detectorSql).toContain("c.fact_category IN ('janma_shani_period', 'vishakha_shani_period', 'anumukha_shani_period')")
    expect(detectorSql).toContain("WHEN 'period_start_iso' THEN 'phase_start_iso'")
    expect(detectorSql).toContain("WHEN 'period_end_iso' THEN 'phase_end_iso'")
    expect(detectorSql).toContain('c.fact_value_text <> d.fact_value_text')
  })

  it('the (j) conjunct also cross-checks saturn_sign/saturn_dignity/duration_days, not just the two ISO timestamps', () => {
    const detectorSql = extractDetectorSql()
    const jSection = detectorSql.slice(detectorSql.lastIndexOf('-- (j)'))
    expect(jSection).toContain("'saturn_sign', 'saturn_dignity'")
    expect(jSection).toContain("fact_key = 'duration_days'")
  })
})
