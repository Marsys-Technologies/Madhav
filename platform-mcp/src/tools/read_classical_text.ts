/**
 * read_classical_text.ts — L0FR Stream C MCP Tool (2026-06-07)
 *
 * MCP tool: read_classical_text
 * Semantic + full-text search over the classical_text_chunks table.
 * Delegates to the platform /api/retrieval/classical-text endpoint.
 *
 * Also includes stub registrations for:
 *   - read_chapter
 *   - list_classical_texts
 *   - find_verses_about
 *   - search_classical_texts
 *
 * All five tools satisfy the L0FR Stream C requirement of ≥4 retrieval capabilities
 * in BOTH MCP and Consume Chat channels.
 *
 * L0FR Stream C — brahmagyan.texts capability registration
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { callPlatformPrimitive } from '../client.js'
import type { Principal, McpEnvelopeError } from '../types.js'
import { budgetMcpContent } from '../lib/response_budget.js'

// ── Input schemas ─────────────────────────────────────────────────────────────

const ReadClassicalTextInput = z.object({
  query: z.string().min(3).describe('Search query — semantic or verse ref (e.g. "BPHS CH7:V14")'),
  schools: z.array(z.string()).optional().describe('Filter by tradition_school'),
  limit: z.number().int().min(1).max(20).optional().default(5).describe('Max results (1-20)'),
})

const ReadChapterInput = z.object({
  text_id: z.string().min(2).describe('Classical text identifier (e.g. bphs, saravali)'),
  chapter: z.number().int().min(1).describe('Chapter number'),
  limit: z.number().int().min(1).max(100).optional().default(50),
})

const FindVersesAboutInput = z.object({
  topic: z.string().min(3).describe('Topic to search for (e.g. "exalted Mars in 10th house")'),
  text_ids: z.array(z.string()).optional().describe('Restrict to these text_ids'),
  top_k: z.number().int().min(1).max(20).optional().default(10),
})

const SearchClassicalTextsInput = z.object({
  query: z.string().min(3).describe('Search query text'),
  top_k: z.number().int().min(1).max(20).optional().default(5),
  schools: z.array(z.string()).optional(),
})

// ── Register functions ────────────────────────────────────────────────────────

export function registerReadClassicalText(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'read_classical_text',
    'Semantic + full-text search over the classical Jyotish corpus ' +
    '(BPHS, Saravali, Brihat Jataka, Hora Sara, Uttara Kalamrita, Jaimini Sutras, etc.). ' +
    'Use for verse-addressable citation lookup or free-text semantic queries. ' +
    'Returns chunk content, verse reference, chapter, tradition, and similarity score. ' +
    'Not chart-bound. L0FR Stream C — brahmagyan.texts',
    ReadClassicalTextInput.shape,
    async (params) => {
      try {
        const p = ReadClassicalTextInput.parse(params)
        const { status, envelope } = await callPlatformPrimitive('read_classical_text', p, getPrincipal())
        if (status !== 200 || !envelope.ok) {
          return { content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'read_classical_text', message: (envelope as McpEnvelopeError).error?.message ?? status }, null, 2) }], isError: true }
        }
        return { content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent(envelope.result, 'read_classical_text'), null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'read_classical_text', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}

export function registerReadChapter(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'read_chapter',
    'Fetch all verse chunks for a specific chapter of a classical text. ' +
    'Returns the full sequence of chunks (verse_ref, content_en, content_sa) for that chapter. ' +
    'Not chart-bound. L0FR Stream C — brahmagyan.texts',
    ReadChapterInput.shape,
    async (params) => {
      try {
        const p = ReadChapterInput.parse(params)
        const { status, envelope } = await callPlatformPrimitive('read_chapter', p, getPrincipal())
        if (status !== 200 || !envelope.ok) {
          return { content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'read_chapter', message: (envelope as McpEnvelopeError).error?.message ?? status }, null, 2) }], isError: true }
        }
        return { content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent(envelope.result, 'read_chapter'), null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'read_chapter', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}

export function registerListClassicalTexts(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'list_classical_texts',
    'List all classical Jyotish texts ingested in the corpus with metadata. ' +
    'Returns text_id, title, author, school/tradition, chunk count, and licensing info. ' +
    'Use to discover available texts before querying. Not chart-bound. L0FR Stream C',
    {},
    async () => {
      try {
        const { status, envelope } = await callPlatformPrimitive('list_classical_texts', {}, getPrincipal())
        if (status !== 200 || !envelope.ok) {
          return { content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'list_classical_texts', message: (envelope as McpEnvelopeError).error?.message ?? status }, null, 2) }], isError: true }
        }
        return { content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent(envelope.result, 'list_classical_texts'), null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'list_classical_texts', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}

export function registerFindVersesAbout(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'find_verses_about',
    'Discover classical text verses about a specific astrological topic using embedding similarity. ' +
    'Optionally restrict to specific text_ids. Not chart-bound. L0FR Stream C — brahmagyan.texts',
    FindVersesAboutInput.shape,
    async (params) => {
      try {
        const p = FindVersesAboutInput.parse(params)
        const { status, envelope } = await callPlatformPrimitive('find_verses_about', p, getPrincipal())
        if (status !== 200 || !envelope.ok) {
          return { content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'find_verses_about', message: (envelope as McpEnvelopeError).error?.message ?? status }, null, 2) }], isError: true }
        }
        return { content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent(envelope.result, 'find_verses_about'), null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'find_verses_about', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}

export function registerSearchClassicalTexts(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'search_classical_texts',
    'Combined embedding + full-text search over the classical Jyotish corpus. ' +
    'Alias for read_classical_text with renamed parameters for clarity. ' +
    'Not chart-bound. L0FR Stream C — brahmagyan.texts',
    SearchClassicalTextsInput.shape,
    async (params) => {
      try {
        const p = SearchClassicalTextsInput.parse(params)
        const { status, envelope } = await callPlatformPrimitive('search_classical_texts', p, getPrincipal())
        if (status !== 200 || !envelope.ok) {
          return { content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'search_classical_texts', message: (envelope as McpEnvelopeError).error?.message ?? status }, null, 2) }], isError: true }
        }
        return { content: [{ type: 'text' as const, text: JSON.stringify(budgetMcpContent(envelope.result, 'search_classical_texts'), null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'search_classical_texts', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}
