/**
 * Suvarna / migration 1269 (TI-L0-29) - STATIC contract: bg_panchanga.depends_on {} -> {bg_ephemeris_engine} (SS Q16).
 *
 * The live proof (disposable PostgreSQL 15 and 17 as a NOSUPERUSER NOINHERIT amjis_app with USAGE but no CREATE on
 * schema public, loaded with the full live 129-row registry graph: apply, acyclicity and topological order, the REAL
 * deps_unsatisfied gate (bg_panchanga and ga_panchanga not blocked; an errored engine DOES block), the real
 * downstream closure, trigger staleness, idempotent re-run, 9 drift cases incl. a would-be cycle, absent row,
 * silent-no-op and 13 mutants) is python-sidecar/tests/test_migration_1269_bg_panchanga_depends_on_ephemeris_engine.py.
 * This file pins the text.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1269_bg_panchanga_depends_on_ephemeris_engine.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1269 - static contract', () => {
  it('changes exactly one cell: bg_panchanga.depends_on to {bg_ephemeris_engine}', () => {
    expect(CODE.match(/\bUPDATE asset_registry SET\b/g)).toHaveLength(1)
    expect(CODE).toContain("UPDATE asset_registry SET depends_on = ARRAY['bg_ephemeris_engine']::text[]")
    expect(CODE).toContain("WHERE asset_id = 'bg_panchanga' AND depends_on = '{}'::text[]")
    const ids = new Set([...CODE.matchAll(/'((?:bg|ga|bo|ka|ph|mi)_[a-z_0-9]+)'/g)].map(m => m[1]))
    expect([...ids].sort()).toEqual(['bg_ephemeris_engine', 'bg_panchanga'])
    // the ledger's rejected target (bg_ephemeris, the table) is not taken
    expect(CODE).not.toMatch(/'bg_ephemeris'/)
  })

  it('is guarded: identity of both rows, no overwrite, no cycle (before AND after), row count', () => {
    expect(CODE).toContain("v_kind IS DISTINCT FROM 'service'")
    expect(CODE).toContain('v_writer IS DISTINCT FROM false')
    expect(CODE).toContain('v_target IS NOT NULL')
    expect(CODE).toContain("e_kind IS DISTINCT FROM 'service'")
    expect(CODE).toContain('has drifted from the audited state')
    expect(CODE).toContain('refusing to overwrite')
    expect(CODE).toContain('would close a cycle')
    expect(CODE).toContain('is on a dependency cycle after the update')
    expect(CODE.match(/WITH RECURSIVE reach/g)).toHaveLength(2)
    expect(CODE).toContain('FOR UPDATE')
    expect(CODE).toContain('GET DIAGNOSTICS v_rows = ROW_COUNT')
    expect(CODE).toContain('after the update')
  })

  it('is registry-row DML only: no CREATE/ALTER/DROP/GRANT/REVOKE/INSERT/DELETE', () => {
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE)\b/im)
    expect(CODE).not.toMatch(/\bINSERT INTO\b|\bDELETE FROM\b|SECURITY DEFINER|\bCREATE\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('states the header facts: review inputs (order, gate, hash, in-flight runs, frozen manifests), staleness, NOT done', () => {
    expect(SQL).toContain('TI-L0-29')
    for (const needle of ['DAG ORDER', 'DISPATCH GATE', 'UPSTREAM HASH', 'IN-FLIGHT RUNS', 'NIRMANA FROZEN MANIFESTS',
      'planned/running/paused', 'deps_unsatisfied', 'assertManifestMatchesRegistryIdentity', '_verify_registry_still_matches_manifest',
      'Assets that go stale: bg_panchanga ONLY', 'NOT DONE HERE', 'asset_registry_seed.ts', 'PRIVILEGE', 'IDEMPOTENT',
      'panchang_engine/__init__.py:63']) expect(SQL).toContain(needle)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range, and its number is 1269', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    expect(Number(FILE.slice(0, 4))).toBe(1269)
    expect(fs.readdirSync(MIG).filter(f => /^1269_/.test(f) && f !== FILE)).toEqual([])
  })
})
