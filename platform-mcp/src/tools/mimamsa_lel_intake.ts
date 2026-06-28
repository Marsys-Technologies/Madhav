/**
 * mimamsa_lel_intake.ts — BRAHMA-MI-5-1: mimamsa.lel_intake
 *
 * L5 Mīmāṃsā: query the 57-event Life Event Log calibration corpus.
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
 * Reference birth: 1984-02-05, 10:43 IST, Bhubaneswar
 *   Source: LIFE_EVENT_LOG_v1_2.md (native-disclosed, v1.7, 57 events, confidence 0.89)
 *
 * Wiring: registerMimamsaLelIntakeTool(server) → server.ts during L5 Mīmāṃsā registration.
 *
 * BRAHMA-MI-5-1
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

// ── Environment ────────────────────────────────────────────────────────────────

const PYTHON_SIDECAR_URL = (
  process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'
).replace(/\/$/, '')

const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''
const TOOL_TIMEOUT_MS = 30_000

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
  total_events: number     // 57
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

// ── Sidecar call ───────────────────────────────────────────────────────────────

async function callSidecar<T>(
  path: string,
  body: Record<string, unknown>
): Promise<T> {
  const url = `${PYTHON_SIDECAR_URL}${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (SIDECAR_API_KEY) {
    headers['X-API-Key'] = SIDECAR_API_KEY
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TOOL_TIMEOUT_MS)

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    if (!response.ok) {
      const text = await response.text().catch(() => '')
      throw new Error(
        `Sidecar HTTP ${response.status} from ${path}: ${text.slice(0, 300)}`
      )
    }

    return (await response.json()) as T
  } finally {
    clearTimeout(timer)
  }
}

// ── Tool registration ──────────────────────────────────────────────────────────

export function registerMimamsaLelIntakeTool(server: McpServer): void {
  server.tool(
    'lel_query',
    'Query the Life Event Log calibration corpus for a chart. '
    + 'Returns life events with Vimshottari dasha context and retrodictive match quality. '
    + 'Filter by chart_id, domain (e.g. career, health, spiritual, relationship, family, loss, finance) '
    + 'and/or date range. '
    + 'NO LEAKAGE: this corpus is for calibration only — must not feed prediction generation. '
    + 'All responses carry provenance_envelope with source_citation (B.3 mandate). '
    + 'BRAHMA-MI-5-1 | mimamsa.lel_intake',
    {
      chart_id: z
        .string()
        .uuid()
        .describe('UUID of the chart whose life events to query. Must be a valid chart UUID.'),
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
      try {
        const result = await callSidecar<LelQueryResult>('/brahma/mimamsa/lel_query', {
          chart_id: params.chart_id,
          domain: params.domain ?? null,
          date_from: params.date_from ?? null,
          date_to: params.date_to ?? null,
          limit: params.limit ?? 100,
        })

        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                {
                  ok: true,
                  events: result.events,
                  total_count: result.total_count,
                  filter_applied: result.filter_applied,
                  provenance_envelope: result.provenance_envelope,
                },
                null,
                2
              ),
            },
          ],
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                {
                  ok: false,
                  error: message,
                  tool: 'lel_query',
                  asset: 'MI-5-1',
                  provenance_envelope: {
                    source: 'mimamsa.lel_intake',
                    asset: 'MI-5-1',
                    lel_version: 'LIFE_EVENT_LOG_v1_2.md v1.7',
                    total_events: 57,
                    confidence: 0.89,
                    source_citation: 'LIFE_EVENT_LOG_v1_2.md (native-disclosed)',
                    no_leakage_note:
                      'life_events is calibration corpus only — must not feed prediction generation',
                    b3_compliant: true,
                    queried_at: new Date().toISOString(),
                  },
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        }
      }
    }
  )
}
