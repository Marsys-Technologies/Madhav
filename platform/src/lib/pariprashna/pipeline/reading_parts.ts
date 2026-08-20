/**
 * Paripraśna pipeline — SEMANTIC READING PARTS (P0-C / RF-1).
 *
 * Port: `SemanticReadingParts`. This is the reading's own vocabulary, shared by
 * the two stages that produce and persist it — the synthesis stage opens,
 * fills and commits blocks through the assembler here, and the persistence
 * stage turns the committed blocks into canonical `message_parts` through
 * `buildCanonicalParts` here. It is a value module, not a stage: it performs no
 * I/O of its own beyond the emitter writes the pre-decomposition closure did.
 *
 * The assembler is a faithful port of the route's block state machine:
 *   · `blockCounter` is turn-global, NOT per-pass — block ids stay
 *     `blk-<passId>-<n>` with `n` monotonically increasing across passes.
 *   · A role change commits the open block before opening the new one.
 *   · `accumulatedText` accumulates ONLY scrubbed prose deltas — thinking text
 *     never enters it, and therefore never reaches persistence or the citation
 *     gate. That asymmetry is deliberate and is preserved exactly.
 *
 * Gate 11 [integrity]: `commitBlock` runs the whole-block register-leak lint as
 * the backstop for a leak pattern split across a delta-chunk boundary (the
 * per-delta lint in the synthesis stage is the first line). A hit is scrubbed
 * and flagged; it NEVER fails the turn.
 */

import { extractCitations } from '@/lib/citations/citation_data_part'
import { detectPredictionCandidates, type PredictionCandidate } from '@/lib/ppl/prediction_detector'
import { lintReaderProse } from '@/lib/pariprashna/citations/register_leak_lint'
import {
  scanMortalityPhrasing,
  type PreWireSentenceRule,
} from '@/lib/pariprashna/safety/phrasing_scan'
import { classifyCommittedBlock } from '@/lib/pariprashna/semantics/block_classifier'
import type { MessagePartInput } from '@/lib/pariprashna/store/schema'
import {
  textPartFromBlock,
  citationPartFromDetection,
  predictionCandidatePartFromDetection,
} from '@/lib/pariprashna/store/route_writer_adapter'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

export type BlockRole = 'prose' | 'thinking'

export interface OpenBlock {
  id: string
  role: BlockRole
  text: string
}

/** The score floor a detected prediction candidate must reach to be persisted. */
export const PREDICTION_SCORE_FLOOR = 0.5

/**
 * The route's block/commit state machine, lifted verbatim. `passId` is public
 * and mutable because the synthesis stage advances it on a real control-flow
 * pass boundary and the next `ensureBlock` must mint an id in the new pass.
 */
export class ReadingPartsAssembler {
  passId: number
  private blockCounter = 0
  private currentBlock: OpenBlock | null = null
  private accumulated = ''
  readonly committedBlocks: OpenBlock[] = []

  constructor(
    private readonly em: PariprashnaEmitter,
    initialPassId: number,
    /**
     * Lane G1-A. When true, `commitBlock` runs the HS-1 mortality-phrasing scan
     * over the whole block as the backstop to the streaming scanner. Default
     * false so every pre-existing caller (and the flag-OFF path) is byte-for-byte
     * unchanged.
     */
    private readonly mortalityScanEnabled = false,
    /**
     * Lane G1-G. Extra pre-wire sentence rules — today, the answer-side
     * entitlement scan — folded into the SAME commit-time pass. Default empty
     * so every pre-existing caller (and the flag-OFF path) is byte-for-byte
     * unchanged.
     *
     * Independent of `mortalityScanEnabled` on purpose: the two are armed by
     * two different feature flags, and `scanMortalityPhrasing`'s
     * `mortalityRulesEnabled` option is what keeps one from silently arming the
     * other when only this one is populated.
     */
    private readonly preWireExtraRules: readonly PreWireSentenceRule[] = [],
    /**
     * Lane P2-A (G2-A). When true, `commitBlock` runs the deterministic
     * commit-time semantic classifier over every PROSE block and carries its
     * `kind`/`role`/`content`/`table`/`gap_text` on the `block.commit` event.
     * Default false so every pre-existing caller (and the flag-OFF path) is
     * byte-for-byte unchanged — the event carries exactly `{ block_id, text }`,
     * same as before this lane.
     */
    private readonly semanticBlocksEnabled = false,
  ) {
    this.passId = initialPassId
  }

