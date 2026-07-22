import 'server-only'

/**
 * prashna_ask_synthesis.ts — W6.2 fix-cycle.
 *
 * Live E2E on the deployed connector found that `prashna_ask` returned raw
 * evidence bundles (`outcome: 'plan'`, a `results` array of tool bundles) with
 * no synthesized verdict — while its own tool description, the retired W4
 * spike's name ("question -> engine -> synthesized answer"), and the master
 * brief's own "one loop, two doors" thesis (A-07: "Paripraśna and prashna_ask
 * are one architecture, raw-tools MCP is not") all promise a full,
 * acharya-grade reading. Native ruling (2026-07-22): this is a real
 * implementation gap, not a legitimate raw-evidence contract — this module
 * closes it.
 *
 * Design choice, stated explicitly: prashna_ask's engine loop is a
 * DETERMINISTIC pre-fetch (the floor/dispatch loop in
 * `platform/src/app/api/mcp/prashna_ask/route.ts` decides which tools to call
 * BEFORE synthesis, via the compiled floor + B.11/dasha guarantees — not the
 * model choosing tools live, unlike consult's `runAgenticLoop`). So this
 * synthesis stage is a SINGLE, non-agentic LLM call over the already-gathered
 * evidence — it does not hand the model a live tool-calling loop. This avoids
 * re-implementing `agentic_loop.ts`'s streaming/multi-turn machinery for a
 * job-handle-polled tool that doesn't need it. If the deterministic floor
 * proves insufficient in practice (the model routinely needs to call more
 * tools than the floor gathered), that's a real, separate future enhancement —
 * not silently routed around here.
 *
 * RC-07 (RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §Cluster 3): this call is a
 * real costed sub-call and is gated by the SAME `CostCapTracker` instance the
 * caller's tool-dispatch loop uses — the call site
 * (`platform/src/app/api/mcp/prashna_ask/route.ts`) checks
 * `tracker.checkAndRecordCall()` immediately before invoking `synthesizeReading`
 * and skips the call entirely (fail-honest degradation, never a hang) if
 * either the call-count or wall-clock cap is already breached. This module
 * itself stays cap-agnostic — it does not import or reference the tracker —
 * the gating lives entirely at the call site, consistent with cost_caps.ts
 * only ever being consulted by call sites, never by the work it wraps.
 *
 * Reuses the SAME acharya-grade system prompt + citation format consult uses
 * (`consumeSystemPromptV2` / `src/lib/claude/system-prompts.ts`) so the two
 * doors produce prose in the same voice — the whole point of "one brain,
 * second door." The base prompt's "call tools live" instruction is explicitly
 * overridden here (this call has no tools available) rather than silently
 * ignored, since a system prompt that says "call get_layer_document" to a
 * model with zero tools in its request would be a real prompt-contract bug,
 * not a stylistic detail.
 */

import { query } from '@/lib/db/client'
import { runAdapter } from '@/lib/adapters/run_adapter'
import type { QueryRequest } from '@/lib/adapters/types'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import { DEFAULT_STACK_ID } from '@/lib/models/registry'
import { consumeSystemPromptV2 } from '@/lib/synthesis/prompts/synthesis_prompt_v2'

export interface SynthesisEvidenceItem {
  tool_name: string
  bundle: { results: unknown[] }
}

export interface SynthesizeReadingInput {
  chartId: string
  question: string
  queryClass: string
  queryIntentSummary: string
  evidence: SynthesisEvidenceItem[]
  unresolvedTools: string[]
  emptyResultTools: string[]
  strippedLeakedCapabilities: string[]
  capTripped: string | null
  /** ISO "YYYY-MM-DD" — the same as_of_date used to resolve chart_header.current_maha_antar
   *  (W6.3 fix-cycle: this call has no live tools, so the model cannot look up "today" itself
   *  the way consult's agentic loop can — it must be told explicitly or it reasons from
   *  training-data recency, e.g. narrating a 2024 dasha window as "current" 1.5 years late,
   *  confirmed live on trace d08d823a). */
  nowContextDate: string
  /** chart_header.current_maha_antar (e.g. "Mercury MD / Saturn AD"), or null if unresolved. */
  currentMahaAntar: string | null
}

