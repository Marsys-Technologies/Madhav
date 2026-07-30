import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import fs from 'fs'
import os from 'os'
import path from 'path'
import crypto from 'crypto'
import type { PoolClient } from 'pg'

import {
  TRACKER_DDL,
  collectMigrationFiles,
  runMigrations,
  MigrationHashMismatchError,
  MigrationRenumberedError,
  loadHashDisclosures,
  loadRenumberDisclosures,
  normalizeSqlForIdentity,
  sqlIdentityOf,
  type DisclosedHashMismatch,
  type DisclosedRenumber,
} from '../migrate'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function tmpDir(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'migrate-test-'))
}

function writeSql(dir: string, name: string, sql: string): string {
  const file = path.join(dir, name)
  fs.writeFileSync(file, sql, 'utf8')
  return file
}

/** Same hash function migrate.ts uses — kept independent so a test never accidentally passes
 *  by importing the implementation's own helper. */
function sha256(sql: string): string {
  return crypto.createHash('sha256').update(sql).digest('hex')
}

interface AppliedRow {
  filename: string
  sha256: string
  /** Comment/whitespace-normalised identity, as the tracker's sql_identity column holds it. */
  sql_identity?: string | null
}

/** Build a mock PoolClient that records all query calls */
function makeClient(applied: AppliedRow[] = [], failOn?: string) {
  const queries: Array<{ text: string; values?: unknown[] }> = []

  const client = {
    query: vi.fn(async (text: string, values?: unknown[]) => {
      const q = typeof text === 'string' ? text.trim() : text
      queries.push({ text: q, values })

      // Simulate tracker creation + the additive sql_identity column
      if (q.includes('CREATE TABLE IF NOT EXISTS _migrations_applied')) {
        return { rows: [] }
      }
      if (q.includes('ADD COLUMN IF NOT EXISTS sql_identity')) {
        return { rows: [] }
      }

      // Simulate the sql_identity backfill writing through to the in-memory tracker
      if (q.includes('UPDATE _migrations_applied SET sql_identity')) {
        const [identity, filename] = (values ?? []) as [string, string]
        const row = applied.find(r => r.filename === filename)
        if (row && (row.sql_identity ?? null) === null) row.sql_identity = identity
        return { rows: [] }
      }

      // Return applied list (filename + sha256 + sql_identity, per the tracker schema)
      if (q.includes('SELECT filename, sha256, sql_identity FROM _migrations_applied')) {
        return {
          rows: applied.map(({ filename, sha256, sql_identity }) => ({
            filename,
            sha256,
            sql_identity: sql_identity ?? null,
          })),
        }
      }

      // Simulate failure on a specific query
      if (failOn && q.toLowerCase().startsWith(failOn.toLowerCase())) {
        throw new Error(`Simulated failure on: ${failOn}`)
      }

      return { rows: [] }
    }),
    release: vi.fn(),
  } as unknown as PoolClient & { queries: typeof queries }

  // Attach for inspection
  ;(client as any).queries = queries
  return client
}

// ─── collectMigrationFiles ────────────────────────────────────────────────────

describe('collectMigrationFiles', () => {
  let dir: string

  beforeEach(() => {
    dir = tmpDir()
  })

  afterEach(() => {
    fs.rmSync(dir, { recursive: true, force: true })
  })

  it('returns files sorted lexically by name across dirs', () => {
    writeSql(dir, '002_b.sql', 'SELECT 2')
    writeSql(dir, '001_a.sql', 'SELECT 1')
    const files = collectMigrationFiles([dir])
    expect(files.map(f => f.name)).toEqual(['001_a.sql', '002_b.sql'])
  })

  it('merges and sorts across multiple dirs', () => {
    const dir2 = tmpDir()
    writeSql(dir, '003_c.sql', 'SELECT 3')
    writeSql(dir2, '001_a.sql', 'SELECT 1')
    try {
      const files = collectMigrationFiles([dir, dir2])
      expect(files.map(f => f.name)).toEqual(['001_a.sql', '003_c.sql'])
    } finally {
      fs.rmSync(dir2, { recursive: true, force: true })
    }
  })

  it('skips non-existent dirs', () => {
    const files = collectMigrationFiles(['/no/such/dir'])
    expect(files).toHaveLength(0)
  })
})

