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
 * - RENUMBER GUARD (Dvārapāla RULING 58 "Hazard 2", closed by SAMĀPTI): the tracker is keyed by
 *   FILENAME, so a migration RENUMBERED after being applied (467 -> 474, 456 -> 457) looks like a
 *   brand-new file under its new name and would be RE-APPLIED. Before applying any ostensibly-new
 *   migration the runner now checks whether its content is already recorded under a DIFFERENT
 *   filename — by exact sha256 AND by `sql_identity` (comment/whitespace-normalised content hash,
 *   because a renumber almost always rewrites the `-- Migration NNN:` header too, which defeats a
 *   raw-hash-only check). On a hit it throws MigrationRenumberedError and refuses to run, until an
 *   operator records an explicit reconciliation in
 *   `scripts/ci/migration_renumber_disclosed.json`. See assertNotRenumberedReapply() below.
 * - --dry-run flag: lists what would be applied; no writes. Still performs the hash comparison
 *   above so an operator finds out about drift from a preview, not only from a real run.
 * - --target <filename> flag: stops after that migration
 *
 * Connection: DATABASE_URL env var (Cloud SQL Auth Proxy in CI via WIF).
 */

import fs from 'fs'
import path from 'path'
import crypto from 'crypto'
import { fileURLToPath } from 'url'
import { Pool, type PoolClient } from 'pg'

export const TRACKER_DDL = `
CREATE TABLE IF NOT EXISTS _migrations_applied (
  id SERIAL PRIMARY KEY,
  filename TEXT UNIQUE NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sha256 TEXT NOT NULL
);
`

/**
 * Second, additive tracker DDL — the filename-independent content identity that makes the
 * renumber guard possible. Kept separate from TRACKER_DDL (which is `CREATE TABLE IF NOT
 * EXISTS` and therefore a no-op against the long-existing production table) so an already-
 * provisioned tracker actually gains the column. Nullable by design: rows applied before this
 * column existed have no identity until the opportunistic backfill fills them in, and rows whose
 * file is no longer on disk (or whose content has drifted past its recorded sha256) never can be
 * backfilled — an honest NULL, not a fabricated value (CLAUDE.md §N.8).
 *
 * This is runner-owned tracker DDL, NOT a numbered migration: `_migrations_applied` is the
 * runner's own bookkeeping table and has always been created/maintained here, never by a
 * migration file.
 */
