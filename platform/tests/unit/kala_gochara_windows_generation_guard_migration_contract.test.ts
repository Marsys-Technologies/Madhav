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
  it('skips only when the stricter production guard exists, is enabled on BOTH row and truncate, and is bound', () => {
    expect(code).toContain("to_regprocedure('public.kala_gochara_generation_guard()') IS NOT NULL")
    expect(code).toMatch(/t\.tgname = 'trg_kgw_generation_guard_row'\s+AND t\.tgenabled = 'O'/)
    expect(code).toMatch(/t\.tgname = 'trg_kgw_generation_guard_truncate'\s+AND t\.tgenabled = 'O'/)
    expect(code).toContain('verified, nothing to create')
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
    // The self-test accepts this migration's refusal text AND the production guard's.
    expect(code).toMatch(/SQLERRM LIKE '%BUILD-PROTECTED%' OR SQLERRM LIKE '%GOCHARA GENERATION GUARD%'/)
  })

  it('has no transaction control (the migration runner wraps each file)', () => {
    expect(code).not.toMatch(/^\s*(BEGIN|COMMIT);/m)
  })

  it('changes no privilege, role or ownership', () => {
    expect(code).not.toMatch(/\bGRANT\b|\bREVOKE\b|ALTER\s+(ROLE|USER|SCHEMA)|CREATE\s+(ROLE|SCHEMA)|OWNER\s+TO/i)
  })
})
