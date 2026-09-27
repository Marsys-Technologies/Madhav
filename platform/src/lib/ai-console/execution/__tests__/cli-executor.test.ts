import { describe, expect, it, vi } from 'vitest'
import { createCliRoleExecutor } from '../cli-executor'
import { createRoleExecutor } from '../index'
import type { ResolvedRoleExecution } from '../types'
import type { CliRunner } from '../../cli/runner'

function execution(overrides: Partial<ResolvedRoleExecution> = {}): ResolvedRoleExecution {
  return {
    role: 'planner', adapterType: 'cli', target: { kind: 'local_cli', cliId: 'claude_code', modelId: null },
    capabilities: { supportsTools: false, supportsStructuredOutput: true }, cliUserId: 'alice', ...overrides,
  }
}

const request = { systemPrompt: 'system', messages: [{ role: 'user' as const, content: 'question' }] }

describe('CLI role executor', () => {
  it('rejects a registered detect-only CLI as unreachable', () => {
    expect(() => createCliRoleExecutor(execution({ target: {
      kind: 'local_cli', cliId: 'codex', modelId: null,
    } }))).toThrowError(expect.objectContaining({ code: 'AI_CLI_UNREACHABLE' }))
  })

  it('is selected by the common executor factory', () => {
    expect(createRoleExecutor(execution()).descriptor).toMatchObject({ cliId: 'claude_code', modelId: null })
  })
  it('uses the exact CLI/default and maps machine output to the common contract', async () => {
    const runExecution = vi.fn().mockResolvedValue({ stdout:
      '{"type":"result","subtype":"success","is_error":false,"result":"answer","usage":{"input_tokens":2,"output_tokens":3}}',
    exitCode: 0, signal: null })
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })
    await expect(executor.generate(request)).resolves.toMatchObject({ text: 'answer', finishReason: 'stop',
      usage: { inputTokens: 2, outputTokens: 3, totalTokens: 5 }, retryCount: 0 })
    expect(runExecution.mock.calls[0][0]).toBe('alice')
    expect(runExecution.mock.calls[0][1]).toBe('claude_code')
    expect(runExecution.mock.calls[0][2]).toMatchObject({ modelId: null })
    expect(runExecution.mock.calls[0][2].stdin).toContain('system')
  })

  it('fails tool-bearing work locally before spawning', async () => {
    const runExecution = vi.fn()
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })
    await expect(executor.generate({ ...request, tools: [{ name: 'unsafe', description: 'x', parameters: {} }] }))
      .rejects.toMatchObject({ code: 'AI_ROLE_INCOMPATIBLE' })
    expect(runExecution).not.toHaveBeenCalled()
  })

  it('passes structured schemas only through the fixed adapter channel and validates the result', async () => {
    const runExecution = vi.fn().mockResolvedValue({ stdout:
      '{"type":"result","subtype":"success","is_error":false,"result":"{\\"ok\\":true}","structured_output":{"ok":true},"usage":{}}',
    exitCode: 0, signal: null })
    const target = execution({ target: { kind: 'local_cli', cliId: 'claude_code', modelId: null } })
    const executor = createCliRoleExecutor(target, { runner: { runExecution } as unknown as CliRunner })
    const schema = { type: 'object' as const, properties: { ok: { type: 'boolean' as const } }, required: ['ok'] }
    await expect(executor.generate({ ...request, responseSchema: schema })).resolves.toMatchObject({ structured: { ok: true } })
    expect(runExecution.mock.calls[0][2]).toMatchObject({ responseSchema: schema })
  })

  it('retries only the identical target once for a transient pre-output failure', async () => {
    const runExecution = vi.fn()
      .mockRejectedValueOnce(Object.assign(new Error('hidden'), { code: 'ETIMEDOUT' }))
      .mockResolvedValueOnce({ stdout:
        '{"type":"result","subtype":"success","is_error":false,"result":"answer","usage":{}}',
      exitCode: 0, signal: null })
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })
    await expect(executor.generate(request)).resolves.toMatchObject({ retryCount: 1 })
    expect(runExecution).toHaveBeenCalledTimes(2)
    expect(runExecution.mock.calls[1]).toEqual(runExecution.mock.calls[0])
  })

  it('streams with pull-driven emission and forwards caller cancellation', async () => {
    let invocationSignal: AbortSignal | undefined
    const runExecution = vi.fn().mockResolvedValue({ stdout:
      '{"type":"result","subtype":"success","is_error":false,"result":"answer","usage":{}}',
    exitCode: 0, signal: null }).mockImplementation((_userId, _cliId, input) => {
      invocationSignal = input.signal
      return Promise.resolve({ stdout:
        '{"type":"result","subtype":"success","is_error":false,"result":"answer","usage":{}}',
      exitCode: 0, signal: null })
    })
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })
    const reader = executor.stream(request).getReader()
    await expect(reader.read()).resolves.toEqual({ done: false, value: { type: 'text_delta', text: 'answer' } })
    expect(invocationSignal?.aborted).toBe(false)
    await reader.cancel()
    expect(invocationSignal?.aborted).toBe(true)
  })
})
