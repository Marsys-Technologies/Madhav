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
    'A name in more than one class is reported with ambiguous=true and a candidates list; pass entity_class to select. ' +
    'Use before any chart or corpus query to normalise the entity reference.',
  input_schema: {
    name: {
      type: 'string',
      description:
        'Entity name to resolve — Sanskrit (e.g. "Sūrya", "Meṣa") or English (e.g. "Sun", "Aries"). Case-insensitive.',
    },
    entity_class: {
      type: 'string',
      description: 'Optional: restrict the match to one ontology class (planet, sign, nakshatra, yoga, dosha, ...).',
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

      const entityClass = typeof args.entity_class === 'string' && args.entity_class.trim() !== '' ? args.entity_class.trim() : null
      // Tie-break and class-aware resolution (TI-L0-14): full text in the NOTES block at the end of this file.
      // The winner is chosen by the ORDER BY below exactly as before (see TIE HOLD in the NOTES block at the end of
      // the file: two explicit preferences keep today's winners), so no served id moves; the statement now also returns the other matching (class, id) rows
      // so the response can say `ambiguous: true` and list them. `entity_class` (optional) restricts the match.
      // A name never silently picks one of several classes without saying so. The varga/concept tie on 'D9'
      // (ADHIṢṬHĀNA Lane A3) is the original case of this: varga wins it, and `candidates` now lists both.
      // `candidates` is capped at CANDIDATE_CAP rows (the largest real overlap today is two classes).
      const result = await query<Record<string, unknown>>(
        `SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa,
                synonyms, description, source_citation
         FROM brahma_ontology
         WHERE ($1 = ANY(synonyms)
            OR lower(canonical_name_en) = lower($1)
            OR lower(canonical_name_sa) = lower($1))
           AND ($2::text IS NULL OR entity_class = $2)
         ORDER BY (entity_class = 'varga') DESC, (entity_class = 'dosha'), entity_class, (canonical_id = 'jaimini_sutram') DESC, canonical_id
         LIMIT ${CANDIDATE_CAP}`,
        [name, entityClass],
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
            ambiguous: false,
            candidates: [],
            input: name,
          },
          is_error: false,
        }
      }

      const keys = new Set(result.rows.map((r) => `${String(r.entity_class)}\u001f${String(r.canonical_id)}`))
      const ambiguous = keys.size > 1
      const candidates = ambiguous ? result.rows.map((r) => ({ canonical_id: r.canonical_id, entity_class: r.entity_class })) : []
      return { content: { ...result.rows[0], ambiguous, candidates }, is_error: false }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}

// Upper bound on the candidates one name can return (the largest real overlap is 2 classes).
const CANDIDATE_CAP = 25

/*
 * NOTES (kept at the end of the file: asset_declarations.json pins evidence lines at the top of it).
 *
 * ADHIṢṬHĀNA Lane A3 (2026-08-08): a bare varga code like 'D9' can match TWO rows - the entity_class='varga'
 * row added that lane AND a pre-existing entity_class='concept' row (canonical_id='navamsa' has carried synonym
 * 'D9' since before; l0_ontology.py CONCEPT_EXTRA). The additive-only registry-completion constraint forbids
 * removing that legacy synonym, so the ambiguity is real at the data level; `entity_class='varga'` is the
 * authoritative class for varga-code identity, so it wins ties deterministically through the ORDER BY. All other
 * resolutions (planets, houses, nakshatras, ...) are unambiguous single matches and unaffected by it.
 *
 * TI-L0-14 (SS Q4, option a): the tie-break picks the SAME winner as before (identical ORDER BY, so no served id
 * moves), but it is no longer SILENT. The query returns every matching (class, id) - up to CANDIDATE_CAP - and the
 * response says `ambiguous: true` with the full `candidates` list when more than one distinct (entity_class,
 * canonical_id) matched, so a caller can pass `entity_class` instead of trusting the tie-break. With `entity_class`
 * supplied the match is restricted to that class.
 *
 * TIE HOLD (SS N-113, until the acharya batch rules): the ORDER BY carries two explicit tie preferences so that NO
 * served resolution changes while the data PRs land. (1) `(entity_class = 'dosha')` sorts a dosha row LAST in any
 * tie: the dosha alias sets (TI-L0-12) make 7 names (kemadruma, Kemadruma, daridra, Daridra, Rajju, Sakata Yoga,
 * Sarpa Yoga) match both a yoga and a dosha; today they resolve to the yoga and still do. Names only a dosha matches
 * resolve to the dosha (newly resolvable). (2) `(canonical_id = 'jaimini_sutram') DESC`, applied AFTER entity_class
 * (so it only orders text vs text), keeps 'Jaimini Sutram' / 'jaimini sutras' on jaimini_sutram now that the
 * corpus text bphs_jaimini (TI-L0-13) also carries those names. THE FLIP IS A ONE-LINE SWITCH: after the ruling,
 * delete `(entity_class = 'dosha'), ` (yoga -> dosha on the 7 names) and/or `(canonical_id = 'jaimini_sutram') DESC, `
 * from this ORDER BY and from the same line in source_query_availability.ts (contract 'resolve-entity'), and
 * update the HOLD tests in resolve_entity.class_aware.test.ts. `candidates` already lists both rows, so a caller
 * is told about the other class regardless of the hold.
 */
