/**
 * Citation data part — emitted from consume route onFinish, indexed by N.
 *
 * Each unique SIG.MSR.NNN detected in the synthesis response becomes a
 * CitationPart. The index (1-based, order of first appearance) drives the
 * inline [N] superscript in the message renderer.
 *
 * R6.3 (2026-05-18): enrichCitations() populates snippet from claim_text
 * in l25_msr_signals via a single batch query before parts are emitted.
 */

import { z } from 'zod'
import { query } from '@/lib/db/client'
import type { MsrSignal } from '@/lib/db/types'

export const CitationPartSchema = z.object({
  type: z.literal('citation'),
  index: z.number().int().positive(),
  signal_id: z.string().regex(/^SIG\.MSR\.\d{3}$/),
  layer: z.enum(['L1', 'L2.5']).default('L2.5'),
  snippet: z.string().max(300).default(''),
})

export type CitationPart = z.infer<typeof CitationPartSchema>

export const citationPart = (args: Omit<CitationPart, 'type'>): CitationPart => ({
  type: 'citation',
  ...args,
})

/** Extract ordered, deduplicated SIG.MSR.NNN citations from a response string. */
export function extractCitations(text: string): CitationPart[] {
  const seen = new Set<string>()
  const result: CitationPart[] = []
  const pattern = /SIG\.MSR\.\d{3}(?!\d)/g
  let match: RegExpExecArray | null
  while ((match = pattern.exec(text)) !== null) {
    const signalId = match[0]
    if (!seen.has(signalId)) {
      seen.add(signalId)
      result.push(citationPart({
        index: result.length + 1,
        signal_id: signalId,
        layer: 'L2.5',
        snippet: '',
      }))
    }
  }
  return result
}

/** Build a map from signal_id → citation index for fast inline lookup. */
export function buildCitationIndex(citations: CitationPart[]): Map<string, number> {
  return new Map(citations.map(c => [c.signal_id, c.index]))
}

/**
 * Enrich citation snippets from l25_msr_signals.claim_text via a single
 * batch query. Best-effort — on DB failure returns citations unmodified.
 */
export async function enrichCitations(citations: CitationPart[]): Promise<CitationPart[]> {
  if (citations.length === 0) return citations
  const ids = citations.map(c => c.signal_id)
  try {
    const result = await query<Pick<MsrSignal, 'signal_id' | 'claim_text'>>(
      'SELECT signal_id, claim_text FROM l25_msr_signals WHERE signal_id = ANY($1)',
      [ids],
    )
    const claimMap = new Map(result.rows.map(r => [r.signal_id, r.claim_text]))
    return citations.map(c => ({
      ...c,
      snippet: claimMap.get(c.signal_id)?.slice(0, 300) ?? c.snippet,
    }))
  } catch (err) {
    console.warn('[enrichCitations] DB lookup failed, returning bare citations', err)
    return citations
  }
}
