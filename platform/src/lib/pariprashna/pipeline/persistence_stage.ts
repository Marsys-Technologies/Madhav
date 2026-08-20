/**
 * Paripraśna pipeline — PERSISTENCE STAGE (P0-C / RF-1).
 *
 * The finalize seam: the shared onFinish write-through, the AI-SDK-data-part →
 * Paripraśna-vocabulary bridge writer, and the canonical assistant-turn write.
 *
 * PB-2/M-2: the ASSISTANT turn's content persists via M-1's canonical
 * `writeTurn` DAL (transactional message row + kind-typed parts) — see the
 * `persistence.writeMessages` closure below. This REPLACES the legacy
 * write-through for the assistant's content; it is never run in parallel with
 * it for the same row.
 *
 * Scope decision (M-2, disclosed): conversation HISTORY (every message prior to
 * this turn, including the user's current query) still persists via the
 * pre-existing legacy `writeConversationMessages` helper, UNCHANGED. Migrating
 * user-message persistence onto a canonical schema is not part of M-1's
 * schema/DAL charter (M-1 built `message_parts` for the ASSISTANT turn's
 * kind-typed content) and is well beyond "persistence seam only" scope —
 * rearchitecting it here risks a real regression (silently dropped user-message
 * history) for no requested benefit. See the M-2 report.
 *
 * WHY THIS STAGE IMPORTS `receipt_stage`: the D-16 provenance stamp is computed
 * inside the finalize block, AFTER the assistant message id is minted and
 * BEFORE the write-through runs, because it rides into
 * `conversation_messages.metadata_json`. The receipt stage owns computing it;
 * this stage owns writing it. Hoisting the call into the route shell would move
 * it ahead of the id mints in SOURCE order. Note (P0-C verification, 2026-08-19):
 * the golden-stream harness cannot currently observe this reordering either way
 * (no scenario asserts on relative id-mint/stamp-compute timing) — keep the
 * stated order because it is the intended contract, not because a test proves
 * it, and land a scenario that pins it before relying on this comment alone.
 */

import type { UIMessage } from 'ai'

