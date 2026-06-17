---
brief_id: M2_D7_PER_TOOL_PLANNER
karn_session_name: KARN-W6-R2-PER-TOOL-PLANNER
wave: 6
stream: D
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 6 open
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (new TypeScript pipeline stage + 17 prompt templates + tests + deploy)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §D2
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: |
    KARN-W2-R1-MSR-ETL (A2), KARN-W2-R2-CHART-FACTS-ETL (A3),
    KARN-W4-R3-CHART-FACTS-QUERY (B3), KARN-W4-R1-A-MINOR (A5) — all COMPLETE.
    Sync 4 gate already satisfied per protocol §5 Wave 6 note.
  blocks: KARN-W7-R1-EVAL-HARNESS (eval harness measures classifier-only vs planner A/B)
parallel_stream_note: |
  Two other Wave-6 briefs run concurrently:
  - KARN-W6-R1-COMPOSITION-RULES (Stream D — modifies bundle/composition_rules.ts and
    bundle/types.ts only; zero overlap with this brief)
  - KARN-W6-R3-PROVENANCE-AUDIT (Stream F — read-only audit scripts; no code overlap)
  W6-R2 is the only brief that creates per_tool_planner.ts and modifies consume/route.ts.
  CRITICAL cross-stream note from W5 close: THREE separate QueryPlan interfaces exist at:
    1. platform/src/lib/router/types.ts  (the primary)
    2. platform/src/lib/retrieve/types.ts
    3. platform/src/lib/bundle/types.ts
  If W6-R2 adds any new QueryPlan field, ALL THREE files must be patched in the same commit.
  This brief adds no new QueryPlan fields (per_tool_planner reads existing fields only),
  so this is advisory only.
estimated_time: 3 days single Claude Code session

carry_forward_notes:
  - "Pipeline order in platform/src/app/api/chat/consume/route.ts (as of W5):
       Step 0: setup + auth
       Step 1: classify → queryPlan  (traceEmitter step 'classify')
       Step 2: compose → bundle      (traceEmitter step 'compose_bundle')
       Steps 3…N: retrieve parallel  (traceEmitter steps per tool name)
       Later: validate, synthesize, audit
     W6-R2 inserts a new stage between Step 2 (compose) and Steps 3…N (retrieve).
     The new stage: plan_per_tool → perToolParams (written to trace as step 'plan_per_tool').
     It does NOT block or replace retrieve — it enriches queryPlan or passes an override
     map that the retrieve calls use."
  - "The retrieve parallel block iterates queryPlan.tools_authorized. The per-tool planner
     produces a Map<tool_name → partial QueryPlan overrides>. The enriched params are merged
     into the queryPlan before the retrieve calls, OR passed alongside it as a separate
     perToolParams argument. Prefer the separate-argument approach to avoid mutating queryPlan
     and to keep A/B testing clean (feature-flag off → skip planner → use original queryPlan)."
  - "RETRIEVAL_TOOLS count is 17 (as of W5-R2 close):
       msr_sql, pattern_register, resonance_register, cluster_atlas, contradiction_register,
       temporal, query_msr_aggregate, cgm_graph_walk, manifest_query, vector_search,
       kp_query, saham_query, divisional_query, chart_facts_query,
       domain_report_query, remedial_codex_query, timeline_query.
     The per-tool planner covers all 17. Prompt templates must be authored for every tool."
  - "Feature flag: gated behind FEATURE_FLAG 'PER_TOOL_PLANNER_ENABLED' (new flag).
     When false → pipeline skips the plan_per_tool step entirely and uses original queryPlan.
     When true → plan_per_tool runs. Default: false for initial deploy; native flips to true
     after smoke verification. Add the flag to platform/src/lib/config/feature_flags.ts."
  - "A/B readiness: the trace step 'plan_per_tool' carries planner_active: true/false.
     W7-R1 eval harness uses this field to separate classifier-only vs planner query runs
     for comparative scoring. The trace step must always be emitted (even when flag=false),
     with planner_active: false and latency_ms: 0 when skipped."
  - "Haiku model: use the same Haiku model ID as used elsewhere in the codebase. Check
     platform/src/lib/models/registry.ts for the Haiku model constant. Do NOT hardcode
     a model string — reference the constant."
  - "Token budget per Haiku call: max 300 input tokens (system prompt + tool description +
     queryPlan excerpt) + max 150 output tokens (JSON param overrides). If any call exceeds
     $0.05 cost equivalent → halt. Use the cost guard in §3.5."
  - "Parallel Haiku calls: fire all tool planners in Promise.all() — same pattern as the
     existing retrieve parallel block. Total wall-clock target: ≤ 1s for all 17 calls."
  - "Vitest baseline: ~979 passing (W5 end-state). 13 pre-existing Jest failures are
     known-residuals and do not count as regressions."

