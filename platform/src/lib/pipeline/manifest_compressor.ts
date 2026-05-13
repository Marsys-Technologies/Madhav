/**
 * manifest_compressor.ts — compresses CAPABILITY_MANIFEST.json primary-tool
 * entries into the planner-ready CompressedEntry[] form.
 *
 * Pure: no filesystem access here. Callers load the manifest and pass it in.
 *
 * Output of `compressedManifestToString()` is the planner's `<manifest>` block.
 * Target: ≤3000 tokens (≤12 000 chars at the 4-chars-per-token estimate fixed
 * by W2-MANIFEST §Hard constraints) for the 8 primary tools.
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
  [k: string]: unknown
}

export interface CapabilityManifest {
  entries: CapabilityManifestEntry[]
  [k: string]: unknown
}

export interface CompressedEntry {
  /** tool_name */
  t: string
  /** ≤15-word description */
  d: string
  /** param names only (not full schema) */
  p: string[]
  /** token_cost_hint */
  c: TokenCostHint
  /** linked_data_asset_id */
  a: string
}

/**
 * The 8 primary tools the LLM-first planner is allowed to call. Listed in the
 * canonical order W2-MANIFEST AC.M.1 prescribes; `compressManifest()` emits
 * entries in this order, then `compressedManifestToString()` re-sorts
 * alphabetically for determinism.
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
] as const

/**
 * Estimate token count using the W2-MANIFEST-fixed formula. Use this single
 * helper everywhere — do not introduce alternative estimates (B.10).
 */
export function estimateTokens(s: string): number {
  return Math.ceil(s.length / 4)
}

function pickDescription(e: CapabilityManifestEntry): string {
  const candidate = (e.tool_description ?? e.description ?? '').trim()
  // Cap at 15 words to honour the CompressedEntry.d contract.
  const words = candidate.split(/\s+/).filter(Boolean)
  return words.slice(0, 15).join(' ')
}

function pickParams(e: CapabilityManifestEntry): string[] {
  const props = e.query_schema?.properties ?? {}
  return Object.keys(props)
}

/**
 * Filter the manifest down to its 8 primary-tool entries and project each into
 * a CompressedEntry. Entries missing a `tool_name` are ignored. Entries whose
 * `tool_name` is not one of the 8 primary tools are also ignored.
 */
export function compressManifest(manifest: CapabilityManifest): CompressedEntry[] {
  const byTool = new Map<string, CapabilityManifestEntry>()
  for (const entry of manifest.entries ?? []) {
    if (entry.tool_name) byTool.set(entry.tool_name, entry)
  }

  const result: CompressedEntry[] = []
  for (const name of PRIMARY_TOOL_NAMES) {
    const entry = byTool.get(name)
    if (!entry) continue
    result.push({
      t: name,
      d: pickDescription(entry),
      p: pickParams(entry),
      c: (entry.token_cost_hint ?? 'med') as TokenCostHint,
      a: entry.linked_data_asset_id ?? '',
    })
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
