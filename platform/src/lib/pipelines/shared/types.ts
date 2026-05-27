/**
 * Shared pipeline types — unit 3.gateway_pipeline_isolation.
 *
 * The two pipelines (single_pass + agentic) share these stage signatures.
 * Each stage is a pure function that takes its inputs + a typed context
 * and returns a result; the route is responsible for wiring them in order.
 *
 * No HTTP / streaming primitives live here — those stay in route.ts (until
 * G5b ships the full split). This module is the seam where the two pipelines
 * meet so behaviour stays byte-identical.
 */

import type { Principal, Permission, DbLike } from '@/lib/auth/authorizeChartAccess'

/** Resolved authentication context for a single consult request. */
export interface AuthContext {
  principal: Principal
  isSuperAdmin: boolean
  permission: Permission
}

/** Resolved chart context (chart row + chart_id). */
export interface ChartContext {
  chartId: string
  chart: {
    id: string
    name: string
    birth_date: string
    birth_time: string
    birth_place: string
    client_id: string
  }
}

/** Result of the auth + chart resolution stage. */
export interface ResolvedRequestContext {
  auth: AuthContext
  chart: ChartContext
}

/** Inputs to the auth + chart resolution stage. */
export interface ResolveContextInput {
  userUid: string
  chartId: string
  db: DbLike
}

/** Error contract — the resolver returns this discriminated union instead of throwing. */
export type ResolveContextResult =
  | { ok: true; ctx: ResolvedRequestContext }
  | { ok: false; reason: 'invalid_chart_id' | 'chart_not_found' | 'db_error' | 'forbidden'; detail?: string }
