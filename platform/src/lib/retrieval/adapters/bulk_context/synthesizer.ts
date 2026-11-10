/**
 * adapters/bulk_context/synthesizer.ts
 *
 * Single-pass Gemini call with citations from the bundled context.
 * Used by bulk-context adapter for non-agentic queries.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { BulkContextBundle } from './bundler'
import { CostTracker } from '../shared/cost_tracker'

export interface SynthesisRequest {
  query: string
  bundle: BulkContextBundle
  chart_id?: string
  trace_id?: string
}

export interface Citation {
  uri: string
  excerpt: string
}

export interface SynthesisResult {
  answer: string
  citations: Citation[]
  model: string
  cost_usd: number
  trace_id?: string
}

/**
 * Synthesize an answer from the pre-fetched bundle using a single LLM call.
 *
 * In production, this calls Vertex AI Gemini 2.5 Flash.
 * For now, returns a structured stub (wired up when Vertex AI client lands).
 */
export async function synthesize(
  request: SynthesisRequest,
  // vertexClient: VertexAIClient  // injected in production
): Promise<SynthesisResult> {
  const tracker = new CostTracker()
  // Stub response for pattern validation
  const stubAnswer = `[SYNTHESIS_STUB] Query: "${request.query}"\n\nContext sections available: ${request.bundle.sections.map(s => s.uri).join(', ')}\n\nFull synthesis requires Vertex AI Gemini 2.5 Flash (wired in Stream E/production).`

  const cost = tracker.track('gemini-2.5-flash', { input_tokens: 0, output_tokens: 0 })

  return {
    answer: stubAnswer,
    citations: request.bundle.sections.map(s => ({
      uri: s.uri,
      excerpt: s.content.slice(0, 200),
    })),
    model: 'gemini-2.5-flash',
    cost_usd: cost.estimated_usd,
    trace_id: request.trace_id,
  }
}
