/**
 * response_budget.ts — shared MCP-channel response-size trimmer (R5.1 C1)
 * ==========================================================================
 * PROBLEM (R5.1 C1 brief): judgment_query / graha_portrait / pact_query serve full-detail
 * payloads sized for internal debugging (up to ~86KB) — practically unusable over a real
 * MCP channel (context-window / token-budget blowout on the client side).
 *
 * THIS FILE is the ONE shared, reusable clipping mechanism for that problem — not three
 * bespoke ad-hoc trims per tool. It is STRUCTURE-AWARE (shrinks specific named arrays
 * inside the response object) rather than a byte-level string truncation — a byte-level
 * truncation of serialized JSON (see platform/src/lib/retrieval/adapters/shared/
 * result_clipper.ts, a sibling utility for a different consumer: LLM-context trimming of
 * arbitrary tool-call text, not MCP JSON envelopes) would produce invalid/truncated JSON
 * mid-object — unacceptable for a structured MCP tool response.
 *
 * MECHANICS:
 *   - Caller declares, per tool, which sections of its own response shape are "trimmable"
 *     arrays (a get/set pair + a floor + a recovery pointer).
 *   - `applyResponseBudget` measures the serialized size; if under budget, returns the
 *     content UNCHANGED (trim_report: null) — most calls never pay this cost's userland
 *     effect at all.
 *   - If over budget, it shrinks the HEAVIEST section first (by measured serialized size),
 *     halving repeatedly down to each section's floor, re-measuring after each cut, until
 *     under budget or every section has been floored.
 *   - Every actual cut is recorded in a TrimReportEntry (path, original_count, kept_count,
 *     reason, recover_via) — attached to the envelope's additive `trim_report` field
 *     (platform/src/lib/retrieval/envelope.ts + its generated mirror here).
 *   - CRITICAL (brief invariant): trimming only ever shortens ARRAYS the response already
 *     computed — it never deletes/invents data, never touches scalar verdict/receipt/
 *     pact_status fields, and the full detail remains reachable server-side via the
 *     `recover_via` instrument + explicit params (e.g. `max_signals`, `include`,
 *     `response_format:'legacy'`) — this file only governs what is DEFAULT-served.
 */
import { judgmentFlag, type JudgmentFlagEntry } from '../generated/envelope.js'

export interface TrimReportEntry {
  path: string
  original_count: number
  kept_count: number
  reason: string
  recover_via: { instrument: string; hint: string }
}

/**
 * C8 §4 — immune honesty-field set (FROZEN, contract C8
 * `~/elev-v2-shared/contracts/C8_REGISTRY_HANDLER_ENVELOPE_v1_0.md`). When any of these
 * fields is present on a response envelope it MUST survive ANY budget_kb (C1) / static-
 * ceiling trim untouched: never declared a trimmable section (so PASS 1/2 can't zero it),
 * never string-truncated by the last-resort walk. A trimmer that can zero the very fields
 * disclosing that trimming happened (or that a result is an honest empty) defeats
 * transparent trimming — this is the scalar-field analogue of the `hardFloor` array-section
 * protection (§N.6). The first eight entries are the FROZEN C8 minimum; the remainder are a
 * spirit-consistent extension for honesty fields that genuinely occur elsewhere in this
 * estate (completeness receipts, epistemic/coverage stamps, reading contracts). Matched by
 * KEY NAME at any nesting depth. */
export const IMMUNE_HONESTY_FIELDS: ReadonlySet<string> = new Set<string>([
  // — FROZEN C8 §4 minimum —
  'judgment_flags',
  'empty_reason',
  'catalog_only_rows_in_page',
  'catalog_only_note',
  'receipt_state',
  'budget_kb_applied',
  'budget_kb_requested',
  'trim_report',
  // — spirit-consistent extension (real fields elsewhere in the estate) —
  'completeness',
  'epistemic',
  'coverage',
  'reading_contract',
  // — SATYA-ŚEṢA W7 (flagship substance-inline, W7.4): the composed digest itself and its
  // completeness receipt are the densest, most-actionable layer of an assess_wealth/
  // assess_career response — under §N.6.2 they are the LAST thing trimmable, not the first.
  // A generic biggest-section-first trim would otherwise zero `reading` the instant it
  // becomes genuinely populated (the exact D-1.5a-class regression CLAUDE.md §N.6.2
  // documents for judgment_query's bearing_yogas). Immunity here means these keys are never
  // even declared as an auto-detected trimmable array/string site (see
  // autoDetectTrimmableSections and truncateLongStringsInPlace below) — stronger than
  // hardFloor, not weaker: the worst-case trimmed response still carries the full digest.
  'reading',
  'domain_completeness',
  'completeness_directive',
  'coverage_map',
])

