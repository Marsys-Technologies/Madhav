/**
 * onfinish_writethrough — unit 3.cutover (G5b setter).
 *
 * Shared, pure write-through driver for both pipelines' onFinish stage.
 *
 * History: the legacy synthesis-orchestrator path in `consult/route.ts`
 * (onFinish at L1483) and the adapter dispatch path (anonymous stream
 * `execute` at L1069) each maintained their own copy of the onFinish
 * write-through block (persistence + observatory cost + citation enrichment
 * + marker parsing + prediction-candidate emit + context_assembly_log +
 * pending stream clear + blind-mode prediction ledger). The two had drifted:
 *
 *   • adapter path did NOT emit `data-cost`
 *   • adapter path did NOT carry `lastAssistantMetadata` into persistence
 *   • adapter path did NOT emit per-citation `data-citation` parts
 *   • adapter path did NOT emit `data-correction` / `data-out-of-domain`
 *   • adapter path did NOT `pendingStreamWriter.clear()`
 *   • adapter path did NOT write the blind-mode prediction ledger entry
 *
 * Unit 3.cutover (Stream A wave 3, sets G5b_onfinish) closes those gaps by
 * routing both onFinish handlers through this single helper. All I/O is
 * injected via the `deps` argument so:
 *   • the function is unit-testable with a recording driver (golden test)
 *   • either path can swap a dependency for a no-op when it does not apply
 *     (e.g. adapter has no `usageHolder` → cost-emit is skipped via opts)
 *
 * What this helper does NOT own:
 *   • the B.11 citation gate itself (that runs *before* this helper — its
 *     result is passed in via `opts.citationGate`). The gate is its own unit
 *     and is exercised by `adapter_citation_gate.test.ts` (0b.1).
 *   • the streaming Response object (still owned by route.ts until the
 *     full pipeline.run() extraction lands post-3.legacy_delete).
 *
 * Acceptance: same input → same recorded action list across both pipelines.
 */

import type { UIMessage } from 'ai'

import { costPart, citationPart, correctionPart, outOfDomainPart, persistencePart, predictionCandidatePart, titlePart } from '@/lib/streams/data_parts'
import { extractCitations } from '@/lib/citations/citation_data_part'
import { parseMarkers } from '@/lib/consume/marker_parser'
import { detectPredictionCandidates } from '@/lib/ppl/prediction_detector'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * Minimal subset of the AI SDK writer the helper needs. Typed as `unknown`
 * for the event so this matches both the AI SDK's `UIMessageStreamWriter<...>`
 * (which uses a discriminated-union event type) and the test capturing writer.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface WriteThroughWriter {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  write: (event: any) => void
}

/** Synth usage shape (matches AI SDK + onAuditEvent capture). */
export interface SynthUsage {
  inputTokens?: number
  outputTokens?: number
  cacheReadInputTokens?: number
  cacheCreationInputTokens?: number
}

/** Model-pricing surface the helper needs. */
export interface PricingClient {
  getPricing: (modelId: string) => unknown
  computeUsd: (pricing: unknown, tokens: {
    input_tokens: number
    output_tokens: number
    cache_read_tokens: number
    cache_write_tokens: number
  }) => number | null
}

/** Persistence surface (write + verify shape from conversation_writer). */
export interface PersistenceClient {
  writeMessages: (args: {
    conversationId: string
    messages: UIMessage[]
    lastAssistantMetadata?: Record<string, unknown>
  }) => Promise<{ verified: boolean; messageIds: string[] }>
}

/** Context-assembly-log writer (fire-and-forget — `void` return). */
export type ContextAssemblyLogWriter = (entry: {
  query_id: string
  l1_tokens: number
  l2_5_signal_tokens: number
  l2_5_pattern_tokens: number
  l4_tokens: number
  vector_tokens: number
  cgm_tokens: number
  synthesis_model_id: string
  model_max_context: number | null
  b3_compliant: boolean
  citation_count: number
  verified_citations: number
}) => void | Promise<void>

/** MSR snippet resolver — maps SIG.MSR.NNN ids → short text. */
export type MsrSnippetResolver = (signalIds: string[]) => Promise<Map<string, string>>

/** Pending-stream writer (only `clear` is required here). */
export interface PendingStreamWriterLike {
  clear: () => void | Promise<void>
}

/** Conversation-title surface (first-turn only). */
export interface TitleClient {
  generate: (messages: UIMessage[], ctx: { queryId: string; conversationId: string; userId: string }) => Promise<string | null>
  update: (conversationId: string, title: string) => Promise<void>
}

/** Blind-mode prediction-ledger appender. */
export type PredictionLedgerAppender = (entry: {
  pred_id: string
  emitted_at: string
  mode: 'blind'
  chart_id: string
  conversation_id: string
  query: string
}) => void | Promise<void>