scope_summary: |
  Create a new pipeline stage 'plan_per_tool' that runs between compose_bundle and
  the parallel retrieve block. The stage calls Haiku in parallel for each authorized
  tool, asking it to produce tool-specific parameter overrides given the query plan.
  Results enrich how each retrieval tool executes (e.g. a different limit, a more
  precise keyword, a targeted dasha_name). Stage is feature-flag gated.

  WORK:
  1. Create platform/src/lib/router/per_tool_planner.ts (new file)
     - planPerTool(queryPlan, tools_authorized, haiku) → Map<string, Partial<QueryPlan>>
     - 17 tool-specific prompt templates (one per tool)
     - Parallel Haiku calls with cost guard
     - Returns overrides map (empty map if feature flag off or error)
  2. Wire into platform/src/app/api/chat/consume/route.ts
     - Import planPerTool and the new feature flag
     - Insert call after compose step (Step 2), before retrieve parallel (Steps 3…N)
     - Emit trace step 'plan_per_tool' in all cases (planner_active: true/false)
     - Merge overrides into retrieve calls
  3. Add PER_TOOL_PLANNER_ENABLED flag to platform/src/lib/config/feature_flags.ts
  4. Tests: per_tool_planner.test.ts (≥12 tests)
  5. Deploy + smoke verify

may_touch:
  - platform/src/lib/router/per_tool_planner.ts               # CREATE
  - platform/src/lib/router/__tests__/per_tool_planner.test.ts # CREATE
  - platform/src/app/api/chat/consume/route.ts                 # MODIFY — wire new stage
  - platform/src/lib/config/feature_flags.ts                   # MODIFY — add flag
  - platform/src/lib/trace/types.ts                            # MODIFY — add plan_per_tool step type if needed
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_D7_PER_TOOL_PLANNER.md  # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_D7_VERIFICATION_<DATE>.txt               # CREATE

