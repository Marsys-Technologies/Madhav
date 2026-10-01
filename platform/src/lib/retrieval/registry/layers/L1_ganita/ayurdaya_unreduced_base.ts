/**
 * ayurdaya_unreduced_base — display-side disclosure for served Āyurdāya (longevity) figures
 * ==========================================================================================
 * SS N-62 Q10 (display-side fix; no stored number, writer, or L1 row is touched).
 *
 * The ga_ayurdaya writer computes the Piṇḍāyu / Aṃśāyu / Naisargikāyu totals with
 * `apply_haranas=False` (ga_ayurdaya_writer.py) — they are UNREDUCED BASE FIGURES: the
 * classical reductive haranas are not applied. A bare "98.75 years" served with no caveat reads
 * as a lifespan figure, which the MACRO_PLAN Ethical Framework (probabilistic, calibrated, not
 * fortune-telling; health/longevity disclosure tiers) forbids.
 *
 * This module is the SINGLE source of the machine-readable fields + plain-language caveat, shared
 * by every served surface that can emit ayurdaya year figures: get_ayurdaya, chart_facts_query,
 * query_signals (the L2 `ayurdaya:*` MSR signals), resolve_metric, and — as a safety net for the
 * generic `categories`-taking tools — a registry-level post-processor (see registry/index.ts).
 *
 * §N.7 item 4 / §N.8 (earned signal): a row is labelled `unreduced_base` / `reductions_applied:false`
 * ONLY when a harana_status this module recognises as "base only" was actually read for the figure:
 *   - a `total_years` row: its OWN harana_status;
 *   - a `<method>_contribution_years` row: the harana_status of the SAME method's total on the same
 *     page / ayanamsha (a contribution is a component of that total);
 *   - the `applicable_method` row (which carries all three raw totals): every method it names must
 *     have a confirmed total on the page.
 * Anything else — an unknown/missing status, a contribution-only or applicable_method-only page with
 * no total to read a status from — is `reduction_status_unverified` with `reductions_applied:null`:
 * an honest null beats an invented judgment (§N.7 item 6). Statuses are applied PER ROW; the page-level
 * summary is `unreduced_base` only if every year row is confirmed, `reduction_status_unverified` if
 * none is, and `mixed_reduction_status` otherwise (see `figure_counts`).
 */
import { judgmentFlag, type JudgmentFlag } from '../../../envelope'

/** `figure_kind` for figures confirmed to be the unreduced base computation. */
export const AYURDAYA_FIGURE_KIND_UNREDUCED_BASE = 'unreduced_base' as const
/** `figure_kind` when a served figure's harana (reduction) status could not be confirmed. */
export const AYURDAYA_FIGURE_KIND_STATUS_UNVERIFIED = 'reduction_status_unverified' as const
/** Page-level only: some rows confirmed unreduced, some unconfirmed (see per-row figure_kind). */
export const AYURDAYA_FIGURE_KIND_MIXED = 'mixed_reduction_status' as const

/** Plain-language caveat served with every unreduced base figure. */
export const AYURDAYA_UNREDUCED_BASE_CAVEAT =
  'Unreduced base figure from the classical pinda/amsa/nisarga computation; no reductions (harana) are applied; not a prediction of lifespan.'

/** Caveat when the reduction status of a served figure could not be confirmed from its own data. */
export const AYURDAYA_STATUS_UNVERIFIED_CAVEAT =
  'Classical pinda/amsa/nisarga figure whose harana (reduction) status could not be confirmed from the served row; do not read it as a reduced or final figure; not a prediction of lifespan.'

/** Caveat for a page whose rows differ in confirmed status. */
export const AYURDAYA_MIXED_CAVEAT =
  'Classical pinda/amsa/nisarga figures: some are confirmed unreduced base figures (no reductions (harana) applied) and some have a harana (reduction) status that could not be confirmed; read each row\'s figure_kind; none is a reduced or final figure; not a prediction of lifespan.'