/** A single trimmable section of a tool's response content. */
export interface TrimmableSection<T> {
  /** Dot-path label used in the trim_report (does not need to be a real JS path — just a
   *  stable, human-readable pointer into the content shape). */
  path: string
  /** Read the current array at this section (undefined/non-array → section skipped). */
  getArray: (content: T) => unknown[] | undefined
  /** Replace the section with a shorter array (same shape/location as getArray). */
  setArray: (content: T, kept: unknown[]) => void
  /** Never cut below this many kept entries (0 allowed — fully droppable section). */
  minKeep: number
  /** How a caller recovers the full section. */
  recover: { instrument: string; hint: string }
  /** Human label used in the trim_report reason string. */
  label: string
  /** D-1.5a wave gate finding (live rebuild verification, 2026-07-15): PASS 2's hard-cap
   *  fallback floors EVERY declared section to 0, overriding minKeep, ranked biggest-
   *  current-size-first. A section that used to be reliably empty/tiny (e.g.
   *  judgment_query's bearing_yogas before its firings-authoritative fix landed) and is
   *  now genuinely populated becomes, simply by virtue of no longer being empty, the
   *  biggest remaining candidate — and gets silently zeroed by PASS 2, defeating the very
   *  fix that populated it. `hardFloor: true` exempts a section from PASS 2's override:
   *  its declared `minKeep` is respected even under the hard-cap fallback. Default
   *  (undefined/false) preserves existing behavior for every other caller/section —
   *  this is opt-in, not a change to PASS 2's general semantics. */
  hardFloor?: boolean
}

export interface BudgetResult<T> {
  content: T
  trim_report: TrimReportEntry[] | null
  trimmed: boolean
  approx_bytes_before: number
  approx_bytes_after: number
}

/** Serialized-size estimate (UTF-8 bytes of JSON.stringify) — same measure the MCP wire
 *  transport actually pays, not a character count. */
export function estimateBytes(value: unknown): number {
  try {
    const json = JSON.stringify(value)
    return json ? Buffer.byteLength(json, 'utf8') : 0
  } catch {
    return 0
  }
}

/** Cut one section's array down toward `floor`, re-measuring `content` after each halving
 *  step, stopping as soon as `content` is at/under `maxBytes` or `floor` is reached.
 *  Only called when `arr.length > floor` (caller's responsibility) — always applies at
 *  least one cut. Returns the count actually kept. */
function shrinkSectionTo<T>(
  content: T,
  section: TrimmableSection<T>,
  arr: unknown[],
  floor: number,
  maxBytes: number,
): number {
  let keepCount = arr.length
  while (estimateBytes(content) > maxBytes && keepCount > floor) {
    keepCount = Math.max(floor, Math.floor(keepCount / 2))
    section.setArray(content, arr.slice(0, keepCount))
  }
  return keepCount
}

