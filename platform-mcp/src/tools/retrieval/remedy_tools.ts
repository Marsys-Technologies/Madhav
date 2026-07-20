/**
 * retrieval/remedy_tools.ts — Stream F Brahmagyan Remedy tools for MCP server
 *
 * Registers 7 tools against brahma_remedy_corpus:
 *   1. query_remedies
 *   2. query_remedies_for_chart
 *   3. list_remedies_by_category
 *   4. read_remedy
 *   5. query_tantric_remedies
 *   6. query_remedies_by_planet
 *   7. query_mantras
 *
 * ZERO LLM — all retrieval is deterministic SQL.
 * Source: BPHS Ch.91-94, Phaladeepika Ch.27-28, Brihat Samhita Ch.53
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { callPlatformPrimitive } from '../../client.js'
import type { Principal, McpEnvelopeError } from '../../types.js'
import { budgetMcpContent } from '../../lib/response_budget.js'

// ── Registration helper ────────────────────────────────────────────────────────

export function registerRemedyTools(server: McpServer, getPrincipal: () => Principal): void {

  // ── 1. query_remedies ──────────────────────────────────────────────────────

  server.tool(
    'query_remedies',
    'Query brahma_remedy_corpus by planet, domain, and/or category. Returns classical remedy prescriptions with mantra and source attestation.',
    {
      planet: z.string().optional().describe('Planet name e.g. Saturn, Moon, Venus'),
      domain: z.string().optional().describe('Domain e.g. career, health, marriage, spirituality'),
      category: z.string().optional().describe('Category: mantras | gemstones | charity | vrata | yantras | puja | tantric | ayurvedic | vastu | behavioral'),
      top_k: z.number().int().min(1).max(50).default(10).describe('Max rows to return'),
    },
    async ({ planet, domain, category, top_k }) => {
      const { status, envelope } = await callPlatformPrimitive(
        'query_remedies',
        { planet, domain, category, top_k },
        getPrincipal(),
      )
      if (status !== 200 || !envelope.ok) {
        return { content: [{ type: 'text' as const, text: JSON.stringify({ error: (envelope as McpEnvelopeError).error?.message ?? status, tool: 'query_remedies' }) }], isError: true }
      }
      const rows = envelope.result as Record<string, unknown>[]
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent({ query_remedies: rows, count: rows.length }, 'query_remedies')) }],
      }
    },
  )

  // ── 2. query_remedies_for_chart ───────────────────────────────────────────

  server.tool(
    'query_remedies_for_chart',
    'Return remedies relevant to a chart affliction. Pass affliction as planet name or domain keyword.',
    {
      affliction: z.string().describe('Planet name or domain keyword e.g. "Saturn", "health"'),
      top_k: z.number().int().min(1).max(20).default(5),
    },
    async ({ affliction, top_k }) => {
      const { status, envelope } = await callPlatformPrimitive(
        'query_remedies_for_chart',
        { affliction, top_k },
        getPrincipal(),
      )
      if (status !== 200 || !envelope.ok) {
        return { content: [{ type: 'text' as const, text: JSON.stringify({ error: (envelope as McpEnvelopeError).error?.message ?? status, tool: 'query_remedies_for_chart' }) }], isError: true }
      }
      const rows = envelope.result as Record<string, unknown>[]
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent({ query_remedies_for_chart: rows, affliction, count: rows.length }, 'query_remedies_for_chart')) }],
      }
    },
  )

  // ── 3. list_remedies_by_category ─────────────────────────────────────────

  server.tool(
    'list_remedies_by_category',
    'List all remedies in one category. 10 categories: mantras | gemstones | charity | vrata | yantras | puja | tantric | ayurvedic | vastu | behavioral',
    {
      category: z.enum([
        'mantras', 'gemstones', 'charity', 'vrata', 'yantras',
        'puja', 'tantric', 'ayurvedic', 'vastu', 'behavioral',
      ]).describe('Remedy category'),
    },
    async ({ category }) => {
      const { status, envelope } = await callPlatformPrimitive(
        'list_remedies_by_category',
        { category },
        getPrincipal(),
      )
      if (status !== 200 || !envelope.ok) {
        return { content: [{ type: 'text' as const, text: JSON.stringify({ error: (envelope as McpEnvelopeError).error?.message ?? status, tool: 'list_remedies_by_category' }) }], isError: true }
      }
      const rows = envelope.result as Record<string, unknown>[]
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent({ list_remedies_by_category: rows, category, count: rows.length }, 'list_remedies_by_category')) }],
      }
    },
  )

  // ── 4. read_remedy ────────────────────────────────────────────────────────

  server.tool(
    'read_remedy',
    'Fetch full remedy record by remedy_id, including ingredients_jsonb and timing_rules_jsonb.',
    {
      remedy_id: z.string().describe('The unique remedy identifier e.g. man_sun_gayatri_001'),
    },
    async ({ remedy_id }) => {
      const { status, envelope } = await callPlatformPrimitive(
        'read_remedy',
        { remedy_id },
        getPrincipal(),
      )
      if (status !== 200 || !envelope.ok) {
        return { content: [{ type: 'text' as const, text: JSON.stringify({ error: (envelope as McpEnvelopeError).error?.message ?? status, tool: 'read_remedy' }) }], isError: true }
      }
      const row = envelope.result as Record<string, unknown> | null
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent({ read_remedy: row ?? null, found: row !== null }, 'read_remedy')) }],
      }
    },
  )

  // ── 5. query_tantric_remedies ─────────────────────────────────────────────

  server.tool(
    'query_tantric_remedies',
    'Query tantric remedies only. All rows have passed the tantric careful-inclusion gate (BPHS/Phaladeepika sources only). Optional filter by deity or planet.',
    {
      deity: z.string().optional().describe('Deity name e.g. Shiva, Durga'),
      planet: z.string().optional().describe('Planet name e.g. Saturn, Rahu'),
    },
    async ({ deity, planet }) => {
      const { status, envelope } = await callPlatformPrimitive(
        'query_tantric_remedies',
        { deity, planet },
        getPrincipal(),
      )
      if (status !== 200 || !envelope.ok) {
        return { content: [{ type: 'text' as const, text: JSON.stringify({ error: (envelope as McpEnvelopeError).error?.message ?? status, tool: 'query_tantric_remedies' }) }], isError: true }
      }
      const rows = envelope.result as Record<string, unknown>[]
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent({ query_tantric_remedies: rows, count: rows.length }, 'query_tantric_remedies')) }],
      }
    },
  )

  // ── 6. query_remedies_by_planet ───────────────────────────────────────────

  server.tool(
    'query_remedies_by_planet',
    'Return all remedies for a given planet across all categories — a complete upaya profile.',
    {
      planet: z.enum(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'])
        .describe('Planet name'),
    },
    async ({ planet }) => {
      const { status, envelope } = await callPlatformPrimitive(
        'query_remedies_by_planet',
        { planet },
        getPrincipal(),
      )
      if (status !== 200 || !envelope.ok) {
        return { content: [{ type: 'text' as const, text: JSON.stringify({ error: (envelope as McpEnvelopeError).error?.message ?? status, tool: 'query_remedies_by_planet' }) }], isError: true }
      }
      const rows = envelope.result as Record<string, unknown>[]
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent({ query_remedies_by_planet: rows, planet, count: rows.length }, 'query_remedies_by_planet')) }],
      }
    },
  )

  // ── 7. query_mantras ──────────────────────────────────────────────────────

  server.tool(
    'query_mantras',
    'Return all mantra remedies (category=mantras) for a planet with Sanskrit mantra and classical source.',
    {
      planet: z.string().optional().describe('Planet name; omit to return all mantras'),
    },
    async ({ planet }) => {
      const { status, envelope } = await callPlatformPrimitive(
        'query_mantras',
        { planet },
        getPrincipal(),
      )
      if (status !== 200 || !envelope.ok) {
        return { content: [{ type: 'text' as const, text: JSON.stringify({ error: (envelope as McpEnvelopeError).error?.message ?? status, tool: 'query_mantras' }) }], isError: true }
      }
      const rows = envelope.result as Record<string, unknown>[]
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent({ query_mantras: rows, planet: planet ?? 'all', count: rows.length }, 'query_mantras')) }],
      }
    },
  )
}
