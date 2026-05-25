/**
 * query_jaimini_drishti.ts — MCP Tier 3 surgical primitive: Jaimini drishti analysis.
 *
 * What it does: Invokes the sidecar POST /jaimini_drishti endpoint to compute
 * sign-to-sign special aspects per the Jaimini system — movable signs aspect fixed
 * signs (except adjacent), fixed signs aspect movable signs (except adjacent), dual
 * signs aspect each other (except adjacent). Distinct from Parashari graha drishti.
 *
 * STUB STATUS: Sidecar endpoint currently returns not_implemented. This wrapper
 * surfaces the tool in the MCP capability registry so the Jaimini drishti analysis
 * slot is reserved. Full implementation lands in M6+ when the Jaimini engine is built
 * in python-sidecar/routers/jaimini.py.
 *
 * When to prefer: Use query_jaimini_drishti for Jaimini-specific chart questions about
 * sign-to-sign aspect relationships, Chara Karakas, Arudha Padas, or Pada Lagna.
 * Do NOT use for Parashari graha drishti — use query_chart_facts or holistic_bundle
 * for those. Note: currently stub — returns not_implemented until M6+ Jaimini engine.
 *
 * Input shape hints:
 *   params — optional; arbitrary key-value params forwarded to the sidecar
 *             (schema TBD at implementation time).
 *
 * Output shape preview: {ok, result: {...}, trace_id, epistemics: {surgical: true}}.
 *   Until the sidecar implements the endpoint, ok will be false with a not_implemented error.
 *
 * Example: query_jaimini_drishti({}) →
 *   {ok: false, error: {class: "not_implemented", message: "Jaimini engine M6+ scope"}}
 *
 * Data source: python-sidecar POST /jaimini_drishti (stub until M6 Jaimini module)
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const QUERY_JAIMINI_DRISHTI_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Computes sign-to-sign special aspects (drishti) per the Jaimini system — ' +
    'movable signs aspect fixed (not adjacent), fixed signs aspect movable (not adjacent), ' +
    'dual signs aspect dual (not adjacent). Distinct from Parashari graha drishti. ' +
    'STUB — returns not_implemented until M6+ Jaimini engine is built.',
  coverageHint: 'Jaimini system: Chara Karakas, Arudha Padas, Pada Lagna, sign-to-sign aspects',
  whenToPrefer:
    'Use query_jaimini_drishti for Jaimini-specific chart questions about sign-to-sign aspects, ' +
    'Chara Karakas, Arudha Padas, or Pada Lagna. ' +
    'Do NOT use for Parashari graha drishti — use query_chart_facts or holistic_bundle instead. ' +
    'Currently stub — returns not_implemented until M6+ Jaimini engine lands.',
})

const QueryJaiminiDrishtiInputSchema = z.object({
  params: z.record(z.string(), z.unknown()).optional().describe(
    'Arbitrary parameters forwarded to the sidecar POST /jaimini_drishti endpoint. ' +
    'Schema is TBD at implementation time (M6+ scope). Pass an empty object or omit entirely ' +
    'to call with default parameters.'
  ),
})

type QueryJaiminiDrishtiInput = z.infer<typeof QueryJaiminiDrishtiInputSchema>

export function registerQueryJaiminiDrishti(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_jaimini_drishti',
    QUERY_JAIMINI_DRISHTI_DESCRIPTION,
    QueryJaiminiDrishtiInputSchema.shape,
    async (args: QueryJaiminiDrishtiInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_jaimini_drishti',
        {
          ...(args.params !== undefined ? { params: args.params } : {}),
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
