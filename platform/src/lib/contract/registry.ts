/**
 * registry.ts — Tool Contract Registry (L0FR Stream C 2026-06-07)
 *
 * Five classical text tools registered:
 *   1. read_classical_text  — semantic search over classical corpus
 *   2. read_chapter          — fetch all chunks for a chapter
 *   3. list_classical_texts  — list all ingested texts with metadata
 *   4. find_verses_about     — topic-based verse discovery
 *   5. search_classical_texts — (alias for read_classical_text, FTS+vector)
 *
 * MCP mirror: platform-mcp/src/contract_bridge.ts MCP_CONTRACT_TOOL_NAMES.
 */

import { z } from 'zod'
import type { ToolContract } from './types'

// ── 1. read_classical_text ────────────────────────────────────────────────────

const readClassicalTextContract: ToolContract<{
  query: string
  schools?: string[]
  tier_max?: number
  limit?: number
}> = {
  canonical_name: 'read_classical_text',

  description: `Semantic search over the classical Jyotish corpus (BPHS, Jaimini Sutras, KP Reader,
Tajaka Neelakanthi, Saravali, Brihat Jataka, Hora Sara, etc.). Use for verse-addressable citation lookup
(e.g. BPHS.1.7-1.12) or free-text semantic queries ("what does Parashara say about exalted Sun in 10H").
Prefer this tool over vector_search when the question is explicitly anchored in a named classical text
or school tradition. Returns verse reference, chunk content, similarity score, and tradition metadata.
Not chart-bound — does not require chart_id.`,

  input_schema: z.object({
    query: z.string().min(3).describe(
      'Semantic search string or verse citation (e.g. "BPHS.1.7" or "Parashara on Moon in 4th house")'
    ),
    schools: z.array(z.string()).optional().describe(
      'Filter by school/tradition: parashari | jaimini | tajika | kp | nadi | bnn'
    ),
    tier_max: z.number().int().min(1).max(4).optional().describe(
      'Maximum text tier to include (1=mandatory only, 4=all including nadi/bnn). Default: 3'
    ),
    limit: z.number().int().min(1).max(20).optional().describe(
      'Maximum results to return. Default: 5'
    ),
  }),

  annotations: {
    readOnly: true,
    idempotent: true,
    surgical: true,
    layer: 'L1',
  },

  role: 'text',
  family: 'school',
  data_dependency: 'classical_text',
  ayanamsha_role: null,
  ayanamsha_id: null,
  per_chart: false,
}

// ── 2. read_chapter ──────────────────────────────────────────────────────────

const readChapterContract: ToolContract<{
  text_id: string
  chapter: number
  limit?: number
}> = {
  canonical_name: 'read_chapter',

  description: `Fetch all verse chunks for a specific chapter of a classical text by chapter number.
Returns the full sequence of chunks (verse_ref, content_en, content_sa) for that chapter.
Use when you need complete chapter coverage rather than a semantic search. Not chart-bound.`,

  input_schema: z.object({
    text_id: z.string().min(2).describe(
      'Text identifier (e.g. bphs, jaimini_sutram, brihat_jataka, saravali, hora_sara)'
    ),
    chapter: z.number().int().min(1).describe('Chapter number (1-based)'),
    limit: z.number().int().min(1).max(100).optional().describe(
      'Maximum chunks to return. Default: 50'
    ),
  }),

  annotations: {
    readOnly: true,
    idempotent: true,
    surgical: true,
    layer: 'L1',
  },

  role: 'text',
  family: 'school',
  data_dependency: 'classical_text',
  ayanamsha_role: null,
  ayanamsha_id: null,
  per_chart: false,
}

// ── 3. list_classical_texts ──────────────────────────────────────────────────

const listClassicalTextsContract: ToolContract<Record<string, never>> = {
  canonical_name: 'list_classical_texts',

  description: `List all classical Jyotish texts ingested in the corpus with metadata.
Returns text_id, title, author, school/tradition, chunk count, and licensing info.
Use to discover available texts before querying with read_classical_text or find_verses_about.
Not chart-bound.`,

  input_schema: z.object({}),

  annotations: {
    readOnly: true,
    idempotent: true,
    surgical: true,
    layer: 'L1',
  },

  role: 'text',
  family: 'school',
  data_dependency: 'classical_text',
  ayanamsha_role: null,
  ayanamsha_id: null,
  per_chart: false,
}

// ── 4. find_verses_about ─────────────────────────────────────────────────────

const findVersesAboutContract: ToolContract<{
  topic: string
  text_ids?: string[]
  top_k?: number
}> = {
  canonical_name: 'find_verses_about',

  description: `Discover classical text verses about a specific astrological topic using embedding similarity.
Optional text_ids filter restricts results to named texts (e.g. ['bphs', 'jaimini_sutram']).
Returns ranked verse chunks with source citation and tradition.
Use for topic-centric research across the classical canon. Not chart-bound.`,

  input_schema: z.object({
    topic: z.string().min(3).describe(
      'Astrological topic or concept to search for (e.g. "Mars in 7th house spouse", "Saturn in 12th moksha")'
    ),
    text_ids: z.array(z.string()).optional().describe(
      'Restrict to these text_ids (e.g. ["bphs", "jaimini_sutram"]). Omit for all texts.'
    ),
    top_k: z.number().int().min(1).max(20).optional().describe(
      'Maximum verses to return. Default: 10'
    ),
  }),

  annotations: {
    readOnly: true,
    idempotent: true,
    surgical: true,
    layer: 'L1',
  },

  role: 'text',
  family: 'school',
  data_dependency: 'classical_text',
  ayanamsha_role: null,
  ayanamsha_id: null,
  per_chart: false,
}

// ── 5. search_classical_texts ────────────────────────────────────────────────

const searchClassicalTextsContract: ToolContract<{
  query: string
  schools?: string[]
  top_k?: number
}> = {
  canonical_name: 'search_classical_texts',

  description: `Combined embedding + full-text search over the classical Jyotish corpus.
Alias for read_classical_text with renamed parameters for clarity.
Returns top-K verse chunks by relevance with source citation, tradition, and chapter metadata.
Not chart-bound.`,

  input_schema: z.object({
    query: z.string().min(3).describe(
      'Search query (e.g. "Moon in 4th house" or "lagna lord in 6th")'
    ),
    schools: z.array(z.string()).optional().describe(
      'Filter by tradition: parashari | jaimini | tajika | kp | samhita'
    ),
    top_k: z.number().int().min(1).max(20).optional().describe(
      'Maximum results. Default: 5'
    ),
  }),

  annotations: {
    readOnly: true,
    idempotent: true,
    surgical: true,
    layer: 'L1',
  },

  role: 'text',
  family: 'school',
  data_dependency: 'classical_text',
  ayanamsha_role: null,
  ayanamsha_id: null,
  per_chart: false,
}

// ── Registry export ──────────────────────────────────────────────────────────

export const TOOL_CONTRACTS: readonly ToolContract<unknown>[] = [
  readClassicalTextContract as ToolContract<unknown>,
  readChapterContract as ToolContract<unknown>,
  listClassicalTextsContract as ToolContract<unknown>,
  findVersesAboutContract as ToolContract<unknown>,
  searchClassicalTextsContract as ToolContract<unknown>,
]

export function getContract(canonical_name: string): ToolContract<unknown> | undefined {
  return TOOL_CONTRACTS.find(c => c.canonical_name === canonical_name)
}

export function getContractNames(): string[] {
  return TOOL_CONTRACTS.map(c => c.canonical_name)
}
