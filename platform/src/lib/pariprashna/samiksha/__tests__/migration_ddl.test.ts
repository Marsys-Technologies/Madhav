/**
 * SAMĪKṢĀ migration DDL static assertions — PB-3 lane L-1.
 *
 * Static-text checks that the migration files carry the exact field set BRIEF_PB-3 §F1 / §G
 * item 2 require, and that the retirement follows MEMO_PB-3_0's rollback path. These do NOT
 * prove the migration APPLIES (that is the ledger_db integration test's job, against a real
 * throwaway DB) — they guard the spec-mandated surface so a field can't silently go missing.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { LIFECYCLE_STATES } from '../schema'

const MIGRATIONS = resolve(__dirname, '../../../../../supabase/migrations')
const ledger = readFileSync(resolve(MIGRATIONS, '470_pariprashna_samiksha_prediction_ledger.sql'), 'utf-8')
const retire = readFileSync(resolve(MIGRATIONS, '471_retire_mcp_predictions.sql'), 'utf-8')

describe('470 — brahma_mimamsa_prediction_ledger DDL', () => {
  it('creates the MEMO-fixed table name', () => {
    expect(ledger).toContain('CREATE TABLE IF NOT EXISTS brahma_mimamsa_prediction_ledger')
  })

  it('carries the full §14.3/§14.2 field set from row one', () => {
    expect(ledger).toMatch(/chart_id\s+uuid\s+NOT NULL/)
    expect(ledger).toMatch(/message_part_id\s+uuid\s+REFERENCES message_parts\(id\)/) // FK → PB-2
    expect(ledger).toContain('claim_text')
    expect(ledger).toContain('domain')
    expect(ledger).toMatch(/"window"\s+daterange/) // daterange, not two date cols
    expect(ledger).toMatch(/confidence\s+numrange/) // numrange, NEVER text (X-5 lesson)
    expect(ledger).toContain('direction')
    expect(ledger).toMatch(/technique_refs\s+text\[\]/)
    expect(ledger).toMatch(/grounding_fact_ids\s+text\[\]/)
    expect(ledger).toContain('created_from_channel')
  })

  it('confidence is a numrange and never a text/enum column', () => {
    expect(ledger).not.toMatch(/confidence\s+text/)
    expect(ledger).not.toMatch(/confidence.*CHECK.*IN\s*\(\s*'high'/)
  })

  it('CHECK constraint enumerates all 9 lifecycle tokens', () => {
    for (const s of LIFECYCLE_STATES) {
      expect(ledger).toContain(`'${s}'`)
    }
  })

  it('carries all five D-16 stamp columns, COPIED (no FK/join to a stamp source)', () => {
    for (const col of ['build_id', 'priors_version', 'formula_versions', 'ranking_config', 'now_context_date']) {
      expect(ledger).toContain(col)
    }
    expect(ledger.toLowerCase()).toContain('copied')
  })

  it('co-locates the outcome columns incl. a numeric Brier input + unverifiable exclusion', () => {
    expect(ledger).toContain('outcome')
    expect(ledger).toContain('outcome_note')
    expect(ledger).toContain('outcome_recorded_at')
    expect(ledger).toContain('outcome_value') // numeric Brier input
    expect(ledger).toContain('bmpl_unverifiable_has_no_value') // Brier-exclusion integrity
  })

  it('installs the immutability trigger forbidding stamp/settled-claim UPDATE once confirmed', () => {
    expect(ledger).toContain('CREATE TRIGGER trg_bmpl_freeze_confirmed')
    expect(ledger).toContain('immutable once')
  })

  it('is additive (no DROP/TRUNCATE of any existing table outside commented DOWN block)', () => {
    const executable = ledger.replace(/^--.*$/gm, '') // strip line comments
    expect(executable).not.toMatch(/DROP TABLE\s+(?!IF EXISTS brahma_mimamsa)/i)
    expect(executable).not.toMatch(/TRUNCATE/i)
  })
})

describe('471 — mcp_predictions retirement (destructive, per MEMO_PB-3_0)', () => {
  it('backs up BEFORE the drop, in the same transaction, per the MEMO rollback path', () => {
    const backupIdx = retire.indexOf('CREATE TABLE mcp_predictions_retired_backup AS TABLE mcp_predictions')
    const dropIdx = retire.indexOf("DROP TABLE mcp_predictions'")
    expect(backupIdx).toBeGreaterThan(-1)
    expect(dropIdx).toBeGreaterThan(-1)
    expect(backupIdx).toBeLessThan(dropIdx) // backup precedes drop
    expect(retire).toMatch(/BEGIN;[\s\S]*COMMIT;/) // single transaction
  })

  it('documents that the SQL rollback alone is insufficient (needs a code revert too)', () => {
    expect(retire).toMatch(/git revert/i)
    expect(retire).toMatch(/CREATE TABLE mcp_predictions AS TABLE mcp_predictions_retired_backup/)
  })

  it('touches ONLY mcp_predictions — never mimamsa_predictions or brahma_prospective_ledger', () => {
    expect(retire).not.toContain('mimamsa_predictions')
    expect(retire).not.toContain('brahma_prospective_ledger')
  })
})
