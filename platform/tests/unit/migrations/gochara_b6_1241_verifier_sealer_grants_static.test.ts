/**
 * Pravāha B6.0 / Codex rounds 9–10 (R9-6, R10-7) — STATIC contract of migration 1241: ONE reviewed, additive grants migration for the verifier and the
 * sealer that BACKFILLS 1240's role-conditional grants and carries its own, driven by ONE jsonb spec, with an exact ACL closure check. The live proof
 * (the real file applied in the composed rehearsal; each 1241-origin grant individually necessary; the late-role backfill; the closure refusals; the
 * column-narrow publication update and legacy-windows read) is python-sidecar/tests/l3/gochara/test_b6_composed_seal_flows.py.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1241_gochara_verifier_sealer_inventory_grants.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
type TableEntry = [string, string, string[] | null, string]
type FnEntry = [string, string]
const SPEC = JSON.parse(CODE.match(/\$spec\$([\s\S]*?)\$spec\$/)![1]) as {
  roles: Record<string, { tables: TableEntry[]; functions: FnEntry[] }>
  builder_backfill: { role: string; functions: string[] }
}
const V = SPEC.roles.gochara_verifier
const S = SPEC.roles.gochara_sealer

describe('migration 1241 — static contract', () => {
  it('is grants only: no DDL, no REVOKE, no TRUNCATE statement, no SECURITY DEFINER, no transaction control', () => {
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|REVOKE|TRUNCATE)\b|SECURITY DEFINER|WITH GRANT OPTION/im)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('names exactly the two principals plus the one builder helper backfill; every entry has origin 1240 or 1241', () => {
    expect(Object.keys(SPEC.roles).sort()).toEqual(['gochara_sealer', 'gochara_verifier'])
    expect(SPEC.builder_backfill).toEqual({ role: 'data_plane_builder', functions: ['ka_gochara_window_qualification_ok(jsonb)'] })
    for (const body of Object.values(SPEC.roles)) {
      for (const [, , , origin] of body.tables) expect(['1240', '1241']).toContain(origin)
      for (const [, origin] of body.functions) expect(['1240', '1241']).toContain(origin)
    }
  })

  it('the verifier: no UPDATE anywhere, DELETE only on 1240\'s own window-verification table, INSERT only on the two verification tables and the append-only seal-brief table (F-R12-4), nothing on the seal', () => {
    for (const [t, p] of V.tables) {
      expect(p).not.toBe('UPDATE')
      if (p === 'DELETE') expect(t).toBe('ka_gochara_eval_window_verification')
      if (p === 'INSERT') expect(['ka_gochara_eval_window_verification', 'ka_gochara_search_inventory_verification', 'ka_gochara_seal_brief']).toContain(t)
    }
    expect(V.tables.filter(([t, p]) => t === 'ka_gochara_search_inventory_verification' && p === 'DELETE')).toEqual([])
    expect(V.functions.map(f => f[0]).join('\n')).not.toMatch(/seal_generation/)
  })

  it('the sealer: writes only INSERT on the seal row and a COLUMN-LEVEL UPDATE of the four publication columns ledger.publish sets; reads the legacy windows ONLY on (chart_id, generation)', () => {
    const writes = S.tables.filter(([, p]) => p !== 'SELECT')
    expect(writes).toHaveLength(3)
    expect(writes).toEqual(expect.arrayContaining([
      ['ka_gochara_generation_seal', 'INSERT', null, '1241'],
      ['kala_gochara_publication', 'UPDATE', ['status', 'published_at', 'content_digest', 'row_counts'], '1241'],
      ['ka_gochara_seal_approval', 'INSERT', null, '1241'],          // R11-3: the approval receipt (append-only; the sealer is the only writer)
    ]))
    expect(S.tables.filter(([t]) => t === 'kala_gochara_windows')).toEqual([['kala_gochara_windows', 'SELECT', ['chart_id', 'generation'], '1241']])
  })

  it('R15-6 (v7): the sealer may SELECT, and ONLY SELECT, the five registry relations its in-transaction registry re-derivation reads (seal_registry_drift) — nothing wider, v7 adds nothing to the verifier', () => {
    const registry = ['ka_gochara_rule_path', 'ka_gochara_rule_path_prerequisite', 'ka_gochara_rule_path_soft_factor', 'ka_gochara_predicate', 'ka_gochara_factor', 'ka_gochara_rule_path_seal']
    for (const t of registry) expect(S.tables.filter(([x]: any) => x === t)).toEqual([[t, 'SELECT', null, '1241']])
    expect(S.tables.filter(([, p]: any) => p === 'SELECT')).toHaveLength(S.tables.length - 3)         // everything but the three writes is a SELECT
    expect(S.functions.map(([f]: any) => f).filter((f: string) => /predicate|factor|rule_path/.test(f))).toEqual([])   // no registry function granted
    for (const t of registry.slice(0, 5)) for (const row of V.tables.filter(([x]: any) => x === t)) expect(row.slice(1, 3)).toEqual(['SELECT', null])   // whatever the verifier already held there stays SELECT-only; v7's edit is in the SEALER block
  })

  it('R11-3: both principals read the migration ledger ONLY at column level (filename, sha256, applied_at); the verifier holds nothing on the receipt; the sealer reads it for the receipt-missing check', () => {
    const ledger = (role: any) => role.tables.filter(([t]: any) => t === '_migrations_applied')
    expect(ledger(S)).toEqual([['_migrations_applied', 'SELECT', ['filename', 'sha256', 'applied_at'], '1241']])
    expect(ledger(V)).toEqual([['_migrations_applied', 'SELECT', ['filename', 'sha256', 'applied_at'], '1241']])
    expect(V.tables.filter(([t]: any) => t === 'ka_gochara_seal_approval')).toEqual([])
    expect(S.tables.filter(([t]: any) => t === 'ka_gochara_seal_approval').map(([, p]: any) => p).sort()).toEqual(['INSERT', 'SELECT'])
    expect(S.functions.map(([f]: any) => f)).toContain('ka_gochara_seal_receipt_missing(uuid,text)')
  })

  it('does NOT carry the L1 reads (chart_facts / chart_dashas): their ACLs belong to the data-plane ownership script', () => {
    expect(CODE).not.toMatch(/\bchart_facts\b|\bchart_dashas\b/)
    expect(SQL).toContain('data-plane-ownership-preflight.ts')
  })

  it('refuses before the window, guards each role (WARNING, never silent), PRINTS the principals found, and closes the ENTIRE ACL (required AND prohibited)', () => {
    expect(CODE).toContain('the protected window (1206, 1240) has not been applied')
    expect(CODE).toContain('NOT FOUND — NO grant was issued to it')
    expect(CODE).toContain('principals found: gochara_verifier=%, gochara_sealer=%, data_plane_builder=%')
    expect(CODE).toContain('post-apply ACL closure failed')
    expect(CODE).toContain('PROHIBITED but held')
    for (const priv of ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']) expect(CODE).toContain(`'${priv}'`)
    expect(CODE).toContain('has_column_privilege')
    expect(CODE).toContain('has_function_privilege')
  })

  it('is a ROUTINE migration numbered above 1240 (a number below 1240 would be an unapplied predecessor of the window)', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4)); expect(n).toBeGreaterThan(1240); expect(n).toBeLessThanOrEqual(1249)
    for (const d of [MIG, path.resolve(__dirname, '../../../python-sidecar/scripts/kala_gochara_cutover')].filter(x => fs.existsSync(x)))
      expect(fs.readdirSync(d).filter(f => /^1241_/.test(f) && f !== FILE)).toEqual([])
  })
})
