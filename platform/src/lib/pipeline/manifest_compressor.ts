/**
 * manifest_compressor.ts — compresses CAPABILITY_MANIFEST.json entries marked
 * `expose_to_planner: true` into the planner-ready CompressedEntry[] form.
 *
 * Pure: no filesystem access here. Callers load the manifest and pass it in.
 *
 * Output of `compressedManifestToString()` is the planner's `<manifest>` block.
 * Token budget: ≤ MANIFEST_TOKEN_BUDGET (default 12 000 tokens) for all tools
 * combined; per-tool description capped at DESCRIPTION_MAX_WORDS (default 60).
 *
 * COV-S3 cutover: filtering is now declarative (expose_to_planner === true)
 * rather than the former hardcoded PRIMARY_TOOL_NAMES list.
 */

export type TokenCostHint = 'low' | 'med' | 'hi'

export interface QuerySchema {
  type: string
  properties?: Record<string, unknown>
  required?: string[]
}

export interface CapabilityManifestEntry {
  canonical_id: string
  tool_name?: string
  tool_description?: string
  description?: string
  query_schema?: QuerySchema
  token_cost_hint?: TokenCostHint
  linked_data_asset_id?: string
  /** JSON Schema for the tool's return value (COV-S1) */
  output_schema?: Record<string, unknown>
  /** Multi-asset tools: plural companion to the singular linked_data_asset_id (COV-S1) */
  linked_data_asset_ids?: string[]
  /** When true, COV-S3 compressor includes this tool in the planner manifest (COV-S1) */
  expose_to_planner?: boolean
  /** Planner few-shot examples (COV-S1) */
  examples?: Array<{ query: string; expected_plan_fragment: string }>
  /**
   * COV-S6 R-rule migration target: gating rules expressed as typed condition/action pairs.
   * Each entry has at minimum `type` and `action`; `type: 'query_type_match'` entries
   * also carry `query_type` (the query class that triggers the constraint).
   */
  gating_constraints?: Array<{
    type: string
    action: string
    query_type?: string
    [k: string]: unknown
  }>
  [k: string]: unknown
}

export interface CapabilityManifest {
  entries: CapabilityManifestEntry[]
  [k: string]: unknown
}

export interface CompressedEntry {
  /** tool_name */
  t: string
  /** ≤60-word description (COV-S3 raised from ≤15 words) */
  d: string
  /** param names only (not full schema) */
  p: string[]
  /** token_cost_hint */
  c: TokenCostHint
  /** linked_data_asset_id (primary asset; prefer linked_data_asset_ids[] for multi-asset tools) */
  a: string
  /**
   * COV-S6: R-rule gating constraints passed through from the manifest entry.
   * Omitted when the entry has no gating_constraints (keeps the compressed output compact).
   */
  g?: CapabilityManifestEntry['gating_constraints']
}

/** Total planner manifest block token budget (W2-MANIFEST hard constraint, raised COV-S3). */
export const MANIFEST_TOKEN_BUDGET = 12_000

/** Per-tool description word cap (COV-S3 raised from 15 to 60). */
export const DESCRIPTION_MAX_WORDS = 60

/**
 * @deprecated COV-S3: compressManifest() now filters by expose_to_planner === true.
 * Retained for backward compatibility with existing tests and golden regression baselines.
 * Do not add new tools here; instead set expose_to_planner: true in manifest_overrides.yaml.
 */
export const PRIMARY_TOOL_NAMES: readonly string[] = [
  'remedial_codex_query',
  'msr_sql',
  'pattern_register',
  'contradiction_register',
  'resonance_register',
  'cluster_atlas',
  'cgm_graph_walk',
  'vector_search',
  'lel_query',
  'multi_school_signal_lookup',
  'convergence_score_lookup',
] as const

/**
 * Estimate token count using the W2-MANIFEST-fixed formula. Use this single
 * helper everywhere — do not introduce alternative estimates (B.10).
 */
export function estimateTokens(s: string): number {
  return Math.ceil(s.length / 4)
}

function pickDescription(e: CapabilityManifestEntry, maxWords = DESCRIPTION_MAX_WORDS): string {
  const candidate = (e.tool_description ?? e.description ?? '').trim()
  const words = candidate.split(/\s+/).filter(Boolean)
  return words.slice(0, maxWords).join(' ')
}

function pickParams(e: CapabilityManifestEntry): string[] {
  const props = e.query_schema?.properties ?? {}
  return Object.keys(props)
}

/**
 * Filter the manifest to entries where `expose_to_planner === true` and project
 * each into a CompressedEntry. Entries missing a `tool_name` are ignored.
 *
 * COV-S3: filtering is declarative — set expose_to_planner: true in
 * manifest_overrides.yaml to include a tool; the Manifest Builder propagates
 * it to CAPABILITY_MANIFEST.json at next CI regeneration.
 */
export function compressManifest(manifest: CapabilityManifest): CompressedEntry[] {
  const result: CompressedEntry[] = []
  for (const entry of manifest.entries ?? []) {
    if (!entry.tool_name) continue
    if (!entry.expose_to_planner) continue
    const compressed: CompressedEntry = {
      t: entry.tool_name,
      d: pickDescription(entry),
      p: pickParams(entry),
      c: (entry.token_cost_hint ?? 'med') as TokenCostHint,
      a: entry.linked_data_asset_id ?? '',
    }
    if (entry.gating_constraints && entry.gating_constraints.length > 0) {
      compressed.g = entry.gating_constraints
    }
    result.push(compressed)
  }
  return result
}

/**
 * Serialize CompressedEntry[] to a deterministic, compact JSON string for
 * inclusion in the planner system prompt. Entries are sorted by `t` so the
 * output is byte-identical for byte-identical input order is irrelevant.
 */
export function compressedManifestToString(entries: CompressedEntry[]): string {
  const sorted = [...entries].sort((a, b) => a.t.localeCompare(b.t))
  // Per-entry compact form; no whitespace; param array preserved as-given.
  return JSON.stringify(sorted)
}