export interface SynthesizeReadingResult {
  reading: string | null
  model_id: string | null
  judgment_flags: string[]
}

/** Overrides the base acharya prompt's "call tools live" instruction — this
 *  call has no tools; evidence is already gathered and provided as context. */
const NO_LIVE_TOOLS_OVERRIDE = `

---
IMPORTANT — OVERRIDE OF THE ABOVE TOOL-CALLING INSTRUCTIONS FOR THIS REQUEST:
You do NOT have any tools available in this call. All chart evidence relevant
to this question has already been gathered and is provided below inside
<evidence> blocks, one per retrieval call that ran. Do not attempt to call
get_layer_document or any other tool — none exist in this context. Synthesize
your reading directly and only from the <evidence> provided.

If <evidence_gaps> lists any items, those specific floor items did not
resolve (unresolved tool name), returned zero rows (a genuine empty result,
not necessarily an error), or were withheld (NO-LEAKAGE policy). Do not
fabricate content to fill these gaps — acknowledge the gap honestly in your
reading if it is material to the question, exactly as you would disclose any
other genuine absence of data.`

function buildChartContext(chart: {
  id: string
  name: string
  birth_date: string
  birth_time: string
  birth_place: string
}) {
  return {
    id: chart.id,
    name: chart.name,
    birth_date: chart.birth_date,
    birth_time: chart.birth_time,
    birth_place: chart.birth_place,
  }
}

// RC-08 fix (RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md, 2026-07-22): the original
// (W6.2, commit 56d4a41f) flat MAX_EVIDENCE_ITEM_CHARS=8_000 was firing
// synthesis_evidence_truncated on ordinary deepdive readings, not just the
// pathological unfiltered-dump case it was built for. Root cause: this route's
// `tool.retrieve()` calls (platform/src/app/api/mcp/prashna_ask/route.ts) run
// in-process against the retrieval registry directly — they never pass through
// platform-mcp's `applyResponseBudget` / `finalizeMcpBudget` (response_budget.ts),
// which only wraps the MCP protocol boundary in the platform-mcp package. So a
// normal floor item's full, untrimmed result set lands here with NO upstream size
// control at all, and a flat per-item cap blind to how many tools the floor
// actually dispatched was both too tight for a lean floor (few tools, budget to
// spare) and non-adaptive for a wide one.
//
// Fix, per RETRIEVAL_STRATEGY_v1_0.md §3.5 (the distillation boundary):
//   1. The per-item budget is now PROPORTIONAL to the evidence set — a shared
//      TOTAL_EVIDENCE_BUDGET_CHARS ceiling divided across however many items
//      actually arrived (floored at MIN_EVIDENCE_ITEM_CHARS so a wide floor can't
//      starve every item to unreadability). A standard ≤10-umbrella-call deepdive
//      (§2 rule 6 target) gets several times the old flat 8,000-char cap per item.
//   2. When an item's results genuinely exceed its budget, trimming is ROW-LEVEL
//      and BEARING-AWARE (§3.5: "rank by bearing-on-the-question, not magnitude";
//      a "dissent quota" for contradictions/anomalies/low-confidence-high-impact
//      rows) — never a blind character slice through the middle of a serialized
//      JSON array, which is lossy in a way that silently favors whichever rows
//      happen to serialize first and can drop the single dissenting or
//      highest-significance row purely because of its position.
//   3. Trim is disclosed (kept/total row counts, whether a dissent row still
//      didn't fit) — never a silent drop (B.10).
const TOTAL_EVIDENCE_BUDGET_CHARS = 320_000
const MIN_EVIDENCE_ITEM_CHARS = 6_000
/** A row this uncertain about its own finding is exactly the "low-confidence-
 *  high-impact" class §3.5(b)'s dissent quota exists to protect: it must survive
 *  a trim ahead of higher-confidence-but-lower-significance filler, never be the
 *  first thing cut just because it sorted late in the tool's raw result order. */
