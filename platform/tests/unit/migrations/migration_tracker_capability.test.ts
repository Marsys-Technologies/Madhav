import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it, vi } from 'vitest'
import type { PoolClient } from 'pg'
import { TRACKER_DDL, runMigrations } from '../../../scripts/migrate'

describe('ordinary migration tracker capability', () => {
  it('does not require public CREATE when the established tracker already exists', async () => {
    const directory = mkdtempSync(join(tmpdir(), 'migration-tracker-capability-'))
    try {
      writeFileSync(join(directory, '1041_compatibility.sql'), 'SELECT 1;')
      const query = vi.fn(async (sql: string) => {
        if (sql.includes("to_regclass('public._migrations_applied')")) return { rows: [{ present: true }] }
        if (sql.includes('SELECT filename, sha256, sql_identity FROM _migrations_applied')) return { rows: [] }
        return { rows: [] }
      })
      const client = { query } as unknown as PoolClient

      await expect(runMigrations(client, [directory], {
        disclosures: new Map(),
        renumberDisclosures: new Map(),
      })).resolves.toEqual(['1041_compatibility.sql'])

      expect(query).not.toHaveBeenCalledWith(TRACKER_DDL)
    } finally {
      rmSync(directory, { recursive: true, force: true })
    }
  })
})
