import { relative } from 'node:path'

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
