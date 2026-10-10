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
import { AYANAMSHA_ALL, AYANAMSHA_INJECTED_ARG, AYANAMSHA_SERVE_ORDER, INVARIANT_AYANAMSHA, PRIMARY_AYANAMSHA } from './constants'
import { InvalidAyanamshaError, resolveAyanamshaArg } from '../chart_facts_helpers'
import { KP_FRAME_AYANAMSHA, KP_FRAME_LABEL } from '../kp_frame'
import { KP_FRAME_CATEGORIES, isKpFrameCategory, partitionKpCategories } from './kp_categories'

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

/** The KP-frame read of a generic reader's KP branch (see `resolveKpFrameAyanamsha`). */
export interface KpFrameAyanamsha {
  /** Always the Krishnamurti read: `{ id: 'krishnamurti', all: false }`. */
  aya: HandlerAyanamsha
  /** The fields every KP-branch response carries: `ayanamsha_id`, `frame_label`, and the note when relevant. */
  echo: { ayanamsha_id: string; frame_label: string; ayanamsha_note?: string }
}

/**
 * KP branch of a generic reader (SS N-357): Krishnamurti Paddhati has ONE frame by doctrine, the
 * Krishnamurti ayanamsha, so a KP read (`get_karakas` system=kp, `get_nakshatra` domain=kp) is
 * served at `krishnamurti` WHATEVER `ayanamsha_id` / `ayanamsha_scope` the caller passed: the
 * Lahiri primary passed explicitly, an alias, "all", `ayanamsha_scope: 'all'`, another stored
 * id, or an unrecognised id. The passed id is ignored exactly as `fetchKpCuspChain` ignores it
 * (never validated, never an error). When the caller asked for something other than
 * Krishnamurti, the response says the request was not applied (`ayanamsha_note`) rather than
 * silently serving a different frame. SS N-368: only an EXPLICIT request counts (`isExplicitAyanamshaRequest`);
 * an omitted id or the bridge-injected Lahiri default asked for nothing, so no note (the frame fields stay).
 * Pure; non-KP branches never call this.
 */
export function resolveKpFrameAyanamsha(args: Record<string, unknown>): KpFrameAyanamsha {
  const aya: HandlerAyanamsha = { id: KP_FRAME_AYANAMSHA, all: false, source: 'explicit' }
  const requested = kpFrameRequestedAs(args)
  const echo: KpFrameAyanamsha['echo'] = { ayanamsha_id: KP_FRAME_AYANAMSHA, frame_label: KP_FRAME_LABEL }
  if (requested !== null) {
    echo.ayanamsha_note =
      `KP has one frame by doctrine (Krishnamurti); the requested ayanamsha_id/scope '${requested}' does not apply here`
  }
  return { aya, echo }
}

/**
 * True when `args` carries the web bridge's injection marker (`ayanamsha_injected: true`, SS N-368) AND the id in
 * `args` is the Lahiri primary the bridge filled in: the caller named no ayanamsha, the default was supplied for
 * them. A marker beside any other id (or no id) is not an injection (the marker cannot mask an explicit request;
 * the bridge strips a caller-supplied marker anyway). Internal to `isExplicitAyanamshaRequest`.
 */
function isInjectedPrimaryDefault(args: Record<string, unknown>): boolean {
  if (args[AYANAMSHA_INJECTED_ARG] !== true) return false
  const r = resolveAyanamshaArg(args['ayanamsha_id'])
  return r.ok && r.source === 'explicit' && r.ayanamsha_id === PRIMARY_AYANAMSHA
}

/**
 * THE one decision "did the caller ask for an ayanamsha?" (SS N-368 "no false notes"). A KP read says "the requested
 * ayanamsha does not apply here" ONLY when this is true, so a default the system filled in is never reported as a
 * request that was ignored. Explicit means:
 *   - an `ayanamsha_id` the caller passed (the Lahiri primary included, an alias, "all", another stored id, nonsense),
 *     unless it is the bridge-injected default (`ayanamsha_injected: true` beside the primary id);
 *   - `ayanamsha_scope: "all"` (the bridge's own spelling of an explicit `ayanamsha_id: "all"`).
 * Not explicit: no id at all (a direct call, the handler's own Lahiri default), a blank id, the injected default.
 * Pure; never throws and never validates (KP ignores the passed id).
 */
