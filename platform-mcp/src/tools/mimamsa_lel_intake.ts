/**
 * mimamsa_lel_intake.ts — BRAHMA-MI-5-1: mimamsa.lel_intake
 *
 * L5 Mīmāṃsā: query the Life Event Log calibration corpus for a chart.
 * chart_id is now required — scopes the query to a specific chart's events.
 *
 * Contract (BRAHMA MI-5-1):
 *   Tables: life_events + event_chart_state_index
 *   Tool:   lel_query(domain?, date_range?)
 *           → {events:[{event_id, event_date, event_type, description, domain,
 *                outcome_observed, dasha_active, antardasha_active,
 *                key_transits, convergence_score, source_citation}],
 *              total_count, filter_applied, provenance_envelope}
 *
 * NO LEAKAGE:
 *   life_events is a calibration corpus ONLY.
 *   It MUST NOT feed into prediction generation pipelines.
 *   All source_citations are non-null (B.3 mandate).
 *   provenance_envelope is present on every response (B.3 mandate).
 *
 * chart_id: required from caller (chart_agnostic_gate RULE-1/4). No default chart.
 *
 * KEYSTONE migration (M6+M7, 2026-07-01):
 *   Migrated from sidecar-direct (PYTHON_SIDECAR_URL) to the registry path via
 *   callPlatformPrimitive('lel_query', ...) — 'lel_query' is whitelisted in
 *   MCP_TO_RETRIEVAL_TOOL (tool_name_bridge.ts, UDA Campaign).
 *   No local DB SQL. No PYTHON_SIDECAR_URL calls. Entitlement gate (M0) preserved.
 *
 * Wiring: registerMimamsaLelIntakeTool(server) → server.ts during L5 Mīmāṃsā registration.
 *
 * BRAHMA-MI-5-1
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { callPlatformPrimitive } from '../client.js'
import { budgetMcpContent } from '../lib/response_budget.js'

// ── Types ──────────────────────────────────────────────────────────────────────

export interface LelEvent {
  event_id: string        // UUID
  event_date: string      // ISO date
  event_type: string      // LEL category
  description: string     // factual description
  domain: string          // category/subcategory compound
  outcome_observed: string | null   // retrodictive match quality
  dasha_active: string | null       // Vimshottari MD lord
  antardasha_active: string | null  // Vimshottari AD lord
  key_transits: string[]            // transit notes
  convergence_score: number | null  // 0.0|0.5|1.0|null
  source_citation: string           // non-null (B.3 mandate)
}

export interface LelProvenanceEnvelope {
  source: string           // 'mimamsa.lel_intake'
  asset: string            // 'MI-5-1'
  lel_version: string      // 'LIFE_EVENT_LOG_v1_2.md v1.7'
  total_events: number     // corpus size
  confidence: number       // 0.89
  source_citation: string  // 'LIFE_EVENT_LOG_v1_2.md (native-disclosed)'
  no_leakage_note: string
  b3_compliant: boolean
  queried_at: string       // ISO datetime
}

export interface LelQueryResult {
  ok: boolean
  events: LelEvent[]
  total_count: number
  filter_applied: {
    domain: string | null
    date_from: string | null
    date_to: string | null
    limit: number
  }
  provenance_envelope: LelProvenanceEnvelope
}

// ── Payload unwrap (WP-1.3d / lel_query-deployed-fix / F-L10-021) ────────────────

/**
 * The /api/mcp/primitives/lel_query route wraps the L5 capability payload in the
 * standard MCP envelope AND the legacy ToolBundle shape:
 *
 *   envelope.result = {
 *     results: [{ content: "<JSON string of the LEL payload>" }], ...ToolBundle fields
 *   }
 *
 * where the LEL payload itself (from query_life_events.ts) is:
 *   { chart_id, events: [...], count, total_matching, filters, provenance }
 *
 * The DEPLOYED bug (E5 envelope-vs-payload lie): this tool previously read
 * `envelope.result.events` / `envelope.result.total_count` directly. Those keys live
 * TWO levels deeper than that (under results[0].content, JSON-encoded) AND the count
 * field is `total_matching`, not `total_count`. So every call collapsed to
 * events:[] / total_count:0 — a dishonest-empty even for the native's 57 rows, while
 * the twin `mimamsa_lel_query` alias (which returns the raw envelope untouched) showed
 * the real data. This helper unwraps the ToolBundle correctly.
 *
 * Returns null ONLY when the payload cannot be located/parsed — the caller surfaces
 * that as an explicit error (never a silent ok:true empty), so honest-empty is reserved
 * for a genuine zero-row result (e.g. a chart with no life events).
 */
