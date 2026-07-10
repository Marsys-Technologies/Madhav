/**
 * tools/l0_brahmagyan.ts — L0 Brahmagyan capability wrappers for MCP
 *
 * Registers the 5 L0 pattern-validation capabilities:
 *   1. resolve_entity    — marsys://tool/L0/resolve_entity
 *   2. list_entities     — marsys://tool/L0/list_entities
 *   3. asset_registry_all — marsys://resource/asset-registry/all (as a tool for MCP compat)
 *   4. asset_registry_l0  — marsys://resource/asset-registry/L0
 *   5. intent_classify    — marsys://prompt/intent-classify (as a tool for MCP compat)
 *
 * These are the first 5 L0FR capabilities — they serve as pattern validation
 * for the unified retrieval registry + MCP parity architecture.
 *
 * DB connection: uses PLATFORM_URL sidecar via REST (no direct PG from MCP).
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

// REMEDIATION D7: NATIVE_CHART_ID removed.
// intent_classify is a global tool — it MUST NOT stamp a chart_id on every call.
// chart_agnostic_gate RULE-6: global scope must not have chart_id in required_inputs.
const PLATFORM_URL = process.env['PLATFORM_URL'] ?? 'http://localhost:3000'

// ── Helper: platform API call ─────────────────────────────────────────────────

// R6 0a-envauth (R-16/O-5): this helper sent only Content-Type — no auth headers
// at all — while its siblings in this same file (resolve_entity, list_entities,
// below) already carry the 3-header pattern (x-mcp-internal-token, x-mcp-user,
// x-mcp-key-id) required by platform's service-to-service + principal auth gate.
// asset_registry_all / asset_registry_l0 (the only two callers of platformGet)
// were the R-16/O-5 401s on GET /api/cockpit/registry. Matched to the proven
// working pattern below rather than inventing a new one.
async function platformGet(path: string): Promise<unknown> {
  const url = `${PLATFORM_URL}${path}`
  const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': MCP_INTERNAL_TOKEN,
      'x-mcp-user': 'mcp-internal',
      'x-mcp-key-id': 'mcp-internal',
    },
  })
  if (!res.ok) {
    throw new Error(`[l0_brahmagyan] platform GET ${path} → ${res.status}`)
  }
  return res.json()
}

// ── 1. resolve_entity ─────────────────────────────────────────────────────────

const ResolveEntityInput = z.object({
  name: z.string().describe(
    'Entity name to resolve — Sanskrit or English. Case-insensitive.'
  ),
})

export function registerResolveEntityTool(server: McpServer): void {
  server.tool(
    'resolve_entity',
    'Resolve a Jyotish entity name (Sanskrit or English) to its canonical form. ' +
    'Returns canonical_id, entity_class (graha / nakshatra / rashi / etc.), and synonym list. ' +
    'Use before any chart or corpus query to normalise the entity reference.',
    ResolveEntityInput.shape,
    async (params) => {
      const input = ResolveEntityInput.parse(params)
      try {
        // F-015: primitives route is POST-only — changed from platformGet (GET) to POST
        const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
        const res = await fetch(`${PLATFORM_URL}/api/mcp/primitives/resolve_entity`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-mcp-internal-token': MCP_INTERNAL_TOKEN,
            'x-mcp-user': 'mcp-internal',
            'x-mcp-key-id': 'mcp-internal',
          },
          body: JSON.stringify({ params: { name: input.name } }),
          signal: AbortSignal.timeout(10_000),
        })
        if (!res.ok) throw new Error(`resolve_entity failed: ${res.status}`)
        const result = await res.json()
        return { content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, message: msg, input: input.name }, null, 2) }],
          isError: true,
        }
      }
    }
  )
}

// ── 2. list_entities ──────────────────────────────────────────────────────────

// R-27 fix: brahma_ontology.entity_class actually stores 'planet'/'sign'/'house' (verified
// against the l0_ontology.py seed source) — 'graha'/'rashi'/'bhava' are accepted here as
// Sanskrit synonyms and normalized server-side (list_entities.ts's ENTITY_CLASS_ALIAS), never
// silently matching zero rows. 'yoga'/'karana' have no dedicated top-level class; requesting
// them now returns an explicit empty_reason instead of a silent empty array.
const ENTITY_CLASSES = [
  'graha', 'planet', 'nakshatra', 'rashi', 'sign', 'bhava', 'house', 'upagraha',
  'dasha_system', 'domain', 'concept', 'karaka', 'aspect_type', 'remedy_type', 'school', 'text',
  'yoga', 'karana',
] as const

const ListEntitiesInput = z.object({
  entity_class: z.enum(ENTITY_CLASSES).optional().describe(
    'Optional: filter by entity class. Accepts the stored vocabulary (planet, sign, house, ' +
    'nakshatra, upagraha, dasha_system, domain, concept, karaka, aspect_type, remedy_type, ' +
    'school, text) or the Sanskrit synonyms graha (→planet), rashi (→sign), bhava (→house). ' +
    '"yoga"/"karana" are accepted but return an explicit empty_reason (no dedicated class exists ' +
    'for them — see query_yoga_catalog for a yoga catalog instead).'
  ),
  limit: z.number().min(1).max(500).optional().default(100).describe(
    'Maximum results to return (default 100, max 500)'
  ),
})

export function registerListEntitiesTool(server: McpServer): void {
  server.tool(
    'list_entities',
    'List all Jyotish entities in the canonical ontology, optionally filtered by class. ' +
    'Returns canonical_id, entity_class, canonical names, and synonym list for each entity.',
    ListEntitiesInput.shape,
    async (params) => {
      const input = ListEntitiesInput.parse(params)
      try {
        // F-015: primitives route is POST-only — changed from platformGet (GET) to POST
        const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
        const body: Record<string, unknown> = { limit: input.limit }
        if (input.entity_class) body['entity_class'] = input.entity_class
        const res = await fetch(`${PLATFORM_URL}/api/mcp/primitives/list_entities`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-mcp-internal-token': MCP_INTERNAL_TOKEN,
            'x-mcp-user': 'mcp-internal',
            'x-mcp-key-id': 'mcp-internal',
          },
          body: JSON.stringify({ params: body }),
          signal: AbortSignal.timeout(10_000),
        })
        if (!res.ok) throw new Error(`list_entities failed: ${res.status}`)
        const result = await res.json()
        return { content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, message: msg }, null, 2) }],
          isError: true,
        }
      }
    }
  )
}

// ── 3. asset_registry_all ─────────────────────────────────────────────────────

const AssetRegistryAllInput = z.object({})

export function registerAssetRegistryAllTool(server: McpServer): void {
  server.tool(
    'asset_registry_all',
    'Full asset_registry snapshot: all build assets across all layers (L0–L5). ' +
    'Includes asset_id, layer, names, target_floor, scope, is_active. ' +
    'Use to understand available data assets before planning retrieval.',
    AssetRegistryAllInput.shape,
    async (_params) => {
      try {
        const result = await platformGet('/api/cockpit/registry')
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, message: msg }, null, 2) }],
          isError: true,
        }
      }
    }
  )
}

// ── 4. asset_registry_l0 ─────────────────────────────────────────────────────

const AssetRegistryL0Input = z.object({})

export function registerAssetRegistryL0Tool(server: McpServer): void {
  server.tool(
    'asset_registry_l0',
    'L0 Brahmagyan asset_registry slice: all brahmagyan layer assets ' +
    '(shastra texts, sutravali rules, ontology, remedies, ephemeris, etc.). ' +
    'Includes current row counts and target_floor for each asset.',
    AssetRegistryL0Input.shape,
    async (_params) => {
      try {
        const result = await platformGet('/api/cockpit/registry?layer=brahmagyan')
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, message: msg }, null, 2) }],
          isError: true,
        }
      }
    }
  )
}

// ── 5. intent_classify ────────────────────────────────────────────────────────

const IntentClassifyInput = z.object({
  query: z.string().describe(
    'The natural-language query to classify for routing intent.'
  ),
})

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

export function registerIntentClassifyTool(server: McpServer): void {
  server.tool(
    'intent_classify',
    'Classify a Jyotish query into one of the canonical intent categories ' +
    '(dasha_timing, transit_analysis, yoga_identification, planet_strength, ' +
    'house_analysis, remedy_lookup, panchanga, classical_rule, chart_overview, ' +
    'prediction_calibration, unknown). Returns the rendered prompt for the LLM.',
    IntentClassifyInput.shape,
    // REMEDIATION D7: removed chart_id: NATIVE_CHART_ID from response.
    // intent_classify is chart-agnostic (global tool) — must not inject a chart_id.
    async (params) => {
      const input = IntentClassifyInput.parse(params)
      const rendered = INTENT_CLASSIFY_TEMPLATE.replace('{{query}}', input.query)
      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify({
              prompt: rendered,
              usage: 'Pass prompt to an LLM for intent classification. Provide chart_id separately when routing.',
            }, null, 2),
          },
        ],
      }
    }
  )
}

// ── Bulk registration ─────────────────────────────────────────────────────────

export function registerL0BrahmagyanTools(server: McpServer): void {
  registerResolveEntityTool(server)
  registerListEntitiesTool(server)
  registerAssetRegistryAllTool(server)
  registerAssetRegistryL0Tool(server)
  registerIntentClassifyTool(server)
}
