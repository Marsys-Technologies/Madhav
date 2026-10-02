import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Migration 1223 -- ga_vargas output-digest spec, seven-column key (F-A2).
 *
 * Static shape test. The behaviour (retire first / insert second under the one-current index, the guard
 * refusing a foreign live spec, the idempotent re-run, the combined S-L1 W1 window) is proved against a
 * disposable PostgreSQL by python-sidecar/tests/test_migration_1222_1223_ga_vargas.py, and the new sha is
 * recomputed there with the repository's own canonical_digest. Here: the file is a guarded retire+insert on
 * asset_output_digest_specs only, the new spec is the migration-883 spec with `fact_subject` appended to
 * key_columns and nothing else, and the replacement is declared in editorial.ts (the knowledge layer pins the
 * spec sha a receipt must carry).
 */
const root = process.cwd()
const migration = fs.readFileSync(
  path.resolve(root, 'migrations/1223_nirmana_l1_ga_vargas_output_digest_spec_seven_column_key.sql'), 'utf8')
const m883 = fs.readFileSync(path.resolve(root, 'migrations/883_nirmana_l1_ga_vargas_output_digest_spec.sql'), 'utf8')
const editorial = fs.readFileSync(path.resolve(root, 'src/lib/retrieval/registry/knowledge/editorial.ts'), 'utf8')

const OLD_SHA = '5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51'
const NEW_SHA = '9c278d217f045f140596b452aa3c929bc83632bf96f0a266a2532dfe2ee60862'
const SIX = ['chart_id', 'graha', 'ayanamsha_id', 'varga', 'fact_category', 'fact_key']

function specLiteral(sql: string): Record<string, unknown> {
  const m = sql.match(/'(\{"version".*?\})'::jsonb/s)
  if (!m) throw new Error('spec literal not found')
  return JSON.parse(m[1]!) as Record<string, unknown>
}
const code = migration.split('\n').filter((l) => !l.trimStart().startsWith('--')).join('\n')

describe('migration 1223 -- ga_vargas digest spec, seven-column key', () => {
  it('starts with lock_timeout, owns no transaction, and has no DDL', () => {
    expect(code.trim().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(code).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/im)
    expect(code).not.toMatch(/^\s*(ALTER|CREATE|DROP|GRANT|REVOKE|TRUNCATE|DELETE)\b/im)
  })

  it('retires the 883 row FIRST, then inserts the new one with ON CONFLICT DO NOTHING', () => {
    const upd = code.indexOf('UPDATE asset_output_digest_specs')
    const ins = code.indexOf('INSERT INTO asset_output_digest_specs')
    expect(upd).toBeGreaterThan(-1)
    expect(ins).toBeGreaterThan(upd)
    expect(code).toContain('ON CONFLICT (asset_id, spec_sha256) DO NOTHING;')
    expect(code).toContain(`spec_sha256 = '${OLD_SHA}'`)
    expect(code).toContain(`'${NEW_SHA}'`)
    expect(code.match(/UPDATE asset_output_digest_specs/g)).toHaveLength(1)
    expect(code.match(/INSERT INTO asset_output_digest_specs/g)).toHaveLength(1)
  })

  it('the new spec is the 883 spec with fact_subject appended to key_columns, nothing else changed', () => {
    const oldSpec = specLiteral(m883) as { components: Array<Record<string, unknown>> }
    const newSpec = specLiteral(migration) as { components: Array<Record<string, unknown>> }
    const oldC = oldSpec.components[0]!
    const newC = newSpec.components[0]!
    expect(oldC['key_columns']).toEqual(SIX)
    expect(newC['key_columns']).toEqual([...SIX, 'fact_subject'])
    const { key_columns: _o, ...oldRest } = oldC
    const { key_columns: _n, ...newRest } = newC
    expect(newRest).toEqual(oldRest)
    expect(newC['value_columns']).toContain('fact_subject')
    expect(newSpec.components).toHaveLength(1)
  })

  it('states the ordering, the serving effect and the live NULL-key count', () => {
    const flat = migration.replace(/^--/gm, ' ').replace(/\s+/g, ' ')
    for (const needle of ['SERVING EFFECT AT APPLY', 'receipt_spec_retired', 'served_generation.ts:200-206',
      'S-L1 window W1', '1221, 1222, 1223, 1226', 'NEVER after', '71,476', 'VERIFICATION BY PRODUCTION STRUCTURE',
      'IDEMPOTENT SHAPE', 'ROLLBACK', '{ga_structural, ga_vargas, ga_dashas,']) {
      expect(flat).toContain(needle)
    }
  })

  it('editorial.ts pins the NEW spec sha for the producer-output claim and the availability requirement', () => {
    expect(editorial).not.toContain(OLD_SHA)
    expect(editorial.match(new RegExp(NEW_SHA, 'g'))?.length).toBe(2)
    expect(editorial).toContain('platform/migrations/1223_nirmana_l1_ga_vargas_output_digest_spec_seven_column_key.sql')
  })
})
