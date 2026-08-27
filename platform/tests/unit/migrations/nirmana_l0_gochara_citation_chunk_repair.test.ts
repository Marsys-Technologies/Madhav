import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'supabase/migrations/631_nirmana_l0_gochara_citation_chunk_repair.sql'),
  'utf8',
)

describe('migration 631 — absent Graha Drishti corpus disposition', () => {
  it('preserves the immutable corpus and fails closed to two explicit gaps', () => {
    expect(migration).not.toMatch(/INSERT\s+INTO\s+classical_text_chunks/i)
    expect(migration).not.toMatch(/UPDATE\s+classical_text_chunks/i)
    expect(migration).not.toMatch(/DELETE\s+FROM\s+classical_text_chunks/i)
    expect(migration).toContain("migration 631 refuses to alter a corpus that already contains bphs_ch26_v001")
    expect(migration).toContain("'CORPUS_GAP:bphs_ch26_graha_drishti'")
    expect(migration).toContain("'CORPUS_GAP:bphs_ch26_graha_drishti_rasi'")
    expect(migration).toContain("status = 'unresolved'")
    expect(migration).toContain("migration 631 refuses unknown Graha Drishti citation state")
  })

  it('pins the revised exact 14-row contract instead of weakening it', () => {
    expect(migration).toContain("count(*) FILTER (WHERE status='resolved') = 1")
    expect(migration).toContain("count(*) FILTER (WHERE status='unresolved') = 13")
    expect(migration).toContain('f87cfce86ed03e45c166977d4ded62a0a530b6ea8844c4e22f6d5340b9b961be')
    expect(migration).toContain('6ea8c824cd9e51b258d58eea7814491372027d7356c207f62d18eb76477f5b3b')
    expect(migration).toContain("migration 631 citation-integrity contract postflight failed")
    expect(migration).not.toMatch(/^BEGIN;/m)
    expect(migration).not.toMatch(/^COMMIT;/m)
  })
})
