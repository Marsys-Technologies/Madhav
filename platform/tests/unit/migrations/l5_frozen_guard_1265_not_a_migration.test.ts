/**
 * Suvarna / 1265 (SS rulings N-104, N-107, N-108) — the owner-path SQL must NEVER be discoverable by the routine migration runner.
 * The SQL (capture of the live-only builder guard, the frozen-history guards, the rollback) lives in the executor package
 * 00_ARCHITECTURE/briefs/suvarna/exec/l5_frozen_guard_1265/sql/ and is applied only by l5_frozen_guard_exec.py (GATE_V2, plan hash, dry run, apply).
 * Why: it creates functions in schema public, which the routine role cannot do; if migrate.ts could see it, the next deploy's migrate job would fail on it.
 * The behaviour proof (a disposable PostgreSQL with production's roles; executor route; mutants) is python-sidecar/tests/test_l5_frozen_guard_1265_*.py.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const PLATFORM = path.resolve(__dirname, '../../..')
const REPO = path.resolve(PLATFORM, '..')
const PKG = path.join(REPO, '00_ARCHITECTURE/briefs/suvarna/exec/l5_frozen_guard_1265')
const MIGRATE_TS = fs.readFileSync(path.join(PLATFORM, 'scripts/migrate.ts'), 'utf8')

// migrate.ts main(): dirs = [../migrations, ../supabase/migrations]; discovery = *.sql files directly inside them
const DIRS = [path.join(PLATFORM, 'migrations'), path.join(PLATFORM, 'supabase/migrations')]
const discovered = DIRS.flatMap(d => fs.readdirSync(d).filter(f => f.endsWith('.sql')).map(f => ({ dir: d, file: f })))

describe('1265 owner-path SQL is not a migration', () => {
  it('migrate.ts still discovers exactly the two migration directories, non-recursively', () => {
    expect(MIGRATE_TS).toContain("path.resolve(scriptDir, '../migrations')")
    expect(MIGRATE_TS).toContain("path.resolve(scriptDir, '../supabase/migrations')")
    expect(MIGRATE_TS.match(/fs\.readdirSync\(dir\)/g)).toHaveLength(1)
  })

  it('the package SQL files exist, in the package path, and under no migrations directory', () => {
    for (const f of ['1265_l5_frozen_row_guards.sql', '1265_l5_frozen_row_guards.ROLLBACK.sql', 'verify_before_apply.sql', 'verify_after_apply.sql']) {
      const p = path.join(PKG, 'sql', f)
      expect(fs.existsSync(p), f).toBe(true)
      expect(p.includes(`${path.sep}migrations${path.sep}`)).toBe(false)
    }
  })

  it('migrate.ts discovery lists no 1265 file and no file carrying the guard objects', () => {
    expect(discovered.filter(x => /^1265[_.]/.test(x.file))).toEqual([])
    const bad = discovered.filter(x => /mimamsa_predictions_frozen_row_guard|l5_frozen_chart_cascade_authorizes|l5_frozen_withdrawal_authorizes/.test(
      fs.readFileSync(path.join(x.dir, x.file), 'utf8')))
    expect(bad).toEqual([])
  })

  it('the package SQL, if copied into a migrations directory by mistake, would be a protected-class file the routine runner cannot apply (guard the shape)', () => {
    const sql = fs.readFileSync(path.join(PKG, 'sql/1265_l5_frozen_row_guards.sql'), 'utf8')
    expect(sql).toMatch(/CREATE OR REPLACE FUNCTION public\./)
    expect(sql).toContain('OWNER-PATH SQL, NOT A MIGRATION')
    expect(sql.replace(/\n-- /g, ' ')).toContain('must never be placed under platform/migrations')
  })

  it('the script never issues a GRANT and never touches asset_registry', () => {
    const code = fs.readFileSync(path.join(PKG, 'sql/1265_l5_frozen_row_guards.sql'), 'utf8').split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
    expect(code).not.toMatch(/\bGRANT\b/)
    expect(code).not.toMatch(/asset_registry/)
  })

  it('the executor and the plan are in the package, and the plan names the pinned GATE_V2 files', () => {
    for (const f of ['l5_frozen_guard_exec.py', 'make_plan.py', 'plan.txt']) expect(fs.existsSync(path.join(PKG, f)), f).toBe(true)
    const plan = fs.readFileSync(path.join(PKG, 'plan.txt'), 'utf8')
    expect(plan).toContain('NOT a migration')
    expect(plan).toContain('prerun_gate.py sha256 01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e')
  })
})
