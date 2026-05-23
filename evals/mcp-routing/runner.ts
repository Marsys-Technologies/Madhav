/**
 * runner.ts — MCPT v3.2 Phase 9b: MCP routing eval runner.
 *
 * For each prompt in prompts.json:
 *   1. Builds a system message with the MCP catalog from getCatalogForTier('super_admin', CATALOG)
 *   2. Calls Anthropic Haiku with tool_choice: {type: 'auto'}
 *   3. Records the first tool call
 *   4. Checks if first_tool matches gold or acceptable_alternatives
 *   5. Writes results to evals/mcp-routing/results_<sha>.json
 *
 * Usage:
 *   # Dry-run (no API key needed — CI safe):
 *   npx tsx evals/mcp-routing/runner.ts
 *
 *   # Live eval (requires ANTHROPIC_API_KEY):
 *   ANTHROPIC_API_KEY=sk-ant-... npx tsx evals/mcp-routing/runner.ts
 *
 * Goal: ≥80% gold-or-acceptable when run with a live ANTHROPIC_API_KEY.
 *
 * MCPT v3.2 Phase 9b — Routing Eval
 */

import { readFileSync, writeFileSync, mkdirSync } from 'fs'
import { execSync } from 'child_process'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PROMPTS_PATH = join(__dirname, 'prompts.json')
const RESULTS_DIR = __dirname

// ── Types ──────────────────────────────────────────────────────────────────────

export interface RoutingPrompt {
  id: string
  prompt: string
  audience_tier: string
  gold_first_tool: string
  acceptable_alternatives: string[]
}

export interface PromptResult {
  id: string
  prompt: string
  gold_first_tool: string
  acceptable_alternatives: string[]
  first_tool_called: string | null
  outcome: 'gold' | 'acceptable' | 'wrong' | 'no_tool_call'
  pass: boolean
  raw_response?: unknown
  error?: string
}