  /** The pass id of the last PROSE block this assembler committed — `-1`
   *  before any prose has committed. Used only when `semanticBlocksEnabled`
   *  is true, to derive the structural "is this the first prose block of its
   *  pass" signal `classifyRole` needs, without any external wiring change:
   *  `passId` is already advanced by the synthesis stage on a real pass
   *  boundary (see synthesis_stage.ts), so comparing against it here is
   *  self-contained. */
  private lastProsePassSeen = -1

  /** Every scrubbed PROSE delta, concatenated. Thinking text is excluded. */
  get accumulatedText(): string {
    return this.accumulated
  }

  /**
   * Keep `accumulated` in step with a block whose text a pre-wire scan changed.
   *
   * `appendProse` writes each delta into BOTH the open block and `accumulated`,
   * so a commit-time redaction that only rewrote `currentBlock.text` left a
   * SECOND, unredacted copy behind — and `accumulated` is not a scratch buffer:
   * it is what feeds the citation extractor, the prediction-candidate detector
   * and persistence. A redaction that reaches the reader's copy but not the
   * persisted one is not a redaction.
   *
   * The replacement is anchored to the block's own text rather than done
   * globally, so an identical sentence elsewhere in the turn is untouched. The
   * anchor is always the block's RAW text — see `commitBlock` for why the
   * register-leak lint's own rewrite must never be the anchor and must never be
   * the replacement.
   */
  private syncAccumulated(before: string, after: string): void {
    if (before === after || !before) return
    const at = this.accumulated.lastIndexOf(before)
    if (at === -1) return
    this.accumulated =
      this.accumulated.slice(0, at) + after + this.accumulated.slice(at + before.length)
  }

