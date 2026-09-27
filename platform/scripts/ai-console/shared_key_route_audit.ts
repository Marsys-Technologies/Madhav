import { readFile, stat } from 'node:fs/promises'
import { dirname, extname, isAbsolute, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

export interface ImportAuditRule {
  readonly ruleId: string
  readonly paths?: readonly string[]
  readonly sourcePatterns?: readonly RegExp[]
}

export interface ImportAuditConfig {
  readonly platformRoot: string
  readonly roots: readonly string[]
  readonly forbidden: readonly ImportAuditRule[]
}

export interface ImportAuditFinding {
  readonly ruleId: string
  readonly chain: readonly string[]
}

export interface ImportAuditResult {
  readonly violations: readonly ImportAuditFinding[]
  readonly scannerErrors: readonly ImportAuditFinding[]
  readonly visitedFiles: number
}

const SCRIPT_EXTENSIONS = new Set(['.ts', '.tsx', '.mts', '.cts', '.js', '.jsx', '.mjs', '.cjs'])
const RESOLUTION_EXTENSIONS = ['.ts', '.tsx', '.mts', '.cts', '.js', '.jsx', '.mjs', '.cjs', '.json', '.css'] as const

const DEFAULT_ROOTS = [
  'src/app/api/pariprashna/route.ts',
  'src/app/api/chat/consult/route.ts',
  'src/app/api/chat/consult/continue/route.ts',
  'src/app/api/mcp/prashna_ask/route.ts',
  'src/app/api/ai-console/connections/route.ts',
  'src/app/api/ai-console/connections/[id]/validate/route.ts',
  'src/app/api/admin/cron/revalidate-ai-connections/route.ts',
] as const

const SHARED_PROVIDER_ENV = /process\s*\.\s*env\s*(?:\.\s*(?:OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_GENERATIVE_AI_API_KEY|DEEPSEEK_API_KEY|XAI_API_KEY|KIMI_API_KEY|MOONSHOT_API_KEY|OPENROUTER_API_KEY)|\[\s*['"](?:OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_GENERATIVE_AI_API_KEY|DEEPSEEK_API_KEY|XAI_API_KEY|KIMI_API_KEY|MOONSHOT_API_KEY|OPENROUTER_API_KEY)['"]\s*\])/

export function defaultImportAuditConfig(platformRoot: string): ImportAuditConfig {
  return {
    platformRoot,
    roots: DEFAULT_ROOTS,
    forbidden: [
      { ruleId: 'AIC_SHARED_PROVIDER_ENV', sourcePatterns: [SHARED_PROVIDER_ENV] },
      {
        ruleId: 'AIC_LEGACY_MODEL_AUTHORITY',
        paths: [
          'src/lib/models/registry.ts',
          'src/lib/models/resolver.ts',
          'src/lib/models/runtime_config.ts',
        ],
      },
      {
        ruleId: 'AIC_LEGACY_DISPATCH_AUTHORITY',
        paths: [
          'src/lib/pipelines/shared/run_adapter_dispatch.ts',
        ],
      },
    ],
  }
}

function normalizedRelative(platformRoot: string, path: string): string | null {
  const value = relative(platformRoot, path).split(sep).join('/')
  return value === '' || value === '..' || value.startsWith('../') || isAbsolute(value) ? null : value
}

async function isFile(path: string): Promise<boolean> {
  try { return (await stat(path)).isFile() } catch { return false }
}

async function resolveInternalImport(platformRoot: string, importer: string, specifier: string): Promise<string | null> {
  const requested = specifier.startsWith('@/')
    ? resolve(platformRoot, 'src', specifier.slice(2))
    : resolve(dirname(importer), specifier)
  if (!normalizedRelative(platformRoot, requested)) return null

  const candidates = new Set<string>([requested])
  const extension = extname(requested)
  if (extension) {
    const withoutExtension = requested.slice(0, -extension.length)
    for (const candidateExtension of RESOLUTION_EXTENSIONS) candidates.add(`${withoutExtension}${candidateExtension}`)
  } else {
    for (const candidateExtension of RESOLUTION_EXTENSIONS) candidates.add(`${requested}${candidateExtension}`)
    for (const candidateExtension of RESOLUTION_EXTENSIONS) candidates.add(resolve(requested, `index${candidateExtension}`))
  }
  for (const candidate of candidates) if (await isFile(candidate)) return candidate
  return null
}

function internalSpecifiers(source: string, path: string): string[] {
  const sourceFile = ts.createSourceFile(path, source, ts.ScriptTarget.Latest, true)
  const values = new Set<string>()
  const add = (node: ts.Expression | undefined) => {
    if (node && ts.isStringLiteralLike(node) && (node.text.startsWith('.') || node.text.startsWith('@/'))) {
      values.add(node.text)
    }
  }
  const visit = (node: ts.Node) => {
    if (ts.isImportDeclaration(node)) add(node.moduleSpecifier)
    if (ts.isExportDeclaration(node)) add(node.moduleSpecifier)
    if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) add(node.arguments[0])
    ts.forEachChild(node, visit)
  }
  visit(sourceFile)
  return [...values].sort()
}

function findingKey(finding: ImportAuditFinding): string {
  return `${finding.ruleId}\0${finding.chain.join('\0')}`
}

export async function auditImportGraph(config: ImportAuditConfig): Promise<ImportAuditResult> {
  const platformRoot = resolve(config.platformRoot)
  const violations = new Map<string, ImportAuditFinding>()
  const scannerErrors = new Map<string, ImportAuditFinding>()
  const visitedGlobally = new Set<string>()

  for (const configuredRoot of config.roots) {
    const root = resolve(platformRoot, configuredRoot)
    const rootRelative = normalizedRelative(platformRoot, root) ?? configuredRoot.split(sep).join('/')
    if (!await isFile(root)) {
      const finding = { ruleId: 'AIC_IMPORT_ROOT_MISSING', chain: [rootRelative] }
      scannerErrors.set(findingKey(finding), finding)
      continue
    }

    const queue: Array<{ path: string; chain: string[] }> = [{ path: root, chain: [rootRelative] }]
    const reached = new Set<string>()
    while (queue.length > 0) {
      const current = queue.shift()!
      if (reached.has(current.path)) continue
      reached.add(current.path)
      visitedGlobally.add(current.path)
      const currentRelative = normalizedRelative(platformRoot, current.path)
      if (!currentRelative) {
        const finding = { ruleId: 'AIC_IMPORT_OUTSIDE_PLATFORM', chain: current.chain }
        scannerErrors.set(findingKey(finding), finding)
        continue
      }

      let source: string
      try { source = await readFile(current.path, 'utf8') } catch {
        const finding = { ruleId: 'AIC_IMPORT_READ_FAILED', chain: current.chain }
        scannerErrors.set(findingKey(finding), finding)
        continue
      }

      for (const rule of config.forbidden) {
        const pathMatch = rule.paths?.includes(currentRelative) === true
        const sourceMatch = rule.sourcePatterns?.some(pattern => {
          pattern.lastIndex = 0
          return pattern.test(source)
        }) === true
        if (pathMatch || sourceMatch) {
          const finding = { ruleId: rule.ruleId, chain: current.chain }
          violations.set(findingKey(finding), finding)
        }
      }

      if (!SCRIPT_EXTENSIONS.has(extname(current.path))) continue
      for (const specifier of internalSpecifiers(source, current.path)) {
        const resolved = await resolveInternalImport(platformRoot, current.path, specifier)
        if (!resolved) {
          const unresolved = specifier.startsWith('@/')
            ? `src/${specifier.slice(2)}`
            : normalizedRelative(platformRoot, resolve(dirname(current.path), specifier)) ?? 'outside-platform'
          const finding = { ruleId: 'AIC_IMPORT_UNRESOLVED', chain: [...current.chain, unresolved] }
          scannerErrors.set(findingKey(finding), finding)
          continue
        }
        const nextRelative = normalizedRelative(platformRoot, resolved)
        if (!nextRelative) {
          const finding = { ruleId: 'AIC_IMPORT_OUTSIDE_PLATFORM', chain: [...current.chain, 'outside-platform'] }
          scannerErrors.set(findingKey(finding), finding)
          continue
        }
        if (!reached.has(resolved)) queue.push({ path: resolved, chain: [...current.chain, nextRelative] })
      }
    }
  }

  const byFinding = (left: ImportAuditFinding, right: ImportAuditFinding) =>
    left.ruleId.localeCompare(right.ruleId) || left.chain.join('\0').localeCompare(right.chain.join('\0'))
  return {
    violations: [...violations.values()].sort(byFinding),
    scannerErrors: [...scannerErrors.values()].sort(byFinding),
    visitedFiles: visitedGlobally.size,
  }
}

function safeLine(finding: ImportAuditFinding): string {
  return `${finding.ruleId} ${finding.chain.join(' -> ')}`
}

export async function main(argv = process.argv.slice(2)): Promise<void> {
  if (argv.length > 0) throw new Error('AIC_AUDIT_ARGUMENTS_FORBIDDEN')
  const platformRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
  const result = await auditImportGraph(defaultImportAuditConfig(platformRoot))
  for (const finding of [...result.scannerErrors, ...result.violations]) process.stdout.write(`${safeLine(finding)}\n`)
  if (result.scannerErrors.length === 0 && result.violations.length === 0) {
    process.stdout.write('AIC_ROUTE_GRAPH_CLEAN\n')
  } else {
    process.exitCode = 1
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(() => {
    process.stderr.write('AIC_ROUTE_GRAPH_SCANNER_FAILED\n')
    process.exitCode = 1
  })
}
