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
// W5 Lane L4 ("tool-search metadata"): the search-index derivation lives in
// src/lib (not here) because the LIVE `tool_search` capability
// (layers/L0_brahmagyan/tool_search.ts) needs it too, and the live serving
// path must never reach into scripts/ (this is the same directional rule the
// module doc above states for getCatalog()/CONTRACT_CATALOG — scripts/ imports
// FROM src/lib, never the reverse). Re-exported here so both the CLI generator
// below and the CI parity test have one import path for all five projections.
export {
  buildToolSearchIndex,
  buildToolSearchIndexEntry,
  searchToolIndex,
  tokenize as toolSearchTokenize,
  MCP_NATIVE_DISCOVERY_ENTRIES,
  type ToolSearchIndexEntry,
  type ToolSearchMatch,
  type ToolSearchResult,
} from '../../src/lib/retrieval/registry/tool_search'

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

// ── MCP-spec tool annotations (W5 lane L3) ───────────────────────────────────
// RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §E W5 standing scope: "annotations
// + family_overrides + input_examples/search_result emissions". Field names below
// are the REAL MCP SDK `ToolAnnotations` shape (verified against this repo's
// installed `@modelcontextprotocol/sdk@1.29.0` `ToolAnnotationsSchema` —
// `title`/`readOnlyHint`/`destructiveHint`/`idempotentHint`/`openWorldHint` — not
// guessed). Derived from the REAL `cap.annotations` field (types.ts, populated
// 118/118 by the W2 descriptor-migration backfill per STATE.md) — this lane does
// not invent a second annotation classification, it projects the existing one
// into the wire-protocol shape no generated surface emitted before this lane
// (the pre-existing `read_only`/`destructive` ad-hoc fields on ChatToolDef/
// McpToolRegistration used the registry's OWN field names, not the MCP spec's
// Hint-suffixed ones a real `server.tool(..., annotations, ...)` call needs).

export interface McpToolAnnotations {
  title?: string
  readOnlyHint?: boolean
  destructiveHint?: boolean
  idempotentHint?: boolean
  openWorldHint?: boolean
}

/**
 * Project `cap.annotations` (+ `cap.display.short_label` as the optional
 * spec `title` hint) into the real MCP `ToolAnnotations` shape. Omits a key
 * entirely when the source field is undefined — MCP annotations are optional
 * hints; emitting `false` where the registry has never classified the
 * capability would fabricate a claim ("this is definitely not destructive")
 * the registry never made. Since W2 backfilled `annotations` on all 118 live
 * capabilities, this is non-empty for the overwhelming majority in practice.
 */
export function buildMcpAnnotations(cap: CapabilityDescriptor): McpToolAnnotations {
  const a = cap.annotations
  const out: McpToolAnnotations = {}
  if (cap.display?.short_label) out.title = cap.display.short_label
  if (a?.read_only !== undefined) out.readOnlyHint = a.read_only
  if (a?.destructive !== undefined) out.destructiveHint = a.destructive
  if (a?.idempotent !== undefined) out.idempotentHint = a.idempotent
  if (a?.open_world !== undefined) out.openWorldHint = a.open_world
  return out
}

// ── Per-family serving overrides (`family_overrides`) + input_examples/
// search_result emissions (W5 lane L3) ───────────────────────────────────────
// types.ts's `family_overrides` field (R-1.1, amendment_version 2) is 0/118
// populated on the live registry — deliberately, per the W2 descriptor-
// migration lane's own note ("both require genuine per-capability editorial
// judgment... left for a future, explicitly-scoped editorial wave"). That
// ruling stands; this lane does NOT author editorial override content. What
// this lane DOES build is the EMISSION mechanism the brief's W5 standing scope
// line asks for: a pure function that, for a given model family, merges any
// declared `family_overrides[family]` onto the base descriptor and emits the
// resulting per-family tool-def shape — so the day an editorial wave populates
// `description_override`/`name_override`/`strict_schema`/`input_examples`/
// `search_result_content_block` on any capability, the served per-family
// projection picks it up with zero code changes. Verified against the REAL
// live registry (currently 0 overrides — every family's projection is
// mechanically identical to the base chat projection today, which is the
// CORRECT and expected output, not a bug) plus unit tests that construct
// real (test-local) override objects to exercise every merge path.

export type ModelFamily = 'anthropic' | 'gemini' | 'openai' | 'deepseek'

export const MODEL_FAMILIES: readonly ModelFamily[] = ['anthropic', 'gemini', 'openai', 'deepseek']

