/**
 * Suvarna / migration numbers 1272 and 1273 (data_plane_builder privileges) -- HELD owner-path executor.
 * The two SQL files carry the migration numbers as history/audit text but are applied ONLY by the gated owner-path
 * executor (00_ARCHITECTURE/briefs/suvarna/exec/dp_builder_privileges/dp_builder_privileges_exec.py). migrate.ts must never
 * discover or run them: it reads exactly platform/migrations and platform/supabase/migrations. This test pins that.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { collectMigrationFiles } from '../../../scripts/migrate'

const PLATFORM = path.resolve(__dirname, '../../..')
const REPO = path.resolve(PLATFORM, '..')
const EXEC_DIR = path.join(REPO, '00_ARCHITECTURE/briefs/suvarna/exec/dp_builder_privileges')
const SQL_FILES = [
  '1272_bind_l2_exact_inputs_builder_reads_shadows.sql',
  '1273_builder_execute_bodha_identity_functions.sql',
]
// the same directory list migrate.ts main() builds (scriptDir/../migrations and scriptDir/../supabase/migrations)
const MIGRATE_DIRS = [path.join(PLATFORM, 'migrations'), path.join(PLATFORM, 'supabase/migrations')]

describe('migrations 1272 / 1273 are owner-path history files, never discovered by migrate.ts', () => {
  it('the SQL files exist next to the executor, outside every migrate.ts directory', () => {
    for (const f of SQL_FILES) {
      expect(fs.existsSync(path.join(EXEC_DIR, f)), f).toBe(true)
      for (const d of MIGRATE_DIRS) {
        expect(path.join(EXEC_DIR, f).startsWith(d + path.sep), `${f} under ${d}`).toBe(false)
        expect(fs.existsSync(path.join(d, f)), `${f} present in ${d}`).toBe(false)
      }
    }
  })

  it('collectMigrationFiles over the real migrate.ts directories lists neither file nor any 1272/1273-numbered file', () => {
    const listed = collectMigrationFiles(MIGRATE_DIRS).map(m => m.name)
    expect(listed.length).toBeGreaterThan(100)
    for (const f of SQL_FILES) expect(listed).not.toContain(f)
    expect(listed.filter(n => /^(1272|1273)_/.test(n))).toEqual([])
  })

  it('discovery is directory-based: pointing it at the executor folder would find them (so the placement, not luck, is what protects)', () => {
    const listed = collectMigrationFiles([EXEC_DIR]).map(m => m.name)
    expect(listed).toEqual(SQL_FILES)
  })

  it('both files say in their own header that migrate.ts never runs them', () => {
    for (const f of SQL_FILES) {
      expect(fs.readFileSync(path.join(EXEC_DIR, f), 'utf8')).toContain('NEVER RUN BY migrate.ts')
    }
  })

  it('migrate.ts main() still builds exactly the two directories this test models', () => {
    const src = fs.readFileSync(path.join(PLATFORM, 'scripts/migrate.ts'), 'utf8')
    const m = src.match(/const dirs = \[([\s\S]*?)\]/)
    expect(m).not.toBeNull()
    const body = m![1]
    expect([...body.matchAll(/'([^']+)'/g)].map(x => x[1])).toEqual(['../migrations', '../supabase/migrations'])
  })
})
