import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '../../errors'
import * as repository from '../../repository'
import type { CliDefinition } from '../registry'
import type { CliRunner } from '../runner'
import { CLI_BUILTIN_MODEL_DB_ID } from '../types'
import { testAndAddManualCliModel, validateCli, validateMachineOutput } from '../validation'

vi.mock('../../repository', () => ({
  assertCliValidationAuthorized: vi.fn(),
  markCliValidationStarted: vi.fn(),
  storeCliValidation: vi.fn(),
  listConfirmedManualCliModels: vi.fn(),
  storeManualCliModel: vi.fn(),
  restoreCliValidation: vi.fn(),
}))

const attempt = { cliId: 'codex' as const, epoch: '42', previous: { state: 'reachable' as const,
  detectedProduct: 'Codex CLI', detectedVersion: '0.155.1', lastCheckedAt: new Date('2026-09-27T00:00:00Z'),
  errorCode: null } }
const identity = { cliId: 'codex' as const, entrypoint: { realpath: '/fixed/codex', device: '1', inode: '2',
  size: 3, modifiedMs: 4, sha256: 'a'.repeat(64) } }

const definition: CliDefinition = {
  id: 'codex', productName: 'Codex CLI', candidates: ['/fixed/codex'], allowedRealpathPrefixes: ['/fixed/'],
  versionArgs: ['--version'], authStatusArgs: ['login', 'status'], supportedVersion: '0.155.1',
  compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: false,
  supportsStructuredOutput: true, execution: {
    args: ['exec', '--json', '-C', '__CWD__', '-'], modelFlag: ['-m'], outputFormat: 'codex_jsonl',
  },
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(repository.markCliValidationStarted).mockResolvedValue(attempt)
  vi.mocked(repository.storeCliValidation).mockResolvedValue('43')
  vi.mocked(repository.listConfirmedManualCliModels).mockResolvedValue([])
  vi.mocked(repository.restoreCliValidation).mockResolvedValue(true)
})