/** harana_status values the writer emits for "base ayus only, reductive haranas not applied". */
const UNREDUCED_BASE_HARANA_STATUSES: ReadonlySet<string> = new Set(['base_only_haranas_deferred_to_w3'])

const ALL_METHODS: readonly string[] = ['pindayu', 'amsayu', 'nisargayu']

type Row = Record<string, unknown>

export type AyurdayaRowFigureKind = typeof AYURDAYA_FIGURE_KIND_UNREDUCED_BASE | typeof AYURDAYA_FIGURE_KIND_STATUS_UNVERIFIED

export interface AyurdayaRowFigure {
  figure_kind: AyurdayaRowFigureKind
  /** false = confirmed unreduced base; null = could not be confirmed (never `true`). */
  reductions_applied: false | null
}

export interface AyurdayaFigureDisclosure {
  figure_kind: AyurdayaRowFigureKind | typeof AYURDAYA_FIGURE_KIND_MIXED
  reductions_applied: false | null
  caveat: string
  figure_counts: { unreduced_base: number; reduction_status_unverified: number }
  judgment_flag: JudgmentFlag
  /** Per-row figure, keyed by the very row object that was passed in. */
  row_figures: Map<Row, AyurdayaRowFigure>
}

export interface AyurdayaDeriveOptions {
  /**
   * Treat a fact-shaped row with NO fact_category as ayurdaya. get_ayurdaya's SELECT omits
   * fact_category because its WHERE already pins it; every other surface leaves this false.
   */
  assumeAyurdayaCategory?: boolean
}

// ── Row normalisation (fact-shaped chart_facts rows AND L2 `ayurdaya:*` MSR signal rows) ──────────

interface NormRow {
  key: 'total_years' | 'applicable_method' | 'contribution'
  method: string | null
  ayanamsha: string
  status: string | null
  /** applicable_method only: the methods its jsonb totals name (null = unknown → all three). */
  totalsMethods: string[] | null
}

/** jsonb may arrive as an object or (driver/transport dependent) as a JSON string. */
function jsonbObject(v: unknown): Record<string, unknown> | null {
  if (v && typeof v === 'object' && !Array.isArray(v)) return v as Record<string, unknown>
  if (typeof v === 'string') {
    try {
      const parsed: unknown = JSON.parse(v)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed as Record<string, unknown>
    } catch { /* not JSON → no object */ }
  }
  return null
}

function keyKind(key: string): NormRow['key'] | null {
  if (key === 'total_years') return 'total_years'
  if (key === 'applicable_method') return 'applicable_method'
  if (key.endsWith('_contribution_years')) return 'contribution'
  return null
}

function methodOf(key: string, subject: unknown, jsonb: Record<string, unknown> | null): string | null {
  const fromJsonb = jsonb?.['method']
  if (typeof fromJsonb === 'string' && fromJsonb) return fromJsonb.toLowerCase()
  if (key.endsWith('_contribution_years')) return key.slice(0, key.indexOf('_')).toLowerCase()
  if (key === 'total_years' && typeof subject === 'string' && subject) return subject.toLowerCase()
  return null
}

function totalsMethodsOf(jsonb: Record<string, unknown> | null): string[] | null {
  const totals = jsonb?.['totals']
  if (totals && typeof totals === 'object' && !Array.isArray(totals)) {
    const names = Object.keys(totals as Record<string, unknown>).map(k => k.toLowerCase())
    return names.length > 0 ? names : null
  }
  return null
}

/**
 * Normalise a fact-shaped or signal-shaped row; null if it is not an ayurdaya year-bearing row.
 *  - fact shape  : fact_category (when present it MUST be 'ayurdaya'), fact_key, fact_value_jsonb.
 *  - signal shape: signal_type_id 'ayurdaya:<fact_key>' (configuration_jsonb carries fact_key /
 *                  harana_status / method), or — for a trimmed projection that dropped those columns —
 *                  a summary text starting 'category=ayurdaya | key=<fact_key> | ... harana_status=…'.
 */
