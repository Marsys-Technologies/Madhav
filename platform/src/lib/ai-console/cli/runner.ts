import 'server-only'
import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process'
import { createHash } from 'node:crypto'
import { createReadStream } from 'node:fs'
import { lstat, mkdtemp, realpath, rm, stat, writeFile } from 'node:fs/promises'
import { dirname, isAbsolute, join, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { isDeepStrictEqual } from 'node:util'
import { StringDecoder } from 'node:string_decoder'
import { z } from 'zod'
import { AiConsoleError, AiErrorCodeSchema } from '../errors'
import { withCliInvocationAuthorization, type CliInvocationHandle } from '../repository'
import { AiEffortSchema, CliIdSchema, type AiEffort, type CliId } from '../types'
import { cliEffortLevels } from '../effort'
import { buildExecutionArgs, CLI_REGISTRY, isSupportedCliVersion, validateCliModelId, type CliDefinition } from './registry'
import { DiscoveredCliModelSchema, parseCliModelCatalog, type CliDiscoveredModel } from './catalog'
import { startCatalogProcess } from '../../../../scripts/ai-cli-bridge/catalog-protocol.mjs'

export interface CliProcessResult {
  readonly stdout: string
  readonly exitCode: number
  readonly signal: NodeJS.Signals | null
}

export interface CliFileIdentity {
  readonly candidate: string
  readonly realpath: string
  readonly device: string
  readonly inode: string
  readonly size: number
  readonly modifiedMs: number
  readonly changedMs: number
  readonly mode: number
  readonly uid: number
  readonly sha256: string
}

export interface CliInstallationIdentity {
  readonly cliId: CliId
  readonly entrypoint: CliFileIdentity
  readonly interpreter?: CliFileIdentity
}

export interface CliRunLimits {
  readonly stdinBytes: number
  readonly stdoutBytes: number
  readonly stderrBytes: number
  readonly timeoutMs: number
  readonly killGraceMs: number
  readonly globalConcurrency: number
  readonly perCliConcurrency: number
}

const DEFAULT_LIMITS: CliRunLimits = Object.freeze({
  stdinBytes: 256 * 1024,
  stdoutBytes: 1024 * 1024,
  stderrBytes: 64 * 1024,
  timeoutMs: 120_000,
  killGraceMs: 500,
  globalConcurrency: 4,
  perCliConcurrency: 2,
})

type Registry = Partial<Record<CliId, CliDefinition>>
interface QueueItem {
  cliId: CliId
  resolve: (release: () => void) => void
  reject: (error: AiConsoleError) => void
  signal?: AbortSignal
  onAbort?: () => void
}

export interface StartedCliProcess extends CliInvocationHandle {
  readonly completion: Promise<CliProcessResult>
  cancel(): void
}

interface PreparedCliProcess {
  readonly executable: string
  readonly processArgs: readonly string[]
  readonly stdinBytes: Buffer
  readonly cwd: string
}

type CliStarter = (prepared: PreparedCliProcess, signal?: AbortSignal) => StartedCliProcess
type CliRevalidator = (userId: string, cliId: CliId, signal: AbortSignal | undefined,
  runner: CliRunner, registry: Registry) => Promise<void>

export interface CliRunner {
  inspectInstallation(cliId: CliId, signal?: AbortSignal): Promise<CliInstallationIdentity>
  confirmValidation(cliId: CliId, identity: CliInstallationIdentity, version: string,
    modelIds: readonly (string | null)[]): Promise<void>
  runVersionValidation(userId: string, cliId: CliId, signal?: AbortSignal): Promise<CliProcessResult>
  runAuthValidation(userId: string, cliId: CliId, signal?: AbortSignal): Promise<CliProcessResult>
  runModelCatalogValidation(userId: string, cliId: CliId, signal?: AbortSignal): Promise<CliDiscoveredModel[]>
  runProbeValidation(userId: string, cliId: CliId, stdin: string, signal?: AbortSignal): Promise<CliProcessResult>
  runModelProbeValidation(userId: string, cliId: CliId, modelId: string, stdin: string, signal?: AbortSignal): Promise<CliProcessResult>
  confirmManualModel(cliId: CliId, identity: CliInstallationIdentity, modelId: string): Promise<void>
  runExecution(userId: string, cliId: CliId, input: { modelId: string | null; stdin: string;
    effort?: AiEffort; responseSchema?: unknown; maxOutputTokens?: number; signal?: AbortSignal }): Promise<CliProcessResult>
  inspectForTests(): { active: number; queued: number }
}

type BridgeFetch = typeof fetch
type ConfirmedCliInstallation = { identity: CliInstallationIdentity; version: string;
  modelIds: ReadonlySet<string | null>; manualModelIds: ReadonlySet<string> }

const BridgeErrorSchema = z.object({ error: z.enum([
  'AI_CLI_NOT_INSTALLED', 'AI_CLI_AUTH_UNAVAILABLE', 'AI_CLI_UNREACHABLE',
  'AI_CLI_TIMEOUT', 'AI_CLI_OUTPUT_LIMIT', 'AI_MODEL_UNAVAILABLE', 'AI_EXECUTION_FAILED',
]) }).strict()
const BridgeProcessSchema = z.object({ stdout: z.string(), exitCode: z.literal(0), signal: z.null() }).strict()
const BridgeIdentitySchema = z.object({
  cliId: CliIdSchema,
  entrypoint: z.object({ candidate: z.string(), realpath: z.string(), device: z.string(), inode: z.string(),
    size: z.number().nonnegative(), modifiedMs: z.number().nonnegative(), changedMs: z.number().nonnegative(),
    mode: z.number().int().nonnegative(), uid: z.number().int().nonnegative(), sha256: z.string().regex(/^[a-f0-9]{64}$/),
  }).strict(),
  interpreter: z.object({ candidate: z.string(), realpath: z.string(), device: z.string(), inode: z.string(),
    size: z.number().nonnegative(), modifiedMs: z.number().nonnegative(), changedMs: z.number().nonnegative(),
    mode: z.number().int().nonnegative(), uid: z.number().int().nonnegative(), sha256: z.string().regex(/^[a-f0-9]{64}$/),
  }).strict().optional(),
}).strict()
const BridgeModelsSchema = z.object({ models: z.array(DiscoveredCliModelSchema).max(100) }).strict()

class RemoteCliRunner implements CliRunner {
  private readonly endpoint: URL
  private readonly token: string
  private readonly fetchImpl: BridgeFetch
  private readonly confirmed = new Map<CliId, ConfirmedCliInstallation>()
  private readonly revalidationFlights = new Map<string, Promise<void>>()
  private readonly catalogRefreshFlights = new Map<string, Promise<void>>()
  private readonly catalogModelIds = new Map<CliId, ReadonlySet<string>>()
  private readonly catalogEfforts = new Map<CliId, ReadonlyMap<string, readonly string[]>>()
  private nextRequestId = 1_000_000

  constructor(options: { endpoint: string; token: string; fetchImpl?: BridgeFetch }) {
    this.endpoint = validateBridgeEndpoint(options.endpoint)
    if (options.token.length < 32 || options.token.includes('\0')) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    this.token = options.token
    this.fetchImpl = options.fetchImpl ?? fetch
  }

  async inspectInstallation(cliId: CliId, signal?: AbortSignal): Promise<CliInstallationIdentity> {
    const body = await this.request({ operation: 'inspect', cliId: CliIdSchema.parse(cliId) }, signal)
    const parsed = BridgeIdentitySchema.safeParse(body)
    if (!parsed.success) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    return Object.freeze(parsed.data)
  }

  async confirmValidation(cliId: CliId, identity: CliInstallationIdentity, version: string,
    modelIds: readonly (string | null)[]): Promise<void> {
    const id = CliIdSchema.parse(cliId)
    const validatedModels = modelIds.map(modelId => modelId === null ? null : validateConfirmedModelId(modelId))
    if (!validatedModels.length || !validatedModels.includes(null)
      || new Set(validatedModels).size !== validatedModels.length) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    await this.request({ operation: 'confirm', cliId: id, identity, version, modelIds: validatedModels })
    this.confirmed.set(id, Object.freeze({ identity, version, modelIds: new Set(validatedModels),
      manualModelIds: confirmedManualModels(this.confirmed.get(id), identity, validatedModels,
        this.catalogModelIds.get(id)) }))
  }

  runVersionValidation(userId: string, cliId: CliId, signal?: AbortSignal) {
    return this.runAuthorized(userId, cliId, { operation: 'version', cliId }, signal, 'validation')
  }

  async runAuthValidation(userId: string, cliId: CliId, signal?: AbortSignal) {
    const result = await this.runAuthorized(userId, cliId, { operation: 'auth', cliId }, signal, 'validation')
    return { ...result, stdout: '' }
  }

  async runModelCatalogValidation(userId: string, cliId: CliId, signal?: AbortSignal) {
    const result = await this.runAuthorizedBody(userId, cliId, { operation: 'catalog', cliId }, signal, 'validation')
    const parsed = BridgeModelsSchema.safeParse(result)
    if (!parsed.success) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    this.catalogModelIds.set(cliId, new Set(parsed.data.models.map(model => model.modelId)))
    this.catalogEfforts.set(cliId, new Map(parsed.data.models.map(model =>
      [model.modelId, model.supportedEfforts ?? []])))
    return parsed.data.models
  }

  runProbeValidation(userId: string, cliId: CliId, stdin: string, signal?: AbortSignal) {
    return this.runAuthorized(userId, cliId, { operation: 'probe', cliId, stdin }, signal, 'validation')
  }

  runModelProbeValidation(userId: string, cliId: CliId, modelId: string, stdin: string, signal?: AbortSignal) {
    return this.runAuthorized(userId, cliId, { operation: 'probe_model', cliId,
      modelId: validateConfirmedModelId(modelId), stdin }, signal, 'validation')
  }

  async confirmManualModel(cliId: CliId, identity: CliInstallationIdentity, modelId: string) {
    const current = this.confirmed.get(cliId)
    if (!current || !isDeepStrictEqual(current.identity, identity)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    this.confirmed.set(cliId, Object.freeze({ ...current,
      modelIds: new Set([...current.modelIds, validateConfirmedModelId(modelId)]),
      manualModelIds: new Set([...current.manualModelIds, modelId]) }))
  }

  async runExecution(userId: string, cliId: CliId, input: { modelId: string | null; stdin: string;
    effort?: AiEffort; responseSchema?: unknown; maxOutputTokens?: number; signal?: AbortSignal }) {
    const id = CliIdSchema.parse(cliId)
    await this.ensureConfirmed(userId, id, input.signal)
    const modelId = input.modelId === null ? null : validateConfirmedModelId(input.modelId)
    if (!this.confirmed.get(id)?.modelIds.has(modelId)
      || (input.effort && !cliEffortLevels(id, modelId,
        modelId ? this.catalogEfforts.get(id)?.get(modelId) : undefined).includes(AiEffortSchema.parse(input.effort)))) {
      await this.refreshConfirmedModels(userId, id, input.signal)
    }
    const confirmed = this.confirmed.get(id)
    if (!confirmed?.modelIds.has(modelId)) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    if (input.effort && !cliEffortLevels(id, modelId,
      modelId ? this.catalogEfforts.get(id)?.get(modelId) : undefined).includes(AiEffortSchema.parse(input.effort))) {
      throw new AiConsoleError('AI_ROLE_INCOMPATIBLE')
    }
    return this.runAuthorized(userId, id, { operation: 'execute', cliId: id, modelId, stdin: input.stdin,
      ...(input.effort ? { effort: input.effort } : {}),
      ...(input.responseSchema === undefined ? {} : { responseSchema: input.responseSchema }),
      ...(input.maxOutputTokens === undefined ? {} : { maxOutputTokens: input.maxOutputTokens }) },
    input.signal, 'execution')
  }

  inspectForTests() { return { active: 0, queued: 0 } }

  private async refreshConfirmedModels(userId: string, cliId: CliId, signal?: AbortSignal): Promise<void> {
    if (!CLI_REGISTRY[cliId].modelCatalog) return
    const key = `${userId}:${cliId}`
    let flight = this.catalogRefreshFlights.get(key)
    if (!flight) {
      flight = this.refreshConfirmedModelsOnce(userId, cliId, signal)
      this.catalogRefreshFlights.set(key, flight)
      void flight.finally(() => {
        if (this.catalogRefreshFlights.get(key) === flight) this.catalogRefreshFlights.delete(key)
      }).catch(() => undefined)
    }
    await flight
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  }

  private async refreshConfirmedModelsOnce(userId: string, cliId: CliId, signal?: AbortSignal): Promise<void> {
    const previous = this.confirmed.get(cliId)
    if (!previous) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    const deadline = AbortSignal.timeout(30_000)
    const combined = signal ? AbortSignal.any([signal, deadline]) : deadline
    try {
      const models = await readUnchangedCatalog(this, userId, cliId, previous.identity, combined)
      const current = this.confirmed.get(cliId)
      if (!current || current.version !== previous.version
        || !isDeepStrictEqual(current.identity, previous.identity)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
      const modelIds = new Set<string | null>([null, ...current.manualModelIds, ...models.map(model => model.modelId)])
      await this.request({ operation: 'confirm', cliId, identity: current.identity,
        version: current.version, modelIds: [...modelIds] }, combined)
      if (combined.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
      this.confirmed.set(cliId, Object.freeze({ ...current, modelIds }))
    } catch (error) {
      if (deadline.aborted && !signal?.aborted) throw new AiConsoleError('AI_CLI_TIMEOUT')
      throw error
    }
  }

  private async ensureConfirmed(userId: string, cliId: CliId, signal?: AbortSignal): Promise<void> {
    if (this.confirmed.has(cliId)) return
    const key = `${userId}:${cliId}`
    let flight = this.revalidationFlights.get(key)
    if (!flight) {
      flight = revalidateCliForExecution(userId, cliId, signal, this, CLI_REGISTRY)
      this.revalidationFlights.set(key, flight)
      void flight.finally(() => {
        if (this.revalidationFlights.get(key) === flight) this.revalidationFlights.delete(key)
      }).catch(() => undefined)
    }
    try { await flight }
    catch (error) {
      if (error instanceof AiConsoleError && (error.code === 'AI_CLI_NOT_GRANTED'
        || (signal?.aborted && error.code === 'AI_EXECUTION_FAILED'))) throw error
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
  }

  private async runAuthorized(userId: string, cliId: CliId, payload: Record<string, unknown>,
    signal: AbortSignal | undefined, purpose: 'execution' | 'validation'): Promise<CliProcessResult> {
    const body = await this.runAuthorizedBody(userId, cliId, payload, signal, purpose)
    const parsed = BridgeProcessSchema.safeParse(body)
    if (!parsed.success) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    return parsed.data
  }

  private async runAuthorizedBody(userId: string, cliId: CliId, payload: Record<string, unknown>,
    signal: AbortSignal | undefined, purpose: 'execution' | 'validation'): Promise<unknown> {
    const handle = await withCliInvocationAuthorization(userId, cliId,
      () => this.startRequest(payload, signal), purpose)
    return await handle.completion
  }

  private startRequest(payload: Record<string, unknown>, signal?: AbortSignal): StartedCliProcess {
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
    const controller = new AbortController()
    const combined = signal ? AbortSignal.any([signal, controller.signal]) : controller.signal
    const pid = this.nextRequestId++
    let cancelled = false
    const completion = this.request(payload, combined)
    void completion.catch(() => undefined)
    return Object.freeze({ pid, completion: completion as Promise<CliProcessResult>, cancel: () => {
      if (cancelled) return
      cancelled = true
      controller.abort()
    } })
  }

  private async request(payload: Record<string, unknown>, signal?: AbortSignal): Promise<unknown> {
    let response: Response
    const timeout = AbortSignal.timeout(DEFAULT_LIMITS.timeoutMs + 5_000)
    const requestSignal = signal ? AbortSignal.any([signal, timeout]) : timeout
    try {
      response = await this.fetchImpl(new URL('/v1/invoke', this.endpoint), {
        method: 'POST', signal: requestSignal, headers: { Authorization: `Bearer ${this.token}`,
          'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(payload),
      })
    } catch {
      throw new AiConsoleError(timeout.aborted && !signal?.aborted ? 'AI_CLI_TIMEOUT'
        : signal?.aborted ? 'AI_EXECUTION_FAILED' : 'AI_CLI_UNREACHABLE')
    }
    const length = Number(response.headers.get('content-length') ?? '0')
    if (Number.isFinite(length) && length > 1_100_000) throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
    let bytes: ArrayBuffer
    try { bytes = await response.arrayBuffer() } catch { throw new AiConsoleError('AI_CLI_UNREACHABLE') }
    if (bytes.byteLength > 1_100_000) throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
    let body: unknown
    try { body = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)) }
    catch { throw new AiConsoleError('AI_CLI_UNREACHABLE') }
    if (!response.ok) {
      const error = BridgeErrorSchema.safeParse(body)
      throw new AiConsoleError(error.success ? error.data.error : 'AI_CLI_UNREACHABLE')
    }
    return body
  }
}

class GovernedCliRunner implements CliRunner {
  private readonly registry: Registry
  private readonly limits: CliRunLimits
  private readonly environment: NodeJS.ProcessEnv
  private active = 0
  private readonly activeByCli = new Map<CliId, number>()
  private readonly queue: QueueItem[] = []
  private readonly validationIdentities = new Map<CliId, CliInstallationIdentity>()
  private readonly confirmedIdentities = new Map<CliId, ConfirmedCliInstallation>()
  private readonly revalidationFlights = new Map<string, Promise<void>>()
  private readonly catalogRefreshFlights = new Map<string, Promise<void>>()
  private readonly catalogModelIds = new Map<CliId, ReadonlySet<string>>()
  private readonly revalidate: CliRevalidator
  private readonly catalogEfforts = new Map<CliId, ReadonlyMap<string, readonly string[]>>()

  constructor(options: { registry?: Registry; limits?: Partial<CliRunLimits>; environment?: NodeJS.ProcessEnv;
    revalidate?: CliRevalidator } = {}) {
    this.registry = options.registry ?? CLI_REGISTRY
    this.limits = Object.freeze({ ...DEFAULT_LIMITS, ...options.limits })
    this.environment = options.environment ?? process.env
    this.revalidate = options.revalidate ?? revalidateCliForExecution
    if (Object.values(this.limits).some(value => !Number.isSafeInteger(value) || value <= 0)) {
      throw new AiConsoleError('AI_EXECUTION_FAILED')
    }
  }

  async inspectInstallation(cliId: CliId, signal?: AbortSignal): Promise<CliInstallationIdentity> {
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
    const definition = this.definition(cliId)
    const identity = await captureInstallationIdentity(definition)
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
    this.validationIdentities.set(cliId, identity)
    return identity
  }

  async confirmValidation(cliId: CliId, identity: CliInstallationIdentity, version: string,
    modelIds: readonly (string | null)[]): Promise<void> {
    const definition = this.definition(cliId)
    if (!definition.execution || !isSupportedCliVersion(definition, version) || identity.cliId !== definition.id) {
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    try { await assertCurrentInstallationIdentity(definition, identity) }
    catch {
      this.invalidateIdentity(cliId, identity)
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    if (!modelIds.length || !modelIds.includes(null)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    const validatedModels = modelIds.map(modelId => modelId === null ? null : validateConfirmedModelId(modelId))
    if (new Set(validatedModels).size !== validatedModels.length) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    this.confirmedIdentities.set(cliId, Object.freeze({ identity, version,
      modelIds: new Set(validatedModels),
      manualModelIds: confirmedManualModels(this.confirmedIdentities.get(cliId), identity, validatedModels,
        this.catalogModelIds.get(cliId)) }))
  }

  async runVersionValidation(userId: string, cliId: CliId, signal?: AbortSignal) {
    const definition = this.invocableDefinition(cliId)
    return await this.runFixedAuthorized(userId, cliId, definition.versionArgs, '', signal,
      undefined, 'validation')
  }

  async runAuthValidation(userId: string, cliId: CliId, signal?: AbortSignal) {
    const args = this.invocableDefinition(cliId).authStatusArgs
    if (!args) throw new AiConsoleError('AI_CLI_AUTH_UNAVAILABLE')
    const result = await this.runFixedAuthorized(userId, cliId, args, '', signal, undefined, 'validation')
    assertSubscriptionAuth(cliId, result.stdout)
    // Auth-status output can contain account identity. Only its safe exit fact
    // crosses the dedicated runner boundary.
    return { ...result, stdout: '' }
  }

  async runModelCatalogValidation(userId: string, cliId: CliId, signal?: AbortSignal) {
    const catalog = this.invocableDefinition(cliId).modelCatalog
    if (!catalog) throw new AiConsoleError('AI_CLI_AUTH_UNAVAILABLE')
    if (cliId === 'claude_code') await this.runAuthValidation(userId, cliId, signal)
    const protocol = catalog.format === 'codex_app_server' || catalog.format === 'claude_control'
    const result = await this.runFixedAuthorized(userId, cliId, catalog.args, '', signal,
      undefined, 'validation', protocol ? (prepared, invocationSignal) => startCatalogProcess({
        cliId: cliId as 'codex' | 'claude_code', executable: prepared.executable,
        args: prepared.processArgs, cwd: prepared.cwd, env: safeEnvironment(this.environment),
        limits: this.limits, signal: invocationSignal,
        error: code => new AiConsoleError(AiErrorCodeSchema.parse(code)),
        cleanup: () => rm(prepared.cwd, { recursive: true, force: true }),
      }) : undefined)
    // Provider-list output may contain credentials. Parse it inside the runner
    // boundary and return only validated identifiers and display names.
    const models = parseCliModelCatalog(catalog.format, result.stdout)
    this.catalogModelIds.set(cliId, new Set(models.map(model => model.modelId)))
    this.catalogEfforts.set(cliId, new Map(models.filter(model => model.supportedEfforts !== undefined)
      .map(model => [model.modelId, model.supportedEfforts!])))
    return models
  }

  async runProbeValidation(userId: string, cliId: CliId, stdin: string, signal?: AbortSignal) {
    const definition = this.invocableDefinition(cliId)
    if (definition.execution.transport === 'kimi_acp') {
      return await this.runFixedAuthorized(userId, cliId, buildExecutionArgs(definition, null), stdin, signal,
        undefined, 'validation', (prepared, invocationSignal) => this.startKimiAcp(prepared, null, invocationSignal))
    }
    return await this.runFixedAuthorized(userId, cliId, buildExecutionArgs(definition, null),
      encodeCliStdin(definition, stdin), signal,
      undefined, 'validation')
  }

  async runModelProbeValidation(userId: string, cliId: CliId, modelId: string, stdin: string, signal?: AbortSignal) {
    const definition = this.invocableDefinition(cliId)
    if ((cliId !== 'codex' && cliId !== 'claude_code') || !definition.authStatusArgs) {
      throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    }
    return this.runFixedAuthorized(userId, cliId, buildExecutionArgs(definition, validateConfirmedModelId(modelId)),
      encodeCliStdin(definition, stdin), signal, undefined, 'validation')
  }

  async confirmManualModel(cliId: CliId, identity: CliInstallationIdentity, modelId: string) {
    const current = this.confirmedIdentities.get(cliId)
    if (!current || !isDeepStrictEqual(current.identity, identity)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    this.confirmedIdentities.set(cliId, Object.freeze({ ...current,
      modelIds: new Set([...current.modelIds, validateConfirmedModelId(modelId)]),
      manualModelIds: new Set([...current.manualModelIds, modelId]) }))
  }

  async runExecution(userId: string, cliId: CliId, input: { modelId: string | null; stdin: string;
    effort?: AiEffort; responseSchema?: unknown; maxOutputTokens?: number; signal?: AbortSignal }) {
    const definition = this.invocableDefinition(cliId)
    await this.ensureConfirmed(userId, cliId, input.signal)
    const modelId = input.modelId === null ? null : validateConfirmedModelId(input.modelId)
    if (definition.modelCatalog?.format === 'codex_app_server'
      || !this.confirmedIdentities.get(cliId)?.modelIds.has(modelId)
      || (input.effort && !cliEffortLevels(cliId, modelId,
        modelId ? this.catalogEfforts.get(cliId)?.get(modelId) : undefined).includes(AiEffortSchema.parse(input.effort)))) {
      // Authentication can change independently of the binary. Recheck the current
      // subscription and model capabilities before inference, even for model default.
      await this.refreshConfirmedModels(userId, cliId, input.signal)
    } else if (definition.modelCatalog?.format === 'claude_control') {
      await this.runAuthValidation(userId, cliId, input.signal)
    }
    const confirmed = this.confirmedIdentities.get(cliId)
    if (!confirmed) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    if (!confirmed.modelIds.has(modelId)) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    const schemaJson = input.responseSchema === undefined ? undefined : JSON.stringify(input.responseSchema)
    const schemaOption = schemaJson === undefined ? {}
      : definition.id === 'codex' ? { schemaPath: '__SCHEMA__' }
        : definition.id === 'claude_code' || definition.id === 'gemini_antigravity'
          ? { schemaPath: schemaJson } : {}
    const args = buildExecutionArgs(definition, input.modelId, { ...schemaOption, effort: input.effort,
      supportedEfforts: input.modelId ? this.catalogEfforts.get(cliId)?.get(input.modelId) : undefined })
    if (definition.execution.transport === 'kimi_acp') {
      return await this.runFixedAuthorized(userId, cliId, args, input.stdin, input.signal,
        undefined, 'execution', (prepared, signal) => this.startKimiAcp(prepared, input.modelId, signal))
    }
    return await this.runFixedAuthorized(userId, cliId, args, encodeCliStdin(definition, input.stdin), input.signal,
      definition.id === 'codex' ? schemaJson : undefined, 'execution')
  }

  private async runFixedAuthorized(userId: string, cliId: CliId, args: readonly string[], stdin: string,
    signal: AbortSignal | undefined, schemaJson: string | undefined,
    purpose: 'execution' | 'validation', starter?: CliStarter): Promise<CliProcessResult> {
    const release = await this.acquire(cliId, signal)
    let prepared: PreparedCliProcess | undefined
    let transferred = false
    try {
      const definition = this.definition(cliId)
      let identity = purpose === 'execution'
        ? this.confirmedIdentities.get(cliId)?.identity
        : this.validationIdentities.get(cliId)
      const handle = await withCliInvocationAuthorization(userId, cliId,
        () => {
          if (!prepared) throw new AiConsoleError('AI_EXECUTION_FAILED')
          const started = starter ? starter(prepared!, signal) : this.start(prepared!, signal)
          transferred = true
          return started
        }, purpose, async () => {
          if (!identity && purpose === 'validation') identity = await this.inspectInstallation(cliId)
          if (!identity) throw new AiConsoleError('AI_CLI_UNREACHABLE')
          prepared = await this.prepare(identity, args, stdin, schemaJson)
          try { await assertCurrentInstallationIdentity(definition, identity) }
          catch {
            this.invalidateIdentity(cliId, identity)
            throw new AiConsoleError('AI_CLI_UNREACHABLE')
          }
        })
      return await handle.completion
    } finally {
      if (prepared && !transferred) await rm(prepared.cwd, { recursive: true, force: true })
      release()
    }
  }

  private invalidateIdentity(cliId: CliId, identity: CliInstallationIdentity) {
    this.catalogEfforts.delete(cliId)
    this.catalogModelIds.delete(cliId)
    if (this.validationIdentities.get(cliId) === identity) this.validationIdentities.delete(cliId)
    if (this.confirmedIdentities.get(cliId)?.identity === identity) this.confirmedIdentities.delete(cliId)
  }

  private async refreshConfirmedModels(userId: string, cliId: CliId, signal?: AbortSignal): Promise<void> {
    if (!this.definition(cliId).modelCatalog) return
    const key = `${userId}:${cliId}`
    let flight = this.catalogRefreshFlights.get(key)
    if (!flight) {
      flight = this.refreshConfirmedModelsOnce(userId, cliId, signal)
      this.catalogRefreshFlights.set(key, flight)
      void flight.finally(() => {
        if (this.catalogRefreshFlights.get(key) === flight) this.catalogRefreshFlights.delete(key)
      }).catch(() => undefined)
    }
    await flight
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  }

  private async refreshConfirmedModelsOnce(userId: string, cliId: CliId, signal?: AbortSignal): Promise<void> {
    const previous = this.confirmedIdentities.get(cliId)
    if (!previous) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    const deadline = AbortSignal.timeout(30_000)
    const combined = signal ? AbortSignal.any([signal, deadline]) : deadline
    try {
      const models = await readUnchangedCatalog(this, userId, cliId, previous.identity, combined)
      const current = this.confirmedIdentities.get(cliId)
      if (!current || current.version !== previous.version
        || !isDeepStrictEqual(current.identity, previous.identity)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
      await this.confirmValidation(cliId, current.identity, current.version,
        [...new Set([null, ...current.manualModelIds, ...models.map(model => model.modelId)])])
    } catch (error) {
      if (deadline.aborted && !signal?.aborted) throw new AiConsoleError('AI_CLI_TIMEOUT')
      throw error
    }
  }

  private async ensureConfirmed(userId: string, cliId: CliId, signal?: AbortSignal): Promise<void> {
    if (this.confirmedIdentities.has(cliId)) return
    const key = `${userId}:${cliId}`
    let flight = this.revalidationFlights.get(key)
    if (!flight) {
      flight = this.revalidate(userId, cliId, signal, this, this.registry)
      this.revalidationFlights.set(key, flight)
      void flight.finally(() => {
        if (this.revalidationFlights.get(key) === flight) this.revalidationFlights.delete(key)
      }).catch(() => undefined)
    }
    try { await flight }
    catch (error) {
      if (error instanceof AiConsoleError && (error.code === 'AI_CLI_NOT_GRANTED'
        || (signal?.aborted && error.code === 'AI_EXECUTION_FAILED'))) throw error
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    if (!this.confirmedIdentities.has(cliId)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  }

  inspectForTests() { return { active: this.active, queued: this.queue.length } }

  private definition(cliId: CliId): CliDefinition {
    if (this.environment.NODE_ENV === 'production'
      && this.environment.MARSYS_AI_LOCAL_CLI_EXECUTION_ENABLED !== 'true') {
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    const parsed = CliIdSchema.parse(cliId)
    const definition = this.registry[parsed]
    if (!definition) throw new AiConsoleError('AI_CLI_NOT_INSTALLED')
    return definition
  }

  private invocableDefinition(cliId: CliId): CliDefinition & { execution: NonNullable<CliDefinition['execution']> } {
    const definition = this.definition(cliId)
    if (!definition.execution) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    return definition as CliDefinition & { execution: NonNullable<CliDefinition['execution']> }
  }

  private acquire(cliId: CliId, signal?: AbortSignal): Promise<() => void> {
    this.definition(cliId)
    if (signal?.aborted) return Promise.reject(new AiConsoleError('AI_EXECUTION_FAILED'))
    if (this.canStart(cliId)) return Promise.resolve(this.reserve(cliId))
    return new Promise((resolveQueue, reject) => {
      const item: QueueItem = { cliId, resolve: resolveQueue, reject, signal }
      item.onAbort = () => {
        const index = this.queue.indexOf(item)
        if (index >= 0) this.queue.splice(index, 1)
        reject(new AiConsoleError('AI_EXECUTION_FAILED'))
      }
      signal?.addEventListener('abort', item.onAbort, { once: true })
      this.queue.push(item)
    })
  }

  private canStart(cliId: CliId): boolean {
    return this.active < this.limits.globalConcurrency
      && (this.activeByCli.get(cliId) ?? 0) < this.limits.perCliConcurrency
  }

  private reserve(cliId: CliId): () => void {
    this.active++
    this.activeByCli.set(cliId, (this.activeByCli.get(cliId) ?? 0) + 1)
    let released = false
    return () => {
      if (released) return
      released = true
      this.active--
      const remaining = (this.activeByCli.get(cliId) ?? 1) - 1
      if (remaining) this.activeByCli.set(cliId, remaining); else this.activeByCli.delete(cliId)
      this.pump()
    }
  }

  private pump() {
    for (let i = 0; i < this.queue.length;) {
      const item = this.queue[i]
      if (item.signal?.aborted) { this.queue.splice(i, 1); item.reject(new AiConsoleError('AI_EXECUTION_FAILED')); continue }
      if (!this.canStart(item.cliId)) { i++; continue }
      this.queue.splice(i, 1)
      item.signal?.removeEventListener('abort', item.onAbort!)
      item.resolve(this.reserve(item.cliId))
    }
  }

  private async prepare(identity: CliInstallationIdentity, args: readonly string[], input: string,
    schemaJson?: string): Promise<PreparedCliProcess> {
    if (process.platform === 'win32') throw new AiConsoleError('AI_CLI_UNREACHABLE')
    if (!Array.isArray(args) || args.some(arg => typeof arg !== 'string' || arg.includes('\0'))) {
      throw new AiConsoleError('AI_EXECUTION_FAILED')
    }
    const stdinBytes = Buffer.from(input, 'utf8')
    if (stdinBytes.byteLength > this.limits.stdinBytes) throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
    const cwd = await mkdtemp(resolve(tmpdir(), 'madhav-ai-cli-'))
    try {
      let schemaPath: string | undefined
      if (schemaJson !== undefined) {
        if (Buffer.byteLength(schemaJson, 'utf8') > 64 * 1024) throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
        schemaPath = join(cwd, 'output-schema.json')
        await writeFile(schemaPath, schemaJson, { encoding: 'utf8', mode: 0o600, flag: 'wx' })
      }
      const fixedArgs = args.map(arg => arg === '__CWD__' ? cwd
        : arg === '__SCHEMA__' && schemaPath ? schemaPath : arg)
      const executable = identity.interpreter?.realpath ?? identity.entrypoint.realpath
      const processArgs = identity.interpreter ? [identity.entrypoint.realpath, ...fixedArgs] : fixedArgs
      return Object.freeze({ executable, processArgs, stdinBytes, cwd })
    } catch (error) {
      await rm(cwd, { recursive: true, force: true })
      throw error
    }
  }

  private start(prepared: PreparedCliProcess, signal?: AbortSignal): StartedCliProcess {
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
    let child: ChildProcessWithoutNullStreams
    try {
      child = spawn(prepared.executable, prepared.processArgs, {
        shell: false, detached: true, cwd: prepared.cwd, env: safeEnvironment(this.environment),
        stdio: ['pipe', 'pipe', 'pipe'],
      })
    } catch {
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    if (!child.pid) {
      // Failed async spawn (for example EACCES) still emits `error` next tick.
      child.on('error', () => undefined)
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }

    let settled = false
    let finalizing = false
    let terminalError: AiConsoleError | undefined
    const lifecycle: { timeout?: NodeJS.Timeout; termination?: Promise<void> } = {}
    const stdout: Buffer[] = []
    let stdoutBytes = 0
    let stderrBytes = 0
    let resolveCompletion!: (value: CliProcessResult) => void
    let rejectCompletion!: (error: AiConsoleError) => void
    const cleanup = async () => {
      if (lifecycle.timeout) clearTimeout(lifecycle.timeout)
      signal?.removeEventListener('abort', onAbort)
      child.stdout.removeAllListeners(); child.stderr.removeAllListeners()
      child.removeAllListeners('close'); child.removeAllListeners('exit')
      child.removeAllListeners('error'); child.on('error', () => undefined)
      try { await rm(prepared.cwd, { recursive: true, force: true }) }
      catch { terminalError ??= new AiConsoleError('AI_EXECUTION_FAILED') }
    }
    const groupExists = () => {
      try { process.kill(-child.pid!, 0); return true }
      catch (error) {
        if ((error as NodeJS.ErrnoException).code === 'ESRCH') return false
        if ((error as NodeJS.ErrnoException).code === 'EPERM') return true
        throw error
      }
    }
    const signalGroup = (killSignal: NodeJS.Signals) => {
      try { process.kill(-child.pid!, killSignal) }
      catch (error) {
        if ((error as NodeJS.ErrnoException).code !== 'ESRCH') throw error
      }
    }
    const terminateGroup = () => {
      if (lifecycle.termination) return lifecycle.termination
      lifecycle.termination = (async () => {
        signalGroup('SIGTERM')
        const escalationAt = Date.now() + this.limits.killGraceMs
        while (groupExists()) {
          if (Date.now() >= escalationAt) signalGroup('SIGKILL')
          await new Promise(resolvePoll => setTimeout(resolvePoll, Math.min(10, this.limits.killGraceMs)))
        }
      })()
      return lifecycle.termination
    }
    const fail = (error: AiConsoleError) => {
      if (settled || terminalError) return
      terminalError = error
      void terminateGroup().catch(() => undefined)
    }
    const onAbort = () => fail(new AiConsoleError('AI_EXECUTION_FAILED'))
    const completion = new Promise<CliProcessResult>((resolvePromise, rejectPromise) => {
      resolveCompletion = resolvePromise; rejectCompletion = rejectPromise
    })
    // Authorization commits after start(). Observe an immediate child failure
    // now so a later commit rejection cannot leave completion unhandled.
    void completion.catch(() => undefined)
    child.stdout.on('data', (chunk: Buffer) => {
      stdoutBytes += chunk.byteLength
      if (stdoutBytes > this.limits.stdoutBytes) { fail(new AiConsoleError('AI_CLI_OUTPUT_LIMIT')); return }
      stdout.push(Buffer.from(chunk))
    })
    child.stderr.on('data', (chunk: Buffer) => {
      stderrBytes += chunk.byteLength
      if (stderrBytes > this.limits.stderrBytes) fail(new AiConsoleError('AI_CLI_OUTPUT_LIMIT'))
    })
    child.on('error', () => fail(new AiConsoleError('AI_CLI_UNREACHABLE')))
    child.on('close', (code, closeSignal) => {
      if (settled || finalizing) return
      finalizing = true
      void (async () => {
        try { await terminateGroup() }
        catch { terminalError ??= new AiConsoleError('AI_EXECUTION_FAILED') }
        settled = true
        await cleanup()
        const failure = terminalError
        if (failure) { rejectCompletion(failure); return }
        if (code !== 0) { rejectCompletion(new AiConsoleError('AI_CLI_UNREACHABLE')); return }
        let decoded: string
        try { decoded = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(stdout)) }
        catch { rejectCompletion(new AiConsoleError('AI_EXECUTION_FAILED')); return }
        resolveCompletion({ stdout: decoded, exitCode: code, signal: closeSignal })
      })()
    })
    lifecycle.timeout = setTimeout(() => fail(new AiConsoleError('AI_CLI_TIMEOUT')), this.limits.timeoutMs)
    lifecycle.timeout.unref?.()
    signal?.addEventListener('abort', onAbort, { once: true })
    child.stdin.on('error', () => undefined)
    child.stdin.end(prepared.stdinBytes)

    let cancelled = false
    return Object.freeze({
      pid: child.pid,
      completion,
      cancel: () => {
        if (cancelled || settled || finalizing) return
        cancelled = true
        fail(new AiConsoleError('AI_EXECUTION_FAILED'))
      },
    })
  }

  private startKimiAcp(prepared: PreparedCliProcess, modelId: string | null,
    signal?: AbortSignal): StartedCliProcess {
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
    let child: ChildProcessWithoutNullStreams
    try {
      child = spawn(prepared.executable, prepared.processArgs, {
        shell: false, detached: true, cwd: prepared.cwd, env: safeEnvironment(this.environment),
        stdio: ['pipe', 'pipe', 'pipe'],
      })
    } catch { throw new AiConsoleError('AI_CLI_UNREACHABLE') }
    if (!child.pid) {
      child.on('error', () => undefined)
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }

    let settled = false
    let finalizing = false
    let terminalError: AiConsoleError | undefined
    let sessionId: string | undefined
    let answer = ''
    let stdoutBytes = 0
    let stderrBytes = 0
    let lineBuffer = ''
    const decoder = new StringDecoder('utf8')
    const lifecycle: { timeout?: NodeJS.Timeout; termination?: Promise<void> } = {}
    let resolveCompletion!: (value: CliProcessResult) => void
    let rejectCompletion!: (error: AiConsoleError) => void
    const completion = new Promise<CliProcessResult>((resolvePromise, rejectPromise) => {
      resolveCompletion = resolvePromise; rejectCompletion = rejectPromise
    })
    void completion.catch(() => undefined)

    const groupExists = () => {
      try { process.kill(-child.pid!, 0); return true }
      catch (error) {
        if ((error as NodeJS.ErrnoException).code === 'ESRCH') return false
        if ((error as NodeJS.ErrnoException).code === 'EPERM') return true
        throw error
      }
    }
    const signalGroup = (killSignal: NodeJS.Signals) => {
      try { process.kill(-child.pid!, killSignal) }
      catch (error) { if ((error as NodeJS.ErrnoException).code !== 'ESRCH') throw error }
    }
    const terminateGroup = () => {
      if (lifecycle.termination) return lifecycle.termination
      lifecycle.termination = (async () => {
        signalGroup('SIGTERM')
        const escalationAt = Date.now() + this.limits.killGraceMs
        while (groupExists()) {
          if (Date.now() >= escalationAt) signalGroup('SIGKILL')
          await new Promise(resolvePoll => setTimeout(resolvePoll, Math.min(10, this.limits.killGraceMs)))
        }
      })()
      return lifecycle.termination
    }
    const cleanup = async () => {
      if (lifecycle.timeout) clearTimeout(lifecycle.timeout)
      signal?.removeEventListener('abort', onAbort)
      child.stdout.removeAllListeners(); child.stderr.removeAllListeners(); child.stdin.removeAllListeners()
      child.removeAllListeners('close'); child.removeAllListeners('exit'); child.removeAllListeners('error')
      child.on('error', () => undefined)
      try { await rm(prepared.cwd, { recursive: true, force: true }) }
      catch { terminalError ??= new AiConsoleError('AI_EXECUTION_FAILED') }
    }
    const finish = (error?: AiConsoleError) => {
      if (settled || finalizing) return
      finalizing = true
      terminalError ??= error
      void (async () => {
        try { await terminateGroup() } catch { terminalError ??= new AiConsoleError('AI_EXECUTION_FAILED') }
        settled = true
        await cleanup()
        if (terminalError) { rejectCompletion(terminalError); return }
        resolveCompletion({ stdout: JSON.stringify({ text: answer }), exitCode: 0, signal: null })
      })()
    }
    const fail = (error: AiConsoleError) => finish(error)
    const onAbort = () => fail(new AiConsoleError('AI_EXECUTION_FAILED'))
    const send = (value: unknown) => {
      if (settled || finalizing || child.stdin.destroyed) return
      const payload = `${JSON.stringify(value)}\n`
      if (Buffer.byteLength(payload, 'utf8') > this.limits.stdinBytes) {
        fail(new AiConsoleError('AI_CLI_OUTPUT_LIMIT')); return
      }
      child.stdin.write(payload)
    }
    const prompt = () => send({ jsonrpc: '2.0', id: 5, method: 'session/prompt', params: {
      sessionId, prompt: [{ type: 'text', text: prepared.stdinBytes.toString('utf8') }],
    } })
    const handle = (raw: unknown) => {
      if (!raw || typeof raw !== 'object') { fail(new AiConsoleError('AI_EXECUTION_FAILED')); return }
      const message = raw as Record<string, unknown>
      if (message.method === 'session/request_permission' && message.id !== undefined) {
        send({ jsonrpc: '2.0', id: message.id, result: { outcome: { outcome: 'cancelled' } } })
        return
      }
      if (message.method === 'session/update') {
        const params = message.params as Record<string, unknown> | undefined
        const update = params?.update as Record<string, unknown> | undefined
        if (!params || params.sessionId !== sessionId || !update || typeof update.sessionUpdate !== 'string') {
          fail(new AiConsoleError('AI_EXECUTION_FAILED')); return
        }
        if (update.sessionUpdate === 'agent_message_chunk') {
          const content = update.content as Record<string, unknown> | undefined
          if (!content || content.type !== 'text' || typeof content.text !== 'string') {
            fail(new AiConsoleError('AI_EXECUTION_FAILED')); return
          }
          answer += content.text
          if (Buffer.byteLength(answer, 'utf8') > this.limits.stdoutBytes) fail(new AiConsoleError('AI_CLI_OUTPUT_LIMIT'))
        } else if (update.sessionUpdate.includes('tool_call')) {
          fail(new AiConsoleError('AI_ROLE_INCOMPATIBLE'))
        }
        return
      }
      if (message.id === 1) {
        const result = message.result as Record<string, unknown> | undefined
        if (result?.protocolVersion !== 1) { fail(new AiConsoleError('AI_CLI_UNREACHABLE')); return }
        send({ jsonrpc: '2.0', id: 2, method: 'session/new', params: { cwd: prepared.cwd, mcpServers: [] } })
      } else if (message.id === 2) {
        const result = message.result as Record<string, unknown> | undefined
        if (!result || typeof result.sessionId !== 'string') { fail(new AiConsoleError('AI_CLI_UNREACHABLE')); return }
        sessionId = result.sessionId
        send({ jsonrpc: '2.0', id: 3, method: 'session/set_config_option', params: {
          sessionId, configId: 'mode', value: 'plan',
        } })
      } else if (message.id === 3) {
        if (message.error) { fail(new AiConsoleError('AI_CLI_UNREACHABLE')); return }
        if (modelId === null) prompt()
        else send({ jsonrpc: '2.0', id: 4, method: 'session/set_config_option', params: {
          sessionId, configId: 'model', value: modelId,
        } })
      } else if (message.id === 4) {
        if (message.error) { fail(new AiConsoleError('AI_MODEL_UNAVAILABLE')); return }
        prompt()
      } else if (message.id === 5) {
        const result = message.result as Record<string, unknown> | undefined
        if (result?.stopReason !== 'end_turn' || !answer) { fail(new AiConsoleError('AI_EXECUTION_FAILED')); return }
        finish()
      } else if (message.id !== undefined || message.method !== undefined) {
        fail(new AiConsoleError('AI_EXECUTION_FAILED'))
      }
    }

    child.stdout.on('data', (chunk: Buffer) => {
      stdoutBytes += chunk.byteLength
      if (stdoutBytes > this.limits.stdoutBytes) { fail(new AiConsoleError('AI_CLI_OUTPUT_LIMIT')); return }
      lineBuffer += decoder.write(chunk)
      let newline = lineBuffer.indexOf('\n')
      while (newline >= 0) {
        const line = lineBuffer.slice(0, newline).trim(); lineBuffer = lineBuffer.slice(newline + 1)
        if (line) {
          try { handle(JSON.parse(line)) } catch { fail(new AiConsoleError('AI_EXECUTION_FAILED')); return }
        }
        newline = lineBuffer.indexOf('\n')
      }
    })
    child.stderr.on('data', (chunk: Buffer) => {
      stderrBytes += chunk.byteLength
      if (stderrBytes > this.limits.stderrBytes) fail(new AiConsoleError('AI_CLI_OUTPUT_LIMIT'))
    })
    child.on('error', () => fail(new AiConsoleError('AI_CLI_UNREACHABLE')))
    child.on('close', () => {
      if (!settled && !finalizing) fail(new AiConsoleError('AI_CLI_UNREACHABLE'))
    })
    lifecycle.timeout = setTimeout(() => fail(new AiConsoleError('AI_CLI_TIMEOUT')), this.limits.timeoutMs)
    lifecycle.timeout.unref?.()
    signal?.addEventListener('abort', onAbort, { once: true })
    child.stdin.on('error', () => fail(new AiConsoleError('AI_CLI_UNREACHABLE')))
    send({ jsonrpc: '2.0', id: 1, method: 'initialize', params: {
      protocolVersion: 1, clientCapabilities: {}, clientInfo: { name: 'Madhav', version: '1' },
    } })

    let cancelled = false
    return Object.freeze({ pid: child.pid, completion, cancel: () => {
      if (cancelled || settled || finalizing) return
      cancelled = true; fail(new AiConsoleError('AI_EXECUTION_FAILED'))
    } })
  }
}

/** Exit zero from an auth-status command alone is not proof of subscription authentication. */
function assertSubscriptionAuth(cliId: CliId, stdout: string): void {
  // Codex auth is checked using the structured app-server account/read response;
  // login/status writes its human-readable status to stderr.
  if (cliId === 'claude_code') {
    let auth: unknown
    try { auth = JSON.parse(stdout) } catch { throw new AiConsoleError('AI_CLI_AUTH_UNAVAILABLE') }
    if (!z.object({ loggedIn: z.literal(true), authMethod: z.literal('claude.ai'),
      apiProvider: z.literal('firstParty') }).passthrough().safeParse(auth).success) {
      throw new AiConsoleError('AI_CLI_AUTH_UNAVAILABLE')
    }
  }
}

async function captureInstallationIdentity(definition: CliDefinition): Promise<CliInstallationIdentity> {
  const entrypoint = await captureTrustedFile(definition.candidates, definition.allowedRealpathPrefixes)
  const interpreter = definition.interpreter
    ? await captureTrustedFile([definition.interpreter.candidate], definition.interpreter.allowedRealpathPrefixes) : undefined
  return Object.freeze({ cliId: definition.id, entrypoint, ...(interpreter ? { interpreter } : {}) })
}

type CliFileMetadata = Omit<CliFileIdentity, 'sha256'>

async function captureTrustedFile(candidates: readonly string[], allowedRealpathPrefixes: readonly string[]): Promise<CliFileIdentity> {
  if (candidates.length === 0) throw new AiConsoleError('AI_CLI_NOT_INSTALLED')
  if (candidates.length !== 1) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  const before = await captureTrustedFileMetadata(candidates[0], allowedRealpathPrefixes)
  let sha256: string
  try {
    const hash = createHash('sha256')
    for await (const chunk of createReadStream(before.realpath)) hash.update(chunk as Buffer)
    sha256 = hash.digest('hex')
  } catch { throw new AiConsoleError('AI_CLI_UNREACHABLE') }
  const after = await captureTrustedFileMetadata(candidates[0], allowedRealpathPrefixes)
  if (!isDeepStrictEqual(before, after)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  return Object.freeze({ ...after, sha256 })
}

async function captureTrustedFileMetadata(candidate: string,
  allowedRealpathPrefixes: readonly string[]): Promise<CliFileMetadata> {
  if (!isAbsolute(candidate)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  try {
    await lstat(candidate)
  } catch (error) {
    throw new AiConsoleError((error as NodeJS.ErrnoException).code === 'ENOENT'
      ? 'AI_CLI_NOT_INSTALLED' : 'AI_CLI_UNREACHABLE')
  }
  try {
    const real = await realpath(candidate)
    const prefix = allowedRealpathPrefixes.find(allowed => {
      const boundary = resolve(allowed)
      return real === boundary || real.startsWith(`${boundary}/`)
    })
    if (!prefix) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    const current = await stat(real)
    const processUid = typeof process.getuid === 'function' ? process.getuid() : current.uid
    if (!current.isFile() || (current.mode & 0o111) === 0 || (current.mode & 0o022) !== 0
      || (current.uid !== 0 && current.uid !== processUid)
      || !await hasTrustedParents(real, prefix, processUid)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    return Object.freeze({ candidate, realpath: real, device: String(current.dev), inode: String(current.ino),
      size: current.size, modifiedMs: current.mtimeMs, changedMs: current.ctimeMs, mode: current.mode,
      uid: current.uid })
  } catch (error) {
    if (error instanceof AiConsoleError) throw error
    throw new AiConsoleError('AI_CLI_UNREACHABLE')
  }
}

async function assertCurrentInstallationIdentity(definition: CliDefinition,
  identity: CliInstallationIdentity): Promise<void> {
  if (identity.cliId !== definition.id || definition.candidates.length !== 1
    || identity.entrypoint.candidate !== definition.candidates[0]) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  const entrypoint = await captureTrustedFileMetadata(identity.entrypoint.candidate,
    definition.allowedRealpathPrefixes)
  if (!isDeepStrictEqual(entrypoint, fileMetadata(identity.entrypoint))) {
    throw new AiConsoleError('AI_CLI_UNREACHABLE')
  }
  if (definition.interpreter) {
    if (!identity.interpreter || identity.interpreter.candidate !== definition.interpreter.candidate) {
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    const interpreter = await captureTrustedFileMetadata(identity.interpreter.candidate,
      definition.interpreter.allowedRealpathPrefixes)
    if (!isDeepStrictEqual(interpreter, fileMetadata(identity.interpreter))) {
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
  } else if (identity.interpreter) throw new AiConsoleError('AI_CLI_UNREACHABLE')
}

function fileMetadata(identity: CliFileIdentity): CliFileMetadata {
  return { candidate: identity.candidate, realpath: identity.realpath, device: identity.device,
    inode: identity.inode, size: identity.size, modifiedMs: identity.modifiedMs, changedMs: identity.changedMs,
    mode: identity.mode, uid: identity.uid }
}

async function hasTrustedParents(real: string, allowedPrefix: string, uid: number): Promise<boolean> {
  const boundary = resolve(allowedPrefix)
  let current = dirname(real)
  while (true) {
    const currentStat = await stat(current)
    if (!currentStat.isDirectory() || (currentStat.mode & 0o022) !== 0
      || (currentStat.uid !== 0 && currentStat.uid !== uid)) return false
    if (current === boundary) return true
    const parent = dirname(current)
    if (parent === current) return false
    current = parent
  }
}

function safeEnvironment(source: NodeJS.ProcessEnv): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {
    PATH: '/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin',
    NODE_ENV: source.NODE_ENV ?? 'production',
  }
  for (const key of ['HOME', 'USER', 'LOGNAME', 'LANG', 'LC_ALL', 'TMPDIR', 'XDG_CONFIG_HOME', 'CODEX_HOME']) {
    const value = source[key]
    if (typeof value === 'string' && value.length > 0 && !value.includes('\0')) env[key] = value
  }
  return env
}

function validateConfirmedModelId(modelId: string): string {
  const parsed = validateCliModelId(modelId)
  if (!parsed) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  return parsed
}

function encodeCliStdin(definition: CliDefinition, prompt: string): string {
  return definition.execution?.transport === 'antigravity_stream_json'
    ? `${JSON.stringify({ event: 'user', message: { content: prompt } })}\n`
    : prompt
}

async function revalidateCliForExecution(userId: string, cliId: CliId, signal: AbortSignal | undefined,
  runner: CliRunner, registry: Registry): Promise<void> {
  const { validateCli } = await import('./validation')
  const result = await validateCli(userId, cliId, signal, { runner, registry })
  if (result.state !== 'reachable') throw new AiConsoleError('AI_CLI_UNREACHABLE')
}

/** Metadata can extend a tested binary's choices, but cannot confirm a replacement binary. */
async function readUnchangedCatalog(runner: CliRunner, userId: string, cliId: CliId,
  identity: CliInstallationIdentity, signal: AbortSignal): Promise<CliDiscoveredModel[]> {
  if (signal.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  const before = await runner.inspectInstallation(cliId, signal)
  if (!isDeepStrictEqual(before, identity)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  const models = await runner.runModelCatalogValidation(userId, cliId, signal)
  if (signal.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  const after = await runner.inspectInstallation(cliId, signal)
  if (signal.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
  if (!isDeepStrictEqual(after, identity)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
  return models
}

function confirmedManualModels(previous: ConfirmedCliInstallation | undefined, identity: CliInstallationIdentity,
  modelIds: readonly (string | null)[], catalogModelIds: ReadonlySet<string> | undefined): ReadonlySet<string> {
  const previousManual = previous && isDeepStrictEqual(previous.identity, identity) ? previous.manualModelIds : undefined
  return new Set(modelIds.filter((modelId): modelId is string => modelId !== null
    && (previousManual?.has(modelId) || !catalogModelIds?.has(modelId))))
}

export function createCliRunner(options: ConstructorParameters<typeof GovernedCliRunner>[0] = {}): CliRunner {
  return new GovernedCliRunner(options)
}

export function createRemoteCliRunner(options: { endpoint: string; token: string; fetchImpl?: BridgeFetch }): CliRunner {
  return new RemoteCliRunner(options)
}

function validateBridgeEndpoint(value: string): URL {
  let endpoint: URL
  try { endpoint = new URL(value) } catch { throw new AiConsoleError('AI_CLI_UNREACHABLE') }
  const privateIpv4 = /^10(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/.test(endpoint.hostname)
  const privateEndpoint = privateIpv4 || endpoint.hostname === '127.0.0.1'
  if (!privateEndpoint || (endpoint.protocol !== 'http:' && endpoint.protocol !== 'https:')) {
    throw new AiConsoleError('AI_CLI_UNREACHABLE')
  }
  if (endpoint.username || endpoint.password || endpoint.search || endpoint.hash) {
    throw new AiConsoleError('AI_CLI_UNREACHABLE')
  }
  return endpoint
}

export function createConfiguredCliRunner(environment: NodeJS.ProcessEnv = process.env): CliRunner {
  const endpoint = environment.MARSYS_AI_CLI_BRIDGE_URL
  const token = environment.MARSYS_AI_CLI_BRIDGE_TOKEN
  if (endpoint || token) {
    if (!endpoint || !token) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    return createRemoteCliRunner({ endpoint, token })
  }
  return createCliRunner({ environment })
}

export const cliRunner = createConfiguredCliRunner()
