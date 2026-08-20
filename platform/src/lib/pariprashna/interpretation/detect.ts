/**
 * pariprashna/interpretation/detect.ts — SIGNIFICANT judgment detection
 * (lane G3-B, PPR-02).
 *
 * PPR-02 names five judgment categories that MUST carry an interpretation
 * set or an explicit waiver: domain verdict, time-indexed, remedial,
 * prediction-detected, rules-in-tension. This module is the DETECTOR — pure,
 * deterministic, DB-free, reusing a REAL structural signal already computed
 * elsewhere in the pipeline wherever one exists, rather than guessing from
 * scratch (CLAUDE.md §N.4 "deterministic-first"):
 *
 *   - domain_verdict — reuses G2-A's `classifyCommittedBlock` role==='verdict'
 *     (the block classifier's own structural "first prose block of its
 *     pass" signal — `semantics/block_classifier.ts`, carried onto the
 *     committed block as `OpenBlock.semantic` by `reading_parts.ts`).
 *     Requires PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED to have been on this
 *     turn — `OpenBlock.semantic` is `undefined` otherwise, so this
 *     category structurally detects nothing on that path (an honest
 *     dependency, not a silently-degraded guess).
 *
 *   - prediction_detected — reuses SAMĪKṢĀ's own Stage-1 detector output
 *     verbatim (the SAME `DetectedPredictionRow[]`
 *     `reading_parts.ts#detectTurnPredictionCandidates` already computed
 *     for the canonical `prediction_candidate` parts) — zero new detection
 *     logic, zero re-derivation.
 *
 *   - rules_in_tension — reuses G2-A's role==='caveat' (a hedged/qualified
 *     block) COMBINED with a REAL structural fact: did this turn actually
 *     consult the `contradiction_register` tool (L2 Bodha's own
 *     contradiction surface — `retrieval/registry/tool_name_bridge.ts`)? A
 *     caveat block alone is just a hedge (`CAVEAT_LEAD_IN` fires on "however",
 *     "that said", etc. for many reasons); a caveat block in a turn that
 *     consulted the contradiction register is a caveat that is plausibly
 *     ABOUT a detected classical tension, which is what PPR-02 means by
 *     "rules-in-tension".
 *
 *   - remedial — the ONE category with no existing structural ROLE to reuse
 *     (G3-D's own roadmap row treats "second-person-imperative detector on
 *     remedial-class blocks" as still-unbuilt future work — there is no
 *     `role: 'remedial'` in `block_classifier.ts` today). Genuinely NEW
 *     detection here: a disclosed lexical scan for remedy-specific terms
 *     (mantra/gemstone/dāna/vrata/...), but never lexicon ALONE — gated on
 *     the REAL structural fact that this turn actually consulted
 *     `remedial_codex_query` (`tool_name_bridge.ts`'s canonical remedy-codex
 *     tool), so a paragraph that merely uses the word "mantra" in a turn
 *     that never retrieved from the remedy codex does not count.
 *
 *   - time_indexed — reuses `samiksha/detector.ts`'s own exported
 *     `TECHNIQUE_KEYWORDS` lexicon (dasha/gochara/tajaka/ashtakavarga/varga
 *     terms) VERBATIM, applied to a paragraph block's own text — the SAME
 *     lexicon the prediction enrichment already trusts to name a timing
 *     technique, reused rather than re-declared (§N.7 item 3: no
 *     wrapper-local constant may shadow an existing one).
 *
 * Every detector is pure and takes only already-computed pipeline outputs —
 * no DB read, no LLM call. `judgment_id`s are deterministic
 * (`sig-<category>-<n>`, `n` a turn-global counter in detection order) so a
 * repeated run against the same fixture produces identical ids.
 */

import type { OpenBlock, DetectedPredictionRow } from '@/lib/pariprashna/pipeline/reading_parts'
import type { ToolBundle } from '@/lib/retrieval/shared_types'
import { TECHNIQUE_KEYWORDS } from '@/lib/pariprashna/samiksha/detector'

import type { SignificantJudgmentCategory } from './schema'

export interface SignificantJudgment {
  judgment_id: string
  category: SignificantJudgmentCategory
  /** The committed block this judgment is anchored to, when known. */
  block_id: string | null
  /** The text sent to the interpretation-set generator. */
  claim_text: string
  /** Human-readable structural justification (audit/debug only — never reader-facing). */
  detection_basis: string
}

