/**
 * read_asset.ts — MCP Tier 4 tool: read a canonical MARSYS-JIS artifact.
 *
 * Returns the raw markdown of a canonical artifact (MSR, UCN, CDLM, CGM, RM,
 * FORENSIC, LEL, MACRO_PLAN, PROJECT_ARCHITECTURE) by canonical_id, with an
 * optional section filter.
 *
 * This is a Tier 4 tool per MCP_BRIEF §4.1. It is surgical (no planner, no
 * B.11 floor enforcement, no synthesis). Use when you need the full text of
 * a synthesis layer document — e.g., the full CGM for a graph overview, or
 * the full FORENSIC for a birth-data audit. For targeted fact lookups within
 * a document, prefer query_signals or query_chart_facts.
 *
 * Access control: Per decision D12 (full transparency), all authenticated
 * callers receive full file content.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { callPlatformAsset } from '../client.js'
import type { Principal } from '../types.js'

// ── Supported canonical IDs ──────────────────────────────────────────────────

const KNOWN_CANONICAL_IDS = [
  'MSR',
  'UCN',
  'CDLM',
  'CGM',
  'RM',
  'FORENSIC',
  'LEL',
  'MACRO_PLAN',
  'PROJECT_ARCHITECTURE',
] as const

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerReadAsset(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'read_asset',

    // ── Tool description (§4.6-standard, ≥100 words) ──────────────────────────
    `What it does: Returns the raw markdown of a canonical MARSYS-JIS artifact
by its canonical_id (e.g., "MSR", "FORENSIC", "UCN", "CDLM", "CGM", "RM", "LEL",
"MACRO_PLAN", "PROJECT_ARCHITECTURE"). Use when you need the full text of a
synthesis layer document, not just a signal-level query result.

When to prefer: Prefer read_asset when you need to read an entire document —
e.g., the full CGM for a comprehensive graph overview, or the full FORENSIC for
a complete birth-data audit. Prefer query_signals or query_chart_facts for
targeted fact lookups within documents. Prefer ask_madhav for any question
requiring synthesis across multiple documents.

Input shape hints: canonical_id — one of the supported canonical IDs listed
above (case-insensitive). section — optional section filter (e.g., "§A",
"Tier 1", "Planetary Positions", or any heading text); if omitted, the full
document is returned.

Output shape preview: {ok, result: {canonical_id, content: "<markdown>",
word_count, path, section_filter}, trace_id, epistemics: {surgical: true}}.

Example: read_asset({canonical_id: "MSR"}) → returns full MSR markdown (~514
signals, 30,000+ words); read_asset({canonical_id: "FORENSIC", section:
"Planetary Positions"}) → returns only the Planetary Positions section.`,

    // ── Input schema ──────────────────────────────────────────────────────────
    {
      canonical_id: z
        .string()
        .describe(
          `One of: ${KNOWN_CANONICAL_IDS.join(', ')}. Case-insensitive.`
        ),
      section: z
        .string()
        .optional()
        .describe(
          'Optional section heading filter (e.g., "§A" or "Planetary Positions"). ' +
          'Returns only the matched section and its content. ' +
          'Omit for the full document.'
        ),
    },

    // ── Handler ────────────────────────────────────────────────────────────────
    async ({ canonical_id, section }) => {
      const principal = getPrincipal()

      const result = await callPlatformAsset(
        { canonical_id, section },
        principal
      )

      if (!result.envelope.ok) {
        const errEnv = result.envelope
        const errorMsg = 'error' in errEnv
          ? `${errEnv.error.class}: ${errEnv.error.message}`
          : 'Unknown error from platform asset endpoint'
        return {
          content: [{ type: 'text' as const, text: `Error: ${errorMsg}` }],
          isError: true,
        }
      }

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(result.envelope, null, 2),
          },
        ],
      }
    }
  )
}
