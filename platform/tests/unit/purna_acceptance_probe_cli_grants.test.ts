import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { defaultChoiceBody, parseArgs } from '../../scripts/probe/set_default'

// Contract for migration 1119 (Purna owner-surrogate ruling OSR-007): one non-revoked grant for the
// dedicated probe principal on exactly two system-owned CLIs, no impersonation, no widening.
const sql = readFileSync(resolve(__dirname, '../../migrations/1119_purna_acceptance_probe_cli_grants.sql'), 'utf8')
const code = sql.split('\n').filter((line) => !line.trim().startsWith('--')).join('\n')

describe('migration 1119 probe CLI grants', () => {
  it('targets exactly the probe principal and exactly codex + claude_code', () => {
    expect(code.match(/'probe-service-account'/g)?.length).toBeGreaterThanOrEqual(3)
    expect(code).toMatch(/i\.cli_id IN \('codex', 'claude_code'\)/)
    expect(code).not.toMatch(/kimi_code|gemini_antigravity/)
  })

  it('is granted_by the probe itself, never a human admin, and audits honestly', () => {
    expect(code).toMatch(/INSERT INTO ai_cli_grants \(user_id, cli_id, granted_by\)\s+SELECT t\.user_id, t\.cli_id, t\.user_id/)
    expect(code).toMatch(/INSERT INTO ai_configuration_audit_log \(user_id, actor_user_id, event, cli_id\)\s+SELECT g\.user_id, g\.user_id, 'cli_granted', g\.cli_id/)
    expect(code).not.toMatch(/xl2wYZ|hunQRY/)
  })

  it('never modifies an existing grant (a revocation is preserved) and changes no privilege or role', () => {
    expect(code).toMatch(/ON CONFLICT \(user_id, cli_id\) DO NOTHING/)
    expect(code).not.toMatch(/\bUPDATE\b|\bDELETE\b|\bTRUNCATE\b|\bDROP\b/i)
    expect(code).not.toMatch(/\bGRANT\s+\w+.*\bTO\b|\bREVOKE\b|ALTER\s+(ROLE|USER)|CREATE\s+ROLE|SECURITY\s+DEFINER/i)
    expect(code).not.toMatch(/profiles\s+SET|UPDATE\s+profiles|INSERT\s+INTO\s+profiles/i)
  })

  it('is a no-op without the probe profile and fails closed on an out-of-scope active grant', () => {
    expect(code).toContain("migration 1119: probe-service-account profile absent or inactive; nothing to grant (no-op)")
    expect(code).toContain("unexpected active grant for probe-service-account outside codex/claude_code")
  })

  it('carries no transaction wrapper (the runner owns the transaction)', () => {
    expect(code).not.toMatch(/^\s*(BEGIN|COMMIT);/m)
  })
})

describe('probe set_default script', () => {
  it('accepts only the two granted CLIs and a plain https origin', () => {
    expect(parseArgs([]).cliId).toBe('codex')
    expect(parseArgs(['--cli', 'claude_code']).cliId).toBe('claude_code')
    expect(() => parseArgs(['--cli', 'kimi_code'])).toThrow()
    expect(() => parseArgs(['--service-url', 'http://example.com'])).toThrow()
    expect(() => parseArgs(['--service-url', 'https://user:pw@example.com'])).toThrow()
    expect(() => parseArgs(['--bogus'])).toThrow()
  })

  it('sends a local_cli choice with the adapter built-in default model and nothing else', () => {
    expect(defaultChoiceBody('codex')).toEqual({ choice: { kind: 'local_cli', cliId: 'codex', modelId: null } })
  })
})
