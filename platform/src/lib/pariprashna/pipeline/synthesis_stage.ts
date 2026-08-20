/**
 * Paripraśna pipeline — SYNTHESIS STAGE (P0-C / RF-1).
 *
 * Port: `Interpretation & Adjudication`.
 *
 * Two halves, in the order the pre-decomposition closure ran them:
 *   1. `assembleSynthesisContext` — the prompt prefix: trimmed conversation
 *      history, the bundle's system content through consult's own
 *      temporal-anchored builder, and the PB-2/M-3 durable-summary splice into
 *      its FIXED structural slot (best-effort, non-fatal — a summary fault must
 *      never cost the reader their reading).
 *   2. `runSynthesisStage` — adapter wiring plus the stream loop that turns
 *      provider events into blocks, passes and seams.
 *
 * PASS/SEAM TRUTH: a pass boundary is derived PURELY from the engine's own
 * control flow — a `tool_use_complete` arriving AFTER prose was already emitted
 * in this pass. It is never inferred from the text. That rule is the reason the
 * seam machinery lives here, next to the loop that observes the control flow,
 * and not in `reading_parts.ts`, which only owns block mechanics.
 *
 * Gate 11 [integrity]: EVERY delta chunk is linted before it reaches the wire.
 * The residual — a leak pattern split exactly across a chunk boundary — is
 * covered by the assembler's whole-block backstop on commit.
 */

import type { ModelMessage, UIMessage } from 'ai'
import { convertToModelMessages } from 'ai'

import type { StackId } from '@/lib/providers/dispatcher'
import { getAdapter } from '@/lib/providers/dispatcher'
import type { ChatRequest } from '@/lib/providers/types'
import {
  buildAdapterMessages,
  buildAdapterChatRequest,
} from '@/lib/providers/adapter-dispatch-helpers'
import {
  runAgenticLoop,
  LOOP_CONFIG_BY_PROVIDER,
  type AgenticLoopConfig,
} from '@/lib/synthesis/agentic_loop'
import { executeMCPTool } from '@/lib/synthesis/mcp_tool_executor'
import { buildChatToolsFromNames } from '@/lib/retrieval/registry/schema_utils'
import { buildConsultSystemContent } from '@/lib/pipelines/shared/run_adapter_dispatch'
import { lintReaderProse } from '@/lib/pariprashna/citations/register_leak_lint'
import { isFirstPaintCitationsEnabled } from '@/lib/pariprashna/citations/flag'
import {
  TurnCitationStream,
  type ResolvedTurnCitation,
  type UnstampedCitationWireEvent,
} from '@/lib/pariprashna/citations/stream_wiring'
import {
  extractCandidateSignalIds,
  fetchCandidateSignalLabels,
  buildTurnCitationResolver,
} from './citation_resolver'
import type { ToolBundle } from '@/lib/retrieval/shared_types'
import type { ChartOrientation } from '@/lib/retrieval/orientation'
import type { PipelinePlan } from '@/lib/pipeline/types'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { StreamingMortalityScanner } from '@/lib/pariprashna/safety/phrasing_scan'
import { PREWIRE_REDACTION_NOTICE } from '@/lib/pariprashna/safety/fixed_responses'
import type { SafetyDecision } from '@/lib/pariprashna/safety'
import { isInjectionContainmentEnabled } from '@/lib/pariprashna/injection/flag'
import { isSemanticBlocksEnabled } from '@/lib/pariprashna/semantics/flag'
import { isHonestControlsEnabled } from '@/lib/pariprashna/honest_controls/flag'
import { isVoiceEnforcementEnabled } from '@/lib/pariprashna/voice/flag'
import { lintVoiceProse } from '@/lib/pariprashna/voice/voice_lint'
import { isDifficultFindingActive, shouldForceDifficultBlockBreak } from '@/lib/pariprashna/voice/pacing'
import type { LengthTier } from '@/lib/pariprashna/protocol/events'
import {
  buildEntitlementScanRules,
  containRetrievedEvidence,
  containToolResult,
  containUserQuestion,
  containPriorTurn,
  ENTITLEMENT_REDACTION_NOTICE,
  INJECTION_CONTAINMENT_CLAUSE,
  rejectIdentityParams,
  ToolSequenceMonitor,
} from '@/lib/pariprashna/injection'
import { TurnMetricsCollector } from '@/lib/pariprashna/observability/turn_metrics'
import {
  recordSynthesisTurnObservation,
  type SynthesisObservationIdentity,
} from '@/lib/pariprashna/observability/synthesis_observation'

import { halt, proceed, resolveActivityLabel, type StageResult, type TurnParams } from './stage_context'
import { PASS_ONE } from './evidence_stage'
import { ReadingPartsAssembler, type OpenBlock } from './reading_parts'
import type { LegacyQueryPlan } from './plan_stage'

/**
 * deep_dive raises the agentic-loop iteration cap so the model can retrieve
 * exhaustively across adaptive passes — the web engine's "dossier / maximal
 * chart coverage" lever (the deterministic B.11 + dasha floors always run; this
 * widens the ADAPTIVE re-entry budget on top of them).
 */
export const DEEP_DIVE_MAX_ITERATIONS = 16

const STACK_TO_ADAPTER: Partial<Record<string, StackId>> = {
  anthropic: 'anthropic',
  gemini: 'google',
  gpt: 'openai',
  deepseek: 'deepseek',
  nim: 'nvidia',
}

const AGENTIC_PROVIDERS = new Set<string>(['anthropic', 'google', 'openai', 'deepseek', 'nvidia'])

