/**
 * M0-T45 / SQ-10 / D-41 part 4 — "a program cannot report its own non-execution."
 *
 * The defect class this file's subject closes: `migrate.ts`'s own completion sentinel
 * (M0-T44 / MIGRATE_COMPLETION_SENTINEL) can only ever assert "the migrate step, once started,
 * ran to completion." It cannot assert "the migrate step ran at all" — a job skipped by a path
 * filter or an `if:`, cancelled, removed, or a `needs:` satisfied by a job GitHub Actions itself
 * marked `skipped`, produces no log for any sentinel to appear in or be grepped from.
 *
 * `verify_migrations_deployed.ts`'s `evaluateMigrationDrift` closes that gap from the consumer
 * side: it compares migrations PRESENT ON DISK in this checkout against rows recorded in
 * `_migrations_applied`, independent of whether `migrate.ts` itself ever ran this deploy.
 *
 * Per the mutation-proof doctrine (D-41, standing since the sentinel-on-failure finding):
 *   (1) behavioural tests below, including THE scenario the check exists for and its converse;
 *   (2) a structural assertion over the source, with paired positives;
 *   (3) at least one INVERSE-DIRECTION case — one that would make the check wrongly PASS if a
 *       comparison were flipped, not only one that would make it wrongly fail;
 *   (4) this file states what the structural test does NOT establish, at the bottom.
 */
import { describe, it, expect, vi } from 'vitest'
import fs from 'fs'
import os from 'os'
import path from 'path'

// The opt-out this file's subject is keyed on (Nirmāṇa R-28.1 / D-49 / SQ-17 — the residual
// PARĪKṢAKA raised against this very script at V-28). `verify_migrations_deployed.ts` now RUNS BY
// DEFAULT and only stays silent when a caller explicitly says `IMPORT_ONLY=1`; the guard used to
// key on `NODE_ENV !== 'test'`, which made a silent exit-0 the default in every environment CI
// already sets `NODE_ENV: test` for. This test imports the module for its pure exports, so it is
// the caller that must opt out — and it must do so BEFORE the import below executes, which is what
// `vi.hoisted` is for (vitest lifts it above the import block).
vi.hoisted(() => {
  process.env.IMPORT_ONLY = '1'
})

import {
  evaluateMigrationDrift,
  collectMigrationFilenames,
  defaultMigrationDirs,
  type MigrationDriftInput,
} from '../ci/verify_migrations_deployed'

describe('evaluateMigrationDrift — the scenario this check exists for', () => {
  it('FAILS when a migration on disk is not recorded as applied (the hazard itself)', () => {
    const input: MigrationDriftInput = {
      filesOnDisk: ['001_a.sql', '002_b.sql'],
      appliedFilenames: ['001_a.sql'], // 002_b.sql never made it into the ledger
    }
    const result = evaluateMigrationDrift(input)
    expect(result.status).toBe('fail')
    if (result.status === 'fail') {
      expect(result.pending).toEqual(['002_b.sql'])
      expect(result.filesOnDiskCount).toBe(2)
      expect(result.appliedCount).toBe(1)
    }
  })

  it('PASSES the identical file set once the ledger records it — same disk state, different ledger', () => {
    const input: MigrationDriftInput = {
      filesOnDisk: ['001_a.sql', '002_b.sql'],
      appliedFilenames: ['001_a.sql', '002_b.sql'],
    }
    const result = evaluateMigrationDrift(input)
    expect(result.status).toBe('pass')
    if (result.status === 'pass') {
      expect(result.filesOnDiskCount).toBe(2)
      expect(result.appliedCount).toBe(2)
    }
  })

  it('PASSES when the ledger has MORE rows than files on disk (renumbered / removed files do not falsely fail)', () => {
    // Production carries ledger rows for files no longer on disk (renumbers, legacy cleanup).
    // The check must not punish that — it only cares that everything ON DISK is covered.
    const input: MigrationDriftInput = {
      filesOnDisk: ['001_a.sql', '002_b.sql'],
      appliedFilenames: ['001_a.sql', '002_b.sql', '999_gone_from_disk.sql'],
    }
    const result = evaluateMigrationDrift(input)
    expect(result.status).toBe('pass')
    if (result.status === 'pass') expect(result.appliedCount).toBe(3)
  })
})