must_not_touch:
  - platform/src/lib/router/router.ts                          # classifier — do not modify
  - platform/src/lib/router/types.ts                           # QueryPlan type — no new fields needed
  - platform/src/lib/retrieve/**                               # retrieval tools — do not modify
  - platform/src/lib/bundle/**                                 # composition layer — W6-R1 territory
  - platform/src/lib/synthesis/**
  - platform/src/lib/audit/**
  - platform/migrations/**
  - platform/src/components/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 03_DOMAIN_REPORTS/**
---

# KARN-W6-R2-PER-TOOL-PLANNER — Execution Brief

## §0 — Context

This is an autonomous Claude Code session. Read this entire brief before writing any code.
Execute §1 (pre-flight) before touching anything. Halt immediately on any pre-flight failure.

**Parent plan:** `M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §D2`.

You are building the `plan_per_tool` pipeline stage. After the query classifier assigns
high-level parameters (query_class, domains, tools_authorized), and after the bundle
composer assembles the document context, this new stage asks Haiku to produce
tool-specific parameter refinements for each authorized retrieval tool. The refinements
override or narrow the default parameters before each tool executes.

This makes retrieval smarter: instead of every tool executing with the same coarse
query-plan parameters, each tool gets a micro-plan tailored to its own data shape.

The stage is feature-flag gated (default off). It is A/B-ready: the trace records
whether the planner was active so the W7 eval harness can compare outcomes.

---

## §1 — Pre-flight self-diagnostics

```bash
# PF.1 — Branch check
git branch --show-current
# Expected: redesign/r0-foundation. Any other → HALT.

# PF.2 — Working tree clean
git status --short
# Expected: clean or only files in may_touch list.

# PF.3 — Confirm per_tool_planner.ts does not yet exist
ls platform/src/lib/router/per_tool_planner.ts 2>/dev/null && echo "EXISTS — HALT" || echo "Not present — OK"
# Expected: "Not present — OK". If file exists → inspect, reconcile or continue if correct.

# PF.4 — Check Haiku model constant in registry
grep -n "haiku\|HAIKU\|claude-haiku" platform/src/lib/models/registry.ts | head -10
# Note the exact model ID constant name (e.g. HAIKU_MODEL_ID or similar).
# Use this constant in per_tool_planner.ts — do NOT hardcode a model string.

# PF.5 — Check feature_flags.ts current content
cat platform/src/lib/config/feature_flags.ts
# Note the pattern for adding a new flag (typically a string constant + getter function).
# PER_TOOL_PLANNER_ENABLED is the new flag name. Default value: false.

# PF.6 — Inspect consume/route.ts pipeline structure
grep -n "classify\|compose\|retrieve\|planPerTool\|plan_per_tool\|tools_authorized" \
  platform/src/app/api/chat/consume/route.ts | head -30
# Confirm: classify step exists, compose step exists, no plan_per_tool yet.
# Locate exact line numbers where the retrieve parallel block begins.

# PF.7 — Confirm RETRIEVAL_TOOLS count is 17
node -e "
const { RETRIEVAL_TOOLS } = require('./platform/src/lib/retrieve/index')
console.log('tools:', RETRIEVAL_TOOLS.map(t => t.name))
" 2>/dev/null || grep "\.tool," platform/src/lib/retrieve/index.ts | wc -l
# Expected: 17 tools.

# PF.8 — Check trace step types
grep -n "step_name\|step_type\|plan_per_tool\|StepType\|TraceStep" \
  platform/src/lib/trace/types.ts | head -20
# Note whether step_name is free-form string or a union type.
# If it's a union type that does NOT already include 'plan_per_tool', add it
# to platform/src/lib/trace/types.ts (within may_touch list).

# PF.9 — Vitest baseline
cd platform && npx vitest run --reporter=verbose 2>&1 | tail -10
# Record pass/fail counts.

# PF.10 — Cloud Run current revision
gcloud run revisions list --service=amjis-web --region=asia-south1 \
  --limit=3 --format="table(name,status.conditions[0].type)"
```

---

## §2 — per_tool_planner.ts — file structure

**Create `platform/src/lib/router/per_tool_planner.ts`:**

```typescript
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

import { generateText } from 'ai'
import { HAIKU_MODEL_ID } from '@/lib/models/registry'   // use the constant found in PF.4
import type { QueryPlan } from '@/lib/router/types'

// ── Output type ───────────────────────────────────────────────────────────────

/**
 * Partial QueryPlan overrides for a single tool.
 * Only the fields relevant to that tool are populated.
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
> & {
  keyword?: string       // free-form keyword passed to tools that accept it
  limit?: number         // override default fetch limit
  dasha_name?: string    // for timeline_query
  planet?: string        // for remedial_codex_query, divisional_query, etc.
  practice_type?: string // for remedial_codex_query
}>

export interface PerToolPlannerResult {
  overrides: Map<string, ToolPlanOverride>
  planner_active: boolean
  latency_ms: number
  tool_count: number
  error?: string
}

// ── Cost guard ────────────────────────────────────────────────────────────────

const MAX_COST_PER_QUERY_USD = 0.05
// Haiku pricing: ~$0.80/M input tokens, ~$4/M output tokens (as of 2026-04).
// Per call budget: 300 input + 150 output = ~$0.00024 + ~$0.0006 ≈ $0.00084 per call.
// 17 tools × $0.00084 ≈ $0.014 — well within $0.05 ceiling.
// Guard fires if any single call exceeds 800 input or 400 output tokens.
const MAX_INPUT_TOKENS = 800
const MAX_OUTPUT_TOKENS = 400
```

---

## §3 — Prompt templates (all 17 tools)

### §3.1 — System prompt (shared)

```typescript
const PLANNER_SYSTEM_PROMPT = `You are a retrieval parameter optimizer for a Jyotish (Vedic astrology) query system.
Given a query plan and a specific retrieval tool, output a JSON object with narrowed parameters for that tool.
Output ONLY valid JSON. No prose, no markdown fences. If no refinement is needed, output {}.
The native is Abhisek Mohanty, born 1984-02-05, Aries Lagna, Sasha Yoga (Saturn exalted in 7H Libra).
Mercury is the chart's primary operational planet (Seven-System Convergence, MSR.413).
Current active MD: Mercury (ends 2027-08-21). Next MD: Ketu (2027-08-21 → 2034-08-21).`
```

### §3.2 — Per-tool user prompt templates

Each template receives: `{ query_text, query_class, domains, forward_looking, planets, houses, time_window }` extracted from the query plan.

```typescript
const TOOL_PROMPT_TEMPLATES: Record<string, (plan: QueryPlan) => string> = {

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
```

---

## §4 — planPerTool function

```typescript
export async function planPerTool(
  queryPlan: QueryPlan,
  toolsAuthorized: string[],
): Promise<PerToolPlannerResult> {
  const start = Date.now()
  const overrides = new Map<string, ToolPlanOverride>()

  if (toolsAuthorized.length === 0) {
    return { overrides, planner_active: true, latency_ms: 0, tool_count: 0 }
  }

  const results = await Promise.allSettled(
    toolsAuthorized.map(async (toolName) => {
      const templateFn = TOOL_PROMPT_TEMPLATES[toolName]
      if (!templateFn) return // unknown tool — no override

      const userPrompt = templateFn(queryPlan)

      const { text, usage } = await generateText({
        model: HAIKU_MODEL_ID,   // use the constant from PF.4
        system: PLANNER_SYSTEM_PROMPT,
        prompt: userPrompt,
        maxTokens: MAX_OUTPUT_TOKENS,
      })

      // Cost guard — input token check
      if ((usage?.promptTokens ?? 0) > MAX_INPUT_TOKENS) {
        console.warn(`[per_tool_planner] ${toolName}: input tokens ${usage?.promptTokens} > ${MAX_INPUT_TOKENS} — skipping override`)
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

  // Log any rejections (network errors, model errors) without propagating
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
```

---

## §5 — Wire into consume/route.ts

### §5.1 — Add feature flag

In `platform/src/lib/config/feature_flags.ts`, add:

```typescript
// Per-tool Haiku planner stage (Wave 6 M2-D2). Default: false until smoke verified.
export const PER_TOOL_PLANNER_ENABLED = 'PER_TOOL_PLANNER_ENABLED'
```

Follow the exact pattern used for `NEW_QUERY_PIPELINE_ENABLED` or equivalent existing flag.
Default runtime value: `false` (opt-in).

### §5.2 — Import in consume/route.ts

Add import near the top of the file (after existing router imports):

```typescript
import { planPerTool } from '@/lib/router/per_tool_planner'
```

Also import the feature flag:
```typescript
// (add to existing configService usage block)
```

### §5.3 — Insert pipeline stage

Locate the compose step (Step 2) and the retrieve parallel block (Steps 3…N). Insert
between them:

```typescript
// --- Step 2b: plan_per_tool (Haiku per-tool parameter refinement) ---
const plannerStart = Date.now()
let perToolOverrides = new Map<string, Partial<typeof queryPlan>>()
const plannerEnabled = configService.getFlag('PER_TOOL_PLANNER_ENABLED')

if (plannerEnabled) {
  const plannerResult = await planPerTool(queryPlan, queryPlan.tools_authorized)
  perToolOverrides = plannerResult.overrides

  traceEmitter.emitStep({
    event: 'step_done',
    query_id: queryId,
    step: {
      query_id: queryId,
      conversation_id: finalConversationId,
      step_seq: /* compose step_seq + 1 */,   // determine correct seq from existing code
      step_name: 'plan_per_tool',
      step_type: 'plan',          // add 'plan' to TraceStep step_type union if needed
      status: 'done',
      started_at: new Date(plannerStart).toISOString(),
      completed_at: new Date().toISOString(),
      latency_ms: plannerResult.latency_ms,
      parallel_group: null,
      data_summary: {
        planner_active: true,
        tools_refined: perToolOverrides.size,
        tool_count: plannerResult.tool_count,
      },
      payload: {},
    },
  })
} else {
  // Always emit the step so A/B analysis can distinguish planner-off runs
  traceEmitter.emitStep({
    event: 'step_done',
    query_id: queryId,
    step: {
      query_id: queryId,
      conversation_id: finalConversationId,
      step_seq: /* compose step_seq + 1 */,
      step_name: 'plan_per_tool',
      step_type: 'plan',
      status: 'done',
      started_at: new Date(plannerStart).toISOString(),
      completed_at: new Date().toISOString(),
      latency_ms: 0,
      parallel_group: null,
      data_summary: { planner_active: false, tools_refined: 0, tool_count: 0 },
      payload: {},
    },
  })
}
```

### §5.4 — Merge overrides into retrieve calls

In the retrieve parallel block (`queryPlan.tools_authorized.map(async (toolName, idx) => ...)`),
access the merged plan when calling `executeWithCache`:

```typescript
// Build the effective query plan for this tool (merge overrides if present)
const toolOverride = perToolOverrides.get(toolName)
const effectivePlan: QueryPlan = toolOverride
  ? { ...queryPlan, ...toolOverride }
  : queryPlan

