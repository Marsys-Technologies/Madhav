import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

// Static contract for migration 1217 (Suvarṇa grant v1.4): exactly INSERT + UPDATE on
// asset_freshness and bg_transit_moorti for data_plane_builder, and nothing else. The
// behavioural fails-before/succeeds-after proof is the DB suite
// tests/integration/builder_freshness_transit_moorti_grants.db.test.ts.
const sql = readFileSync(resolve(__dirname, '../../../migrations/1217_suvarna_builder_freshness_and_transit_moorti_grants.sql'), 'utf8')
const code = sql.split('\n').filter((l) => !l.trim().startsWith('--')).join('\n')
const executable = code.replace(/DO \$\$[\s\S]*?END \$\$;/g, '')

describe('migration 1217 data_plane_builder freshness + transit_moorti grants', () => {
  it('issues exactly two GRANTs: INSERT, UPDATE on asset_freshness and bg_transit_moorti', () => {
    const grants = [...executable.matchAll(/^\s*GRANT\s+(.+?)\s+ON\s+TABLE\s+(\S+)\s+TO\s+(\S+);/gim)]
    expect(grants.map((g) => [g[1].replace(/\s+/g, ' ').trim().toUpperCase(), g[2], g[3]])).toEqual([
      ['INSERT, UPDATE', 'public.asset_freshness', 'data_plane_builder'],
      ['INSERT, UPDATE', 'public.bg_transit_moorti', 'data_plane_builder'],
    ])
    // Nothing else is executable besides those two statements.
    expect(executable.replace(/\s+/g, ' ').trim().split(';').filter(Boolean)).toHaveLength(2)
  })

  it('grants no DELETE/TRUNCATE/TRIGGER/REFERENCES/ALL, no grant option, no sequence/schema/all-tables scope', () => {
    expect(executable).not.toMatch(/\b(DELETE|TRUNCATE|REFERENCES|TRIGGER|ALL\s+PRIVILEGES|WITH\s+GRANT\s+OPTION)\b/i)
    expect(executable).not.toMatch(/\bALL\b/i)
    expect(executable).not.toMatch(/ON\s+(ALL\s+TABLES|SEQUENCE|SCHEMA|FUNCTION)/i)
    // Column-level grants are not used (table-level by design; rationale in the header).
    expect(executable).not.toMatch(/GRANT\s+\w+\s*\(/i)
  })

  it('does not revoke, alter roles/ownership, or change SECURITY DEFINER', () => {
    expect(executable).not.toMatch(/\b(REVOKE|ALTER\s+ROLE|ALTER\s+USER|CREATE\s+ROLE|OWNER\s+TO|SECURITY\s+DEFINER|ALTER\s+DEFAULT\s+PRIVILEGES)\b/i)
    expect(executable).not.toMatch(/\b(CREATE|DROP|ALTER)\s+(TABLE|FUNCTION|TRIGGER|POLICY|INDEX)\b/i)
  })

  it('does not touch the Gochara contract-table family (owned by Pravaha)', () => {
    expect(executable).not.toMatch(/ka_gochara_|kala_gochara_/)
  })

  it('stays out of the capability-census digest-spec scan (keeps the census byte-identical)', () => {
    // scripts/generate_capability_estate_census.ts scans every migration file whose raw text
    // contains this token; a mention anywhere in this file (comments included) would change the
    // generated census. Assembled so this test file itself is not a scanned migration.
    const token = ['asset', 'output', 'digest', 'specs'].join('_')
    expect(sql).not.toContain(token)
  })

  it('fails closed on both granted tables for both privileges', () => {
    for (const t of ['asset_freshness', 'bg_transit_moorti']) {
      for (const p of ['INSERT', 'UPDATE']) {
        expect(code).toContain(`has_table_privilege('data_plane_builder', 'public.${t}', '${p}')`)
      }
    }
    expect(code).toMatch(/RAISE EXCEPTION/)
  })
})
