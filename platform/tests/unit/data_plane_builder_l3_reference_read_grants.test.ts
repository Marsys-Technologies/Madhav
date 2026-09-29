import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

// Contract for migration 1073 (salvaged from PR #2717): SELECT-only grants on exactly three
// L0 reference tables for data_plane_builder. Migration 1074 (ALTER ROLE ... SET) and a
// phala_rectification grant are intentionally excluded (Purna OSR-008).
const sql = readFileSync(resolve(__dirname, '../../migrations/1073_data_plane_builder_l3_reference_read_grants.sql'), 'utf8')
const code = sql.split('\n').filter((l) => !l.trim().startsWith('--')).join('\n')
const executable = code.replace(/DO \$\$[\s\S]*?END \$\$;/g, '')

describe('migration 1073 data_plane_builder L3 reference read grants', () => {
  it('grants SELECT on exactly the three L0 reference tables', () => {
    const grants = [...executable.matchAll(/^\s*GRANT\s+(.+?)\s+ON\s+TABLE\s+(\S+)\s+TO\s+(\S+);/gim)]
    expect(grants.map((g) => [g[1].trim().toUpperCase(), g[2], g[3]])).toEqual([
      ['SELECT', 'public.bg_transit_moorti', 'data_plane_builder'],
      ['SELECT', 'public.bg_synthetic_cohort', 'data_plane_builder'],
      ['SELECT', 'public.bg_synthetic_cohort_md', 'data_plane_builder'],
    ])
  })

  it('contains no write privileges, role alteration, revoke, or ownership change', () => {
    expect(executable).not.toMatch(/\b(INSERT|UPDATE|DELETE|TRUNCATE|REFERENCES|TRIGGER|ALL\s+PRIVILEGES|WITH\s+GRANT\s+OPTION)\b/i)
    expect(executable).not.toMatch(/\b(ALTER\s+ROLE|ALTER\s+USER|REVOKE|CREATE\s+ROLE|OWNER\s+TO)\b/i)
    expect(executable).not.toMatch(/ON\s+(ALL\s+TABLES|SEQUENCE|SCHEMA)/i)
  })

  it('does not grant phala_rectification and asserts the hold', () => {
    expect(executable).not.toMatch(/phala_rectification/)
    expect(code).toContain("has_table_privilege('data_plane_builder','public.phala_rectification','SELECT')")
  })

  it('is transactional and fails closed on each granted table', () => {
    expect(code).toMatch(/^BEGIN;/m)
    expect(code).toMatch(/^COMMIT;/m)
    for (const t of ['bg_transit_moorti', 'bg_synthetic_cohort', 'bg_synthetic_cohort_md']) {
      expect(code).toContain(`has_table_privilege('data_plane_builder','public.${t}','SELECT')`)
    }
  })
})
