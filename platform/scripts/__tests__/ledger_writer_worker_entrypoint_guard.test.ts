/**
 * Entrypoint-guard tests for `platform/scripts/pariprashna/ledger_writer_worker.ts`
 * (Nirmāṇa WORK_QUEUE M0-T60, Standing Queue SQ-24 — the third member of the defect class
 * ruling D-9 elevated to binding precedent; siblings M0-T11 / finding F-2 in `scripts/migrate.ts`
 * and M0-T15 in `scripts/seed/asset_registry_seed.ts`).
 *
 * THE DEFECT THESE TESTS EXIST TO CATCH. The worker used to gate its own `main()` call on an
 * environment sentinel:
 *
 *     // Guard: only run when invoked directly, so a test may import this file.
 *     if (process.env.NODE_ENV !== 'test') { void main() }
 *
 * That answers "is NODE_ENV set to the string 'test'?", which is not the question. The question is
 * "was this module the process entrypoint, or did something merely import it?" — and here the
 * sentinel answered wrongly in BOTH directions, measured before the repair:
 *
 *   · IMPORT with NODE_ENV unset  → exit 1, `ARM3_CONNECT_FAILED` — `main()` ran as an import
 *     side effect. `main()` opens a pool on `LEDGER_WRITER_DATABASE_URL`, the sole
 *     `role_ledger_write` credential, drains `pariprashna_ledger_outbox` into
 *     `brahma_mimamsa_prediction_ledger`, and calls `process.exit()`. So the import mutated the
 *     prediction ledger AND hijacked the exit of whatever imported it. Every ordinary developer
 *     and agent shell has NODE_ENV unset.
 *   · DIRECT RUN with NODE_ENV=test → exit 0, zero bytes of output — the documented operator
 *     invocation silently drained nothing, and a scheduler would have recorded a success.
 *
 * WHY THIS IS NOT THE `IMPORT_ONLY` CONTRACT THE CI GATES USE. `scripts/ci/dispatch_gate.ts` and
 * `scripts/ci/verify_migrations_deployed.ts` were repaired the other way (M0-T50 / ruling D-49,
 * documented at `scripts/audit/A3_env_matrix.md` Addendum A3.4) because a GATE's hazard is FAILING
 * to run, so its safe default must be RUN. A mutating worker's hazard is RUNNING, so its safe
 * default is DO NOT RUN. Opposite hazards, opposite defaults — A3.4 operator rule 5.
 *
 * WHY A SUBPROCESS. The bug lives in module top-level evaluation, so it can only be observed by
 * evaluating the module in a fresh process. An in-process `import()` from vitest inherits vitest's
 * own `NODE_ENV=test` and therefore cannot see the defect at all — a test that cannot fail is not
 * a guard (CLAUDE.md §N.8).
 *
 * WHY THIS IS SAFE. Every child process is given an explicitly-constructed environment.
 * `process.env` is deliberately NOT spread into it, so a real `LEDGER_WRITER_DATABASE_URL`
 * exported in a developer or CI shell can never reach a process this file deliberately causes to
 * run the worker. The credential supplied points at port 1 — privileged, reserved, and listened on
 * by nothing — so `pool.query('SELECT current_user')` fails with ECONNREFUSED before
 * `drainOutbox` is ever reached. No test here touches a real database in either direction, and
 * nothing is ever written to `brahma_mimamsa_prediction_ledger` or `pariprashna_ledger_outbox`.
 *
 * THE OBSERVABLE. `ARM3_CONNECT_FAILED` is printed by `main()` on the very first query after the
 * pool is constructed, and it is the earliest marker that survives having no database in reach.
 * `ARM3_` alone is the negative assertion, so an entered `main()` is caught whichever of its two
 * early failure paths it takes.
 */
import { describe, it, expect } from 'vitest'
import { spawnSync, type SpawnSyncReturns } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'
import { pathToFileURL } from 'url'
// In-process import of the module under test. It is only safe BECAUSE of the guard this file
// exists to prove — before the repair this line would have run the ledger writer inside the
// vitest worker in any environment that exported the credential.
import { isDirectEntrypoint } from '../pariprashna/ledger_writer_worker'

const PLATFORM_DIR = path.resolve(__dirname, '../..')
const TSX = path.join(PLATFORM_DIR, 'node_modules', '.bin', 'tsx')
const WORKER_REL = path.join('scripts', 'pariprashna', 'ledger_writer_worker.ts')
const WORKER_TS = path.join(PLATFORM_DIR, WORKER_REL)

/**
 * Deliberately unreachable. Port 1 is privileged and reserved; nothing listens on it in any
 * environment this suite runs in. It is supplied so that `main()` gets PAST its
 * `if (!url) { ARM3_NO_CREDENTIAL; exit(1) }` line — otherwise the two directions of the guard
 * would be indistinguishable from a missing-credential failure.
 */
const UNREACHABLE_URL = 'postgresql://nobody:nobody@127.0.0.1:1/nirmana_m0t60_nodb'

