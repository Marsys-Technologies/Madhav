import { describe, it, expect, vi, afterAll } from 'vitest'
import type { PoolClient } from 'pg'
import fs from 'fs'
import os from 'os'
import path from 'path'
import { GOCHARA_MIGRATION_READBACKS, readBackGocharaMigration, runMigrations } from '../migrate'

describe('P06b per-migration catalogue readbacks', () => {
  it('executes each real SELECT-only script in a read-only transaction and exposes its results', async () => {
    const output = vi.spyOn(console, 'log').mockImplementation(() => {})
    try {
      for (const filename of Object.keys(GOCHARA_MIGRATION_READBACKS)) {
        const sql: string[] = []
        const client = { query: async (s: string) => { sql.push(s); return [{ rows: [{ server_version_num: '150017' }] }] } }
        await readBackGocharaMigration(client as unknown as PoolClient, filename)
        expect(sql).toHaveLength(1)
        expect(sql[0]).toContain('BEGIN READ ONLY;')
        expect(sql[0]).toContain('server_version_num')
        expect(sql[0].replace(/--[^\n]*/g, '').replace(/'(?:[^']|'')*'/g, '')).not.toMatch(/\b(?:INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b/i)
        expect(output).toHaveBeenLastCalledWith(expect.stringContaining(filename))
        expect(output).toHaveBeenLastCalledWith(expect.stringContaining('150017'))
      }
    } finally { output.mockRestore() }
  })
  it('propagates a readback error and rolls back its read-only transaction', async () => {
    const calls: string[] = []
    const client = { query: async (s: string) => { calls.push(s); if (s !== 'ROLLBACK') throw new Error('catalog unavailable') } }
    await expect(readBackGocharaMigration(client as unknown as PoolClient, '1381_gochara_near_miss_seal_integration.sql')).rejects.toThrow('catalog unavailable')
    expect(calls.at(-1)).toBe('ROLLBACK')
  })
  it('reads back a committed migration before applying the next selected file', async () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'p06b-readback-'))
    const output = vi.spyOn(console, 'log').mockImplementation(() => {})
    try {
      const filename = '1381_gochara_near_miss_seal_integration.sql'
      fs.writeFileSync(path.join(dir, filename), 'SELECT 1381;')
      fs.writeFileSync(path.join(dir, '1382_test_successor.sql'), 'SELECT 1382;')
      const calls: string[] = []
      // The runner restores the entry role after each migration body (migrate.ts, main's atomic DDL+ledger commit).
      const client = { query: async (s: string) => {
        calls.push(s.trim())
        return { rows: s.trim() === "SELECT current_setting('role') AS role" ? [{ role: 'none' }] : [] }
      } }
      await runMigrations(client as unknown as PoolClient, [dir], {
        only: new Set([filename, '1382_test_successor.sql']),
        disclosures: new Map(), renumberDisclosures: new Map(),
      })
      const readback = calls.findIndex(s => s.includes('BEGIN READ ONLY;'))
      expect(readback).toBeGreaterThan(calls.indexOf('COMMIT'))
      expect(readback).toBeLessThan(calls.indexOf('SELECT 1382;'))
    } finally { output.mockRestore(); fs.rmSync(dir, { recursive: true, force: true }) }
  })
})

// NB-03: replay is an explicit ledger/readback operation; migration SQL is never re-executed.
describe('P06B-NB-03 guarded replay', () => {
  const filename = '1381_gochara_near_miss_seal_integration.sql'
  const content = fs.readFileSync(path.resolve(import.meta.dirname, '../../migrations', filename), 'utf8')
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'p06b-replay-'))
  const dirs=[dir]
  fs.writeFileSync(path.join(dir,filename),content)
  fs.writeFileSync(path.join(dir,'1308_gochara_near_miss_storage.sql'),'SELECT 1308;')
  afterAll(()=>fs.rmSync(dir,{recursive:true,force:true}))
  async function invoke(rows: Array<{filename: string, sha256: string}>, only = new Set([filename])) {
    const calls: string[] = []
    const client = { query: async (sql: string) => {
      calls.push(sql)
      return { rows: sql.startsWith('SELECT filename, sha256') ? rows : [] }
    } }
    const result = runMigrations(client as unknown as PoolClient, dirs, {only, replayGochara: true})
    return {calls, result}
  }
  it('refuses an unapplied migration without executing its SQL or tracker DDL', async () => {
    const {calls,result} = await invoke([])
    await expect(result).rejects.toThrow(/replay.*not applied/)
    expect(calls.every(sql => /^SELECT /i.test(sql))).toBe(true)
  })
  it('refuses a ledger hash mismatch without executing SQL or a readback', async () => {
    const {calls,result} = await invoke([{filename,sha256:'0'.repeat(64)}])
    await expect(result).rejects.toThrow(/hash mismatch|sha256/i)
    expect(calls.every(sql => /^SELECT /i.test(sql))).toBe(true)
  })
  it('refuses an unreviewed filename before any database call', async () => {
    const {calls,result} = await invoke([], new Set(['1382_gochara_authority_no_truncate.sql']))
    await expect(result).rejects.toThrow(/replay.*readback/)
    expect(calls).toEqual([])
  })
  it('refuses an absent filename before any database call', async () => {
    const {calls,result} = await invoke([], new Set(['999999_missing.sql']))
    await expect(result).rejects.toThrow(/replay.*readback/)
    expect(calls).toEqual([])
  })
  it('skips matching SQL on both replays and repeats independent readback without DDL', async () => {
    const {createHash} = await import('crypto')
    const rows = [{filename, sha256:createHash('sha256').update(content).digest('hex')}]
    for (let n=0;n<2;n++) {
      const {calls,result} = await invoke(rows)
      await expect(result).resolves.toEqual([])
      expect(calls.some(sql => sql.includes('BEGIN READ ONLY;'))).toBe(true)
      expect(calls).not.toContain(content)
      expect(calls.every(sql => /^SELECT /i.test(sql) || sql.includes('BEGIN READ ONLY;'))).toBe(true)
    }
  })
  it('preflights every requested hash before producing any readback', async () => {
    const {createHash} = await import('crypto')
    const rows=[{filename,sha256:createHash('sha256').update(content).digest('hex')},
      {filename:'1308_gochara_near_miss_storage.sql',sha256:'0'.repeat(64)}]
    const {calls,result}=await invoke(rows,new Set(rows.map(r=>r.filename)))
    await expect(result).rejects.toThrow(/hash mismatch|sha256/i)
    expect(calls.every(sql => /^SELECT /i.test(sql))).toBe(true)
  })
})

it('guarded replay CLI requires an explicit reviewed set and forbids apply/preview modes', async () => {
  const {parseMigrationCliArgs}=await import('../migrate')
  expect(parseMigrationCliArgs(['--replay-gochara','--only','1381_gochara_near_miss_seal_integration.sql']).replayGochara).toBe(true)
  for (const args of [ ['--replay-gochara'], ['--replay-gochara','--only','a.sql','--dry-run'],
    ['--replay-gochara','--target','a.sql'] ]) {
    expect(()=>parseMigrationCliArgs(args)).toThrow(/replay requires/)
  }
})
