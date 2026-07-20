/**
 * projection_builders.ts — R-1 projection compiler, pure derivation logic
 * ================================================================================
 * Retrieval Plane Elevation, plan §3 R-1 item 2 ("Build the projection compiler").
 * ADDITIVE ONLY: nothing here is imported by any live-serving path. This module
 * exports pure functions over the REAL `getCatalog()` registry (no DB, no fs) so
 * both the CLI generator (`generate_projections.ts`, writes artifacts to disk)
 * AND the CI parity test (`projection_compiler_parity.test.ts`, asserts
 * completeness/validity in-memory) call the SAME derivation code — the r5
 * codegen-parity discipline (`platform-mcp/src/__tests__/r5_codegen_parity.test.ts`):
 * one source, tested directly, not re-derived by the test.
 *
 * FOUR PROJECTIONS (plan §3 R-1 item 2 a–d), each a pure function over
 * `CapabilityDescriptor[]`:
 *   (a) buildChatToolDefs   — chat tool-def projection (§R-1.2a)
 *   (b) buildMcpToolRegistrations — MCP tool-registration projection (§R-1.2b)
 *   (c) buildMachineCensus  — machine-readable census, every field (§R-1.2d)
 *   (d) buildDocsResourceCatalog — marsys://resource/catalog shape (§R-1.2e)
 *
 * SCOPE NOTE — projection selection uses the REAL `projection_tags` field the
 * W2 descriptor-migration lane already populated on 118/120 live capabilities
 * (see STATE.md "W2 — Lane: Descriptor migration"). This compiler does not
 * invent a second classification; it reads the one the registry already
 * declares. The 2 capabilities with `projection_tags` left `undefined`
 * (`channel/chat_dispatch`, `channel/mcp_wiring` — internal introspection,
 * per that lane's own note) are correctly excluded from ALL FOUR projections
 * below, not silently included with a guessed tag.
 *
 * TYPE-RESOLUTION NOTE (real finding, not fabricated): 6/120 live capabilities
 * (the 4 sidecar-backed L0 ephemeris/sutravali `query_*`/`ephemeris_cache_*`
 * tools registered via the OLDER narrowed `ToolCapability`/`ResourceCapability`
 * shape) carry `primitive_type` instead of the main `CapabilityDescriptor`'s
 * `type` field — `cap.type` is `undefined` for these six. `resolveType()`
 * below falls back to `primitive_type` so no capability silently drops out of
 * the census; this is flagged, not fixed (fixing the registration shape is
 * out of this lane's additive-only scope and touches files this lane does not
 * own).
 */
import type {
  CapabilityDescriptor,
  InputSchema,
  ParameterSchema,
} from '../../src/lib/retrieval/registry/types'

// ── Shared helpers ──────────────────────────────────────────────────────────

/** MCP tool-naming rule per registry_bridge.ts's own header doc: snake_case, no hyphens, ≤64 chars. */
export const MCP_NAME_PATTERN = /^[a-z0-9_]{1,64}$/

/**
 * Resolve a capability's primitive type, tolerating the 6 live capabilities
 * registered via the older narrowed shape (`primitive_type` instead of `type`
 * — see module doc comment). Never returns undefined/blank; falls back to
 * `'unknown'` only if BOTH fields are absent (should not happen on any real
 * registered capability; asserted against in the parity test).
 */
export function resolveType(cap: CapabilityDescriptor): string {
  const anyCap = cap as unknown as { type?: string; primitive_type?: string }
  return anyCap.type ?? anyCap.primitive_type ?? 'unknown'
}

/** JSON-Schema-shaped node for one ParameterSchema entry (recursive for array/object). */
function paramToJsonSchemaNode(param: ParameterSchema): Record<string, unknown> {
  const node: Record<string, unknown> = { type: param.type }
  if (param.description) node['description'] = param.description
  if (param.enum) node['enum'] = param.enum
  if (param.default !== undefined) node['default'] = param.default
  if (param.type === 'array' && param.items) node['items'] = paramToJsonSchemaNode(param.items)
  if (param.type === 'object' && param.properties) {
    node['properties'] = Object.fromEntries(
      Object.entries(param.properties).map(([k, v]) => [k, paramToJsonSchemaNode(v)]),
    )
  }
  return node
}

/**
 * `CapabilityDescriptor.input_schema` (a `Record<string, ParameterSchema>`) is
 * already JSON-Schema-shaped per-field (type/description/enum/items/properties)
 * — this wraps it in the standard `{type:'object', properties, required}`
 * envelope. Not a fabrication: every field it emits traces to a real
 * ParameterSchema property; nothing is invented (no numeric min/max bounds
 * exist on ParameterSchema, so none are emitted — same "don't invent
 * constraints the descriptor doesn't declare" discipline `generate_registry_shims.ts`
 * documents for the same underlying gap).
 */
