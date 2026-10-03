/**
 * Suvarna / migration 1260 — STATIC contract (seven cross-asset ON DELETE CASCADE foreign keys dropped, detector views added).
 * The live proof (a disposable PostgreSQL cluster: cascade precondition, apply, no child deleted by a parent delete, the
 * detector's orphan counts, idempotent re-run, definition guards, lock_timeout, SECURITY INVOKER, and 11 mutants) is
 * python-sidecar/tests/test_migration_1260_cross_asset_cascade_fks.py. This file pins the text so a drive-by edit
 * (an eighth key, a RESTRICT re-creation, a dropped guard, a data write) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1260_cross_asset_cascade_fks_to_detector.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')

const REFS = [
  ['phala_anchors_convergence_id_fkey', 'phala_anchors', 'convergence_id', 'kala_convergence', 'convergence_id'],
  ['kala_darshana_convergence_id_fkey', 'kala_darshana', 'convergence_id', 'kala_convergence', 'convergence_id'],
  ['kala_obstruction_convergence_id_fkey', 'kala_obstruction', 'convergence_id', 'kala_convergence', 'convergence_id'],
  ['phala_pramana_anchor_id_fkey', 'phala_pramana', 'anchor_id', 'phala_anchors', 'anchor_id'],
  ['phala_sankrama_source_anchor_id_fkey', 'phala_sankrama', 'source_anchor_id', 'phala_anchors', 'anchor_id'],
  ['phala_sodhana_anchor_id_fkey', 'phala_sodhana', 'anchor_id', 'phala_anchors', 'anchor_id'],
  ['phala_suddha_sodhana_anchor_id_fkey', 'phala_suddha_sodhana', 'anchor_id', 'phala_anchors', 'anchor_id'],
]
// Out of scope by SS ruling: must never appear in the executable SQL.
const OUT_OF_SCOPE = ['kala_bhavishya_convergence_id_fkey', 'phala_anchors_bhavishya_id_fkey',
  'phala_muhurta_linked_anchor_id_fkey', 'phala_mitigation_linked_anchor_id_fkey', 'chart_fact_identity', 'charts']

describe('migration 1260 — static contract', () => {
  it('has ONE data-driven reference list, exactly the seven approved references, in order', () => {
    const arrays = CODE.match(/\brefs text\[\] := ARRAY\[([\s\S]*?)\];/g) ?? []
    expect(arrays).toHaveLength(1)
    const first = arrays[0]
    if (first === undefined) throw new Error('Expected the asserted single reference list')
    const rows = [...first.matchAll(/'([a-z_]+\|[a-z_]+\|[a-z_]+\|[a-z_]+\|[a-z_]+)'/g)].map(m => (m[1] ?? '').split('|'))
    expect(rows).toEqual(REFS)
    for (const [con] of REFS) expect(CODE.match(new RegExp(`\\b${con}\\b`, 'g'))).toHaveLength(1)
  })

  it('keeps the out-of-scope links out of the executable SQL', () => {
    for (const t of OUT_OF_SCOPE) expect(CODE).not.toMatch(new RegExp(`\\b${t}\\b`))
    expect(SQL).toContain('NOT DONE HERE')
  })

  it('is schema-only: no data write, no grant, no revoke, no table/column/index drop, no transaction control', () => {
    expect(CODE).not.toMatch(/\b(INSERT INTO|DELETE FROM|TRUNCATE|GRANT|REVOKE)\b/i)
    expect(CODE).not.toMatch(/\bUPDATE\s+\w+\s+SET\b/i)
    expect(CODE).not.toMatch(/\bDROP (TABLE|INDEX|COLUMN|VIEW|SCHEMA|TRIGGER|FUNCTION)\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/ADD CONSTRAINT|SET NULL|ON DELETE (RESTRICT|NO ACTION)/i)
    expect(CODE.match(/DROP CONSTRAINT/g)).toHaveLength(1)
    expect(CODE).not.toContain('DROP CONSTRAINT IF EXISTS') // each drop is guarded one by one, never blanket IF EXISTS
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('guards table/column existence and the exact constraint definition; tolerates only absent or exact', () => {
    for (const n of ['does not exist', 'is not an ordinary table', 'pg_get_constraintdef', 'ON DELETE CASCADE',
      'is not the constraint this migration was written against', 'is already absent']) expect(CODE).toContain(n)
    expect(CODE).toContain("regexp_replace(pg_get_constraintdef(c.oid), ' public\\.', ' ', 'g')")
  })

  it('post-checks: none left, no cascading FK left, FK count fell by exactly the dropped number, views security_invoker, seven rows', () => {
    for (const n of ['still exists on public', 'a cascading foreign key from', 'something else changed',
      'not security_invoker', 'does not return exactly']) expect(CODE).toContain(n)
  })

  it('builds two SECURITY INVOKER views from the same list and grants nothing', () => {
    expect(CODE.match(/CREATE OR REPLACE VIEW/g)).toHaveLength(2)
    expect(CODE.match(/WITH \(security_invoker = true\)/g)).toHaveLength(2)
    expect(CODE).toContain('vw_cross_asset_reference_orphans_by_chart')
    expect(CODE).toContain('vw_cross_asset_reference_orphans')
    expect(CODE).toContain('FILTER (WHERE p.%I IS NULL)')
  })

  it('states the header facts: design choice, writer effect, orphans today, trigger scan, serving effect, locks, not-done', () => {
    for (const n of ['HELD', 'AFTER S-L1', "on SS's review", 'DESIGN CHOICE: DROP', 'DEFERRABLE INITIALLY DEFERRED does not help',
      'EFFECT ON THE EXISTING WRITERS', 'ORPHANS TODAY', '0 on all seven references', 'TRIGGER SCAN', 'BLIND SPOTS',
      'SERVING EFFECT AT APPLY: none expected', 'LOCK-WAIT RISK', 'NOT DONE HERE', 'VERIFICATION BY PRODUCTION STRUCTURE',
      'ROLLBACK', 'Q-L4-03', 'F-3', 'migration 363', 'migration 680']) expect(FLAT).toContain(n)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1200)
    expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1260_/.test(f) && f !== FILE)).toEqual([])
  })
})