/**
 * Shrink `content`'s declared trimmable sections until its serialized size is at or under
 * `maxKb` KB, or every section has been floored — whichever comes first. Mutates `content`
 * in place via each section's `setArray` (content is always a fresh, per-request object in
 * every call site this ships with — never a shared/cached reference) and also returns it.
 *
 * Sections are cut in DESCENDING order of their own current serialized size — the biggest
 * offender goes first, matching the "lean section summaries, not full detail" mandate
 * (small sections are left alone whenever the big ones alone can close the gap).
 *
 * HARD-CAP PASS (R5.1 C1 fix — a live independent verifier caught the original version of
 * this file silently returning `trimmed:true` on a response that was STILL over budget
 * after every declared section had been floored to its normal `minKeep`; "I floored
 * everything I know how to floor" is not the same claim as "this response is under
 * budget", and this file must never conflate the two). If PASS 1 (respecting each
 * section's declared `minKeep`) is not enough, PASS 2 re-applies the same declared
 * sections but floors every one of them all the way to 0 (overriding `minKeep` — a
 * documented, explicit degrade-further step, not a silent one: every section touched in
 * PASS 2 gets its own trim_report entry saying so). If content is STILL over budget after
 * PASS 2 — meaning the base, non-trimmable content alone exceeds the ceiling — this
 * function does NOT pretend otherwise: a final `(whole response)` trim_report entry
 * records the honest residual gap instead of a silent pass-through (W3-L5 budget
 * unification, GT-45: the former `still_over_budget` boolean on this return value was
 * dead output on every call path — nobody read it, `finalizeMcpBudget` below recomputes
 * its own over-budget check independently rather than reading it — so it was removed
 * rather than left "surfaced but unread"; the `(whole response)` trim_report entry is
 * the one real, already-consumed honesty signal for this condition).
 */
export function applyResponseBudget<T>(
  content: T,
  maxKb: number,
  sections: TrimmableSection<T>[],
): BudgetResult<T> {
  const before = estimateBytes(content)
  const maxBytes = maxKb * 1024
  if (before <= maxBytes) {
    return { content, trim_report: null, trimmed: false, approx_bytes_before: before, approx_bytes_after: before }
  }

  // ONE entry per path (R5.1 C1 fix — a live independent verifier caught the original
  // version pushing a SEPARATE trim_report entry per pass, with long per-entry prose;
  // for a section touched in both PASS 1 and PASS 2 that meant two verbose entries where
  // one honest one suffices, and the resulting trim_report array became a multi-KB
  // artifact in its own right — the exact "clip mechanism's own overhead blows the
  // budget it's enforcing" failure this rewrite closes). Keyed by path so PASS 2
  // UPDATES a section's PASS-1 entry rather than duplicating it; `original_count`
  // always reflects the TRUE pre-trim count (first write wins), `kept_count` always
  // reflects the latest state (last write wins).
  const trimReportByPath = new Map<string, TrimReportEntry>()
  const recordTrim = (section: TrimmableSection<T>, trueOriginal: number, kept: number, hardCap: boolean): void => {
    const existing = trimReportByPath.get(section.path)
    trimReportByPath.set(section.path, {
      path: section.path,
      original_count: existing?.original_count ?? trueOriginal,
      kept_count: kept,
      // Short by design — this array itself counts against the same byte budget it
      // enforces (R5.1 C1 fix); verbose per-entry prose is the mechanism this rewrite
      // removes. The shared mechanism/rationale lives in this file's module doc-comment,
      // not repeated per entry.
      reason: hardCap ? `${section.label}: floored to ${kept} (hard-cap)` : `${section.label}: trimmed to ${kept}`,
      recover_via: section.recover,
    })
  }

  const runPass = (floorOverride: 'declared' | 'zero'): void => {
    // Re-rank by CURRENT size on every pass invocation — cutting one section changes the
    // overall total but not other sections' sizes, so a single ranking-then-iterate pass
    // per floor tier is safe and avoids re-sorting after every micro-cut within a tier.
    const ranked = sections
      .map(section => ({ section, arr: section.getArray(content) }))
      .filter((x): x is { section: TrimmableSection<T>; arr: unknown[] } => Array.isArray(x.arr) && x.arr.length > 0)
      .map(x => ({ ...x, size: estimateBytes(x.arr) }))
      .sort((a, b) => b.size - a.size)

    for (const { section, arr } of ranked) {
      if (estimateBytes(content) <= maxBytes) break
      const floor = floorOverride === 'zero' && !section.hardFloor ? 0 : section.minKeep
      if (arr.length <= floor) continue // nothing left to cut at this tier for this section
      const kept = shrinkSectionTo(content, section, arr, floor, maxBytes)
      if (kept < arr.length) {
        recordTrim(section, arr.length, kept, floorOverride === 'zero')
      }
    }
  }

  // PASS 1 — respect each section's declared minKeep.
  runPass('declared')

  // PASS 2 (hard-cap fallback) — only runs if PASS 1 wasn't enough. Floors every declared
  // section to 0, overriding minKeep, and says so explicitly per section (merged into the
  // SAME per-path entry PASS 1 created, not a second entry — see recordTrim above).
  if (estimateBytes(content) > maxBytes) {
    runPass('zero')
  }

  const afterSections = estimateBytes(content)
  const stillOverBudgetAfterSections = afterSections > maxBytes
  if (stillOverBudgetAfterSections) {
    trimReportByPath.set('(whole response)', {
      path: '(whole response)',
      original_count: before,
      kept_count: afterSections,
      reason: `still ${afterSections}B after flooring every section to 0 (ceiling ${maxBytes}B) — base content exceeds budget`,
      recover_via: { instrument: 'response_format:legacy', hint: 'full untrimmed response' },
    })
  }

  const trimReport = trimReportByPath.size > 0 ? Array.from(trimReportByPath.values()) : null

  return {
    content,
    trim_report: trimReport,
    trimmed: trimReport !== null,
    approx_bytes_before: before,
    approx_bytes_after: afterSections,
  }
}

