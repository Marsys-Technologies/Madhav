/**
 * Idempotent migration runner.
 * - Reads platform/migrations/*.sql and platform/supabase/migrations/*.sql
 * - Tracks applied migrations in _migrations_applied (id, filename, applied_at, sha256)
 * - For each unapplied migration in lexical order:
 *     BEGIN; <SQL>; INSERT INTO _migrations_applied; COMMIT;
 *   On any error: ROLLBACK and exit non-zero
 * - --dry-run flag: lists what would be applied; no writes
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

async function getApplied(client: PoolClient): Promise<Set<string>> {
  const res = await client.query('SELECT filename FROM _migrations_applied')
  return new Set(res.rows.map((r: { filename: string }) => r.filename))
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
  const applied = await getApplied(client)
  const files = collectMigrationFiles(dirs)
  const pending = files.filter(f => !applied.has(f.name))

  if (dryRun) {
    return pending.map(f => f.name)
  }

  const ran: string[] = []
  for (const file of pending) {
    const sql = fs.readFileSync(path.join(file.dir, file.name), 'utf8')
    const sha256 = crypto.createHash('sha256').update(sql).digest('hex')

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

main()
