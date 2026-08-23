/**
 * CONSUMER-SIDE MIGRATION-DRIFT CHECK — Nirmāṇa M0-T45 / SQ-10, D-41 part 4.
 *
 * ── THE GAP THIS CLOSES ──────────────────────────────────────────────────────────────────────
 * M0-T44 (RES-1 / D-18 part 2) made `.github/workflows/deploy.yml`'s `migrate` step ASSERT its
 * own completion — it tees `npx tsx scripts/migrate.ts` and greps the log for the
 * `MIGRATE_RUNNER_COMPLETE` sentinel, so "the migrator ran and printed nothing" can no longer be
 * confused with "the migrator never ran at all".
 *
 * What that fix STRUCTURALLY CANNOT close, because the thing failing to happen is the only thing
 * that could have reported it (D-41 part 4, verbatim): "a program cannot report its own
 * non-execution." The `migrate` job itself being skipped by a path filter or an `if:`, cancelled,
 * removed from the workflow, or — the case D-41 names as worst and least obvious — a downstream
 * `needs: [migrate]` satisfied by a job GitHub Actions marked `skipped` rather than `success`.
 * No grep inside that job's own log can ever see any of these, because there is no log.
 *
 * THE FIX (D-41 part 4's own framing): a CONSUMER-SIDE assertion. Something that does not live
 * inside the migrate step at all — a separate job, run with `if: always()` so a skip/cancel of
 * `migrate` cannot skip it in turn — counts the migrations PRESENT IN THE DEPLOYED CHECKOUT
 * against the rows `_migrations_applied` is supposed to hold, and fails when `pending > 0`.
 *
 * ── WHAT THIS SCRIPT DOES ────────────────────────────────────────────────────────────────────
 * Two independently-obtained counts, compared:
 *   1. `.sql` filenames on disk in THIS checkout's migration directories (`platform/migrations`,
 *      `platform/supabase/migrations`) — the migrations the deployed image actually carries.
 *   2. `filename` rows in `_migrations_applied` — what the deploy is supposed to have recorded.
 * `pending = (1) minus (2)`. `pending.length > 0` fails. Read-only: exactly one `SELECT` against
 * the ledger, no DDL, no DML, no migration ever applied from here.
 *
 * Folds in the identical, previously-unowned observation at `fresh_chart_smoke.yml:219` (D-41
 * part 4: "carries the same unasserted invocation ... FOLDED INTO SQ-10 rather than left as a
 * loose observation") — this same script is invoked a second time in that workflow, against the
 * ephemeral smoke database, immediately after its own `npx tsx scripts/migrate.ts` step.
 *
 * ── WHAT THIS DOES NOT COVER (stated, not assumed) ───────────────────────────────────────────
 * - The whole `deploy.yml` workflow never running at all (disabled, deleted, GitHub outage) —
 *   nothing running inside that workflow can observe its own total non-invocation either. This
 *   is the same "a program cannot report its own non-execution" limit one level up; closing it
 *   needs an external watcher, which is out of this task's scope.
 * - THIS job itself being skipped/cancelled/removed — the identical hazard class recurs at this
 *   level by construction (there is no infinite regress of consumer-side checks). Placing it with
 *   `if: always()` and no `needs`-driven skip path removes the one skip mode this task was asked
 *   to close (a `needs:` satisfied by a skipped `migrate`); it does not remove every conceivable
 *   way to delete or disable this job too.
 * - A migration applied then reverted at the SQL level without removing its ledger row, or a
 *   ledger row inserted without the SQL having run — this check trusts `_migrations_applied` as
 *   the record of what ran, exactly as `migrate.ts` itself does. It is not a schema-content diff.
 */
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { Pool } from 'pg'

/** `.sql` filenames found across the configured migration directories, or `null` if NONE of the
 *  configured directories could even be found — a broken-checkout signal, never "zero migrations
 *  exist" (this repo has hundreds; see the `filesOnDisk.length === 0` branch below for why an
 *  empty-but-present result is treated with the same suspicion). */
export type FilesOnDisk = string[] | null

/** `filename` values read from `_migrations_applied`, or `null` if the ledger could not be
 *  queried at all (connection failure, missing table, permission error, ...). */
export type AppliedFilenames = string[] | null

export interface MigrationDriftInput {
  filesOnDisk: FilesOnDisk
  appliedFilenames: AppliedFilenames
}

export type MigrationDriftResult =
  | { status: 'not_checkable'; reason: string }
  | { status: 'pass'; filesOnDiskCount: number; appliedCount: number }
  | { status: 'fail'; filesOnDiskCount: number; appliedCount: number; pending: string[] }

/**
 * Pure decision function — no I/O, no DB, no filesystem. `evaluateMigrationDrift` takes the two
 * already-collected counts and returns exactly one of three outcomes.
 *
 * `status: 'pass'` is returned from exactly ONE place in this function (see the structural test
 * in `verify_migrations_deployed.test.ts`), and only after BOTH sides were determinable AND the
 * computed `pending` set is empty — an honest `not_checkable` is returned instead of a pass for
 * every case where either side is missing or the disk-side count looks like a broken read.
 */
