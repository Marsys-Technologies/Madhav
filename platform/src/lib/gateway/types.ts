/**
 * Gateway types — unit 3.gateway_pipeline_isolation.
 *
 * The gateway sits between any caller (portal pipeline, MCP server, future
 * agents) and the unified tool contract (G3_contract from unit 2b). It hosts:
 *   • search_tools(query|family) — discoverability over the contract catalog
 *   • invoke_tool(name, params)  — the single chokepoint that
 *       (a) resolves principal + chart_id + ayanamsha_id from the request
 *       (b) authorizes via authorizeChartAccess (per-chart authz)
 *       (c) enforces the B.11 forced-first holistic-read floor
 *       (d) dispatches to the registered tool executor.
 *
 * No retrieval logic lives here — the gateway is plumbing. Tool implementations
 * live in `platform/src/lib/retrieve/**` (owned by sibling unit
 * 3.tool_asset_recon) and are wired in via `registerExecutor` from
 * `executor_registry.ts` to avoid the cross-fence import.
 */

import type { ToolContract, ToolFamily, ToolRole } from '@/lib/contract'
import type { Principal, Permission, DbLike } from '@/lib/auth/authorizeChartAccess'

/** Result row returned from `search_tools`. */
export interface ToolSearchResult {
  canonical_name: string
  description: string
  family: ToolFamily
  role: ToolRole
  per_chart: boolean
  ayanamsha_role: string | null
}

/** Discoverability query — by family, by role, or by free-text. */
export interface ToolSearchQuery {
  /** Free-text query — case-insensitive match on canonical_name OR description. */
  query?: string
  /** Restrict to a family. */
  family?: ToolFamily
  /** Restrict to a role. */
  role?: ToolRole
  /** Max results. Defaults to 32. */
  limit?: number
}

/** Context every `invoke_tool` call must supply. */
export interface InvokeContext {
  /** Authenticated principal (uid + role). Required for per-chart authz. */
  principal: Principal
  /** Chart binding for the call. Required for any `per_chart` tool. */
  chartId?: string
  /** Optional ayanamsha override (engine-isolation, Unit 1.1). */
  ayanamshaId?: string
  /**
   * B.11 floor evidence — has the holistic-read floor (MSR/UCN/CGM minimum)
   * already executed for this query? Set by the pipeline once the floor has
   * run; gateway will reject tool calls when missing AND the requested tool
   * is not itself part of the floor.
   *
   * The gateway accepts a structural assertion (the pipeline marks this
   * `true` once it has executed the canonical floor); it does not re-run
   * MSR/UCN/CGM itself. This keeps the gateway plumbing-only.
   */
  b11FloorSatisfied?: boolean
  /** DB handle for authz. Defaults to the production pg client when omitted. */
  db?: DbLike
}

/** What the gateway accepts for invocation. */
export interface InvokeRequest<TInput = unknown> {
  /** Canonical tool name (from the contract registry). */
  name: string
  /** Input params; will be validated against the contract's Zod schema. */
  params: TInput
  /** Caller context — principal, chart, ayanamsha, B.11 status. */
  ctx: InvokeContext
}

/** Structured failure modes. */
export type InvokeErrorCode =
  | 'UNKNOWN_TOOL'
  | 'INVALID_PARAMS'
  | 'CHART_REQUIRED'
  | 'AUTHZ_DENIED'
  | 'AUTHZ_INSUFFICIENT'   // 'view' permission, but tool requires 'all'
  | 'B11_FLOOR_MISSING'
  | 'NO_EXECUTOR'

export class GatewayError extends Error {
  constructor(
    public readonly code: InvokeErrorCode,
    message: string,
    public readonly meta?: Record<string, unknown>,
  ) {
    super(message)
    this.name = 'GatewayError'
  }
}

/** Outcome of `invoke_tool`. */
export interface InvokeResult<TOutput = unknown> {
  ok: true
  data: TOutput
  /** Echo of the resolved chart/ayanamsha so callers can record provenance. */
  resolved: {
    chartId: string | null
    ayanamshaId: string | null
    permission: Permission | null
  }
}

/**
 * Tool executor — opaque function that the unit owning `lib/retrieve/**`
 * registers per canonical_name. The gateway is contract-only; this indirection
 * keeps the fence clean.
 */
export type ToolExecutor<TInput = unknown, TOutput = unknown> = (
  params: TInput,
  ctx: InvokeContext,
  contract: ToolContract<TInput>,
) => Promise<TOutput>