describe('evaluateMigrationDrift — honest not_checkable, never a silent pass', () => {
  it('is not_checkable when the deployed-image migration list cannot be enumerated at all', () => {
    const result = evaluateMigrationDrift({ filesOnDisk: null, appliedFilenames: ['001_a.sql'] })
    expect(result.status).toBe('not_checkable')
  })

  it('is not_checkable when every configured migration directory reads as empty (broken-checkout smell)', () => {
    const result = evaluateMigrationDrift({ filesOnDisk: [], appliedFilenames: ['001_a.sql'] })
    expect(result.status).toBe('not_checkable')
  })

  it('is not_checkable when the ledger cannot be queried, even though the disk side is healthy', () => {
    const result = evaluateMigrationDrift({
      filesOnDisk: ['001_a.sql', '002_b.sql'],
      appliedFilenames: null,
    })
    expect(result.status).toBe('not_checkable')
    // The critical property: an unknown ledger must NOT default to "assume applied" (pass) or
    // "assume empty" (which would coincidentally still fail, but for the wrong reason and via
    // the wrong code path — see the structural test below for why that distinction matters).
    expect(result.status).not.toBe('pass')
  })

  it('never reports not_checkable as exit-code-0 territory in the CLI\'s own vocabulary', () => {
    // Documentation-as-test: the three statuses are mutually exclusive string literals, so a
    // caller cannot mistake 'not_checkable' for 'pass' by loose truthiness.
    const notCheckable = evaluateMigrationDrift({ filesOnDisk: null, appliedFilenames: null })
    expect(notCheckable.status).toBe('not_checkable')
    expect(notCheckable.status === ('pass' as typeof notCheckable.status)).toBe(false)
  })
})

describe('evaluateMigrationDrift — inverse-direction mutation coverage', () => {
  // These cases are chosen specifically to fail under a flipped comparison, not merely to widen
  // line coverage. Per D-41: "include at least one INVERSE-DIRECTION mutation — one that makes
  // the signal fire when it should NOT, not only one that suppresses it." The behavioural tests
  // above already prove the check catches a real gap (fires when it should). These prove the
  // check does NOT fire when it should not, and that a plausible inversion of the core filter
  // would be caught by at least one of the two.

  it('does not fire on a fully-applied set of size 1 (guards against `!applied.has` silently inverted)', () => {
    // If `filesOnDisk.filter(f => !applied.has(f))` were mutated to `filter(f => applied.has(f))`,
    // this single-file, fully-applied case would flip from pending=[] to pending=['001_a.sql'] —
    // i.e. the mutant would make a healthy state report FAIL. This test pins the correct
    // direction: applied and current must PASS.
    const result = evaluateMigrationDrift({
      filesOnDisk: ['001_a.sql'],
      appliedFilenames: ['001_a.sql'],
    })
    expect(result.status).toBe('pass')
  })

  it('does not fire on a large fully-applied set (guards against an off-by-one on pending.length)', () => {
    // If `pending.length > 0` were mutated to `pending.length >= 0` (always true) the check
    // would ALWAYS fail, including here — a healthy, fully-applied 5-file set. This is the
    // inverse-direction case for the pass/fail threshold itself: it must not fire on a genuinely
    // clean state, symmetric to the "fires when it should" cases above.
    const names = ['001_a.sql', '002_b.sql', '003_c.sql', '004_d.sql', '005_e.sql']
    const result = evaluateMigrationDrift({ filesOnDisk: names, appliedFilenames: [...names] })
    expect(result.status).toBe('pass')
  })

  it('fires on exactly the pending subset in a mixed set — not the whole set, not zero', () => {
    // A mutant that inverted the filter predicate would report ALL 3 files pending (or 0)
    // instead of exactly the 1 genuinely unapplied file. Pinning the exact pending array — not
    // just "status is fail" — is what makes this test catch that specific inversion rather than
    // any other pending>0 mutant that a coarser assertion would also happen to pass.
    const result = evaluateMigrationDrift({
      filesOnDisk: ['001_a.sql', '002_b.sql', '003_c.sql'],
      appliedFilenames: ['001_a.sql', '003_c.sql'],
    })
    expect(result.status).toBe('fail')
    if (result.status === 'fail') expect(result.pending).toEqual(['002_b.sql'])
  })
})

