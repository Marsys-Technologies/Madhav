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
import type { Principal } from '../types.js'
import { describeProxyFailure } from './registry_bridge.js'
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
  type DrillPointerType,
  type CoverageStamp,
} from '../generated/envelope.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function callRegistryCapability(uri: string, args: Record<string, unknown>, principal: Principal): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(25_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    // R5.2 A3 (battery X-2 finding, same class as registry_bridge.ts's identical fix):
    // don't leak the raw HTTP status code into the MCP-facing error text.
    throw new Error(describeProxyFailure(uri, res.status, text))
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
    drill_pointers?: { instrument: string; hint: string; pointer_type?: DrillPointerType }[]
    judgment_flags?: string[]
    as_of_date?: string
    epistemic?: ReturnType<typeof buildEpistemicSummary>
    coverage?: CoverageStamp | null
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
      coverage: v3Extras?.coverage,
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

// ── R-5 fix: typed error envelope, never leak raw SQL/driver detail ──────────
//
// Denial ≠ empty ≠ internal error (register R-5): a caught error's `String(err)` may be a
// deliberately-authored, safe validation/denial message ("chart_id is required",
// "ENTITLEMENT_DENIED: ...") OR a raw driver/SQL error ('column "salience_score" does not
// exist', a stack frame, a connection string). The former is safe to echo verbatim; the
// latter must NEVER reach the client — it leaks internal schema/implementation detail and
// gives callers no stable, typed thing to branch on. classifyErrorMessage() distinguishes
// the three classes; errorOutput() logs the raw detail server-side only when it collapses
// an internal-looking message to the generic safe one.
type McpErrorClass = 'validation' | 'permission_denied' | 'internal_error'

