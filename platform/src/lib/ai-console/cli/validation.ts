import 'server-only'
import { z } from 'zod'
import { AiConsoleError, normalizeAiError } from '../errors'
import {
  assertCliValidationAuthorized, markCliValidationStarted, restoreCliValidation, storeCliValidation,
} from '../repository'
import { CliIdSchema, type CliId } from '../types'
import { CLI_REGISTRY, parseSupportedVersion, type CliDefinition, type CliOutputFormat } from './registry'
import { cliRunner, type CliRunner } from './runner'
import { CLI_BUILTIN_MODEL_DB_ID } from './types'

type ValidationRegistry = Partial<Record<CliId, CliDefinition>>
export interface CliValidationResult {
  readonly cliId: CliId
  readonly productName: string
  readonly state: 'reachable' | 'not_installed' | 'auth_unavailable' | 'unreachable' | 'needs_attention'
  readonly detectedVersion?: string
  readonly modelCount: number
  readonly errorCode?: string
}

const PROBE = 'Reply with exactly OK.'

export async function validateCli(userId: string, cliId: unknown, signal?: AbortSignal,
  dependencies: { runner?: CliRunner; registry?: ValidationRegistry } = {}): Promise<CliValidationResult> {
  const id = CliIdSchema.parse(cliId)
  await assertCliValidationAuthorized(userId, id)
  const definition = (dependencies.registry ?? CLI_REGISTRY)[id]
  if (!definition) throw new AiConsoleError('AI_CLI_NOT_INSTALLED')
  const runner = dependencies.runner ?? cliRunner
  const attempt = await markCliValidationStarted(id)
  let superseded = false
  const publish = async (write: Parameters<typeof storeCliValidation>[1], epoch = attempt.epoch): Promise<string> => {
    const nextEpoch = await storeCliValidation(id, write, epoch)
    if (!nextEpoch) {
      superseded = true
      throw new AiConsoleError('AI_EXECUTION_FAILED')
    }
    return nextEpoch
  }

  try {
    if (definition.candidates.length === 0) {
      const write = { state: 'not_installed' as const, errorCode: 'AI_CLI_NOT_INSTALLED' as const }
      await publish(write)
      return { cliId: id, productName: definition.productName, state: write.state, modelCount: 0,
        errorCode: write.errorCode }
    }
    if (!definition.execution || !definition.authStatusArgs) {
      try { await runner.inspectInstallation(id) }
      catch (error) {
        const safe = normalizeAiError(error, { source: 'cli' })
        const state = safe.code === 'AI_CLI_NOT_INSTALLED' ? 'not_installed' as const : 'unreachable' as const
        await publish({ state, errorCode: cliErrorCode(safe.code) })
        return { cliId: id, productName: definition.productName, state, modelCount: 0, errorCode: safe.code }
      }
      await publish({ state: 'needs_attention', detectedProduct: definition.productName,
        errorCode: 'AI_CLI_UNREACHABLE' })
      return { cliId: id, productName: definition.productName, state: 'needs_attention', modelCount: 0,
        errorCode: 'AI_CLI_UNREACHABLE' }
    }

    let version: string | null = null
    let installationIdentity: Awaited<ReturnType<CliRunner['inspectInstallation']>>
    try {
      installationIdentity = await runner.inspectInstallation(id)
      const versionResult = await runner.runVersionValidation(userId, id, signal)
      version = parseSupportedVersion(definition, versionResult.stdout)
      if (!version) {
        await publish({ state: 'needs_attention', detectedProduct: definition.productName,
          errorCode: 'AI_EXECUTION_FAILED' })
        return { cliId: id, productName: definition.productName, state: 'needs_attention', modelCount: 0,
          errorCode: 'AI_EXECUTION_FAILED' }
      }
    } catch (error) {
      if (superseded) throw error
      if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
      const safe = normalizeAiError(error, { source: 'cli' })
      if (safe.code === 'AI_CLI_NOT_GRANTED') throw new AiConsoleError('AI_CLI_NOT_GRANTED')
      const state = safe.code === 'AI_CLI_NOT_INSTALLED' ? 'not_installed' as const : 'unreachable' as const
      await publish({ state, errorCode: cliErrorCode(safe.code) })
      return { cliId: id, productName: definition.productName, state, modelCount: 0, errorCode: safe.code }
    }

    try {
      // Output may contain account identity. Success/failure is the only retained fact.
      await runner.runAuthValidation(userId, id, signal)
    } catch (error) {
      if (superseded) throw error
      if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
      const safe = normalizeAiError(error, { source: 'cli' })
      if (safe.code === 'AI_CLI_NOT_GRANTED') throw new AiConsoleError('AI_CLI_NOT_GRANTED')
      await publish({ state: 'auth_unavailable', detectedProduct: definition.productName,
        detectedVersion: version, errorCode: 'AI_CLI_AUTH_UNAVAILABLE' })
      return { cliId: id, productName: definition.productName, state: 'auth_unavailable',
        detectedVersion: version, modelCount: 0, errorCode: 'AI_CLI_AUTH_UNAVAILABLE' }
    }

    try {
      const probe = await runner.runProbeValidation(userId, id, PROBE, signal)
      const parsed = validateMachineOutput(definition.execution.outputFormat, probe.stdout)
      if (parsed.text.trim().toUpperCase() !== 'OK') throw new AiConsoleError('AI_EXECUTION_FAILED')
      const model = { modelId: CLI_BUILTIN_MODEL_DB_ID, displayName: 'Built-in default',
        compatibleRoles: [...definition.compatibleRoles], supportsTools: definition.supportsTools,
        supportsStructuredOutput: definition.supportsStructuredOutput, isBuiltinDefault: true }
      const completedEpoch = await publish({ state: 'reachable', detectedProduct: definition.productName,
        detectedVersion: version, models: [model] })
      try { await runner.confirmValidation(id, installationIdentity, version) }
      catch {
        await publish({ state: 'needs_attention', detectedProduct: definition.productName,
          detectedVersion: version, errorCode: 'AI_CLI_UNREACHABLE' }, completedEpoch)
        return { cliId: id, productName: definition.productName, state: 'needs_attention',
          detectedVersion: version, modelCount: 0, errorCode: 'AI_CLI_UNREACHABLE' }
      }
      return { cliId: id, productName: definition.productName, state: 'reachable',
        detectedVersion: version, modelCount: 1 }
    } catch (error) {
      if (superseded) throw error
      if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
      const safe = normalizeAiError(error, { source: 'cli' })
      if (safe.code === 'AI_CLI_NOT_GRANTED') throw new AiConsoleError('AI_CLI_NOT_GRANTED')
      const state = safe.code === 'AI_CLI_TIMEOUT' || safe.code === 'AI_CLI_OUTPUT_LIMIT'
        ? 'unreachable' as const : 'needs_attention' as const
      await publish({ state, detectedProduct: definition.productName,
        detectedVersion: version, errorCode: cliErrorCode(safe.code) })
      return { cliId: id, productName: definition.productName, state, detectedVersion: version,
        modelCount: 0, errorCode: safe.code }
    }
  } catch (error) {
    if (!superseded) {
      try { await restoreCliValidation(attempt) } catch { /* Preserve the safe terminal error. */ }
    }
    throw error
  }
}

