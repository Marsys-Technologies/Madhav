import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Nirmāṇa L1 chart_dashas scope-cap sentinel vocabulary contract (migration 652).
 *
 * F-A10 (L1_W1_ANALYSIS_BATCH_A.md): write_dasha_scope_cap_sentinels() stamps
 * both scope-cap sentinel rows with verification_pass_status='scope_cap_sentinel',
 * a literal not present in chart_dashas_verification_pass_status_check --
 * confirmed live, 0 rows with system_id='scope_cap' on all three built charts.
 * This migration admits the new value; it does NOT touch cd_level_n_max4, so
 * the Prana (level_n=5) sentinel still cannot land (SD-DASHA-1, reserved for
 * the native). This is a textual contract test (no live DB) -- it exists so a
 * future edit cannot silently widen the vocabulary beyond the one named value,
 * or drop the existing four tiers, without a test failing to say so.
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/652_nirmana_l1_ga_dashas_scope_cap_sentinel_vocab.sql'),
  'utf8',
)

describe('migration 652 — chart_dashas verification_pass_status vocabulary', () => {
  it('drops and re-adds the exact named constraint, not a blanket rewrite', () => {
    expect(migration).toContain('DROP CONSTRAINT chart_dashas_verification_pass_status_check')
    expect(migration).toContain('ADD CONSTRAINT chart_dashas_verification_pass_status_check')
  })

  it('adds scope_cap_sentinel without dropping any of the four existing tiers', () => {
    for (const tier of ['two_pass_verified', 'classical_match', 'divergent_flagged', 'single', 'scope_cap_sentinel']) {
      expect(migration).toContain(`'${tier}'::text`)
    }
  })

  it('never DROPs or ADDs a constraint on cd_level_n_max4 — the Prana row stays a deliberate non-fix (SD-DASHA-1)', () => {
    expect(migration).not.toMatch(/(DROP|ADD)\s+CONSTRAINT\s+cd_level_n_max4/i)
    expect(migration).toMatch(/SD-DASHA-1/)
  })

  it('verifies against the LIVE pg_get_constraintdef, not a literal restating its own assumption', () => {
    expect(migration).toContain('pg_get_constraintdef(oid)')
    expect(migration).toMatch(/live_def NOT LIKE '%scope_cap_sentinel%'/)
    expect(migration).toMatch(/RAISE EXCEPTION 'migration 652: live constraint definition does not admit scope_cap_sentinel/)
  })

  it('also refuses silently if the rewrite dropped one of the four pre-existing tiers', () => {
    expect(migration).toMatch(/RAISE EXCEPTION 'migration 652: rewrite dropped one of the four pre-existing tiers/)
  })
})
