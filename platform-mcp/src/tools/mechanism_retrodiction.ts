/**
 * mechanism_retrodiction.ts — DOCTRINE-WAVES D-4b Lane B-5: mechanism_retrodiction
 *
 * L5 Mīmāṃsā: CONFIRMATION-ONLY retrodictive evidence surface. Joins the chart's
 * pre-2020 Life Event Log entries to the classical dasha-lord/house-activation
 * mechanism ("this chart's 2nd-house mechanism has fired N times: …").
 *
 * NO LEAKAGE (mirrors mimamsa_lel_intake.ts): this tool reads only the past
 * (event_date < 2020-01-01, hard-coded server-side, never caller-settable) and
 * reports historical overlaps. It MUST NOT feed prediction generation pipelines.
 *
 * Wiring: registerMechanismRetrodictionTool(server, principal) → server.ts during
 * L5 Mīmāṃsā registration.
 *
 * Delegates to callPlatformPrimitive('mechanism_retrodiction_get', ...) — whitelisted
 * in MCP_TO_RETRIEVAL_TOOL (tool_name_bridge.ts). No local DB SQL, no sidecar calls.
 *
 * BRAHMA-MI-5 (B-5)
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { callPlatformPrimitive } from '../client.js'

// ── Payload unwrap ────────────────────────────────────────────────────────────
//
// getToolByName().retrieve() (tool_name_bridge.ts capabilityResultToToolBundle)
// wraps every registry capability's `{content, is_error}` return into a legacy
// ToolBundle: envelope.result = { results: [{ content: "<JSON string>" }], ... }.
// This unwraps that one level (mirrors mimamsa_lel_intake.ts's unwrapLelPayload,
// simplified — this capability's payload has no total_matching/total_count quirk).
function unwrapMechanismPayload(envelopeResult: unknown): Record<string, unknown> | null {
  if (!envelopeResult || typeof envelopeResult !== 'object') return null
  const bundle = envelopeResult as Record<string, unknown>

  let payloadRaw: unknown = null
  const results = bundle['results']
  if (Array.isArray(results) && results.length > 0) {
    const first = results[0] as Record<string, unknown> | undefined
    payloadRaw = first?.['content']
  } else if ('mechanisms' in bundle) {
    payloadRaw = bundle
  }
  if (payloadRaw == null) return null

  if (typeof payloadRaw === 'string') {
    try {
      return JSON.parse(payloadRaw) as Record<string, unknown>
    } catch {
      return null
    }
  }
  if (typeof payloadRaw === 'object') return payloadRaw as Record<string, unknown>
  return null
}

// ── Tool registration ────────────────────────────────────────────────────────

export function registerMechanismRetrodictionTool(server: McpServer, principal: Principal): void {
  server.tool(
    'mechanism_retrodiction_get',
    'CONFIRMATION-ONLY retrodictive evidence surface (never prediction input). Joins the '
    + "chart's pre-2020 Life Event Log entries to the classical house-lord/Vimshottari-dasha "
    + "activation mechanism: for each domain-mapped event, reports whether that house's sign "
    + 'lord was running as Mahadasha (MD) or Antardasha (AD) lord on the event date. Returns '
    + "per-house firing counts (\"this chart's 2nd-house mechanism has fired N times\"), the "
    + 'confirming events, non-confirming mapped events, and events whose domain has no '
    + 'classical house mapping (honest gap, never dropped). Hard-excludes events on/after '
    + '2020-01-01 (sealed test split) — not a caller-settable parameter. Feeds the L5 '
    + 'retrodictive-evidence section only. BRAHMA-MI-5 (B-5).',
    {
      chart_id: z
        .string()
        .uuid()
        .describe('UUID of the chart to evaluate. Required — no default chart.'),
      ayanamsha_id: z
        .string()
        .optional()
        .describe("Ayanamsha filter (default: 'lahiri_chitrapaksha')."),
      domain: z
        .string()
        .optional()
        .describe("Filter to one domain prefix (e.g. 'wealth', 'career', 'health', 'relationship', 'spiritual', 'education', 'family', 'travel', 'loss', 'finance')."),
      house: z
        .number()
        .int()
        .min(1)
        .max(12)
        .optional()
        .describe('Filter to one house number (1-12). Omit to report all houses with any mapped event.'),
      dasha_level: z
        .enum(['md', 'ad', 'both'])
        .optional()
        .describe("Which dasha level counts as a firing: 'md', 'ad', or 'both' (default: 'both')."),
      limit: z
        .number()
        .int()
        .min(1)
        .max(50)
        .optional()
        .describe('Max LEL events considered (default: 50, max: 50).'),
    },
    async (params) => {
      if (!params.chart_id) {
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: 'chart_id is required', tool: 'mechanism_retrodiction_get' }, null, 2) }],
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

      const { status, envelope } = await callPlatformPrimitive(
        'mechanism_retrodiction_get',
        {
          chart_id: params.chart_id,
          ayanamsha_id: params.ayanamsha_id ?? null,
          domain: params.domain ?? null,
          house: params.house ?? null,
          dasha_level: params.dasha_level ?? null,
          limit: params.limit ?? 50,
        },
        principal,
      )

      if (status !== 200 || !envelope.ok) {
        const errorMsg = !envelope.ok
          ? envelope.error?.message ?? 'mechanism_retrodiction_get primitive failed'
          : `HTTP ${status} from mechanism_retrodiction_get primitive`
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              ok: false,
              error: errorMsg,
              tool: 'mechanism_retrodiction_get',
              asset: 'B-5',
              no_leakage_note: 'life_events is calibration corpus only — must not feed prediction generation',
            }, null, 2),
          }],
          isError: true,
        }
      }

      const payload = unwrapMechanismPayload(envelope.result)
      if (payload === null) {
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              ok: false,
              error: 'mechanism_retrodiction_get returned a well-formed envelope but the payload could not be located/parsed — NOT a genuine empty result.',
              tool: 'mechanism_retrodiction_get',
              asset: 'B-5',
            }, null, 2),
          }],
          isError: true,
        }
      }

      return {
        content: [{ type: 'text' as const, text: JSON.stringify({ ok: true, ...payload }, null, 2) }],
      }
    },
  )
}
