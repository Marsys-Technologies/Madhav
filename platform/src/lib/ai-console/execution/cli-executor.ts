import 'server-only'
import { inspect } from 'node:util'
import Ajv from 'ajv'
import { encode } from 'gpt-tokenizer'
import { AiConsoleError, normalizeAiError } from '../errors'
import { CLI_REGISTRY, type CliDefinition } from '../cli/registry'
import { cliRunner, type CliRunner } from '../cli/runner'
import { validateMachineOutput } from '../cli/validation'
import type { CliId } from '../types'
import type { ResolvedRoleExecution } from './types'
import type {
  RoleExecutionEvent, RoleExecutionRequest, RoleExecutionResult, RoleExecutor, SafeCliExecutorDescriptor,
} from './provider-executor'
import { isStructuredOutputValidationError, StructuredOutputValidationError } from './structured-output-error'
import { attachSafeExecutionFailureFacts, setSafeExecutionStreamFacts } from './execution-facts'

interface Dependencies {
  runner?: CliRunner
  registry?: Partial<Record<CliId, CliDefinition>>
}

const validator = new Ajv({ strict: false, allErrors: false })
const TRANSIENT = new Set(['AI_CLI_TIMEOUT', 'AI_CLI_UNREACHABLE'])

export function createCliRoleExecutor(execution: ResolvedRoleExecution, dependencies: Dependencies = {}): RoleExecutor {
  if (execution.adapterType !== 'cli' || execution.target.kind !== 'local_cli' || !execution.cliUserId) {
    throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role)
  }
  const registry = dependencies.registry ?? CLI_REGISTRY
  const definition = registry[execution.target.cliId]
  if (!definition) throw new AiConsoleError('AI_CLI_NOT_INSTALLED', execution.role)
  if (!definition.execution) throw new AiConsoleError('AI_CLI_UNREACHABLE', execution.role)
  const descriptor: SafeCliExecutorDescriptor = Object.freeze({ role: execution.role,
    cliId: execution.target.cliId, modelId: execution.target.modelId })
  const runner = dependencies.runner ?? cliRunner
  const executor: RoleExecutor = {
    descriptor,
    generate: request => generate(execution, definition, runner, request),
    stream: request => stream(execution, definition, runner, request),
  }
  Object.defineProperty(executor, 'toJSON', { enumerable: false, value: () => ({ descriptor }) })
  Object.defineProperty(executor, inspect.custom, { enumerable: false,
    value: () => `[CliRoleExecutor ${JSON.stringify(descriptor)}]` })
  return Object.freeze(executor)
}

async function generate(execution: ResolvedRoleExecution, definition: CliDefinition, runner: CliRunner,
  request: RoleExecutionRequest, onRetryCount?: (retryCount: number) => void): Promise<RoleExecutionResult> {
  if ((request.tools?.length ?? 0) > 0 || request.toolChoice && request.toolChoice !== 'none') {
    // The common contract carries definitions but no authorized handler authority.
    throw attachSafeExecutionFailureFacts(new AiConsoleError('AI_ROLE_INCOMPATIBLE', execution.role),
      { retryCount: 0 })
  }
  if (request.responseSchema && (!execution.capabilities.supportsStructuredOutput
    || !definition.supportsStructuredOutput)) throw attachSafeExecutionFailureFacts(
    new AiConsoleError('AI_ROLE_INCOMPATIBLE', execution.role), { retryCount: 0 })
  if (request.abortSignal?.aborted) throw attachSafeExecutionFailureFacts(
    new AiConsoleError('AI_EXECUTION_FAILED', execution.role), { retryCount: 0 })

  let transport: { stdin: string; responseSchema?: RoleExecutionRequest['responseSchema'] } = {
    stdin: serializePrompt(request), responseSchema: request.responseSchema,
  }
  if (definition.id === 'codex' && request.responseSchema) {
    try { transport = selectCodexSchemaTransport(transport.stdin, request.responseSchema) }
    catch (error) {
      throw attachSafeExecutionFailureFacts(new AiConsoleError(
        error instanceof AiConsoleError ? error.code : 'AI_EXECUTION_FAILED', execution.role), { retryCount: 0 })
    }
  }
  let retryCount = 0
  onRetryCount?.(retryCount)
  while (true) {
    try {
      const result = await runner.runExecution(execution.cliUserId!, definition.id, {
        modelId: execution.target.kind === 'local_cli' ? execution.target.modelId : null,
        effort: execution.target.effort ?? undefined,
        ...transport, maxOutputTokens: request.maxOutputTokens,
        signal: request.abortSignal,
      })
      const parsed = validateMachineOutput(definition.execution!.outputFormat, result.stdout)
      enforceModelOutputLimit(parsed, request.maxOutputTokens)
      let structured = parsed.structured
      if (request.responseSchema) {
        if (structured === undefined) {
          try { structured = JSON.parse(parsed.text) as unknown }
          catch { throw new StructuredOutputValidationError(execution.role, parsed.text) }
        }
        if (!validator.compile(request.responseSchema)(structured)) {
          throw new StructuredOutputValidationError(execution.role, parsed.text)
        }
      }
      return { text: parsed.text, ...(request.responseSchema ? { structured } : {}), toolCalls: [],
        finishReason: 'stop', usage: parsed.usage, retryCount, fallbackUsed: false,
        activeModelId: execution.target.kind === 'local_cli'
          ? execution.target.modelId ?? `${execution.target.cliId}:built-in-default` : 'selected-model' }
    } catch (error) {
      if (request.abortSignal?.aborted) throw attachSafeExecutionFailureFacts(
        new AiConsoleError('AI_EXECUTION_FAILED', execution.role), { retryCount })
      if (isStructuredOutputValidationError(error)) {
        throw attachSafeExecutionFailureFacts(error, { retryCount })
      }
      const safe = normalizeAiError(error, { source: 'cli', role: execution.role })
      if (retryCount === 0 && TRANSIENT.has(safe.code)) {
        retryCount = 1
        onRetryCount?.(retryCount)
        continue
      }
      throw attachSafeExecutionFailureFacts(new AiConsoleError(safe.code, execution.role), { retryCount })
    }
  }
}

