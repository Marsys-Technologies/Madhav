/**
 * /api/mcp/writes/[action] — MCP write-tool dispatcher.
 *
 * Handles three governance-critical write actions for MCP callers:
 *   log_prediction    → logPrediction() from ppl_writer.ts   [RETIRED no-op — see below]
 *   record_outcome    → recordOutcome() from ppl_writer.ts   [RETIRED no-op — see below]
 *   flag_disagreement → flagDisagreement() from disagreement_writer.ts
 *
 * RETIREMENT (PB-3 SAMĪKṢĀ lane L-1, MEMO_PB-3_0, 2026-07-28): the `mcp_predictions` table
 * behind log_prediction / record_outcome was dropped (migration 471); ppl_writer's
 * logPrediction/recordOutcome are now inert no-ops. These two handlers therefore no longer
 * persist anything. Their disposition (re-point at brahma_mimamsa_prediction_ledger vs.
 * remove the actions) is L-5's charge per LEDGER_MAP_PB-3.md; L-1 only retired the table +
 * the direct writers. flag_disagreement is unaffected.
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
  buildEntitlementDenialEnvelope,
} from '@/lib/mcp/epistemics'
import { checkRateLimit, buildRateLimitErrorEnvelope } from '@/lib/mcp/rate_limiter'
import { logPrediction, recordOutcome } from '@/lib/mcp/ppl_writer'
import { flagDisagreement } from '@/lib/mcp/disagreement_writer'
import { recordLelEvent } from '@/lib/mcp/lel_event_writer'
import { enqueueLelRecalibration } from '@/lib/build/recalibrationEnqueue'
import {
  fileProspectivePrediction,
  listProspectivePredictions,
  matchOpenPredictionsForLelEvent,
  type FileProspectivePredictionInput,
  type LifecycleStatus,
} from '@/lib/lel/prospective_ledger'
import type { PredictionEntry, OutcomeEntry } from '@/lib/mcp/ppl_writer'
import type { InterventionLedgerEntryInput } from '@/lib/mcp/intervention_ledger_writer'
import type { DisagreementEntry } from '@/lib/mcp/disagreement_writer'
import type { LelEvent } from '@/lib/mcp/lel_event_writer'
import { validateServiceToken } from '@/lib/mcp/service_token'

export const maxDuration = 30

// ── Allowed actions ───────────────────────────────────────────────────────────

const ALLOWED_ACTIONS = [
  'log_prediction',
  'record_outcome',
  'flag_disagreement',
  'lel_event_record',
  'prospective_ledger_file',
  'prospective_ledger_list',
  'intervention_ledger_record',
] as const
type WriteAction = (typeof ALLOWED_ACTIONS)[number]

function isAllowedAction(action: string): action is WriteAction {
  return (ALLOWED_ACTIONS as readonly string[]).includes(action)
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
  if (
    chartId &&
    (action === 'record_outcome' ||
      action === 'log_prediction' ||
      action === 'lel_event_record' ||
      action === 'prospective_ledger_file' ||
      action === 'prospective_ledger_list' ||
      action === 'intervention_ledger_record')
  ) {
    const { authorizeChartAccess } = await import('@/lib/auth/authorizeChartAccess')
    const { resolveMcpPrincipalRole } = await import('@/lib/mcp/auth')
    const { query } = await import('@/lib/db/client')
    const role = await resolveMcpPrincipalRole(userUid)
    const perm = await authorizeChartAccess({ principal: { uid: userUid, role }, chartId, db: { query } })
    // R5.1 C2 item 3 (Denial ≠ empty): every AUTHZ_DENIED site here now returns the
    // distinct `entitlement_denied` envelope (never bare 'auth') — see epistemics.ts's
    // buildEntitlementDenialEnvelope doc comment.
    if (action === 'record_outcome' && perm !== 'all') {
      return NextResponse.json(
        buildEntitlementDenialEnvelope({
          chart_id: chartId, permission_required: 'all',
          remediation: 'record_outcome requires write (all) permission for this chart.',
        }),
        { status: 401 }
      )
    }
    // lel_event_record is a Nirmāṇa (build/write) action — owner/super_admin only.
    if (action === 'lel_event_record' && perm !== 'all') {
      return NextResponse.json(
        buildEntitlementDenialEnvelope({
          chart_id: chartId, permission_required: 'all',
          remediation: 'lel_event_record requires write (all) permission for this chart.',
        }),
        { status: 401 }
      )
    }
    // prospective_ledger_file is a filing (write) action — §11 "explicit filing only" is
    // enforced at the DB layer (filing_method CHECK); this is the ordinary write-perm
    // gate, same tier as lel_event_record.
    if (action === 'prospective_ledger_file' && perm !== 'all') {
      return NextResponse.json(
        buildEntitlementDenialEnvelope({
          chart_id: chartId, permission_required: 'all',
          remediation: 'prospective_ledger_file requires write (all) permission for this chart.',
        }),
        { status: 401 }
      )
    }
    // intervention_ledger_record is a filing (write) action into mimamsa_intervention_ledger
    // (item 42 / gate G7) — same write-perm tier as prospective_ledger_file.
    if (action === 'intervention_ledger_record' && perm !== 'all') {
      return NextResponse.json(
        buildEntitlementDenialEnvelope({
          chart_id: chartId, permission_required: 'all',
          remediation: 'intervention_ledger_record requires write (all) permission for this chart.',
        }),
        { status: 401 }
      )
    }
    if (action === 'prospective_ledger_list' && perm === 'deny') {
      return NextResponse.json(
        buildEntitlementDenialEnvelope({
          chart_id: chartId, permission_required: 'view',
          remediation: 'prospective_ledger_list requires view permission for this chart.',
        }),
        { status: 401 }
      )
    }
    if (action === 'log_prediction' && perm === 'deny') {
      return NextResponse.json(
        buildEntitlementDenialEnvelope({
          chart_id: chartId, permission_required: 'view',
          remediation: 'log_prediction requires view permission for this chart.',
        }),
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

  if (action === 'lel_event_record') {
    try {
      if (!chartId) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message: 'chart_id is required for lel_event_record',
          }),
          { status: 400 }
        )
      }

      const event = body.event as Partial<LelEvent> | undefined
      if (!event) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message: 'body.event is required for lel_event_record',
          }),
          { status: 400 }
        )
      }

      if (!event.event_class || !event.event_date || !event.description || !event.domain) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message: 'lel_event_record requires: event.event_class, event.event_date, event.description, event.domain',
          }),
          { status: 400 }
        )
      }

      // Persist the event (validates event_class against brahma_event_ontology).
      let saved
      try {
        saved = await recordLelEvent({
          chartId,
          event: {
            event_id: typeof event.event_id === 'string' ? event.event_id : undefined,
            event_class: event.event_class,
            event_date: event.event_date,
            event_type: typeof event.event_type === 'string' ? event.event_type : undefined,
            description: event.description,
            domain: event.domain,
            outcome_observed: typeof event.outcome_observed === 'boolean' ? event.outcome_observed : undefined,
            source_citation: typeof event.source_citation === 'string' ? event.source_citation : undefined,
          },
          // Provenance stamped from the resolved principal, not caller body.
          provenance: {
            key_id: keyId,
            trace_id: typeof body.trace_id === 'string' ? body.trace_id : null,
            caller_context: typeof event.source_citation === 'string' ? event.source_citation : null,
          },
        })
      } catch (writeErr) {
        // Unknown event class (or other validation failure inside the writer).
        const msg = writeErr instanceof Error ? writeErr.message : String(writeErr)
        return NextResponse.json(
          buildErrorEnvelope({ error_class: 'validation', message: msg }),
          { status: 400 }
        )
      }

      // Debounced recalibration enqueue — best-effort side effect. A failure to
      // enqueue must NOT fail the save (the event is already durably recorded).
      const force = body.force === true
      let recalibration: Record<string, unknown> = { enqueued: false }
      try {
        const enqueue = await enqueueLelRecalibration({ chartId, triggeredBy: userUid, force })
        recalibration = { ...enqueue }
      } catch (enqErr) {
        const msg = enqErr instanceof Error ? enqErr.message : String(enqErr)
        console.error('[mcp:writes] lel_event_record recalibration enqueue error', msg)
        recalibration = { enqueued: false, reason: 'enqueue_error' }
      }

      // D-4a Lane A-4 outcome-matching hook — best-effort side effect, same discipline
      // as the recalibration enqueue above: a failure here must NOT fail the save.
      // Matches this newly-appended LEL event against this chart's OPEN prospective
      // predictions in the same event_class (Lane A-1 tolerance reuse — see
      // matchOpenPredictionsForLelEvent's doc comment in prospective_ledger.ts).
      let prospective_ledger_matches: Record<string, unknown> = { matched_count: 0 }
      try {
        const matches = await matchOpenPredictionsForLelEvent({
          chart_id: chartId,
          life_event_id: saved.id,
          event_class: event.event_class,
          event_date: event.event_date,
        })
        prospective_ledger_matches = { matched_count: matches.length, matches }
      } catch (matchErr) {
        const msg = matchErr instanceof Error ? matchErr.message : String(matchErr)
        console.error('[mcp:writes] lel_event_record prospective-ledger match error', msg)
        prospective_ledger_matches = { matched_count: 0, reason: 'match_error' }
      }

      return NextResponse.json(
        buildEnvelope({
          trace_id: traceId,
          audience_tier: audienceTier,
          epistemics,
          result: {
            event_id: saved.event_id,
            recorded_at: saved.recorded_at,
            created: saved.created,
            recalibration,
            prospective_ledger_matches,
          },
        })
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('[mcp:writes] lel_event_record error', msg)
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'orchestrator_error', message: msg }),
        { status: 500 }
      )
    }
  }

  if (action === 'prospective_ledger_file') {
    // D-4a Lane A-4. §11 governance: this is THE explicit-filing surface — there is no
    // other sanctioned path into brahma_prospective_ledger. filed_by is stamped from
    // the resolved principal (userUid), never trusted from the caller body, exactly
    // like key_id elsewhere in this file — the filing provenance cannot be spoofed.
    try {
      if (!chartId) {
        return NextResponse.json(
          buildErrorEnvelope({ error_class: 'validation', message: 'chart_id is required for prospective_ledger_file' }),
          { status: 400 }
        )
      }
      const entry = body.entry as Partial<FileProspectivePredictionInput> | undefined
      if (!entry || !entry.claim || !entry.event_class || !entry.claim_shape || !entry.model ||
          !entry.formula_version || entry.confidence === undefined || !entry.falsifier || !entry.generator_class ||
          !entry.source_citation) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message:
              'prospective_ledger_file requires body.entry: claim, event_class, claim_shape, model, ' +
              'formula_version, confidence, falsifier, generator_class, source_citation ' +
              '(+ point_date | window_start/window_end | milestones, per claim_shape).',
          }),
          { status: 400 }
        )
      }

      const input: FileProspectivePredictionInput = {
        chart_id: chartId,
        claim: entry.claim,
        event_class: entry.event_class,
        claim_shape: entry.claim_shape,
        point_date: entry.point_date,
        window_start: entry.window_start,
        window_end: entry.window_end,
        milestones: entry.milestones,
        model: entry.model,
        formula_version: entry.formula_version,
        confidence: entry.confidence,
        falsifier: entry.falsifier,
        generator_class: entry.generator_class,
        configuration_signature: entry.configuration_signature ?? null,
        filed_by: userUid, // stamped from resolved principal — §11 provenance
        source_citation: entry.source_citation,
        // D-5 Lane G-5 (BRIEF_D5 §4, DR-16): only meaningful for
        // generator_class='engine' + adverse-valence event_class — fileProspectivePrediction
        // itself enforces the hard 5-property gate; this route only threads the caller's
        // payload through, it does not weaken or bypass the check.
        dr16_adverse_disclosure: entry.dr16_adverse_disclosure,
      }

      const filed = await fileProspectivePrediction(input)
      return NextResponse.json(
        buildEnvelope({
          trace_id: traceId,
          audience_tier: audienceTier,
          epistemics,
          result: {
            prediction: filed.row,
            governance: filed.governance,
            ...(filed.dr16_disclosure ? { dr16_disclosure: filed.dr16_disclosure } : {}),
          },
        })
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('[mcp:writes] prospective_ledger_file error', msg)
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'validation', message: msg }),
        { status: 400 }
      )
    }
  }

  if (action === 'prospective_ledger_list') {
    try {
      if (!chartId) {
        return NextResponse.json(
          buildErrorEnvelope({ error_class: 'validation', message: 'chart_id is required for prospective_ledger_list' }),
          { status: 400 }
        )
      }
      const status = typeof body.status === 'string' ? body.status : undefined
      const eventClass = typeof body.event_class === 'string' ? body.event_class : undefined
      const limit = typeof body.limit === 'number' ? body.limit : undefined
      const listed = await listProspectivePredictions(chartId, {
        status: status as LifecycleStatus | undefined,
        eventClass,
        limit,
      })
      return NextResponse.json(
        buildEnvelope({
          trace_id: traceId,
          audience_tier: audienceTier,
          epistemics,
          result: { predictions: listed.rows, count: listed.rows.length, governance: listed.governance },
        })
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('[mcp:writes] prospective_ledger_list error', msg)
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'orchestrator_error', message: msg }),
        { status: 500 }
      )
    }
  }

  if (action === 'intervention_ledger_record') {
    // ṢAḌ-DARŚANA W4 item 42 / gate G7: the serve-time write path into
    // mimamsa_intervention_ledger (KALA_W4_UPAYA_DESIGN §4.1 ruling S-1; migration 532's
    // "FILED live, at serve time, through the sanctioned HTTP action"). filed_by is stamped
    // from the resolved principal (userUid), never trusted from the caller body — identical
    // rule to prospective_ledger_file above. Beyond field-presence this route adds no
    // validation of its own: the table's CHECKs/FKs (incl. the ADJUDICATION-12
    // _inferred_never_sealed CHECK) are the authorities and their verbatim errors surface.
    try {
      if (!chartId) {
        return NextResponse.json(
          buildErrorEnvelope({ error_class: 'validation', message: 'chart_id is required for intervention_ledger_record' }),
          { status: 400 }
        )
      }
      const entry = body.entry as Partial<InterventionLedgerEntryInput> | undefined
      const requiredFields = [
        'intent', 'intervention_class', 'rite_or_activity_class', 'window_start', 'window_end',
        'precision_regime', 'precision_basis', 'adjudication_record', 'score_vector',
        'efficacy_tier', 'source_citation', 'paddhati_version', 'predicted_differential',
        'adoption_basis', 'engine_version',
      ] as const
      const missing = !entry
        ? [...requiredFields]
        : requiredFields.filter((f) => entry[f] === undefined || entry[f] === null || entry[f] === '')
      if (!entry || missing.length > 0) {
        return NextResponse.json(
          buildErrorEnvelope({
            error_class: 'validation',
            message:
              'intervention_ledger_record requires body.entry with: ' + missing.join(', ') +
              ' (event_class, prediction_id, authority_basis are nullable; filed_by is stamped server-side).',
          }),
          { status: 400 }
        )
      }

      const { recordInterventionLedgerEntry } = await import('@/lib/mcp/intervention_ledger_writer')
      const recorded = await recordInterventionLedgerEntry({
        chart_id: chartId,
        intent: entry.intent as string,
        intervention_class: entry.intervention_class as InterventionLedgerEntryInput['intervention_class'],
        rite_or_activity_class: entry.rite_or_activity_class as string,
        event_class: typeof entry.event_class === 'string' && entry.event_class.length > 0 ? entry.event_class : null,
        window_start: entry.window_start as string,
        window_end: entry.window_end as string,
        precision_regime: entry.precision_regime as InterventionLedgerEntryInput['precision_regime'],
        precision_basis: entry.precision_basis as string,
        adjudication_record: entry.adjudication_record as Record<string, unknown>,
        score_vector: entry.score_vector as Record<string, unknown>,
        efficacy_tier: entry.efficacy_tier as InterventionLedgerEntryInput['efficacy_tier'],
        source_citation: entry.source_citation as string,
        paddhati_version: entry.paddhati_version as string,
        predicted_differential: entry.predicted_differential as string,
        prediction_id: typeof entry.prediction_id === 'string' && entry.prediction_id.length > 0 ? entry.prediction_id : null,
        adoption_basis: entry.adoption_basis as InterventionLedgerEntryInput['adoption_basis'],
        authority_basis: typeof entry.authority_basis === 'string' && entry.authority_basis.length > 0 ? entry.authority_basis : null,
        engine_version: entry.engine_version as string,
        filed_by: userUid, // stamped from resolved principal — never the caller body
      })
      return NextResponse.json(
        buildEnvelope({
          trace_id: traceId,
          audience_tier: audienceTier,
          epistemics,
          result: { intervention_id: recorded.intervention_id, created: recorded.created },
        })
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('[mcp:writes] intervention_ledger_record error', msg)
      return NextResponse.json(
        buildErrorEnvelope({ error_class: 'validation', message: msg }),
        { status: 400 }
      )
    }
  }

  // Unreachable (isAllowedAction guard above), but TypeScript requires exhaustive check.
  return NextResponse.json(
    buildErrorEnvelope({ error_class: 'validation', message: 'Unhandled action' }),
    { status: 400 }
  )
}
