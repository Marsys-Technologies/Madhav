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
import { classifyScope } from './intent_scope_classifier.js'
import { budgetMcpContent } from '../lib/response_budget.js'

// REMEDIATION D7: NATIVE_CHART_ID removed.
// intent_classify is a global tool — it MUST NOT stamp a chart_id on every call.
// chart_agnostic_gate RULE-6: global scope must not have chart_id in required_inputs.
const PLATFORM_URL = process.env['PLATFORM_URL'] ?? 'http://localhost:3000'

// ── Helper: platform API call ─────────────────────────────────────────────────

// W4-loop-1 (E-5 group1): asset_registry_all / asset_registry_l0 hit
// GET /api/cockpit/registry, which is a session-authenticated cockpit route (not
// a service-to-service MCP endpoint) and 401'd every mcp-internal call regardless
// of headers. The working twin (catalog_assets_all in register_p1_aliases.ts)
// reaches the SAME asset-registry data through the service-token-gated
// /api/retrieval/capability route via the `marsys://resource/asset-registry/*`
// URIs. Repointed both asset_registry_* tools onto that proven path.
async function callRegistryCapability(uri: string, args: Record<string, unknown>): Promise<unknown> {
  const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': MCP_INTERNAL_TOKEN,
      'x-mcp-user': 'mcp-internal',
      'x-mcp-key-id': 'mcp-internal',
    },
    body: JSON.stringify({ uri, args }),
  })
  if (!res.ok) {
    throw new Error(`[l0_brahmagyan] capability ${uri} → ${res.status}`)
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) {
    throw new Error(`[l0_brahmagyan] capability error: ${data.error ?? 'unknown'}`)
  }
  return data.content
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
        const result = budgetMcpContent(await res.json(), 'resolve_entity')
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
        const result = budgetMcpContent(await res.json(), 'list_entities')
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
        const result = budgetMcpContent(await callRegistryCapability('marsys://resource/asset-registry/all', {}), 'asset_registry_all')
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
        const result = budgetMcpContent(await callRegistryCapability('marsys://resource/asset-registry/L0', {}), 'asset_registry_l0')
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

export function registerIntentClassifyTool(server: McpServer): void {
  server.tool(
    'intent_classify',
    'Classify a Jyotish query into a Vidhi scope tuple — DETERMINISTIC rule/pattern matching ' +
    '(zero LLM inference). Returns {scope_tuple:{intent, domains[], width, depth, horizon, ' +
    'intervention, entitlement}, confidence, method:"deterministic_rules", matched_rules[], ' +
    'fallback_prompt, fallback_recommended, usage}. The scope_tuple is what the Vidhi compiler ' +
    'consumes and what a consumer echoes back for correction before execution (CR-28 / DR-8). ' +
    'When fallback_recommended is true (low confidence / unmatched intent), pass fallback_prompt ' +
    'to an LLM for a stronger classification.',
    IntentClassifyInput.shape,
    // REMEDIATION D7: intent_classify is chart-agnostic (global tool) — must not inject a chart_id.
    // CR-28 / DR-8 (DIS.021): redesigned from prompt-delegation to a deterministic scope-tuple
    // classifier; the old rendered prompt is retained as fallback_prompt.
    async (params) => {
      const input = IntentClassifyInput.parse(params)
      const result = budgetMcpContent(classifyScope(input.query), 'intent_classify')
      return {
        content: [
          { type: 'text' as const, text: JSON.stringify(result, null, 2) },
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
