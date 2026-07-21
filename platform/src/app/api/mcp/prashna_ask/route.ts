/**
 * /api/mcp/prashna_ask — internal, service-to-service-only engine route for the
 * prashna_ask MCP tool.
 *
 * ── Why this route exists (W6 redesign) ──────────────────────────────────────
 * Investigation for Task 4 (the prashna_ask↔engine bridge) found that
 * `callPipelinePlanner` and `compileFloorForPlan` — the FROZEN engine — only run
 * inside the `platform` deployable, and that `platform-mcp` has no import path to
 * them. So prashna_ask's actual engine call, NO-LEAKAGE enforcement, and cost-cap
 * tracking all have to live here, in `platform`, behind a route `platform-mcp`
 * calls over HTTP — mirroring the existing `/api/mcp/primitives/[tool]` pattern,
 * not inventing a new one.
 *
 * ── Auth (SAME mechanism every other /api/mcp/* route uses) ─────────────────
 * `platform-mcp/src/client.ts` reaches `platform` via a Google-signed OIDC
 * identity token (`GoogleAuth.getIdTokenClient(PLATFORM_URL)`) presented as
 * `Authorization: Bearer <token>`. That token's cryptographic verification is
 * Cloud Run's own IAM gate (`run.invoker` on amjis-web for amjis-mcp-runtime) —
 * infrastructure-level, not application code. The application-level companion
 * check every existing `/api/mcp/*` route layers on top is `validateServiceToken`
 * (X-MCP-Internal-Token shared secret, Layer 1) plus the resolved-principal
 * headers `X-MCP-User` / `X-MCP-Key-Id` (Layer 2). This route reuses exactly that
 * two-layer pattern — see `/api/mcp/primitives/[tool]/route.ts` for the sibling
 * implementation this one was copied from. (`@/lib/auth/oidc.ts`'s
 * `verifyOidcToken` is a DIFFERENT, currently-unused-in-production mechanism for a
 * different caller — Cloud Scheduler — not the platform-mcp→platform path; it is
 * not the "existing OIDC-verification mechanism" for THIS caller.)
 *
 * Per-call chart-access authorization reuses `authorizeChartAccess` (same brain
 * `/api/mcp/primitives/[tool]/route.ts` calls for per-chart primitives).
 *
 * ── Contract ──────────────────────────────────────────────────────────────────
 * POST body: { chart_id: string, question: string, response_format?: string,
 * entitlement?: string }.
 *
 * `entitlement` in the body is accepted for logging/observability only — the
 * cost caps that actually govern this call are resolved from the SERVER-VERIFIED
 * role (`resolveMcpPrincipalRole(userUid)`), never from a client-supplied field.
 * Trusting a client-supplied entitlement for a privilege decision would let any
 * caller mint itself an elevated cost-cap tier.
 *
 * ── Engine invocation sequence ────────────────────────────────────────────────
 * Follows `/api/chat/consult/route.ts`'s real sequence exactly (see that file for
 * the full annotated version this is derived from): callPipelinePlanner →
 * arbitrateBudgets → derive toolsAuthorized → compileFloorForPlan (when
 * plan.scope_tuple is present) → ensureB11WholeChartReadFloor →
 * ensureDashaContextFloor. `filterLeakedCapabilities` (Part A) is then applied to
 * the resulting toolsAuthorized BEFORE any tool actually dispatches.
 *
 * Unlike the consult route's `Promise.all` parallel tool-fetch, this route
 * dispatches tools SEQUENTIALLY, one at a time, calling
 * `CostCapTracker.checkAndRecordCall()` before each dispatch — parallel dispatch
 * cannot honor a "stop after N calls / after T ms" contract mid-flight. When a cap
 * trips, dispatch stops immediately; the response reports whatever tool results
 * were already gathered plus a completeness receipt naming the unserved tools and
 * a `judgment_flags` entry naming which cap tripped. Per ratified doctrine, this
 * is never silently truncated and presented as complete.
 *
 * Runs synchronously, in one HTTP response, up to the resolved
 * `maxWallClockMs` (a few minutes for elevated entitlements) — a later task
 * builds the async job-handle wrapper around this call on the platform-mcp side.
 */

