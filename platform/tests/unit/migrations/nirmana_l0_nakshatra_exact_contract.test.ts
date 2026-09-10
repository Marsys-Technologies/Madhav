import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'supabase/migrations/625_nirmana_l0_nakshatra_exact_contract.sql'),
  'utf8',
)

describe('migration 625 — nakshatra exact integrity', () => {
  it('pins every owned projection and fails closed', () => {
    expect(migration).toContain('bbbf686205c208efe0a7f6dbd192b27e63931a9b37f442d194d8d17b72ee3fde')
    expect(migration).toContain('09eeb0e2027486201274b36427a17cee7eb1c60eceb3c3bf334c53b6fbc990a9')
    expect(migration).toContain('143ce4a335d0cc7fac4b7bb3137c713c238e7f6b06f2477d7ecf7aa14d88d9bb')
    expect(migration).toContain('migration 625 refuses unknown bg_nakshatra registry contract')
    expect(migration).toContain('reference_nakshatra_matrix.(matrix_type,from_key,to_key)')
    expect(migration).not.toMatch(/^BEGIN;/m)
  })
})
