/**
 * pariprashna_synthesis_prompt_v1.ts — PB-1 (DHĀRĀ) lane S-3.
 *
 * Route-scoped synthesis system prompt for the PARIPRAŚNA route ONLY.
 *
 * This is a NEW prompt variant. It is deliberately separate from consult's
 * `synthesis_prompt_v2.ts` (which uses GFM `[^N]` footnotes) and does not import
 * or mutate it — consult's prompt must remain byte-identical. The two routes
 * diverge here: Paripraśna uses INLINE SENTINELS that a server-side rewriter
 * (src/lib/pariprashna/citations/rewriter.ts) resolves live during streaming,
 * rather than end-of-answer footnote definitions.
 *
 * Sentinel contract (must match rewriter.ts / grammar.ts):
 *
 *     ⟦cite: <ref>⟧
 *
 * placed inline immediately after the clause it supports. The rewriter replaces
 * each resolved sentinel with a clean numbered marker and emits a
 * citation.define event carrying the reader label + grade out-of-band, so the
 * model NEVER writes an internal id or a footnote block into visible prose.
 */

import { consumeSystemPrompt, type ConsumeStyle } from '@/lib/claude/system-prompts'

interface ChartContext {
  id: string
  name: string
  birth_date: string
  birth_time: string
  birth_place: string
}

interface ReportEntry {
  domain: string
  title: string
  version: string
}

/**
 * Paripraśna citation appendix — INLINE SENTINELS.
 *
 * Note the U+27E6 / U+27E7 white-square brackets: `⟦` … `⟧`. The rewriter is
 * TOLERANT (it also accepts `[[cite: … ]]`, spacing, and case variants and
 * normalizes them), but the model should aim for the canonical form.
 */
export const PARIPRASHNA_CITATION_APPENDIX = `

---
CITATION FORMAT — INLINE SENTINELS (Paripraśna):
When a statement rests on a retrieved signal, mark it with an INLINE citation
sentinel placed immediately after the supporting clause:

    ⟦cite: <ref>⟧

where <ref> is the exact reference id as it appears in the retrieved context
(for example a signal id from the assembled evidence). The sentinel is consumed
by the streaming pipeline and rendered to the reader as a small numbered marker;
you never see or write the final number yourself.

Example (write this):
    "Mercury anchors an eight-system convergence⟦cite: SIG.MSR.413⟧, making it the
    chart's primary operational force."

STRICT OUTPUT RULES — violations degrade the reader stream:
• Place the sentinel INLINE, right after the clause it supports. Do NOT collect
  citations into a footnote block at the end of the answer.
• Use the ⟦cite: …⟧ sentinel form. Do NOT use [^N] footnotes, (→ SIG…) wrappers,
  or bare ids in visible prose.
• Put ONLY the reference id inside the sentinel — nothing else.
• Do NOT invent reference ids. Cite only ids present in the retrieved context.
  An unrecognized ref is surfaced to the reader as "unverified" — avoid it.
• Never write internal identifiers (signal ids, asset ids like bo_/ga_/…, table
  names, or register acronyms) in the visible prose OUTSIDE a sentinel. The
  reader must only ever see human language and the numbered markers.
• Write Sanskrit terms in plain text with a brief inline gloss where helpful:
  "Sasa Mahapurusha Yoga (Saturn exalted in a kendra)".`

/**
 * Build the Paripraśna-route synthesis system prompt.
 *
 * Same base as other routes (`consumeSystemPrompt`) + the inline-sentinel
 * appendix. Scoped to Paripraśna: nothing here is imported by consult.
 */
export function pariprashnaSynthesisPrompt(
  chart: ChartContext,
  reports: ReportEntry[],
  style: ConsumeStyle = 'acharya',
  blindMode: boolean = false,
): string {
  return consumeSystemPrompt(chart, reports, style, blindMode) + PARIPRASHNA_CITATION_APPENDIX
}