export interface EvalResults {
  run_at: string
  git_sha: string
  mode: 'live' | 'dry_run'
  model: string
  total: number
  passed: number
  failed: number
  pass_rate: number
  goal: string
  goal_met: boolean | null
  results: PromptResult[]
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function getGitSha(): string {
  try {
    return execSync('git rev-parse --short HEAD', { stdio: ['pipe', 'pipe', 'pipe'] })
      .toString()
      .trim()
  } catch {
    return 'unknown'
  }
}

export function loadPrompts(): RoutingPrompt[] {
  const raw = readFileSync(PROMPTS_PATH, 'utf-8')
  return JSON.parse(raw) as RoutingPrompt[]
}

/**
 * Build the system message that presents the MCP tool catalog to the LLM.
 * Uses getCatalogForTier to apply tier-appropriate ordering and annotations.
 */
function buildSystemMessage(tier: string): string {
  // We import the catalog inline to avoid a hard build dependency in the eval runner.
  // In live mode the catalog is loaded dynamically; in dry-run it is bypassed.
  const tools = getCatalogForTierInline(tier)
  const toolDocs = tools
    .map(t => `### ${t.name}\n${t.description}`)
    .join('\n\n')

  return `You are an expert Jyotish (Vedic astrology) assistant operating the MARSYS-JIS MCP server.
You have access to the following tools. Your task is to identify the BEST tool to call first for the user's question.

${toolDocs}

Instructions:
- Call the most appropriate tool first based on the descriptions above.
- Do NOT synthesize an answer without calling a tool.
- Use tool_choice=auto and let your reasoning guide the first tool selection.`
}

/**
 * Inline catalog loader — avoids requiring a TypeScript build step.
 * Returns the catalog entries with their descriptions for prompt injection.
 *
 * In a full implementation this would import from:
 *   import { CATALOG } from '../../platform-mcp/src/tools/catalog.js'
 *   import { getCatalogForTier } from '../../platform-mcp/src/tools/tier_catalog.js'
 *
 * For the eval runner we embed a minimal catalog derived from the tool catalog
 * documentation to avoid needing to compile platform-mcp first.
 */
function getCatalogForTierInline(tier: string): Array<{ name: string; description: string }> {
  const catalog = [
    {
      name: 'chart_summary',
      description: 'What it does: Returns a canonical ~50-fact bundle spanning birth metadata, planetary positions, house assignments, yogas, arudha lagna, current dasha state, and sensitive points in a single call. When to prefer: Use when you need a wide-by-default chart snapshot covering multiple categories. Prefer query_chart_facts when you need a single category. Prefer holistic_bundle when cross-layer synthesis is needed.',
    },
    {
      name: 'query_chart_facts',
      description: 'What it does: Queries the chart_facts table with structured filters (category, planet, house). 2,717 rows across 27 categories including shadbala, ashtakavarga_sav, kp_cusp, bhava_bala, varshphal, avastha. When to prefer: Use for single fact lookups ("What is Saturn\'s shadbala?", "Which planets are in house 7?"). Prefer query_signals for MSR signal corpus data. Prefer holistic_bundle when synthesis is needed.',
    },
    {
      name: 'query_signals',
      description: 'What it does: Queries the MSR signal corpus (499+ astrological signals) with structured filters (domain, planet, dasha_lord, min_confidence, forward_looking). When to prefer: Use for "give me all forward-looking career signals" style queries. Prefer holistic_bundle when interpretation is also needed.',
    },
    {
      name: 'query_dasha_periods',
      description: 'What it does: Returns the Vimshottari dasha schedule (Mahadasha, Antardasha, Pratyantar) with exact start/end dates. Input: at (single ISO date), range ({start, end}), or omit for full sequence. When to prefer: Use for "what dasha is active on date X?" without synthesis overhead.',
    },
    {
      name: 'query_panchanga',
      description: 'What it does: Returns the 5 limbs of the Vedic day (tithi, vara, nakshatra, yoga, karana) plus hora, choghadiya, and muhurat windows for any date. 73,414 rows covering 1900–2100. When to prefer: Use for date-specific panchang questions ("What is today\'s nakshatra?", "When is Rahu Kalam?").',
    },
    {
      name: 'query_ephemeris',
      description: 'What it does: Returns date-indexed planetary positions (sign, degree, nakshatra, retrograde status, speed) for a given planet and date range. When to prefer: Use for "What sign was Saturn in during Q1 2024?" or retrograde status checks.',
    },
    {
      name: 'query_transit_event',
      description: 'What it does: Searches ephemeris_daily for specific transit events (sign ingresses, conjunctions, degree crossings) within a date range. When to prefer: Use for "When does Saturn enter Aquarius?" style questions. Prefer query_ephemeris for day-by-day position data.',
    },
    {
      name: 'lel_query',
      description: 'What it does: Queries the Life Event Log (LEL) — 36 verified life events, 5 period summaries, 6 chronic patterns — with optional category, date range, and significance filters. When to prefer: Use to retrieve verified life events ("what career events happened 2015–2020?").',
    },
    {
      name: 'vector_search',
      description: 'What it does: Semantically searches the RAG chunk corpus (MSR signals, UCN, CDLM, domain reports, L1 facts) using Vertex AI 768-dim embeddings. 4,589+ RAG chunks. When to prefer: Use for "find content similar to X" queries where you do not know the exact signal ID.',
    },
    {
      name: 'get_cgm_subgraph',
      description: 'What it does: Traverses the Cross-Domain Linkage Matrix (CGM) from a seed node and returns a subgraph of connected signals and domains up to N hops. When to prefer: Use to map cross-domain signal topology ("what signals are connected to SIG.MSR.234?").',
    },
    {
      name: 'cross_school_lookup',
      description: 'What it does: Checks an astrological claim against Parashara, Jaimini, KP, and Tajaka and returns where each school agrees, disagrees, or is silent, with a convergence score (0–1). When to prefer: Use when the question is explicitly about multi-school convergence on a rule. Prefer multi_school_bundle when you also want per-school evidence queries.',
    },
    {
      name: 'read_asset',
      description: 'What it does: Returns the raw markdown of a canonical MARSYS-JIS artifact by its canonical_id (MSR, UCN, CDLM, CGM, RM, FORENSIC, LEL). When to prefer: Use when you need the full text of a synthesis layer document.',
    },
    {
      name: 'read_classical_text',
      description: 'What it does: Retrieves excerpts from the MARSYS-JIS classical corpus (BPHS, KP Reader, Jaimini Sutram, Tajaka Neelakanthi) ranked by semantic similarity to a query. When to prefer: Use when the question requires a classical textual citation ("what does Parashara say about Ketu in the 12th?").',
    },
    {
      name: 'holistic_bundle',
      description: 'What it does: Performs a parallel 8-tool holistic read of the MARSYS-JIS corpus, fanning out across MSR signals, CGM subgraph, UCN/RM/CDLM vector layers, LEL events, current panchang, and active dasha state. When to prefer: FIRST CALL when any synthesis question requires cross-layer context. Use individual surgical primitives when you need only one data type.',
    },
    {
      name: 'multi_school_bundle',
      description: 'What it does: Runs a parallel multi-school convergence check on an astrological claim — fires cross_school_lookup, per-school evidence queries (Parashara/Jaimini/KP/Tajaka), and reads the most-cited classical text reference. When to prefer: Use when the question explicitly concerns whether all four schools agree or disagree on a claim.',
    },
    {
      name: 'get_trace',
      description: 'What it does: Returns the full query_trace_steps ledger for a prior MCP query — every pipeline stage with inputs, outputs, latencies, and token estimates. When to prefer: Use after a holistic_bundle call to debug what happened.',
    },
    {
      name: 'list_recent_queries',
      description: 'What it does: Returns recent MCP call history for the current API key. When to prefer: Use when you want an audit of what this API key has called recently.',
    },
  ]

  // super_admin gets full catalog; client hides ops tools
  const opsTools = new Set(['data_coverage', 'tool_health', 'log_prediction', 'record_outcome', 'flag_disagreement'])
  if (tier === 'client') {
    return catalog.filter(t => !opsTools.has(t.name))
  }
  return catalog
}

/**
 * Determine the outcome for a prompt result.
 */
function classifyOutcome(
  firstToolCalled: string | null,
  gold: string,
  acceptable: string[],
): 'gold' | 'acceptable' | 'wrong' | 'no_tool_call' {
  if (firstToolCalled === null) return 'no_tool_call'
  if (firstToolCalled === gold) return 'gold'
  if (acceptable.includes(firstToolCalled)) return 'acceptable'
  return 'wrong'
}

// ── Dry-run mode ───────────────────────────────────────────────────────────────

/**
 * Dry-run mode: simulate a routing eval without making API calls.
 *
 * Returns mock results where every prompt is "called" with its gold_first_tool.
 * This validates the eval infrastructure (structure, scoring, output writing)
 * without requiring ANTHROPIC_API_KEY.
 */
function runDryRun(prompts: RoutingPrompt[]): EvalResults {
  const results: PromptResult[] = prompts.map(p => {
    const firstTool = p.gold_first_tool // Simulate perfect routing
    const outcome = classifyOutcome(firstTool, p.gold_first_tool, p.acceptable_alternatives)
    return {
      id: p.id,
      prompt: p.prompt,
      gold_first_tool: p.gold_first_tool,
      acceptable_alternatives: p.acceptable_alternatives,
      first_tool_called: firstTool,
      outcome,
      pass: outcome === 'gold' || outcome === 'acceptable',
    }
  })

  const passed = results.filter(r => r.pass).length
  const total = results.length

  return {
    run_at: new Date().toISOString(),
    git_sha: getGitSha(),
    mode: 'dry_run',
    model: 'dry-run-mock',
    total,
    passed,
    failed: total - passed,
    pass_rate: passed / total,
    goal: '>=80% gold-or-acceptable',
    goal_met: null, // Not meaningful in dry-run — use live mode for real eval
    results,
  }
}

// ── Live mode (requires ANTHROPIC_API_KEY) ─────────────────────────────────────

/**
 * Live mode: calls Anthropic Haiku with tool_choice: auto for each prompt.
 *
 * Requires ANTHROPIC_API_KEY environment variable.
 * Uses the @anthropic-ai/sdk (if installed) or falls back to raw fetch.
 */
async function runLive(prompts: RoutingPrompt[]): Promise<EvalResults> {
  const apiKey = process.env['ANTHROPIC_API_KEY']
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY is not set. Use dry-run mode or set the env var.')
  }

