/**
 * argument_composer.ts — ṢAḌ-DARŚANA W0.3 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W0.3 · §2 file map
 * · §12/E7.4 "the argument-composer library").
 * ==========================================================================
 * THE shared, deterministic prose engine that turns a `kala_envelope.ts` `ArgumentReading`
 * into served text: "ONE shared, tested, deterministic prose-composition engine (thesis/
 * evidence/dissent/falsifier templates) used by all eight tools — one voice, one gate, no
 * inter-view drift (duplicate-copy class pre-empted at the prose layer)."
 * (KALA_SUPREME_ELEVATION_v1_0.md §12 E7.4)
 *
 * ══════════════════════════════════════════════════════════════════════════════════════
 * HARD RAIL (CLAUDE.md §N (B.10) + SHAD_DARSHANA_BRIEF_v2_0.md §7):
 * "the argument composer is template-over-computed-data; no generative call in any
 * serving path."
 *
 * This file contains NO network calls, NO LLM/model client of any kind, and NO import of
 * one. Every exported function is a pure, deterministic string template over data the
 * CALLER already computed (fact_ids, claims, tiers, dates it supplies). Given the same
 * input, every function here returns byte-identical output, forever — that determinism IS
 * the B.10 compliance proof, and it is what makes this file mechanically testable (see
 * argument_composer.test.ts, which includes a literal "no generative call" source-text
 * guard alongside the compositional tests).
 *
 * If a future change to this file ever needs something an LLM call could provide (tone
 * variation, summarization, phrasing judgment) — STOP. That is out of contract for this
 * file by design; the answer is a better template or a new field on `ArgumentReading`
 * upstream, never a generative call here.
 * ══════════════════════════════════════════════════════════════════════════════════════
 */

import type {
  ArgumentReading,
  ArgumentEvidence,
  ArgumentDissent,
  ArgumentVerdict,
  ArgumentVerdictTier,
  ArgumentFalsifier,
  KalaCoverageEntry,
  KalaFreshness,
} from './kala_envelope.js'

// ── per-clause composers ────────────────────────────────────────────────────────────

/** The thesis clause is served verbatim (trimmed) — it is already the caller's most
 *  carefully-composed sentence; this function exists so every call site goes through the
 *  same normalization (trim) rather than each facade trimming ad hoc. */
export function composeThesis(reading: ArgumentReading): string {
  return reading.thesis.trim()
}

const STRENGTH_CLAUSE: Record<NonNullable<ArgumentEvidence['strength']>, string> = {
  strong: ' — strong evidence',
  moderate: ' — moderate evidence',
  weak: ' — weak evidence',
}

/** One evidence driver → one sentence. Fact-id count is stated explicitly (never just
 *  "supported by facts") so a caller reading only the composed text still gets a
 *  groundedness signal; an evidence row with zero fact_ids is composed HONESTLY as
 *  uncited, never silently smoothed over (B.10 / §N.7 narration-fidelity discipline —
 *  a sentence must trace to what it cites, not imply a citation that isn't there). */
export function composeEvidenceSentence(evidence: ArgumentEvidence): string {
  const strengthClause = evidence.strength ? STRENGTH_CLAUSE[evidence.strength] : ''
  const factsClause =
    evidence.fact_ids.length > 0
      ? ` (${evidence.fact_ids.length} fact${evidence.fact_ids.length === 1 ? '' : 's'}: ${evidence.fact_ids.join(', ')})`
      : ' (uncited)'
  return `${evidence.claim.trim()}${strengthClause}${factsClause}`
}

/** One dissent row → one sentence, always naming its source system so disagreement reads
 *  as intelligence, not noise (Elevation §0 vision property 4). */
export function composeDissentSentence(dissent: ArgumentDissent): string {
  const factsClause =
    dissent.fact_ids.length > 0
      ? ` (${dissent.fact_ids.length} fact${dissent.fact_ids.length === 1 ? '' : 's'})`
      : ' (uncited)'
  return `${dissent.source.trim()} dissents: ${dissent.claim.trim()}${factsClause}`
}

const VERDICT_TIER_LABEL: Record<ArgumentVerdictTier, string> = {
  structural_prior: 'structural prior — pre-calibration',
  calibrated_provisional: 'calibrated (provisional)',
  calibrated: 'calibrated',
  unresolved: 'unresolved',
}

/** The verdict clause always states its own calibration tier inline — never a bare
 *  percentage or unqualified claim (LAW ZERO: tiers, not fake percentages). */
export function composeVerdictSentence(verdict: ArgumentVerdict): string {
  return `${verdict.statement.trim()} [tier: ${VERDICT_TIER_LABEL[verdict.tier]}]`
}

