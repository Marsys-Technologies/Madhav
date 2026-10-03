/**
 * Suvarna / migration 1267 (TI-L0-08) - STATIC contract: the registry side of the rider relation, one nullable
 * self-referencing column asset_registry.producer_asset_id set for exactly three riders.
 *
 * The live proof (disposable PostgreSQL 15 and 17 as a NOSUPERUSER NOINHERIT amjis_app with USAGE but no CREATE on
 * schema public: apply, constraint enforcement, no relation/ACL change, trigger not fired, idempotent re-run, partial
 * state, 7 drift cases, absent riders, silent-no-op defence and 16 mutants) is
 * python-sidecar/tests/test_migration_1267_asset_registry_rider_producer_relation.py. This file pins the text.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1267_asset_registry_rider_producer_relation.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1267 - static contract', () => {
  it('adds exactly one nullable column and exactly two constraints, all on asset_registry', () => {
    expect(CODE.match(/ADD COLUMN IF NOT EXISTS producer_asset_id text;/g)).toHaveLength(1)
    expect(CODE.match(/\bADD COLUMN\b/g)).toHaveLength(1)
    expect(CODE.match(/ADD CONSTRAINT/g)).toHaveLength(2)
    expect(CODE).toContain('asset_registry_producer_asset_id_fkey')
    expect(CODE).toContain('FOREIGN KEY (producer_asset_id) REFERENCES asset_registry(asset_id) ON DELETE RESTRICT')
    expect(CODE).toContain('asset_registry_producer_not_self')
    expect(CODE).toContain('CHECK (producer_asset_id IS NULL OR producer_asset_id <> asset_id)')
    expect(CODE.match(/\bALTER TABLE\b/g)).toHaveLength(3)
    for (const m of CODE.matchAll(/\bALTER TABLE (\w+)/g)) expect(m[1]).toBe('asset_registry')
    expect(CODE).not.toMatch(/DROP COLUMN|DROP CONSTRAINT|RENAME|ALTER COLUMN|SET DATA TYPE|\bTYPE\b\s+\w+\s+USING/i)
  })

  it('names exactly the three audited riders and their audited producers', () => {
    expect(CODE).toContain("ARRAY['bg_nakshatra_medical', 'bg_sign_medical', 'bg_transit_engine']")
    expect(CODE).toContain("WHEN 'bg_transit_engine' THEN 'bg_transit_rules' ELSE 'bg_medical_mappings'")
    // writes only the new column, nothing else, and no other asset id appears in executable SQL
    const sets = [...CODE.matchAll(/UPDATE asset_registry SET (\w+) =/g)].map(m => m[1])
    expect(sets).toEqual(['producer_asset_id'])
    const ids = new Set([...CODE.matchAll(/'((?:bg|ga|bo|ka|ph|mi)_[a-z_0-9]+)'/g)].map(m => m[1]))
    expect([...ids].sort()).toEqual(['bg_medical_mappings', 'bg_nakshatra_medical', 'bg_sign_medical', 'bg_transit_engine', 'bg_transit_rules'])
  })

  it('creates no schema object a routine runner could not (no CREATE, no GRANT, no function/trigger/index/table)', () => {
    expect(CODE).not.toMatch(/\bCREATE\b/i)
    expect(CODE).not.toMatch(/\bGRANT\b|\bREVOKE\b|SECURITY DEFINER|\bDROP\b|\bTRUNCATE\b|\bDELETE FROM\b|\bINSERT INTO\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('is guarded: producer must exist/be active/data/have a writer, rider identity pinned, no overwrite, post-checked', () => {
    expect(CODE).toContain('p_writer IS DISTINCT FROM true')
    expect(CODE).toContain('p_active IS DISTINCT FROM true')
    expect(CODE).toContain("p_kind IS DISTINCT FROM 'data'")
    expect(CODE).toContain("v_kind IS DISTINCT FROM 'data' OR v_target IS DISTINCT FROM v_rider")
    expect(CODE).toContain('refusing to overwrite')
    expect(CODE).toContain('FOR UPDATE')
    expect(CODE).toContain('GET DIAGNOSTICS v_rows = ROW_COUNT')
    expect(CODE).toContain('after the migration') // post-check present
    expect(CODE.match(/pg_constraint/g)!.length).toBeGreaterThanOrEqual(3)
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('states the header facts: concern, design choice, no reader yet, trigger not fired, privilege, NOT done', () => {
    expect(SQL).toContain('TI-L0-08')
    expect(SQL).toContain('DESIGN CHOICE FOR SS')
    expect(SQL).toContain('NO READER YET')
    expect(SQL).toContain('Does NOT fire nirmana_registry_receipt_invalidation')
    expect(SQL).toContain('NO asset goes stale')
    expect(SQL).toContain('PRIVILEGE')
    expect(SQL).toContain('NOT CREATE on schema public')
    expect(SQL).toContain('NOT DONE HERE')
    expect(SQL).toContain('asset_declarations.json')
    expect(SQL).toContain('IDEMPOTENT')
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range, and its number is 1267', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    expect(Number(FILE.slice(0, 4))).toBe(1267)
    expect(fs.readdirSync(MIG).filter(f => /^1267_/.test(f) && f !== FILE)).toEqual([])
  })
})
