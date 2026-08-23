/**
 * Entrypoint-guard tests for `platform/scripts/migrate.ts` (Nirmāṇa finding F-2, WORK_QUEUE
 * M0-T11).
 *
 * THE DEFECT THESE TESTS EXIST TO CATCH. migrate.ts used to gate its own `main()` call on an
 * environment sentinel:
 *
 *     if (process.env.NODE_ENV !== 'test') { main() }
 *
 * That answers "is NODE_ENV set to the string 'test'?", which is NOT the question. The question
 * is "was this module the process entrypoint, or did something merely import it?". Any shell
 * with `NODE_ENV` unset — which is every ordinary developer and agent shell — that imports a
 * pure helper out of this module (`sqlIdentityOf`, `normalizeSqlForIdentity`,
 * `collectMigrationFiles`; `migration_renumber_disclosed.json` documents exactly such an import
 * as the supported way to compute a sql_identity) runs the entire migrator as an import side
 * effect. Combined with an exported `DATABASE_URL` that points at production, an `import`
 * applies every unapplied migration.
 *
 * WHY A SUBPROCESS. The bug lives in module top-level evaluation, so it can only be observed by
 * evaluating the module in a fresh process. An in-process `import()` from vitest inherits
 * vitest's own `NODE_ENV=test` and therefore cannot see the defect at all — a test that cannot
 * fail is not a guard (CLAUDE.md §N.8).
 *
 * WHY THIS IS SAFE. Every child process is given an explicitly-constructed environment whose
 * `DATABASE_URL` points at a port nothing listens on. `process.env` is deliberately NOT spread
 * into it: a real `DATABASE_URL` exported in a developer or CI shell must never reach a process
 * this file may deliberately cause to run the migrator. The connection attempt failing with
 * ECONNREFUSED is precisely the observable that tells us whether `main()` was entered — no
 * database is ever reached, in either direction.
 */
import { describe, it, expect } from 'vitest'
import { spawnSync, type SpawnSyncReturns } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'

const PLATFORM_DIR = path.resolve(__dirname, '../..')
const TSX = path.join(PLATFORM_DIR, 'node_modules', '.bin', 'tsx')
const MIGRATE_TS = path.join(PLATFORM_DIR, 'scripts', 'migrate.ts')

/**
 * Deliberately unreachable. Port 1 is privileged and reserved; nothing listens on it in any
 * environment this suite runs in, so `pool.connect()` fails immediately with ECONNREFUSED.
 * That failure is the *evidence* these tests read — it is how we observe whether `main()` ran
 * without ever pointing the migrator at a real database.
 */
const UNREACHABLE_DATABASE_URL = 'postgresql://nobody:nobody@127.0.0.1:1/nirmana_m0t11_nodb'

function runTsx(args: string[]): SpawnSyncReturns<string> {
  // Constructed from scratch, NOT spread from process.env — see the file docstring. NODE_ENV is
  // intentionally absent, reproducing the ordinary shell in which the hazard is live.
  const env: NodeJS.ProcessEnv = {
    PATH: process.env.PATH ?? '',
    HOME: process.env.HOME ?? '',
    DATABASE_URL: UNREACHABLE_DATABASE_URL,
  }
  return spawnSync(TSX, args, {
    cwd: PLATFORM_DIR,
    env,
    encoding: 'utf8',
    timeout: 180_000,
  })
}

function output(r: SpawnSyncReturns<string>): string {
  return `${r.stdout ?? ''}${r.stderr ?? ''}`
}

// tsx is a devDependency; if node_modules is not installed there is nothing to assert about.
const tsxPresent = fs.existsSync(TSX)

describe.skipIf(!tsxPresent)('migrate.ts entrypoint guard (F-2)', () => {
  it('A — importing the module with NODE_ENV unset does NOT run the migrator', () => {
    // A real named import from a real module file — the exact shape
    // `scripts/ci/migration_renumber_disclosed.json` documents as the supported way to compute
    // a sql_identity, and the exact shape KĀRAKA M0-T4 tripped. Deliberately NOT `tsx -e`:
    // eval'd code is loaded through tsx's CJS-interop path and does not reproduce the hazard
    // faithfully.
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'migrate-entrypoint-'))
    const harness = path.join(dir, 'harness.ts')
    fs.writeFileSync(
      harness,
      `import { sqlIdentityOf } from ${JSON.stringify(MIGRATE_TS)}\n` +
        `console.log('IMPORTED_OK', typeof sqlIdentityOf)\n`,
      'utf8'
    )

    let combined: string
    let status: number | null
    try {
      const r = runTsx([harness])
      combined = output(r)
      status = r.status
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }

    // The import itself must succeed — the module is legitimately importable for its helpers.
    expect(combined).toContain('IMPORTED_OK function')
    // ...and must have had NO database side effect. ECONNREFUSED here means main() ran.
    expect(combined).not.toMatch(/ECONNREFUSED/)
    expect(combined).not.toMatch(/Migration failed/)
    expect(status).toBe(0)
  }, 180_000)

  it('B — running the module directly still enters main() and attempts to connect', () => {
    const r = runTsx(['scripts/migrate.ts', '--dry-run'])
    const combined = output(r)

    // Reaching pool.connect() is the proof main() was entered. If the entrypoint check were
    // wrong in the other direction (guard too strict, deploy silently no-ops), this process
    // would exit 0 having done nothing and this assertion would fail.
    expect(combined).toMatch(/ECONNREFUSED/)
    expect(r.status).not.toBe(0)
  }, 180_000)
})
