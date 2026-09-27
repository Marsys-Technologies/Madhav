import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawn, type ChildProcess } from 'node:child_process'
import { preflightOwnerFixture } from './owner_preflight'
import { assertDisposableAiConsoleDatabaseUrl } from './test_database_guard'

export type AcceptanceStatus = 'PASS' | 'FAIL' | 'UNQUALIFIED'
export type AcceptanceCommandKind = 'command' | 'test'

export interface AcceptanceEnvironment { readonly [name: string]: string | undefined }

export interface AcceptanceCommand {
  readonly id: string
  readonly command: string
  readonly args: readonly string[]
  readonly kind: AcceptanceCommandKind
  readonly timeoutMs: number
  readonly environment: 'base' | 'database' | 'browser' | 'build'
  readonly prerequisite?: (env: AcceptanceEnvironment) => string | null
}

export interface AcceptanceCommandResult {
  readonly exitCode: number
  readonly executedCount?: number
  readonly skippedCount?: number
  readonly timedOut?: boolean
}

export interface AcceptanceDimension {
  readonly id: string
  readonly label: string
  readonly status: AcceptanceStatus
  readonly code: string
  readonly commandKind: AcceptanceCommandKind
  readonly exitCode: number | null
  readonly executedCount: number | null
  readonly skippedCount: number | null
}

export interface LocalAcceptanceReport {
  readonly schemaVersion: 'madhav.ai-console.local-acceptance.v1'
  readonly createdAt: string
  readonly revision: string
  readonly dimensions: readonly AcceptanceDimension[]
  readonly summary: { readonly pass: number; readonly fail: number; readonly unqualified: number }
}

export interface LocalAcceptanceOptions {
  readonly env: AcceptanceEnvironment
  readonly revision: string
  readonly execute: (command: AcceptanceCommand) => Promise<AcceptanceCommandResult>
  readonly now?: () => Date
}

const PLATFORM_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
const LOCAL_BIN = (name: string) => resolve(PLATFORM_ROOT, 'node_modules/.bin', name)
const DEFAULT_TIMEOUT_MS = 300_000
const PROVIDERS = ['openai', 'anthropic', 'gemini', 'xai', 'deepseek', 'kimi', 'openrouter'] as const
const CLIS = ['codex', 'claude_code', 'gemini_antigravity', 'kimi_code'] as const

function browserPrerequisite(env: AcceptanceEnvironment): string | null {
  return env.MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
    && env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
    && Boolean(env.SMOKE_SESSION_COOKIE?.trim())
    && Boolean(env.AI_CONSOLE_E2E_OWNER_CONFIG_PATH?.trim())
    && isAbsolute(env.AI_CONSOLE_E2E_OWNER_CONFIG_PATH ?? '')
    && env.AI_CONSOLE_E2E_EXTERNAL_SERVER === 'true'
    && Boolean(env.AI_CONSOLE_E2E_ARTIFACT_DIR)
    && env.__AIC_OWNER_FIXTURE_VALIDATED === 'true'
    ? null : env.__AIC_OWNER_FIXTURE_CODE ?? 'AIC_ACCEPTANCE_BROWSER_PREREQUISITE_MISSING'
}

function providerPrerequisite(env: AcceptanceEnvironment): string | null {
  return browserPrerequisite(env) ?? (env.AI_CONSOLE_PROVIDER_SMOKE_AUTHORIZED === 'true'
    ? null : 'AIC_ACCEPTANCE_PROVIDER_AUTHORIZATION_MISSING')
}

function cliPrerequisite(env: AcceptanceEnvironment): string | null {
  return browserPrerequisite(env) ?? (env.AI_CONSOLE_CLI_SMOKE_AUTHORIZED === 'true'
    ? null : 'AIC_ACCEPTANCE_CLI_AUTHORIZATION_MISSING')
}

