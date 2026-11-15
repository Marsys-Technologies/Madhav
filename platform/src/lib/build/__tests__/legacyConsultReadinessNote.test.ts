import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'
const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('server-only', () => ({}))
import { readLegacyConsultReadinessNote } from '../legacyConsultReadinessNote'

const LATEST = 'SELECT build_id FROM build_events WHERE chart_id = $1 ORDER BY emitted_at DESC LIMIT 1'
const CHECKPOINTS = `SELECT DISTINCT ON (asset_id) asset_id, status
           FROM build_checkpoints
          WHERE build_id = $1
          ORDER BY asset_id, completed_at DESC NULLS LAST`
beforeEach(() => { queryMock.mockReset() })

describe('observed legacy checkpoint context', () => {
  it('retains the one chart-bound read and undefined when no build was observed', async () => {
    queryMock.mockResolvedValue({ rows: [] })
    expect(await readLegacyConsultReadinessNote('chart')).toBeUndefined()
    expect(queryMock).toHaveBeenCalledExactlyOnceWith(LATEST, ['chart'])
  })

  it('uses the first returned build and exact checkpoint SQL, with no note for empty rows', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ build_id: 'first' }, { build_id: 'second' }] })
      .mockResolvedValueOnce({ rows: [] })
    expect(await readLegacyConsultReadinessNote('chart')).toBeUndefined()
    expect(queryMock.mock.calls).toEqual([[LATEST, ['chart']], [CHECKPOINTS, ['first']]])
  })

  it('bounds an all-success note to observed rows without claiming chart completeness', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ build_id: 'build' }] })
      .mockResolvedValueOnce({ rows: [{ asset_id: 'b', status: 'success' }, { asset_id: 'a', status: 'success' }] })
    const note = await readLegacyConsultReadinessNote('chart')
    expect(note).toBe('Legacy checkpoint summary: all 2 observed asset checkpoints report success. Completeness across current chart assets/data domains is not established.')
    expect(note).not.toContain('All data domains available')
    expect(queryMock.mock.calls).toEqual([[LATEST, ['chart']], [CHECKPOINTS, ['build']]])
  })

  it('preserves observed row order, successful/non-successful lists and counts in the partial note', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ build_id: 'build' }] }).mockResolvedValueOnce({ rows: [
      { asset_id: 'failed-first', status: 'failed' },
      { asset_id: 'ready-second', status: 'success' },
      { asset_id: 'pending-third', status: 'pending' },
    ] })
    expect(await readLegacyConsultReadinessNote('chart')).toBe([
      'Legacy checkpoint summary: observed asset checkpoint results.',
      'Observed asset checkpoints reporting success: [ready-second].',
      'Observed asset checkpoints not reporting success: [failed-first, pending-third].',
      'Do NOT hallucinate data for unbuilt assets — say "data not yet available" for those domains.',
      '(1 of 3 observed asset checkpoints report success)',
      'Completeness across current chart assets/data domains is not established.',
    ].join(' '))
    expect(queryMock).toHaveBeenCalledTimes(2)
  })

  it('retains zero successful observed rows without asserting a current-asset denominator', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ build_id: 'build' }] })
      .mockResolvedValueOnce({ rows: [{ asset_id: 'pending', status: 'pending' }] })
    const note = await readLegacyConsultReadinessNote('chart')
    expect(note).toContain('reporting success: [].')
    expect(note).toContain('not reporting success: [pending].')
    expect(note).toContain('(0 of 1 observed asset checkpoints report success)')
    expect(note).toContain('Completeness across current chart assets/data domains is not established.')
    expect(queryMock).toHaveBeenCalledTimes(2)
  })

  it.each([0, 1])('retains nonfatal query failure at stage %i', async stage => {
    if (stage) queryMock.mockResolvedValueOnce({ rows: [{ build_id: 'build' }] })
    queryMock.mockRejectedValueOnce(new Error('synthetic unavailable'))
    expect(await readLegacyConsultReadinessNote('chart')).toBeUndefined()
    expect(queryMock).toHaveBeenCalledTimes(stage + 1)
  })

  it('retains the synchronous query failure boundary', async () => {
    queryMock.mockImplementation(() => { throw new Error('synthetic unavailable') })
    expect(await readLegacyConsultReadinessNote('chart')).toBeUndefined()
    expect(queryMock).toHaveBeenCalledOnce()
  })
})

