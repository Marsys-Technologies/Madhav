import 'server-only'
import { inspect } from 'node:util'
import Ajv from 'ajv'
import type { LanguageModelV3 } from '@ai-sdk/provider'
import { streamAdapterRaw } from '@/lib/adapters/raw'
import type {
  JSONSchema, QueryRequest, RuntimeAdapterBinding, SafeRuntimeModelDescriptor, ToolDefinition,
} from '@/lib/adapters/types'
import { AiConsoleError, normalizeAiError, type PublicAiError } from '../errors'
import type { AiRole, ProviderId } from '../types'
import type { ProviderRuntimeFailure, ResolvedRoleExecution } from './types'

export interface SafeProviderExecutorDescriptor extends SafeRuntimeModelDescriptor {
  readonly role: AiRole
}

export interface RoleExecutionRequest {
  systemPrompt: string
  messages: QueryRequest['messages']
  tools?: ToolDefinition[]
  toolChoice?: QueryRequest['toolChoice']
  responseSchema?: JSONSchema
  maxOutputTokens?: number
  temperature?: number
  reasoning?: QueryRequest['reasoning']
  multiStep?: QueryRequest['multiStep']
  abortSignal?: AbortSignal
}

export interface NormalizedUsage {
  inputTokens: number
  outputTokens: number
  totalTokens: number
}

export interface RoleToolCall { name: string; args: unknown; callId: string }
export type RoleExecutionEvent =
  | { type: 'text_delta'; text: string }
  | { type: 'reasoning_delta'; text: string }
  | { type: 'tool_call'; name: string; args: unknown; callId: string }
  | { type: 'tool_result'; callId: string; result: unknown }
  | { type: 'finish'; finishReason: string; usage: NormalizedUsage; retryCount: number }

export interface RoleExecutionResult {
  text: string
  structured?: unknown
  toolCalls: RoleToolCall[]
  finishReason: string
  usage: NormalizedUsage
  retryCount: number
}

export interface RoleExecutor {
  readonly descriptor: SafeProviderExecutorDescriptor
  generate(request: RoleExecutionRequest): Promise<RoleExecutionResult>
  stream(request: RoleExecutionRequest): ReadableStream<RoleExecutionEvent>
}

const MARKABLE = new Set<ProviderRuntimeFailure['code']>([
  'AI_CONNECTION_INVALID', 'AI_MODEL_UNAVAILABLE', 'AI_ROLE_INCOMPATIBLE',
  'AI_PROVIDER_UNREACHABLE', 'AI_PERMISSION_DENIED', 'AI_BILLING_UNAVAILABLE', 'AI_RATE_LIMITED',
])
const TRANSIENT = new Set<PublicAiError['code']>(['AI_PROVIDER_UNREACHABLE', 'AI_RATE_LIMITED'])
const structuredOutputValidator = new Ajv({ strict: false, allErrors: false })

export function createProviderRoleExecutor(execution: ResolvedRoleExecution): RoleExecutor {
  if (execution.adapterType !== 'provider' || execution.target.kind !== 'provider_model'
    || !execution.createRuntimeBinding) throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role)

  const descriptor = Object.freeze({
    role: execution.role,
    providerId: execution.target.providerId,
    connectionId: execution.target.connectionId,
    modelId: execution.target.modelId,
  })
  const executor = {
    descriptor,
    generate: (request: RoleExecutionRequest) => generate(execution, descriptor, request),
    stream: (request: RoleExecutionRequest) => stream(execution, descriptor, request),
  }
  Object.defineProperty(executor, 'toJSON', {
    enumerable: false, value: () => ({ descriptor }),
  })
  Object.defineProperty(executor, inspect.custom, {
    enumerable: false, value: () => `[ProviderRoleExecutor ${JSON.stringify(descriptor)}]`,
  })
  return Object.freeze(executor)
}

