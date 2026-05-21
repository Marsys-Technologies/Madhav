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
 * with exact domain/confidence/dasha_lord filters. Prefer ask_madhav when you want
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
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Principal } from '../types.js';
export declare function registerVectorSearch(server: McpServer, getPrincipal: () => Principal): void;
//# sourceMappingURL=vector_search.d.ts.map