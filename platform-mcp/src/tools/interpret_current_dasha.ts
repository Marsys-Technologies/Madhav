/**
 * interpret_current_dasha.ts — MCP Tier 3 composition recipe: dasha + yoga synthesis.
 *
 * What it does: Calls query_dasha_periods and query_chart_facts(yoga) in parallel,
 * then aggregates the results to show which natal yogas are activated by the current
 * Mahadasha (MD) or Antardasha (AD). No LLM is invoked — pure data aggregation.
 *
 * Algorithm:
 *   1. query_dasha_periods({ active_only: true }) → extract MD/AD/PD.
 *   2. query_chart_facts({ categories: ["yoga"], limit: 100 }) → natal yoga rows.
 *   3. For each yoga row, check if yoga's planet/lord field matches current MD or AD.
 *      Set is_activated_by_dasha: true if matched.
 *
 * When to prefer: Use when you need a quick cross-reference of active dashas against
 * natal yoga activations. For deeper MSR synthesis, call holistic_bundle.
 *
 * Session: TR-P9-S2
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const INTERPRET_CURRENT_DASHA_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Aggregates current dasha context (MD/AD/PD) with natal yoga data to identify ' +
    'which yogas are activated by the active dasha period. Calls query_dasha_periods + ' +
    'query_chart_facts(yoga) in parallel; no LLM invoked. Returns dasha_context, relevant_yogas, ' +
    'and a synthesis note. For deeper interpretation, follow up with holistic_bundle.',
  whenToPrefer:
    'Use when you need a quick overlay of "which natal yogas are lit up by the current MD/AD?" ' +
    'without full synthesis overhead. Prefer holistic_bundle when you also need MSR signal ' +
    'corpus interpretation or multi-layer chart synthesis.',
})

const InterpretCurrentDashaInputSchema = z.object({
  date: z.string().optional().describe(
    'ISO date for evaluation (e.g. "2026-05-25"). Defaults to today if omitted.'
  ),
  subset_size: z.number().int().min(10).max(100).optional().default(30).describe(
    'Max yoga rows to evaluate for dasha activation (10–100). Defaults to 30.'
  ),
})

type InterpretCurrentDashaInput = z.infer<typeof InterpretCurrentDashaInputSchema>

// ── Envelope unwrap helper ────────────────────────────────────────────────────

function unwrapEnvelope(envelope: unknown): unknown {
  const env = envelope as Record<string, unknown> | null | undefined
  if (!env) return null
  const results = env['results'] as Array<{ content: unknown }> | undefined
  if (results && results.length > 0) {
    const raw = results[0]!.content
    return typeof raw === 'string' ? JSON.parse(raw) : raw
  }
  return env['result'] ?? null
}

// ── Dasha context extraction ──────────────────────────────────────────────────

interface DashaContext {
  md: string | null
  ad: string | null
  pd: string | null
  md_start: string | null
  md_end: string | null
}

function extractDashaContext(data: unknown): DashaContext {
  const fallback: DashaContext = { md: null, ad: null, pd: null, md_start: null, md_end: null }
  if (!data || typeof data !== 'object') return fallback

  const obj = data as Record<string, unknown>

  // Try periods array first
  const periods = obj['periods'] as Array<Record<string, unknown>> | undefined
  if (Array.isArray(periods) && periods.length > 0) {
    const period = periods[0]!
    return {
      md: (period['mahadasha'] as string | null) ?? (period['md'] as string | null) ?? null,
      ad: (period['antardasha'] as string | null) ?? (period['ad'] as string | null) ?? null,
      pd: (period['pratyantar'] as string | null) ?? (period['pd'] as string | null) ?? null,
      md_start: (period['start'] as string | null) ?? (period['md_start'] as string | null) ?? null,
      md_end: (period['end'] as string | null) ?? (period['md_end'] as string | null) ?? null,
    }
  }

  // Try flat object
  return {
    md: (obj['mahadasha'] as string | null) ?? (obj['md'] as string | null) ?? null,
    ad: (obj['antardasha'] as string | null) ?? (obj['ad'] as string | null) ?? null,
    pd: (obj['pratyantar'] as string | null) ?? (obj['pd'] as string | null) ?? null,
    md_start: (obj['start'] as string | null) ?? (obj['md_start'] as string | null) ?? null,
    md_end: (obj['end'] as string | null) ?? (obj['md_end'] as string | null) ?? null,
  }
}

// ── Yoga row extraction ───────────────────────────────────────────────────────

interface YogaRow {
  yoga_name: string
  planet: string | null
}

function extractYogaRows(data: unknown, limit: number): YogaRow[] {
  if (!data || typeof data !== 'object') return []
  const obj = data as Record<string, unknown>

  // Batched response: rows_by_category.yoga
  const rowsByCat = obj['rows_by_category'] as Record<string, unknown[]> | undefined
  if (rowsByCat && Array.isArray(rowsByCat['yoga'])) {
    return rowsByCat['yoga'].slice(0, limit).map(r => rowToYoga(r))
  }

  // Single rows array
  const rows = obj['rows'] as unknown[] | undefined
  if (Array.isArray(rows)) {
    return rows.slice(0, limit).map(r => rowToYoga(r))
  }

  return []
}

function rowToYoga(r: unknown): YogaRow {
  if (!r || typeof r !== 'object') return { yoga_name: 'unknown', planet: null }
  const row = r as Record<string, unknown>
  const name =
    (row['yoga_name'] as string | undefined) ??
    (row['value_text'] as string | undefined) ??
    (row['fact_value'] as string | undefined) ??
    'unknown'
  const planet =
    (row['planet'] as string | undefined) ??
    (row['lord'] as string | undefined) ??
    (row['planet_lord'] as string | undefined) ??
    null
  return { yoga_name: name, planet }
}

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerInterpretCurrentDasha(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'interpret_current_dasha',
    INTERPRET_CURRENT_DASHA_DESCRIPTION,
    InterpretCurrentDashaInputSchema.shape,
    async (args: InterpretCurrentDashaInput) => {
      const principal = getPrincipal()
      const evaluationDate = args.date ?? new Date().toISOString().slice(0, 10)
      const subsetSize = args.subset_size ?? 30

      // ── Parallel fetch ────────────────────────────────────────────────────
      const [dashaResult, yogaResult] = await Promise.all([
        callPlatformPrimitive(
          'query_dasha_periods',
          { active_only: true },
          principal
        ),
        callPlatformPrimitive(
          'query_chart_facts',
          { categories: ['yoga'], limit: 100 },
          principal
        ),
      ])

      // ── Extract dasha context (graceful on error) ──────────────────────
      let dashaContext: DashaContext = { md: null, ad: null, pd: null, md_start: null, md_end: null }
      const dataSources: string[] = []

      if (dashaResult.envelope.ok && dashaResult.status < 400) {
        const raw = dashaResult.envelope as unknown as Record<string, unknown>
        const unwrapped = unwrapEnvelope(raw)
        dashaContext = extractDashaContext(unwrapped)
        dataSources.push('query_dasha_periods')
      }

      // ── Extract yoga rows ──────────────────────────────────────────────
      let relevantYogas: Array<{ yoga_name: string; is_activated_by_dasha: boolean }> = []

      if (yogaResult.envelope.ok && yogaResult.status < 400) {
        const raw = yogaResult.envelope as unknown as Record<string, unknown>
        const unwrapped = unwrapEnvelope(raw)
        const yogaRows = extractYogaRows(unwrapped, subsetSize)

        // Activation check: planet matches MD or AD (case-insensitive)
        const activeDashas = [dashaContext.md, dashaContext.ad]
          .filter(Boolean)
          .map(d => (d as string).toLowerCase())

        relevantYogas = yogaRows.map(row => ({
          yoga_name: row.yoga_name,
          is_activated_by_dasha:
            row.planet !== null &&
            activeDashas.includes(row.planet.toLowerCase()),
        }))

        dataSources.push('query_chart_facts:yoga')
      }

      return okResult({
        ok: true,
        evaluation_date: evaluationDate,
        dasha_context: dashaContext,
        relevant_yogas: relevantYogas,
        synthesis_note:
          'interpret_current_dasha aggregated dasha+yoga data. ' +
          'For deeper MSR synthesis, call holistic_bundle.',
        data_sources: dataSources,
      })
    }
  )
}
