/**
 * tool_search.ts — Wave 5 Lane L4 ("tool-search metadata")
 * ================================================================================
 * RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §E W5 standing scope line:
 * "tool-search metadata". Investigation at lane-open found: `listCapabilities()`
 * (registry/index.ts) filters only on `type` / `layer` / `name_prefix` — there is
 * NO keyword/free-text index over the ~120-capability catalog anywhere in the
 * registry, the projection compiler (`scripts/manifest/generate_projections.ts`),
 * or the served MCP surface (`registry_bridge.ts`'s `list_assets` enumerates the
 * unrelated cockpit `asset_registry` table, not this retrieval registry). This is
 * gap (a) from the task's own framing — no searchable index exists at all — not
 * (b) a metadata-shape gap. `CapabilityDescriptor` already carries everything a
 * keyword index needs (name, description, display.short_label/one_line, layer,
 * archetype, tool_role, traversal_level, projection_tags); nothing new is
 * fabricated here — this module only tokenizes/normalizes fields that already
 * exist on every live descriptor.
 *
 * Pure, dependency-free derivation over `CapabilityDescriptor[]` — no DB, no fs,
 * no network — so BOTH of the following call the exact same functions (by-
 * construction-no-drift, the same discipline `catalog.ts`'s header documents for
 * the MCP/chat channel split):
 *   1. The generated-projection-compiler artifact
 *      (`scripts/manifest/generate_projections.ts` → `projection_builders.ts`,
 *      which re-exports `buildToolSearchIndex` from here) — a static,
 *      regenerate-on-demand JSON snapshot for census/CI/docs use.
 *   2. The live `tool_search` capability
 *      (`layers/L0_brahmagyan/tool_search.ts`), bridged onto MCP as the
 *      `tool_search` tool (`registry_bridge.ts`) — builds the SAME index from
 *      the live `getCatalog()` on every call and searches it in-memory.
 *
 * SCOPE / HONESTY NOTE: this is exact/substring keyword match over tokenized
 * fields, NOT fuzzy matching and NOT semantic/embedding search (that would be a
 * `vector_search`-style corpus, a materially different and heavier build — out
 * of scope for this lane's "first cut", see the lane's own closing report).
 * Case-insensitive, token-substring scored, deterministic (no LLM, no ranking
 * model) — good enough to answer "which tool(s) touch dasha / muhurta / yoga
 * activation" without a caller needing to already know exact tool names.
 */
import type { CapabilityDescriptor } from './types'

// ── Shared helpers ────────────────────────────────────────────────────────────

/** Minimal stopword list — enough to keep single-letter/glue-word noise out of
 *  the keyword set without attempting a full NLP stopword list (would be a
 *  fabricated precision this module doesn't need). */
const STOPWORDS = new Set([
  'the', 'a', 'an', 'of', 'for', 'to', 'and', 'or', 'is', 'are', 'this',
  'that', 'with', 'on', 'in', 'at', 'by', 'from', 'as', 'via', 'its', 'be',
  'not', 'no', 'if', 'it', 'into', 'over', 'per', 'used', 'use', 'uses',
  'you', 'your', 'can', 'will', 'than', 'then', 'also', 'any', 'all', 'each',
])

/** Lowercase, alnum-only tokenization. `>2` chars filters noise (single/double
 *  letter tokens) while still keeping short-but-meaningful astrology tokens
 *  (e.g. 'd9', 'rm', 'msr' pass; 'a'/'to' do not). */
export function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z0-9]+/g) ?? []).filter(
    (t) => t.length > 2 && !STOPWORDS.has(t),
  )
}

/** Mirrors `projection_builders.ts`'s own `resolveType()` fallback (6/120 live
 *  capabilities carry `primitive_type` instead of `type` — see that module's
 *  header for the documented, flagged-not-fixed registry inconsistency). Kept
 *  as an independent copy (not imported) so this module has zero dependency on
 *  the scripts/ directory — the live serving path never reaches into scripts/. */
function resolveTypeLocal(cap: CapabilityDescriptor): string {
  const anyCap = cap as unknown as { type?: string; primitive_type?: string }
  return anyCap.type ?? anyCap.primitive_type ?? 'unknown'
}

// ── Index entry (the "tool-search metadata" the task asks for) ──────────────

