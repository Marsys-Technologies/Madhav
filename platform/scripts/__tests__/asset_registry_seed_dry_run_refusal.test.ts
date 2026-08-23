/**
 * DRY_RUN-refusal tests for `platform/scripts/seed/asset_registry_seed.ts`
 * (Nirmāṇa WORK_QUEUE M0-T19; implements ruling D-17).
 *
 * THE DEFECT THESE TESTS EXIST TO CATCH. `DRY_RUN` occurred ZERO times in the seeder, yet two
 * retired briefs document it — and pair it with production on the same command line:
 *
 *     DATABASE_URL=$PROD_DB_URL DRY_RUN=1 npx tsx scripts/seed/asset_registry_seed.ts
 *       — 99_ARCHIVE/BRIEFS_RETIRED/CLAUDECODE_BRIEF_L0_PHASE_ALPHA_v1_0.md:514 (and :637,
 *         which instructs the operator to act on what the dry run reports)
 *       — 99_ARCHIVE/BRIEFS_RETIRED/CLAUDECODE_BRIEF_COCKPIT_POLISH_ROUND_v1_0.md:257
 *
 * The flag was silently ignored, so the documented "preview" ran a full
 * `INSERT INTO asset_registry … ON CONFLICT DO UPDATE` against production. That is CLAUDE.md
 * §N.8 INVERTED — not a green with no detector, but a SAFETY MECHANISM WITH NO IMPLEMENTATION —
 * and it fails in the direction that does damage, harming the operator who is being careful
 * rather than the one making a mistake.
 *
 * D-17 authorised neither "implement dry-run" (unplanned capability; a hastily-built preview
 * that is subtly wrong would be a NEW unearned safety signal) nor "strike the doc" (retain-in-
 * place archival hygiene, and it only fixes the copies we know about). It authorised a THIRD
 * option: the seeder REFUSES. `DRY_RUN` set + dry-run not implemented ⇒ exit non-zero
 * immediately with a diagnostic saying so. A refusal at the point of danger protects the
 * operator regardless of which document sent them, including ones nobody has found.
 *
 * WHY A SUBPROCESS. The claim under test is about the PROCESS: what a real operator run does,
 * what it prints, what it exits with, and — critically — how FAR it got before refusing. An
 * in-process unit call on an exported predicate could not observe the ordering, which is half
 * the ruling. These tests also deliberately import NOTHING from the seeder: ruling D-13
 * standing-instructs every agent not to import from `asset_registry_seed.ts` (it exports
 * `ASSETS`, and its `main()` upserts the control-plane registry), and a subprocess needs no
 * import to observe anything asserted here.
 *
 * WHY THIS IS SAFE. Every child process is given an explicitly-constructed environment —
 * `process.env` is deliberately NOT spread in, so a real `DATABASE_URL` exported in a developer
 * or CI shell can never reach a process this file causes to run the seeder. The `DATABASE_URL`
 * supplied points at a port nothing listens on. No test here reaches a real database and
 * nothing is ever written to `asset_registry`.
 *
 * THE ORDERING OBSERVABLE. `main()`'s first logging action is `validateFormulas()`, which prints
 * `Validating formulas...` BEFORE any `pg.Client` is constructed. Its ABSENCE is therefore proof
 * the refusal fired earlier than any database connection could have been attempted. (The seeder
 * additionally cannot complete today: `validateFormulas()` aborts on `bg_cohort`'s
 * `COHORT_SIZE`. That is a PRE-EXISTING, UNRELATED defect pinned to R0 carry-forward and
 * deliberately not fixed here — D-17 §3, I13. The refusal must not depend on that abort, which
 * is why test D asserts the marker is REACHED on a normal run rather than asserting any
 * particular downstream failure.)
 */
import { describe, it, expect } from 'vitest'
import { spawnSync, type SpawnSyncReturns } from 'child_process'
import fs from 'fs'
import path from 'path'

const PLATFORM_DIR = path.resolve(__dirname, '../..')
const TSX = path.join(PLATFORM_DIR, 'node_modules', '.bin', 'tsx')
const SEED_REL = 'scripts/seed/asset_registry_seed.ts'

/**
 * Deliberately unreachable. Port 1 is privileged and reserved; nothing listens on it in any
 * environment this suite runs in. Supplied so that `main()` gets PAST its `if (!dbUrl) throw`
 * line on the control run, and so that a refusal failure would be visibly a refusal failure
 * rather than a missing-env failure.
 */
const UNREACHABLE_DATABASE_URL = 'postgresql://nobody:nobody@127.0.0.1:1/nirmana_m0t19_nodb'

