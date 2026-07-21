/**
 * retrieval/registry/layers/L0_brahmagyan/tool_search.ts
 *
 * Tool: marsys://tool/L0/tool_search
 * Wave 5 Lane L4 ("tool-search metadata"). Keyword search over the FULL live
 * capability catalog (~120 tools/resources/prompts across L0–L5) so a caller
 * can discover a tool by describing what it needs ("dasha activation window",
 * "muhurta", "yoga firings") instead of already knowing the exact tool name —
 * the same discovery gap Claude Code's own deferred-tool ToolSearch mechanism
 * closes for its own tool roster. Global scope — chart-agnostic (searches
 * metadata, not chart data).
 *
 * Derivation logic (`tool_search.ts` sibling module, one level up) is shared
 * verbatim with the generated projection-compiler artifact
 * (`scripts/manifest/generate_projections.ts`'s `tool_search_index.generated.json`)
 * — same functions, zero drift between what's documented as searchable and what
 * is actually searched at serve time.
 */
import type { CapabilityDescriptor } from '../../types'
import { buildToolSearchIndex, searchToolIndex } from '../../tool_search'

export const toolSearchCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/tool_search',
  type: 'tool',
  layer: 'L0',
  name: 'tool_search',
  description:
    'Keyword search over the full MARSYS tool/resource/prompt catalog (~120 capabilities ' +
    'across L0-L5). Returns matching tool names, descriptions, and layer/domain tags — NOT ' +
    'the full catalog. Use this before assuming a needed capability does not exist, or when ' +
    'the exact tool name is unknown (e.g. query="dasha activation", "muhurta", "yoga firings", ' +
    '"remedies"). Case-insensitive keyword/substring match across name, description, layer, ' +
    'and domain tags — not fuzzy or semantic search; a query with zero token overlap against ' +
    'every catalog entry returns an honest empty result, not a fabricated best-effort guess.',
  input_schema: {
    query: {
      type: 'string',
      description: 'Keyword(s) describing the capability you need (e.g. "dasha", "muhurta timing", "remedy for saturn").',
    },
    limit: {
      type: 'number',
      description: 'Max matching tools to return (default 20, max 100).',
    },
  },
  scope: 'global',
  archetype: 'orientation_digest',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: false,
  lel_capable: false,
  data_source: 'computed',
  projection_tags: ['mcp_full', 'mcp_consult', 'chat'],
  annotations: {
    read_only: true,
    idempotent: true,
    destructive: false,
    open_world: false,
  },
  display: {
    short_label: 'Tool search',
    one_line: 'Keyword search over the full MARSYS tool/resource/prompt catalog.',
  },
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
    },
  },
  async handler(args, _ctx) {
    try {
      const query = String(args?.['query'] ?? '').trim()
      if (!query) {
        return { content: { error: 'query is required (non-empty string)' }, is_error: true }
      }
      const limitRaw = args?.['limit']
      const limit = limitRaw != null ? Math.min(Math.max(1, Number(limitRaw)), 100) : 20

      // Dynamic import of catalog.ts (not a top-level import): catalog.ts imports
      // this layer's index.ts to trigger registration, so a top-level import here
      // would be circular. This is the SAME pattern already used elsewhere in this
      // registry for the identical reason (chart_agnostic_gate_registry.test.ts,
      // catalog.test.ts — `const { getCatalog } = await import('./catalog')`).
      // Safe because getCatalog() is only invoked inside this handler function body
      // (at call time, long after both modules have finished loading), never at
      // module-evaluation time.
      const { getCatalog } = await import('../../catalog')
      const caps = getCatalog()
      const index = buildToolSearchIndex(caps)
      const result = searchToolIndex(index, query, limit)

      return {
        content: {
          ...result,
          catalog_total: caps.length,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
