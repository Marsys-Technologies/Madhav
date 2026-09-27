import { describe, expect, it } from 'vitest'
import { AI_ROLES } from '../../types'
import { CLI_REGISTRY, buildExecutionArgs, parseSupportedVersion } from '../registry'

describe('closed CLI registry', () => {
  it('registers only the four approved products and enables only inspected headless CLIs', () => {
    expect(Object.keys(CLI_REGISTRY)).toEqual(['codex', 'claude_code', 'gemini_antigravity', 'kimi_code'])
    expect(CLI_REGISTRY.codex.execution).toBeUndefined()
    expect(CLI_REGISTRY.codex.compatibleRoles).toEqual([])
    expect(CLI_REGISTRY.claude_code.execution).toBeDefined()
    expect(CLI_REGISTRY.gemini_antigravity.execution).toBeUndefined()
    expect(CLI_REGISTRY.kimi_code.execution).toBeUndefined()
    expect(Object.isFrozen(CLI_REGISTRY.codex.candidates)).toBe(true)
    expect(Object.isFrozen(CLI_REGISTRY.claude_code.execution!.modelFlag)).toBe(true)
  })

  it('accepts only the independently inspected versions', () => {
    expect(parseSupportedVersion(CLI_REGISTRY.codex, 'codex-cli 0.155.1')).toBe('0.155.1')
    expect(parseSupportedVersion(CLI_REGISTRY.codex, 'codex-cli 0.155.2')).toBeNull()
    expect(parseSupportedVersion(CLI_REGISTRY.claude_code, '2.1.56 (Claude Code)')).toBe('2.1.56')
    expect(parseSupportedVersion(CLI_REGISTRY.claude_code, '2.2.0')).toBeNull()
  })

  it('constructs fixed execution arguments without fallback or user flags', () => {
    expect(() => buildExecutionArgs(CLI_REGISTRY.codex, null)).toThrow()
    const claude = buildExecutionArgs(CLI_REGISTRY.claude_code, null)
    expect(claude).toContain('--no-session-persistence')
    expect(claude).toContain('--strict-mcp-config')
    expect(claude).toContain('--setting-sources')
    expect(claude).toContain('{}')
    expect(claude).not.toContain('--fallback-model')
    expect(claude).not.toContain('--model')
    const selected = buildExecutionArgs(CLI_REGISTRY.claude_code, 'claude-test', { schemaPath: '{}' })
    expect(selected.slice(-4)).toEqual(['--model', 'claude-test', '--json-schema', '{}'])
  })

  it('rejects model argument injection and exposes all four compatible roles', () => {
    expect(() => buildExecutionArgs(CLI_REGISTRY.claude_code, '--help')).toThrow()
    expect(() => buildExecutionArgs(CLI_REGISTRY.claude_code, 'model\n--danger')).toThrow()
    expect(() => buildExecutionArgs(CLI_REGISTRY.claude_code, 'x'.repeat(513))).toThrow()
    expect(CLI_REGISTRY.codex.compatibleRoles).toEqual([])
    expect(CLI_REGISTRY.claude_code.compatibleRoles).toEqual(AI_ROLES)
  })
})
