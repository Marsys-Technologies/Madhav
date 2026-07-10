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

// R-27 fix: brahma_ontology.entity_class stores 'planet'/'sign'/'house' (the l0_ontology.py
// writer's vocabulary — verified against the seed source), not the Sanskrit terms 'graha'/
// 'rashi'/'bhava' this tool's own schema previously advertised as valid — so entity_class=
// 'graha' (or 'rashi'/'bhava') silently matched zero rows every time. Aliased below.
// 'yoga' and 'karana' have NO matching top-level entity_class at all — 'yoga' exists only as
// a single canonical_id=yoga row under entity_class='concept' (the CONCEPT of a yoga, not a
// catalog of individual yogas; the actual yoga catalog lives in bg_yogas, a different table
// entirely) and 'karana' likewise. These are NOT alias-mapped (no honest 1:1 target); a request
// for either returns an explicit empty_reason instead of a silent empty array.
const ENTITY_CLASS_ALIAS: Record<string, string> = {
  graha: 'planet', planet: 'planet',
  rashi: 'sign', sign: 'sign',
  bhava: 'house', house: 'house',
  nakshatra: 'nakshatra',
  upagraha: 'upagraha',
}
const VALID_ENTITY_CLASSES = ['planet', 'sign', 'house', 'nakshatra', 'upagraha', 'dasha_system', 'domain', 'concept', 'karaka', 'aspect_type', 'remedy_type', 'school', 'text']
const UNBACKED_CLASSES = new Set(['yoga', 'karana'])

export const listEntitiesCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/list_entities',
  type: 'tool',
  layer: 'L0',
  name: 'list_entities',
  description:
    'List all Jyotish entities in the canonical ontology, optionally filtered by class ' +
    '(graha/planet, nakshatra, rashi/sign, bhava/house, upagraha, etc — Sanskrit/English ' +
    'synonyms are accepted and normalized to the stored vocabulary). ' +
    'Returns canonical_id, entity_class, canonical names, and synonym list for each entity.',
  input_schema: {
    entity_class: {
      type: 'string',
      description:
        'Optional filter: entity class to list. Accepts either the stored vocabulary ' +
        '(planet, sign, house, nakshatra, upagraha, dasha_system, domain, concept, karaka, ' +
        'aspect_type, remedy_type, school, text) or the Sanskrit synonyms graha (→planet), ' +
        'rashi (→sign), bhava (→house). If omitted, returns all classes. ' +
        '"yoga"/"karana" are NOT valid filters here (see empty_reason if requested) — they ' +
        'have no dedicated top-level class; use query_yoga_catalog / L0 panchanga tools instead.',
      enum: ['graha', 'planet', 'nakshatra', 'rashi', 'sign', 'bhava', 'house', 'upagraha',
        'dasha_system', 'domain', 'concept', 'karaka', 'aspect_type', 'remedy_type', 'school', 'text'],
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
      const requestedClass = args.entity_class as string | undefined

      if (requestedClass && UNBACKED_CLASSES.has(requestedClass)) {
        return {
          content: {
            entities: [],
            total: 0,
            empty_reason:
              `entity_class="${requestedClass}" has no dedicated top-level class in brahma_ontology ` +
              `— it exists only as a single canonical_id="${requestedClass}" row under entity_class=` +
              `"concept" (the CONCEPT of a ${requestedClass}, not a catalog of individual ${requestedClass}s). ` +
              `Valid class vocabulary: ${VALID_ENTITY_CLASSES.join(', ')} ` +
              '(Sanskrit synonyms graha/rashi/bhava also accepted, normalized to planet/sign/house). ' +
              `For a catalog of individual yogas, use query_yoga_catalog instead.`,
          },
          is_error: false,
        }
      }

      const resolvedClass = requestedClass ? (ENTITY_CLASS_ALIAS[requestedClass] ?? requestedClass) : undefined
      const params: unknown[] = [limit]

      let sql =
        `SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa, synonyms
         FROM brahma_ontology`

      if (resolvedClass) {
        sql += ` WHERE entity_class = $2`
        params.push(resolvedClass)
      }

      sql += ` ORDER BY entity_class, canonical_name_en LIMIT $1`

      const result = await query<Record<string, unknown>>(sql, params)

      return {
        content: {
          entities: result.rows ?? [],
          total: result.rows?.length ?? 0,
          filters: { entity_class_requested: requestedClass ?? null, entity_class_resolved: resolvedClass ?? null },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