export const TRACKER_IDENTITY_DDL = `
ALTER TABLE _migrations_applied ADD COLUMN IF NOT EXISTS sql_identity TEXT;
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
  /**
   * Renumber-reconciliation allowlist, keyed by the NEW filename. Defaults to loading
   * `scripts/ci/migration_renumber_disclosed.json` from disk. Tests pass an explicit map
   * (including an empty one) so the renumber guard is exercised deterministically.
   */
  renumberDisclosures?: Map<string, DisclosedRenumber>
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

/**
 * One itemized, dated, attributed reconciliation for a migration whose content is already
 * recorded in `_migrations_applied` under a DIFFERENT filename — i.e. a renumber. Same
 * discipline as DisclosedHashMismatch and `migration_number_guard.ts`'s DisclosedAddition:
 * every field is required, and the pin is exact (new name + old name + the `sql_identity` that
 * ties them together), so an entry can never become a standing "this file may re-run" exemption.
 *
 * `disposition` is the operator's actual answer to the question the guard asks:
 *  - `already-applied-under-old-name` — the SQL genuinely ran under `applied_filename`. The
 *    runner records `new_filename` as applied WITHOUT executing it. This is the correct
 *    disposition for a plain renumber and is what makes the guard non-blocking in practice.
 *  - `intentional-reapply` — the operator has confirmed the SQL is idempotent and re-running it
 *    under the new name is the intent. The runner executes it normally.
 */
export interface DisclosedRenumber {
  new_filename: string
  applied_filename: string
  sql_identity: string
  disposition: 'already-applied-under-old-name' | 'intentional-reapply'
  reason: string
  disclosed_via: string
  disclosed_on: string
}

interface RenumberDisclosureFile {
  entries: DisclosedRenumber[]
}

/** Repo-root-relative default path to the renumber-reconciliation allowlist. */
export function defaultRenumberDisclosurePath(): string {
  const scriptDir = path.dirname(new URL(import.meta.url).pathname)
  return path.join(scriptDir, 'ci', 'migration_renumber_disclosed.json')
}

const RENUMBER_DISPOSITIONS = new Set(['already-applied-under-old-name', 'intentional-reapply'])

/**
 * Load the renumber-reconciliation allowlist, keyed by the NEW filename. An entry missing a
 * required field (or carrying an unrecognised `disposition`) is dropped and warned about —
 * treated as UNDISCLOSED, exactly like loadHashDisclosures. Missing file -> empty map.
 */
export function loadRenumberDisclosures(
  filePath: string = defaultRenumberDisclosurePath()
): Map<string, DisclosedRenumber> {
  const out = new Map<string, DisclosedRenumber>()
  let raw: string
  try {
    raw = fs.readFileSync(filePath, 'utf8')
  } catch {
    return out
  }
  const parsed = JSON.parse(raw) as RenumberDisclosureFile
  for (const entry of parsed.entries ?? []) {
    const missing: string[] = []
    if (!entry.new_filename) missing.push('new_filename')
    if (!entry.applied_filename) missing.push('applied_filename')
    if (!entry.sql_identity) missing.push('sql_identity')
    if (!entry.disposition || !RENUMBER_DISPOSITIONS.has(entry.disposition)) {
      missing.push(`disposition (one of: ${[...RENUMBER_DISPOSITIONS].join(' | ')})`)
    }
    if (!entry.reason) missing.push('reason')
    if (!entry.disclosed_via) missing.push('disclosed_via')
    if (!entry.disclosed_on) missing.push('disclosed_on')
    if (missing.length > 0) {
      console.warn(
        `[migration-renumber-disclosure] entry for "${entry.new_filename ?? '(unknown)'}" is ` +
        `missing/invalid field(s): ${missing.join(', ')} — treated as UNDISCLOSED, not a partial pass.`
      )
      continue
    }
    out.set(entry.new_filename, entry)
  }
  return out
}

/**
 * Thrown when an ostensibly-NEW migration's content is already recorded as applied under a
 * DIFFERENT filename — the renumber hazard named in Dvārapāla RULING 58 and realised for real in
 * this repository twice (467 -> 474, and 456 -> 457 whose SQL genuinely executed twice, 1h49m
 * apart, undetected, surviving only because it happened to be idempotent).
 *
 * Never resolved automatically: re-applying could double-apply non-idempotent SQL, and silently
 * skipping could drop a genuinely-new migration that merely resembles an old one. The operator
 * records which it is in `scripts/ci/migration_renumber_disclosed.json`.
 */
export class MigrationRenumberedError extends Error {
  constructor(
    public readonly newFilename: string,
    public readonly appliedFilename: string,
    public readonly matchKind: 'sha256' | 'sql_identity',
    public readonly sqlIdentity: string
  ) {
    super(
      `Migration "${newFilename}" looks new (no row in _migrations_applied under that name), but its ` +
      `SQL content is ALREADY recorded as applied under a different filename: "${appliedFilename}".\n` +
      `  matched on:   ${matchKind === 'sha256'
        ? 'exact sha256 of the file content'
        : 'sql_identity (content with SQL comments stripped and whitespace normalised)'}\n` +
      `  sql_identity: ${sqlIdentity}\n` +
      `This is the renumbered-migration hazard: the tracker is keyed by FILENAME, so a migration that ` +
      `was applied as "${appliedFilename}" and then renumbered to "${newFilename}" would be RE-APPLIED — ` +
      `silently double-applying if the SQL is idempotent, and failing mid-deploy if it is not.\n` +
      `The runner will not guess. Record the reconciliation in ` +
      `platform/scripts/ci/migration_renumber_disclosed.json with one of:\n` +
      `  disposition "already-applied-under-old-name" — the SQL already ran as "${appliedFilename}"; ` +
      `record "${newFilename}" as applied WITHOUT executing it (the normal answer for a renumber).\n` +
      `  disposition "intentional-reapply" — the SQL is idempotent and re-running it under the new ` +
      `name is deliberate; execute it normally.`
    )
    this.name = 'MigrationRenumberedError'
  }
}

/**
 * Normalise SQL to a filename- and formatting-independent form: SQL comments removed, all
 * whitespace runs collapsed to a single space, trimmed. String literals are preserved exactly —
 * single-quoted literals (including the '' escape), double-quoted identifiers, and dollar-quoted
 * bodies ($$...$$ / $tag$...$tag$, as used by plpgsql function bodies) are copied verbatim, so a
 * `--` or `/*` inside a literal is never mistaken for a comment.
 *
 * Why comment-stripping and not a raw hash: verified empirically against this repo's own history.
 * The one production instance of the hazard — `456_lel_schema_v2_event_shapes.sql` renumbered to
 * `457_...` — rewrote the `-- Migration NNN:` header in the same commit, so the two files have
 * DIFFERENT sha256 values. A raw-content guard would not have caught the very defect it exists to
 * catch (CLAUDE.md §N.8: a detector must measure the claim it asserts). Normalised, the two files
 * are identical.
 */
