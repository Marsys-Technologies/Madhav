/**
 * chandra_balam_for_native.ts — MCP Tier 3 surgical primitive: Chandra Bala for the native.
 *
 * What it does: Computes the Chandra Bala (Moon Strength) score for the native
 * (Abhisek Mohanty, birth Moon sign: Pisces / Meena, moon_sign_id=12) on a given date.
 * Chandra Bala assesses the strength of the Moon on a given day by its position
 * relative to the native's natal Moon sign using the classical positional scoring:
 * positions 1,3,6,7,10,11 from birth Moon sign are auspicious; others are weak.
 *
 * Classical source: Muhurta Chintamani §Chandra Bala; DP "Chandra Bala" reference.
 *
 * Position scores from birth Moon sign:
 *   1=0.80 (same sign), 2=0.30, 3=0.90 (Kshema), 4=0.20, 5=0.30,
 *   6=0.90 (Sadhaka), 7=0.85 (Mitra), 8=0.10 (Vadha), 9=0.40,
 *   10=0.90 (Karma), 11=0.95 (Labha — most auspicious), 12=0.30 (loss).
 *
 * Note: Chandra Bala is distinct from Tara Bala — Tara Bala uses nakshatra-level
 * counting (27 nakshatras); Chandra Bala uses sign-level counting (12 signs).
 * Both are combined 60/40 in the native overlay for muhurta scoring.
 *
 * When to prefer: Use for "Is the Moon well-placed for the native today by Chandra
 * Bala?" Prefer muhurta_finder for window search with both tara + chandra overlay.
 * Prefer tara_balam_for_native for nakshatra-level Moon strength.
 * Prefer query_panchanga for the full daily panchang snapshot.
 *
 * Input shape hints:
 *   date — required ISO date (YYYY-MM-DD).
 *   tier — optional audience tier hint.
 *
 * Output shape preview: {ok, result: {chandra_bala_score, interpretation,
 *   moon_nakshatra, moon_sign, position_from_birth_moon, date},
 *   trace_id, epistemics: {surgical: true}}.
 *
 * Example: chandra_balam_for_native({date: "2026-05-25"}) →
 *   {ok: true, result: {chandra_bala_score: 0.90, interpretation: "Auspicious — 10th from birth Moon (Karma).",
 *   moon_nakshatra: "Purva Phalguni", moon_sign: "Leo", position_from_birth_moon: 6}}
 *
 * TR-P4-S2: new MCP wrapper.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

export const CHANDRA_BALAM_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Computes the Chandra Bala (Moon Strength) score for the native (birth Moon sign: ' +
    'Pisces/Meena, moon_sign_id=12) on a given date. Scores the Moon\'s sign position relative to ' +
    'the native\'s birth Moon sign (1–12). Positions 1,3,6,7,10,11 are auspicious; 4,8,12 are weak. ' +
    'Returns chandra_bala_score (0–1), interpretation, moon_nakshatra, and moon_sign.',
  whenToPrefer:
    'Use for "Is the Moon favourably placed for the native today?" (sign-level strength check). ' +
    'Prefer tara_balam_for_native for nakshatra-level Tara Bala (finer granularity). ' +
    'Prefer muhurta_finder for a full scored window search combining both tara + chandra overlay. ' +
    'Prefer query_panchanga for the complete daily panchang snapshot. ' +
    'Source: MC §Chandra Bala; DP "Chandra Bala" reference.',
})

const ChandraBalamInputSchema = z.object({
  date: z.string().describe(
    'ISO date (YYYY-MM-DD) to compute Chandra Bala for.'
  ),
  tier: z.string().optional().default('super_admin'),
})

type ChandraBalamInput = z.infer<typeof ChandraBalamInputSchema>

export function registerChandraBalamForNative(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'chandra_balam_for_native',
    CHANDRA_BALAM_DESCRIPTION,
    ChandraBalamInputSchema.shape,
    async (args: ChandraBalamInput) => {
      const principal = getPrincipal()

      const { status, envelope } = await callPlatformPrimitive(
        'query_chandra_balam',
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
