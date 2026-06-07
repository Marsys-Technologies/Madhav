/**
 * retrieval/registry/layers/L0_brahmagyan/list_entities.ts
 *
 * Tool: marsys://tool/L0/list_entities
 * Lists all entities in brahma_ontology, optionally filtered by class.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { ToolCapability } from '../../types'

export const listEntitiesCapability: ToolCapability = {
  uri: 'marsys://tool/L0/list_entities',
  primitive_type: 'tool',
  layer: 'L0',
  name: 'list_entities',
  description:
    'List all Jyotish entities in the canonical ontology, optionally filtered by class ' +
    '(graha / nakshatra / rashi / bhava / etc.). ' +
    'Returns canonical_id, entity_class, canonical names, and synonym list for each entity.',
  input_schema: {
    type: 'object',
    properties: {
      entity_class: {
        type: 'string',
        description:
          'Optional filter: entity class to list. One of: graha, nakshatra, rashi, bhava, upagraha, yoga, karana. ' +
          'If omitted, returns all classes.',
        enum: ['graha', 'nakshatra', 'rashi', 'bhava', 'upagraha', 'yoga', 'karana'],
      },
      limit: {
        type: 'number',
        description: 'Maximum results to return (default 100, max 500).',
        default: 100,
      },
    },
    required: [],
    additionalProperties: false,
  },
  output_schema: {
    type: 'object',
    properties: {
      entities: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            canonical_id: { type: 'string' },
            entity_class: { type: 'string' },
            canonical_name_en: { type: 'string' },
            canonical_name_sa: { type: 'string' },
            synonyms: { type: 'array', items: { type: 'string' } },
          },
        },
      },
      total: { type: 'number' },
    },
  },
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      latency_ms_p50: 30,
    },
    bulk_context: {
      pre_fetch_priority: 40,
      always_include: false,
      result_size_kb_p50: 8,
    },
    result_max_kb: 32,
  },
  async handler(args: Record<string, unknown>, ctx) {
    const db = ctx?.db
    if (!db) throw new Error('list_entities: no DB connection in context')

    const limit = Math.min((args.limit as number) ?? 100, 500)
    const params: unknown[] = [limit]

    let query =
      `SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa, synonyms
       FROM brahma_ontology`

    if (args.entity_class) {
      query += ` WHERE entity_class = $2`
      params.push(args.entity_class as string)
    }

    query += ` ORDER BY entity_class, canonical_name_en LIMIT $1`

    const rows = await db.query(query, params)

    return {
      entities: rows ?? [],
      total: rows?.length ?? 0,
    }
  },
}
