/**
 * get_shadbala_full.ts — MCP Tier 3 surgical primitive: full Shadbala roll-up.
 *
 * What it does: Queries chart_facts for all shadbala component rows, groups them
 * into the six canonical Shadbala components per planet, sums each component, and
 * returns total virupa + rupa with sufficiency assessment against classical minimums.
 *
 * Six Shadbala components:
 *   1. Sthana Bala    — positional strength (uchcha, saptvarga, ojayugma, kendradi, drekkana)
 *   2. Dig Bala       — directional strength
 *   3. Kala Bala      — temporal strength (natonnata, paksha, tribhaga, varsha, masa, dina, hora, ayana, yuddha)
 *   4. Cheshta Bala   — motional strength
 *   5. Naisargika Bala — natural strength
 *   6. Drig Bala      — aspectual strength
 *
 * Classical minimum rupas (Parashari):
 *   Sun: 6.5, Moon: 6.0, Mars: 5.0, Mercury: 7.0, Jupiter: 6.5, Venus: 5.5, Saturn: 5.0
 *
 * When to prefer: Use for "Is Saturn shadbala-sufficient?" or "What is Jupiter's total Shadbala?"
 * Prefer query_chart_facts for raw shadbala rows without roll-up.
 * Prefer holistic_bundle for strength in interpretive context.
 *
 * Input shape hints:
 *   planets — optional array of planet names to filter. Omit for all 7 classical planets.
 *
 * Output shape preview:
 *   {ok, shadbala: {Planet: {sthana_bala, dig_bala, kala_bala, cheshta_bala, naisargika_bala,
 *    drig_bala, total_virupa, total_rupa, minimum_required_rupa, is_sufficient}},
 *    source_rows_used}
 *
 * TR-P6-S3: new MCP tool.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'

// ── Classical minimum rupas ───────────────────────────────────────────────────

export const MINIMUM_RUPAS: Record<string, number> = {
  Sun: 6.5,
  Moon: 6.0,
  Mars: 5.0,
  Mercury: 7.0,
  Jupiter: 6.5,
  Venus: 5.5,
  Saturn: 5.0,
}

const CLASSICAL_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'] as const
type ClassicalPlanet = typeof CLASSICAL_PLANETS[number]

// ── Component grouping via regex ──────────────────────────────────────────────

function classifyComponent(componentName: string): keyof ShadbalaComponents | null {
  if (/sthana|uchcha|saptvarga|ojayugma|kendradi|drekkana/i.test(componentName)) return 'sthana_bala'
  // Dig Bala: match "dig" as a standalone word segment (not inside "drig"/"drishti")
  if (/(?<![r])dig(?![r])/i.test(componentName)) return 'dig_bala'
  if (/kala|natonnata|paksha|tribhaga|varsha|masa|dina|(?<![d])hora(?![\w])|ayana|yuddha/i.test(componentName)) return 'kala_bala'
  if (/cheshta/i.test(componentName)) return 'cheshta_bala'
  if (/naisargika|sahaj/i.test(componentName)) return 'naisargika_bala'
  if (/drig|drishti/i.test(componentName)) return 'drig_bala'
  return null
}

interface ShadbalaComponents {
  sthana_bala: number
  dig_bala: number
  kala_bala: number
  cheshta_bala: number
  naisargika_bala: number
  drig_bala: number
}

// ── Zod schema ────────────────────────────────────────────────────────────────

const GetShadbalaFullInputSchema = z.object({
  planets: z.array(z.enum(CLASSICAL_PLANETS)).optional().describe(
    'Optional filter: array of planet names to include in the output. ' +
    'Omit to return all 7 classical planets. ' +
    'Valid values: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn.'
  ),
})

type GetShadbalaFullInput = z.infer<typeof GetShadbalaFullInputSchema>

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerGetShadbalaFull(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'get_shadbala_full',
    'What it does: Fetches all shadbala component rows from chart_facts and rolls them up into ' +
    'the six canonical Shadbala groups (Sthana, Dig, Kala, Cheshta, Naisargika, Drig Bala) per planet. ' +
    'Returns total virupa, total rupa (virupa / 60), classical minimum required rupa, and is_sufficient flag. ' +
    'Classical minimums: Sun 6.5, Moon 6.0, Mars 5.0, Mercury 7.0, Jupiter 6.5, Venus 5.5, Saturn 5.0 rupas. ' +
    'When to prefer: Use for "Is Saturn shadbala-sufficient?" or full shadbala breakdown. ' +
    'Prefer query_chart_facts for raw rows. Prefer holistic_bundle for interpretive context.',
    GetShadbalaFullInputSchema.shape,
    async (args: GetShadbalaFullInput) => {
      const principal = getPrincipal()

      // ── Step 1: Fetch all shadbala rows ──────────────────────────────────────
      const { status, envelope } = await callPlatformPrimitive(
        'query_chart_facts',
        { categories: ['shadbala'], limit: 200 },
        principal
      )

      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }

      // ── Step 2: Extract rows from response envelope ───────────────────────────
      const resultObj = (envelope as Record<string, unknown>)['result'] as Record<string, unknown> | undefined

      let allRows: unknown[] = []

      if (resultObj) {
        // Try ToolBundle results[0].content wrapping
        const bundleResults = resultObj['results'] as Array<{ content: string }> | undefined
        if (bundleResults && bundleResults.length > 0 && typeof bundleResults[0].content === 'string') {
          try {
            const parsed = JSON.parse(bundleResults[0].content) as Record<string, unknown>
            if (parsed['rows_by_category'] && typeof parsed['rows_by_category'] === 'object') {
              const byCategory = parsed['rows_by_category'] as Record<string, unknown[]>
              allRows = byCategory['shadbala'] ?? []
            } else if (Array.isArray(parsed['rows'])) {
              allRows = parsed['rows']
            } else if (Array.isArray(parsed)) {
              allRows = parsed
            }
          } catch { /* ignore parse errors */ }
        }
        // Fallback: direct rows_by_category
        if (allRows.length === 0 && resultObj['rows_by_category']) {
          const byCategory = resultObj['rows_by_category'] as Record<string, unknown[]>
          allRows = byCategory['shadbala'] ?? []
        }
        // Fallback: direct rows array
        if (allRows.length === 0 && Array.isArray(resultObj['rows'])) {
          allRows = resultObj['rows'] as unknown[]
        }
      }

      const sourceRowsUsed = allRows.length

      // ── Step 3: Group rows by planet, classify components ────────────────────
      const planetMap: Record<string, ShadbalaComponents> = {}

      for (const row of allRows) {
        const r = row as Record<string, unknown>
        const planet = r['planet'] as string | undefined
        const componentName = (r['component_name'] ?? r['sub_category'] ?? r['label'] ?? '') as string
        const valueNum = typeof r['value_num'] === 'number' ? r['value_num'] : 0

        if (!planet) continue

        // Apply planet filter if specified
        if (args.planets && args.planets.length > 0) {
          if (!(args.planets as string[]).includes(planet)) continue
        } else {
          // Default: only classical planets
          if (!(CLASSICAL_PLANETS as readonly string[]).includes(planet)) continue
        }

        if (!planetMap[planet]) {
          planetMap[planet] = {
            sthana_bala: 0,
            dig_bala: 0,
            kala_bala: 0,
            cheshta_bala: 0,
            naisargika_bala: 0,
            drig_bala: 0,
          }
        }

        const group = classifyComponent(componentName)
        if (group) {
          planetMap[planet][group] += valueNum
        }
      }

      // ── Step 4: Build output with rupa + sufficiency assessment ──────────────
      type ShadbalaEntry = ShadbalaComponents & {
        total_virupa: number
        total_rupa: number
        minimum_required_rupa: number
        is_sufficient: boolean
      }

      const shadbala: Record<string, ShadbalaEntry> = {}

      const planetsToReport = args.planets && args.planets.length > 0
        ? args.planets
        : (CLASSICAL_PLANETS as readonly ClassicalPlanet[])

      for (const planet of planetsToReport) {
        const components = planetMap[planet] ?? {
          sthana_bala: 0,
          dig_bala: 0,
          kala_bala: 0,
          cheshta_bala: 0,
          naisargika_bala: 0,
          drig_bala: 0,
        }

        const totalVirupa =
          components.sthana_bala +
          components.dig_bala +
          components.kala_bala +
          components.cheshta_bala +
          components.naisargika_bala +
          components.drig_bala

        const totalRupa = totalVirupa / 60
        const minimumRupa = MINIMUM_RUPAS[planet] ?? 5.0
        const isSufficient = totalRupa >= minimumRupa

        shadbala[planet] = {
          ...components,
          total_virupa: totalVirupa,
          total_rupa: totalRupa,
          minimum_required_rupa: minimumRupa,
          is_sufficient: isSufficient,
        }
      }

      return okResult({
        ok: true,
        shadbala,
        source_rows_used: sourceRowsUsed,
      })
    }
  )
}
