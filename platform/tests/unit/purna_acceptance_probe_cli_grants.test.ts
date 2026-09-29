import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { defaultChoiceBody, parseArgs, PROBE_SERVICE_ORIGIN } from '../../scripts/probe/set_default'

// Contract for migration 1119 (Purna owner-surrogate rulings OSR-007/OSR-011): one non-revoked grant
// for the dedicated probe principal on exactly one system-owned, tool-less CLI (claude_code), no
// impersonation, no widening, and no failure on a database that predates the AI Console tables.
const sql = readFileSync(resolve(__dirname, '../../migrations/1119_purna_acceptance_probe_cli_grants.sql'), 'utf8')
const code = sql.split('\n').filter((line) => !line.trim().startsWith('--')).join('\n')

describe('migration 1119 probe CLI grant', () => {
  it('targets exactly the probe principal and exactly claude_code', () => {
    expect(code.match(/'probe-service-account'/g)?.length).toBeGreaterThanOrEqual(5)
    expect(code).toMatch(/VALUES \('probe-service-account', 'claude_code', 'probe-service-account'\)/)
    expect(code).not.toMatch(/'codex'|kimi_code|gemini_antigravity/)
  })

  it('is granted_by the probe itself, never a human admin, and audits both audit tables', () => {
    expect(code).toMatch(/INSERT INTO ai_configuration_audit_log \(user_id, actor_user_id, event, cli_id\)\s+SELECT g\.user_id, g\.user_id, 'cli_granted', g\.cli_id/)
    expect(code).toMatch(/INSERT INTO admin_audit_log \(actor_id, action, target_user_id, detail\)\s+SELECT g\.user_id, 'ai_cli_grant', g\.user_id/)
    expect(code).toContain("'source', 'migration 1119 (Purna OSR-007)'")
    expect(code).not.toMatch(/xl2wYZ|hunQRY/)
  })

  it('never modifies an existing grant (a revocation is preserved) and changes no privilege or role', () => {
    expect(code).toMatch(/ON CONFLICT \(user_id, cli_id\) DO NOTHING/)
    expect(code).not.toMatch(/\bUPDATE\b|\bDELETE\b|\bTRUNCATE\b|\bDROP\b/i)
    expect(code).not.toMatch(/\bGRANT\s+\w+.*\bTO\b|\bREVOKE\b|ALTER\s+(ROLE|USER)|CREATE\s+ROLE|SECURITY\s+DEFINER/i)
    expect(code).not.toMatch(/UPDATE\s+profiles|INSERT\s+INTO\s+profiles/i)
  })

  it('is a NOTICE-only no-op when the AI Console tables, probe profile or installation are absent', () => {
    for (const relation of ['profiles', 'ai_cli_installations', 'ai_cli_grants', 'ai_configuration_audit_log', 'admin_audit_log']) {
      expect(code).toContain(`to_regclass('public.${relation}') IS NULL`)
    }
    expect(code).toContain('AI Console / audit tables not present yet; nothing to grant (no-op)')
    expect(code).toContain('probe-service-account profile absent or inactive; nothing to grant (no-op)')
    expect(code).toContain('claude_code installation row absent; nothing to grant (no-op)')
  })

  it('fails only when the intended grant is missing, and never on extra grants it did not create', () => {
    expect(code).toContain('has no claude_code grant row after insert')
    expect(code).toMatch(/RAISE NOTICE 'migration 1119: probe-service-account holds other active CLI grants/)
    expect(code.match(/RAISE EXCEPTION/g)?.length).toBe(1)
  })

  it('carries no transaction wrapper (the runner owns the transaction)', () => {
    expect(code).not.toMatch(/^\s*(BEGIN|COMMIT);/m)
  })
})

describe('probe set_default script', () => {
  it('accepts only the granted CLI and has no way to redirect the session to another origin', () => {
    expect(parseArgs([]).cliId).toBe('claude_code')
    expect(parseArgs(['--cli', 'claude_code']).cliId).toBe('claude_code')
    expect(() => parseArgs(['--cli', 'codex'])).toThrow()
    expect(() => parseArgs(['--cli', 'kimi_code'])).toThrow()
    expect(() => parseArgs(['--service-url', 'https://example.com'])).toThrow()
    expect(() => parseArgs(['--bogus'])).toThrow()
    expect(new URL(PROBE_SERVICE_ORIGIN).protocol).toBe('https:')
    const source = readFileSync(resolve(__dirname, '../../scripts/probe/set_default.ts'), 'utf8')
    expect(source).toContain("redirect: 'error'")
  })

  it('sends a local_cli choice with the adapter built-in default model and nothing else', () => {
    expect(defaultChoiceBody('claude_code')).toEqual({ choice: { kind: 'local_cli', cliId: 'claude_code', modelId: null } })
  })
})
