import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const MIGRATIONS_DIR = resolve(__dirname, '../../../../migrations')

describe('migration 008 - per-native namespacing', () => {
  const sql = readFileSync(resolve(MIGRATIONS_DIR, '008_per_native_namespacing.sql'), 'utf-8')

  it('adds native_id to messages', () => expect(sql).toContain('ALTER TABLE public.messages'))
  it('adds panel_metadata to messages', () => expect(sql).toContain('panel_metadata JSONB'))
  it('includes rollback comments', () => expect(sql).toContain('ROLLBACK'))
  it('creates composite index on messages', () => expect(sql).toContain('idx_messages_native_conversation'))
})

describe('migration 009 - msr_signals', () => {
  const sql = readFileSync(resolve(MIGRATIONS_DIR, '009_msr_signals.sql'), 'utf-8')

  it('creates msr_signals table', () => expect(sql).toContain('CREATE TABLE IF NOT EXISTS public.msr_signals'))
  it('has confidence check constraint', () => expect(sql).toContain('msr_signals_confidence_range'))
  it('has native_id with default', () => expect(sql).toContain("DEFAULT 'abhisek'"))
  it('includes rollback comments', () => expect(sql).toContain('ROLLBACK'))
})
