/**
 * Migration 1121 — database write guard for correction-archived conversations
 * (JATAKA-REQ-02; Jātaka Phase-A hardening, item 5). Source-level contract only:
 * authored, never applied in this phase. The trigger re-checks, inside the
 * inserting transaction and under a share lock on the parent conversation row,
 * that the conversation is not correction-archived — closing the window between
 * the application's final recheck and the insert.
 */
import { describe, expect, it } from 'vitest'
import fs from 'fs'
import path from 'path'

const MIGRATION = path.resolve(__dirname, '../../../supabase/migrations/1121_jataka_correction_archive_write_guard.sql')
const sql = fs.existsSync(MIGRATION) ? fs.readFileSync(MIGRATION, 'utf8') : ''
const statements = sql.replace(/--[^\n]*/g, '')

describe('1121_jataka_correction_archive_write_guard.sql', () => {
  it('exists at the JATAKA-REQ-02 reserved number', () => {
    expect(fs.existsSync(MIGRATION)).toBe(true)
  })

  it('defines an idempotent guard function that locks the parent conversation and refuses correction history', () => {
    expect(statements).toMatch(/CREATE OR REPLACE FUNCTION public\.jataka_refuse_write_to_correction_archive\(\)/i)
    expect(statements).toMatch(/FROM public\.conversations\s+WHERE id = NEW\.conversation_id\s+FOR SHARE/i)
    expect(statements).toMatch(/SELECT archive_reason INTO (\w+)[\s\S]*IF \1 = 'chart_details_changed'/i)
    expect(statements).toMatch(/RAISE EXCEPTION 'CONVERSATION_ARCHIVED_READ_ONLY/i)
    expect(statements).toMatch(/ERRCODE = 'check_violation'/i)
  })

  it.each(['conversation_messages', 'conversation_branches'])('guards every insert into %s, idempotently', (table) => {
    expect(statements).toMatch(new RegExp(`DROP TRIGGER IF EXISTS jataka_correction_archive_guard ON public\\.${table}`, 'i'))
    expect(statements).toMatch(
      new RegExp(`CREATE TRIGGER jataka_correction_archive_guard\\s+BEFORE INSERT ON public\\.${table}\\s+FOR EACH ROW EXECUTE FUNCTION public\\.jataka_refuse_write_to_correction_archive\\(\\)`, 'i'),
    )
  })

  it('changes no data and drops no table, column or constraint', () => {
    expect(statements).not.toMatch(/DROP\s+(TABLE|COLUMN|CONSTRAINT|INDEX|FUNCTION)|TRUNCATE|DELETE\s+FROM|UPDATE\s+public\.|ALTER\s+TABLE/i)
  })
})
