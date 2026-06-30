/**
 * /api/mcp/writes/[action] — MCP write-tool dispatcher.
 *
 * Handles three governance-critical write actions for MCP callers:
 *   log_prediction    → logPrediction() from ppl_writer.ts
 *   record_outcome    → recordOutcome() from ppl_writer.ts
 *   flag_disagreement → flagDisagreement() from disagreement_writer.ts
 *
 * Auth model (two-layer, identical to /api/mcp/execute and primitives):
 *   Layer 1: X-MCP-Internal-Token — service-to-service secret.
 *   Layer 2: X-MCP-User, X-MCP-Audience-Tier, X-MCP-Key-Id — resolved principal.
 *
 * Rate limiting: same checkRateLimit() call as other MCP endpoints.
 *   Writes carry a small fixed cost estimate (50 tokens) since they don't
 *   invoke LLM synthesis. The rate limit is primarily to protect against
 *   spam writes.
 *
 * Write provenance (G4 — MCP_BRIEF §6):
 *   Every write carries key_id, trace_id (if provided), and timestamp.
 *   These are set from the resolved principal + caller body, not from
 *   untrusted client-side values.
 *
 * Error handling:
 *   All write operations wrap in try/catch. Errors return
 *   buildErrorEnvelope({error_class: "orchestrator_error"}).
 *
 * @module api/mcp/writes/[action]
 */

import 'server-only'
import { NextResponse } from 'next/server'
import {
  buildEnvelope,
  buildErrorEnvelope,
  buildEpistemicsBlock,
} from '@/lib/mcp/epistemics'
import { checkRateLimit, buildRateLimitErrorEnvelope } from '@/lib/mcp/rate_limiter'
import { logPrediction, recordOutcome } from '@/lib/mcp/ppl_writer'
import { flagDisagreement } from '@/lib/mcp/disagreement_writer'
import type { PredictionEntry, OutcomeEntry } from '@/lib/mcp/ppl_writer'
import type { DisagreementEntry } from '@/lib/mcp/disagreement_writer'

export const maxDuration = 30

// ── Allowed actions ───────────────────────────────────────────────────────────

const ALLOWED_ACTIONS = ['log_prediction', 'record_outcome', 'flag_disagreement'] as const
type WriteAction = (typeof ALLOWED_ACTIONS)[number]

function isAllowedAction(action: string): action is WriteAction {
  return (ALLOWED_ACTIONS as readonly string[]).includes(action)
}

// ── Service-to-service token validation ───────────────────────────────────────

function validateServiceToken(req: Request): boolean {
  const token = req.headers.get('x-mcp-internal-token')
  const expected = process.env.MCP_INTERNAL_TOKEN
  if (!expected) {
    if (process.env.NODE_ENV === 'development') return true
    console.error('[mcp:writes] MCP_INTERNAL_TOKEN not set in production')
    return false
  }
  return token === expected
}

// ── Route params ──────────────────────────────────────────────────────────────

interface RouteParams {
  params: Promise<{ action: string }>
}

// ── POST handler ──────────────────────────────────────────────────────────────

