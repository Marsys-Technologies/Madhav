import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '../../errors'
import * as repository from '../../repository'
import type { CliDefinition } from '../registry'
import type { CliRunner } from '../runner'
import { CLI_BUILTIN_MODEL_DB_ID } from '../types'
import { validateCli, validateMachineOutput } from '../validation'

vi.mock('../../repository', () => ({
  assertCliValidationAuthorized: vi.fn(),
  markCliValidationStarted: vi.fn(),
  storeCliValidation: vi.fn(),
}))

const definition: CliDefinition = {
  id: 'codex', productName: 'Codex CLI', candidates: ['/fixed/codex'], allowedRealpathPrefixes: ['/fixed/'],
  versionArgs: ['--version'], authStatusArgs: ['login', 'status'], supportedVersion: '0.155.1',
  compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: false,
  supportsStructuredOutput: true, execution: {
    args: ['exec', '--json', '-C', '__CWD__', '-'], modelFlag: ['-m'], outputFormat: 'codex_jsonl',
  },
}

beforeEach(() => vi.clearAllMocks())

describe('CLI validation', () => {
  it('grant-gates before detection, discards auth identity, and persists one built-in default', async () => {
    const version = vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.155.1', exitCode: 0, signal: null })
    const auth = vi.fn().mockResolvedValue({ stdout: '{"account":"private@example.com"}', exitCode: 0, signal: null })
    const probe = vi.fn().mockResolvedValue({ stdout: '{"type":"item.completed","item":{"type":"agent_message","text":"OK"}}\n{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}', exitCode: 0, signal: null })
    const runner = { runVersionValidation: version, runAuthValidation: auth,
      runProbeValidation: probe } as unknown as CliRunner
    const result = await validateCli('alice', 'codex', undefined, { runner, registry: { codex: definition } })
    expect(repository.assertCliValidationAuthorized).toHaveBeenCalledWith('alice', 'codex')
    expect(repository.markCliValidationStarted).toHaveBeenCalledWith('codex')
    expect(auth).toHaveBeenCalledWith('alice', 'codex', undefined)
    expect(probe).toHaveBeenCalledWith('alice', 'codex', 'Reply with exactly OK.', undefined)
    expect(result).toEqual({ cliId: 'codex', productName: 'Codex CLI', state: 'reachable',
      detectedVersion: '0.155.1', modelCount: 1 })
    const persisted = vi.mocked(repository.storeCliValidation).mock.calls[0][1]
    expect(JSON.stringify(persisted)).not.toContain('private@example.com')
    expect(persisted.models?.[0]).toMatchObject({ modelId: CLI_BUILTIN_MODEL_DB_ID, isBuiltinDefault: true })
  })

  it('rejects unsupported versions before auth or generation', async () => {
    const version = vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.155.2', exitCode: 0, signal: null })
    const auth = vi.fn(); const probe = vi.fn()
    const runner = { runVersionValidation: version, runAuthValidation: auth,
      runProbeValidation: probe } as unknown as CliRunner
    const result = await validateCli('alice', 'codex', undefined, { runner, registry: { codex: definition } })
    expect(result.state).toBe('needs_attention')
    expect(version).toHaveBeenCalledOnce(); expect(auth).not.toHaveBeenCalled(); expect(probe).not.toHaveBeenCalled()
    expect(repository.storeCliValidation).toHaveBeenCalledWith('codex', expect.objectContaining({ state: 'needs_attention' }))
  })

  it('maps auth failure without retaining auth output and marks unsupported products unavailable', async () => {
    const runner = { runVersionValidation: vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.155.1', exitCode: 0, signal: null }),
      runAuthValidation: vi.fn().mockRejectedValue(new AiConsoleError('AI_CLI_UNREACHABLE')),
      runProbeValidation: vi.fn() } as unknown as CliRunner
    expect((await validateCli('alice', 'codex', undefined, { runner, registry: { codex: definition } })).state)
      .toBe('auth_unavailable')
    expect((await validateCli('alice', 'kimi_code', undefined, { runner,
      registry: { kimi_code: { ...definition, id: 'kimi_code', productName: 'Kimi Code', execution: undefined } } })).state)
      .toBe('not_installed')
  })

  it('strictly parses only demonstrated machine output shapes', () => {
    expect(validateMachineOutput('codex_jsonl', '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}\n{"type":"turn.completed","usage":{}}')).toMatchObject({ text: 'hello' })
    expect(validateMachineOutput('claude_json', '{"type":"result","subtype":"success","is_error":false,"result":"hello","usage":{"input_tokens":2,"output_tokens":3}}')).toMatchObject({ text: 'hello', usage: { inputTokens: 2, outputTokens: 3, totalTokens: 5 } })
    expect(() => validateMachineOutput('codex_jsonl', '{broken')).toThrow()
    expect(() => validateMachineOutput('claude_json', '{"result":"hello","is_error":true}')).toThrow()
  })
})
