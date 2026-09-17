import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const sql = readFileSync(resolve(__dirname, '../../../../migrations/1040_planner_inquiry_successor_lifecycle.sql'), 'utf8')

describe('migration 1040 planner inquiry successor lifecycle', () => {
  it('keeps lineage relational and retention-safe', () => {
    expect(sql).toMatch(/ADD COLUMN IF NOT EXISTS parent_inquiry_id uuid[\s\S]*?REFERENCES planner_inquiry_lifecycles\(inquiry_id\) ON DELETE RESTRICT/)
    expect(sql).toMatch(/DELETE FROM public\.planner_inquiry_lifecycles parent[\s\S]*?NOT EXISTS \([\s\S]*?child\.parent_inquiry_id=parent\.inquiry_id/)
  })

  it('requires a terminal blocked parent and a bound successor snapshot', () => {
    expect(sql).toContain("p_parent_final_contract->>'status' IS DISTINCT FROM 'BLOCKED'")
    expect(sql).toContain("p_contract_jsonb#>'{successor,parent_contract}' IS DISTINCT FROM p_parent_final_contract")
    expect(sql).toContain("p_parent_final_contract - 'status' - 'status_reasons'")
    expect(sql).toContain("reason='evidence-admitted successor issued'")
  })

  it('refuses continuation while a parent action is still active', () => {
    expect(sql).toMatch(/reservation\.state IN \('reserved', 'dispatched'\)/)
    expect(sql).toContain("RAISE EXCEPTION 'INQUIRY_ACTION_IN_PROGRESS'")
  })

  it('uses a fixed-path security-definer primitive with no public execute grant', () => {
    expect(sql).toContain('CREATE OR REPLACE FUNCTION create_planner_inquiry_successor_lifecycle(')
    expect(sql).toContain('SECURITY DEFINER')
    expect(sql).toContain('SET search_path = pg_catalog, pg_temp')
    expect(sql).toContain('REVOKE ALL ON FUNCTION create_planner_inquiry_successor_lifecycle(')
    expect(sql).toContain(') FROM PUBLIC;')
    expect(sql).toContain(') TO role_web_serve;')
  })

  it('closes the temporary protected-owner edge before migration success', () => {
    expect(sql).toContain("EXECUTE format('REVOKE purna_inquiry_owner FROM %I', session_user)")
    expect(sql).toContain('protected-owner membership cleanup did not converge')
    expect(sql).not.toMatch(/^BEGIN;|^COMMIT;$/m)
  })
})
