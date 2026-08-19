/**
 * /api/pariprashna — Paripraśna consult route (lane PB-1/S-1, wave DHĀRĀ).
 *
 * A FORK (never an edit) of `/api/chat/consult/route.ts`. The consult route
 * runs the whole planner → tool-fetch → bundle pipeline BEFORE opening its
 * stream (inside `runAdapterDispatch`), so its first bytes only arrive after
 * the planner (an LLM call, seconds) completes, and a planner fault surfaces as
 * a post-nothing HTTP 4xx/5xx.
 *
 * Paripraśna INVERTS that ordering: the SSE stream opens and writes `turn.open`
 * + `phase{plan,start}` as its FIRST bytes, BEFORE the planner runs. Everything
 * heavy (chart resolution, planner, retrieval, synthesis, persistence) then runs
 * INSIDE the stream, and every fault — planner, chart, adapter — becomes an
 * in-stream `error` event, never a post-headers HTTP status.
 *
 * What it SHARES with consult (in-process, no forking of engine internals):
 *   • the SAME in-process retrieval registry (`getToolByName` → `getCapability`
 *     → `cap.handler(...)` — a direct function call, ZERO HTTP to any MCP edge);
 *   • the SAME planner (`callPipelinePlanner`), floor compiler, budget arbiter,
 *     NO-LEAKAGE filter, agentic loop (`runAgenticLoop` + `executeMCPTool`);
 *   • the SAME persistence path (`runOnFinishWriteThrough` → the existing
 *     `writeConversationMessages`), with the prediction-candidate detector left
 *     wired exactly as it fires today (it lives inside that shared helper).
 *
 * What differs: the wire format. Instead of AI-SDK UIMessage data-parts, this
 * route emits the typed Paripraśna vocabulary (`@/lib/pariprashna/protocol`),
 * Zod-validated end-to-end with ZERO `as any` in the writer path.
 *
 * ── P0-C / RF-1 PORTS REFACTOR (behaviour-preserving) ───────────────────────
 * This file was 1,179 lines and was the collision point for six later lanes.
 * Its pipeline now lives in `@/lib/pariprashna/pipeline/*` as the typed stage
 * modules PARIPRASHNA_ARCHITECTURE §3 names, and this file is the SHELL: it
 * mints the turn's identity, opens the stream, owns the emitter and the single
 * `finish()`, calls the stages in order, and maps the one fatal catch. Nothing
 * about the wire changed — the equality is proven scenario-by-scenario by
 * `tests/pariprashna/route_ports/`, whose baselines were captured against the
 * pre-refactor file (git history, commit order).
 *
 * WHERE TO MAKE A CHANGE NOW (the whole point of the refactor):
 *   safety / injection / entitlement  → pipeline/safety_gate.ts
 *   planning, floors, NO-LEAKAGE      → pipeline/plan_stage.ts
 *   retrieval, evidence, completeness → pipeline/evidence_stage.ts
 *   synthesis stream, passes, seams   → pipeline/synthesis_stage.ts
 *   citation / grounding validation   → pipeline/validation_stage.ts
 *   block + canonical-part vocabulary → pipeline/reading_parts.ts
 *   provenance + reader receipt       → pipeline/receipt_stage.ts
 *   write-through + canonical write   → pipeline/persistence_stage.ts
 *
 * Lane scope (PB-1/S-1): protocol + route only. The existing consult route is
 * byte-identical (must_not_touch). Verbosity binding is stubbed — see TODO(PB-4).
 */

import { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { openTurnBuffer, appendBufferedEvent } from '@/lib/pariprashna/protocol/ring_buffer'
import { beginTurnCapture, captureEvent, endTurnCapture } from '@/lib/pariprashna/protocol/stream_capture'

import type { TurnIdentity } from '@/lib/pariprashna/pipeline/stage_context'
import { admitRequest, admitWithinLimits, bindTurnParams, authorizeTurn } from '@/lib/pariprashna/pipeline/safety_gate'
import { runPlanStage } from '@/lib/pariprashna/pipeline/plan_stage'
import { runEvidenceStage } from '@/lib/pariprashna/pipeline/evidence_stage'
import { assembleSynthesisContext, runSynthesisStage } from '@/lib/pariprashna/pipeline/synthesis_stage'
import { runValidationStage } from '@/lib/pariprashna/pipeline/validation_stage'
import { emitCompletenessReceipt } from '@/lib/pariprashna/pipeline/receipt_stage'
import { runPersistenceStage } from '@/lib/pariprashna/pipeline/persistence_stage'

export const maxDuration = 120

export async function POST(request: Request): Promise<Response> {
  const requestStartedAt = Date.now()

  // ── Pre-stream: auth + validation only (fast; real HTTP responses). ────────
  // Everything DB/LLM-bound runs INSIDE the stream so `turn.open` is the first
  // byte and every downstream fault is an in-stream `error` event.
  const admission = await admitRequest(request)
  if (!admission.admitted) return admission.response
  const { user, body, chartId, messages } = admission.value

  // ── Bind request params (pure — no DB/LLM). ────────────────────────────────
  const params = await bindTurnParams(body, request)

  // ── NCD-8 pre-dispatch limits (web door). ──────────────────────────────────
  // Still PRE-STREAM, so a ceiling refusal is a real HTTP 429 with a branchable
  // code rather than an in-stream error — and it lands before the planner, the
  // first LLM call of the turn. Needs `params` because the ceiling is evaluated
  // against the model this turn actually bound. Flag-OFF by default.
  const withinLimits = await admitWithinLimits({ user, params })
  if (!withinLimits.admitted) return withinLimits.response

  // Conversation identity is resolvable synchronously (generated for a first
  // turn) so `turn.open` can carry it before any DB round-trip.
  const clientConversationId = body.conversationId
  const identity: TurnIdentity = {
    chartId,
    clientConversationId,
    isFirstTurn: !clientConversationId,
    conversationId: clientConversationId ?? crypto.randomUUID(),
    turnId: crypto.randomUUID(),
    queryId: crypto.randomUUID(),
  }
  const { turnId, conversationId } = identity

  // ── Open the stream. `turn.open` + `phase{plan,start}` are the FIRST bytes. ─
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      // PB-2/M-5: seed this turn's ring buffer BEFORE the first event is
      // emitted, so a resume request that races the very first byte still
      // finds turn metadata. Awaited (not fire-and-forget) for exactly that
      // reason — the write is a single Redis SET (or in-memory Map.set) and
      // is not on the model-latency critical path.
      await openTurnBuffer({ turnId, chartId, conversationId })
      // SAMĀPTI/B-PB8-BYTEEQ: opt-in, sampled, durable capture of this turn's
      // raw wire stream so BRIEF_PB-2 §G-1's "byte-equality against one real
      // deployed reading" can actually be run (see
      // protocol/stream_capture.ts). OFF unless PARIPRASHNA_STREAM_CAPTURE=1;
      // decided ONCE here so a turn is captured whole or not at all.
      beginTurnCapture({ turnId, conversationId, chartId })
      const em = new PariprashnaEmitter(controller, (event) => {
        void appendBufferedEvent(turnId, event)
        void captureEvent(turnId, event)
      })

      // FIRST BYTES — before the planner, before any DB/LLM work.
      em.turnOpen({
        turn_id: turnId,
        conversation_id: conversationId,
        chart_id: chartId,
        model_id: params.modelId,
        reading_depth: params.readingDepth,
        length_tier: params.lengthTier,
      })
      em.phase({ phase: 'plan', status: 'start' })

      const finish = (status: 'ok' | 'error' | 'aborted'): void => {
        em.turnClose({ turn_id: turnId, status, ms: Date.now() - requestStartedAt })
        em.close()
        // Release the in-process capture mark AFTER the terminal turn.close has
        // been emitted (and therefore captured) — never before.
        endTurnCapture(turnId)
      }

      try {
        // ── Entitlement + conversation resolution (PPR-11, fail-closed). ─────
        const authorized = await authorizeTurn({ em, user, identity })
        if (authorized.halted) return finish(authorized.status)

        // ── Plan: query text → planner → budgets → floors → NO-LEAKAGE. ──────
        const planned = await runPlanStage({ em, request, messages, identity, params })
        if (planned.halted) return finish(planned.status)
        const {
          plan,
          queryPlan,
          manifest,
          orientationPromise,
          queryText,
          lastUserMessage,
          toolsAuthorized,
          plannerModelId,
          plannerLatencyMs,
          judgmentFlags,
        } = planned.value

        // ── Evidence: retrieval pass 1 + completeness receipt. ───────────────
        const evidence = await runEvidenceStage({
          em,
          request,
          chartId,
          userUid: user.uid,
          plan,
          queryPlan,
          manifest,
          toolsAuthorized,
          orientationPromise,
        })

        // ── Synthesis: prompt assembly, then the streaming interpretation. ───
        const synthesisContext = await assembleSynthesisContext({
          messages,
          bundle: evidence.bundle,
          plan,
          orientation: evidence.orientation,
          conversationId,
        })
        const synthesized = await runSynthesisStage({
          em,
          request,
          messages,
          queryText,
          params,
          queryPlan,
          context: synthesisContext,
        })
        if (synthesized.halted) return finish(synthesized.status)
        const { assembler, accumulatedText, synthesisStartedAt } = synthesized.value

        // ── Validation: the B.11 citation gate (adapter-path parity). ────────
        const citationGate = runValidationStage({
          em,
          accumulatedText,
          bundle: evidence.bundle,
          validToolResults: evidence.validToolResults,
          plan,
          judgmentFlags,
        })

        // ── Finalize: provenance stamp, write-through, canonical turn write. ─
        await runPersistenceStage({
          em,
          identity,
          params,
          user,
          isSuperAdmin: authorized.value.isSuperAdmin,
          messages,
          lastUserMessage,
          plan,
          plannerModelId,
          plannerLatencyMs,
          committedBlocks: assembler.committedBlocks,
          accumulatedText,
          validToolResults: evidence.validToolResults,
          citationGate,
          synthesisStartedAt,
        })

        // Completeness + aggregated judgment flags (grade/flag — always emitted).
        emitCompletenessReceipt({ em, completenessReceipt: evidence.completenessReceipt })

        em.phase({ phase: 'finalize', status: 'end' })
        return finish('ok')
      } catch (fatal) {
        console.error('[pariprashna] fatal in-stream error:', fatal)
        em.error({ code: 'INTERNAL', message: fatal instanceof Error ? fatal.message : String(fatal), retryable: false })
        return finish('error')
      }
    },
  })

  return new Response(stream, {
    headers: {
      'content-type': 'text/event-stream; charset=utf-8',
      'cache-control': 'no-cache, no-transform',
      connection: 'keep-alive',
      'x-accel-buffering': 'no',
    },
  })
}