export function isExplicitAyanamshaRequest(args: Record<string, unknown>): boolean {
  const r = resolveAyanamshaArg(args['ayanamsha_id'])
  if (!r.ok) return true
  if (r.source === 'all') return true
  const scope = args['ayanamsha_scope']
  const scopeAll = typeof scope === 'string' && scope.trim().toLowerCase() === AYANAMSHA_ALL
  if (r.source === 'omitted') return scopeAll
  // an id is present: explicit, unless the bridge put it there; an injected id never hides a scope "all" the caller passed
  return !isInjectedPrimaryDefault(args) || scopeAll
}

/**
 * What the caller EXPLICITLY asked for when it is NOT the Krishnamurti frame (`'all'`, the received value of an
 * unrecognised id, or the passed non-Krishnamurti id); `null` when nothing was asked (`isExplicitAyanamshaRequest`
 * false: an omitted or bridge-injected default) or when Krishnamurti itself was. Never throws, never validates.
 */
export function kpFrameRequestedAs(args: Record<string, unknown>): string | null {
  if (!isExplicitAyanamshaRequest(args)) return null
  const r = resolveAyanamshaArg(args['ayanamsha_id'])
  const scope = args['ayanamsha_scope']
  const scopeAll = typeof scope === 'string' && scope.trim().toLowerCase() === AYANAMSHA_ALL
  if (!r.ok) return String(r.received)
  if (r.source === 'all') return AYANAMSHA_ALL
  if (r.source === 'explicit' && !isInjectedPrimaryDefault(args)) {
    return r.ayanamsha_id !== KP_FRAME_AYANAMSHA ? String(args['ayanamsha_id']) : null
  }
  return scopeAll ? AYANAMSHA_ALL : null
}

/**
 * How a category list relates to the KP frame (SS N-358, "a KP category is served in the KP frame"):
 *   - `none`    no KP-frame category in the list: the handler's existing path, byte for byte;
 *   - `kp_only` every category is a KP-frame category: the whole page is read at krishnamurti
 *               exactly like the KP branch (`resolveKpFrameAyanamsha`);
 *   - `mixed`   KP and other categories together: KP rows from krishnamurti, the rest from the
 *               requested/default ayanamsha (`pushMixedKpAyanamshaFilter`).
 */
export interface KpCategoryPlan {
  mode: 'none' | 'kp_only' | 'mixed'
  kp: string[]
  other: string[]
}

export function planKpCategories(categories: readonly string[]): KpCategoryPlan {
  const { kp, other } = partitionKpCategories(categories)
  const mode = kp.length === 0 ? 'none' : other.length === 0 ? 'kp_only' : 'mixed'
  return { mode, kp, other }
}

/**
 * Two-leg ayanamsha predicate of a MIXED page (leading ` AND `):
 *
 *   AND ((fact_category = ANY(ARRAY['cusp_kp_lords',...]::text[]) AND ayanamsha_id = 'krishnamurti')
 *        OR (fact_category <> ALL(ARRAY[...]::text[]) [AND ayanamsha_id = $n | IN ($n,'INVARIANT') | nothing for "all"]))
 *
 * KP-frame categories come ONLY from krishnamurti (one frame, also under "all"); every other
 * category keeps the primary/requested filter, the INVARIANT inclusion and the "all" opt-out of
 * `pushAyanamshaFilter`. One query, so LIMIT / OFFSET / COUNT stay consistent with the page.
 *
 * The KP category names and the KP ayanamsha id are CODE CONSTANTS (kp_categories.ts / kp_frame.ts,
 * pinned `[a-z_]+` by kp_categories_pin.test.ts), inlined as SQL literals exactly like the serve-order
 * ids in `ayanamshaServeOrderBy`; no caller input is interpolated. Because nothing extra is bound, the
 * bind positions ($1 chart, $2 categories, ayanamsha $3, LIMIT/OFFSET after) are the ones the page had
 * before KP categories were read in their own frame. Emitted on one line with single spaces: the
 * five-ayanamsha test simulator parses this exact form.
 */
export function pushMixedKpAyanamshaFilter(
  aya: HandlerAyanamsha,
  params: unknown[],
  opts: { includeInvariant?: boolean } = {},
): string {
  const kpArray = `ARRAY[${KP_FRAME_CATEGORIES.map((c) => `'${c}'`).join(',')}]::text[]`
  let rest = ''
  if (aya.id !== null) {
    params.push(aya.id)
    const n = params.length
    rest = opts.includeInvariant ? ` AND ayanamsha_id IN ($${n}, '${INVARIANT_AYANAMSHA}')` : ` AND ayanamsha_id = $${n}`
  }
  return ` AND ((fact_category = ANY(${kpArray}) AND ayanamsha_id = '${KP_FRAME_AYANAMSHA}') OR (fact_category <> ALL(${kpArray})${rest}))`
}

