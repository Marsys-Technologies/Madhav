import { describe, expect, it, vi } from 'vitest'
import { createCliRoleExecutor } from '../cli-executor'
import { createRoleExecutor } from '../index'
import type { ResolvedRoleExecution } from '../types'
import type { CliRunner } from '../../cli/runner'
import { StructuredOutputValidationError } from '../structured-output-error'
import { encode } from 'gpt-tokenizer'
import { safeExecutionFailureFacts } from '../execution-facts'
import { CLI_REGISTRY } from '../../cli/registry'
import { PipelinePlanInputJsonSchema } from '@/lib/pipeline/types'
import type { RoleExecutionRequest } from '../provider-executor'
type ResponseSchema = NonNullable<RoleExecutionRequest['responseSchema']>

function execution(overrides: Partial<ResolvedRoleExecution> = {}): ResolvedRoleExecution {
  return {
    role: 'planner', adapterType: 'cli', target: { kind: 'local_cli', cliId: 'claude_code', modelId: null },
    capabilities: { supportsTools: false, supportsStructuredOutput: true }, cliUserId: 'alice', ...overrides,
  }
}

const request = { systemPrompt: 'system', messages: [{ role: 'user' as const, content: 'question' }] }

function codexOutput(text: string) {
  return { stdout: [JSON.stringify({ type: 'item.completed', item: { type: 'agent_message', text } }),
    JSON.stringify({ type: 'turn.completed', usage: { input_tokens: 1, output_tokens: 1 } })].join('\n'),
    exitCode: 0, signal: null }
}

const minimalPlan = { query_class: 'predictive', query_intent_summary: 'Synthetic timing lookup', asset_bundle: [],
  tool_calls: [{ tool_name: 'chart_facts_query', params: { arbitrary: { nested: [1, true, null], extra: 'preserved' } },
    token_budget: 100, priority: 1, reason: 'Synthetic lookup' }] }
const codexExecution = () => execution({ target: { kind: 'local_cli', cliId: 'codex', modelId: 'selected-model', effort: 'high' } })

function freezeDeep<T>(value: T): T {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freezeDeep)
    Object.freeze(value)
  }
  return value
}

