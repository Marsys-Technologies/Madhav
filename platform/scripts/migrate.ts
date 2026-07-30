/**
 * Idempotent migration runner.
 * - Reads platform/migrations/*.sql and platform/supabase/migrations/*.sql
 * - Tracks applied migrations in _migrations_applied (id, filename, applied_at, sha256)
 * - For each unapplied migration in lexical order:
 *     BEGIN; <SQL>; INSERT INTO _migrations_applied; COMMIT;
 *   On any error: ROLLBACK and exit non-zero
 * - For each ALREADY-applied migration: recompute its sha256 and compare against the value
 *   stored at apply time. Identical -> genuinely skip. Different -> throw MigrationHashMismatchError
 *   (fail loudly, non-zero exit) — the runner never auto-re-applies and never silently continues.
 *   See Dvārapāla RULING 58 / 00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md.
 * - EXCEPTION — disclosed-residual allowlist (Dvārapāla RULING 73): a mismatch whose exact
 *   (stored, current) hash PAIR is itemized in `scripts/ci/migration_hash_disclosed_residuals.json`
 *   logs a visible non-fatal warning and is treated as a genuine skip, same discipline as
 *   `migration_number_guard.ts`'s `disclosed_additions` (itemized/dated/attributed, never a
 *   blanket pass). The pin is exact: if the on-disk content is edited AGAIN past the disclosed
 *   "current" hash, the guard still fails loudly — disclosure freezes ONE historical mismatch,
 *   it is not a standing exemption for the file. See loadHashDisclosures() below.
 * - --dry-run flag: lists what would be applied; no writes. Still performs the hash comparison
 *   above so an operator finds out about drift from a preview, not only from a real run.
 * - --target <filename> flag: stops after that migration
 *
 * Connection: DATABASE_URL env var (Cloud SQL Auth Proxy in CI via WIF).
 */

import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { Pool, type PoolClient } from 'pg'

export const TRACKER_DDL = `
CREATE TABLE IF NOT EXISTS _migrations_applied (
  id SERIAL PRIMARY KEY,
  filename TEXT UNIQUE NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sha256 TEXT NOT NULL
);
`

export interface MigrationFile {
  name: string
  dir: string
}

export interface RunOptions {
  dryRun?: boolean
  target?: string
  /**
   * Disclosed-residual allowlist (Dvārapāla RULING 73), keyed by filename. Defaults to loading
   * `scripts/ci/migration_hash_disclosed_residuals.json` from disk. Tests pass an explicit map
   * (including an empty one) so disclosure behavior is exercised deterministically without
   * depending on the real file's current contents.
   */
  disclosures?: Map<string, DisclosedHashMismatch>
}

/**
 * One itemized, dated, attributed entry pinning a SPECIFIC historical (stored, current) hash
 * pair for a migration whose already-applied content no longer matches what was recorded at
 * apply time — Dvārapāla RULING 73. Same discipline as `migration_number_guard.ts`'s
 * `DisclosedAddition`: every field is required, or the entry does not count as disclosed and
 * the guard fails exactly as if the file were never listed. The pin is exact and two-sided —
 * BOTH `stored_sha256` (what production actually has) and `current_sha256_at_disclosure` (what
 * disk actually has, as of the disclosure) must match live reality for the warning path to take.
 * If the file is edited again after disclosure, `current_sha256_at_disclosure` stops matching
 * and the guard fails loudly — the disclosure pins one specific historical mismatch, not a
 * standing exemption.
 */
export interface DisclosedHashMismatch {
  filename: string
  stored_sha256: string
  current_sha256_at_disclosure: string
  cause: string
  disclosed_via: string
  fixed_by_samapti: boolean
}

interface HashDisclosureFile {
  entries: DisclosedHashMismatch[]
}

/** Repo-root-relative default path to the disclosed-residual allowlist. */
export function defaultHashDisclosurePath(): string {
  const scriptDir = path.dirname(new URL(import.meta.url).pathname)
  return path.join(scriptDir, 'ci', 'migration_hash_disclosed_residuals.json')
}

/**
 * Load the disclosed-residual allowlist into a filename-keyed map. An entry missing a required
 * field is dropped (treated as UNDISCLOSED), same as `migration_number_guard.ts`'s E4 check —
 * a partial disclosure is not a partial pass. Missing file -> empty map (no disclosures active),
 * never a hard error, so a fresh checkout without the file behaves exactly like RULING 58's
 * original fail-loud-on-any-mismatch guard.
 */