// ─── runMigrations ────────────────────────────────────────────────────────────

describe('runMigrations', () => {
  let dir: string

  beforeEach(() => {
    dir = tmpDir()
  })

  afterEach(() => {
    fs.rmSync(dir, { recursive: true, force: true })
  })

  it('bootstrap creates tracker table', async () => {
    const client = makeClient()
    await runMigrations(client, [dir])

    const ddlCall = (client as any).queries.find((q: any) =>
      q.text.includes('CREATE TABLE IF NOT EXISTS _migrations_applied')
    )
    expect(ddlCall).toBeDefined()
  })

  it('skips already-applied migrations whose hash still matches', async () => {
    const sqlOne = 'CREATE TABLE t1 (id INT)'
    writeSql(dir, '001_first.sql', sqlOne)
    writeSql(dir, '002_second.sql', 'CREATE TABLE t2 (id INT)')

    // 001 already applied, with the sha256 that matches its current on-disk content
    const client = makeClient([{ filename: '001_first.sql', sha256: sha256(sqlOne) }])
    const ran = await runMigrations(client, [dir])

    expect(ran).toEqual(['002_second.sql'])
    // Should NOT have a BEGIN for 001
    const beginCalls = (client as any).queries.filter((q: any) => q.text === 'BEGIN')
    expect(beginCalls).toHaveLength(1)
  })

  it('applies new migrations in lexical order', async () => {
    writeSql(dir, '002_b.sql', 'SELECT 2')
    writeSql(dir, '001_a.sql', 'SELECT 1')

    const client = makeClient()
    const ran = await runMigrations(client, [dir])

    expect(ran).toEqual(['001_a.sql', '002_b.sql'])
  })

  it('rolls back and throws on SQL failure', async () => {
    const sqlOk = 'SELECT 1'
    writeSql(dir, '001_ok.sql', sqlOk)
    writeSql(dir, '002_bad.sql', 'BOOM')

    // Fail when running the actual migration SQL for 002_bad
    const client = makeClient(
      [{ filename: '001_ok.sql', sha256: sha256(sqlOk) }],
      'BOOM'
    )

    await expect(runMigrations(client, [dir])).rejects.toThrow('Simulated failure')

    const rollbackCall = (client as any).queries.find((q: any) => q.text === 'ROLLBACK')
    expect(rollbackCall).toBeDefined()
  })

  it('dry-run returns pending list without writing', async () => {
    const sqlA = 'SELECT 1'
    writeSql(dir, '001_a.sql', sqlA)
    writeSql(dir, '002_b.sql', 'SELECT 2')

    const client = makeClient([{ filename: '001_a.sql', sha256: sha256(sqlA) }])
    const pending = await runMigrations(client, [dir], { dryRun: true })

    expect(pending).toEqual(['002_b.sql'])

    // No BEGIN / COMMIT / INSERT should have been called
    const writes = (client as any).queries.filter((q: any) =>
      ['BEGIN', 'COMMIT', 'ROLLBACK'].includes(q.text) ||
      q.text.includes('INSERT INTO _migrations_applied')
    )
    expect(writes).toHaveLength(0)
  })

  it('stops after --target migration', async () => {
    writeSql(dir, '001_a.sql', 'SELECT 1')
    writeSql(dir, '002_b.sql', 'SELECT 2')
    writeSql(dir, '003_c.sql', 'SELECT 3')

    const client = makeClient()
    const ran = await runMigrations(client, [dir], { target: '002_b.sql' })

    expect(ran).toEqual(['001_a.sql', '002_b.sql'])
    expect(ran).not.toContain('003_c.sql')
  })

  // ─── RULING 58: sha256 mismatch on an already-applied migration ────────────

  it('fails loudly (does not skip, does not re-apply) when an already-applied migration was edited', async () => {
    const originalSql = 'CREATE TABLE t1 (id INT)'
    const editedSql = 'CREATE TABLE t1 (id INT, name TEXT)'
    writeSql(dir, '001_first.sql', editedSql) // file on disk has been edited...

    // ...but the tracker recorded the hash of the ORIGINAL content at apply time
    const client = makeClient([{ filename: '001_first.sql', sha256: sha256(originalSql) }])

    await expect(runMigrations(client, [dir])).rejects.toThrow(MigrationHashMismatchError)
    await expect(runMigrations(client, [dir])).rejects.toThrow('001_first.sql')

    // Never re-applied: no BEGIN/COMMIT/INSERT should have been issued for it
    const writes = (client as any).queries.filter((q: any) =>
      ['BEGIN', 'COMMIT'].includes(q.text) || q.text.includes('INSERT INTO _migrations_applied')
    )
    expect(writes).toHaveLength(0)
  })

  it('mismatch error names both the stored and current sha256', async () => {
    const originalSql = 'SELECT 1'
    const editedSql = 'SELECT 2'
    writeSql(dir, '001_a.sql', editedSql)

    const storedHash = sha256(originalSql)
    const currentHash = sha256(editedSql)
    const client = makeClient([{ filename: '001_a.sql', sha256: storedHash }])

    try {
      await runMigrations(client, [dir])
      expect.unreachable('expected runMigrations to throw')
    } catch (err) {
      expect(err).toBeInstanceOf(MigrationHashMismatchError)
      const mismatch = err as MigrationHashMismatchError
      expect(mismatch.filename).toBe('001_a.sql')
      expect(mismatch.storedSha256).toBe(storedHash)
      expect(mismatch.currentSha256).toBe(currentHash)
      expect(mismatch.message).toContain(storedHash)
      expect(mismatch.message).toContain(currentHash)
    }
  })

  it('does not throw when a later migration is unrelated to an earlier, unchanged one', async () => {
    const sqlOne = 'CREATE TABLE t1 (id INT)'
    writeSql(dir, '001_first.sql', sqlOne)
    writeSql(dir, '002_second.sql', 'CREATE TABLE t2 (id INT)')
    writeSql(dir, '003_third.sql', 'CREATE TABLE t3 (id INT)')

    const client = makeClient([
      { filename: '001_first.sql', sha256: sha256(sqlOne) },
      { filename: '002_second.sql', sha256: sha256('CREATE TABLE t2 (id INT)') },
    ])
    const ran = await runMigrations(client, [dir])

    expect(ran).toEqual(['003_third.sql'])
  })

  it('dry-run also fails loudly on hash drift instead of silently reporting nothing pending', async () => {
    const originalSql = 'SELECT 1'
    const editedSql = 'SELECT 1 -- edited'
    writeSql(dir, '001_a.sql', editedSql)

    const client = makeClient([{ filename: '001_a.sql', sha256: sha256(originalSql) }])

    await expect(runMigrations(client, [dir], { dryRun: true })).rejects.toThrow(
      MigrationHashMismatchError
    )
  })

  // ─── RULING 73: disclosed-residual allowlist for known historical sha256 mismatches ──────

  function disclosureFor(
    filename: string,
    storedSha256: string,
    currentSha256: string,
    overrides: Partial<DisclosedHashMismatch> = {}
  ): Map<string, DisclosedHashMismatch> {
    return new Map([
      [
        filename,
        {
          filename,
          stored_sha256: storedSha256,
          current_sha256_at_disclosure: currentSha256,
          cause: 'test cause',
          disclosed_via: 'DVA RULING 73',
          fixed_by_samapti: false,
          ...overrides,
        },
      ],
    ])
  }

  it('(a) disclosed mismatch with the exact pinned pair warns and is treated as a skip, not fatal', async () => {
    const storedSql = 'CREATE TABLE t1 (id INT)'
    const currentSql = 'CREATE TABLE t1 (id INT, extra TEXT)' // edited after apply — the known drift
    writeSql(dir, '001_first.sql', currentSql)

    const storedHash = sha256(storedSql)
    const currentHash = sha256(currentSql)
    const client = makeClient([{ filename: '001_first.sql', sha256: storedHash }])
    const disclosures = disclosureFor('001_first.sql', storedHash, currentHash)

    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    try {
      const ran = await runMigrations(client, [dir], { disclosures })
      expect(ran).toEqual([]) // genuinely skipped, not (re-)applied
      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining('[migration-hash-disclosure]')
      )
      expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('001_first.sql'))
    } finally {
      warnSpy.mockRestore()
    }

    // Never (re-)applied: no BEGIN/COMMIT/INSERT should have been issued for it
    const writes = (client as any).queries.filter((q: any) =>
      ['BEGIN', 'COMMIT'].includes(q.text) || q.text.includes('INSERT INTO _migrations_applied')
    )
    expect(writes).toHaveLength(0)
  })

  it('(b) an undisclosed mismatch still fails loudly even when a disclosures map is present for OTHER files', async () => {
    const storedSql = 'CREATE TABLE t1 (id INT)'
    const editedSql = 'CREATE TABLE t1 (id INT, extra TEXT)'
    writeSql(dir, '001_undisclosed.sql', editedSql)

    const client = makeClient([{ filename: '001_undisclosed.sql', sha256: sha256(storedSql) }])
    // Disclosures map is non-empty but does NOT contain '001_undisclosed.sql' — same as a
    // 17th, never-disclosed mismatch landing alongside 16 legitimately disclosed ones.
    const disclosures = disclosureFor(
      'some_other_disclosed_file.sql',
      sha256('unrelated'),
      sha256('unrelated-edited')
    )

    await expect(runMigrations(client, [dir], { disclosures })).rejects.toThrow(
      MigrationHashMismatchError
    )
    await expect(runMigrations(client, [dir], { disclosures })).rejects.toThrow(
      '001_undisclosed.sql'
    )
  })

  it('(c) a disclosed file edited AGAIN past its pinned current hash still fails loudly — disclosure is not a standing exemption', async () => {
    const storedSql = 'CREATE TABLE t1 (id INT)'
    const disclosedCurrentSql = 'CREATE TABLE t1 (id INT, extra TEXT)' // the pinned "current" at disclosure time
    const editedAgainSql = 'CREATE TABLE t1 (id INT, extra TEXT, yet_another TEXT)' // edited AFTER disclosure

    writeSql(dir, '001_first.sql', editedAgainSql) // on-disk content has moved past the pin

    const storedHash = sha256(storedSql)
    const client = makeClient([{ filename: '001_first.sql', sha256: storedHash }])
    // Disclosure pins (stored, disclosedCurrent) — NOT (stored, editedAgain)
    const disclosures = disclosureFor(
      '001_first.sql',
      storedHash,
      sha256(disclosedCurrentSql)
    )

    await expect(runMigrations(client, [dir], { disclosures })).rejects.toThrow(
      MigrationHashMismatchError
    )

    // Confirm the thrown error carries the CURRENT (post-second-edit) hash, not the stale pin —
    // i.e. the guard is comparing against live reality, not silently trusting the disclosure.
    try {
      await runMigrations(client, [dir], { disclosures })
      expect.unreachable('expected runMigrations to throw')
    } catch (err) {
      const mismatch = err as MigrationHashMismatchError
      expect(mismatch.currentSha256).toBe(sha256(editedAgainSql))
      expect(mismatch.currentSha256).not.toBe(sha256(disclosedCurrentSql))
    }
  })

  it('does not disclose a mismatch whose STORED hash does not match the pinned pair either (DB row changed since disclosure)', async () => {
    const originalSql = 'SELECT 1'
    const editedSql = 'SELECT 2'
    writeSql(dir, '001_a.sql', editedSql)

    // DB's stored hash is some THIRD value, not what the disclosure pinned as "stored"
    const client = makeClient([{ filename: '001_a.sql', sha256: sha256('SELECT 999') }])
    const disclosures = disclosureFor('001_a.sql', sha256(originalSql), sha256(editedSql))

    await expect(runMigrations(client, [dir], { disclosures })).rejects.toThrow(
      MigrationHashMismatchError
    )
  })
})

