import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Nirmāṇa L1 ga_sade_sati integrity contract — FINAL widening pass (migration 754, F-A14).
 *
 * Migration 748 covered sade_sati_cycle/sade_sati_phase_quarter; migration 752 added the Dhaiya
 * family; migration 753 added the Phase family (10/15 categories). This adds the last five
 * categories (sade_sati_modifier_overlay, sade_sati_saturn_retrograde_subset,
 * sade_sati_cancellation_check, sade_sati_concurrent_dasha_overlay,
 * sade_sati_downstream_cross_reference), taking coverage to 15/15 — ALL of ga_sade_sati's own
 * declared fact_categories now carry a real integrity conjunct. integrity_check_sql is a single
 * UPDATE ... SET column, not additive SQL, so migration 754 carries the FULL replacement value:
 * the prior ten conjuncts (a)-(j) verbatim, plus seven new conjuncts (k)-(q). This textual test
 * verifies the migration's SHAPE — read-only and bind-parameter-free per the real
 * elevation-pipeline validator, all seventeen conjuncts survive — not a live-DB re-run of the
 * contract itself, which was verified and mutation-tested live against production during
 * authoring.
 */
const migration = fs.readFileSync(
  path.resolve(
    process.cwd(),
    'migrations/754_nirmana_l1_ga_sade_sati_integrity_contract_final.sql',
  ),
  'utf8',
)

function extractDetectorSql(): string {
  const start = migration.indexOf('$ck$')
  const end = migration.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL in migration 754')
  }
  return migration.slice(start + 4, end)
}

describe('migration 754 — ga_sade_sati integrity_check_sql (FINAL widening, 15/15)', () => {
  it('targets ga_sade_sati by name, not a blanket UPDATE', () => {
    expect(migration).toMatch(/UPDATE asset_registry SET integrity_check_sql = \$ck\$/)
    expect(migration.trim().endsWith("WHERE asset_id = 'ga_sade_sati';")).toBe(true)
  })

  it('is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql()
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
  })

  it('carries the ten prior conjuncts (a)-(j) verbatim (full-replacement column, not additive)', () => {
    for (const marker of [
      /-- \(a\) quarter_intensity_rationale_jsonb's first element/,
      /-- \(b\) cycle_start_iso must precede cycle_end_iso/,
      /-- \(c\) duration_days must equal the actual day-span between cycle_start_iso/,
      /-- \(d\) dhaiya_period\.period_start_iso must precede period_end_iso/,
      /-- \(e\) dhaiya_period\.duration_days must equal the actual day-span/,
      /-- \(f\) kantaka_shani_period \/ ashtama_shani_period \/ ardha_ashtama_shani_period's/,
      /-- \(g\) kantaka_shani_period \/ ashtama_shani_period's duration_days and saturn_sign/,
      /-- \(h\) sade_sati_phase\.phase_start_iso must precede phase_end_iso/,
      /-- \(i\) sade_sati_phase\.duration_days must equal the actual day-span/,
      /-- \(j\) janma_shani_period \/ vishakha_shani_period \/ anumukha_shani_period's/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('carries all seven new final-widening conjuncts', () => {
    for (const marker of [
      /-- \(k\) sade_sati_modifier_overlay's 5 flag keys/,
      /-- \(l\) sade_sati_saturn_retrograde_subset\.retrograde_start_iso must precede/,
      /-- \(m\) sade_sati_saturn_retrograde_subset\.duration_days must equal/,
      /-- \(n\) sade_sati_cancellation_check\.cancellation_active_flag must equal/,
      /-- \(o\) sade_sati_concurrent_dasha_overlay's verification_pass_status/,
      /-- \(p\)\/\(q\) sade_sati_downstream_cross_reference's d10_karya_bhava_activation_flag/,
    ]) {
      expect(migration).toMatch(marker)
    }
  })

  it('conjunct (n) re-derives cancellation_active_flag from the JSONB presence, not a restated literal', () => {
    const detectorSql = extractDetectorSql()
    const nSection = detectorSql.slice(
      detectorSql.indexOf('-- (n)'),
      detectorSql.indexOf('-- (o)'),
    )
    expect(nSection).toContain("(a.fact_value_text = 'true') <> (j.fact_value_jsonb IS NOT NULL)")
  })

  it("conjunct (o) checks the writer's own constant honest tier, not a data-dependent value", () => {
    const detectorSql = extractDetectorSql()
    const oSection = detectorSql.slice(
      detectorSql.indexOf('-- (o)'),
      detectorSql.indexOf('-- (p)/(q)'),
    )
    expect(oSection).toContain("fact_category = 'sade_sati_concurrent_dasha_overlay'")
    expect(oSection).toContain("verification_pass_status <> 'single'")
  })

  it('conjuncts (p)/(q) cross-check against the VISHAKHA phase specifically (the canonical first-phase representative)', () => {
    const detectorSql = extractDetectorSql()
    const pqSection = detectorSql.slice(detectorSql.indexOf('-- (p)/(q)'))
    expect(pqSection).toContain("c.fact_subject || '.VISHAKHA'")
    expect(pqSection).toContain("c.fact_key = 'd10_karya_bhava_activation_flag'")
    expect(pqSection).toContain("c.fact_key = 'argala_during_period_jsonb'")
    expect(pqSection).toContain('c.fact_value_jsonb IS DISTINCT FROM d.fact_value_jsonb')
  })

  it('carries no distinctness conjunct (D-CND-03 rule 4 basis unchanged from migration 748)', () => {
    expect(migration).toContain('no distinctness conjunct here (D-CND-03 rule 4)')
  })
})