export function loadHashDisclosures(filePath: string = defaultHashDisclosurePath()): Map<string, DisclosedHashMismatch> {
  const out = new Map<string, DisclosedHashMismatch>()
  let raw: string
  try {
    raw = fs.readFileSync(filePath, 'utf8')
  } catch {
    return out
  }
  const parsed = JSON.parse(raw) as HashDisclosureFile
  for (const entry of parsed.entries ?? []) {
    const missing: string[] = []
    if (!entry.filename) missing.push('filename')
    if (!entry.stored_sha256) missing.push('stored_sha256')
    if (!entry.current_sha256_at_disclosure) missing.push('current_sha256_at_disclosure')
    if (!entry.cause) missing.push('cause')
    if (!entry.disclosed_via) missing.push('disclosed_via')
    if (typeof entry.fixed_by_samapti !== 'boolean') missing.push('fixed_by_samapti')
    if (missing.length > 0) {
      console.warn(
        `[migration-hash-disclosure] entry for "${entry.filename ?? '(unknown)'}" is missing ` +
        `required field(s): ${missing.join(', ')} — treated as UNDISCLOSED, not a partial pass.`
      )
      continue
    }
    out.set(entry.filename, entry)
  }
  return out
}

/**
 * Thrown when a migration already recorded in _migrations_applied no longer matches the sha256
 * stored at apply time — i.e. its file was edited after it was applied. This is always an
 * operator decision (revert the file, or carry the change forward as a NEW migration), never
 * something the runner resolves on its own: never silently skip, never auto-re-apply.
 */
export class MigrationHashMismatchError extends Error {
  constructor(
    public readonly filename: string,
    public readonly storedSha256: string,
    public readonly currentSha256: string
  ) {
    super(
      `Migration "${filename}" is already recorded as applied in _migrations_applied, but its SQL ` +
      `content on disk no longer matches the sha256 recorded when it was applied.\n` +
      `  stored sha256:  ${storedSha256}\n` +
      `  current sha256: ${currentSha256}\n` +
      `An already-applied migration must never be edited. This is an operator decision, not something ` +
      `the migration runner will resolve automatically — either revert "${filename}" to the content that ` +
      `was applied, or create a NEW migration file to carry the intended change forward.`
    )
    this.name = 'MigrationHashMismatchError'
  }
}

export function collectMigrationFiles(dirs: string[]): MigrationFile[] {
  const files: MigrationFile[] = []
  for (const dir of dirs) {
    if (!fs.existsSync(dir)) continue
    const entries = fs.readdirSync(dir)
      .filter(f => f.endsWith('.sql'))
      .sort()
    files.push(...entries.map(name => ({ name, dir })))
  }
  files.sort((a, b) => a.name.localeCompare(b.name))
  return files
}

/** Returns a map of filename -> sha256 recorded at apply time, for every applied migration. */
async function getApplied(client: PoolClient): Promise<Map<string, string>> {
  const res = await client.query('SELECT filename, sha256 FROM _migrations_applied')
  return new Map(
    res.rows.map((r: { filename: string; sha256: string }) => [r.filename, r.sha256])
  )
}

function readMigrationSql(file: MigrationFile): string {
  return fs.readFileSync(path.join(file.dir, file.name), 'utf8')
}

function sha256Of(sql: string): string {
  return crypto.createHash('sha256').update(sql).digest('hex')
}

/**
 * If `file` is already applied, verify its on-disk content still matches the stored hash.
 * Throws MigrationHashMismatchError on mismatch — UNLESS the mismatch is an exact match for a
 * disclosed residual (Dvārapāla RULING 73): both the stored hash AND the current on-disk hash
 * equal the pinned pair in `disclosures`, in which case this logs a visible non-fatal warning
 * and returns (genuine skip, not a silent pass — the warning is real output, not suppressed).
 * A disclosed filename whose CURRENT hash has drifted past the pinned `current_sha256_at_disclosure`
 * (edited again after disclosure) is NOT covered — it falls through to the same fail-loud path
 * as an undisclosed file, because the disclosure pins one specific historical mismatch, not a
 * standing exemption. Returns nothing on match (or if not applied yet) — the caller decides
 * what to do next (skip vs. apply).
 */
