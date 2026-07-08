/**
 * D7 — Registry-backed MCP Tool Bridge
 * =====================================
 * Exposes the new registry capabilities as MCP tools on the server.
 * Called from server.ts during tool registration.
 *
 * This is the "by-construction-no-drift" connection:
 *   registry.getCapability(uri).handler === the function both channels call
 *
 * All new consolidated MCP tools delegate to the same CapabilityDescriptor.handler
 * that the chat channel calls via getCapability(uri). Same handler → drift impossible.
 *
 * D7 consolidated tool surface (§2.1 of brief) — ~12 workflow-shaped tools:
 *   get_chart_orientation  → marsys://tool/L2/query_ucd
 *   get_domain_reading     → marsys://tool/L2/query_domain_reading
 *   get_signals            → marsys://tool/L2/query_signals
 *   traverse_graph         → marsys://tool/L2/traverse_chart_graph
 *   get_positions          → marsys://tool/L1/get_positions
 *   get_dashas             → marsys://tool/L1/get_dashas
 *   get_temporal_windows   → marsys://tool/L3/query_temporal_activation
 *   get_projections        → marsys://tool/L3/query_projections
 *   get_classical_citation → marsys://tool/L0/query_classical_texts
 *   get_remedies           → marsys://tool/L2/query_remedies
 *   get_chart_quality      → marsys://tool/L2/query_quality_scorecard
 *   list_assets            → marsys://resource/asset-registry/all
 *
 * Provider-spec obligations (RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC §B.i):
 *   - outputSchema + structuredContent + text fallback (dual output)
 *   - cursor pagination on list/search tools
 *   - response_format / verbosity enum on umbrella tools
 *   - UUIDs resolved to names in output
 *   - tool names: snake_case, no hyphens, ≤64 chars
 *   - transport: Streamable HTTP only (matches server.ts)
 *
 * chart_agnostic_gate: all per_chart tools require chart_id; error if missing.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
// R5 W1 (design §E-6 + brief §Lane signals_query/synthesis_query): wires get_signals
// (signals_query) and get_chart_orientation (synthesis_query) onto the W0b generated
// contract path — the SAME buildRetrievalEnvelope + response_format negotiation
// pattern register_p1_ganita.ts's ganita_yogas_get established. Imports the GENERATED
// module (not a hand-mirror) — see scripts/generate_envelope.ts / src/generated/envelope.ts.
import {
  buildRetrievalEnvelope,
  resolveEnvelopeFormat,
  type EnvelopeFormat,
  type ChartHeader,
} from '../generated/envelope.js'

// ── Platform URL (for proxy calls to the platform API) ───────────────────────

const PLATFORM_URL = (
  process.env['PLATFORM_URL'] ?? 'http://localhost:3000'
).replace(/\/$/, '')

// Service-to-service token — must match MCP_INTERNAL_TOKEN on amjis-web.
// Required by /api/retrieval/capability (F1 gate, M0.5).
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Ayanamsha normalization (F-006/F-011/F-031) ───────────────────────────────
// Signals are stored under 'lahiri_chitrapaksha'. Tools historically defaulted
// to 'LAHIRI' causing a join mismatch → 0 rows. This map aliases all known
// spellings to the canonical stored id so default + explicit calls both work.
const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri:               'lahiri_chitrapaksha',
  lahiri_chitrapaksha:  'lahiri_chitrapaksha',
  lahiri_chitra:        'lahiri_chitrapaksha',
  true_chitra:          'lahiri_chitrapaksha',
  true_citra:           'lahiri_chitrapaksha',
  LAHIRI:               'lahiri_chitrapaksha',
  Lahiri:               'lahiri_chitrapaksha',
}
const DEFAULT_AYANAMSHA = 'lahiri_chitrapaksha'

function normalizeAyanamsha(id?: string): string {
  if (!id) return DEFAULT_AYANAMSHA
  return AYANAMSHA_ALIAS[id] ?? id
}

// ── Platform primitive caller ─────────────────────────────────────────────────

/**
 * Call a platform primitive via /api/mcp/primitives/{tool}.
 * Used for tools (e.g. vector_search) that are not in the registry.
 *
 * R5 W0a punch-list fix (P7 — corpus search 401). Root cause per
 * RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §20: this helper sent only
 * X-MCP-Internal-Token, but /api/mcp/primitives/[tool]/route.ts's Layer 2 gate
 * requires X-MCP-User + X-MCP-Key-Id (X-MCP-Audience-Tier is informational).
 * The working 3-header pattern already existed in resources/capabilities.ts —
 * copied here per the design doc's named fix class.
 */
async function callPlatformPrimitive(
  tool: string,
  params: Record<string, unknown>,
  principal: Principal,
): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/primitives/${tool}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Audience-Tier': principal.role === 'super_admin' ? 'super_admin' : 'client',
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ params }),
    signal: AbortSignal.timeout(20_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[registry_bridge] primitive call '${tool}' failed (${res.status}): ${text.slice(0, 200)}`)
  }
  return res.json()
}

// ── DB proxy helper ───────────────────────────────────────────────────────────

/**
 * Minimal DB proxy: calls platform API which holds the actual PG connection.
 * The MCP server does not hold a direct DB connection.
 */
async function platformQuery(
  sql: string,
  params: unknown[]
): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) {
    throw new Error(`[registry_bridge] platform DB query failed: ${res.status}`)
  }
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

/**
 * Build a SynergyContext for capability handlers.
 */
function buildCtx(chartId?: string) {
  return {
    db: { query: platformQuery },
    chart_id: chartId,
    lel_enabled: false,
  }
}

// ── Unified envelope helper (R5 W1 — mirrors register_p1_ganita.ts's envelope()) ──

// Three-arg call sites are UNCHANGED (format defaults to 'legacy', v3Extras undefined) —
// they get the exact legacy shape. Call sites opting into 'v3' pass format='v3' +
// v3Extras; those extras are silently ignored under 'legacy' (additive-only, brief §6.3).
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
    },
    format,
  )
}

// ── Dual output helper ────────────────────────────────────────────────────────

// S3 fix (R5 W0a perf lane, design §21 serialization tax — measured 2.4x):
// above this size, skip the redundant text-duplicate serialization. Below it,
// dual output is still built but WITHOUT pretty-printing (indent:2 was a
// measured 20-30% byte inflation for zero client benefit — structuredContent
// already carries the full typed payload).
const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

/**
 * Build MCP tool response with both structuredContent and text fallback.
 * Provider-spec obligation: dual output per MCP spec.
 *
 * R5 W0a punch-list (P3 fix class): dropped the `null, 2` pretty-print indent —
 * pure serialization padding, no information content.
 * S3 (R5 W0a perf lane): compact JSON.stringify, not indent:2; above the size
 * threshold the text fallback is replaced with a pointer to structuredContent
 * instead of re-serializing the full payload a second time on the wire. See
 * JL-003 for the 50KB threshold ruling.
 */
function dualOutput(data: unknown): {
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
} {
  const structuredContent = { type: 'object' as const, object: data }
  const json = JSON.stringify(data)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return {
      structuredContent,
      content: [{
        type: 'text' as const,
        text: '[large payload — see structuredContent; text duplicate suppressed per S3 serialization-tax fix]',
      }],
    }
  }
  return {
    structuredContent,
    content: [{ type: 'text' as const, text: json }],
  }
}

// ── Error output ──────────────────────────────────────────────────────────────

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  const data = { ok: false, error: message, tool, ...extra }
  return { ...dualOutput(data), isError: true as const }
}

// ── Registry capability caller ────────────────────────────────────────────────

/**
 * Call a registry capability via the platform's /api/retrieval/capability endpoint.
 *
 * The MCP server is a separate Node package (platform-mcp) and cannot import
 * the Next.js platform's TypeScript modules directly. Instead, it calls the
 * platform's HTTP API, which holds the live registry and DB connection.
 *
 * Endpoint: POST /api/retrieval/capability
 * Body: { uri, args }
 * Response: { ok: boolean, content: unknown, error?: string }
 */
async function callRegistryCapability(
  uri: string,
  args: Record<string, unknown>,
  _chartId?: string   // chart_id is already in args; kept for call-site clarity
): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': MCP_INTERNAL_TOKEN,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(20_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[registry_bridge] capability call failed (${res.status}): ${text.slice(0, 200)}`)
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) {
    throw new Error(`[registry_bridge] capability error: ${data.error ?? 'unknown'}`)
  }
  return data.content
}

