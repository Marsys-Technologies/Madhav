/**
 * types.ts — Shared TypeScript interfaces for the platform-mcp MCP server.
 *
 * These interfaces mirror platform/src/lib/mcp/types.ts intentionally.
 * The MCP server is a separate deployment unit from the platform — no cross-process
 * imports are allowed. Duplication is the correct pattern here.
 *
 * Implements MCP_BRIEF §4.2 response envelope contract.
 */

// ── Tool call types ───────────────────────────────────────────────────────────

/** Body sent to a legacy /api/mcp/execute or /api/mcp/plan call. Kept for reference only. */
export interface McpToolCall {
  tool: string
  params: Record<string, unknown>
}

// ── Epistemics block ──────────────────────────────────────────────────────────

/** Mandatory ethics/epistemics block on every MCP response (MCP_BRIEF D7). */
export interface EpistemicsBlock {
  /** True for surgical primitive calls (primitives, bundles, reads); false for legacy full-pipeline calls. */
  surgical: boolean
  /**
   * Calibrated confidence band for the answer.
   *
   * 'none' (F-126) = the served result set is EMPTY, so there is no finding for a
   * band to grade. Not a weak finding — the absence of one. Mirrors
   * platform/src/lib/mcp/types.ts, which is where the value is produced.
   */
  confidence_band: 'high' | 'medium' | 'low' | 'none'
  /**
   * Evidence state of the served result (F-126), when the producing surface
   * measured it: 'present' | 'empty' | 'indeterminate'. Absent where nothing
   * measured it — never defaulted.
   */
  evidence_state?: 'present' | 'empty' | 'indeterminate'
  /**
   * Horizon in days for predictive answers; null for non-predictive.
   * Example: 90 = "applies within the next ~3 months".
   */
  horizon_days: number | null
  /**
   * The specific condition that would falsify this answer.
   * Required for predictive answers; null for factual.
   */
  falsifier: string | null
}

// ── Synthesis audit block ─────────────────────────────────────────────────────

/**
 * Audit block proving B.11 Whole-Chart-Read floor was honored.
 * Present on holistic-synthesis responses.
 */
export interface SynthesisAuditBlock {
  /** L2.5 tools that actually fired in this pipeline run. */
  l25_tools_fired: string[]
  /** Human-readable summary of L2.5 contribution. */
  l25_contribution_summary: string
  /** Top signal IDs most influential in the synthesis. */
  dominant_signals: string[]
  /** Jyotish domains touched by the synthesis. */
  domains_touched: string[]
  /** True when ≥1 L2.5 tool fired (B.11 floor satisfied). */
  holistic_read_passed: boolean
}

// ── MCP envelope types ────────────────────────────────────────────────────────

/** Successful MCP response envelope (MCP_BRIEF §4.2). */
export interface McpEnvelopeSuccess {
  ok: true
  trace_id: string
  // audience_tier removed (Stream A 3.tier_excision 2026-05-28).
  epistemics: EpistemicsBlock
  result: unknown
  citations: unknown[]
  plan: unknown
  predictions_logged: unknown[]
  synthesis_audit: SynthesisAuditBlock | null
  suggested_followups: string[]
  warnings: string[]
}

/** Error MCP response envelope (MCP_BRIEF §4.2). */
export interface McpEnvelopeError {
  ok: false
  trace_id: string
  error: {
    class: string
    message: string
    remediation?: string
  }
}

/** Union type of success and error envelopes. */
export type McpEnvelope = McpEnvelopeSuccess | McpEnvelopeError

// ── Platform call result ──────────────────────────────────────────────────────

/** Result of a callPlatform* function — the HTTP status and parsed envelope. */
export interface PlatformCallResult {
  status: number
  envelope: McpEnvelope
}

// ── Principal ─────────────────────────────────────────────────────────────────

/** Resolved principal from Bearer key validation. */
export interface Principal {
  user_uid: string
  // audience_tier removed (Stream A 3.tier_excision 2026-05-28).
  key_id: string
  /** Role from profiles table. Populated by M0 entitlement gate (2026-06-30). */
  role: 'guest' | 'super_admin'
  /**
   * Bound model family for this API key (M6 declared profile 2026-07-01).
   * Undefined = undeclared → universal-best surface served.
   * Values: 'anthropic' | 'gemini' | 'openai' | 'deepseek'
   */
  model_family?: 'anthropic' | 'gemini' | 'openai' | 'deepseek'
}

// ── Key validation response ───────────────────────────────────────────────────

/** Response from GET /api/mcp/keys/validate */
export interface KeyValidateResponse {
  valid: boolean
  user_uid?: string
  // audience_tier removed (Stream A 3.tier_excision 2026-05-28).
  key_id?: string
  /** Role resolved from profiles table (M0 entitlement gate). */
  role?: 'guest' | 'super_admin'
  /**
   * Bound model family for this key (M6 declared profile 2026-07-01).
   * Null = undeclared → universal-best surface served.
   */
  model_family?: string | null
  error?: string
}
