/**
 * handler_ayanamsha.ts — handler-level Lahiri-primary default (SS N-339 / N-342, PR-2).
 * =====================================================================================
 * PR-1 put the default at the WEB BRIDGE (`tool_name_bridge.ts`). In-process callers (synergy,
 * the planner, compiled floors, MCP primitives that call `cap.handler` directly) never pass
 * through that bridge, so the default ALSO lives in every registry handler that serves
 * ayanamsha-bearing rows. This file is the one place a handler gets it from.
 *
 * Contract (identical to the bridge, because both call the PR-1 resolver `resolveAyanamshaArg`):
 *   - `ayanamsha_id` omitted / null / blank      -> `PRIMARY_AYANAMSHA` (lahiri_chitrapaksha)
 *   - short id / any case ("LAHIRI", "kp", ...)  -> the stored long id
 *   - `ayanamsha_id: "all"` OR `ayanamsha_scope: "all"` (with no explicit id)
 *                                                -> explicit opt-out: the old pooled shape, no
 *                                                   ayanamsha filter, `ayanamsha_scope: "all"`
 *                                                   echoed in the response
 *   - unknown id                                 -> throws `InvalidAyanamshaError` (message lists
 *                                                   the stored ids); handlers' try/catch turns it
 *                                                   into an `is_error` result — never a silent
 *                                                   zero-row query
 *   An explicit stored id beats `ayanamsha_scope: "all"` (the more specific instruction wins).
 *
 * `INVARIANT` sentinel: ayanamsha-independent facts are stored under `ayanamsha_id = 'INVARIANT'`
 * (birth panchanga limbs, naisargika bala, nakshatra_cross_ayanamsha, ...). It is a sentinel, NOT
 * a sixth ayanamsha. Handlers whose categories can be INVARIANT-stored pass
 * `includeInvariant: true` so a primary filter reads `ayanamsha_id IN ($n, 'INVARIANT')`.
 *
 * Ordering: `ayanamshaServeOrderBy()` is the FINAL ORDER BY tie-break every pooled/paged handler
 * appends. It sorts in `AYANAMSHA_SERVE_ORDER` (Lahiri first), never alphabetically, so under
 * `"all"` a LIMIT/OFFSET page cannot hide Lahiri behind krishnamurti rows.
 *
 * Pure: no I/O, no DB. No alias map lives here (the vocabulary is `chart_facts_helpers.ts`).
 */
import { AYANAMSHA_ALL, AYANAMSHA_SERVE_ORDER, INVARIANT_AYANAMSHA, PRIMARY_AYANAMSHA } from './constants'
import { InvalidAyanamshaError, resolveAyanamshaArg } from '../chart_facts_helpers'

export interface HandlerAyanamsha {
  /** Stored id to filter on, or `null` for the explicit `"all"` opt-out. */
  id: string | null
  /** True for the explicit `"all"` opt-out (pooled, unfiltered). */
  all: boolean
  source: 'omitted' | 'explicit' | 'all'
}

/**
 * Resolve a handler's `ayanamsha_id` / `ayanamsha_scope` args. Throws `InvalidAyanamshaError`
 * (never returns a silent zero-row id) for an unknown value.
 */
export function resolveHandlerAyanamsha(args: Record<string, unknown>): HandlerAyanamsha {
  const r = resolveAyanamshaArg(args['ayanamsha_id'])
  if (!r.ok) throw new InvalidAyanamshaError(r.received)
  if (r.source === 'all') return { id: null, all: true, source: 'all' }
  if (r.source === 'omitted') {
    const scope = args['ayanamsha_scope']
    if (typeof scope === 'string' && scope.trim().toLowerCase() === AYANAMSHA_ALL) {
      return { id: null, all: true, source: 'all' }
    }
    return { id: r.ayanamsha_id, all: false, source: 'omitted' }
  }
  return { id: r.ayanamsha_id, all: false, source: 'explicit' }
}

export type HandlerAyanamshaAttempt =
  | { ok: true; aya: HandlerAyanamsha }
  | { ok: false; result: { content: Record<string, unknown>; is_error: true } }

/**
 * Non-throwing variant for handlers that resolve BEFORE their `try` block: an unknown id becomes
 * a structured `is_error` result (message lists the stored ids), never an uncaught exception and
 * never a silent zero-row query. `extra` is merged into the error content (e.g. `{ chart_id }`).
 */
export function tryResolveHandlerAyanamsha(
  args: Record<string, unknown>,
  extra: Record<string, unknown> = {},
): HandlerAyanamshaAttempt {
  try {
    return { ok: true, aya: resolveHandlerAyanamsha(args) }
  } catch (err) {
    if (err instanceof InvalidAyanamshaError) {
      return {
        ok: false,
        result: {
          content: { error: err.message, code: err.code, stored_ids: err.stored_ids, ...extra },
          is_error: true,
        },
      }
    }
    throw err
  }
}

/**
 * Append the ayanamsha predicate to `params` and return the SQL fragment (with a leading
 * ` AND `), or `''` for the `"all"` opt-out. `includeInvariant` widens the filter to the
 * INVARIANT sentinel rows (see file header).
 */
export function pushAyanamshaFilter(
  aya: HandlerAyanamsha,
  params: unknown[],
  opts: { column?: string; includeInvariant?: boolean } = {},
): string {
  if (aya.id === null) return ''
  const col = opts.column ?? 'ayanamsha_id'
  params.push(aya.id)
  const n = params.length
  return opts.includeInvariant
    ? ` AND ${col} IN ($${n}, '${INVARIANT_AYANAMSHA}')`
    : ` AND ${col} = $${n}`
}

/**
 * ORDER BY item that sorts a stored `ayanamsha_id` in `AYANAMSHA_SERVE_ORDER` (Lahiri first),
 * with the column itself as the deterministic last resort (the INVARIANT sentinel is not in the
 * serve order, so it sorts after the five, NULLS LAST). Use as the FINAL ORDER BY term(s), or as
 * the first term wherever `ayanamsha_id` used to be the leading sort key.
 */
export function ayanamshaServeOrderBy(column = 'ayanamsha_id'): string {
  const list = AYANAMSHA_SERVE_ORDER.map((id) => `'${id}'`).join(',')
  return `array_position(ARRAY[${list}]::text[], ${column}::text), ${column}`
}

/** Response provenance for the resolved scope: the `"all"` marker, or the id that was served. */
export function ayanamshaScopeEcho(aya: HandlerAyanamsha): { ayanamsha_scope: 'all' } | { ayanamsha_id: string } {
  return aya.id === null ? { ayanamsha_scope: AYANAMSHA_ALL } : { ayanamsha_id: aya.id }
}

/** Human-readable scope for empty_reason strings. */
export function describeAyanamshaScope(aya: HandlerAyanamsha): string {
  return aya.id === null ? "all ayanamshas (ayanamsha_scope 'all')" : `ayanamsha '${aya.id}'`
}

export { PRIMARY_AYANAMSHA }