/**
 * Citation gate result (already computed by the pipeline before this helper
 * runs). The helper does NOT re-run the gate; it only reads counts off of
 * the result to populate `context_assembly_log`.
 */
export interface CitationGateOutcome {
  gateResult: 'PASS' | 'WARN' | 'ERROR'
  layer1Count: number
  layer2Verified: number
}

/** What both pipelines pass into the helper. */
export interface OnFinishWriteThroughOpts {
  // ── identity ────────────────────────────────────────────────────────────
  /** Which pipeline invoked the helper — for diagnostics + golden-test label. */
  pipelineKind: 'single_pass' | 'agentic'
  /** Query id (uuid). */
  queryId: string
  /** Conversation id (uuid). */
  conversationId: string
  /** Chart id (uuid). */
  chartId: string
  /** Firebase uid. */
  userUid: string
  /** Whether this is the conversation's first turn. */
  isFirstTurn: boolean
  /** LEL-informed mode toggle (blind-mode ledger writes when false). */
  lelContextEnabled: boolean

  // ── synthesis result ────────────────────────────────────────────────────
  /** Final message list to persist (history + assistant). */
  finalMessages: UIMessage[]
  /** Plain-text assistant output for marker / citation / prediction scans. */
  assistantText: string
  /** Last user message text (for blind-mode ledger query field). */
  lastUserQuery: string
  /** Metadata payload attached to the last assistant message in persistence. */
  lastAssistantMetadata?: Record<string, unknown>

  // ── observability inputs ────────────────────────────────────────────────
  /** Synthesis model id. */
  modelId: string
  /** Max input tokens for the model (null when unknown). */
  modelMaxContext: number | null
  /** Synthesis usage holder value (null when adapter path has no holder). */
  synthUsage: SynthUsage | null
  /** ms from request start to onFinish entry (for data-cost). */
  synthesisElapsedMs: number
  /** B.11 citation gate outcome (run by the pipeline before this helper). */
  citationGate: CitationGateOutcome
  /** Token counts already aggregated per layer (avoids re-walking tool_results). */
  contextAssembly: {
    l1_tokens: number
    l2_5_signal_tokens: number
    l2_5_pattern_tokens: number
    l4_tokens: number
    vector_tokens: number
    cgm_tokens: number
  }

