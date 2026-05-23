/**
 * vector_search.ts — MCP Tier 3 surgical primitive: semantic RAG chunk search.
 *
 * What it does: Performs semantic similarity search over the platform's RAG chunk
 * corpus using Vertex AI 768-dimensional text embeddings. Given a text query,
 * returns the top-K most semantically similar chunks ranked by cosine similarity.
 * The corpus contains chunks from MSR signals, UCN sections, CDLM cells, domain
 * reports, RM elements, and L1 fact excerpts. Tagged surgical: true; bypasses
 * planner and synthesis.
 *
 * When to prefer: Use vector_search when you need "documents similar to X" —
 * e.g., "find signals that discuss Saturn's separation anxiety pattern" — rather
 * than a structured filter query. Prefer query_signals for structured MSR lookups
 * with exact domain/confidence/dasha_lord filters. Prefer holistic_bundle when you want
 * the semantically similar content synthesized into an answer.
 *
 * Input shape hints:
 *   text — required; the query text to embed and match against the corpus.
 *   doc_type — optional array; filter to specific document types. Valid values:
 *     "l1_fact", "ucn_section", "msr_signal", "cdlm_cell", "domain_report", "rm_element".
 *   top_k — optional integer; number of top results to return (default 10, max 50).
 *
 * Output shape preview: {ok, result: {chunks: VectorChunk[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *
 * Example: vector_search({text: "Saturn creates obstacles in career until 36", top_k: 5}) →
 *   {ok: true, result: {chunks: [{chunk_id: "msr_signal_234", score: 0.91,
 *   text: "Saturn as Amatyakaraka...", doc_type: "msr_signal"}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

const DOC_TYPES = ['l1_fact', 'ucn_section', 'msr_signal', 'cdlm_cell', 'domain_report', 'rm_element'] as const

export const VECTOR_SEARCH_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Semantically searches the RAG chunk corpus (MSR signals, UCN, CDLM, domain reports, L1 facts) ' +
    'using Vertex AI 768-dim embeddings and returns top-K chunks ranked by cosine similarity.',
  enumSource: DOC_TYPES,
  coverageHint: '4,589+ RAG chunks across all synthesis layers',
  whenToPrefer:
    'Use for "find content similar to X" queries where you do not know the exact signal ID. ' +
    'Prefer query_signals for structured MSR lookups with exact domain/confidence/dasha_lord filters. ' +
    'Prefer holistic_bundle when semantically similar content needs to be synthesized into an answer.',
})

const VectorSearchInputSchema = z.object({
  text: z.string().describe('Query text to semantically match against the RAG chunk corpus.'),
  doc_type: z.array(z.enum(DOC_TYPES)).optional().describe(
    'Filter to specific document types. Options: l1_fact, ucn_section, msr_signal, ' +
    'cdlm_cell, domain_report, rm_element.'
  ),
  top_k: z.number().int().min(1).max(50).optional().default(10).describe(
    'Number of top results to return (default 10, max 50).'
  ),
})

type VectorSearchInput = z.infer<typeof VectorSearchInputSchema>

export function registerVectorSearch(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'vector_search',
    VECTOR_SEARCH_DESCRIPTION,
    VectorSearchInputSchema.shape,
    async (args: VectorSearchInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'vector_search',
        {
          text: args.text,
          ...(args.doc_type ? { doc_type: args.doc_type } : {}),
          top_k: args.top_k ?? 10,
        },
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }
      return okResult(envelope)
    }
  )
}
