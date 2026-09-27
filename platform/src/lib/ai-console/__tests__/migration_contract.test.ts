import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const path = resolve(__dirname, '../../../../migrations/1120_ai_console_byok_routing.sql')
const tables = ['ai_provider_connections', 'ai_connection_models', 'ai_custom_configurations',
  'ai_custom_configuration_roles', 'ai_user_defaults', 'ai_cli_installations', 'ai_cli_models',
  'ai_cli_grants', 'ai_conversation_selections', 'ai_turn_routing_snapshots',
  'ai_turn_role_invocations', 'ai_configuration_audit_log']

describe('AI Console governed persistence contract', () => {
  const sql = () => readFileSync(path, 'utf8')
  it('creates exactly the twelve relations transactionally and idempotently', () => {
    const text = sql()
    expect(text).toMatch(/BEGIN;/)
    expect(text.trim()).toMatch(/COMMIT;$/)
    expect(text.match(/CREATE TABLE IF NOT EXISTS/g)).toHaveLength(12)
    for (const table of tables) expect(text).toContain(`CREATE TABLE IF NOT EXISTS ${table}`)
    expect(text).not.toMatch(/INSERT INTO (?:public\.)?asset_registry/)
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
  it('retains immutable snapshots and append-only correlated start/terminal receipts', () => {
    const text = sql()
    expect(text).toContain('UNIQUE (user_id, correlation_id)')
    expect(text).toContain('PRIMARY KEY (snapshot_id, role, phase)')
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
})
