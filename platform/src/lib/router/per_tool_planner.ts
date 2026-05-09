/**
 * per_tool_planner.ts — M2 Wave 6 D2: per-tool Haiku planning stage
 *
 * Takes a classified QueryPlan + list of authorized tools, fires a
 * Haiku call per tool in parallel, and returns a Map of tool-specific
 * QueryPlan overrides that narrow/refine the retrieval parameters.
 *
 * Feature-flag gated via PER_TOOL_PLANNER_ENABLED.
 * A/B-ready: trace step always emitted; planner_active=false when skipped.
 *
 * Wave 6 M2-D2. Parent: M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §D2.
 */
import 'server-only'

import { generateText } from 'ai'
import { resolveModel } from '@/lib/models/resolver'
import { TITLE_MODEL_ID } from '@/lib/models/registry'
import type { QueryPlan } from '@/lib/router/types'

// ── Output types ──────────────────────────────────────────────────────────────

/**
 * Partial QueryPlan overrides for a single tool.
 * Only the fields relevant to that tool are populated.
 * Extra retrieval hints (keyword, limit, etc.) are non-QueryPlan fields
 * merged into the effectivePlan at the call site via `as QueryPlan`.
 */
export type ToolPlanOverride = Partial<Pick<QueryPlan,
  | 'planets'
  | 'houses'
  | 'domains'
  | 'graph_seed_hints'
  | 'edge_type_filter'
  | 'graph_traversal_depth'
  | 'vector_search_filter'
  | 'dasha_context_required'
  | 'time_window'
  | 'sade_sati_query'
  | 'eclipse_query'
  | 'retrograde_query'
  | 'retrograde_planet'
>> & {
  keyword?: string
  limit?: number
  dasha_name?: string
  planet?: string
  practice_type?: string
  divisional_chart?: string
  category?: string
  fact_id_prefix?: string
}

export interface PerToolPlannerResult {
  overrides: Map<string, ToolPlanOverride>
  planner_active: boolean
  latency_ms: number
  tool_count: number
  error?: string
}

// ── Cost guard ────────────────────────────────────────────────────────────────

// Haiku pricing: ~$0.80/M input tokens, ~$4/M output tokens (as of 2026-04).
// Per call budget: 300 input + 150 output = ~$0.00024 + ~$0.0006 ≈ $0.00084.
// 17 tools × $0.00084 ≈ $0.014 — well within $0.05 ceiling.
// Guard fires if any single call exceeds these token limits.
const MAX_INPUT_TOKENS = 800
const MAX_OUTPUT_TOKENS = 400

// ── System prompt (shared across all tool calls) ──────────────────────────────

const PLANNER_SYSTEM_PROMPT = `You are a retrieval parameter optimizer for a Jyotish (Vedic astrology) query system.
Given a query plan and a specific retrieval tool, output a JSON object with narrowed parameters for that tool.
Output ONLY valid JSON. No prose, no markdown fences. If no refinement is needed, output {}.
The native is Abhisek Mohanty, born 1984-02-05, Aries Lagna, Sasha Yoga (Saturn exalted in 7H Libra).
Mercury is the chart's primary operational planet (Seven-System Convergence, MSR.413).
Current active MD: Mercury (ends 2027-08-21). Next MD: Ketu (2027-08-21 → 2034-08-21).`

// ── Per-tool user prompt templates ────────────────────────────────────────────

