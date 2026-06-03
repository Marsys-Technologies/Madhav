/**
 * bo_2-7.ts — BO-2-7: bodha_signal_search MCP tool.
 *
 * Asset:  bodha.embeddings (BO-2-7)
 * Layer:  L2 Bodha — Chart Intelligence
 * Table:  bodha_signal_embeddings (pgvector, 768-dim)
 * Model:  text-multilingual-embedding-002 (Vertex AI)
 *
 * This tool feeds the corpus.search vector-search path. It:
 *   1. Accepts a natural-language query + optional domain/valence filters.
 *   2. Calls the platform sidecar /api/bodha/signal-search endpoint which
 *      runs the Vertex AI embedding + pgvector ANN search.
 *   3. Returns the top-k most semantically similar MSR signals with their
 *      domain, valence, claim_text, source_citation, and cosine similarity.
 *
 * MCP tool name: bodha_signal_search
 * Surgical: true (raw retrieval; no LLM synthesis)
 *
 * BRAHMA-BO-2-7
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { callPlatformPrimitive } from '../client.js'

// ── Input schema ──────────────────────────────────────────────────────────────

const BodyaSignalSearchInputSchema = z.object({
  /** Natural-language query to embed and search against bodha_signal_embeddings. */
  query: z.string().min(1).max(2000).describe(
    'Natural-language query to embed and search against bodha.embeddings (bodha_signal_embeddings).'
  ),
  /** Maximum number of signals to return (1–20, default 5). */
  limit: z.number().int().min(1).max(20).optional().default(5).describe(
    'Number of nearest-neighbour signals to return (1–20, default 5).'
  ),
  /** Optional domain filter — restricts results to one Jyotish domain. */
  domain: z.string().optional().describe(
    'Optional: restrict results to signals in this domain (e.g. "career", "health", "relationships").'
  ),
  /** Optional valence filter — restricts results to "positive", "negative", or "neutral". */
  valence: z.enum(['positive', 'negative', 'neutral', 'mixed']).optional().describe(
    'Optional: restrict results to signals of this valence.'
  ),
})

type BodyaSignalSearchInput = z.infer<typeof BodyaSignalSearchInputSchema>

// ── Result types ──────────────────────────────────────────────────────────────

export interface BodyaSignalResult {
  signal_id: string
  domain: string
  valence: string | null
  claim_text: string
  source_citation: string | null
  similarity: number
}

export interface BodyaSignalSearchResult {
  query: string
  limit: number
  domain_filter: string | undefined
  valence_filter: string | undefined
  results: BodyaSignalResult[]
  result_count: number
  embedding_model: string
  table: string
  surgical: true
}

// ── Tool registration ─────────────────────────────────────────────────────────

/**
 * Register the bodha_signal_search MCP tool on the given server.
 *
 * @param server       The McpServer instance to register on.
 * @param getPrincipal Accessor for the current request's resolved principal.
 */
export function registerBodyaSignalSearch(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'bodha_signal_search',
    'Search bodha.embeddings (bodha_signal_embeddings) via pgvector cosine similarity. ' +
    'Embed a natural-language query with Vertex AI text-multilingual-embedding-002 (768-dim) ' +
    'and return the top-k most semantically similar MSR signals. ' +
    'Feeds the corpus.search vector-search path. Surgical: raw retrieval only, no synthesis.',
    {
      query:   z.string().min(1).max(2000).describe('Natural-language query.'),
      limit:   z.number().int().min(1).max(20).optional().default(5).describe('Top-k results (default 5).'),
      domain:  z.string().optional().describe('Optional Jyotish domain filter.'),
      valence: z.enum(['positive', 'negative', 'neutral', 'mixed']).optional().describe('Optional valence filter.'),
    },
    async ({ query, limit, domain, valence }: BodyaSignalSearchInput) => {
      const principal = getPrincipal()

      const params: Record<string, unknown> = {
        query,
        limit: limit ?? 5,
      }
      if (domain !== undefined) params['domain'] = domain
      if (valence !== undefined) params['valence'] = valence

      const { status, envelope } = await callPlatformPrimitive(
        'bodha_signal_search',
        params,
        principal
      )

      if (!envelope.ok) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                error: envelope.error.message,
                error_class: envelope.error.class,
                remediation: envelope.error.remediation ?? 'Check platform-mcp logs.',
                tool: 'bodha_signal_search',
                http_status: status,
              }),
            },
          ],
          isError: true,
        }
      }

      const result = envelope.result as BodyaSignalSearchResult

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify({
              ...result,
              provenance_envelope: {
                source: 'bodha.embeddings',
                asset: 'BO-2-7',
                computed_at: new Date().toISOString(),
              },
            }, null, 2),
          },
        ],
      }
    }
  )
}

// ── Platform primitive handler (for platform/src/app/api/mcp/primitives/) ─────
//
// This section documents the expected platform-side handler contract.
// The handler lives at: platform/src/app/api/mcp/primitives/bodha_signal_search/route.ts
// It must:
//   1. Accept POST with { params: { query, limit?, domain?, valence? } }
//   2. Call the python-sidecar /api/bodha/signal-search endpoint (which runs
//      bo_2-7.py:vector_search_signals under the hood)
//   3. Return a McpEnvelope with result: BodyaSignalSearchResult
//
// The python-sidecar endpoint is wired in platform/python-sidecar/main.py as:
//   POST /api/bodha/signal-search
// pointing at brahmagyan.bodha.bo_2-7:vector_search_signals
//
// ── End of contract documentation ─────────────────────────────────────────────