  // ── writer + emit ───────────────────────────────────────────────────────
  /** UI message stream writer (data parts). */
  writer: WriteThroughWriter
  /**
   * Trace SSE emit. Typed loosely so callers can pass `traceEmitter.emitStep`
   * (whose argument is a discriminated union) without TS variance complaints.
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  emit: (event: any) => void
}

/** Injected I/O surfaces (mockable for tests). */
export interface OnFinishWriteThroughDeps {
  persistence: PersistenceClient
  pricing: PricingClient
  contextAssemblyLog: ContextAssemblyLogWriter
  fetchMsrSnippets: MsrSnippetResolver
  pendingStreamWriter: PendingStreamWriterLike
  title: TitleClient
  predictionLedger: PredictionLedgerAppender
}

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

/**
 * Drive the onFinish write-through stage shared by both pipelines.
 *
 * Side-effect ordering (locks the legacy onFinish sequence exactly):
 *   1. data-cost (when synthUsage present)
 *   2. context_assembly_log (fire-and-forget)
 *   3. persistence (await; emits data-persistence)
 *   4. data-citation parts (one per SIG.MSR.NNN cited)
 *   5. data-correction / data-out-of-domain (when synthesis markers present)
 *   6. data-prediction-candidate parts (>= 0.5 score)
 *   7. first-turn data-title + background title generation
 *   8. pendingStreamWriter.clear()
 *   9. blind-mode prediction-ledger append (when !lelContextEnabled)
 *
 * Errors in any single step are logged and swallowed — onFinish must not
 * throw post-stream (would corrupt the HTTP pipe).
 */
export async function runOnFinishWriteThrough(
  opts: OnFinishWriteThroughOpts,
  deps: OnFinishWriteThroughDeps,
): Promise<void> {
  // 1. data-cost — Observatory cost tile.
  if (opts.synthUsage) {
    try {
      const pricing = deps.pricing.getPricing(opts.modelId)
      const dollars =
        deps.pricing.computeUsd(pricing, {
          input_tokens: opts.synthUsage.inputTokens ?? 0,
          output_tokens: opts.synthUsage.outputTokens ?? 0,
          cache_read_tokens: opts.synthUsage.cacheReadInputTokens ?? 0,
          cache_write_tokens: opts.synthUsage.cacheCreationInputTokens ?? 0,
        }) ?? 0
      opts.writer.write({
        type: 'data-cost',
        data: costPart({
          model: opts.modelId,
          input_tokens: opts.synthUsage.inputTokens ?? 0,
          output_tokens: opts.synthUsage.outputTokens ?? 0,
          dollars,
          ms: opts.synthesisElapsedMs,
        }),
      })
    } catch (err) {
      console.error('[onfinish_writethrough] cost emit error', err)
    }
  }

  // 2. context_assembly_log — fire-and-forget bookkeeping.
  try {
    void deps.contextAssemblyLog({
      query_id: opts.queryId,
      ...opts.contextAssembly,
      synthesis_model_id: opts.modelId,
      model_max_context: opts.modelMaxContext,
      b3_compliant: opts.citationGate.gateResult === 'PASS',
      citation_count: opts.citationGate.layer1Count,
      verified_citations: opts.citationGate.layer2Verified,
    })
  } catch (err) {
    console.error('[onfinish_writethrough] context_assembly_log error', err)
  }

  // 3. persistence — write all messages, emit data-persistence.
  try {
    const writeResult = await deps.persistence.writeMessages({
      conversationId: opts.conversationId,
      messages: opts.finalMessages,
      lastAssistantMetadata: opts.lastAssistantMetadata,
    })
    opts.writer.write({
      type: 'data-persistence',
      data: persistencePart({
        conversation_id: opts.conversationId,
        message_id: writeResult.messageIds.at(-1) ?? '',
        status: writeResult.verified ? 'ok' : 'error',
      }),
    })
  } catch (err) {
    console.error('[onfinish_writethrough] persistence failed', err)
  }

  // 4. data-citation — per-SIG.MSR.NNN enrichment.
  if (opts.assistantText) {
    try {
      const citations = extractCitations(opts.assistantText)
      if (citations.length > 0) {
        const snippets = await deps.fetchMsrSnippets(citations.map((c) => c.signal_id))
        for (const c of citations) {
          opts.writer.write({
            type: 'data-citation',
            data: citationPart({
              index: c.index,
              signal_id: c.signal_id,
              layer: c.layer,
              snippet: snippets.get(c.signal_id) ?? '',
            }),
          })
        }
      }
    } catch (err) {
      console.error('[onfinish_writethrough] citation enrichment error', err)
    }
  }

  // 5. data-correction / data-out-of-domain — synthesis markers.
  if (opts.assistantText) {
    try {
      const { correction, outOfDomain } = parseMarkers(opts.assistantText)
      if (correction) {
        opts.writer.write({
          type: 'data-correction',
          data: correctionPart({
            original_claim: correction.original_claim,
            corrected_claim: correction.corrected_claim,
            classical_source: correction.classical_source,
          }),
        })
      }
      if (outOfDomain) {
        opts.writer.write({
          type: 'data-out-of-domain',
          data: outOfDomainPart({ reason: outOfDomain.reason }),
        })
      }
    } catch (err) {
      console.error('[onfinish_writethrough] marker parse error', err)
    }
  }

  // 6. data-prediction-candidate — score >= 0.5 regex hits.
  if (opts.assistantText) {
    try {
      const candidates = detectPredictionCandidates(opts.assistantText).filter((c) => c.score >= 0.5)
      for (const candidate of candidates) {
        opts.writer.write({
          type: 'data-prediction-candidate',
          data: predictionCandidatePart({
            text: candidate.text,
            offset: candidate.offset,
            score: candidate.score,
            horizon: candidate.horizon,
          }),
        })
      }
    } catch (err) {
      console.error('[onfinish_writethrough] prediction candidate error', err)
    }
  }

  // 7. first-turn data-title + background title generation.
  if (opts.isFirstTurn) {
    try {
      opts.writer.write({
        type: 'data-title',
        data: titlePart({ conversation_id: opts.conversationId }),
      })
      // Generate title best-effort — non-blocking.
      void deps.title
        .generate(opts.finalMessages, {
          queryId: opts.queryId,
          conversationId: opts.conversationId,
          userId: opts.userUid,
        })
        .then((title) => {
          if (title) void deps.title.update(opts.conversationId, title)
        })
        .catch(() => {
          /* non-fatal */
        })
    } catch (err) {
      console.error('[onfinish_writethrough] title emit error', err)
    }
  }

  // 8. pendingStreamWriter.clear() — TTL row cleanup.
  try {
    void deps.pendingStreamWriter.clear()
  } catch (err) {
    console.error('[onfinish_writethrough] pending stream clear error', err)
  }

  // 9. blind-mode prediction-ledger append.
  if (!opts.lelContextEnabled) {
    try {
      void deps.predictionLedger({
        pred_id: `PRED.BLIND.${Date.now()}`,
        emitted_at: new Date().toISOString(),
        mode: 'blind',
        chart_id: opts.chartId,
        conversation_id: opts.conversationId,
        query: opts.lastUserQuery,
      })
    } catch (err) {
      console.error('[onfinish_writethrough] prediction ledger error', err)
    }
  }
}