async function generate(execution: ResolvedRoleExecution, descriptor: SafeProviderExecutorDescriptor,
  request: RoleExecutionRequest): Promise<RoleExecutionResult> {
  const reader = stream(execution, descriptor, request).getReader()
  let text = ''
  const toolCalls: RoleToolCall[] = []
  let finishReason = 'error'
  let usage: NormalizedUsage = { inputTokens: 0, outputTokens: 0, totalTokens: 0 }
  let retryCount = 0
  while (true) {
    const next = await reader.read()
    if (next.done) break
    const event = next.value
    if (event.type === 'text_delta') text += event.text
    else if (event.type === 'tool_call') toolCalls.push({ name: event.name, args: event.args, callId: event.callId })
    else if (event.type === 'finish') {
      finishReason = event.finishReason; usage = event.usage; retryCount = event.retryCount
    }
  }
  let structured: unknown
  if (request.responseSchema) {
    try {
      structured = JSON.parse(text) as unknown
      if (!structuredOutputValidator.compile(request.responseSchema)(structured)) {
        throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role)
      }
    }
    catch { throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role) }
  }
  return { text, ...(request.responseSchema ? { structured } : {}), toolCalls, finishReason, usage, retryCount }
}

function stream(execution: ResolvedRoleExecution, descriptor: SafeProviderExecutorDescriptor,
  request: RoleExecutionRequest): ReadableStream<RoleExecutionEvent> {
  const localAbort = new AbortController()
  let cancelled = false
  let iterator: AsyncIterator<unknown> | undefined
  let disposeCurrent: (() => void) | undefined
  let retryCount = 0
  let emitted = false
  let settled = false
  let pulling: Promise<void> | undefined
  let detachExternalAbort = () => undefined
  const dispose = () => { const current = disposeCurrent; disposeCurrent = undefined; current?.() }
  const returnIteratorSafely = (current: AsyncIterator<unknown> | undefined) => {
    try { void Promise.resolve(current?.return?.()).catch(() => undefined) }
    catch { /* external abort is already terminal */ }
  }

  async function openAttempt(): Promise<boolean> {
    if (cancelled) return false
    if (request.abortSignal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role)
    const binding = await execution.createRuntimeBinding!()
    let disposed = false
    disposeCurrent = () => { if (!disposed) { disposed = true; binding.dispose() } }
    if (cancelled) { dispose(); return false }
    if (request.abortSignal?.aborted) {
      dispose()
      throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role)
    }
    assertExactBinding(binding.providerId, binding.connectionId, binding.modelId, descriptor)
    const runtimeDescriptor = adapterDescriptor(descriptor)
    const runtimeBinding = adapterBinding(binding.model, runtimeDescriptor)
    const abortSignal = request.abortSignal
      ? AbortSignal.any([request.abortSignal, localAbort.signal]) : localAbort.signal
    const raw = streamAdapterRaw({
      callType: callType(execution.role), systemPrompt: request.systemPrompt,
      messages: request.messages, tools: request.tools, toolChoice: request.toolChoice,
      responseSchema: request.responseSchema, maxOutputTokens: request.maxOutputTokens,
      temperature: request.temperature, reasoning: request.reasoning, multiStep: request.multiStep,
      disableSdkRetry: true, abortSignal, runtimeBinding, runtimeDescriptor,
    })
    iterator = raw.result.fullStream[Symbol.asyncIterator]()
    return true
  }

  async function terminalError(cause: unknown): Promise<never | 'retry'> {
    dispose(); iterator = undefined
    if (cancelled || request.abortSignal?.aborted) {
      throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role)
    }
    const normalized = normalizeAiError(cause, { source: 'provider', role: execution.role })
    if (!emitted && retryCount === 0 && TRANSIENT.has(normalized.code)) {
      retryCount = 1
      return 'retry'
    }
    settled = true
    detachExternalAbort()
    if (execution.markRuntimeFailure && MARKABLE.has(normalized.code as ProviderRuntimeFailure['code'])) {
      try { await execution.markRuntimeFailure(normalized as ProviderRuntimeFailure) }
      catch { /* Health telemetry must not replace the safe terminal provider error. */ }
    }
    throw new AiConsoleError(normalized.code, execution.role)
  }

  async function pullOne(controller: ReadableStreamDefaultController<RoleExecutionEvent>): Promise<void> {
    if (((request.tools?.length ?? 0) > 0 && !execution.capabilities.supportsTools)
      || (request.responseSchema !== undefined && !execution.capabilities.supportsStructuredOutput)) {
      settled = true
      detachExternalAbort()
      throw new AiConsoleError('AI_ROLE_INCOMPATIBLE', execution.role)
    }
    while (!cancelled) {
      try {
        if (!iterator && !await openAttempt()) return
        const next = await iterator!.next()
        if (next.done) {
          settled = true
          detachExternalAbort()
          dispose(); iterator = undefined
          controller.close()
          return
        }
        const event = translate(next.value, retryCount)
        if (!event) continue
        emitted = true
        controller.enqueue(event)
        return
      } catch (cause) {
        if (cancelled) return
        if (await terminalError(cause) === 'retry') continue
      }
    }
  }

  return new ReadableStream<RoleExecutionEvent>({
    start(controller) {
      if (!request.abortSignal) return
      const onAbort = () => {
        if (settled) return
        settled = true
        cancelled = true
        detachExternalAbort()
        localAbort.abort()
        const current = iterator
        iterator = undefined
        dispose()
        returnIteratorSafely(current)
        controller.error(new AiConsoleError('AI_EXECUTION_FAILED', execution.role))
      }
      detachExternalAbort = () => {
        request.abortSignal?.removeEventListener('abort', onAbort)
        detachExternalAbort = () => undefined
      }
      request.abortSignal.addEventListener('abort', onAbort, { once: true })
      if (request.abortSignal.aborted) onAbort()
    },
    pull(controller) {
      pulling ??= pullOne(controller).finally(() => { pulling = undefined })
      return pulling
    },
    async cancel() {
      if (settled) return
      settled = true
      cancelled = true
      detachExternalAbort()
      localAbort.abort()
      try { await iterator?.return?.() } catch { /* cancellation is already terminal */ }
      dispose()
    },
  })
}

