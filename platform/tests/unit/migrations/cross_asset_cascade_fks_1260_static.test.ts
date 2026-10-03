/**
 * Suvarna / migration 1260 — STATIC contract (seven cross-asset ON DELETE CASCADE foreign keys dropped; five chart_id ->
 * charts(id) ON DELETE CASCADE ownership links added so chart deletion still reaches the L4 tables; the orphan detector is
 * plain read-only SQL, NOT a DB object). The live proof (a disposable PostgreSQL cluster, run as amjis_app on a
 * production-mirrored layout where amjis_app has no CREATE on schema public: cascade precondition, apply, no child deleted by a
 * parent delete, the detector's orphan counts, the DELETE-ROUTE scenario, idempotent re-run, definition guards, STOP guards,
 * active-run guard, lock_timeout, and 16 mutants) is python-sidecar/tests/test_migration_1260_cross_asset_cascade_fks.py. This
 * file pins the text so a drive-by edit (an eighth key, a RESTRICT re-creation, a CREATE VIEW, a dropped guard, a data write)
 * is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const DET = path.resolve(__dirname, '../../../scripts/nirmana')
const FILE = '1260_cross_asset_cascade_fks_to_detector.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const FLAT = SQL.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const DET_SQL = fs.readFileSync(path.join(DET, 'cross_asset_reference_orphans.sql'), 'utf8')
const DET_CODE = DET_SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const DET_PY = fs.readFileSync(path.join(DET, 'cross_asset_reference_orphans.py'), 'utf8')

const REFS = [
  ['phala_anchors_convergence_id_fkey', 'phala_anchors', 'convergence_id', 'kala_convergence', 'convergence_id'],
  ['kala_darshana_convergence_id_fkey', 'kala_darshana', 'convergence_id', 'kala_convergence', 'convergence_id'],
  ['kala_obstruction_convergence_id_fkey', 'kala_obstruction', 'convergence_id', 'kala_convergence', 'convergence_id'],
  ['phala_pramana_anchor_id_fkey', 'phala_pramana', 'anchor_id', 'phala_anchors', 'anchor_id'],
  ['phala_sankrama_source_anchor_id_fkey', 'phala_sankrama', 'source_anchor_id', 'phala_anchors', 'anchor_id'],
  ['phala_sodhana_anchor_id_fkey', 'phala_sodhana', 'anchor_id', 'phala_anchors', 'anchor_id'],
  ['phala_suddha_sodhana_anchor_id_fkey', 'phala_suddha_sodhana', 'anchor_id', 'phala_anchors', 'anchor_id'],
]
const CHART_LINKS = [
  ['phala_anchors_chart_id_fkey', 'phala_anchors'], ['phala_pramana_chart_id_fkey', 'phala_pramana'],
  ['phala_sankrama_chart_id_fkey', 'phala_sankrama'], ['phala_sodhana_chart_id_fkey', 'phala_sodhana'],
  ['phala_suddha_sodhana_chart_id_fkey', 'phala_suddha_sodhana'],
]
// Out of scope by SS ruling: must never appear in the executable SQL.
const OUT_OF_SCOPE = ['kala_bhavishya_convergence_id_fkey', 'phala_anchors_bhavishya_id_fkey',
  'phala_muhurta_linked_anchor_id_fkey', 'phala_mitigation_linked_anchor_id_fkey', 'chart_fact_identity', 'phala_muhurta', 'phala_mitigation']

describe('migration 1260 — static contract', () => {
  it('has ONE reference list: exactly the seven approved references, in order', () => {
    const arrays = CODE.match(/\brefs text\[\] := ARRAY\[([\s\S]*?)\];/g) ?? []
    expect(arrays).toHaveLength(1)
    const first = arrays[0]
    if (first === undefined) throw new Error('Expected the asserted single reference list')
    const rows = [...first.matchAll(/'([a-z_]+\|[a-z_]+\|[a-z_]+\|[a-z_]+\|[a-z_]+)'/g)].map(m => (m[1] ?? '').split('|'))
    expect(rows).toEqual(REFS)
    for (const [con] of REFS) expect(CODE.match(new RegExp(`\\b${con}\\b`, 'g'))).toHaveLength(1)
  })

  it('has ONE chart-link list: exactly the five L4 tables, each FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE', () => {
    const arrays = CODE.match(/\bchart_links text\[\] := ARRAY\[([\s\S]*?)\];/g) ?? []
    expect(arrays).toHaveLength(1)
    const first = arrays[0]
    if (first === undefined) throw new Error('Expected the asserted single chart-link list')
    expect([...first.matchAll(/'([a-z_]+\|[a-z_]+)'/g)].map(m => (m[1] ?? '').split('|'))).toEqual(CHART_LINKS)
    expect(CODE).toContain("chart_def constant text := 'FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE'")
  })

  it('keeps the out-of-scope links out of the executable SQL', () => {
    for (const t of OUT_OF_SCOPE) expect(CODE).not.toMatch(new RegExp(`\\b${t}\\b`))
    expect(SQL).toContain('NOT DONE HERE')
  })

  it('creates NO database object (no view/function/table/index), writes no data, grants nothing, no transaction control', () => {
    expect(CODE).not.toMatch(/\bCREATE\s+(OR\s+REPLACE\s+)?(VIEW|FUNCTION|TABLE|INDEX|TRIGGER|SCHEMA|EXTENSION)\b/i)
    expect(CODE).not.toMatch(/security_invoker|COMMENT ON/)
    expect(CODE).not.toMatch(/\b(INSERT INTO|DELETE FROM|TRUNCATE|GRANT|REVOKE)\b/i)
    expect(CODE).not.toMatch(/\bUPDATE\s+\w+\s+SET\b/i)
    expect(CODE).not.toMatch(/\bDROP (TABLE|INDEX|COLUMN|VIEW|SCHEMA|TRIGGER|FUNCTION)\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/SET NULL|ON DELETE (RESTRICT|NO ACTION)/i)
    expect(CODE.match(/DROP CONSTRAINT/g)).toHaveLength(1)
    expect(CODE.match(/ADD CONSTRAINT/g)).toHaveLength(1)
    expect(CODE).not.toContain('DROP CONSTRAINT IF EXISTS') // each drop is guarded one by one, never blanket IF EXISTS
    expect(CODE.indexOf('ADD CONSTRAINT')).toBeLessThan(CODE.indexOf('DROP CONSTRAINT')) // links added before cascades dropped
  })

  it('starts with the transaction-local 5s lock_timeout and enforces the active-run guard', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE).toContain('$runs$')
    expect(CODE).toContain("r.state NOT IN ('completed', 'failed', 'stopped')")
    expect(CODE).toContain('active build run(s)')
    for (const a of ['ka_sangam', 'ka_kala_darshana', 'ka_vighnakara', 'ka_bhavishya_lekha', 'ph_nimitta', 'ph_pramana',
      'ph_sodhana', 'ph_suddha_sodhana', 'ph_sankrama']) expect(CODE).toContain(`'${a}'`)
  })

  it('guards table/column existence, exact constraint definitions and the chart_id preconditions (STOP, never invent)', () => {
    for (const n of ['does not exist', 'is not an ordinary table', 'pg_get_constraintdef', 'ON DELETE CASCADE',
      'is not the constraint this migration was written against', 'is already absent', 'has no chart_id column',
      'will not invent a derivation', 'chart_id is nullable', 'has no charts row; report, do not backfill',
      'is not the expected chart link']) expect(CODE).toContain(n)
    expect(CODE).toContain("regexp_replace(pg_get_constraintdef(c.oid), ' public\\.', ' ', 'g')")
  })

  it('post-checks: none left, no cascading FK left, each chart link present+validated+CASCADE, FK count delta exact', () => {
    for (const n of ['still exists on public', 'a cascading foreign key from', 'is missing, not validated, not ON DELETE CASCADE',
      'c.convalidated AND c.confdeltype', 'something else changed', 'fk_before - dropped + added']) expect(CODE).toContain(n)
  })

  it('ships the detector as plain read-only SQL + a read-only runner, never build-blocking', () => {
    expect(DET_CODE).not.toMatch(/\b(INSERT|UPDATE|DELETE|TRUNCATE|CREATE|ALTER|DROP|GRANT|REVOKE)\b/i)
    expect(DET_CODE.split(';').filter(s => s.trim().length > 0)).toHaveLength(2)
    for (const [con] of REFS) expect(DET_CODE.split(`'${con}'`).length - 1).toBeGreaterThanOrEqual(2)
    expect(DET_PY).toContain('conn.read_only = True')
    expect(DET_PY).toContain('EXPECTED_REFERENCES = 7')
    expect(DET_PY.toLowerCase()).toContain('never build-blocking')
  })

  it('states the header facts: design choice, writer effect, orphans today, trigger scan, chart deletion, detector, locks, not-done', () => {
    for (const n of ['HELD', 'AFTER S-L1', "on SS's review", 'DESIGN CHOICE: DROP', 'DEFERRABLE INITIALLY DEFERRED does not help',
      'EFFECT ON THE EXISTING WRITERS', 'ORPHANS TODAY', '0 on all seven references', 'TRIGGER SCAN', 'BLIND SPOTS',
      'SERVING EFFECT AT APPLY', 'CHART DELETION', 'PRIVACY regression', 'charts/[id]/route.ts:87-107', 'OWNERSHIP link',
      'THE DETECTOR (no DB object; read-only; REPORTED, NEVER BUILD-BLOCKING)', 'LOCK-WAIT RISK', 'ACTIVE RUNS (ENFORCED',
      'NOT DONE HERE', 'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', 'Q-L4-03', 'F-3', 'migration 363', 'migration 680',
      'PR #3019', '222 foreign keys']) expect(FLAT).toContain(n)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4))
    expect(n).toBeGreaterThanOrEqual(1200)
    expect(n).toBeLessThanOrEqual(1299)
    expect(fs.readdirSync(MIG).filter(f => /^1260_/.test(f) && f !== FILE)).toEqual([])
  })
})
