/**
 * Suvarna / migration 1266 (TI-L0-07) - STATIC contract: asset_registry correction batch
 * (bg_parihara_rules.target_floor 449 -> 440; has_writer false -> true for bg_nakshatra_medical and bg_transit_engine).
 *
 * The live proof (disposable PostgreSQL 15 and 17 as a NOSUPERUSER NOINHERIT amjis_app with USAGE but no CREATE on
 * schema public: apply, idempotent re-run, partial state, drift refusal, absent rows, silent-no-op defence, and 13
 * mutants) is python-sidecar/tests/test_migration_1266_l0_registry_floor_and_rider_has_writer.py. This file pins the
 * text so a drive-by edit (a fourth cell, a CREATE, a guard removed) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1266_l0_registry_parihara_floor_and_rider_has_writer.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1266 - static contract', () => {
  it('changes exactly three cells: the parihara floor and the two riders has_writer', () => {
    expect(CODE.match(/\bUPDATE asset_registry SET\b/g)).toHaveLength(2)
    const sets = [...CODE.matchAll(/UPDATE asset_registry SET (\w+) = (\w+)/g)].map(m => `${m[1]}=${m[2]}`)
    expect(sets.sort()).toEqual(['has_writer=true', 'target_floor=440'])
    expect(CODE).toContain("ARRAY['bg_nakshatra_medical', 'bg_transit_engine']")
    // bg_sign_medical is ALREADY has_writer = true and must not be touched; no other asset id is written
    expect(CODE).not.toContain('bg_sign_medical')
    expect(CODE).not.toContain('bg_medical_mappings')
    expect(CODE).not.toContain('bg_transit_rules')
  })

  it('is guarded on the audited live values and raises on drift', () => {
    expect(CODE).toContain("'6d886abbfa16a5c5d6b6688dd8d01b17'") // md5(count_sql) of bg_parihara_rules
    expect(CODE).toContain('c81dda22bcfe765b0e4d0750db3780c5') // md5(count_sql) of bg_nakshatra_medical
    expect(CODE).toContain('40a0fe926e122a3fb8fe2e628dc33614') // md5(count_sql) of bg_transit_engine
    expect(CODE).toContain('v_floor = 449')
    expect(CODE).toContain('v_floor = 440')
    expect(CODE.match(/drifted from the audited state/g)).toHaveLength(2)
    expect(CODE).toContain('FOR UPDATE')
    expect(CODE.match(/GET DIAGNOSTICS v_rows = ROW_COUNT/g)).toHaveLength(2)
    expect(CODE).toContain('after the update') // post-check present
  })

  it('is registry-row DML only: no CREATE/ALTER/DROP/GRANT/REVOKE/INSERT/DELETE, nothing in schema public to create', () => {
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE)\b/im)
    expect(CODE).not.toMatch(/\bINSERT INTO\b|\bDELETE FROM\b|SECURITY DEFINER|\bCREATE\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('states the header facts: concern, trigger and staleness, cascade, what is NOT done, privilege', () => {
    expect(SQL).toContain('TI-L0-07')
    expect(SQL).toContain('nirmana_registry_receipt_invalidation')
    expect(SQL).toContain('Assets that go stale: bg_parihara_rules ONLY')
    expect(SQL).toContain('EXPECTED CASCADE')
    expect(SQL).toContain('Build.exercised')
    expect(SQL).toContain('NOT DONE HERE')
    expect(SQL).toContain('asset_registry_seed.ts')
    expect(SQL).toContain('PRIVILEGE')
    expect(SQL).toContain('No CREATE, no GRANT, no DDL')
    expect(SQL).toContain('IDEMPOTENT')
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range, and its number is 1266', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBe(1266)
    expect(fs.readdirSync(MIG).filter(f => /^1266_/.test(f) && f !== FILE)).toEqual([])
  })
})