// ── finalizeMcpBudget — the whole-response, self-verifying entry point ────────

export type DrillPointerLike = { instrument: string; hint: string; [k: string]: unknown }

export interface FinalizeMcpBudgetOptions<T> {
  maxKb: number
  sections: TrimmableSection<T>[]
  /** Field on `content` holding the tool's semantic drill_pointers array (merged with
   *  each trim_report entry's `recover_via`, deduped). Default 'drill_pointers'. */
  drillPointersField?: string
  /** Field on `content` to append an honest over-budget note to if the hard cap below
   *  still can't close the gap. Default 'judgment_flags'. */
  judgmentFlagsField?: string
  /** C1 (budget_kb, contract C1): the caller-supplied `budget_kb` request param, if any.
   *  Echoed back verbatim as `budget_kb_requested` on a trimmed response. The nominal
   *  ceiling actually applied (`maxKb`) is always echoed as `budget_kb_applied` on a trimmed
   *  response regardless of this field. Both are members of the C8 §4 immune set. */
  budgetKbRequested?: number
}

/**
 * The self-verifying whole-response entry point (R5.1 C1 hard-cap fix).
 *
 * PROBLEM THIS CLOSES: the original version of this mechanism ran `applyResponseBudget`
 * against `content`, then had the CALLER attach the resulting `trim_report` +
 * merged `drill_pointers` to `content` AFTERWARD, un-measured. For a response that needed
 * many sections trimmed (i.e. exactly the responses this mechanism exists for), the
 * trim_report array's OWN serialized bytes could be several KB — enough on their own to
 * push a response that measured "under budget" pre-attachment back OVER budget once
 * attached. A live independent verifier caught exactly this (structuredContent measured
 * ~7KB heavier than the pre-attachment number for graha_portrait). This function closes
 * that gap by measuring the ACTUAL FINAL OBJECT — trim_report and merged drill_pointers
 * included — and degrading the trim_report itself (never the underlying data sections
 * again) if attaching it reopened the gap:
 *   1. Run applyResponseBudget as before (data-section trimming, PASS 1 + hard-cap PASS 2).
 *   2. Attach `trim_report` + merge `recover_via` pointers into `drill_pointers`.
 *   3. Re-measure the WHOLE content object. If still over `maxKb`, shrink trim_report
 *      itself — biggest entry first — same halving discipline as a data section, down to
 *      a single one-line summary entry, then (if that alone is still too much) to null.
 *   4. If the response is STILL over budget after trim_report is gone entirely (meaning
 *      the base content plus merged drill_pointers alone exceed the ceiling), that is
 *      recorded as an honest `judgment_flags` entry — cheap (one short string) — rather
 *      than silently shipped over budget.
 */
