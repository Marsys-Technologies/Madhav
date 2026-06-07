/**
 * retrieval/registry/layers/L0_brahmagyan/intent_classify.ts
 *
 * Prompt: marsys://prompt/intent-classify
 * Template prompt used by the Bulk Context adapter for query intent tagging.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { PromptCapability, PromptMessage } from '../../types'

const INTENT_CLASSIFY_TEMPLATE = `You are a Jyotish query classifier. Your job is to identify the PRIMARY intent of a query about a birth chart.

INTENTS (pick exactly ONE):
- dasha_timing: questions about planetary periods, sub-periods, Vimshottari or Jaimini dashas
- transit_analysis: current planetary transits, Gochar, upcoming transits
- yoga_identification: identifying chart yogas (Raj Yoga, Dhana Yoga, etc.)
- planet_strength: graha bala, Shadbala, dignity, debilitation, exaltation
- house_analysis: bhava analysis, house lords, house strength
- remedy_lookup: upayas, mantras, gemstones, rituals, remedies
- panchanga: tithi, vara, nakshatra, yoga, karana, muhurta
- classical_rule: looking up a specific classical text rule or sutra
- chart_overview: general chart reading, lagna analysis, overall summary
- prediction_calibration: evaluating or calibrating a specific prediction
- unknown: none of the above

QUERY:
{{query}}

Respond with ONLY valid JSON:
{"primary_intent": "<intent>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}`

export const intentClassifyCapability: PromptCapability = {
  uri: 'marsys://prompt/intent-classify',
  primitive_type: 'prompt',
  layer: 'L0',
  name: 'intent_classify',
  description:
    'System prompt template for fast query intent classification. ' +
    'Used by the Bulk Context adapter (bulk_context/intent_classifier.ts) ' +
    'as LLM fallback when regex confidence is low. ' +
    'Returns a structured intent tag from the canonical QueryIntent enum.',
  arguments: [
    {
      name: 'query',
      description: 'The natural-language query to classify.',
      required: true,
    },
  ],
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      latency_ms_p50: 200,
    },
    bulk_context: {
      pre_fetch_priority: 100,
      always_include: false,
    },
    result_max_kb: 1,
  },
  async renderer(args: Record<string, string>, _ctx): Promise<PromptMessage[]> {
    const query = args['query']?.trim() ?? ''
    const rendered = INTENT_CLASSIFY_TEMPLATE.replace('{{query}}', query)
    return [
      {
        role: 'user',
        content: rendered,
      },
    ]
  },
}
