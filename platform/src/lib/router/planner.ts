import 'server-only'

import crypto from 'crypto'
import { generateText } from 'ai'
import { z } from 'zod'

import { resolveModel } from '@/lib/models/resolver'
import { getWorkerForModel } from '@/lib/models/registry'
import { configService } from '@/lib/config/index'
import { telemetry } from '@/lib/telemetry/index'

import {
  RETRIEVAL_CAPABILITY_SPEC,
  renderRetrievalCapabilitySpec,
} from './retrieval_capability_spec'
import type {
  PlanContext,
  RichQueryPlan,
  ToolCallSpec,
} from './types'
import type {
  Bundle,
  BundleEntry,
  ManifestData,
} from '@/lib/bundle/types'

/**
 * planner.ts — BHISMA Stream 2 §4.2 + §4.3
 *
 * The unified planning step. Replaces classify + compose + plan_per_tool when
 * `LLM_FIRST_PLANNER_ENABLED=true`. The planning LLM receives the query, a
 * compact chart context, the full Retrieval Capability Spec, and the audience
 * tier; it emits a RichQueryPlan with per-tool parameter specs already
 * filled in.
 *
 * The worker model is resolved from the synthesis model's family per ADR-1
 * (anthropic→haiku-4-5, google→gemini-2.5-flash, openai→gpt-4o-mini,
 * deepseek→deepseek-chat). Failures are loud, not silent (ADR-3): a parsing
 * error after one retry throws a structured PlannerError.
 */

// ────────────────────────────────────────────────────────────────────────────
// Errors — loud, never silent (ADR-3)
// ────────────────────────────────────────────────────────────────────────────

export class PlannerError extends Error {
  readonly stage: 'llm_call' | 'parse' | 'schema_validate'
  readonly model_id: string
  readonly attempt: number
  readonly raw_response?: string