/** Logged by `main()` before any `pg.Client` is constructed — the earliest proof main() ran on. */
const MAIN_PROCEEDED_MARKER = /Validating formulas\.\.\./

/** The refusal must NAME the flag and SAY it is refusing — a bare non-zero exit is not enough. */
const REFUSAL_NAMES_FLAG = /DRY_RUN/
const REFUSAL_SAYS_REFUSING = /REFUS/i
const REFUSAL_SAYS_NOT_IMPLEMENTED = /not implemented/i

/**
 * Constructed from scratch, NOT spread from process.env — see the file docstring.
 * `extra` supplies the variable under test; omit `DRY_RUN` entirely for the control run.
 */
function runSeed(extra: Record<string, string>): SpawnSyncReturns<string> {
  const env: NodeJS.ProcessEnv = {
    PATH: process.env.PATH ?? '',
    HOME: process.env.HOME ?? '',
    ...extra,
  }
  return spawnSync(TSX, [SEED_REL], {
    cwd: PLATFORM_DIR,
    env,
    encoding: 'utf8',
    timeout: 180_000,
  })
}

function output(r: SpawnSyncReturns<string>): string {
  return `${r.stdout ?? ''}${r.stderr ?? ''}`
}

function expectRefused(r: SpawnSyncReturns<string>): void {
  const combined = output(r)
  // (a) It refused, in words, naming the flag and its absence of implementation.
  expect(combined).toMatch(REFUSAL_NAMES_FLAG)
  expect(combined).toMatch(REFUSAL_SAYS_REFUSING)
  expect(combined).toMatch(REFUSAL_SAYS_NOT_IMPLEMENTED)
  // (b) It exited non-zero. A refusal that exits 0 is a warning, and a warning scrolls past.
  expect(r.status).not.toBe(0)
  expect(r.status).not.toBeNull()
  // (c) It refused BEFORE main() did anything — earlier than validateFormulas(), which is
  //     itself earlier than any pg.Client. No connection can have been attempted.
  expect(combined).not.toMatch(MAIN_PROCEEDED_MARKER)
  expect(combined).not.toMatch(/ECONNREFUSED/)
  // (d) Nothing that looks like a write was announced.
  expect(combined).not.toMatch(/Seed complete/)
}

// tsx is a devDependency; if node_modules is not installed there is nothing to assert about.
const tsxPresent = fs.existsSync(TSX)

describe.skipIf(!tsxPresent)('asset_registry_seed.ts DRY_RUN refusal (M0-T19, ruling D-17)', () => {
  it('A — DRY_RUN=1, the exact documented invocation, is refused', () => {
    expectRefused(runSeed({ DATABASE_URL: UNREACHABLE_DATABASE_URL, DRY_RUN: '1' }))
  }, 180_000)

  it('B — DRY_RUN=0 is refused too: PRESENCE is the trigger, not truthiness', () => {
    // An operator who typed DRY_RUN=0 meaning "off" loses nothing but one error message. An
    // operator who typed DRY_RUN=false expecting a preview would, under a truthiness test,
    // perform the live production upsert. Guessing which they meant is worse than refusing both.
    expectRefused(runSeed({ DATABASE_URL: UNREACHABLE_DATABASE_URL, DRY_RUN: '0' }))
    expectRefused(runSeed({ DATABASE_URL: UNREACHABLE_DATABASE_URL, DRY_RUN: 'false' }))
  }, 180_000)

  it('C — DRY_RUN="" is refused, and the refusal precedes even the DATABASE_URL check', () => {
    // No DATABASE_URL at all: if the refusal were placed after `if (!dbUrl) throw`, this run
    // would fail for the wrong reason and the refusal text would be absent.
    expectRefused(runSeed({ DRY_RUN: '' }))
  }, 180_000)

  it('D — with DRY_RUN absent the seeder still proceeds on its normal path', () => {
    // The guard must not become a blanket refusal. This is the other direction: an ordinary
    // operator run reaches main() and gets as far as validateFormulas() exactly as before.
    const r = runSeed({ DATABASE_URL: UNREACHABLE_DATABASE_URL })
    const combined = output(r)
    expect(combined).toMatch(MAIN_PROCEEDED_MARKER)
    expect(combined).not.toMatch(REFUSAL_SAYS_REFUSING)
    // Deliberately NOT asserting a particular downstream outcome: today this run dies in
    // validateFormulas() on the pre-existing bg_cohort defect; once that is repaired under R0
    // it will die on ECONNREFUSED against port 1 instead. Non-zero holds either way, and this
    // test must not encode the bug it is not allowed to fix.
    expect(r.status).not.toBe(0)
  }, 180_000)
})