describe('Codex schema transport — original schema remains the validator', () => {
  it('guides the actual planner schema instead of sending it to a strict native contract', async () => {
    const original = JSON.stringify(PipelinePlanInputJsonSchema)
    const input = freezeDeep({ ...request, responseSchema: PipelinePlanInputJsonSchema })
    const runExecution = vi.fn(async (_user, _cli, transport) => {
      // Contract-only refusal: strict:true requires a closed root with every
      // declared field required. Application validation below is real AJV.
      if (transport.responseSchema && (transport.responseSchema.additionalProperties !== false
        || Object.keys(transport.responseSchema.properties).length !== transport.responseSchema.required.length)) {
        throw new Error('strict schema contract refused')
      }
      return codexOutput(JSON.stringify(minimalPlan))
    })
    const executor = createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
    await expect(executor.generate(input)).resolves.toMatchObject({ structured: minimalPlan, retryCount: 0,
      fallbackUsed: false, activeModelId: 'selected-model' })
    expect(runExecution).toHaveBeenCalledOnce()
    const transport = runExecution.mock.calls[0][2]
    expect(transport).not.toHaveProperty('responseSchema')
    expect(transport.stdin).toContain(original)
    expect(transport.stdin).toMatch(/only.*JSON/i)
    expect(JSON.stringify(PipelinePlanInputJsonSchema)).toBe(original)
    expect(input.responseSchema).toBe(PipelinePlanInputJsonSchema)
  })

  it.each(['not json private candidate', JSON.stringify({ asset_bundle: [], tool_calls: [] })])(
    'keeps invalid guided output as a typed candidate for repair (%s)', async (candidate) => {
      const runExecution = vi.fn().mockResolvedValue(codexOutput(candidate))
      const executor = createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
      const failure = await executor.generate({ ...request, responseSchema: PipelinePlanInputJsonSchema }).catch(error => error)
      expect(failure).toBeInstanceOf(StructuredOutputValidationError)
      expect(failure.candidateText()).toBe(candidate)
      expect(String(failure)).not.toContain(candidate)
      expect(safeExecutionFailureFacts(failure)).toEqual({ retryCount: 0 })
      expect(runExecution).toHaveBeenCalledOnce()
    })

  it('retains native transport and the identical schema for a supported closed schema', async () => {
    const schema = freezeDeep<ResponseSchema>({ type: 'object', properties: { answer: { type: 'string' } },
      required: ['answer'], additionalProperties: false })
    const runExecution = vi.fn().mockResolvedValue(codexOutput('{"answer":"ok"}'))
    const executor = createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
    await expect(executor.generate({ ...request, responseSchema: schema })).resolves.toMatchObject({ structured: { answer: 'ok' } })
    expect(runExecution.mock.calls[0][2].responseSchema).toBe(schema)
    expect(runExecution.mock.calls[0][2].stdin).toBe('<system>\nsystem\n</system>\n\n<user>\nquestion\n</user>')
  })

  it('guides an uncertain keyword while enforcing its original domain semantics locally', async () => {
    const schema: ResponseSchema = { type: 'object', properties: { answer: { type: 'string', minLength: 2 } },
      required: ['answer'], additionalProperties: false }
    const runExecution = vi.fn().mockResolvedValue(codexOutput('{"answer":"x"}'))
    const executor = createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
    await expect(executor.generate({ ...request, responseSchema: schema })).rejects.toBeInstanceOf(StructuredOutputValidationError)
    expect(runExecution.mock.calls[0][2]).not.toHaveProperty('responseSchema')
    expect(runExecution.mock.calls[0][2].stdin).toContain(JSON.stringify(schema))
    expect(runExecution).toHaveBeenCalledOnce()
  })

  it('does not treat an open nested object as native-compatible just because the root is closed', async () => {
    const schema: ResponseSchema = { type: 'object', properties: { params: { type: 'object' } }, required: ['params'], additionalProperties: false }
    const structured = { params: { arbitrary: { nested: [1, 2] } } }
    const runExecution = vi.fn().mockResolvedValue(codexOutput(JSON.stringify(structured)))
    await expect(createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
      .generate({ ...request, responseSchema: schema })).resolves.toMatchObject({ structured })
    expect(runExecution.mock.calls[0][2]).not.toHaveProperty('responseSchema')
  })

  it('cannot bypass the 64 KiB schema limit by omitting native responseSchema', async () => {
    const runExecution = vi.fn()
    const failure = await createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
      .generate({ ...request, responseSchema: { type: 'object', description: 'x'.repeat(64 * 1024) } }).catch(error => error)
    expect(failure).toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    expect(safeExecutionFailureFacts(failure)).toEqual({ retryCount: 0 })
    expect(runExecution).not.toHaveBeenCalled()
  })

  it('checks the 256 KiB stdin limit after appending guidance', async () => {
    const runExecution = vi.fn()
    await expect(createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
      .generate({ ...request, systemPrompt: 'x'.repeat(256 * 1024 - 100), responseSchema: PipelinePlanInputJsonSchema }))
      .rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    expect(runExecution).not.toHaveBeenCalled()
  })

  it('keeps schema-free Codex input unchanged', async () => {
    const runExecution = vi.fn().mockResolvedValue(codexOutput('answer'))
    await createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner }).generate(request)
    expect(runExecution.mock.calls[0][2]).toMatchObject({ responseSchema: undefined,
      stdin: '<system>\nsystem\n</system>\n\n<user>\nquestion\n</user>' })
  })

  it('leaves the same planner schema unchanged for other CLIs', async () => {
    const runExecution = vi.fn().mockResolvedValue({ stdout: JSON.stringify({ type: 'result', subtype: 'success',
      is_error: false, result: JSON.stringify(minimalPlan), usage: {} }), exitCode: 0, signal: null })
    await createCliRoleExecutor(execution(), { runner: { runExecution } as unknown as CliRunner })
      .generate({ ...request, responseSchema: PipelinePlanInputJsonSchema })
    expect(runExecution.mock.calls[0][2].responseSchema).toBe(PipelinePlanInputJsonSchema)
    expect(runExecution.mock.calls[0][2].stdin).not.toContain(JSON.stringify(PipelinePlanInputJsonSchema))
  })

  it('retries the same guided transport and exact target once with existing attribution', async () => {
    const runExecution = vi.fn().mockRejectedValueOnce(Object.assign(new Error('synthetic timeout'), { code: 'ETIMEDOUT' }))
      .mockResolvedValueOnce(codexOutput(JSON.stringify(minimalPlan)))
    const abort = new AbortController()
    await expect(createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
      .generate({ ...request, responseSchema: PipelinePlanInputJsonSchema, abortSignal: abort.signal, maxOutputTokens: 1024 }))
      .resolves.toMatchObject({ retryCount: 1, fallbackUsed: false, activeModelId: 'selected-model' })
    expect(runExecution).toHaveBeenCalledTimes(2)
    expect(runExecution.mock.calls[0]).toEqual(runExecution.mock.calls[1])
    expect(runExecution.mock.calls[0]).toMatchObject(['alice', 'codex', { modelId: 'selected-model', effort: 'high',
      signal: abort.signal, maxOutputTokens: 1024 }])
    expect(runExecution.mock.calls[0][2]).not.toHaveProperty('responseSchema')
  })

  it('never switches native transport after a native execution failure', async () => {
    const schema: ResponseSchema = { type: 'object', properties: { answer: { type: 'string' } }, required: ['answer'], additionalProperties: false }
    const runExecution = vi.fn().mockRejectedValue(new Error('synthetic native refusal'))
    await expect(createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
      .generate({ ...request, responseSchema: schema })).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(runExecution).toHaveBeenCalledOnce()
    expect(runExecution.mock.calls[0][2].responseSchema).toBe(schema)
  })

  it('retains the native subset through closed nested arrays and objects', async () => {
    const schema: ResponseSchema = { type: 'object', properties: { rows: { type: 'array', items: {
      type: 'object', properties: { score: { type: 'number' } }, required: ['score'], additionalProperties: false,
    } } }, required: ['rows'], additionalProperties: false }
    const structured = { rows: [{ score: 1 }] }
    const runExecution = vi.fn().mockResolvedValue(codexOutput(JSON.stringify(structured)))
    await createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
      .generate({ ...request, responseSchema: schema })
    expect(runExecution.mock.calls[0][2].responseSchema).toBe(schema)
  })

  it('keeps pre-abort and tool refusal before guided execution', async () => {
    const runExecution = vi.fn()
    const executor = createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
    const abort = new AbortController()
    abort.abort()
    await expect(executor.generate({ ...request, responseSchema: PipelinePlanInputJsonSchema, abortSignal: abort.signal }))
      .rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    await expect(executor.generate({ ...request, responseSchema: PipelinePlanInputJsonSchema,
      tools: [{ name: 'unsafe', description: 'fixture', parameters: {} }] }))
      .rejects.toMatchObject({ code: 'AI_ROLE_INCOMPATIBLE' })
    expect(runExecution).not.toHaveBeenCalled()
  })

  it('enforces output tokens before guided generate or stream exposes a plan', async () => {
    const runExecution = vi.fn().mockResolvedValue(codexOutput(JSON.stringify(minimalPlan)))
    const executor = createCliRoleExecutor(codexExecution(), { runner: { runExecution } as unknown as CliRunner })
    const input = { ...request, responseSchema: PipelinePlanInputJsonSchema, maxOutputTokens: 1 }
    await expect(executor.generate(input)).rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    await expect(executor.stream(input).getReader().read()).rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
  })
})

