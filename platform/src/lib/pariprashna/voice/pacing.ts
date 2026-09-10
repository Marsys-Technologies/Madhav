/**
 * pariprashna/voice/pacing.ts — lane G3-D / P2-L (PPR-04, roadmap line 104).
 *
 * Two small, pure helpers the pacing policy needs beyond `voice_lint.ts`'s
 * text-level checks:
 *
 *  · `isDifficultFindingActive` — the honest "difficult finding" proxy. No
 *    per-block difficulty classifier exists in this codebase (see
 *    `voice_lint.ts`'s header for what was checked and ruled out:
 *    `semantics/block_classifier.ts`'s `WireReadingRole` has no such notion,
 *    and no typed-confidence lane had landed in this worktree's base at the
 *    time this lane was built — verified via `git log --oneline origin/main`
 *    turning up no confidence-tier work). The real, already-wired signal this
 *    lane uses instead is the turn's own G1-A `SafetyDecision`: an HS-class
 *    genuinely fired for THIS turn. Coarser than block-level (turn-scoped, not
 *    per-block) — disclosed here rather than hidden behind a narrower-sounding
 *    claim (CLAUDE.md §N.8).
 *
 *  · `shouldForceDifficultBlockBreak` — "shorter committed blocks" for
 *    difficult findings, implemented as a STRUCTURAL behavior (an early,
 *    sentence-boundary-respecting `commitBlock()` in `synthesis_stage.ts`'s
 *    streaming loop) rather than a text-lint check, because block segmentation
 *    is not something a text-scanning lint can express — it is a decision
 *    about when the assembler closes the currently-open block. Purely a
 *    BLOCK-granularity effect: it never touches `passId` or emits a seam, so
 *    it cannot violate the file's own documented PASS/SEAM TRUTH invariant
 *    ("a pass boundary is derived purely from the engine's own control flow").
 *    This is the server-side half of "one affordance away" (PPR-04 / roadmap
 *    line 104): keeping a difficult-finding block terse is what lets a future
 *    client (G3-E) offer an expand affordance instead of the server inlining
 *    the full detail inline; no UI is built by this lane.
 */

import type { SafetyDecision } from '@/lib/pariprashna/safety'

/**
 * A committed prose block in a difficult-finding context is force-closed once
 * it crosses this length AND sits at a sentence boundary — chosen to keep a
 * committed block roughly paragraph-sized (a few sentences) rather than
 * accumulating an entire multi-paragraph difficult-finding answer into one
 * block.
 */
export const DIFFICULT_BLOCK_MAX_CHARS = 420

const SENTENCE_END = /[.!?]["')\]]?\s*$/

/**
 * True once an open block's accumulated text has crossed the difficult-finding
 * length floor AND ends at a sentence boundary — so a forced break never lands
 * mid-sentence. Pure and side-effect-free; the caller (`synthesis_stage.ts`)
 * decides what to do with the answer (call `assembler.commitBlock()`).
 */
export function shouldForceDifficultBlockBreak(blockTextSoFar: string): boolean {
  return blockTextSoFar.length >= DIFFICULT_BLOCK_MAX_CHARS && SENTENCE_END.test(blockTextSoFar)
}

/**
 * The honest "difficult finding" proxy: this turn's G1-A safety classification
 * actually enforced AND at least one HS-class actually fired. `enforced:
 * false` (the flag-off value, per `SafetyDecision`'s own doc comment) and an
 * empty `classes_detected` (enforced, but nothing fired) both correctly read
 * as "not difficult" — this is never true by omission.
 */
export function isDifficultFindingActive(
  safetyDecision?: Pick<SafetyDecision, 'enforced' | 'classes_detected'>,
): boolean {
  return Boolean(safetyDecision?.enforced && (safetyDecision.classes_detected?.length ?? 0) > 0)
}
