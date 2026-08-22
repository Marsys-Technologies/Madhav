/**
 * Paripraśna pipeline — SAFETY GATE (P0-C / RF-1).
 *
 * Ports covered TODAY (architecture §3): `NormalizedQuery` and
 * `EntitlementDecision`.
 *   · `admitRequest`  — pre-stream admission: authentication, the
 *     PARIPRASHNA_ENABLED rollback flag, body parse, and request validation.
 *     These are the ONLY checks that may answer with a real HTTP status: they
 *     run before the stream opens, so no header has been written yet.
 *   · `bindTurnParams` — pure parameter binding (no DB, no LLM).
 *   · `admitWithinLimits` — the NCD-8 pre-dispatch gate for the WEB door (one of
 *     the two doors the ruling names). Runs after `bindTurnParams` (it needs the
 *     bound synthesis model) and BEFORE the stream opens, so a refusal is a real
 *     HTTP 429 with a branchable code — a designed failure state, not a 500 and
 *     not an in-stream error the client has to parse out of an SSE body.
 *   · `authorizeTurn` — in-stream chart resolution, per-chart authorization
 *     (PPR-11, fail-closed), SUBJECT-CONSENT resolution (PPR-14, P1 lane G1-B,
 *     flag-gated OFF by default) and conversation resolution. Every fault here
 *     is an in-stream `error` EVENT, never an HTTP status — the stream is
 *     already open.
 *
 * Note the two are different questions and both must pass: `authorizeChartAccess`
 * asks whether the CALLER may touch this chart; `resolveSubjectConsent` asks
 * whether this SUBJECT's interpretive corpus may be served to anyone at all.
 *
 *   · `runSafetyPolicyGate` — the `SafetyPolicyDecision` port (PPR-12, P1 lane
 *     G1-A, flag-gated OFF by default). Runs AFTER `authorizeTurn` (it needs
 *     the consent lane's `subject_kind` for the NCD-4 branch) and BEFORE
 *     `runPlanStage` (§3: "a blocked class must never build a retrieval plan").
 *     A hard stop here is NOT an `error` event — it is a real, composed,
 *     deliberate answer, so the turn closes `ok` with a fixed prose block.
 *
 * INJECTION CONTAINMENT (PPR-13) IS NOT IN THIS MODULE, and that is a placement
 * decision rather than an absence. Lane G1-G built it as
 * `@/lib/pariprashna/injection`, wired into the stages whose data it actually
 * guards: the planner's inputs and the plan closure in `plan_stage.ts`, the
 * prompt containers + tool-sequence trace + answer-side entitlement scan in
 * `synthesis_stage.ts`, and the commit-time entitlement backstop in
 * `reading_parts.ts`. Nothing about it lives here because nothing about it
 * happens at admission time. It is flag-gated OFF by default
 * (`PARIPRASHNA_INJECTION_CONTAINMENT`), so with the flag off this route's
 * behaviour is unchanged and no claim of containment is being made (§N.8).
 */

import type { UIMessage } from 'ai'

import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import { getConversation, insertConversationWithId } from '@/lib/conversations'
import { configService } from '@/lib/config/index'
import { enforceTurnLimits } from '@/lib/limits'
import {
  DEFAULT_MODEL_ID,
  DEFAULT_STACK_ID,
  STACK_ROUTING,
  getModelMeta,
  isValidModelId,
  type ModelStack,
} from '@/lib/models/registry'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import {
  ReadingDepthSchema,
  LengthTierSchema,
  type ReadingDepth,
  type LengthTier,
} from '@/lib/pariprashna/protocol/events'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

