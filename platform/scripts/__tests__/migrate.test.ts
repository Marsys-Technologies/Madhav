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
  loadHashDisclosures,
  type DisclosedHashMismatch,
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
}

/** Build a mock PoolClient that records all query calls */
function makeClient(applied: AppliedRow[] = [], failOn?: string) {
  const queries: Array<{ text: string; values?: unknown[] }> = []

  const client = {
    query: vi.fn(async (text: string, values?: unknown[]) => {
      const q = typeof text === 'string' ? text.trim() : text
      queries.push({ text: q, values })

      // Simulate tracker creation
      if (q.includes('CREATE TABLE IF NOT EXISTS _migrations_applied')) {
        return { rows: [] }
      }

      // Return applied list (filename + sha256, per the tracker schema)
      if (q.includes('SELECT filename, sha256 FROM _migrations_applied')) {
        return { rows: applied.map(({ filename, sha256 }) => ({ filename, sha256 })) }
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
