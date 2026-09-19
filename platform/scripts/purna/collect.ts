import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { execFileSync } from 'node:child_process'
import { McpClient } from '../audit/doctrine_harness/lib/mcp_client'
import { mintFreshProbeSessionCookie } from '../probe/session_auth'
import { collectManagedCase, collectPortalCase, collectRawCase } from './channel_clients'
import { synthesizeRawLifecycleEvidence } from './raw_external_synthesis'
import { casesForSuite, validateProtocol, type AcceptanceCaseInput, type AcceptanceSuite } from './acceptance_cases'
import { assertLiveEvidence, createCollectionArtifact, type AcceptanceCase, type CollectedCase } from './collection_types'

interface Config { schema_version: 'purna-collection-config/v1'; environment: 'candidate' | 'live'; expected_revision: string; chart_id: string; portal_url: string; mcp_url: string; authorization_approval_id: string; max_polls?: number; max_actions?: number; portal_timeout_ms?: number; mcp_timeout_ms?: number }
class McpRequestDeadlineError extends Error { constructor() { super('PURNA_COLLECTION_MCP_REQUEST_DEADLINE') } }
async function withMcpDeadline<T>(operation: Promise<T>, timeoutMs: number): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined
  try {
    return await Promise.race([
      operation,
      new Promise<T>((_resolve, reject) => { timer = setTimeout(() => reject(new McpRequestDeadlineError()), timeoutMs) }),
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
export async function collect(config: Config, cases: readonly AcceptanceCase[]): Promise<readonly CollectedCase[]> {
  const mcp = new McpClient(config.mcp_url, bearer()); await mcp.init()
  const invoker = { call: async (name: string, args: Record<string, unknown>) => {
    try {
      const outcome = await withMcpDeadline(mcp.callTool(name, args), config.mcp_timeout_ms ?? 90_000)
      return outcome.isToolError ? { __purna_tool_error: true } : outcome.content
    } catch (error) {
      return error instanceof McpRequestDeadlineError ? { __purna_timeout: true } : { __purna_tool_error: true }
    }
  } }
  const sessionCookie = await mintFreshProbeSessionCookie(config.portal_url, process.env.PROBE_UID ?? 'probe-service-account')
  const rows: CollectedCase[] = []
  for (const test of cases) {
    rows.push(await collectPortalCase({ test, expectedRevision: config.expected_revision, source: config.environment, chartId: config.chart_id, endpoint: config.portal_url, sessionCookie, timeoutMs: config.portal_timeout_ms }))
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