import { halt, proceed, type StageResult, type TurnIdentity, type TurnParams } from './stage_context'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export interface RequestBody {
  chartId?: string
  conversationId?: string
  messages?: UIMessage[]
  /** Adapter stack (anthropic | gemini | gpt | deepseek | nim | marsys). */
  stack?: string
  /** PB-1/S-1 param: explicit synthesis model id. Binds directly when valid. */
  model_id?: string
  /** PB-1/S-1 param: 'auto' | 'deep_dive'. deep_dive forces the completeness path. */
  reading_depth?: string
  /** PB-1/S-1 param: verbosity/length tier — see TODO(PB-4) (no live web binding). */
  length_tier?: string
  style?: string
  lel_context_enabled?: boolean
  /**
   * P4-G — the reader's answer to a `window_ask` this client previously received. The client
   * echoes back the ask's opaque `ledger_row_id` alongside the reader's own words; the plan
   * stage feeds both to `captureWindowAnswer`, which RE-VERIFIES the row against the DB before
   * writing anything. Absent on every ordinary turn.
   */
  window_ask_answer?: { ledger_row_id?: string; text?: string }
}

export interface AdmittedRequest {
  user: { uid: string }
  body: RequestBody
  chartId: string
  messages: UIMessage[]
}

/** Pre-stream admission. A rejection is a real HTTP response (nothing streamed yet). */
export async function admitRequest(
  request: Request,
): Promise<{ admitted: false; response: Response } | { admitted: true; value: AdmittedRequest }> {
  const user = await getServerUser()
  if (!user) return { admitted: false, response: res.unauthenticated() }

  // PB-1 rollback gate — the whole wave's rollback design IS this flag.
  // Off means this route does not exist for this deploy: a deliberate 404,
  // never silent processing of a half-wired surface.
  if (!configService.getFlag('PARIPRASHNA_ENABLED')) {
    return { admitted: false, response: res.notFound('Paripraśna is not enabled.') }
  }

  let body: RequestBody
  try {
    body = await request.json()
  } catch {
    return { admitted: false, response: res.badRequest('Invalid JSON body') }
  }

  const { chartId, messages } = body
  if (!chartId || !messages) {
    return { admitted: false, response: res.badRequest('chartId and messages are required') }
  }
  if (!UUID_RE.test(chartId)) {
    return { admitted: false, response: res.badRequest('INVALID_CHART_ID: chartId must be a valid UUID') }
  }

  return { admitted: true, value: { user, body, chartId, messages } }
}

/** Bind request params. Pure apart from the effective-model lookup. */
export async function bindTurnParams(body: RequestBody, request: Request): Promise<TurnParams> {
  const VALID_STACKS = Object.keys(STACK_ROUTING) as ModelStack[]
  const selectedStack: ModelStack = VALID_STACKS.includes(body.stack as ModelStack)
    ? (body.stack as ModelStack)
    : DEFAULT_STACK_ID

  // model_id (PB-1/S-1) binds DIRECTLY to the synthesis model when it names a
  // known model; otherwise fall back to the stack's synthesis primary.
  const stackSynthPrimary = await getEffectiveModel(selectedStack, 'synthesis', 'primary', request)
  const modelId = isValidModelId(body.model_id ?? '') ? (body.model_id as string) : stackSynthPrimary
  const modelMeta = getModelMeta(modelId) ?? getModelMeta(DEFAULT_MODEL_ID)!

  // reading_depth: 'auto' | 'deep_dive'. Unknown → 'auto'.
  const readingDepth: ReadingDepth = ReadingDepthSchema.safeParse(body.reading_depth).success
    ? (body.reading_depth as ReadingDepth)
    : 'auto'

  // P2-C (PPR-09/16): verbosity/length tier now HAS a real, flag-gated
  // behavioral contract — `synthesis_stage.assembleSynthesisContext` appends a
  // fixed length-discipline instruction to the system prompt for `brief`/
  // `exhaustive` when `PARIPRASHNA_HONEST_CONTROLS_ENABLED` is on (default
  // off; `standard` is always a no-op, flag on or off). Superseded the prior
  // TODO(PB-4), which was accurate at the time: the tier was accepted +
  // echoed on `turn.open` and stamped into persistence metadata, but changed
  // nothing about synthesis.
  const lengthTier: LengthTier = LengthTierSchema.safeParse(body.length_tier).success
    ? (body.length_tier as LengthTier)
    : 'standard'

  // P4-G: bind the window-ask answer echo, if this turn carries one. Shape-validated only —
  // authority over WHETHER it may resolve anything belongs to `captureWindowAnswer`, which
  // re-reads the row from the DB. Binding here would be the wrong place to decide that.
  const rawAnswer = body.window_ask_answer
  const windowAskAnswer =
    rawAnswer &&
    typeof rawAnswer.ledger_row_id === 'string' &&
    UUID_RE.test(rawAnswer.ledger_row_id) &&
    typeof rawAnswer.text === 'string' &&
    rawAnswer.text.trim().length > 0
      ? { ledgerRowId: rawAnswer.ledger_row_id, text: rawAnswer.text }
      : null

  return {
    selectedStack,
    modelId,
    modelMeta,
    readingDepth,
    deepDive: readingDepth === 'deep_dive',
    lengthTier,
    lelContextEnabled: body.lel_context_enabled !== false,
    style: body.style ?? 'acharya',
    windowAskAnswer,
  }
}

