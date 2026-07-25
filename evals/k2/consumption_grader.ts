#!/usr/bin/env tsx
/**
 * evals/k2/consumption_grader.ts — Lane K2 item 1 (EL-04, EL-05, EL-23).
 *
 * Post-hoc grader over ANY captured sealed-harness transcript (evals/omega7/harness_runs/*.json
 * shape, or the richer {calls, final_answer, ...} shape — see types.ts). Computes three
 * first-class grading dimensions the standing battery was missing per EL-23:
 *
 *   (a) consumption_ratio      — servable concepts (Ω3 "served" state, per domain×chart) that
 *                                 were actually surfaced in this transcript / total servable.
 *   (b) accounting_completeness — did the final answer HONESTLY report its own coverage, or
 *                                 claim completeness without evidence (the EL-07/EL-23 false-
 *                                 confidence pattern)?
 *   (c) volunteered_findings_count — how many of the chart's own top-N chart-defining findings
 *                                 (EL-05) were surfaced UNPROMPTED (any naive-question answer
 *                                 counts, by construction of the sealed harness's one-turn
 *                                 naive user message).
 *
 * This does NOT replace the sealed harness's own mechanical concept-hit grader (§2 of
 * SEALED_EVALUATOR_HARNESS_v1_0.md, frozen, scored against the harness's smaller
 * required_concepts list). It is the BROADER Ω3-scale accounting the charter asks K2 to add as
 * a first-class grading dimension alongside it — same matching discipline (tool called AND
 * fact_id/token found in the raw result), reused against the full per-domain concept universe.
 *
 * Usage:
 *   npx tsx evals/k2/consumption_grader.ts <transcript.json> <domain> <chart_id> [--final-answer <file>]
 *
 * Library usage: import { gradeConsumption } from './consumption_grader.js'
 */
import { readFileSync } from 'fs'
import { loadAccounting, loadTranscript, resultTextByTool, bareToolName } from './transcript_utils.js'
import type { AccountingRow, NormalizedTranscript } from './types.js'

// ─────────────────────────────────────────────────────────────────────────────
// (a) consumption_ratio
// ─────────────────────────────────────────────────────────────────────────────

export interface ConceptHitResult {
  concept_id: string
  hit: boolean
  reason: 'tool_never_called' | 'substance_absent' | 'hit' | 'no_evidence_on_record'
}

/**
 * Faithful to the sealed harness's own matching discipline (§2): a servable concept is a HIT
 * iff its serving tool was actually called in the transcript AND at least one of its evidence
 * fact_ids (or, absent fact_ids, the concept_id's own distinguishing suffix) appears verbatim
 * in that tool's raw result text. Partial credit does not exist at the per-concept level.
 */
export function scoreConceptHits(
  rows: AccountingRow[],
  transcript: NormalizedTranscript,
): ConceptHitResult[] {
  const byTool = resultTextByTool(transcript.calls)
  const calledTools = new Set(transcript.calls.map((c) => bareToolName(c.tool)))

  return rows.map((row): ConceptHitResult => {
    const tool = row.evidence?.tool ? bareToolName(row.evidence.tool) : undefined
    if (!tool) return { concept_id: row.concept_id, hit: false, reason: 'no_evidence_on_record' }
    if (!calledTools.has(tool)) {
      return { concept_id: row.concept_id, hit: false, reason: 'tool_never_called' }
    }
    const resultText = byTool.get(tool) ?? ''
    const factIds = row.evidence?.fact_ids ?? []
    const distinguishingToken = row.concept_id.split('.').pop() ?? row.concept_id
    const hit =
      (factIds.length > 0 && factIds.some((fid) => resultText.includes(fid))) ||
      (factIds.length === 0 && resultText.includes(distinguishingToken))
    return { concept_id: row.concept_id, hit, reason: hit ? 'hit' : 'substance_absent' }
  })
}

export interface ConsumptionRatioResult {
  domain: string
  chart_id: string
  servable_total: number
  surfaced_count: number
  consumption_ratio: number
  misses: ConceptHitResult[]
}

