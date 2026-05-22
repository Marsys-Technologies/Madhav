/**
 * read_classical_text.ts — MCP Tier 4 tool: semantic search over the MARSYS classical corpus.
 *
 * Returns excerpts from the four indexed classical texts (BPHS, KP Reader,
 * Jaimini Sutram, Tajaka Neelakanthi) ranked by semantic similarity to a query.
 * This is a direct retrieval read — no planner, no B.11 floor enforcement.
 * The response is tagged surgical: true in the epistemics block.
 *
 * Per arch §3.7, this is a Tier 4 raw-asset read that enables classical quoting.
 * Use it to ground interpretive claims in canonical śāstra text.
 *
 * Architecture note: routes through /api/mcp/primitives/read_classical_text →
 * classical_text_search retrieval tool → rag_chunks WHERE canonical_id LIKE
 * 'classical_texts/%'. Vertex AI text-embedding-004 (768-dim) for similarity ranking.
 *
 * Access control: all authenticated tiers (super_admin, acharya, client).
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'

// ── Supported classical texts ─────────────────────────────────────────────────

const CLASSICAL_TEXT_IDS = ['BPHS', 'KP_READER', 'JAIMINI', 'TAJAKA'] as const

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerReadClassicalText(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'read_classical_text',

    // ── Tool description (§4.6-standard, ≥100 words) ──────────────────────────
    `What it does: Retrieves excerpts from the MARSYS-JIS classical corpus —
Brihat Parashara Hora Shastra (BPHS), KP Reader, Jaimini Sutram, and Tajaka
Neelakanthi — ranked by semantic similarity to your query. Use to ground
interpretive claims in canonical śāstra text, quote classical authority for a
yoga or dasha interpretation, or surface the classical-text basis for a signal
in the MSR corpus.

When to prefer: Use read_classical_text when the question requires a classical
textual citation ("what does Parashara say about Ketu in the 12th?"). Prefer
vector_search for cross-layer semantic retrieval including MSR signals and LEL
data. Prefer query_chart_facts or query_signals for structured fact lookups that
do not require textual quoting.

Input shape hints: query — required; the Sanskrit concept, yoga name, or
interpretive question to search for (e.g., "Ketu in 12th house moksha",
"Hamsa yoga Jupiter exaltation"). text_id — optional; filter to a specific
text: "BPHS", "KP_READER", "JAIMINI", or "TAJAKA". limit — optional; max
excerpts to return (default 5, max 20).

Output shape preview: {ok, result: {results: [{text_key, title, chapter,
verse_range, content, similarity}]}, trace_id, epistemics: {surgical: true}}.

Example: read_classical_text({query: "Hamsa yoga Jupiter exaltation",
text_id: "BPHS", limit: 3}) → returns up to 3 BPHS excerpts closest to
the Hamsa-yoga concept, with chapter and verse_range for citation.`,

    // ── Input schema ──────────────────────────────────────────────────────────
    {
      query: z
        .string()
        .describe(
          'The Sanskrit concept, yoga name, or interpretive question to search for. ' +
          'E.g., "Ketu in 12th house moksha" or "Hamsa yoga Jupiter exaltation".'
        ),
      text_id: z
        .enum(CLASSICAL_TEXT_IDS)
        .optional()
        .describe(
          `Optional: restrict to a specific classical text. One of: ${CLASSICAL_TEXT_IDS.join(', ')}. ` +
          'Omit to search across all four texts.'
        ),
      limit: z
        .number()
        .int()
        .min(1)
        .max(20)
        .optional()
        .default(5)
        .describe('Max excerpts to return (default 5, max 20).'),
    },

    // ── Handler ────────────────────────────────────────────────────────────────
    async ({ query, text_id, limit }) => {
      const principal = getPrincipal()

      // Map text_id enum to the schools filter expected by classical_text_search.
      // classical_text_search uses tradition/text_key filtering via the schools param.
      const schools = text_id ? [text_id.toLowerCase()] : undefined

      const result = await callPlatformPrimitive(
        'read_classical_text',
        { query, schools, limit },
        principal
      )

      if (!result.envelope.ok) {
        const errEnv = result.envelope
        const errorMsg = 'error' in errEnv
          ? `${errEnv.error.class}: ${errEnv.error.message}`
          : 'Unknown error from platform primitive endpoint'
        return {
          content: [{ type: 'text' as const, text: `Error: ${errorMsg}` }],
          isError: true,
        }
      }

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(result.envelope, null, 2),
          },
        ],
      }
    }
  )
}