function normalizeAyurdayaRow(row: Row, assumeCategory: boolean): NormRow | null {
  const ayanamsha = typeof row['ayanamsha_id'] === 'string' ? row['ayanamsha_id'] : ''
  const category = row['fact_category']
  const hasCategory = category !== undefined && category !== null

  // fact shape
  if (hasCategory || (assumeCategory && row['fact_key'] !== undefined)) {
    if (hasCategory && category !== 'ayurdaya') return null
    const key = String(row['fact_key'] ?? '')
    const kind = keyKind(key)
    if (!kind) return null
    const jsonb = jsonbObject(row['fact_value_jsonb'])
    const status = typeof jsonb?.['harana_status'] === 'string' ? jsonb['harana_status'] : null
    return { key: kind, method: methodOf(key, row['fact_subject'], jsonb), ayanamsha, status, totalsMethods: totalsMethodsOf(jsonb) }
  }

  // signal shape — signal_type_id is the clean detector
  const typeId = row['signal_type_id']
  if (typeof typeId === 'string' && typeId.startsWith('ayurdaya:')) {
    const key = typeId.slice('ayurdaya:'.length)
    const kind = keyKind(key)
    if (!kind) return null
    const cfg = jsonbObject(row['configuration_jsonb'])
    const status = typeof cfg?.['harana_status'] === 'string' ? cfg['harana_status'] : null
    return { key: kind, method: methodOf(key, null, cfg), ayanamsha, status, totalsMethods: totalsMethodsOf(cfg) }
  }

  // signal shape — text fallback (summary carries `category=ayurdaya | key=… | harana_status=…`)
  const text = typeof row['signal_summary_text'] === 'string' ? row['signal_summary_text']
    : typeof row['summary'] === 'string' ? row['summary'] : null
  if (text && text.startsWith('category=ayurdaya')) {
    const key = /\bkey=([A-Za-z0-9_]+)/.exec(text)?.[1] ?? ''
    const kind = keyKind(key)
    if (!kind) return null
    const status = /\bharana_status=([A-Za-z0-9_]+)/.exec(text)?.[1] ?? null
    const method = /\bmethod=([A-Za-z]+)/.exec(text)?.[1]?.toLowerCase() ?? methodOf(key, null, null)
    return { key: kind, method, ayanamsha, status, totalsMethods: null }
  }
  return null
}

/**
 * True iff `row` carries an Āyurdāya year figure: a method total (`total_years`), a per-graha
 * contribution (`<method>_contribution_years`), or the applicable_method row (whose jsonb carries
 * all three raw totals) — in either chart_facts shape or L2 `ayurdaya:*` signal shape.
 */
export function isAyurdayaYearsRow(row: Row, opts: AyurdayaDeriveOptions = {}): boolean {
  return normalizeAyurdayaRow(row, opts.assumeAyurdayaCategory === true) !== null
}

function isConfirmed(status: string | null): boolean {
  return status !== null && UNREDUCED_BASE_HARANA_STATUSES.has(status)
}

function figureFor(confirmed: boolean): AyurdayaRowFigure {
  return confirmed
    ? { figure_kind: AYURDAYA_FIGURE_KIND_UNREDUCED_BASE, reductions_applied: false }
    : { figure_kind: AYURDAYA_FIGURE_KIND_STATUS_UNVERIFIED, reductions_applied: null }
}