function databasePrerequisite(env: AcceptanceEnvironment): string | null {
  if (env.RUN_DB_TESTS !== '1' || !env.AI_CONSOLE_TEST_DATABASE_URL) return 'AIC_ACCEPTANCE_DB_PREREQUISITE_MISSING'
  try { assertDisposableAiConsoleDatabaseUrl(env.AI_CONSOLE_TEST_DATABASE_URL); return null }
  catch { return 'AIC_ACCEPTANCE_DB_NOT_DISPOSABLE_LOCAL' }
}

function e2e(id: string, tag: string, prerequisite = browserPrerequisite): AcceptanceCommand {
  return {
    id, kind: 'test', prerequisite, command: LOCAL_BIN('playwright'), timeoutMs: DEFAULT_TIMEOUT_MS,
    environment: 'browser',
    args: ['test', '--config=tests/e2e/ai-console/playwright.config.ts', '--project=chromium', '--grep', tag],
  }
}

export function acceptanceCommands(): AcceptanceCommand[] {
  return [
    { id: 'migration_guard', kind: 'command', command: 'npm', args: ['run', 'guard:migration-numbers'], timeoutMs: DEFAULT_TIMEOUT_MS, environment: 'base' },
    { id: 'typecheck', kind: 'command', command: LOCAL_BIN('tsc'), args: ['--noEmit'], timeoutMs: DEFAULT_TIMEOUT_MS, environment: 'base' },
    { id: 'eslint', kind: 'command', command: LOCAL_BIN('eslint'), args: ['--max-warnings=0', 'scripts/ai-console', 'src/lib/ai-console', 'src/app/api/ai-console', 'src/components/ai-console', 'src/components/pariprashna', 'tests/e2e/ai-console'], timeoutMs: DEFAULT_TIMEOUT_MS, environment: 'base' },
    { id: 'focused_tests', kind: 'test', command: LOCAL_BIN('vitest'), args: ['run', 'src/lib/ai-console', 'src/app/api/ai-console', 'src/app/api/pariprashna', 'src/app/api/chat/consult', 'src/app/api/mcp/prashna_ask'], timeoutMs: DEFAULT_TIMEOUT_MS, environment: 'base' },
    { id: 'disposable_database', kind: 'test', prerequisite: databasePrerequisite, command: LOCAL_BIN('vitest'), args: ['run', 'src/lib/ai-console/__tests__/migration_db.test.ts', 'src/lib/ai-console/__tests__/repository_isolation.db.test.ts'], timeoutMs: DEFAULT_TIMEOUT_MS, environment: 'database' },
    { id: 'pariprashna_desktop_gates', kind: 'test', command: 'npm', args: ['run', 'pariprashna:gates'], timeoutMs: DEFAULT_TIMEOUT_MS, environment: 'base' },
    { id: 'pariprashna_mobile_gates', kind: 'test', command: 'npm', args: ['run', 'pariprashna:gates:mobile'], timeoutMs: DEFAULT_TIMEOUT_MS, environment: 'base' },
    e2e('authenticated_desktop', '@desktop'),
    e2e('authenticated_mobile', '@mobile'),
    e2e('direct_custom_default_pinning', '@routing'),
    e2e('backend_default', '@backend'),
    e2e('mcp_evidence_only', '@mcp'),
    ...PROVIDERS.map(provider => e2e(`provider_${provider}`, `@provider-${provider}`, providerPrerequisite)),
    ...CLIS.map(cli => e2e(`cli_${cli}`, `@cli-${cli.replaceAll('_', '-')}`, cliPrerequisite)),
    e2e('leakage_inspection', '@leakage'),
    { id: 'route_graph_clean', kind: 'command', command: LOCAL_BIN('tsx'), args: ['scripts/ai-console/shared_key_route_audit.ts'], timeoutMs: DEFAULT_TIMEOUT_MS, environment: 'base' },
    { id: 'build', kind: 'command', command: LOCAL_BIN('next'), args: ['build', '--webpack'], timeoutMs: 600_000, environment: 'build' },
  ]
}

