/**
 * classical_text_tools.ts — L0FR Stream C capabilities
 *
 * read_chapter, list_classical_texts, find_verses_about
 * (read_classical_text / search_classical_texts live in classical_text_search.ts)
 *
 * L0FR Stream C implementation — 2026-06-07
 */

import 'server-only'
import { query } from '@/lib/db/client'
import type { ClassicalTextSearchResult } from './classical_text_search'
import { classical_text_search } from './classical_text_search'

// ── read_chapter ───────────────────────────────────────────────────────────────

export interface ReadChapterInput {
  text_id: string
  chapter: number
  limit?: number
}

export interface ReadChapterOutput {
  text_id: string
  chapter: number
  chunks: Array<{
    chunk_id: string
    verse_ref: string | null
    content_en: string
    content_sa: string | null
  }>
  total: number
}

export async function read_chapter(input: ReadChapterInput): Promise<ReadChapterOutput> {
  const { text_id, chapter, limit = 50 } = input
  const cap = Math.min(limit, 100)

  const result = await query<{
    chunk_id: string
    verse_ref: string | null
    content_en: string
    content_sa: string | null
  }>(
    `SELECT chunk_id, verse_ref, content_en, content_sa
     FROM classical_text_chunks
     WHERE text_id = $1 AND chapter = $2
     ORDER BY verse_start, chunk_id
     LIMIT $3`,
    [text_id, chapter, cap]
  )

  return {
    text_id,
    chapter,
    chunks: result.rows,
    total: result.rowCount ?? 0,
  }
}

// ── list_classical_texts ───────────────────────────────────────────────────────

export interface ListClassicalTextsOutput {
  texts: Array<{
    text_id: string
    title: string
    author: string | null
    school: string | null
    tradition: string | null
    chunk_count: number
    source_url: string | null
    license: string | null
  }>
  total: number
}

export async function list_classical_texts(): Promise<ListClassicalTextsOutput> {
  const result = await query<{
    text_id: string
    title_en: string
    author: string | null
    school: string | null
    tradition: string | null
    chunk_count: string
    source_url: string | null
    license: string | null
  }>(
    `SELECT
       t.text_id,
       t.title_en,
       t.author,
       t.school,
       t.tradition,
       COUNT(c.chunk_id) AS chunk_count,
       s.source_url,
       t.license
     FROM classical_texts t
     LEFT JOIN classical_text_chunks c ON c.text_id = t.text_id
     LEFT JOIN classical_texts_source s ON s.text_id = t.text_id
     GROUP BY t.text_id, t.title_en, t.author, t.school, t.tradition, s.source_url, t.license
     ORDER BY t.text_id`
  )

  return {
    texts: result.rows.map(r => ({
      text_id: r.text_id,
      title: r.title_en,
      author: r.author,
      school: r.school,
      tradition: r.tradition,
      chunk_count: parseInt(r.chunk_count ?? '0', 10),
      source_url: r.source_url,
      license: r.license,
    })),
    total: result.rowCount ?? 0,
  }
}

// ── find_verses_about ─────────────────────────────────────────────────────────

export interface FindVersesAboutInput {
  topic: string
  text_ids?: string[]
  top_k?: number
}

export interface FindVersesAboutOutput {
  results: ClassicalTextSearchResult[]
  total: number
  topic: string
}

export async function find_verses_about(input: FindVersesAboutInput): Promise<FindVersesAboutOutput> {
  const { topic, text_ids, top_k = 10 } = input

  // Use classical_text_search with school filter derived from text_ids
  // text_ids maps to tradition_school via DB lookup if provided
  let schools: string[] | undefined

  if (text_ids && text_ids.length > 0) {
    // Fetch tradition_school values for provided text_ids
    const result = await query<{ tradition_school: string }>(
      `SELECT DISTINCT tradition_school
       FROM classical_text_chunks
       WHERE text_id = ANY($1::text[]) AND tradition_school IS NOT NULL`,
      [text_ids]
    )
    const schoolSet = result.rows.map(r => r.tradition_school).filter(Boolean)
    if (schoolSet.length > 0) schools = schoolSet
  }

  const searchResult = await classical_text_search({
    query: topic,
    schools,
    limit: top_k,
  })

  // If text_ids specified, post-filter by text_id (in case school maps to multiple texts)
  let results = searchResult.results
  if (text_ids && text_ids.length > 0) {
    const idSet = new Set(text_ids)
    results = results.filter(r => idSet.has(r.text_key))
  }

  return { results, total: results.length, topic }
}

// ── read_classical_text_by_ref ────────────────────────────────────────────────
// (verse_ref lookup — supplement to the search-based read_classical_text)

export interface ReadClassicalTextByRefInput {
  text_id: string
  verse_ref: string
}

export interface ReadClassicalTextByRefOutput {
  chunk_id: string | null
  text_id: string
  verse_ref: string
  content_en: string | null
  content_sa: string | null
  chapter: number | null
  source_citation: string | null
  found: boolean
}

export async function read_classical_text_by_ref(
  input: ReadClassicalTextByRefInput
): Promise<ReadClassicalTextByRefOutput> {
  const { text_id, verse_ref } = input

  const result = await query<{
    chunk_id: string
    text_id: string
    verse_ref: string
    content_en: string
    content_sa: string | null
    chapter: number | null
    source_citation: string | null
  }>(
    `SELECT chunk_id, text_id, verse_ref, content_en, content_sa, chapter, source_citation
     FROM classical_text_chunks
     WHERE text_id = $1 AND verse_ref = $2
     LIMIT 1`,
    [text_id, verse_ref]
  )

  if (result.rows.length === 0) {
    return {
      chunk_id: null,
      text_id,
      verse_ref,
      content_en: null,
      content_sa: null,
      chapter: null,
      source_citation: null,
      found: false,
    }
  }

  const row = result.rows[0]!
  return {
    chunk_id: row.chunk_id,
    text_id: row.text_id,
    verse_ref: row.verse_ref,
    content_en: row.content_en,
    content_sa: row.content_sa,
    chapter: row.chapter,
    source_citation: row.source_citation,
    found: true,
  }
}
