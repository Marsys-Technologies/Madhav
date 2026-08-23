/**
 * ARGV-channel dry-run refusal tests for `platform/scripts/seed/asset_registry_seed.ts`
 * (Nirmāṇa WORK_QUEUE M0-T37; implements ruling D-28 part 3, which extends D-17).
 *
 * THE DEFECT THESE TESTS EXIST TO CATCH. M0-T19 closed the ENVIRONMENT half of the DRY_RUN
 * hazard: `DRY_RUN` present in the environment ⇒ refuse before any database connection. Its own
 * finding F-1 then reported that SIX sibling scripts in this same tree spell dry-run as an ARGV
 * FLAG, not an environment variable:
 *
 *     scripts/migrate.ts:691                        const dryRun = args.includes('--dry-run')
 *     scripts/cleanup_orphaned_firebase_users.ts:16 const DRY_RUN = process.argv.includes('--dry-run')
 *     scripts/observatory/smoke_test.ts:53          const DRY_RUN = process.argv.includes('--dry-run')
 *     scripts/governance/icr_pr_gate.ts:175         const dryRun = args.includes('--dry-run')
 *     (+ the bootstrap scripts F-1 named)
 *
 * ADHIKĀRIN measured the gap directly (D-28 part 3): "asset_registry_seed.ts HAS NO ARGV PARSING
 * WHATSOEVER … so `npx tsx scripts/seed/asset_registry_seed.ts --dry-run` does not error on an
 * unrecognised flag — IT IGNORES IT AND RUNS A FULL LIVE UPSERT, exactly as the DRY_RUN env var
 * did." The ruling: "D-17's ordered refusal must therefore trip on BOTH CHANNELS: the DRY_RUN
 * environment variable AND an argv --dry-run (and its obvious spellings)."
 *
 * This channel is arguably the worse of the two. `DRY_RUN=1` is something an operator
 * half-remembers from a document; `--dry-run` is the spelling THE SURROUNDING CODEBASE ITSELF
 * TAUGHT THEM.
 *
 * WHY UNRECOGNISED FLAGS REFUSE TOO (tests I and J). An allowlist of "obvious spellings" is a
 * guess about which words an operator will reach for, and a spelling nobody imagined would fall
 * straight through into the live upsert — which is exactly how `--dry-run` became invisible in
 * the first place. This seeder understands NO arguments at all, so ANY argument is one it does
 * not understand, and silently ignoring it is the defect class, not the flag. The spelling list
 * therefore chooses only WHICH DIAGNOSTIC is printed; it is not what makes the guard safe.
 *
 * WHAT IS DELIBERATELY NOT DONE HERE: dry-run is NOT implemented. D-17 chose refusal over
 * implementation on the merits (unplanned capability, P9; and a hastily-built preview that is
 * subtly wrong would be a NEW unearned safety signal — the exact defect this campaign removes),
 * and D-28 part 3 completes that choice rather than reversing it.
 *
 * WHY A SUBPROCESS, AND WHY IT IS SAFE — as in the sibling env-channel suite: the claim under
 * test is about the PROCESS (what it prints, what it exits with, and how far it got), nothing is
 * imported from the seeder (ruling D-13 forbids importing it), and every child environment is
 * CONSTRUCTED FROM SCRATCH rather than spread from `process.env`, so a real `DATABASE_URL`
 * exported in a developer or CI shell can never reach a process this file spawns. The
 * `DATABASE_URL` supplied points at a port nothing listens on.
 *
 * THE ORDERING OBSERVABLE. `main()`'s first logging action is `validateFormulas()`, which prints
 * `Validating formulas...` BEFORE any `pg.Client` is constructed. Its ABSENCE is proof the
 * refusal fired earlier than any connection could have been attempted. (The seeder additionally
 * cannot complete today: `validateFormulas()` aborts on `bg_cohort`'s `COHORT_SIZE` — a
 * PRE-EXISTING, UNRELATED defect pinned to R0 carry-forward and deliberately not fixed here
 * (I13). The refusal must not depend on that abort; test K asserts the normal path is REACHED
 * rather than asserting any particular downstream failure.)
 */