/** Lane P2-E. A short, loggable error code for the `llm_usage_events.status='error'` row. */
function extractStreamErrorCode(err: unknown): string {
  if (err && typeof err === 'object') {
    const e = err as { code?: unknown; name?: unknown; message?: unknown }
    if (typeof e.code === 'string' && e.code.length > 0) return e.code
    if (typeof e.name === 'string' && e.name.length > 0) return e.name
    if (typeof e.message === 'string' && e.message.length > 0) return e.message.slice(0, 200)
  }
  return 'unknown_error'
}

export interface SynthesisContext {
  /** The full system prefix (bundle + guidance + durable-summary splice). */
  systemContentWithSummary: string
  /**
   * The trimmed history the adapter messages are built from. Computed HERE and
   * carried forward rather than recomputed in `runSynthesisStage`: the
   * pre-decomposition closure called `convertToModelMessages` exactly once.
   */
  trimmedConversationHistory: ModelMessage[]
}

/**
 * Lane P2-C (PPR-09/16) — honest length shaping. `length_tier` previously had
 * NO live effect on synthesis (TODO(PB-4) in `safety_gate.ts`): the composer
 * offered a Length pill, the request carried a real `length_tier`, and none of
 * it changed a single byte of the prompt. This is the fix, not a cosmetic
 * echo: a short, FIXED instruction appended to the system prompt, distinct per
 * tier and gated behind `isHonestControlsEnabled()`.
 *
 * `standard` (and the flag-OFF path) appends NOTHING — the default reading is
 * byte-identical to today's whether or not the flag is on, which is the same
 * "the requested tier that means no change should cause no change" discipline
 * NO-LEAKAGE and the safety prompt policy already follow elsewhere in this
 * file. This is deterministic prompt guidance, not a computed chart claim —
 * it does not re-derive or restate any L1/L2+ fact, so it carries no
 * DERIVATION_LEDGER obligation (§B.3 is about claims, not verbosity framing).
 */
const LENGTH_TIER_GUIDANCE: Partial<Record<LengthTier, string>> = {
  brief:
    'Length discipline for THIS reading: BRIEF. Lead with the verdict and the ' +
    'load-bearing evidence only. Omit secondary corroboration, tangential ' +
    'detail, and elaboration the core claim does not need. Do not shorten by ' +
    'dropping citations — every claim still needs its grounding, just fewer ' +
    'claims.',
  exhaustive:
    'Length discipline for THIS reading: EXHAUSTIVE. Cover every relevant ' +
    'domain, corroborating signal, and classical nuance the retrieved ' +
    'evidence supports. Do not truncate for brevity or hold back a ' +
    'well-grounded point to save space.',
}

