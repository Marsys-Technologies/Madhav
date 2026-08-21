/**
 * epistemics.ts — MCP response envelope builder.
 *
 * Centralises the construction of the MCP_BRIEF §4.2 envelope so every
 * /api/mcp/* endpoint returns a consistent shape. The epistemics block is
 * mandatory on every response (per D7 — the ethical framework does not erode
 * in the MCP transport).
 *
 * Exports:
 *   buildEpistemicsBlock()    — constructs the mandatory EpistemicsBlock
 *   buildSynthesisAudit()     — constructs the SynthesisAuditBlock for ask_madhav
 *   buildEnvelope()           — constructs a success McpEnvelope
 *   buildErrorEnvelope()      — constructs an error McpEnvelope
 */

import type {
  McpEnvelope,
  McpSuccessEnvelope,
  McpErrorEnvelope,
  EpistemicsBlock,
  EvidenceState,
  SynthesisAuditBlock,
  McpCitation,
  PplEntry,
  DenialBlock,
} from '@/lib/mcp/types'
import type { PipelinePlan } from '@/lib/pipeline/types'

// ── L2.5 tool set (same definition as route.ts B.11 enforcement) ──────────────

const L2_5_TOOLS = new Set([
  'msr_sql',
  'query_msr_aggregate',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'cgm_graph_walk',
])

// ── EpistemicsBlock builder ───────────────────────────────────────────────────

export interface BuildEpistemicsBlockParams {
  /**
   * True for surgical primitive calls (no B.11 floor enforcement, no synthesis).
   * False for ask_madhav / execute_plan (full pipeline).
   */
  surgical: boolean
  /**
   * Calibrated confidence band. Defaults to 'medium' when not explicitly set.
   * For surgical calls (single fact lookups) that returned rows, 'high' is
   * appropriate. For holistic synthesis, use 'medium' unless there is strong
   * convergence. For a result set that came back EMPTY, pass 'none' — a band
   * grades a finding, and there is no finding to grade (F-126).
   */
  confidence_band?: 'high' | 'medium' | 'low' | 'none'
  /**
   * Evidence state of the served result, as measured by
   * `lib/mcp/evidence_state.ts#detectEvidenceState`. Omit where nothing measured
   * the result — the field is then absent rather than defaulted (§N.7 item 6:
   * an honest null beats an invented judgment).
   */
  evidence_state?: EvidenceState
  /**
   * Prediction horizon in days. Set for predictive answers; null otherwise.
   */
  horizon_days?: number | null
  /**
   * Specific falsifier condition. Required for predictive; null for factual.
   */
  falsifier?: string | null
}

/**
 * Build the mandatory EpistemicsBlock for any MCP response.
 */
export function buildEpistemicsBlock(params: BuildEpistemicsBlockParams): EpistemicsBlock {
  return {
    surgical: params.surgical,
    confidence_band: params.confidence_band ?? 'medium',
    ...(params.evidence_state ? { evidence_state: params.evidence_state } : {}),
    horizon_days: params.horizon_days ?? null,
    falsifier: params.falsifier ?? null,
  }
}

// ── SynthesisAuditBlock builder ───────────────────────────────────────────────

export interface BuildSynthesisAuditParams {
  /** Names of tools that actually fired during this pipeline run. */
  tools_fired: string[]
  /** Human-readable summary of L2.5 contribution. */
  l25_contribution_summary?: string
  /** Signal IDs most influential in the synthesis. */
  dominant_signals?: string[]
  /** Jyotish domains touched by the synthesis. */
  domains_touched?: string[]
}

/**
 * Build the SynthesisAuditBlock. Computes l25_tools_fired and holistic_read_passed
 * from the full tools_fired list.
 */
