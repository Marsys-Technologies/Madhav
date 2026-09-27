/**
 * Migration 1122 — chart-context staleness metadata (JATAKA-REQ-03; Jātaka
 * Phase-A2 integrity, item 2). Source-level contract only: authored, never
 * applied in this phase. Additive columns on `event_chart_state_index` and
 * `mimamsa_predictions` that mark a preserved row as superseded by a correction
 * without deleting, editing or reclassifying it.
 */
import { describe, expect, it } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIGRATION = path.resolve(__dirname, '../../../supabase/migrations/1122_jataka_chart_context_staleness.sql')
const sql = fs.existsSync(MIGRATION) ? fs.readFileSync(MIGRATION, 'utf8') : ''
const statements = sql.replace(/--[^\n]*/g, '')

const TABLES = ['event_chart_state_index', 'mimamsa_predictions'] as const

describe('1122_jataka_chart_context_staleness.sql', () => {
  it('exists at the JATAKA-REQ-03 reserved number', () => {
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
    expect(statements).toMatch(
      new RegExp(`conname = '${table}_stale_reason_check'`, 'i'),
    )
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

  it.each(TABLES)('indexes the current (non-stale) rows of %s — the shape every consumer filter needs', (table) => {
    expect(statements).toMatch(
      new RegExp(`CREATE INDEX IF NOT EXISTS idx_${table}_chart_current\\s+ON public\\.${table}\\(chart_id\\)\\s+WHERE chart_context_stale_at IS NULL`, 'i'),
    )
  })

  it('never deletes, rewrites or reclassifies an existing row — additive columns only', () => {
    expect(statements).not.toMatch(/DROP\s+(TABLE|COLUMN|CONSTRAINT|INDEX|FUNCTION)|TRUNCATE|DELETE\s+FROM|UPDATE\s+public\./i)
    // lifecycle_status/outcome/confirmed/denied may be named in descriptive prose
    // (comments, COMMENT ON COLUMN) but no individual ALTER/CHECK statement here
    // may touch them — checked per statement (split on ;), not across the file.
    const perStatement = statements.split(';')
    const mutatesLifecycle = perStatement.some(
      (stmt) => /ALTER\s+TABLE|CHECK\s*\(/i.test(stmt) && /lifecycle_status/i.test(stmt),
    )
    expect(mutatesLifecycle).toBe(false)
  })

  it('never touches life_events', () => {
    expect(statements).not.toMatch(/life_events/i)
  })
})