  const model = 'claude-haiku-4-5'
  const results: PromptResult[] = []

  for (const p of prompts) {
    const systemMessage = buildSystemMessage(p.audience_tier)
    const toolDefs = getCatalogForTierInline(p.audience_tier).map(t => ({
      name: t.name,
      description: t.description,
      input_schema: {
        type: 'object' as const,
        properties: {},
        required: [],
      },
    }))

    let firstToolCalled: string | null = null
    let rawResponse: unknown = null
    let error: string | undefined

    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model,
          max_tokens: 1024,
          system: systemMessage,
          tools: toolDefs,
          tool_choice: { type: 'auto' },
          messages: [{ role: 'user', content: p.prompt }],
        }),
      })

      if (!response.ok) {
        const errText = await response.text()
        throw new Error(`API error ${response.status}: ${errText}`)
      }

      const data = await response.json() as {
        content: Array<{ type: string; name?: string }>
        stop_reason: string
      }
      rawResponse = data

      // Find first tool_use block
      const toolUseBlock = data.content?.find(block => block.type === 'tool_use')
      if (toolUseBlock?.name) {
        firstToolCalled = toolUseBlock.name
      }
    } catch (e) {
      error = String(e)
      console.error(`[routing-eval] Error for prompt ${p.id}: ${error}`)
    }

    const outcome = classifyOutcome(firstToolCalled, p.gold_first_tool, p.acceptable_alternatives)
    results.push({
      id: p.id,
      prompt: p.prompt,
      gold_first_tool: p.gold_first_tool,
      acceptable_alternatives: p.acceptable_alternatives,
      first_tool_called: firstToolCalled,
      outcome,
      pass: outcome === 'gold' || outcome === 'acceptable',
      raw_response: rawResponse,
      error,
    })

    // Brief pause to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 200))
  }

  const passed = results.filter(r => r.pass).length
  const total = results.length
  const passRate = passed / total

  return {
    run_at: new Date().toISOString(),
    git_sha: getGitSha(),
    mode: 'live',
    model,
    total,
    passed,
    failed: total - passed,
    pass_rate: passRate,
    goal: '>=80% gold-or-acceptable',
    goal_met: passRate >= 0.8,
    results,
  }
}

