import 'server-only'
import { z } from 'zod'
import { AiConsoleError, normalizeAiError } from '../errors'
import {
  assertCliValidationAuthorized, markCliValidationStarted, restoreCliValidation, storeCliValidation,
  listConfirmedManualCliModels, storeManualCliModel,
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
  dependencies: { runner?: CliRunner; registry?: ValidationRegistry; metadataOnly?: boolean } = {}): Promise<CliValidationResult> {
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
    if (!definition.execution || (!definition.authStatusArgs && !definition.modelCatalog)) {
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
    let installationIdentity: Awaited<ReturnType<CliRunner['inspectInstallation']>> | undefined
    try {
      installationIdentity = await runner.inspectInstallation(id)
      const versionResult = await runner.runVersionValidation(userId, id, signal)
      version = parseSupportedVersion(definition, versionResult.stdout)
      if (!version) {
        const detectedVersion = versionResult.stdout.match(/\b\d+\.\d+\.\d+\b/)?.[0]
        await publish({ state: 'needs_attention', detectedProduct: definition.productName,
          ...(detectedVersion ? { detectedVersion } : {}),
          errorCode: 'AI_EXECUTION_FAILED' })
        return { cliId: id, productName: definition.productName, state: 'needs_attention', modelCount: 0,
          ...(detectedVersion ? { detectedVersion } : {}),
          errorCode: 'AI_EXECUTION_FAILED' }
      }
    } catch (error) {
      if (superseded) throw error
      if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
      const safe = normalizeAiError(error, { source: 'cli' })
      if (safe.code === 'AI_CLI_NOT_GRANTED') throw new AiConsoleError('AI_CLI_NOT_GRANTED')
      if (dependencies.metadataOnly && attempt.previous.state === 'reachable'
        && installationIdentity && attempt.previous.entrypointSha256 === installationIdentity.entrypoint.sha256
        && attempt.previous.detectedVersion && safe.code !== 'AI_CLI_NOT_INSTALLED') {
        await publish({ state: 'reachable', detectedProduct: definition.productName,
          detectedVersion: attempt.previous.detectedVersion,
          entrypointSha256: installationIdentity.entrypoint.sha256 })
        return { cliId: id, productName: definition.productName, state: 'reachable',
          detectedVersion: attempt.previous.detectedVersion, modelCount: 0, errorCode: safe.code }
      }
      const state = safe.code === 'AI_CLI_NOT_INSTALLED' ? 'not_installed' as const : 'unreachable' as const
      await publish({ state, errorCode: cliErrorCode(safe.code) })
      return { cliId: id, productName: definition.productName, state, modelCount: 0, errorCode: safe.code }
    }

    if (!installationIdentity || !version) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    let discoveredModels: Awaited<ReturnType<CliRunner['runModelCatalogValidation']>> = []
    try {
      if (definition.modelCatalog) {
        discoveredModels = await runner.runModelCatalogValidation(userId, id, signal)
      } else {
        // Output may contain account identity. Success/failure is the only retained fact.
        await runner.runAuthValidation(userId, id, signal)
      }
    } catch (error) {
      if (superseded) throw error
      if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
      const safe = normalizeAiError(error, { source: 'cli' })
      if (safe.code === 'AI_CLI_NOT_GRANTED') throw new AiConsoleError('AI_CLI_NOT_GRANTED')
      if (dependencies.metadataOnly && attempt.previous.state === 'reachable'
        && attempt.previous.detectedVersion === version
        && (attempt.previous.entrypointSha256 === installationIdentity.entrypoint.sha256
          || attempt.previous.entrypointSha256 == null)
        && safe.code !== 'AI_CLI_AUTH_UNAVAILABLE') {
        await publish({ state: 'reachable', detectedProduct: definition.productName,
          detectedVersion: version,
          ...(attempt.previous.entrypointSha256 == null ? {}
            : { entrypointSha256: installationIdentity.entrypoint.sha256 }) })
        return { cliId: id, productName: definition.productName, state: 'reachable',
          detectedVersion: version, modelCount: 0, errorCode: safe.code }
      }
      await publish({ state: 'auth_unavailable', detectedProduct: definition.productName,
        detectedVersion: version, errorCode: 'AI_CLI_AUTH_UNAVAILABLE' })
      return { cliId: id, productName: definition.productName, state: 'auth_unavailable',
        detectedVersion: version, modelCount: 0, errorCode: 'AI_CLI_AUTH_UNAVAILABLE' }
    }

    try {
      const unchangedValidatedInstallation = attempt.previous.state === 'reachable'
        && attempt.previous.detectedVersion === version
        && attempt.previous.entrypointSha256 === installationIdentity.entrypoint.sha256
      // Pre-refresh installations have no persisted hash. Preserve their previously
      // tested availability on the same version, without fabricating execution proof.
      // The execution revalidation path still inspects and tests the actual binary.
      const legacyValidatedInstallation = attempt.previous.state === 'reachable'
        && attempt.previous.detectedVersion === version
        && attempt.previous.entrypointSha256 == null
      if (dependencies.metadataOnly && !unchangedValidatedInstallation && !legacyValidatedInstallation) {
        const models = discoveredModels.map(discovered => ({ ...catalogModelForStorage(discovered),
          isCatalogDiscovered: true, compatibleRoles: [...definition.compatibleRoles],
          supportsTools: definition.supportsTools, supportsStructuredOutput: definition.supportsStructuredOutput,
          isBuiltinDefault: false }))
        await publish({ state: 'needs_attention', detectedProduct: definition.productName,
          detectedVersion: version, entrypointSha256: installationIdentity.entrypoint.sha256,
          errorCode: 'AI_CLI_UNREACHABLE', models })
        return { cliId: id, productName: definition.productName, state: 'needs_attention',
          detectedVersion: version, modelCount: models.length }
      }
      if (!dependencies.metadataOnly) {
        const probe = await runner.runProbeValidation(userId, id, PROBE, signal)
        const parsed = validateMachineOutput(definition.execution.outputFormat, probe.stdout)
        if (parsed.text.trim().toUpperCase() !== 'OK') throw new AiConsoleError('AI_EXECUTION_FAILED')
      }
      const model = { modelId: CLI_BUILTIN_MODEL_DB_ID, displayName: 'Built-in default',
        compatibleRoles: [...definition.compatibleRoles], supportsTools: definition.supportsTools,
        supportsStructuredOutput: definition.supportsStructuredOutput, isBuiltinDefault: true }
      const models = [model, ...discoveredModels.map(discovered => ({ ...catalogModelForStorage(discovered),
        isCatalogDiscovered: true,
        compatibleRoles: [...definition.compatibleRoles], supportsTools: definition.supportsTools,
        supportsStructuredOutput: definition.supportsStructuredOutput, isBuiltinDefault: false }))]
      const completedEpoch = await publish({ state: 'reachable', detectedProduct: definition.productName,
        detectedVersion: version, models,
        ...(dependencies.metadataOnly && legacyValidatedInstallation ? {}
          : { entrypointSha256: installationIdentity.entrypoint.sha256 }) })
      if (dependencies.metadataOnly && legacyValidatedInstallation) {
        return { cliId: id, productName: definition.productName, state: 'reachable',
          detectedVersion: version, modelCount: models.length }
      }
      try { await runner.confirmValidation(id, installationIdentity, version,
        [...new Set([null, ...discoveredModels.map(discovered => discovered.modelId),
          ...await listConfirmedManualCliModels(id, version, installationIdentity.entrypoint.sha256)])]) }
      catch {
        await publish({ state: 'needs_attention', detectedProduct: definition.productName,
          detectedVersion: version, errorCode: 'AI_CLI_UNREACHABLE' }, completedEpoch)
        return { cliId: id, productName: definition.productName, state: 'needs_attention',
          detectedVersion: version, modelCount: 0, errorCode: 'AI_CLI_UNREACHABLE' }
      }
      return { cliId: id, productName: definition.productName, state: 'reachable',
        detectedVersion: version, modelCount: models.length }
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

function catalogModelForStorage(model: Awaited<ReturnType<CliRunner['runModelCatalogValidation']>>[number]) {
  return { modelId: model.modelId, displayName: model.displayName,
    ...(model.supportedEfforts === undefined ? {} : { supportedEfforts: model.supportedEfforts }),
    ...(model.defaultEffort === undefined ? {} : { defaultEffort: model.defaultEffort }) }
}

/** Test an explicit Codex/Claude model through the subscription CLI before adding it to host choices. */
export async function testAndAddManualCliModel(userId: string, cliId: CliId, modelId: string,
  signal?: AbortSignal, runner: CliRunner = cliRunner): Promise<void> {
  if (cliId !== 'codex' && cliId !== 'claude_code') throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
  await assertCliValidationAuthorized(userId, cliId)
  const definition = CLI_REGISTRY[cliId]
  const validation = await validateCli(userId, cliId, signal, { runner })
  if (validation.state !== 'reachable' || !validation.detectedVersion) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  const before = await runner.inspectInstallation(cliId)
  const probe = await runner.runModelProbeValidation(userId, cliId, modelId, PROBE, signal)
  if (validateMachineOutput(definition.execution!.outputFormat, probe.stdout).text.trim().toUpperCase() !== 'OK') {
    throw new AiConsoleError('AI_EXECUTION_FAILED')
  }
  if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  const after = await runner.inspectInstallation(cliId)
  if (JSON.stringify(before) !== JSON.stringify(after)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  await storeManualCliModel(userId, cliId, modelId, validation.detectedVersion, after.entrypoint.sha256)
  await runner.confirmManualModel(cliId, after, modelId)
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
  if (format === 'kimi_acp_json') {
    let raw: unknown
    try { raw = JSON.parse(stdout) } catch { throw new AiConsoleError('AI_EXECUTION_FAILED') }
    const parsed = z.object({ text: z.string().min(1) }).strict().safeParse(raw)
    if (!parsed.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
    return { text: parsed.data.text, usage: { inputTokens: null, outputTokens: null, totalTokens: null } }
  }
  if (format === 'claude_json') {
    let raw: unknown
    try { raw = JSON.parse(stdout) } catch { throw new AiConsoleError('AI_EXECUTION_FAILED') }
    const parsed = z.object({ type: z.literal('result'), subtype: z.literal('success'), is_error: z.literal(false),
      result: z.string(), structured_output: z.unknown().optional(), usage: UsageSchema.optional() }).passthrough().safeParse(raw)
    if (!parsed.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
    const inputTokens = parsed.data.usage?.input_tokens ?? null
    const outputTokens = parsed.data.usage?.output_tokens ?? null
    return { text: parsed.data.result, structured: parsed.data.structured_output,
      usage: { inputTokens, outputTokens,
        totalTokens: inputTokens === null || outputTokens === null ? null : inputTokens + outputTokens },
      reportedOutputTokens: parsed.data.usage?.output_tokens }
  }

  if (format === 'antigravity_stream_json') {
    const lines = stdout.split(/\r?\n/).filter(Boolean)
    let initialized = false
    let completed = false
    let text = ''
    let inputTokens: number | null = null
    let outputTokens: number | null = null
    let totalTokens: number | null = null
    for (const line of lines) {
      let raw: unknown
      try { raw = JSON.parse(line) } catch { throw new AiConsoleError('AI_EXECUTION_FAILED') }
      const envelope = z.object({ event: z.enum(['init', 'step_update', 'result']) }).passthrough().safeParse(raw)
      if (!envelope.success || completed) throw new AiConsoleError('AI_EXECUTION_FAILED')
      if (envelope.data.event === 'init') {
        const init = z.object({ init: z.object({ cwd: z.string(), permission_mode: z.string(),
          tools: z.array(z.unknown()) }).passthrough() }).passthrough().safeParse(raw)
        if (!init.success || initialized) throw new AiConsoleError('AI_EXECUTION_FAILED')
        initialized = true
      } else if (envelope.data.event === 'step_update') {
        const step = z.object({ step_update: z.object({
          step_type: z.enum(['user_input', 'agent_response']), state: z.string(),
        }).passthrough() }).passthrough().safeParse(raw)
        if (!initialized || !step.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
      } else {
        const result = z.object({ result: z.object({ status: z.literal('SUCCESS'), response: z.string().min(1),
          usage: UsageSchema.extend({ total_tokens: z.number().int().nonnegative().optional() }).optional(),
        }).passthrough() }).passthrough().safeParse(raw)
        if (!initialized || !result.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
        text = result.data.result.response
        inputTokens = result.data.result.usage?.input_tokens ?? null
        outputTokens = result.data.result.usage?.output_tokens ?? null
        totalTokens = result.data.result.usage?.total_tokens
          ?? (inputTokens === null || outputTokens === null ? null : inputTokens + outputTokens)
        completed = true
      }
    }
    if (!initialized || !completed || !text) throw new AiConsoleError('AI_EXECUTION_FAILED')
    return { text, usage: { inputTokens, outputTokens, totalTokens },
      reportedOutputTokens: outputTokens ?? undefined }
  }

  let text = ''
  let inputTokens: number | null = null
  let outputTokens: number | null = null
  let reportedOutputTokens: number | undefined
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
      inputTokens = terminal.data.usage?.input_tokens ?? null
      outputTokens = terminal.data.usage?.output_tokens ?? null
      reportedOutputTokens = terminal.data.usage?.output_tokens
      completed = true
    } else if (!['thread.started', 'turn.started', 'item.started'].includes(event.data.type)) {
      throw new AiConsoleError('AI_EXECUTION_FAILED')
    }
  }
  if (!text || !completed) throw new AiConsoleError('AI_EXECUTION_FAILED')
  return { text, usage: { inputTokens, outputTokens,
    totalTokens: inputTokens === null || outputTokens === null ? null : inputTokens + outputTokens },
    reportedOutputTokens }
}