// ── B.11 orient-before-domain enforcement ─────────────────────────────────────

/**
 * B.11 Whole-Chart-Read Protocol (PROJECT_ARCHITECTURE §H.4):
 * Every domain-specific query must be preceded by an orientation digest
 * from the L2 UCD (query_ucd / get_chart_orientation). In the MCP channel,
 * which is stateless per-request and has no shared session state, we enforce
 * this STRUCTURALLY: each non-floor domain tool handler fetches the UCD
 * before doing its domain work and includes the result as `orientation_context`
 * in the output. This means orient-before-domain is guaranteed by construction —
 * the tool itself ensures orientation has happened, not a soft prompt convention.
 *
 * Floor tools (get_chart_orientation itself, get_classical_citation, list_assets)
 * are exempt — they ARE the floor or are chart-agnostic.
 *
 * If the UCD call fails (e.g. no bodha data yet), we return a graceful-empty
 * stub so the domain tool can still serve — a failed orientation is non-blocking
 * but annotated in the response.
 */
async function fetchOrientationContext(
  chart_id: string,
  ayanamsha_id?: string,
): Promise<{ orientation_context: unknown; orientation_ok: boolean }> {
  try {
    const ucdData = await callRegistryCapability(
      'marsys://tool/L2/query_ucd',
      { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), top_k_signals: 10, response_format: 'digest' },
      chart_id,
    )
    return { orientation_context: ucdData, orientation_ok: true }
  } catch (err) {
    // Non-blocking: domain tool still runs; orientation failure is annotated
    return {
      orientation_context: {
        b11_note: 'UCD orientation pre-fetch failed (graceful-empty). Domain tool executed without holistic context.',
        error: String(err),
      },
      orientation_ok: false,
    }
  }
}

// ── Tool registrations ────────────────────────────────────────────────────────

/**
 * Register all D7 consolidated MCP tools on the server.
 *
 * All per_chart tools: chart_id is REQUIRED — no default fallback.
 * chart_agnostic_gate RULE-1: per_chart scope → chart_id in required_inputs.
 *
 * B.11 enforcement: all per_chart domain tools call fetchOrientationContext()
 * before executing their domain query. The UCD result is included in the
 * response as `orientation_context` so the LLM always has holistic context.
 */