/**
 * NCD-8 pre-dispatch spend/rate gate for the WEB door.
 *
 * Ruling: `PARIPRASHNA_DECISION_REGISTER_v1_0.md` NCD-8 — "Spend caps $2/turn ·
 * $40/day, pre-dispatch, both doors" (RULED 2026-08-18); requirement PPR-25 in
 * `PARIPRASHNA_ARCHITECTURE_v1_0.md`.
 *
 * PRE-DISPATCH means before the first LLM call. On this door that first call is
 * the planner, inside `runPlanStage` — so this gate sits upstream of the stream
 * entirely. It is placed after `bindTurnParams` because the ceiling is evaluated
 * against the model this turn has actually bound, not a guess.
 *
 * A refusal is a REAL HTTP 429 carrying `LIMIT_RATE_LIMIT_EXCEEDED` or
 * `LIMIT_SPEND_CEILING_EXCEEDED` and a message stating the ceiling. Deliberately
 * NOT an in-stream `error` event: at this point no header has been written, and a
 * ceiling refusal is a normal, explainable outcome the client should be able to
 * branch on from the status line alone.
 *
 * Flag-gated (`PARIPRASHNA_LIMITS_ENABLED`, default false) inside
 * `enforceTurnLimits` — when off this returns `admitted: true` having done no DB
 * or pricing work.
 */
export async function admitWithinLimits(args: {
  user: { uid: string }
  params: TurnParams
}): Promise<{ admitted: false; response: Response } | { admitted: true }> {
  const decision = await enforceTurnLimits({
    userId: args.user.uid,
    channel: 'web',
    modelId: args.params.modelId,
    outputTokens: args.params.modelMeta.maxOutputTokens,
  })

  if (decision.allowed) return { admitted: true }

  return {
    admitted: false,
    response: decision.code === 'LIMIT_RATE_LIMIT_EXCEEDED'
      ? res.rateLimited(decision.message, decision.retry_after_seconds)
      : res.spendCeilingExceeded(decision.message),
  }
}

export interface AuthorizedTurn {
  isSuperAdmin: boolean
  /**
   * The consent lane's `subject_kind`, carried forward for the SafetyPolicyGate
   * (lane G1-A). `null` when SUBJECT_CONSENT_ENFORCEMENT is OFF — i.e. when
   * nobody checked. The safety gate treats `null` as NOT-PROVEN-native_self and
   * fails toward the stricter path; it is never read as "probably the native".
   */
  subjectKind: 'native_self' | 'cohort' | 'test' | null
}

/**
 * In-stream entitlement (PPR-11) + conversation resolution. Faults become
 * `error` events; the caller only finishes the turn.
 */