/** Printed by `main()` on its first query — the earliest proof main() ran with no DB in reach. */
const MAIN_RAN_MARKER = /ARM3_CONNECT_FAILED/
/** Any arm-3 diagnostic at all. Catches an entered `main()` via either early failure path. */
const ANY_MAIN_MARKER = /ARM3_/

function runTsx(args: string[], extraEnv: NodeJS.ProcessEnv = {}): SpawnSyncReturns<string> {
  // Constructed from scratch, NOT spread from process.env — see the file docstring.
  const env: NodeJS.ProcessEnv = {
    PATH: process.env.PATH ?? '',
    HOME: process.env.HOME ?? '',
    LEDGER_WRITER_DATABASE_URL: UNREACHABLE_URL,
    ...extraEnv,
  }
  return spawnSync(TSX, args, { cwd: PLATFORM_DIR, env, encoding: 'utf8', timeout: 180_000 })
}

function output(r: SpawnSyncReturns<string>): string {
  return `${r.stdout ?? ''}${r.stderr ?? ''}`
}

/** A throwaway module whose only content is a side-effect import of the worker. */
function withImportHarness(fn: (harnessPath: string) => void): void {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'arm3-entrypoint-'))
  try {
    const harness = path.join(dir, 'harness.ts')
    fs.writeFileSync(
      harness,
      `import ${JSON.stringify(WORKER_TS)}\nconsole.log('IMPORT_RETURNED_OK')\n`,
      'utf8',
    )
    fn(harness)
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
}

// tsx is a devDependency; if node_modules is not installed there is nothing to assert about.
const tsxPresent = fs.existsSync(TSX)

describe.skipIf(!tsxPresent)('ledger_writer_worker.ts entrypoint guard (M0-T60)', () => {
  it('A — importing the worker with NODE_ENV unset does NOT run it', () => {
    // This is the direction that was live before the repair: exit 1, ARM3_CONNECT_FAILED.
    withImportHarness((harness) => {
      const r = runTsx([harness])
      const combined = output(r)

      expect(combined).toMatch(/IMPORT_RETURNED_OK/)
      expect(combined).not.toMatch(ANY_MAIN_MARKER)
      // `main()` exits 1 on its failure paths; a clean 0 proves nothing hijacked the exit.
      expect(r.status).toBe(0)
    })
  }, 180_000)

  it('B — importing the worker with NODE_ENV=test also does NOT run it', () => {
    // Passed under the old guard too, for the wrong reason. Kept so the pair is symmetric and a
    // future polarity flip cannot hide in the half nobody asserts.
    withImportHarness((harness) => {
      const r = runTsx([harness], { NODE_ENV: 'test' })
      const combined = output(r)

      expect(combined).toMatch(/IMPORT_RETURNED_OK/)
      expect(combined).not.toMatch(ANY_MAIN_MARKER)
      expect(r.status).toBe(0)
    })
  }, 180_000)

  it('C — CAN-FAIL: running the worker directly under NODE_ENV=test still enters main()', () => {
    // The half the old guard broke: it exited 0 having printed nothing. Reverting to the
    // `NODE_ENV !== 'test'` form fails this test, and only this test.
    const r = runTsx([WORKER_REL, '--once'], { NODE_ENV: 'test' })
    const combined = output(r)

    expect(combined).toMatch(MAIN_RAN_MARKER)
    expect(r.status).toBe(1)
  }, 180_000)

  it('D — running the worker directly with NODE_ENV unset still enters main()', () => {
    const r = runTsx([WORKER_REL, '--once'])
    const combined = output(r)

    expect(combined).toMatch(MAIN_RAN_MARKER)
    expect(r.status).toBe(1)
  }, 180_000)

  it('E — a `./`-prefixed direct run is still a direct run', () => {
    // realpath/resolve normalisation, asserted rather than assumed: a spelling difference must
    // not turn the documented operator invocation into a silent no-op.
    const r = runTsx([`./${WORKER_REL}`, '--once'])
    const combined = output(r)

    expect(combined).toMatch(MAIN_RAN_MARKER)
    expect(r.status).toBe(1)
  }, 180_000)
})

/** Runs whether or not tsx is installed — it needs no subprocess. */
describe('ledger_writer_worker.ts entrypoint guard — the detector itself', () => {
  it('F — under vitest the worker module is never the entrypoint', () => {
    expect(process.argv[1] ?? '').not.toMatch(/ledger_writer_worker/)
    expect(isDirectEntrypoint(pathToFileURL(WORKER_TS).href, process.argv[1])).toBe(false)
  })

  it('G — the detector answers true for a genuine direct run, and false on bad input', () => {
    // Guards against a "safe" implementation that just returns false unconditionally, which
    // would make the worker unrunnable while every negative assertion above still passed.
    expect(isDirectEntrypoint(pathToFileURL(WORKER_TS).href, WORKER_TS)).toBe(true)
    expect(isDirectEntrypoint(pathToFileURL(WORKER_TS).href, undefined)).toBe(false)
    expect(isDirectEntrypoint('not-a-url', WORKER_TS)).toBe(false)
  })
})