/**
 * The KP dasha system (SS N-362 a / N-368): `chart_dashas` rows with this `system_id` are the Moon's KP sub-period chain,
 * KP content, so they are read at krishnamurti and labelled wherever they appear. Not one of the six KP categories (those
 * are `chart_facts` categories); a dasha SYSTEM id. Pinned `[a-z_]+` (inlined as a SQL literal, like the KP category names).
 */
export const KP_FRAME_DASHA_SYSTEM = 'vimshottari_kp'

/**
 * Two-leg ayanamsha predicate of a MULTI-SYSTEM dasha page (`get_dashas` system="all" or an unrecognised system value;
 * leading ` AND `), the `chart_dashas` counterpart of `pushMixedKpAyanamshaFilter`:
 *
 *   AND ((d.system_id = 'vimshottari_kp' AND d.ayanamsha_id = 'krishnamurti')
 *        OR (d.system_id IS DISTINCT FROM 'vimshottari_kp' [AND d.ayanamsha_id = $n | nothing for "all"]))
 *
 * The KP system comes ONLY from krishnamurti (one frame, also under "all"); every other system keeps the requested/default
 * ayanamsha filter and the "all" opt-out (`IS DISTINCT FROM`, so a NULL system_id is served exactly as before). The KP
 * system name and id are CODE CONSTANTS inlined as literals, nothing extra is bound: the bind positions, LIMIT / OFFSET and
 * ORDER BY of the page are the ones it had before. One statement, so the page, its cursor and its generation fence stay
 * the single-statement snapshot. Single-line, single-spaced: the test simulator parses this exact form.
 */
export function pushMixedKpSystemAyanamshaFilter(
  aya: HandlerAyanamsha,
  params: unknown[],
  opts: { column?: string; systemColumn?: string } = {},
): string {
  const col = opts.column ?? 'ayanamsha_id'
  const sys = opts.systemColumn ?? 'system_id'
  let rest = ''
  if (aya.id !== null) {
    params.push(aya.id)
    rest = ` AND ${col} = $${params.length}`
  }
  return ` AND ((${sys} = '${KP_FRAME_DASHA_SYSTEM}' AND ${col} = '${KP_FRAME_AYANAMSHA}') OR (${sys} IS DISTINCT FROM '${KP_FRAME_DASHA_SYSTEM}'${rest}))`
}

/** True for a `chart_dashas` row of the KP dasha system (the rows a multi-system page labels). */
export function isKpDashaRow(row: Record<string, unknown>): boolean {
  return row['system_id'] === KP_FRAME_DASHA_SYSTEM
}

/**
 * Response fields of a MULTI-SYSTEM dasha page that carries KP rows: `kp_frame` (the system read at krishnamurti and the
 * label) always, plus `ayanamsha_note` when the caller EXPLICITLY asked for something other than Krishnamurti AND the page
 * has KP rows (the id applies to the other systems' rows only). Same rule and wording as `mixedKpFrameEcho`.
 */
export function mixedKpSystemEcho(
  args: Record<string, unknown>,
  pageHasKpRows: boolean,
): { kp_frame: { ayanamsha_id: string; frame_label: string; systems: string[] }; ayanamsha_note?: string } {
  const requested = kpFrameRequestedAs(args)
  return {
    kp_frame: { ayanamsha_id: KP_FRAME_AYANAMSHA, frame_label: KP_FRAME_LABEL, systems: [KP_FRAME_DASHA_SYSTEM] },
    ...(requested !== null && pageHasKpRows
      ? {
          ayanamsha_note:
            `KP has one frame by doctrine (Krishnamurti); the requested ayanamsha_id/scope '${requested}' does not apply to the KP-frame rows ` +
            `(read at ${KP_FRAME_AYANAMSHA}); it applies to the other rows only`,
        }
      : {}),
  }
}

/**
 * Row labelling of a KP-involving page: KP-frame rows (`all: true` labels every row, for a page that is
 * KP throughout) get `frame_label` additively; every other row is returned untouched (same object).
 * Rows already carry their `ayanamsha_id` (krishnamurti on KP rows), which is the machine-readable frame.
 */
export function labelKpFrameRows<T extends Record<string, unknown>>(rows: readonly T[], all = false): T[] {
  return rows.map((r) => (all || isKpFrameCategory(r['fact_category']) ? { ...r, frame_label: KP_FRAME_LABEL } : r))
}

/**
 * Response fields of a MIXED page: `kp_frame` (which categories were read at krishnamurti and the
 * label) always, plus `ayanamsha_note` when the caller asked for something other than Krishnamurti
 * AND the page carries KP rows. The top-level `ayanamsha_id` / `ayanamsha_scope` of the page keeps
 * describing the non-KP rows.
 */
