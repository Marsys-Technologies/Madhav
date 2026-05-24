/**
 * get_planet_avastha.ts — MCP Tier 3 surgical primitive: Avasthas (planetary states).
 *
 * What it does: Returns the avastha (planetary state/condition) for a specific planet
 * from the chart_facts table, plus a classical meaning string. Avasthas encode the
 * experiential state of a planet's significations — whether they are fulfilled,
 * frustrated, delayed, or volatile.
 *
 * Six avasthas (Parashari):
 *   Lajjita (Ashamed), Garvita (Proud), Kshudita (Hungry), Trushita (Thirsty),
 *   Mudita (Delighted), Kshobhita (Agitated).
 *
 * Fallback chain:
 *   1. chart_facts category "avastha" — direct row lookup.
 *   2. chart_facts category "dignity_scores" — infer avastha from dignity sign.
 *   3. Default to "Mudita" (neutral-positive) with source "default_fallback".
 *
 * When to prefer: Use for "What is Jupiter's avastha?" or "Is Venus agitated?"
 * Prefer holistic_bundle when interpretation in context is needed alongside the fact.
 *
 * Input shape hints:
 *   planet — one of the nine grahas (excluding outer nodes: Rahu/Ketu supported
 *     via chart_facts lookup but excluded from dignity fallback).
 *   use_natal — boolean (default true). Reserved for future transit-avastha mode.
 *
 * Output shape preview:
 *   {ok, planet, avastha, avastha_meaning, is_natal, source, trace_id}
 *
 * TR-P6-S3: new MCP tool.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'

// ── Avastha meaning map ───────────────────────────────────────────────────────

export const AVASTHA_MEANINGS: Record<string, string> = {
  Lajjita: 'Ashamed — planet is suppressed; significations delayed or frustrated',
  Garvita: 'Proud — planet is strong; significations fulfilled',
  Kshudita: 'Hungry — planet lacks support; results delayed',
  Trushita: 'Thirsty — planet craves what it lacks; creates longing',
  Mudita: 'Delighted — planet is comfortable; benevolent results',
  Kshobhita: 'Agitated — planet is disturbed; volatile results',
}

const VALID_AVASTHAS = Object.keys(AVASTHA_MEANINGS)

// ── Dignity → avastha inference map ──────────────────────────────────────────
// When chart_facts has no avastha row but does have dignity_scores,
// map dignity classification to the closest classical avastha.

const DIGNITY_TO_AVASTHA: Record<string, string> = {
  exalted: 'Garvita',
  own_sign: 'Mudita',
  great_friend: 'Mudita',
  friend: 'Mudita',
  neutral: 'Mudita',
  enemy: 'Kshudita',
  great_enemy: 'Kshudita',
  debilitated: 'Lajjita',
}

// ── Zod schema ────────────────────────────────────────────────────────────────

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'] as const

const GetPlanetAvasthaInputSchema = z.object({
  planet: z.enum(PLANETS).describe(
    'The graha to look up. One of: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.'
  ),
  use_natal: z.boolean().optional().default(true).describe(
    'When true (default), returns natal chart avastha. ' +
    'Reserved for future transit-avastha mode; currently only natal is supported.'
  ),
})

type GetPlanetAvasthaInput = z.infer<typeof GetPlanetAvasthaInputSchema>

// ── Helper: unwrap envelope results[0].content ────────────────────────────────

function unwrapRows(envelope: Record<string, unknown>): unknown[] {
  const raw = (envelope?.['results'] as Array<{ content: string }> | undefined)?.[0]?.content
  const data: unknown = typeof raw === 'string' ? JSON.parse(raw) : raw
  if (data && typeof data === 'object' && Array.isArray((data as Record<string, unknown>)['rows'])) {
    return (data as Record<string, unknown>)['rows'] as unknown[]
  }
  // Fallback: data IS the rows array
  if (Array.isArray(data)) return data
  return []
}

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerGetPlanetAvastha(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'get_planet_avastha',
    'What it does: Returns the avastha (planetary state) for a specific graha from the chart_facts ' +
    'table. Avasthas classify a planet\'s experiential condition: Lajjita (Ashamed/suppressed), ' +
    'Garvita (Proud/strong), Kshudita (Hungry/lacking), Trushita (Thirsty/craving), ' +
    'Mudita (Delighted/comfortable), Kshobhita (Agitated/disturbed). ' +
    'Falls back to dignity-derived avastha if no direct avastha row exists. ' +
    'When to prefer: Use for "What is Jupiter\'s avastha?" Prefer holistic_bundle for interpretation in context.',
    GetPlanetAvasthaInputSchema.shape,
    async (args: GetPlanetAvasthaInput) => {
      const principal = getPrincipal()

      // ── Step 1: Query chart_facts for avastha category ───────────────────────
      const avasthaResult = await callPlatformPrimitive(
        'query_chart_facts',
        { categories: ['avastha'], limit: 100 },
        principal
      )

      if (!avasthaResult.envelope.ok || avasthaResult.status >= 400) {
        return errorResult(avasthaResult.envelope)
      }

      // Extract rows from the response envelope
      const avasthaEnvelope = (avasthaResult.envelope as Record<string, unknown>)['result'] as Record<string, unknown> | undefined

      let avasthaRows: unknown[] = []
      if (avasthaEnvelope) {
        // Try ToolBundle results[0].content wrapping first
        const bundleResults = avasthaEnvelope['results'] as Array<{ content: string }> | undefined
        if (bundleResults && bundleResults.length > 0 && typeof bundleResults[0].content === 'string') {
          try {
            const parsed = JSON.parse(bundleResults[0].content) as Record<string, unknown>
            // Batched response: rows_by_category.avastha
            if (parsed['rows_by_category'] && typeof parsed['rows_by_category'] === 'object') {
              const byCategory = parsed['rows_by_category'] as Record<string, unknown[]>
              avasthaRows = byCategory['avastha'] ?? []
            } else if (Array.isArray(parsed['rows'])) {
              avasthaRows = parsed['rows']
            } else if (Array.isArray(parsed)) {
              avasthaRows = parsed
            }
          } catch { /* ignore parse errors */ }
        }
        // Fallback: direct rows_by_category on the envelope result
        if (avasthaRows.length === 0 && avasthaEnvelope['rows_by_category']) {
          const byCategory = avasthaEnvelope['rows_by_category'] as Record<string, unknown[]>
          avasthaRows = byCategory['avastha'] ?? []
        }
        // Fallback: direct rows array
        if (avasthaRows.length === 0 && Array.isArray(avasthaEnvelope['rows'])) {
          avasthaRows = avasthaEnvelope['rows'] as unknown[]
        }
      }

      // Find row matching the requested planet
      const planetRow = avasthaRows.find((row) => {
        const r = row as Record<string, unknown>
        return (
          typeof r['planet'] === 'string' &&
          r['planet'].toLowerCase() === args.planet.toLowerCase()
        )
      }) as Record<string, unknown> | undefined

      if (planetRow) {
        // Extract avastha value from the row
        const rawAvastha =
          (planetRow['value_text'] as string | undefined) ??
          (planetRow['avastha'] as string | undefined) ??
          ''

        // Normalise to capitalised form matching AVASTHA_MEANINGS keys
        const matched = VALID_AVASTHAS.find(
          (a) => a.toLowerCase() === rawAvastha.toLowerCase()
        )
        const avastha = matched ?? rawAvastha

        return okResult({
          ok: true,
          planet: args.planet,
          avastha,
          avastha_meaning: AVASTHA_MEANINGS[avastha] ?? `Unknown avastha: ${avastha}`,
          is_natal: args.use_natal ?? true,
          source: 'chart_facts' as const,
        })
      }

      // ── Step 2: Fallback — try dignity_scores for inference ──────────────────
      const dignityResult = await callPlatformPrimitive(
        'query_chart_facts',
        { categories: ['dignity_scores'], limit: 50 },
        principal
      )

      if (dignityResult.envelope.ok && dignityResult.status < 400) {
        const dignityEnvelope = (dignityResult.envelope as Record<string, unknown>)['result'] as Record<string, unknown> | undefined
        let dignityRows: unknown[] = []

        if (dignityEnvelope) {
          const bundleResults = dignityEnvelope['results'] as Array<{ content: string }> | undefined
          if (bundleResults && bundleResults.length > 0 && typeof bundleResults[0].content === 'string') {
            try {
              const parsed = JSON.parse(bundleResults[0].content) as Record<string, unknown>
              if (parsed['rows_by_category'] && typeof parsed['rows_by_category'] === 'object') {
                const byCategory = parsed['rows_by_category'] as Record<string, unknown[]>
                dignityRows = byCategory['dignity_scores'] ?? []
              } else if (Array.isArray(parsed['rows'])) {
                dignityRows = parsed['rows']
              }
            } catch { /* ignore */ }
          }
          if (dignityRows.length === 0 && dignityEnvelope['rows_by_category']) {
            const byCategory = dignityEnvelope['rows_by_category'] as Record<string, unknown[]>
            dignityRows = byCategory['dignity_scores'] ?? []
          }
          if (dignityRows.length === 0 && Array.isArray(dignityEnvelope['rows'])) {
            dignityRows = dignityEnvelope['rows'] as unknown[]
          }
        }

        const dignityRow = dignityRows.find((row) => {
          const r = row as Record<string, unknown>
          return (
            typeof r['planet'] === 'string' &&
            r['planet'].toLowerCase() === args.planet.toLowerCase()
          )
        }) as Record<string, unknown> | undefined

        if (dignityRow) {
          const dignityClass =
            (dignityRow['value_text'] as string | undefined) ??
            (dignityRow['dignity'] as string | undefined) ??
            ''
          const inferredAvastha = DIGNITY_TO_AVASTHA[dignityClass.toLowerCase()] ?? 'Mudita'

          return okResult({
            ok: true,
            planet: args.planet,
            avastha: inferredAvastha,
            avastha_meaning: AVASTHA_MEANINGS[inferredAvastha]!,
            is_natal: args.use_natal ?? true,
            source: 'computed' as const,
          })
        }
      }

      // ── Step 3: Default fallback ──────────────────────────────────────────────
      return okResult({
        ok: true,
        planet: args.planet,
        avastha: 'Mudita',
        avastha_meaning: AVASTHA_MEANINGS['Mudita']!,
        is_natal: args.use_natal ?? true,
        source: 'default_fallback' as const,
      })
    }
  )
}
