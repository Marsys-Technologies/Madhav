/**
 * Suvarna / migration 1255 — STATIC contract (GRANT SELECT on six L0 reference tables to data_plane_builder).
 * The live proof (a disposable PostgreSQL 15 and 17 cluster: apply, idempotent re-run, SELECT-only by every
 * path, guards, extra-privilege refusal, lock_timeout, and 14 mutants) is
 * python-sidecar/tests/test_migration_1255_builder_reference_grants.py. This file pins the text so a drive-by
 * edit (a seventh table, a broader privilege, a REVOKE) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1255_builder_reference_tables_select_grants.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

const SIX = [
  'reference_nakshatra',
  'reference_nakshatra_pada',
  'bg_shashtiamsha_deities',
  'bg_graha_naisargika_friendship',
  'bg_motion_state_thresholds',
  'brahma_vichara_constants',
]
const HELD_OUT = ['bg_prashna_significators', 'yoga_family_members', 'prashna_charts']

describe('migration 1255 — static contract', () => {
  it('has ONE data-driven table list, exactly the six approved tables, in order', () => {
    const arrays = CODE.match(/tables text\[\] := ARRAY\[([\s\S]*?)\];/g) ?? []
    expect(arrays).toHaveLength(1)
    const names = [...arrays[0].matchAll(/'([a-z_]+)'/g)].map(m => m[1])
    expect(names).toEqual(SIX)
    // The table names appear nowhere else in executable SQL: guards, grants and post-check all iterate the list.
    for (const t of SIX) expect(CODE.match(new RegExp(`\\b${t}\\b`, 'g'))).toHaveLength(1)
  })

  it('holds out bg_prashna_significators, yoga_family_members and prashna_charts from the executable SQL', () => {
    for (const t of HELD_OUT) expect(CODE).not.toContain(t)
    expect(SQL).toContain('HELD OUT')
  })

  it('is SELECT-only grants and nothing else changes schema, data or membership', () => {
    const grants = CODE.match(/GRANT [^']+'|GRANT [^;]+;/g) ?? []
    expect(grants.filter(g => /GRANT SELECT ON TABLE %s TO data_plane_builder/.test(g))).toHaveLength(1)
    expect(CODE.match(/\bGRANT\b/g)).toHaveLength(1)
    expect(CODE).not.toMatch(/\bREVOKE\b|WITH GRANT OPTION|SECURITY DEFINER|\bINSERT INTO\b|\bUPDATE\b\s+\w+\s+SET|\bDELETE FROM\b/i)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE)\b/im)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
    expect(CODE).not.toMatch(/GRANT (ALL|[A-Z, ]*(INSERT|UPDATE|DELETE|TRUNCATE|REFERENCES|TRIGGER))/)
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('is guarded (role, existence, relkind), skips held grants, and post-checks SELECT and the absence of extras', () => {
    expect(CODE).toContain("rolname = 'data_plane_builder'")
    expect(CODE).toContain('does not exist')
    expect(CODE).toContain("kind NOT IN ('r', 'p')")
    expect(CODE).toContain("has_table_privilege('data_plane_builder', rel, 'SELECT')")
    expect(CODE).toContain("has_any_column_privilege('data_plane_builder', rel, p)")
    expect(CODE).toContain("ARRAY['INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']")
    expect(CODE).toContain('holds more than SELECT')
    expect(CODE).toContain('lacks SELECT')
  })

  it('states the header facts: ordering, serving effect, never-REVOKE, readers, proven vs inferred', () => {
    expect(SQL).toContain('ORDERING.')
    expect(SQL).toContain('SERVING EFFECT AT APPLY: none (no registry/freshness/trigger touched)')
    expect(SQL).toContain('never REVOKE')
    expect(SQL).toContain('PROVEN vs INFERRED')
    for (const reader of ['ga_nakshatra.py', 'ga_sensitive_degree_writer.py', 'ga_vargas_writer.py',
      'ga_condition_writer.py', 'ga_vichara_writer.py']) expect(SQL).toContain(reader)
  })

  it('is a ROUTINE migration (not in the protected public-schema set), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4)); expect(n).toBeGreaterThanOrEqual(1200); expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1255_/.test(f) && f !== FILE)).toEqual([])
  })
})