function enforceModelOutputLimit(parsed: ReturnType<typeof validateMachineOutput>, maxOutputTokens?: number): void {
  if (maxOutputTokens === undefined) return
  if (!Number.isSafeInteger(maxOutputTokens) || maxOutputTokens <= 0) {
    throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
  }
  const measured = Math.max(
    parsed.reportedOutputTokens ?? 0,
    encode(parsed.text).length,
    parsed.structured === undefined ? 0 : encode(JSON.stringify(parsed.structured)).length,
  )
  if (measured > maxOutputTokens) throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
}

function stream(execution: ResolvedRoleExecution, definition: CliDefinition, runner: CliRunner,
  request: RoleExecutionRequest): ReadableStream<RoleExecutionEvent> {
  const localAbort = new AbortController()
  const signal = request.abortSignal
    ? AbortSignal.any([request.abortSignal, localAbort.signal]) : localAbort.signal
  let events: RoleExecutionEvent[] | undefined
  let loading: Promise<void> | undefined
  let cancelled = false
  const publishRetryCount = (retryCount: number) => setSafeExecutionStreamFacts(output, { retryCount })
  const output = new ReadableStream<RoleExecutionEvent>({
    async pull(controller) {
      if (cancelled) return
      loading ??= generate(execution, definition, runner, { ...request, abortSignal: signal }, publishRetryCount).then(result => {
        events = []
        if (result.text) events.push({ type: 'text_delta', text: result.text })
        events.push({ type: 'finish', finishReason: result.finishReason, usage: result.usage,
          retryCount: result.retryCount, fallbackUsed: result.fallbackUsed, activeModelId: result.activeModelId })
      })
      try { await loading }
      catch (error) { controller.error(error); return }
      if (cancelled) return
      const next = events!.shift()
      if (next) controller.enqueue(next); else controller.close()
    },
    cancel() { cancelled = true; localAbort.abort() },
  })
  publishRetryCount(0)
  return output
}

function serializePrompt(request: RoleExecutionRequest): string {
  const lines = [`<system>\n${request.systemPrompt}\n</system>`]
  for (const message of request.messages) {
    lines.push(`<${message.role}>\n${message.content}\n</${message.role}>`)
  }
  return lines.join('\n\n')
}

/**
 * Codex 0.158 sends --output-schema unchanged with strict:true. Only use that
 * transport for a small proven subset; unknown keywords/references/combinators
 * choose JSON guidance, never a rewrite of the caller's domain schema. Both
 * transports still pass through the ORIGINAL schema's AJV validation above.
 */
function selectCodexSchemaTransport(stdin: string, originalSchema: NonNullable<RoleExecutionRequest['responseSchema']>): {
  stdin: string; responseSchema?: RoleExecutionRequest['responseSchema']
} {
  let schemaJson: string
  try { schemaJson = JSON.stringify(originalSchema) }
  catch { throw new AiConsoleError('AI_EXECUTION_FAILED') }
  if (typeof schemaJson !== 'string') throw new AiConsoleError('AI_EXECUTION_FAILED')
  // Guided transport must not evade the runner's schema-file bound.
  if (Buffer.byteLength(schemaJson, 'utf8') > 64 * 1024) throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
  const native = isCodexStrictSubset(JSON.parse(schemaJson), schemaJson.length)
  if (!native) {
    stdin += `\n\n<response_schema>\n${schemaJson}\n</response_schema>\n` +
      'Return only valid JSON matching the response schema above. Do not include prose or markdown fences.'
  }
  if (Buffer.byteLength(stdin, 'utf8') > 256 * 1024) throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
  return native ? { stdin, responseSchema: originalSchema } : { stdin }
}

function isCodexStrictSubset(schema: unknown, serializedChars: number): boolean {
  const record = (value: unknown): value is Record<string, unknown> =>
    typeof value === 'object' && value !== null && !Array.isArray(value)
  // Conservative size/depth/property guards deliberately stay below the API
  // limits. Falling outside this subset selects guidance, not schema rejection.
  if (!record(schema) || schema.type !== 'object' || serializedChars > 15_000) return false
  let properties = 0
  const visit = (node: unknown, depth: number): boolean => {
    if (!record(node) || depth > 5) return false
    const annotations = ['description', 'title']
    if (annotations.some(key => node[key] !== undefined && typeof node[key] !== 'string')) return false
    if (node.type === 'object') {
      if (Object.keys(node).some(key => !['type', 'properties', 'required', 'additionalProperties', ...annotations].includes(key))
        || node.additionalProperties !== false || !record(node.properties) || !Array.isArray(node.required)) return false
      const keys = Object.keys(node.properties)
      properties += keys.length
      if (properties > 100 || keys.length === 0 || node.required.length !== keys.length
        || new Set(node.required).size !== keys.length || !keys.every(key => (node.required as unknown[]).includes(key))) return false
      return Object.values(node.properties).every(child => visit(child, depth + 1))
    }
    if (node.type === 'array') {
      return Object.keys(node).every(key => ['type', 'items', ...annotations].includes(key))
        && visit(node.items, depth + 1)
    }
    return typeof node.type === 'string' && ['string', 'number', 'integer', 'boolean'].includes(node.type)
      && Object.keys(node).every(key => ['type', ...annotations].includes(key))
  }
  return visit(schema, 1)
}
