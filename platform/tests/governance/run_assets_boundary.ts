import { createHash } from 'node:crypto'
import ts from 'typescript'

// Exact retained Identity seam and Build query from accepted e2d595b1300b.
// These are per-port identities, not a count-based or directory exemption.
const identityBody = 'a30e8dc730cf6129034e1cc44edf7134e1b6a96f5157682b9a6eded8201d3d06'
const buildSql = '69c2c0c8e08ffb2ba6efb2948052c993d5dd0a1336b83116072806c6d99e6665'

export function inspectRunAssetsBoundary(routeText: string, ownerText: string): string[] {
  const violations: string[] = []
  const route = ts.createSourceFile('route.ts', routeText, ts.ScriptTarget.Latest, true)
  const owner = ts.createSourceFile('runAssets.ts', ownerText, ts.ScriptTarget.Latest, true)
  const hash = (text: string) => createHash('sha256').update(text).digest('hex')
  const functions = (source: ts.SourceFile, name: string) => source.statements.filter(
    (node): node is ts.FunctionDeclaration => ts.isFunctionDeclaration(node) && node.name?.text === name,
  )
  const auth = functions(route, 'requireSuperAdmin')
  const get = functions(route, 'GET')
  const read = functions(owner, 'readBuildRunAssets')
  if (auth.length !== 1 || hash(auth[0].getText(route)) !== identityBody) {
    violations.push('retained Identity profile-read seam changed')
  }
  if (get.length !== 1 || read.length !== 1) violations.push('missing or duplicated route/Build owner')

  function enclosingFunction(node: ts.Node): ts.FunctionDeclaration | undefined {
    for (let parent = node.parent; parent; parent = parent.parent) {
      if (ts.isFunctionDeclaration(parent)) return parent
      if (ts.isFunctionLike(parent)) return undefined
    }
  }

  function inspect(source: ts.SourceFile, isRoute: boolean) {
    const expectedImports = new Map<string, string[]>(isRoute ? [
      ['next/server', ['NextRequest', 'NextResponse']],
      ['@/lib/firebase/server', ['getServerUser']],
      ['@/lib/db/client', ['query']],
      ['@/lib/build/runAssets', ['readBuildRunAssets']],
    ] : [
      ['server-only', []],
      ['@/lib/db/client', ['query']],
      ['@/lib/db/columnPresence', ['blockedByAssetIdColumnPresent']],
    ])
    const foundImports = new Set<string>()
    for (const node of source.statements) {
      if (!ts.isImportDeclaration(node)) continue
      const specifier = ts.isStringLiteral(node.moduleSpecifier) ? node.moduleSpecifier.text : ''
      const allowed = expectedImports.get(specifier)
      const bindings = node.importClause?.namedBindings
      const names = bindings && ts.isNamedImports(bindings)
        ? bindings.elements.map(binding => [binding.propertyName?.text ?? binding.name.text, binding.name.text])
        : []
      if (!allowed || node.importClause?.name || node.importClause?.isTypeOnly || (bindings && !ts.isNamedImports(bindings)) ||
        names.some(([imported, local]) => imported !== local || !allowed.includes(imported)) ||
        names.length !== allowed.length) violations.push('unapproved port import or alias')
      foundImports.add(specifier)
    }
    if ([...expectedImports.keys()].some(key => !foundImports.has(key))) violations.push('missing port import')

    let queryCalls = 0
    let readCalls = 0
    let probeCalls = 0
    function visit(node: ts.Node) {
      if (ts.isCallExpression(node)) {
        const name = ts.isIdentifier(node.expression) ? node.expression.text : undefined
        const enclosing = enclosingFunction(node)
        if (name === 'query') {
          queryCalls++
          if (isRoute) {
            if (enclosing !== auth[0]) violations.push('Portal bypasses Build data owner')
          } else {
            if (enclosing !== read[0] || node.arguments.length !== 2 ||
              hash(node.arguments[0].getText(source)) !== buildSql ||
              node.arguments[1].getText(source) !== '[id]') violations.push('Build SQL/namespace/bind contract changed')
          }
        }
        if (name === 'readBuildRunAssets') {
          readCalls++
          if (!isRoute || enclosing !== get[0] || node.arguments.length !== 1 ||
            node.arguments[0].getText(source) !== 'id') violations.push('route must call its Build owner with the admitted id')
        }
        if (name === 'blockedByAssetIdColumnPresent') {
          probeCalls++
          if (isRoute || enclosing !== read[0] || node.arguments.length !== 0) violations.push('column probe escaped Build owner')
        }
        if (node.expression.kind === ts.SyntaxKind.ImportKeyword || name === 'require' || name === 'eval') {
          violations.push('unreviewed dynamic module or code escape')
        }
      }
      if (ts.isIdentifier(node) && ['query', 'readBuildRunAssets', 'blockedByAssetIdColumnPresent'].includes(node.text)) {
        const imported = ts.isImportSpecifier(node.parent) && node.parent.name === node
        const called = ts.isCallExpression(node.parent) && node.parent.expression === node
        const declared = !isRoute && ts.isFunctionDeclaration(node.parent) &&
          node.parent === read[0] && node.parent.name === node
        if (!imported && !called && !declared) violations.push('data port escaped its declared callsite')
      }
      if (ts.isVariableDeclaration(node) && node.name.getText(source) === 'blockedByCol') {
        if (isRoute || node.initializer?.getText(source) !==
          "includeBlockedBy ? 'bra.blocked_by_asset_id' : 'NULL::text AS blocked_by_asset_id'" ||
          !(node.parent.flags & ts.NodeFlags.Const)) {
          violations.push('optional-column compatibility contract changed')
        }
      }
      if (ts.isVariableDeclaration(node) && node.name.getText(source) === 'includeBlockedBy' &&
        (isRoute || node.initializer?.getText(source) !== 'await blockedByAssetIdColumnPresent()' ||
          !(node.parent.flags & ts.NodeFlags.Const))) violations.push('column probe result changed')
      if (!isRoute && ts.isBinaryExpression(node) && node.left.getText(source) === 'id' &&
        node.operatorToken.kind >= ts.SyntaxKind.FirstAssignment &&
        node.operatorToken.kind <= ts.SyntaxKind.LastAssignment) violations.push('bound run id modified')
      ts.forEachChild(node, visit)
    }
    visit(source)
    if (queryCalls !== 1) violations.push('port must have exactly its one declared query call')
    if (readCalls !== (isRoute ? 1 : 0)) violations.push('route/Build read port disconnected')
    if (probeCalls !== (isRoute ? 0 : 1)) violations.push('Build optional-column probe disconnected')
  }
  inspect(route, true)
  inspect(owner, false)
  return [...new Set(violations)]
}