  commitBlock(): void {
    if (this.currentBlock) {
      // The RAW deltas this block contributed. This — NOT the post-lint text —
      // is the copy sitting in `accumulated`, because `appendProse` writes the
      // delta into both places and nothing downstream of it rewrites
      // `accumulated`. It is the only correct anchor for `syncAccumulated`.
      const rawBlockText = this.currentBlock.text
      // Gate 11 [integrity] backstop: every prose block is scanned for internal
      // identifier leaks (SIG.* ids, asset-id prefixes, register acronyms
      // MSR/UCN/CGM/CDLM/LEL, table names) before it ever reaches the wire or
      // the canonical store — the model's own prose can and does reference
      // these terms directly (confirmed in production), independent of the
      // citation-sentinel path. Never fails the turn; hits are
      // rewritten/redacted and reported as a telemetry flag.
      if (this.currentBlock.role === 'prose') {
        const lint = lintReaderProse(this.currentBlock.text)
        if (lint.leakCount > 0) {
          this.currentBlock.text = lint.clean
          this.em.flag({
            code: 'register_leak_scrubbed',
            level: 'warn',
            detail: `${lint.leakCount} internal identifier(s) scrubbed from reader prose`,
          })
        }
        // HS-1 point (c) BACKSTOP (lane G1-A). The streaming scanner in
        // `synthesis_stage.ts` is the first line and already works on whole
        // sentences; this catches the case it structurally cannot — a whole
        // block assembled by a path that did not go through the scanner
        // (clarification prose, a future non-streaming composer). It scrubs the
        // COMMITTED and PERSISTED text, which is the copy the reader can come
        // back to. Armed only when the gate is on; a pass-through otherwise.
        //
        // Lane G1-G folds the answer-side entitlement rules into this SAME
        // commit-time scan rather than adding a second walk over the block. The
        // reason it matters here specifically: this is the copy that gets
        // PERSISTED, so a foreign chart id surviving to this point would live in
        // `message_parts` for as long as the conversation does, long after the
        // stream that carried it is gone.
        if (this.mortalityScanEnabled || this.preWireExtraRules.length > 0) {
          const scanOptions = {
            extraRules: this.preWireExtraRules,
            mortalityRulesEnabled: this.mortalityScanEnabled,
          }
          // Captured AFTER the lint, so it is what the scans actually saw.
          const textBeforeScans = this.currentBlock.text
          const scan = scanMortalityPhrasing(this.currentBlock.text, scanOptions)
          if (scan.hits.length > 0 || scan.scan_failed) {
            this.currentBlock.text = scan.clean
            this.em.flag({
              code: 'safety_prewire_mortality_redacted',
              level: 'error',
              detail: scan.scan_failed
                ? 'the pre-wire mortality scan errored on commit; the block was withheld (fail-closed)'
                : `${scan.hits.length} sentence(s) withheld from the committed block`,
            })
          }
          const entitlementRedactions = scan.extra_hits.filter((h) => h.caused_redaction)
          if (entitlementRedactions.length > 0) {
            // `scan.clean` already has BOTH classes removed, so this assignment
            // is idempotent with the one above and correct when only this class
            // fired. Server log carries the rule ids and span hashes; the wire
            // gets a count (gate 11 [integrity]).
            this.currentBlock.text = scan.clean
            console.error(
              '[pariprashna/injection] PRE-WIRE entitlement leak redacted from a COMMITTED block:',
              entitlementRedactions.map((h) => ({ rule: h.rule, span: h.redacted_span_hash })),
            )
            this.em.flag({
              code: 'injection_entitlement_leak_redacted',
              level: 'error',
              detail: `${entitlementRedactions.length} sentence(s) referencing an unauthorized chart withheld from the committed block`,
            })
          }
          // Whatever the two pre-wire classes above removed, remove from the
          // turn's accumulated text too — see `syncAccumulated`. Applies to the
          // mortality branch as well as the entitlement one: the gap was there
          // for both, and fixing it for only the newer one would leave the
          // older, more safety-critical redaction the leakier of the two.
          //
          // ── WHY THIS SITS INSIDE THE FLAG GUARD, AND WHY THE ANCHOR IS THE
          //    RAW TEXT (P0, independent re-verification) ────────────────────
          // It used to sit outside, anchored on the text as it was BEFORE the
          // register-leak lint. That made this lane's changes visible with both
          // feature flags OFF: `lintReaderProse` is NOT gated by G1-A or G1-G —
          // it is pre-existing citation/identifier-leak lint that always runs —
          // so on any block containing a `SIG.MSR.NNN`-shaped token the lint's
          // scrub propagated into `accumulated`, which it never did before this
          // lane. `accumulated` feeds `detectTurnCitations` (persisted citation
          // parts), `detectTurnPredictionCandidates` (the SAMĪKṢĀ ledger) and
          // `runValidationStage` (the B.11 `citation_gate` grade), so a
          // production turn with no flag flipped silently lost its citation
          // parts. The lane's claim is "ships flag-OFF, zero production impact";
          // this line was the one place that was false.
          //
          // Two consequences, both load-bearing:
          //   · INSIDE the guard, so with both flags off nothing here runs and
          //     `accumulated` is byte-identical to pre-G1-G behaviour.
          //   · The anchor is `rawBlockText`, not the post-lint text, because
          //     `accumulated` holds the raw deltas. Anchoring on the post-lint
          //     text would silently no-op (`lastIndexOf` → -1) whenever the lint
          //     had fired, leaving the foreign chart id in the copy that feeds
          //     persistence — a redaction that reaches the reader but not the
          //     ledger, which is the exact defect `syncAccumulated` exists for.
          //
          // When the lint DID rewrite the block the replacement cannot simply
          // be borrowed from the scanned (linted) surface — that would carry the
          // lint's scrub into `accumulated` as a side effect, i.e. re-introduce
          // the same flag-OFF-style behaviour change one flag deeper. The
          // pre-wire scan is therefore re-run on the raw surface so the RAW copy
          // loses exactly the sentences the pre-wire classes removed, and
          // nothing else.
          if (this.currentBlock.text !== textBeforeScans) {
            const replacement = scan.scan_failed
              ? '' // fail closed: an unscannable block contributes nothing.
              : rawBlockText === textBeforeScans
                ? this.currentBlock.text
                : scanMortalityPhrasing(rawBlockText, scanOptions).clean
            this.syncAccumulated(rawBlockText, replacement)
          }
        }
      }
      // Lane P2-A (G2-A): commit-time semantic classification, PROSE blocks
      // only (a 'thinking' block is never reader-rendered and must never be
      // classified as if it were). Computed from `this.currentBlock.text`
      // AFTER the lint/pre-wire scans above, so classification runs on the
      // exact text that reaches the wire, never on a since-redacted copy.
      if (this.semanticBlocksEnabled && this.currentBlock.role === 'prose') {
        const isFirstProseInPass = this.passId !== this.lastProsePassSeen
        this.lastProsePassSeen = this.passId
        const classification = classifyCommittedBlock(this.currentBlock.text, { isFirstProseInPass })
        this.em.blockCommit({
          block_id: this.currentBlock.id,
          text: this.currentBlock.text,
          kind: classification.kind,
          role: classification.role,
          content: classification.content,
          table: classification.table,
          gap_text: classification.gapText,
        })
      } else {
        this.em.blockCommit({ block_id: this.currentBlock.id, text: this.currentBlock.text })
      }
      this.committedBlocks.push({
        id: this.currentBlock.id,
        role: this.currentBlock.role,
        text: this.currentBlock.text,
      })
      this.currentBlock = null
    }
  }

