import 'server-only'
import { query } from '@/lib/db/client'

interface ClassicalTextSummary {
  text_key: string
  title: string
  author: string | null
  tradition: string
  school: string
  tier: number
  language_original: string
  translation_author: string | null
  chunk_count: number
  attribution_baseline_confidence: number
}

export async function getClassicalTextSummary(textKey: string): Promise<ClassicalTextSummary | null> {
  const { rows } = await query<ClassicalTextSummary>(
    `SELECT text_key, title, author, tradition, school, tier, language_original,
            translation_author, chunk_count, attribution_baseline_confidence
     FROM classical_texts WHERE text_key = $1 LIMIT 1`,
    [textKey]
  )
  return rows[0] ?? null
}
