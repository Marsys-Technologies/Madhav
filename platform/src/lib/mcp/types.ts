/**
 * types.ts — Shared TypeScript types for the MCP platform surface.
 *
 * Used by: auth.ts, epistemics.ts, suggested_followups.ts, /api/mcp/* routes,
 *          admin UI components, and test files.
 *
 * These types implement the MCP_BRIEF §4.2 response envelope contract exactly.
 */

import type { PipelinePlan } from '@/lib/pipeline/types'

// ── Auth ─────────────────────────────────────────────────────────────────────

/** Resolved principal returned by validateMcpKey on success. */
export interface McpPrincipal {
  /** Firebase UID bound to the API key. */
  user_uid: string
  // audience_tier removed (Stream A 3.tier_excision 2026-05-28). Access is governed by authorizeChartAccess (G2).
  audience_tier?: string
  /** Short key prefix (key_id column) — included in audit headers. */
  key_id: string
  /** Firebase role from profiles table. Populated by M0 entitlement gate (2026-06-30). */
  role: 'guest' | 'super_admin'
  /**
   * Bound model family for this API key (M6 declared profile 2026-07-01).
   * Undefined = undeclared → universal-best surface served.
   * Values: 'anthropic' | 'gemini' | 'openai' | 'deepseek'
   */
  model_family?: 'anthropic' | 'gemini' | 'openai' | 'deepseek'
}

// ── Epistemics ────────────────────────────────────────────────────────────────

/** Mandatory ethics/epistemics block on every MCP response (MCP_BRIEF §4.2 + D7). */
export interface EpistemicsBlock {
  /** True for surgical primitive calls; false for ask_madhav full-pipeline calls. */
  surgical: boolean
  /** Calibrated confidence band for the answer. */
  confidence_band: 'high' | 'medium' | 'low'
  /**
   * Horizon in days for predictive answers; null for non-predictive.
   * Example: 90 = "this applies within the next ~3 months".
   */
  horizon_days: number | null
  /**
   * The specific condition that would falsify this answer.
   * Required for predictive answers; null for factual.
   */
  falsifier: string | null
}

// ── Synthesis audit ───────────────────────────────────────────────────────────

/**
 * Audit block proving B.11 Whole-Chart-Read floor was honored (MCP_BRIEF §4.2).
 * Present on ask_madhav and execute_plan responses; absent on surgical primitives.
 */
export interface SynthesisAuditBlock {
  /** L2.5 tools that actually fired in this pipeline run. */
  l25_tools_fired: string[]
  /** Human-readable summary of L2.5 contribution, e.g. "12 MSR signals + 7 CGM edges". */
  l25_contribution_summary: string
  /** Top signal IDs most influential in the synthesis. */
  dominant_signals: string[]
  /** Jyotish domains touched by the synthesis. */
  domains_touched: string[]
  /**
   * True when ≥1 L2.5 tool fired (B.11 floor satisfied).
   * False when the floor was bypassed — only valid for mode="factual" surgical calls;
   * in all other cases a warning is emitted.
   */
  holistic_read_passed: boolean
}

// ── Citations ─────────────────────────────────────────────────────────────────

/** A single citation entry in the MCP response envelope. */
export interface McpCitation {
  /** Signal or asset ID, e.g. "SIG.MSR.234" or "FORENSIC§birth_data". */
  id: string
  /** Which canonical layer this citation came from. */
  layer: 'L1' | 'L1.5' | 'L2.5' | 'L4'
  /** Short excerpt or snippet from the cited source. */
  snippet?: string
}

// ── PPL entries ───────────────────────────────────────────────────────────────

/** A prospective-prediction log entry created during a predictive MCP call. */
export interface PplEntry {
  pred_id: string
  emitted_at: string
  mode: 'predictive' | 'blind'
  query: string
  confidence: number | null
  horizon_days: number | null
  falsifier: string | null
  trace_id: string
}

// ── MCP response envelope ─────────────────────────────────────────────────────

/** Successful MCP response envelope (MCP_BRIEF §4.2). */
export interface McpSuccessEnvelope {
  ok: true
  /** Trace ID — same as query_id; pass to get_trace() to inspect. */
  trace_id: string
  // audience_tier removed (Stream A 3.tier_excision 2026-05-28).
  audience_tier?: string
  /** Mandatory epistemics block (D7). */
  epistemics: EpistemicsBlock
  /** Tool-specific payload. */
  result: unknown
  /** Citations from the synthesis (ask_madhav / execute_plan only). */
  citations: McpCitation[]
  /** Full PipelinePlan (ask_madhav / execute_plan only). */
  plan: PipelinePlan | null
  /** PPL entries created during this call (predictive calls only). */
  predictions_logged: PplEntry[]
  /** B.11 audit (ask_madhav / execute_plan only). */
  synthesis_audit: SynthesisAuditBlock | null
  /** 2-3 plausible follow-up questions (ask_madhav only). */
  suggested_followups: string[]
  /** Non-fatal warnings (e.g. B.11 floor bypassed with warning). */
  warnings: string[]
}

/** Error MCP response envelope (MCP_BRIEF §4.2). */
export interface McpErrorEnvelope {
  ok: false
  /** Trace ID if a trace was started before the error; may be empty string. */
  trace_id: string
  error: {
    /** Error class for programmatic handling. */
    class: 'auth' | 'validation' | 'planner_error' | 'orchestrator_error' | 'rate_limit' | 'internal'
    /** Human-readable error message. */
    message: string
    /** Optional remediation hint. */
    remediation?: string
  }
}

/** Union of success and error envelopes. */
export type McpEnvelope = McpSuccessEnvelope | McpErrorEnvelope

// ── API key record ────────────────────────────────────────────────────────────

/** Row shape returned by GET /api/mcp/keys (never includes key_hash). */
export interface McpApiKeyRow {
  key_id: string
  label: string | null
  // audience_tier removed (Stream A 3.tier_excision 2026-05-28).
  audience_tier?: string
  user_uid: string
  scopes: string[]
  created_at: string
  last_used_at: string | null
  revoked_at: string | null
  /** Bound model family for profiled surface. Null = undeclared (universal-best). M6. */
  model_family?: string | null
}

/** Shape of the one-time creation response (includes full_key shown once). */
export interface McpKeyCreatedResponse {
  key_id: string
  /** The full bearer token — shown exactly once at creation time. */
  full_key: string
  label: string | null
  // audience_tier removed (Stream A 3.tier_excision 2026-05-28).
  audience_tier?: string
  user_uid: string
  created_at: string
  /** Bound model family for this key. Null = undeclared (universal-best). M6. */
  model_family?: string | null
}