  ensureBlock(role: BlockRole): OpenBlock {
    if (this.currentBlock && this.currentBlock.role !== role) this.commitBlock()
    if (!this.currentBlock) {
      const id = `blk-${this.passId}-${++this.blockCounter}`
      this.currentBlock = { id, role, text: '' }
      this.em.blockOpen({ block_id: id, pass_id: this.passId, role })
    }
    return this.currentBlock
  }

  /** Append a scrubbed PROSE delta to both the open block and the turn text. */
  appendProse(block: OpenBlock, cleanDelta: string): void {
    block.text += cleanDelta
    this.em.blockDelta({ block_id: block.id, delta: cleanDelta })
    this.accumulated += cleanDelta
  }

  /** Append a THINKING delta — block-local only, never to `accumulatedText`. */
  appendThinking(block: OpenBlock, delta: string): void {
    block.text += delta
    this.em.blockDelta({ block_id: block.id, delta })
  }
}

export interface DetectedCitationRow {
  index: number
  signal_id: string
  layer: string
}

/**
 * The detector's own row, carried WHOLE. `offset` is not used by the canonical
 * part mapping but IS passed through to the SAMĪKṢĀ ledger capture — narrowing
 * this type would silently drop it.
 */
export type DetectedPredictionRow = PredictionCandidate

export interface CanonicalPartsInput {
  committedBlocks: readonly OpenBlock[]
  accumulatedText: string
  /** signal_id → snippet, resolved by the persistence stage's MSR reader. */
  snippets: Map<string, string>
  /**
   * Lane G2-B (P0C-R5 fix). When the live citation rewriter ran this turn
   * (`synthesis_stage.ts`'s `citationRewriteEnabled`), `accumulatedText`
   * contains resolved `[n]` markers, not raw `SIG.MSR.NNN` tokens — the
   * register-leak lint has already scrubbed/rewritten every such token before
   * it ever reached `accumulatedText`, so `detectTurnCitations` structurally
   * finds nothing on that path (the dead path this fix closes). Supplying the
   * rewriter's OWN resolution ledger here bypasses the re-scan entirely: the
   * canonical citation parts are built from what was actually resolved on the
   * wire, never re-derived from already-scrubbed prose. Omitted → falls back
   * to `detectTurnCitations(accumulatedText)`, the pre-existing behavior.
   */
  preResolvedCitations?: readonly DetectedCitationRow[]
}

export interface CanonicalPartsOutput {
  parts: MessagePartInput[]
  citations: readonly DetectedCitationRow[]
  predictionCandidates: DetectedPredictionRow[]
}

/** Citations detected in the turn's prose (pre-snippet-resolution). */
export function detectTurnCitations(accumulatedText: string): DetectedCitationRow[] {
  return extractCitations(accumulatedText).map((c) => ({
    index: c.index,
    signal_id: c.signal_id,
    layer: c.layer,
  }))
}

/** Prediction candidates at or above the persistence score floor. */
export function detectTurnPredictionCandidates(accumulatedText: string): DetectedPredictionRow[] {
  return detectPredictionCandidates(accumulatedText).filter((c) => c.score >= PREDICTION_SCORE_FLOOR)
}

/**
 * Build the canonical `message_parts` for the assistant turn, in the route's
 * own kind-grouped order: every prose text part, then every citation, then
 * every prediction candidate — with `seq` contiguous from 0.
 *
 * Only 'prose' blocks become `text` parts (`reasoning` kind is left for a
 * future lane — see route_writer_adapter.ts's header).
 */
export function buildCanonicalParts(input: CanonicalPartsInput): CanonicalPartsOutput {
  const parts: MessagePartInput[] = []
  let partSeq = 0

  for (const b of input.committedBlocks) {
    if (b.role === 'prose') {
      parts.push(textPartFromBlock({ block_id: b.id, text: b.text }, partSeq++))
    }
  }

  const citations = input.preResolvedCitations ?? detectTurnCitations(input.accumulatedText)
  for (const c of citations) {
    parts.push(
      citationPartFromDetection(
        {
          index: c.index,
          signal_id: c.signal_id,
          layer: c.layer,
          snippet: input.snippets.get(c.signal_id) ?? '',
        },
        partSeq++,
      ),
    )
  }

  const predictionCandidates = detectTurnPredictionCandidates(input.accumulatedText)
  for (const c of predictionCandidates) {
    parts.push(
      predictionCandidatePartFromDetection({ text: c.text, score: c.score, horizon: c.horizon }, partSeq++),
    )
  }

  return { parts, citations, predictionCandidates }
}
