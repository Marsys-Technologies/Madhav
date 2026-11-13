/**
 * classical_text_tools.ts — L0FR Stream C capabilities
 *
 * read_chapter, list_classical_texts, find_verses_about
 * (read_classical_text / search_classical_texts live in classical_text_search.ts)
 *
 * L0FR Stream C implementation — 2026-06-07
 */

import 'server-only'
import type { ClassicalTextSearchResult } from './classical_text_search'
import { classical_text_search } from './classical_text_search'
import { readClassicalTextSchools } from '@/lib/brahmagyan/classical_text_reads'

export {
  read_chapter,
  list_classical_texts,
  read_classical_text_by_ref,
  type ReadChapterInput,
  type ReadChapterOutput,
  type ListClassicalTextsOutput,
  type ReadClassicalTextByRefInput,
  type ReadClassicalTextByRefOutput,
} from '@/lib/brahmagyan/classical_text_reads'

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
    const schoolSet = await readClassicalTextSchools(text_ids)
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