export interface DetectSignificantJudgmentsArgs {
  committedBlocks: readonly OpenBlock[]
  /** SAMĪKṢĀ's raw Stage-1 hits (score >= the persistence floor) — reused verbatim. */
  predictionCandidates: readonly DetectedPredictionRow[]
  validToolResults: readonly ToolBundle[]
}

/** Real, structural: did this turn's own tool broker actually call `toolName`? */
function toolConsulted(validToolResults: readonly ToolBundle[], toolName: string): boolean {
  return validToolResults.some((tb) => tb.tool_name === toolName)
}

/** The remedial lexicon — disclosed as fresh (no prior structural role exists
 *  for "remedial" — see module header). Deliberately narrow terms so an
 *  unrelated paragraph mentioning "charity" in a wealth context, say, does
 *  not alone qualify — the `remedial_codex_query` gate is the real anchor. */
const REMEDIAL_LEXICON: readonly string[] = [
  'mantra', 'gemstone', 'ratna', 'rudraksha', 'rudrāksha', 'donation', 'dāna', 'dana',
  'puja', 'pūjā', 'pooja', 'yantra', 'vrata', 'fast on', 'fasting', 'homa', 'havan',
  'propitiate', 'propitiation',
]

function matchesLexicon(text: string, lexicon: readonly string[]): boolean {
  const lower = text.toLowerCase()
  return lexicon.some((term) => lower.includes(term))
}

function matchesTechniqueKeywords(text: string): boolean {
  const lower = text.toLowerCase()
  return TECHNIQUE_KEYWORDS.some(([, kws]) => kws.some((k) => lower.includes(k)))
}

/** A structurally-classified, non-empty paragraph prose block. */
function isClassifiedParagraph(b: OpenBlock): boolean {
  return b.role === 'prose' && b.semantic?.kind === 'paragraph' && b.text.trim().length > 0
}

export function detectSignificantJudgments(
  args: DetectSignificantJudgmentsArgs,
): SignificantJudgment[] {
  const { committedBlocks, predictionCandidates, validToolResults } = args
  const out: SignificantJudgment[] = []
  const counters: Partial<Record<SignificantJudgmentCategory, number>> = {}
  const nextId = (category: SignificantJudgmentCategory): string => {
    const n = (counters[category] ?? 0) + 1
    counters[category] = n
    return `sig-${category}-${n}`
  }

  const contradictionConsulted = toolConsulted(validToolResults, 'contradiction_register')
  const remedialConsulted = toolConsulted(validToolResults, 'remedial_codex_query')

  for (const b of committedBlocks) {
    if (b.role !== 'prose' || !b.semantic) continue

    if (b.semantic.role === 'verdict') {
      out.push({
        judgment_id: nextId('domain_verdict'),
        category: 'domain_verdict',
        block_id: b.id,
        claim_text: b.text,
        detection_basis: "G2-A block role='verdict' (first prose block of its pass)",
      })
    }

    if (b.semantic.role === 'caveat' && contradictionConsulted) {
      out.push({
        judgment_id: nextId('rules_in_tension'),
        category: 'rules_in_tension',
        block_id: b.id,
        claim_text: b.text,
        detection_basis: "G2-A block role='caveat' + turn consulted contradiction_register",
      })
    }

    if (isClassifiedParagraph(b) && remedialConsulted && matchesLexicon(b.text, REMEDIAL_LEXICON)) {
      out.push({
        judgment_id: nextId('remedial'),
        category: 'remedial',
        block_id: b.id,
        claim_text: b.text,
        detection_basis: 'remedy lexicon match + turn consulted remedial_codex_query',
      })
    }

    if (isClassifiedParagraph(b) && matchesTechniqueKeywords(b.text)) {
      out.push({
        judgment_id: nextId('time_indexed'),
        category: 'time_indexed',
        block_id: b.id,
        claim_text: b.text,
        detection_basis:
          'samiksha/detector.ts TECHNIQUE_KEYWORDS match (dasha/gochara/tajaka/ashtakavarga/varga)',
      })
    }
  }

  for (const c of predictionCandidates) {
    const owner = committedBlocks.find((b) => b.role === 'prose' && b.text.includes(c.text))
    out.push({
      judgment_id: nextId('prediction_detected'),
      category: 'prediction_detected',
      block_id: owner?.id ?? null,
      claim_text: c.text,
      detection_basis: 'SAMĪKṢĀ Stage-1 prediction detector hit (score >= persistence floor)',
    })
  }

  return out
}