function unwrapLelPayload(
  envelopeResult: unknown,
): { events: LelEvent[]; total_count: number; count: number; filters: unknown } | null {
  if (!envelopeResult || typeof envelopeResult !== 'object') return null
  const bundle = envelopeResult as Record<string, unknown>

  // Locate the raw payload: either the ToolBundle results[0].content (normal path),
  // or — defensively — a flat object that already carries `events`.
  let payloadRaw: unknown = null
  const results = bundle['results']
  if (Array.isArray(results) && results.length > 0) {
    const first = results[0] as Record<string, unknown> | undefined
    payloadRaw = first?.['content']
  } else if ('events' in bundle) {
    payloadRaw = bundle
  }
  if (payloadRaw == null) return null

  let payload: Record<string, unknown> | null = null
  if (typeof payloadRaw === 'string') {
    try {
      payload = JSON.parse(payloadRaw) as Record<string, unknown>
    } catch {
      return null
    }
  } else if (typeof payloadRaw === 'object') {
    payload = payloadRaw as Record<string, unknown>
  }
  if (!payload || !Array.isArray(payload['events'])) return null

  const events = payload['events'] as LelEvent[]
  // Honest total: prefer the capability's family-size receipt (total_matching, computed
  // BEFORE the LIMIT), fall back to total_count, then to the served page length.
  const total_count = Number(
    payload['total_matching'] ?? payload['total_count'] ?? events.length,
  )
  const count = Number(payload['count'] ?? events.length)
  return { events, total_count, count, filters: payload['filters'] ?? null }
}

// ── Tool registration ──────────────────────────────────────────────────────────

