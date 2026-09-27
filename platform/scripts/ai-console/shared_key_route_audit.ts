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
  'src/app/api/ai-console/connections/[id]/route.ts',
  'src/app/api/ai-console/connections/[id]/validate/route.ts',
  'src/app/api/admin/cron/revalidate-ai-connections/route.ts',
] as const

const LEGACY_PROVIDER_AUTHORITIES = [
  { envKeys: ['OPENAI_API_KEY'], paths: ['src/lib/providers/openai/adapter.ts', 'src/lib/adapters/providers/adapter_openai.ts', 'src/lib/models/openai.ts'] },
  { envKeys: ['ANTHROPIC_API_KEY'], paths: ['src/lib/providers/anthropic/adapter.ts', 'src/lib/adapters/providers/adapter_anthropic.ts'] },
  { envKeys: ['GOOGLE_GENERATIVE_AI_API_KEY'], paths: ['src/lib/providers/google/adapter.ts', 'src/lib/adapters/providers/adapter_gemini.ts'] },
  { envKeys: ['DEEPSEEK_API_KEY'], paths: ['src/lib/providers/deepseek/adapter.ts', 'src/lib/adapters/providers/adapter_deepseek.ts'] },
  { envKeys: ['NVIDIA_NIM_API_KEY'], paths: ['src/lib/providers/nvidia/adapter.ts', 'src/lib/adapters/providers/adapter_nim.ts', 'src/lib/models/nvidia.ts', 'src/lib/llm/providers/nim_observed.ts'] },
  { envKeys: ['XAI_API_KEY'], paths: [] },
  { envKeys: ['KIMI_API_KEY', 'MOONSHOT_API_KEY'], paths: [] },
  { envKeys: ['OPENROUTER_API_KEY'], paths: [] },
] as const
const PROVIDER_ENV_KEYS: ReadonlySet<string> = new Set(LEGACY_PROVIDER_AUTHORITIES.flatMap(entry => [...entry.envKeys]))
const LEGACY_PROVIDER_SINKS = [...new Set(LEGACY_PROVIDER_AUTHORITIES.flatMap(entry => [...entry.paths]))]