const result = await executeWithCache(t, effectivePlan, cache)
```

This preserves the original queryPlan (important for audit/trace correctness) while
passing refined parameters to the tool.

### §5.5 — step_seq renumbering

After inserting step 2b, the retrieve steps shift from 3…N to 4…N+1. Update the
`step_seq: 3 + idx` line in the retrieve parallel block to `step_seq: 4 + idx`.

**Also update the TraceStep step_type union if needed.** Check `platform/src/lib/trace/types.ts`:
if `step_type` is a union that does not include `'plan'`, add it. If it is a free-form
string, no change needed.

---

## §6 — Tests

**Create `platform/src/lib/router/__tests__/per_tool_planner.test.ts`:**

```typescript
/**
 * per_tool_planner.test.ts — Wave 6 M2-D2
 * Tests the per-tool planner in isolation, mocking Haiku calls.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { QueryPlan } from '@/lib/router/types'
```

Mock `generateText` to return controlled outputs:
```typescript
vi.mock('ai', () => ({
  generateText: vi.fn(),
}))
import { generateText } from 'ai'
```

Tests (≥ 12):

1. **Returns empty overrides for empty tools_authorized list** — `planPerTool(plan, [])` →
   `overrides.size === 0`, `tool_count === 0`, `planner_active === true`

2. **Returns an override for msr_sql when Haiku returns valid JSON** —
   mock `generateText` to return `'{"planets":["Saturn"],"houses":[7]}'` →
   `overrides.get('msr_sql')?.planets` equals `['Saturn']`

3. **Skips override when Haiku returns `{}`** — mock returns `'{}'` →
   `overrides.has('msr_sql')` is false

4. **Handles malformed JSON gracefully** — mock returns `'not json'` →
   no throw, `overrides.has('msr_sql')` is false

5. **Handles Haiku call rejection gracefully** — mock rejects →
   no throw, `overrides.has('tool')` is false, `planner_active === true`

6. **Skips unknown tool name** — pass `tools_authorized: ['nonexistent_tool']` →
   `overrides.size === 0`, no throw

7. **Processes multiple tools in parallel** — mock returns valid JSON for 3 tools →
   `overrides.size === 3`, all three keys present

8. **planner_active is true when any tools processed** — result has `planner_active: true`

9. **latency_ms is a non-negative number** — `result.latency_ms >= 0`

10. **template for temporal tool includes KETU note** — inspect `TOOL_PROMPT_TEMPLATES.temporal`
    call output; assert it contains 'KETU' string

11. **template for timeline_query includes KETU next MD note** — assert template output
    contains '2027-08-21' or 'Ketu MD'

12. **Override merge preserves original queryPlan immutability** — after merging with
    `{ ...queryPlan, ...override }` in consume/route.ts, original `queryPlan.planets`
    is unchanged. (Test this in a separate isolated scenario or as a structural assertion
    on the merge pattern.)

---

## §7 — Acceptance criteria

### AC.1 — Branch state
`git branch --show-current` returns `redesign/r0-foundation`.

### AC.2 — per_tool_planner.ts created
```bash
ls platform/src/lib/router/per_tool_planner.ts
```
File exists.

### AC.3 — 17 prompt templates present
```bash
grep -c "TOOL_PROMPT_TEMPLATES\[" platform/src/lib/router/per_tool_planner.ts || \
  grep -c "^  [a-z_]*: (plan)" platform/src/lib/router/per_tool_planner.ts
```
Shows 17 entries (one per retrieval tool).

### AC.4 — Feature flag added
```bash
grep "PER_TOOL_PLANNER_ENABLED" platform/src/lib/config/feature_flags.ts
```
Flag present with default value false.

### AC.5 — consume/route.ts wired
```bash
grep "planPerTool\|plan_per_tool\|perToolOverrides" platform/src/app/api/chat/consume/route.ts
```
Shows the import + call site + trace emission.

### AC.6 — Trace always emits plan_per_tool step
```bash
grep -c "plan_per_tool" platform/src/app/api/chat/consume/route.ts
```
≥ 2 occurrences (one for planner_active=true branch, one for planner_active=false).

### AC.7 — TypeScript compiles clean
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v node_modules | grep "error TS" | head -10
```
No new errors.

### AC.8 — Per-tool planner tests pass
```bash
cd platform && npx vitest run src/lib/router/__tests__/per_tool_planner.test.ts \
  --reporter=verbose 2>&1 | tail -20
```
≥ 12 tests pass. Zero failures.

### AC.9 — Full vitest suite: no new failures
```bash
cd platform && npx vitest run 2>&1 | tail -5
```
Pass count ≥ pre-flight baseline. 13 pre-existing Jest failures are expected residuals.

### AC.10 — Deploy: new Cloud Run revision
```bash
bash platform/scripts/cloud_build_submit.sh
gcloud run revisions list --service=amjis-web --region=asia-south1 \
  --limit=3 --format="table(name,status.conditions[0].type)"
```
New revision ACTIVE at 100%.

### AC.11 — Smoke: planner trace step appears with flag=false
After deploy, issue any Consume query with flag=false (default). In the trace (query_plans
table or trace SSE stream), confirm step_name='plan_per_tool' appears with
`data_summary.planner_active = false`. This proves the stage is wired even when skipped.

### AC.12 — A/B smoke: planner active with flag=true
Set `MARSYS_FLAG_PER_TOOL_PLANNER_ENABLED=true` locally (or via Cloud Run env override).
Issue one query. Confirm `data_summary.planner_active = true` and `tools_refined ≥ 1`
in the trace.

---

## §8 — Halt conditions

Halt immediately with a 5-line halt summary if:

1. **PF.1 fails:** Wrong branch.
2. **Haiku model constant not found in registry (PF.4):** Cannot safely reference the model.
   Do not hardcode. HALT and report exact grep output from PF.4.
3. **TypeScript errors in consume/route.ts after wiring** that cannot be resolved within
   the may_touch scope (e.g. a TraceStep type constraint that requires modifying a
   must_not_touch file). Report exact error lines.
4. **Latency in AC.12 smoke > 3s total for plan_per_tool step:** Investigate. If Haiku
   calls are serializing rather than running in parallel, that's a Promise.allSettled bug.
   Fix and re-smoke before claiming close.
5. **AC.9 regression: > 3 new vitest failures** vs pre-flight baseline.
6. **Cloud Build failure after 1 retry:** HALT with build log excerpt.

Non-halting: individual Haiku call timeouts (caught by Promise.allSettled error path);
tools without templates silently skipped; `{}` responses silently skipped.

---

## §9 — Closing summary template

```
SESSION CLOSE — M2_D7_PER_TOOL_PLANNER — <ISO timestamp>

Pre-flight findings:
  Haiku model constant: <name from PF.4>
  Feature flag pattern: <observed pattern from PF.5>
  RETRIEVAL_TOOLS count confirmed: <count from PF.7>
  Trace step_type union: <free-form string | union; 'plan' added: yes/no>
  Vitest baseline: <X passing / Y failing>

ACs result:
  AC.1:  <PASS|FAIL> — branch redesign/r0-foundation
  AC.2:  <PASS|FAIL> — per_tool_planner.ts created
  AC.3:  <PASS|FAIL> — 17 prompt templates present
  AC.4:  <PASS|FAIL> — PER_TOOL_PLANNER_ENABLED flag added (default false)
  AC.5:  <PASS|FAIL> — consume/route.ts wired (import + call + trace)
  AC.6:  <PASS|FAIL> — plan_per_tool step emitted in both flag=true and flag=false paths
  AC.7:  <PASS|FAIL> — TypeScript compiles clean
  AC.8:  <PASS|FAIL> — per-tool planner tests: ≥12 passing
  AC.9:  <PASS|FAIL> — no new vitest failures
  AC.10: <PASS|FAIL> — Cloud Run revision updated
  AC.11: <PASS|FAIL> — smoke: step appears with planner_active=false (flag off)
  AC.12: <PASS|FAIL> — A/B smoke: planner_active=true, tools_refined≥1 (flag on)

Files created/modified:
  platform/src/lib/router/per_tool_planner.ts               (CREATE)
  platform/src/lib/router/__tests__/per_tool_planner.test.ts (CREATE)
  platform/src/app/api/chat/consume/route.ts                 (MODIFY — stage wired)
  platform/src/lib/config/feature_flags.ts                   (MODIFY — flag added)
  platform/src/lib/trace/types.ts                            (MODIFY if needed — 'plan' step_type)

DB changes: none
Cloud Run: <prior revision> → <new revision>

Tests:
  Before: <X passed / Y failed>
  After:  <X' passed / Y' failed>
  Delta:  <new failures count>

Performance:
  plan_per_tool latency (flag=true, AC.12 smoke): <ms>
  tools_refined in smoke: <count>

Halt-and-report cases: <none | description>
Brief status: <COMPLETE | HALTED_AT_AC.N>
Next brief in stream: KARN-W7-R1-EVAL-HARNESS (sequential, Wave 7)
```

After emitting closing summary, append session entry to
`00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1,
and flip `status: COMPLETE` in this brief's frontmatter.

---

*End of CLAUDECODE_BRIEF_M2_D7_PER_TOOL_PLANNER v1.0 (authored 2026-04-30 — Wave 6 open).*
