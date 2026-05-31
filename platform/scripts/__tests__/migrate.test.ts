import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import fs from 'fs'
import os from 'os'
import path from 'path'
import type { PoolClient } from 'pg'

import { TRACKER_DDL, collectMigrationFiles, runMigrations } from '../migrate'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function tmpDir(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'migrate-test-'))
}

function writeSql(dir: string, name: string, sql: string): string {
  const file = path.join(dir, name)
  fs.writeFileSync(file, sql, 'utf8')
  return file
}

/** Build a mock PoolClient that records all query calls */
function makeClient(applied: string[] = [], failOn?: string) {
  const queries: Array<{ text: string; values?: unknown[] }> = []

  const client = {
    query: vi.fn(async (text: string, values?: unknown[]) => {
      const q = typeof text === 'string' ? text.trim() : text
      queries.push({ text: q, values })

      // Simulate tracker creation
      if (q.includes('CREATE TABLE IF NOT EXISTS _migrations_applied')) {
        return { rows: [] }
      }

      // Return applied list
      if (q.includes('SELECT filename FROM _migrations_applied')) {
        return { rows: applied.map(filename => ({ filename })) }
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

  it('skips already-applied migrations', async () => {
    writeSql(dir, '001_first.sql', 'CREATE TABLE t1 (id INT)')
    writeSql(dir, '002_second.sql', 'CREATE TABLE t2 (id INT)')

    // 001 already applied
    const client = makeClient(['001_first.sql'])
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
    writeSql(dir, '001_ok.sql', 'SELECT 1')
    writeSql(dir, '002_bad.sql', 'BOOM')

    // Fail when running the actual migration SQL for 002_bad
    const client = makeClient(['001_ok.sql'], 'BOOM')

    await expect(runMigrations(client, [dir])).rejects.toThrow('Simulated failure')

    const rollbackCall = (client as any).queries.find((q: any) => q.text === 'ROLLBACK')
    expect(rollbackCall).toBeDefined()
  })

  it('dry-run returns pending list without writing', async () => {
    writeSql(dir, '001_a.sql', 'SELECT 1')
    writeSql(dir, '002_b.sql', 'SELECT 2')

    const client = makeClient(['001_a.sql'])
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
})