// Fixed safety margin subtracted from the nominal ceiling for BOTH the initial
// data-section trim and every post-attachment re-check below. Covers (a) the
// dualOutput-style `{type:'object', object: <content>}` wrapper a caller may add AFTER
// this function returns (this file has no way to see that wrapper, so it must leave
// room for it), and (b) general safety margin so a response doesn't land within a few
// bytes of the true ceiling (fragile against trivial future content growth). A live
// independent verifier's re-check is what surfaced both the wrapper-overhead gap and a
// then-remaining ~40-byte-from-the-edge case — 512B comfortably covers both.
const SAFETY_MARGIN_BYTES = 512

export function finalizeMcpBudget<T extends Record<string, unknown>>(
  content: T,
  opts: FinalizeMcpBudgetOptions<T>,
): T {
  const drillPointersField = opts.drillPointersField ?? 'drill_pointers'
  const judgmentFlagsField = opts.judgmentFlagsField ?? 'judgment_flags'
  const maxBytes = opts.maxKb * 1024 - SAFETY_MARGIN_BYTES
  const effectiveMaxKb = maxBytes / 1024

  const result = applyResponseBudget(content, effectiveMaxKb, opts.sections)
  if (!result.trimmed) return content

  const mutable = content as Record<string, unknown>
  // C1 (budget_kb) response fields — attached ONLY on a trimmed response (a response that
  // fit under budget short-circuits above and carries neither field). `budget_kb_applied` is
  // the nominal ceiling actually applied after any caller/verbosity clamping (opts.maxKb, NOT
  // the internal safety-margined target); `budget_kb_requested` echoes the caller's param iff
  // supplied. Both are in the C8 §4 immune set (never subsequently trimmed). Set BEFORE the
  // post-attachment re-measure below so their (tiny) bytes are counted in the degrade check.
  mutable['budget_kb_applied'] = opts.maxKb
  if (opts.budgetKbRequested !== undefined) mutable['budget_kb_requested'] = opts.budgetKbRequested
  const existingPointers = (mutable[drillPointersField] as DrillPointerLike[] | undefined) ?? []
  mutable['trim_report'] = result.trim_report
  mutable[drillPointersField] = mergeTrimPointersIntoPointers(existingPointers, result.trim_report)

  // Re-measure the WHOLE object now that trim_report + merged pointers are attached —
  // the step the original mechanism skipped.
  if (estimateBytes(content) > maxBytes) {
    let report = [...(result.trim_report ?? [])]
    // Drop the single largest-by-bytes entry at a time until under budget or only one
    // entry remains (never go to a fully-empty array here — see the null fallback below).
    while (report.length > 1 && estimateBytes(content) > maxBytes) {
      let worstIdx = 0
      let worstBytes = -1
      for (let i = 0; i < report.length; i++) {
        const b = estimateBytes(report[i])
        if (b > worstBytes) { worstBytes = b; worstIdx = i }
      }
      report.splice(worstIdx, 1)
      mutable['trim_report'] = report
    }
    if (estimateBytes(content) > maxBytes) {
      // Even a 1-entry trim_report doesn't fit — collapse to a minimal summary.
      mutable['trim_report'] = [{
        path: '(trim_report)',
        original_count: result.trim_report?.length ?? 0,
        kept_count: 1,
        reason: 'full trim_report omitted to fit budget',
        recover_via: { instrument: 'response_format:legacy', hint: 'full untrimmed response' },
      }]
    }
    if (estimateBytes(content) > maxBytes) {
      // Still over even with trim_report gone — the merged drill_pointers additions are
      // the next-cheapest thing to give up. Revert to the tool's own semantic pointers.
      mutable[drillPointersField] = existingPointers
    }
    if (estimateBytes(content) > maxBytes) {
      // Last resort: every declared array section is already at 0 and trim_report/
      // drill_pointers have already been given up — the remaining bytes are scalar
      // PROSE fields (e.g. a tool's own `note`/`reason` narrative strings) this
      // function was never told about by name. Rather than leave those unbounded,
      // truncate any long string found anywhere in `content` (bounded-depth walk,
      // never touches arrays/numbers/booleans/short strings) until under budget.
      truncateLongStringsInPlace(content, maxBytes)
    }
  }

  // The TRUE requirement (opts.maxKb, no safety margin) is what actually gets reported —
  // the internal SAFETY_MARGIN_BYTES is a deliberately-conservative working target for
  // this function's OWN trimming decisions, not the bar a caller's honesty flag should
  // be judged against. (Fixes a real messaging bug this file had: a response that fits
  // the true ceiling but not the margined internal target must not claim "still over
  // budget" — that's a false alarm, not honesty.)
  const trueCeilingBytes = opts.maxKb * 1024
  if (estimateBytes(content) > trueCeilingBytes) {
    const existingFlags = (mutable[judgmentFlagsField] as JudgmentFlagEntry[] | undefined) ?? []
    mutable[judgmentFlagsField] = [
      ...existingFlags,
      judgmentFlag('budget_exceeded_after_trim', `${opts.maxKb}kb budget still exceeded after full trim.`),
    ]
  }

  return content
}

