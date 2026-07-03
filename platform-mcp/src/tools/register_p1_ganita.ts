/**
 * P1 Group 1 — Per-chart computed-chart tools (9 tools)
 * ======================================================
 * Exposes L1 Gaṇita capabilities that existed in the registry but were NOT previously
 * MCP-exposed. Per BA-P1 brief §Step 1 (RM §3.2 Group-1 table).
 *
 * All tools:
 *   - call callRegistryCapability() → platform /api/retrieval/capability
 *   - wrap response in RetrievalEnvelope v1 (verdict/ranking_basis null until P4/P2)
 *   - token cap: 25k default limit
 *   - scope: per_chart (chart_id required)
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
    signal: AbortSignal.timeout(25_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[p1_ganita] capability call failed (${res.status}): ${text.slice(0, 200)}`)
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) throw new Error(`[p1_ganita] capability error: ${data.error ?? 'unknown'}`)
  return data.content
}

function envelope(content: unknown, toolName: string) {
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
    query_class: 'per_chart_structural',
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

// Ayanamsha alias normalization (F-006/F-011/F-031)
const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri: 'lahiri_chitrapaksha', LAHIRI: 'lahiri_chitrapaksha', Lahiri: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha', true_chitra: 'lahiri_chitrapaksha',
}
function normalizeAyanamsha(id?: string): string {
  if (!id) return 'lahiri_chitrapaksha'
  return AYANAMSHA_ALIAS[id] ?? id
}

// Facet → L1 URI dispatch tables
const STRUCTURAL_FACET_URI: Record<string, string> = {
  aspects:      'marsys://tool/L1/get_aspects',
  conjunctions: 'marsys://tool/L1/get_aspects',
  sambandha:    'marsys://tool/L1/get_aspects',
  argala:       'marsys://tool/L1/get_argala',
  dispositors:  'marsys://tool/L1/get_dispositors',
  functional:   'marsys://tool/L1/get_dispositors',
  parivartana:  'marsys://tool/L1/get_yoga_dosha',
  yoga_fires:   'marsys://tool/L1/get_yoga_dosha',
  dosha_fires:  'marsys://tool/L1/get_yoga_dosha',
  graha_yuddha: 'marsys://tool/L1/get_yoga_dosha',
}

const CONDITION_FACET_URI: Record<string, string> = {
  dignity:  'marsys://tool/L1/get_dignity',
  avasthas: 'marsys://tool/L1/get_avasthas',
  karakas:  'marsys://tool/L1/get_karakas',
}

export function registerP1GanitaTools(server: McpServer): void {

  // ── 1. ganita_strength_get ────────────────────────────────────────────────
  server.tool(
    'ganita_strength_get',
    'Retrieve Shadbala and allied strength metrics for a chart (L1 Gaṇita). Returns planet-by-planet ' +
    'strength scores: Sthana Bala (positional), Dig Bala (directional), Kaala Bala (temporal), ' +
    'Cheshta Bala (motional), Naisargika Bala (natural), Drig Bala (aspectual) — plus Ishta-Kashta, ' +
    'Vimsopaka, and Bhava Bala. Use to determine which planets are capable of delivering significations.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_strength_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_strength', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit: limit ?? 25000, offset: offset ?? 0,
        })
        return dualOutput(envelope(data, 'ganita_strength_get'))
      } catch (err) {
        return errorOutput('ganita_strength_get', String(err), { chart_id })
      }
    }
  )

  // ── 2. ganita_structural_get ──────────────────────────────────────────────
  server.tool(
    'ganita_structural_get',
    'Retrieve structural chart relationships via a single facet-parameterized tool (L1 Gaṇita). ' +
    'ONE tool covers all inter-planetary structural layers: ' +
    'aspects (Graha Drishti), argala (planetary intervention), dispositors (sign-ruler chain), ' +
    'parivartana (exchange), yoga_fires (classical yoga patterns), dosha_fires (affliction patterns), ' +
    'conjunctions (same-sign occupancy), sambandha (relational bonds), ' +
    'functional (functional benefic/malefic roles), graha_yuddha (planetary war). ' +
    'Specify exactly one facet per call.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      facet: z.enum([
        'aspects', 'argala', 'dispositors', 'parivartana',
        'yoga_fires', 'dosha_fires', 'conjunctions', 'sambandha',
        'functional', 'graha_yuddha',
      ]).describe('Which structural relationship layer to retrieve.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, facet, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_structural_get', 'chart_id is required')
      const uri = STRUCTURAL_FACET_URI[facet]
      if (!uri) return errorOutput('ganita_structural_get', `Unknown facet: ${facet}`)
      try {
        const data = await callRegistryCapability(uri, {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
          limit: limit ?? 25000, offset: offset ?? 0, facet,
        })
        return dualOutput(envelope({ facet, ...( typeof data === 'object' && data ? data : { rows: data }) }, 'ganita_structural_get'))
      } catch (err) {
        return errorOutput('ganita_structural_get', String(err), { chart_id, facet })
      }
    }
  )

  // ── 3. ganita_condition_get ───────────────────────────────────────────────
  server.tool(
    'ganita_condition_get',
    'Retrieve planetary condition data for a chart (L1 Gaṇita). ' +
    'Three facets: dignity (exaltation/debilitation/own-sign/friend/enemy + neecha-bhanga/vargottama), ' +
    'avasthas (Baladi/Jagradadi/Deeptadi state classifications), ' +
    'karakas (Chara Karakas AK→DK via Jaimini degree + Sthira Karakas). ' +
    'Default facet: dignity. Use to assess the intrinsic capability and vitality of each planet.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      facet: z.enum(['dignity', 'avasthas', 'karakas']).optional()
        .describe("Which condition layer: 'dignity' | 'avasthas' | 'karakas'. Default: 'dignity'"),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, facet, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_condition_get', 'chart_id is required')
      const resolvedFacet = facet ?? 'dignity'
      const uri = CONDITION_FACET_URI[resolvedFacet]
      if (!uri) return errorOutput('ganita_condition_get', `Unknown facet: ${resolvedFacet}`)
      try {
        const data = await callRegistryCapability(uri, {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
          limit: limit ?? 25000, offset: offset ?? 0,
        })
        return dualOutput(envelope({ facet: resolvedFacet, ...( typeof data === 'object' && data ? data : { rows: data }) }, 'ganita_condition_get'))
      } catch (err) {
        return errorOutput('ganita_condition_get', String(err), { chart_id, facet: resolvedFacet })
      }
    }
  )

  // ── 4. ganita_sade_sati_get ───────────────────────────────────────────────
  server.tool(
    'ganita_sade_sati_get',
    'Retrieve Sade Sati and the full Saturn transit period family for a chart (L1 Gaṇita). ' +
    'Covers all 15 classical Saturn period categories: Sade Sati cycles (with peak/rising/setting phases), ' +
    'Janma Shani, Ashtama Shani, Ardhashtama Shani, Dhaiya (Kantaka/2.5 year), and compound markers. ' +
    'Use to assess Saturn\'s current influence and upcoming heavy-transit windows.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_sade_sati_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_sade_sati', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit: limit ?? 25000, offset: offset ?? 0,
        })
        return dualOutput(envelope(data, 'ganita_sade_sati_get'))
      } catch (err) {
        return errorOutput('ganita_sade_sati_get', String(err), { chart_id })
      }
    }
  )

  // ── 5. ganita_tajaka_get ──────────────────────────────────────────────────
  server.tool(
    'ganita_tajaka_get',
    'Retrieve Tajaka (Varshaphal / annual horoscopy) data for a chart (L1 Gaṇita). ' +
    'Tajaka is the Perso-Arabic annual chart system used for year-by-year prediction: ' +
    'returns the current-year annual chart planetary positions, Muntha lord, year lord (Varshesha), ' +
    'Harsha Bala scores, and Tajaka aspects (Ithasala, Ishrafa, Nakta, Yamaya, Manahoo, Khallasara). ' +
    'Use for yearly-window predictions layered over the natal Vimshottari frame.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_tajaka_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_tajik', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit: limit ?? 25000, offset: offset ?? 0,
        })
        return dualOutput(envelope(data, 'ganita_tajaka_get'))
      } catch (err) {
        return errorOutput('ganita_tajaka_get', String(err), { chart_id })
      }
    }
  )

  // ── 6. ganita_nakshatra_get ───────────────────────────────────────────────
  server.tool(
    'ganita_nakshatra_get',
    'Retrieve Nakshatra-based strength data for a chart (L1 Gaṇita). ' +
    'Returns Tara Bala (the 9-fold Tara classification of each of the 27 nakshatras relative to ' +
    'the natal Moon nakshatra: Janma/Sampat/Vipat/Kshema/Pratyak/Sadhaka/Vadha/Mitra/Ati-Mitra) ' +
    'and Chandra Bala (12-sign Moon transit strength rating). ' +
    'Essential for Muhurta and transit timing quality assessment.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_nakshatra_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_tara_chandra_bala', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit: limit ?? 25000, offset: offset ?? 0,
        })
        return dualOutput(envelope(data, 'ganita_nakshatra_get'))
      } catch (err) {
        return errorOutput('ganita_nakshatra_get', String(err), { chart_id })
      }
    }
  )

  // ── 7. ganita_yogas_get ───────────────────────────────────────────────────
  server.tool(
    'ganita_yogas_get',
    'Retrieve Yoga and Dosha detections for a chart (L1 Gaṇita). ' +
    'Covers all classical yoga types: Raja Yogas, Dhana Yogas, Pancha Mahapurusha (Ruchaka/Bhadra/' +
    'Hamsa/Malavya/Shasha), Viparita Raja, Neecha Bhanga, and Parivartana Yogas; ' +
    'plus doshas: Mangal Dosha, Kemadruma, Grahan Yoga, Shrapit, Shakata. ' +
    'Returns yoga_name, constituent planets, house conditions, and activation_flag. ' +
    'Use with L2 get_signals for cross-validated signal coverage.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_yogas_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_yoga_dosha', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit: limit ?? 25000, offset: offset ?? 0,
        })
        return dualOutput(envelope(data, 'ganita_yogas_get'))
      } catch (err) {
        return errorOutput('ganita_yogas_get', String(err), { chart_id })
      }
    }
  )

  // ── 8. phala_rectification_get ────────────────────────────────────────────
  server.tool(
    'phala_rectification_get',
    'Retrieve birth-time rectification analysis for a chart (L4 Phala). ' +
    'Returns candidate birth times with plausibility scores, the rectification methodology applied ' +
    '(event-based Tattva Shodhana, Nadi-style rising sign confirmation, Shadbala consistency check), ' +
    'and which Life Event Log entries anchor each candidate time. ' +
    'Use when birth time accuracy is in question before committing to chart interpretation.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('phala_rectification_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L4/query_rectification', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit: limit ?? 25000, offset: offset ?? 0,
        })
        return dualOutput(envelope(data, 'phala_rectification_get'))
      } catch (err) {
        return errorOutput('phala_rectification_get', String(err), { chart_id })
      }
    }
  )

  // ── 9. ganita_transit_anchors_get ─────────────────────────────────────────
  server.tool(
    'ganita_transit_anchors_get',
    'Retrieve natal transit anchor data for a chart (L1 Gaṇita — ga_transit_anchors table). ' +
    'Returns the natal sign, house-from-Moon count, and absolute sidereal degree for each of the ' +
    '9 grahas (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu) across all 5 ayanamshas. ' +
    '45 rows per chart. These anchors are the substrate for all Gochara (transit) computations: ' +
    'sign-ingress triggers, degree-exact conjunctions, Vedha/obstruction rules, ' +
    'and Ashtakavarga bindu scoring per transit sign.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha filter (e.g. 'lahiri_chitrapaksha'). Omit for all 5."),
      graha: z.string().optional().describe('Filter to one graha: sun/moon/mars/mercury/jupiter/venus/saturn/rahu/ketu.'),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 50, max: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, graha, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_transit_anchors_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_transit_anchors', {
          chart_id, ayanamsha_id: ayanamsha_id ? normalizeAyanamsha(ayanamsha_id) : undefined,
          graha, limit: limit ?? 50, offset: offset ?? 0,
        })
        return dualOutput(envelope(data, 'ganita_transit_anchors_get'))
      } catch (err) {
        return errorOutput('ganita_transit_anchors_get', String(err), { chart_id })
      }
    }
  )
}
