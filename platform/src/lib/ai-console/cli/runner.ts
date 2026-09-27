import 'server-only'
import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process'
import { createHash } from 'node:crypto'
import { lstatSync, mkdtempSync, readFileSync, realpathSync, rmSync, statSync, writeFileSync } from 'node:fs'
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
  readonly realpath: string
  readonly device: string
  readonly inode: string
  readonly size: number
  readonly modifiedMs: number
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

export interface CliRunner {
  inspectInstallation(cliId: CliId): CliInstallationIdentity
  confirmValidation(cliId: CliId, identity: CliInstallationIdentity, version: string): void
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
  private readonly confirmedIdentities = new Map<CliId, { identity: CliInstallationIdentity; version: string }>()

  constructor(options: { registry?: Registry; limits?: Partial<CliRunLimits>; environment?: NodeJS.ProcessEnv } = {}) {
    this.registry = options.registry ?? CLI_REGISTRY
    this.limits = Object.freeze({ ...DEFAULT_LIMITS, ...options.limits })
    this.environment = options.environment ?? process.env
    if (Object.values(this.limits).some(value => !Number.isSafeInteger(value) || value <= 0)) {
      throw new AiConsoleError('AI_EXECUTION_FAILED')
    }
  }

  inspectInstallation(cliId: CliId): CliInstallationIdentity {
    const definition = this.definition(cliId)
    return captureInstallationIdentity(definition)
  }

  confirmValidation(cliId: CliId, identity: CliInstallationIdentity, version: string): void {
    const definition = this.definition(cliId)
    if (!definition.execution || version !== definition.supportedVersion || identity.cliId !== definition.id) {
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    const current = captureInstallationIdentity(definition)
    if (!isDeepStrictEqual(current, identity)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
    this.confirmedIdentities.set(cliId, Object.freeze({ identity: current, version }))
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
    try {
      const handle = await withCliInvocationAuthorization(userId, cliId,
        () => this.start(cliId, args, stdin, signal, schemaJson, purpose === 'execution'), purpose)
      return await handle.completion
    } finally { release() }
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

  private start(cliId: CliId, args: readonly string[], input: string, signal?: AbortSignal,
    schemaJson?: string, requireConfirmedIdentity = false): StartedCliProcess {
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
    if (process.platform === 'win32') throw new AiConsoleError('AI_CLI_UNREACHABLE')
    const definition = this.definition(cliId)
    if (!Array.isArray(args) || args.some(arg => typeof arg !== 'string' || arg.includes('\0'))) {
      throw new AiConsoleError('AI_EXECUTION_FAILED')
    }
    const stdinBytes = Buffer.from(input, 'utf8')
    if (stdinBytes.byteLength > this.limits.stdinBytes) throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
    const cwd = mkdtempSync(resolve(tmpdir(), 'madhav-ai-cli-'))
    let schemaPath: string | undefined
    if (schemaJson !== undefined) {
      if (Buffer.byteLength(schemaJson, 'utf8') > 64 * 1024) {
        rmSync(cwd, { recursive: true, force: true })
        throw new AiConsoleError('AI_CLI_OUTPUT_LIMIT')
      }
      schemaPath = join(cwd, 'output-schema.json')
      writeFileSync(schemaPath, schemaJson, { encoding: 'utf8', mode: 0o600, flag: 'wx' })
    }
    const fixedArgs = args.map(arg => arg === '__CWD__' ? cwd : arg === '__SCHEMA__' && schemaPath ? schemaPath : arg)
    let identity: CliInstallationIdentity
    try {
      // This is the last filesystem work before spawn. Execution is bound to
      // the exact entrypoint/interpreter bytes validated for this process.
      identity = captureInstallationIdentity(definition)
      if (requireConfirmedIdentity) {
        const confirmed = this.confirmedIdentities.get(cliId)
        if (!confirmed || confirmed.version !== definition.supportedVersion
          || !isDeepStrictEqual(confirmed.identity, identity)) throw new AiConsoleError('AI_CLI_UNREACHABLE')
      }
    } catch (error) {
      rmSync(cwd, { recursive: true, force: true })
      throw error
    }
    const executable = identity.interpreter?.realpath ?? identity.entrypoint.realpath
    const processArgs = identity.interpreter ? [identity.entrypoint.realpath, ...fixedArgs] : fixedArgs
    let child: ChildProcessWithoutNullStreams
    try {
      child = spawn(executable, processArgs, {
        shell: false, detached: true, cwd, env: safeEnvironment(this.environment), stdio: ['pipe', 'pipe', 'pipe'],
      })
    } catch {
      rmSync(cwd, { recursive: true, force: true })
      throw new AiConsoleError('AI_CLI_UNREACHABLE')
    }
    if (!child.pid) {
      // Failed async spawn (for example EACCES) still emits `error` next tick.
      child.on('error', () => undefined)
      rmSync(cwd, { recursive: true, force: true })
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
    const cleanup = () => {
      if (lifecycle.timeout) clearTimeout(lifecycle.timeout)
      signal?.removeEventListener('abort', onAbort)
      child.stdout.removeAllListeners(); child.stderr.removeAllListeners()
      child.removeAllListeners('close'); child.removeAllListeners('exit')
      child.removeAllListeners('error'); child.on('error', () => undefined)
      rmSync(cwd, { recursive: true, force: true })
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
        const failure = terminalError
        cleanup()
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
    child.stdin.end(stdinBytes)

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

function captureInstallationIdentity(definition: CliDefinition): CliInstallationIdentity {
  const entrypoint = captureTrustedFile(definition.candidates, definition.allowedRealpathPrefixes)
  const interpreter = definition.interpreter
    ? captureTrustedFile([definition.interpreter.candidate], definition.interpreter.allowedRealpathPrefixes) : undefined
  return Object.freeze({ cliId: definition.id, entrypoint, ...(interpreter ? { interpreter } : {}) })
}

function captureTrustedFile(candidates: readonly string[], allowedRealpathPrefixes: readonly string[]): CliFileIdentity {
  let sawCandidate = false
  for (const candidate of candidates) {
    if (!isAbsolute(candidate)) continue
    try {
      lstatSync(candidate)
      sawCandidate = true
      const real = realpathSync(candidate)
      const prefix = allowedRealpathPrefixes.find(allowed => real.startsWith(allowed))
      if (!prefix) continue
      const stat = statSync(real)
      const uid = typeof process.getuid === 'function' ? process.getuid() : stat.uid
      if (!stat.isFile() || (stat.mode & 0o111) === 0 || (stat.mode & 0o022) !== 0
        || (stat.uid !== 0 && stat.uid !== uid) || !hasTrustedParents(real, prefix, uid)) continue
      return Object.freeze({ realpath: real, device: String(stat.dev), inode: String(stat.ino), size: stat.size,
        modifiedMs: stat.mtimeMs, sha256: createHash('sha256').update(readFileSync(real)).digest('hex') })
    } catch { /* try only the next fixed candidate */ }
  }
  throw new AiConsoleError(sawCandidate ? 'AI_CLI_UNREACHABLE' : 'AI_CLI_NOT_INSTALLED')
}

function hasTrustedParents(real: string, allowedPrefix: string, uid: number): boolean {
  const boundary = resolve(allowedPrefix)
  let current = dirname(real)
  while (true) {
    const stat = statSync(current)
    if (!stat.isDirectory() || (stat.mode & 0o022) !== 0 || (stat.uid !== 0 && stat.uid !== uid)) return false
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