function classifyErrorMessage(message: string): { error_class: McpErrorClass; safe_message: string } {
  if (/ENTITLEMENT_DENIED|AUTHZ_DENIED|lacks .* access/i.test(message)) {
    return { error_class: 'permission_denied', safe_message: message }
  }
  if (/ is required($|[^a-zA-Z])|^either `|^Unknown facet|^Unsupported /i.test(message)) {
    return { error_class: 'validation', safe_message: message }
  }
  const looksInternal =
    /column ".*" does not exist|relation ".*" does not exist|syntax error at or near|ECONNREFUSED|invalid input syntax|PostgresError|\bat \S+\.(ts|js):\d+|\.node_modules[\\/]/i.test(message)
  if (looksInternal) {
    return {
      error_class: 'internal_error',
      safe_message: 'An internal error occurred while serving this request. The specific ' +
        'cause has been logged server-side and is not exposed to the client (never leak raw ' +
        'SQL/driver detail — R-5).',
    }
  }
  return { error_class: 'internal_error', safe_message: message }
}

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  const { error_class, safe_message } = classifyErrorMessage(message)
  if (error_class === 'internal_error' && safe_message !== message) {
    console.error(`[${tool}] internal_error (raw, server-only, never sent to client): ${message}`)
  }
  const data = { ok: false, error: { class: error_class, message: safe_message }, tool, ...extra }
  return { ...dualOutput(data), isError: true as const }
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
// R-17 fix: parivartana and graha_yuddha were both routed to get_yoga_dosha, which has no
// backing category for either (its 6 categories are yoga_fires/yoga_label/dosha_fires/
// dosha_label/bhadra_flag/panchaka_flag) — both facets silently returned the identical
// unfiltered ~107-row yoga/dosha union. Their real data lives elsewhere: parivartana
// (mutual sign exchange) is fact_category parivartana_per_varga on get_dispositors;
// graha_yuddha (planetary war) has its own dedicated capability, get_graha_yuddha.
const STRUCTURAL_FACET_URI: Record<string, string> = {
  aspects:      'marsys://tool/L1/get_aspects',
  conjunctions: 'marsys://tool/L1/get_aspects',
  sambandha:    'marsys://tool/L1/get_aspects',
  argala:       'marsys://tool/L1/get_argala',
  dispositors:  'marsys://tool/L1/get_dispositors',
  functional:   'marsys://tool/L1/get_dispositors',
  parivartana:  'marsys://tool/L1/get_dispositors',
  yoga_fires:   'marsys://tool/L1/get_yoga_dosha',
  dosha_fires:  'marsys://tool/L1/get_yoga_dosha',
  graha_yuddha: 'marsys://tool/L1/get_graha_yuddha',
}

// R-17 fix: each facet's DECLARED fact_category set. Used two ways: (1) narrows the
// underlying query via `categories` so facets sharing a URI (aspects/conjunctions/sambandha;
// dispositors/parivartana; yoga_fires/dosha_fires) actually return DIFFERENT row sets instead
// of the tool's full unfiltered union; (2) a serve-time assertion (below) verifies every
// returned row's fact_category is actually a member of this set — fails loudly instead of
// silently serving a mismatched category set if the map ever drifts from the underlying
// tool's real categories again.
//
// `functional` (functional benefic/malefic role) has NO dedicated L1 fact_category — that
// classification is derived logic living in graha_portrait.ts (R-6), not a stored chart_facts
// row. Declared as an empty/unbacked facet below: rejected outright rather than silently
// serving unrelated dispositor rows (canonical-or-floor: no backing category = no serve).
const FACET_CATEGORIES: Record<string, string[]> = {
  aspects: [
    'aspect_parashari_given', 'aspect_parashari_received', 'aspect_parashari_per_varga',
    'aspect_jaimini', 'aspect_jaimini_per_varga', 'aspect_matrix_summary', 'aspect_tajik',
  ],
  conjunctions: ['conjunction_within_orb', 'conjunction_per_varga'],
  sambandha:    ['lord_aspects_lord_per_varga', 'lord_in_house_per_varga'],
  dispositors:  [
    'graha_dispositor_chain', 'dispositor_chain_per_varga', 'composite_dispositor_strength',
    'parivartana_per_varga', 'kala_sarpa_per_varga',
  ],
  parivartana:  ['parivartana_per_varga'],
  yoga_fires:   ['yoga_fires', 'yoga_label', 'bhadra_flag'],
  dosha_fires:  ['dosha_fires', 'dosha_label'],
  graha_yuddha: ['graha_yuddha'],
  // argala intentionally omitted: get_argala is a single-purpose tool with no sibling facets
  // sharing its URI, so there is no cross-facet contamination risk to assert against.
}

// Facets with no valid backing category at all — rejected before dispatch (see comment above).
const NO_BACKING_FACETS = new Set(['functional'])

// R5.3 B2 (Q9-N-3 ruling): Pancha Mahapurusha classical rule table (own-sign/exaltation +
// kendra). Static classical astrology (not chart data) — used only to LABEL already-fetched
// per-chart facts (yoga_label rows + graha_position sign/house_d1), never to compute a new
// chart value (B.10).
const KENDRA_HOUSES = new Set([1, 4, 7, 10])
const PANCHA_MAHAPURUSHA: {
  yoga: string; karaka: string; planet: string; ownSigns: string[]; exaltSign: string
}[] = [
  { yoga: 'Ruchaka', karaka: 'Mars',    planet: 'MAR', ownSigns: ['Aries', 'Scorpio'],       exaltSign: 'Capricorn' },
  { yoga: 'Bhadra',  karaka: 'Mercury', planet: 'MER', ownSigns: ['Gemini', 'Virgo'],        exaltSign: 'Virgo' },
  { yoga: 'Hamsa',   karaka: 'Jupiter', planet: 'JUP', ownSigns: ['Sagittarius', 'Pisces'],  exaltSign: 'Cancer' },
  { yoga: 'Malavya', karaka: 'Venus',   planet: 'VEN', ownSigns: ['Taurus', 'Libra'],        exaltSign: 'Pisces' },
  { yoga: 'Sasa',    karaka: 'Saturn',  planet: 'SAT', ownSigns: ['Capricorn', 'Aquarius'],  exaltSign: 'Libra' },
]

/** Builds per-yoga formed/not-formed sentences for the 5 Pancha Mahapurusha yogas from rows
 *  and planetary positions THIS RESPONSE ALREADY FETCHED (yoga_label presence = fired, per
 *  JL-004's ratified convention; graha_position sign/house_d1 = already-computed L1 facts,
 *  not a new derivation). Zero new computation. */
function buildPanchaMahapurushaVerdict(
  yogaDoshaRows: Record<string, unknown>[],
  posByPlanet: Record<string, { sign?: string; house?: number; factId?: string }>,
) {
  const firedYogaNames = new Set(
    yogaDoshaRows
      .filter(r => r['fact_category'] === 'yoga_label')
      .map(r => String(r['fact_value_text'] ?? '')),
  )

  const perYoga = PANCHA_MAHAPURUSHA.map(entry => {
    const pos = posByPlanet[entry.planet]
    const formed = firedYogaNames.has(`${entry.yoga} Yoga`) || firedYogaNames.has(`${entry.karaka} Yoga`)
    const sourceRow = yogaDoshaRows.find(
      r => r['fact_category'] === 'yoga_label' && String(r['fact_value_text'] ?? '').startsWith(entry.yoga),
    )
    const citations = (sourceRow?.['fact_value_jsonb'] as { classical_citations?: { text_id: string; chapter?: number }[] } | undefined)
      ?.classical_citations
    const citationText = citations?.length
      ? citations.map(c => c.chapter ? `${c.text_id} ch.${c.chapter}` : c.text_id).join(', ')
      : undefined

    let reason: string
    if (formed) {
      const dignity = pos?.sign === entry.exaltSign ? 'exalted' : entry.ownSigns.includes(pos?.sign ?? '') ? 'own sign' : 'condition satisfied'
      reason = `${entry.karaka} is in ${pos?.sign ?? 'unknown sign'} (${dignity})${typeof pos?.house === 'number' ? `, house ${pos.house}` : ''} — the own/exaltation-in-kendra condition is satisfied.` +
        (citationText ? ` Classical basis: ${citationText}.` : '')
    } else if (pos?.sign && !entry.ownSigns.includes(pos.sign) && pos.sign !== entry.exaltSign) {
      reason = `${entry.karaka} is in ${pos.sign} — neither own sign (${entry.ownSigns.join('/')}) nor exalted (${entry.exaltSign}); the condition fails on the sign leg.`
    } else if (pos?.sign && (entry.ownSigns.includes(pos.sign) || pos.sign === entry.exaltSign) && typeof pos.house === 'number' && !KENDRA_HOUSES.has(pos.house)) {
      reason = `${entry.karaka} is in ${pos.sign} (own/exalted sign) but house ${pos.house} is not a kendra (1st/4th/7th/10th); the condition fails on the kendra leg.`
    } else {
      reason = `${entry.karaka}'s position was not available in this response to state a specific failed condition; not formed per its absence from the yoga_label rows served.`
    }

    return {
      yoga: `${entry.yoga} (${entry.karaka} Mahapurusha Yoga)`,
      status: formed ? 'formed' : 'not formed',
      statement: `${entry.yoga} (${entry.karaka} Mahapurusha Yoga) is ${formed ? 'formed' : 'not formed'}. ${reason}`,
    }
  })

  const formedList = perYoga.filter(p => p.status === 'formed')
  const summary = formedList.length > 0
    ? `Yes, ${formedList.length} of 5 Pancha Mahapurusha yoga${formedList.length === 1 ? '' : 's'} — ${formedList.map(p => p.yoga).join(', ')} — ${formedList.length === 1 ? 'is' : 'are'} formed; the other ${5 - formedList.length} ${5 - formedList.length === 1 ? 'is' : 'are'} not formed.`
    : 'No Pancha Mahapurusha yoga is formed in this chart.'

  return { summary, per_yoga: perYoga }
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

