/**
 * query_signals.ts — MCP Tier 3 surgical primitive: MSR signal corpus lookup.
 *
 * What it does: Queries the MSR (Master Signal Register) corpus of 499+ astrological
 * signals with structured filters. Returns raw signal rows — domain, valence, dasha
 * activations, confidence, significance, forward-looking flag, and signal text. This
 * is a direct L2.5 data read that bypasses the planner and synthesis stages. Tagged
 * surgical: true in the epistemics block.
 *
 * When to prefer: Use query_signals when you need raw signal data from the MSR corpus
 * rather than synthesized prose. Prefer over holistic_bundle when the goal is "give me
 * all forward-looking signals in the career domain" as a structured list. Prefer
 * holistic_bundle when interpretation or cross-domain synthesis is also required.
 *
 * Input shape hints:
 *   domain — optional; e.g. "career", "health", "relationships", "spiritual".
 *   planet — optional; filter to signals involving a specific planet.
 *   dasha_lord — optional; filter to signals activated by a specific dasha lord.
 *   min_confidence — optional float 0.0–1.0; filter to signals above this threshold.
 *   forward_looking — optional boolean; true = only prospective signals.
 *   limit — optional; max signals to return (default 50).
 *
 * Output shape preview: {ok, result: {signals: MsrSignalRow[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_signals({domain: "career", forward_looking: true, min_confidence: 0.8}) →
 *   {ok: true, result: {signals: [{signal_id: "SIG.MSR.234", domain: "career", ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

// ── LL.1 calibration constants (backport from portal msr_sql.ts, NAP.M4.5 approved) ──────────

// LL.1 production weights — inlined from
// 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ll1_weights_promoted_v1_0.json
// (30 signals, NAP.M4.5 approved 2026-05-02). Signals absent from this map default to 1.0.
const LL1_PRODUCTION_WEIGHTS = new Map<string, number>([
  ['SIG.MSR.001', 1.0],     // prior_id SIG.01
  ['SIG.MSR.009', 1.0],     // prior_id SIG.09
  ['SIG.MSR.010', 1.0],     // prior_id SIG.10
  ['SIG.MSR.012', 1.0],     // prior_id SIG.12
  ['SIG.MSR.013', 1.0],     // prior_id SIG.13 + direct
  ['SIG.MSR.015', 1.0],     // prior_id SIG.15
  ['SIG.MSR.030', 1.0],
  ['SIG.MSR.118', 0.4545],
  ['SIG.MSR.119', 0.4545],
  ['SIG.MSR.143', 0.4545],
  ['SIG.MSR.145', 0.9091],
  ['SIG.MSR.163', 1.0],
  ['SIG.MSR.170', 1.0],
  ['SIG.MSR.198', 1.0],
  ['SIG.MSR.229', 1.0],
  ['SIG.MSR.251', 1.0],
  ['SIG.MSR.278', 1.0],
  ['SIG.MSR.291', 1.0],
  ['SIG.MSR.295', 1.0],
  ['SIG.MSR.297', 1.0],
  ['SIG.MSR.300', 1.0],
  ['SIG.MSR.301', 1.0],
  ['SIG.MSR.391', 1.0],
  ['SIG.MSR.402', 0.7273],
  ['SIG.MSR.476', 1.0],
])

// Domain-specific confidence floors.
// Finance/wealth signals cluster in the 0.35–0.60 range; global 0.6 floor over-filters them.
const FINANCE_WEALTH_DOMAINS = new Set(['finance', 'wealth'])
const DEFAULT_CONFIDENCE_FLOOR = 0.6
const FINANCE_WEALTH_CONFIDENCE_FLOOR = 0.35

// LL.3 R.LL3.2 — Pancha-Mahapurusha clique dedup.
// These 7 signal IDs form one natal yoga; consolidate to MAX-weight entry to prevent
// N× double-counting. SIG.MSR.402 is invalidated; SIG.MSR.402b is the corrected form —
// both are included so the modifier fires regardless of DB state.
const PANCHA_MP_CLIQUE = new Set([
  'SIG.MSR.117', 'SIG.MSR.118', 'SIG.MSR.119',
  'SIG.MSR.143', 'SIG.MSR.145',
  'SIG.MSR.402', 'SIG.MSR.402b',
])
const PANCHA_MP_CONSOLIDATED_ID = 'PANCHA_MP_CLIQUE_CONSOLIDATED'

interface ToolBundleResult {
  content: string
  source_canonical_id: string
  source_version?: string
  confidence?: number
  significance?: number
  signal_id?: string
  [key: string]: unknown
}

/**
 * Apply LL.1 calibration to a set of ToolBundleResults:
 *   1. Multiply confidence by LL.1 weight (signals absent from map → weight 1.0).
 *   2. Filter out results that fall below the domain confidence floor.
 *   3. Deduplicate the Pancha-MP clique to a single MAX-weight entry.
 *
 * The domain parameter is used only for determining the confidence floor;
 * it should match the domain(s) requested by the caller.
 */