const DISSENT_CONFIDENCE_THRESHOLD = 0.5
/** Added to a dissent row's rank score so it always outranks a non-dissent row —
 *  the quota is a real floor, not a soft tiebreaker. */
const DISSENT_RANK_BONUS = 1_000
/** Conservative estimate of a row's contribution to the enclosing array's own
 *  JSON punctuation/newlines/indentation beyond the row's own serialized size.
 *  Under-counting here only makes selection stop very slightly early — never
 *  over budget. */
const PER_ROW_OVERHEAD_CHARS = 40

/** Best-effort read of a row's bearing signal. `ToolBundleResult` (the shared
 *  retrieval type every registered tool's `results` conform to — see
 *  `@/lib/retrieval/shared_types`) already carries `significance` and
 *  `confidence`; this is read defensively since `SynthesisEvidenceItem.bundle`
 *  is deliberately typed as `unknown[]`, not every row is guaranteed to
 *  populate those optional fields. */
function readBearingHints(row: unknown): { significance: number; isDissent: boolean } {
  if (typeof row !== 'object' || row === null) return { significance: 0, isDissent: false }
  const r = row as Record<string, unknown>
  const significance = typeof r.significance === 'number' ? r.significance : 0
  const confidence = typeof r.confidence === 'number' ? r.confidence : undefined
  const isDissent = confidence !== undefined && confidence < DISSENT_CONFIDENCE_THRESHOLD
  return { significance, isDissent }
}

export interface RowSelectionResult {
  keptResults: unknown[]
  keptCount: number
  totalCount: number
  /** Dissent rows that STILL didn't fit even after the dissent bonus — should be
   *  0 in the common case; only nonzero in the degenerate case where dissent rows
   *  alone already exceed the item's budget. Disclosed honestly, never hidden. */
  droppedDissentCount: number
}

/**
 * Select which rows of a single evidence item's `results` array fit within
 * `budgetChars`, ranked by bearing (significance, with a dissent-quota bonus for
 * low-confidence rows) rather than by original array position — the §3.5 "rank
 * by bearing-on-the-question, not magnitude" rule made concrete for this prompt.
 * Kept rows are returned in their ORIGINAL relative order (readability), even
 * though selection itself is bearing-ranked.
 */
export function selectRowsWithinBudget(results: unknown[], budgetChars: number): RowSelectionResult {
  const scored = results.map((row, index) => {
    const { significance, isDissent } = readBearingHints(row)
    const serialized = JSON.stringify(row, null, 2) ?? 'null'
    return {
      index,
      size: serialized.length,
      score: significance + (isDissent ? DISSENT_RANK_BONUS : 0),
      isDissent,
    }
  })
  // Highest bearing first; index is a stable tiebreak for equal-score rows —
  // NOT a magnitude/position rule, just deterministic output among genuine ties.
  const ranked = [...scored].sort((a, b) => b.score - a.score || a.index - b.index)

  const keepIndices = new Set<number>()
  let used = 0
  for (const candidate of ranked) {
    const cost = candidate.size + PER_ROW_OVERHEAD_CHARS
    if (used + cost > budgetChars) continue // doesn't fit — a smaller lower-bearing row later in ranked order still might
    keepIndices.add(candidate.index)
    used += cost
  }

  const droppedDissentCount = scored.filter((c) => c.isDissent && !keepIndices.has(c.index)).length

  if (keepIndices.size === 0 && results.length > 0) {
    // Degenerate case: even the single highest-bearing row alone exceeds the
    // budget. Keep it anyway so the tool isn't silently zeroed out — its JSON
    // gets character-sliced by the caller as a last resort.
    keepIndices.add(ranked[0].index)
  }

  const keptResults = results.filter((_, i) => keepIndices.has(i))
  return { keptResults, keptCount: keptResults.length, totalCount: results.length, droppedDissentCount }
}