/**
 * Bounded-depth walk that truncates any string value longer than `MAX_STRING_CHARS`
 * (appending an ellipsis marker) until `content`'s serialized size is at/under
 * `maxBytes` or every long string found has been shortened — whichever comes first.
 * Only touches string VALUES (never keys, never array/object structure) — the true
 * last-resort lever once every declared array section and the trim_report/drill_pointers
 * machinery have already given everything they can.
 */
const MAX_STRING_CHARS = 120
const MAX_WALK_DEPTH = 6

function truncateLongStringsInPlace(root: unknown, maxBytes: number): void {
  const longStringSites: { obj: Record<string, unknown> | unknown[]; key: string | number }[] = []
  const walk = (node: unknown, depth: number): void => {
    if (depth > MAX_WALK_DEPTH || node === null || typeof node !== 'object') return
    if (Array.isArray(node)) {
      node.forEach((v, i) => {
        if (typeof v === 'string' && v.length > MAX_STRING_CHARS) longStringSites.push({ obj: node, key: i })
        else walk(v, depth + 1)
      })
      return
    }
    for (const [k, v] of Object.entries(node as Record<string, unknown>)) {
      // C8 §4: an immune honesty field's string value (e.g. empty_reason, catalog_only_note,
      // a completeness receipt mark) is never truncated, and its subtree is never descended
      // into — these fields disclose that trimming happened / that a result is an honest
      // empty, so mangling them defeats transparent trimming. Shed rows elsewhere instead.
      if (IMMUNE_HONESTY_FIELDS.has(k)) continue
      if (typeof v === 'string' && v.length > MAX_STRING_CHARS) longStringSites.push({ obj: node as Record<string, unknown>, key: k })
      else walk(v, depth + 1)
    }
  }
  walk(root, 0)
  // Longest strings first — fewest truncations needed to close the gap.
  longStringSites.sort((a, b) => {
    const av = Array.isArray(a.obj) ? (a.obj[a.key as number] as string) : (a.obj[a.key as string] as string)
    const bv = Array.isArray(b.obj) ? (b.obj[b.key as number] as string) : (b.obj[b.key as string] as string)
    return bv.length - av.length
  })
  for (const site of longStringSites) {
    if (estimateBytes(root) <= maxBytes) break
    const current = Array.isArray(site.obj) ? (site.obj[site.key as number] as string) : (site.obj[site.key as string] as string)
    const truncated = current.slice(0, MAX_STRING_CHARS) + '…[truncated for budget]'
    if (Array.isArray(site.obj)) site.obj[site.key as number] = truncated
    else site.obj[site.key as string] = truncated
  }
}