describe('collectMigrationFilenames — filesystem collector', () => {
  it('returns null when none of the configured directories exist', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'verify-migrations-'))
    fs.rmSync(dir, { recursive: true, force: true }) // guaranteed not to exist
    const result = collectMigrationFilenames([dir, path.join(dir, 'also-missing')])
    expect(result).toBeNull()
  })

  it('returns an empty array (not null) when a configured directory exists but is empty', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'verify-migrations-'))
    try {
      expect(collectMigrationFilenames([dir])).toEqual([])
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })

  it('collects .sql files across multiple directories and ignores non-.sql files', () => {
    const dirA = fs.mkdtempSync(path.join(os.tmpdir(), 'verify-migrations-a-'))
    const dirB = fs.mkdtempSync(path.join(os.tmpdir(), 'verify-migrations-b-'))
    try {
      fs.writeFileSync(path.join(dirA, '001_a.sql'), 'select 1;')
      fs.writeFileSync(path.join(dirA, 'README.md'), 'not a migration')
      fs.writeFileSync(path.join(dirB, '002_b.sql'), 'select 2;')
      const result = collectMigrationFilenames([dirA, dirB])
      expect(result).not.toBeNull()
      expect((result as string[]).sort()).toEqual(['001_a.sql', '002_b.sql'])
    } finally {
      fs.rmSync(dirA, { recursive: true, force: true })
      fs.rmSync(dirB, { recursive: true, force: true })
    }
  })
})

describe('defaultMigrationDirs — resolves the same two directories migrate.ts reads', () => {
  it('resolves to platform/migrations and platform/supabase/migrations', () => {
    const scriptUrl = 'file:///repo/platform/scripts/ci/verify_migrations_deployed.ts'
    const dirs = defaultMigrationDirs(scriptUrl)
    expect(dirs).toEqual([
      path.resolve('/repo/platform/scripts/ci', '../../migrations'),
      path.resolve('/repo/platform/scripts/ci', '../../supabase/migrations'),
    ])
    expect(dirs[0]).toBe(path.normalize('/repo/platform/migrations'))
    expect(dirs[1]).toBe(path.normalize('/repo/platform/supabase/migrations'))
  })
})

/**
 * STRUCTURAL ASSERTION over `evaluateMigrationDrift`'s own source.
 *
 * WHAT THIS PROVES: `status: 'pass'` is returned from exactly one place in the function, and it
 * is textually the LAST branch — after the three `not_checkable` guards and the `pending.length
 * > 0` fail branch. A second, hidden path to `status: 'pass'` (e.g. an early return added later
 * that skips the pending check) cannot exist without this test failing, independent of whether
 * any behavioural test happens to exercise that path.
 *
 * WHAT THIS DOES NOT PROVE (stated per D-41's requirement, not assumed):
 *   - It does NOT prove the single `pass` branch is ever actually REACHED with the right
 *     preconditions — the behavioural tests above do that.
 *   - It does NOT prove `pending.length > 0` is the correct condition (a mutant changing `> 0`
 *     to `> 1` would leave this structural test green; the inverse-direction behavioural tests
 *     above are what catches that class of defect).
 *   - It does NOT execute the CLI's `main()` — only the pure decision function's source is
 *     scanned. `main()`'s wiring (DATABASE_URL presence, exit codes) is covered separately below.
 */
describe('evaluateMigrationDrift — status: "pass" has exactly one emission point', () => {
  it('is returned from exactly one place, and only after the not_checkable guards and pending check', () => {
    const sourcePath = path.resolve(__dirname, '../ci/verify_migrations_deployed.ts')
    const source = fs.readFileSync(sourcePath, 'utf8')

    // Paired positive: prove we read the right file before trusting an empty offenders list.
    expect(source).toContain('export function evaluateMigrationDrift')

    const fnStart = source.indexOf('export function evaluateMigrationDrift')
    const fnEnd = source.indexOf(
      '\n/**\n * Enumerate `.sql` filenames across the given directories'
    )
    expect(fnStart).toBeGreaterThan(-1)
    expect(fnEnd).toBeGreaterThan(fnStart)
    const fnBody = source.slice(fnStart, fnEnd)

    const passOccurrences = fnBody.match(/status:\s*'pass'/g) ?? []
    expect(passOccurrences.length).toBe(1)

    // Ordering check: the three not_checkable returns and the fail return must all appear
    // BEFORE the pass return, textually — i.e. pass cannot be reached by falling through
    // anything other than the bottom of the function.
    const notCheckableCount = (fnBody.match(/status:\s*'not_checkable'/g) ?? []).length
    expect(notCheckableCount).toBe(3) // filesOnDisk null, filesOnDisk empty, appliedFilenames null

    const passIndex = fnBody.indexOf("status: 'pass'")
    const failIndex = fnBody.indexOf("status: 'fail'")
    const lastNotCheckableIndex = fnBody.lastIndexOf("status: 'not_checkable'")
    expect(failIndex).toBeGreaterThan(lastNotCheckableIndex)
    expect(passIndex).toBeGreaterThan(failIndex)
  })
})