import 'server-only'
import { NextResponse } from 'next/server'
// Trigger capability registration for all layers (L0–L5) at module load — same
// requirement as /api/mcp/primitives/[tool]/route.ts.
import '@/lib/retrieval/registry/catalog'
import { validateServiceToken } from '@/lib/mcp/service_token'
import { resolveMcpPrincipalRole } from '@/lib/mcp/auth'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { query } from '@/lib/db/client'
import { buildErrorEnvelope, buildEntitlementDenialEnvelope } from '@/lib/mcp/epistemics'
import { callPipelinePlanner } from '@/lib/pipeline/pipeline_planner'
import { arbitrateBudgets } from '@/lib/pipeline/budget_arbiter'
import {
  compileFloorForPlan,
  ensureB11WholeChartReadFloor,
  ensureDashaContextFloor,
} from '@/lib/pipeline/compiled_floor_adapter'
import { filterLeakedCapabilities } from '@/lib/pipeline/no_leakage_filter'
import { CostCapTracker, resolveCostCapsForEntitlement } from '@/lib/pipeline/cost_caps'
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import { DEFAULT_STACK_ID } from '@/lib/models/registry'
import { getEffectiveModel } from '@/lib/models/runtime_config'

// Wall-clock generous enough for the elevated super_admin cost cap (300s) plus
// margin for the HTTP round trip; the resolved per-entitlement cap enforces the
// tighter internal budget.
export const maxDuration = 320

interface PrashnaAskRequestBody {
  chart_id?: string
  question?: string
  response_format?: string
  /** Logging/observability only — see file header. Never used for privilege. */
  entitlement?: string
}

interface ToolDispatchOutcome {
  tool_name: string
  status: 'done' | 'error'
  result_count: number
  latency_ms: number
}