export async function assembleSynthesisContext(args: {
  messages: UIMessage[]
  bundle: { assets: unknown }
  plan: PipelinePlan
  orientation: ChartOrientation | null
  conversationId: string
  /** Lane G1-A. Omitted → no policy block (flag-OFF path and older callers). */
  safetyDecision?: SafetyDecision
  /** Lane P2-C. Omitted → no length instruction (flag-OFF path and older callers). */
  lengthTier?: LengthTier
}): Promise<SynthesisContext> {
  const { messages, bundle, plan, orientation, conversationId } = args

  const injectionContained = isInjectionContainmentEnabled()

  let trimmedConversationHistory: ModelMessage[] = await convertToModelMessages(
    messages.filter((m) => m.role === 'user' || m.role === 'assistant').slice(-5).slice(0, -1),
  )
  // ── INJECTION CONTAINMENT (lane G1-G · PPR-13): prior turns are DATA. ──────
  // `QUERY_INDEPENDENCE_GATE` already tells the model to treat history as
  // "background noise" — TA §14A.1 calls that out by name as "a prompt
  // heuristic, not a defense". This is the structural half: each prior turn's
  // text goes inside a container whose own delimiters the payload cannot close.
  // Only the TEXT parts are wrapped; tool-result and other structured parts are
  // left untouched so nothing downstream that inspects part shapes changes.
  if (injectionContained) {
    trimmedConversationHistory = trimmedConversationHistory.map((m) => {
      if (m.role !== 'user' && m.role !== 'assistant') return m
      const role = m.role
      if (typeof m.content === 'string') {
        return { ...m, content: containPriorTurn(m.content, role) } as ModelMessage
      }
      if (!Array.isArray(m.content)) return m
      return {
        ...m,
        content: m.content.map((part) =>
          part && typeof part === 'object' && (part as { type?: string }).type === 'text'
            ? { ...part, text: containPriorTurn((part as { text: string }).text, role) }
            : part,
        ),
      } as ModelMessage
    })
  }

  const rawBundleSystemContent = (bundle.assets as Array<{ content: string }>)
    .map((a) => a.content)
    .filter(Boolean)
    .join('\n\n')
  // The retrieved evidence — asset file text read verbatim off storage by
  // `bundle_hydrator`, i.e. the classical-corpus passages TA §14A.1's abuse case
  // A2 is about. Wrapped whole rather than per-asset: the bundle is joined into
  // one system block downstream, so one container is what the model actually
  // sees, and per-asset containers would only multiply the surfaces a payload
  // could try to close.
  const bundleSystemContent = injectionContained
    ? containRetrievedEvidence(rawBundleSystemContent)
    : rawBundleSystemContent
  const currentMahaAntar =
    orientation?.chart_header?.current_maha_antar ?? orientation?.dasha_context?.current_maha_antar ?? null
  const systemContent = buildConsultSystemContent({
    bundleSystemContent,
    synthesisGuidance: plan.synthesis_guidance,
    nowContextDate: new Date().toISOString().slice(0, 10),
    currentMahaAntar,
  })

  // ── PB-2/M-3 (SMṚTI durable summaries) — narrow, additive splice. ──────────
  // Folds a durable, citation-preserving summary of EARLIER canonical turns
  // into a FIXED structural slot ahead of the system content built above
  // (src/lib/pariprashna/summaries/assemble.ts) so the assembled prefix's
  // cache-relevant structure is unchanged turn-to-turn when no new
  // summarization threshold crossing occurred. Best-effort and non-fatal, same
  // convention as the orientation promise's `.catch()`.
  //
  // Assistant turns persist canonically via lane M-2's `writeTurn`, so
  // `message_parts` rows exist for pariprashna conversations and this splice is
  // LIVE. Disclosed scope residual: only assistant rows are canonical today —
  // user/history messages still persist via the legacy path, so summaries are
  // built from assistant turns only.
  let conversationSummaryText: string | null = null
  try {
    const { getConversationSummaryForSplice } = await import('@/lib/pariprashna/summaries/splice')
    conversationSummaryText = await getConversationSummaryForSplice(conversationId)
  } catch (err) {
    console.error('[pariprashna] durable-summary splice failed (non-fatal):', err)
  }
  const { assembleSynthesisPrefix } = await import('@/lib/pariprashna/summaries/assemble')
  let systemContentWithSummary = assembleSynthesisPrefix({
    precedingBlock: systemContent ?? '',
    summaryText: conversationSummaryText,
  })

  // ── LENGTH SHAPING (lane P2-C · PPR-09/16). ────────────────────────────────
  // Narrow, additive splice — same position/convention as the durable-summary
  // splice immediately above: appended to the FIXED structural prefix, not
  // interleaved with the untrusted evidence bundle. `standard` (the schema
  // default) intentionally adds nothing, so the common case's prompt is
  // unchanged whether or not the flag is on.
  if (isHonestControlsEnabled() && args.lengthTier) {
    const lengthGuidance = LENGTH_TIER_GUIDANCE[args.lengthTier]
    if (lengthGuidance) {
      systemContentWithSummary = [systemContentWithSummary, lengthGuidance].filter(Boolean).join('\n\n---\n\n')
    }
  }

  // ── INJECTION CONTAINMENT: the clause that makes the tags mean something. ──
  // Appended AFTER the evidence and the summary splice and BEFORE the safety
  // policy, so the ordering downstream-of-untrusted-content reads:
  //     … evidence … → summary → injection clause → safety policy
  // Both policy blocks therefore sit downstream of every untrusted container,
  // which is the only structural leverage a prompt has and is used deliberately
  // here for the same reason G1-A documents it for the safety policy. The
  // safety policy stays LAST; this lane does not take its position.
  if (injectionContained) {
    systemContentWithSummary = [systemContentWithSummary, INJECTION_CONTAINMENT_CLAUSE]
      .filter(Boolean)
      .join('\n\n---\n\n')
  }

  // ── SAFETY: synthesis-time prompt policy (lane G1-A · HS-1 point (b)). ─────
  // Appended LAST, after the evidence bundle and after the summary splice, so
  // that content injected into retrieved evidence (abuse case A2) cannot appear
  // downstream of the policy and claim to override it. Position is the only
  // structural leverage a prompt has, and it is used deliberately.
  //
  // This is the MIDDLE of HS-1's three controls precisely because it depends on
  // a model's cooperation. Plan-time exclusion and the pre-wire scan do not.
  if (args.safetyDecision?.enforced) {
    const { appendSafetyPromptPolicy } = await import('@/lib/pariprashna/safety')
    systemContentWithSummary = appendSafetyPromptPolicy(
      systemContentWithSummary,
      args.safetyDecision.classes_detected,
    )
  }

  return { systemContentWithSummary, trimmedConversationHistory }
}

export interface SynthesisStageOutput {
  assembler: ReadingPartsAssembler
  accumulatedText: string
  synthesisStartedAt: number
  finalPassId: number
  /**
   * Lane G1-G. `null` when injection containment is flag-OFF — which is the
   * honest value: no monitor was built, so nothing was measured. It is NOT
   * "the sequence was checked and was clean" (§N.8).
   */
  toolSequenceMonitor: ToolSequenceMonitor | null
  /**
   * Lane G2-B. Every citation the live rewriter actually resolved this turn,
   * in wire order — `[]` (not null) when the flag is off, matching the
   * honest-empty convention `toolSequenceMonitor` uses `null` for: here the
   * distinction is moot because a caller that gates on `citationRewriteEnabled`
   * already knows whether to trust this list, so an empty array (never
   * populated) reads correctly either way.
   */
  resolvedCitations: readonly ResolvedTurnCitation[]
  /** `TurnCitationStream.hallucinationCount`, or 0 when the flag is off. */
  citationHallucinationCount: number
  /** Whether this turn actually ran the live citation-rewriter path. */
  citationRewriteEnabled: boolean
}