// ── R6 3b-budgets (R-1/R-8) — generic auto-detected sections for proxy tools ──────
//
// PROBLEM: many MCP tools in this codebase are thin PROXIES (regAlias/globalAlias in
// register_p1_aliases.ts, callSidecarPath / callPlatformPrim calls) whose response shape
// is owned by a downstream handler (a registry capability, a Python sidecar route) this
// lane does not always control or have time to hand-declare TrimmableSections for one at a
// time. Rather than leave those un-budgeted (the R-1/R-8 defect class this run closes),
// this helper walks the response object, finds every array-valued field (top-level and one
// level of nesting — deep enough to catch the common `{content: {rows: [...]}}` /
// `{data: {anchors: [...]}}` shapes without a full recursive walk that could mis-target
// scalar-shaped tools), and declares each a genuinely trimmable section: dot-path label,
// same tool name + a `response_format:'legacy'`-style recovery hint (the honest answer for
// a proxy this lane doesn't own the pagination contract of), minKeep tuned to preserve a
// still-useful sample (10) rather than trimming a small array to nothing.
export function autoDetectTrimmableSections<T extends Record<string, unknown>>(
  content: T,
  toolName: string,
): TrimmableSection<T>[] {
  const sections: TrimmableSection<T>[] = []
  const seenPaths = new Set<string>()

  const declareIfArray = (path: string, getter: (c: T) => unknown[] | undefined, setter: (c: T, kept: unknown[]) => void) => {
    const arr = getter(content)
    if (!Array.isArray(arr) || arr.length <= 10 || seenPaths.has(path)) return
    seenPaths.add(path)
    sections.push({
      path,
      label: path,
      minKeep: 10,
      getArray: getter,
      setArray: setter,
      recover: {
        instrument: toolName,
        hint: `call ${toolName} again with a narrower filter/date_range, or a smaller top_k/limit, to reach the rest of "${path}"`,
      },
    })
  }

  for (const key of Object.keys(content)) {
    // C8 §4: never declare an immune honesty field (e.g. judgment_flags array) trimmable —
    // it must survive any budget_kb trim untouched. Skips the field AND (if it is an object)
    // its whole subtree from auto-detection.
    if (IMMUNE_HONESTY_FIELDS.has(key)) continue
    const topVal = (content as Record<string, unknown>)[key]
    if (Array.isArray(topVal)) {
      declareIfArray(
        key,
        (c) => { const v = (c as Record<string, unknown>)[key]; return Array.isArray(v) ? v : undefined },
        (c, kept) => { (c as Record<string, unknown>)[key] = kept },
      )
    } else if (topVal && typeof topVal === 'object' && !Array.isArray(topVal)) {
      for (const nestedKey of Object.keys(topVal as Record<string, unknown>)) {
        if (IMMUNE_HONESTY_FIELDS.has(nestedKey)) continue
        const nestedVal = (topVal as Record<string, unknown>)[nestedKey]
        if (Array.isArray(nestedVal)) {
          const path = `${key}.${nestedKey}`
          declareIfArray(
            path,
            (c) => {
              const outer = (c as Record<string, unknown>)[key]
              if (!outer || typeof outer !== 'object') return undefined
              const inner = (outer as Record<string, unknown>)[nestedKey]
              return Array.isArray(inner) ? inner : undefined
            },
            (c, kept) => {
              const outer = (c as Record<string, unknown>)[key]
              if (outer && typeof outer === 'object') (outer as Record<string, unknown>)[nestedKey] = kept
            },
          )
        }
      }
    }
  }

  return sections
}

/**
 * R6 3b-budgets (R-1/R-8) — apply the generic auto-detected budget to a RetrievalEnvelope-
 * shaped object (`{..., content: <the actual payload>, trim_report}`), IN PLACE.
 *
 * This is the single wiring point used by every `dualOutput()` in register_p1_ganita.ts /
 * register_p1_synthesis.ts / register_p1_aliases.ts — the shared envelope shape means one
 * function here covers every tool built on top of it (ganita_condition_get, kala_life_arc_get,
 * kala_projections_get, ganita_positions_get, mimamsa_lel_query, and the rest of the estate)
 * without hand-declaring per-tool TrimmableSections one at a time. A tool that already
 * declared its own explicit sections (e.g. bodha_signals_get) is unaffected — this only acts
 * on the `content` object, and re-running it after an explicit trim is a no-op if already
 * under budget (estimateBytes short-circuits).
 */