export const TOOL_PROMPT_TEMPLATES: Record<string, (plan: QueryPlan) => string> = {

  msr_sql: (plan) => `
Tool: msr_sql — queries the Master Signal Register (499 signals).
Query: "${plan.query_text}"
Query class: ${plan.query_class}
Planets mentioned: ${JSON.stringify(plan.planets ?? [])}
Houses mentioned: ${JSON.stringify(plan.houses ?? [])}

Output JSON with zero or more of:
- "planets": string[] — planet names to filter signals (e.g. ["Saturn", "Mercury"])
- "houses": number[] — house numbers (1-12) to filter
- "keyword": string — signal_name keyword
- "limit": number (default 15, max 30)
Example: {"planets":["Saturn"],"houses":[7,10],"limit":20}`,

  pattern_register: (plan) => `
Tool: pattern_register — queries pattern clusters (W3 expansion, 70+ patterns).
Query: "${plan.query_text}"
Domains: ${JSON.stringify(plan.domains)}

Output JSON with zero or more of:
- "keyword": string — pattern name keyword
- "domains": string[] — domain filter
- "limit": number (default 10)`,

  resonance_register: (plan) => `
Tool: resonance_register — queries resonance pairs (26 entries, cross-domain signal affinities).
Query: "${plan.query_text}"
Domains: ${JSON.stringify(plan.domains)}

Output JSON with zero or more of:
- "domains": string[] — filter by domain pair involvement
- "keyword": string
- "limit": number (default 10)`,

  cluster_atlas: (plan) => `
Tool: cluster_atlas — queries MSR signal clusters (semantic groupings).
Query: "${plan.query_text}"
Planets: ${JSON.stringify(plan.planets ?? [])}

Output JSON with zero or more of:
- "keyword": string — cluster theme keyword
- "planets": string[] — planet filter
- "limit": number (default 8)`,

  contradiction_register: (plan) => `
Tool: contradiction_register — queries contradictions (27 entries, cross-system conflicts).
Query: "${plan.query_text}"
Planets: ${JSON.stringify(plan.planets ?? [])}

Output JSON with zero or more of:
- "keyword": string
- "domains": string[]
- "limit": number (default 8)`,

  temporal: (plan) => `
Tool: temporal — queries dasha chain, sade sati, eclipses, retrograde stations.
Query: "${plan.query_text}"
Forward looking: ${plan.forward_looking}
Time window: ${JSON.stringify(plan.time_window ?? null)}

Output JSON with zero or more of:
- "dasha_context_required": boolean
- "sade_sati_query": boolean
- "eclipse_query": boolean
- "retrograde_query": boolean
- "retrograde_planet": string
- "time_window": {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"}
Note: next MD after Mercury is KETU (2027-08-21). Never output Saturn as upcoming MD.`,

  query_msr_aggregate: (plan) => `
Tool: query_msr_aggregate — returns aggregated MSR signal statistics by category/valence.
Query: "${plan.query_text}"
Query class: ${plan.query_class}

Output JSON with zero or more of:
- "planets": string[]
- "houses": number[]
- "limit": number (default 10)`,

  cgm_graph_walk: (plan) => `
Tool: cgm_graph_walk — walks the CGM (Chart Geometry Matrix) graph from seed nodes.
Query: "${plan.query_text}"
Planets: ${JSON.stringify(plan.planets ?? [])}
Houses: ${JSON.stringify(plan.houses ?? [])}
Graph hints: ${JSON.stringify(plan.graph_seed_hints ?? [])}

Output JSON with zero or more of:
- "graph_seed_hints": string[] — node IDs to start walk (e.g. ["PLN.SATURN","HSE.7"])
- "edge_type_filter": string[] — edge types to traverse
  (valid: GRAHA_ASPECT, BHAV_ASPECT, JAIMINI_ASPECT, OWNERSHIP, TENANCY,
   EXALT_DEBIL_AFFINITY, KARAKA_ROLE, YOGA_MEMBERSHIP, DASHA_ACTIVATION,
   DIVISIONAL_CONFIRMATION, COMBUST_WAR, KAKSHYA_ZONE, SAHAM_COMPOSITION)
- "graph_traversal_depth": number (1-3, default 2)`,

  manifest_query: (plan) => `
Tool: manifest_query — retrieves document manifest entries by canonical_id or path pattern.
Query: "${plan.query_text}"
Query class: ${plan.query_class}

Output JSON with zero or more of:
- "keyword": string — canonical_id or path substring to filter
- "limit": number (default 5)`,

  vector_search: (plan) => `
Tool: vector_search — semantic vector search over rag_chunks embeddings.
Query: "${plan.query_text}"
Domains: ${JSON.stringify(plan.domains)}
Vector filter: ${JSON.stringify(plan.vector_search_filter ?? {})}

Output JSON with zero or more of:
- "vector_search_filter": {"doc_type": string[], "layer": string}
  (valid doc_types: "forensic_section","msr_signal","ucn_paragraph","domain_report",
   "cgm_node","lel_event","pattern","cluster","resonance","contradiction",
   "l4_remedial","l5_timeline")
- "keyword": string — narrow the semantic query
- "limit": number (default 10)`,

  kp_query: (plan) => `
Tool: kp_query — queries KP (Krishnamurti Paddhati) cusp significators.
Query: "${plan.query_text}"
Houses: ${JSON.stringify(plan.houses ?? [])}
Planets: ${JSON.stringify(plan.planets ?? [])}

Output JSON with zero or more of:
- "houses": number[] — cusp house numbers to retrieve
- "planets": string[] — significator planet filter
- "limit": number (default 12)`,

  saham_query: (plan) => `
Tool: saham_query — queries Tajika Lots (36 sahams, Arabic parts).
Query: "${plan.query_text}"
Domains: ${JSON.stringify(plan.domains)}

Output JSON with zero or more of:
- "keyword": string — saham name keyword (e.g. "fortune", "spirit", "marriage")
- "domains": string[] — domain filter
- "limit": number (default 12)`,

  divisional_query: (plan) => `
Tool: divisional_query — queries divisional chart placements (D1, D9, D10, etc.).
Query: "${plan.query_text}"
Planets: ${JSON.stringify(plan.planets ?? [])}
Houses: ${JSON.stringify(plan.houses ?? [])}

Output JSON with zero or more of:
- "planets": string[] — planet filter
- "planet": string — single planet (alternative to array)
- "divisional_chart": string — e.g. "D9", "D10", "D1"
- "limit": number (default 20)`,

  cross_varga_dignity_query: (plan) => `
Tool: cross_varga_dignity_query — §3.15 CSI cross-divisional dignity ledger surface.
Returns per-planet D1 / D9 / D10 sign + dignity (exalted, debilitated, own_sign,
mooltrikona, neutral, shadow_node) and vargottama status.
Query: "${plan.query_text}"
Planets: ${JSON.stringify(plan.planets ?? [])}

Output JSON with zero or one of:
- "planets": string[] — canonical planet names: Sun, Moon, Mars, Mercury, Jupiter,
  Venus, Saturn, Rahu, Ketu. Omit (or pass empty array) for all 9 planets.`,

  chart_facts_query: (plan) => `
Tool: chart_facts_query — parametric query over chart_facts table (795 rows, §1–§27 coverage).
Query: "${plan.query_text}"
Planets: ${JSON.stringify(plan.planets ?? [])}
Houses: ${JSON.stringify(plan.houses ?? [])}

Output JSON with zero or more of:
- "category": string — e.g. "planet","house","yoga","dasha_vimshottari","shadbala","kp_cusp"
- "divisional_chart": string — e.g. "D1","D9","D10"
- "planets": string[] — filter by planet name in value_json
- "houses": number[] — filter by house number
- "fact_id_prefix": string — e.g. "PLN.","HSE.","YOG."
- "limit": number (default 20)`,

  domain_report_query: (plan) => `
Tool: domain_report_query — retrieves L3 domain report chunks (rag_chunks, doc_type=domain_report).
Query: "${plan.query_text}"
Domains: ${JSON.stringify(plan.domains)}

Output JSON with zero or more of:
- "domains": string[] — domain names
  (valid: career, dharma, children, financial, health, longevity, parents,
   psychology, mind, relationships, marriage, spiritual, travel)
- "keyword": string
- "limit": number (default 10, max 25)`,

  remedial_codex_query: (plan) => `
Tool: remedial_codex_query — retrieves L4 remedial prescriptions (doc_type=l4_remedial).
Query: "${plan.query_text}"
Planets: ${JSON.stringify(plan.planets ?? [])}

Output JSON with zero or more of:
- "planet": string — e.g. "Mercury", "Saturn", "Mars"
- "practice_type": string — one of: gemstone, mantra, yantra, devata, dinacharya, propit
- "keyword": string
- "limit": number (default 8, max 20)`,

  timeline_query: (plan) => `
Tool: timeline_query — retrieves L5 lifetime timeline arc chunks (doc_type=l5_timeline).
Query: "${plan.query_text}"
Forward looking: ${plan.forward_looking}
Time window: ${JSON.stringify(plan.time_window ?? null)}

Output JSON with zero or more of:
- "dasha_name": string — e.g. "Mercury MD", "Ketu MD", "Venus MD"
  IMPORTANT: Next MD after Mercury is KETU MD (2027-08-21). Never output Saturn MD as upcoming.
- "keyword": string
- "limit": number (default 8, max 15)`,
}

