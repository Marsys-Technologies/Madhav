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
      const { status, envelope } = await callPlatformPrimitive(
        'lel_query',
        {
          chart_id: params.chart_id,
          domain: params.domain ?? null,
          date_from: params.date_from ?? null,
          date_to: params.date_to ?? null,
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

      // Unwrap from the registry envelope — result carries the LEL payload.
      const result = envelope.result as LelQueryResult | null

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(
              {
                ok: true,
                events: result?.events ?? [],
                total_count: result?.total_count ?? 0,
                filter_applied: result?.filter_applied ?? {
                  domain: params.domain ?? null,
                  date_from: params.date_from ?? null,
                  date_to: params.date_to ?? null,
                  limit: params.limit ?? 100,
                },
                provenance_envelope: result?.provenance_envelope ?? {
                  source: 'mimamsa.lel_intake',
                  asset: 'MI-5-1',
                  lel_version: 'LIFE_EVENT_LOG_v1_2.md v1.7',
                  no_leakage_note: 'life_events is calibration corpus only — must not feed prediction generation',
                  b3_compliant: true,
                  queried_at: new Date().toISOString(),
                },
              },
              null,
              2
            ),
          },
        ],
      }
    }
  )
}