export interface FamilyToolDef {
  family: ModelFamily
  /** `name_override` applied if declared, else the base capability name. */
  name: string
  /** `description_override` applied if declared, else the base description. */
  description: string
  /** Base `input_schema`, with the OpenAI strict-mode transform applied iff `strict_schema` is set. */
  input_schema: Record<string, unknown>
  uri: string
  layer: string
  annotations: McpToolAnnotations
  /** True iff this family's override declares `strict_schema: true`. */
  strict_schema: boolean
  /** Few-shot `input_examples`, verbatim from the override, or null if none declared. */
  input_examples: Array<Record<string, unknown>> | null
  /** True iff this family's override opts into MCP `search_result` content-block framing. */
  search_result_content_block: boolean
  /** True iff `cap.family_overrides?.[family]` is declared at all (any field). */
  has_override: boolean
  name_overridden: boolean
  description_overridden: boolean
}

/**
 * OpenAI structured-output strict-mode transform (per `FamilyOverrideSpec.
 * strict_schema`'s own doc comment: "additionalProperties:false, all-required").
 * A mechanical JSON-Schema transform derived from the schema's OWN declared
 * properties — it does not invent constraints or content, it tightens an
 * already-real schema per OpenAI's documented strict-mode contract.
 */
export function applyStrictSchemaTransform(schema: Record<string, unknown>): Record<string, unknown> {
  const properties = (schema['properties'] ?? {}) as Record<string, unknown>
  return {
    ...schema,
    properties,
    additionalProperties: false,
    required: Object.keys(properties),
  }
}

export function buildFamilyToolDef(cap: CapabilityDescriptor, family: ModelFamily): FamilyToolDef {
  const override = cap.family_overrides?.[family]
  const baseDescription = cap.display?.full_description ?? cap.description
  const description = override?.description_override ?? baseDescription
  const name = override?.name_override ?? cap.name
  const strict = override?.strict_schema === true
  let inputSchema = toJsonSchema(cap.input_schema, cap.required_inputs)
  if (strict) inputSchema = applyStrictSchemaTransform(inputSchema)
  return {
    family,
    name,
    description,
    input_schema: inputSchema,
    uri: cap.uri,
    layer: cap.layer,
    annotations: buildMcpAnnotations(cap),
    strict_schema: strict,
    input_examples: override?.input_examples ?? null,
    search_result_content_block: override?.search_result_content_block === true,
    has_override: override !== undefined,
    name_overridden: override?.name_override !== undefined,
    description_overridden: override?.description_override !== undefined,
  }
}

/** Same population as (a) chat tool defs (type=tool + `chat` projection_tag) — family
 * overrides are an LLM function-calling concern, the same surface `family_overrides`'
 * own doc comment cites ("MARO reads these to shape... per model family"). */
export function buildFamilyToolDefs(caps: CapabilityDescriptor[], family: ModelFamily): FamilyToolDef[] {
  return caps
    .filter((c) => resolveType(c) === 'tool' && hasTag(c, 'chat'))
    .map((c) => buildFamilyToolDef(c, family))
    .sort((a, b) => a.name.localeCompare(b.name))
}

export function buildAllFamilyToolDefs(caps: CapabilityDescriptor[]): Record<ModelFamily, FamilyToolDef[]> {
  const out = {} as Record<ModelFamily, FamilyToolDef[]>
  for (const family of MODEL_FAMILIES) out[family] = buildFamilyToolDefs(caps, family)
  return out
}

/**
 * Honest collision report: if a future editorial wave sets `name_override` on
 * two capabilities to the same string for one family, that family's tool-def
 * set would no longer have unique names (an MCP/function-calling requirement).
 * Reports collisions rather than silently de-duping or crashing — mirrors this
 * codebase's "honest report, not narrowed to hide false positives" convention.
 */
export function findFamilyNameCollisions(defs: FamilyToolDef[]): string[] {
  const counts = new Map<string, number>()
  for (const d of defs) counts.set(d.name, (counts.get(d.name) ?? 0) + 1)
  return [...counts.entries()]
    .filter(([, n]) => n > 1)
    .map(([name]) => name)
    .sort()
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
  /**
   * MCP-spec-shaped tool annotations (W5 lane L3 — see `buildMcpAnnotations()`
   * above). Additive alongside the pre-existing `read_only`/`destructive`
   * fields (kept for backward compat with existing consumers); this is the
   * first emission of the full readOnlyHint/destructiveHint/idempotentHint/
   * openWorldHint shape a real MCP client's approval flow reads.
   */
  annotations: McpToolAnnotations
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
    annotations: buildMcpAnnotations(cap),
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
  /** MCP-spec-shaped tool annotations (W5 lane L3) — see `buildMcpAnnotations()`. */
  annotations: McpToolAnnotations
}

export function buildMcpToolRegistration(cap: CapabilityDescriptor): McpToolRegistration {
  return {
    tool_name: cap.name,
    description: cap.display?.full_description ?? cap.description,
    input_schema: toJsonSchema(cap.input_schema, cap.required_inputs),
    uri: cap.uri,
    layer: cap.layer,
    name_valid: MCP_NAME_PATTERN.test(cap.name),
    annotations: buildMcpAnnotations(cap),
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
