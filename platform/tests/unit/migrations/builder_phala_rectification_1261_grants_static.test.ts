/**
 * Suvarna / migration 1261 — STATIC contract (GRANT SELECT, INSERT, DELETE on phala_rectification and
 * phala_rectification_best to data_plane_builder). The live proof (a disposable PostgreSQL cluster: apply, the writer's
 * exact statements as the builder, exactly-three-privileges, idempotent re-run, guards incl. a non-owner migration user,
 * extra-privilege refusal, lock_timeout, and 14 mutants) is
 * python-sidecar/tests/test_migration_1261_builder_phala_rectification_grants.py. This file pins the text so a drive-by
 * edit (UPDATE, a third table, a REVOKE, life_events) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1261_builder_phala_rectification_dml_grants.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1261 — static contract', () => {
  it('has ONE table list (exactly the two tables) and ONE privilege list (exactly SELECT, INSERT, DELETE)', () => {
    const tables = CODE.match(/\btables text\[\] := ARRAY\[([\s\S]*?)\];/g) ?? []
    const privs = CODE.match(/\bprivs text\[\] := ARRAY\[([\s\S]*?)\];/g) ?? []
    expect(tables).toHaveLength(1)
    expect(privs).toHaveLength(1)
    expect([...(tables[0] ?? '').matchAll(/'([a-z_]+)'/g)].map(m => m[1])).toEqual(['phala_rectification', 'phala_rectification_best'])
    expect([...(privs[0] ?? '').matchAll(/'([A-Z]+)'/g)].map(m => m[1])).toEqual(['SELECT', 'INSERT', 'DELETE'])
    for (const t of ['phala_rectification', 'phala_rectification_best']) expect(CODE.match(new RegExp(`'${t}'`, 'g'))).toHaveLength(1)
  })

  it('is grants only, to data_plane_builder only; nothing else, and the held-out objects stay out', () => {
    expect(CODE.match(/EXECUTE format\('GRANT/g)).toHaveLength(1)
    expect(CODE).toContain("GRANT %s ON TABLE %s TO data_plane_builder")
    expect(CODE).not.toMatch(/\bREVOKE\b|WITH GRANT OPTION|SECURITY DEFINER|\bINSERT INTO\b|\bUPDATE\s+\w+\s+SET|\bDELETE FROM\b|\bSEQUENCE\b/i)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE)\b/im)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/TO (PUBLIC|role_)/)
    for (const t of ['life_events', 'chart_fact_identity', 'role_sidecar']) expect(CODE).not.toContain(t)
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('is guarded (role, existence, relkind, grantor) and post-checks the three privileges and the absence of extras', () => {
    for (const n of ["rolname = 'data_plane_builder'", '1261: role data_plane_builder does not exist', "kind NOT IN ('r', 'p')",
      "pg_has_role(current_user, owner, 'USAGE')", "has_table_privilege('data_plane_builder', rel, p)",
      "has_any_column_privilege('data_plane_builder', rel, x)", "ARRAY['UPDATE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']",
      'holds more than SELECT, INSERT, DELETE', 'lacks % on']) expect(CODE).toContain(n)
  })

  it('states the header facts: writer verbs, no sequences, grantor, the ka_kshetra / 1073 side effect, the life_events gap', () => {
    for (const n of ['HELD', 'AFTER S-L1', "on SS's review", 'WHAT THE WRITER ACTUALLY NEEDS', 'SEQUENCES: none', 'WHO ISSUES THE GRANT',
      'data_plane_builder=ard/amjis_app', 'Migration 1073', 'SIDE EFFECTS AND TIMING', 'AFTER THE S-L3 ka_kshetra BUILD AND BEFORE S-L4', 'DECLARED J1 VIOLATION', 'WILL RAISE', 'NO DIRECT TABLE GRANT on life_events', 'migration 1274', 'ka_kshetra', 'NOT SUFFICIENT BY ITSELF',
      'life_events', 'SERVING EFFECT AT APPLY: none', 'never REVOKE', 'VERIFICATION AFTER APPLY', 'Q-L4-04']) expect(FLAT).toContain(n)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1200)
    expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1261_/.test(f) && f !== FILE)).toEqual([])
  })
})
