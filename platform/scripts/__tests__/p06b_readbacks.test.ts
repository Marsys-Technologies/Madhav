import { describe, it, expect, vi } from 'vitest'
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
      const client = { query: async (s: string) => {
        calls.push(s.trim())
        // the runner restores its entry role after a committed migration (#3595): answer that bookkeeping read
        return { rows: s === "SELECT current_setting('role') AS role" ? [{ role: 'none' }] : [] }
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
