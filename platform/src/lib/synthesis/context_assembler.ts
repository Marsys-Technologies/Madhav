/**
 * MARSYS-JIS — context_assembly step (W2-CTX-ASSEMBLY)
 *
 * Optional LLM step inserted between retrieval and synthesis in the
 * NEW_QUERY_PIPELINE_ENABLED path. Gated behind CONTEXT_ASSEMBLY_ENABLED
 * (default OFF). When OFF, route.ts forwards the raw ToolBundle[] directly
 * — this module is never called.
 *
 * When ON: receives the full retrieval bundle and asks the assembler model
 * to compress + reorder it (remove redundancy, surface most-relevant first,
 * preserve all citation metadata). On any failure (provider error, parse
 * error, schema mismatch) the function falls through to a pass-through
 * bundle with `context_assembly_model_id: 'pass-through'` so the downstream
 * pipeline never breaks because of an assembly fault.
 *
 * Trace contract: emits a single `context_assembly` step (step_type: 'llm')
 * via traceEmitter using the caller-allocated step_seq. The deterministic
 * `context_assembly` emit inside SingleModelOrchestrator continues to fire
 * after this step — they coexist (different seqs) so the trace UI can read
 * either.
 *
 * ── Token-budgeted layer assembler (GANGA-P3-R2-S2) ─────────────────────────
 * assembleContext() is a pure, synchronous utility that packs LayerContext
 * objects into a token-budgeted string for the synthesis LLM. No LLM calls.
 * Used by single_model_strategy.ts to log assembly metadata and verify B.11
 * compliance on the assembled context.
 */

import 'server-only'

import { generateText } from 'ai'

import { resolveModel, googleProviderOptions } from '@/lib/models/resolver'
import { getModelMeta } from '@/lib/models/registry'
import { traceEmitter } from '@/lib/trace/emitter'
import { telemetry } from '@/lib/telemetry/index'
import type { QueryPlan, ToolBundle } from '@/lib/retrieve/types'

import type { ContextBundle } from './types'

// Tool-name → layer partitioning. Mirrors the MON-8 writeContextAssemblyLog
// classification in route.ts so per-layer token totals on the ContextBundle
// align with the context_assembly_log schema.
const L1_TOOLS = new Set([
  'chart_facts_query', 'divisional_query', 'kp_query',
  'manifest_query', 'query_kp_ruling_planets', 'query_varshaphala',
  'saham_query', 'temporal', 'timeline_query',
])
const L2_5_TOOLS = new Set([
  'msr_sql', 'query_msr_aggregate', 'query_signal_state',
  'pattern_register', 'resonance_register',
  'contradiction_register', 'cluster_atlas',
])
const L4_TOOLS = new Set(['remedial_codex_query', 'domain_report_query'])

const CHARS_PER_TOKEN = 4

interface CallerOpts {
  queryId: string
  conversationId?: string
  stepSeq: number
}

interface LayerTokens {
  l1: number
  l2_5: number
  l4: number
  vector: number
  cgm: number
  total: number
}

function countTokens(toolBundles: ToolBundle[]): LayerTokens {
  let l1 = 0, l2_5 = 0, l4 = 0, vector = 0, cgm = 0
  for (const tb of toolBundles) {
    let chars = 0
    for (const r of tb.results) chars += r.content.length
    const tokens = Math.ceil(chars / CHARS_PER_TOKEN)
    if (tb.tool_name === 'vector_search') vector += tokens
    else if (tb.tool_name === 'cgm_graph_walk') cgm += tokens
    else if (L1_TOOLS.has(tb.tool_name)) l1 += tokens
    else if (L2_5_TOOLS.has(tb.tool_name)) l2_5 += tokens
    else if (L4_TOOLS.has(tb.tool_name)) l4 += tokens
  }
  return { l1, l2_5, l4, vector, cgm, total: l1 + l2_5 + l4 + vector + cgm }
}

function passThrough(
  toolBundles: ToolBundle[],
  modelId: string,
  latencyMs: number,
): ContextBundle {
  const t = countTokens(toolBundles)
  return {
    tool_bundles: toolBundles,
    context_assembly_compressed: true,
    context_assembly_model_id: modelId,
    context_assembly_latency_ms: latencyMs,
    l1_tokens: t.l1,
    l2_5_tokens: t.l2_5,
    l4_tokens: t.l4,
    vector_tokens: t.vector,
    cgm_tokens: t.cgm,
    total_tokens: t.total,
  }
}