// ─── RULING 58 "Hazard 2": the filename-keyed renumber hazard (467 -> 474 class) ────────────

describe('normalizeSqlForIdentity', () => {
  it('strips line comments, block comments and whitespace differences', () => {
    const a = `-- Migration 467: do the thing\nUPDATE t SET x = 1\n  WHERE id = 2;\n`
    const b = `-- Migration 474: do the thing (renumbered 467->474 after a rebase collision)\n` +
      `/* extra note */\nUPDATE t   SET x = 1 WHERE id = 2;`
    expect(sha256(a)).not.toBe(sha256(b)) // a raw-content guard would MISS this
    expect(normalizeSqlForIdentity(a)).toBe('UPDATE t SET x = 1 WHERE id = 2;')
    expect(sqlIdentityOf(a)).toBe(sqlIdentityOf(b))
  })

  it('never mistakes -- or /* INSIDE a string literal for a comment', () => {
    const withLiteral = `INSERT INTO t (note) VALUES ('a -- not a comment /* nor this */');`
    expect(normalizeSqlForIdentity(withLiteral)).toBe(withLiteral)
    // ...and two files differing only INSIDE the literal must NOT share an identity
    const other = `INSERT INTO t (note) VALUES ('b -- not a comment /* nor this */');`
    expect(sqlIdentityOf(withLiteral)).not.toBe(sqlIdentityOf(other))
  })

  it('preserves dollar-quoted bodies verbatim (plpgsql functions)', () => {
    const fn = `CREATE FUNCTION f() RETURNS int AS $$\n  -- kept: this is code, not a comment\n  SELECT 1;\n$$ LANGUAGE sql;`
    expect(normalizeSqlForIdentity(fn)).toContain('-- kept: this is code, not a comment')
  })

  it('handles nested block comments the way Postgres does', () => {
    expect(normalizeSqlForIdentity('SELECT /* outer /* inner */ still-comment */ 1;')).toBe('SELECT 1;')
  })

  it("distinguishes migrations that genuinely differ, so the guard cannot false-positive on 'looks similar'", () => {
    expect(sqlIdentityOf('UPDATE t SET x = 1;')).not.toBe(sqlIdentityOf('UPDATE t SET x = 2;'))
  })

  it('collapses the REAL 456 -> 457 renumber from this repo (header rewritten, SQL unchanged)', () => {
    // platform/migrations/457_lel_schema_v2_event_shapes.sql was applied as 456_..., then
    // renumbered to 457_... in commit 54c809bc, which ALSO rewrote its header comment. Both
    // filenames are in production's _migrations_applied with DIFFERENT sha256 values — the SQL
    // genuinely executed twice, 1h49m apart, undetected. Replay the header edit against the real
    // on-disk file: raw hash moves, sql_identity must not.
    const real = path.resolve(__dirname, '../../migrations/457_lel_schema_v2_event_shapes.sql')
    if (!fs.existsSync(real)) return // file retired later — the synthetic cases above still hold
    const as457 = fs.readFileSync(real, 'utf8')
    const as456 = as457
      .replace('-- Migration 457:', '-- Migration 456:')
      .replace(
        /-- \(renumbered 456->457[\s\S]*?\)\n/,
        ''
      )
    expect(as456).not.toBe(as457)
    expect(sha256(as456)).not.toBe(sha256(as457)) // raw-hash guard: MISS
    expect(sqlIdentityOf(as456)).toBe(sqlIdentityOf(as457)) // identity guard: CATCH
  })
})