/** Classify every ayurdaya year row in `rows` (per row; see the module header for the rules). */
function classifyRows(rows: readonly Row[], assumeCategory: boolean): Map<Row, AyurdayaRowFigure> {
  const norm: Array<[Row, NormRow]> = []
  for (const r of rows) {
    const n = normalizeAyurdayaRow(r, assumeCategory)
    if (n) norm.push([r, n])
  }
  // Confirmed-ness of each (ayanamsha, method) total — every total row for that key must be confirmed.
  const totalConfirmed = new Map<string, boolean>()
  for (const [, n] of norm) {
    if (n.key !== 'total_years' || !n.method) continue
    const k = `${n.ayanamsha}|${n.method}`
    totalConfirmed.set(k, (totalConfirmed.get(k) ?? true) && isConfirmed(n.status))
  }
  const out = new Map<Row, AyurdayaRowFigure>()
  for (const [row, n] of norm) {
    let confirmed: boolean
    if (n.key === 'total_years') {
      confirmed = isConfirmed(n.status)
    } else if (n.key === 'contribution') {
      confirmed = n.method !== null && totalConfirmed.get(`${n.ayanamsha}|${n.method}`) === true
    } else {
      const methods = n.totalsMethods ?? ALL_METHODS
      confirmed = methods.every(m => totalConfirmed.get(`${n.ayanamsha}|${m}`) === true)
    }
    out.set(row, figureFor(confirmed))
  }
  return out
}

/** Page-level summary of a per-row figure map (null when empty). */
function summarize(rowFigures: Map<Row, AyurdayaRowFigure>): AyurdayaFigureDisclosure | null {
  if (rowFigures.size === 0) return null
  let unreduced = 0
  let unverified = 0
  for (const f of rowFigures.values()) {
    if (f.figure_kind === AYURDAYA_FIGURE_KIND_UNREDUCED_BASE) unreduced++; else unverified++
  }
  const figure_counts = { unreduced_base: unreduced, reduction_status_unverified: unverified }
  if (unverified === 0) {
    return {
      figure_kind: AYURDAYA_FIGURE_KIND_UNREDUCED_BASE, reductions_applied: false, caveat: AYURDAYA_UNREDUCED_BASE_CAVEAT,
      figure_counts, row_figures: rowFigures,
      judgment_flag: judgmentFlag('ayurdaya_unreduced_base_figures', AYURDAYA_UNREDUCED_BASE_CAVEAT, 'info'),
    }
  }
  const mixed = unreduced > 0
  const caveat = mixed ? AYURDAYA_MIXED_CAVEAT : AYURDAYA_STATUS_UNVERIFIED_CAVEAT
  return {
    figure_kind: mixed ? AYURDAYA_FIGURE_KIND_MIXED : AYURDAYA_FIGURE_KIND_STATUS_UNVERIFIED,
    reductions_applied: null, caveat, figure_counts, row_figures: rowFigures,
    judgment_flag: judgmentFlag('ayurdaya_unreduced_base_figures', caveat, 'warning'),
  }
}

/**
 * Derive the disclosure for a served set of rows. Returns null when the rows carry no Āyurdāya year
 * figure (nothing to caveat; never fabricated for a page that does not carry one).
 */
export function deriveAyurdayaFigureDisclosure(
  rows: readonly Row[],
  opts: AyurdayaDeriveOptions = {},
): AyurdayaFigureDisclosure | null {
  return summarize(classifyRows(rows, opts.assumeAyurdayaCategory === true))
}

/**
 * Annotate (non-mutating) every year-bearing row with its OWN `figure_kind` + `reductions_applied`.
 * Only adds keys — every stored value (fact_value_num, fact_value_text, fact_value_jsonb) is passed
 * through untouched. Rows with no year figure (e.g. maraka_grahas) are returned as-is.
 */
export function annotateAyurdayaYearRows(rows: readonly Row[], disclosure: AyurdayaFigureDisclosure | null): Row[] {
  if (!disclosure) return [...rows]
  return rows.map(r => {
    const f = disclosure.row_figures.get(r)
    return f ? { ...r, figure_kind: f.figure_kind, reductions_applied: f.reductions_applied } : r
  })
}