export async function runSynthesisStage(args: {
  em: PariprashnaEmitter
  request: Request
  messages: UIMessage[]
  queryText: string
  params: TurnParams
  queryPlan: LegacyQueryPlan
  context: SynthesisContext
  /** Lane G1-A. Enforced → the pre-wire mortality scan is armed. */
  safetyDecision?: SafetyDecision
  /**
   * Lane G1-G. Every chart the CALLER is entitled to — at minimum this turn's
   * authenticated `chart_id`. Drives the answer-side entitlement scan. Omitted
   * → the scan contributes no rules (the flag-OFF path and older callers).
   */
  authorizedChartIds?: readonly string[]
  /**
   * Lane G1-G. Capabilities the plan stage deliberately removed. A call to one
   * of these is the strongest tool-sequence anomaly available.
   */
  removedCapabilities?: readonly string[]
  /**
   * Lane G2-B. This turn's own retrieval-pass-1 results
   * (`EvidenceStageOutput.validToolResults`) — the evidence scope the live
   * citation resolver prefetches labels against. Omitted → the citation
   * rewriter (when the flag is on) simply has no candidate ids to prefetch,
   * so every sentinel resolves unverified rather than silently widening scope
   * to some other source.
   */
  validToolResults?: readonly ToolBundle[]
  /**
   * Lane P2-E (PPR-33/GAP-14). Per-turn identity for the `llm_usage_events`
   * observability write — see `observability/synthesis_observation.ts` for
   * why this is optional and what happens when it is omitted (honest skip,
   * never a fabricated conversation_id/user_id). Omitted by every caller
   * today; wiring it through `app/api/pariprashna/route.ts` is a follow-up
   * outside this lane's `may_touch` scope.
   */
  observability?: SynthesisObservationIdentity
}): Promise<StageResult<SynthesisStageOutput>> {
  const { em, request, queryText, params, queryPlan, context } = args
  const { systemContentWithSummary, trimmedConversationHistory } = context
  const injectionContained = isInjectionContainmentEnabled()

  // ── Adapter + agentic loop wiring (SAME engine as consult). ────────────────
  const adapterId: StackId | undefined =
    STACK_TO_ADAPTER[params.selectedStack] ?? (params.modelMeta.provider as StackId | undefined)
  if (!adapterId) {
    em.error({ code: 'NO_ADAPTER', message: `No adapter for stack=${params.selectedStack}.`, retryable: false, phase: 'synthesize' })
    return halt('error')
  }
  // The CURRENT question, contained (lane G1-G). `queryText` itself is
  // untouched — persistence, the safety classifier and the receipt all read the
  // plain text; only what the synthesis model reads is wrapped.
  const adapterMessages = buildAdapterMessages(
    trimmedConversationHistory,
    injectionContained ? containUserQuestion(queryText) : queryText,
  )
  let adapterChatReq: ChatRequest = buildAdapterChatRequest(adapterMessages, params.modelId, systemContentWithSummary)
  const adapter = getAdapter(adapterId)
  const useAgenticLoop = AGENTIC_PROVIDERS.has(adapterId)
  const loopMaxIterations = params.deepDive ? DEEP_DIVE_MAX_ITERATIONS : 8

  if (useAgenticLoop) {
    const providerManifest = adapter.getManifest()
    const toolsCfg = adapter.tools({
      toolLoopMode: providerManifest.adaptiveToolLoop,
      tools: buildChatToolsFromNames(queryPlan.tools_authorized ?? []),
      maxIterations: loopMaxIterations,
    })
    adapterChatReq = { ...adapterChatReq, toolsConfig: toolsCfg, tools: toolsCfg.tools }
  }

  // ── Synthesis stream → prose blocks + adaptive-pass seams. ─────────────────
  em.phase({ phase: 'synthesize', status: 'start', pass_id: PASS_ONE })
  const synthesisStartedAt = Date.now()

  // Lane P2-E (PPR-33/GAP-14). One collector for the whole turn — TTFT, the
  // max provider-event gap, token usage, the register-lint firing rate and
  // delta→commit lag. Pure/in-memory; read once via `.snapshot()` below.
  const metrics = new TurnMetricsCollector(synthesisStartedAt)
  /** Set when the stream loop's catch fires — `undefined` means success. */
  let streamErrorCode: string | undefined
  /** Guards against double-finalizing (the abort path returns early). */
  let observabilityFinalized = false
  /**
   * Lane P2-E turn-end observability. Called from BOTH the client-abort early
   * return and the normal end of the function, so an aborted turn is measured
   * exactly like a completed one rather than silently dropped.
   */
  const finalizeObservability = (opts?: { aborted?: boolean }): void => {
    if (observabilityFinalized) return
    observabilityFinalized = true
    const synthesisFinishedAt = Date.now()
    const metricsSnapshot = metrics.snapshot()
    // ALWAYS-ON, real-today summary — SERVER LOG ONLY, deliberately NOT an
    // `em.flag` (never touches the SSE wire). Two independent reasons:
    //   1. Wire-protocol discipline: every event type is a client-visible
    //      protocol surface the PB-2 golden-stream harness
    //      (`tests/pariprashna/route_ports/route_golden_stream.test.ts`)
    //      byte-compares against a committed baseline; a NEW event type on
    //      every turn is a real protocol change, not an internals-only one,
    //      and is out of this lane's scope to make.
    //   2. This content is inherently non-deterministic (wall-clock latency,
    //      inter-event gaps) — the golden harness's OWN determinism check
    //      (same scenario run twice must produce identical records) would
    //      fail on it even if the event type were added to the baseline.
    //      Ops/cost telemetry does not need to be part of a byte-identical
    //      reader-facing contract.
    console.log(
      '[pariprashna/observability] synthesis_turn_metrics',
      JSON.stringify({
        ttft_ms: metricsSnapshot.ttft_ms,
        latency_ms: synthesisFinishedAt - synthesisStartedAt,
        max_event_gap_ms: metricsSnapshot.max_event_gap_ms,
        events: metricsSnapshot.event_count,
        passes: metricsSnapshot.pass_count,
        register_lint_fires: metricsSnapshot.register_lint.fires,
        register_lint_delta_calls: metricsSnapshot.register_lint.delta_calls,
        delta_commit_lag_avg_ms:
          metricsSnapshot.delta_commit_lag_ms.count > 0
            ? Math.round(metricsSnapshot.delta_commit_lag_ms.total_ms / metricsSnapshot.delta_commit_lag_ms.count)
            : null,
        aborted: opts?.aborted === true,
      }),
    )
    // Fire-and-forget: the EXISTING llm_usage_events schema (migration 001,
    // `channel` migration 574) this lane wires. Never awaited — a telemetry
    // write must not add latency to turn completion (same discipline
    // `stream_capture.ts`/`ring_buffer.ts` already use on this hot path).
    void recordSynthesisTurnObservation({
      identity: args.observability,
      stackId: adapterId,
      modelId: params.modelId,
      startedAt: new Date(synthesisStartedAt),
      finishedAt: new Date(synthesisFinishedAt),
      status: opts?.aborted || streamErrorCode ? 'error' : 'success',
      errorCode: opts?.aborted ? 'client_aborted' : streamErrorCode,
      snapshot: metricsSnapshot,
    })
  }

  // Pass/seam state — derived PURELY from the engine's own control flow
  // (tool-use events after prose), never from text/prose heuristics.
  // ── The PRE-WIRE pass's rule set (G1-A mortality + G1-G entitlement). ──────
  // ONE pass over the prose, TWO pattern classes, each armed by its own flag —
  // the fold TA §14A.1 asks for ("the register lint already walks the text;
  // entitlement checking is a second pattern class in the same pass"). An empty
  // `authorizedChartIds` is legal and means every chart reference is foreign,
  // which is the correct fail-closed reading of "entitlements unresolved".
  const entitlementRules =
    injectionContained
      ? buildEntitlementScanRules({ authorizedChartIds: args.authorizedChartIds ?? [] })
      : []
  const mortalityRulesEnabled = args.safetyDecision?.enforced === true
  const prewireArmed = mortalityRulesEnabled || entitlementRules.length > 0

  // ── Lane G3-D (P2-L, PPR-04) — voice enforcement. ──────────────────────────
  // Computed once per turn: `difficultFindingActive` is meaningless while the
  // lane itself is off, and it is the same turn-level "difficult finding"
  // proxy the per-delta pass below and the assembler's whole-block backstop
  // both read (see `voice/pacing.ts`'s `isDifficultFindingActive`).
  const voiceEnforcementEnabled = isVoiceEnforcementEnabled()
  const difficultFindingActive = voiceEnforcementEnabled && isDifficultFindingActive(args.safetyDecision)

  const assembler = new ReadingPartsAssembler(
    em,
    PASS_ONE,
    mortalityRulesEnabled,
    entitlementRules,
    isSemanticBlocksEnabled(),
    // Lane P2-E: real delta→commit lag, measured inside the assembler itself
    // (see `reading_parts.ts` — an internal role-switch commit would be
    // invisible to a lag measured from out here).
    (lagMs) => metrics.recordDeltaCommitLag(lagMs),
    voiceEnforcementEnabled,
    difficultFindingActive,
  )
  let proseSeenInPass = false
  let awaitingResume = false
  let lastToolInSeam = ''

  // ── SAFETY: the PRE-WIRE mortality scan (lane G1-A · HS-1 point (c)). ──────
  // The third and last of HS-1's three controls, and the only one that does not
  // depend on either the planner or the model cooperating. It holds prose back
  // to the last SENTENCE boundary (bounded — MAX_HOLDBACK_CHARS) so a
  // "…around 2047." cannot be split across two deltas and slip out one half at
  // a time — the residual the register-leak lint documents and accepts for
  // internal identifiers, and which is not acceptable here.
  //
  // `null` when NEITHER pattern class is armed — with both flags off there is
  // no hold-back, no behaviour change, and the stream is byte-for-byte what it
  // is today. Note the honest consequence of G1-G's widening: arming injection
  // containment ALONE now builds the scanner, so the sentence-level hold-back
  // (and its latency shape — prose arriving sentence-wise rather than
  // token-wise) applies on that flag too, not only on the safety gate. That is
  // the price of scanning whole sentences, it is the same price G1-A documented,
  // and it is stated here rather than discovered after the flip.
  //
  // Lane G1-G widens the SAME scanner rather than adding a second one: the
  // holdback, the sentence splitting, the carried context across a stream seam
  // and the fail-closed path are exactly what a cross-tenant check needs, and a
  // parallel scanner would be a second copy of all four to keep in step.
  const mortalityScanner = prewireArmed
    ? new StreamingMortalityScanner(undefined, {
        extraRules: entitlementRules,
        mortalityRulesEnabled,
      })
    : null
  let prewireHitsReported = 0
  let entitlementHitsReported = 0
  const reportEntitlementHits = (): void => {
    if (!mortalityScanner) return
    if (mortalityScanner.extraHits.length <= entitlementHitsReported) return
    const fresh = mortalityScanner.extraHits.slice(entitlementHitsReported)
    entitlementHitsReported = mortalityScanner.extraHits.length
    // Loud on the server: reaching this line means generated prose named a chart
    // this session is not entitled to read — a cross-tenant confidentiality
    // event, not a phrasing nit. Rule ids only; the token itself is never logged
    // (it is the identifier the redaction exists to protect) and its hash is on
    // the hit for correlation.
    console.error(
      '[pariprashna/injection] PRE-WIRE entitlement leak redacted — generated prose referenced a chart outside the caller entitlements:',
      fresh.map((h) => ({ rule: h.rule, span: h.redacted_span_hash, removed: h.caused_redaction })),
    )
    em.flag({
      code: 'injection_entitlement_leak_redacted',
      level: 'error',
      detail: `${fresh.length} sentence(s) referencing an unauthorized chart withheld at the output stage`,
    })
  }
  const reportPrewireHits = (): void => {
    if (!mortalityScanner) return
    reportEntitlementHits()
    if (mortalityScanner.hits.length > prewireHitsReported) {
      const n = mortalityScanner.hits.length - prewireHitsReported
      prewireHitsReported = mortalityScanner.hits.length
      // Loud on the server: reaching this line means the plan-time exclusion
      // AND the prompt policy both failed to stop a mortality-date composition.
      console.error(
        '[pariprashna/safety] PRE-WIRE mortality phrasing redacted — both upstream HS-1 controls missed:',
        mortalityScanner.hits.slice(-n).map((h) => h.rule),
      )
      em.flag({
        code: 'safety_prewire_mortality_redacted',
        level: 'error',
        detail: `${n} sentence(s) withheld at the output stage`,
      })
    }
  }
  // The reader-facing notice is emitted ONCE, after the stream closes and the
  // last block commits — never mid-stream, which would interleave a block into
  // an already-open one and break the assembler's block state machine.
  //
  // The hold-back buffer must be drained before ANY block commit, or the tail
  // of a block would be silently dropped. Called at every commit point.
  const drainScannerInto = (): void => {
    if (!mortalityScanner) return
    const rest = mortalityScanner.flush()
    reportPrewireHits()
    if (rest) assembler.appendProse(assembler.ensureBlock('prose'), rest)
  }

  // ── Lane G3-D voice enforcement — the SAME per-delta lint pass. ────────────
  // Chained immediately after whichever register-leak/citation-rewrite +
  // mortality-scan pass already ran on a delta (BOTH the citation-stream-on
  // and citation-stream-off branches below call this at the identical point —
  // right before the safe delta is appended), not a second independent walk
  // over the text. No-op (returns `text` unchanged) when the flag is off.
  const applyVoiceLint = (text: string): string => {
    if (!voiceEnforcementEnabled || !text) return text
    const voice = lintVoiceProse(text, { difficultFinding: difficultFindingActive })
    for (const f of voice.flags) {
      em.flag({ code: f.code, level: f.level, detail: f.detail })
    }
    return voice.clean
  }

  // ── INJECTION CONTAINMENT: the tool-sequence anomaly trace (G1-G · PPR-13). ─
  // Watches the AGENTIC LOOP specifically. Retrieval pass 1 iterates
  // `toolsAuthorized` and so cannot diverge from the plan by construction; the
  // loop can, because `synthesis/mcp_tool_executor.ts` dispatches whatever tool
  // name came back from the model without re-checking it against the authorized
  // set. See `injection/tool_sequence.ts` for the full account.
  //
  // FLAG, NOT BLOCK — TA §14A.1 rules that in those words. This callback records
  // and then dispatches unconditionally; it never refuses.
  const toolSequenceMonitor = injectionContained
    ? new ToolSequenceMonitor({
        authorized: queryPlan.tools_authorized ?? [],
        forbidden: args.removedCapabilities ?? [],
      })
    : null

  const baseLoopConfig: AgenticLoopConfig | undefined = LOOP_CONFIG_BY_PROVIDER[adapterId]
  const loopConfig: AgenticLoopConfig | undefined = baseLoopConfig
    ? { ...baseLoopConfig, maxIterations: loopMaxIterations }
    : undefined

  // ── G2-B: live citation rewriter (lane G2-B · PPR-08/FD-2/FD-6). ──────────
  // Flag-OFF path below (`citationStream === null`) is byte-for-byte the
  // pre-existing per-delta `lintReaderProse` call with no resolver — nothing
  // here runs a query, builds a rewriter, or changes control flow when the
  // flag is off.
  const citationRewriteEnabled = isFirstPaintCitationsEnabled()
  const onCitationWireEvent = (event: UnstampedCitationWireEvent): void => {
    if (event.type === 'citation.define') {
      em.citationDefine({
        index: event.index,
        signal_id: event.signal_id,
        layer: event.layer,
        snippet: event.snippet,
        reader_label: event.reader_label,
        grade: event.grade,
      })
    } else {
      em.flag({ code: event.code, level: event.level, detail: event.detail })
    }
  }
  let citationStream: TurnCitationStream | null = null
  if (citationRewriteEnabled) {
    const candidateIds = extractCandidateSignalIds({ validToolResults: args.validToolResults ?? [] })
    const labels = await fetchCandidateSignalLabels(candidateIds)
    citationStream = new TurnCitationStream({
      resolver: buildTurnCitationResolver(labels),
      modelId: params.modelId,
      onWireEvent: onCitationWireEvent,
    })
  }
  // Any text a citation-stream flush (a hold-back timeout or the terminal
  // `.end()`) produces must go through the SAME mortality-scan + append path
  // as an ordinary delta — see `drainScannerInto`'s own comment: the hold-back
  // buffer must be drained before any block commit, or the tail is silently
  // dropped. This is that same discipline for the citation rewriter's own
  // hold-back.
  const appendCitationFlushText = (text: string): void => {
    if (!text) return
    const safe = mortalityScanner ? mortalityScanner.push(text) : text
    reportPrewireHits()
    if (safe) assembler.appendProse(assembler.ensureBlock('prose'), safe)
  }

  try {
    const chatStream =
      useAgenticLoop && loopConfig
        ? runAgenticLoop(
            adapter,
            adapterChatReq,
            async (toolCall) => {
              toolSequenceMonitor?.record(toolCall.name)
              // The plan closure sanitizes `plan.tool_calls[].params`. It does
              // NOT reach here: `toolCall.input` is chosen by the MODEL, after
              // any injected content has entered its context, and
              // `mcp_tool_executor` forwards it verbatim as tool params. The
              // bridge overwrites `args.chart_id` only for `per_chart`
              // capabilities, so for any other scope a foreign identity param
              // would survive into the handler. Same rejection, same rule set,
              // applied at the second door into the same function.
              if (injectionContained) {
                const rejected = rejectIdentityParams(
                  toolCall.input as Record<string, unknown>,
                  queryPlan.chart_id,
                )
                if (rejected.length > 0) {
                  console.error(
                    '[pariprashna/injection] REJECTED model-supplied identity params from an agentic tool call:',
                    { tool: toolCall.name, keys: rejected },
                  )
                  em.flag({
                    code: 'injection_tool_input_identity_param_rejected',
                    level: 'error',
                    detail: `${rejected.length} model-supplied identity parameter(s) rejected from a mid-turn tool call`,
                  })
                }
              }
              const output = await executeMCPTool(toolCall, { queryPlan })
              // A tool result is untrusted content that re-enters the model's
              // context as a `role: 'user'` turn (`synthesis/agentic_loop.ts`) —
              // structurally indistinguishable from the reader speaking, for any
              // provider that flattens tool results. Contained for exactly that
              // reason, and containment happens HERE rather than inside
              // `executeMCPTool` so the shared executor stays byte-identical for
              // the consult door, which is not in this lane's scope.
              return injectionContained ? containToolResult(toolCall.name, output) : output
            },
            loopConfig,
          )
        : adapter.chat(adapterChatReq)

    for await (const event of chatStream) {
      // Lane P2-E. Observes every raw event (TTFT, max inter-event gap, token
      // usage from 'usage' events) without altering it — the same event
      // object flows into the branches below untouched.
      metrics.recordEvent(event)
      if (request.signal.aborted) {
        appendCitationFlushText(citationStream?.end() ?? '')
        drainScannerInto()
        assembler.commitBlock()
        finalizeObservability({ aborted: true })
        return halt('aborted')
      }
      if (event.type === 'text_delta') {
        if (awaitingResume) {
          // Prose resumed after the engine re-entered retrieval → close seam.
          em.seamSet({ pass_id: assembler.passId, summary: lastToolInSeam ? `Consulted ${lastToolInSeam}` : 'Continued analysis' })
          em.phase({ phase: 'synthesize', status: 'start', pass_id: assembler.passId })
          awaitingResume = false
        }
        const blk: OpenBlock = assembler.ensureBlock('prose')
        if (citationStream) {
          // G2-B live path: the rewriter resolves sentinels to inline markers
          // + fires `citation.define`/`flag` wire events DURING streaming, and
          // is itself the register-leak lint's single lint/emit exit
          // (rewriter.ts) — no separate `lintReaderProse` call here. Lane P2-E
          // residual: `metrics.recordRegisterLint` is NOT called on this path —
          // the rewriter doesn't expose a comparable leak count today, and
          // fabricating one would violate §N.8. When first-paint citations is
          // on, the register-lint-firing-rate metric under-counts; both flags
          // default off, so this is a disclosed gap, not a live one.
          const rewritten = citationStream.write(event.text)
          // HS-1 point (c): same ordering as the flag-OFF path below — the
          // mortality scan runs AFTER the citation/register-leak pass.
          const safeDelta = mortalityScanner ? mortalityScanner.push(rewritten) : rewritten
          reportPrewireHits()
          // Lane G3-D: SAME pass, chained last (see `applyVoiceLint` above).
          const voiceSafeDelta = applyVoiceLint(safeDelta)
          if (voiceSafeDelta) assembler.appendProse(blk, voiceSafeDelta)
        } else {
          // Gate 11 [integrity]: lint EVERY delta chunk before it reaches the
          // wire — the model's own prose directly references internal register
          // acronyms (confirmed in production: "(UCN §...)", "Cross-Domain
          // Linkage Matrix (CDLM)"), independent of the citation-sentinel path
          // this route already guards. Never fails the turn; a hit is scrubbed
          // and reported as a telemetry flag. Residual: a leak pattern split
          // exactly across a delta chunk boundary can still slip through here —
          // the assembler's whole-block lint on commit is the backstop.
          const deltaLint = lintReaderProse(event.text)
          const cleanDelta = deltaLint.clean
          // Lane P2-E: the register-lint firing rate — "the health signal that
          // the primary defenses work" (roadmap line 91). Every delta counts as
          // one measurement, firing or not; see `TurnMetricsCollector` docstring.
          metrics.recordRegisterLint(deltaLint.leakCount)
          if (deltaLint.leakCount > 0) {
            em.flag({
              code: 'register_leak_scrubbed',
              level: 'warn',
              detail: `${deltaLint.leakCount} internal identifier(s) scrubbed from streamed prose`,
            })
          }
          // HS-1 point (c): the mortality scan runs AFTER the register lint (the
          // lint's redactions cannot create a mortality phrase, only remove
          // identifiers) and returns only sentence-complete, scanned text. When
          // the gate is off, `mortalityScanner` is null and this is a pass-through.
          const safeDelta = mortalityScanner ? mortalityScanner.push(cleanDelta) : cleanDelta
          reportPrewireHits()
          // Lane G3-D: SAME pass, chained last (see `applyVoiceLint` above).
          const voiceSafeDelta = applyVoiceLint(safeDelta)
          if (voiceSafeDelta) assembler.appendProse(blk, voiceSafeDelta)
        }
        proseSeenInPass = true
        // ── Lane G3-D pacing policy — "shorter committed blocks" for difficult
        // findings. A pure BLOCK-granularity effect (never touches `passId` or
        // emits a seam), so it cannot violate this file's own documented
        // PASS/SEAM TRUTH invariant. `blk` is still the block just appended to
        // in whichever branch ran above.
        if (voiceEnforcementEnabled && difficultFindingActive && shouldForceDifficultBlockBreak(blk.text)) {
          const lengthAtBreak = blk.text.length
          assembler.commitBlock()
          em.flag({
            code: 'voice_pacing_block_shortened',
            level: 'info',
            detail: `committed a difficult-finding block early at ${lengthAtBreak} chars (pacing policy)`,
          })
        }
      } else if (event.type === 'thinking_delta') {
        appendCitationFlushText(citationStream?.tick() ?? '')
        const blk = assembler.ensureBlock('thinking')
        assembler.appendThinking(blk, event.thinking)
      } else if (event.type === 'tool_use_start') {
        appendCitationFlushText(citationStream?.tick() ?? '')
        em.activity({ key: `pass${assembler.passId}:tool:${event.id}`, label_key: resolveActivityLabel(event.name), pass_id: assembler.passId, status: 'running' })
      } else if (event.type === 'tool_use_complete') {
        // Engine re-entered retrieval. If prose was already emitted this pass,
        // THIS is a pass boundary (real control-flow truth).
        appendCitationFlushText(citationStream?.tick() ?? '')
        drainScannerInto()
        assembler.commitBlock()
        if (proseSeenInPass) {
          assembler.passId += 1
          metrics.recordPass()
          proseSeenInPass = false
          lastToolInSeam = event.name
          em.phase({ phase: 'retrieve', status: 'start', pass_id: assembler.passId })
          em.seamOpen({ pass_id: assembler.passId, label_key: `pariprashna.pass.${assembler.passId}` })
          awaitingResume = true
        } else {
          lastToolInSeam = event.name
        }
        em.activity({ key: `pass${assembler.passId}:tool:${event.id}`, label_key: resolveActivityLabel(event.name), pass_id: assembler.passId, status: 'done' })
      } else if (event.type === 'error') {
        console.error('[pariprashna] adapter error event:', event.error)
        em.flag({ code: 'adapter_error', level: 'warn', detail: event.error })
      }
    }
  } catch (adapterErr) {
    console.error('[pariprashna] synthesis stream error:', adapterErr)
    em.flag({ code: 'synthesis_stream_error', level: 'error', detail: String(adapterErr) })
    streamErrorCode = extractStreamErrorCode(adapterErr)
  }
  // Terminal citation-stream flush — exactly once per turn (the abort branch
  // above is the other terminal path and returns before reaching here).
  appendCitationFlushText(citationStream?.end() ?? '')
  drainScannerInto()
  assembler.commitBlock()
  // A scan that FAILED (not "found nothing") is reported as its own flag. The
  // scanner fails closed — `scanMortalityPhrasing` returns '' rather than the
  // input — so a failure shows up as missing prose, and this flag is what says
  // why rather than leaving it looking like the model went quiet.
  //
  // The wording is conditional (G1-G) because the same scanner can now be armed
  // with ONLY the entitlement rules, and calling that failure "the mortality
  // scan" would name the wrong control in the one message an operator reads
  // during an incident. When mortality rules ARE armed the string is G1-A's,
  // byte-for-byte.
  if (mortalityScanner?.scanFailed) {
    em.flag({
      code: 'safety_prewire_scan_failed',
      level: 'error',
      detail: mortalityRulesEnabled
        ? 'the pre-wire mortality scan errored; the affected span was withheld (fail-closed)'
        : 'the pre-wire entitlement scan errored; the affected span was withheld (fail-closed)',
    })
  }
  if (mortalityScanner && mortalityScanner.hits.length > 0) {
    em.blockOpen({ block_id: 'safety-prewire-notice', pass_id: assembler.passId, role: 'prose' })
    em.blockDelta({ block_id: 'safety-prewire-notice', delta: PREWIRE_REDACTION_NOTICE })
    em.blockCommit({ block_id: 'safety-prewire-notice', text: PREWIRE_REDACTION_NOTICE })
  }
  // The G1-G counterpart notice. A separate block from the mortality one because
  // they are separate withholdings with separate reasons — a turn can trip both,
  // and collapsing them would tell the reader the wrong thing about one of them.
  // Fires only when a redaction ACTUALLY happened (`caused_redaction`): a leak
  // that a mortality rule was already removing is worth logging, but does not
  // earn a second reader-facing notice about a sentence that was going anyway.
  const entitlementRedactions = (mortalityScanner?.extraHits ?? []).filter((h) => h.caused_redaction)
  if (entitlementRedactions.length > 0) {
    em.blockOpen({ block_id: 'injection-entitlement-notice', pass_id: assembler.passId, role: 'prose' })
    em.blockDelta({ block_id: 'injection-entitlement-notice', delta: ENTITLEMENT_REDACTION_NOTICE })
    em.blockCommit({ block_id: 'injection-entitlement-notice', text: ENTITLEMENT_REDACTION_NOTICE })
  }
  // The tool-sequence trace flag (G1-G · PPR-13). Codes + counts only; the raw
  // capability names stay in the server log, the same gate-11 discipline the
  // NO-LEAKAGE and mortality-exclusion flags follow.
  if (toolSequenceMonitor?.anomalous) {
    const trace = toolSequenceMonitor.traceFlag()
    console.warn(
      '[pariprashna/injection] tool-sequence anomaly (trace only — never a block):',
      toolSequenceMonitor.anomalies,
    )
    em.flag({
      code: 'injection_tool_sequence_anomaly',
      level: toolSequenceMonitor.severity(),
      detail: `${trace.anomaly_count} tool-sequence anomal${trace.anomaly_count === 1 ? 'y' : 'ies'} in ${trace.total_calls} call(s): ${trace.codes.join(', ')}`,
    })
  }
  em.phase({ phase: 'synthesize', status: 'end', pass_id: assembler.passId, ms: Date.now() - synthesisStartedAt })

  finalizeObservability()

  return proceed({
    assembler,
    accumulatedText: assembler.accumulatedText,
    synthesisStartedAt,
    finalPassId: assembler.passId,
    toolSequenceMonitor,
    resolvedCitations: citationStream?.resolvedCitations ?? [],
    citationHallucinationCount: citationStream?.hallucinationCount ?? 0,
    citationRewriteEnabled,
  })
}
