/**
 * read_classical_text.ts — MCP Tier 4 tool: semantic search over the MARSYS classical corpus.
 *
 * Returns excerpts from the indexed classical texts ranked by semantic similarity to a query,
 * or an exact chapter:verse lookup when `citation` or `chapter`+`verse` params are supplied.
 *
 * Classical corpus lives in `classical_chunks` table (separate from `rag_chunks`).
 * As of Phase 0 audit (2026-05-25): 14 texts, 8,349 chunks, 8,337 with embeddings.
 * Known text_key values include: bphs, phaladeepika, saravali, jaimini_sutra, brihat_jataka,
 * kp_texts, hora_sara, uttara_kalamrita, prashna_marga, brihat_samhita, dhruva_nadi_sampler,
 * bhrigu_nandi_nadi, chandra_kala_nadi, tajaka_neelakanthi (may vary — check DB for exact list).
 *
 * Bug fixed (TR-P2-S3 / C10): previous version passed text_id.toLowerCase() as `schools` filter
 * (matching ct.school e.g. 'parashari'), which is WRONG. The fix passes it as `text_key` filter
 * (matching ct.text_key e.g. 'bphs'). Platform-side retrieval tool update to honour text_key
 * is tracked as TR-P2-S3-RES-1 (out of scope for this session; tests mock callPlatformPrimitive).
 *
 * Citation lookup added (TR-P2-S3): supply `citation: "BPHS.33.1"` or `chapter`+`verse` together
 * for an exact verse lookup. Falls back to semantic search if exact lookup returns 0 rows.
 *
 * Per arch §3.7, this is a Tier 4 raw-asset read that enables classical quoting.
 * Use it to ground interpretive claims in canonical śāstra text.
 *
 * Architecture note: routes through /api/mcp/primitives/read_classical_text →
 * classical_text_search retrieval tool → classical_chunks JOIN classical_texts.
 * Vertex AI text-embedding-004 (768-dim) for similarity ranking.
 *
 * Access control: all authenticated tiers (super_admin, acharya, client).
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

// ── Supported classical texts ─────────────────────────────────────────────────
// Extended from the original 4 to reflect all 14 texts now indexed in the DB.
// text_id values map to ct.text_key (lowercase, underscore-separated).

const CLASSICAL_TEXT_IDS = [
  'BPHS',
  'KP_READER',
  'JAIMINI',
  'TAJAKA',
  'PHALADEEPIKA',
  'SARAVALI',
  'BRIHAT_JATAKA',
  'HORA_SARA',
  'UTTARA_KALAMRITA',
  'PRASHNA_MARGA',
  'BRIHAT_SAMHITA',
  'DHRUVA_NADI_SAMPLER',
  'BHRIGU_NANDI_NADI',
  'CHANDRA_KALA_NADI',
] as const

export const READ_CLASSICAL_TEXT_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Retrieves excerpts from the MARSYS-JIS classical corpus (BPHS, Phaladeepika, ' +
    'Saravali, KP Reader, Jaimini Sutram, Tajaka Neelakanthi, Brihat Jataka, and 7 more texts) ' +
    'ranked by semantic similarity to a query. Supports exact chapter:verse lookup via `citation` param.',
  enumSource: CLASSICAL_TEXT_IDS,
  coverageHint: 'Vertex AI 768-dim embeddings; 14 texts, 8,349 chunks; limit 1–20 excerpts per call',
  whenToPrefer:
    'Use when the question requires a classical textual citation ("what does Parashara say about Ketu in the 12th?"). ' +
    'Use `citation: "BPHS.33.1"` for exact verse lookup. ' +
    'Prefer vector_search for cross-layer semantic retrieval including MSR signals and LEL data. ' +
    'Prefer query_chart_facts or query_signals for structured fact lookups that do not require quoting.',
  tierAccess: 'super_admin + acharya. Classical text corpus is acharya-grade.',
})

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerReadClassicalText(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'read_classical_text',

    READ_CLASSICAL_TEXT_DESCRIPTION,

    // ── Input schema ──────────────────────────────────────────────────────────
    {
      query: z
        .string()
        .optional()
        .describe(
          'The Sanskrit concept, yoga name, or interpretive question to search for. ' +
          'E.g., "Ketu in 12th house moksha" or "Hamsa yoga Jupiter exaltation". ' +
          'Optional when citation param is supplied (citation provides the lookup key).'
        ),
      text_id: z
        .enum(CLASSICAL_TEXT_IDS)
        .optional()
        .describe(
          `Optional: restrict to a specific classical text. One of: ${CLASSICAL_TEXT_IDS.join(', ')}. ` +
          'Omit to search across all indexed texts.'
        ),
      citation: z
        .string()
        .optional()
        .describe(
          'Citation string in the form "TEXT_ID.chapter.verse", e.g. "BPHS.33.1" or "PHALADEEPIKA.7.12". ' +
          'When supplied, performs an exact chapter:verse lookup (ignores `chapter`/`verse` params). ' +
          'Falls back to semantic search if the exact verse is not found in the corpus.'
        ),
      chapter: z
        .number()
        .int()
        .min(1)
        .optional()
        .describe(
          'Chapter number for exact lookup. Must be combined with `verse` and `text_id` for a precise result. ' +
          'Ignored when `citation` is supplied.'
        ),
      verse: z
        .number()
        .int()
        .min(1)
        .optional()
        .describe(
          'Verse number for exact lookup. Must be combined with `chapter` and `text_id` for a precise result. ' +
          'Ignored when `citation` is supplied.'
        ),
      limit: z
        .number()
        .int()
        .min(1)
        .max(20)
        .optional()
        .default(5)
        .describe('Max excerpts to return for semantic search (default 5, max 20). Ignored for exact lookup.'),
    },

    // ── Handler ────────────────────────────────────────────────────────────────
    async ({ query, text_id, citation, chapter, verse, limit }) => {
      const principal = getPrincipal()

      // ── Citation resolution ──────────────────────────────────────────────
      // Parse "BPHS.33.1" → { textKey: "bphs", chapter: 33, verse: 1 }
      let resolvedTextKey: string | undefined = text_id ? text_id.toLowerCase() : undefined
      let resolvedChapter: number | undefined = chapter
      let resolvedVerse: number | undefined = verse
      let isExactLookup = false

      if (citation) {
        const parts = citation.split('.')
        if (parts.length >= 3) {
          resolvedTextKey = parts[0].toLowerCase()
          const parsedChapter = parseInt(parts[1], 10)
          const parsedVerse = parseInt(parts[2], 10)
          if (!isNaN(parsedChapter) && !isNaN(parsedVerse)) {
            resolvedChapter = parsedChapter
            resolvedVerse = parsedVerse
            isExactLookup = true
          }
        }
      } else if (chapter !== undefined && verse !== undefined && resolvedTextKey) {
        isExactLookup = true
      }

      // ── Build tool params ────────────────────────────────────────────────
      // Fix (C10 / TR-P2-S3): pass text_key filter (ct.text_key = 'bphs'), NOT schools filter
      // (ct.school = 'parashari'). The previous bug passed text_id.toLowerCase() as `schools`,
      // which mapped to the school/tradition column instead of the per-work text_key column.
      //
      // Note: the platform-side classical_text_search retrieval tool currently reads `schools`
      // from params and filters ct.school. A follow-on session (TR-P2-S3-RES-1) must update
      // classical_text_search_tool.ts to also read `text_key` from params and filter ct.text_key.
      // Until that lands, exact text filtering in production requires that update.

      const toolParams: Record<string, unknown> = {
        query: query ?? (citation ? `exact lookup: ${citation}` : 'classical text'),
        limit,
      }

      if (resolvedTextKey) {
        toolParams['text_key'] = resolvedTextKey
      }

      if (isExactLookup) {
        toolParams['chapter'] = resolvedChapter
        toolParams['verse'] = resolvedVerse
        toolParams['exact_lookup'] = true
      }

      // ── Platform call ────────────────────────────────────────────────────
      const result = await callPlatformPrimitive(
        'read_classical_text',
        toolParams,
        principal
      )

      if (!result.envelope.ok) {
        const errEnv = result.envelope
        const errorMsg = 'error' in errEnv
          ? `${errEnv.error.class}: ${errEnv.error.message}`
          : 'Unknown error from platform primitive endpoint'
        const validIds = CLASSICAL_TEXT_IDS.join(', ')
        return {
          content: [{ type: 'text' as const, text: `Error: ${errorMsg} Valid text IDs: ${validIds}.` }],
          isError: true,
        }
      }

      // ── Augment with lookup metadata ────────────────────────────────────
      const baseResult = okResult(result.envelope)

      if (isExactLookup || citation) {
        // Inject citation metadata into the response text
        const parsed = JSON.parse(baseResult.content[0].text as string) as Record<string, unknown>
        parsed['lookup_mode'] = isExactLookup ? 'exact' : 'semantic'
        if (citation) parsed['citation_requested'] = citation
        if (resolvedTextKey) parsed['text_key_filter'] = resolvedTextKey
        if (resolvedChapter !== undefined) parsed['chapter_filter'] = resolvedChapter
        if (resolvedVerse !== undefined) parsed['verse_filter'] = resolvedVerse

        // Note fallback if platform returned results via semantic (no exact match signal)
        const toolBundle = (parsed['result'] as Record<string, unknown> | undefined) ?? parsed
        const results = (toolBundle['results'] as unknown[] | undefined) ?? []
        if (isExactLookup && results.length === 0) {
          parsed['fallback'] = 'semantic_search'
          parsed['fallback_reason'] = 'exact chapter:verse not found in corpus; semantic search returned 0 results'
        }

        return {
          content: [{ type: 'text' as const, text: JSON.stringify(parsed, null, 2) }],
        }
      }

      return baseResult
    }
  )
}
