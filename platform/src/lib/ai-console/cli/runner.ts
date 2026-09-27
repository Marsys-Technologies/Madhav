import 'server-only'
import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process'
import { lstatSync, mkdtempSync, realpathSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { dirname, isAbsolute, join, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { AiConsoleError } from '../errors'
import { withCliInvocationAuthorization, type CliInvocationHandle } from '../repository'
import { CliIdSchema, type CliId } from '../types'
import { buildExecutionArgs, CLI_REGISTRY, type CliDefinition } from './registry'

export interface CliProcessResult {
  readonly stdout: string
  readonly exitCode: number
  readonly signal: NodeJS.Signals | null
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

  constructor(options: { registry?: Registry; limits?: Partial<CliRunLimits>; environment?: NodeJS.ProcessEnv } = {}) {
    this.registry = options.registry ?? CLI_REGISTRY
    this.limits = Object.freeze({ ...DEFAULT_LIMITS, ...options.limits })
    this.environment = options.environment ?? process.env
    if (Object.values(this.limits).some(value => !Number.isSafeInteger(value) || value <= 0)) {
      throw new AiConsoleError('AI_EXECUTION_FAILED')
    }
  }

  runVersionValidation(userId: string, cliId: CliId, signal?: AbortSignal) {
    return this.runFixedAuthorized(userId, cliId, this.definition(cliId).versionArgs, '', signal,
      undefined, 'validation')
  }

  async runAuthValidation(userId: string, cliId: CliId, signal?: AbortSignal) {
    const args = this.definition(cliId).authStatusArgs
    if (!args) throw new AiConsoleError('AI_CLI_AUTH_UNAVAILABLE')
    const result = await this.runFixedAuthorized(userId, cliId, args, '', signal, undefined, 'validation')
    // Auth-status output can contain account identity. Only its safe exit fact
    // crosses the dedicated runner boundary.
    return { ...result, stdout: '' }
  }

  runProbeValidation(userId: string, cliId: CliId, stdin: string, signal?: AbortSignal) {
    const definition = this.definition(cliId)
    return this.runFixedAuthorized(userId, cliId, buildExecutionArgs(definition, null), stdin, signal,
      undefined, 'validation')
  }

  runExecution(userId: string, cliId: CliId, input: { modelId: string | null; stdin: string;
    responseSchema?: unknown; signal?: AbortSignal }) {
    const definition = this.definition(cliId)
    // No approved CLI exposes a machine-readable model catalog. Until one does,
    // the sole catalog entry is the built-in default represented by null.
    if (input.modelId !== null) return Promise.reject(new AiConsoleError('AI_MODEL_UNAVAILABLE'))
    const schemaJson = input.responseSchema === undefined ? undefined : JSON.stringify(input.responseSchema)
    const schemaOption = schemaJson === undefined ? {}
      : definition.id === 'codex' ? { schemaPath: '__SCHEMA__' }
        : definition.id === 'claude_code' ? { schemaPath: schemaJson } : {}
    const args = buildExecutionArgs(definition, input.modelId, schemaOption)
    return this.runFixedAuthorized(userId, cliId, args, input.stdin, input.signal,
      definition.id === 'codex' ? schemaJson : undefined, 'execution')
  }

  private async runFixedAuthorized(userId: string, cliId: CliId, args: readonly string[], stdin: string,
    signal: AbortSignal | undefined, schemaJson: string | undefined,
    purpose: 'execution' | 'validation'): Promise<CliProcessResult> {
    const release = await this.acquire(cliId, signal)
    try {
      const handle = await withCliInvocationAuthorization(userId, cliId,
        () => this.start(cliId, args, stdin, signal, schemaJson), purpose)
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
    schemaJson?: string): StartedCliProcess {
    if (signal?.aborted) throw new AiConsoleError('AI_EXECUTION_FAILED')
    const definition = this.definition(cliId)
    const executable = resolveTrustedExecutable(definition)
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
    const processArgs = args.map(arg => arg === '__CWD__' ? cwd : arg === '__SCHEMA__' && schemaPath ? schemaPath : arg)
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
    let terminalError: AiConsoleError | undefined
    const lifecycle: { killTimer?: NodeJS.Timeout; timeout?: NodeJS.Timeout } = {}
    const stdout: Buffer[] = []
    let stdoutBytes = 0
    let stderrBytes = 0
    let resolveCompletion!: (value: CliProcessResult) => void
    let rejectCompletion!: (error: AiConsoleError) => void
    const cleanup = () => {
      if (lifecycle.timeout) clearTimeout(lifecycle.timeout)
      if (lifecycle.killTimer) clearTimeout(lifecycle.killTimer)
      signal?.removeEventListener('abort', onAbort)
      child.stdout.removeAllListeners(); child.stderr.removeAllListeners()
      child.removeAllListeners('close'); child.removeAllListeners('exit')
      child.removeAllListeners('error'); child.on('error', () => undefined)
      rmSync(cwd, { recursive: true, force: true })
    }
    const killGroup = () => {
      try { process.kill(-child.pid!, 'SIGTERM') } catch { try { child.kill('SIGTERM') } catch { /* already gone */ } }
      lifecycle.killTimer ??= setTimeout(() => {
        try { process.kill(-child.pid!, 'SIGKILL') } catch { try { child.kill('SIGKILL') } catch { /* already gone */ } }
      }, this.limits.killGraceMs)
      lifecycle.killTimer.unref?.()
    }
    const fail = (error: AiConsoleError) => {
      if (settled || terminalError) return
      terminalError = error
      killGroup()
    }
    const onAbort = () => fail(new AiConsoleError('AI_EXECUTION_FAILED'))
    const completion = new Promise<CliProcessResult>((resolvePromise, rejectPromise) => {
      resolveCompletion = resolvePromise; rejectCompletion = rejectPromise
    })
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
      if (settled) return
      settled = true
      const failure = terminalError
      cleanup()
      if (failure) { rejectCompletion(failure); return }
      if (code !== 0) { rejectCompletion(new AiConsoleError('AI_CLI_UNREACHABLE')); return }
      let decoded: string
      try { decoded = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(stdout)) }
      catch { rejectCompletion(new AiConsoleError('AI_EXECUTION_FAILED')); return }
      resolveCompletion({ stdout: decoded, exitCode: code, signal: closeSignal })
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
        if (cancelled || settled) return
        cancelled = true
        fail(new AiConsoleError('AI_EXECUTION_FAILED'))
      },
    })
  }
}

function resolveTrustedExecutable(definition: CliDefinition): string {
  let sawCandidate = false
  for (const candidate of definition.candidates) {
    if (!isAbsolute(candidate)) continue
    try {
      lstatSync(candidate)
      sawCandidate = true
      const real = realpathSync(candidate)
      const prefix = definition.allowedRealpathPrefixes.find(allowed => real.startsWith(allowed))
      if (!prefix) continue
      const stat = statSync(real)
      const uid = typeof process.getuid === 'function' ? process.getuid() : stat.uid
      if (!stat.isFile() || (stat.mode & 0o111) === 0 || (stat.mode & 0o022) !== 0
        || (stat.uid !== 0 && stat.uid !== uid) || !hasTrustedParents(real, prefix, uid)) continue
      return real
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
