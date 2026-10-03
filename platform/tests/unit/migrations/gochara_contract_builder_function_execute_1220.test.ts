/**
 * Migration 1220 static contract (the live proof is
 * tests/integration/gochara_contract_builder_function_execute.db.test.ts).
 *   - routine window: NOT in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS, and the file
 *     contains only GRANT statements (creates/alters/drops nothing);
 *   - grants go only to data_plane_builder, never to PUBLIC, never WITH GRANT OPTION;
 *   - every EXECUTE grant names a schema-qualified, signature-qualified function;
 *   - no write privilege on the generation-seal table and no EXECUTE on the seal function.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const FILE = '1220_gochara_contract_builder_function_execute.sql'
const sql = fs.readFileSync(path.resolve(__dirname, '../../../migrations', FILE), 'utf8')
const statements = sql
  .split('\n')
  .filter(l => !l.trim().startsWith('--'))
  .join('\n')
  .split(';')
  .map(s => s.trim())
  .filter(Boolean)

describe('migration 1220 — static contract', () => {
  it('is routine: not listed in the protected public-schema windows', () => {
    const migrate = fs.readFileSync(path.resolve(__dirname, '../../../scripts/migrate.ts'), 'utf8')
    expect(migrate).not.toContain(FILE)
  })

  it('contains only GRANT statements', () => {
    expect(statements.length).toBeGreaterThan(0)
    for (const s of statements) expect(s, s).toMatch(/^GRANT\s/)
  })

  it('grants only to data_plane_builder, never PUBLIC or WITH GRANT OPTION', () => {
    for (const s of statements) {
      expect(s, s).toMatch(/TO data_plane_builder$/)
      expect(s, s).not.toMatch(/TO PUBLIC|WITH GRANT OPTION/i)
    }
  })

  it('every EXECUTE grant is schema- and signature-qualified; exactly 18 of them', () => {
    const exec = statements.filter(s => /^GRANT EXECUTE/.test(s))
    expect(exec).toHaveLength(18)
    for (const s of exec) expect(s, s).toMatch(/^GRANT EXECUTE ON FUNCTION public\.ka_gochara_\w+\([^)]*\) TO data_plane_builder$/)
  })

  it('withholds the seal: SELECT only on the seal table, no EXECUTE on seal_generation or the seal guard', () => {
    const seal = statements.filter(s => /ka_gochara_generation_seal\b/.test(s))
    expect(seal).toEqual(['GRANT SELECT ON public.ka_gochara_generation_seal TO data_plane_builder'])
    expect(sql).not.toMatch(/GRANT EXECUTE ON FUNCTION public\.ka_gochara_seal_generation/)
    expect(sql).not.toMatch(/GRANT EXECUTE ON FUNCTION public\.ka_gochara_generation_seal_guard/)
  })
})
