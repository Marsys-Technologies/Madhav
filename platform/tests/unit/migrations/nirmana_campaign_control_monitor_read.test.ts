import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const migrationPath = join(process.cwd(), 'migrations/636_nirmana_campaign_control_monitor_read.sql')
const sql = existsSync(migrationPath) ? readFileSync(migrationPath, 'utf8') : ''

describe('migration 636: Nirmana campaign-control monitor observation read', () => {
  it('grants only the monitor-observation read needed by atomic supersession', () => {
    expect(sql).toMatch(/GRANT SELECT ON TABLE public\.nirmana_elevation_monitor_observations\s+TO nirmana_campaign_control_writer/)
    expect(sql).toContain('has_table_privilege')
    expect(sql).toContain("'SELECT'")
    expect(sql).toContain("'INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER'")
    expect(sql).not.toContain('GRANT ALL')
    expect(sql).not.toMatch(/^BEGIN;$/m)
    expect(sql).not.toMatch(/^COMMIT;$/m)
  })
})