// ── Main export ───────────────────────────────────────────────────────────────

export async function planPerTool(
  queryPlan: QueryPlan,
  toolsAuthorized: string[],
): Promise<PerToolPlannerResult> {
  const start = Date.now()
  const overrides = new Map<string, ToolPlanOverride>()

  if (toolsAuthorized.length === 0) {
    return { overrides, planner_active: true, latency_ms: 0, tool_count: 0 }
  }

  const model = resolveModel(TITLE_MODEL_ID)

  const results = await Promise.allSettled(
    toolsAuthorized.map(async (toolName) => {
      const templateFn = TOOL_PROMPT_TEMPLATES[toolName]
      if (!templateFn) return

      const userPrompt = templateFn(queryPlan)

      const { text, usage } = await generateText({
        model,
        system: PLANNER_SYSTEM_PROMPT,
        prompt: userPrompt,
        maxOutputTokens: MAX_OUTPUT_TOKENS,
      })

      if ((usage?.inputTokens ?? 0) > MAX_INPUT_TOKENS) {
        console.warn(`[per_tool_planner] ${toolName}: input tokens ${usage?.inputTokens} > ${MAX_INPUT_TOKENS} — skipping override`)
        return
      }

      try {
        const parsed: ToolPlanOverride = JSON.parse(text.trim())
        if (typeof parsed === 'object' && parsed !== null && Object.keys(parsed).length > 0) {
          overrides.set(toolName, parsed)
        }
      } catch {
        // Malformed JSON from Haiku — skip this tool's override silently
      }
    })
  )

  results.forEach((r, i) => {
    if (r.status === 'rejected') {
      console.warn(`[per_tool_planner] ${toolsAuthorized[i]} failed:`, r.reason)
    }
  })

  return {
    overrides,
    planner_active: true,
    latency_ms: Date.now() - start,
    tool_count: toolsAuthorized.length,
  }
}