describe('runMigrations — renumbered-migration guard', () => {
  let dir: string

  beforeEach(() => {
    dir = tmpDir()
  })

  afterEach(() => {
    fs.rmSync(dir, { recursive: true, force: true })
  })

  function renumberDisclosure(
    newFilename: string,
    appliedFilename: string,
    sqlIdentity: string,
    overrides: Partial<DisclosedRenumber> = {}
  ): Map<string, DisclosedRenumber> {
    return new Map([
      [
        newFilename,
        {
          new_filename: newFilename,
          applied_filename: appliedFilename,
          sql_identity: sqlIdentity,
          disposition: 'already-applied-under-old-name',
          reason: 'test reason',
          disclosed_via: 'test',
          disclosed_on: '2026-07-30',
          ...overrides,
        } as DisclosedRenumber,
      ],
    ])
  }

  it('CAN-FAIL: renaming an already-applied migration to a new number is REFUSED, not re-applied', async () => {
    // Reproduce the hazard exactly: 467_x.sql was applied; the file is now named 474_x.sql.
    const migrationSql = 'INSERT INTO ledger (k, v) VALUES (1, 1);' // deliberately NOT idempotent
    writeSql(dir, '474_x.sql', migrationSql)

    const client = makeClient([{ filename: '467_x.sql', sha256: sha256(migrationSql) }])

    await expect(runMigrations(client, [dir], { renumberDisclosures: new Map() })).rejects.toThrow(
      MigrationRenumberedError
    )

    // The whole point: the SQL must NOT have run a second time.
    const executed = (client as any).queries.filter((q: any) => q.text === migrationSql)
    expect(executed).toHaveLength(0)
    const inserts = (client as any).queries.filter((q: any) =>
      q.text.includes('INSERT INTO _migrations_applied')
    )
    expect(inserts).toHaveLength(0)
  })

  it('names both filenames and the match kind in the refusal', async () => {
    const migrationSql = 'UPDATE asset_registry SET target_floor = 40 WHERE asset_id = $$x$$;'
    writeSql(dir, '474_x.sql', migrationSql)
    const client = makeClient([{ filename: '467_x.sql', sha256: sha256(migrationSql) }])

    try {
      await runMigrations(client, [dir], { renumberDisclosures: new Map() })
      expect.unreachable('expected runMigrations to throw')
    } catch (err) {
      expect(err).toBeInstanceOf(MigrationRenumberedError)
      const e = err as MigrationRenumberedError
      expect(e.newFilename).toBe('474_x.sql')
      expect(e.appliedFilename).toBe('467_x.sql')
      expect(e.matchKind).toBe('sha256')
      expect(e.message).toContain('474_x.sql')
      expect(e.message).toContain('467_x.sql')
    }
  })

  it('catches a renumber that ALSO rewrote the header comment (raw sha256 differs) via sql_identity', async () => {
    const appliedSql = '-- Migration 467: the thing\nUPDATE t SET x = 1;\n'
    const renumberedSql = '-- Migration 474: the thing (renumbered after rebase)\nUPDATE t SET x = 1;\n'
    writeSql(dir, '474_x.sql', renumberedSql)

    // The applied row's stored sha256 is of the OLD text — a raw-hash comparison cannot match.
    const client = makeClient([
      { filename: '467_x.sql', sha256: sha256(appliedSql), sql_identity: sqlIdentityOf(appliedSql) },
    ])
    expect(sha256(appliedSql)).not.toBe(sha256(renumberedSql))

    try {
      await runMigrations(client, [dir], { renumberDisclosures: new Map() })
      expect.unreachable('expected runMigrations to throw')
    } catch (err) {
      expect(err).toBeInstanceOf(MigrationRenumberedError)
      expect((err as MigrationRenumberedError).matchKind).toBe('sql_identity')
    }
  })

  it('backfills sql_identity for already-applied rows whose on-disk content still matches', async () => {
    const appliedSql = '-- Migration 467: the thing\nUPDATE t SET x = 1;\n'
    writeSql(dir, '467_x.sql', appliedSql)

    const rows: AppliedRow[] = [{ filename: '467_x.sql', sha256: sha256(appliedSql) }]
    const client = makeClient(rows)
    await runMigrations(client, [dir], { renumberDisclosures: new Map() })

    expect(rows[0].sql_identity).toBe(sqlIdentityOf(appliedSql))
  })

  it('does NOT backfill sql_identity for a row whose on-disk content has drifted (disclosed residual class)', async () => {
    const storedSql = 'UPDATE t SET x = 1;'
    const driftedSql = 'UPDATE t SET x = 2;'
    writeSql(dir, '467_x.sql', driftedSql)

    const rows: AppliedRow[] = [{ filename: '467_x.sql', sha256: sha256(storedSql) }]
    const client = makeClient(rows)
    const disclosures = new Map<string, DisclosedHashMismatch>([
      [
        '467_x.sql',
        {
          filename: '467_x.sql',
          stored_sha256: sha256(storedSql),
          current_sha256_at_disclosure: sha256(driftedSql),
          cause: 'test',
          disclosed_via: 'test',
          fixed_by_samapti: false,
        },
      ],
    ])
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    try {
      await runMigrations(client, [dir], { disclosures, renumberDisclosures: new Map() })
    } finally {
      warnSpy.mockRestore()
    }
    // An honest NULL: we cannot prove which content actually ran, so we do not stamp one.
    expect(rows[0].sql_identity ?? null).toBeNull()
  })

  it('a genuinely NEW migration is unaffected by the guard', async () => {
    writeSql(dir, '467_x.sql', 'UPDATE t SET x = 1;')
    writeSql(dir, '475_new.sql', 'UPDATE t SET y = 9;')
    const client = makeClient([{ filename: '467_x.sql', sha256: sha256('UPDATE t SET x = 1;') }])

    const ran = await runMigrations(client, [dir], { renumberDisclosures: new Map() })
    expect(ran).toEqual(['475_new.sql'])
  })

  it('dry-run surfaces the renumber from a PREVIEW, not only from a real run', async () => {
    const migrationSql = 'INSERT INTO ledger (k, v) VALUES (1, 1);'
    writeSql(dir, '474_x.sql', migrationSql)
    const client = makeClient([{ filename: '467_x.sql', sha256: sha256(migrationSql) }])

    await expect(
      runMigrations(client, [dir], { dryRun: true, renumberDisclosures: new Map() })
    ).rejects.toThrow(MigrationRenumberedError)
  })

  it("disclosed 'already-applied-under-old-name' records the new filename WITHOUT executing the SQL", async () => {
    const migrationSql = 'INSERT INTO ledger (k, v) VALUES (1, 1);'
    writeSql(dir, '474_x.sql', migrationSql)
    const client = makeClient([{ filename: '467_x.sql', sha256: sha256(migrationSql) }])
    const renumbers = renumberDisclosure('474_x.sql', '467_x.sql', sqlIdentityOf(migrationSql))

    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    let ran: string[]
    try {
      ran = await runMigrations(client, [dir], { renumberDisclosures: renumbers })
    } finally {
      warnSpy.mockRestore()
      logSpy.mockRestore()
    }

    expect(ran).toEqual([]) // reported as NOT applied — it did not run
    const executed = (client as any).queries.filter((q: any) => q.text === migrationSql)
    expect(executed).toHaveLength(0) // the SQL never ran a second time
    const inserts = (client as any).queries.filter((q: any) =>
      q.text.includes('INSERT INTO _migrations_applied')
    )
    expect(inserts).toHaveLength(1) // but the new filename IS now tracked
    expect(inserts[0].values?.[0]).toBe('474_x.sql')
  })

  it("disclosed 'intentional-reapply' executes normally", async () => {
    const migrationSql = 'UPDATE t SET x = 1;' // idempotent by construction
    writeSql(dir, '474_x.sql', migrationSql)
    const client = makeClient([{ filename: '467_x.sql', sha256: sha256(migrationSql) }])
    const renumbers = renumberDisclosure('474_x.sql', '467_x.sql', sqlIdentityOf(migrationSql), {
      disposition: 'intentional-reapply',
    })

    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    let ran: string[]
    try {
      ran = await runMigrations(client, [dir], { renumberDisclosures: renumbers })
    } finally {
      warnSpy.mockRestore()
    }
    expect(ran).toEqual(['474_x.sql'])
    const executed = (client as any).queries.filter((q: any) => q.text === migrationSql)
    expect(executed).toHaveLength(1)
  })

  it('a disclosure pinned to a DIFFERENT old filename does not cover this renumber', async () => {
    const migrationSql = 'INSERT INTO ledger (k, v) VALUES (1, 1);'
    writeSql(dir, '474_x.sql', migrationSql)
    const client = makeClient([{ filename: '467_x.sql', sha256: sha256(migrationSql) }])
    const renumbers = renumberDisclosure('474_x.sql', '999_other.sql', sqlIdentityOf(migrationSql))

    await expect(runMigrations(client, [dir], { renumberDisclosures: renumbers })).rejects.toThrow(
      MigrationRenumberedError
    )
  })

  it('a disclosure whose pinned sql_identity no longer matches the file does not cover it', async () => {
    const migrationSql = 'INSERT INTO ledger (k, v) VALUES (1, 1);'
    writeSql(dir, '474_x.sql', migrationSql)
    const client = makeClient([{ filename: '467_x.sql', sha256: sha256(migrationSql) }])
    const renumbers = renumberDisclosure('474_x.sql', '467_x.sql', sqlIdentityOf('SOMETHING ELSE;'))

    await expect(runMigrations(client, [dir], { renumberDisclosures: renumbers })).rejects.toThrow(
      MigrationRenumberedError
    )
  })
})

