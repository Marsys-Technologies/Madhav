import { join, relative } from 'node:path'

import ts from 'typescript'

interface BoundaryViolation {
  line: number
  kind: 'raw database import' | 'unresolved module load' | 'adapter SQL'
  detail: string
}

const rawModules = new Set(['src/lib/db/client.ts', 'src/lib/storage/postgres.ts'])
const directSql = /\b(?:SELECT\s+[\s\S]*?\bFROM|INSERT\s+INTO|UPDATE\s+[\w."]+\s+SET|DELETE\s+FROM|(?:ALTER|CREATE|DROP|TRUNCATE)\s+TABLE)\b/i

/** Examine only the named adapter. A scoped owner may import its own database implementation. */
export function inspectDbAdapter(
  program: ts.Program,
  source: ts.SourceFile,
  platformRoot: string,
  moduleHost: ts.ModuleResolutionHost = ts.sys,
): BoundaryViolation[] {
  const checker = program.getTypeChecker()
  const violations: BoundaryViolation[] = []

  function report(node: ts.Node, kind: BoundaryViolation['kind'], detail: string) {
    const line = source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1
    violations.push({ line, kind, detail })
  }

  function localName(file: string) {
    return relative(platformRoot, file).replaceAll('\\', '/')
  }

  function rawOrigin(symbol: ts.Symbol | undefined, seen = new Set<ts.Symbol>()): string | undefined {
    if (!symbol) return
    const declarations = symbol.declarations
    if (declarations?.length && declarations.every((node) =>
      (ts.isExportSpecifier(node) && (node.isTypeOnly || node.parent.parent.isTypeOnly)) ||
      (ts.isNamespaceExport(node) && node.parent.isTypeOnly)
    )) return

    const origin = symbol.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(symbol) : symbol
    if (!(origin.flags & (ts.SymbolFlags.Value | ts.SymbolFlags.Module)) || seen.has(origin)) return
    seen.add(origin)
    for (const declaration of origin.declarations ?? []) {
      const file = localName(declaration.getSourceFile().fileName)
      if (rawModules.has(file) || /(?:^|\/)node_modules\/(?:@types\/)?pg\//.test(file)) return file
      if (file === 'src/lib/storage/index.ts' && origin.name === 'getStorageClient') return file
      if (ts.isVariableDeclaration(declaration) && declaration.initializer) {
        const value = declaration.initializer
        const inherited = rawOrigin(checker.getSymbolAtLocation(value), seen)
        if (inherited) return inherited
      }
    }
    if (origin.flags & ts.SymbolFlags.Module) {
      for (const member of checker.getExportsOfModule(origin)) {
        const raw = rawOrigin(member, seen)
        if (raw) return raw
      }
    }
  }

  function checkModule(node: ts.Node, specifier: ts.Expression | undefined, names?: readonly ts.ModuleExportName[]) {
    if (!specifier || !ts.isStringLiteralLike(specifier)) {
      report(node, 'unresolved module load', 'module source must be statically resolvable')
      return
    }
    if (/^pg(?:\/|$)/.test(specifier.text)) {
      report(node, 'raw database import', specifier.text)
      return
    }
    let moduleSymbol = checker.getSymbolAtLocation(specifier)
    if (!moduleSymbol && ts.isCallExpression(node)) {
      const resolved = ts.resolveModuleName(specifier.text, source.fileName, program.getCompilerOptions(), moduleHost).resolvedModule
      const file = resolved && localName(resolved.resolvedFileName)
      if (file && rawModules.has(file)) {
        report(node, 'raw database import', `${specifier.text} resolves to ${file}`)
        return
      }
      const resolvedSource = resolved && program.getSourceFile(resolved.resolvedFileName)
      if (resolvedSource) moduleSymbol = checker.getSymbolAtLocation(resolvedSource)
      if (!moduleSymbol) {
        report(node, 'unresolved module load', `cannot inspect ${specifier.text}`)
        return
      }
    }
    if (!names) {
      const raw = rawOrigin(moduleSymbol)
      if (raw) report(node, 'raw database import', `${specifier.text} resolves to ${raw}`)
      return
    }
    for (const name of names) {
      const raw = rawOrigin(checker.getSymbolAtLocation(name))
      if (raw) report(name, 'raw database import', `${name.text} resolves to ${raw}`)
    }
  }

  function visit(node: ts.Node) {
    if (ts.isImportDeclaration(node) && !node.importClause?.isTypeOnly) {
      const bindings = node.importClause?.namedBindings
      if (bindings && ts.isNamedImports(bindings)) {
        const names = bindings.elements.filter((binding) => !binding.isTypeOnly).map((binding) => binding.name)
        if (node.importClause?.name) names.push(node.importClause.name)
        if (names.length) checkModule(node, node.moduleSpecifier, names)
      } else {
        checkModule(node, node.moduleSpecifier, bindings ? undefined : node.importClause?.name && [node.importClause.name])
      }
    } else if (ts.isExportDeclaration(node) && !node.isTypeOnly && node.moduleSpecifier) {
      const exports = node.exportClause
      if (exports && ts.isNamedExports(exports)) {
        const names = exports.elements.filter((binding) => !binding.isTypeOnly).map((binding) => binding.name)
        if (names.length) checkModule(node, node.moduleSpecifier, names)
      } else {
        checkModule(node, node.moduleSpecifier)
      }
    } else if (ts.isImportEqualsDeclaration(node) && !node.isTypeOnly && ts.isExternalModuleReference(node.moduleReference)) {
      checkModule(node, node.moduleReference.expression)
    } else if (ts.isCallExpression(node) &&
      (node.expression.kind === ts.SyntaxKind.ImportKeyword ||
        (ts.isIdentifier(node.expression) && node.expression.text === 'require'))) {
      checkModule(node, node.arguments[0])
    } else if (ts.isStringLiteralLike(node) || ts.isTemplateExpression(node)) {
      const value = ts.isTemplateExpression(node)
        ? node.head.text + node.templateSpans.map((span) => `?${span.literal.text}`).join('')
        : node.text
      if (directSql.test(value)) report(node, 'adapter SQL', 'move the SQL statement into the data owner')
    }
    ts.forEachChild(node, visit)
  }

  visit(source)
  return violations
}

const migrationHealthOwners = {
  route: ['src/app/api/mcp/health/migrations/route.ts', 'GET'],
  facade: ['src/lib/db/migration-set.ts', 'readAppliedMigrationSet'],
  auth: ['src/lib/mcp/service_token.ts', 'validateServiceToken'],
  digest: ['src/lib/mcp/migration_set_digest.ts', 'readMigrationSet'],
  query: ['src/lib/db/client.ts', 'query'],
} as const

type MigrationHealthPortViolation = 'missing owner export' | 'unresolved local module'
  | 'route must call its facade once' | 'route has an unapproved local value import'
  | 'facade must inject only the canonical query'
  | 'digest must call its injected query once without escape'

/** Keep the named Portal/MCP GET, Data/release facade and digest, and DB infrastructure port connected. */
export function inspectMigrationHealthPort(program: ts.Program, platformRoot: string): MigrationHealthPortViolation[] {
  const checker = program.getTypeChecker()
  const violations: MigrationHealthPortViolation[] = []

  function origin(symbol: ts.Symbol | undefined): ts.Symbol | undefined {
    if (symbol && symbol.flags & ts.SymbolFlags.Alias) return checker.getAliasedSymbol(symbol)
    return symbol
  }

  function owner([file, name]: readonly [string, string]) {
    const source = program.getSourceFile(join(platformRoot, file))
    const sourceModule = source && checker.getSymbolAtLocation(source)
    const exports = sourceModule ? checker.getExportsOfModule(sourceModule) : []
    const symbol = origin(exports.find((item) => item.name === name))
    if (!source || !symbol?.valueDeclaration || symbol.valueDeclaration.getSourceFile() !== source) return
    return { source, symbol, exports, declaration: symbol.valueDeclaration }
  }

  function valueSymbol(node: ts.Node): ts.Symbol | undefined {
    if (ts.isShorthandPropertyAssignment(node)) return origin(checker.getShorthandAssignmentValueSymbol(node))
    return origin(checker.getSymbolAtLocation(node))
  }

  function references(root: ts.Node, symbol: ts.Symbol): ts.Node[] {
    const found: ts.Node[] = []
    function visit(node: ts.Node) {
      if (ts.isTypeNode(node) || ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) return
      const isPropertyName = ts.isPropertyAccessExpression(node.parent) && node.parent.name === node
      const isShorthandName = ts.isShorthandPropertyAssignment(node.parent) && node.parent.name === node
      if (!isPropertyName && !isShorthandName && valueSymbol(node) === symbol) {
        found.push(node)
        return
      }
      ts.forEachChild(node, visit)
    }
    ts.forEachChild(root, visit)
    return found
  }

  function inOwnerBody(node: ts.Node, body: ts.Block): boolean {
    for (let parent = node.parent; parent; parent = parent.parent) {
      if (parent === body) return true
      if (ts.isFunctionLike(parent) || ts.isIfStatement(parent) || ts.isConditionalExpression(parent)
        || ts.isIterationStatement(parent, false) || ts.isSwitchStatement(parent)) return false
      if (ts.isBinaryExpression(parent) && [
        ts.SyntaxKind.AmpersandAmpersandToken, ts.SyntaxKind.BarBarToken, ts.SyntaxKind.QuestionQuestionToken,
      ].includes(parent.operatorToken.kind)) return false
    }
    return false
  }

  const route = owner(migrationHealthOwners.route)
  const facade = owner(migrationHealthOwners.facade)
  const auth = owner(migrationHealthOwners.auth)
  const digest = owner(migrationHealthOwners.digest)
  const query = owner(migrationHealthOwners.query)
  if (!route || !facade || !auth || !digest || !query) return ['missing owner export']
  const querySymbol = query.symbol

  function isLocalSpecifier(node: ts.Node | undefined): boolean {
    return !!node && ts.isStringLiteralLike(node) && (node.text.startsWith('.') || node.text.startsWith('@/'))
  }

  function unapprovedLocalValueImport(node: ts.Node, allowedOwners: readonly { source: ts.SourceFile; symbol: ts.Symbol }[]): boolean {
    if (ts.isImportDeclaration(node) && isLocalSpecifier(node.moduleSpecifier)) {
      const clause = node.importClause
      if (clause?.isTypeOnly) return false
      const bindings = clause?.namedBindings
      if (!bindings || !ts.isNamedImports(bindings) || clause?.name) return true
      const source = checker.getSymbolAtLocation(node.moduleSpecifier)?.declarations?.[0]
      return bindings.elements.some((item) => !item.isTypeOnly && !allowedOwners.some((allowed) =>
        source === allowed.source && valueSymbol(item.name) === allowed.symbol))
    }
    if (ts.isExportDeclaration(node) && !node.isTypeOnly && isLocalSpecifier(node.moduleSpecifier)) {
      return !node.exportClause || !ts.isNamedExports(node.exportClause)
        || node.exportClause.elements.some((item) => !item.isTypeOnly)
    }
    if (ts.isImportEqualsDeclaration(node) && !node.isTypeOnly && ts.isExternalModuleReference(node.moduleReference)) {
      return isLocalSpecifier(node.moduleReference.expression)
    }
    if (ts.isCallExpression(node) && (node.expression.kind === ts.SyntaxKind.ImportKeyword
      || (ts.isIdentifier(node.expression) && node.expression.text === 'require'))) {
      const name = node.arguments[0]
      return !name || !ts.isStringLiteralLike(name) || isLocalSpecifier(name)
    }
    return ts.forEachChild(node, (child) => unapprovedLocalValueImport(child, allowedOwners) || undefined) ?? false
  }

  function exportsQuery(symbol: ts.Symbol): boolean {
    if (symbol.declarations?.length && symbol.declarations.every((node) =>
      ts.isExportSpecifier(node) && (node.isTypeOnly || node.parent.parent.isTypeOnly))) return false
    return origin(symbol) === querySymbol
  }

  for (const { source } of [route, facade, digest]) {
    const unresolved = source.statements.some((node) => {
      if (!ts.isImportDeclaration(node) && !ts.isExportDeclaration(node)) return false
      const name = node.moduleSpecifier
      return name && isLocalSpecifier(name) && !checker.getSymbolAtLocation(name)
    })
    if (unresolved) {
      violations.push('unresolved local module')
      break
    }
  }

  if (unapprovedLocalValueImport(route.source, [facade, auth])) violations.push('route has an unapproved local value import')

  const get = route.declaration
  const body = ts.isFunctionDeclaration(get) && get.body
  const routeReferences = references(route.source, facade.symbol)
  const [routeRef] = routeReferences
  if (!body || routeReferences.length !== 1 || !ts.isCallExpression(routeRef.parent)
    || routeRef.parent.expression !== routeRef || routeRef.parent.arguments.length !== 0
    || !ts.isAwaitExpression(routeRef.parent.parent) || !inOwnerBody(routeRef, body)) {
    violations.push('route must call its facade once')
  }

  const applied = facade.declaration
  const forward = ts.isFunctionDeclaration(applied) && applied.body?.statements.length === 1
    ? applied.body.statements[0] : undefined
  const injected = forward && ts.isReturnStatement(forward) && forward.expression
  const queryReferences = references(facade.source, query.symbol)
  if (!injected || !ts.isCallExpression(injected) || valueSymbol(injected.expression) !== digest.symbol
    || injected.arguments.length !== 1 || queryReferences.length !== 1 || injected.arguments[0] !== queryReferences[0]
    || unapprovedLocalValueImport(facade.source, [digest, query]) || facade.exports.some(exportsQuery)) {
    violations.push('facade must inject only the canonical query')
  }

  const read = digest.declaration
  const parameter = ts.isFunctionDeclaration(read) && read.parameters.length === 1 && read.parameters[0]
  const port = parameter && !parameter.initializer && !parameter.dotDotDotToken && ts.isIdentifier(parameter.name)
    && valueSymbol(parameter.name)
  const portReferences = port && ts.isFunctionDeclaration(read) && read.body ? references(read.body, port) : []
  const [use] = portReferences
  if (portReferences.length !== 1 || !ts.isCallExpression(use.parent) || use.parent.expression !== use
    || use.parent.arguments.length !== 1 || !ts.isAwaitExpression(use.parent.parent)
    || !ts.isFunctionDeclaration(read) || !read.body || !inOwnerBody(use, read.body)
    || inspectDbAdapter(program, digest.source, platformRoot).some((row) => row.kind !== 'adapter SQL')) {
    violations.push('digest must call its injected query once without escape')
  }
  return violations
}