export function toJsonSchema(input?: InputSchema, required?: string[]): Record<string, unknown> {
  const properties: Record<string, unknown> = {}
  if (input) {
    for (const [key, param] of Object.entries(input)) {
      properties[key] = paramToJsonSchemaNode(param)
    }
  }
  const schema: Record<string, unknown> = { type: 'object', properties }
  if (required && required.length > 0) schema['required'] = [...required]
  return schema
}

function hasTag(cap: CapabilityDescriptor, tag: 'chat' | 'mcp_full' | 'mcp_compact' | 'mcp_consult'): boolean {
  return (cap.projection_tags ?? []).includes(tag)
}

// ── (c) Machine census — every capability, every declared field ─────────────

export interface MachineCensusEntry {
  uri: string
  type: string
  layer: string
  name: string
  scope: string
  archetype: string
  traversal_level: string
  tool_role: string
  data_source: string | null
  mutation: boolean | null
  emits_references: boolean
  lel_capable: boolean
  calibration_context_only: boolean
  bearing_first: boolean
  required_inputs: string[]
  input_param_count: number
  projection_tags: string[]
  short_label: string | null
  one_line: string | null
  read_only: boolean | null
  destructive: boolean | null
  open_world: boolean | null
  has_density_contract: boolean
  has_output_schema: boolean
  has_family_overrides: boolean
  has_register_glossary: boolean
  has_drill_children: boolean
}

export function buildMachineCensusEntry(cap: CapabilityDescriptor): MachineCensusEntry {
  return {
    uri: cap.uri,
    type: resolveType(cap),
    layer: cap.layer,
    name: cap.name,
    scope: cap.scope,
    archetype: cap.archetype,
    traversal_level: cap.traversal_level,
    tool_role: cap.tool_role,
    data_source: cap.data_source ?? null,
    mutation: cap.mutation ?? null,
    emits_references: cap.emits_references,
    lel_capable: cap.lel_capable,
    calibration_context_only: cap.calibration_context_only === true,
    bearing_first: cap.demand_ranking?.bearing_first === true,
    required_inputs: cap.required_inputs ?? [],
    input_param_count: cap.input_schema ? Object.keys(cap.input_schema).length : 0,
    projection_tags: cap.projection_tags ?? [],
    short_label: cap.display?.short_label ?? null,
    one_line: cap.display?.one_line ?? null,
    read_only: cap.annotations?.read_only ?? null,
    destructive: cap.annotations?.destructive ?? null,
    open_world: cap.annotations?.open_world ?? null,
    has_density_contract: cap.density_contract !== undefined,
    has_output_schema: cap.output_schema !== undefined,
    has_family_overrides: cap.family_overrides !== undefined,
    has_register_glossary: (cap.register?.glossary ? Object.keys(cap.register.glossary).length : 0) > 0,
    has_drill_children: (cap.drill_children?.length ?? 0) > 0,
  }
}

export interface MachineCensus {
  generated_at: string
  generator: string
  generator_version: string
  source: string
  total: number
  entries: MachineCensusEntry[]
  summary: {
    by_layer: Record<string, number>
    by_type: Record<string, number>
    by_scope: Record<string, number>
    by_archetype: Record<string, number>
    by_tool_role: Record<string, number>
    by_data_source: Record<string, number>
    by_projection_tag: Record<string, number>
    no_projection_tags: string[]
    type_resolved_via_primitive_type_fallback: string[]
  }
}

function tally(values: string[]): Record<string, number> {
  const out: Record<string, number> = {}
  for (const v of values) out[v] = (out[v] ?? 0) + 1
  return out
}

export function buildMachineCensus(caps: CapabilityDescriptor[], generatedAt: string = new Date().toISOString()): MachineCensus {
  const entries = caps.map(buildMachineCensusEntry).sort((a, b) => a.uri.localeCompare(b.uri))
  const tagCounts: Record<string, number> = {}
  for (const e of entries) for (const t of e.projection_tags) tagCounts[t] = (tagCounts[t] ?? 0) + 1
  return {
    generated_at: generatedAt,
    generator: 'generate_projections.ts',
    generator_version: '1.0',
    source: 'getCatalog() (platform/src/lib/retrieval/registry/catalog.ts) — live registry, no DB read',
    total: entries.length,
    entries,
    summary: {
      by_layer: tally(entries.map((e) => e.layer)),
      by_type: tally(entries.map((e) => e.type)),
      by_scope: tally(entries.map((e) => e.scope)),
      by_archetype: tally(entries.map((e) => e.archetype)),
      by_tool_role: tally(entries.map((e) => e.tool_role)),
      by_data_source: tally(entries.map((e) => e.data_source ?? 'undeclared')),
      by_projection_tag: tagCounts,
      no_projection_tags: entries.filter((e) => e.projection_tags.length === 0).map((e) => e.uri),
      type_resolved_via_primitive_type_fallback: caps
        .filter((c) => (c as unknown as { type?: string }).type === undefined)
        .map((c) => c.uri)
        .sort(),
    },
  }
}

