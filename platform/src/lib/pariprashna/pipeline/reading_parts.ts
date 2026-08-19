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
  ) {
    this.passId = initialPassId
  }

  /** Every scrubbed PROSE delta, concatenated. Thinking text is excluded. */
  get accumulatedText(): string {
    return this.accumulated
  }

  commitBlock(): void {
    if (this.currentBlock) {
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
          const scan = scanMortalityPhrasing(this.currentBlock.text, {
            extraRules: this.preWireExtraRules,
            mortalityRulesEnabled: this.mortalityScanEnabled,
          })
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
        }
      }
      this.em.blockCommit({ block_id: this.currentBlock.id, text: this.currentBlock.text })
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
}

export interface CanonicalPartsOutput {
  parts: MessagePartInput[]
  citations: DetectedCitationRow[]
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

  const citations = detectTurnCitations(input.accumulatedText)
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
