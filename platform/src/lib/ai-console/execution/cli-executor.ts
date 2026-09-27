import 'server-only'
import { inspect } from 'node:util'
import Ajv from 'ajv'
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
  request: RoleExecutionRequest): Promise<RoleExecutionResult> {
  if ((request.tools?.length ?? 0) > 0 || request.toolChoice && request.toolChoice !== 'none') {
    // The common contract carries definitions but no authorized handler authority.
    throw new AiConsoleError('AI_ROLE_INCOMPATIBLE', execution.role)
  }
  if (request.responseSchema && (!execution.capabilities.supportsStructuredOutput
    || !definition.supportsStructuredOutput)) throw new AiConsoleError('AI_ROLE_INCOMPATIBLE', execution.role)
  if (request.abortSignal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role)

  const prompt = serializePrompt(request)
  let retryCount = 0
  while (true) {
    try {
      const result = await runner.runExecution(execution.cliUserId!, definition.id, {
        modelId: execution.target.kind === 'local_cli' ? execution.target.modelId : null,
        stdin: prompt, responseSchema: request.responseSchema, signal: request.abortSignal,
      })
      const parsed = validateMachineOutput(definition.execution!.outputFormat, result.stdout)
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
        finishReason: 'stop', usage: parsed.usage, retryCount }
    } catch (error) {
      if (request.abortSignal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED', execution.role)
      if (isStructuredOutputValidationError(error)) throw error
      const safe = normalizeAiError(error, { source: 'cli', role: execution.role })
      if (retryCount === 0 && TRANSIENT.has(safe.code)) { retryCount = 1; continue }
      throw new AiConsoleError(safe.code, execution.role)
    }
  }
}

function stream(execution: ResolvedRoleExecution, definition: CliDefinition, runner: CliRunner,
  request: RoleExecutionRequest): ReadableStream<RoleExecutionEvent> {
  const localAbort = new AbortController()
  const signal = request.abortSignal
    ? AbortSignal.any([request.abortSignal, localAbort.signal]) : localAbort.signal
  let events: RoleExecutionEvent[] | undefined
  let loading: Promise<void> | undefined
  let cancelled = false
  return new ReadableStream<RoleExecutionEvent>({
    async pull(controller) {
      if (cancelled) return
      loading ??= generate(execution, definition, runner, { ...request, abortSignal: signal }).then(result => {
        events = []
        if (result.text) events.push({ type: 'text_delta', text: result.text })
        events.push({ type: 'finish', finishReason: result.finishReason, usage: result.usage,
          retryCount: result.retryCount })
      })
      try { await loading }
      catch (error) { controller.error(error); return }
      if (cancelled) return
      const next = events!.shift()
      if (next) controller.enqueue(next); else controller.close()
    },
    cancel() { cancelled = true; localAbort.abort() },
  })
}

function serializePrompt(request: RoleExecutionRequest): string {
  const lines = [`<system>\n${request.systemPrompt}\n</system>`]
  for (const message of request.messages) {
    lines.push(`<${message.role}>\n${message.content}\n</${message.role}>`)
  }
  return lines.join('\n\n')
}