describe('loadRenumberDisclosures', () => {
  let dir: string

  beforeEach(() => {
    dir = tmpDir()
  })

  afterEach(() => {
    fs.rmSync(dir, { recursive: true, force: true })
  })

  it('returns an empty map when the file does not exist', () => {
    expect(loadRenumberDisclosures(path.join(dir, 'nope.json')).size).toBe(0)
  })

  it('drops an entry with an unrecognised disposition — not a partial pass', () => {
    const file = path.join(dir, 'renumbers.json')
    fs.writeFileSync(
      file,
      JSON.stringify({
        entries: [
          {
            new_filename: 'a.sql',
            applied_filename: 'b.sql',
            sql_identity: 'abc',
            disposition: 'just-let-it-through',
            reason: 'r',
            disclosed_via: 'v',
            disclosed_on: '2026-07-30',
          },
        ],
      })
    )
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    try {
      expect(loadRenumberDisclosures(file).has('a.sql')).toBe(false)
      expect(warnSpy).toHaveBeenCalled()
    } finally {
      warnSpy.mockRestore()
    }
  })

  it('the checked-in allowlist parses and is empty by design', () => {
    const real = path.resolve(__dirname, '../ci/migration_renumber_disclosed.json')
    expect(fs.existsSync(real)).toBe(true)
    expect(loadRenumberDisclosures(real).size).toBe(0)
  })
})

