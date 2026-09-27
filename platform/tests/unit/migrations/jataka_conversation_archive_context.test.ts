/**
 * Migration 1120 — Jātaka conversation archive context (JATAKA-REQ-01).
 *
 * Source-level contract only: this phase authors the migration but never
 * applies it. The file must be additive and idempotent, constrain the archive
 * reason, link a correction archive to its rebuild run without cascading a
 * delete, and contain no destructive statement.
 */
import { describe, expect, it } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIGRATION = path.resolve(__dirname, '../../../supabase/migrations/1120_jataka_conversation_archive_context.sql')
const sql = fs.existsSync(MIGRATION) ? fs.readFileSync(MIGRATION, 'utf8') : ''
// Strip `--` comments so prose cannot satisfy or trip a statement assertion.
const statements = sql.replace(/--[^\n]*/g, '')

describe('1120_jataka_conversation_archive_context.sql', () => {
  it('exists at the JATAKA-REQ-01 reserved number, outside the L3 (1070–1119) and Pūrṇa (1042–1069) ranges', () => {
    expect(fs.existsSync(MIGRATION)).toBe(true)
  })

  it('adds the three archive-context columns idempotently', () => {
    expect(statements).toMatch(/ADD COLUMN IF NOT EXISTS archive_reason TEXT/i)
    expect(statements).toMatch(/ADD COLUMN IF NOT EXISTS archived_chart_snapshot JSONB/i)
    expect(statements).toMatch(/ADD COLUMN IF NOT EXISTS archived_by_run_id UUID/i)
  })

  it('constrains the reason to chart_details_changed (or NULL for manual archives), guarded by pg_constraint', () => {
    expect(statements).toMatch(/conversations_archive_reason_check/)
    expect(statements).toMatch(/CHECK \(archive_reason IS NULL OR archive_reason IN \('chart_details_changed'\)\)/i)
    expect(statements).toMatch(/NOT EXISTS[\s\S]*pg_constraint[\s\S]*conversations_archive_reason_check/i)
  })

  it('links the rebuild run with ON DELETE SET NULL, guarded by pg_constraint', () => {
    expect(statements).toMatch(/REFERENCES public\.build_runs\(id\) ON DELETE SET NULL/i)
    expect(statements).toMatch(/NOT EXISTS[\s\S]*pg_constraint[\s\S]*conversations_archived_by_run_id_fkey/i)
  })

  it('requires a snapshot whenever a conversation is archived for a chart correction', () => {
    expect(statements).toMatch(/conversations_correction_archive_snapshot_check/)
    expect(statements).toMatch(
      /archive_reason IS DISTINCT FROM 'chart_details_changed'\s+OR \(archived_at IS NOT NULL AND archived_chart_snapshot IS NOT NULL\)/i,
    )
  })

  it('indexes archived rows per chart and reason idempotently', () => {
    expect(statements).toMatch(/CREATE INDEX IF NOT EXISTS idx_conversations_chart_archive_reason/i)
    expect(statements).toMatch(/WHERE archived_at IS NOT NULL/i)
  })

  it('contains no destructive or data-rewriting statement', () => {
    expect(statements).not.toMatch(/DROP\s+(TABLE|COLUMN|CONSTRAINT|INDEX)|TRUNCATE|DELETE\s+FROM|UPDATE\s+public\.conversations|ALTER\s+COLUMN/i)
  })

  it('documents the snapshot semantics and the system-locked read-only rule', () => {
    expect(sql).toMatch(/pre-correction/i)
    expect(sql).toMatch(/read-only/i)
  })
})
