import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'

export type AcceptanceStatus = 'PASS' | 'FAIL' | 'UNQUALIFIED'
export type AcceptanceCommandKind = 'command' | 'test'

export interface AcceptanceEnvironment { readonly [name: string]: string | undefined }

export interface AcceptanceCommand {
  readonly id: string
  readonly command: string
  readonly args: readonly string[]
  readonly kind: AcceptanceCommandKind
  readonly prerequisite?: (env: AcceptanceEnvironment) => string | null
}

export interface AcceptanceCommandResult {
  readonly exitCode: number
  readonly executedCount?: number
  readonly skippedCount?: number
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
const PROVIDERS = ['openai', 'anthropic', 'gemini', 'xai', 'deepseek', 'kimi', 'openrouter'] as const
const CLIS = ['codex', 'claude_code', 'gemini_antigravity', 'kimi_code'] as const

function browserPrerequisite(env: AcceptanceEnvironment): string | null {
  return env.MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
    && env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
    && Boolean(env.SMOKE_SESSION_COOKIE?.trim())
    && Boolean(env.AI_CONSOLE_E2E_OWNER_CONFIG_PATH?.trim())
    && isAbsolute(env.AI_CONSOLE_E2E_OWNER_CONFIG_PATH ?? '')
    ? null : 'AIC_ACCEPTANCE_BROWSER_PREREQUISITE_MISSING'
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
  if (env.RUN_DB_TESTS !== '1' || !env.DATABASE_URL) return 'AIC_ACCEPTANCE_DB_PREREQUISITE_MISSING'
  try {
    const target = new URL(env.DATABASE_URL)
    const local = target.hostname === 'localhost' || target.hostname === '127.0.0.1' || target.hostname === '::1'
    const database = target.pathname.slice(1)
    return local && database.startsWith('ai_console_test_') ? null : 'AIC_ACCEPTANCE_DB_NOT_DISPOSABLE_LOCAL'
  } catch { return 'AIC_ACCEPTANCE_DB_NOT_DISPOSABLE_LOCAL' }
}

function e2e(id: string, tag: string, prerequisite = browserPrerequisite): AcceptanceCommand {
  return {
    id, kind: 'test', prerequisite, command: 'npx',
    args: ['playwright', 'test', '--config=tests/e2e/ai-console/playwright.config.ts', '--project=chromium', '--grep', tag],
  }
}

function commands(): AcceptanceCommand[] {
  return [
    { id: 'migration_guard', kind: 'command', command: 'npm', args: ['run', 'guard:migration-numbers'] },
    { id: 'typecheck', kind: 'command', command: 'npx', args: ['tsc', '--noEmit'] },
    { id: 'eslint', kind: 'command', command: 'npm', args: ['run', 'lint', '--', 'scripts/ai-console', 'src/lib/ai-console', 'src/app/api/ai-console', 'src/components/ai-console', 'src/components/pariprashna', 'tests/e2e/ai-console'] },
    { id: 'focused_tests', kind: 'test', command: 'npx', args: ['vitest', 'run', 'src/lib/ai-console', 'src/app/api/ai-console', 'src/app/api/pariprashna', 'src/app/api/chat/consult', 'src/app/api/mcp/prashna_ask'] },
    { id: 'disposable_database', kind: 'test', prerequisite: databasePrerequisite, command: 'npx', args: ['vitest', 'run', 'src/lib/ai-console/__tests__/migration_db.test.ts', 'src/lib/ai-console/__tests__/repository_isolation.db.test.ts'] },
    { id: 'pariprashna_desktop_gates', kind: 'test', command: 'npm', args: ['run', 'pariprashna:gates'] },
    { id: 'pariprashna_mobile_gates', kind: 'test', command: 'npm', args: ['run', 'pariprashna:gates:mobile'] },
    e2e('authenticated_desktop', '@desktop'),
    e2e('authenticated_mobile', '@mobile'),
    e2e('direct_custom_default_pinning', '@routing'),
    e2e('backend_default', '@backend'),
    e2e('mcp_evidence_only', '@mcp'),
    ...PROVIDERS.map(provider => e2e(`provider_${provider}`, `@provider-${provider}`, providerPrerequisite)),
    ...CLIS.map(cli => e2e(`cli_${cli}`, `@cli-${cli.replaceAll('_', '-')}`, cliPrerequisite)),
    e2e('leakage_inspection', '@leakage'),
    { id: 'route_graph_clean', kind: 'command', command: 'npm', args: ['run', 'ai-console:audit-shared-keys'] },
    { id: 'build', kind: 'command', command: 'npm', args: ['run', 'build'] },
  ]
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
  for (const command of commands()) {
    const missing = command.prerequisite?.(options.env) ?? null
    if (missing) {
      dimensions.push({ id: command.id, label: LABELS[command.id] ?? command.id, status: 'UNQUALIFIED', code: missing,
        commandKind: command.kind, exitCode: null, executedCount: null, skippedCount: null })
      continue
    }
    const result = await options.execute(command)
    const testUnqualified = command.kind === 'test' && (result.executedCount ?? 0) === 0
    dimensions.push({
      id: command.id,
      label: LABELS[command.id] ?? (command.id.startsWith('provider_') ? `Provider ${command.id.slice(9)}` : command.id.startsWith('cli_') ? `CLI ${command.id.slice(4)}` : command.id),
      status: result.exitCode !== 0 ? 'FAIL' : testUnqualified ? 'UNQUALIFIED' : 'PASS',
      code: result.exitCode !== 0 ? 'AIC_ACCEPTANCE_COMMAND_FAILED' : testUnqualified ? 'AIC_ACCEPTANCE_ZERO_EXECUTED' : 'AIC_ACCEPTANCE_PASSED',
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

async function execute(command: AcceptanceCommand): Promise<AcceptanceCommandResult> {
  return new Promise(resolveResult => {
    const child = spawn(command.command, command.args, { cwd: PLATFORM_ROOT, env: process.env, shell: false, stdio: ['ignore', 'pipe', 'pipe'] })
    let output = ''
    let overflow = false
    const append = (chunk: Buffer) => {
      if (overflow) return
      output += chunk.toString('utf8')
      if (Buffer.byteLength(output, 'utf8') > 2_000_000) {
        overflow = true
        output = ''
        child.kill('SIGTERM')
      }
    }
    child.stdout.on('data', append)
    child.stderr.on('data', append)
    child.once('error', () => resolveResult({ exitCode: 1 }))
    child.once('close', code => {
      if (overflow) return resolveResult({ exitCode: 1 })
      const counts = command.kind === 'test' ? parseTestCounts(output) : {}
      resolveResult({ exitCode: code ?? 1, ...counts })
    })
  })
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
  const report = await runLocalAcceptance({ env: process.env, revision: await revision(), execute })
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