import { query } from '@/lib/db/client'
import { writeConversationMessages } from '@/lib/persistence/conversation_writer'
import { createPendingStreamWriter } from '@/lib/persistence/pending_streams_writer'
import { generateConversationTitle } from '@/lib/conversations/title'
import { updateConversationTitle } from '@/lib/conversations'
import {
  runOnFinishWriteThrough,
  type WriteThroughWriter,
} from '@/lib/pipelines/shared/onfinish_writethrough'
import { computeCostUsd, getModelPricingSync } from '@/lib/llm/pricing'
import { writeContextAssemblyLog } from '@/lib/db/monitoring-write'
import { writeTurn } from '@/lib/pariprashna/store/writer'
import { CANONICAL_SCHEMA_VERSION, type CanonicalMessage } from '@/lib/pariprashna/store/schema'
import { withProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'
import { captureDetectedCandidates } from '@/lib/pariprashna/samiksha/capture'
import type { ResolvedTurnCitation } from '@/lib/pariprashna/citations/stream_wiring'
import type { ServerGroundingSummary } from '@/lib/pariprashna/protocol/events'
import type { ToolBundle } from '@/lib/retrieval/shared_types'
import type { PipelinePlan } from '@/lib/pipeline/types'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

import type { TurnIdentity, TurnParams } from './stage_context'
import {
  buildCanonicalParts,
  detectTurnCitations,
  type DetectedCitationRow,
  type OpenBlock,
} from './reading_parts'
import { computeTurnReceiptProvenance } from './receipt_stage'
import type { CitationGateOutcome } from './validation_stage'

/**
 * MSR snippet resolver (read-only). Copy of the consult route's helper — this
 * is a retrieval read, NOT the message-write path (that is shared, below).
 */
export async function fetchMsrSnippets(signalIds: string[]): Promise<Map<string, string>> {
  if (signalIds.length === 0) return new Map()
  try {
    const placeholders = signalIds.map((_, i) => `$${i + 1}`).join(', ')
    const { rows } = await query<{ signal_id: string; name: string; description: string }>(
      `SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signals WHERE signal_id::text IN (${placeholders})`,
      signalIds,
    )
    return new Map(
      rows.map((r) => {
        const full = r.name
          ? r.description
            ? `${r.name} — ${r.description}`
            : r.name
          : r.description ?? ''
        return [r.signal_id, full.length > 295 ? full.slice(0, 294) + '…' : full]
      }),
    )
  } catch {
    return new Map()
  }
}

// Minimal, specific shapes for the AI-SDK data-parts the write-through helper
// emits — narrow interfaces (NOT `any`) so the adapter-writer can map them onto
// the Paripraśna vocabulary with full type safety.
interface CitationDataPart {
  index: number
  signal_id: string
  layer: string
  snippet: string
}
interface PersistenceDataPart {
  conversation_id: string
  message_id: string
  status: 'ok' | 'error'
}
interface PredictionCandidateDataPart {
  text: string
  score: number
  horizon: string | null
}
interface WriteThroughEvent {
  type: string
  data?: unknown
}

export async function runPersistenceStage(args: {
  em: PariprashnaEmitter
  identity: TurnIdentity
  params: TurnParams
  user: { uid: string }
  isSuperAdmin: boolean
  messages: UIMessage[]
  lastUserMessage: UIMessage | undefined
  plan: PipelinePlan
  plannerModelId: string
  plannerLatencyMs: number
  committedBlocks: readonly OpenBlock[]
  accumulatedText: string
  validToolResults: ToolBundle[]
  citationGate: CitationGateOutcome
  synthesisStartedAt: number
  /** Lane G1-A. Enforced → the turn's predictive output is sampled (HS-6). */
  safetyDecision?: import('@/lib/pariprashna/safety').SafetyDecision
  /**
   * Lane G2-B (P0C-R5 fix). Whether the live citation rewriter ran this turn
   * (`synthesis_stage.ts`'s `citationRewriteEnabled`). Drives which citation
   * source persistence trusts: TRUE → the rewriter's own resolution ledger
   * (`resolvedCitations`, never a re-scan of already-scrubbed
   * `accumulatedText`); FALSE/omitted → the pre-existing
   * `detectTurnCitations(accumulatedText)` regex path, unchanged.
   */
  citationRewriteEnabled?: boolean
  /** Lane G2-B. The rewriter's resolution ledger — see `citationRewriteEnabled`. */
  resolvedCitations?: readonly ResolvedTurnCitation[]
  /**
   * Lane G2-B. Server-derived grounding summary for this turn
   * (`citations/grounding_summary.ts`). Attached to the `turn.commit` wire
   * event when present; absent → the client falls back to its own citation
   * tally, visibly labeled as an estimate (never silently substituted).
   */
  groundingSummary?: ServerGroundingSummary
}): Promise<void> {
  const {
    em,
    identity,
    params,
    user,
    isSuperAdmin,
    messages,
    lastUserMessage,
    plan,
    plannerModelId,
    plannerLatencyMs,
    committedBlocks,
    accumulatedText,
    validToolResults,
    citationGate,
    synthesisStartedAt,
    citationRewriteEnabled = false,
    resolvedCitations = [],
    groundingSummary,
  } = args
  const { turnId, queryId, conversationId, chartId, isFirstTurn } = identity

  em.phase({ phase: 'finalize', status: 'start' })
  const pendingStreamWriter = createPendingStreamWriter(queryId, conversationId, user.uid)

  if (!accumulatedText) {
    // No prose produced — persistence is skipped by the shared helper, so
    // report the honest gap rather than silently omitting turn.commit.
    em.flag({ code: 'empty_synthesis', level: 'warn', detail: 'No assistant text produced.' })
    return
  }

  const historyMsgs: UIMessage[] = (messages as UIMessage[]).map(
    (m) => ({ ...m, id: crypto.randomUUID() }) as UIMessage,
  )
  const assistantMessageId = crypto.randomUUID()
  // Used for onfinish's title-generation step only (needs the FULL turn incl.
  // assistant text) — NOT for persistence (see the `persistence.writeMessages`
  // closure below, which ignores `args.messages` and writes history/assistant
  // separately).
  const persistMsgs: UIMessage[] = [
    ...historyMsgs,
    { id: assistantMessageId, role: 'assistant' as const, parts: [{ type: 'text', text: accumulatedText }] } as UIMessage,
  ]
  const lastUserText = ((lastUserMessage?.parts ?? []) as Array<{ type: string; text?: string }>)
    .filter((p) => p.type === 'text')
    .map((p) => p.text ?? '')
    .join(' ')
    .trim()

  // D-16 provenance stamp (lane PB-2/M-6) — see receipt_stage.ts.
  const { provenanceStamp } = await computeTurnReceiptProvenance({ em, chartId, conversationId })

  // Adapter-writer: maps the write-through's AI-SDK data-parts onto the
  // Paripraśna vocabulary. Typed with a narrow event interface (NOT `any`) —
  // assignable to WriteThroughWriter because its `write` param is `any`, so no
  // cast is needed at the boundary.
  const bridgeWriter: WriteThroughWriter = {
    write: (evt: WriteThroughEvent): void => {
      switch (evt.type) {
        case 'data-citation': {
          const d = evt.data as CitationDataPart
          em.citationDefine({ index: d.index, signal_id: d.signal_id, layer: d.layer, snippet: d.snippet })
          break
        }
        case 'data-persistence': {
          const d = evt.data as PersistenceDataPart
          em.turnCommit({
            turn_id: turnId,
            conversation_id: d.conversation_id,
            message_id: d.message_id,
            status: d.status,
            assistant_chars: accumulatedText.length,
            // Lane G2-B. Additive/optional — absent when the flag is off or no
            // summary was built, in which case the client's own citation
            // tally is the (visibly labeled) degrade path.
            ...(groundingSummary ? { grounding_summary: groundingSummary } : {}),
          })
          break
        }
        case 'data-prediction-candidate': {
          // Detector left wired exactly as it fires today (inside the shared
          // helper); surfaced here as an info flag.
          const d = evt.data as PredictionCandidateDataPart
          em.flag({ code: 'prediction_candidate', level: 'info', detail: `${d.text} (score=${d.score}${d.horizon ? `, horizon=${d.horizon}` : ''})` })
          break
        }
        case 'data-correction': {
          em.flag({ code: 'correction', level: 'info' })
          break
        }
        case 'data-out-of-domain': {
          em.flag({ code: 'out_of_domain', level: 'warn' })
          break
        }
        default:
          // data-cost / data-title / etc — not part of the Paripraśna wire.
          break
      }
    },
  }

  const tokensForAdapter = (predicate: (toolName: string) => boolean): number => {
    let chars = 0
    for (const tb of validToolResults) {
      if (!predicate(tb.tool_name)) continue
      for (const r of tb.results) chars += r.content.length
    }
    return Math.ceil(chars / 4)
  }

  await runOnFinishWriteThrough(
    {
      pipelineKind: 'agentic',
      queryId,
      conversationId,
      chartId,
      userUid: user.uid,
      isFirstTurn,
      lelContextEnabled: params.lelContextEnabled,
      finalMessages: persistMsgs,
      assistantText: accumulatedText,
      lastUserQuery: lastUserText,
      // provenance_stamp rides as an ADDITIVE sibling of `custom` (never inside
      // it) — DB-only metadata, never read back into planning/synthesis, never
      // streamed (see the D-16 note in receipt_stage.ts).
      lastAssistantMetadata: withProvenanceStamp(
        {
          custom: {
            model: params.modelId,
            queryId,
            planning_model_id: plannerModelId,
            planning_latency_ms: plannerLatencyMs,
            disclosure_tier: isSuperAdmin ? 'super_admin' : 'client',
            query_class: plan.query_class,
            stack: params.selectedStack,
            style: params.style,
            reading_depth: params.readingDepth,
            length_tier: params.lengthTier,
            pipeline: 'pariprashna',
            conversationId,
          },
        },
        provenanceStamp,
      ),
      modelId: params.modelId,
      modelMaxContext: params.modelMeta.maxInputTokens ?? null,
      synthUsage: null,
      synthesisElapsedMs: Date.now() - synthesisStartedAt,
      citationGate: {
        gateResult: citationGate.gateResult,
        layer1Count: citationGate.layer1Count,
        layer2Verified: citationGate.layer2Verified,
      },
      contextAssembly: {
        l1_tokens: tokensForAdapter((n) => ['chart_facts_query', 'divisional_query', 'kp_query', 'manifest_query'].includes(n)),
        l2_5_signal_tokens: tokensForAdapter((n) => ['msr_sql', 'query_msr_aggregate', 'query_signal_state'].includes(n)),
        l2_5_pattern_tokens: tokensForAdapter((n) => ['pattern_register', 'resonance_register', 'contradiction_register', 'cluster_atlas'].includes(n)),
        l4_tokens: tokensForAdapter((n) => ['remedial_codex_query', 'domain_report_query'].includes(n)),
        vector_tokens: tokensForAdapter((n) => n === 'vector_search'),
        cgm_tokens: tokensForAdapter((n) => n === 'cgm_graph_walk'),
      },
      writer: bridgeWriter,
      emit: () => {
        /* trace sink — Paripraśna surfaces state via its own vocabulary */
      },
    },
    {
      persistence: {
        writeMessages: async (writeArgs) => {
          // History rows — legacy path, UNCHANGED (see scope-decision comment
          // above). `writeArgs.messages` (== persistMsgs, history + assistant)
          // is deliberately NOT used here — the assistant row is written
          // canonically below instead.
          const historyResult = await writeConversationMessages({
            conversationId,
            messages: historyMsgs,
          })

          // Assistant row — PB-2/M-2 canonical path. Built from the turn's own
          // in-memory data via route_writer_adapter.ts's production mapping
          // functions (now behind reading_parts.buildCanonicalParts) — the SAME
          // functions lane M-2's byte-equality gate
          // (tests/pariprashna/reducer/canonical_serialization_golden.test.ts)
          // exercises independently against a client-reducer simulation.
          //
          // Lane G2-B (P0C-R5 fix): when the live rewriter ran this turn, its
          // OWN resolution ledger is the citation source of truth —
          // `accumulatedText` at this point contains resolved `[n]` markers,
          // not raw `SIG.MSR.NNN` tokens (the register-leak lint already
          // rewrote/redacted every such token before it reached
          // `accumulatedText`), so re-scanning it here would silently find
          // nothing regardless of what the reader actually saw. Snippets are
          // already known from the resolver's prefetch — no second DB round
          // trip. Flag-off path is UNCHANGED: detect from prose, fetch
          // snippets only when something was actually detected.
          let citationsFound: DetectedCitationRow[]
          let snippets: Map<string, string>
          if (citationRewriteEnabled) {
            citationsFound = resolvedCitations.map((c) => ({
              index: c.index,
              signal_id: c.signal_id,
              layer: c.layer,
            }))
            snippets = new Map(resolvedCitations.map((c) => [c.signal_id, c.snippet]))
          } else {
            citationsFound = detectTurnCitations(accumulatedText)
            snippets =
              citationsFound.length > 0
                ? await fetchMsrSnippets(citationsFound.map((c) => c.signal_id))
                : new Map<string, string>()
          }
          const { parts: canonicalParts, predictionCandidates: predictionCandidatesFound } =
            buildCanonicalParts({
              committedBlocks,
              accumulatedText,
              snippets,
              preResolvedCitations: citationRewriteEnabled ? citationsFound : undefined,
            })

          const canonicalMessage: CanonicalMessage = {
            id: assistantMessageId,
            conversation_id: conversationId,
            role: 'assistant',
            schema_version: CANONICAL_SCHEMA_VERSION,
            model_id: params.modelId,
            provider: params.modelMeta.provider,
            metadata: writeArgs.lastAssistantMetadata,
          }

          let canonicalOk = true
          try {
            await writeTurn(canonicalMessage, canonicalParts)
          } catch (err) {
            console.error('[pariprashna] canonical writeTurn failed', err)
            canonicalOk = false
          }

          // ── SAMĪKṢĀ capture (PB-3.1 G1) — the prediction loop's ENTRY POINT.
          // The parts above already carry the `message_parts.id` the ledger FK
          // needs; this writes the matching `detected` ledger row per candidate
          // so the review tab's Awaiting section stops being structurally empty
          // and a human can confirm a real claim. `detected` is NOT
          // auto-promotion (W-1): it carries no D-16 stamp and no confidence
          // band, and only the human's explicit confirm advances it. See
          // lib/pariprashna/samiksha/capture.ts for the full rationale and for
          // why the in-stream mount needs a wire change first.
          //
          // Strictly non-fatal and strictly after the turn is committed: a
          // ledger fault must never cost the reader their reading.
          if (canonicalOk && predictionCandidatesFound.length > 0) {
            try {
              const capture = await captureDetectedCandidates({
                chartId,
                messageId: assistantMessageId,
                candidates: predictionCandidatesFound,
                citations: citationsFound.map((c) => ({ signal_id: c.signal_id, layer: c.layer })),
                nowDate: provenanceStamp.now_context_date,
              })
              console.info(
                `[pariprashna] samiksha capture: ${capture.created.length} detected, ` +
                  `${capture.skippedExisting} already-ledgered, ${capture.unpaired} unpaired ` +
                  `(message ${assistantMessageId})`,
              )
            } catch (err) {
              console.error('[pariprashna] samiksha detected-row capture failed', err)
            }

            // ── HS-6 (lane G1-A): sample this predictive reading into the
            // §IS.8 red-team pool. Same placement and same discipline as the
            // samiksha capture above — strictly after the turn is committed,
            // strictly non-fatal. §IS.8 is a governance cadence with no runtime
            // mechanism, so what this builds is the POOL a red-team session
            // draws from; it makes the cadence's input auditable and does not
            // claim to make the cadence run.
            if (args.safetyDecision?.enforced) {
              try {
                const { recordPredictiveSample, defaultSafetyDb } = await import('@/lib/pariprashna/safety')
                const sampled = await recordPredictiveSample(defaultSafetyDb(), {
                  sampleId: crypto.randomUUID(),
                  chartId,
                  turnId: identity.turnId,
                  predictionCandidateCount: predictionCandidatesFound.length,
                  receiptHash: null,
                  safetyClasses: args.safetyDecision.classes_detected,
                })
                if (!sampled) {
                  console.warn('[pariprashna/safety] predictive sample NOT recorded for turn', identity.turnId)
                }
              } catch (err) {
                console.error('[pariprashna/safety] predictive sampling failed (non-fatal)', err)
              }
            }
          }

          return {
            verified: historyResult.verified && canonicalOk,
            messageIds: [...historyResult.messageIds, assistantMessageId],
          }
        },
      },
      pricing: {
        getPricing: (mid) => getModelPricingSync(mid),
        computeUsd: (pricing, tokens) => computeCostUsd(pricing as Parameters<typeof computeCostUsd>[0], tokens),
      },
      contextAssemblyLog: (entry) => {
        void writeContextAssemblyLog(entry)
      },
      fetchMsrSnippets: (ids) => fetchMsrSnippets(ids),
      pendingStreamWriter,
      title: {
        generate: (msgs, c) => generateConversationTitle(msgs, c),
        update: (cid, t) => updateConversationTitle(cid, t).then(() => undefined),
      },
      predictionLedger: async (entry) => {
        try {
          const fs = await import('fs/promises')
          const path = await import('path')
          const ledgerPath = path.join(process.cwd(), '..', '06_LEARNING_LAYER', 'PREDICTION_LEDGER', 'prediction_ledger.jsonl')
          const line =
            JSON.stringify({
              ...entry,
              outcome: null,
              confidence: null,
              horizon: null,
              falsifier: null,
              note: 'Auto-logged blind-mode query (pariprashna). Outcome/confidence/horizon/falsifier to be filled by native.',
            }) + '\n'
          await fs.appendFile(ledgerPath, line, 'utf8')
        } catch {
          /* non-fatal */
        }
      },
    },
  )
}
