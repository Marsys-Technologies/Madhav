import 'server-only'
import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process'
import { createHash } from 'node:crypto'
import { createReadStream } from 'node:fs'
import { lstat, mkdtemp, realpath, rm, stat, writeFile } from 'node:fs/promises'
import { dirname, isAbsolute, join, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { isDeepStrictEqual } from 'node:util'
import { AiConsoleError } from '../errors'
import { withCliInvocationAuthorization, type CliInvocationHandle } from '../repository'
import { CliIdSchema, type CliId } from '../types'
import { buildExecutionArgs, CLI_REGISTRY, type CliDefinition } from './registry'

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

export interface CliRunner {
  inspectInstallation(cliId: CliId): Promise<CliInstallationIdentity>
  confirmValidation(cliId: CliId, identity: CliInstallationIdentity, version: string): Promise<void>
  runVersionValidation(userId: string, cliId: CliId, signal?: AbortSignal): Promise<CliProcessResult>
  runAuthValidation(userId: string, cliId: CliId, signal?: AbortSignal): Promise<CliProcessResult>
  runProbeValidation(userId: string, cliId: CliId, stdin: string, signal?: AbortSignal): Promise<CliProcessResult>
  runExecution(userId: string, cliId: CliId, input: { modelId: string | null; stdin: string;
    responseSchema?: unknown; signal?: AbortSignal }): Promise<CliProcessResult>
  inspectForTests(): { active: number; queued: number }
}

class GovernedCliRunner implements CliRunner {
  private readonly registry: Registry
  private readonly limits: CliRunLimits
  private readonly environment: NodeJS.ProcessEnv
  private active = 0
  private readonly activeByCli = new Map<CliId, number>()
  private readonly queue: QueueItem[] = []
  private readonly validationIdentities = new Map<CliId, CliInstallationIdentity>()
  private readonly confirmedIdentities = new Map<CliId, { identity: CliInstallationIdentity; version: string }>()

  constructor(options: { registry?: Registry; limits?: Partial<CliRunLimits>; environment?: NodeJS.ProcessEnv } = {}) {
    this.registry = options.registry ?? CLI_REGISTRY
    this.limits = Object.freeze({ ...DEFAULT_LIMITS, ...options.limits })
    this.environment = options.environment ?? process.env
    if (Object.values(this.limits).some(value => !Number.isSafeInteger(value) || value <= 0)) {
      throw new AiConsoleError('AI_EXECUTION_FAILED')
    }
  }

  async inspectInstallation(cliId: CliId): Promise<CliInstallationIdentity> {
    const definition = this.definition(cliId)
    const identity = await captureInstallationIdentity(definition)
    this.validationIdentities.set(cliId, identity)
    return identity
  }

  async confirmValidation(cliId: CliId, identity: CliInstallationIdentity, version: string): Promise<void> {
    const definition = this.definition(cliId)
    if (!definition.execution || version !== definition.supportedVersion || identity.cliId !== definition.id) {
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    try { await assertCurrentInstallationIdentity(definition, identity) }
    catch {
      this.invalidateIdentity(cliId, identity)
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    this.confirmedIdentities.set(cliId, Object.freeze({ identity, version }))
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
    // Auth-status output can contain account identity. Only its safe exit fact
    // crosses the dedicated runner boundary.
    return { ...result, stdout: '' }
  }

  async runProbeValidation(userId: string, cliId: CliId, stdin: string, signal?: AbortSignal) {
    const definition = this.invocableDefinition(cliId)
    return await this.runFixedAuthorized(userId, cliId, buildExecutionArgs(definition, null), stdin, signal,
      undefined, 'validation')
  }

  async runExecution(userId: string, cliId: CliId, input: { modelId: string | null; stdin: string;
    responseSchema?: unknown; signal?: AbortSignal }) {
    const definition = this.invocableDefinition(cliId)
    // No approved CLI exposes a machine-readable model catalog. Until one does,
    // the sole catalog entry is the built-in default represented by null.
    if (input.modelId !== null) throw new AiConsoleError('AI_MODEL_UNAVAILABLE')
    const schemaJson = input.responseSchema === undefined ? undefined : JSON.stringify(input.responseSchema)
    const schemaOption = schemaJson === undefined ? {}
      : definition.id === 'codex' ? { schemaPath: '__SCHEMA__' }
        : definition.id === 'claude_code' ? { schemaPath: schemaJson } : {}
    const args = buildExecutionArgs(definition, input.modelId, schemaOption)
    return await this.runFixedAuthorized(userId, cliId, args, input.stdin, input.signal,
      definition.id === 'codex' ? schemaJson : undefined, 'execution')
  }

  private async runFixedAuthorized(userId: string, cliId: CliId, args: readonly string[], stdin: string,
    signal: AbortSignal | undefined, schemaJson: string | undefined,
    purpose: 'execution' | 'validation'): Promise<CliProcessResult> {
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
          const started = this.start(prepared!, signal)
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
    if (this.validationIdentities.get(cliId) === identity) this.validationIdentities.delete(cliId)
    if (this.confirmedIdentities.get(cliId)?.identity === identity) this.confirmedIdentities.delete(cliId)
  }

  inspectForTests() { return { active: this.active, queued: this.queue.length } }

  private definition(cliId: CliId): CliDefinition {
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

export function createCliRunner(options: ConstructorParameters<typeof GovernedCliRunner>[0] = {}): CliRunner {
  return new GovernedCliRunner(options)
}

export const cliRunner = createCliRunner()
