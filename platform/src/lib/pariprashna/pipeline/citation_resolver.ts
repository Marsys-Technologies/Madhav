/**
 * pariprashna/pipeline/citation_resolver.ts — G2-B "Citations at first
 * paint" (PPR-08, FD-2/FD-6).
 *
 * Builds the `CitationResolver` the live citation rewriter
 * (`citations/stream_wiring.ts`) uses to grade a sentinel DURING streaming.
 *
 * `CitationResolver.resolve` is SYNCHRONOUS by contract (`citations/types.ts`
 * — the rewriter calls it inline in the hot streaming loop and cannot await a
 * live DB round-trip per sentinel). So resolution here is a two-step split:
 *
 *   1. `fetchCandidateSignalLabels` — ONE prefetch query, run once before the
 *      synthesis stream opens, keyed on every `SIG.MSR.NNN`-shaped id visible
 *      in THIS TURN's own retrieved evidence (`EvidenceStageOutput.
 *      validToolResults`). Scoped to this turn's evidence deliberately: a
 *      sentinel naming a signal id that is real in the catalog but was never
 *      part of what THIS turn actually retrieved is not grounded for this
 *      answer, and must resolve to null (→ unverified / hallucination-
 *      counted) rather than borrow a grade from an unrelated context. A
 *      superset scan (extra candidate ids that never get cited) costs one
 *      wasted row in the prefetch, never a correctness problem — the
 *      candidate ids are just a cache-population hint, not a filter.
 *   2. `buildTurnCitationResolver` — wraps the resulting Map in the
 *      synchronous `CitationResolver` interface. A ref found resolves to
 *      grade `primary` (CitationGrade's own doc: "directly grounded in an L1
 *      fact / firings-authoritative signal" — which is exactly what an MSR
 *      signal id surfaced through this turn's own evidence pass is); a ref
 *      not found returns null, the honest "I don't know" (§N.7 item 6).
 */

import { query } from '@/lib/db/client'
import type { CitationGrade, CitationResolver, ResolvedCitation } from '@/lib/pariprashna/citations/types'
import type { ToolBundle } from '@/lib/retrieval/shared_types'

const SIGNAL_ID_RE = /SIG\.MSR\.\d{3}/g
const SNIPPET_MAX = 295

interface CandidateSignalLabel {
  reader_label: string
  grade: CitationGrade
}

/** Scan this turn's retrieved tool results for candidate SIG.MSR.NNN ids. */
export function extractCandidateSignalIds(args: {
  validToolResults: readonly ToolBundle[]
}): string[] {
  const ids = new Set<string>()
  for (const tb of args.validToolResults) {
    for (const r of tb.results) {
      for (const m of r.content.matchAll(SIGNAL_ID_RE)) ids.add(m[0])
    }
  }
  return [...ids]
}

/**
 * Fetch reader labels for candidate ids from `bodha_msr_signals`. Never
 * throws — a prefetch fault degrades to an empty map (every sentinel this
 * turn then resolves to `null` / unverified, the honest fail-closed
 * direction for a resolver that could not check its source), matching the
 * fail-open-to-honest-null discipline `register_leak_lint.ts`'s own
 * `lintReaderProse` documents for its internal-error path.
 */
export async function fetchCandidateSignalLabels(
  signalIds: readonly string[],
): Promise<Map<string, CandidateSignalLabel>> {
  if (signalIds.length === 0) return new Map()
  try {
    const placeholders = signalIds.map((_, i) => `$${i + 1}`).join(', ')
    const { rows } = await query<{ signal_id: string; name: string; description: string }>(
      `SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signals WHERE signal_id::text IN (${placeholders})`,
      signalIds as string[],
    )
    return new Map(
      rows.map((r) => {
        const full = r.name ? (r.description ? `${r.name} — ${r.description}` : r.name) : (r.description ?? r.signal_id)
        const snippet = full.length > SNIPPET_MAX ? full.slice(0, SNIPPET_MAX - 1) + '…' : full
        return [r.signal_id, { reader_label: snippet, grade: 'primary' as CitationGrade }]
      }),
    )
  } catch (err) {
    console.error(
      '[pariprashna] citation resolver prefetch failed (non-fatal — refs resolve unverified this turn):',
      err,
    )
    return new Map()
  }
}

/** Build a synchronous CitationResolver from a pre-fetched label map. */
export function buildTurnCitationResolver(
  labels: ReadonlyMap<string, CandidateSignalLabel>,
): CitationResolver {
  return {
    resolve(ref: string): ResolvedCitation | null {
      const hit = labels.get(ref)
      if (!hit) return null
      return {
        ref,
        reader_label: hit.reader_label,
        grade: hit.grade,
        audit_detail: `resolved from bodha_msr_signals where signal_id='${ref}' (this turn's retrieved evidence)`,
      }
    },
    readerLabel(idToken: string): string | null {
      return labels.get(idToken)?.reader_label ?? null
    },
  }
}
