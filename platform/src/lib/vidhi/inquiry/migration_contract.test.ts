import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const sql = readFileSync(resolve(__dirname, '../../../../migrations/1033_planner_inquiry_lifecycle.sql'), 'utf8')

describe('migration 1033 planner inquiry lifecycle', () => {
  it('binds durable state to existing principal and chart authorities without cascade deletion', () => {
    expect(sql).toMatch(/principal_uid text NOT NULL REFERENCES profiles\(id\) ON DELETE RESTRICT/)
    expect(sql).toMatch(/chart_id uuid NOT NULL REFERENCES charts\(id\) ON DELETE RESTRICT/)
    expect(sql).toMatch(/inquiry_id uuid NOT NULL REFERENCES planner_inquiry_lifecycles\(inquiry_id\) ON DELETE RESTRICT/)
  })

  it('enables RLS for both sensitive tables and excludes the sidecar role', () => {
    expect(sql).toContain('ALTER TABLE planner_inquiry_lifecycles ENABLE ROW LEVEL SECURITY')
    expect(sql).toContain('ALTER TABLE planner_inquiry_evidence_receipts ENABLE ROW LEVEL SECURITY')
    expect(sql).not.toContain('TO role_web_serve, role_sidecar')
    expect(sql.match(/app_chart_context\(\)/g)?.length).toBeGreaterThanOrEqual(4)
  })

  it('grants only lifecycle mutation and immutable evidence insertion needed by the web role', () => {
    expect(sql).toContain('GRANT SELECT, INSERT, UPDATE ON planner_inquiry_lifecycles TO role_web_serve')
    expect(sql).toContain('GRANT SELECT, INSERT ON planner_inquiry_evidence_receipts TO role_web_serve')
    expect(sql).not.toMatch(/GRANT[^;]*UPDATE ON planner_inquiry_evidence_receipts/)
    expect(sql).not.toMatch(/GRANT[^;]*DELETE/)
  })

  it('permits append-only multi-page receipts while preserving revision uniqueness', () => {
    expect(sql).toContain('UNIQUE (inquiry_id, revision)')
    expect(sql).not.toContain('UNIQUE (inquiry_id, plan_item_id)')
    expect(sql).toContain('(inquiry_id, plan_item_id, revision)')
  })

  it('pins semantic, execution-plan, and capability snapshot hashes independently', () => {
    expect(sql).toMatch(/semantic_contract_hash text NOT NULL/)
    expect(sql).toMatch(/execution_plan_hash text NOT NULL/)
    expect(sql).toMatch(/capability_content_hash text NOT NULL/)
  })
})