describe('CLI role executor', () => {
  it('rejects a registered detect-only CLI as unreachable', () => {
    expect(() => createCliRoleExecutor(execution({ target: {
      kind: 'local_cli', cliId: 'kimi_code', modelId: null,
    } }), { registry: { kimi_code: { ...CLI_REGISTRY.kimi_code, execution: undefined } } }))
      .toThrowError(expect.objectContaining({ code: 'AI_CLI_UNREACHABLE' }))
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

  it('attaches the exact retry count to an abort after one CLI retry', async () => {
    let secondStarted!: () => void
    const started = new Promise<void>(resolve => { secondStarted = resolve })
    const runExecution = vi.fn()
      .mockRejectedValueOnce(Object.assign(new Error('hidden'), { code: 'ETIMEDOUT' }))
      .mockImplementationOnce((_userId, _cliId, input: { signal: AbortSignal }) => {
        secondStarted()
        return new Promise((_resolve, reject) => input.signal.addEventListener('abort', () => {
          reject(new DOMException('private abort detail', 'AbortError'))
        }, { once: true }))
      })
    const abort = new AbortController()
    const reader = createCliRoleExecutor(execution(), {
      runner: { runExecution } as unknown as CliRunner,
    }).stream({ ...request, abortSignal: abort.signal }).getReader()

    const pending = reader.read().catch(error => error)
    await started
    abort.abort()
    const failure = await pending
    expect(failure).toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(safeExecutionFailureFacts(failure)).toEqual({ retryCount: 1 })
    expect(String(failure)).not.toContain('private abort detail')
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
