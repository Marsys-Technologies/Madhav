/**
 * retrieval/registry/layers/L0_brahmagyan/list_entities.ts
 *
 * Tool: marsys://tool/L0/list_entities
 * Lists all entities in brahma_ontology, optionally filtered by class.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const listEntitiesCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/list_entities',
  type: 'tool',
  layer: 'L0',
  name: 'list_entities',
  description:
    'List all Jyotish entities in the canonical ontology, optionally filtered by class ' +
    '(graha / nakshatra / rashi / bhava / etc.). ' +
    'Returns canonical_id, entity_class, canonical names, and synonym list for each entity.',
  input_schema: {
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
  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'umbrella',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
    },
    bulk_context: {
      pre_fetch_priority: 40,
      always_include: false,
    },
  },
  async handler(args, _ctx) {
    try {
      const limit = Math.min((args.limit as number) ?? 100, 500)
      const params: unknown[] = [limit]

      let sql =
        `SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa, synonyms
         FROM brahma_ontology`

      if (args.entity_class) {
        sql += ` WHERE entity_class = $2`
        params.push(args.entity_class as string)
      }

      sql += ` ORDER BY entity_class, canonical_name_en LIMIT $1`

      const result = await query<Record<string, unknown>>(sql, params)

      return {
        content: {
          entities: result.rows ?? [],
          total: result.rows?.length ?? 0,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
