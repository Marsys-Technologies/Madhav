/**
 * Shared fixtures for PB-1 lane S-3 citation-pipeline tests.
 */

import type {
  CitationResolver,
  PariprashnaCitationEvent,
  RewriteChunk,
  ResolvedCitation,
} from '@/lib/pariprashna/citations'
import { CitationStreamRewriter } from '@/lib/pariprashna/citations'
import type { RewriterOptions } from '@/lib/pariprashna/citations/rewriter'

/**
 * A deterministic fixture resolver.
 *  - `SIG.MSR.<n>` refs resolve to a graded reader label.
 *  - Any ref containing "GHOST" resolves to null (→ unverified / hallucination).
 *  - readerLabel maps a handful of id-shaped tokens to human labels for the
 *    lint REWRITE verdict; everything else returns null (→ REDACT).
 */
export function makeFixtureResolver(): CitationResolver {
  const labels: Record<string, string> = {
    'SIG.MSR.413': 'Mercury eight-system convergence',
    'SIG.MSR.042': 'Saturn–Moon mutual aspect',
    bo_laksana: 'core signal reading',
    ga_positions: 'natal positions',
  }
  return {
    resolve(ref: string): ResolvedCitation | null {
      if (ref.includes('GHOST')) return null
      const label = labels[ref] ?? `signal ${ref}`
      const grade: ResolvedCitation['grade'] = ref === 'SIG.MSR.413' ? 'primary' : 'supporting'
      return {
        ref,
        reader_label: label,
        grade,
        audit_detail: `resolved from bodha_msr_signals where signal_id='${ref}'`,
      }
    },
    readerLabel(idToken: string): string | null {
      return labels[idToken] ?? null
    },
  }
}

export function makeRewriter(overrides: Partial<RewriterOptions> = {}): CitationStreamRewriter {
  return new CitationStreamRewriter({
    resolver: makeFixtureResolver(),
    modelId: 'fixture-model',
    ...overrides,
  })
}

/** Drive a rewriter through a list of deltas at a fixed clock, then end(). */
export function runStream(
  rw: CitationStreamRewriter,
  deltas: string[],
  opts: { startMs?: number; perDeltaMs?: number } = {},
): { text: string; events: PariprashnaCitationEvent[] } {
  const start = opts.startMs ?? 0
  const step = opts.perDeltaMs ?? 1
  let text = ''
  const events: PariprashnaCitationEvent[] = []
  deltas.forEach((d, i) => {
    const chunk: RewriteChunk = rw.write(d, start + i * step)
    text += chunk.text
    events.push(...chunk.events)
  })
  const tail = rw.end()
  text += tail.text
  events.push(...tail.events)
  return { text, events }
}