export function registerMimamsaLelIntakeTool(server: McpServer, principal: Principal): void {
  // REMEDIATION D7 (RULE-3): scrubbed native name + event count from LLM-visible description.
  // Also added required chart_id parameter (RULE-1: per_chart tools must have chart_id).
  // The LEL corpus is per-chart calibration data — chart_id is required to scope it.
  //
  // KEYSTONE (M6+M7): routes through callPlatformPrimitive('lel_query', ...)
  // which is whitelisted in tool_name_bridge.MCP_TO_RETRIEVAL_TOOL.
  // Zero sidecar SQL. Entitlement gate (M0 remoteAuthorize) preserved.
  server.tool(
    'lel_query',
    'Query the Life Event Log calibration corpus for a chart. '
    + 'Returns life events with Vimshottari dasha context and retrodictive match quality. '
    + 'Filter by chart_id, domain (e.g. career, health, spiritual, relationship, family, loss, finance) '
    + 'and/or date range. '
    + 'Requires chart_id — corpus is scoped per chart. '
    + 'NO LEAKAGE: this corpus is for calibration only — must not feed prediction generation. '
    + 'All responses carry provenance_envelope with source_citation (B.3 mandate). '
    + 'BRAHMA-MI-5-1 | mimamsa.lel_intake',
    {
      chart_id: z
        .string()
        .uuid()
        .describe(
          'UUID of the chart whose Life Event Log to query. Required — no default chart.'
        ),
      domain: z
        .string()
        .optional()
        .describe(
          'Case-insensitive substring filter on event domain or event_type. '
          + 'Examples: "career", "health", "spiritual", "relationship", "family", '
          + '"loss", "finance", "creative", "psychological", "travel", "education".'
        ),
      date_from: z
        .string()
        .regex(/^\d{4}-\d{2}-\d{2}$/, 'Must be YYYY-MM-DD')
        .optional()
        .describe('Lower bound date filter (inclusive). Format: YYYY-MM-DD.'),
      date_to: z
        .string()
        .regex(/^\d{4}-\d{2}-\d{2}$/, 'Must be YYYY-MM-DD')
        .optional()
        .describe('Upper bound date filter (inclusive). Format: YYYY-MM-DD.'),
      limit: z
        .number()
        .int()
        .min(1)
        .max(200)
        .optional()
        .default(100)
        .describe('Maximum number of events to return (default: 100, max: 200).'),
    },
    async (params) => {
      if (!params.chart_id) {
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: 'chart_id is required', tool: 'lel_query' }, null, 2) }],
          isError: true as const,
        }
      }
      const authorized = await remoteAuthorize(principal, params.chart_id)
      if (!authorized) {
        return {
          content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }],
          isError: true,
        }
      }

      // KEYSTONE: delegate to the registry path via callPlatformPrimitive.
      // 'lel_query' is whitelisted in MCP_TO_RETRIEVAL_TOOL (tool_name_bridge.ts).
      // WP-1.3d param alignment: the L5 capability (query_life_events.ts) reads
      // `start_date` / `end_date`, NOT `date_from` / `date_to` — the old names were
      // silently dropped at the boundary. Map them so date filters actually apply.
      const { status, envelope } = await callPlatformPrimitive(
        'lel_query',
        {
          chart_id: params.chart_id,
          domain: params.domain ?? null,
          start_date: params.date_from ?? null,
          end_date: params.date_to ?? null,
          limit: params.limit ?? 100,
        },
        principal,
      )

      if (status !== 200 || !envelope.ok) {
        const errorMsg = !envelope.ok
          ? envelope.error?.message ?? 'lel_query primitive failed'
          : `HTTP ${status} from lel_query primitive`
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              ok: false,
              error: errorMsg,
              tool: 'lel_query',
              asset: 'MI-5-1',
              provenance_envelope: {
                source: 'mimamsa.lel_intake',
                asset: 'MI-5-1',
                lel_version: 'LIFE_EVENT_LOG_v1_2.md v1.7',
                no_leakage_note: 'life_events is calibration corpus only — must not feed prediction generation',
                b3_compliant: true,
                queried_at: new Date().toISOString(),
              },
            }, null, 2),
          }],
          isError: true,
        }
      }

      // Unwrap the ToolBundle-wrapped LEL payload (WP-1.3d / F-L10-021). See
      // unwrapLelPayload above for the exact nesting the deployed bug got wrong.
      const payload = unwrapLelPayload(envelope.result)

      // Honesty gate: a null here means the envelope was well-formed (status 200,
      // ok:true) but we could NOT find/parse the LEL payload — that is NOT a genuine
      // empty result, so we must not emit ok:true events:[]. Surface it as an error.
      if (payload === null) {
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              ok: false,
              error: 'lel_query: response envelope did not carry a parseable LEL payload',
              tool: 'lel_query',
              asset: 'MI-5-1',
              provenance_envelope: {
                source: 'mimamsa.lel_intake',
                asset: 'MI-5-1',
                lel_version: 'LIFE_EVENT_LOG_v1_2.md v1.7',
                no_leakage_note: 'life_events is calibration corpus only — must not feed prediction generation',
                b3_compliant: true,
                queried_at: new Date().toISOString(),
              },
            }, null, 2),
          }],
          isError: true,
        }
      }

      const budgeted = budgetMcpContent(
        {
          ok: true,
          events: payload.events,
          total_count: payload.total_count,
          count: payload.count,
          filter_applied: payload.filters ?? {
            domain: params.domain ?? null,
            date_from: params.date_from ?? null,
            date_to: params.date_to ?? null,
            limit: params.limit ?? 100,
          },
          provenance_envelope: {
            source: 'mimamsa.lel_intake',
            asset: 'MI-5-1',
            lel_version: 'LIFE_EVENT_LOG_v1_2.md v1.7',
            total_events: payload.total_count,
            no_leakage_note: 'life_events is calibration corpus only — must not feed prediction generation',
            b3_compliant: true,
            queried_at: new Date().toISOString(),
          },
        },
        'lel_query',
      )

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(budgeted, null, 2),
          },
        ],
      }
    }
  )
}