export async function POST(request: Request) {
  // ── Layer 1: service-to-service auth (same as every other /api/mcp/* route) ──
  if (!validateServiceToken(request)) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'auth',
        message: 'Invalid service token',
        remediation: 'MCP server must pass MCP_INTERNAL_TOKEN header',
      }),
      { status: 401 },
    )
  }

  // ── Layer 2: resolved principal headers ──────────────────────────────────────
  const userUid = request.headers.get('x-mcp-user')
  const keyId = request.headers.get('x-mcp-key-id')
  if (!userUid || !keyId) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'auth',
        message: 'Missing principal headers (X-MCP-User, X-MCP-Key-Id)',
      }),
      { status: 401 },
    )
  }

  // ── Parse + validate body ─────────────────────────────────────────────────────
  let body: PrashnaAskRequestBody
  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      buildErrorEnvelope({ error_class: 'validation', message: 'Request body must be valid JSON' }),
      { status: 400 },
    )
  }

  const chartId = body.chart_id
  const question = body.question
  if (!chartId || !question || !question.trim()) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'validation',
        message: 'chart_id and question are both required',
      }),
      { status: 400 },
    )
  }

  // ── Per-call chart-access authorization (same brain as the primitives route) ─
  const role = await resolveMcpPrincipalRole(userUid)
  const perm = await authorizeChartAccess({ principal: { uid: userUid, role }, chartId, db: { query } })
  if (perm === 'deny') {
    return NextResponse.json(
      buildEntitlementDenialEnvelope({ chart_id: chartId, permission_required: 'view' }),
      { status: 401 },
    )
  }

  // ── Cost-cap resolution — SERVER-VERIFIED role only, never the request body's
  // `entitlement` field (see file header). ────────────────────────────────────
  const costCaps = resolveCostCapsForEntitlement(role)
  const tracker = new CostCapTracker(costCaps)

  const queryId = crypto.randomUUID()

  // ── Engine invocation: callPipelinePlanner (same call consult/route.ts makes) ─
  const [plannerModelId, plannerFallbackModelId] = await Promise.all([
    getEffectiveModel(DEFAULT_STACK_ID, 'planner_fast', 'primary'),
    getEffectiveModel(DEFAULT_STACK_ID, 'planner_fast', 'fallback'),
  ])

  const plannerOutcome = await callPipelinePlanner(
    question,
    [],
    plannerModelId,
    chartId,
    undefined,
    queryId,
    plannerFallbackModelId,
  )

  if (plannerOutcome.outcome === 'clarification_needed') {
    return NextResponse.json({
      ok: true,
      trace_id: queryId,
      outcome: 'clarification_needed',
      question: plannerOutcome.question,
      missing_scope_dims: plannerOutcome.missing_scope_dims ?? [],
      suggested_options: plannerOutcome.suggested_options ?? [],
    })
  }
  if (plannerOutcome.outcome === 'fault') {
    return NextResponse.json(
      buildErrorEnvelope({
        trace_id: queryId,
        error_class: 'orchestrator_error',
        message: `Planner fault: ${plannerOutcome.reason}`,
        remediation: plannerOutcome.retryable ? 'Retry the same request.' : 'Rephrase the question.',
      }),
      { status: 422 },
    )
  }

  const plan = plannerOutcome.plan

  // ── Budget arbitration (identical to consult/route.ts) ───────────────────────
  const arbitrated = arbitrateBudgets(
    plan.tool_calls.map((tc) => ({ tool_name: tc.tool_name, priority: tc.priority, token_budget: tc.token_budget })),
    {
      synthesis_model_max_context: 128_000,
      system_prompt_reserve: 800,
      synthesis_guidance_reserve: plan.synthesis_guidance ? 200 : 0,
      safety_margin: 0.85,
      min_tokens_per_tool: 200,
    },
  )
  for (let i = 0; i < plan.tool_calls.length; i++) {
    plan.tool_calls[i].token_budget = arbitrated[i].token_budget
  }

  // ── toolsAuthorized derivation + B.11/dasha floor adoption (identical sequence
  // to consult/route.ts) ───────────────────────────────────────────────────────
  const toolsAuthorized = Array.from(new Set(plan.tool_calls.map((tc) => tc.tool_name)))

  if (plan.scope_tuple) {
    const compiledFloor = compileFloorForPlan(plan.scope_tuple, chartId)
    for (const tc of compiledFloor.toolCalls) {
      if (!toolsAuthorized.includes(tc.tool_name)) {
        plan.tool_calls.push(tc)
        toolsAuthorized.push(tc.tool_name)
      }
    }
  }
  ensureB11WholeChartReadFloor(plan, toolsAuthorized)
  ensureDashaContextFloor(plan, toolsAuthorized)

  // ── NO-LEAKAGE enforcement (Part A) — BEFORE any tool actually dispatches ────
  const dispatchableTools = filterLeakedCapabilities(toolsAuthorized)
  const dispatchableSet = new Set(dispatchableTools)
  const leakedTools = toolsAuthorized.filter((t) => !dispatchableSet.has(t))

  const paramsByTool = new Map<string, Record<string, unknown>>(
    plan.tool_calls.map((tc) => [tc.tool_name, tc.params]),
  )

  // ── Sequential, cost-cap-gated tool dispatch — STREAMED (W6 Part 1) ─────────
  //
  // The dispatch loop below is unchanged in what it computes and enforces
  // (same cap checks, same NO-LEAKAGE-filtered tool list, same per-tool
  // try/catch) — the only change is that instead of accumulating everything
  // silently and returning one NextResponse.json blob at the very end, the
  // loop body now lives inside a ReadableStream's `start()` and emits one
  // NDJSON progress line per completed dispatch iteration, ending with a
  // single `{"event":"final", ...}` line carrying the EXACT SAME body shape
  // this route returned before this change (verify against route.test.ts).
  //
  // Progress is emitted AFTER each iteration completes (not before) — a
  // caller polling prashna_status wants to know what has ALREADY happened
  // (which tool just finished, how many are done), not merely that dispatch
  // is about to attempt one. This also means the emitted `tools_dispatched_count`
  // is always accurate against `toolEventLog` at the moment of emission.
  //
  // Plan object handed to getToolByName().retrieve() — that wrapper reads
  // plan['chart_id'] directly (tool_name_bridge.ts's getToolByName) to build the
  // per_chart handler args, exactly like /api/mcp/primitives/[tool]/route.ts's
  // queryPlan. Passed as Record<string, unknown> (getToolByName's own return
  // type), not cast to the RetrievalTool/QueryPlan interface — that interface is
  // for the executeWithCache-compatible path consult/route.ts uses; this route
  // dispatches directly (no cache) so it uses getToolByName's native shape.
  const queryPlanLike: Record<string, unknown> = {
    query_plan_id: queryId,
    query_text: question,
    query_class: plan.query_class,
    domains: plan.domains ?? [],
    forward_looking: plan.forward_looking ?? false,
    tools_authorized: dispatchableTools,
    chart_id: chartId,
  }

  const encoder = new TextEncoder()
  const dispatchLoopStart = Date.now()

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        await runDispatchLoop(controller)
      } catch (err) {
        // Anything unexpected in the loop body (a non-serializable value in
        // toolResults, an emitProgress/JSON.stringify failure, etc.) must not
        // surface to the client as a bare stream-read exception with no
        // trace_id/chart_id to correlate it against. Emit a structured error
        // line — same NDJSON framing as `progress`/`final` — then close.
        console.error('[mcp:prashna_ask] stream body failed', err instanceof Error ? err.message : String(err))
        try {
          controller.enqueue(
            encoder.encode(
              JSON.stringify({
                event: 'error',
                trace_id: queryId,
                chart_id: chartId,
                message: err instanceof Error ? err.message : String(err),
              }) + '\n',
            ),
          )
          // Close normally so the reader actually receives the error line above.
          // ReadableStreamDefaultController.error() clears the internal queue —
          // calling it AFTER a successful enqueue would discard that chunk
          // before any reader consumes it, defeating the whole point of
          // reporting a structured error. controller.error() is reserved
          // below for the case where we couldn't even enqueue the error line.
          controller.close()
        } catch {
          controller.error(err)
        }
        return
      }
      controller.close()
    },
  })

  async function runDispatchLoop(controller: ReadableStreamDefaultController<Uint8Array>): Promise<void> {
      const toolResults: Array<{ tool_name: string; bundle: import('@/lib/retrieval/shared_types').ToolBundle }> = []
      const toolEventLog: ToolDispatchOutcome[] = []
      const judgmentFlags: string[] = []
      let costCapTripped: { reason: string; judgmentFlag: string } | null = null
      let unservedTools: string[] = []
      const unresolvedTools: string[] = []

      const emitProgress = (lastTool: string): void => {
        controller.enqueue(
          encoder.encode(
            JSON.stringify({
              event: 'progress',
              tools_dispatched_count: toolEventLog.length,
              cap_ceiling: { maxCalls: costCaps.maxCalls, maxWallClockMs: costCaps.maxWallClockMs },
              elapsed_ms: Date.now() - dispatchLoopStart,
              last_tool: lastTool,
            }) + '\n',
          ),
        )
      }

      for (let i = 0; i < dispatchableTools.length; i++) {
        const toolName = dispatchableTools[i]

        // Resolve BEFORE checking the cap — an unresolved tool name is not a real
        // dispatch attempt and must not consume a call-count slot from the budget.
        const tool = getToolByName(toolName)
        if (!tool) {
          // Unresolved name — not a cap event, but it IS a planned tool that never
          // ran, so it must be disclosed. Silently dropping it here would violate
          // this route's own "never presented as complete when something planned
          // didn't run" invariant just as surely as a cost-cap trip would.
          unresolvedTools.push(toolName)
          continue
        }

        const check = tracker.checkAndRecordCall()
        if (check.stopped) {
          costCapTripped = { reason: check.reason ?? 'unknown_cap', judgmentFlag: check.judgmentFlag ?? 'cost_cap_exceeded' }
          judgmentFlags.push(check.judgmentFlag ?? 'cost_cap_exceeded')
          unservedTools = dispatchableTools.slice(i)
          break
        }

        const toolStart = Date.now()
        try {
          const bundle = await tool.retrieve(queryPlanLike, paramsByTool.get(toolName))
          toolResults.push({ tool_name: toolName, bundle })
          toolEventLog.push({ tool_name: toolName, status: 'done', result_count: bundle.results.length, latency_ms: Date.now() - toolStart })
        } catch (err) {
          toolEventLog.push({ tool_name: toolName, status: 'error', result_count: 0, latency_ms: Date.now() - toolStart })
          console.error(`[mcp:prashna_ask] tool dispatch failed for ${toolName}`, err instanceof Error ? err.message : String(err))
        }

        emitProgress(toolName)
      }

      if (leakedTools.length > 0) {
        judgmentFlags.push('no_leakage_capabilities_stripped')
      }
      if (unresolvedTools.length > 0) {
        judgmentFlags.push('planned_tools_unresolved')
      }

      const isPartial = costCapTripped !== null || unresolvedTools.length > 0

      const finalBody = {
        ok: true,
        trace_id: queryId,
        chart_id: chartId,
        outcome: 'plan',
        query_class: plan.query_class,
        query_intent_summary: plan.query_intent_summary,
        completeness: {
          status: isPartial ? 'partial' : 'complete',
          tools_dispatched: toolEventLog,
          unserved_tools: unservedTools,
          unresolved_tools: unresolvedTools,
          stripped_leaked_capabilities: leakedTools,
          cap_tripped: costCapTripped?.reason ?? null,
        },
        judgment_flags: judgmentFlags,
        results: toolResults,
      }

      controller.enqueue(encoder.encode(JSON.stringify({ event: 'final', ...finalBody }) + '\n'))
  }

  return new Response(stream, {
    status: 200,
    headers: { 'Content-Type': 'application/x-ndjson' },
  })
}
