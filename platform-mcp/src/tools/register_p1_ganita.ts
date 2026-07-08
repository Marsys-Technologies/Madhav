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
// R5 W0b-codegen (design §19): imports the GENERATED envelope module — the mirror that
// used to live at '../lib/envelope.js' was hand-written and has been deleted. See
// scripts/generate_envelope.ts for the generator; src/generated/envelope.ts is its output.
import {
  buildRetrievalEnvelope,
  resolveEnvelopeFormat,
  extractGroundingFromFactRows,
  buildEpistemicSummary,
  type EnvelopeFormat,
  type ChartHeader,
} from '../generated/envelope.js'

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

// R5 W0a punch-list (P3): envelope changes are additive-only (R5_AUTHORITY_DOSSIER §2) — every
// field below still ships, verbatim, on every call. The fix is that `pagination` is no longer
// unconditionally hollow: callers that already know their real offset/limit/total (the content
// they just fetched) may pass it through instead of it being silently dropped on the floor.
//
// R5 W0b (unified populated envelope, design §10/§19): `envelope()` now delegates to the
// shared buildRetrievalEnvelope() (canonical home: platform/src/lib/retrieval/envelope.ts;
// this process's mirror: ../lib/envelope.ts). Three-arg call sites are UNCHANGED — they still
// get the exact legacy shape (format defaults to 'legacy', v3Extras is undefined). Call sites
// that want the populated v3 envelope pass `format='v3'` + `v3Extras`; those extras are
// silently ignored under 'legacy' so existing consumers see a byte-identical response
// (brief §6.3 consumer format negotiation — default legacy until the W4 battery passes).
function envelope(
  content: unknown,
  toolName: string,
  pagination?: { offset: number; limit: number; total: number | null },
  format: EnvelopeFormat = 'legacy',
  v3Extras?: {
    chart_header?: ChartHeader | null
    verdict?: unknown
    ranking_basis?: Record<string, unknown> | null
    grounding?: { fact_ids: string[]; citations: string[]; grounding_score: number | null }
    drill_pointers?: { instrument: string; hint: string }[]
    judgment_flags?: string[]
    as_of_date?: string
    epistemic?: ReturnType<typeof buildEpistemicSummary>
  },
) {
  return buildRetrievalEnvelope(
    {
      tool: toolName,
      content,
      pagination,
      chart_header: v3Extras?.chart_header,
      verdict: v3Extras?.verdict,
      ranking_basis: v3Extras?.ranking_basis,
      grounding: v3Extras?.grounding,
      drill_pointers: v3Extras?.drill_pointers,
      judgment_flags: v3Extras?.judgment_flags,
      as_of_date: v3Extras?.as_of_date,
      epistemic: v3Extras?.epistemic,
    },
    format,
  )
}

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

// R5 W0a punch-list (P3, 174KB yogas overflow): dropped the `null, 2` pretty-print indent —
// pure serialization padding (~30-40% of wire bytes on large row sets), no information content.
// structuredContent + content dual-output is retained (provider-spec obligation, not padding).
// S3 fix (R5 W0a perf lane): text duplicate suppressed above threshold (structuredContent already
// carries the full payload) — see JL-003 for the 50KB threshold ruling.
function dualOutput(data: unknown) {
  const structuredContent = { type: 'object' as const, object: data }
  const json = JSON.stringify(data)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return { structuredContent, content: [{ type: 'text' as const, text: '[large payload — see structuredContent]' }] }
  }
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
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

