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
 *   · `authorizeTurn` — in-stream chart resolution, per-chart authorization
 *     (PPR-11, fail-closed) and conversation resolution. Every fault here is an
 *     in-stream `error` EVENT, never an HTTP status — the stream is already open.
 *
 * PORT NOT YET IMPLEMENTED — `SafetyPolicyDecision` (PPR-12/PPR-13).
 * The route has never carried a safety classifier or an injection scan; this
 * file does not invent one. P1's safety-gate and injection-scan lanes own that
 * port, and this module is its declared home: a `classifyTurnSafety()` inserted
 * between `authorizeTurn` and the plan stage is the whole wiring change.
 * Until it exists there is NO safety decision to record — an honest absence,
 * never a green-looking default (§N.8).
 */

import type { UIMessage } from 'ai'

import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import { getConversation, insertConversationWithId } from '@/lib/conversations'
import { configService } from '@/lib/config/index'
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

  // TODO(PB-4): verbosity/length tier has NO live behavioral contract in the web
  // synthesis path — the adapter dispatch builds systemContent from the bundle +
  // synthesis_guidance only and never applies a ConsumeStyle/verbosity suffix
  // (the `reading_depth:deep_dive` + `exhaustive` verbosity contract landed
  // MCP-side, out of scope for this Next.js app). We accept + echo the tier on
  // `turn.open` and stamp it into persistence metadata, but it does NOT yet
  // change synthesis length. Wire the real length lever in wave PB-4.
  const lengthTier: LengthTier = LengthTierSchema.safeParse(body.length_tier).success
    ? (body.length_tier as LengthTier)
    : 'standard'

  return {
    selectedStack,
    modelId,
    modelMeta,
    readingDepth,
    deepDive: readingDepth === 'deep_dive',
    lengthTier,
    lelContextEnabled: body.lel_context_enabled !== false,
    style: body.style ?? 'acharya',
  }
}

export interface AuthorizedTurn {
  isSuperAdmin: boolean
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

  return proceed({ isSuperAdmin })
}
