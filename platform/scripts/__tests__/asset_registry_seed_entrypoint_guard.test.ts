/**
 * Entrypoint-guard tests for `platform/scripts/seed/asset_registry_seed.ts`
 * (Nirmāṇa WORK_QUEUE M0-T15; the LIVE member of the defect class ruling D-9 elevated to
 * binding precedent, sibling of M0-T11 / finding F-2 in `scripts/migrate.ts`).
 *
 * THE DEFECT THESE TESTS EXIST TO CATCH. asset_registry_seed.ts used to gate its own `main()`
 * call on an environment sentinel:
 *
 *     if (process.env.NODE_ENV !== 'test') { main().catch(...) }
 *
 * That answers "is NODE_ENV set to the string 'test'?", which is NOT the question. The question
 * is "was this module the process entrypoint, or did something merely import it?".
 *
 * This instance is worse than migrate.ts's. The module deliberately EXPORTS `ASSETS` (it is the
 * authoritative in-repo asset catalogue), two test files already import that export
 * (`scripts/__tests__/catalog_reconciliation.test.ts`, `tests/unit/build/w2_weights_acyclicity.test.ts`),
 * so the import path is real rather than hypothetical — and `main()` executes
 * `INSERT INTO asset_registry … ON CONFLICT DO UPDATE` plus the same upsert against
 * `asset_coefficients`. An import from any shell with `DATABASE_URL` exported and `NODE_ENV`
 * unset — which is every ordinary developer and agent shell — silently rewrote control-plane
 * registry rows as an import side effect.
 *
 * WHY A SUBPROCESS. The bug lives in module top-level evaluation, so it can only be observed by
 * evaluating the module in a fresh process. An in-process `import()` from vitest inherits
 * vitest's own `NODE_ENV=test` and therefore cannot see the defect at all — a test that cannot
 * fail is not a guard (CLAUDE.md §N.8).
 *
 * WHY THIS IS SAFE. Every child process is given an explicitly-constructed environment whose
 * `DATABASE_URL` points at a port nothing listens on. `process.env` is deliberately NOT spread
 * into it: a real `DATABASE_URL` exported in a developer or CI shell must never reach a process
 * this file may deliberately cause to run the seeder. No test here ever reaches a real database,
 * in either direction, and nothing is ever written to `asset_registry`.
 *
 * THE OBSERVABLE IS NOT THE CONNECTION. `main()`'s first action after reading `DATABASE_URL` is
 * `validateFormulas()`, which logs `Validating formulas...` BEFORE any `pg.Client` exists. That
 * line is therefore the earliest and most reliable answer to "did main() run?", and it needs no
 * database anywhere in reach.
 *
 * It is also, today, the ONLY answer available: the seeder currently aborts inside
 * `validateFormulas()` on `bg_cohort` ("Unknown variables in formula \"COHORT_SIZE\"") and so
 * never reaches `client.connect()` at all. That abort is a PRE-EXISTING defect unrelated to this
 * guard (introduced 2026-07-29, PR #887) — reported separately, deliberately not fixed here. It
 * means these tests cannot assert ECONNREFUSED without asserting the bug, so they assert the
 * log marker plus the exit status instead, both of which stay correct whether or not the formula
 * defect is later fixed.
 */
import { describe, it, expect } from 'vitest'
import { spawnSync, type SpawnSyncReturns } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'
import { pathToFileURL } from 'url'
// In-process import of the module under test — legitimate, and the same shape the two existing
// importers use. It is only safe BECAUSE of the guard this file exists to prove.
import { isDirectEntrypoint } from '../seed/asset_registry_seed'

const PLATFORM_DIR = path.resolve(__dirname, '../..')
const TSX = path.join(PLATFORM_DIR, 'node_modules', '.bin', 'tsx')
const SEED_TS = path.join(PLATFORM_DIR, 'scripts', 'seed', 'asset_registry_seed.ts')