// R5 W0b-codegen parity gate (design §19 STRANGLER, brief §6.2): the three pilot instruments'
// input schemas are exported as named consts so the parity test can import the SAME zod
// schema objects the live handwritten shim registers — no re-typed duplicate schema in the
// test file. Compared against src/generated/registry_shims.ts's independently-generated
// schemas (derived from the registry CapabilityDescriptor) for byte-identical parse behavior.
export const ganitaStrengthGetInputSchema = {
  chart_id: z.string().uuid().describe('Chart UUID. Required.'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
  limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
  offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
}

export const ganitaSadeSatiGetInputSchema = {
  chart_id: z.string().uuid().describe('Chart UUID. Required.'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
  limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
  offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
}

export const ganitaTajakaGetInputSchema = {
  chart_id: z.string().uuid().describe('Chart UUID. Required.'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
  limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
  offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
}

export function registerP1GanitaTools(server: McpServer): void {

  // ── 1. ganita_strength_get ────────────────────────────────────────────────
  server.tool(
    'ganita_strength_get',
    'Retrieve Shadbala and allied strength metrics for a chart (L1 Gaṇita). Returns planet-by-planet ' +
    'strength scores: Sthana Bala (positional), Dig Bala (directional), Kaala Bala (temporal), ' +
    'Cheshta Bala (motional), Naisargika Bala (natural), Drig Bala (aspectual) — plus Ishta-Kashta, ' +
    'Vimsopaka, and Bhava Bala. Use to determine which planets are capable of delivering significations.',
    ganitaStrengthGetInputSchema,
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
    ganitaSadeSatiGetInputSchema,
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
    ganitaTajakaGetInputSchema,
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
    'Use with L2 get_signals for cross-validated signal coverage. ' +
    'response_format=\'v3\' (opt-in; default \'legacy\') returns the R5 unified envelope: ' +
    'a populated verdict (fired-yoga/dosha/flag counts), grounding (fact_ids + citations from ' +
    'this response\'s own rows), ranking_basis (the actual serve order), drill_pointers ' +
    '(query_signals for cross-validated salience, mimamsa_insight_get for calibrated outlooks), ' +
    'judgment_flags (e.g. zero-row / truncated-page honesty markers), and chart_header.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      // R5 W0a punch-list (P3): the prior default (25000, echoing an unbounded schema promise)
      // silently overrode get_yoga_dosha's own sane default (500) and inflated the response
      // to 174KB. The handler's hard cap is 2000 rows (get_yoga_dosha.ts Math.min(...,2000)) —
      // schema bounds now tell the truth about what the server will actually return.
      limit: z.number().int().min(1).max(2000).optional().describe('Max rows (default: 500, hard cap: 2000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
      // R5 W0b consumer format negotiation (brief §6.3): default 'legacy' — byte-identical to
      // the pre-W0b response. 'v3' opts in to the populated unified envelope (closes P3).
      response_format: z.enum(['legacy', 'v3']).optional()
        .describe("Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/ranking_basis/drill_pointers/chart_header — opt-in until the R5 W4 battery flips the default)."),
    },
    async ({ chart_id, ayanamsha_id, limit, offset, response_format }) => {
      if (!chart_id) return errorOutput('ganita_yogas_get', 'chart_id is required')
      try {
        const resolvedOffset = offset ?? 0
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        const format = resolveEnvelopeFormat(response_format)
        const data = await callRegistryCapability('marsys://tool/L1/get_yoga_dosha', {
          chart_id, ayanamsha_id: resolvedAyanamsha, limit, offset: resolvedOffset,
        }) as { total?: number; rows?: Record<string, unknown>[] } | undefined
        const total = typeof data?.total === 'number' ? data.total : null

        if (format !== 'v3') {
          return dualOutput(envelope(data, 'ganita_yogas_get', {
            offset: resolvedOffset,
            limit: limit ?? 500,
            total,
          }))
        }

        // ── v3 population (design §10; closes P3's hollow-envelope defect for this instrument) ──
        const rows = data?.rows ?? []

        // verdict: honest aggregation of the CATEGORIES ALREADY SERVED IN THIS RESPONSE (no new
        // computation — B.10). yoga_label/dosha_label rows ARE the fired entries (this chart's
        // engine writes fired items directly; there is no separate boolean yoga_fires/dosha_fires
        // row for the served categories — see JL-004).
        const categoryCounts: Record<string, number> = {}
        for (const r of rows) {
          const cat = String(r['fact_category'] ?? 'unknown')
          categoryCounts[cat] = (categoryCounts[cat] ?? 0) + 1
        }
        const verdict = {
          yogas_fired: categoryCounts['yoga_label'] ?? 0,
          doshas_fired: categoryCounts['dosha_label'] ?? 0,
          bhadra_flag_rows: categoryCounts['bhadra_flag'] ?? 0,
          panchaka_flag_rows: categoryCounts['panchaka_flag'] ?? 0,
          category_counts: categoryCounts,
          note: 'Counts are of ROWS SERVED IN THIS PAGE only — see pagination.total for the full count.',
        }

        const grounding = extractGroundingFromFactRows(rows)

        const judgment_flags: string[] = []
        if (rows.length === 0) judgment_flags.push('zero_rows_returned')
        if (total !== null && resolvedOffset + rows.length < total) judgment_flags.push('partial_page_more_available')

        const ranking_basis = {
          mode: 'catalog_order',
          fields: ['fact_category', 'ayanamsha_id', 'fact_key'],
          note: 'get_yoga_dosha orders alphabetically by category/key, not by strength or salience — ' +
            'for salience-ranked cross-validation use query_signals(signal_type_class=yoga|dosha).',
        }

        const drill_pointers = [
          { instrument: 'query_signals', hint: 'signal_type_class=yoga|dosha for salience-ranked cross-validation against L2 Bodha.' },
          { instrument: 'mimamsa_insight_get', hint: 'calibrated_outlook / load_bearing insight units built on top of these firings.' },
        ]

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability('marsys://tool/L1/get_chart_header', {
            chart_id, ayanamsha_id: resolvedAyanamsha,
          }) as ChartHeader
        } catch {
          chart_header = null // frame-safety header is best-effort; never fails the instrument
        }

        const epistemic = buildEpistemicSummary({
          verifiedFraction: grounding.grounding_score,
          note: 'verified_fraction = share of this page\'s rows with verification_pass_status=two_pass_verified.',
        })

        return dualOutput(envelope(data, 'ganita_yogas_get', {
          offset: resolvedOffset,
          limit: limit ?? 500,
          total,
        }, 'v3', { chart_header, verdict, ranking_basis, grounding, drill_pointers, judgment_flags, epistemic }))
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
