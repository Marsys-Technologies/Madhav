import 'server-only'
import { query } from '@/lib/db/client'

interface ClassicalTextSummary {
  text_key: string
  title: string
  author: string | null
  tradition: string
  school: string
  tier: number
  language_original: string | null
  translation_author: string | null
  chunk_count: number | null
  attribution_baseline_confidence: number | null
}

export async function getClassicalTextSummary(textKey: string): Promise<ClassicalTextSummary | null> {
  const { rows } = await query<ClassicalTextSummary>(
    `SELECT t.text_id AS text_key, t.title_en AS title,
            t.author, t.tradition, t.school, t.tier,
            NULL::text AS language_original, NULL::text AS translation_author,
            NULL::integer AS chunk_count, NULL::numeric AS attribution_baseline_confidence
     FROM public.classical_texts t
     WHERE t.text_id = $1
     LIMIT 1`,
    [textKey]
  )
  return rows[0] ?? null
}
