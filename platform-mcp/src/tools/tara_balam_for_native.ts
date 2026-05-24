/**
 * tara_balam_for_native.ts — MCP Tier 3 surgical primitive: Tara Bala for the native.
 *
 * What it does: Computes the Tara Bala (Star Strength) score for the native
 * (Abhisek Mohanty, birth nakshatra: Purva Bhadrapada, nakshatra_id=25) on a
 * given date. Tara Bala is a classical Vedic muhurta technique assessing the
 * Moon's daily nakshatra relative to the native's birth nakshatra using the
 * Nava Tara Chakra (9-tara cycle).
 *
 * Classical source: Muhurta Chintamani §Tara Bala; Brihat Parashara Hora
 * Shastra §Tara; Jataka Parijata §Tara Bala computation.
 *
 * Tara positions (1-indexed from birth nakshatra):
 *   1=Janma (neutral 0.50), 2=Sampat (auspicious 0.90), 3=Vipat (inauspicious 0.00),
 *   4=Kshema (0.85), 5=Pratyari (0.10), 6=Sadhaka (0.95), 7=Vadha (0.00),
 *   8=Mitra (0.80), 9=Ati-Mitra (1.00). Cycle repeats for positions 10–27 with
 *   0.80 (secondary) and 0.60 (tertiary) attenuation.
 *
 * When to prefer: Use for "Is today a good day for the native by Tara Bala?" or
 * muhurta screening on a specific date. Prefer muhurta_finder for finding the best
 * window over a range. Prefer query_panchanga for the full daily panchang snapshot.
 *
 * Input shape hints:
 *   date — required ISO date (YYYY-MM-DD).
 *   tier — optional audience tier hint.
 *
 * Output shape preview: {ok, result: {tara_count, tara_name, score, interpretation,
 *   moon_nakshatra, date}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: tara_balam_for_native({date: "2026-05-25"}) →
 *   {ok: true, result: {tara_count: 6, tara_name: "Sadhaka", score: 0.95,
 *   interpretation: "Auspicious — achievement tara; favourable for purposeful action.",
 *   moon_nakshatra: "Purva Phalguni"}}
 *
 * TR-P4-S2: new MCP wrapper.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

export const TARA_BALAM_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Computes the Tara Bala (Star Strength) score for the native (birth nakshatra: ' +
    'Purva Bhadrapada, id=25) on a given date. Uses the Nava Tara Chakra — the 9-tara cycle ' +
    '(Janma→Ati-Mitra) counted from the native\'s birth nakshatra to the Moon\'s daily nakshatra. ' +
    'Returns tara_count (1–27), tara_name, score (0–1), and an interpretation string.',
  whenToPrefer:
    'Use for "Is today auspicious by Tara Bala?" or muhurta screening for a single date. ' +
    'Prefer muhurta_finder to search across a date range for the best window. ' +
    'Prefer query_panchanga for the full panchang snapshot including all five limbs. ' +
    'Source: MC §Tara Bala; BPHS §Tara.',
})

const TaraBalamInputSchema = z.object({
  date: z.string().describe(
    'ISO date (YYYY-MM-DD) to compute Tara Bala for.'
  ),
  tier: z.string().optional().default('super_admin'),
})

type TaraBalamInput = z.infer<typeof TaraBalamInputSchema>

export function registerTaraBalamForNative(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'tara_balam_for_native',
    TARA_BALAM_DESCRIPTION,
    TaraBalamInputSchema.shape,
    async (args: TaraBalamInput) => {
      const principal = getPrincipal()

      const { status, envelope } = await callPlatformPrimitive(
        'query_tara_balam',
        {
          date: args.date,
        },
        principal
      )

      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }
      return okResult(envelope)
    }
  )
}
