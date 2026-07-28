/**
 * Honest grounding-grade rollup for a turn's `GroundingSummary.gradeSummaryLabel`.
 *
 * ── Why this exists (PB-1/integrate hardening) ───────────────────────────────
 * The live adapter (`s1LiveAdapter.ts`) and the dev fixture-playback adapter
 * (`c2ProtocolAdapter.ts`) both synthesize the turn's grounding summary
 * client-side (S-1's `turn.commit` carries persistence metadata, NOT a grounding
 * rollup). Both previously derived the confident chip label from mere citation
 * COUNT — `citationsSeen > 0 ? 'Core claim: WELL-GROUNDED' : …` — which asserts a
 * WELL-GROUNDED verdict on the strength of a SINGLE citation of ANY grade. That
 * is a fabricated confident verdict: exactly the overclaiming this instrument
 * exists to prevent (CLAUDE.md B.1 facts/interpretation separation, B.10 no
 * fabricated claim, and the §6.7 "never fabricated" grade-chip rule of
 * `PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md`).
 *
 * ── What we do instead ───────────────────────────────────────────────────────
 * Each `citation.define` on the stream already carries S-3's per-citation grade
 * (`CitationDefineEvent.grade`, mapped to C-1's `Grade`). We tally the ACTUAL
 * distribution of resolved grades and derive the core-claim label HONESTLY from
 * that distribution — never from the count alone:
 *
 *   • WELL-GROUNDED  — at least one `confirmed` citation AND zero weak
 *                       (`catalog`/`honest_gap`) citations. The whole grounding
 *                       set is strong.
 *   • SUPPORTED      — some strong grounding exists (≥1 confirmed/supported) but
 *                       it is mixed with weaker rows, OR it is supported-only
 *                       with nothing confirmed. Honestly partial.
 *   • CATALOG-ONLY — UNVERIFIED — every citation is a catalog/label match awaiting
 *                       cross-verification, i.e. NO strong grade resolved. This is
 *                       ALSO where an unverified single citation lands, and where a
 *                       stream that carried no grade at all lands (S-1's `grade` is
 *                       optional; the mapper defaults an absent grade to `catalog`).
 *                       We therefore NEVER show a confident verdict for data we
 *                       could not verify.
 *   • HONEST GAP     — no citations at all: the chart was silent, verified.
 *
 * The §6.7 chip vocabulary (`WELL-GROUNDED` / `SUPPORTED` / `CATALOG-ONLY —
 * UNVERIFIED` / `HONEST GAP`) is the single source of truth for these labels.
 */

import type { Grade } from './types'

/** Running tally of resolved per-citation grades for one turn. */
export interface GradeTally {
  confirmed: number
  supported: number
  catalog: number
  honest_gap: number
}

export function emptyGradeTally(): GradeTally {
  return { confirmed: 0, supported: 0, catalog: 0, honest_gap: 0 }
}

/** Record one resolved citation grade into the tally (mutates in place). */
export function tallyGrade(tally: GradeTally, grade: Grade): void {
  tally[grade] += 1
}

export const GRADE_SUMMARY_WELL_GROUNDED = 'Core claim: WELL-GROUNDED'
export const GRADE_SUMMARY_SUPPORTED = 'Core claim: SUPPORTED'
export const GRADE_SUMMARY_CATALOG_ONLY = 'Core claim: CATALOG-ONLY — UNVERIFIED'
export const GRADE_SUMMARY_HONEST_GAP = 'Honest gap — silence verified across consulted factors.'

/**
 * Derive the honest `gradeSummaryLabel` for a turn from its ACTUAL grade
 * distribution. Never returns a confident label on the strength of count alone.
 */
export function rollUpGradeSummaryLabel(tally: GradeTally): string {
  const total = tally.confirmed + tally.supported + tally.catalog + tally.honest_gap
  if (total === 0) return GRADE_SUMMARY_HONEST_GAP

  const strong = tally.confirmed + tally.supported
  const weak = tally.catalog + tally.honest_gap

  // WELL-GROUNDED requires an actual confirmed anchor AND no weaker/unverified
  // rows dragging the claim down. A single catalog/unverified row disqualifies it.
  if (tally.confirmed > 0 && weak === 0) return GRADE_SUMMARY_WELL_GROUNDED

  // Some verified support exists, but the set is mixed or supported-only.
  if (strong > 0) return GRADE_SUMMARY_SUPPORTED

  // Nothing resolved to a strong grade — do NOT assert confidence.
  return GRADE_SUMMARY_CATALOG_ONLY
}