export function registerRegistryBridgeTools(server: McpServer, principal: Principal): void {

  // ── get_chart_orientation (L-ORIENT umbrella — synthesis_query, design §5 #7) ──
  // marsys://tool/L2/query_ucd
  server.tool(
    'get_chart_orientation',
    'Mandatory first call for any chart reading. Retrieves the L2 Bodha synthesis layer\'s Unified Chart Digest (UCD) — the holistic portrait of the chart distilled from 573 MSR signals, the CDLM domain activation grid, the CGM causal graph, and the Life Event Log. In classical Jyotish, an acharya reads the whole chart before any domain. This tool enforces that discipline: it surfaces the Lagna lord condition, Moon nakshatra character, dominant cross-domain themes, and active contradictions. entity_profiles (design §E-6) are hierarchically-aggregated composite-ranked signal groups — one row per graha, not twenty atomic signals — computed by the SAME ranking pipeline get_signals uses. Call this before get_domain_reading, get_signals, or any other per-chart tool — the B.11 Whole-Chart-Read Protocol requires it. envelope_format=\'v3\' (opt-in; default \'legacy\') returns the R5 unified envelope alongside the existing response_format verbosity control.',
    {
      chart_id: z.string().uuid().describe(
        'UUID of the chart to read. Required — no default chart.'
      ),
      ayanamsha_id: z.string().optional().describe(
        "Ayanamsha for signals (default: 'LAHIRI')"
      ),
      top_k_signals: z.number().int().min(1).max(100).optional().describe(
        'Number of top MSR signals to return (default: 20)'
      ),
      top_k_entities: z.number().int().min(1).max(30).optional().describe(
        'Number of hierarchically-aggregated entity profiles to return (default: 10).'
      ),
      response_format: z.enum(['full', 'summary', 'digest']).optional().describe(
        'Output verbosity: full (all fields), summary (key fields), digest (counts + entity_profiles only, no atomic signals). Default: summary.'
      ),
      envelope_format: z.enum(['legacy', 'v3']).optional()
        .describe("Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/ranking_basis/drill_pointers/chart_header — opt-in until the R5 W4 battery flips the default). Distinct from response_format, which governs digest verbosity."),
    },
    async ({ chart_id, ayanamsha_id, top_k_signals, top_k_entities, response_format, envelope_format }) => {
      if (!chart_id) return errorOutput('get_chart_orientation', 'chart_id is required')
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        const fmt = response_format ?? 'summary'
        const format = resolveEnvelopeFormat(envelope_format)
        const raw = await callRegistryCapability(
          'marsys://tool/L2/query_ucd',
          { chart_id, ayanamsha_id: resolvedAyanamsha, top_k_signals: top_k_signals ?? 20,
            top_k_entities: top_k_entities ?? 10, response_format: fmt },
          chart_id
        )
        // R5 W1 fix: callRegistryCapability returns the capability handler's raw return
        // value ({ content, is_error }) — this call site was reading fields directly off
        // that wrapper (responseData['chart_id'] etc), which are actually one level
        // deeper under `.content`, and always resolved to undefined. Unwrap here (matches
        // get_domain_reading's established pattern) before any field access.
        const wrapper = raw as Record<string, unknown>
        const responseData = (wrapper['content'] as Record<string, unknown>) ?? wrapper

        // F-026: response_format bounding is now genuinely applied server-side
        // (query_ucd.ts) too; this MCP-layer bounding remains as defense-in-depth /
        // backward-compat for callers relying on the exact prior shape.
        let bounded: Record<string, unknown>
        if (fmt === 'digest') {
          bounded = {
            chart_id: responseData['chart_id'],
            ayanamsha_id: responseData['ayanamsha_id'],
            digest: responseData['digest'],
            entity_profiles: responseData['entity_profiles'],
            convergence_domains: responseData['convergence_domains'],
            provenance: responseData['provenance'],
            response_format: 'digest',
          }
        } else if (fmt === 'summary') {
          const signals = (responseData['top_signals'] as unknown[]) ?? []
          bounded = { ...responseData, top_signals: signals.slice(0, 10), response_format: 'summary' }
        } else {
          const signals = (responseData['top_signals'] as unknown[]) ?? []
          bounded = { ...responseData, top_signals: signals.slice(0, 100), response_format: 'full' }
        }

        if (format !== 'v3') {
          return dualOutput(envelope(bounded, 'get_chart_orientation'))
        }

        // ── v3 population (design §10/§E-6) ──────────────────────────────────
        const entityProfiles = (responseData['entity_profiles'] as Record<string, unknown>[]) ?? []
        const rankingBasis = (responseData['ranking_basis'] as Record<string, unknown> | null) ?? null
        const digestBlock = (responseData['digest'] as Record<string, unknown>) ?? {}

        const verdict = {
          entity_profile_count: entityProfiles.length,
          msr_signal_count: digestBlock['msr_signal_count'] ?? null,
          contradiction_count: digestBlock['contradiction_count'] ?? null,
          weakest_graha: digestBlock['weakest_graha'] ?? null,
          top_priority_class: digestBlock['top_priority_class'] ?? null,
          note: 'entity_profile_count/msr_signal_count are chart-wide aggregates already computed by this response — not recomputed here.',
        }

        const citations = Array.from(new Set(
          ((responseData['top_signals'] as Record<string, unknown>[]) ?? [])
            .map(s => s['citation_human']).filter((v): v is string => typeof v === 'string' && v.length > 0)
        ))
        const grounding = { fact_ids: [], citations, grounding_score: null }

        const judgment_flags: string[] = []
        if (entityProfiles.length === 0) judgment_flags.push('zero_entity_profiles')

        const drill_pointers = [
          { instrument: 'get_signals', hint: 'atomic composite-ranked signal drill for any entity_profiles.top_signal_ids.' },
          { instrument: 'get_domain_reading', hint: 'domain-conditioned reading for a specific life domain.' },
        ]

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability(
            'marsys://tool/L1/get_chart_header', { chart_id, ayanamsha_id: resolvedAyanamsha }, chart_id
          ) as ChartHeader
        } catch {
          chart_header = null
        }

        return dualOutput(
          envelope(bounded, 'get_chart_orientation', undefined, 'v3',
            { chart_header, verdict, ranking_basis: rankingBasis, grounding, drill_pointers, judgment_flags })
        )
      } catch (err) {
        return errorOutput('get_chart_orientation', String(err), { chart_id })
      }
    }
  )

  // ── get_domain_reading (L-DOMAIN drill) ──────────────────────────────────
  // marsys://tool/L2/query_domain_reading
  server.tool(
    'get_domain_reading',
    'Retrieves the L2 Bodha domain activation reading for a specific life domain (career, relationship, health, wealth, spirituality, character). In Jyotish, each domain (bhava) is governed by a karaka planet and a set of signifying houses — career by the 10th lord and its dispositor chain; relationship by the 7th lord and Venus; health by the Lagna lord and the 6th/8th. This tool surfaces which MSR signals are active in the named domain, ranked by computed_salience, with their constituent L1 facts and classical derivation chain. Always returns an orientation_context from the L2 UCD as the holistic frame (B.11 by construction).',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      domain: z.string().describe(
        'Life domain to drill: career, relationship, character, spirituality, wealth, health, or other domain name.'
      ),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      cursor: z.string().optional().describe('Pagination cursor (from previous response.next_cursor)'),
      max_lenses: z.number().int().min(1).max(12).optional().describe(
        'Max question lenses to return (default: 3 for token safety; pass 12 for full payload).'
      ),
      max_signals_per_lens: z.number().int().min(1).max(100).optional().describe(
        'Max signals per lens (default: 20).'
      ),
      max_signal_refs: z.number().int().min(1).max(2000).optional().describe(
        'Max signal IDs in signal_id_refs (default 200; capped at 2000).'
      ),
      response_format: z.enum(['default', 'full']).optional().describe(
        "Payload verbosity. 'default': token-safe (shared_signal_ids_array omitted, signal_id_refs ≤200). 'full': includes arrays (signal_id_refs ≤2000)."
      ),
    },
    async ({ chart_id, domain, ayanamsha_id, cursor, max_lenses, max_signals_per_lens, max_signal_refs, response_format }) => {
      if (!chart_id) return errorOutput('get_domain_reading', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before domain drill.
        // S1 fix (R5 W0a perf lane): orientation fetch and the domain query are
        // independent HTTP calls (both hit the platform API) — parallelize
        // rather than serially awaiting each (measured ~458ms/call added by
        // the serial UCD pre-fetch; this is the biggest median win in §21).
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id)),
          callRegistryCapability(
            'marsys://tool/L2/query_domain_reading',
            { chart_id, domain, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), cursor,
              ...(response_format ? { response_format } : {}),
              ...(max_signal_refs != null ? { max_signal_refs } : {}) },
            chart_id
          ),
        ])
        // F-021R: Bound the response — default 3 lenses × 20 signals (was 17MB / 90k signal objects)
        // callRegistryCapability returns data.content from the HTTP response, where
        // the handler itself wraps in { content: {...}, is_error: false }. So the
        // actual payload is one level deeper: data → { content: { question_lenses } }.
        const domainWrapper = data as Record<string, unknown>
        const inner = (domainWrapper['content'] as Record<string, unknown>) ?? domainWrapper
        const lenses = (inner['question_lenses'] as unknown[]) ?? []
        const maxLenses = max_lenses ?? 3
        const maxSig = max_signals_per_lens ?? 20
        const lensesToBound = lenses.slice(0, maxLenses)
        const boundedLenses = lensesToBound.map((lens) => {
          const l = lens as Record<string, unknown>
          // all_relevant_ranked_jsonb is stored as { total_count, ranked_signals: [...] }
          // (a JSONB object, not a flat array). Slice ranked_signals and preserve total_count.
          const arj = l['all_relevant_ranked_jsonb']
          let boundedArj: unknown
          let totalSignals = 0
          if (arj && typeof arj === 'object' && !Array.isArray(arj)) {
            const arjObj = arj as Record<string, unknown>
            const ranked = Array.isArray(arjObj['ranked_signals'])
              ? (arjObj['ranked_signals'] as unknown[])
              : []
            totalSignals = ranked.length
            boundedArj = { ...arjObj, ranked_signals: ranked.slice(0, maxSig), total_count: ranked.length }
          } else if (Array.isArray(arj)) {
            // Flat array fallback (schema v1 compat)
            totalSignals = (arj as unknown[]).length
            boundedArj = (arj as unknown[]).slice(0, maxSig)
          } else {
            boundedArj = arj
          }
          // F-023: template_element_ids_jsonb may contain duplicate refs — dedup
          const templateIds = Array.isArray(l['template_element_ids_jsonb'])
            ? (l['template_element_ids_jsonb'] as string[])
            : []
          const uniqueTemplateIds = [...new Set(templateIds)]
          return {
            ...l,
            all_relevant_ranked_jsonb: boundedArj,
            all_relevant_total: totalSignals,
            template_element_ids_jsonb: uniqueTemplateIds,
          }
        })
        return dualOutput({
          orientation_context,
          orientation_ok,
          ...inner,
          question_lenses: boundedLenses,
          lenses_total: lenses.length,
          lenses_returned: boundedLenses.length,
          token_safety_note: `Bounded to ${maxLenses} lenses × ${maxSig} signals. Pass max_lenses=12 + max_signals_per_lens=100 for full payload.`,
        })
      } catch (err) {
        return errorOutput('get_domain_reading', String(err), { chart_id, domain })
      }
    }
  )

  // ── get_signals (L-SIGNAL ranked signals — signals_query, design §5 #5) ──
  // marsys://tool/L2/query_signals
  server.tool(
    'get_signals',
    'Retrieves ranked MSR (Multi-Signal Repository) signals for a chart — the 573-signal corpus of astrological patterns derived from L1 Gaṇita facts. Each signal encodes a classical Jyotish observation (yoga, placement, aspect, nakshatra condition) with its constituent L1 fact_ids, a computed_salience score reflecting how prominently it operates in this chart, and the domain tags it activates. Use min_salience to focus on high-confidence signals (≥0.7 = strong; ≥0.5 = moderate). The signal layer is the analytical backbone: get_domain_reading and get_chart_orientation both synthesize from this corpus. Query directly when you need raw signal evidence for a specific claim. response_format=\'v3\' (opt-in; default \'legacy\') returns the R5 unified envelope: populated verdict (signal counts + composite-ranking mode), grounding (signal_id/citation coverage in this page), ranking_basis (the actual composite-4D scoring basis when domain was specified), drill_pointers (get_chart_orientation for the entity-level digest, traverse_graph for causal context), judgment_flags, and chart_header.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      domain: z.string().optional().describe('Filter by domain (e.g. career, health)'),
      min_salience: z.number().min(0).max(1).optional().describe(
        'Minimum computed_salience threshold (0–1). Ranked by computed_salience DESC — NOT signature_tier.'
      ),
      limit: z.number().int().min(1).max(200).optional().describe('Max signals (default: 50)'),
      // R5 W1 fix: this facet was declared but silently ignored — the call below forwarded
      // it as `limit`, but query_signals.ts's handler only reads `top_k`/`offset` (design
      // §18's "diverging param names" premise finding: top_k vs limit). cursor is now
      // translated to a numeric offset instead of being dropped on the floor (E-5).
      cursor: z.string().optional().describe('Pagination cursor — a stringified offset (e.g. "50"). Use next_cursor from a prior response.'),
      lel_enabled: z.boolean().optional().describe(
        'Include lel_origin=true signals (Life Event Log calibration). Default: false.'
      ),
      response_format: z.enum(['legacy', 'v3']).optional()
        .describe("Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/ranking_basis/drill_pointers/chart_header — opt-in until the R5 W4 battery flips the default)."),
    },
    async ({ chart_id, ayanamsha_id, domain, min_salience, limit, cursor, lel_enabled, response_format }) => {
      if (!chart_id) return errorOutput('get_signals', 'chart_id is required')
      try {
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        const format = resolveEnvelopeFormat(response_format)
        const resolvedLimit = limit ?? 50
        const resolvedOffset = cursor && /^\d+$/.test(cursor) ? Number(cursor) : 0

        // B.11: fetch holistic orientation before signal drill (S1: parallelized)
        const [{ orientation_context, orientation_ok }, raw] = await Promise.all([
          fetchOrientationContext(chart_id, resolvedAyanamsha),
          callRegistryCapability(
            'marsys://tool/L2/query_signals',
            { chart_id, ayanamsha_id: resolvedAyanamsha, domain, min_salience,
              top_k: resolvedLimit, offset: resolvedOffset, lel_enabled: lel_enabled ?? false },
            chart_id
          ),
        ])
        // callRegistryCapability returns the capability handler's raw return value
        // ({ content, is_error }) — unwrap `.content` for the real payload (matches
        // get_domain_reading's unwrap pattern; get_signals previously skipped this step).
        const wrapper = raw as Record<string, unknown>
        const inner = (wrapper['content'] as Record<string, unknown>) ?? wrapper

        if (format !== 'v3') {
          return dualOutput({
            orientation_context, orientation_ok,
            ...envelope(inner, 'get_signals', { offset: resolvedOffset, limit: resolvedLimit, total: null }),
          })
        }

        // ── v3 population (design §10/§E-6) ──────────────────────────────────
        const signals = (inner['signals'] as Record<string, unknown>[]) ?? []
        const returned_count = Number(inner['returned_count'] ?? signals.length)
        const truncated = Boolean(inner['truncated'])

        const fact_ids = Array.from(new Set(
          signals.flatMap(s => ((s['constituent_facts_array'] as string[] | null) ?? []))
        )).filter(Boolean)
        const citations = Array.from(new Set(
          signals.map(s => s['citation_human']).filter((v): v is string => typeof v === 'string' && v.length > 0)
        ))
        const verifiedCount = signals.filter(s => {
          const st = s['verification_pass_status']
          return st === 'two_pass_verified' || st === 'pass'
        }).length
        const grounding = {
          fact_ids, citations,
          grounding_score: signals.length > 0 ? Math.round((verifiedCount / signals.length) * 1000) / 1000 : null,
        }

        const rankingBasis = (inner['ranking_basis'] as Record<string, unknown> | null) ?? null
        const verdict = {
          returned_count,
          truncated,
          domain: domain ?? null,
          ranking_mode: rankingBasis?.['mode'] ?? 'salience_fallback',
          note: 'Counts are of SIGNALS SERVED IN THIS PAGE only — pass a higher limit/cursor for more.',
        }

        const judgment_flags: string[] = []
        if (returned_count === 0) judgment_flags.push('zero_rows_returned')
        if (truncated) judgment_flags.push('response_size_truncated')

        const drill_pointers = [
          { instrument: 'get_chart_orientation', hint: 'entity_profiles for the hierarchically-aggregated, same-pipeline orient view (design §E-6).' },
          { instrument: 'get_cgm_subgraph', hint: 'traverse causal context from these signal_ids.' },
        ]

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability(
            'marsys://tool/L1/get_chart_header', { chart_id, ayanamsha_id: resolvedAyanamsha }, chart_id
          ) as ChartHeader
        } catch {
          chart_header = null // frame-safety header is best-effort; never fails the instrument
        }

        return dualOutput({
          orientation_context, orientation_ok,
          ...envelope(inner, 'get_signals', { offset: resolvedOffset, limit: resolvedLimit, total: null },
            'v3', { chart_header, verdict, ranking_basis: rankingBasis, grounding, drill_pointers, judgment_flags }),
        })
      } catch (err) {
        return errorOutput('get_signals', String(err), { chart_id })
      }
    }
  )

  // ── traverse_graph (CGM graph traversal) ─────────────────────────────────
  // marsys://tool/L2/traverse_chart_graph
  server.tool(
    'traverse_graph',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      seed_signal_ids: z.array(z.string()).min(1).optional().describe(
        'Seed signal UUIDs to start traversal from (use signal_id values from get_signals). ' +
        'Alternative to about/about_from/about_to for address-seeded traversal (R5 W2).'
      ),
      mode: z.enum(['neighbors', 'paths', 'cluster']).optional().describe(
        'Traversal mode: neighbors (adjacent nodes), paths (shortest paths between seeds), cluster (community). Default: neighbors.'
      ),
      depth: z.number().int().min(1).max(3).optional().describe('Traversal depth (default: 2, max: 3)'),
      about: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression (AddressExpression object or DSL string, e.g. "lord_of(bhava 10)") ' +
        'seeding neighbors mode — resolved via the shared address resolver.'
      ),
      about_from: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression for the paths-mode start node, e.g. "lord_of(bhava 10)".'
      ),
      about_to: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression for the paths-mode end node, e.g. {type:"graha", graha:"Moon"}.'
      ),
      direction: z.enum(['directed', 'both']).optional().describe(
        'R5 W2: directed follows real from_node_id→to_node_id edges only; both treats edges as undirected. Default: both.'
      ),
      min_strength: z.number().min(0).max(1).optional().describe(
        'R5 W2: filter traversal/edges to computed_strength >= this floor.'
      ),
    },
    async ({ chart_id, seed_signal_ids, mode, depth, about, about_from, about_to, direction, min_strength }) => {
      if (!chart_id) return errorOutput('traverse_graph', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before graph traversal (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id),
          callRegistryCapability(
            'marsys://tool/L2/traverse_chart_graph',
            {
              chart_id,
              seed_signal_ids,
              mode: mode ?? 'neighbors',
              depth: depth ?? 2,
              about,
              about_from,
              about_to,
              direction,
              min_strength,
            },
            chart_id
          ),
        ])
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('traverse_graph', String(err), { chart_id })
      }
    }
  )

  // ── get_positions (L1 Gaṇita graha positions) ────────────────────────────
  // marsys://tool/L1/get_positions
  server.tool(
    'get_positions',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      planet: z.string().optional().describe('Optional: filter by planet name (e.g. Sun, Moon, Mars)'),
    },
    async ({ chart_id, ayanamsha_id, planet }) => {
      if (!chart_id) return errorOutput('get_positions', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/get_positions',
          { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), planet },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_positions', String(err), { chart_id })
      }
    }
  )

  // ── get_dashas (L1 Vimshottari dasha chain) ──────────────────────────────
  // marsys://tool/L1/get_dashas
  server.tool(
    'get_dashas',
    'Retrieves the dasha (planetary period) chain from L1 Gaṇita. Default system: VIMSHOTTARI — the 120-year Parashara sequence (Sun 6 yr, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17, Ketu 7, Venus 20), subdivided into antardasha and pratyantardasha. Other systems available: YOGINI, ASHTOTTARI, CHARA, NARAYANA, SHOOLA, KALACHAKRA. The running period lord colors all life events during its tenure: its natal placement, lordship, aspects received, and conjunctions determine what it delivers. Use this to identify which lords are active now and in the near future, then cross-reference with get_temporal_windows and get_signals to see which yogas those lords activate. Pass date_from=birth_date to exclude pre-birth rows (the dasha running at birth may have started before the birth date).',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      system_id: z.string().optional().describe(
        "Dasha system to retrieve (default: 'VIMSHOTTARI'). Options: VIMSHOTTARI | YOGINI | ASHTOTTARI | CHARA | NARAYANA | SHOOLA | KALACHAKRA."
      ),
      date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe(
        "ISO date YYYY-MM-DD. Filters to dashas whose end_date >= this date, excluding rows that ended before this point. Pass the chart's birth date (e.g. '1984-02-05') to exclude pre-birth rows."
      ),
      limit: z.number().int().min(1).max(200).optional().describe('Max dasha rows (default: 50)'),
      cursor: z.string().optional().describe('Pagination cursor'),
    },
    async ({ chart_id, ayanamsha_id, system_id, date_from, limit, cursor }) => {
      if (!chart_id) return errorOutput('get_dashas', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/get_dashas',
          {
            chart_id,
            ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
            dasha_system: system_id ?? 'VIMSHOTTARI',
            ...(date_from ? { date_from } : {}),
            limit: limit ?? 50,
            cursor,
          },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_dashas', String(err), { chart_id })
      }
    }
  )

  // ── get_temporal_windows (L3 temporal activation + convergence) ──────────
  // marsys://tool/L3/query_temporal_activation + query_convergence_windows
  server.tool(
    'get_temporal_windows',
    'Retrieves the L3 Kāla temporal activation layer for a date range — identifying which Jyotish periods (Vimshottari dasha, antardasha, pratyantardasha) are running, which MSR signals are activated by those period lords, and where convergence windows occur (multiple activation streams peaking simultaneously). In classical Jyotish, timing is the hardest discipline: a powerful yoga (structural combination) only gives its results when its constituent lords run their period. This tool applies that temporal gate — distinguishing signals that are structurally present from those that are temporally ripe. Returns orientation_context (B.11) alongside temporal data.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('Start date YYYY-MM-DD'),
      date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('End date YYYY-MM-DD'),
      include_convergence: z.boolean().optional().describe('Include convergence windows (default: true)'),
    },
    async ({ chart_id, ayanamsha_id, date_from, date_to, include_convergence }) => {
      if (!chart_id) return errorOutput('get_temporal_windows', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before temporal domain query (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id)),
          callRegistryCapability(
            'marsys://tool/L3/query_temporal_activation',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), date_from, date_to, include_convergence: include_convergence ?? true },
            chart_id
          ),
        ])
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('get_temporal_windows', String(err), { chart_id })
      }
    }
  )

  // ── get_projections (L3 probabilistic projections) ───────────────────────
  // marsys://tool/L3/query_projections
  server.tool(
    'get_projections',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      domain: z.string().optional().describe('Domain to project (e.g. career, relationship)'),
      horizon_years: z.number().int().min(1).max(20).optional().describe('Projection horizon in years (default: 5)'),
      max_projections: z.number().int().min(1).max(200).optional().describe(
        'Max projections to return (default: 20; was unbounded at 117KB+).'
      ),
    },
    async ({ chart_id, ayanamsha_id, domain, horizon_years, max_projections }) => {
      if (!chart_id) return errorOutput('get_projections', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before predictive projection (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id)),
          callRegistryCapability(
            'marsys://tool/L3/query_projections',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), domain, horizon_years: horizon_years ?? 5 },
            chart_id
          ),
        ])
        // F-008: Cap projections array — was 117KB unbounded
        const projData = data as Record<string, unknown>
        const projections = (projData['projections'] as unknown[]) ?? []
        const cap = max_projections ?? 20
        const boundedProjections = projections.slice(0, cap)
        return dualOutput({
          orientation_context,
          orientation_ok,
          ...projData,
          projections: boundedProjections,
          projections_total: projections.length,
          projections_returned: boundedProjections.length,
        })
      } catch (err) {
        return errorOutput('get_projections', String(err), { chart_id })
      }
    }
  )

  // ── get_classical_citation (L0 classical text retrieval) ─────────────────
  // marsys://tool/L0/query_classical_texts
  // Global scope — no chart_id required
  server.tool(
    'get_classical_citation',
    {
      query: z.string().describe('Topic or verse to search for in classical Jyotish texts.'),
      text_ids: z.array(z.string()).optional().describe('Optional: limit to specific text IDs'),
      limit: z.number().int().min(1).max(20).optional().describe('Max results (default: 5)'),
      cursor: z.string().optional().describe('Pagination cursor'),
    },
    async ({ query, text_ids, limit, cursor }) => {
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L0/query_classical_texts',
          { query, text_ids, limit: limit ?? 5, cursor },
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('get_classical_citation', String(err))
      }
    }
  )

  // ── get_remedies (L2 remedy prescriptions) ───────────────────────────────
  // marsys://tool/L2/query_remedies
  server.tool(
    'get_remedies',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      domain: z.string().optional().describe('Filter remedies by life domain'),
      remedy_type: z.string().optional().describe('Filter by type: mantra, gemstone, ritual, upaya'),
    },
    async ({ chart_id, domain, remedy_type }) => {
      if (!chart_id) return errorOutput('get_remedies', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before remedy prescription (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id),
          callRegistryCapability(
            'marsys://tool/L2/query_remedies',
            { chart_id, domain, remedy_type },
            chart_id
          ),
        ])
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('get_remedies', String(err), { chart_id })
      }
    }
  )

  // ── get_chart_quality (calibration + trust) ───────────────────────────────
  // marsys://tool/L2/query_quality_scorecard
  server.tool(
    'get_chart_quality',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
    },
    async ({ chart_id }) => {
      if (!chart_id) return errorOutput('get_chart_quality', 'chart_id is required')
      try {
        // B.11: fetch holistic orientation before quality/calibration surface (S1: parallelized)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id),
          callRegistryCapability(
            'marsys://tool/L2/query_quality_scorecard',
            { chart_id },
            chart_id
          ),
        ])
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('get_chart_quality', String(err), { chart_id })
      }
    }
  )

  // ── list_assets (asset catalog) ───────────────────────────────────────────
  // marsys://resource/asset-registry/all
  // Global scope — no chart_id required
  server.tool(
    'list_assets',
    {
      layer: z.string().optional().describe('Filter by layer: L0, L1, L2, L3, L4, L5'),
      limit: z.number().int().min(1).max(200).optional().describe('Max assets (default: 81)'),
      cursor: z.string().optional().describe('Pagination cursor'),
    },
    async ({ layer, limit, cursor }) => {
      try {
        // list_assets → platform cockpit registry (direct HTTP; no @/ import possible)
        const data = await callRegistryCapability(
          'marsys://resource/asset-registry/all',
          { layer, limit: limit ?? 81, cursor }
        )
        return dualOutput({ ...(data as Record<string, unknown>), pagination: { cursor, limit } })
      } catch (err) {
        return errorOutput('list_assets', String(err))
      }
    }
  )

  // ── D8 APEX TOOLS ─────────────────────────────────────────────────────────
  // assess_marriage / assess_career / assess_health / assess_wealth
  // yoga_activation_by_dasha
  // get_cgm_subgraph / query_chart_facts / vector_search

  // ── assess_marriage (D8 L-DOMAIN reconciled bundle) ──────────────────────
  server.tool(
    'assess_marriage',
    'Reconciled marriage/relationship assessment for a chart. Orchestrates the 7th lord + Venus kāraka + D9 + bhāvat-bhāva analysis across the Bodha synthesis layer (L2), Kāla temporal activation (L3), and the contradiction surface. Returns convergences, tensions, activating dasha window, and classical citations for the relationship domain. judgment_flags marks inferences requiring acharya validation. chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
    },
    async ({ chart_id, ayanamsha_id }) => {
      if (!chart_id) return errorOutput('assess_marriage', 'chart_id is required')
      try {
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id)),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_marriage',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id) },
            chart_id
          ),
        ])
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('assess_marriage', String(err), { chart_id })
      }
    }
  )

  // ── assess_career (D8 L-DOMAIN reconciled bundle) ────────────────────────
  server.tool(
    'assess_career',
    'Reconciled career/vocation assessment for a chart. Orchestrates the 10th lord + Saturn kāraka + D10 + yoga detection + activating dasha window. Calls Bodha domain reading (L2), Kāla temporal activation (L3), and the contradiction surface. Returns convergences, tensions, and judgment_flags for inferences requiring acharya validation. chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
    },
    async ({ chart_id, ayanamsha_id }) => {
      if (!chart_id) return errorOutput('assess_career', 'chart_id is required')
      try {
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id)),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_career',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id) },
            chart_id
          ),
        ])
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('assess_career', String(err), { chart_id })
      }
    }
  )

  // ── assess_health (D8 L-DOMAIN reconciled bundle) ────────────────────────
  server.tool(
    'assess_health',
    'Reconciled health/vitality assessment for a chart. Orchestrates the 1st + 6th + 8th lords + Sun kāraka + afflictions + D1/D6 analysis. Calls Bodha domain reading (L2), Kāla temporal activation (L3), and the contradiction surface. Returns convergences, tensions, and judgment_flags for inferences requiring acharya validation. chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
    },
    async ({ chart_id, ayanamsha_id }) => {
      if (!chart_id) return errorOutput('assess_health', 'chart_id is required')
      try {
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id)),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_health',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id) },
            chart_id
          ),
        ])
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('assess_health', String(err), { chart_id })
      }
    }
  )

  // ── assess_wealth (D8 L-DOMAIN reconciled bundle) ────────────────────────
  server.tool(
    'assess_wealth',
    'Reconciled wealth/prosperity assessment for a chart. Orchestrates the 2nd + 11th lords + Jupiter kāraka + dasha activation window + classical citations. Calls Bodha domain reading (L2), Kāla temporal activation (L3), and the contradiction surface. Returns convergences, tensions, and judgment_flags for inferences requiring acharya validation. chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
    },
    async ({ chart_id, ayanamsha_id }) => {
      if (!chart_id) return errorOutput('assess_wealth', 'chart_id is required')
      try {
        // S1 fix: orientation + domain assessment parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id)),
          callRegistryCapability(
            'marsys://tool/L-DOMAIN/assess_wealth',
            { chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id) },
            chart_id
          ),
        ])
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('assess_wealth', String(err), { chart_id })
      }
    }
  )

  // ── yoga_activation_by_dasha (D8 L-TIMING bridge) ────────────────────────
  server.tool(
    'yoga_activation_by_dasha',
    'Bridges the L2 Bodha yoga-signal catalog and the L3 Kāla timing activation surface. Returns yoga signals (signal_type_class=yoga) active within the given dasha window, ranked by salience × dasha_alignment_score. Each result includes activation_start, activation_end, active_dasha_periods_jsonb, and constituent_fact_ids for drill-down. Use to answer "which yogas are ripening now?" chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      dasha_period: z.string().optional().describe(
        "Dasha-antardasha label to filter by (e.g. 'saturn-venus'). Case-insensitive substring match against active_dasha_periods_jsonb."
      ),
      date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('Start of window (YYYY-MM-DD). Default: today.'),
      date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe('End of window (YYYY-MM-DD). Default: 3 years from today.'),
      top_k: z.number().int().min(1).max(200).optional().describe('Max activated yogas to return (default: 30).'),
      min_salience: z.number().min(0).max(1).optional().describe('Minimum salience threshold (0–1, default: 0).'),
    },
    async ({ chart_id, ayanamsha_id, dasha_period, date_from, date_to, top_k, min_salience }) => {
      if (!chart_id) return errorOutput('yoga_activation_by_dasha', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L-TIMING/yoga_activation_by_dasha',
          {
            chart_id,
            ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
            ...(dasha_period ? { dasha_period } : {}),
            ...(date_from ? { date_from } : {}),
            ...(date_to ? { date_to } : {}),
            ...(top_k != null ? { top_k } : {}),
            ...(min_salience != null ? { min_salience } : {}),
          },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('yoga_activation_by_dasha', String(err), { chart_id })
      }
    }
  )

  // ── get_cgm_subgraph (CGM graph: per-chart subgraph traversal) ────────────
  // marsys://tool/L2/traverse_chart_graph
  // Apex alias: expose traverse_chart_graph as get_cgm_subgraph for D8 surface.
  server.tool(
    'get_cgm_subgraph',
    'Traverses the Causal Graph Model (CGM) for a chart — the bodha_cgm_nodes + bodha_cgm_edges graph built from L2 Bodha signals. Four modes: neighbors (BFS from seed node_ids), paths (shortest path between two nodes), convergence (top hub nodes by in-degree), contradictions (nodes with conflicting signal valence). Use to explore causal chains, find convergence hubs, or surface contradictions in the chart\'s signal graph. chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      mode: z.enum(['neighbors', 'paths', 'convergence', 'contradictions']).optional().describe(
        'Traversal mode (default: neighbors).'
      ),
      seed_node_ids: z.array(z.string().uuid()).optional().describe(
        'Seed node UUIDs (from bodha_cgm_nodes) for neighbors/paths modes.'
      ),
      depth: z.number().int().min(1).max(3).optional().describe('BFS depth for neighbors mode (1–3, default 1).'),
      seed_node: z.string().uuid().optional().describe('Source node UUID for paths mode.'),
      target_node: z.string().uuid().optional().describe('Target node UUID for paths mode.'),
      query_text: z.string().optional().describe('Semantic seed: finds top-3 similar nodes and runs BFS from them.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'LAHIRI')"),
      about: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression (e.g. "lord_of(bhava 10)") seeding neighbors mode — resolved via the shared address resolver.'
      ),
      about_from: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression for the paths-mode start node, e.g. "lord_of(bhava 10)".'
      ),
      about_to: z.union([z.string(), z.record(z.string(), z.unknown())]).optional().describe(
        'R5 W2: address expression for the paths-mode end node, e.g. {type:"graha", graha:"Moon"}.'
      ),
      direction: z.enum(['directed', 'both']).optional().describe(
        'R5 W2: directed follows real from_node_id→to_node_id edges only; both treats edges as undirected. Default: both.'
      ),
      min_strength: z.number().min(0).max(1).optional().describe(
        'R5 W2: filter traversal/edges to computed_strength >= this floor.'
      ),
    },
    async ({ chart_id, mode, seed_node_ids, depth, seed_node, target_node, query_text, ayanamsha_id, about, about_from, about_to, direction, min_strength }) => {
      if (!chart_id) return errorOutput('get_cgm_subgraph', 'chart_id is required')
      try {
        // S1 fix: orientation + graph traversal parallelized (independent HTTP calls)
        const [{ orientation_context, orientation_ok }, data] = await Promise.all([
          fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id)),
          callRegistryCapability(
            'marsys://tool/L2/traverse_chart_graph',
            {
              chart_id,
              ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
              mode: mode ?? 'neighbors',
              ...(seed_node_ids ? { seed_node_ids } : {}),
              ...(depth != null ? { depth } : {}),
              ...(seed_node ? { seed_node } : {}),
              ...(target_node ? { target_node } : {}),
              ...(query_text ? { query_text } : {}),
              ...(about ? { about } : {}),
              ...(about_from ? { about_from } : {}),
              ...(about_to ? { about_to } : {}),
              ...(direction ? { direction } : {}),
              ...(min_strength != null ? { min_strength } : {}),
            },
            chart_id
          ),
        ])
        return dualOutput({ orientation_context, orientation_ok, ...data as Record<string, unknown> })
      } catch (err) {
        return errorOutput('get_cgm_subgraph', String(err), { chart_id })
      }
    }
  )

  // ── query_chart_facts (L1 chart_facts EAV-crosstab lookup) ────────────────
  // marsys://tool/L1/chart_facts_query  (D7 gap-fill / B.11 floor tool)
  //
  // R5 W1 (lane: chart_query) fix: this tool 404'd unconditionally in prod (R5_RUN_LEDGER
  // NF-1) because the registry-side handler called a Python sidecar route that does not
  // exist. The handler was rewritten to query chart_facts directly (see
  // register_d7_channel.ts) — this shim now also: (a) adds `about` (design §27.1 universal
  // address facet — "lagna", {graha}, {bhava}, {house_lord}) and `shape` (pivoted/rows,
  // design §1/§18 EAV-crosstab mandate); (b) drops `as_of_date`/`from_date`/`to_date` —
  // chart_facts has no validity_start/validity_end columns, so these params could never
  // have done anything (a dead-param bug of the same class as P1's as_of_date, fixed here
  // by removing the illusion of the filter rather than silently ignoring it). See
  // R5_JUDGMENT_LEDGER for the ruling on both changes.
  server.tool(
    'query_chart_facts',
    'EAV-crosstab lookup over the chart_facts table (27,554 rows per chart, single ayanamsha per call). Covers planet positions, dignities, strengths, house placements, divisional charts, yogas, doshas, and more. Default shape="pivoted" returns ONE wide row per fact_subject (e.g. lagna -> {sign, sign_lord, house_d1, pada, longitude_sidereal}) instead of raw EAV rows — shape="rows" returns the flat form. The `about` facet lets you address the chart astrologically instead of guessing categories: about="lagna", about={graha:"Saturn"}, about={bhava:10} (the house itself), about={house_lord:10} (resolves the Nth house rashi from the lagna + classical BPHS rulership and returns the resolved lord graha\'s facts — the resolution chain is served back in `about_resolution`). Returns fact_id references for downstream drill. B.11-floor-injected. chart_id is required — never defaulted.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      about: z.union([
        z.string(),
        z.object({ graha: z.string().optional(), bhava: z.number().int().min(1).max(12).optional(), house_lord: z.number().int().min(1).max(12).optional() }),
      ]).optional().describe('Astrological address facet: "lagna", a graha name, {graha}, {bhava:N}, or {house_lord:N}.'),
      category: z.string().optional().describe(
        'Fact category filter (e.g. "graha_position", "graha_dignity_per_varga", "yoga_label", "house_bhava_bala_total"). Comma-separated for multiple.'
      ),
      planet: z.string().optional().describe('Graha name filter (e.g. "Sun", "Moon", "Saturn", "Rahu", "Ketu").'),
      house: z.number().int().min(1).max(12).optional().describe('Bhava number (1–12) filter.'),
      sign: z.string().optional().describe('Rashi name filter (e.g. "Aries", "Scorpio").'),
      nakshatra: z.string().optional().describe('Nakshatra name filter.'),
      divisional_chart: z.string().optional().describe('Divisional chart code filter (e.g. "D9", "D10").'),
      keyword: z.string().optional().describe('Free-text keyword search over fact_key/fact_value_text.'),
      shape: z.enum(['pivoted', 'rows']).optional().describe('"pivoted" (default, one wide row per subject) or "rows" (flat EAV rows).'),
      limit: z.number().int().min(1).max(1000).optional().describe('Max subjects/rows to return (default: 100, max: 1000).'),
    },
    async ({ chart_id, ayanamsha_id, about, category, planet, house, sign, nakshatra, divisional_chart, keyword, shape, limit }) => {
      if (!chart_id) return errorOutput('query_chart_facts', 'chart_id is required')
      try {
        const data = await callRegistryCapability(
          'marsys://tool/L1/chart_facts_query',
          {
            chart_id,
            ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
            ...(about !== undefined ? { about } : {}),
            ...(category ? { category } : {}),
            ...(planet ? { planet } : {}),
            ...(house != null ? { house } : {}),
            ...(sign ? { sign } : {}),
            ...(nakshatra ? { nakshatra } : {}),
            ...(divisional_chart ? { divisional_chart } : {}),
            ...(keyword ? { keyword } : {}),
            ...(shape ? { shape } : {}),
            ...(limit != null ? { limit } : {}),
          },
          chart_id
        )
        return dualOutput(data)
      } catch (err) {
        return errorOutput('query_chart_facts', String(err), { chart_id })
      }
    }
  )

  // ── vector_search (semantic retrieval — chart-agnostic) ───────────────────
  // Not in the registry; calls platform primitive directly.
  server.tool(
    'vector_search',
    'Semantic vector search over the MARSYS document corpus (domain reports, signal narratives, classical text excerpts, life event annotations). Returns the top-k most semantically similar documents to the query. Chart-agnostic — no chart_id required. Use to find relevant astrological literature, prior domain reports, or signal descriptions matching a natural-language query.',
    {
      query_text: z.string().describe('Natural-language query for semantic retrieval. Required.'),
      top_k: z.number().int().min(1).max(50).optional().describe('Number of results to return (default: 10).'),
      doc_type: z.array(z.string()).optional().describe(
        'Document type filter (e.g. ["domain_report"], ["signal_narrative"], ["classical_text"]). Omit for all types.'
      ),
    },
    async ({ query_text, top_k, doc_type }) => {
      if (!query_text) return errorOutput('vector_search', 'query_text is required')
      try {
        const data = await callPlatformPrimitive('vector_search', {
          query_text,
          top_k: top_k ?? 10,
          ...(doc_type ? { doc_type } : {}),
        }, principal)
        return dualOutput(data)
      } catch (err) {
        return errorOutput('vector_search', String(err))
      }
    }
  )
}