/** The nested, machine-readable disclosure object served by the generic (non-flat) surfaces. */
export function ayurdayaDisclosureObject(disclosure: AyurdayaFigureDisclosure): Record<string, unknown> {
  return {
    figure_kind: disclosure.figure_kind,
    reductions_applied: disclosure.reductions_applied,
    caveat: disclosure.caveat,
    figure_counts: disclosure.figure_counts,
    applies_to: 'ayurdaya rows/signals with fact_key total_years / *_contribution_years / applicable_method; each carries its own figure_kind',
  }
}

/**
 * chart_facts_query adapter: when the served rows carry Āyurdāya year figures, return a result whose
 * content starts with a nested `ayurdaya_figure_disclosure` object and a `judgment_flags` entry
 * (placed FIRST so a tail-clipping bundler cannot drop them). Returns the same reference unchanged
 * otherwise, so every non-ayurdaya response is byte-identical.
 */
export function withAyurdayaFigureDisclosure<T extends { content: unknown; is_error: boolean }>(
  result: T,
  servedRows: readonly Row[],
): T {
  const disclosure = deriveAyurdayaFigureDisclosure(servedRows)
  if (!disclosure || !result.content || typeof result.content !== 'object' || Array.isArray(result.content)) return result
  const { judgment_flags: priorFlags, ...rest } = result.content as Record<string, unknown>
  const flags = Array.isArray(priorFlags) ? priorFlags : []
  return {
    ...result,
    content: {
      ayurdaya_figure_disclosure: ayurdayaDisclosureObject(disclosure),
      judgment_flags: [...flags, disclosure.judgment_flag],
      ...rest,
    },
  }
}

// ── Registry-level safety net (generic `categories`-taking tools, assess_*, bundles, …) ───────────
//
// WHAT THIS SAFETY NET DOES NOT COVER (coverage limits — read before relying on it; each is a place a
// served Āyurdāya figure can still go out WITHOUT a per-row figure_kind / page-level disclosure):
//
//  1. Rows without a recognisable shape are not disclosed. A fact-shaped row is recognised only if it
//     carries `fact_category` === 'ayurdaya' (+ a year-bearing `fact_key`); a signal-shaped row only
//     via `signal_type_id` 'ayurdaya:<key>' or a `summary` / `signal_summary_text` that STARTS with
//     'category=ayurdaya'. A projection that drops `fact_category` (without `assumeAyurdayaCategory`,
//     which only get_ayurdaya passes) is invisible here.
//  2. Objects nested deeper than WALK_MAX_DEPTH (8) below `content` — or beyond WALK_MAX_NODES /
//     WALK_MAX_KEYS_PER_OBJECT — are not disclosed. A bound hit is warned once (visible), not silent,
//     but the figures beyond it are served without disclosure.
//  3. Prose-only mentions are not disclosed. A number embedded in free text (a narrated sentence, a
//     `reading` / `note` string that does not start with 'category=ayurdaya') is never detected; only
//     structured rows are. The caveat for such a sentence must come from whoever wrote the sentence.
//  4. Per-row rewrite inside COMPOSED tools (assess_*, domain readings, bundles, any tool that
//     re-projects rows) is only as good as what the composed tool leaves in its output: if it drops the
//     rows, or projects away `fact_category` / `signal_type_id` / the `category=ayurdaya` summary prefix,
//     nothing remains to recognise — the rows (or figures) then ship with no disclosure at all. The
//     composed-tool test (register_d8_assess_domain.ayurdaya_composition.test.ts) pins the one projection
//     assess_* uses today (summary text survives). `dossier` is a platform-mcp-native tool with no registry
//     descriptor: it is never wrapped by this post-processor; it serves concept-slice handles
//     (`serving_tool` + `serving_args`), not rows, so each drilled call is wrapped on its own.
//  5. The wrapper declines (returns the result by reference, unannotated) when: `is_error` is true; `content`
//     is not a plain object (an array / string / null content is never walked); `content` already carries
//     a top-level `ayurdaya_figure_disclosure` OR `figure_kind` (chart_facts_query, get_ayurdaya,
//     query_signals own their disclosure — chart_facts_query gets the page-level disclosure and
//     `figure_counts` only, NOT a per-row annotation); or the handler is not `type: 'tool'`.
//  6. A pre-existing non-array `content.judgment_flags` is left untouched (the flag is then present only at
//     `result.judgment_flags`).
//  7. A row an inner tool already tagged (`figure_kind` string present) keeps that tag — it is counted,
//     never recomputed (an inner tool's confirmation against its own total is not re-litigated on a page
//     that may have lost the total).