// ── Main entry ─────────────────────────────────────────────────────────────────

export interface RunOptions {
  dryRun?: boolean
}

/**
 * Run the routing eval.
 *
 * @param opts.dryRun  If true (or ANTHROPIC_API_KEY is absent), runs in dry-run mode.
 * @returns            EvalResults object (also written to results_<sha>.json)
 */
export async function runEval(opts: RunOptions = {}): Promise<EvalResults> {
  const prompts = loadPrompts()
  const apiKey = process.env['ANTHROPIC_API_KEY']
  const useDryRun = opts.dryRun === true || !apiKey

  let evalResults: EvalResults

  if (useDryRun) {
    console.log('[routing-eval] Running in DRY-RUN mode (no API key needed)')
    evalResults = runDryRun(prompts)
  } else {
    console.log(`[routing-eval] Running LIVE eval with ${prompts.length} prompts…`)
    evalResults = await runLive(prompts)
  }

  // Write results artifact
  const sha = evalResults.git_sha
  const resultPath = join(RESULTS_DIR, `results_${sha}.json`)
  mkdirSync(RESULTS_DIR, { recursive: true })
  writeFileSync(resultPath, JSON.stringify(evalResults, null, 2))

  console.log(`\n[routing-eval] Mode: ${evalResults.mode.toUpperCase()}`)
  console.log(`[routing-eval] Result: ${evalResults.passed}/${evalResults.total} pass (${(evalResults.pass_rate * 100).toFixed(1)}%)`)
  if (evalResults.goal_met !== null) {
    console.log(`[routing-eval] Goal (>=80%): ${evalResults.goal_met ? 'MET ✓' : 'NOT MET ✗'}`)
  }
  console.log(`[routing-eval] Written to: ${resultPath}`)

  return evalResults
}

// ── CLI invocation ─────────────────────────────────────────────────────────────

// Run when invoked directly (not imported)
const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]
if (isMain) {
  const dryRun = !process.env['ANTHROPIC_API_KEY']
  if (dryRun) {
    console.log('[routing-eval] ANTHROPIC_API_KEY not set — running in dry-run mode.')
    console.log('[routing-eval] To run a live eval: ANTHROPIC_API_KEY=sk-ant-... npx tsx evals/mcp-routing/runner.ts')
  }
  runEval({ dryRun }).catch(err => {
    console.error('[routing-eval] Fatal error:', err)
    process.exit(1)
  })
}