// ── (a) Chat tool-def projection ─────────────────────────────────────────────
// Scoped to type === 'tool' capabilities carrying the 'chat' projection_tag —
// resources/prompts don't have a chat function-calling analog in this
// codebase's TOOL_CONTRACTS shape (see comparison report for the honest count
// of resources/prompts this excludes, not silently folded in).

export interface ChatToolDef {
  name: string
  description: string
  input_schema: Record<string, unknown>
  uri: string
  layer: string
  read_only: boolean | null
  destructive: boolean | null
}

export function buildChatToolDef(cap: CapabilityDescriptor): ChatToolDef {
  return {
    name: cap.name,
    description: cap.display?.full_description ?? cap.description,
    input_schema: toJsonSchema(cap.input_schema, cap.required_inputs),
    uri: cap.uri,
    layer: cap.layer,
    read_only: cap.annotations?.read_only ?? null,
    destructive: cap.annotations?.destructive ?? null,
  }
}

export function buildChatToolDefs(caps: CapabilityDescriptor[]): ChatToolDef[] {
  return caps
    .filter((c) => resolveType(c) === 'tool' && hasTag(c, 'chat'))
    .map(buildChatToolDef)
    .sort((a, b) => a.name.localeCompare(b.name))
}

// ── (b) MCP tool-registration projection ─────────────────────────────────────
// Scoped to type === 'tool' capabilities carrying the 'mcp_full' projection_tag
// — the surface a `server.tool(name, description, schema, handler)` loop would
// register 1:1. Resources/prompts with mcp_full/mcp_compact/mcp_consult tags
// would map to server.resource()/server.prompt() instead — reported as a
// separate, honest count (`mcp_resource_registrations`/`mcp_prompt_registrations`
// below), never silently coerced into a tool-shaped entry.

export interface McpToolRegistration {
  tool_name: string
  description: string
  input_schema: Record<string, unknown>
  uri: string
  layer: string
  name_valid: boolean
}

export function buildMcpToolRegistration(cap: CapabilityDescriptor): McpToolRegistration {
  return {
    tool_name: cap.name,
    description: cap.display?.full_description ?? cap.description,
    input_schema: toJsonSchema(cap.input_schema, cap.required_inputs),
    uri: cap.uri,
    layer: cap.layer,
    name_valid: MCP_NAME_PATTERN.test(cap.name),
  }
}

export function buildMcpToolRegistrations(caps: CapabilityDescriptor[]): McpToolRegistration[] {
  return caps
    .filter((c) => resolveType(c) === 'tool' && hasTag(c, 'mcp_full'))
    .map(buildMcpToolRegistration)
    .sort((a, b) => a.tool_name.localeCompare(b.tool_name))
}

export interface McpNonToolRegistration {
  uri: string
  type: string
  name: string
  projection_tags: string[]
}

/** Honest accounting of mcp_full/mcp_compact/mcp_consult-tagged resources/prompts NOT in buildMcpToolRegistrations. */
export function buildMcpNonToolRegistrations(caps: CapabilityDescriptor[]): McpNonToolRegistration[] {
  return caps
    .filter((c) => resolveType(c) !== 'tool' && (hasTag(c, 'mcp_full') || hasTag(c, 'mcp_compact') || hasTag(c, 'mcp_consult')))
    .map((c) => ({ uri: c.uri, type: resolveType(c), name: c.name, projection_tags: c.projection_tags ?? [] }))
    .sort((a, b) => a.uri.localeCompare(b.uri))
}

// ── (d) Docs resource stub — marsys://resource/catalog shape ────────────────

export interface DocsCatalogEntry {
  uri: string
  type: string
  layer: string
  name: string
  short_label: string | null
  one_line: string | null
  scope: string
  archetype: string
  tool_role: string
  projection_tags: string[]
}

export interface DocsResourceCatalog {
  uri: 'marsys://resource/catalog'
  mime_type: 'application/json'
  generated_at: string
  total: number
  capabilities: DocsCatalogEntry[]
  summary: {
    by_layer: Record<string, number>
    by_type: Record<string, number>
  }
}

export function buildDocsResourceCatalog(
  caps: CapabilityDescriptor[],
  generatedAt: string = new Date().toISOString(),
): DocsResourceCatalog {
  const capabilities: DocsCatalogEntry[] = caps
    .map((c) => ({
      uri: c.uri,
      type: resolveType(c),
      layer: c.layer,
      name: c.name,
      short_label: c.display?.short_label ?? null,
      one_line: c.display?.one_line ?? null,
      scope: c.scope,
      archetype: c.archetype,
      tool_role: c.tool_role,
      projection_tags: c.projection_tags ?? [],
    }))
    .sort((a, b) => a.uri.localeCompare(b.uri))
  return {
    uri: 'marsys://resource/catalog',
    mime_type: 'application/json',
    generated_at: generatedAt,
    total: capabilities.length,
    capabilities,
    summary: {
      by_layer: tally(capabilities.map((c) => c.layer)),
      by_type: tally(capabilities.map((c) => c.type)),
    },
  }
}
