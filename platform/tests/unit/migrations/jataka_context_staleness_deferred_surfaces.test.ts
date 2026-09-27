/**
 * Migration 1123 — chart-context staleness for the three deferred surfaces
 * (JATAKA-REQ-04; Jātaka Phase-A3 source integrity). Source-level contract
 * only: authored, never applied in this phase. Additive columns on
 * `brahma_mimamsa_prediction_ledger`, `brahma_prospective_ledger` and
 * `mimamsa_calibration_snapshot` — same shape as migration 1122's columns on
 * event_chart_state_index/mimamsa_predictions — marking a preserved row as
 * superseded by a correction without deleting, editing or reclassifying it.
 */
import { describe, expect, it } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIGRATION = path.resolve(__dirname, '../../../supabase/migrations/1123_jataka_context_staleness_deferred_surfaces.sql')
const sql = fs.existsSync(MIGRATION) ? fs.readFileSync(MIGRATION, 'utf8') : ''
const statements = sql.replace(/--[^\n]*/g, '')

const TABLES = ['brahma_mimamsa_prediction_ledger', 'brahma_prospective_ledger', 'mimamsa_calibration_snapshot'] as const

describe('1123_jataka_context_staleness_deferred_surfaces.sql', () => {
  it('exists at the JATAKA-REQ-04 reserved number', () => {
    expect(fs.existsSync(MIGRATION)).toBe(true)
  })

  it.each(TABLES)('adds the three staleness columns to %s, idempotently', (table) => {
    const re = new RegExp(
      `ALTER TABLE public\\.${table}\\s+` +
        `ADD COLUMN IF NOT EXISTS chart_context_stale_at TIMESTAMPTZ,\\s*` +
        `ADD COLUMN IF NOT EXISTS chart_context_stale_reason TEXT,\\s*` +
        `ADD COLUMN IF NOT EXISTS chart_context_superseded_by_run_id UUID`,
      'i',
    )
    expect(statements).toMatch(re)
  })

  it.each(TABLES)('constrains %s.chart_context_stale_reason to the known vocabulary, pg_constraint-guarded', (table) => {
    expect(statements).toMatch(new RegExp(`conname = '${table}_stale_reason_check'`, 'i'))
    expect(statements).toMatch(
      new RegExp(
        `ADD CONSTRAINT ${table}_stale_reason_check\\s+CHECK \\(chart_context_stale_reason IS NULL OR chart_context_stale_reason IN \\('chart_details_changed'\\)\\)`,
        'i',
      ),
    )
  })

  it.each(TABLES)('keeps stale_at and stale_reason paired on %s (both set or both NULL)', (table) => {
    expect(statements).toMatch(new RegExp(`conname = '${table}_stale_pair_check'`, 'i'))
    expect(statements).toMatch(
      new RegExp(
        `ADD CONSTRAINT ${table}_stale_pair_check\\s+CHECK \\(\\(chart_context_stale_at IS NULL\\) = \\(chart_context_stale_reason IS NULL\\)\\)`,
        'i',
      ),
    )
  })

  it.each(TABLES)('points %s.chart_context_superseded_by_run_id at build_runs, SET NULL on prune', (table) => {
    expect(statements).toMatch(new RegExp(`conname = '${table}_superseded_by_run_id_fkey'`, 'i'))
    expect(statements).toMatch(
      new RegExp(
        `ADD CONSTRAINT ${table}_superseded_by_run_id_fkey\\s+FOREIGN KEY \\(chart_context_superseded_by_run_id\\)\\s+REFERENCES public\\.build_runs\\(id\\) ON DELETE SET NULL`,
        'i',
      ),
    )
  })

  it.each(TABLES)('indexes the current (non-stale) rows of %s', (table) => {
    expect(statements).toMatch(
      new RegExp(`CREATE INDEX IF NOT EXISTS idx_${table}_chart_current\\s+ON public\\.${table}\\(chart_id\\)\\s+WHERE chart_context_stale_at IS NULL`, 'i'),
    )
  })

  it('never deletes, rewrites or reclassifies an existing row, and never touches a frozen or checked lifecycle/outcome column', () => {
    expect(statements).not.toMatch(/DROP\s+(TABLE|COLUMN|CONSTRAINT|INDEX|FUNCTION)|TRUNCATE|DELETE\s+FROM|UPDATE\s+public\./i)
    const perStatement = statements.split(';')
    const touchesGuardedColumn = perStatement.some(
      (stmt) =>
        /ALTER\s+TABLE|CHECK\s*\(/i.test(stmt) &&
        /lifecycle_status|\boutcome\b|claim_text|confidence|window|direction|domain\b|build_id|priors_version|formula_versions|ranking_config|now_context_date/i.test(stmt),
    )
    expect(touchesGuardedColumn).toBe(false)
  })

  it('never touches life_events or the already-migrated event_chart_state_index/mimamsa_predictions columns', () => {
    expect(statements).not.toMatch(/life_events/i)
    expect(statements).not.toMatch(/ALTER TABLE public\.(event_chart_state_index|mimamsa_predictions)/i)
  })
})