function adapterDescriptor(descriptor: SafeProviderExecutorDescriptor): SafeRuntimeModelDescriptor {
  return Object.freeze({ providerId: descriptor.providerId, connectionId: descriptor.connectionId,
    modelId: descriptor.modelId })
}

function adapterBinding(model: LanguageModelV3, descriptor: SafeRuntimeModelDescriptor): RuntimeAdapterBinding {
  const binding = Object.create(null)
  Object.defineProperties(binding, {
    providerId: { value: descriptor.providerId, enumerable: true },
    connectionId: { value: descriptor.connectionId, enumerable: true },
    modelId: { value: descriptor.modelId, enumerable: true },
    model: { value: model, enumerable: false },
    toJSON: { value: () => { throw new AiConsoleError('AI_EXECUTION_FAILED') } },
    [inspect.custom]: { value: () => '[RuntimeAdapterBinding REDACTED]' },
  })
  return Object.freeze(binding) as RuntimeAdapterBinding
}

function assertExactBinding(providerId: ProviderId, connectionId: string, modelId: string,
  descriptor: SafeRuntimeModelDescriptor): void {
  if (providerId !== descriptor.providerId || connectionId !== descriptor.connectionId
    || modelId !== descriptor.modelId) {
    throw new AiConsoleError('AI_EXECUTION_FAILED')
  }
}

function callType(role: AiRole): QueryRequest['callType'] {
  if (role === 'synthesizer') return 'synthesis'
  if (role === 'planner') return 'planner_fast'
  if (role === 'deep_planner') return 'planner_deep'
  return 'worker'
}

function translate(value: unknown, retryCount: number): RoleExecutionEvent | undefined {
  if (!value || typeof value !== 'object') return undefined
  const part = value as Record<string, unknown>
  if (part.type === 'text-delta' && typeof part.text === 'string') return { type: 'text_delta', text: part.text }
  if (part.type === 'reasoning-delta' && typeof part.text === 'string') return { type: 'reasoning_delta', text: part.text }
  if (part.type === 'tool-call' && typeof part.toolName === 'string' && typeof part.toolCallId === 'string') {
    return { type: 'tool_call', name: part.toolName, args: part.input, callId: part.toolCallId }
  }
  if (part.type === 'tool-result' && typeof part.toolCallId === 'string') {
    return { type: 'tool_result', callId: part.toolCallId, result: part.output }
  }
  if (part.type === 'finish') {
    const rawUsage = part.totalUsage && typeof part.totalUsage === 'object'
      ? part.totalUsage as Record<string, unknown> : {}
    const inputTokens = token(rawUsage.inputTokens)
    const outputTokens = token(rawUsage.outputTokens)
    return { type: 'finish', finishReason: finishReason(part.finishReason),
      usage: { inputTokens, outputTokens, totalTokens: inputTokens + outputTokens }, retryCount }
  }
  if (part.type === 'error') throw part.error
  return undefined
}

function token(value: unknown): number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 ? value : 0
}

function finishReason(value: unknown): string {
  if (value === 'tool-calls') return 'tool_calls'
  return typeof value === 'string' ? value.replaceAll('-', '_') : 'error'
}
