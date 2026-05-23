/**
 * chart_summary.ts — MCP Tier 1 super-endpoint: canonical wide-by-default fact bundle.
 *
 * Returns a canonical ~50-fact bundle for a chart in a single call, spanning
 * birth metadata, planetary positions, house assignments, yogas, arudha lagna,
 * current dasha state, and sensitive points.
 *
 * Internally:
 *   - Calls callPlatformPrimitive('query_chart_facts', {categories: [...], batched: true})
 *     for non-divisional categories (birth_metadata, yoga, arudha, vimshottari_dasha,
 *     sensitive_point) — one round-trip.
 *   - For divisional-specific categories (planet, house), calls once per divisional_chart
 *     with the divisional_chart filter (Phase 4a), then combines results.
 *
 * Return shape:
 *   {
 *     ok: true,
 *     chart_id: string,
 *     divisional_charts: string[],
 *     categories_fetched: string[],
 *     total_rows: number,
 *     rows_by_category: {
 *       birth_metadata: row[],
 *       planet: row[],     // all divisionals combined
 *       house: row[],
 *       yoga: row[],
 *       arudha: row[],
 *       vimshottari_dasha: row[],
 *       sensitive_point: row[],
 *       ...additional included categories
 *     }
 *   }
 *
 * MCPT v3.2 Phase 4c
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'
import { okResult, errorResult } from './_envelope.js'

// ── Constants ─────────────────────────────────────────────────────────────────

/** Default divisional charts included in the canonical bundle. */
const DEFAULT_DIVISIONAL_CHARTS = ['D1', 'D9', 'D10'] as const

/**
 * Categories that are divisional-chart-sensitive (planet positions, house
 * assignments change per divisional). These are fetched per divisional_chart.
 */
const DIVISIONAL_SENSITIVE_CATEGORIES = ['planet', 'house'] as const

/**
 * Categories in the canonical bundle that are NOT divisional-chart-sensitive.
 * Fetched in one batched call.
 */
const BULK_CATEGORIES = [
  'birth_metadata',
  'yoga',
  'arudha',
  'dasha_vimshottari',
  'sensitive_point',
] as const

/** All categories in the canonical default bundle. */
const DEFAULT_CATEGORIES = [
  ...BULK_CATEGORIES,
  ...DIVISIONAL_SENSITIVE_CATEGORIES,
] as const

// ── Description ───────────────────────────────────────────────────────────────

export const CHART_SUMMARY_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns a canonical wide-by-default fact bundle for a chart in a single call, ' +
    'spanning birth metadata, planetary positions, house assignments, yogas, arudha lagna, ' +
    'current dasha state, and sensitive points across D1/D9/D10 by default.',
  coverageHint: 'Canonical ~50+ rows in ≤2 round-trips; replaces 5+ separate query_chart_facts calls.',
  whenToPrefer:
    'Use as the FIRST CALL for any chart interpretation task. ' +
    'Replaces 5+ separate query_chart_facts calls. ' +
    'Use include_categories / exclude_categories to narrow the bundle. ' +
    'Surgical follow-ups via query_chart_facts for edge cases.',
})

// ── Input schema ──────────────────────────────────────────────────────────────

const ChartSummaryInputSchema = z.object({
  chart_id: z.string().optional().describe(
    'Chart identifier. Defaults to the native (Abhisek Mohanty). ' +
    'Omit for the singleton MARSYS-JIS chart.'
  ),
  divisional_charts: z.array(z.string()).optional().default(['D1', 'D9', 'D10']).describe(
    'Divisional charts to include for planet + house categories. ' +
    'Defaults to ["D1", "D9", "D10"]. Example: ["D1", "D9", "D10", "D12"].'
  ),
  include_categories: z.array(z.string()).optional().describe(
    'If set, only these categories are fetched (plus birth_metadata which is always included). ' +
    'Useful to narrow a wide bundle to specific layers.'
  ),
  exclude_categories: z.array(z.string()).optional().describe(
    'If set, skip these categories from the canonical default list. ' +
    'Example: ["sensitive_point"] to omit sensitive points.'
  ),
})

