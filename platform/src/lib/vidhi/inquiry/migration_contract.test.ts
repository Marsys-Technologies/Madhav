import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const sql = readFileSync(resolve(__dirname, '../../../../migrations/1033_planner_inquiry_lifecycle.sql'), 'utf8')
const storePoolSource = readFileSync(resolve(__dirname, 'store_pool.ts'), 'utf8')

describe('migration 1033 planner inquiry lifecycle', () => {
  it('binds durable state to existing principal and chart authorities with bounded receipt retention', () => {
    expect(sql).toMatch(/principal_uid text NOT NULL REFERENCES profiles\(id\) ON DELETE RESTRICT/)
    expect(sql).toMatch(/chart_id uuid NOT NULL REFERENCES charts\(id\) ON DELETE RESTRICT/)
    expect(sql).toMatch(/inquiry_id uuid NOT NULL REFERENCES planner_inquiry_lifecycles\(inquiry_id\) ON DELETE CASCADE/)
    expect(sql).toMatch(/retention_expires_at timestamptz NOT NULL/)
  })

  it('enables RLS for both sensitive tables and excludes the sidecar role', () => {
    expect(sql).toContain('ALTER TABLE planner_inquiry_lifecycles ENABLE ROW LEVEL SECURITY')
    expect(sql).toContain('ALTER TABLE planner_inquiry_evidence_receipts ENABLE ROW LEVEL SECURITY')
    expect(sql).not.toContain('TO role_web_serve, role_sidecar')
    expect(sql.match(/app_chart_context\(\)/g)?.length).toBeGreaterThanOrEqual(4)
  })

  it('grants only lifecycle mutation and immutable evidence insertion needed by the web role', () => {
    expect(sql).toContain('REVOKE INSERT ON planner_inquiry_lifecycles FROM role_web_serve')
    expect(sql).toContain('GRANT SELECT ON planner_inquiry_lifecycles TO role_web_serve')
    expect(sql).toMatch(/GRANT UPDATE \(contract_jsonb, status, revision, current_jti_hash, updated_at\)/)
    expect(sql).toContain('GRANT SELECT, INSERT ON planner_inquiry_evidence_receipts TO role_web_serve')
    expect(sql).not.toMatch(/GRANT[^;]*UPDATE ON planner_inquiry_evidence_receipts/)
    expect(sql).not.toMatch(/GRANT[^;]*DELETE/)
    expect(sql).toContain('planner_inquiry_immutable_guard_trigger')
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
    expect(sql).toMatch(/authorization_jsonb jsonb NOT NULL/)
  })

  it('scopes retention purge and active limits to the authenticated principal and chart', () => {
    expect(sql).toContain('CREATE OR REPLACE FUNCTION create_planner_inquiry_lifecycle(')
    expect(sql).toMatch(/p_principal_uid IS DISTINCT FROM current_setting\('app\.principal_id', true\)/)
    expect(sql).toContain('p_chart_id IS DISTINCT FROM public.app_chart_context()')
    expect(sql).toMatch(/principal_uid=p_principal_uid AND chart_id=p_chart_id/)
    expect(sql).toContain("created_at > now() - interval '1 hour'")
    expect(sql).toContain('recent_count >= 32')
    expect(sql).toContain('active_count >= 8')
    expect(sql).toContain('purge_expired_planner_inquiries_global()')
    const purgeFunction = sql.match(
      /CREATE OR REPLACE FUNCTION purge_expired_planner_inquiries_global\(\)[\s\S]*?\$\$;/,
    )?.[0]
    expect(purgeFunction).toContain('SET search_path = pg_catalog, pg_temp')
    expect(purgeFunction).toContain('DELETE FROM public.planner_inquiry_lifecycles')
    expect(purgeFunction).not.toContain('SET search_path = public')
    expect(sql).toContain('DROP FUNCTION IF EXISTS create_planner_inquiry_lifecycle(uuid, text, uuid')
    expect(sql).toContain('DROP FUNCTION IF EXISTS planner_inquiry_immutable_guard()')
  })

  it('uses a dedicated fail-closed role pool and pins both RLS contexts', () => {
    expect(storePoolSource).toContain('INQUIRY_STORE_DATABASE_URL')
    expect(storePoolSource).toContain('DB_INQUIRY_USER')
    expect(storePoolSource).toContain('DB_INQUIRY_PASSWORD')
    expect(storePoolSource).toContain('refusing to use the broad application pool')
    expect(storePoolSource).not.toContain('process.env.DB_USER')
    expect(storePoolSource).not.toContain('process.env.DB_PASSWORD')
    expect(storePoolSource).toContain("[PRINCIPAL_ID_GUC, principalUid]")
    expect(storePoolSource).toContain("[CHART_CONTEXT_GUC, pinnedChart]")
  })
})