export async function authorizeTurn(args: {
  em: PariprashnaEmitter
  user: { uid: string }
  identity: TurnIdentity
}): Promise<StageResult<AuthorizedTurn>> {
  const { em, user, identity } = args
  const { chartId, conversationId, clientConversationId } = identity

  const chartResult = await query<{ id: string; name: string; client_id: string }>(
    'SELECT id, name, client_id FROM charts WHERE id=$1',
    [chartId],
  )
  if (!chartResult.rows[0]) {
    em.error({ code: 'CHART_NOT_FOUND', message: 'Chart not found.', retryable: false, phase: 'plan' })
    return halt('error')
  }
  const profileResult = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  const isSuperAdmin = profileResult.rows[0]?.role === 'super_admin'

  const { authorizeChartAccess } = await import('@/lib/auth/authorizeChartAccess')
  type DbLike = import('@/lib/auth/authorizeChartAccess').DbLike
  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role: isSuperAdmin ? 'super_admin' : 'guest' },
    chartId,
    db: { query: (sql: string, params?: unknown[]) => query(sql, params).then((r) => ({ rows: r.rows })) } as DbLike,
  })
  if (permission === 'deny') {
    em.error({ code: 'FORBIDDEN', message: 'Not authorized for this chart.', retryable: false, phase: 'plan' })
    return halt('error')
  }

  // ── SUBJECT CONSENT (P1 G1-B · NCD-9 · PPR-14 · abuse case A9). ────────────
  // `authorizeChartAccess` above answered "may this CALLER touch this chart?".
  // This answers the question nothing used to ask: "may this SUBJECT's L2+
  // interpretive corpus be served at all?" — no output for a chart whose
  // subject lacks a consent row, `native_self` strictly checked rather than
  // self-certified, under-18 subjects guardian-only and never a cohort.
  //
  // Ordering is deliberate: consent is resolved AFTER authorization, so an
  // unauthorized caller learns nothing about the subject's consent state.
  //
  // Inert until SUBJECT_CONSENT_ENFORCEMENT is ON (default OFF) — with the flag
  // off `resolveSubjectConsent` returns allow/`enforcement_disabled` without
  // touching the database, so this block adds no query to today's hot path.
  const { resolveSubjectConsent, defaultConsentDb } = await import('@/lib/pariprashna/consent')
  const consentDecision = await resolveSubjectConsent({
    chartId,
    principalId: user.uid,
    db: defaultConsentDb(),
  })
  if (consentDecision.outcome === 'refuse') {
    // A designed refusal, explained — never a bare error and never a silent
    // empty reading (§3.5.A.4: "the entitlement layer refuses, and the refusal
    // is a designed state, not an error").
    em.error({
      code: `SUBJECT_CONSENT_REQUIRED:${consentDecision.reason}`,
      message: consentDecision.message,
      retryable: false,
      phase: 'plan',
    })
    return halt('error')
  }

  // ── Conversation resolution / eager insert (mirrors consult). ──────────────
  if (clientConversationId) {
    const existing = await getConversation({ id: clientConversationId, userId: user.uid, isSuperAdmin })
    if (!existing || existing.chart_id !== chartId) {
      em.error({ code: 'CONVERSATION_NOT_FOUND', message: 'Conversation not found.', retryable: false, phase: 'plan' })
      return halt('error')
    }
  } else {
    try {
      await insertConversationWithId({ id: conversationId, chartId, userId: user.uid, module: 'consume' })
    } catch (err) {
      const msg = String(err).toLowerCase()
      if (!msg.includes('duplicate') && !msg.includes('unique') && !msg.includes('conflict')) {
        em.error({ code: 'CONVERSATION_INIT_FAILED', message: 'Failed to initialize conversation.', retryable: true, phase: 'plan' })
        return halt('error')
      }
    }
  }

  return proceed({ isSuperAdmin, subjectKind: consentDecision.subject_kind })
}