describe('main() CLI wiring — never exits 0 on an unreachable database', () => {
  it('a run with an unreachable DATABASE_URL exits non-zero and never claims PASS', async () => {
    const { execFileSync } = await import('child_process')
    const platformDir = path.resolve(__dirname, '../..')
    let stdout = ''
    let status = 0
    try {
      stdout = execFileSync('npx', ['tsx', 'scripts/ci/verify_migrations_deployed.ts'], {
        cwd: platformDir,
        // Explicitly unreachable — this test must be incapable of touching a live database
        // even if one happens to be configured in the ambient environment.
        // IMPORT_ONLY is cleared deliberately: this test process sets it to '1' above so it can
        // import the module, and `...process.env` would otherwise hand that opt-out to the child
        // and silence the very CLI this case exists to exercise. The assertions below are the
        // proof it did not — an ECONNREFUSED in the child's output and a non-zero exit are only
        // producible by a `main()` that actually ran.
        env: {
          ...process.env,
          DATABASE_URL: 'postgresql://nobody@127.0.0.1:1/nodb',
          NODE_ENV: 'production',
          IMPORT_ONLY: '',
        },
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 60_000,
      })
    } catch (err) {
      const e = err as { status?: number; stdout?: string; stderr?: string }
      status = e.status ?? -1
      stdout = `${e.stdout ?? ''}${e.stderr ?? ''}`
    }
    // Paired positive first: the process really did fail to reach the database …
    expect(stdout).toMatch(/ECONNREFUSED|not_checkable|could not query/i)
    // … and only then does the non-zero exit / absence of a PASS claim mean anything.
    expect(status).not.toBe(0)
    expect(stdout).not.toContain('PASS —')
  }, 60_000)

  /**
   * ── Entrypoint-guard detector (Nirmāṇa R-28.1 / V-28 / D-49 / SQ-17) ───────────────────────
   *
   * The case above pins NODE_ENV=production in the child, so it was structurally incapable of
   * seeing the residual PARĪKṢAKA found against this script at V-28: the guard used to read
   * `if (process.env.NODE_ENV !== 'test')`, so under `NODE_ENV=test` — which .github/workflows/
   * ci.yml already exports job-wide on unit-tests, db-integration-tests and planner-regression —
   * this gate exited 0 with no stdout and no stderr, having compared nothing. The guard now keys
   * on an explicit `IMPORT_ONLY=1` opt-out instead, so the gate RUNS BY DEFAULT.
   *
   * These two cases are the detector for that, and they are paired so neither is vacuous: the
   * first proves the gate still runs (and still refuses to report a pass) under NODE_ENV=test,
   * the second proves the explicit opt-out is what silences it. Reverting the guard to the
   * NODE_ENV form, or flipping its polarity, fails the first.
   */
  it('CAN-FAIL: under NODE_ENV=test with no opt-out, the check still runs and refuses a pass', async () => {
    const { execFileSync } = await import('child_process')
    const platformDir = path.resolve(__dirname, '../..')
    let out = ''
    let status = 0
    try {
      out = execFileSync('npx', ['tsx', 'scripts/ci/verify_migrations_deployed.ts'], {
        cwd: platformDir,
        // NODE_ENV=test is the point of this case. IMPORT_ONLY is cleared deliberately: this test
        // process sets it to '1' so it can import the module, and `...process.env` would otherwise
        // hand that opt-out to the child and silence the gate under test.
        env: {
          ...process.env,
          DATABASE_URL: 'postgresql://nobody@127.0.0.1:1/nodb',
          NODE_ENV: 'test',
          IMPORT_ONLY: '',
        },
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 60_000,
      })
    } catch (err) {
      const e = err as { status?: number; stdout?: string; stderr?: string }
      status = e.status ?? -1
      out = `${e.stdout ?? ''}${e.stderr ?? ''}`
    }
    expect(out).toContain('NOT CHECKABLE')
    expect(status).toBe(2)
    expect(out).not.toContain('PASS —')
  }, 60_000)

  it('the explicit IMPORT_ONLY=1 opt-out still suppresses the CLI (what lets this file import it)', async () => {
    const { execFileSync } = await import('child_process')
    const platformDir = path.resolve(__dirname, '../..')
    let out = ''
    let status = 0
    try {
      out = execFileSync('npx', ['tsx', 'scripts/ci/verify_migrations_deployed.ts'], {
        cwd: platformDir,
        env: {
          ...process.env,
          DATABASE_URL: 'postgresql://nobody@127.0.0.1:1/nodb',
          NODE_ENV: 'test',
          IMPORT_ONLY: '1',
        },
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 60_000,
      })
    } catch (err) {
      const e = err as { status?: number; stdout?: string; stderr?: string }
      status = e.status ?? -1
      out = `${e.stdout ?? ''}${e.stderr ?? ''}`
    }
    expect(out).toBe('')
    expect(status).toBe(0)
  }, 60_000)
})
