/**
 * invoke_tool — the single chokepoint for every gateway-routed tool call.
 *
 * Order of operations (each is a hard gate):
 *   1. Resolve contract by canonical_name → UNKNOWN_TOOL on miss.
 *   2. Validate params against the contract's Zod schema → INVALID_PARAMS on
 *      schema failure.
 *   3. Resolve chart_id:
 *        per_chart tools → require ctx.chartId OR params.chart_id (Zod schemas
 *        already declare chart_id when the tool is per_chart); else CHART_REQUIRED.
 *        non per_chart tools → chart_id is optional.
 *   4. Authorize via authorizeChartAccess — required for any per_chart tool;
 *      'deny' → AUTHZ_DENIED. (Read-only is 'view'; we treat the consult/MCP
 *      retrieval surface as read-only, so 'view' is sufficient. Write tools
 *      registered via the gateway must demand 'all' themselves.)
 *   5. B.11 floor — if the tool is NOT in B11_FLOOR_TOOL_NAMES AND
 *      ctx.b11FloorSatisfied is not true → B11_FLOOR_MISSING.
 *   6. Resolve ayanamsha_id — ctx.ayanamshaId overrides contract default;
 *      passed through to the executor.
 *   7. Look up executor in the registry → NO_EXECUTOR on miss.
 *   8. Dispatch.
 *
 * The gateway returns either a `{ ok: true, data, resolved }` object or
 * throws a `GatewayError`. Throwing (instead of a result union) keeps the
 * happy path ergonomic and matches the rest of the codebase's pattern.
 */

import { getContract } from '@/lib/contract'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import type { DbLike } from '@/lib/auth/authorizeChartAccess'
import {
  GatewayError,
  type InvokeRequest,
  type InvokeResult,
} from './types'
import { isFloorTool } from './b11_floor'
import { getExecutor } from './executor_registry'

/** Lazy import of the production pg client — avoids pulling `server-only` into tests. */
async function defaultDb(): Promise<DbLike> {
  const mod = await import('@/lib/db/client')
  return { query: mod.query }
}

export async function invokeTool<TInput = unknown, TOutput = unknown>(
  req: InvokeRequest<TInput>,
): Promise<InvokeResult<TOutput>> {
  const { name, params, ctx } = req

  // 1. Contract lookup
  const contract = getContract(name)
  if (!contract) {
    throw new GatewayError('UNKNOWN_TOOL', `No contract for tool "${name}".`, {
      name,
    })
  }

  // 2. Param validation (Zod). We don't mutate `params` — if Zod returns
  //    a transformed shape (e.g. backward-compat aliases), pass that down.
  const parsed = contract.input_schema.safeParse(params)
  if (!parsed.success) {
    throw new GatewayError(
      'INVALID_PARAMS',
      `Schema validation failed for tool "${name}".`,
      { name, issues: parsed.error.issues },
    )
  }
  const validatedParams = parsed.data as TInput

  // 3. Chart resolution.
  //    Per-chart tools must have a chart_id either in the params (Zod schema
  //    enforces shape; we read the field defensively) or in ctx.chartId.
  let chartId: string | null = ctx.chartId ?? null
  if (!chartId && validatedParams && typeof validatedParams === 'object') {
    const maybe = (validatedParams as Record<string, unknown>).chart_id
    if (typeof maybe === 'string' && maybe.length > 0) chartId = maybe
  }
  if (contract.per_chart && !chartId) {
    throw new GatewayError(
      'CHART_REQUIRED',
      `Tool "${name}" is per-chart but no chart_id was supplied.`,
      { name },
    )
  }

  // 4. Authorization — only for per_chart tools (non-chart tools like
  //    read_classical_text are corpus reads and skip per-chart authz).
  let permission: Awaited<ReturnType<typeof authorizeChartAccess>> | null = null
  if (contract.per_chart && chartId) {
    const db = ctx.db ?? (await defaultDb())
    permission = await authorizeChartAccess({
      principal: ctx.principal,
      chartId,
      db,
    })
    if (permission === 'deny') {
      throw new GatewayError(
        'AUTHZ_DENIED',
        `Principal ${ctx.principal.uid} denied access to chart ${chartId}.`,
        { name, chartId },
      )
    }
  }

  // 5. B.11 floor — structural enforcement.
  //    A non-floor tool may not run until the pipeline has marked the floor
  //    satisfied. Floor tools are always allowed (they ARE the floor).
  if (!isFloorTool(name) && !ctx.b11FloorSatisfied) {
    throw new GatewayError(
      'B11_FLOOR_MISSING',
      `Tool "${name}" requires the B.11 holistic-read floor before invocation. ` +
        'Run MSR/UCN/CGM (or a holistic bundle) first and set ctx.b11FloorSatisfied.',
      { name },
    )
  }

  // 6. Resolve ayanamsha — ctx overrides contract default.
  const ayanamshaId = ctx.ayanamshaId ?? contract.ayanamsha_id ?? null

  // 7. Executor lookup
  const executor = getExecutor(name)
  if (!executor) {
    throw new GatewayError(
      'NO_EXECUTOR',
      `No executor registered for tool "${name}". The contract is present ` +
        'but no retrieval-layer implementation has been wired in.',
      { name },
    )
  }

  // 8. Dispatch — executor sees the validated params + the resolved context.
  const data = (await executor(
    validatedParams as unknown,
    { ...ctx, chartId: chartId ?? undefined, ayanamshaId: ayanamshaId ?? undefined },
    contract,
  )) as TOutput

  return {
    ok: true,
    data,
    resolved: {
      chartId,
      ayanamshaId,
      permission,
    },
  }
}