/** Walk bounds (exported so tests can assert the documented behaviour at the edge). */
export const WALK_MAX_DEPTH = 8
export const WALK_MAX_NODES = 250_000
export const WALK_MAX_KEYS_PER_OBJECT = 5_000

const warned = new Set<string>()
/** Log a loss-of-disclosure condition once per distinct message so it is visible, never silent. */
function warnOnce(message: string): void {
  if (warned.has(message)) return
  warned.add(message)
  try { console.warn(`[ayurdaya_unreduced_base] ${message}`) } catch { /* logging must never throw */ }
}
/** Test hook: forget which warnings were already emitted. */
export function __resetAyurdayaWarningsForTests(): void { warned.clear() }

interface WalkResult { rows: Row[]; boundHit: boolean }

/** True for objects the walk must not descend into (typed arrays / DataView / ArrayBuffer). */
function isOpaqueBinary(v: object): boolean {
  return ArrayBuffer.isView(v) || v instanceof ArrayBuffer
}

/** Collect every ayurdaya year-bearing object reachable (bounded) inside `content`. */
function collectAyurdayaRows(content: unknown): WalkResult {
  const rows: Row[] = []
  let nodes = 0
  let boundHit = false
  const walk = (v: unknown, depth: number): void => {
    if (!v || typeof v !== 'object' || isOpaqueBinary(v)) return
    if (depth > WALK_MAX_DEPTH || nodes >= WALK_MAX_NODES) { boundHit = true; return }
    nodes++
    if (Array.isArray(v)) { for (const x of v) walk(x, depth + 1); return }
    const o = v as Row
    if (normalizeAyurdayaRow(o, false)) rows.push(o)
    const keys = Object.keys(o)
    if (keys.length > WALK_MAX_KEYS_PER_OBJECT) { boundHit = true; return }
    for (const k of keys) walk(o[k], depth + 1)
  }
  walk(content, 0)
  return { rows, boundHit }
}

/**
 * Copy-on-write rewrite: returns `v` itself when nothing beneath it changed, otherwise a shallow copy
 * along the changed path. Never mutates (so frozen / shared / cached objects are safe).
 */
function rewrite(v: unknown, replace: ReadonlyMap<Row, Row>): unknown {
  let nodes = 0
  const go = (x: unknown, depth: number): unknown => {
    if (!x || typeof x !== 'object' || isOpaqueBinary(x)) return x
    if (depth > WALK_MAX_DEPTH || nodes >= WALK_MAX_NODES) return x
    nodes++
    if (Array.isArray(x)) {
      let copy: unknown[] | null = null
      for (let i = 0; i < x.length; i++) {
        const nv = go(x[i], depth + 1)
        if (nv !== x[i]) { copy ??= x.slice(); copy[i] = nv }
      }
      return copy ?? x
    }
    const o = x as Row
    const replacement = replace.get(o)
    const keys = Object.keys(o)
    if (keys.length > WALK_MAX_KEYS_PER_OBJECT) return replacement ?? x
    let copy: Row | null = replacement ? { ...replacement } : null
    for (const k of keys) {
      const nv = go(o[k], depth + 1)
      if (nv !== o[k]) { copy ??= { ...o }; copy[k] = nv }
    }
    return copy ?? x
  }
  return go(v, 0)
}

