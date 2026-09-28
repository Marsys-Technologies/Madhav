import { describe, expect, it } from 'vitest'
import { AI_ROLES } from '../../types'
import { CLI_REGISTRY, buildExecutionArgs, parseSupportedVersion } from '../registry'

describe('closed CLI registry', () => {
  it('registers only the four approved products and enables only inspected headless CLIs', () => {
    expect(Object.keys(CLI_REGISTRY)).toEqual(['codex', 'claude_code', 'gemini_antigravity', 'kimi_code'])
    expect(CLI_REGISTRY.codex.execution).toBeDefined()
    expect(CLI_REGISTRY.codex.compatibleRoles).toEqual(AI_ROLES)
    expect(CLI_REGISTRY.claude_code.execution).toBeDefined()
    expect(CLI_REGISTRY.claude_code.candidates).toEqual(['/Users/Dev/.local/bin/claude'])
    expect(CLI_REGISTRY.claude_code.allowedRealpathPrefixes)
      .toEqual(['/Users/Dev/.local/share/claude/versions/'])
    expect(CLI_REGISTRY.claude_code.interpreter).toBeUndefined()
    expect(CLI_REGISTRY.gemini_antigravity).toMatchObject({
      candidates: ['/Users/Dev/.local/bin/agy'], supportedVersion: '1.2.12',
      compatibleRoles: AI_ROLES,
      modelCatalog: { args: ['models'], format: 'antigravity_models' },
      execution: { transport: 'antigravity_stream_json', outputFormat: 'antigravity_stream_json' },
    })
    expect(CLI_REGISTRY.kimi_code).toMatchObject({
      candidates: ['/Users/Dev/.kimi-code/bin/kimi'], supportedVersion: '2.0.2',
      compatibleRoles: AI_ROLES,
      modelCatalog: { args: ['provider', 'list', '--json'], format: 'kimi_provider_json' },
      execution: { transport: 'kimi_acp', outputFormat: 'kimi_acp_json' },
    })
    expect(Object.isFrozen(CLI_REGISTRY.codex.candidates)).toBe(true)
    expect(Object.isFrozen(CLI_REGISTRY.claude_code.execution!.modelFlag)).toBe(true)
  })

  it('accepts only the independently inspected versions', () => {
    expect(parseSupportedVersion(CLI_REGISTRY.codex, 'codex-cli 0.155.1')).toBe('0.155.1')
    expect(parseSupportedVersion(CLI_REGISTRY.codex, 'codex-cli 0.155.2')).toBeNull()
    expect(parseSupportedVersion(CLI_REGISTRY.claude_code, '2.1.239 (Claude Code)')).toBe('2.1.239')
    expect(parseSupportedVersion(CLI_REGISTRY.claude_code, '2.2.0')).toBeNull()
    expect(parseSupportedVersion(CLI_REGISTRY.gemini_antigravity, 'agy version 1.2.12')).toBe('1.2.12')
    expect(parseSupportedVersion(CLI_REGISTRY.gemini_antigravity, 'agy version 1.1.16')).toBeNull()
    expect(parseSupportedVersion(CLI_REGISTRY.kimi_code, '2.0.2')).toBe('2.0.2')
  })

  it('constructs fixed execution arguments without fallback or user flags', () => {
    const codex = buildExecutionArgs(CLI_REGISTRY.codex, null)
    expect(codex).toEqual(['exec', '--sandbox', 'read-only', '--ephemeral', '--ignore-user-config',
      '--ignore-rules', '--skip-git-repo-check', '--color', 'never', '--json', '--cd', '__CWD__', '-'])
    expect(buildExecutionArgs(CLI_REGISTRY.codex, 'gpt-test', { schemaPath: '__SCHEMA__' }).slice(-5))
      .toEqual(['--model', 'gpt-test', '--output-schema', '__SCHEMA__', '-'])
    const claude = buildExecutionArgs(CLI_REGISTRY.claude_code, null)
    expect(claude).toContain('--no-session-persistence')
    expect(claude).toContain('--strict-mcp-config')
    expect(claude).toContain('--setting-sources')
    expect(claude).toContain('{"mcpServers":{}}')
    expect(claude).not.toContain('--fallback-model')
    expect(claude).not.toContain('--model')
    const selected = buildExecutionArgs(CLI_REGISTRY.claude_code, 'claude-test', { schemaPath: '{}' })
    expect(selected.slice(-4)).toEqual(['--model', 'claude-test', '--json-schema', '{}'])
    expect(buildExecutionArgs(CLI_REGISTRY.gemini_antigravity, 'gemini-3.8-flash-low')).toEqual([
      '--sandbox', '--disable-slash-commands', '--input-format', 'stream-json', '--output-format',
      'stream-json', '--print-timeout', '2m', '--model', 'gemini-3.8-flash-low',
    ])
    expect(buildExecutionArgs(CLI_REGISTRY.kimi_code, 'kimi-code/k3-256k')).toEqual(['acp'])
  })

  it('rejects model argument injection and exposes all four compatible roles', () => {
    expect(() => buildExecutionArgs(CLI_REGISTRY.claude_code, '--help')).toThrow()
    expect(() => buildExecutionArgs(CLI_REGISTRY.claude_code, 'model\n--danger')).toThrow()
    expect(() => buildExecutionArgs(CLI_REGISTRY.claude_code, 'x'.repeat(513))).toThrow()
    expect(CLI_REGISTRY.codex.compatibleRoles).toEqual(AI_ROLES)
    expect(CLI_REGISTRY.claude_code.compatibleRoles).toEqual(AI_ROLES)
    expect(CLI_REGISTRY.gemini_antigravity.compatibleRoles).toEqual(AI_ROLES)
    expect(CLI_REGISTRY.kimi_code.compatibleRoles).toEqual(AI_ROLES)
  })
})
