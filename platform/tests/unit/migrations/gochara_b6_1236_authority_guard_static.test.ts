/**
 * Pravāha B6.0 — STATIC contract of migration 1236, and the writer allow-list gate: no code path other than the operator flip script
 * writes kala_gochara_authority (the serving pointer). Live proof: tests/integration/gochara_b6_1236_authority_guard.db.test.ts.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const ROOT = path.resolve(__dirname, '../../../..')
const FILE = '1236_gochara_authority_refuses_governed_generation.sql'
const SQL = fs.readFileSync(path.join(ROOT, 'platform/migrations', FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1236 — static contract', () => {
  it('adds exactly one CHECK, with the governed pattern of 1153, creating no function or trigger', () => {
    expect(CODE.match(/ALTER TABLE/g) ?? []).toHaveLength(1)
    expect(CODE).toContain("CHECK (authoritative_generation !~ '^([5-9]|[1-9][0-9]+)\\.[0-9]+$')")
    const g1153 = fs.readFileSync(path.join(ROOT, 'platform/migrations/1153_gochara_sky_event_substrate.sql'), 'utf8')
    expect(g1153).toContain("g ~ '^([5-9]|[1-9][0-9]+)\\.[0-9]+$'")                          // the SAME pattern as ka_gochara_generation_governed
    expect(CODE).not.toMatch(/\bCREATE\b|\bDROP\b|\bGRANT\b|\bREVOKE\b|\bDELETE\b|\bUPDATE\b|\bTRIGGER\b/)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })
  it('refuses to apply over an existing governed row, and over a replay; verifies the constraint is validated', () => {
    for (const t of ['kala_gochara_authority_missing', 'migration_1236_already_applied', 'a governed generation is already authoritative', 'convalidated'])
      expect(SQL).toContain(t)
  })
  it('is a ROUTINE migration (no CREATE on schema public is needed) and unique in the reserved block', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4)); expect(n).toBeGreaterThanOrEqual(1230); expect(n).toBeLessThanOrEqual(1249)
    expect(fs.readdirSync(path.join(ROOT, 'platform/migrations')).filter(f => /^1236_/.test(f) && f !== FILE)).toEqual([])
  })
})

// The writer allow-list: the serving pointer is written ONLY by operator-run flip/rollback scripts (five today, listed below; test fixtures excepted). NOTE: flip_authority.py takes the generation as an argument — before 1236 nothing stopped it naming '5.0'. A new writer anywhere is a
// governance event, not a drive-by change — this gate fails until the allow-list is amended in review.
describe('kala_gochara_authority writers — allow-list gate', () => {
  const ALLOWED = new Set([
    'platform/python-sidecar/scripts/kala_gochara_cutover/step08_flip.py',                       // the operator flip (D-FLIP is the native's)
    'platform/scripts/gochara/flip_authority.py',                                                // chart-agnostic operator flip tooling (MR-08)
    'platform/scripts/gochara/rollback_authority.py',                                            // its rollback (DELETE the row)
    'platform/scripts/dispatch_utkarsha_w63_authority_flip_abhinandan.py',                       // one-off W6.3 flip (historical, operator-run)
    'platform/scripts/dispatch_utkarsha_w63_rollback_abhinandan.py',                             // its rollback
  ])
  function walk(dir: string, out: string[]): void {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      if (['node_modules', '.git', '.next', 'dist', '__pycache__', '.venv'].includes(e.name)) continue
      const p = path.join(dir, e.name)
      if (e.isDirectory()) walk(p, out)
      else if (/\.(py|ts|tsx|js|mjs)$/.test(e.name)) out.push(p)
    }
  }
  it('no source file outside the operator flip/rollback scripts INSERTs or UPDATEs the authority table', () => {
    const files: string[] = []
    for (const d of ['platform/python-sidecar', 'platform/src', 'platform/scripts', 'platform-mcp/src']) if (fs.existsSync(path.join(ROOT, d))) walk(path.join(ROOT, d), files)
    const writers = files.filter(f => {
      const rel = path.relative(ROOT, f).split(path.sep).join('/')
      if (rel.includes('/tests/') || /\.test\.(ts|tsx|js)$/.test(rel) || /\/test_[^/]*\.py$/.test(rel)) return false        // fixtures may write their own copy
      if (rel.includes('/evidence/')) return false
      const src = fs.readFileSync(f, 'utf8')
      return /(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(public\.)?kala_gochara_authority\b/i.test(src)
    }).map(f => path.relative(ROOT, f).split(path.sep).join('/'))
    const unexpected = writers.filter(w => !ALLOWED.has(w))
    expect(unexpected, `unexpected writers of kala_gochara_authority: ${unexpected.join(', ')}`).toEqual([])
  })
})