function cliErrorCode(code: string): 'AI_CLI_NOT_INSTALLED' | 'AI_CLI_AUTH_UNAVAILABLE' | 'AI_CLI_UNREACHABLE'
  | 'AI_CLI_TIMEOUT' | 'AI_CLI_OUTPUT_LIMIT' | 'AI_EXECUTION_FAILED' {
  const parsed = z.enum(['AI_CLI_NOT_INSTALLED', 'AI_CLI_AUTH_UNAVAILABLE', 'AI_CLI_UNREACHABLE',
    'AI_CLI_TIMEOUT', 'AI_CLI_OUTPUT_LIMIT', 'AI_EXECUTION_FAILED']).safeParse(code)
  return parsed.success ? parsed.data : 'AI_EXECUTION_FAILED'
}

const UsageSchema = z.object({ input_tokens: z.number().int().nonnegative().optional(),
  output_tokens: z.number().int().nonnegative().optional() }).passthrough()
export function validateMachineOutput(format: CliOutputFormat, stdout: string) {
  if (format === 'claude_json') {
    let raw: unknown
    try { raw = JSON.parse(stdout) } catch { throw new AiConsoleError('AI_EXECUTION_FAILED') }
    const parsed = z.object({ type: z.literal('result'), subtype: z.literal('success'), is_error: z.literal(false),
      result: z.string(), structured_output: z.unknown().optional(), usage: UsageSchema.optional() }).passthrough().safeParse(raw)
    if (!parsed.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
    const inputTokens = parsed.data.usage?.input_tokens ?? 0
    const outputTokens = parsed.data.usage?.output_tokens ?? 0
    return { text: parsed.data.result, structured: parsed.data.structured_output,
      usage: { inputTokens, outputTokens, totalTokens: inputTokens + outputTokens } }
  }

  let text = ''
  let inputTokens = 0
  let outputTokens = 0
  let completed = false
  const lines = stdout.split(/\r?\n/).filter(Boolean)
  if (!lines.length) throw new AiConsoleError('AI_EXECUTION_FAILED')
  for (const line of lines) {
    let raw: unknown
    try { raw = JSON.parse(line) } catch { throw new AiConsoleError('AI_EXECUTION_FAILED') }
    const event = z.object({ type: z.string() }).passthrough().safeParse(raw)
    if (!event.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
    if (completed) throw new AiConsoleError('AI_EXECUTION_FAILED')
    if (event.data.type === 'item.completed') {
      const item = z.object({ item: z.object({ type: z.string(), text: z.string().optional() }).passthrough() })
        .passthrough().safeParse(raw)
      if (!item.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
      if (item.data.item.type === 'agent_message') {
        if (!item.data.item.text) throw new AiConsoleError('AI_EXECUTION_FAILED')
        text += item.data.item.text
      }
    } else if (event.data.type === 'turn.completed') {
      if (!text) throw new AiConsoleError('AI_EXECUTION_FAILED')
      const terminal = z.object({ usage: UsageSchema.optional() }).passthrough().safeParse(raw)
      if (!terminal.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
      inputTokens = terminal.data.usage?.input_tokens ?? 0
      outputTokens = terminal.data.usage?.output_tokens ?? 0
      completed = true
    } else if (!['thread.started', 'turn.started', 'item.started'].includes(event.data.type)) {
      throw new AiConsoleError('AI_EXECUTION_FAILED')
    }
  }
  if (!text || !completed) throw new AiConsoleError('AI_EXECUTION_FAILED')
  return { text, usage: { inputTokens, outputTokens, totalTokens: inputTokens + outputTokens } }
}
