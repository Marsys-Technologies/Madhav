import { describe, expect, it, vi } from 'vitest'
import { createCliRoleExecutor } from '../cli-executor'
import { createRoleExecutor } from '../index'
import type { ResolvedRoleExecution } from '../types'
import type { CliRunner } from '../../cli/runner'
import { StructuredOutputValidationError } from '../structured-output-error'
import { encode } from 'gpt-tokenizer'

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
    await expect(executor.generate({ ...request, maxOutputTokens: 256 })).resolves.toMatchObject({ text: 'answer', finishReason: 'stop',
      usage: { inputTokens: 2, outputTokens: 3, totalTokens: 5 }, retryCount: 0 })
    expect(runExecution.mock.calls[0][0]).toBe('alice')
    expect(runExecution.mock.calls[0][1]).toBe('claude_code')
    expect(runExecution.mock.calls[0][2]).toMatchObject({ modelId: null, maxOutputTokens: 256 })
    expect(runExecution.mock.calls[0][2].stdin).toContain('system')
  })

  it('accepts a short reported answer inside a large machine envelope', async () => {
    const stdout = JSON.stringify({ type: 'result', subtype: 'success', is_error: false,
      result: 'ok', usage: { output_tokens: 1 }, padding: 'x'.repeat(20_000) })
    const runExecution = vi.fn().mockResolvedValue({ stdout, exitCode: 0, signal: null })
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })

    await expect(executor.generate({ ...request, maxOutputTokens: 2 }))
      .resolves.toMatchObject({ text: 'ok', usage: { outputTokens: 1 } })
  })

  it('rejects authoritative over-token output before generate or stream exposes any result', async () => {
    const runExecution = vi.fn().mockResolvedValue({ stdout:
      '{"type":"result","subtype":"success","is_error":false,"result":"short","usage":{"output_tokens":3}}',
    exitCode: 0, signal: null })
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })

    await expect(executor.generate({ ...request, maxOutputTokens: 2 }))
      .rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    const reader = executor.stream({ ...request, maxOutputTokens: 2 }).getReader()
    await expect(reader.read()).rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
  })

  it('rejects underreported zero-token oversized text before generate or stream exposes output', async () => {
    const answer = 'substantial semantic answer '.repeat(80)
    const localTokens = encode(answer).length
    const runExecution = vi.fn().mockResolvedValue({ stdout: JSON.stringify({
      type: 'result', subtype: 'success', is_error: false, result: answer, usage: { output_tokens: 0 },
    }), exitCode: 0, signal: null })
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })

    await expect(executor.generate({ ...request, maxOutputTokens: localTokens - 1 }))
      .rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    const reader = executor.stream({ ...request, maxOutputTokens: localTokens - 1 }).getReader()
    await expect(reader.read()).rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
  })

  it('rejects underreported one-token multibyte output in generate and stream', async () => {
    const answer = 'नमस्ते 🌕 — ज्योतिषीय उत्तर'
    const estimatedTokens = encode(answer).length
    const runExecution = vi.fn().mockResolvedValue({ stdout: JSON.stringify({
      type: 'result', subtype: 'success', is_error: false, result: answer, usage: { output_tokens: 1 },
    }), exitCode: 0, signal: null })
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })

    await expect(executor.generate({ ...request, maxOutputTokens: estimatedTokens - 1 }))
      .rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    const reader = executor.stream({ ...request, maxOutputTokens: estimatedTokens - 1 }).getReader()
    await expect(reader.read()).rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    await expect(executor.generate({ ...request, maxOutputTokens: estimatedTokens }))
      .resolves.toMatchObject({ text: answer })
  })

  it('counts an underreported structured candidate before generate or stream can return it', async () => {
    const structured = { answer: 'private '.repeat(200) }
    const runExecution = vi.fn().mockResolvedValue({ stdout: JSON.stringify({
      type: 'result', subtype: 'success', is_error: false, result: 'ok', structured_output: structured,
      usage: { output_tokens: 1 },
    }), exitCode: 0, signal: null })
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })
    const schema = { type: 'object' as const, properties: { answer: { type: 'string' as const } }, required: ['answer'] }

    await expect(executor.generate({ ...request, responseSchema: schema, maxOutputTokens: 2 }))
      .rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    const reader = executor.stream({ ...request, responseSchema: schema, maxOutputTokens: 2 }).getReader()
    await expect(reader.read()).rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
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

  it('preserves only the internal typed structured failure for same-executor repair', async () => {
    const runExecution = vi.fn().mockResolvedValue({ stdout:
      '{"type":"result","subtype":"success","is_error":false,"result":"{\\"ok\\":\\"secret-bad\\"}","structured_output":{"ok":"secret-bad"},"usage":{}}',
    exitCode: 0, signal: null })
    const executor = createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })
    const schema = { type: 'object' as const, properties: { ok: { type: 'boolean' as const } }, required: ['ok'] }

    const failure = await executor.generate({ ...request, responseSchema: schema }).catch(error => error)
    expect(failure).toBeInstanceOf(StructuredOutputValidationError)
    expect(failure.candidateText()).toContain('secret-bad')
    expect(String(failure)).not.toContain('secret-bad')
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
