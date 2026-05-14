/**
 * Tool 26: classical_attribution_lookup
 * Structured lookup in classical_attributions JOIN classical_chunks JOIN classical_texts.
 * Full implementation M8-E-S1 (2026-05-14).
 */

import 'server-only'
import { query } from '@/lib/db/client'

export interface ClassicalAttributionLookupInput {
  signal_ids: string[]
  attribution_type?: 'confirms' | 'contradicts' | 'partial' | 'extends' | 'silent'
  confidence_tier?: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface ClassicalAttributionRecord {
  attribution_id: string
  msr_signal_id: string
  text_key: string
  title: string
  author: string | null
  chapter: string | null
  verse_range: string | null
  content: string
  attribution_type: 'confirms' | 'contradicts' | 'partial' | 'extends' | 'silent'
  confidence: number
  confidence_tier: 'HIGH' | 'MEDIUM' | 'LOW'
  derivation_notes: string | null
  translation_cross_checked: boolean
}

export interface ClassicalAttributionLookupOutput {
  attributions: ClassicalAttributionRecord[]
  signal_ids_queried: string[]
  signal_ids_with_attributions: string[]
  signal_ids_silent: string[]
}

interface AttributionRow {
  attribution_id: string
  msr_signal_id: string
  text_key: string
  title: string
  author: string | null
  chapter: string | null
  verse_range: string | null
  content: string
  attribution_type: string
  confidence: number
  confidence_tier: string
  derivation_notes: string | null
  translation_cross_checked: boolean
}

export async function classical_attribution_lookup(
  input: ClassicalAttributionLookupInput
): Promise<ClassicalAttributionLookupOutput> {
  const { signal_ids, attribution_type, confidence_tier } = input

  if (signal_ids.length === 0) {
    return {
      attributions: [],
      signal_ids_queried: [],
      signal_ids_with_attributions: [],
      signal_ids_silent: [],
    }
  }

  const params: unknown[] = [signal_ids]
  let idx = 2
  const conditions: string[] = ['ca.msr_signal_id = ANY($1::text[])']

  if (attribution_type) {
    conditions.push(`ca.attribution_type = $${idx++}`)
    params.push(attribution_type)
  }
  if (confidence_tier) {
    conditions.push(`ca.confidence_tier = $${idx++}`)
    params.push(confidence_tier)
  }

  const sql = `
    SELECT
      ca.id::text             AS attribution_id,
      ca.msr_signal_id,
      ct.text_key,
      ct.title,
      ct.author,
      cc.chapter,
      cc.verse_range,
      cc.content,
      ca.attribution_type,
      ca.confidence,
      ca.confidence_tier,
      ca.derivation_notes,
      ca.translation_cross_checked
    FROM classical_attributions ca
    JOIN classical_chunks cc ON cc.id = ca.chunk_id
    JOIN classical_texts ct ON ct.id = cc.text_id
    WHERE ${conditions.join(' AND ')}
    ORDER BY ca.msr_signal_id, ca.confidence DESC
  `

  const { rows } = await query<AttributionRow>(sql, params)

  const attributions: ClassicalAttributionRecord[] = rows.map(row => ({
    attribution_id: row.attribution_id,
    msr_signal_id: row.msr_signal_id,
    text_key: row.text_key,
    title: row.title,
    author: row.author,
    chapter: row.chapter,
    verse_range: row.verse_range,
    content: row.content,
    attribution_type: row.attribution_type as ClassicalAttributionRecord['attribution_type'],
    confidence: Number(row.confidence),
    confidence_tier: row.confidence_tier as ClassicalAttributionRecord['confidence_tier'],
    derivation_notes: row.derivation_notes,
    translation_cross_checked: row.translation_cross_checked,
  }))

  const found = new Set(attributions.map(a => a.msr_signal_id))
  const signal_ids_with_attributions = signal_ids.filter(id => found.has(id))
  const signal_ids_silent = signal_ids.filter(id => !found.has(id))

  return {
    attributions,
    signal_ids_queried: signal_ids,
    signal_ids_with_attributions,
    signal_ids_silent,
  }
}
