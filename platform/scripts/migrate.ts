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
 * Throws MigrationHashMismatchError on mismatch. Returns nothing on match (or if not applied
 * yet) — the caller decides what to do next (skip vs. apply).
 */
function assertAppliedHashMatches(
  file: MigrationFile,
  applied: Map<string, string>,
  sql: string
): void {
  const storedSha256 = applied.get(file.name)
  if (storedSha256 === undefined) return // not applied yet — nothing to compare
  const currentSha256 = sha256Of(sql)
  if (currentSha256 !== storedSha256) {
    throw new MigrationHashMismatchError(file.name, storedSha256, currentSha256)
  }
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

  await client.query(TRACKER_DDL)
  const files = collectMigrationFiles(dirs)

  if (dryRun) {
    const applied = await getApplied(client)
    for (const file of files) {
      if (!applied.has(file.name)) continue
      assertAppliedHashMatches(file, applied, readMigrationSql(file))
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
      // Never auto-re-apply, never silently continue past a mismatch.
      assertAppliedHashMatches(file, applied, sql)
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
