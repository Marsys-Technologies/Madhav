import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { execFileSync } from 'node:child_process'
import { McpClient } from '../audit/doctrine_harness/lib/mcp_client'
import { mintFreshProbeSessionCookie } from '../probe/session_auth'
import { collectManagedCase, collectPortalCase, collectRawCase } from './channel_clients'
import { synthesizeRawLifecycleEvidence } from './raw_external_synthesis'
import { casesForSuite, validateProtocol, type AcceptanceCaseInput, type AcceptanceSuite } from './acceptance_cases'
import { assertLiveEvidence, createCollectionArtifact, type AcceptanceCase, type CollectedCase } from './collection_types'

export interface Config { schema_version: 'purna-collection-config/v1'; environment: 'candidate' | 'live'; expected_revision: string; chart_id: string; portal_url: string; mcp_url: string; authorization_approval_id: string; max_polls?: number; max_actions?: number; portal_timeout_ms?: number; mcp_timeout_ms?: number }
class McpRequestDeadlineError extends Error { constructor() { super('PURNA_COLLECTION_MCP_REQUEST_DEADLINE') } }
export async function withMcpDeadline<T>(operation: (signal: AbortSignal) => Promise<T>, timeoutMs: number): Promise<T> {
  const abort = new AbortController()
  let timer: ReturnType<typeof setTimeout> | undefined
  try {
    return await Promise.race([
      operation(abort.signal),
      new Promise<T>((_resolve, reject) => { timer = setTimeout(() => { abort.abort(); reject(new McpRequestDeadlineError()) }, timeoutMs) }),
    ])
  } finally { if (timer) clearTimeout(timer) }
}
function object(value: unknown): Record<string, unknown> { if (typeof value !== 'object' || value === null || Array.isArray(value)) throw new Error('PURNA_COLLECTION_CONFIG_INVALID'); return value as Record<string, unknown> }
function parseConfig(value: unknown): Config { const data = object(value); if (data.schema_version !== 'purna-collection-config/v1' || !['candidate', 'live'].includes(String(data.environment)) || ![data.expected_revision, data.chart_id, data.portal_url, data.mcp_url, data.authorization_approval_id].every((item) => typeof item === 'string' && item.length > 0)) throw new Error('PURNA_COLLECTION_CONFIG_INVALID'); return data as unknown as Config }
function asCase(value: AcceptanceCaseInput): AcceptanceCase {
  if (!value.question || !value.scope_tuple || !value.expected) throw new Error('PURNA_COLLECTION_CASE_INVALID')
  return {
    id: value.case_id,
    question: value.question,
    scope_tuple: value.scope_tuple as Record<string, unknown>,
    requiredDimensions: value.required_dimensions,
    expected: value.expected,
  }
}
function bearer(): string {
  const value = process.env.MARSYS_MCP_KEY ?? process.env.MCP_SMOKE_BEARER_TOKEN
  if (value) return value
  try {
    const resolved = execFileSync('gcloud', ['secrets', 'versions', 'access', 'latest', '--secret=mcp-canary-key', '--project=madhav-astrology'], { encoding: 'utf8' }).trim()
    if (resolved) return resolved
  } catch { /* Deliberately do not report credential-provider output. */ }
  throw new Error('PURNA_COLLECTION_MCP_CREDENTIAL_UNAVAILABLE')
}
export interface CollectionDependencies {
  readonly createMcp?: (url: string, token: string) => Pick<McpClient, 'init' | 'callTool'>
  readonly mintSession?: (serviceUrl: string, uid: string, signal: AbortSignal) => Promise<string>
}
export async function collect(config: Config, cases: readonly AcceptanceCase[], dependencies: CollectionDependencies = {}): Promise<readonly CollectedCase[]> {
  const mcp = (dependencies.createMcp ?? ((url, token) => new McpClient(url, token)))(config.mcp_url, bearer())
  let mcpPreflight: 'timeout' | 'error' | null = null
  try { await withMcpDeadline((signal) => mcp.init(signal), config.mcp_timeout_ms ?? 90_000) } catch (error) { mcpPreflight = error instanceof McpRequestDeadlineError ? 'timeout' : 'error' }
  const invoker = { call: async (name: string, args: Record<string, unknown>) => {
    if (mcpPreflight) return mcpPreflight === 'timeout' ? { __purna_timeout: true } : { __purna_tool_error: true }
    try {
      const outcome = await withMcpDeadline((signal) => mcp.callTool(name, args, signal), config.mcp_timeout_ms ?? 90_000)
      return outcome.isToolError ? { __purna_tool_error: true } : outcome.content
    } catch (error) {
      return error instanceof McpRequestDeadlineError ? { __purna_timeout: true } : { __purna_tool_error: true }
    }
  } }
  let sessionCookie: string | null = null
  let sessionDiagnostic: string | undefined
  try {
    sessionCookie = await withMcpDeadline(
      (signal) => (dependencies.mintSession ?? mintFreshProbeSessionCookie)(config.portal_url, process.env.PROBE_UID ?? 'probe-service-account', signal),
      config.portal_timeout_ms ?? 180_000,
    )
  } catch (error) { sessionDiagnostic = error instanceof McpRequestDeadlineError ? 'PORTAL_SESSION_MINT_DEADLINE' : 'PORTAL_SESSION_MINT_FAILED' }
  const rows: CollectedCase[] = []
  for (const test of cases) {
    rows.push(await collectPortalCase({ test, expectedRevision: config.expected_revision, source: config.environment, chartId: config.chart_id, endpoint: config.portal_url, sessionCookie, sessionDiagnostic, timeoutMs: config.portal_timeout_ms }))
    rows.push(await collectManagedCase({ test, expectedRevision: config.expected_revision, source: config.environment, chartId: config.chart_id, invoker, maxPolls: config.max_polls ?? 30, wait: () => new Promise((done) => setTimeout(done, 1000)) }))
    rows.push(await collectRawCase({ test, expectedRevision: config.expected_revision, source: config.environment, chartId: config.chart_id, invoker, maxActions: config.max_actions ?? 64, synthesize: synthesizeRawLifecycleEvidence }))
  }
  return rows
}
export async function main(argv = process.argv.slice(2)): Promise<void> {
  const args = new Map<string, string>(); for (let index = 0; index < argv.length; index += 2) if (argv[index]?.startsWith('--') && argv[index + 1] && !args.has(argv[index]!)) args.set(argv[index]!, argv[index + 1]!); else throw new Error('PURNA_COLLECTION_CLI_INVALID')
  if ([...args.keys()].some((flag) => !['--suite', '--config', '--artifact-dir', '--case'].includes(flag))) throw new Error('PURNA_COLLECTION_CLI_INVALID')
  const suite = args.get('--suite'); const configPath = args.get('--config'); const artifactDir = args.get('--artifact-dir'); const caseId = args.get('--case'); if (!['beyond_acarya', 'product'].includes(String(suite)) || !configPath || !artifactDir || args.size < 3 || args.size > 4) throw new Error('PURNA_COLLECTION_CLI_REQUIRED_ARGUMENT_MISSING')
  const protocolPath = new URL('../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PRODUCT_ACCEPTANCE_PROTOCOL_v2.json', import.meta.url)
  const protocol = validateProtocol(JSON.parse(await readFile(protocolPath, 'utf8')))
  const sourceCases = casesForSuite(protocol, suite as AcceptanceSuite)
  const selected = caseId ? sourceCases.filter((item) => item.case_id === caseId) : sourceCases
  if (!selected.length) throw new Error('PURNA_COLLECTION_CASE_UNKNOWN')
  const config = parseConfig(JSON.parse(await readFile(configPath, 'utf8'))); const rows = await collect(config, selected.map(asCase)); const invalid = rows.filter((row) => { try { assertLiveEvidence(row); return false } catch { return true } })
  const artifact = createCollectionArtifact({
    suite: suite as AcceptanceSuite,
    environment: config.environment,
    expectedRevision: config.expected_revision,
    authorizationApprovalId: config.authorization_approval_id,
    caseInputs: selected,
    rows,
  })
  const directory = resolve(artifactDir); await mkdir(directory, { recursive: true }); const path = resolve(directory, `collection-${new Date().toISOString().replace(/[:.]/g, '-')}.json`); await writeFile(path, `${JSON.stringify(artifact, null, 2)}\n`, { flag: 'wx' }); process.stdout.write(`${JSON.stringify({ path, collection_hash: artifact.collection_hash, rows: rows.length, accepted: rows.length - invalid.length, rejected: invalid.length })}\n`); if (invalid.length) throw new Error('PURNA_COLLECTION_INCOMPLETE')
}
if (import.meta.url === `file://${process.argv[1]}`) main().catch((error: unknown) => { process.stderr.write(`${error instanceof Error ? error.message : 'PURNA_COLLECTION_FAILED'}\n`); process.exitCode = 1 })