export function formatEvidenceBlock(evidence: SynthesisEvidenceItem[]): { block: string; truncatedTools: string[] } {
  if (evidence.length === 0) {
    return { block: '(no evidence was gathered for this request)', truncatedTools: [] }
  }
  const truncatedTools: string[] = []
  const perItemBudgetChars = Math.max(
    MIN_EVIDENCE_ITEM_CHARS,
    Math.floor(TOTAL_EVIDENCE_BUDGET_CHARS / evidence.length),
  )
  const block = evidence
    .map((e) => {
      const results = Array.isArray(e.bundle.results) ? e.bundle.results : []
      const fullSerialized = JSON.stringify(results, null, 2) ?? '[]'
      if (fullSerialized.length <= perItemBudgetChars) {
        return `<evidence tool="${e.tool_name}">\n${fullSerialized}\n</evidence>`
      }
      truncatedTools.push(e.tool_name)

      const selection = selectRowsWithinBudget(results, perItemBudgetChars)
      const keptSerialized = JSON.stringify(selection.keptResults, null, 2) ?? '[]'
      const rowsWereDropped = selection.keptCount < selection.totalCount

      // Degenerate fallback: even the selected (highest-bearing) row set's own
      // JSON still exceeds the budget (e.g. a single monolithic result blob, not
      // an array of many small rows) — character-slice as a last resort, same as
      // the pre-RC-08 behavior, but only ever applied to the highest-bearing
      // content already selected, never a blind cut across the raw array.
      const finalSerialized =
        keptSerialized.length <= perItemBudgetChars ? keptSerialized : keptSerialized.slice(0, perItemBudgetChars)

      const disclosure = rowsWereDropped
        ? `... [TRUNCATED — kept ${selection.keptCount} of ${selection.totalCount} rows, ranked by ` +
          `bearing-on-the-question (RETRIEVAL_STRATEGY §3.5); dissent/low-confidence-high-impact rows ` +
          `are protected first` +
          (selection.droppedDissentCount > 0
            ? `, though ${selection.droppedDissentCount} dissent row(s) still did not fit`
            : '') +
          ` — the reading should not claim exhaustive coverage of every row from this specific tool]`
        : `... [TRUNCATED — this tool's highest-bearing content alone exceeds the per-item budget and was ` +
          `character-truncated — the reading should not claim exhaustive coverage of this tool]`

      return `<evidence tool="${e.tool_name}" truncated="true">\n${finalSerialized}\n${disclosure}\n</evidence>`
    })
    .join('\n\n')
  return { block, truncatedTools }
}

/**
 * W6.3 fix-cycle (native-directed, live trace d08d823a): builds the explicit
 * "today is X, current period is Y" anchor. Without this the model has no way
 * to know the request's actual current date/dasha and reasons from whatever
 * date its training data biases it toward — confirmed live as a ~1.5-year-
 * stale MD/AD narration. Degrades honestly (never fabricates a period) when
 * `currentMahaAntar` is unresolved.
 */
function formatTemporalAnchor(input: SynthesizeReadingInput): string {
  const dashaLine = input.currentMahaAntar
    ? `The native's current Vimshottari dasha period, as of this date, is ${input.currentMahaAntar} — treat this as the CURRENT period, not upcoming or past.`
    : `The native's current Vimshottari dasha period could not be resolved for this request — do not state or imply a specific current Mahadasha/Antardasha; disclose the gap instead.`
  return (
    `Today's date is ${input.nowContextDate}. ${dashaLine} Reason about "current", ` +
    `"now", "upcoming", and "past" periods relative to THIS date and period only — ` +
    `do not rely on any other date you might otherwise assume.`
  )
}

function formatGapsBlock(input: SynthesizeReadingInput): string {
  const gaps: string[] = []
  for (const t of input.unresolvedTools) gaps.push(`${t}: unresolved tool name, never dispatched`)
  for (const t of input.emptyResultTools) gaps.push(`${t}: dispatched successfully, returned zero rows`)
  for (const t of input.strippedLeakedCapabilities) gaps.push(`${t}: withheld by NO-LEAKAGE policy`)
  if (input.capTripped) gaps.push(`request stopped early: ${input.capTripped} cap tripped, remaining floor items not attempted`)
  if (gaps.length === 0) return '(no gaps — all planned floor items resolved with data)'
  return gaps.map((g) => `- ${g}`).join('\n')
}