describe('loadHashDisclosures', () => {
  let dir: string

  beforeEach(() => {
    dir = tmpDir()
  })

  afterEach(() => {
    fs.rmSync(dir, { recursive: true, force: true })
  })

  it('returns an empty map when the file does not exist', () => {
    const map = loadHashDisclosures(path.join(dir, 'nope.json'))
    expect(map.size).toBe(0)
  })

  it('loads well-formed entries keyed by filename', () => {
    const file = path.join(dir, 'disclosures.json')
    fs.writeFileSync(
      file,
      JSON.stringify({
        entries: [
          {
            filename: 'abc.sql',
            stored_sha256: 'aaa',
            current_sha256_at_disclosure: 'bbb',
            cause: 'test',
            disclosed_via: 'DVA RULING 73',
            fixed_by_samapti: false,
          },
        ],
      })
    )
    const map = loadHashDisclosures(file)
    expect(map.size).toBe(1)
    expect(map.get('abc.sql')?.stored_sha256).toBe('aaa')
  })

  it('drops an entry missing a required field and warns — treated as UNDISCLOSED, not a partial pass', () => {
    const file = path.join(dir, 'disclosures.json')
    fs.writeFileSync(
      file,
      JSON.stringify({
        entries: [
          {
            filename: 'incomplete.sql',
            stored_sha256: 'aaa',
            // current_sha256_at_disclosure missing
            cause: 'test',
            disclosed_via: 'DVA RULING 73',
            fixed_by_samapti: false,
          },
        ],
      })
    )
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    try {
      const map = loadHashDisclosures(file)
      expect(map.has('incomplete.sql')).toBe(false)
      expect(warnSpy).toHaveBeenCalled()
    } finally {
      warnSpy.mockRestore()
    }
  })
})