function assertAppliedHashMatches(
  file: MigrationFile,
  applied: Map<string, string>,
  sql: string,
  disclosures: Map<string, DisclosedHashMismatch> = new Map()
): void {
  const storedSha256 = applied.get(file.name)
  if (storedSha256 === undefined) return // not applied yet — nothing to compare
  const currentSha256 = sha256Of(sql)
  if (currentSha256 === storedSha256) return // matches — genuine skip

  const disclosed = disclosures.get(file.name)
  if (
    disclosed &&
    disclosed.stored_sha256 === storedSha256 &&
    disclosed.current_sha256_at_disclosure === currentSha256
  ) {
    console.warn(
      `[migration-hash-disclosure] "${file.name}" has a KNOWN, disclosed sha256 mismatch — ` +
      `treated as a skip, not applied, not fatal.\n` +
      `  stored sha256:  ${storedSha256}\n` +
      `  current sha256: ${currentSha256}\n` +
      `  cause: ${disclosed.cause}\n` +
      `  disclosed via: ${disclosed.disclosed_via}\n` +
      `  This disclosure pins ONE specific historical mismatch. If "${file.name}" is edited ` +
      `again, its new hash will no longer match the pinned pair and this guard will fail loudly.`
    )
    return
  }

  // Either not disclosed at all, or disclosed but the pinned pair no longer matches live
  // reality (e.g. the file was edited again after disclosure, or the DB row changed) —
  // fail exactly as RULING 58's original guard does. Disclosure is not a standing exemption.
  throw new MigrationHashMismatchError(file.name, storedSha256, currentSha256)
}

/**
 * Core migration logic — exported for unit tests.
 * Returns list of migration filenames that were (or would be) applied.
 */
export async function runMigrations(
  client: PoolClient,
  dirs: string[],
  options: RunOptions = {}
): Promise<string[]> {
  const { dryRun = false, target } = options
  // Defaults to loading scripts/ci/migration_hash_disclosed_residuals.json from disk (real
  // production behavior — main() never passes this explicitly). Tests pass an explicit Map
  // (including `new Map()`) so disclosure behavior is exercised deterministically.
  const disclosures = options.disclosures ?? loadHashDisclosures()

  await client.query(TRACKER_DDL)
  const files = collectMigrationFiles(dirs)

  if (dryRun) {
    const applied = await getApplied(client)
    for (const file of files) {
      if (!applied.has(file.name)) continue
      assertAppliedHashMatches(file, applied, readMigrationSql(file), disclosures)
    }
    return files.filter(f => !applied.has(f.name)).map(f => f.name)
  }

  const ran: string[] = []
  for (const file of files) {
    // Re-query per file so seed migrations that bulk-insert into _migrations_applied
    // are reflected before we decide whether to apply subsequent files.
    const applied = await getApplied(client)
    const sql = readMigrationSql(file)

    if (applied.has(file.name)) {
      // Already applied: verify content hasn't drifted since apply time, then genuinely skip.
      // Never auto-re-apply, never silently continue past a mismatch (unless disclosed —
      // see assertAppliedHashMatches's own docstring for the exact, pinned exception).
      assertAppliedHashMatches(file, applied, sql, disclosures)
      continue
    }

    const sha256 = sha256Of(sql)

    await client.query('BEGIN')
    try {
      await client.query(sql)
      await client.query(
        'INSERT INTO _migrations_applied (filename, sha256) VALUES ($1, $2)',
        [file.name, sha256]
      )
      await client.query('COMMIT')
      ran.push(file.name)
    } catch (err) {
      await client.query('ROLLBACK')
      throw err
    }

    if (target && file.name === target) break
  }

  return ran
}

async function main(): Promise<void> {
  const args = process.argv.slice(2)
  const dryRun = args.includes('--dry-run')
  const targetIdx = args.indexOf('--target')
  const target = targetIdx !== -1 ? args[targetIdx + 1] : undefined

  const scriptDir = path.dirname(new URL(import.meta.url).pathname)
  const dirs = [
    path.resolve(scriptDir, '../migrations'),
    path.resolve(scriptDir, '../supabase/migrations'),
  ]

  const pool = new Pool({ connectionString: process.env.DATABASE_URL })
  const client = await pool.connect()
  try {
    const ran = await runMigrations(client, dirs, { dryRun, target })
    if (dryRun) {
      console.log('Dry run — would apply:')
      ran.forEach(name => console.log(`  ${name}`))
    } else {
      ran.forEach(name => console.log(`Applied: ${name}`))
    }
  } catch (err) {
    console.error('Migration failed:', err)
    process.exit(1)
  } finally {
    client.release()
    await pool.end()
  }
}

// Guard: only execute when run directly, not when imported by tests.
// Unguarded main() caused an unhandled rejection (ECONNREFUSED) in vitest
// because there is no database in the CI test environment.
if (process.env.NODE_ENV !== 'test') {
  main()
}