function calibrateResults(
  results: ToolBundleResult[],
  domain?: string,
  domains?: string[],
): ToolBundleResult[] {
  const effectiveDomains = domains && domains.length > 0
    ? domains
    : domain ? [domain] : []

  const isFinanceWealth = effectiveDomains.some(d => FINANCE_WEALTH_DOMAINS.has(d))
  const domain_floor = isFinanceWealth
    ? FINANCE_WEALTH_CONFIDENCE_FLOOR
    : DEFAULT_CONFIDENCE_FLOOR

  // Step 1: apply LL.1 weights to calibrate confidence
  let calibrated: ToolBundleResult[] = results.map(r => ({
    ...r,
    confidence: (r.confidence ?? 0) * (r.signal_id != null ? (LL1_PRODUCTION_WEIGHTS.get(r.signal_id) ?? 1.0) : 1.0),
  }))

  // Step 2: apply confidence floor — drop calibrated results below the floor
  calibrated = calibrated.filter(r => (r.confidence ?? 0) >= domain_floor)

  // Step 3: Pancha-MP clique dedup — consolidate ≥2 clique members to MAX entry
  const cliqueMembers = calibrated.filter(r => r.signal_id != null && PANCHA_MP_CLIQUE.has(r.signal_id))
  if (cliqueMembers.length >= 2) {
    const nonClique = calibrated.filter(r => r.signal_id == null || !PANCHA_MP_CLIQUE.has(r.signal_id))
    const maxEntry = cliqueMembers.reduce((a, b) =>
      (a.confidence ?? 0) >= (b.confidence ?? 0) ? a : b
    )
    calibrated = [
      ...nonClique,
      {
        ...maxEntry,
        signal_id: PANCHA_MP_CONSOLIDATED_ID,
        content:
          `[PANCHA_MP_CLUSTER] Pancha-Mahapurusha yoga configuration: ${cliqueMembers.map(r => r.signal_id).join(', ')}. ` +
          `Consolidated per LL.3 R.LL3.2 cluster-modifier (prevents ${cliqueMembers.length}× double-counting). ` +
          `Representative signal: ${maxEntry.content}`,
      },
    ]
  }

  return calibrated
}

export const QUERY_SIGNALS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Queries the MSR signal corpus (499+ astrological signals) with structured ' +
    'filters (domain, domains[], planet, dasha_lord, min_confidence, forward_looking, valence, temporal_activation) ' +
    'and returns raw signal rows without synthesis.',
  coverageHint: '499+ signals across all Jyotish domains',
  whenToPrefer:
    'Use for "give me all forward-looking career signals" style queries. ' +
    'Prefer holistic_bundle when interpretation or cross-domain synthesis is also needed. ' +
    'Prefer query_chart_facts for raw chart-fact rows rather than MSR signals.',
})

const QuerySignalsInputSchema = z.object({
  domain: z.string().optional().describe(
    'Jyotish domain filter. Examples: "career", "health", "relationships", "spiritual".'
  ),
  domains: z.array(z.string()).optional().describe(
    'Multiple domain filters. When provided, returns signals matching any of the listed domains. ' +
    'Prefer this over repeated single-domain calls.'
  ),
  planet: z.string().optional().describe('Filter to signals involving a specific planet.'),
  dasha_lord: z.string().optional().describe(
    'Filter to signals activated by a specific dasha lord (e.g. "Saturn", "Ketu").'
  ),
  min_confidence: z.number().min(0).max(1).optional().describe(
    'Minimum confidence threshold (0.0–1.0). Returns signals at or above this level.'
  ),
  forward_looking: z.boolean().optional().describe(
    'If true, return only prospective (forward-looking) signals.'
  ),
  valence: z.enum(['benefic', 'malefic', 'context-dependent']).optional().describe(
    'Filter by signal valence. "benefic" = helpful/positive outcomes; "malefic" = challenging/difficult; "context-dependent" = mixed or situational.'
  ),
  temporal_activation: z.enum(['permanent', 'dasha_tied', 'transit_tied']).optional().describe(
    'Filter by activation pattern. "permanent" = natal, always active; "dasha_tied" = active only in specific dasha periods; "transit_tied" = active only during specific transits.'
  ),
  limit: z.number().int().min(1).max(500).optional().default(50).describe(
    'Max signals to return (default 50, max 500).'
  ),
})

type QuerySignalsInput = z.infer<typeof QuerySignalsInputSchema>

export function registerQuerySignals(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_signals',
    QUERY_SIGNALS_DESCRIPTION,
    QuerySignalsInputSchema.shape,
    async (args: QuerySignalsInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_signals',
        {
          ...(args.domain ? { domain: args.domain } : {}),
          ...(args.domains && args.domains.length > 0 ? { domains: args.domains } : {}),
          ...(args.planet ? { planet: args.planet } : {}),
          ...(args.dasha_lord ? { dasha_lord: args.dasha_lord } : {}),
          ...(args.min_confidence !== undefined ? { min_confidence: args.min_confidence, confidence_floor: args.min_confidence } : {}),
          ...(args.forward_looking !== undefined ? { forward_looking: args.forward_looking } : {}),
          ...(args.valence !== undefined ? { valence: [args.valence] } : {}),
          ...(args.temporal_activation !== undefined ? { temporal_activation: [args.temporal_activation] } : {}),
          limit: args.limit ?? 50,
        },
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }

      // Apply LL.1 calibration: weights, domain confidence floors, Pancha-MP clique dedup.
      // Mirrors the calibration applied by portal msr_sql.ts (NAP.M4.5 approved).
      const rawEnvelope = envelope as unknown as {
        result?: { results?: ToolBundleResult[] }
        [key: string]: unknown
      }
      if (
        rawEnvelope.result != null &&
        typeof rawEnvelope.result === 'object' &&
        Array.isArray((rawEnvelope.result as { results?: unknown }).results)
      ) {
        const bundle = rawEnvelope.result as { results: ToolBundleResult[]; [key: string]: unknown }
        bundle.results = calibrateResults(bundle.results, args.domain, args.domains)
      }

      return okResult(envelope)
    }
  )
}