export function applyAutoBudgetToEnvelope(
  envelopeObj: Record<string, unknown>,
  toolName: string,
  maxKb = 40,
): void {
  const content = envelopeObj['content']
  if (!content || typeof content !== 'object' || Array.isArray(content)) return
  const sections = autoDetectTrimmableSections(content as Record<string, unknown>, toolName)
  if (sections.length === 0) return
  const result = applyResponseBudget(content as Record<string, unknown>, maxKb, sections)
  if (result.trim_report) {
    const existing = Array.isArray(envelopeObj['trim_report']) ? (envelopeObj['trim_report'] as TrimReportEntry[]) : []
    envelopeObj['trim_report'] = [...existing, ...result.trim_report]
  }
}

/**
 * W3-L5 (budget unification, R-2 item 5 / W-8) — the single call every previously-
 * unclamped MCP tool registration now makes before building its dual-output response.
 * Thin composition of the two generic mechanisms this file already ships
 * (`autoDetectTrimmableSections` + `finalizeMcpBudget`) — the exact pattern
 * register_p1_aliases.ts's `dualOutput` already used for its own tools; this just gives
 * every OTHER registration file (which had no budget wiring at all — the ~36-of-~115
 * unclamped surface, GT-48) the same one-line call instead of hand-rolling it per file.
 * A no-op (besides the cheap `estimateBytes` short-circuit) when `content` is already
 * under budget, so calling it unconditionally is safe.
 */
export function budgetMcpContent<T>(content: T, toolName: string, maxKb = 40): T {
  if (!content || typeof content !== 'object' || Array.isArray(content)) return content
  const obj = content as Record<string, unknown>
  const sections = autoDetectTrimmableSections(obj, toolName)
  if (sections.length === 0) return content
  return finalizeMcpBudget(obj, { maxKb, sections }) as unknown as T
}

// ── SATYA-ŚEṢA W3 — kala/gochara family budget-census extension ─────────────
// The two family members (`kala_windows_get`, `kala_bundle_get`) whose response-
// budget ceiling is a plain `maxKb` literal at their own call site rather than a
// per-file ledger constant like register_gochara_windows.ts's own
// `GOCHARA_RESPONSE_BUDGET_KB` (which covers the other three family members:
// gochara_activation_get/forecast_get/election_avoidance_get). Declared here
// (this file, not registry_bridge.ts) because platform-mcp/src/lib/
// response_budget.ts is this family's own budget-wiring home per the SATYA-ŚEṢA
// W2/W3 brief's file-ownership split. Source-text-parsed by platform/scripts/
// census/elev_gates/_tool_enumeration.ts alongside registry_bridge.ts's
// MCP_RESPONSE_BUDGET_KB and register_gochara_windows.ts's
// GOCHARA_RESPONSE_BUDGET_KB — together the full budget_census_gate ledger for
// this family. Keep in sync BY HAND with:
//   kala_windows_get → register_p1_aliases.ts's `dualOutput(data, 'kala_windows_get')`
//                       (dualOutput's own default `maxKb = 40` parameter, this file)
//   kala_bundle_get  → retrieval/kala_temporal.ts's `budgetMcpContent(result, TOOL_NAME)`
//                       (budgetMcpContent's own default `maxKb = 40` parameter, this file)
export const KALA_TEMPORAL_FAMILY_BUDGET_KB = {
  kala_windows_get: 40,
  kala_bundle_get: 40,
} as const

function mergeTrimPointersIntoPointers(
  pointers: DrillPointerLike[],
  trimReport: TrimReportEntry[] | null,
): DrillPointerLike[] {
  if (!trimReport || trimReport.length === 0) return pointers
  const seen = new Set(pointers.map(p => `${p.instrument}::${p.hint}`))
  const merged = [...pointers]
  for (const entry of trimReport) {
    const key = `${entry.recover_via.instrument}::${entry.recover_via.hint}`
    if (seen.has(key)) continue
    seen.add(key)
    merged.push({ instrument: entry.recover_via.instrument, hint: entry.recover_via.hint })
  }
  return merged
}