export function computeConsumptionRatio(
  domain: string,
  chartId: string,
  transcript: NormalizedTranscript,
): ConsumptionRatioResult {
  const accounting = loadAccounting(domain, chartId)
  const servable = accounting.rows.filter((r) => r.state === 'served')
  const hits = scoreConceptHits(servable, transcript)
  const surfaced = hits.filter((h) => h.hit)
  return {
    domain,
    chart_id: chartId,
    servable_total: servable.length,
    surfaced_count: surfaced.length,
    consumption_ratio: servable.length > 0 ? surfaced.length / servable.length : 0,
    misses: hits.filter((h) => !h.hit),
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// (b) accounting_completeness — honesty of the answer's own coverage claim
// ─────────────────────────────────────────────────────────────────────────────

const COMPLETENESS_CLAIM_PATTERNS = [
  /\bcomplete(ly)?\b/i,
  /\bfull(y)? (analysis|picture|reading|coverage|depth)\b/i,
  /\bcomprehensive\b/i,
  /\bevery (aspect|angle|factor|concept)\b/i,
  /\ball (aspects|factors|angles|relevant (data|signals))\b/i,
  /\bnothing (was )?missed\b/i,
  /\bexhaustive\b/i,
]

const HONEST_GAP_PATTERNS = [
  /\bnot (computed|found|available|in your data)\b/i,
  /\bno data\b/i,
  /\b(did not|didn't) (check|query|consult)\b/i,
  /\blimited to\b/i,
  /\bunable to verify\b/i,
  /\bhonest(ly)? (gap|empty|absence)\b/i,
  /\bempty_reason\b/i,
  /\bnot yet (computed|implemented)\b/i,
  /\bnot surfaced\b/i,
  /\bnot in what I queried\b/i,
]

const EVIDENCE_BASIS_PATTERNS = [
  /\b\d+\s*(of|\/)\s*\d+\b/, // "12 of 15", "12/15"
  /\b\d{1,3}(\.\d+)?%\b/, // "82%" — explicit ratio
  /\bconsumption[_ ]ratio\b/i,
  /\bcoverage\b.*\b\d/i,
]

export type CompletenessVerdict =
  | 'HONEST_COMPLETENESS_CLAIM' // claims completeness AND backs it with an evidenced figure
  | 'FALSE_COMPLETENESS_CLAIM' // claims completeness with no evidence, while real ratio is low
  | 'HONEST_GAP' // does not overclaim; explicitly reports what it did not cover
  | 'UNSTATED' // neither claims completeness nor reports a gap — not gradeable either way

export interface AccountingCompletenessResult {
  verdict: CompletenessVerdict
  score: number // 0..1
  claims_completeness: boolean
  reports_gap: boolean
  evidence_based: boolean
  matched_claim_phrases: string[]
  matched_gap_phrases: string[]
}

/**
 * Honesty check, not a quality check: a response that says "I did not check dispositor chains"
 * scores BETTER here than one that says "this is a complete analysis" with no receipt, even if
 * the latter happens to have a higher raw consumption_ratio. This is deliberate — EL-23's whole
 * point is that "excellent for its scope" must not be conflatable with "complete against the
 * corpus," and DARPANA's own §8.4 honesty-balance read wants HONEST_GAP > 0, FALSE claims = 0.
 */
export function computeAccountingCompleteness(
  finalAnswer: string,
  actualConsumptionRatio: number | null,
): AccountingCompletenessResult {
  const matched_claim_phrases = COMPLETENESS_CLAIM_PATTERNS.filter((p) => p.test(finalAnswer)).map((p) => p.source)
  const matched_gap_phrases = HONEST_GAP_PATTERNS.filter((p) => p.test(finalAnswer)).map((p) => p.source)
  const claims_completeness = matched_claim_phrases.length > 0
  const reports_gap = matched_gap_phrases.length > 0
  const evidence_based = EVIDENCE_BASIS_PATTERNS.some((p) => p.test(finalAnswer))

  let verdict: CompletenessVerdict
  let score: number
  const ratioLooksIncomplete = actualConsumptionRatio !== null && actualConsumptionRatio < 0.9

  if (claims_completeness && !evidence_based && ratioLooksIncomplete) {
    verdict = 'FALSE_COMPLETENESS_CLAIM'
    score = 0
  } else if (claims_completeness && evidence_based) {
    verdict = 'HONEST_COMPLETENESS_CLAIM'
    score = 1
  } else if (reports_gap) {
    verdict = 'HONEST_GAP'
    score = 1
  } else if (!claims_completeness) {
    verdict = 'UNSTATED'
    score = 0.5
  } else {
    // Claims completeness, no evidence, but we don't have a ratio to contradict it against —
    // treat as unstated-but-risky rather than fabricating a FALSE verdict without proof.
    verdict = 'UNSTATED'
    score = 0.5
  }

  return { verdict, score, claims_completeness, reports_gap, evidence_based, matched_claim_phrases, matched_gap_phrases }
}

// ─────────────────────────────────────────────────────────────────────────────
// (c) volunteered_findings_count — EL-05
// ─────────────────────────────────────────────────────────────────────────────

/** A single chart-defining finding, with alias spellings collapsed under ONE canonical label so
 * a denominator never double-counts "Śaśa Yoga" and "Shasha Yoga" as two distinct findings. */
export interface FindingRef {
  canonical: string
  aliases?: string[]
}

const F = (canonical: string, ...aliases: string[]): FindingRef => ({ canonical, aliases })

/**
 * The chart's own top-N chart-defining findings (verbatim from `reading_notes_get`'s verified
 * CR-38/71/80 content for the native chart 482012f1 — see evals/k2/reading_notes_accretion_check.ts
 * for the live-tool cross-check). Callers grading a different chart should pass their own
 * `topFindings` list; this default exists so the grader is runnable out of the box against the
 * native chart's flagship domains without requiring a second lookup pass.
 */
export const DEFAULT_TOP_FINDINGS_482012F1: Record<'wealth' | 'career', FindingRef[]> = {
  wealth: [
    F('Dhana Yoga'),
    F('Śaśa Yoga', 'Shasha Yoga', 'Sasha Yoga'),
    F('Budha-Āditya', 'Budha-Aditya', 'Budhaditya'),
    F('wealth-loss mechanism', 'H2 wealth-loss', 'wealth loss mechanism'),
    F('Arudha Lagna', 'AL in H9'),
    F('Neecha-Bhaṅga', 'Neecha Bhanga', 'Neecha-Bhanga', 'debilitation cancellation'),
    F('Indu Lagna', 'Dhana lagna'),
    F('Kāla-Sarpa', 'Kala Sarpa', 'Kaal Sarp'),
    F('Anapha Yoga'),
    F('Kemadruma'),
    F('Ketu Mahadasha', 'Ketu MD', 'Ketu Mahādaśā'),
    F('Venus Mahadasha', 'Venus MD', 'Venus Mahādaśā'),
  ],
  career: [
    F('Śaśa Yoga', 'Shasha Yoga', 'Sasha Yoga'),
    F('10th lord', '10L', 'tenth lord'),
    F('Budha-Āditya', 'Budha-Aditya', 'Budhaditya'),
    F('Karakāṁśa', 'Karakamsha', 'Karakansha'),
    F('Arudha Lagna'),
    F('Dasha spine', 'dasha sequence'),
    F('Mercury Mahadasha', 'Mercury MD'),
    F('Ketu Mahadasha', 'Ketu MD'),
    F('special lagnas', 'special lagna'),
  ],
}

export interface VolunteeredFindingsResult {
  reference_findings_count: number
  volunteered_findings_count: number
  volunteered_findings: string[]
  volunteering_ratio: number
}

function stripDiacritics(s: string): string {
  return s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

export function computeVolunteeredFindings(
  finalAnswer: string,
  topFindings: FindingRef[],
): VolunteeredFindingsResult {
  const haystack = stripDiacritics(finalAnswer)
  const volunteered: string[] = []
  for (const finding of topFindings) {
    const labels = [finding.canonical, ...(finding.aliases ?? [])]
    const found = labels.some(
      (label) => finalAnswer.toLowerCase().includes(label.toLowerCase()) || haystack.includes(stripDiacritics(label)),
    )
    if (found) volunteered.push(finding.canonical)
  }
  return {
    reference_findings_count: topFindings.length,
    volunteered_findings_count: volunteered.length,
    volunteered_findings: volunteered,
    volunteering_ratio: topFindings.length > 0 ? volunteered.length / topFindings.length : 0,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Combined grade
// ─────────────────────────────────────────────────────────────────────────────

export interface K2ConsumptionGrade {
  domain: string
  chart_id: string
  consumption: ConsumptionRatioResult
  accounting_completeness: AccountingCompletenessResult
  volunteered_findings: VolunteeredFindingsResult
}

export function gradeConsumption(
  domain: string,
  chartId: string,
  transcript: NormalizedTranscript,
  finalAnswer: string,
  topFindings?: string[],
): K2ConsumptionGrade {
  const consumption = computeConsumptionRatio(domain, chartId, transcript)
  const accounting_completeness = computeAccountingCompleteness(finalAnswer, consumption.consumption_ratio)
  const findings =
    topFindings ??
    DEFAULT_TOP_FINDINGS_482012F1[domain as 'wealth' | 'career'] ??
    []
  const volunteered_findings = computeVolunteeredFindings(finalAnswer, findings)
  return { domain, chart_id: chartId, consumption, accounting_completeness, volunteered_findings }
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────

function isMain(): boolean {
  return process.argv[1] != null && import.meta.url === `file://${process.argv[1]}`
}

if (isMain()) {
  const [transcriptPath, domain, chartId, ...rest] = process.argv.slice(2)
  if (!transcriptPath || !domain || !chartId) {
    console.error(
      'Usage: npx tsx evals/k2/consumption_grader.ts <transcript.json> <domain> <chart_id> [--final-answer <file>]',
    )
    process.exit(1)
  }
  const faFlag = rest.indexOf('--final-answer')
  const finalAnswer = faFlag >= 0 ? readFileSync(rest[faFlag + 1], 'utf-8') : ''
  const transcript = loadTranscript(transcriptPath)
  if (!finalAnswer && !transcript.final_answer) {
    console.warn(
      'WARNING: no final_answer text available (transcript has no final_answer field and ' +
        '--final-answer was not passed). accounting_completeness and volunteered_findings will ' +
        'both score against an empty string — consumption_ratio (tool-substance based) is still valid.',
    )
  }
  const grade = gradeConsumption(domain, chartId, transcript, finalAnswer || transcript.final_answer || '')
  console.log(JSON.stringify(grade, null, 2))
}