  constructor(message: string, opts: {
    stage: PlannerError['stage']
    model_id: string
    attempt: number
    raw_response?: string
    cause?: unknown
  }) {
    super(message, opts.cause ? { cause: opts.cause } : undefined)
    this.name = 'PlannerError'
    this.stage = opts.stage
    this.model_id = opts.model_id
    this.attempt = opts.attempt
    this.raw_response = opts.raw_response
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Output schema — what the planning LLM must emit (Zod-checked)
// ────────────────────────────────────────────────────────────────────────────

const QUERY_CLASSES = [
  'factual',
  'interpretive',
  'predictive',
  'cross_domain',
  'discovery',
  'holistic',
  'remedial',
  'cross_native',
] as const

const OUTPUT_SHAPES = [
  'single_answer',
  'three_interpretation',
  'time_indexed_prediction',
  'structured_data',
] as const

const PlannerOutputSchema = z.object({
  query_class: z.enum(QUERY_CLASSES),
  domains: z.array(z.string()).default([]),
  forward_looking: z.boolean(),
  history_mode: z.enum(['synthesized', 'research']),
  panel_mode: z.boolean(),
  expected_output_shape: z.enum(OUTPUT_SHAPES),
  graph_seed_hints: z.array(z.string()).optional(),
  query_intent_summary: z.string().min(1),
  planning_rationale: z.string().min(1),
  synthesis_guidance: z.string().min(1),
  tool_calls: z
    .array(
      z.object({
        tool_name: z.string().min(1),
        params: z.record(z.string(), z.unknown()).default({}),
        priority: z.union([z.literal(1), z.literal(2), z.literal(3)]),
        reason: z.string().min(1),
      }),
    )
    .min(1),
})

type PlannerOutput = z.infer<typeof PlannerOutputSchema>

// ────────────────────────────────────────────────────────────────────────────
// Public API
// ────────────────────────────────────────────────────────────────────────────

export interface PlannerConfig {
  /** Override the worker model resolved from synthesis_model_id. */
  model_id?: string
  /** Override the LLM temperature. Default 0.0 — planning is structured output. */
  temperature?: number
  /** Override the max output tokens. */
  max_tokens?: number
}

/**
 * Run the LLM-first planner over `context` and return a fully-populated
 * RichQueryPlan. Throws PlannerError on hard failure (ADR-3) — never returns
 * a silent fallback.
 */
export async function plan(
  context: PlanContext,
  config: PlannerConfig = {},
): Promise<RichQueryPlan> {
  const modelId =
    config.model_id ??
    configService.getValue<string>(
      'PLANNER_MODEL_OVERRIDE',
      getWorkerForModel(context.synthesis_model_id),
    )
  const temperature =
    config.temperature ?? configService.getValue<number>('PLANNER_TEMPERATURE', 0.0)
  const maxTokens =
    config.max_tokens ?? configService.getValue<number>('PLANNER_MAX_TOKENS', 2048)

  const systemPrompt = buildPlannerSystemPrompt()
  const userMessage = buildPlannerUserMessage(context)

  const start = Date.now()
  const parsed = await callPlanner({
    modelId,
    system: systemPrompt,
    user: userMessage,
    temperature,
    maxTokens,
  })
  const planning_latency_ms = Date.now() - start

  // Stitch caller-controlled and computed fields onto the LLM output.
  const tool_calls: ToolCallSpec[] = parsed.tool_calls.map((tc) => ({
    tool_name: tc.tool_name,
    params: tc.params,
    priority: tc.priority,
    reason: tc.reason,
  }))

  const richPlan: RichQueryPlan = {
    // QueryPlan core
    query_plan_id: crypto.randomUUID(),
    query_text: context.query,
    query_class: parsed.query_class,
    domains: parsed.domains,
    forward_looking: parsed.forward_looking,
    audience_tier: context.audience_tier,
    tools_authorized: tool_calls.map((tc) => tc.tool_name),
    history_mode: parsed.history_mode,
    panel_mode: parsed.panel_mode,
    expected_output_shape: parsed.expected_output_shape,
    manifest_fingerprint: context.manifest_fingerprint,
    schema_version: '1.0',
    graph_seed_hints: parsed.graph_seed_hints ?? [],
    router_confidence: 1.0,
    router_model_id: modelId,
    // Rich extensions
    query_intent_summary: parsed.query_intent_summary,
    planning_rationale: parsed.planning_rationale,
    synthesis_guidance: parsed.synthesis_guidance,
    tool_calls,
    planning_model_id: modelId,
    planning_latency_ms,
  }

  return richPlan
}

// ────────────────────────────────────────────────────────────────────────────
// LLM call with one retry on parse/schema failure
// ────────────────────────────────────────────────────────────────────────────

interface CallArgs {
  modelId: string
  system: string
  user: string
  temperature: number
  maxTokens: number
}

async function callPlanner(args: CallArgs): Promise<PlannerOutput> {
  const { modelId } = args
  const model = resolveModel(modelId)

  // Attempt 1
  let raw1 = ''
  try {
    const r = await generateText({
      model,
      system: args.system,
      messages: [{ role: 'user', content: args.user }],
      temperature: args.temperature,
      maxOutputTokens: args.maxTokens,
    })
    raw1 = r.text
    telemetry.recordCost(
      'planner',
      modelId,
      r.usage?.inputTokens ?? 0,
      r.usage?.outputTokens ?? 0,
      0,
    )
  } catch (err) {
    telemetry.recordError(
      'planner',
      'llm_call_attempt_1_failed',
      err instanceof Error ? err : new Error(String(err)),
    )
    throw new PlannerError('Planner LLM call failed (attempt 1)', {
      stage: 'llm_call',
      model_id: modelId,
      attempt: 1,
      cause: err,
    })
  }

  const parsed1 = tryParseAndValidate(raw1)
  if (parsed1.ok) return parsed1.value

  // Attempt 2 — strict retry with the parse error fed back
  const retryUser = [
    `Your previous response failed schema validation. Error: ${parsed1.error}`,
    '',
    'Output ONLY a raw JSON object with no prose, no markdown, no code fences.',
    'Start with { and end with }.',
    '',
    args.user,
  ].join('\n')

  let raw2 = ''
  try {
    const r = await generateText({
      model,
      system: args.system,
      messages: [{ role: 'user', content: retryUser }],
      temperature: 0.0, // force determinism on retry
      maxOutputTokens: args.maxTokens,
    })
    raw2 = r.text
    telemetry.recordCost(
      'planner',
      modelId,
      r.usage?.inputTokens ?? 0,
      r.usage?.outputTokens ?? 0,
      0,
    )
  } catch (err) {
    telemetry.recordError(
      'planner',
      'llm_call_attempt_2_failed',
      err instanceof Error ? err : new Error(String(err)),
    )
    throw new PlannerError('Planner LLM call failed (attempt 2 / retry)', {
      stage: 'llm_call',
      model_id: modelId,
      attempt: 2,
      raw_response: raw1,
      cause: err,
    })
  }

  const parsed2 = tryParseAndValidate(raw2)
  if (parsed2.ok) return parsed2.value

  // Both attempts failed — fail loud (ADR-3)
  telemetry.recordMetric('planner', 'hard_fail', 1, { model: modelId })
  throw new PlannerError(`Planner output failed schema after retry: ${parsed2.error}`, {
    stage: 'schema_validate',
    model_id: modelId,
    attempt: 2,
    raw_response: raw2,
  })
}

type ParseResult =
  | { ok: true; value: PlannerOutput }
  | { ok: false; error: string }

function tryParseAndValidate(rawText: string): ParseResult {
  const stripped = stripFences(rawText)
  let parsed: unknown
  try {
    parsed = JSON.parse(stripped)
  } catch (e) {
    return { ok: false, error: `JSON.parse failed: ${e instanceof Error ? e.message : String(e)}` }
  }
  const validation = PlannerOutputSchema.safeParse(parsed)
  if (!validation.success) {
    return { ok: false, error: validation.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join('; ') }
  }
  // Tool names must be a subset of the registered RCS tools.
  const known = new Set(RETRIEVAL_CAPABILITY_SPEC.map((e) => e.tool_name))
  const unknown = validation.data.tool_calls
    .map((tc) => tc.tool_name)
    .filter((n) => !known.has(n))
  if (unknown.length > 0) {
    return { ok: false, error: `Unknown tool_name(s): ${unknown.join(', ')}. Valid: ${[...known].join(', ')}` }
  }
  return { ok: true, value: validation.data }
}

function stripFences(raw: string): string {
  const trimmed = raw.trim()
  const fenceMatch = trimmed.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?```\s*$/)
  return fenceMatch ? fenceMatch[1].trim() : trimmed
}

// ────────────────────────────────────────────────────────────────────────────
// System prompt — §4.3
// ────────────────────────────────────────────────────────────────────────────

function buildPlannerSystemPrompt(): string {
  const rcs = renderRetrievalCapabilitySpec()
  return `You are the MARSYS-JIS Query Planner. Your job is to read a Jyotish query about a specific native and produce a single JSON plan that drives every downstream pipeline step.

You decide:
1. What the user actually wants (intent summary)
2. Which retrieval tools to call from the catalog below
3. Exactly what parameters to pass to each tool to get the highest-quality, most-relevant data
4. What guidance to give the synthesis LLM about angle, depth, and emphasis

Output ONLY raw JSON — no prose, no markdown, no code fences.

## Native context

The native's birth chart and the FORENSIC layer are always available to the synthesis step regardless of your tool selection — you do NOT need to schedule a tool call to retrieve them. The chart context (name, birth date/time/place, active dasha) is provided in the user message.

The current_date is provided in the user message; use it whenever you need to reason about temporal windows. Never invent a date; never assume "now" without using current_date.

## Retrieval tool catalog

There are 18 retrieval tools. Choose only those relevant to the query. Each tool's data surface, params, cost, and optimal usage patterns are below.

${rcs}

## Mandatory context (always available — do NOT schedule a tool call for these)

- FORENSIC chart data (the native's birth chart) — always pre-loaded into synthesis context.
- Chart name, birth date/time/place, active mahadasha — passed in the user message.

## Output format

Emit exactly one JSON object. Start with \`{\` and end with \`}\`. No fences, no prose.

\`\`\`
{
  "query_class": "factual" | "interpretive" | "predictive" | "cross_domain" | "discovery" | "holistic" | "remedial" | "cross_native",
  "domains": ["career", ...],            // empty array allowed
  "forward_looking": boolean,
  "history_mode": "synthesized" | "research",
  "panel_mode": boolean,                  // true ONLY for holistic
  "expected_output_shape": "single_answer" | "three_interpretation" | "time_indexed_prediction" | "structured_data",
  "graph_seed_hints": ["PLN.SATURN", "HSE.10", ...],   // optional; CGM node IDs for cgm_graph_walk seeds

  "query_intent_summary": "One-sentence summary of what the user actually wants.",
  "planning_rationale": "1–3 sentences: why these tools, in this priority, with these params.",
  "synthesis_guidance": "Instruction to the synthesis LLM: angle, depth, emphasis, what to lead with. 2–4 sentences.",

  "tool_calls": [
    {
      "tool_name": "msr_sql",
      "params": { "domains": ["career"], "min_significance": 0.7, "limit": 25 },
      "priority": 1,                       // 1 = critical, 2 = important, 3 = supplementary
      "reason": "1 sentence explaining why this tool with these params."
    }
    // ... more tool_calls ...
  ]
}
\`\`\`

## Planning principles (read carefully)

1. **Intent first.** Restate what the user actually wants in one sentence before choosing tools. If the question is ambiguous, pick the most useful interpretation given the chart context — do not refuse.

2. **Tool selection follows intent.** Choose only the tools that contribute to answering THIS query. A predictive question does not need vector_search across L4 remedial; a factual lookup does not need cluster_atlas. Less is more, but never starve the synthesis step.

3. **Parameter specificity.** Pass concrete params, not generic ones. If the query names Saturn, set planets:["Saturn"]. If it names house 10, set houses:[10]. If it implies a domain, set domains:["career"]. Generic params waste retrieval budget.

4. **Priority is meaningful.** priority=1 = critical (drop these and the answer is wrong); priority=2 = important (helpful context); priority=3 = supplementary (nice-to-have, dropped first under token pressure). Most plans have 2–5 priority-1 calls; everything else is 2 or 3.

5. **synthesis_guidance is your handoff to the writer.** Tell the synthesis LLM what angle to take, what depth to go to, what to lead with, what NOT to focus on. Examples:
   - "Lead with the Mercury–Saturn dispositor chain; treat the dasha context as secondary framing."
   - "This is a calibration question — quote the BAV bindus directly and rank-order the planets; do NOT interpret beyond the numbers."
   - "Acharya audience — three-interpretation shape, name every cited signal_id, do not euphemise contradictions."

6. **Breadth vs specificity.** Holistic queries get many tools at moderate limits; precise factual queries get few tools at low limits. The token budget is real — over-fetching weakens synthesis quality.

7. **Always include FORENSIC mandatorily through synthesis.** You do NOT add it as a tool call (it is pre-loaded). Build your plan assuming the native's full birth chart is already in context.

## Field rules

- audience_tier and manifest_fingerprint are caller-controlled — they are NOT in your output. The caller stitches them in.
- query_plan_id, query_text, schema_version, planning_model_id, planning_latency_ms are filled by the caller — NOT in your output.
- forward_looking: true if and only if the query asks about future events or timing.
- panel_mode: true ONLY for holistic queries.
- history_mode: "research" for discovery and cross_native; "synthesized" for all others.
- expected_output_shape: factual→single_answer; predictive→time_indexed_prediction; discovery and cross_native→structured_data; everything else (interpretive, cross_domain, holistic, remedial)→three_interpretation.
- graph_seed_hints: extract every chart entity named in the query and map each to a valid CGM node ID. Prefixes: PLN.<PLANET>, HSE.<N>, SGN.<SIGN>, NAK.<NAKSHATRA>, YOG.<NAME>, KRK.C8.<KARAKA>, KRK.C7.<KARAKA>, SEN.<NAME>, DSH.MD.<PLANET>, DSH.AD.<PLANET>, DVS.<DIVISIONAL>.<ENT>, UCN.SEC.<PART>.<SUB>, KARAKA.<NAME>. If the query is generic, leave empty [].
- tool_calls.tool_name MUST be one of the 18 names in the catalog above. Spelling matters.

## Planning Principle 9 — cross_varga_dignity_query scheduling (added 2026-05-10, VARGA-ETL-FULL-S1-CPA)

Schedule \`cross_varga_dignity_query\` at priority-1 for any query that:
- Mentions cross-varga / multi-chart strength comparison ("how strong is X across charts",
  "navamsha comparison", "three-state dignity", "vargottama").
- Names a specific planet whose D1/D9/D10 dignity arc is asymmetric (Saturn — D1 exalted,
  D9 debilitated NBRY, D10 angular; Venus — D1 neutral, D9 debilitated NBRY).
- Is holistic (always include for cross-chart anchoring).
For domain-specific interpretive queries (career, marriage, etc.), include this tool
alongside \`divisional_query\` for the relevant varga so the synthesis layer has both the
single-chart placements AND the cross-walk.

## Few-shot examples

### Example 1 — factual

User query: "What sign is my Mercury placed in?"
Output:
{"query_class":"factual","domains":[],"forward_looking":false,"history_mode":"synthesized","panel_mode":false,"expected_output_shape":"single_answer","graph_seed_hints":["PLN.MERCURY"],"query_intent_summary":"Look up the rashi placement of natal Mercury.","planning_rationale":"Pure chart lookup — chart_facts_query is the primary path; vector_search over L1 facts as a safety net.","synthesis_guidance":"State the sign in one sentence. No interpretation unless the user follows up.","tool_calls":[{"tool_name":"chart_facts_query","params":{"category":"planet","planet":"Mercury","divisional_chart":"D1"},"priority":1,"reason":"D1 placement of Mercury is the answer."},{"tool_name":"vector_search","params":{"layer":"L1","doc_type":["l1_fact"],"top_k":6},"priority":2,"reason":"Backstop — covers the case where chart_facts_query misses the row."}]}

### Example 2 — interpretive

User query: "What does my chart say about my career prospects?"
Output:
{"query_class":"interpretive","domains":["career"],"forward_looking":false,"history_mode":"synthesized","panel_mode":false,"expected_output_shape":"three_interpretation","graph_seed_hints":["HSE.10","PLN.MERCURY","KRK.C8.AmK"],"query_intent_summary":"Interpret the natal chart's career signature, surfacing strongest signals and their resonances.","planning_rationale":"Career interpretation lives in MSR signals, supported by patterns and resonances. cgm_graph_walk anchors the interpretation in the 10th-house and Amatyakaraka neighbourhood. domain_report_query brings the L3 career synthesis.","synthesis_guidance":"Three-interpretation shape. Lead with the dominant career signature (cite signal_ids), follow with structural support (patterns/resonances), close with cross-domain caveats. Acharya tone if audience permits.","tool_calls":[{"tool_name":"msr_sql","params":{"domains":["career"],"min_significance":0.7,"limit":25},"priority":1,"reason":"Career-tagged signals at significance ≥0.7 are the spine of the interpretation."},{"tool_name":"pattern_register","params":{"domains":["career"],"min_strength":0.6},"priority":2,"reason":"Named yogas/patterns that organise the career story."},{"tool_name":"cgm_graph_walk","params":{"seeds":["HSE.10","PLN.MERCURY","KRK.C8.AmK"],"depth":2},"priority":2,"reason":"Surfaces dispositor chains and aspect web around the career axis."},{"tool_name":"resonance_register","params":{"theme":"career","min_strength":0.6},"priority":2,"reason":"Confluences that amplify single signals into a recognisable pattern."},{"tool_name":"domain_report_query","params":{"domains":["career"],"limit":6},"priority":2,"reason":"L3 career_dharma synthesis sections for narrative grounding."},{"tool_name":"vector_search","params":{"doc_type":["l1_fact","ucn_section","msr_signal","cdlm_cell"],"top_k":25},"priority":3,"reason":"Semantic backstop across L1 facts and synthesis layers."}]}

### Example 3 — predictive

User query: "When will I see a significant career change in the next two years?"
Output:
{"query_class":"predictive","domains":["career"],"forward_looking":true,"history_mode":"synthesized","panel_mode":false,"expected_output_shape":"time_indexed_prediction","graph_seed_hints":["DSH.MD.MERCURY","DSH.MD.KETU","HSE.10"],"query_intent_summary":"Identify the highest-probability career-change windows in the next 24 months and rank them by signal density.","planning_rationale":"Predictive timing requires temporal context. Mercury MD ends 2027-08-21; the next MD is Ketu MD. The 2-year window straddles both, plus AD/PD layers. msr_sql with dasha_activation filter gives the activated signals; resonance_register surfaces confluences in the same window.","synthesis_guidance":"Time-indexed prediction shape. State 1–3 candidate windows with date ranges and probability bands. Cite the dasha lord(s) activating each window. Be explicit about uncertainty — this is calibrated, not deterministic.","tool_calls":[{"tool_name":"temporal","params":{"time_window":{"start":"2026-05-01","end":"2028-05-01"},"dasha_context_required":true},"priority":1,"reason":"Dasha chain across the 2-year window is the spine of any prediction."},{"tool_name":"msr_sql","params":{"domains":["career"],"dasha_activation":["Mercury","Ketu"],"min_significance":0.65},"priority":1,"reason":"Career signals activated by either dasha lord during the window."},{"tool_name":"resonance_register","params":{"theme":"career_transition","min_strength":0.6},"priority":2,"reason":"Confluences that mark genuine inflection points vs noise."},{"tool_name":"timeline_query","params":{"dasha_name":"Ketu MD"},"priority":2,"reason":"Upcoming Ketu MD arc is the framing for any post-2027 prediction."}]}

### Example 4 — cross_domain

User query: "How do my career and marriage show up together in my chart — is there tension between them?"
Output:
{"query_class":"cross_domain","domains":["career","relationships"],"forward_looking":false,"history_mode":"synthesized","panel_mode":false,"expected_output_shape":"three_interpretation","graph_seed_hints":["HSE.7","HSE.10","PLN.VENUS","PLN.SATURN"],"query_intent_summary":"Surface where career and marriage axes interact, with explicit attention to tension points.","planning_rationale":"Cross-domain tension is precisely what contradiction_register is for. Pair with msr_sql on both domains, then walk the CGM between the 7th and 10th house anchors.","synthesis_guidance":"Three-interpretation. DO NOT euphemise contradictions — surface them. Lead with the dominant tension, follow with reinforcement signals, close with the structural pattern that makes both domains co-arise. Cite contradiction_ids and signal_ids.","tool_calls":[{"tool_name":"contradiction_register","params":{"domains":["career","relationships"],"min_severity":0.6},"priority":1,"reason":"The tension surface; this is the question."},{"tool_name":"msr_sql","params":{"domains":["career","relationships"],"min_significance":0.7,"limit":35},"priority":1,"reason":"Both domains' high-significance signals."},{"tool_name":"cgm_graph_walk","params":{"seeds":["HSE.7","HSE.10","PLN.VENUS","PLN.SATURN"],"depth":2},"priority":2,"reason":"Relational neighbourhood between the two house axes."},{"tool_name":"pattern_register","params":{"domains":["career","relationships"],"min_strength":0.6},"priority":2,"reason":"Patterns that bridge both axes."},{"tool_name":"vector_search","params":{"top_k":25},"priority":3,"reason":"Semantic backstop without filter — cross-domain needs breadth."}]}

### Example 5 — discovery

User query: "What unusual patterns or exceptional features does my chart show?"
Output:
{"query_class":"discovery","domains":[],"forward_looking":false,"history_mode":"research","panel_mode":false,"expected_output_shape":"structured_data","graph_seed_hints":[],"query_intent_summary":"Surface rare or otherwise-noteworthy patterns and clusters in this chart.","planning_rationale":"Discovery is the cluster_atlas's job, supported by the high-rarity slice of pattern_register. Resonances pick out unexpected confluences.","synthesis_guidance":"Structured-data shape. Tabulate the top patterns/clusters by rarity and significance. State each one's claim crisply; do NOT pad with interpretation. Acharya audience expects density.","tool_calls":[{"tool_name":"cluster_atlas","params":{"min_rarity":0.7,"limit":15},"priority":1,"reason":"The discovery layer's primary surface."},{"tool_name":"pattern_register","params":{"min_strength":0.7,"limit":20},"priority":1,"reason":"Named patterns above the strength threshold."},{"tool_name":"resonance_register","params":{"min_strength":0.75,"limit":10},"priority":2,"reason":"High-strength resonances that mark unexpected confluences."},{"tool_name":"msr_sql","params":{"min_significance":0.85,"limit":15},"priority":2,"reason":"Top-significance signals as anchor points."}]}

### Example 2c — interpretive with cross-varga focus

User query: "How does Saturn behave across my charts? Walk me through D1, D9, and D10."
Output:
{"query_class":"interpretive","domains":[],"forward_looking":false,"history_mode":"synthesized","panel_mode":false,"expected_output_shape":"three_interpretation","graph_seed_hints":["PLN.SATURN"],"query_intent_summary":"Surface Saturn's three-state dignity arc across D1 / D9 / D10 and interpret the cross-varga shift.","planning_rationale":"This is the canonical cross-varga dignity question. cross_varga_dignity_query is the §3.15 CSI ledger surface — pair with divisional_query for D9 + D10 specifics, and msr_sql for Saturn-tagged signals.","synthesis_guidance":"Three-interpretation. Open with the three-state arc (D1 exalted Libra → D9 debilitated Aries with NBRY → D10 angular Taurus). Cite CSI.SATURN, D9.SATURN, D10.SATURN. Frame Saturn as the primary deliverer per Ishta/Kashta §6.7.","tool_calls":[{"tool_name":"cross_varga_dignity_query","params":{"planets":["Saturn"]},"priority":1,"reason":"§3.15 CSI ledger — Saturn-only slice."},{"tool_name":"divisional_query","params":{"varga":"D9","planet":"Saturn"},"priority":1,"reason":"D9 Saturn placement + NBRY context."},{"tool_name":"divisional_query","params":{"varga":"D10","planet":"Saturn"},"priority":1,"reason":"D10 Saturn placement (angular Taurus)."},{"tool_name":"msr_sql","params":{"planets":["Saturn"],"min_significance":0.7,"limit":15},"priority":2,"reason":"Saturn-tagged signals for interpretive layer."}]}

### Example 6 — holistic

User query: "Give me a complete and comprehensive reading of my chart covering all major life areas."
Output:
{"query_class":"holistic","domains":["career","finance","relationships","health","spiritual","psychology"],"forward_looking":false,"history_mode":"synthesized","panel_mode":true,"expected_output_shape":"three_interpretation","graph_seed_hints":[],"query_intent_summary":"Produce a comprehensive read across all major life domains with explicit attention to the chart's organising spine.","planning_rationale":"Holistic needs breadth. MSR + patterns + resonances + clusters + contradictions + L3 reports across domains, plus the §3.15 CSI cross-varga dignity ledger as the cross-chart anchor. Token budget is tight — most calls are priority 2 with broad limits.","synthesis_guidance":"Panel-mode three-interpretation. Open with the chart's organising spine in 2–3 sentences (lean on the CSI cross-varga picture for the spine), then per-domain sections. Surface contradictions explicitly. Cite signal_ids throughout.","tool_calls":[{"tool_name":"msr_sql","params":{"min_significance":0.7,"limit":50},"priority":1,"reason":"High-significance signals across all domains."},{"tool_name":"pattern_register","params":{"min_strength":0.6,"limit":20},"priority":1,"reason":"Yogas that anchor the life-shape."},{"tool_name":"cross_varga_dignity_query","params":{},"priority":1,"reason":"§3.15 CSI ledger — full 9-planet cross-varga picture; the cross-chart anchor for the holistic spine."},{"tool_name":"resonance_register","params":{"min_strength":0.65,"limit":15},"priority":2,"reason":"Confluences that organise multiple signals."},{"tool_name":"cluster_atlas","params":{"min_rarity":0.6,"limit":10},"priority":2,"reason":"Recognisable life-shapes."},{"tool_name":"contradiction_register","params":{"min_severity":0.6,"limit":12},"priority":2,"reason":"Tensions are part of an honest holistic read."},{"tool_name":"domain_report_query","params":{"domains":["career","financial","relationships","health","spiritual","psychology"],"limit":12},"priority":2,"reason":"L3 syntheses for each major domain."},{"tool_name":"vector_search","params":{"top_k":40},"priority":3,"reason":"Breadth backstop."}]}

### Example 7 — remedial

User query: "What remedies should I do for my Saturn placement?"
Output:
{"query_class":"remedial","domains":[],"forward_looking":false,"history_mode":"synthesized","panel_mode":false,"expected_output_shape":"three_interpretation","graph_seed_hints":["PLN.SATURN"],"query_intent_summary":"Surface scripturally-grounded remedies for the native's Saturn placement.","planning_rationale":"remedial_codex_query is the primary; pattern_register confirms which Saturn condition we are addressing.","synthesis_guidance":"Three-interpretation. Lead with practice_type (gemstone, mantra, etc.) most relevant to the native's specific Saturn condition. Cite scripture per entry. Note contraindications honestly.","tool_calls":[{"tool_name":"remedial_codex_query","params":{"planet":"Saturn","limit":8},"priority":1,"reason":"Saturn-specific remedies, all practice types."},{"tool_name":"msr_sql","params":{"planets":["Saturn"],"min_significance":0.6,"limit":15},"priority":2,"reason":"What Saturn condition are we addressing?"},{"tool_name":"pattern_register","params":{"planets":["Saturn"],"min_strength":0.6},"priority":2,"reason":"Saturn yogas that may modulate which remedy applies."}]}

### Example 8 — cross_native

User query: "Across charts with similar Saturn placements, what patterns are common?"
Output:
{"query_class":"cross_native","domains":[],"forward_looking":false,"history_mode":"research","panel_mode":false,"expected_output_shape":"structured_data","graph_seed_hints":["PLN.SATURN"],"query_intent_summary":"Aggregate cross-chart patterns associated with comparable Saturn placements.","planning_rationale":"query_msr_aggregate is the cross-chart surface. cluster_atlas supplies the pattern vocabulary to look for.","synthesis_guidance":"Structured-data shape. Tabulate patterns by prevalence within the Saturn cohort. Acharya/research audience — quote raw counts, do not interpret beyond the data.","tool_calls":[{"tool_name":"query_msr_aggregate","params":{"planets":["Saturn"],"group_by":"house","limit":12},"priority":1,"reason":"Cross-chart Saturn-placement aggregation."},{"tool_name":"cluster_atlas","params":{"min_rarity":0.5,"limit":15},"priority":2,"reason":"Pattern vocabulary for comparison."},{"tool_name":"pattern_register","params":{"planets":["Saturn"],"min_strength":0.6,"limit":15},"priority":2,"reason":"Saturn-specific patterns to test for prevalence."}]}

End of examples. Output ONLY the JSON for the actual user query — no commentary, no fences.`
}

// ────────────────────────────────────────────────────────────────────────────
// User message — the dynamic per-query payload
// ────────────────────────────────────────────────────────────────────────────

function buildPlannerUserMessage(context: PlanContext): string {
  const lines: string[] = []

  lines.push('## Native context')
  lines.push(`Name: ${context.chart_context.name}`)
  lines.push(`Birth date: ${context.chart_context.birth_date}`)
  lines.push(`Birth time: ${context.chart_context.birth_time}`)
  lines.push(`Birth place: ${context.chart_context.birth_place}`)
  if (context.chart_context.active_dasha) {
    lines.push(`Active mahadasha: ${context.chart_context.active_dasha}`)
  }
  lines.push('')

  lines.push('## Current date')
  lines.push(context.current_date)
  lines.push('')

  lines.push('## Audience tier')
  lines.push(context.audience_tier)
  lines.push('')

  if (context.conversation_history.length > 0) {
    const recent = context.conversation_history.slice(-3)
    lines.push('## Recent conversation (last 3 turns)')
    for (const turn of recent) {
      lines.push(`${turn.role.toUpperCase()}: ${turn.content}`)
    }
    lines.push('')
  }

  lines.push('## Query to plan')
  lines.push(context.query)

  return lines.join('\n')
}

// ────────────────────────────────────────────────────────────────────────────
// Bundle builder — §4.4 retires rule_composer when planner is on
//
// In the new path, the bundle is just the always-required floor (FORENSIC plus
// any other always_required entries in the manifest). The planner's tool_calls
// supply the rest of the synthesis context via retrieval, so a thick bundle is
// no longer needed. Token-budget priority is enforced via tool_calls priority.
// ────────────────────────────────────────────────────────────────────────────

export function buildPlannerFloorBundle(
  plan: RichQueryPlan,
  manifest: ManifestData,
): Bundle {
  const floor = manifest.entries.filter((e) => e.always_required === true)

  const entries: BundleEntry[] = floor.map((asset) => ({
    canonical_id: asset.canonical_id,
    version: asset.version ?? '1.0',
    content_hash:
      'sha256:' + crypto.createHash('sha256').update(asset.canonical_id).digest('hex'),
    token_count: asset.token_count ?? 0,
    role: 'floor',
    source: 'planner',
  }))

  const sortedIds = [...entries.map((e) => e.canonical_id)].sort()
  const bundle_hash =
    'sha256:' + crypto.createHash('sha256').update(sortedIds.join('\n')).digest('hex')

  return {
    bundle_id: crypto.randomUUID(),
    query_plan_reference: plan.query_plan_id,
    manifest_fingerprint: manifest.fingerprint,
    mandatory_context: entries,
    total_tokens: entries.reduce((s, e) => s + e.token_count, 0),
    bundle_hash,
    schema_version: '1.0',
  }
}