const BASE_ENVIRONMENT = ['PATH', 'HOME', 'TMPDIR', 'CI'] as const
const BROWSER_ENVIRONMENT = ['MARSYS_FLAG_AI_CONSOLE_BYOK', 'NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK',
  'SMOKE_SESSION_COOKIE', 'AI_CONSOLE_E2E_OWNER_CONFIG_PATH', 'AI_CONSOLE_E2E_BASE_URL',
  'AI_CONSOLE_E2E_EXTERNAL_SERVER', 'AI_CONSOLE_E2E_ARTIFACT_DIR',
  'AI_CONSOLE_PROVIDER_SMOKE_AUTHORIZED', 'AI_CONSOLE_CLI_SMOKE_AUTHORIZED'] as const
const BUILD_ENVIRONMENT = ['NEXT_PUBLIC_FIREBASE_API_KEY', 'NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN',
  'NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET', 'NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID',
  'NEXT_PUBLIC_FIREBASE_APP_ID', 'NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID'] as const

export function environmentForCommand(command: AcceptanceCommand, source: AcceptanceEnvironment): Record<string, string> {
  const keys = [...BASE_ENVIRONMENT,
    ...(command.environment === 'browser' ? BROWSER_ENVIRONMENT : []),
    ...(command.environment === 'database' ? ['AI_CONSOLE_TEST_DATABASE_URL'] as const : []),
    ...(command.environment === 'build' ? BUILD_ENVIRONMENT : [])]
  const environment: Record<string, string> = {}
  for (const key of keys) if (source[key] !== undefined) environment[key] = source[key]!
  if (command.environment === 'database') environment.RUN_DB_TESTS = '1'
  return environment
}

const LABELS: Record<string, string> = {
  migration_guard: 'Migration number guard', typecheck: 'TypeScript', eslint: 'Scoped ESLint',
  focused_tests: 'Focused AI Console and route tests', disposable_database: 'Disposable database behavior',
  pariprashna_desktop_gates: 'Pariprashna desktop gates', pariprashna_mobile_gates: 'Pariprashna mobile gates',
  authenticated_desktop: 'Authenticated desktop browser flow', authenticated_mobile: 'Authenticated mobile browser flow',
  direct_custom_default_pinning: 'Direct, custom, Default, and pinning flow', backend_default: 'Logged-in backend default',
  mcp_evidence_only: 'MCP evidence-only flow', leakage_inspection: 'Leakage inspection',
  route_graph_clean: 'Shared-key route graph clean', build: 'Production build',
}

