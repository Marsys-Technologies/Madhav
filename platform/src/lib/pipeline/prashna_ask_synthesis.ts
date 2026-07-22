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
 * evidence — it does not hand the model a live tool-calling loop. This keeps
 * the whole request bounded by the existing cost caps (call-count counts
 * retrieval dispatches, not this call) and avoids re-implementing
 * `agentic_loop.ts`'s streaming/multi-turn machinery for a job-handle-polled
 * tool that doesn't need it. If the deterministic floor proves insufficient
 * in practice (the model routinely needs to call more tools than the floor
 * gathered), that's a real, separate future enhancement — not silently routed
 * around here.
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

function formatEvidenceBlock(evidence: SynthesisEvidenceItem[]): string {
  if (evidence.length === 0) return '(no evidence was gathered for this request)'
  return evidence
    .map(
      (e) =>
        `<evidence tool="${e.tool_name}">\n${JSON.stringify(e.bundle.results, null, 2)}\n</evidence>`,
    )
    .join('\n\n')
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

  const userMessage = [
    `<user_question>${input.question}</user_question>`,
    `Query class: ${input.queryClass}. Intent summary: ${input.queryIntentSummary}.`,
    '',
    'Gathered evidence:',
    formatEvidenceBlock(input.evidence),
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