export async function POST(request: Request, { params }: RouteParams) {
  // Layer 1: service-to-service auth
  if (!validateServiceToken(request)) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'auth',
        message: 'Invalid service token',
        remediation: 'MCP server must pass MCP_INTERNAL_TOKEN header',
      }),
      { status: 401 }
    )
  }

  // Layer 2: resolved principal headers
  const userUid = request.headers.get('x-mcp-user')
  const audienceTierHeader = request.headers.get('x-mcp-audience-tier') as
    | 'client'
    | 'super_admin'
    | null
  const keyId = request.headers.get('x-mcp-key-id')

  if (!userUid || !audienceTierHeader || !keyId) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'auth',
        message: 'Missing principal headers',
        remediation: 'MCP server must set X-MCP-User, X-MCP-Audience-Tier, X-MCP-Key-Id',
      }),
      { status: 401 }
    )
  }

  const audienceTier: 'client' | 'super_admin' =
    audienceTierHeader === 'super_admin' ? 'super_admin' : 'client'

  // Rate limiting: 50-token cost estimate for write operations (no LLM synthesis).
  const rateLimitResult = await checkRateLimit(keyId, 50)
  if (!rateLimitResult.allowed) {
    return NextResponse.json(
      buildRateLimitErrorEnvelope(rateLimitResult.reason ?? 'rate_limit'),
      {
        status: 429,
        headers: { 'Retry-After': String(rateLimitResult.retry_after_seconds ?? 60) },
      }
    )
  }

  // Resolve action from URL segment.
  const { action } = await params

  // Trace ID for write operations (no pipeline trace; use a UUID for audit correlation).
  const traceId = crypto.randomUUID()

  if (!isAllowedAction(action)) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'validation',
        message: `Unknown write action: ${action}`,
        remediation: `Supported actions: ${ALLOWED_ACTIONS.join(', ')}`,
      }),
      { status: 400 }
    )
  }

  // Parse request body.
  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      buildErrorEnvelope({ error_class: 'validation', message: 'Invalid JSON body' }),
      { status: 400 }
    )
  }

  // M0 entitlement gate — authorize chart access when chart_id is supplied.
  const chartId = body['chart_id'] as string | undefined
  if (chartId && (action === 'record_outcome' || action === 'log_prediction')) {
    const { authorizeChartAccess } = await import('@/lib/auth/authorizeChartAccess')
    const { resolveMcpPrincipalRole } = await import('@/lib/mcp/auth')
    const { query } = await import('@/lib/db/client')
    const role = await resolveMcpPrincipalRole(userUid)
    const perm = await authorizeChartAccess({ principal: { uid: userUid, role }, chartId, db: { query } })
    if (action === 'record_outcome' && perm !== 'all') {
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'auth', message: 'AUTHZ_DENIED', remediation: 'record_outcome requires write (all) permission for this chart' }),
        { status: 401 }
      )
    }
    if (action === 'log_prediction' && perm === 'deny') {
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'auth', message: 'AUTHZ_DENIED', remediation: 'log_prediction requires view permission for this chart' }),
        { status: 401 }
      )
    }
  }

  // Build common epistemics block for write responses.
  const epistemics = buildEpistemicsBlock({ surgical: true })

  // ── Dispatch ──────────────────────────────────────────────────────────────

  if (action === 'log_prediction') {
    try {
      const entry = body.entry as Partial<PredictionEntry> | undefined
      if (!entry) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message: 'body.entry is required for log_prediction',
          }),
          { status: 400 }
        )
      }

      // Validate required fields.
      if (!entry.horizon || !entry.domain || !entry.prediction_text || !entry.confidence || !entry.falsifier) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message: 'log_prediction requires: horizon, domain, prediction_text, confidence, falsifier',
          }),
          { status: 400 }
        )
      }

      // Stamp provenance from the resolved principal (not from caller body).
      const predictionEntry: PredictionEntry = {
        prediction_id: typeof entry.prediction_id === 'string' ? entry.prediction_id : undefined,
        horizon: entry.horizon,
        domain: entry.domain,
        prediction_text: entry.prediction_text,
        confidence: entry.confidence,
        falsifier: entry.falsifier,
        source: {
          key_id: keyId,  // from resolved principal, not caller body
          trace_id: typeof (body.trace_id) === 'string' ? body.trace_id : null,
          caller_context: typeof entry.source?.caller_context === 'string'
            ? entry.source.caller_context
            : null,
        },
      }

      const prediction_id = await logPrediction(predictionEntry)
      return NextResponse.json(
        buildEnvelope({
          trace_id: traceId,
          audience_tier: audienceTier,
          epistemics,
          result: { prediction_id },
        })
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('[mcp:writes] log_prediction error', msg)
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'orchestrator_error', message: msg }),
        { status: 500 }
      )
    }
  }

  if (action === 'record_outcome') {
    try {
      const entry = body.entry as Partial<OutcomeEntry> | undefined
      if (!entry) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message: 'body.entry is required for record_outcome',
          }),
          { status: 400 }
        )
      }

      if (!entry.prediction_id || !entry.outcome_text || entry.verified === undefined) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message: 'record_outcome requires: prediction_id, outcome_text, verified',
          }),
          { status: 400 }
        )
      }

      const outcomeEntry: OutcomeEntry = {
        prediction_id: entry.prediction_id,
        outcome_text: entry.outcome_text,
        verified: entry.verified,
        notes: typeof entry.notes === 'string' ? entry.notes : null,
        source: {
          key_id: keyId,
          trace_id: typeof (body.trace_id) === 'string' ? body.trace_id : null,
        },
      }

      const result = await recordOutcome(outcomeEntry)
      return NextResponse.json(
        buildEnvelope({
          trace_id: traceId,
          audience_tier: audienceTier,
          epistemics,
          result: { linked_to: outcomeEntry.prediction_id, found: result.ok },
          ...(result.ok ? {} : {
            warnings: [`prediction_id ${outcomeEntry.prediction_id} not found in PPL`],
          }),
        })
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('[mcp:writes] record_outcome error', msg)
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'orchestrator_error', message: msg }),
        { status: 500 }
      )
    }
  }

  if (action === 'flag_disagreement') {
    try {
      const entry = body.entry as Partial<DisagreementEntry> | undefined
      if (!entry) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message: 'body.entry is required for flag_disagreement',
          }),
          { status: 400 }
        )
      }

      if (!entry.class || !entry.description || !entry.source_session) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message: 'flag_disagreement requires: class, description, source_session',
          }),
          { status: 400 }
        )
      }

      const disagreementEntry: DisagreementEntry = {
        class: entry.class,
        description: entry.description,
        source_session: entry.source_session,
        proposed_resolution: typeof entry.proposed_resolution === 'string'
          ? entry.proposed_resolution
          : null,
        source: {
          key_id: keyId,
          trace_id: typeof (body.trace_id) === 'string' ? body.trace_id : null,
        },
      }

      const disagreement_id = await flagDisagreement(disagreementEntry)
      return NextResponse.json(
        buildEnvelope({
          trace_id: traceId,
          audience_tier: audienceTier,
          epistemics,
          result: { disagreement_id },
        })
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('[mcp:writes] flag_disagreement error', msg)
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'orchestrator_error', message: msg }),
        { status: 500 }
      )
    }
  }

  // Unreachable (isAllowedAction guard above), but TypeScript requires exhaustive check.
  return NextResponse.json(
    buildErrorEnvelope({ error_class: 'validation', message: 'Unhandled action' }),
    { status: 400 }
  )
}