type ChartSummaryInput = z.infer<typeof ChartSummaryInputSchema>

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerChartSummaryTool(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'chart_summary',

    CHART_SUMMARY_DESCRIPTION,

    ChartSummaryInputSchema.shape,

    async (input: ChartSummaryInput) => {
      const principal = getPrincipal()

      // ── Resolve categories to fetch ─────────────────────────────────────────

      const divisionalCharts: string[] =
        (input.divisional_charts && input.divisional_charts.length > 0)
          ? input.divisional_charts
          : [...DEFAULT_DIVISIONAL_CHARTS]

      // Determine base category list
      let baseCategories: string[]
      if (input.include_categories && input.include_categories.length > 0) {
        // include_categories overrides the default list; always ensure birth_metadata
        baseCategories = Array.from(
          new Set(['birth_metadata', ...input.include_categories])
        )
      } else {
        baseCategories = [...DEFAULT_CATEGORIES]
        // Apply exclude_categories filter
        if (input.exclude_categories && input.exclude_categories.length > 0) {
          const excluded = new Set(input.exclude_categories)
          baseCategories = baseCategories.filter(c => !excluded.has(c))
        }
      }

      // Split into bulk (non-divisional) and divisional-sensitive categories
      const divisionalSensitiveSet = new Set<string>(DIVISIONAL_SENSITIVE_CATEGORIES)
      const bulkCats = baseCategories.filter(c => !divisionalSensitiveSet.has(c))
      const divCats = baseCategories.filter(c => divisionalSensitiveSet.has(c))

      // rows_by_category accumulator
      const rowsByCategory: Record<string, unknown[]> = {}

      // ── Round-trip 1: bulk non-divisional categories ────────────────────────

      if (bulkCats.length > 0) {
        const bulkParams: Record<string, unknown> = {
          category: bulkCats,
          batched: true,
          limit: 200,
        }
        if (input.chart_id) bulkParams['chart_id'] = input.chart_id

        const { status: bulkStatus, envelope: bulkEnvelope } =
          await callPlatformPrimitive('query_chart_facts', bulkParams, principal)

        if (!bulkEnvelope.ok || bulkStatus >= 400) {
          return errorResult(bulkEnvelope)
        }

        // Merge rows_by_category from bulk response
        const bulkResult = bulkEnvelope.result as Record<string, unknown> | undefined
        if (bulkResult) {
          const rowsByCat = bulkResult['rows_by_category'] as Record<string, unknown[]> | undefined
          if (rowsByCat) {
            for (const [cat, rows] of Object.entries(rowsByCat)) {
              if (!rowsByCategory[cat]) rowsByCategory[cat] = []
              rowsByCategory[cat].push(...rows)
            }
          }
          // Also handle flat rows array (single-category fallback)
          const flatRows = bulkResult['rows'] as unknown[] | undefined
          if (flatRows && flatRows.length > 0) {
            for (const row of flatRows) {
              const r = row as Record<string, unknown>
              const cat = (r['category'] as string) ?? 'unknown'
              if (!rowsByCategory[cat]) rowsByCategory[cat] = []
              rowsByCategory[cat].push(r)
            }
          }
        }
      }

      // ── Round-trip 2: divisional-sensitive categories (planet, house) ───────
      //
      // One call per divisional chart, filtered by divisional_chart param (Phase 4a).
      // Results from all divisional charts are combined into a single array per
      // category (so rowsByCategory['planet'] contains rows from D1 + D9 + D10).

      if (divCats.length > 0) {
        for (const divChart of divisionalCharts) {
          const divParams: Record<string, unknown> = {
            category: divCats,
            batched: true,
            divisional_chart: divChart,
            limit: 200,
          }
          if (input.chart_id) divParams['chart_id'] = input.chart_id

          const { status: divStatus, envelope: divEnvelope } =
            await callPlatformPrimitive('query_chart_facts', divParams, principal)

          if (!divEnvelope.ok || divStatus >= 400) {
            return errorResult(divEnvelope)
          }

          const divResult = divEnvelope.result as Record<string, unknown> | undefined
          if (divResult) {
            const rowsByCat = divResult['rows_by_category'] as Record<string, unknown[]> | undefined
            if (rowsByCat) {
              for (const [cat, rows] of Object.entries(rowsByCat)) {
                if (!rowsByCategory[cat]) rowsByCategory[cat] = []
                rowsByCategory[cat].push(...rows)
              }
            }
            const flatRows = divResult['rows'] as unknown[] | undefined
            if (flatRows && flatRows.length > 0) {
              for (const row of flatRows) {
                const r = row as Record<string, unknown>
                const cat = (r['category'] as string) ?? 'unknown'
                if (!rowsByCategory[cat]) rowsByCategory[cat] = []
                rowsByCategory[cat].push(r)
              }
            }
          }
        }
      }

      // ── Compute totals ──────────────────────────────────────────────────────

      const totalRows = Object.values(rowsByCategory).reduce(
        (sum, rows) => sum + rows.length,
        0
      )

      const categoriesFetched = [...bulkCats, ...divCats]

      return okResult({
        ok: true,
        chart_id: input.chart_id ?? 'native',
        divisional_charts: divisionalCharts,
        categories_fetched: categoriesFetched,
        total_rows: totalRows,
        rows_by_category: rowsByCategory,
      })
    }
  )
}
