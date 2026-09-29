import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

// Contract for migration 1071 after the production deploy failure
// (`permission denied for schema public`: the migration login has no CREATE on `public`).
// The DDL that needs CREATE must run ONLY when the stricter production guard is absent, must never be
// silently skipped, and the migration must not carry transaction control (the runner supplies it).
const sql = readFileSync(
  resolve(__dirname, '../../migrations/1071_kala_gochara_windows_generation_guard.sql'), 'utf8')
const code = sql.split('\n').filter((line) => !line.trim().startsWith('--')).join('\n')

describe('migration 1071 conditional guard install', () => {
  it('skips only when the stricter production guard is bound by OID, function, events and enabled mode on BOTH triggers', () => {
    expect(code).toContain("to_regprocedure('public.kala_gochara_generation_guard()') IS NOT NULL")
    for (const [name, tgtype] of [['trg_kgw_generation_guard_row', 27], ['trg_kgw_generation_guard_truncate', 34]] as const) {
      const block = code.slice(code.indexOf(`t.tgname = '${name}'`))
      expect(block).toContain("t.tgrelid = to_regclass('public.kala_gochara_windows')")
      expect(block.slice(0, 400)).toContain("t.tgfoid = to_regprocedure('public.kala_gochara_generation_guard()')")
      expect(block.slice(0, 400)).toContain(`t.tgtype = ${tgtype} AND t.tgenabled = 'O'`)
    }
  })

  it('never uses a literal ::regclass/::regprocedure cast in the skip predicate (plan-time error on fresh databases)', () => {
    const predicate = code.slice(code.indexOf('DO $mig1071$'), code.indexOf('EXECUTE $ddl1071$'))
    expect(predicate).not.toMatch(/'[^']+'::regclass|'[^']+'::regprocedure/)
  })

  it('proves the skip behaviourally: a v1 UPDATE must be refused with the production guard message, else RAISE', () => {
    const predicate = code.slice(code.indexOf('DO $mig1071$'), code.indexOf('EXECUTE $ddl1071$'))
    expect(predicate).toContain("SQLERRM LIKE '%GOCHARA GENERATION GUARD%'")
    expect(predicate).toContain('the guard is installed but inert')
    expect(predicate).toContain('behavioural probe NOT RUN (no generation=v1 row present')
  })

  it('carries the original DDL unchanged inside a guarded EXECUTE with distinct dollar-quote tags', () => {
    expect(code).toMatch(/DO \$mig1071\$/)
    expect(code).toMatch(/EXECUTE \$ddl1071\$/)
    expect(code).toContain('CREATE OR REPLACE FUNCTION kala_gochara_windows_generation_guard_row()')
    expect(code).toContain('CREATE OR REPLACE FUNCTION kala_gochara_windows_generation_guard_truncate()')
    expect(code).toContain('CREATE TRIGGER trg_kala_gochara_windows_generation_guard_row')
    expect(code).toContain('CREATE TRIGGER trg_kala_gochara_windows_generation_guard_truncate')
    expect(code).toContain("SET LOCAL lock_timeout = '2s'")
  })

  it('never skips silently: the create path keeps its fail-closed catalog checks and behavioural self-test', () => {
    expect(code).toContain('migration 1071 did not take effect; still missing:')
    expect(code).toContain("migration 1071 self-test FAILED: a generation=''v1'' UPDATE was permitted")
    // The create-path self-test accepts only this migration's own refusal text.
    const createPath = code.slice(code.indexOf('EXECUTE $ddl1071$'))
    expect(createPath).toContain("SQLERRM LIKE '%BUILD-PROTECTED%'")
    expect(createPath).not.toContain('GOCHARA GENERATION GUARD')
  })

  it('has no transaction control (the migration runner wraps each file)', () => {
    expect(code).not.toMatch(/^\s*(BEGIN|COMMIT);/m)
  })

  it('changes no privilege, role or ownership', () => {
    expect(code).not.toMatch(/\bGRANT\b|\bREVOKE\b|ALTER\s+(ROLE|USER|SCHEMA)|CREATE\s+(ROLE|SCHEMA)|OWNER\s+TO/i)
  })
})
