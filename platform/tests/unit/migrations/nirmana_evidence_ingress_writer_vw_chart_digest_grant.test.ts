import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const sql = readFileSync(
  join(process.cwd(), 'migrations/1031_nirmana_evidence_ingress_writer_vw_chart_digest_grant.sql'),
  'utf8',
)

describe('migration 1031: bo_samvada verifier view grant', () => {
  it('grants only SELECT on the exact digest view to the ingress verifier', () => {
    expect(sql).toContain("'nirmana_evidence_ingress_writer'")
    expect(sql).toContain("'vw_chart_digest'")
    expect(sql).toContain("'SELECT'")
    expect(sql).toMatch(/GRANT SELECT ON TABLE %I\.%I TO nirmana_evidence_ingress_writer/)
    expect(sql).not.toMatch(/GRANT\s+ALL/i)
    expect(sql).not.toMatch(/GRANT\s+(?:INSERT|UPDATE|DELETE|TRUNCATE|REFERENCES|TRIGGER)/i)
  })

  it('fails closed unless the verifier role and view already exist', () => {
    expect(sql).toContain('FROM pg_roles')
    expect(sql).toContain('to_regclass')
    expect(sql).toContain('RAISE EXCEPTION')
    expect(sql).toContain('has_table_privilege')
  })
})
