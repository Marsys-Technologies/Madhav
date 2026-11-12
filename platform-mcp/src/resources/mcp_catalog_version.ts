/** Request-scoped served tools/list metadata. Generated retrieval facts remain separate. */
import { createHash } from 'node:crypto'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { normalizeObjectSchema } from '@modelcontextprotocol/sdk/server/zod-compat.js'
import { toJsonSchemaCompat } from '@modelcontextprotocol/sdk/server/zod-json-schema-compat.js'
import { ListToolsResultSchema, type Tool } from '@modelcontextprotocol/sdk/types.js'
import {
  MCP_SURFACE_PROFILES,
  MCP_SURFACE_PROFILES_GENERATED_AT,
} from '../generated/mcp_surface_profiles.generated.js'

export const RETRIEVAL_REGISTRY_PROFILE_TOTAL = MCP_SURFACE_PROFILES.full.total
export const RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT = MCP_SURFACE_PROFILES_GENERATED_AT
export const MCP_CATALOG_TOOLS_CHANGED_AT = null
export const MCP_CATALOG_TOOLS_CHANGED_AT_NOTE =
  'No attributable served-catalog change timestamp is recorded. Compare catalog_version; ' +
  'generated-manifest, deployment and process times are not served-catalog change times.'
export const SERVED_CATALOG_UNAVAILABLE = 'SERVED_CATALOG_UNAVAILABLE'

const UNAVAILABLE = { ok: false as const, code: SERVED_CATALOG_UNAVAILABLE }
export type ServedCatalogSnapshot =
  | { ok: true; tools: Tool[]; count: number; version: string }
  | typeof UNAVAILABLE
export type ServedCatalogReader = () => ServedCatalogSnapshot

/** Exact SDK1.29 registered-tool descriptor projection; callbacks/context are never read. */
interface RegisteredToolDescriptor {
  enabled: boolean
  title?: string
  description?: string
  inputSchema?: Parameters<typeof normalizeObjectSchema>[0]
  outputSchema?: Parameters<typeof normalizeObjectSchema>[0]
  annotations?: Tool['annotations']
  execution?: Tool['execution']
  _meta?: Tool['_meta']
}

function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical)
  if (value !== null && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
      .map(([key, child]) => [key, canonical(child)]))
  }
  return value
}

export function captureServedCatalog(server: McpServer): ServedCatalogSnapshot {
  try {
    const registry = (server as unknown as {
      _registeredTools?: Record<string, RegisteredToolDescriptor>
    })._registeredTools
    if (!registry || typeof registry !== 'object' || Array.isArray(registry) ||
      (Object.getPrototypeOf(registry) !== Object.prototype && Object.getPrototypeOf(registry) !== null)) return UNAVAILABLE
    const tools: unknown[] = []
    for (const [name, tool] of Object.entries(registry)) {
      if (!tool || typeof tool !== 'object' || Array.isArray(tool) || typeof tool.enabled !== 'boolean') return UNAVAILABLE
      if (!tool.enabled) continue
      const input = normalizeObjectSchema(tool.inputSchema)
      const descriptor: Record<string, unknown> = {
        name, title: tool.title, description: tool.description,
        inputSchema: input
          ? toJsonSchemaCompat(input, { strictUnions: true, pipeStrategy: 'input' })
          : { type: 'object', properties: {} },
        annotations: tool.annotations, execution: tool.execution, _meta: tool._meta,
      }
      if (tool.outputSchema) {
        const output = normalizeObjectSchema(tool.outputSchema)
        if (output) descriptor.outputSchema = toJsonSchemaCompat(output, { strictUnions: true, pipeStrategy: 'output' })
      }
      tools.push(descriptor)
    }
    // Match real JSON wire omission/null semantics; reject callbacks and non-JSON public values.
    const wire = JSON.parse(JSON.stringify({ tools }, (_key, value: unknown) => {
      if (typeof value === 'function' || typeof value === 'symbol' || typeof value === 'bigint') {
        throw new Error(SERVED_CATALOG_UNAVAILABLE)
      }
      return value
    })) as { tools: Tool[] }
    if (!ListToolsResultSchema.safeParse(wire).success) return UNAVAILABLE
    if (new Set(wire.tools.map(tool => tool.name)).size !== wire.tools.length) return UNAVAILABLE
    const sorted = [...wire.tools].sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0)
    const hash = createHash('sha256').update(JSON.stringify(canonical(sorted))).digest('hex')
    return { ok: true, tools: wire.tools, count: wire.tools.length, version: `catalog-2+t${wire.tools.length}+s${hash}` }
  } catch {
    return UNAVAILABLE
  }
}

/** Metadata registers before the profile gate, but cannot observe an unfinished bootstrap. */
export function createRequestServedCatalogReader(server: McpServer): {
  read: ServedCatalogReader
  markRegistrationComplete: () => void
} {
  let ready = false
  return {
    read: () => ready ? captureServedCatalog(server) : UNAVAILABLE,
    markRegistrationComplete: () => { ready = true },
  }
}

export interface ServedToolCensus { count: number | null; names: string[]; note: string }
export function censusServedTools(server: McpServer): ServedToolCensus {
  const snapshot = captureServedCatalog(server)
  return snapshot.ok
    ? { count: snapshot.count, names: snapshot.tools.map(tool => tool.name).sort(), note: 'Exact SDK1.29 public tools/list projection after request gates; profile-scoped.' }
    : { count: null, names: [], note: 'Served catalog unavailable; never fabricated or replaced by generated retrieval metadata.' }
}

/** Await public SDK submission; fulfillment does not establish delivery or a host relist. */
export async function notifyIfCatalogStale(
  clientVersion: string | undefined,
  snapshot: Extract<ServedCatalogSnapshot, { ok: true }>,
  server?: McpServer,
): Promise<{ live: string; stale: boolean; notified: boolean }> {
  const stale = typeof clientVersion === 'string' && clientVersion.length > 0 && clientVersion !== snapshot.version
  let notified = false
  if (stale && server) {
    try {
      if (server.isConnected()) {
        await server.server.sendToolListChanged()
        notified = true
      }
    } catch {
      // Snapshot/cache truth survives a disconnected or rejected notification submission.
    }
  }
  return { live: snapshot.version, stale, notified }
}