/**
 * Post-process a capability result: if ANY ayurdaya year row/signal is reachable inside it and the
 * result does not already carry the disclosure (get_ayurdaya / chart_facts_query / query_signals set
 * their own), annotate COPIES of those rows with their own figure_kind/reductions_applied (never
 * mutating the handler's — possibly cached or frozen — objects), prepend the nested disclosure to
 * content, and add the closed-vocabulary flag at BOTH `content.judgment_flags` (what MCP-bridged tools
 * read) and `result.judgment_flags`.
 *
 * - Rows that already carry `figure_kind` (a composed/inner tool tagged them) are never recomputed or
 *   overwritten; they are counted from their existing value.
 * - It never throws. If the row rewrite fails, the page-level disclosure + flag are still attached
 *   (they cannot throw) and a warning is logged once. A walk-bound hit is warned too.
 * - A result with no ayurdaya figure is returned by reference unchanged.
 */
export function postProcessAyurdayaDisclosure<T>(result: T): T {
  try {
    if (!result || typeof result !== 'object') return result
    const r = result as unknown as { content?: unknown; is_error?: unknown; judgment_flags?: unknown }
    if (r.is_error === true) return result
    const content = r.content
    if (!content || typeof content !== 'object' || Array.isArray(content) || isOpaqueBinary(content)) return result
    const c = content as Row
    if (c['ayurdaya_figure_disclosure'] !== undefined || c['figure_kind'] !== undefined) return result

    const { rows, boundHit } = collectAyurdayaRows(c)
    if (boundHit) warnOnce(`result walk hit its bound (depth ${WALK_MAX_DEPTH} / ${WALK_MAX_NODES} objects / ${WALK_MAX_KEYS_PER_OBJECT} keys); ayurdaya rows beyond it, if any, were not disclosed`)
    if (rows.length === 0) return result

    // Per-row figures from the full row set (context for contribution/applicable_method rows), except
    // rows an inner tool already tagged: those keep their existing value and are never recomputed.
    const computed = classifyRows(rows, false)
    const finalFigures = new Map<Row, AyurdayaRowFigure>()
    const fresh = new Map<Row, Row>()
    for (const row of rows) {
      const existing = row['figure_kind']
      if (typeof existing === 'string') {
        finalFigures.set(row, figureFor(existing === AYURDAYA_FIGURE_KIND_UNREDUCED_BASE))
        continue
      }
      const f = computed.get(row)
      if (!f) continue
      finalFigures.set(row, f)
      fresh.set(row, { ...row, figure_kind: f.figure_kind, reductions_applied: f.reductions_applied })
    }
    const disclosure = summarize(finalFigures)
    if (!disclosure) return result

    let body: unknown = c
    try {
      body = rewrite(c, fresh)
    } catch (err) {
      warnOnce(`row annotation failed (${err instanceof Error ? err.message : String(err)}); page-level disclosure attached without per-row tags`)
    }
    const bodyObj = (body && typeof body === 'object' && !Array.isArray(body) ? body : c) as Row
    const { judgment_flags: contentFlags, ...bodyRest } = bodyObj
    // content.judgment_flags is what MCP-bridged tools read; keep any non-array value untouched.
    const contentFlagsOut = contentFlags !== undefined && !Array.isArray(contentFlags)
      ? contentFlags
      : [...(Array.isArray(contentFlags) ? contentFlags : []), disclosure.judgment_flag]
    const priorResultFlags = Array.isArray(r.judgment_flags) ? r.judgment_flags : []
    return {
      ...(result as object),
      content: {
        ayurdaya_figure_disclosure: ayurdayaDisclosureObject(disclosure),
        judgment_flags: contentFlagsOut,
        ...bodyRest,
      },
      judgment_flags: [...priorResultFlags, disclosure.judgment_flag],
    } as T
  } catch (err) {
    warnOnce(`post-processor failed (${err instanceof Error ? err.message : String(err)}); result returned without ayurdaya disclosure`)
    return result
  }
}