export function buildSynthesisAudit(params: BuildSynthesisAuditParams): SynthesisAuditBlock {
  const l25_tools_fired = params.tools_fired.filter(t => L2_5_TOOLS.has(t))
  const holistic_read_passed = l25_tools_fired.length > 0

  const l25_contribution_summary =
    params.l25_contribution_summary ??
    (l25_tools_fired.length > 0
      ? `${l25_tools_fired.length} L2.5 tool${l25_tools_fired.length > 1 ? 's' : ''} fired: ${l25_tools_fired.join(', ')}`
      : 'No L2.5 tools fired — B.11 floor bypassed.')

  return {
    l25_tools_fired,
    l25_contribution_summary,
    dominant_signals: params.dominant_signals ?? [],
    domains_touched: params.domains_touched ?? [],
    holistic_read_passed,
  }
}

// ── Success envelope builder ──────────────────────────────────────────────────

export interface BuildEnvelopeParams {
  trace_id: string
  audience_tier: 'client' | 'super_admin'
  epistemics: EpistemicsBlock
  result: unknown
  citations?: McpCitation[]
  plan?: PipelinePlan | null
  predictions_logged?: PplEntry[]
  synthesis_audit?: SynthesisAuditBlock | null
  suggested_followups?: string[]
  warnings?: string[]
}

/**
 * Build a success McpEnvelope per MCP_BRIEF §4.2.
 */
export function buildEnvelope(params: BuildEnvelopeParams): McpSuccessEnvelope {
  return {
    ok: true,
    trace_id: params.trace_id,
    audience_tier: params.audience_tier,
    epistemics: params.epistemics,
    result: params.result,
    citations: params.citations ?? [],
    plan: params.plan ?? null,
    predictions_logged: params.predictions_logged ?? [],
    synthesis_audit: params.synthesis_audit ?? null,
    suggested_followups: params.suggested_followups ?? [],
    warnings: params.warnings ?? [],
  }
}

// ── Error envelope builder ────────────────────────────────────────────────────

export interface BuildErrorEnvelopeParams {
  trace_id?: string
  error_class: McpErrorEnvelope['error']['class']
  message: string
  remediation?: string
  /** R5.1 C2 item 3 — present only for error_class === 'entitlement_denied'. */
  denial?: DenialBlock
}

/**
 * Build an error McpEnvelope per MCP_BRIEF §4.2.
 */
export function buildErrorEnvelope(params: BuildErrorEnvelopeParams): McpErrorEnvelope {
  return {
    ok: false,
    trace_id: params.trace_id ?? '',
    error: {
      class: params.error_class,
      message: params.message,
      ...(params.remediation ? { remediation: params.remediation } : {}),
    },
    ...(params.denial ? { denial: params.denial } : {}),
  }
}

/**
 * R5.1 C2 item 3 (Denial ≠ empty). Build a distinctly-shaped entitlement-denial
 * McpErrorEnvelope — every MCP entrypoint that runs `authorizeChartAccess` and gets
 * `'deny'` should build its error response through this helper (instead of a bare
 * `error_class: 'auth'`) so the wire shape is unambiguous and consistent across every
 * instrument that can hit this path (primitives, writes, bundles).
 *
 * Never repurposes the empty-with-reason (U4) mechanism — this is a NEW additive state.
 * Never fabricates: `chart_id` and `permission_required` are always the exact values the
 * caller already checked.
 */
export function buildEntitlementDenialEnvelope(params: {
  trace_id?: string
  chart_id: string
  permission_required: 'view' | 'all'
  message?: string
  remediation?: string
}): McpErrorEnvelope {
  return buildErrorEnvelope({
    trace_id: params.trace_id,
    error_class: 'entitlement_denied',
    message: params.message ?? `AUTHZ_DENIED: caller does not have ${params.permission_required} access to chart ${params.chart_id}.`,
    remediation: params.remediation ??
      'This chart exists but you have no chart_grants row for it (or it is genuinely absent) — ' +
      'distinct from a query that legitimately matched zero rows. Request access from the chart owner.',
    denial: {
      reason: 'entitlement',
      chart_id: params.chart_id,
      permission_found: 'deny',
      permission_required: params.permission_required,
      distinct_from_empty: true,
    },
  })
}

// Re-export the full McpEnvelope type for convenience at call sites.
export type { McpEnvelope, DenialBlock }
