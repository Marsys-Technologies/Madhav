/**
 * P1 Group 3 — Synthesis-adjacent surface tools (3 tools)
 * =========================================================
 * Exposes L5 Mīmāṃsā, L2 Bodha, and L3 Kāla capabilities
 * that existed in the registry but were NOT previously MCP-exposed.
 * Per BA-P1 brief §Step 3.
 *
 * mimamsa_insight_get  → marsys://tool/L5/query_insights (PD-1: 14 rows, STRUCTURAL mode)
 * bodha_discoveries_get → bodha_discoveries table (acharya-grade cross-domain observations)
 * kala_life_arc_get    → marsys://tool/L3/query_life_arc (kala_jivana_parva biographical parvas)
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function callRegistryCapability(uri: string, args: Record<string, unknown>): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-mcp-internal-token': MCP_INTERNAL_TOKEN },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(20_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[p1_synthesis] capability call failed (${res.status}): ${text.slice(0, 200)}`)
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) throw new Error(`[p1_synthesis] capability error: ${data.error ?? 'unknown'}`)
  return data.content
}

async function platformQuery(sql: string, params: unknown[]): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-mcp-internal-token': MCP_INTERNAL_TOKEN },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) throw new Error(`[p1_synthesis] platform DB query failed: ${res.status}`)
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

function envelope(content: unknown, toolName: string, queryClass: string) {
  return {
    envelope_version: 'v1',
    tool: toolName,
    verdict: null,
    ranking_basis: null,
    grounding: { fact_ids: [], citations: [], grounding_score: null },
    pagination: { offset: 0, limit: 0, total: null, next_cursor: null },
    drill_pointers: [],
    judgment_flags: [],
    insight_type: null,
    query_class: queryClass,
    content,
  }
}

function dualOutput(data: unknown) {
  return {
    structuredContent: { type: 'object' as const, object: data },
    content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }],
  }
}

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  return { ...dualOutput({ ok: false, error: message, tool, ...extra }), isError: true as const }
}

export function registerP1SynthesisTools(server: McpServer): void {

  // ── 1. mimamsa_insight_get ────────────────────────────────────────────────
  server.tool(
    'mimamsa_insight_get',
    'Retrieve L5 Mīmāṃsā insight units for a chart. ' +
    'Returns calibrated insight units from the mimamsa_insight_units table: ' +
    'calibrated outlooks (prediction→outcome match scores), manifestation-grammar learnings, ' +
    'emergent-law discoveries (pattern candidates from cross-chart mining), ' +
    'load-bearing conclusions (the chart\'s most consequential structural claims), ' +
    'and negative-knowledge statements (what this chart rules out). ' +
    'IMPORTANT: The system is in STRUCTURAL mode (L5 SEALED per BA build arc). ' +
    'calibration_status=\'prior_only\' — empirical scores populate as outcome data accrues. ' +
    'All units carry provenance chains back to L1 chart_facts.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      insight_type: z.enum([
        'calibrated_outlook', 'manifestation_grammar', 'emergent_law',
        'load_bearing', 'negative_knowledge',
      ]).optional().describe('Filter by insight type. Omit for all types.'),
      domain: z.string().optional().describe('Filter by life domain (career, health, relationship, wealth, etc.).'),
      min_rank: z.number().min(0).max(1).optional().describe('Minimum rank_consequence threshold (0..1, default: 0).'),
      top_k: z.number().int().min(1).max(200).optional().describe('Max insight units (default: 30, max: 200).'),
      include_negative_knowledge: z.boolean().optional()
        .describe('Include is_negative_knowledge=true rows (default: true).'),
    },
    async ({ chart_id, insight_type, domain, min_rank, top_k, include_negative_knowledge }) => {
      if (!chart_id) return errorOutput('mimamsa_insight_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L5/query_insights', {
          chart_id, insight_type, domain,
          min_rank: min_rank ?? 0,
          top_k: top_k ?? 30,
          include_negative_knowledge: include_negative_knowledge !== false,
        })
        const wrapped = {
          calibration_status: 'prior_only',
          mode: 'STRUCTURAL',
          note: 'L5 Mīmāṃsā is SEALED in STRUCTURAL mode. Empirical calibration accrues as outcome data is recorded.',
          ...(typeof data === 'object' && data ? data : { content: data }),
        }
        return dualOutput(envelope(wrapped, 'mimamsa_insight_get', 'synthesis_calibration'))
      } catch (err) {
        return errorOutput('mimamsa_insight_get', String(err), { chart_id })
      }
    }
  )

  // ── 2. bodha_discoveries_get ──────────────────────────────────────────────
  server.tool(
    'bodha_discoveries_get',
    'Retrieve acharya-grade cross-domain discoveries for a chart from L2 Bodha. ' +
    'Queries the bodha_discoveries table — the "Bimba" (image/reflection) layer of Bodha, ' +
    'which contains the system\'s highest-signal cross-domain observations: ' +
    'patterns that surface only when multiple L1 data streams are synthesized. ' +
    'Examples: Saturn-Ketu mutual aspect amplifying 8th house themes across D1+D9+D10; ' +
    'strong Atmakaraka-Arudha Pada relationship forecasting public prominence. ' +
    'Returns discovery_id, domain tags, supporting fact_ids, salience score, and narrative.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      domain:   z.string().optional().describe('Filter by life domain (career, health, relationship, wealth, etc.).'),
      min_salience: z.number().min(0).max(1).optional().describe('Minimum salience score (0..1, default: 0).'),
      limit:    z.number().int().min(1).max(200).optional().describe('Max results (default: 30, max: 200).'),
      offset:   z.number().int().min(0).optional().describe('Pagination offset (default: 0).'),
    },
    async ({ chart_id, domain, min_salience, limit, offset }) => {
      if (!chart_id) return errorOutput('bodha_discoveries_get', 'chart_id is required')
      try {
        const params: unknown[] = [chart_id]
        const filters: string[] = ['chart_id = $1']
        if (domain) { params.push(domain); filters.push(`domain = $${params.length}`) }
        if (min_salience != null && min_salience > 0) {
          params.push(min_salience); filters.push(`salience_score >= $${params.length}`)
        }
        params.push(limit ?? 30)
        params.push(offset ?? 0)
        const sql = `
          SELECT *
          FROM bodha_discoveries
          WHERE ${filters.join(' AND ')}
          ORDER BY salience_score DESC NULLS LAST
          LIMIT $${params.length - 1} OFFSET $${params.length}
        `
        const result = await platformQuery(sql, params)
        return dualOutput(envelope({
          discoveries: result.rows,
          total: result.rows.length,
          filters: { domain, min_salience },
          source_table: 'bodha_discoveries',
        }, 'bodha_discoveries_get', 'synthesis_cross_domain'))
      } catch (err) {
        return errorOutput('bodha_discoveries_get', String(err), { chart_id })
      }
    }
  )

  // ── 3. kala_life_arc_get ──────────────────────────────────────────────────
  server.tool(
    'kala_life_arc_get',
    'Retrieve the biographical life-arc (Jīvana Parva) for a chart from L3 Kāla. ' +
    'Returns the kala_jivana_parva view: the life divided into named biographical periods ' +
    '(Parvas) based on Vimshottari mahadasha + dasha-sequence logic. Each Parva covers ' +
    'a named life stage with its dominant dasha lord, expected thematic domain, ' +
    'start/end years (age-based), and cross-links to LEL events that fell within that Parva. ' +
    'Use as the temporal backbone for reading the native\'s life story.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      include_lel_events: z.boolean().optional()
        .describe('Include Life Event Log matches for each Parva (default: true).'),
      limit:   z.number().int().min(1).max(100).optional().describe('Max Parvas (default: 50).'),
      offset:  z.number().int().min(0).optional().describe('Pagination offset (default: 0).'),
    },
    async ({ chart_id, include_lel_events, limit, offset }) => {
      if (!chart_id) return errorOutput('kala_life_arc_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L3/query_life_arc', {
          chart_id,
          include_lel_events: include_lel_events !== false,
          limit: limit ?? 50,
          offset: offset ?? 0,
        })
        return dualOutput(envelope(data, 'kala_life_arc_get', 'temporal_life_arc'))
      } catch (err) {
        return errorOutput('kala_life_arc_get', String(err), { chart_id })
      }
    }
  )
}