export function normalizeSqlForIdentity(sql: string): string {
  const out: string[] = []
  let i = 0
  const n = sql.length
  while (i < n) {
    const c = sql[i]

    // -- line comment
    if (c === '-' && sql[i + 1] === '-') {
      while (i < n && sql[i] !== '\n') i++
      out.push(' ')
      continue
    }

    // /* block comment */ — Postgres allows nesting
    if (c === '/' && sql[i + 1] === '*') {
      let depth = 1
      i += 2
      while (i < n && depth > 0) {
        if (sql[i] === '/' && sql[i + 1] === '*') {
          depth++
          i += 2
        } else if (sql[i] === '*' && sql[i + 1] === '/') {
          depth--
          i += 2
        } else {
          i++
        }
      }
      out.push(' ')
      continue
    }

    // 'single-quoted literal' (with '' escape) and "double-quoted identifier" (with "" escape)
    if (c === "'" || c === '"') {
      const q = c
      out.push(q)
      i++
      while (i < n) {
        if (sql[i] === q) {
          if (sql[i + 1] === q) {
            out.push(q, q)
            i += 2
            continue
          }
          out.push(q)
          i++
          break
        }
        out.push(sql[i])
        i++
      }
      continue
    }

    // $tag$ dollar-quoted body $tag$
    if (c === '$') {
      let j = i + 1
      while (j < n && /[A-Za-z0-9_]/.test(sql[j])) j++
      if (j < n && sql[j] === '$') {
        const tag = sql.slice(i, j + 1)
        const end = sql.indexOf(tag, j + 1)
        if (end === -1) {
          out.push(sql.slice(i))
          i = n
          continue
        }
        out.push(sql.slice(i, end + tag.length))
        i = end + tag.length
        continue
      }
    }

    // whitespace run -> single space
    if (/\s/.test(c)) {
      while (i < n && /\s/.test(sql[i])) i++
      out.push(' ')
      continue
    }

    out.push(c)
    i++
  }
  return out.join('').split(/\s+/).filter(Boolean).join(' ')
}

