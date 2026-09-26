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

/**
 * Fail-closed refusal for bare-name resolution that matches more than one
 * brahma_ontology row. Twin of the python-sidecar's
 * brahmagyan.l0_ontology.AmbiguousEntityError, following the
 * AmbiguousGrahaIdentity pattern (l0_semantic_release.py).
 *
 * brahma_ontology identity is the composite (entity_class, canonical_id) —
 * native Decision 16 (2026-09-26) / mandate Ruling 2 / ADK-0003: a consumer
 * resolving on canonical_id alone is the defect, not the data. Declared
 * cross-class polysemy is registered in brahma_polysemy_registry
 * (migration 1125, HELD); resolution rule: "class-qualified citation
 * required; bare resolution of a registered id refuses".
 */
export class AmbiguousEntityError extends Error {
  constructor(
    name: string,
    candidates: Array<{ canonical_id: unknown; entity_class: unknown }>,
    entityClass: string | null,
  ) {
    const listing = candidates
      .map((c) => `${String(c.entity_class)}.${String(c.canonical_id)}`)
      .join(', ')
    super(
      `Ambiguous entity "${name}"` +
        (entityClass ? ` within class "${entityClass}"` : '') +
        `: matches ${candidates.length} rows (${listing}). ` +
        'brahma_ontology identity is the composite (entity_class, canonical_id); ' +
        're-call with entity_class to resolve within a class ' +
        '(polysemy registry: brahma_polysemy_registry, migration 1125; ' +
        'Decision 16 / mandate Ruling 2 / ADK-0003).',
    )
    this.name = 'AmbiguousEntityError'
  }
}

export const resolveEntityCapability: CapabilityDescriptor = {
  // W-L0-4 served-surface contract: explicit declaration (detector:
  // __tests__/l0_density_contract.test.ts — do not remove; values follow the
  // deriveDensityContract evidence rules in ../../descriptor_defaults.ts).
  density_contract: {
    max_verdict_bytes: 1024,
    max_digest_bytes: 4096,
    paginated: false,
    facets: ['name'],
    empty_reason: true,
  },
  uri: 'marsys://tool/L0/resolve_entity',
  type: 'tool',
  layer: 'L0',
  name: 'resolve_entity',
  description:
    'Resolve a Jyotish entity name (Sanskrit or English) to its canonical form. ' +
    'Returns canonical_id, entity_class (graha / nakshatra / rashi / etc.), and synonym list. ' +
    'Use before any chart or corpus query to normalise the entity reference. ' +
    'Identity is the composite (entity_class, canonical_id): a bare name that matches rows in ' +
    'MORE THAN ONE class (e.g. the declared polysemy pairs in brahma_polysemy_registry — ' +
    'kemadruma, sade_sati, phaladeepika, kp, ...) is REFUSED with an AmbiguousEntityError ' +
    'naming the candidate classes; re-call with entity_class to resolve within a class.',
  input_schema: {
    name: {
      type: 'string',
      description:
        'Entity name to resolve — Sanskrit (e.g. "Sūrya", "Meṣa") or English (e.g. "Sun", "Aries"). Case-insensitive.',
    },
    entity_class: {
      type: 'string',
      description:
        'Optional class qualifier (e.g. "yoga", "dosha", "concept", "school", "text"). ' +
        'Scopes resolution to one entity class. REQUIRED when the name is polysemous across ' +
        'classes — a bare resolution of a multiply-registered name refuses loudly ' +
        '(Decision 16 / mandate Ruling 2 / ADK-0003; registry: brahma_polysemy_registry).',
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
      const entityClass = (args.entity_class as string)?.trim() || null

      // W-L0-9 fail-closed resolution (native Decision 16 / mandate Ruling 2 /
      // ADK-0003, 2026-09-26): brahma_ontology's identity IS the composite
      // (entity_class, canonical_id) — the live constraint
      // brahma_ontology_canonical_unique (ws2_l0_ontology.sql:26). Bare
      // canonical_id is deliberately NOT unique (730 distinct over 741 rows, 11
      // declared cross-class pairs + argala via held 1121, verified live
      // 2026-09-26; registry: brahma_polysemy_registry, migration 1125).
      // Resolution rule: "class-qualified citation required; bare resolution of
      // a registered id refuses". So: fetch ALL matching rows; a bare lookup
      // returning >1 row refuses loudly (AmbiguousEntityError naming the id and
      // the candidate classes) instead of silently picking one; a class-qualified
      // lookup resolves within the class.
      //
      // ONE named exception, preserved from ADHIṢṬHĀNA Lane A3 (2026-08-08): a
      // bare varga code like 'D9' can match TWO rows — the entity_class='varga'
      // row AND a pre-existing entity_class='concept' row (canonical_id='navamsa'
      // has carried synonym 'D9' since before that lane; the additive-only
      // registry-completion constraint forbids removing that legacy synonym).
      // entity_class='varga' is the authoritative class for varga-code identity,
      // so when the match set contains exactly one varga row, it wins
      // deterministically. All other multi-row sets refuse. The single-row and
      // not-found paths are byte-identical to the pre-W-L0-9 behaviour.
      const result = await query<Record<string, unknown>>(
        `SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa,
                synonyms, description, source_citation
         FROM brahma_ontology
         WHERE ($1 = ANY(synonyms)
            OR lower(canonical_name_en) = lower($1)
            OR lower(canonical_name_sa) = lower($1))
           AND ($2::text IS NULL OR entity_class = $2)
         ORDER BY (entity_class = 'varga') DESC, entity_class, canonical_id`,
        [name, entityClass],
      )

      const rows = result.rows ?? []

      if (rows.length === 0) {
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

      if (rows.length > 1 && entityClass === null) {
        const vargaRows = rows.filter((r) => r.entity_class === 'varga')
        if (vargaRows.length === 1) {
          return { content: vargaRows[0], is_error: false }
        }
      }

      if (rows.length > 1) {
        throw new AmbiguousEntityError(name, rows, entityClass)
      }

      return { content: rows[0], is_error: false }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