// ═══════════════════════════════════════════════════════════════════════════
// The SafetyPolicyDecision port (P1 lane G1-A · PPR-12 · MP §3.5.C)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Classify the turn, record the decision, and short-circuit the ones that must
 * never reach the planner.
 *
 * THREE OUTCOMES:
 *   · halted 'ok'  — HS-2 (fixed calm response, NO plan built) or the HS-3/HS-4
 *     seal path (acknowledgment, review opened, no reading composed). Both are
 *     ANSWERS, not faults, so the turn closes `ok` and the client renders prose
 *     rather than an error banner.
 *   · proceed with a `reframe`/`interstitial` decision — the turn runs, under
 *     the capability exclusion + prompt policy + pre-wire scan the decision
 *     carries, with the withhold/interstitial notice already emitted.
 *   · proceed with `proceed` — nothing fired; the turn is unchanged.
 *
 * The decision is returned in every case, including flag-OFF, because the
 * receipt lane (G3-A) reads `safety_decision` on EVERY turn.
 */
export async function runSafetyPolicyGate(args: {
  em: PariprashnaEmitter
  identity: TurnIdentity
  messages: UIMessage[]
  subjectKind: 'native_self' | 'cohort' | 'test' | null
}): Promise<StageResult<import('@/lib/pariprashna/safety').SafetyDecision>> {
  const { em, identity, messages, subjectKind } = args

  // The same extraction the plan stage does, run here because the gate must see
  // the question BEFORE the planner does.
  const lastUserMessage = messages.filter((m) => m.role === 'user').at(-1)
  const queryText = (lastUserMessage?.parts ?? [])
    .filter((p) => p.type === 'text')
    .map((p) => (p as { type: string; text?: string }).text ?? '')
    .join(' ')
    .trim()

  const {
    classifyTurnSafety,
    HS2_FIXED_RESPONSE,
    HS1_WITHHOLD_NOTICE,
    HS4_AGGREGATE_FRAMING_NOTICE,
    SEAL_PENDING_ACKNOWLEDGMENT,
    NCD4_INTERSTITIAL_NOTICE,
  } = await import('@/lib/pariprashna/safety')

  const decision = await classifyTurnSafety({
    turnId: identity.turnId,
    chartId: identity.chartId,
    queryText,
    subjectKind,
  })

  if (!decision.enforced) return proceed(decision)

  // The decision is reported on the wire as a COUNT + action, never as the
  // matched text and never as the rule ids (gate 11 [integrity] — the same
  // discipline the NO-LEAKAGE flag follows).
  em.flag({
    code: `safety_decision:${decision.action}`,
    level: decision.action === 'proceed' ? 'info' : 'warn',
    detail:
      decision.classes_detected.length === 0
        ? 'no safety class detected'
        : `${decision.classes_detected.length} safety class(es) detected`,
  })

  const speak = (blockId: string, text: string): void => {
    em.blockOpen({ block_id: blockId, pass_id: 1, role: 'prose' })
    em.blockDelta({ block_id: blockId, delta: text })
    em.blockCommit({ block_id: blockId, text })
  }

  if (decision.action === 'hard_stop') {
    // HS-2. Nothing was retrieved, nothing was planned, no model was called —
    // so there is nothing this response could have been steered into revealing.
    speak('safety-hs2-0', HS2_FIXED_RESPONSE)
    em.phase({ phase: 'plan', status: 'end' })
    return halt('ok')
  }

  if (decision.action === 'seal_pending_signoff') {
    speak('safety-seal-0', SEAL_PENDING_ACKNOWLEDGMENT)
    em.phase({ phase: 'plan', status: 'end' })
    return halt('ok')
  }

  if (decision.action === 'interstitial') {
    // NCD-4: the deliberation pause, then the reading proceeds under the same
    // reframe controls the decision carries.
    speak('safety-ncd4-0', NCD4_INTERSTITIAL_NOTICE)
  }

  if (decision.classes_detected.includes('hs1_date_of_death')) {
    speak('safety-hs1-0', HS1_WITHHOLD_NOTICE)
  }
  if (decision.classes_detected.includes('hs4_mortality_window')) {
    speak('safety-hs4-0', HS4_AGGREGATE_FRAMING_NOTICE)
  }

  return proceed(decision)
}
