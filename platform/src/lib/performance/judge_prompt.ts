/**
 * Gate I Performance — judge prompt v1.0.
 *
 * Brief: CLAUDECODE_BRIEF.md (GATE-I-PERF-CMD-001), W8a.
 *
 * The judge sees the original user query plus the planner's output, and
 * returns a structured verdict on whether the plan was appropriate. The
 * rubric is anchored to the project's planner-prompt requirements
 * (PLANNER_PROMPT v2.1+ — see CLAUDE.md / project_pipeline_gap_plan_complete).
 *
 * Output schema:
 *   { verdict: 'correct' | 'wrong' | 'ambiguous', reasoning: string }
 */

export const JUDGE_PROMPT_VERSION = '1.0'

export interface JudgeInput {
  query_text: string
  query_class: string | null
  plan_type: string | null
  tools_selected: string[]
  planner_confidence: number | null
}

export function buildJudgePrompt(input: JudgeInput): string {
  const tools = input.tools_selected.length > 0 ? input.tools_selected.join(', ') : '(none)'
  return `You are an evaluator scoring whether a Jyotish-system query planner picked the right plan.

ORIGINAL QUERY:
${input.query_text}

PLANNER OUTPUT:
- query_class: ${input.query_class ?? '(unset)'}
- plan_type:   ${input.plan_type ?? '(unset)'}
- tools_selected: ${tools}
- planner_confidence: ${input.planner_confidence ?? '(unset)'}

RUBRIC (anchored to PLANNER_PROMPT v2.1):
1. query_class must reflect the query's actual intent (factual / interpretive / predictive /
   cross_domain / discovery / holistic / remedial / cross_native).
2. plan_type must match the expected output shape — single_answer for direct factual asks,
   three_interpretation for interpretive, time_indexed_prediction for forward-looking with horizon,
   structured_data for tabular output.
3. tools_selected should include at least one L2.5 retrieval tool for any interpretive,
   holistic, or predictive query (msr_sql, query_msr_aggregate, pattern_register, cgm_graph_walk,
   resonance_register, cluster_atlas, contradiction_register).
4. For factual queries, vector_search alone is acceptable; L2.5 tools are not required.
5. Holistic queries must include broad L2.5 coverage (>=2 distinct L2.5 tools).

Return a single JSON object with exactly two keys: "verdict" (one of "correct", "wrong",
"ambiguous") and "reasoning" (1–2 sentences citing the rubric clause(s) that drove the verdict).
Do not include any text outside the JSON object.`
}

export interface JudgeVerdict {
  verdict: 'correct' | 'wrong' | 'ambiguous'
  reasoning: string
}

/**
 * Parse the LLM output into a JudgeVerdict. Returns null on parse failure;
 * the caller records an 'ambiguous' verdict with a 'judge_call_failed' note.
 */
export function parseJudgeResponse(raw: string): JudgeVerdict | null {
  if (!raw) return null
  // Try to extract a JSON object from the response, in case the LLM wrapped
  // it in prose or ```json fences.
  const match = raw.match(/\{[\s\S]*\}/)
  if (!match) return null
  try {
    const obj = JSON.parse(match[0]) as Partial<JudgeVerdict>
    if (obj.verdict !== 'correct' && obj.verdict !== 'wrong' && obj.verdict !== 'ambiguous') {
      return null
    }
    return {
      verdict: obj.verdict,
      reasoning: typeof obj.reasoning === 'string' ? obj.reasoning : '',
    }
  } catch {
    return null
  }
}
