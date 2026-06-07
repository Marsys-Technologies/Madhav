/**
 * retrieval/registry/layers/L0_brahmagyan/resolve_entity.ts
 *
 * Tool: marsys://tool/L0/resolve_entity
 * Resolves a named entity (graha, nakshatra, sign, etc.) to its canonical form.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { ToolCapability } from '../../types'

export const resolveEntityCapability: ToolCapability = {
  uri: 'marsys://tool/L0/resolve_entity',
  primitive_type: 'tool',
  layer: 'L0',
  name: 'resolve_entity',
  description:
    'Resolve a Jyotish entity name (Sanskrit or English) to its canonical form. ' +
    'Returns canonical_id, entity_class (graha / nakshatra / rashi / etc.), and synonym list. ' +
    'Use before any chart or corpus query to normalise the entity reference.',
  input_schema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description:
          'Entity name to resolve — Sanskrit (e.g. "Sūrya", "Meṣa") or English (e.g. "Sun", "Aries"). Case-insensitive.',
      },
    },
    required: ['name'],
    additionalProperties: false,
  },
  output_schema: {
    type: 'object',
    properties: {
      canonical_id: { type: 'string' },
      entity_class: { type: 'string' },
      canonical_name_en: { type: 'string' },
      canonical_name_sa: { type: 'string' },
      synonyms: { type: 'array', items: { type: 'string' } },
      description: { type: 'string' },
      source_citation: { type: 'string' },
    },
    required: ['canonical_id', 'entity_class', 'canonical_name_en', 'synonyms'],
  },
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      always_prefetch: false,
      latency_ms_p50: 20,
    },
    bulk_context: {
      pre_fetch_priority: 80,
      always_include: false,
      result_size_kb_p50: 1,
    },
    result_max_kb: 4,
  },
  /**
   * Handler: resolves entity from brahma_ontology table.
   * Searches: synonyms array, canonical_name_en, canonical_name_sa.
   */
  async handler(args: Record<string, unknown>, ctx) {
    const db = ctx?.db
    if (!db) throw new Error('resolve_entity: no DB connection in context')

    const name = (args.name as string)?.trim()
    if (!name) throw new Error('resolve_entity: name is required')

    const row = await db.query(
      `SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa,
              synonyms, description, source_citation
       FROM brahma_ontology
       WHERE $1 = ANY(synonyms)
          OR lower(canonical_name_en) = lower($1)
          OR lower(canonical_name_sa) = lower($1)
       LIMIT 1`,
      [name],
    )

    if (!row || row.length === 0) {
      return {
        canonical_id: null,
        entity_class: null,
        canonical_name_en: null,
        canonical_name_sa: null,
        synonyms: [],
        description: null,
        source_citation: null,
        not_found: true,
        input: name,
      }
    }

    return row[0]
  },
}