import { describe, it, expect } from 'vitest'
import { spawnSync, type SpawnSyncReturns } from 'child_process'
import fs from 'fs'
import path from 'path'

const PLATFORM_DIR = path.resolve(__dirname, '../..')
const TSX = path.join(PLATFORM_DIR, 'node_modules', '.bin', 'tsx')
const SEED_REL = 'scripts/seed/asset_registry_seed.ts'

/** Deliberately unreachable: port 1 is privileged and reserved; nothing listens on it. */
const UNREACHABLE_DATABASE_URL = 'postgresql://nobody:nobody@127.0.0.1:1/nirmana_m0t37_nodb'

/** Logged by `main()` before any `pg.Client` is constructed — the earliest proof main() ran on. */
const MAIN_PROCEEDED_MARKER = /Validating formulas\.\.\./

const REFUSAL_SAYS_REFUSING = /REFUS/i
const REFUSAL_NAMES_DRY_RUN = /DRY[-_ ]?RUN/i
const REFUSAL_SAYS_NOT_IMPLEMENTED = /not implemented/i
/** An unknown-argument refusal must say the script takes no arguments — not just "unknown". */
const REFUSAL_SAYS_NO_ARGUMENTS = /accepts no command-line arguments/i

/**
 * Constructed from scratch, NOT spread from process.env — see the file docstring.
 * `args` are appended after the script path, exactly where an operator would type them.
 */
function runSeed(args: string[], extra: Record<string, string> = {}): SpawnSyncReturns<string> {
  const env: NodeJS.ProcessEnv = {
    PATH: process.env.PATH ?? '',
    HOME: process.env.HOME ?? '',
    ...extra,
  }
  return spawnSync(TSX, [SEED_REL, ...args], {
    cwd: PLATFORM_DIR,
    env,
    encoding: 'utf8',
    timeout: 180_000,
  })
}

function output(r: SpawnSyncReturns<string>): string {
  return `${r.stdout ?? ''}${r.stderr ?? ''}`
}

/** The properties every refusal on this channel must have, whatever the token. */
function expectRefusedBeforeAnyConnection(r: SpawnSyncReturns<string>): string {
  const combined = output(r)
  // (a) It refused, in words.
  expect(combined).toMatch(REFUSAL_SAYS_REFUSING)
  // (b) Non-zero. A refusal that exits 0 is a warning, and a warning scrolls past.
  expect(r.status).not.toBe(0)
  expect(r.status).not.toBeNull()
  // (c) It refused BEFORE main() did anything — earlier than validateFormulas(), which is itself
  //     earlier than any pg.Client. No connection can have been attempted.
  expect(combined).not.toMatch(MAIN_PROCEEDED_MARKER)
  expect(combined).not.toMatch(/ECONNREFUSED/)
  // (d) Nothing that looks like a write was announced.
  expect(combined).not.toMatch(/Seed complete/)
  return combined
}

/** A refusal that additionally identifies itself as the dry-run refusal. */
function expectDryRunRefusal(r: SpawnSyncReturns<string>, token: string): void {
  const combined = expectRefusedBeforeAnyConnection(r)
  expect(combined).toMatch(REFUSAL_NAMES_DRY_RUN)
  expect(combined).toMatch(REFUSAL_SAYS_NOT_IMPLEMENTED)
  // The operator must see the token THEY typed echoed back, not a generic paraphrase — otherwise
  // they cannot tell which of several arguments the seeder objected to.
  expect(combined).toContain(token)
}

// tsx is a devDependency; if node_modules is not installed there is nothing to assert about.
const tsxPresent = fs.existsSync(TSX)