export function defaultImportAuditConfig(platformRoot: string): ImportAuditConfig {
  return {
    platformRoot,
    roots: DEFAULT_ROOTS,
    forbidden: [
      { ruleId: 'AIC_SHARED_PROVIDER_ENV' },
      { ruleId: 'AIC_LEGACY_PROVIDER_SINK', paths: LEGACY_PROVIDER_SINKS },
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

interface InternalEdges { readonly specifiers: readonly string[]; readonly unsupported: readonly string[] }

function unwrapExpression(node: ts.Expression): ts.Expression {
  let current = node
  while (ts.isParenthesizedExpression(current) || ts.isAsExpression(current)
    || ts.isTypeAssertionExpression(current) || ts.isNonNullExpression(current)
    || ts.isSatisfiesExpression(current) || ts.isPartiallyEmittedExpression(current)) current = current.expression
  return current
}

function staticString(node: ts.Expression | undefined, values: ReadonlyMap<string, string>): string | null {
  if (!node) return null
  const current = unwrapExpression(node)
  if (ts.isStringLiteralLike(current)) return current.text
  if (ts.isIdentifier(current)) return values.get(current.text) ?? null
  if (ts.isBinaryExpression(current) && current.operatorToken.kind === ts.SyntaxKind.PlusToken) {
    const left = staticString(current.left, values)
    const right = staticString(current.right, values)
    return left === null || right === null ? null : left + right
  }
  if (ts.isTemplateExpression(current)) {
    let value = current.head.text
    for (const span of current.templateSpans) {
      const expression = staticString(span.expression, values)
      if (expression === null) return null
      value += expression + span.literal.text
    }
    return value
  }
  return null
}

function assignments(sourceFile: ts.SourceFile): Array<{ readonly name: ts.BindingName | ts.Expression; readonly value: ts.Expression }> {
  const result: Array<{ name: ts.BindingName | ts.Expression; value: ts.Expression }> = []
  const visit = (node: ts.Node) => {
    if ((ts.isVariableDeclaration(node) || ts.isParameter(node)) && node.initializer) result.push({ name: node.name, value: node.initializer })
    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.EqualsToken) result.push({ name: node.left, value: node.right })
    ts.forEachChild(node, visit)
  }
  visit(sourceFile)
  return result
}

function collectStaticStrings(sourceFile: ts.SourceFile): Map<string, string> {
  const strings = new Map<string, string>()
  const flows = assignments(sourceFile)
  let changed = true
  while (changed) {
    changed = false
    for (const flow of flows) {
      if (!ts.isIdentifier(flow.name) || strings.has(flow.name.text)) continue
      const value = staticString(flow.value, strings)
      if (value !== null) { strings.set(flow.name.text, value); changed = true }
    }
  }
  return strings
}

function propertyName(node: ts.Expression | ts.PropertyName | undefined, strings: ReadonlyMap<string, string>): string | null {
  if (!node) return null
  if (ts.isComputedPropertyName(node)) return staticString(node.expression, strings)
  if (ts.isIdentifier(node) || ts.isStringLiteralLike(node) || ts.isNumericLiteral(node)) return node.text
  return staticString(node as ts.Expression, strings)
}

function usesSharedProviderEnvironment(source: string, path: string): { found: boolean; unsupported: readonly string[] } {
  const sourceFile = ts.createSourceFile(path, source, ts.ScriptTarget.Latest, true)
  const strings = collectStaticStrings(sourceFile)
  const flows = assignments(sourceFile)
  const globalAliases = new Set(['globalThis', 'global'])
  const processAliases = new Set(['process'])
  const environmentAliases = new Set<string>()
  let found = false
  const unsupported = new Set<string>()

  for (const statement of sourceFile.statements) {
    if (ts.isImportDeclaration(statement) && ts.isStringLiteralLike(statement.moduleSpecifier)
      && ['process', 'node:process'].includes(statement.moduleSpecifier.text)) {
      const clause = statement.importClause
      if (clause?.name) processAliases.add(clause.name.text)
      const bindings = clause?.namedBindings
      if (bindings && ts.isNamespaceImport(bindings)) processAliases.add(bindings.name.text)
      if (bindings && ts.isNamedImports(bindings)) {
        for (const element of bindings.elements) {
          const imported = (element.propertyName ?? element.name).text
          if (imported === 'env') environmentAliases.add(element.name.text)
          if (imported === 'default') processAliases.add(element.name.text)
        }
      }
    }
    if (ts.isImportEqualsDeclaration(statement) && ts.isExternalModuleReference(statement.moduleReference)
      && staticString(statement.moduleReference.expression, strings)
      && ['process', 'node:process'].includes(staticString(statement.moduleReference.expression, strings)!)) {
      processAliases.add(statement.name.text)
    }
  }

  const staticMember = (node: ts.Expression): { readonly base: ts.Expression; readonly key: string | null } | null => {
    const current = unwrapExpression(node)
    if (ts.isPropertyAccessExpression(current)) return { base: current.expression, key: current.name.text }
    if (ts.isElementAccessExpression(current)) return { base: current.expression,
      key: staticString(current.argumentExpression, strings) }
    return null
  }
  const isReflectGet = (node: ts.Expression): boolean => {
    const current = unwrapExpression(node)
    const member = staticMember(current)
    return Boolean(member && ts.isIdentifier(unwrapExpression(member.base))
      && (unwrapExpression(member.base) as ts.Identifier).text === 'Reflect' && member.key === 'get')
  }
  const isProcessModuleLoad = (node: ts.Expression): boolean => {
    const current = unwrapExpression(node)
    return ts.isCallExpression(current) && ts.isIdentifier(unwrapExpression(current.expression))
      && (unwrapExpression(current.expression) as ts.Identifier).text === 'require'
      && current.arguments.length === 1
      && ['process', 'node:process'].includes(staticString(current.arguments[0], strings) ?? '')
  }
  type Taint = 'global' | 'process' | 'environment'
  const taintOf = (node: ts.Expression): Taint | null => {
    const current = unwrapExpression(node)
    if (ts.isIdentifier(current)) {
      if (environmentAliases.has(current.text)) return 'environment'
      if (processAliases.has(current.text)) return 'process'
      if (globalAliases.has(current.text)) return 'global'
      return null
    }
    if (isProcessModuleLoad(current)) return 'process'
    const member = staticMember(current)
    if (member) {
      const base = taintOf(member.base)
      if (base === 'global' && member.key === 'process') return 'process'
      if (base === 'process' && member.key === 'env') return 'environment'
    }
    if (ts.isCallExpression(current) && isReflectGet(current.expression) && current.arguments.length >= 2) {
      const base = taintOf(current.arguments[0])
      const key = staticString(current.arguments[1], strings)
      if (base === 'global' && key === 'process') return 'process'
      if (base === 'process' && key === 'env') return 'environment'
    }
    if (ts.isObjectLiteralExpression(current)) {
      for (const property of current.properties) {
        if (ts.isSpreadAssignment(property)) {
          const spread = taintOf(property.expression)
          if (spread) return spread
        }
      }
    }
    return null
  }
  const bind = (name: ts.BindingName | ts.Expression, taint: Taint): boolean => {
    const current = ts.isExpression(name) ? unwrapExpression(name) : name
    if (ts.isIdentifier(current)) {
      const target = taint === 'global' ? globalAliases : taint === 'process' ? processAliases : environmentAliases
      if (!target.has(current.text)) { target.add(current.text); return true }
      return false
    }
    const properties = ts.isObjectBindingPattern(current) ? current.elements : ts.isObjectLiteralExpression(current)
      ? current.properties : []
    let changed = false
    for (const property of properties) {
      if ((ts.isBindingElement(property) && property.dotDotDotToken) || ts.isSpreadAssignment(property)) {
        if (taint === 'environment') found = true
        const target = ts.isBindingElement(property) ? property.name : property.expression
        changed = bind(target, taint) || changed
        continue
      }
      const keyNode = ts.isBindingElement(property) ? property.propertyName ?? (ts.isIdentifier(property.name) ? property.name : undefined)
        : property.name
      const key = propertyName(keyNode, strings)
      const target = ts.isBindingElement(property) ? property.name
        : ts.isPropertyAssignment(property) ? property.initializer
          : ts.isShorthandPropertyAssignment(property) ? property.name : undefined
      if (!target) continue
      if (taint === 'environment') {
        if (key && PROVIDER_ENV_KEYS.has(key)) found = true
        continue
      }
      if (taint === 'process' && key === 'env') changed = bind(target, 'environment') || changed
      if (taint === 'global' && key === 'process') changed = bind(target, 'process') || changed
    }
    return changed
  }
  let changed = true
  while (changed) {
    changed = false
    for (const flow of flows) {
      const taint = taintOf(flow.value)
      if (taint) changed = bind(flow.name, taint) || changed
    }
  }

  const isValueIdentifier = (node: ts.Identifier): boolean => {
    const parent = node.parent
    if ((ts.isVariableDeclaration(parent) || ts.isParameter(parent) || ts.isBindingElement(parent)) && parent.name === node) return false
    if (ts.isBinaryExpression(parent) && parent.left === node
      && parent.operatorToken.kind >= ts.SyntaxKind.FirstAssignment
      && parent.operatorToken.kind <= ts.SyntaxKind.LastAssignment) return false
    if (ts.isPropertyAccessExpression(parent) && parent.name === node) return false
    if ((ts.isPropertyAssignment(parent) || ts.isShorthandPropertyAssignment(parent)) && parent.name === node) return false
    if (ts.isImportClause(parent) || ts.isNamespaceImport(parent) || ts.isImportSpecifier(parent)) return false
    return true
  }
  const isModeledEnvironmentParent = (node: ts.Expression): boolean => {
    const parent = node.parent
    if (ts.isParenthesizedExpression(parent) || ts.isAsExpression(parent) || ts.isTypeAssertionExpression(parent)
      || ts.isNonNullExpression(parent) || ts.isSatisfiesExpression(parent)) return true
    if ((ts.isVariableDeclaration(parent) || ts.isParameter(parent)) && parent.initializer === node) return true
    if (ts.isBinaryExpression(parent) && parent.operatorToken.kind === ts.SyntaxKind.EqualsToken && parent.right === node) {
      return ts.isIdentifier(unwrapExpression(parent.left)) || ts.isObjectLiteralExpression(unwrapExpression(parent.left))
    }
    if ((ts.isPropertyAccessExpression(parent) || ts.isElementAccessExpression(parent)) && parent.expression === node) return true
    if (ts.isCallExpression(parent) && isReflectGet(parent.expression) && parent.arguments[0] === node) return true
    if (ts.isSpreadAssignment(parent)) return true
    if (ts.isBinaryExpression(parent) && parent.operatorToken.kind === ts.SyntaxKind.InKeyword && parent.right === node) return true
    return false
  }
  const inspect = (node: ts.Node) => {
    if (ts.isPropertyAccessExpression(node) && taintOf(node.expression) === 'environment' && PROVIDER_ENV_KEYS.has(node.name.text)) {
      found = true
    }
    if (ts.isElementAccessExpression(node) && taintOf(node.expression) === 'environment') {
      const key = staticString(node.argumentExpression, strings)
      if (key === null) unsupported.add('dynamic-environment-key')
      else if (PROVIDER_ENV_KEYS.has(key)) found = true
    }
    if (ts.isElementAccessExpression(node) && taintOf(node.expression) === 'process'
      && staticString(node.argumentExpression, strings) === null) unsupported.add('dynamic-environment-key')
    if (ts.isCallExpression(node) && isReflectGet(node.expression) && node.arguments.length >= 2) {
      const base = taintOf(node.arguments[0])
      const key = staticString(node.arguments[1], strings)
      if (base && key === null) unsupported.add('dynamic-environment-key')
      else if (base === 'environment' && key && PROVIDER_ENV_KEYS.has(key)) found = true
    }
    if (ts.isCallExpression(node) && !isReflectGet(node.expression)) {
      if (node.arguments.some(argument => taintOf(argument) === 'environment')) unsupported.add('unmodeled-environment-operation')
      const callee = staticMember(node.expression)
      if (callee && taintOf(callee.base) === 'environment') unsupported.add('unmodeled-environment-operation')
    }
    if (ts.isSpreadAssignment(node) && taintOf(node.expression) === 'environment') found = true
    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.InKeyword
      && taintOf(node.right) === 'environment') {
      const key = staticString(node.left, strings)
      if (key === null) unsupported.add('dynamic-environment-key')
      else if (PROVIDER_ENV_KEYS.has(key)) found = true
    }
    if (ts.isExpression(node) && taintOf(node) === 'environment'
      && (!ts.isIdentifier(node) || isValueIdentifier(node)) && !isModeledEnvironmentParent(node)) {
      unsupported.add('unmodeled-environment-operation')
    }
    ts.forEachChild(node, inspect)
  }
  inspect(sourceFile)
  return { found, unsupported: [...unsupported].sort() }
}

function isImportMetaUrl(node: ts.Expression): boolean {
  const current = unwrapExpression(node)
  return ts.isPropertyAccessExpression(current) && current.name.text === 'url'
    && current.expression.kind === ts.SyntaxKind.MetaProperty
}

function internalEdges(source: string, path: string): InternalEdges {
  const sourceFile = ts.createSourceFile(path, source, ts.ScriptTarget.Latest, true)
  const strings = collectStaticStrings(sourceFile)
  const values = new Set<string>()
  const unsupported = new Set<string>()
  const createRequireFactories = new Set<string>()
  const moduleNamespaces = new Set<string>()
  for (const statement of sourceFile.statements) {
    if (!ts.isImportDeclaration(statement) || !ts.isStringLiteralLike(statement.moduleSpecifier)
      || !['module', 'node:module'].includes(statement.moduleSpecifier.text)) continue
    const bindings = statement.importClause?.namedBindings
    if (bindings && ts.isNamedImports(bindings)) {
      for (const element of bindings.elements) if ((element.propertyName ?? element.name).text === 'createRequire') {
        createRequireFactories.add(element.name.text)
      }
    } else if (bindings && ts.isNamespaceImport(bindings)) moduleNamespaces.add(bindings.name.text)
  }
  const isCreateRequire = (node: ts.Expression): boolean => {
    const current = unwrapExpression(node)
    if (ts.isIdentifier(current)) return createRequireFactories.has(current.text)
    return ts.isPropertyAccessExpression(current) && current.name.text === 'createRequire'
      && ts.isIdentifier(current.expression) && moduleNamespaces.has(current.expression.text)
  }
  const loaderAliases = new Set<string>()
  const flows = assignments(sourceFile)
  const isModuleRequire = (node: ts.Expression): boolean => {
    const current = unwrapExpression(node)
    if (ts.isPropertyAccessExpression(current)) return ts.isIdentifier(current.expression)
      && current.expression.text === 'module' && current.name.text === 'require'
    return ts.isElementAccessExpression(current) && ts.isIdentifier(current.expression)
      && current.expression.text === 'module' && staticString(current.argumentExpression, strings) === 'require'
  }
  let changed = true
  while (changed) {
    changed = false
    for (const flow of flows) {
      if (!ts.isIdentifier(flow.name) || loaderAliases.has(flow.name.text)) continue
      const value = unwrapExpression(flow.value)
      if (isCreateRequire(value) && !createRequireFactories.has(flow.name.text)) {
        createRequireFactories.add(flow.name.text); changed = true; continue
      }
      const fromFactory = ts.isCallExpression(value) && isCreateRequire(value.expression)
      if (fromFactory && (value.arguments.length !== 1
        || !(isImportMetaUrl(value.arguments[0]) || (ts.isIdentifier(unwrapExpression(value.arguments[0]))
          && (unwrapExpression(value.arguments[0]) as ts.Identifier).text === '__filename')))) unsupported.add('create-require-base')
      const boundModuleRequire = ts.isCallExpression(value) && ts.isPropertyAccessExpression(value.expression)
        && value.expression.name.text === 'bind' && isModuleRequire(value.expression.expression)
      if ((fromFactory && value.arguments.length === 1 && (isImportMetaUrl(value.arguments[0])
        || (ts.isIdentifier(unwrapExpression(value.arguments[0])) && (unwrapExpression(value.arguments[0]) as ts.Identifier).text === '__filename')))
        || isModuleRequire(value)
        || boundModuleRequire || (ts.isIdentifier(value) && (value.text === 'require' || loaderAliases.has(value.text)))) {
        loaderAliases.add(flow.name.text); changed = true
      }
    }
  }
  const isLoader = (node: ts.Expression) => {
    const current = unwrapExpression(node)
    return (ts.isIdentifier(current) && (current.text === 'require' || loaderAliases.has(current.text))) || isModuleRequire(current)
  }
  const add = (node: ts.Expression | undefined, dynamicCode: string) => {
    const specifier = staticString(node, strings)
    if (specifier === null) { unsupported.add(dynamicCode); return }
    if (specifier.startsWith('.') || specifier.startsWith('@/')) values.add(specifier)
  }
  const visit = (node: ts.Node) => {
    if (ts.isImportDeclaration(node)) add(node.moduleSpecifier, 'dynamic-import')
    if (ts.isExportDeclaration(node) && node.moduleSpecifier) add(node.moduleSpecifier, 'dynamic-import')
    if (ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference)) add(node.moduleReference.expression, 'dynamic-require')
    if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      if (node.arguments[0] && ts.isStringLiteralLike(unwrapExpression(node.arguments[0]))) add(node.arguments[0], 'dynamic-import')
      else unsupported.add('dynamic-import')
    }
    if (ts.isCallExpression(node) && isCreateRequire(node.expression)
      && (node.arguments.length !== 1 || !(isImportMetaUrl(node.arguments[0])
        || (ts.isIdentifier(unwrapExpression(node.arguments[0]))
          && (unwrapExpression(node.arguments[0]) as ts.Identifier).text === '__filename')))) {
      unsupported.add('create-require-base')
    }
    if (ts.isCallExpression(node) && isLoader(node.expression)) add(node.arguments[0], 'dynamic-require')
    ts.forEachChild(node, visit)
  }
  visit(sourceFile)
  return { specifiers: [...values].sort(), unsupported: [...unsupported].sort() }
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

      const providerEnvironment = usesSharedProviderEnvironment(source, current.path)
      for (const reason of providerEnvironment.unsupported) {
        const finding = { ruleId: 'AIC_PROVIDER_ENV_UNSUPPORTED', chain: [...current.chain, reason] }
        scannerErrors.set(findingKey(finding), finding)
      }
      for (const rule of config.forbidden) {
        const pathMatch = rule.paths?.includes(currentRelative) === true
        const providerEnvironmentMatch = rule.ruleId === 'AIC_SHARED_PROVIDER_ENV'
          && providerEnvironment.found
        const sourceMatch = rule.sourcePatterns?.some(pattern => {
          pattern.lastIndex = 0
          return pattern.test(source)
        }) === true
        if (pathMatch || providerEnvironmentMatch || sourceMatch) {
          const finding = { ruleId: rule.ruleId, chain: current.chain }
          violations.set(findingKey(finding), finding)
        }
      }

      if (!SCRIPT_EXTENSIONS.has(extname(current.path))) continue
      const edges = internalEdges(source, current.path)
      for (const unsupported of edges.unsupported) {
        const finding = { ruleId: 'AIC_IMPORT_UNSUPPORTED', chain: [...current.chain, unsupported] }
        scannerErrors.set(findingKey(finding), finding)
      }
      for (const specifier of edges.specifiers) {
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
