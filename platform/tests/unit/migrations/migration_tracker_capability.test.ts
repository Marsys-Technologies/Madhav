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
        if (sql === "SELECT current_setting('role') AS role, current_setting('search_path') AS search_path") return { rows: [{ role: 'none', search_path: 'pg_catalog, public' }] }
        if (sql.includes("to_regclass('public._migrations_applied')")) return { rows: [{ present: true }] }
        if (sql.includes('SELECT filename, sha256, sql_identity FROM _migrations_applied')) return { rows: [] }
        return { rows: [] }
      })
      const client = { query } as unknown as PoolClient

      await expect(runMigrations(client, [directory], {
        disclosures: new Map(),
        renumberDisclosures: new Map(),
      })).resolves.toEqual(['1041_compatibility.sql'])

      expect(client.query).toHaveBeenCalledWith("SELECT current_setting('role') AS role, current_setting('search_path') AS search_path")
      expect(client.query).toHaveBeenCalledWith("SELECT pg_catalog.set_config('role', $1, false)", ['none'])
      expect(client.query).toHaveBeenCalledWith("SELECT pg_catalog.set_config('search_path', $1, false)", ['pg_catalog, public'])

      expect(query).not.toHaveBeenCalledWith(TRACKER_DDL)
    } finally {
      rmSync(directory, { recursive: true, force: true })
    }
  })
})