/**
 * Attempt to parse + validate the LLM response into a ToolBundle[]. Returns
 * the original bundles on any structural mismatch — the model can drop
 * results but must not invent ones, so we keep only entries whose
 * tool_bundle_id is present in the input set.
 */
function parseAssemblerOutput(
  raw: string,
  original: ToolBundle[],
): ToolBundle[] | null {
  let parsed: unknown
  try {
    // The model may wrap the JSON in code fences; strip the most common forms.
    const stripped = raw
      .replace(/^```(?:json)?\s*/i, '')
      .replace(/\s*```\s*$/i, '')
      .trim()
    parsed = JSON.parse(stripped)
  } catch {
    return null
  }
  const arr = Array.isArray(parsed) ? parsed : null
  if (!arr) return null

  const byId = new Map(original.map(tb => [tb.tool_bundle_id, tb]))
  const out: ToolBundle[] = []
  for (const item of arr) {
    if (!item || typeof item !== 'object') continue
    const id = (item as { tool_bundle_id?: unknown }).tool_bundle_id
    if (typeof id !== 'string') continue
    const orig = byId.get(id)
    if (!orig) continue
    // Trust the original metadata; only the `results` array may be
    // reordered/compressed. Anything else from the model is discarded so a
    // hallucinated tool_name or version cannot leak downstream.
    const results = (item as { results?: unknown }).results
    if (!Array.isArray(results)) {
      out.push(orig)
      continue
    }
    const allowedSignals = new Set(orig.results.map(r => r.signal_id ?? r.content))
    const filtered = results.filter(r =>
      r && typeof r === 'object' && typeof (r as { content?: unknown }).content === 'string'
      && allowedSignals.has(
        (r as { signal_id?: string; content: string }).signal_id
          ?? (r as { content: string }).content,
      ),
    ) as ToolBundle['results']
    out.push({ ...orig, results: filtered.length > 0 ? filtered : orig.results })
  }
  return out.length > 0 ? out : null
}

/**
 * P5 D.5.1 — short-circuit threshold. If the combined tool-result token
 * estimate is below this value, skip the context-assembler LLM call
 * entirely. Small bundles (e.g. factual queries returning 3-4 rows) do not
 * benefit from compression and the extra round-trip adds 1-2s with no
 * quality gain. Empirically, 2000 tokens is where compression starts paying
 * for itself (latency + dollars).
 */
export const CONTEXT_ASSEMBLY_TOKEN_THRESHOLD = 2000

/** Best-effort token estimate for a ToolBundle list — 1 token ≈ 4 chars. */
export function estimateBundleTokens(bundles: ToolBundle[]): number {
  return Math.ceil(JSON.stringify(bundles).length / 4)
}

