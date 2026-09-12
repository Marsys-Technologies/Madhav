/**
 * Paripraśna pipeline — shared typed-port plumbing (P0-C / RF-1).
 *
 * PARIPRASHNA_ARCHITECTURE §3 defines the channel-neutral core as a chain of
 * typed ports:
 *
 *   NormalizedQuery → EntitlementDecision → SafetyPolicyDecision
 *     → ScopeTuple | ClarificationRequest → AcharyaPlan
 *     → ToolBroker → EvidenceBundle → Interpretation & Adjudication
 *     → Grounding/Safety Validation → SemanticReadingParts
 *     → TurnProvenance + AcharyaReadingReceipt
 *
 * This module holds what every stage needs and no stage owns: the turn's
 * identity, the bound request parameters, the stage-result discriminant, and
 * the one label resolver two stages share.
 *
 * DEVIATION NOTE (declared, not silent): RF-1 names eight stage modules. This
 * is a ninth, support-only file. Splitting eight modules out of one closure
 * needs a place for the types they pass between them and for
 * `resolveActivityLabel`, which BOTH `evidence_stage` and `synthesis_stage`
 * call. The alternatives were a stage→stage import (a false dependency) or
 * duplicating the resolver (two copies of a gate-11 integrity control — worse).
 */

import { getCapability } from '@/lib/retrieval/registry'
import { TOOL_NAME_TO_URI } from '@/lib/retrieval/registry/tool_name_bridge'
import { resolveReaderLabel, FALLBACK_READER_LABEL } from '@/lib/pariprashna/lexicon'
import type { ReadingDepth, LengthTier } from '@/lib/pariprashna/protocol/events'
import type { ModelStack } from '@/lib/models/registry'

/** The terminal status a stage can demand of the turn. */
export type TurnStatus = 'ok' | 'error' | 'aborted'

/**
 * A stage either produces its value or halts the turn. A halting stage has
 * ALREADY emitted its own `error`/`flag`/`phase` events — the shell only calls
 * `finish(status)`. This mirrors the pre-decomposition `return finish(...)`
 * early-returns exactly: same events, same order, same terminal status.
 */
export type StageResult<T> = { halted: true; status: TurnStatus } | { halted: false; value: T }

export function halt(status: TurnStatus): { halted: true; status: TurnStatus } {
  return { halted: true, status }
}

export function proceed<T>(value: T): { halted: false; value: T } {
  return { halted: false, value }
}

/** Identity minted once per turn, before the first byte. */
export interface TurnIdentity {
  turnId: string
  queryId: string
  conversationId: string
  chartId: string
  /** True when the client supplied no conversationId (this turn opened it). */
  isFirstTurn: boolean
  /** The client-supplied conversation id, or undefined on a first turn. */
  clientConversationId?: string
}

/** The bound, validated request parameters (the NormalizedQuery port). */
export interface TurnParams {
  selectedStack: ModelStack
  modelId: string
  modelMeta: NonNullable<ReturnType<typeof import('@/lib/models/registry').getModelMeta>>
  readingDepth: ReadingDepth
  deepDive: boolean
  lengthTier: LengthTier
  lelContextEnabled: boolean
  style: string
  /**
   * P4-G — the reader's answer to a previously-emitted `window_ask`, when this turn carries
   * one. `null` on every ordinary turn. See `safety_gate.bindTurnParams` for the binding and
   * `samiksha/window_ask/capture.ts` for what is (and is not) done with it.
   */
  windowAskAnswer?: { ledgerRowId: string; text: string } | null
}

// ── Gate 11 [integrity] ──────────────────────────────────────────────────────
// `label_key`/`detail` on activity.upsert are CLIENT-VISIBLE wire content
// (design plan §7.8/§8.4.4 — server resolves label_key -> display string; the
// client renders verbatim). Never pass a raw tool name / registry URI / layer
// name through to either field — resolve via S-2's closed-lexicon reader_label
// mapping, falling back to FALLBACK_READER_LABEL + a CI warning exactly like
// the registry's own resolveReaderLabel() contract.
export function resolveActivityLabel(toolNameOrUri: string): string {
  const uri = toolNameOrUri.startsWith('marsys://') ? toolNameOrUri : TOOL_NAME_TO_URI[toolNameOrUri]
  const capability = uri ? getCapability(uri) : undefined
  if (!capability) {
    console.warn(
      `[pariprashna] activity label: no registry capability resolved for "${toolNameOrUri}" — using fallback reader label`,
    )
    return FALLBACK_READER_LABEL
  }
  return resolveReaderLabel(capability)
}