const CONTRACT = {"route_identity_calls": ["2f71809f26b37cea3c247c674a29f94f2bbbd6a7137f947c9d12329e6cb36adb", "7ffeedd827157f6e308053f6edf91c45b0699a4709deaa7d59a37f4a0746e589", "d46c1e0c2b36544bd5d5c139a8695b12c003f75a2b4f0f67c2e95a5a2487a50a"], "msr_body": "46130f90262e0565b2f9a9cdd9a73adb87b0f650b83a53ba0cf86ec2ae05fb17", "readiness_body": "8cf5806635918244486eacc7e191769c5c60b275dfa315a31d97867a748a9270"}
const printer = ts.createPrinter({ removeComments: true, newLine: ts.NewLineKind.LineFeed })
const hash = (value: string) => createHash('sha256').update(value).digest('hex')
const normalized = (node: ts.Node, source: ts.SourceFile) => printer.printNode(ts.EmitHint.Unspecified, node, source)
const parse = (name: string, text: string) => ts.createSourceFile(name, text, ts.ScriptTarget.Latest, true)
function nodes(source: ts.SourceFile): ts.Node[] {
  const result: ts.Node[] = []
  const visit = (node: ts.Node) => { result.push(node); ts.forEachChild(node, visit) }
  visit(source)
  return result
}
function queryHashes(source: ts.SourceFile): string[] {
  return nodes(source).filter(ts.isCallExpression)
    .filter(node => ts.isIdentifier(node.expression) && node.expression.text === 'query')
    .map(node => hash(normalized(node, source))).sort()
}
function namedImport(source: ts.SourceFile, target: string, binding: string) {
  const imports = source.statements.filter(ts.isImportDeclaration)
    .filter(node => ts.isStringLiteral(node.moduleSpecifier) && node.moduleSpecifier.text === target)
  expect(imports).toHaveLength(1)
  const clause = imports[0].importClause
  expect(clause?.name).toBeUndefined()
  expect(clause?.isTypeOnly).toBe(false)
  const bindings = clause?.namedBindings
  expect(bindings && ts.isNamedImports(bindings)).toBe(true)
  const elements = bindings && ts.isNamedImports(bindings) ? bindings.elements : []
  expect(elements).toHaveLength(1)
  expect(elements[0].name.text).toBe(binding)
  expect(elements[0].propertyName?.text ?? elements[0].name.text).toBe(binding)
  expect(elements[0].isTypeOnly).toBe(false)
  return elements[0]
}
function nearestFunction(node: ts.Node): ts.Node | undefined {
  let parent = node.parent
  while (parent && !ts.isFunctionLike(parent)) parent = parent.parent
  return parent
}
function checkBinding(reference: ts.Identifier, expected: ts.Node, all: ts.Node[]) {
  const scopes = new Set<ts.Node>()
  for (let node: ts.Node | undefined = reference; node; node = node.parent) {
    if (ts.isBlock(node) || ts.isFunctionLike(node) || ts.isSourceFile(node)) scopes.add(node)
  }
  const names = (name: ts.BindingName): string[] => ts.isIdentifier(name) ? [name.text]
    : name.elements.flatMap(element => ts.isBindingElement(element) ? names(element.name) : [])
  const visible = all.filter(node => {
    let bound: string[] = [], scope: ts.Node | undefined, functionScoped = false
    if (ts.isImportSpecifier(node)) { bound = [node.name.text]; scope = node.getSourceFile() }
    else if (ts.isParameter(node)) { bound = names(node.name); scope = node.parent }
    else if (ts.isVariableDeclaration(node)) {
      bound = names(node.name)
      functionScoped = ts.isVariableDeclarationList(node.parent) && !(node.parent.flags & ts.NodeFlags.BlockScoped)
    } else if (ts.isFunctionDeclaration(node) || ts.isClassDeclaration(node)) bound = node.name ? [node.name.text] : []
    if (!bound.includes(reference.text)) return false
    if (!scope) {
      scope = node.parent
      while (scope && !(ts.isSourceFile(scope) || ts.isFunctionLike(scope) || (!functionScoped && ts.isBlock(scope)))) scope = scope.parent
    }
    return !!scope && scopes.has(scope)
  })
  expect(visible).toEqual([expected])
}
function checkOwner(name: string, text: string, symbol: string, expectedBody: string) {
  const source = parse(name, text)
  const imports = source.statements.filter(ts.isImportDeclaration)
    .map(node => ts.isStringLiteral(node.moduleSpecifier) ? node.moduleSpecifier.text : undefined)
  expect(imports).toEqual(['server-only', '@/lib/db/client'])
  namedImport(source, '@/lib/db/client', 'query')
  const functions = source.statements.filter(ts.isFunctionDeclaration)
  expect(functions).toHaveLength(1)
  expect(functions[0].name?.text).toBe(symbol)
  expect(functions[0].modifiers?.some(node => node.kind === ts.SyntaxKind.AsyncKeyword)).toBe(true)
  expect(functions[0].modifiers?.some(node => node.kind === ts.SyntaxKind.ExportKeyword)).toBe(true)
  expect(hash(normalized(functions[0].body!, source))).toBe(expectedBody)
  expect(source.statements.every(node => ts.isImportDeclaration(node) || ts.isFunctionDeclaration(node))).toBe(true)
}
function inspect(routeText: string, msrText: string, readinessText: string) {
  const route = parse('route.ts', routeText), all = nodes(route)
  expect(queryHashes(route)).toEqual(CONTRACT.route_identity_calls)
  const msrImport = namedImport(route, '@/lib/bodha/msrSignalSnippets', 'fetchMsrSnippets')
  const readinessImport = namedImport(route, '@/lib/build/legacyConsultReadinessNote', 'readLegacyConsultReadinessNote')
  const dispatchImport = namedImport(route, '@/lib/pipelines/shared', 'runAdapterDispatch')
  namedImport(route, '@/lib/db/client', 'query')
  expect(route.statements.filter(ts.isImportDeclaration).filter(node => ts.isStringLiteral(node.moduleSpecifier) && /(?:db\/client|^pg$)/.test(node.moduleSpecifier.text))).toHaveLength(1)
  const execute = route.statements.filter(ts.isFunctionDeclaration).filter(node => node.name?.text === 'executeMeteredRequest')
  expect(execute).toHaveLength(1)
  const dispatches = all.filter(ts.isCallExpression).filter(node => ts.isIdentifier(node.expression)
    && node.expression.text === 'runAdapterDispatch' && nearestFunction(node) === execute[0])
  expect(dispatches).toHaveLength(1)
  const dispatch = dispatches[0]
  checkBinding(dispatch.expression as ts.Identifier, dispatchImport, all)
  expect(dispatch.arguments).toHaveLength(1)
  const options = dispatch.arguments[0]
  expect(ts.isObjectLiteralExpression(options)).toBe(true)
  const properties = ts.isObjectLiteralExpression(options) ? options.properties : []
  expect(properties.some(ts.isSpreadAssignment)).toBe(false)
  const dispatchValue = (name: string) => {
    const matching = properties.filter(property => property.name
      && (ts.isIdentifier(property.name) || ts.isStringLiteral(property.name)) && property.name.text === name)
    expect(matching).toHaveLength(1)
    const property = matching[0]
    const value = ts.isShorthandPropertyAssignment(property) ? property.name
      : ts.isPropertyAssignment(property) ? property.initializer : undefined
    expect(value && ts.isIdentifier(value) && value.text).toBe(name)
    return value as ts.Identifier
  }
  checkBinding(dispatchValue('fetchMsrSnippets'), msrImport, all)
  const noteValue = dispatchValue('dataReadinessNote')
  const readCalls = all.filter(ts.isCallExpression).filter(node => ts.isIdentifier(node.expression)
    && node.expression.text === 'readLegacyConsultReadinessNote' && nearestFunction(node) === execute[0])
  expect(readCalls).toHaveLength(1)
  const awaited = readCalls[0].parent
  expect(ts.isAwaitExpression(awaited)).toBe(true)
  const noteDeclaration = awaited.parent
  expect(ts.isVariableDeclaration(noteDeclaration) && noteDeclaration.name.getText(route)).toBe('dataReadinessNote')
  expect(readCalls[0].arguments.map(arg => normalized(arg, route))).toEqual(['chartId'])
  expect(nearestFunction(readCalls[0])).toBe(execute[0])
  checkBinding(readCalls[0].expression as ts.Identifier, readinessImport, all)
  checkBinding(noteValue, noteDeclaration, all)
  for (const identifier of all.filter(ts.isIdentifier).filter(node => node.text === 'query')) {
    if (ts.isImportSpecifier(identifier.parent)) continue
    if (ts.isCallExpression(identifier.parent) && identifier.parent.expression === identifier) continue
    if (ts.isPropertyAssignment(identifier.parent) && identifier.parent.name === identifier) continue
    let parent: ts.Node | undefined = identifier.parent
    while (parent && !ts.isTypeNode(parent) && !ts.isStatement(parent)) parent = parent.parent
    expect(parent && ts.isTypeNode(parent)).toBe(true)
  }
  checkOwner('msr.ts', msrText, 'fetchMsrSnippets', CONTRACT.msr_body)
  checkOwner('readiness.ts', readinessText, 'readLegacyConsultReadinessNote', CONTRACT.readiness_body)
}

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..')
const source = {
  route: () => readFileSync(path.join(root, 'src/app/api/chat/consult/route.ts'), 'utf8'),
  msr: () => readFileSync(path.join(root, 'src/lib/bodha/msrSignalSnippets.ts'), 'utf8'),
  readiness: () => readFileSync(path.join(root, 'src/lib/build/legacyConsultReadinessNote.ts'), 'utf8'),
}
describe('exact legacy Consult owner boundaries', () => {
  it('connects the two owners and retains only the three exact Identity query/delegate callsites', () => {
    inspect(source.route(), source.msr(), source.readiness())
  })
  it('allows harmless import comments/formatting and unrelated presentation scope', () => {
    const route = source.route().replace('import { fetchMsrSnippets }', 'import { /* owner binding */\n fetchMsrSnippets,\n}')
      .replace('import { readLegacyConsultReadinessNote }', 'import {\n readLegacyConsultReadinessNote /* same owner */,\n}')
      .replace('import { runAdapterDispatch }', 'import { /* dispatch */ runAdapterDispatch, }')
      + `\nfunction presentationOnly() {
          const readLegacyConsultReadinessNote = () => 'presentation-local'
          const item = [{ status: 'visible' }].find(row => row.status === 'visible')
          return [item, readLegacyConsultReadinessNote()]
        }\n`
    const msr = source.msr().replace("import 'server-only'", 'import /* boundary */ "server-only"')
      .replace('import { query }', 'import { /* transport */ query, }')
    const readiness = source.readiness().replace('import { query }', 'import {\n query, /* same transport */\n}')
    inspect(route, msr, readiness)
  })

  const reviewedMutations = [
    { name: 'noop MSR dispatch callback with whole-tree shorthand decoy', apply: (route: string) => route.replace('    fetchMsrSnippets,', '    fetchMsrSnippets: async () => new Map(),') + '\nvoid ({ fetchMsrSnippets })\n' },
    { name: 'readiness dispatch value discarded', apply: (route: string) => route.replace('    dataReadinessNote,', '    dataReadinessNote: dataReadinessNote && undefined,') },
    { name: 'local readiness owner shadow', apply: (route: string) => route.replace('async function executeMeteredRequest(request: Request) {', 'async function executeMeteredRequest(request: Request) {\n  const readLegacyConsultReadinessNote = async () => undefined') },
  ]
  it.each(reviewedMutations)('rejects reviewed $name', mutation => {
    const route = source.route(), changed = mutation.apply(route)
    expect(changed).not.toBe(route)
    expect(() => inspect(changed, source.msr(), source.readiness())).toThrow()
  })

  const mutations = [
    { name: 'extra route query', target: 'route', from: 'await readLegacyConsultReadinessNote(chartId)', to: 'await query("SELECT * FROM build_runs")' },
    { name: 'changed Identity predicate at same query count', target: 'route', from: 'client_id FROM charts WHERE id=$1', to: 'client_id FROM charts WHERE id=$2' },
    { name: 'wrong domain owner import', target: 'route', from: '@/lib/bodha/msrSignalSnippets', to: '@/lib/build/msrSignalSnippets' },
    { name: 'disconnected snippet callback', target: 'route', from: '    fetchMsrSnippets,', to: '    fetchMsrSnippets: async () => new Map(),' },
    { name: 'missing readiness await', target: 'route', from: 'await readLegacyConsultReadinessNote(chartId)', to: 'readLegacyConsultReadinessNote(chartId)' },
    { name: 'query value escape', target: 'route', from: 'export async function POST', to: 'const unauthorizedQuery = query\nexport async function POST' },
    { name: 'extra raw owner import', target: 'msr', from: "import 'server-only'", to: "import 'server-only'\nimport { Pool } from 'pg'" },
    { name: 'stale MSR schema column', target: 'msr', from: 'signal_summary_text', to: 'signal_description' },
    { name: 'changed 295 truncation contract', target: 'msr', from: 'full.length > 295', to: 'full.length > 999' },
    { name: 'missing server boundary', target: 'readiness', from: "import 'server-only'", to: '// server-only' },
    { name: 'wrong checkpoint chart bind', target: 'readiness', from: '[chartId]', to: '[null]' },
    { name: 'changed latest-build selection', target: 'readiness', from: 'emitted_at DESC', to: 'emitted_at ASC' },
    { name: 'lost checkpoint DISTINCT', target: 'readiness', from: 'SELECT DISTINCT ON (asset_id)', to: 'SELECT' },
    { name: 'reintroduced universal availability claim', target: 'readiness', from: 'Completeness across current chart assets/data domains is not established.', to: 'All data domains available.' },
  ] as const
  it.each(mutations)('rejects $name', mutation => {
    const texts = { route: source.route(), msr: source.msr(), readiness: source.readiness() }
    expect(texts[mutation.target]).toContain(mutation.from)
    texts[mutation.target] = texts[mutation.target].replace(mutation.from, mutation.to)
    expect(() => inspect(texts.route, texts.msr, texts.readiness)).toThrow()
  })
})