/**
 * Deliberately unreachable. Port 1 is privileged and reserved; nothing listens on it in any
 * environment this suite runs in, so `client.connect()` fails immediately with ECONNREFUSED.
 * It is supplied so that `main()` gets PAST its `if (!dbUrl) throw` line — otherwise the two
 * directions of the guard would be indistinguishable from a missing-env failure.
 */
const UNREACHABLE_DATABASE_URL = 'postgresql://nobody:nobody@127.0.0.1:1/nirmana_m0t15_nodb'

/** Logged by `main()` before any `pg.Client` is constructed — the earliest proof main() ran. */
const MAIN_RAN_MARKER = /Validating formulas\.\.\./

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

describe.skipIf(!tsxPresent)('asset_registry_seed.ts entrypoint guard (M0-T15)', () => {
  it('A — importing ASSETS with NODE_ENV unset does NOT run the seeder', () => {
    // A real named import from a real module file — the exact shape the two existing importers
    // use. Deliberately NOT `tsx -e`: eval'd code is loaded through tsx's CJS-interop path and
    // does not reproduce the hazard faithfully.
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'seed-entrypoint-'))
    const harness = path.join(dir, 'harness.ts')
    fs.writeFileSync(
      harness,
      `import { ASSETS } from ${JSON.stringify(SEED_TS)}\n` +
        `console.log('IMPORTED_OK', Array.isArray(ASSETS), ASSETS.length)\n`,
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

    // The import itself must succeed — the module is legitimately importable for ASSETS.
    expect(combined).toMatch(/IMPORTED_OK true \d+/)
    // ...and must have had NO side effect. main() logs this before it builds a Client, so it
    // catches an entered main() even with no database anywhere in reach.
    expect(combined).not.toMatch(MAIN_RAN_MARKER)
    // Belt and braces: neither the seeder's own failure path nor any connection attempt.
    expect(combined).not.toMatch(/Seed failed/)
    expect(combined).not.toMatch(/ECONNREFUSED/)
    // main()'s failure path calls process.exit(1). A clean 0 proves nothing hijacked the exit.
    expect(status).toBe(0)
  }, 180_000)

  it('B — running the module directly still enters main()', () => {
    const r = runTsx(['scripts/seed/asset_registry_seed.ts'])
    const combined = output(r)

    // If the entrypoint check were wrong in the other direction (guard too strict, the
    // documented `npx tsx scripts/seed/asset_registry_seed.ts` operator run silently no-ops),
    // this process would exit 0 having printed nothing and both assertions would fail.
    expect(combined).toMatch(MAIN_RAN_MARKER)
    expect(r.status).not.toBe(0)
  }, 180_000)
})

/**
 * Runs whether or not tsx is installed — it needs no subprocess.
 *
 * Documents, as a standing assertion rather than a one-off observation, what happens to the two
 * pre-existing in-process importers (`scripts/__tests__/catalog_reconciliation.test.ts` and
 * `tests/unit/build/w2_weights_acyclicity.test.ts`) under this guard: `process.argv[1]` inside a
 * vitest worker is vitest's own entry, never the seed module, so the guard answers false and
 * `main()` does not run. That was ALSO the outcome before the fix — but for the wrong reason
 * (vitest happening to set `NODE_ENV=test`). The importers are unaffected either way; what
 * changed is that their safety no longer depends on an environment variable.
 */
describe('asset_registry_seed.ts entrypoint guard — in-process importers', () => {
  it('C — under vitest the seed module is never the entrypoint', () => {
    expect(process.argv[1] ?? '').not.toMatch(/asset_registry_seed/)
    expect(isDirectEntrypoint(pathToFileURL(SEED_TS).href, process.argv[1])).toBe(false)
  })

  it('C2 — the detector still answers true for a genuine direct run, and false on bad input', () => {
    // Guards against a "safe" implementation that just returns false unconditionally.
    expect(isDirectEntrypoint(pathToFileURL(SEED_TS).href, SEED_TS)).toBe(true)
    expect(isDirectEntrypoint(pathToFileURL(SEED_TS).href, undefined)).toBe(false)
    expect(isDirectEntrypoint('not-a-url', SEED_TS)).toBe(false)
  })
})
