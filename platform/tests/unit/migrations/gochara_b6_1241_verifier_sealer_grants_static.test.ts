/**
 * Pravāha B6.0 / Codex round 9 R9-6 — STATIC contract of migration 1241 (verifier + sealer inventory-side grants). The live proof (the real
 * migration applied in the composed rehearsal; each grant individually necessary; the first seal, the replace-on-rerun and the contention
 * flows) is python-sidecar/tests/l3/gochara/test_b6_composed_seal_flows.py.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1241_gochara_verifier_sealer_inventory_grants.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const grants = CODE.match(/^\s*GRANT [^;]+;/gm) ?? []

describe('migration 1241 — static contract', () => {
  it('is grants only: no object is created, nothing is revoked, no transaction control', () => {
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|REVOKE|TRUNCATE)\b|SECURITY DEFINER|WITH GRANT OPTION/im)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
    expect(grants.length).toBeGreaterThan(0)
  })

  it('grants to exactly the two principals, never to the builder or PUBLIC', () => {
    for (const g of grants) {
      expect(g).toMatch(/TO gochara_(verifier|sealer);$/)
      expect(g).not.toMatch(/data_plane_builder|PUBLIC/)
    }
  })

  it('gives the verifier INSERT only on the inventory verification table (no DELETE, no UPDATE) and nothing on the seal or build data', () => {
    const verifier = grants.filter(g => g.endsWith('TO gochara_verifier;')).join('\n')
    expect(verifier).toContain('GRANT SELECT, INSERT ON public.ka_gochara_search_inventory_verification TO gochara_verifier;')
    expect(verifier).not.toMatch(/\bDELETE\b|\bUPDATE\b/)
    expect(verifier).not.toMatch(/ka_gochara_generation_seal|ka_gochara_seal_generation|ka_gochara_relationship_record|ka_gochara_eval_window\b/)
  })

  it('gives the sealer no write on build or verification data (INSERT only the seal row, UPDATE only the publication)', () => {
    const sealer = grants.filter(g => g.endsWith('TO gochara_sealer;')).join('\n')
    expect(sealer).toContain('GRANT INSERT ON public.ka_gochara_generation_seal TO gochara_sealer;')
    expect(sealer).toContain('GRANT UPDATE ON public.kala_gochara_publication TO gochara_sealer;')
    expect(sealer.match(/\bINSERT\b/g)?.length).toBe(1)
    expect(sealer.match(/\bUPDATE\b/g)?.length).toBe(1)
    expect(sealer).not.toMatch(/\bDELETE\b/)
  })

  it('does NOT grant the L1 reads (chart_facts / chart_dashas): their ACLs belong to the data-plane ownership script', () => {
    expect(CODE).not.toMatch(/\bchart_facts\b|\bchart_dashas\b/)
    expect(SQL).toContain('data-plane-ownership-preflight.ts')
  })

  it('refuses to apply before the window, guards each role, PRINTS the principals found and verifies grants and absences', () => {
    expect(CODE).toContain('the protected window (1206, 1240) has not been applied')
    expect(CODE).toContain("rolname = 'gochara_verifier'")
    expect(CODE).toContain("rolname = 'gochara_sealer'")
    expect(CODE).toContain('NOT FOUND — NO grant was issued')
    expect(CODE).toContain('principals found: gochara_verifier=%, gochara_sealer=%')
    expect(CODE).toContain('post-apply check failed')
  })

  it('is a ROUTINE migration numbered above 1240 (a number below 1240 would be an unapplied predecessor of the window)', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    const n = Number(FILE.slice(0, 4)); expect(n).toBeGreaterThan(1240); expect(n).toBeLessThanOrEqual(1249)
    for (const d of [MIG, path.resolve(__dirname, '../../../python-sidecar/scripts/kala_gochara_cutover')].filter(x => fs.existsSync(x)))
      expect(fs.readdirSync(d).filter(f => /^1241_/.test(f) && f !== FILE)).toEqual([])
  })
})
