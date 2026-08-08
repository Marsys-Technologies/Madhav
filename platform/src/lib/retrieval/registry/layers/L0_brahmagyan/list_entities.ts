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
import {
  buildHonestPagination,
  computeFilterFingerprint,
  checkCursorFingerprint,
  CURSOR_FILTER_MISMATCH_FLAG,
} from '@/lib/retrieval/envelope'

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
  // ADHIṢṬHĀNA Lane A3 (2026-08-08): 'varga' (divisional chart, e.g. D9/Navamsha)
  // is a new top-level entity_class — 30 rows seeded, canonical_id 'd1'..'d2700'.
  // 'amsa' is the Sanskrit term for a varga division; aliased for symmetry with
  // the graha/rashi/bhava Sanskrit aliases above.
  varga: 'varga', amsa: 'varga',
}
const VALID_ENTITY_CLASSES = ['planet', 'sign', 'house', 'nakshatra', 'upagraha', 'dasha_system', 'domain', 'concept', 'karaka', 'aspect_type', 'remedy_type', 'school', 'text', 'varga']
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
        'aspect_type, remedy_type, school, text, varga) or the Sanskrit synonyms graha (→planet), ' +
        'rashi (→sign), bhava (→house), amsa (→varga). If omitted, returns all classes. ' +
        '"yoga"/"karana" are NOT valid filters here (see empty_reason if requested) — they ' +
        'have no dedicated top-level class; use query_yoga_catalog / L0 panchanga tools instead.',
      enum: ['graha', 'planet', 'nakshatra', 'rashi', 'sign', 'bhava', 'house', 'upagraha',
        'dasha_system', 'domain', 'concept', 'karaka', 'aspect_type', 'remedy_type', 'school', 'text',
        'varga', 'amsa'],
    },
    limit: {
      type: 'number',
      description: 'Maximum results to return (default 100, max 500).',
      default: 100,
    },
    cursor: {
      type: 'string',
      description:
        'Opaque pagination cursor from a previous response\'s `next_cursor` (W3 — ' +
        'RETRIEVAL_PLANE_ELEVATION_PLAN §R-2 item 4). Embeds the offset to continue from AND ' +
        'a fingerprint of the filters that produced it. Replaying a cursor with a DIFFERENT ' +
        '`entity_class` than the call that minted it is detected: the response restarts at ' +
        'offset 0 for the new filter and sets judgment_flags: ["cursor_filter_mismatch"] ' +
        'instead of silently returning the wrong family\'s next page.',
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

      // W3 (RETRIEVAL_PLANE_ELEVATION_PLAN §R-2 item 4 / master brief §E) — cursor filter/sort
      // fingerprint. `entity_class` is this capability's only facet (there is no sort param),
      // so the fingerprint is computed over exactly that. Replaying a cursor minted under a
      // DIFFERENT entity_class must never silently splice into this call's (different) result
      // family at the stale offset — checkCursorFingerprint resets to offset 0 and reports the
      // mismatch instead.
      const currentFingerprint = computeFilterFingerprint({ entity_class: resolvedClass ?? null })
      const cursorArg = args.cursor as string | undefined
      const cursorCheck = checkCursorFingerprint(cursorArg, currentFingerprint)
      const offset = cursorCheck.offset

      const params: unknown[] = [limit, offset]

      let sql =
        `SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa, synonyms
         FROM brahma_ontology`

      if (resolvedClass) {
        sql += ` WHERE entity_class = $3`
        params.push(resolvedClass)
      }

      sql += ` ORDER BY entity_class, canonical_name_en LIMIT $1 OFFSET $2`

      // WP-1.5 (LCA-18/LCA-8) receipt honesty: this tool previously set `total` to the SERVED
      // row count (capped at the LIMIT) — so a 652-entity ontology served 100 while reporting
      // `total:100`, silently hiding 552 rows (whole entity classes invisible). Run a COUNT
      // under the SAME filter for the TRUE family size, and declare the trim honestly via
      // buildHonestPagination (real total + more_available + a working cursor).
      const countSql = resolvedClass
        ? `SELECT COUNT(*)::int AS total FROM brahma_ontology WHERE entity_class = $1`
        : `SELECT COUNT(*)::int AS total FROM brahma_ontology`
      const countParams = resolvedClass ? [resolvedClass] : []

      const [result, countRes] = await Promise.all([
        query<Record<string, unknown>>(sql, params),
        query<{ total: number }>(countSql, countParams),
      ])

      const served = result.rows?.length ?? 0
      const total_entities = Number(countRes.rows[0]?.total ?? served)
      const pagination = buildHonestPagination({
        served,
        limit,
        offset,
        total: total_entities,
        filterFingerprint: currentFingerprint,
      })

      // W3 — an explicit flag, never a silently-wrong page: a mismatched cursor replay is
      // reported here rather than trusted for the stale offset (already reset to 0 above).
      const judgment_flags: string[] = cursorCheck.mismatch ? [CURSOR_FILTER_MISMATCH_FLAG] : []

      return {
        content: {
          entities: result.rows ?? [],
          served_count: served,
          // `total` is now the TRUE ontology-family size under this filter (not the served slice).
          total: total_entities,
          more_available: pagination.more_available,
          next_cursor: pagination.next_cursor,
          judgment_flags,
          ...(cursorCheck.mismatch
            ? {
                cursor_filter_mismatch_note:
                  'The supplied cursor was minted under a different entity_class filter than this ' +
                  'call. Restarted at offset 0 for the CURRENT filter instead of returning the next ' +
                  "page of the cursor's original (different) family. Re-issue the query without a " +
                  'cursor, or use the cursor from a response that matches this call\'s entity_class.',
              }
            : {}),
          budget_note: pagination.more_available
            ? `Showing ${served} of ${total_entities} entities — raise \`limit\` (max 500) or narrow by entity_class to see the rest. No rows are silently dropped.`
            : undefined,
          filters: { entity_class_requested: requestedClass ?? null, entity_class_resolved: resolvedClass ?? null },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