export function evaluateMigrationDrift(input: MigrationDriftInput): MigrationDriftResult {
  const { filesOnDisk, appliedFilenames } = input

  if (filesOnDisk === null) {
    return {
      status: 'not_checkable',
      reason:
        'could not enumerate migration files in this checkout — none of the configured ' +
        'migration directories exist. This is a broken-checkout signal, not "zero migrations ' +
        'exist", and is never treated as a pass.',
    }
  }

  if (filesOnDisk.length === 0) {
    return {
      status: 'not_checkable',
      reason:
        'zero .sql files found across every configured migration directory. This repo carries ' +
        'hundreds of migrations, so a count of zero means the check looked at nothing, not that ' +
        'nothing is pending (mirrors migrate.ts\'s own "files_on_disk=0 is a configuration ' +
        'result, not an up-to-date result" rule) — never treated as a pass.',
    }
  }

  if (appliedFilenames === null) {
    return {
      status: 'not_checkable',
      reason:
        'could not query _migrations_applied (connection error, missing table, or permission ' +
        'error). Cannot determine what the deploy actually applied, so a missing answer is ' +
        'never treated as a pass.',
    }
  }

  const applied = new Set(appliedFilenames)
  const pending = filesOnDisk.filter(f => !applied.has(f)).sort()

  if (pending.length > 0) {
    return {
      status: 'fail',
      filesOnDiskCount: filesOnDisk.length,
      appliedCount: applied.size,
      pending,
    }
  }

  return { status: 'pass', filesOnDiskCount: filesOnDisk.length, appliedCount: applied.size }
}

/**
 * Enumerate `.sql` filenames across the given directories (the "deployed image" side).
 * Read-only filesystem access — no writes, no execution of any file's contents.
 *
 * Returns `null` only when NONE of `dirs` exist at all — a directory that exists but is empty
 * still counts as "found" here; `evaluateMigrationDrift` is what decides an empty RESULT (0
 * files across directories that DO exist) is itself suspicious, not this collector.
 */
export function collectMigrationFilenames(dirs: string[]): FilesOnDisk {
  let anyDirExists = false
  const files: string[] = []
  for (const dir of dirs) {
    if (!fs.existsSync(dir)) continue
    anyDirExists = true
    const entries = fs.readdirSync(dir).filter(f => f.endsWith('.sql'))
    files.push(...entries)
  }
  if (!anyDirExists) return null
  return files
}

/**
 * Read-only query against the migrations ledger. Exactly one `SELECT`; never writes, never
 * creates the table (unlike `migrate.ts`'s `TRACKER_DDL`, which this script deliberately does
 * NOT invoke or import — D-13 forbids importing `migrate.ts`, and this task is read-only by its
 * own constraint regardless).
 *
 * Any failure — connection refused, table missing, permission denied, a malformed URL — is
 * caught and reported as `null`, never surfaced as "zero rows applied". Those are different
 * facts: zero rows applied is real data (every migration is genuinely pending); `null` is "the
 * question could not be asked".
 */
export async function queryAppliedFilenames(databaseUrl: string): Promise<AppliedFilenames> {
  const pool = new Pool({ connectionString: databaseUrl })
  try {
    const res = await pool.query('SELECT filename FROM _migrations_applied')
    return res.rows.map((r: { filename: string }) => r.filename)
  } catch (err) {
    console.error('[verify-migrations-deployed] could not query _migrations_applied:', err)
    return null
  } finally {
    await pool.end().catch(() => {})
  }
}

/** The default two migration directories `migrate.ts` reads, resolved relative to THIS file
 *  (one directory deeper than `scripts/migrate.ts`, hence `../../` here vs its own `../`). */
export function defaultMigrationDirs(scriptFileUrl: string): string[] {
  const scriptDir = path.dirname(fileURLToPath(scriptFileUrl))
  return [
    path.resolve(scriptDir, '../../migrations'),
    path.resolve(scriptDir, '../../supabase/migrations'),
  ]
}

function formatFailureMessage(result: Extract<MigrationDriftResult, { status: 'fail' }>): string {
  return (
    `${result.pending.length} migration(s) present in this checkout are NOT recorded in ` +
    `_migrations_applied: ${result.pending.join(', ')}. files_on_disk=${result.filesOnDiskCount} ` +
    `applied=${result.appliedCount}. This means the deploy's migrate step did not run to ` +
    `completion against THIS database — it may have been skipped by a path filter or an if:, ` +
    `cancelled, removed, or satisfied a needs: dependency while itself being skipped. ` +
    `See D-41 part 4 / Nirmāṇa SQ-10.`
  )
}

async function main(): Promise<void> {
  const databaseUrl = process.env.DATABASE_URL
  if (!databaseUrl) {
    console.error(
      '::error::DATABASE_URL not set — cannot query the migrations ledger. Refusing to report a pass.'
    )
    process.exit(2)
  }

  const dirs = defaultMigrationDirs(import.meta.url)
  const filesOnDisk = collectMigrationFilenames(dirs)
  const appliedFilenames = await queryAppliedFilenames(databaseUrl as string)
  const result = evaluateMigrationDrift({ filesOnDisk, appliedFilenames })

  if (result.status === 'pass') {
    console.log(
      `[verify-migrations-deployed] PASS — ${result.filesOnDiskCount} migration file(s) on ` +
      `disk, all recorded in _migrations_applied (${result.appliedCount} ledger row(s), which ` +
      `may include rows for files no longer on disk).`
    )
    process.exit(0)
  }

  if (result.status === 'fail') {
    console.error(`::error::${formatFailureMessage(result)}`)
    process.exit(1)
  }

  console.error(`::error::migration-drift check is NOT CHECKABLE: ${result.reason}`)
  process.exit(2)
}

// Guard: only execute when run directly, not when imported by tests — same convention as
// scripts/ci/dispatch_gate.ts.
if (process.env.NODE_ENV !== 'test') {
  main()
}