describe('CLI validation', () => {
  it('tests an exact Claude model through the CLI before persisting and confirming it', async () => {
    const claudeIdentity = { ...identity, cliId: 'claude_code' as const }
    const output = { stdout: JSON.stringify({ type: 'result', subtype: 'success', is_error: false, result: 'OK' }),
      exitCode: 0, signal: null }
    const runner = { inspectInstallation: vi.fn().mockResolvedValue(claudeIdentity),
      runVersionValidation: vi.fn().mockResolvedValue({ stdout: '2.1.284', exitCode: 0, signal: null }),
      runAuthValidation: vi.fn().mockResolvedValue({ stdout: '', exitCode: 0, signal: null }),
      runModelCatalogValidation: vi.fn(), runProbeValidation: vi.fn().mockResolvedValue(output),
      runModelProbeValidation: vi.fn().mockResolvedValue(output), confirmValidation: vi.fn(),
      confirmManualModel: vi.fn(),
    } as unknown as CliRunner
    await testAndAddManualCliModel('alice', 'claude_code', 'claude-test', undefined, runner)
    expect(runner.runModelProbeValidation).toHaveBeenCalledWith('alice', 'claude_code', 'claude-test',
      'Reply with exactly OK.', undefined)
    expect(repository.storeManualCliModel).toHaveBeenCalledWith('alice', 'claude_code', 'claude-test',
      '2.1.284', claudeIdentity.entrypoint.sha256)
    expect(runner.confirmManualModel).toHaveBeenCalledWith('claude_code', claudeIdentity, 'claude-test')
  })

  it('does not persist a CLI candidate that fails its exact-model probe', async () => {
    const claudeIdentity = { ...identity, cliId: 'claude_code' as const }
    const output = { stdout: JSON.stringify({ type: 'result', subtype: 'success', is_error: false, result: 'OK' }),
      exitCode: 0, signal: null }
    const runner = { inspectInstallation: vi.fn().mockResolvedValue(claudeIdentity),
      runVersionValidation: vi.fn().mockResolvedValue({ stdout: '2.1.284', exitCode: 0, signal: null }),
      runAuthValidation: vi.fn().mockResolvedValue({ stdout: '', exitCode: 0, signal: null }),
      runModelCatalogValidation: vi.fn(), runProbeValidation: vi.fn().mockResolvedValue(output),
      runModelProbeValidation: vi.fn().mockResolvedValue({ ...output, stdout: JSON.stringify({
        type: 'result', subtype: 'success', is_error: false, result: 'NO',
      }) }), confirmValidation: vi.fn(), confirmManualModel: vi.fn(),
    } as unknown as CliRunner
    await expect(testAndAddManualCliModel('alice', 'claude_code', 'claude-test', undefined, runner))
      .rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(repository.storeManualCliModel).not.toHaveBeenCalled()
  })

  it('restores a previously tested manual model to the confirmed set after CLI revalidation', async () => {
    vi.mocked(repository.listConfirmedManualCliModels).mockResolvedValueOnce(['approved-model'])
    const output = { stdout: '{"type":"item.completed","item":{"type":"agent_message","text":"OK"}}\n{"type":"turn.completed","usage":{}}',
      exitCode: 0, signal: null }
    const runner = { inspectInstallation: vi.fn().mockResolvedValue(identity), confirmValidation: vi.fn(),
      runVersionValidation: vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.158.0', exitCode: 0, signal: null }),
      runAuthValidation: vi.fn().mockResolvedValue({ stdout: '', exitCode: 0, signal: null }),
      runProbeValidation: vi.fn().mockResolvedValue(output), runModelCatalogValidation: vi.fn(),
    } as unknown as CliRunner
    const result = await validateCli('alice', 'codex', undefined, { runner })
    expect(result.state).toBe('reachable')
    expect(runner.confirmValidation).toHaveBeenCalledWith('codex', identity, '0.158.0', [null, 'approved-model'])
  })

  it('discovers and persists a subscription model catalog without retaining provider secrets', async () => {
    const catalogDefinition: CliDefinition = {
      ...definition,
      id: 'kimi_code', productName: 'Kimi Code', candidates: ['/fixed/kimi'], supportedVersion: '2.0.2',
      authStatusArgs: undefined,
      modelCatalog: { args: ['provider', 'list', '--json'], format: 'kimi_provider_json' },
      supportsStructuredOutput: false,
      execution: { args: ['acp'], modelFlag: [], outputFormat: 'kimi_acp_json', transport: 'kimi_acp' },
    }
    const kimiIdentity = { ...identity, cliId: 'kimi_code' as const }
    const runModelCatalogValidation = vi.fn().mockResolvedValue([
      { modelId: 'kimi-code/k3', displayName: 'K3' },
      { modelId: 'kimi-code/k3-256k', displayName: 'K3-256k' },
    ])
    const confirmValidation = vi.fn()
    const runner = { inspectInstallation: vi.fn().mockReturnValue(kimiIdentity), confirmValidation,
      runVersionValidation: vi.fn().mockResolvedValue({ stdout: '2.0.2', exitCode: 0, signal: null }),
      runAuthValidation: vi.fn(), runModelCatalogValidation,
      runProbeValidation: vi.fn().mockResolvedValue({ stdout: JSON.stringify({ text: 'OK' }),
        exitCode: 0, signal: null }) } as unknown as CliRunner

    const result = await validateCli('alice', 'kimi_code', undefined,
      { runner, registry: { kimi_code: catalogDefinition } })

    expect(runModelCatalogValidation).toHaveBeenCalledWith('alice', 'kimi_code', undefined)
    expect(runner.runAuthValidation).not.toHaveBeenCalled()
    expect(result).toMatchObject({ state: 'reachable', modelCount: 3 })
    const persisted = vi.mocked(repository.storeCliValidation).mock.calls[0][1]
    expect(persisted.models).toEqual([
      expect.objectContaining({ modelId: CLI_BUILTIN_MODEL_DB_ID, isBuiltinDefault: true }),
      expect.objectContaining({ modelId: 'kimi-code/k3', displayName: 'K3', isBuiltinDefault: false }),
      expect.objectContaining({ modelId: 'kimi-code/k3-256k', displayName: 'K3-256k', isBuiltinDefault: false }),
    ])
    expect(confirmValidation).toHaveBeenCalledWith('kimi_code', kimiIdentity, '2.0.2',
      [null, 'kimi-code/k3', 'kimi-code/k3-256k'])
    expect(JSON.stringify(persisted)).not.toContain('secret')
  })

  it('grant-gates before detection, discards auth identity, and persists one built-in default', async () => {
    const version = vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.155.1', exitCode: 0, signal: null })
    const auth = vi.fn().mockResolvedValue({ stdout: '{"account":"private@example.com"}', exitCode: 0, signal: null })
    const probe = vi.fn().mockResolvedValue({ stdout: '{"type":"item.completed","item":{"type":"agent_message","text":"OK"}}\n{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}', exitCode: 0, signal: null })
    const inspectInstallation = vi.fn().mockReturnValue(identity); const confirmValidation = vi.fn()
    const runner = { inspectInstallation, confirmValidation, runVersionValidation: version, runAuthValidation: auth,
      runProbeValidation: probe } as unknown as CliRunner
    const result = await validateCli('alice', 'codex', undefined, { runner, registry: { codex: definition } })
    expect(repository.assertCliValidationAuthorized).toHaveBeenCalledWith('alice', 'codex')
    expect(repository.markCliValidationStarted).toHaveBeenCalledWith('codex')
    expect(auth).toHaveBeenCalledWith('alice', 'codex', undefined)
    expect(probe).toHaveBeenCalledWith('alice', 'codex', 'Reply with exactly OK.', undefined)
    expect(confirmValidation).toHaveBeenCalledWith('codex', identity, '0.155.1', [null])
    expect(result).toEqual({ cliId: 'codex', productName: 'Codex CLI', state: 'reachable',
      detectedVersion: '0.155.1', modelCount: 1 })
    const persisted = vi.mocked(repository.storeCliValidation).mock.calls[0][1]
    expect(JSON.stringify(persisted)).not.toContain('private@example.com')
    expect(persisted.models?.[0]).toMatchObject({ modelId: CLI_BUILTIN_MODEL_DB_ID, isBuiltinDefault: true })
  })

  it('rejects unsupported versions before auth or generation', async () => {
    const version = vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.155.2', exitCode: 0, signal: null })
    const auth = vi.fn(); const probe = vi.fn()
    const runner = { inspectInstallation: vi.fn().mockReturnValue(identity), confirmValidation: vi.fn(),
      runVersionValidation: version, runAuthValidation: auth,
      runProbeValidation: probe } as unknown as CliRunner
    const result = await validateCli('alice', 'codex', undefined, { runner, registry: { codex: definition } })
    expect(result.state).toBe('needs_attention')
    expect(version).toHaveBeenCalledOnce(); expect(auth).not.toHaveBeenCalled(); expect(probe).not.toHaveBeenCalled()
    expect(repository.storeCliValidation).toHaveBeenCalledWith('codex',
      expect.objectContaining({ state: 'needs_attention' }), '42')
  })

  it('maps auth failure without retaining auth output and marks unsupported products unavailable', async () => {
    const runner = { inspectInstallation: vi.fn().mockReturnValue(identity), confirmValidation: vi.fn(),
      runVersionValidation: vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.155.1', exitCode: 0, signal: null }),
      runAuthValidation: vi.fn().mockRejectedValue(new AiConsoleError('AI_CLI_UNREACHABLE')),
      runProbeValidation: vi.fn() } as unknown as CliRunner
    expect((await validateCli('alice', 'codex', undefined, { runner, registry: { codex: definition } })).state)
      .toBe('auth_unavailable')
    expect((await validateCli('alice', 'kimi_code', undefined, { runner,
      registry: { kimi_code: { ...definition, id: 'kimi_code', productName: 'Kimi Code', candidates: [],
        authStatusArgs: undefined, execution: undefined } } })).state)
      .toBe('not_installed')
  })

  it('detects Codex without invoking it and keeps it unavailable for execution', async () => {
    const inspectInstallation = vi.fn().mockReturnValue({ cliId: 'codex', fingerprint: 'fixed-installation' })
    const runVersionValidation = vi.fn(); const runAuthValidation = vi.fn(); const runProbeValidation = vi.fn()
    const runner = { inspectInstallation, runVersionValidation, runAuthValidation,
      runProbeValidation } as unknown as CliRunner
    const codex = { ...definition, execution: undefined, authStatusArgs: undefined,
      compatibleRoles: [], supportsStructuredOutput: false }
    await expect(validateCli('alice', 'codex', undefined, { runner, registry: { codex } })).resolves.toEqual({
      cliId: 'codex', productName: 'Codex CLI', state: 'needs_attention', modelCount: 0,
      errorCode: 'AI_CLI_UNREACHABLE',
    })
    expect(inspectInstallation).toHaveBeenCalledWith('codex')
    expect(runVersionValidation).not.toHaveBeenCalled()
    expect(runAuthValidation).not.toHaveBeenCalled()
    expect(runProbeValidation).not.toHaveBeenCalled()
    expect(repository.storeCliValidation).toHaveBeenCalledWith('codex', {
      state: 'needs_attention', detectedProduct: 'Codex CLI', errorCode: 'AI_CLI_UNREACHABLE',
    }, '42')
  })

  it('restores the prior state when revocation interrupts a current validation attempt', async () => {
    const runner = { inspectInstallation: vi.fn().mockReturnValue(identity), confirmValidation: vi.fn(),
      runVersionValidation: vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.155.1', exitCode: 0, signal: null }),
      runAuthValidation: vi.fn().mockRejectedValue(new AiConsoleError('AI_CLI_NOT_GRANTED')),
      runProbeValidation: vi.fn() } as unknown as CliRunner
    await expect(validateCli('alice', 'codex', undefined, { runner, registry: { codex: definition } }))
      .rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })
    expect(repository.restoreCliValidation).toHaveBeenCalledWith(attempt)
  })

  it('restores the prior state when caller abort interrupts validation', async () => {
    const controller = new AbortController()
    const runner = { inspectInstallation: vi.fn().mockReturnValue(identity), confirmValidation: vi.fn(),
      runVersionValidation: vi.fn().mockImplementation(async () => {
      controller.abort(); throw new AiConsoleError('AI_EXECUTION_FAILED')
    }), runAuthValidation: vi.fn(), runProbeValidation: vi.fn() } as unknown as CliRunner
    await expect(validateCli('alice', 'codex', controller.signal, { runner, registry: { codex: definition } }))
      .rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(repository.restoreCliValidation).toHaveBeenCalledWith(attempt)
  })

  it('fails a stale validation outcome instead of publishing or returning it', async () => {
    vi.mocked(repository.storeCliValidation).mockResolvedValue(null)
    const confirmValidation = vi.fn()
    const runner = { inspectInstallation: vi.fn().mockReturnValue(identity), confirmValidation,
      runVersionValidation: vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.155.1', exitCode: 0, signal: null }),
      runAuthValidation: vi.fn().mockResolvedValue({ stdout: '', exitCode: 0, signal: null }),
      runProbeValidation: vi.fn().mockResolvedValue({ stdout: '{"type":"item.completed","item":{"type":"agent_message","text":"OK"}}\n{"type":"turn.completed","usage":{}}', exitCode: 0, signal: null }) } as unknown as CliRunner
    await expect(validateCli('alice', 'codex', undefined, { runner, registry: { codex: definition } }))
      .rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(confirmValidation).not.toHaveBeenCalled()
  })

  it('withdraws a just-published model when executable identity confirmation fails', async () => {
    vi.mocked(repository.storeCliValidation).mockResolvedValueOnce('43').mockResolvedValueOnce('44')
    const runner = { inspectInstallation: vi.fn().mockReturnValue(identity),
      confirmValidation: vi.fn(() => { throw new AiConsoleError('AI_CLI_UNREACHABLE') }),
      runVersionValidation: vi.fn().mockResolvedValue({ stdout: 'codex-cli 0.155.1', exitCode: 0, signal: null }),
      runAuthValidation: vi.fn().mockResolvedValue({ stdout: '', exitCode: 0, signal: null }),
      runProbeValidation: vi.fn().mockResolvedValue({ stdout: '{"type":"item.completed","item":{"type":"agent_message","text":"OK"}}\n{"type":"turn.completed","usage":{}}', exitCode: 0, signal: null }) } as unknown as CliRunner
    await expect(validateCli('alice', 'codex', undefined, { runner, registry: { codex: definition } }))
      .resolves.toMatchObject({ state: 'needs_attention', errorCode: 'AI_CLI_UNREACHABLE', modelCount: 0 })
    expect(repository.storeCliValidation).toHaveBeenNthCalledWith(2, 'codex', expect.objectContaining({
      state: 'needs_attention', errorCode: 'AI_CLI_UNREACHABLE',
    }), '43')
  })

  it('strictly parses only demonstrated machine output shapes', () => {
    expect(validateMachineOutput('codex_jsonl', '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}\n{"type":"turn.completed","usage":{}}')).toMatchObject({ text: 'hello' })
    expect(validateMachineOutput('claude_json', '{"type":"result","subtype":"success","is_error":false,"result":"hello","usage":{"input_tokens":2,"output_tokens":3}}')).toMatchObject({ text: 'hello', usage: { inputTokens: 2, outputTokens: 3, totalTokens: 5 } })
    expect(validateMachineOutput('antigravity_stream_json', [
      JSON.stringify({ event: 'init', init: { cwd: '/tmp/isolated', permission_mode: 'always-proceed', tools: [] } }),
      JSON.stringify({ event: 'step_update', step_update: { step_type: 'agent_response', state: 'DONE', text_delta: 'hello' } }),
      JSON.stringify({ event: 'result', result: { status: 'SUCCESS', response: 'hello',
        usage: { input_tokens: 2, output_tokens: 3, total_tokens: 5 } } }),
    ].join('\n'))).toMatchObject({ text: 'hello', usage: { inputTokens: 2, outputTokens: 3, totalTokens: 5 } })
    expect(validateMachineOutput('kimi_acp_json', '{"text":"hello"}')).toMatchObject({ text: 'hello' })
    expect(() => validateMachineOutput('codex_jsonl', '{broken')).toThrow()
    expect(() => validateMachineOutput('claude_json', '{"result":"hello","is_error":true}')).toThrow()
    expect(() => validateMachineOutput('antigravity_stream_json', [
      JSON.stringify({ event: 'init', init: { cwd: '/tmp', permission_mode: 'always-proceed', tools: [] } }),
      JSON.stringify({ event: 'step_update', step_update: { step_type: 'tool', state: 'DONE' } }),
      JSON.stringify({ event: 'result', result: { status: 'SUCCESS', response: 'unsafe' } }),
    ].join('\n'))).toThrow()
  })

  it.each([
    ['partial answer', '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}'],
    ['terminal before answer', '{"type":"turn.completed","usage":{}}\n{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}'],
    ['duplicate terminal', '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}\n{"type":"turn.completed","usage":{}}\n{"type":"turn.completed","usage":{}}'],
    ['failure event', '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}\n{"type":"turn.failed","error":{"message":"private"}}\n{"type":"turn.completed","usage":{}}'],
    ['event after terminal', '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}\n{"type":"turn.completed","usage":{}}\n{"type":"thread.started"}'],
  ])('rejects Codex JSONL with %s', (_name, stdout) => {
    expect(() => validateMachineOutput('codex_jsonl', stdout)).toThrowError(AiConsoleError)
  })
})