export function registerP1GanitaTools(server: McpServer, principal: Principal): void {

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
        }, principal)
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
    'Specify exactly one facet per call. ' +
    'response_format=\'v3\' (opt-in; default \'legacy\') returns the R5 unified envelope; for ' +
    'facet=dosha_fires it additionally states an explicit Kala Sarpa Dosha natal verdict ' +
    '(fired/not-fired, Rahu/Ketu house axis) sourced from the genuinely computed ' +
    'kala_sarpa_per_varga L1 fact rather than the unrelated dosha_label catalog row.',
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
      response_format: z.enum(['legacy', 'v3']).optional()
        .describe("Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/" +
          'drill_pointers/chart_header — for facet=dosha_fires includes an explicit Kala Sarpa verdict).'),
    },
    async ({ chart_id, facet, ayanamsha_id, limit, offset, response_format }) => {
      if (!chart_id) return errorOutput('ganita_structural_get', 'chart_id is required')
      // R-17 fix: reject facets with no backing category outright, rather than silently
      // serving whatever unrelated rows the routed-to tool happens to return.
      if (NO_BACKING_FACETS.has(facet)) {
        return errorOutput(
          'ganita_structural_get',
          `facet="${facet}" has no dedicated L1 fact_category — this classification is derived ` +
          'logic (see graha_portrait.ts functional_nature), not a stored chart_facts row. ' +
          'Use graha_portrait with include=["functional_nature"] instead.',
          { chart_id, facet },
        )
      }
      const uri = STRUCTURAL_FACET_URI[facet]
      if (!uri) return errorOutput('ganita_structural_get', `Unknown facet: ${facet}`)
      try {
        const resolvedOffset = offset ?? 0
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        const format = resolveEnvelopeFormat(response_format)
        const declaredCategories = FACET_CATEGORIES[facet]
        const data = await callRegistryCapability(uri, {
          chart_id, ayanamsha_id: resolvedAyanamsha,
          limit: limit ?? 25000, offset: resolvedOffset, facet,
          ...(declaredCategories ? { categories: declaredCategories } : {}),
        }, principal) as Record<string, unknown> | undefined
        const merged: Record<string, unknown> = { facet, ...(typeof data === 'object' && data ? data : { rows: data }) }

        // R-17 serve-time assertion: verify every returned row's fact_category is actually a
        // member of this facet's declared set. Fails loudly (rather than silently serving a
        // mismatched category set) if the map ever drifts from the underlying tool's real
        // categories again — this is the exact failure mode that caused the graha_yuddha/
        // parivartana bug in the first place.
        if (declaredCategories) {
          const mergedRows = Array.isArray(merged['rows']) ? merged['rows'] as Record<string, unknown>[] : []
          const declaredSet = new Set(declaredCategories)
          const offendingCategories = [...new Set(
            mergedRows
              .map(r => r['fact_category'] as string | undefined)
              .filter((c): c is string => Boolean(c) && !declaredSet.has(c as string))
          )]
          if (offendingCategories.length > 0) {
            return errorOutput(
              'ganita_structural_get',
              `facet="${facet}" routing assertion failed: returned rows include ` +
              `fact_category(s) [${offendingCategories.join(', ')}] outside the facet's declared ` +
              `set [${declaredCategories.join(', ')}]. This is a facet→category map bug, not a ` +
              'data problem — the map must be corrected, not the assertion widened.',
              { chart_id, facet },
            )
          }
        }

        if (format !== 'v3') {
          return dualOutput(envelope(merged, 'ganita_structural_get'))
        }

        // ── v3 population (R5.3 B2, Q9-N-1: dosha_fires had NO narration of any kind — always
        // legacy format; see the FACET_TO_TYPE + kala_sarpa_per_varga fixes in get_yoga_dosha.ts
        // for the wiring + data-availability half of this fix) ──
        const rows = Array.isArray(merged['rows']) ? merged['rows'] as Record<string, unknown>[] : []
        const grounding = extractGroundingFromFactRows(rows)
        const judgment_flags: string[] = []
        if (rows.length === 0) judgment_flags.push('zero_rows_returned')

        const drill_pointers: { instrument: string; hint: string; pointer_type: DrillPointerType }[] = [
          { instrument: 'get_signals', hint: 'signal_type_class=yoga|dosha for salience-ranked cross-validation against L2 Bodha (SC-18: was previously mis-pointed at the non-existent MCP tool name "query_signals").', pointer_type: 'opposing_yoga' },
        ]

        let verdict: unknown = {
          facet,
          rows_served: rows.length,
          note: 'Row-count receipt; a facet-specific narrated verdict is added for facet=dosha_fires.',
        }

        if (facet === 'dosha_fires') {
          const ks = merged['kala_sarpa_per_varga'] as
            | { natal?: Record<string, unknown>[]; divisional_fired?: Record<string, unknown>[] }
            | undefined
          const natalRow = ks?.natal?.[0]
          const natalDetail = natalRow?.['fact_value_jsonb'] as
            | { fires?: boolean; rahu_house?: number; ketu_house?: number }
            | undefined
          const catalogRow = rows.find(r => r['fact_category'] === 'dosha_label' && r['fact_value_text'] === 'Kala Sarpa Dosha')

          if (natalDetail && typeof natalDetail.fires === 'boolean') {
            const fires = natalDetail.fires === true
            const divisionalFiredList = (ks?.divisional_fired ?? [])
              .map(r => (r['fact_value_jsonb'] as { varga?: string } | undefined)?.varga)
              .filter((v): v is string => Boolean(v))
            verdict = {
              facet,
              kala_sarpa_dosha: {
                natal_verdict: fires ? 'formed' : 'not_formed',
                statement: fires
                  ? `Kala Sarpa Dosha IS formed in the natal (D1/Rasi) chart — Rahu occupies house ${natalDetail.rahu_house}, Ketu house ${natalDetail.ketu_house}, with all seven non-nodal grahas confined to the arc between them on one side.`
                  : `Kala Sarpa Dosha is NOT formed in the natal (D1/Rasi) chart. The Rahu-Ketu axis is present — Rahu occupies house ${natalDetail.rahu_house}, Ketu house ${natalDetail.ketu_house} — but the classical condition requires ALL SEVEN non-nodal grahas confined within the arc between Rahu and Ketu on one side; this D1 detection returning not-fired means at least one graha falls outside that arc.`,
                rahu_house: natalDetail.rahu_house,
                ketu_house: natalDetail.ketu_house,
                source_fact_id: natalRow?.['fact_id'],
                reconciliation_note: catalogRow
                  ? `A generic "Kala Sarpa Dosha" catalog row does appear among this chart's dosha_label rows (fact_id ${String(catalogRow['fact_id'])}), but its cited constituent fact is a generic placeholder unrelated to Rahu/Ketu placement, shared by dozens of unrelated catalog rows — it is NOT the verified per-chart computation. The kala_sarpa_per_varga fact above (fact_category=kala_sarpa_per_varga, fact_key=ks_detection, varga=D1) is the authoritative, genuinely per-chart-computed Rahu/Ketu detection.`
                  : 'No competing "Kala Sarpa Dosha" catalog row was present in this page.',
                divisional_charts_with_fires_true: divisionalFiredList,
                divisional_note: divisionalFiredList.length > 0
                  ? `Several divisional (varga) charts DO show Kala Sarpa formation (fires=true): ${divisionalFiredList.join(', ')}. These are DIVISIONAL findings, not natal — they do not contradict the D1 natal verdict above.`
                  : 'No divisional (varga) chart in this response showed fires=true.',
              },
            }
            drill_pointers.push({ instrument: 'ganita_structural_get', hint: 'facet=dispositors surfaces the full kala_sarpa_per_varga row set (all vargas) directly.', pointer_type: 'other' })
          }
        }

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability('marsys://tool/L1/get_chart_header', {
            chart_id, ayanamsha_id: resolvedAyanamsha,
          }, principal) as ChartHeader
        } catch {
          chart_header = null // frame-safety header is best-effort; never fails the instrument
        }

        const total = typeof merged['total'] === 'number' ? merged['total'] as number : null

        return dualOutput(envelope(merged, 'ganita_structural_get', {
          offset: resolvedOffset,
          limit: limit ?? 25000,
          total,
        }, 'v3', { chart_header, verdict, grounding, drill_pointers, judgment_flags }))
      } catch (err) {
        return errorOutput('ganita_structural_get', String(err), { chart_id, facet })
      }
    }
  )

  // ── 3. ganita_condition_get ───────────────────────────────────────────────
  server.tool(
    'ganita_condition_get',
    'Retrieve planetary condition data for a chart (L1 Gaṇita). ' +
    'Three facets: dignity (exaltation/debilitation/own-sign/friend/enemy + vargottama; NOTE: ' +
    'neecha-bhanga/debility-cancellation is NOT computed anywhere in this build — see ' +
    'MARSYS_DEFECT_GAP_REGISTER Y-3 — this facet does not detect or report it despite the ' +
    'classical name appearing in dignity theory), ' +
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
        }, principal)
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
        }, principal)
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
        }, principal)
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
        }, principal)
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
    'Covers classical yoga types actually evaluated in this build: Pancha Mahapurusha (Ruchaka/' +
    'Bhadra/Hamsa/Malavya/Shasha) and Parivartana Yogas; plus doshas: Mangal Dosha, Kemadruma, ' +
    'Grahan Yoga, Shrapit, Shakata. HONEST GAP (see MARSYS_DEFECT_GAP_REGISTER §1): Viparita Raja, ' +
    'Neecha Bhanga (debility-cancellation), Dhana Yoga, and the house-lord Raja Yoga family are ' +
    'NOT evaluated by any live path in this build (skip-listed or dead legacy code) — they will ' +
    'never fire from this tool regardless of chart data; do not infer their absence/presence from ' +
    'a missing/present row here. ' +
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
        }, principal) as { total?: number; rows?: Record<string, unknown>[] } | undefined
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
        // R5.3 B2 (Q9-N-3 ruling): the row-count receipt above is a receipt, not narration.
        // Fetch graha positions (already-computed L1 fact_category, zero new computation) to
        // label the 5 named Pancha Mahapurusha yogas formed/not-formed with a citable reason —
        // best-effort: if the fetch fails, verdict still ships with the receipt fields above.
        let panchaMahapurusha: ReturnType<typeof buildPanchaMahapurushaVerdict> | undefined
        try {
          const positionsData = await callRegistryCapability('marsys://tool/L1/get_positions', {
            chart_id, ayanamsha_id: resolvedAyanamsha, categories: ['graha_position'], limit: 200,
          }, principal) as { rows?: Record<string, unknown>[] } | undefined
          const posByPlanet: Record<string, { sign?: string; house?: number; factId?: string }> = {}
          for (const r of positionsData?.rows ?? []) {
            const subj = String(r['fact_subject'] ?? '')
            if (!subj) continue
            const slot = (posByPlanet[subj] ??= {})
            if (r['fact_key'] === 'sign') slot.sign = String(r['fact_value_text'] ?? '')
            if (r['fact_key'] === 'house_d1' && r['fact_value_num'] != null) slot.house = Number(r['fact_value_num'])
          }
          panchaMahapurusha = buildPanchaMahapurushaVerdict(rows, posByPlanet)
        } catch {
          panchaMahapurusha = undefined // best-effort narration enrichment; never fails the instrument
        }

        const verdict = {
          yogas_fired: categoryCounts['yoga_label'] ?? 0,
          doshas_fired: categoryCounts['dosha_label'] ?? 0,
          bhadra_flag_rows: categoryCounts['bhadra_flag'] ?? 0,
          panchaka_flag_rows: categoryCounts['panchaka_flag'] ?? 0,
          category_counts: categoryCounts,
          note: 'Counts are of ROWS SERVED IN THIS PAGE only — see pagination.total for the full count.',
          ...(panchaMahapurusha ? { pancha_mahapurusha: panchaMahapurusha } : {}),
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

        // Typed per design §28.4 (R5 W3 Phase B) — additive `pointer_type` alongside the
        // pre-existing {instrument, hint} shape.
        const drill_pointers: { instrument: string; hint: string; pointer_type: DrillPointerType }[] = [
          { instrument: 'get_signals', hint: 'signal_type_class=yoga|dosha for salience-ranked cross-validation against L2 Bodha (SC-18: was previously mis-pointed at the non-existent MCP tool name "query_signals").', pointer_type: 'opposing_yoga' },
          { instrument: 'mimamsa_insight_get', hint: 'calibrated_outlook / load_bearing insight units built on top of these firings.', pointer_type: 'other' },
        ]

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability('marsys://tool/L1/get_chart_header', {
            chart_id, ayanamsha_id: resolvedAyanamsha,
          }, principal) as ChartHeader
        } catch {
          chart_header = null // frame-safety header is best-effort; never fails the instrument
        }

        const epistemic = buildEpistemicSummary({
          verifiedFraction: grounding.grounding_score,
          note: 'verified_fraction = share of this page\'s rows with verification_pass_status=two_pass_verified.',
        })

        // D5 coverage receipt (design §10.5): `total` above is a genuine COUNT(*) against
        // the SAME chart_id/category/ayanamsha filters this page was drawn from (get_yoga_dosha.ts) —
        // not a re-guess. family names the filtered set this page is a slice of.
        const coverage: CoverageStamp = {
          family: `yoga_dosha_rows[categories=${(data as { categories?: string[] } | undefined)?.categories?.join(',') ?? 'all'}]`,
          served: rows.length,
          total,
        }

        return dualOutput(envelope(data, 'ganita_yogas_get', {
          offset: resolvedOffset,
          limit: limit ?? 500,
          total,
        }, 'v3', { chart_header, verdict, ranking_basis, grounding, drill_pointers, judgment_flags, epistemic, coverage }))
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
        }, principal)
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
        }, principal)
        return dualOutput(envelope(data, 'ganita_transit_anchors_get'))
      } catch (err) {
        return errorOutput('ganita_transit_anchors_get', String(err), { chart_id })
      }
    }
  )
}