export function parseTestCounts(output: string): { executedCount: number; skippedCount: number } {
  const plain = output.replace(/\u001b\[[0-9;]*m/g, '')
  const vitest = plain.match(/(?:^|\n)\s*Tests\s+(?:(\d+)\s+passed)?(?:\s*\|\s*)?(?:(\d+)\s+skipped)?/)
  if (vitest) return { executedCount: Number(vitest[1] ?? 0), skippedCount: Number(vitest[2] ?? 0) }
  const passed = [...plain.matchAll(/(?:^|\n)\s*(\d+)\s+passed\b/gi)].at(-1)
  const skipped = [...plain.matchAll(/(?:^|\n)\s*(\d+)\s+skipped\b/gi)].at(-1)
  return { executedCount: Number(passed?.[1] ?? 0), skippedCount: Number(skipped?.[1] ?? 0) }
}

export async function runLocalAcceptance(options: LocalAcceptanceOptions): Promise<LocalAcceptanceReport> {
  const dimensions: AcceptanceDimension[] = []
  for (const command of acceptanceCommands()) {
    const missing = command.prerequisite?.(options.env) ?? null
    if (missing) {
      dimensions.push({ id: command.id, label: LABELS[command.id] ?? command.id, status: 'UNQUALIFIED', code: missing,
        commandKind: command.kind, exitCode: null, executedCount: null, skippedCount: null })
      continue
    }
    const result = await options.execute(command)
    const testUnqualified = command.kind === 'test' && (result.executedCount ?? 0) === 0
    const failedCode = result.timedOut ? 'AIC_ACCEPTANCE_COMMAND_TIMEOUT' : 'AIC_ACCEPTANCE_COMMAND_FAILED'
    dimensions.push({
      id: command.id,
      label: LABELS[command.id] ?? (command.id.startsWith('provider_') ? `Provider ${command.id.slice(9)}` : command.id.startsWith('cli_') ? `CLI ${command.id.slice(4)}` : command.id),
      status: result.exitCode !== 0 ? 'FAIL' : testUnqualified ? 'UNQUALIFIED' : 'PASS',
      code: result.exitCode !== 0 ? failedCode : testUnqualified ? 'AIC_ACCEPTANCE_ZERO_EXECUTED' : 'AIC_ACCEPTANCE_PASSED',
      commandKind: command.kind,
      exitCode: result.exitCode,
      executedCount: command.kind === 'test' ? result.executedCount ?? 0 : null,
      skippedCount: command.kind === 'test' ? result.skippedCount ?? 0 : null,
    })
  }
  return {
    schemaVersion: 'madhav.ai-console.local-acceptance.v1',
    createdAt: (options.now?.() ?? new Date()).toISOString(),
    revision: options.revision,
    dimensions,
    summary: {
      pass: dimensions.filter(row => row.status === 'PASS').length,
      fail: dimensions.filter(row => row.status === 'FAIL').length,
      unqualified: dimensions.filter(row => row.status === 'UNQUALIFIED').length,
    },
  }
}

export function acceptanceExitCode(report: LocalAcceptanceReport): 0 | 1 | 2 {
  if (report.summary.fail > 0) return 1
  return report.summary.unqualified > 0 ? 2 : 0
}

function terminateProcessGroup(child: ChildProcess, signal: NodeJS.Signals): void {
  try {
    if (child.pid && process.platform !== 'win32') process.kill(-child.pid, signal)
    else child.kill(signal)
  } catch { child.kill(signal) }
}

export async function executeAcceptanceCommand(
  command: AcceptanceCommand,
  sourceEnvironment: AcceptanceEnvironment,
): Promise<AcceptanceCommandResult> {
  return new Promise(resolveResult => {
    const child: ChildProcess = spawn(command.command, command.args, { cwd: PLATFORM_ROOT,
      env: environmentForCommand(command, sourceEnvironment) as NodeJS.ProcessEnv, shell: false,
      detached: process.platform !== 'win32', stdio: ['ignore', 'pipe', 'pipe'] })
    let output = ''
    let overflow = false
    let settled = false
    let timedOut = false
    let forceTimer: ReturnType<typeof setTimeout> | undefined
    let boundedCloseTimer: ReturnType<typeof setTimeout> | undefined
    const finish = (result: AcceptanceCommandResult) => {
      if (settled) return
      settled = true
      if (deadlineTimer) clearTimeout(deadlineTimer)
      if (forceTimer) clearTimeout(forceTimer)
      if (boundedCloseTimer) clearTimeout(boundedCloseTimer)
      resolveResult(result)
    }
    const append = (chunk: Buffer) => {
      if (overflow) return
      output += chunk.toString('utf8')
      if (Buffer.byteLength(output, 'utf8') > 2_000_000) {
        overflow = true
        output = ''
        terminateProcessGroup(child, 'SIGTERM')
      }
    }
    child.stdout?.on('data', append)
    child.stderr?.on('data', append)
    const deadlineTimer: ReturnType<typeof setTimeout> = setTimeout(() => {
      timedOut = true
      output = ''
      terminateProcessGroup(child, 'SIGTERM')
      forceTimer = setTimeout(() => terminateProcessGroup(child, 'SIGKILL'), 1_000)
      boundedCloseTimer = setTimeout(() => finish({ exitCode: 124, timedOut: true }), 3_000)
    }, command.timeoutMs)
    child.once('error', () => finish({ exitCode: timedOut ? 124 : 1, timedOut }))
    child.once('close', (code: number | null) => {
      if (timedOut) return finish({ exitCode: 124, timedOut: true })
      if (overflow) return finish({ exitCode: 1 })
      const counts = command.kind === 'test' ? parseTestCounts(output) : {}
      finish({ exitCode: code ?? 1, ...counts })
    })
  })
}

export async function prepareAcceptanceEnvironment(source: AcceptanceEnvironment): Promise<AcceptanceEnvironment> {
  const prepared: Record<string, string | undefined> = { ...source }
  const path = source.AI_CONSOLE_E2E_OWNER_CONFIG_PATH
  if (!path) return prepared
  const result = await preflightOwnerFixture(path, { platformRoot: PLATFORM_ROOT,
    baseUrl: source.AI_CONSOLE_E2E_BASE_URL ?? 'http://localhost:3000' })
  if (result.ok) {
    prepared.__AIC_OWNER_FIXTURE_VALIDATED = 'true'
    prepared.AI_CONSOLE_E2E_ARTIFACT_DIR = result.config.leakage.artifactDirectory
  }
  else prepared.__AIC_OWNER_FIXTURE_CODE = result.code
  return prepared
}

function safeReportPath(createdAt: string): string | null {
  if (process.env.AI_CONSOLE_ACCEPTANCE_JSON !== 'true') return null
  const directory = resolve(PLATFORM_ROOT, 'verification/ai-console')
  const normalized = relative(PLATFORM_ROOT, directory).split(sep).join('/')
  if (normalized !== 'verification/ai-console') throw new Error('AIC_ACCEPTANCE_REPORT_PATH_REJECTED')
  return resolve(directory, `acceptance-${createdAt.replace(/[:.]/g, '-')}.json`)
}

async function revision(): Promise<string> {
  return new Promise(resolveRevision => {
    const child = spawn('git', ['rev-parse', 'HEAD'], { cwd: PLATFORM_ROOT, shell: false, stdio: ['ignore', 'pipe', 'ignore'] })
    let value = ''
    child.stdout.on('data', chunk => { if (value.length < 80) value += String(chunk) })
    child.once('error', () => resolveRevision('UNKNOWN'))
    child.once('close', code => resolveRevision(code === 0 && /^[0-9a-f]{40}\s*$/.test(value) ? value.trim() : 'UNKNOWN'))
  })
}

export async function main(argv = process.argv.slice(2)): Promise<void> {
  if (argv.length > 0) throw new Error('AIC_ACCEPTANCE_ARGUMENTS_FORBIDDEN')
  const env = await prepareAcceptanceEnvironment(process.env)
  const report = await runLocalAcceptance({ env, revision: await revision(),
    execute: command => executeAcceptanceCommand(command, env) })
  process.stdout.write(`AI Console local acceptance ${report.createdAt} ${report.revision}\n`)
  for (const row of report.dimensions) {
    const counts = row.commandKind === 'test' ? ` executed=${row.executedCount ?? 0} skipped=${row.skippedCount ?? 0}` : ''
    process.stdout.write(`${row.status} ${row.id} ${row.code}${counts}\n`)
  }
  process.stdout.write(`SUMMARY pass=${report.summary.pass} fail=${report.summary.fail} unqualified=${report.summary.unqualified}\n`)
  const reportPath = safeReportPath(report.createdAt)
  if (reportPath) {
    await mkdir(dirname(reportPath), { recursive: true })
    await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' })
    process.stdout.write(`REPORT verification/ai-console/${reportPath.split(sep).at(-1)}\n`)
  }
  process.exitCode = acceptanceExitCode(report)
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    const code = error instanceof Error && /^AIC_[A-Z0-9_]+$/.test(error.message) ? error.message : 'AIC_ACCEPTANCE_RUNNER_FAILED'
    process.stderr.write(`${code}\n`)
    process.exitCode = 1
  })
}
