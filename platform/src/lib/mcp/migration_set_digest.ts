/**
 * migration_set_digest.ts — a digest of the applied-migration ledger, for the MCP service's /health.
 *
 * The amjis-mcp service holds no database connection (see register_gochara_windows.ts, DB ACCESS NOTE), so the
 * ledger is read here, in the platform, and served to it over the internal-token route
 * `GET /api/mcp/health/migrations`. Only `_migrations_applied.filename` is selected: no sha256, no applied_at,
 * no row id leaves the database through this path.
 *
 * Digest (what the KĀLA-YANTRA http_probe records as `migration_set`): sha256 over the UTF-8 bytes of every
 * applied filename, sorted by code point (filenames are ASCII), each followed by one LF. Anyone holding the
 * ledger's filename list can recompute it with `LC_ALL=C sort | sha256sum`.
 *
 * Unavailable is an honest null with a named reason (CLAUDE.md §N.7.6): an unreadable or empty ledger never
 * becomes an empty-set digest, which would read as "no migrations applied".
 */
import { createHash } from 'node:crypto'

export const MIGRATION_LEDGER_SQL = 'SELECT filename FROM _migrations_applied'

export const MIGRATION_SET_ALGORITHM = 'sha256 of the applied filenames sorted by code point, each followed by LF'

export interface MigrationSetDigest {
  count: number
  sha256: string
  algorithm: string
}

export type MigrationSetRead =
  | { ok: true; migration_set: MigrationSetDigest }
  | { ok: false; reason: string }

export function digestMigrationFilenames(filenames: readonly string[]): MigrationSetDigest {
  const sorted = [...filenames].sort()
  const hash = createHash('sha256')
  for (const name of sorted) hash.update(`${name}\n`, 'utf8')
  return { count: sorted.length, sha256: hash.digest('hex'), algorithm: MIGRATION_SET_ALGORITHM }
}

/** `run` executes the one fixed statement; it is injected so the digest logic needs no database to be tested. */
export async function readMigrationSet(
  run: (sql: string) => Promise<{ rows: Array<Record<string, unknown>> }>,
): Promise<MigrationSetRead> {
  let rows: Array<Record<string, unknown>>
  try {
    rows = (await run(MIGRATION_LEDGER_SQL)).rows
  } catch (err) {
    // The error class only: a driver message can carry a host or a role name.
    const kind = err instanceof Error ? err.constructor.name : typeof err
    return { ok: false, reason: `ledger_unreadable: the _migrations_applied query failed (${kind})` }
  }
  const filenames = rows.map((row) => row['filename'])
  if (filenames.length === 0) {
    return { ok: false, reason: 'ledger_empty: _migrations_applied has no rows' }
  }
  if (!filenames.every((name): name is string => typeof name === 'string' && name.length > 0)) {
    return { ok: false, reason: 'ledger_malformed: a _migrations_applied row has no filename' }
  }
  return { ok: true, migration_set: digestMigrationFilenames(filenames) }
}