/**
 * Fetch the {id, name, birth_date, birth_time, birth_place} row this module
 * and `consumeSystemPromptV2`'s `ChartContext` both need. Same query
 * `/api/chat/consult/route.ts` already runs (`SELECT ... FROM charts WHERE
 * id=$1`) — not a new lookup pattern.
 */
async function fetchChartContextRow(chartId: string) {
  const result = await query<{ id: string; name: string; birth_date: string; birth_time: string; birth_place: string }>(
    'SELECT id, name, birth_date, birth_time, birth_place FROM charts WHERE id=$1',
    [chartId],
  )
  return result.rows[0] ?? null
}

/**
 * Run the single, non-agentic synthesis call. Never throws — a failure here
 * (DB lookup, model call, empty output) resolves to `{reading: null, ...}`
 * plus a `judgment_flags` entry naming the failure, so the caller can still
 * return the honest evidence bundle rather than a hard error on the whole
 * request; synthesis is presented as an addition to the grounded evidence,
 * not a replacement that can take the whole response down with it.
 */
export async function synthesizeReading(
  input: SynthesizeReadingInput,
): Promise<SynthesizeReadingResult> {
  const judgmentFlags: string[] = []

  let chartRow: Awaited<ReturnType<typeof fetchChartContextRow>>
  try {
    chartRow = await fetchChartContextRow(input.chartId)
  } catch (err) {
    console.error('[prashna_ask_synthesis] chart context lookup failed', err instanceof Error ? err.message : String(err))
    return { reading: null, model_id: null, judgment_flags: ['synthesis_skipped_chart_context_unresolved'] }
  }
  if (!chartRow) {
    return { reading: null, model_id: null, judgment_flags: ['synthesis_skipped_chart_context_unresolved'] }
  }

  const systemPrompt =
    consumeSystemPromptV2(buildChartContext(chartRow), [], 'acharya', false) + NO_LIVE_TOOLS_OVERRIDE

  const { block: evidenceBlock, truncatedTools } = formatEvidenceBlock(input.evidence)
  if (truncatedTools.length > 0) {
    judgmentFlags.push('synthesis_evidence_truncated')
  }

  const userMessage = [
    `<user_question>${input.question}</user_question>`,
    `<temporal_anchor>${formatTemporalAnchor(input)}</temporal_anchor>`,
    `Query class: ${input.queryClass}. Intent summary: ${input.queryIntentSummary}.`,
    '',
    'Gathered evidence:',
    evidenceBlock,
    '',
    '<evidence_gaps>',
    formatGapsBlock(input),
    '</evidence_gaps>',
  ].join('\n')

  let synthesisModelId: string
  try {
    synthesisModelId = await getEffectiveModel(DEFAULT_STACK_ID, 'synthesis', 'primary')
  } catch (err) {
    console.error('[prashna_ask_synthesis] model resolution failed', err instanceof Error ? err.message : String(err))
    return { reading: null, model_id: null, judgment_flags: ['synthesis_skipped_model_unresolved'] }
  }

  const req: QueryRequest = {
    callType: 'synthesis',
    modelOverride: { modelId: synthesisModelId },
    systemPrompt,
    messages: [{ role: 'user', content: userMessage }],
    traceId: input.chartId,
  }

  try {
    const interaction = await runAdapter(req)
    const reading = interaction.finalText?.trim()
    if (!reading) {
      judgmentFlags.push('synthesis_returned_empty')
      return { reading: null, model_id: synthesisModelId, judgment_flags: judgmentFlags }
    }
    return { reading, model_id: synthesisModelId, judgment_flags: judgmentFlags }
  } catch (err) {
    console.error('[prashna_ask_synthesis] synthesis call failed', err instanceof Error ? err.message : String(err))
    return { reading: null, model_id: synthesisModelId, judgment_flags: ['synthesis_call_failed'] }
  }
}