describe.skipIf(!tsxPresent)('asset_registry_seed.ts argv dry-run refusal (M0-T37, ruling D-28 part 3)', () => {
  it('E — `--dry-run`, the spelling six sibling scripts in this tree use, is refused', () => {
    expectDryRunRefusal(
      runSeed(['--dry-run'], { DATABASE_URL: UNREACHABLE_DATABASE_URL }),
      '--dry-run',
    )
  }, 180_000)

  it('F — the obvious spellings are refused: --dryrun, --dry_run, --DRY-RUN, --dry-run=true', () => {
    // Case, separator and value-form variants of the same intent. Each is a spelling a careful
    // operator could plausibly type; each would otherwise have been ignored identically.
    for (const token of ['--dryrun', '--dry_run', '--DRY-RUN', '--dry-run=true', 'dry-run']) {
      expectDryRunRefusal(runSeed([token], { DATABASE_URL: UNREACHABLE_DATABASE_URL }), token)
    }
  }, 180_000)

  it('G — the SYNONYM forms are refused: -n, --check, --preview, --no-write', () => {
    // `-n` is dry-run in make(1), rsync(1) and several others; --check/--preview/--no-write are
    // the other words operators reach for when they want "show me, do not do it". D-28 part 3
    // names "--dry-run (and its obvious spellings)" without enumerating; the asymmetry from D-17
    // decides the rest — refusing someone who meant something else costs one error message,
    // missing a spelling someone typed expecting a preview costs a production upsert to the
    // control-plane table this campaign is repairing.
    for (const token of ['-n', '--check', '--preview', '--no-write', '--noop', '--simulate']) {
      expectDryRunRefusal(runSeed([token], { DATABASE_URL: UNREACHABLE_DATABASE_URL }), token)
    }
  }, 180_000)

  it('H — the argv refusal precedes even the DATABASE_URL check', () => {
    // No DATABASE_URL at all. If the refusal were placed after `if (!dbUrl) throw`, this run
    // would fail for the wrong reason and no refusal text would appear.
    const combined = output(runSeed(['--dry-run']))
    expect(combined).toMatch(REFUSAL_SAYS_REFUSING)
    expect(combined).not.toMatch(/DATABASE_URL env var required/)
    expect(combined).not.toMatch(MAIN_PROCEEDED_MARKER)
  }, 180_000)

  it('I — an UNRECOGNISED flag is refused, not silently ignored', () => {
    // The general case. Silently ignoring an argument nobody parses is the mechanism that made
    // `--dry-run` invisible; a guard that only knows the spellings we thought of reproduces it
    // for the next word. This seeder accepts no arguments, so it says so.
    const r = runSeed(['--frobnicate'], { DATABASE_URL: UNREACHABLE_DATABASE_URL })
    const combined = expectRefusedBeforeAnyConnection(r)
    expect(combined).toMatch(REFUSAL_SAYS_NO_ARGUMENTS)
    expect(combined).toContain('--frobnicate')
  }, 180_000)

  it('J — a bare positional argument is refused too', () => {
    // Not every stale token is flag-shaped. A leftover file path or asset id is just as ignored.
    const r = runSeed(['bg_cohort'], { DATABASE_URL: UNREACHABLE_DATABASE_URL })
    const combined = expectRefusedBeforeAnyConnection(r)
    expect(combined).toMatch(REFUSAL_SAYS_NO_ARGUMENTS)
    expect(combined).toContain('bg_cohort')
  }, 180_000)

  it('K — with NO arguments and no DRY_RUN the seeder still proceeds on its normal path', () => {
    // The other direction: the guard must not become a blanket refusal. An ordinary operator run
    // reaches main() and gets as far as validateFormulas() exactly as it did before this change.
    const r = runSeed([], { DATABASE_URL: UNREACHABLE_DATABASE_URL })
    const combined = output(r)
    expect(combined).toMatch(MAIN_PROCEEDED_MARKER)
    expect(combined).not.toMatch(REFUSAL_SAYS_REFUSING)
    // Deliberately NOT asserting a particular downstream outcome: today this run dies in
    // validateFormulas() on the pre-existing bg_cohort defect; once that is repaired under R0 it
    // will die on ECONNREFUSED against port 1 instead. Non-zero holds either way, and this test
    // must not encode the bug it is not allowed to fix.
    expect(r.status).not.toBe(0)
  }, 180_000)
})