/** `null` falsifier composes to `null` (not an empty string / placeholder sentence) — an
 *  honest absence must stay absent all the way through composition, never papered over
 *  with filler prose (the specificity-gate class of defect this campaign explicitly
 *  guards against, Elevation §5 E3). */
export function composeFalsifierSentence(falsifier: ArgumentFalsifier | null): string | null {
  if (!falsifier) return null
  const byClause = falsifier.resolves_by ? ` (resolves by ${falsifier.resolves_by})` : ' (open-ended)'
  return `Falsified if: ${falsifier.statement.trim()}${byClause}`
}

// ── coverage / freshness prose (honest-empty / not_in_corpus / staleness) ──────────

/** Renders one 3-state coverage entry as a sentence. `computed` entries compose to a
 *  short positive statement; `honest_empty`/`not_in_corpus` entries ALWAYS carry their
 *  reason in the composed text — an entry missing its reason composes to an explicit
 *  placeholder rather than silently dropping the gap (B.10: never fabricate, and never
 *  silently omit an honest gap either). */
export function composeCoverageSentence(entry: KalaCoverageEntry): string {
  switch (entry.state) {
    case 'computed':
      return `${entry.concept}: computed.`
    case 'honest_empty':
      return `${entry.concept}: honestly empty — ${entry.reason ?? '(no reason recorded — composer defect)'}.`
    case 'not_in_corpus':
      return `${entry.concept}: not in corpus — ${entry.reason ?? '(no reason recorded — composer defect)'}.`
  }
}

/** Renders a freshness attestation as a sentence; staleness is always stated, never
 *  silently dropped from the composed text (kills the LC-5 class at the prose layer too,
 *  not just in the raw envelope field).
 *
 *  SAMĀPTI A7-N8-AUDIT F-20: three-state, matching `KalaFreshness.stale`. The former
 *  `if (!freshness.stale)` collapsed `null` (staleness NOT DETERMINABLE) into the same
 *  branch as `false` (checked, and current) and asserted the literal prose
 *  "Freshness: current." — an affirmative freshness claim with no horizon behind it.
 *  `null` now renders as an honest UNKNOWN carrying its reason, exactly as
 *  `composeCoverageSentence` above renders `honest_empty` / `not_in_corpus`. */
export function composeFreshnessSentence(freshness: KalaFreshness): string {
  if (freshness.stale === null || freshness.stale === undefined) {
    return `Freshness: UNKNOWN — ${freshness.stale_reason ?? '(no reason recorded — composer defect)'}.`
  }
  if (freshness.stale === false) return 'Freshness: current.'
  return `Freshness: STALE — ${freshness.stale_reason ?? '(no reason recorded — composer defect)'}.`
}

// ── the whole argument, composed ────────────────────────────────────────────────────

export interface ComposedArgument {
  thesis_sentence: string
  evidence_sentences: string[]
  dissent_sentences: string[]
  verdict_sentence: string
  falsifier_sentence: string | null
  /** All clauses joined into one served block, in argument order: thesis → evidence →
   *  dissent → verdict → falsifier (Elevation §5 E3's canonical order). Falsifier is
   *  omitted from the joined text (not from the structured field above) when `null` —
   *  an honestly-absent falsifier does not get a "no falsifier stated" filler sentence,
   *  per the specificity-gate discipline (filler that doesn't vary by chart fails CI). */
  full_text: string
}

/**
 * Composes a complete `ArgumentReading` into served text. This is the ONE function every
 * kala_* tool facade calls to turn its computed reading into prose — "one voice, one
 * gate" (E7.4). Deterministic: identical `reading` in ⇒ identical `ComposedArgument` out,
 * every time (see argument_composer.test.ts's determinism assertion).
 */
export function composeArgument(reading: ArgumentReading): ComposedArgument {
  const thesis_sentence = composeThesis(reading)
  const evidence_sentences = reading.evidence.map(composeEvidenceSentence)
  const dissent_sentences = reading.dissent.map(composeDissentSentence)
  const verdict_sentence = composeVerdictSentence(reading.verdict)
  const falsifier_sentence = composeFalsifierSentence(reading.falsifier)

  const clauses = [thesis_sentence, ...evidence_sentences, ...dissent_sentences, verdict_sentence]
  if (falsifier_sentence) clauses.push(falsifier_sentence)

  return {
    thesis_sentence,
    evidence_sentences,
    dissent_sentences,
    verdict_sentence,
    falsifier_sentence,
    full_text: clauses.filter((clause) => clause.length > 0).join(' '),
  }
}