export async function contextAssembler(
  toolBundles: ToolBundle[],
  queryPlan: QueryPlan,
  modelId: string,
  opts: CallerOpts,
): Promise<ContextBundle> {
  const startedAt = Date.now()
  const startedAtIso = new Date(startedAt).toISOString()

  traceEmitter.emitStep({
    event: 'step_start',
    query_id: opts.queryId,
    step: {
      query_id: opts.queryId,
      conversation_id: opts.conversationId,
      step_seq: opts.stepSeq,
      step_name: 'context_assembly',
      step_type: 'llm',
      status: 'running',
      started_at: startedAtIso,
      data_summary: { model: modelId },
      payload: {},
    },
  })

  const systemPrompt =
    'You are the context_assembly step of an astrology query pipeline.\n' +
    'You receive raw retrieval results from multiple retrieval tools.\n' +
    'Your job:\n' +
    '1. Remove redundant passages (the same signal cited by multiple tools).\n' +
    '2. Reorder by relevance to the query — most directly relevant first.\n' +
    '3. Preserve every signal_id and source reference exactly as given.\n' +
    '4. Do NOT synthesize, interpret, or fabricate new signals.\n' +
    'Output ONLY a raw JSON array (no prose, no markdown, no code fences). ' +
    'Each element MUST be a ToolBundle with the same tool_bundle_id you received ' +
    'and a `results` array containing only entries whose signal_id (or content) ' +
    'appeared in the input.'

  const userPrompt = [
    `Query: ${queryPlan.query_text}`,
    `Query class: ${queryPlan.query_class}`,
    '',
    'Retrieval results (input ToolBundle[]):',
    JSON.stringify(toolBundles, null, 2),
    '',
    'Return the compressed, reordered ToolBundle[] as a raw JSON array.',
  ].join('\n')

  let usage: { inputTokens?: number; outputTokens?: number } | undefined
  let assembled: ToolBundle[] | null = null
  let errorMsg: string | null = null

  // Retry + timeout guard — applies to ALL providers, not just NIM.
  //
  // Without maxRetries: 0, the AI SDK retries errors up to 3 times.
  // For NIM: each call can hang 90s (nimFetch AbortSignal.timeout) → 3×90s = 270s.
  // For Anthropic/Gemini/OpenAI: large retrieval bundles can take 20-40s per call →
  // 3×40s = 120s, which hits Cloud Run maxDuration before synthesis even starts.
  // maxRetries: 0 ensures the first error surfaces immediately → passThrough.
  //
  // AbortSignal.timeout(15_000): hard-caps any single assembler call at 15s.
  // Context assembly is a JSON-reorder step, not open-ended synthesis — 15s is
  // generous. On abort the catch fires, errorMsg is set, passThrough returns the
  // original bundles unchanged, and synthesis proceeds normally.
  const assemblerSignal = AbortSignal.timeout(15_000)

  try {
    const result = await generateText({
      model: resolveModel(modelId),
      system: systemPrompt,
      messages: [{ role: 'user', content: userPrompt }],
      temperature: 0,
      maxOutputTokens: 8000,
      maxRetries: 0,
      abortSignal: assemblerSignal,
      // Apply Google safety overrides when the assembler model is a Gemini model.
      // Returns undefined for all non-Google models — spread is a no-op.
      ...(googleProviderOptions(modelId) && {
        providerOptions: googleProviderOptions(modelId),
      }),
    })
    usage = result.usage
    assembled = parseAssemblerOutput(result.text, toolBundles)
    if (!assembled) errorMsg = 'parse_or_schema_mismatch'
  } catch (err) {
    // BUG-CA-3: err.message can be undefined for AI SDK AbortError / timeout wrapper
    // objects whose Error subclass never sets message in the constructor.
    // undefined ?? 'unknown_error' = 'unknown_error' — the exact string seen in
    // production traces. Fall through: rawMsg → err.name → 'llm_call_error'.
    const rawMsg = err instanceof Error ? err.message : String(err)
    errorMsg = rawMsg || (err instanceof Error ? err.name : null) || 'llm_call_error'
    telemetry.recordError(
      'context_assembler',
      'llm_call_failed',
      err instanceof Error ? err : new Error(String(err)),
    )
  }

  const latencyMs = Date.now() - startedAt

  if (!assembled) {
    console.warn(`[context_assembler] assembly failed (${errorMsg}); passing through`)
    traceEmitter.emitStep({
      event: 'step_error',
      query_id: opts.queryId,
      step: {
        query_id: opts.queryId,
        conversation_id: opts.conversationId,
        step_seq: opts.stepSeq,
        step_name: 'context_assembly',
        step_type: 'llm',
        status: 'error',
        started_at: startedAtIso,
        completed_at: new Date().toISOString(),
        latency_ms: latencyMs,
        data_summary: { model: modelId, result: errorMsg ?? 'llm_call_error' },
        payload: {},
      },
    })
    // BUG-CA-4: wrap passThrough in try/catch — countTokens iterates tb.results
    // and accesses r.content.length; if any result has content:undefined, it throws
    // TypeError which propagates to route.ts outer catch → HTTP 500 → no response.
    try {
      return passThrough(toolBundles, 'pass-through', latencyMs)
    } catch {
      return {
        tool_bundles: toolBundles,
        context_assembly_compressed: true,
        context_assembly_model_id: 'pass-through',
        context_assembly_latency_ms: latencyMs,
        l1_tokens: 0,
        l2_5_tokens: 0,
        l4_tokens: 0,
        vector_tokens: 0,
        cgm_tokens: 0,
        total_tokens: 0,
      }
    }
  }

  const tokens = countTokens(assembled)

  traceEmitter.emitStep({
    event: 'step_done',
    query_id: opts.queryId,
    step: {
      query_id: opts.queryId,
      conversation_id: opts.conversationId,
      step_seq: opts.stepSeq,
      step_name: 'context_assembly',
      step_type: 'llm',
      status: 'done',
      started_at: startedAtIso,
      completed_at: new Date().toISOString(),
      latency_ms: latencyMs,
      data_summary: {
        model: modelId,
        input_tokens: usage?.inputTokens ?? 0,
        output_tokens: usage?.outputTokens ?? 0,
        token_estimate: tokens.total,
      },
      payload: {
        l1_tokens: tokens.l1,
        l2_tokens: tokens.l2_5,
        total_tokens: tokens.total,
      },
    },
  })

  telemetry.recordCost(
    'context_assembler',
    modelId,
    usage?.inputTokens ?? 0,
    usage?.outputTokens ?? 0,
    0,
  )

  return {
    tool_bundles: assembled,
    context_assembly_compressed: true,
    context_assembly_model_id: modelId,
    context_assembly_latency_ms: latencyMs,
    l1_tokens: tokens.l1,
    l2_5_tokens: tokens.l2_5,
    l4_tokens: tokens.l4,
    vector_tokens: tokens.vector,
    cgm_tokens: tokens.cgm,
    total_tokens: tokens.total,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Token-budgeted layer assembler (GANGA-P3-R2-S2 — CTX-ASSEMBLER)
//
// Pure, synchronous — no LLM calls. Packs LayerContext objects into a
// token-budgeted string with section headers for the synthesis LLM.
// Checks B.11 compliance on the assembled output via checkB11Compliance.
// ─────────────────────────────────────────────────────────────────────────────

import { checkB11Compliance } from './b11_guard'
import { writeContextAssemblyLog } from '@/lib/db/trace/context_assembly_writer'
import type { ContextAssemblyItem } from '@/lib/db/trace/context_assembly_writer'

export interface LayerContext {
  /** e.g. 'L1', 'L2_5', 'L3' */
  layer: 'L1' | 'L2_5' | 'L3'
  /** e.g. 'MSR', 'UCN', 'CGM', 'query_retrieval', 'FORENSIC' */
  artifactId: string
  content: string
  /** Rough token estimate: Math.ceil(content.length / 4) */
  tokenEstimate: number
  /** 1 = highest (keep even if budget tight); 3 = lowest (drop first) */
  priority: number
}

export interface AssemblyOptions {
  /** Total token budget for assembled context (default: 12000) */
  maxTokens: number
  /** Artifact IDs that must be included even if over budget */
  requiredLayers: string[]
  queryId?: string
}

export interface AssemblyResult {
  /** The final packed string for the synthesis LLM */
  assembledContext: string
  /** Which artifact IDs made it into the assembly */
  includedArtifacts: string[]
  /** Which were dropped due to budget */
  droppedArtifacts: string[]
  totalTokenEstimate: number
  /** True if required L2.5 layers (MSR, UCN, CGM) are present */
  b11Compliant: boolean
}

const DEFAULT_ASSEMBLY_OPTIONS: AssemblyOptions = {
  maxTokens: 12_000,
  requiredLayers: ['MSR', 'UCN', 'CGM'],
}

const LAYER_HEADERS: Record<string, string> = {
  L1:   'L1: CHART FACTS',
  L2_5: 'L2.5: HOLISTIC SYNTHESIS',
  L3:   'L3: QUERY RETRIEVAL',
}

const ARTIFACT_LABELS: Record<string, string> = {
  MSR:             'MSR — MASTER SIGNAL REGISTER',
  UCN:             'UCN — UNIFIED CHART NARRATIVE',
  CDLM:            'CDLM — CROSS-DOMAIN LINKAGE MATRIX',
  CGM:             'CGM — CAUSAL GRAPH MODEL',
  RM:              'RM — RESONANCE MAP',
  FORENSIC:        'FORENSIC — CHART FACTS',
  query_retrieval: 'QUERY RETRIEVAL',
}

/**
 * Assembles a token-budgeted context payload from layer contexts.
 *
 * Ordering:
 *   1. Required layers (requiredLayers match) — always included even if over budget
 *   2. Optional layers sorted by priority ascending (1 = keep first)
 *
 * Section headers separate layers so the synthesis LLM can navigate them.
 * Calls checkB11Compliance on the assembled string to set b11Compliant.
 */
export function assembleContext(
  layers: LayerContext[],
  options?: Partial<AssemblyOptions>,
): AssemblyResult {
  const opts: AssemblyOptions = { ...DEFAULT_ASSEMBLY_OPTIONS, ...options }
  const requiredSet = new Set(opts.requiredLayers)

  // Partition: required vs optional
  const required = layers.filter(l => requiredSet.has(l.artifactId))
  const optional = layers
    .filter(l => !requiredSet.has(l.artifactId))
    .sort((a, b) => a.priority - b.priority)

  const included: LayerContext[] = []
  const droppedArtifacts: string[] = []
  let totalTokens = 0

  // Always include required layers (warn if over budget, but include anyway)
  for (const layer of required) {
    included.push(layer)
    totalTokens += layer.tokenEstimate
  }

  if (totalTokens > opts.maxTokens) {
    console.warn(JSON.stringify({
      event: 'context_assembler_budget_exceeded_by_required',
      required_tokens: totalTokens,
      max_tokens: opts.maxTokens,
      query_id: opts.queryId ?? null,
    }))
  }

  // Greedily pack optional layers within remaining budget
  for (const layer of optional) {
    if (totalTokens + layer.tokenEstimate <= opts.maxTokens) {
      included.push(layer)
      totalTokens += layer.tokenEstimate
    } else {
      droppedArtifacts.push(layer.artifactId)
    }
  }

  // Format the assembled string with section headers
  // Group by layer type for clean separation
  const sections: string[] = []
  const layerOrder: Array<'L1' | 'L2_5' | 'L3'> = ['L1', 'L2_5', 'L3']
  for (const layerType of layerOrder) {
    const layerItems = included.filter(l => l.layer === layerType)
    if (layerItems.length === 0) continue

    sections.push(`=== ${LAYER_HEADERS[layerType] ?? layerType} ===`)
    for (const item of layerItems) {
      const label = ARTIFACT_LABELS[item.artifactId] ?? item.artifactId
      sections.push(`\n--- ${label} ---`)
      sections.push(item.content)
    }
  }

  const assembledContext = sections.join('\n')

  // Check B.11 compliance on the assembled output
  const b11Result = checkB11Compliance(assembledContext)

  if (!b11Result.compliant) {
    console.log(JSON.stringify({
      event: 'context_assembler_b11_partial',
      missing: b11Result.missingLayers,
      present: b11Result.presentLayers,
      query_id: opts.queryId ?? null,
    }))
  }

  // TRACE-T1: emit per-item assembly rows when a queryId is available.
  if (opts.queryId) {
    const stepId = `assemble:${opts.queryId}`
    const budget = opts.maxTokens
    let committedTokens = 0
    const traceItems: ContextAssemblyItem[] = []
    let rank = 0

    // Mirror the pack order: required first (all included), then optional (sorted by priority)
    for (const layer of [...required, ...optional]) {
      const isIncluded = included.includes(layer)
      const mappedLayer: ContextAssemblyItem['layer'] =
        layer.layer === 'L1' ? 'L1' : 'L2_5'
      traceItems.push({
        query_id: opts.queryId!,
        assembly_step_id: stepId,
        item_rank: rank++,
        source_bundle: layer.layer,
        source_item_id: layer.artifactId,
        layer: mappedLayer,
        token_cost: layer.tokenEstimate,
        status: isIncluded ? 'INCLUDED' : 'DROPPED',
        drop_reason: isIncluded ? undefined : 'BUDGET_EXCEEDED',
        cumulative_tokens_at_decision: committedTokens,
        budget_at_decision: budget,
      })
      if (isIncluded) committedTokens += layer.tokenEstimate
    }
    writeContextAssemblyLog(traceItems)
  }

  return {
    assembledContext,
    includedArtifacts: included.map(l => l.artifactId),
    droppedArtifacts,
    totalTokenEstimate: totalTokens,
    b11Compliant: b11Result.compliant,
  }
}
