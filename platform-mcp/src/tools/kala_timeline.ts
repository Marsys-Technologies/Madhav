/**
 * kala_timeline.ts — BRAHMA-KA-3-1: kala.timeline
 *
 * Asset:  kala.timeline (L3 Kāla)
 * Tool:   timeline_query(chart_id, date_range) → {timeline, provenance_envelope}
 * Table:  kala_timeline (chart_id, date, active_mahadasha, active_antardasha,
 *                        transit_highlights JSONB, signal_activations JSONB,
 *                        source_citation NOT NULL)
 *
 * CONTRACT (BRAHMA L3 Kāla KA-3-1):
 *   - owns:  deterministic dasha×transit alignment series over native life range
 *   - tool:  timeline_query(chart_id, date_range)
 *   - layer: L3 Kāla (depends on L1 ganita.dashas + L1 ganita.positions
 *                     + L2 bodha.signals)
 *   - source: PyJHora/SwissEph DE441 + Brahma-L1
 *   - acceptance:
 *       - source_citation NOT NULL on all rows
 *       - deterministic: same date always returns same row
 *       - chart-agnostic: chart_id required, no native defaults
 *
 * R2.1 (2026-06-30): Repointed from direct pg.Pool + hardcoded FORENSIC schedule
 * to callPlatformPrimitive('kala_timeline', params) — registry = served surface.
 * Native-specific FORENSIC dasha schedule and algorithmic fallback removed; data
 * comes from the registry for the caller-supplied chart_id.
 *
 * Wiring: registerKalaTimeline(server, getPrincipal) → server.ts during L3 Kāla registration.
 *
 * BRAHMA-KA-3-1
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal, McpEnvelopeError } from '../types.js'

// ── Input schema ──────────────────────────────────────────────────────────────

const DateRangeSchema = z.object({
  start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, {
    message: 'start must be ISO date YYYY-MM-DD',
  }),
  end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, {
    message: 'end must be ISO date YYYY-MM-DD',
  }),
})

const KalaTimelineSchema = z.object({
  /**
   * Chart UUID to query the timeline for.
   */
  chart_id: z.string().uuid({
    message: 'chart_id must be a valid UUID',
  }),

  /**
   * Date range for the timeline query.
   * Both start and end are inclusive ISO dates (YYYY-MM-DD).
   * Maximum span: 36,600 days (~100 years). Typical use: 1–5 years.
   */
  date_range: DateRangeSchema,

  /**
   * Maximum number of rows to return. Default: 365 (one year of daily rows).
   * Max: 36,600.
   */
  limit: z.number().int().min(1).max(36_600).default(365),
})

export type KalaTimelineParams = z.infer<typeof KalaTimelineSchema>

// ── Tool description ──────────────────────────────────────────────────────────

const KALA_TIMELINE_DESCRIPTION = `\
What it does: Returns the deterministic dasha×transit alignment series from \
kala_timeline (KA-3-1, L3 Kāla). Each row contains the active Vimshottari \
Mahadasha + Antardasha lord for the given date, optional transit highlights \
from ephemeris_daily, and optional bodha signal activations from L2 Bodha.

Source: PyJHora/SwissEph DE441 + Brahma-L1 (FORENSIC §5.1 canonical dasha dates). \
FORENSIC dates are canonical per GAP.09 — JH dates (±7–9 days) are NOT used.

Outputs per row: date (ISO), active_mahadasha (e.g. "Saturn", "Mercury"), \
active_antardasha (sub-period lord), transit_highlights (array of planet/longitude \
events from ephemeris_daily — empty if table not populated), signal_activations \
(bodha signals lit by this dasha×transit state — empty if bodha tables empty), \
source_citation (always "PyJHora/SwissEph DE441 + Brahma-L1").

When to prefer: Use timeline_query to understand the dasha context for any date \
or date range — e.g. "what MD/AD was active during event X?", "show the dasha \
sequence for 2010–2030". Pair with holistic_bundle (B.11 floor) for whole-chart \
synthesis. For a single date's dasha, use date_range {start: DATE, end: DATE} \
with limit=1. For multi-year dasha arc analysis, use a wider range with limit \
up to 36600 (daily granularity).

Provenance: Every row carries source_citation = "PyJHora/SwissEph DE441 + Brahma-L1". \
Response includes provenance_envelope with asset, unit, layer, depends, and range.`

// ── Registration ──────────────────────────────────────────────────────────────

/**
 * Register the timeline_query tool on the MCP server.
 *
 * timeline_query delegates to callPlatformPrimitive('kala_timeline', params)
 * which routes through the registry surface. The caller must supply chart_id —
 * no native default is applied.
 *
 * @param server       The McpServer instance to register the tool on.
 * @param getPrincipal Getter for the resolved principal from Bearer key validation.
 */
export function registerKalaTimeline(server: McpServer, getPrincipal: () => Principal): void {
  server.registerTool(
    'timeline_query',
    {
      description: KALA_TIMELINE_DESCRIPTION,
      inputSchema: KalaTimelineSchema,
    },
    async (params: KalaTimelineParams) => {
      const { date_range, limit } = params
      if (new Date(date_range.start) > new Date(date_range.end)) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                { error: 'date_range.start must be ≤ date_range.end', tool: 'timeline_query' },
                null,
                2,
              ),
            },
          ],
          isError: true,
        }
      }

      try {
        const { status, envelope } = await callPlatformPrimitive(
          'kala_timeline',
          { chart_id: params.chart_id, date_range, limit },
          getPrincipal(),
        )

        if (status !== 200 || !envelope.ok) {
          return {
            content: [
              {
                type: 'text' as const,
                text: JSON.stringify(
                  { error: (envelope as McpEnvelopeError).error?.message ?? status, tool: 'timeline_query', asset: 'KA-3-1' },
                  null,
                  2,
                ),
              },
            ],
            isError: true,
          }
        }

        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(envelope.result, null, 2),
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
                { error: message, tool: 'timeline_query', asset: 'KA-3-1' },
                null,
                2,
              ),
            },
          ],
          isError: true,
        }
      }
    },
  )
}
