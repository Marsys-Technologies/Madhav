/**
 * retrieval/registry/layers/L0_brahmagyan/intent_classify.ts
 *
 * Prompt: marsys://prompt/intent-classify
 * Template prompt used by the Bulk Context adapter for query intent tagging.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { CapabilityDescriptor } from '../../types'

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

export const intentClassifyCapability: CapabilityDescriptor = {
  uri: 'marsys://prompt/intent-classify',
  type: 'prompt',
  layer: 'L0',
  name: 'intent_classify',
  description:
    'System prompt template for fast query intent classification. ' +
    'Used by the Bulk Context adapter (bulk_context/intent_classifier.ts) ' +
    'as LLM fallback when regex confidence is low. ' +
    'Returns a structured intent tag from the canonical QueryIntent enum.',
  input_schema: {
    query: {
      type: 'string',
      description: 'The natural-language query to classify.',
    },
  },
  required_inputs: ['query'],
  scope: 'global',
  archetype: 'orientation_digest',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
    },
    bulk_context: {
      pre_fetch_priority: 100,
      always_include: false,
    },
  },
  async handler(args, _ctx) {
    const queryText = (args['query'] as string)?.trim() ?? ''
    const rendered = INTENT_CLASSIFY_TEMPLATE.replace('{{query}}', queryText)
    return {
      content: rendered,
      is_error: false,
    }
  },
}
