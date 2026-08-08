/**
 * retrieval/registry/layers/L0_brahmagyan/resolve_entity.ts
 *
 * Tool: marsys://tool/L0/resolve_entity
 * Resolves a named entity (graha, nakshatra, sign, etc.) to its canonical form.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const resolveEntityCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/resolve_entity',
  type: 'tool',
  layer: 'L0',
  name: 'resolve_entity',
  description:
    'Resolve a Jyotish entity name (Sanskrit or English) to its canonical form. ' +
    'Returns canonical_id, entity_class (graha / nakshatra / rashi / etc.), and synonym list. ' +
    'Use before any chart or corpus query to normalise the entity reference.',
  input_schema: {
    name: {
      type: 'string',
      description:
        'Entity name to resolve — Sanskrit (e.g. "Sūrya", "Meṣa") or English (e.g. "Sun", "Aries"). Case-insensitive.',
    },
  },
  required_inputs: ['name'],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
    },
    bulk_context: {
      pre_fetch_priority: 80,
      always_include: false,
    },
  },
  async handler(args, _ctx) {
    try {
      const name = (args.name as string)?.trim()
      if (!name) return { content: 'name is required', is_error: true }

      // ADHIṢṬHĀNA Lane A3 (2026-08-08): a bare varga code like 'D9' can match
      // TWO rows — the new entity_class='varga' row added this lane AND a
      // pre-existing entity_class='concept' row (e.g. canonical_id='navamsa'
      // has carried synonym 'D9' since before this lane; l0_ontology.py
      // CONCEPT_EXTRA). The additive-only registry-completion constraint for
      // this lane forbids removing that legacy synonym, so the ambiguity is
      // real at the data level — without a deterministic tie-break, which row
      // `LIMIT 1` returns is an accident of query-plan/physical row order,
      // not a guarantee. `entity_class='varga'` is the authoritative class for
      // varga-code identity going forward (see l0_ontology.py's VARGA_DATA
      // comment), so it wins ties deterministically here. All other
      // resolutions (planets, houses, nakshatras, ...) are unambiguous single
      // matches and are unaffected by this ORDER BY.
      const result = await query<Record<string, unknown>>(
        `SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa,
                synonyms, description, source_citation
         FROM brahma_ontology
         WHERE $1 = ANY(synonyms)
            OR lower(canonical_name_en) = lower($1)
            OR lower(canonical_name_sa) = lower($1)
         ORDER BY (entity_class = 'varga') DESC, entity_class, canonical_id
         LIMIT 1`,
        [name],
      )

      if (!result.rows || result.rows.length === 0) {
        return {
          content: {
            canonical_id: null,
            entity_class: null,
            canonical_name_en: null,
            canonical_name_sa: null,
            synonyms: [],
            description: null,
            source_citation: null,
            not_found: true,
            input: name,
          },
          is_error: false,
        }
      }

      return { content: result.rows[0], is_error: false }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
