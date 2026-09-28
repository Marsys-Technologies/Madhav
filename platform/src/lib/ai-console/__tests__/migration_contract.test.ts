import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const path = resolve(__dirname, '../../../../migrations/1124_ai_console_byok_routing.sql')
const tables = ['ai_provider_connections', 'ai_connection_models', 'ai_custom_configurations',
  'ai_custom_configuration_roles', 'ai_user_defaults', 'ai_cli_installations', 'ai_cli_models',
  'ai_cli_grants', 'ai_conversation_selections', 'ai_turn_routing_snapshots',
  'ai_turn_role_invocations', 'ai_configuration_audit_log']

function constraintAllowlist(text: string, name: string, column: string): string[] {
  const start = text.indexOf(`ADD CONSTRAINT ${name}`)
  if (start < 0) throw new Error(`Missing constraint ${name}`)
  const statement = text.slice(start, text.indexOf(';', start))
  const body = statement.match(new RegExp(
    `CHECK\\s*\\(\\s*${column}\\s+IN\\s*\\(([^)]*)\\)\\s*\\)`, 's'))?.[1]
  if (!body) throw new Error(`Missing exact ${column} IN body for ${name}`)
  return [...body.matchAll(/'([^']+)'/g)].map(match => match[1])
}

describe('AI Console governed persistence contract', () => {
  const sql = () => readFileSync(path, 'utf8')
  it('retains distinct audit identities for rename, credential replacement, and duplication', () => {
    for (const event of ['connection_renamed', 'connection_credential_replaced', 'configuration_duplicated']) {
      expect(sql()).toContain(`'${event}'`)
    }
  })
  it('creates twelve idempotent relations inside the canonical runner transaction', () => {
    const text = sql()
    expect(text).not.toMatch(/^\s*(?:BEGIN|START TRANSACTION|COMMIT|ROLLBACK|END)\s*;/im)
    expect(text).toContain('Transaction owned by platform/scripts/migrate.ts')
    const runner = readFileSync(resolve(__dirname, '../../../../scripts/migrate.ts'), 'utf8')
    expect(runner).toMatch(/await client\.query\('BEGIN'\)[\s\S]*?INSERT INTO _migrations_applied[\s\S]*?await client\.query\('COMMIT'\)/)
    expect(text.match(/CREATE TABLE IF NOT EXISTS/g)).toHaveLength(12)
    for (const table of tables) expect(text).toContain(`CREATE TABLE IF NOT EXISTS ${table}`)
    expect(text).not.toMatch(/INSERT INTO (?:public\.)?asset_registry/)
  })
  it('serializes deferred checks without upgrading FK key-share locks', () => {
    const text = sql()
    expect(text).not.toMatch(/FOR UPDATE/)
    expect(text.match(/FOR NO KEY UPDATE/g)).toHaveLength(3)
  })
  it('rejects statement-level history truncation and restricts erasure to the conversation cascade', () => {
    const text = sql()
    expect(text).toContain('BEFORE TRUNCATE ON %I FOR EACH STATEMENT')
    expect(text).toContain('REVOKE UPDATE, DELETE, TRUNCATE ON TABLE %I FROM service_role')
    expect(text).not.toMatch(/GRANT[^;]*TRUNCATE/)
    expect(text).toContain('conversation_id uuid PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE')
    expect(text).toContain('conversation_id uuid REFERENCES conversations(id) ON DELETE CASCADE')
    expect(text).toContain('snapshot_id uuid NOT NULL REFERENCES ai_turn_routing_snapshots(id) ON DELETE CASCADE')
    expect(text).toContain("TG_OP = 'DELETE' AND pg_trigger_depth() > 1")
    expect(text).toContain('NOT EXISTS (SELECT 1 FROM conversations WHERE id = OLD.conversation_id)')
    expect(text).toContain('NOT EXISTS (SELECT 1 FROM ai_turn_routing_snapshots WHERE id = OLD.snapshot_id)')
  })
  it('enforces names, zero-or-one explicit default, choice ownership, and deferred completeness', () => {
    const text = sql()
    expect(text.match(/\(user_id, lower\(name\)\)/g)).toHaveLength(2)
    expect(text).toContain('user_id text PRIMARY KEY REFERENCES profiles(id) ON DELETE RESTRICT')
    expect(text).not.toMatch(/INSERT INTO ai_user_defaults/)
    expect(text).toContain('DEFERRABLE INITIALLY DEFERRED')
    expect(text).toContain('ai_check_four_roles')
    expect(text).toContain('ai_check_conversation_owner')
    expect(text).toContain('FOREIGN KEY (user_id, connection_id)')
    expect(text).toContain('FOREIGN KEY (user_id, configuration_id)')
  })
  it('separates confirmed validity from reachability and supports encryption and tombstones', () => {
    const text = sql()
    for (const field of ['credential_validity', 'validation_state', 'last_validated_at',
      'last_checked_at', 'credential_ciphertext', 'wrapped_dek', 'credential_nonce',
      'credential_tag', 'wrap_nonce', 'wrap_tag', 'kek_version', 'keyed_fingerprint', 'deleted_at']) {
      expect(text).toContain(field)
    }
    expect(text).not.toMatch(/\b(?:api_key|plaintext|access_token|secret_key)\s+(?:text|varchar|bytea)/i)
    expect(text).toContain('ai_configuration_version_guard')
  })
  it('persists explicit per-model tool and structured-output capability evidence', () => {
    const text = sql()
    const providerModel = text.slice(text.indexOf('CREATE TABLE IF NOT EXISTS ai_connection_models'), text.indexOf('CREATE TABLE IF NOT EXISTS ai_cli_installations'))
    const cliModel = text.slice(text.indexOf('CREATE TABLE IF NOT EXISTS ai_cli_models'), text.indexOf('CREATE UNIQUE INDEX IF NOT EXISTS ai_cli_builtin_default_idx'))
    for (const table of [providerModel, cliModel]) {
      expect(table).toMatch(/supports_tools boolean NOT NULL DEFAULT false/)
      expect(table).toMatch(/supports_structured_output boolean NOT NULL DEFAULT false/)
    }
  })
  it('retains immutable snapshots and append-only correlated start/terminal receipts', () => {
    const text = sql()
    expect(text).toContain('UNIQUE (user_id, correlation_id)')
    expect(text).toContain('invocation_id uuid NOT NULL')
    expect(text).toContain('PRIMARY KEY (snapshot_id, role, invocation_id, phase)')
    expect(text).toContain('FOREIGN KEY (snapshot_id, role, invocation_id, start_phase)')
    expect(text).toContain("phase IN ('start', 'terminal')")
    expect(text).toContain('ai_reject_history_mutation')
    expect(text).toContain('BEFORE UPDATE OR DELETE')
    expect(text).toContain('ai_snapshot_shape')
    expect(text).toContain('ON DELETE RESTRICT')
  })
  it('uses closed vocabularies, refresh/grant/correlation indexes, and service-only RLS', () => {
    const text = sql()
    for (const value of ['synthesizer', 'planner', 'deep_planner', 'worker', 'openai',
      'anthropic', 'google', 'xai', 'deepseek', 'kimi', 'openrouter', 'codex',
      'claude_code', 'gemini_antigravity', 'kimi_code', 'unreachable']) expect(text).toContain(`'${value}'`)
    for (const table of tables) expect(text).toContain(`'${table}'`)
    expect(text).toContain('ENABLE ROW LEVEL SECURITY')
    expect(text).toContain('REVOKE ALL ON TABLE')
    expect(text).toContain('TO service_role')
    expect(text).toContain('ai_connections_refresh_idx')
    expect(text).toContain('ai_grants_cli_idx')
    expect(text).toContain('ai_snapshots_conversation_idx')
  })
  it('widens Observatory vocabulary without turning external synthesis into usage', () => {
    const text = sql()
    expect(constraintAllowlist(text, 'llm_usage_events_provider_check', 'provider')).toEqual([
      'anthropic', 'openai', 'gemini', 'deepseek', 'nim', 'xai', 'kimi', 'openrouter', 'cli',
    ])
    expect(constraintAllowlist(text, 'llm_usage_events_pipeline_stage_check', 'pipeline_stage')).toEqual([
      'classify', 'compose', 'retrieve', 'synthesize', 'synthesizer', 'audit', 'other',
      'planner', 'deep_planner', 'worker', 'title', 'history_summary', 'interpretation_sets',
    ])
    expect(constraintAllowlist(text, 'llm_usage_events_status_check', 'status')).toEqual([
      'success', 'error', 'timeout', 'cancelled',
    ])
    expect(text).toContain("call_stage='external_synthesis_handoff'")
    expect(text).toContain('ALTER COLUMN model_id DROP NOT NULL')
    expect(text).toContain('ALTER COLUMN provider DROP NOT NULL')
    expect(text).toContain('llm_call_log_model_provider_shape_check')
    expect(text).toMatch(/call_stage\s*=\s*'external_synthesis_handoff'\s+AND model_id IS NULL AND provider IS NULL/)
    expect(text).toMatch(/call_stage\s*<>\s*'external_synthesis_handoff'\s+AND model_id IS NOT NULL AND provider IS NOT NULL/)
    expect(text).toContain('DROP CONSTRAINT IF EXISTS llm_call_log_model_provider_shape_check')
    expect(text).not.toMatch(/llm_usage_events[^;]*external_synthesis/s)
  })
  it('records validation success and rejection with only a safe error code', () => {
    const text = sql()
    expect(text).toContain("'connection_validation_succeeded'")
    expect(text).toContain("'connection_validation_rejected'")
    expect(text).toMatch(/error_code text CHECK \(error_code IN/)
  })
})
