import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const sql = readFileSync(
  resolve(__dirname, '../../../../supabase/migrations/1038_planner_managed_prashna_jobs.sql'),
  'utf8',
)

describe('migration 1038 durable managed Prashna jobs', () => {
  it('binds immutable ownership and request identity to principal, key, and chart', () => {
    expect(sql).toContain('principal_uid text NOT NULL REFERENCES profiles(id) ON DELETE CASCADE')
    expect(sql).toContain('principal_key_id text NOT NULL')
    expect(sql).toContain("principal_auth_kind text NOT NULL CHECK (principal_auth_kind IN ('api_key', 'oauth'))")
    expect(sql).toContain('FOREIGN KEY (api_key_id) REFERENCES mcp_api_keys(key_id) ON DELETE CASCADE')
    expect(sql).toContain('FOREIGN KEY (oauth_token_hash) REFERENCES mcp_oauth_tokens(access_token_hash) ON DELETE CASCADE')
    expect(sql).toContain('planner_managed_prashna_job_credential_guard_trigger')
    expect(sql).toContain('FOR NO KEY UPDATE')
    expect(sql).toContain('WHERE key_id = NEW.api_key_id AND revoked_at IS NULL')
    expect(sql).toContain('chart_id uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE')
    expect(sql).toContain('request_jsonb jsonb NOT NULL')
    expect(sql).toContain('planner_managed_prashna_job_immutable_guard_trigger')
    expect(sql).toContain("hashtextextended('managed-job-id:' || p_job_id::text, 0)")
    expect(sql).toContain("RAISE EXCEPTION 'MANAGED_JOB_IDEMPOTENCY_CONFLICT'")
    expect(sql).toContain('planner managed job credential is no longer active')
  })

  it('makes the table inaccessible directly and exposes only principal-checking functions', () => {
    expect(sql).toContain('REVOKE ALL ON planner_managed_prashna_jobs FROM PUBLIC, role_web_serve')
    expect(sql.match(/REVOKE ALL ON FUNCTION .* FROM PUBLIC;/g)).toHaveLength(8)
    expect(sql).not.toMatch(/GRANT (SELECT|INSERT|UPDATE|DELETE) ON planner_managed_prashna_jobs/)
    expect(sql).toContain("p_principal_uid IS DISTINCT FROM current_setting('app.principal_id', true)")
    expect(sql).toContain('p_chart_id IS DISTINCT FROM public.app_chart_context()')
    expect(sql).toContain('ALTER TABLE planner_managed_prashna_jobs ENABLE ROW LEVEL SECURITY')
  })

  it('bounds admission, leases, retries, results, and retention', () => {
    expect(sql).toContain('recent_count >= 32')
    expect(sql).toContain('active_count >= 8')
    expect(sql).toContain("attempt_count BETWEEN 0 AND 3")
    expect(sql).toContain('current_job.attempt_count >= 3')
    expect(sql).toContain("error_text='MANAGED_JOB_RETRY_EXHAUSTED'")
    expect(sql).toContain("now() + interval '24 hours'")
    expect(sql).toContain('planner_managed_prashna_jobs_state_shape')
    expect(sql).toContain('terminal_worker_id=p_lease_owner')
    expect(sql).toContain('job.result_jsonb IS NOT DISTINCT FROM p_result_jsonb')
    expect(sql).toContain('job.error_text IS NOT DISTINCT FROM bounded_error')
  })

  it('documents a complete destructive DOWN without presenting it as routine cleanup', () => {
    expect(sql).toContain('-- DOWN (manual, destructive; retain/export terminal job evidence before use):')
    expect(sql.match(/^-- DROP /gm)).toHaveLength(9)
  })
})