export interface ToolSearchIndexEntry {
  uri: string
  name: string
  type: string
  layer: string
  scope: string
  /** Domain/retrieval-shape tag — the descriptor's own `archetype` (flat_fact,
   *  temporal, cross_domain, etc.). Not a new taxonomy; reuses the D1 contract
   *  field every capability already declares. */
  family: string
  tool_role: string
  short_label: string | null
  one_line: string | null
  description: string
  /** Deduped, sorted, tokenized keyword set derived from name/description/
   *  display/layer/archetype/tool_role/traversal_level/projection_tags. */
  keywords: string[]
}

export function buildToolSearchIndexEntry(cap: CapabilityDescriptor): ToolSearchIndexEntry {
  const shortLabel = cap.display?.short_label ?? null
  const oneLine = cap.display?.one_line ?? null
  const description = oneLine ?? cap.description
  const keywordSource = [
    cap.name,
    cap.description,
    shortLabel ?? '',
    oneLine ?? '',
    cap.layer,
    cap.archetype,
    cap.tool_role,
    cap.traversal_level,
    ...(cap.projection_tags ?? []),
  ].join(' ')
  const keywords = Array.from(new Set(tokenize(keywordSource))).sort()
  return {
    uri: cap.uri,
    name: cap.name,
    type: resolveTypeLocal(cap),
    layer: cap.layer,
    scope: cap.scope,
    family: cap.archetype,
    tool_role: cap.tool_role,
    short_label: shortLabel,
    one_line: oneLine,
    description,
    keywords,
  }
}

/**
 * Build the full search index — one entry per live capability, no filtering,
 * no dropping. Deliverable requirement (a): "for every capability, emit a
 * normalized set of search fields" — this is that function; completeness is
 * asserted by the CI parity test (index.length === getCatalog().length).
 */
export function buildToolSearchIndex(caps: CapabilityDescriptor[]): ToolSearchIndexEntry[] {
  return caps.map(buildToolSearchIndexEntry).sort((a, b) => a.uri.localeCompare(b.uri))
}

// ── Search ────────────────────────────────────────────────────────────────────

export interface ToolSearchMatch {
  uri: string
  name: string
  type: string
  layer: string
  scope: string
  family: string
  short_label: string | null
  one_line: string | null
  description: string
  /** Relative relevance score (name match weighted highest, then keyword,
   *  then description substring) — a ranking signal, not a probability. */
  score: number
  matched_keywords: string[]
}

export interface ToolSearchResult {
  query: string
  query_tokens: string[]
  total_matches: number
  returned: number
  results: ToolSearchMatch[]
}

/**
 * Keyword/substring search over a pre-built index. Deterministic; no fuzzy
 * matching, no embeddings (see module header honesty note). Every query token
 * is matched independently (OR semantics across tokens, so "dasha activation"
 * surfaces anything matching either word) and scored by where the match
 * occurred (name > keyword > description).
 */
export function searchToolIndex(
  index: ToolSearchIndexEntry[],
  query: string,
  limit = 20,
): ToolSearchResult {
  const queryTokens = tokenize(query)
  const rawTokens = queryTokens.length > 0 ? queryTokens : [query.toLowerCase().trim()].filter(Boolean)
  const cappedLimit = Math.max(1, Math.min(limit, 100))

  const scored: ToolSearchMatch[] = []
  for (const entry of index) {
    const matched = new Set<string>()
    let score = 0
    const nameLower = entry.name.toLowerCase()
    const descLower = entry.description.toLowerCase()
    for (const qt of rawTokens) {
      if (!qt) continue
      if (nameLower === qt) {
        score += 5
        matched.add(qt)
      } else if (nameLower.includes(qt)) {
        score += 3
        matched.add(qt)
      }
      if (entry.keywords.some((k) => k === qt)) {
        score += 2
        matched.add(qt)
      } else if (entry.keywords.some((k) => k.includes(qt))) {
        score += 1
        matched.add(qt)
      }
      if (descLower.includes(qt)) {
        score += 1
        matched.add(qt)
      }
    }
    if (score > 0) {
      scored.push({
        uri: entry.uri,
        name: entry.name,
        type: entry.type,
        layer: entry.layer,
        scope: entry.scope,
        family: entry.family,
        short_label: entry.short_label,
        one_line: entry.one_line,
        description: entry.description,
        score,
        matched_keywords: [...matched].sort(),
      })
    }
  }
  scored.sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
  const total = scored.length
  const results = scored.slice(0, cappedLimit)
  return {
    query,
    query_tokens: rawTokens,
    total_matches: total,
    returned: results.length,
    results,
  }
}