/** Filename-independent, comment/whitespace-independent content identity for a migration. */
export function sqlIdentityOf(sql: string): string {
  return crypto.createHash('sha256').update(normalizeSqlForIdentity(sql)).digest('hex')
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

/** One `_migrations_applied` row, as the runner needs it. */
export interface AppliedMigration {
  /** sha256 of the exact file content recorded at apply time. */
  sha256: string
  /**
   * Comment/whitespace-normalised content identity, or null for rows applied before the column
   * existed whose content could not be backfilled (file gone from disk, or content drifted past
   * its recorded sha256 so we cannot honestly claim to know what ran).
   */
  sqlIdentity: string | null
}

/** Returns a map of filename -> applied-row facts, for every applied migration. */
async function getApplied(client: PoolClient): Promise<Map<string, AppliedMigration>> {
  const res = await client.query('SELECT filename, sha256, sql_identity FROM _migrations_applied')
  return new Map(
    res.rows.map((r: { filename: string; sha256: string; sql_identity?: string | null }) => [
      r.filename,
      { sha256: r.sha256, sqlIdentity: r.sql_identity ?? null },
    ])
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
  applied: Map<string, AppliedMigration>,
  sql: string,
  disclosures: Map<string, DisclosedHashMismatch> = new Map()
): void {
  const storedSha256 = applied.get(file.name)?.sha256
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
 * For a migration that is NOT in `_migrations_applied` under its own name, check whether its
 * content is already recorded under a DIFFERENT name — the renumber hazard.
 *
 * Two independent matches, both filename-blind:
 *   1. exact sha256 — catches a pure `git mv` with no content edit at all;
 *   2. sql_identity — catches the realistic case where the renumber also rewrote the
 *      `-- Migration NNN:` header comment (the 456 -> 457 instance in this repo's own history).
 *
 * Returns the disclosed reconciliation when one exactly pins this (new, applied, identity) triple,
 * so the caller can honour its `disposition`. Returns undefined when there is no renumber at all.
 * Throws MigrationRenumberedError when there IS a renumber and it has not been reconciled.
 */
function assertNotRenumberedReapply(
  file: MigrationFile,
  sql: string,
  applied: Map<string, AppliedMigration>,
  renumbers: Map<string, DisclosedRenumber> = new Map()
): DisclosedRenumber | undefined {
  const currentSha256 = sha256Of(sql)
  const currentIdentity = sqlIdentityOf(sql)

  let matchedFilename: string | undefined
  let matchKind: 'sha256' | 'sql_identity' | undefined

  for (const [appliedName, row] of applied) {
    if (appliedName === file.name) continue
    if (row.sha256 === currentSha256) {
      matchedFilename = appliedName
      matchKind = 'sha256'
      break // exact match is the strongest signal — stop here
    }
    if (row.sqlIdentity !== null && row.sqlIdentity === currentIdentity && !matchedFilename) {
      matchedFilename = appliedName
      matchKind = 'sql_identity'
      // keep scanning: an exact sha256 match elsewhere is a better explanation
    }
  }

  if (matchedFilename === undefined || matchKind === undefined) return undefined

  const disclosed = renumbers.get(file.name)
  if (
    disclosed &&
    disclosed.applied_filename === matchedFilename &&
    disclosed.sql_identity === currentIdentity
  ) {
    console.warn(
      `[migration-renumber-disclosure] "${file.name}" carries the same SQL as already-applied ` +
      `"${matchedFilename}" (matched on ${matchKind}) — this is a DISCLOSED renumber.\n` +
      `  disposition: ${disclosed.disposition}\n` +
      `  reason: ${disclosed.reason}\n` +
      `  disclosed via: ${disclosed.disclosed_via} on ${disclosed.disclosed_on}\n` +
      `  This disclosure pins ONE specific (new, applied, sql_identity) triple. If any of the ` +
      `three changes, the guard fails loudly again.`
    )
    return disclosed
  }

  throw new MigrationRenumberedError(file.name, matchedFilename, matchKind, currentIdentity)
}

/**
 * Opportunistic, idempotent backfill of `sql_identity` for rows applied before the column existed.
 *
 * ONLY backfills a row whose file is present on disk AND whose current content still hashes to the
 * sha256 recorded at apply time — i.e. where we can prove what actually ran. Rows whose file is
 * gone, or whose content has drifted (the disclosed-residual set), are left NULL rather than
 * stamped with an identity derived from content we cannot prove was the content applied.
 *
 * Without this, the renumber guard's `sql_identity` arm would be dead code against the existing
 * ~360-row tracker until every migration is re-applied — i.e. forever.
 */
async function backfillSqlIdentities(
  client: PoolClient,
  files: MigrationFile[],
  applied: Map<string, AppliedMigration>
): Promise<number> {
  let filled = 0
  for (const file of files) {
    const row = applied.get(file.name)
    if (!row || row.sqlIdentity !== null) continue
    let sql: string
    try {
      sql = readMigrationSql(file)
    } catch {
      continue
    }
    if (sha256Of(sql) !== row.sha256) continue // content drifted — cannot prove what ran
    await client.query(
      'UPDATE _migrations_applied SET sql_identity = $1 WHERE filename = $2 AND sql_identity IS NULL',
      [sqlIdentityOf(sql), file.name]
    )
    row.sqlIdentity = sqlIdentityOf(sql)
    filled++
  }
  return filled
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
  const renumbers = options.renumberDisclosures ?? loadRenumberDisclosures()

  await client.query(TRACKER_DDL)
  await client.query(TRACKER_IDENTITY_DDL)
  const files = collectMigrationFiles(dirs)

  if (dryRun) {
    const applied = await getApplied(client)
    for (const file of files) {
      if (applied.has(file.name)) {
        assertAppliedHashMatches(file, applied, readMigrationSql(file), disclosures)
        continue
      }
      // Surface a renumbered re-apply from the PREVIEW too, not only from a real run —
      // same reasoning as the dry-run hash check above it.
      assertNotRenumberedReapply(file, readMigrationSql(file), applied, renumbers)
    }
    return files.filter(f => !applied.has(f.name)).map(f => f.name)
  }

  // Fill in sql_identity for pre-existing rows we can prove the content of, so the renumber
  // guard has real coverage over the existing tracker rather than only over future applies.
  const filled = await backfillSqlIdentities(client, files, await getApplied(client))
  if (filled > 0) {
    console.log(`[migration-identity-backfill] recorded sql_identity for ${filled} previously-applied migration(s).`)
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

    // Looks new by filename — but is it? Throws unless this is genuinely new content, or a
    // renumber that an operator has explicitly reconciled.
    const disclosedRenumber = assertNotRenumberedReapply(file, sql, applied, renumbers)

    const sha256 = sha256Of(sql)
    const identity = sqlIdentityOf(sql)

    if (disclosedRenumber?.disposition === 'already-applied-under-old-name') {
      // The SQL genuinely ran under the old filename. Record the new name as applied WITHOUT
      // executing it — the whole point of the guard is that this SQL must not run twice.
      await client.query(
        'INSERT INTO _migrations_applied (filename, sha256, sql_identity) VALUES ($1, $2, $3)',
        [file.name, sha256, identity]
      )
      console.log(
        `Reconciled (not executed): ${file.name} — already applied as ` +
        `${disclosedRenumber.applied_filename}`
      )
      if (target && file.name === target) break
      continue
    }

    await client.query('BEGIN')
    try {
      await client.query(sql)
      await client.query(
        'INSERT INTO _migrations_applied (filename, sha256, sql_identity) VALUES ($1, $2, $3)',
        [file.name, sha256, identity]
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

/**
 * The one token a deploy step can grep for to assert the migrator reached the end of its work.
 *
 * It is deliberately a distinctive constant rather than prose: a log-scraping assertion that
 * matches on wording breaks the first time the wording is improved, and the temptation is then
 * to relax the assertion rather than fix it.
 */
export const MIGRATE_COMPLETION_SENTINEL = 'MIGRATE_RUNNER_COMPLETE'

/** What one run did, MEASURED after the run rather than inferred from the absence of output. */
export interface MigrationRunSummary {
  mode: 'apply' | 'dry-run'
  /** `.sql` files found across the configured migration directories. */
  filesOnDisk: number
  /** Rows in `_migrations_applied` — includes rows for files no longer on disk. */
  ledgerRows: number
  /** On-disk files the ledger records as applied. `filesOnDisk - pending`, by construction. */
  onDiskApplied: number
  pending: number
  pendingNames: string[]
  appliedThisRun: number
  appliedNames: string[]
}

/**
 * Measure the post-run state so the run can state its result instead of implying it.
 *
 * Everything here is queried or counted after the fact — nothing is derived by arithmetic from
 * what the run *thought* it was doing, because that arithmetic is exactly the inference this
 * exists to replace (a reconciled-not-executed row, for instance, never appears in `ran`).
 * Read-only: one directory scan and one SELECT.
 */
export async function summarizeMigrationRun(
  client: PoolClient,
  dirs: string[],
  ran: string[],
  options: { dryRun?: boolean } = {}
): Promise<MigrationRunSummary> {
  const dryRun = options.dryRun ?? false
  const files = collectMigrationFiles(dirs)
  const applied = await getApplied(client)
  const pendingNames = files.filter(f => !applied.has(f.name)).map(f => f.name)
  return {
    mode: dryRun ? 'dry-run' : 'apply',
    filesOnDisk: files.length,
    ledgerRows: applied.size,
    onDiskApplied: files.length - pendingNames.length,
    pending: pendingNames.length,
    pendingNames,
    appliedThisRun: dryRun ? 0 : ran.length,
    appliedNames: dryRun ? [] : [...ran],
  }
}

/** Keep a name list readable in a CI log without hiding that it was truncated. */
function nameList(names: string[], limit = 10): string {
  if (names.length <= limit) return names.join(', ')
  return `${names.slice(0, limit).join(', ')}, … and ${names.length - limit} more`
}

/**
 * Render the summary as the lines a run prints unconditionally on its success path.
 *
 * Nirmāṇa M0-T44 / SQ-08, from V-3's residual RES-1 and ruling D-18 part 2. Before this, the
 * success path printed NOTHING when nothing was pending — `ran.forEach(...)` over an empty
 * array — so `.github/workflows/deploy.yml`'s unasserted `npx tsx scripts/migrate.ts` produced
 * byte-identical output (none, exit 0) for two different states: "everything was already
 * applied" and "the migrator never ran". CLAUDE.md §N.4 names the second as the real hazard
 * behind its own doctrine; §N.8 names the shape — a success signal whose detector cannot tell
 * "the work was unnecessary" from "the work never happened".
 *
 * So the counts here are not decoration. They are the claim's evidence, and they are
 * self-checking: `files_on_disk - on_disk_applied` must equal `pending`, and a reader who
 * distrusts the sentence can count the `.sql` files and the ledger rows themselves.
 */
export function formatMigrationSummary(s: MigrationRunSummary): string[] {
  const lines: string[] = [
    `[migrate] ${s.filesOnDisk} migration file(s) on disk; ${s.onDiskApplied} of them recorded ` +
    `in _migrations_applied (${s.ledgerRows} ledger row(s) in total, including any whose file ` +
    `is no longer on disk); ${s.pending} pending; ${s.appliedThisRun} applied by this run.`,
  ]

  if (s.filesOnDisk === 0) {
    // Never dress up "I looked at nothing" as "everything is applied".
    lines.push(
      '[migrate] No migration files were found in the configured directories. This is a ' +
      'configuration result, not an up-to-date result — nothing was checked.'
    )
  } else if (s.mode === 'dry-run') {
    lines.push(
      s.pending === 0
        ? '[migrate] Dry run: nothing would be applied — every migration on disk is already ' +
          'recorded as applied.'
        : `[migrate] Dry run: ${s.pending} migration(s) would be applied — ${nameList(s.pendingNames)}.`
    )
  } else if (s.appliedThisRun === 0 && s.pending === 0) {
    lines.push(
      '[migrate] Nothing to apply — every migration on disk is already recorded as applied. ' +
      'This run reached the end of its work; the result is asserted here rather than inferred ' +
      'from an absence of output.'
    )
  } else if (s.pending === 0) {
    lines.push(`[migrate] Applied ${s.appliedThisRun} migration(s); nothing left pending.`)
  } else {
    lines.push(
      `[migrate] Applied ${s.appliedThisRun} migration(s); ${s.pending} still pending ` +
      `(${nameList(s.pendingNames)}) — expected only when --target stopped the run early.`
    )
  }

  // Terminal, and last: a log cut short before this line cannot show it.
  lines.push(
    `[migrate] ${MIGRATE_COMPLETION_SENTINEL} mode=${s.mode} files_on_disk=${s.filesOnDisk} ` +
    `ledger_rows=${s.ledgerRows} on_disk_applied=${s.onDiskApplied} pending=${s.pending} ` +
    `applied_this_run=${s.appliedThisRun}`
  )
  return lines
}

/**
 * Everything `main()` does once it holds a client: run the migrations, then report.
 *
 * Extracted from `main()` so the reporting has a real detector behind it — `main()` builds its
 * own Pool from DATABASE_URL and is therefore untestable without a database, which is precisely
 * how the silent success path went unnoticed. This throws on failure exactly as `runMigrations`
 * does; the sentinel is printed only after the run returns, so a failed run cannot emit it.
 */
export async function runCli(
  client: PoolClient,
  dirs: string[],
  options: RunOptions = {},
  log: (line: string) => void = console.log
): Promise<MigrationRunSummary> {
  const dryRun = options.dryRun ?? false
  const ran = await runMigrations(client, dirs, options)

  if (dryRun) {
    log('Dry run — would apply:')
    ran.forEach(name => log(`  ${name}`))
  } else {
    ran.forEach(name => log(`Applied: ${name}`))
  }

  const summary = await summarizeMigrationRun(client, dirs, ran, { dryRun })
  for (const line of formatMigrationSummary(summary)) log(line)
  return summary
}

/**
 * Prefix on every line this runner relays from the server. Deliberately distinct from
 * `MIGRATE_COMPLETION_SENTINEL` and from `[migrate]`, so a relayed line can never be mistaken
 * for — or matched by a grep looking for — the runner's own completion assertion.
 */
export const PG_NOTICE_PREFIX = '[migrate:pg]'

/**
 * The subset of `pg`'s `NoticeMessage` this runner relays. Structural, not nominal, so the
 * formatter is testable without constructing a real protocol message.
 */
export interface ServerNoticeLike {
  severity?: string | undefined
  message?: string | undefined
  code?: string | undefined
  detail?: string | undefined
  hint?: string | undefined
  where?: string | undefined
}

/**
 * Render the line breaks inside one server-controlled string as their two-character escapes,
 * so relayed text CANNOT SYNTHESISE A LINE BOUNDARY in the log it is relayed into.
 *
 * Why this is not cosmetic (Nirmāṇa D-65, demonstrated at M0-T57): the deploy step tees this
 * runner's combined output to `/tmp/migrate.log` and asserts the run completed by grepping for
 * `^\[migrate\] MIGRATE_RUNNER_COMPLETE`. `message`/`detail`/`hint`/`where` are written by
 * whoever wrote the migration's `RAISE NOTICE`, and were relayed verbatim — so a notice
 * containing a newline emitted a SECOND PHYSICAL LINE beginning with the runner's own prefix,
 * byte-shaped exactly like the runner's own completion claim. Anchoring the grep (M0-T57) closed
 * the single-line case only: an anchor pins the start of a line, it cannot tell you who created
 * the line boundary. This is the emitter-side close of that residual.
 *
 * ESCAPE, NOT STRIP, and deliberately so: F-A's `there is already a transaction in progress`
 * warnings are the reason the relay exists at all (D-58), PostgreSQL genuinely emits multi-line
 * `detail` and `where` (PL/pgSQL context stacks especially), and a warning truncated at its first
 * newline would trade a forgery hole for an observability one. Every byte of the server's text
 * survives; only its ability to end a log line does not.
 *
 * Pure and total — no I/O, no throw — so it has a real unit-level detector (CLAUDE.md §N.8).
 */
export function escapeRelayedLineBreaks(value: string): string {
  return value.replace(/\r/g, '\\r').replace(/\n/g, '\\n')
}

/** One log line for one server notice. Pure — no I/O, so it has a real unit-level detector. */
export function formatServerNotice(notice: ServerNoticeLike | null | undefined): string {
  // EVERY interpolated field below is server-controlled, so every one of them is escaped —
  // escaping `message` alone would leave the same hole open one field to the right.
  const esc = (value: string): string => escapeRelayedLineBreaks(value)
  const severity = esc(notice?.severity ?? 'NOTICE')
  const message = esc(notice?.message ?? '(no message)')
  const extras: string[] = []
  if (notice?.code) extras.push(`code=${esc(notice.code)}`)
  if (notice?.detail) extras.push(`detail=${esc(notice.detail)}`)
  if (notice?.hint) extras.push(`hint=${esc(notice.hint)}`)
  if (notice?.where) extras.push(`where=${esc(notice.where)}`)
  const tail = extras.length > 0 ? ` (${extras.join('; ')})` : ''
  return `${PG_NOTICE_PREFIX} ${severity}: ${message}${tail}`
}

/**
 * Relay every server NOTICE/WARNING this connection receives to STDERR.
 *
 * Until this existed, `main()` built its pool and never attached a `notice` listener, so
 * node-postgres dropped every `RAISE NOTICE` and every server WARNING on the floor: a migration
 * that self-verifies, run by a runner that discards the self-verification, leaves an operator
 * unable to tell "the detector ran and was green" from "there is no detector" — only
 * `RAISE EXCEPTION` survived (CLAUDE.md §N.8 at the transport layer; Nirmāṇa D-58).
 *
 * STDERR, not stdout, and never the `log` channel: the deploy step greps its combined log for
 * `MIGRATE_COMPLETION_SENTINEL`, and relayed server text must be incapable of being read as the
 * runner's own completion claim.
 *
 * The handler cannot throw: an exception raised inside an EventEmitter callback would surface as
 * an uncaught exception and kill a migration run, which would make an observability change into
 * a correctness hazard. It reports transaction state nowhere and changes nothing about how this
 * runner opens, commits or rolls back anything.
 */
export function attachNoticeListener(
  client: { on(event: 'notice', listener: (notice: ServerNoticeLike) => void): unknown },
  emit: (line: string) => void = line => console.error(line)
): void {
  client.on('notice', notice => {
    try {
      emit(formatServerNotice(notice))
    } catch {
      /* never let relaying a diagnostic break the run it is describing */
    }
  })
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
  attachNoticeListener(client)
  try {
    await runCli(client, dirs, { dryRun, target })
  } catch (err) {
    console.error('Migration failed:', err)
    process.exit(1)
  } finally {
    client.release()
    await pool.end()
  }
}

/**
 * Is THIS module the process entrypoint, or was it merely imported by something else?
 *
 * Exported so the question has a real, directly-testable detector behind it rather than an
 * inline expression nothing can exercise (CLAUDE.md §N.8).
 *
 * Compares the module's own URL against `process.argv[1]`, the path the runtime was told to
 * execute. Both sides are normalised through `fs.realpathSync` where possible, so a symlinked
 * checkout, a `./`-prefixed spelling, or a `/tmp` → `/private/tmp` style realpath difference
 * does not make a direct run look like an import. Any failure to resolve either side answers
 * `false`: the safe direction is "assume imported", because a wrongly-false answer makes an
 * explicit `npx tsx scripts/migrate.ts` exit silently and loudly wrong, while a wrongly-true
 * answer applies migrations to production as an import side effect.
 */
export function isDirectEntrypoint(moduleUrl: string, argv1: string | undefined): boolean {
  if (!argv1) return false
  let modulePath: string
  try {
    modulePath = fileURLToPath(moduleUrl)
  } catch {
    return false
  }
  const entryPath = path.resolve(argv1)
  if (modulePath === entryPath) return true
  try {
    return fs.realpathSync(modulePath) === fs.realpathSync(entryPath)
  } catch {
    return false
  }
}

// Guard: only execute when this module IS the entrypoint — never as an import side effect.
//
// This used to read `if (process.env.NODE_ENV !== 'test')`, which asks the wrong question
// (Nirmāṇa finding F-2, WORK_QUEUE M0-T11). An environment sentinel says nothing about how the
// module was loaded: in ANY shell with NODE_ENV unset — which is every ordinary developer and
// agent shell — importing one of this module's pure helpers (`sqlIdentityOf`,
// `normalizeSqlForIdentity`, `collectMigrationFiles`; `scripts/ci/migration_renumber_disclosed.json`
// documents exactly such an import as the supported way to compute a sql_identity) ran the whole
// migrator. With DATABASE_URL exported, an `import` applied every unapplied migration to
// production. A KĀRAKA agent tripped this; nothing was applied only because that shell happened
// to have no DATABASE_URL and the fallback connection was refused.
//
// The entrypoint check answers the actual question and is environment-independent, so the test
// suite no longer relies on vitest happening to set NODE_ENV either. Both directions are covered
// by `scripts/__tests__/migrate_entrypoint_guard.test.ts`.
if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  main()
}