export function mixedKpFrameEcho(
  args: Record<string, unknown>,
  kpCategories: readonly string[],
  pageHasKpRows: boolean,
): { kp_frame: { ayanamsha_id: string; frame_label: string; categories: string[] }; ayanamsha_note?: string } {
  const requested = kpFrameRequestedAs(args)
  return {
    kp_frame: { ayanamsha_id: KP_FRAME_AYANAMSHA, frame_label: KP_FRAME_LABEL, categories: [...kpCategories] },
    ...(requested !== null && pageHasKpRows
      ? {
          ayanamsha_note:
            `KP has one frame by doctrine (Krishnamurti); the requested ayanamsha_id/scope '${requested}' does not apply to the KP-frame rows ` +
            `(read at ${KP_FRAME_AYANAMSHA}); it applies to the other rows only`,
        }
      : {}),
  }
}

/**
 * One call that gives a reader with a CALLER-SUPPLIED category list (`categories` / `category`) the
 * whole KP rule of SS N-358 ("a KP category is served in the KP frame"), so a reader that does not
 * own the KP categories still never reads one at the Lahiri primary:
 *
 *   - no KP-frame category in `categories`  -> `mode: 'none'`: EXACTLY the reader's previous path
 *     (`resolveHandlerAyanamsha` + `pushAyanamshaFilter` + `ayanamshaScopeEcho`; an unknown id still
 *     throws); rows are returned untouched;
 *   - only KP-frame categories              -> `mode: 'kp_only'`: the whole page is read at
 *     krishnamurti whatever id/scope was passed (alias, "all", nonsense: never validated, like the KP
 *     branch of get_karakas), the echo carries `ayanamsha_id` + `frame_label` (+ `ayanamsha_note` when
 *     the caller asked for another frame) and every row gets `frame_label`;
 *   - both                                  -> `mode: 'mixed'`: KP rows from krishnamurti, the rest from
 *     the requested/default ayanamsha (`pushMixedKpAyanamshaFilter`), `kp_frame` in the echo, KP rows
 *     labelled, the others untouched.
 *
 * `filter(params, opts)` may be called once per statement (page, count) with that statement's own
 * `params`. Pure: no I/O.
 */
export interface KpAwareRead {
  mode: KpCategoryPlan['mode']
  /** The ayanamsha that describes the page (krishnamurti on a KP-only page). */
  aya: HandlerAyanamsha
  /** The KP-frame categories among the requested ones (empty when `mode` is `none`). */
  kpCategories: string[]
  /** Append the ayanamsha predicate for this statement to `params`; returns the SQL fragment. */
  filter(params: unknown[], opts?: { includeInvariant?: boolean }): string
  /** The scope fields to spread into the response content (replaces `ayanamshaScopeEcho(aya)`). */
  echo(rows: readonly Record<string, unknown>[]): Record<string, unknown>
  /** Add `frame_label` to the KP rows (all rows on a KP-only page); other rows are returned as they are. */
  label<T extends Record<string, unknown>>(rows: readonly T[]): T[]
}

export function planKpAwareRead(args: Record<string, unknown>, categories: readonly string[]): KpAwareRead {
  const plan = planKpCategories(categories)
  if (plan.mode === 'none') {
    const aya = resolveHandlerAyanamsha(args)
    return {
      mode: 'none',
      aya,
      kpCategories: [],
      filter: (params, opts) => pushAyanamshaFilter(aya, params, opts),
      echo: () => ({ ...ayanamshaScopeEcho(aya) }),
      label: <T extends Record<string, unknown>>(rows: readonly T[]): T[] => rows as T[],
    }
  }
  if (plan.mode === 'kp_only') {
    const kpFrame = resolveKpFrameAyanamsha(args)
    return {
      mode: 'kp_only',
      aya: kpFrame.aya,
      kpCategories: plan.kp,
      filter: (params, opts) => pushAyanamshaFilter(kpFrame.aya, params, opts),
      echo: () => ({ ...kpFrame.echo }),
      label: (rows) => labelKpFrameRows(rows, true),
    }
  }
  const aya = resolveHandlerAyanamsha(args)
  return {
    mode: 'mixed',
    aya,
    kpCategories: plan.kp,
    filter: (params, opts) => pushMixedKpAyanamshaFilter(aya, params, opts),
    echo: (rows) => ({
      ...ayanamshaScopeEcho(aya),
      ...mixedKpFrameEcho(args, plan.kp, rows.some((r) => r['frame_label'] !== undefined)),
    }),
    label: (rows) => labelKpFrameRows(rows),
  }
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
