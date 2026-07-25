#!/usr/bin/env tsx
/**
 * evals/k2/instrumentation_tracks.ts — Lane K2 item 3 (EL-22): the four mandated
 * instrumentation tracks, captured from a sealed-harness transcript so every future battery run
 * (not just Darpana run 1) emits them. Per `UAT_DARPANA_DESIGN_v1_0.md` §6.0/§6.1/§6.2/§6.3:
 *
 *   - Experience telemetry (§6.1)         — t_total, tool_calls_n, error/retry counts, etc.
 *   - Investigation track   I1–I5 (§6.0)  — tool reasoning, lead-following, iterative
 *                                            deepening, coverage judgment, evidence fidelity.
 *   - Vidhi planner track   V1–V5 (§6.2)  — intent, tool selection, astrological coverage,
 *                                            instruction quality, plan sufficiency.
 *   - Retrieval-plane track RE1–RE5 (§6.3) — routing fidelity, envelope conformance, density,
 *                                            drill-pointer efficacy, payload integrity.
 *
 * SCOPE (honest, per B.10): this module is the CAPTURE mechanism the charter asks for — it
 * extracts every raw ledger a human/Opus judge needs (`leads_offered`/`leads_pursued`,
 * `aspects_required`/`aspects_planned`/`aspects_missed`, fallback-taken ledger, envelope-field
 * presence, etc.) and computes every dimension that is MECHANICALLY decidable from transcript
 * structure alone. The Darpana design is explicit that I1/I3/I4/I5 and V1/V4/V5's final 0–2
 * scores are Phase-4 JUDGMENT calls by a dedicated Opus auditor reading full transcripts with
 * question-level context this module does not have (e.g. "was tool selection question-driven"
 * requires knowing what the question NEEDED). Fabricating those numbers here would violate
 * B.10 exactly as surely as inventing a chart value — so this module emits
 * `judgment: null, judged_by: 'PENDING_OPUS_AUDITOR'` for the dimensions that genuinely require
 * a reasoning judge, and a real computed value for every dimension that does not.
 *
 * Usage (library): import { captureInstrumentation } from './instrumentation_tracks.js'
 * Usage (CLI):      npx tsx evals/k2/instrumentation_tracks.ts <transcript.json> [domain] [chart_id]
 */
import { readFileSync } from 'fs'
import { loadTranscript, lenientParseJson, bareToolName } from './transcript_utils.js'
import type { NormalizedTranscript, TranscriptCall } from './types.js'

// ─────────────────────────────────────────────────────────────────────────────
// §6.1 — Experience telemetry (fully mechanical)
// ─────────────────────────────────────────────────────────────────────────────

export type ExperienceBand = 'SMOOTH' | 'ACCEPTABLE' | 'STRAINED' | 'BROKEN-FEELING' | 'not_captured'

export interface ExperienceTelemetry {
  t_total_ms: number | 'not_captured'
  t_first_signal_ms: number | 'not_captured'
  tool_calls_n: number
  tool_errors_n: number
  retry_recoveries_n: number
  payload_kb_total: number
  truncation_events: number
  followups_needed: boolean | 'not_captured'
  experience_band: ExperienceBand
  friction_notes: string
  d6_relevant: boolean
}

const TRUNCATION_MARKERS = [/"truncated"\s*:\s*true/i, /"pages_total"\s*:\s*\d+/i, /pagination.*(cut|trim)/i]

export function captureExperienceTelemetry(transcript: NormalizedTranscript): ExperienceTelemetry {
  const calls = transcript.calls
  const tool_calls_n = calls.length
  const tool_errors_n = calls.filter((c) => Boolean(c.error)).length
  const retry_recoveries_n = calls.filter((c) => c.retried).length
  const payload_kb_total = calls.reduce((sum, c) => sum + Buffer.byteLength(c.result_raw ?? '', 'utf-8'), 0) / 1024
  const truncation_events = calls.filter((c) => TRUNCATION_MARKERS.some((p) => p.test(c.result_raw ?? ''))).length

  const hasTimestamps = calls.some((c) => c.t_start_ms != null)
  const t_total_ms =
    transcript.t_query_posed_ms != null && transcript.t_answer_complete_ms != null
      ? transcript.t_answer_complete_ms - transcript.t_query_posed_ms
      : hasTimestamps
        ? Math.max(...calls.map((c) => c.t_end_ms ?? 0)) - Math.min(...calls.map((c) => c.t_start_ms ?? 0))
        : 'not_captured'
  const t_first_signal_ms =
    transcript.t_first_signal_ms ?? (hasTimestamps ? Math.min(...calls.map((c) => c.t_start_ms ?? Infinity)) : 'not_captured')

  let experience_band: ExperienceBand
  if (t_total_ms === 'not_captured') {
    experience_band = 'not_captured'
  } else if (tool_errors_n > 0 && retry_recoveries_n === 0) {
    experience_band = 'BROKEN-FEELING'
  } else if (tool_errors_n > 0 || retry_recoveries_n > 1 || t_total_ms > 90_000) {
    experience_band = 'STRAINED'
  } else if (retry_recoveries_n === 1 || t_total_ms > 30_000) {
    experience_band = 'ACCEPTABLE'
  } else {
    experience_band = 'SMOOTH'
  }

  const frictionParts: string[] = []
  if (tool_errors_n > 0) frictionParts.push(`${tool_errors_n} tool error(s) visible in transcript`)
  if (truncation_events > 0) frictionParts.push(`${truncation_events} truncation/pagination artifact(s)`)
  if (t_total_ms !== 'not_captured' && t_total_ms > 60_000) frictionParts.push(`long wait (${Math.round(t_total_ms / 1000)}s total)`)

  return {
    t_total_ms,
    t_first_signal_ms,
    tool_calls_n,
    tool_errors_n,
    retry_recoveries_n,
    payload_kb_total: Math.round(payload_kb_total * 100) / 100,
    truncation_events,
    followups_needed: transcript.followups_needed ?? 'not_captured',
    experience_band,
    friction_notes: transcript.friction_notes ?? (frictionParts.length > 0 ? frictionParts.join('; ') : 'none observed'),
    d6_relevant: false, // set true by the caller when latency is traced to build/materialization state
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// §6.0 — Investigation track (I1–I5): raw ledger, mechanical where possible
// ─────────────────────────────────────────────────────────────────────────────

/** Structural markers §N.6/RS-4 serving surfaces use for escalation/lead affordances. */
const LEAD_FIELD_KEYS = [
  'drill_pointers',
  'escalation',
  'escalation_valve',
  'contradiction',
  'contradictions',
  'firing_yogas',
  'active_windows',
  'judgment_flags',
  'leads',
]

interface Lead {
  source_tool: string
  field: string
  value: unknown
}

/** Walks a parsed tool result for the known lead-bearing field names (I2's raw ledger). */
function extractLeadsFromResult(tool: string, raw: string): Lead[] {
  let parsed: unknown
  try {
    parsed = lenientParseJson(raw)
  } catch {
    return []
  }
  const leads: Lead[] = []
  const walk = (node: unknown, depth: number) => {
    if (depth > 12 || node == null || typeof node !== 'object') return
    if (Array.isArray(node)) {
      for (const item of node) walk(item, depth + 1)
      return
    }
    for (const [key, value] of Object.entries(node as Record<string, unknown>)) {
      if (LEAD_FIELD_KEYS.includes(key) && value != null && !(Array.isArray(value) && value.length === 0)) {
        leads.push({ source_tool: tool, field: key, value })
      }
      walk(value, depth + 1)
    }
  }
  walk(parsed, 0)
  return leads
}

export interface InvestigationLedger {
  leads_offered: Array<{ source_tool: string; field: string; summary: string }>
  leads_pursued: Array<{ source_tool: string; field: string; summary: string }>
  leads_ignored: Array<{ source_tool: string; field: string; summary: string }>
  tool_diversity_ratio: number // distinct tools / total calls — raw signal for I1
  rounds_with_new_info: number // raw signal for I3 (iterative deepening)
  evidence_fidelity: {
    // I5 raw signal: numeric/degree assertions in the final answer that do NOT appear anywhere
    // in retrieved tool results (the transcript-side twin of answer_eval.ts's fabrication scan).
    unsupported_numeric_claims: string[]
  }
}

export interface InvestigationTrack {
  ledger: InvestigationLedger
  I1_tool_reasoning: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; raw_signal: number }
  I2_lead_following: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; leads_pursued_ratio: number }
  I3_iterative_deepening: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; raw_signal: number }
  I4_coverage_judgment: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; benchmark_note: string }
  I5_evidence_fidelity: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; unsupported_claim_count: number }
}

function summarizeLeadValue(value: unknown): string {
  const s = typeof value === 'string' ? value : JSON.stringify(value)
  return s.length > 160 ? s.slice(0, 157) + '...' : s
}

export function captureInvestigationTrack(transcript: NormalizedTranscript): InvestigationTrack {
  const calls = transcript.calls
  const allLeads = calls.flatMap((c) => extractLeadsFromResult(bareToolName(c.tool), c.result_raw ?? ''))

  // A lead is "pursued" if a LATER call's tool or arguments plausibly follows it — heuristic:
  // the lead's stringified value shares a distinguishing token (>=6 chars, alnum) with a later
  // call's tool name or argument values. This is intentionally a coarse, declared heuristic
  // (raw signal for a human/Opus judge), not a claim of certainty.
  const laterCallText = (fromIndex: number) =>
    calls
      .slice(fromIndex + 1)
      .map((c) => `${c.tool} ${JSON.stringify(c.arguments)}`)
      .join(' ')

  const leads_offered: InvestigationLedger['leads_offered'] = []
  const leads_pursued: InvestigationLedger['leads_pursued'] = []
  const leads_ignored: InvestigationLedger['leads_ignored'] = []

  for (const lead of allLeads) {
    const callIdx = calls.findIndex((c) => bareToolName(c.tool) === lead.source_tool)
    const entry = { source_tool: lead.source_tool, field: lead.field, summary: summarizeLeadValue(lead.value) }
    leads_offered.push(entry)
    const tokens = summarizeLeadValue(lead.value)
      .match(/[A-Za-z0-9_]{6,}/g)
      ?.slice(0, 5) ?? []
    const rest = laterCallText(callIdx)
    const pursued = tokens.some((t) => rest.includes(t))
    ;(pursued ? leads_pursued : leads_ignored).push(entry)
  }

  const distinctTools = new Set(calls.map((c) => bareToolName(c.tool))).size
  const tool_diversity_ratio = calls.length > 0 ? distinctTools / calls.length : 0

  // Rounds-with-new-info: count call-boundary transitions where the NEXT call's arguments
  // reference a token that only appeared in a PRIOR call's result (evidence retrieval actually
  // informed the next call, i.e. multi-hop, not blind fetch-and-write).
  let rounds_with_new_info = 0
  for (let i = 1; i < calls.length; i++) {
    const priorResultTokens = new Set(
      (calls[i - 1].result_raw ?? '').match(/[A-Za-z0-9_]{8,}/g)?.slice(0, 200) ?? [],
    )
    const thisArgsText = JSON.stringify(calls[i].arguments)
    if ([...priorResultTokens].some((t) => thisArgsText.includes(t))) rounds_with_new_info++
  }

  const finalAnswer = transcript.final_answer ?? ''
  const allResultText = calls.map((c) => c.result_raw ?? '').join('\n')
  const degreeClaims = finalAnswer.match(/\b\d{1,2}°\s*\d{0,2}'?\s*\w*/g) ?? []
  const unsupported_numeric_claims = degreeClaims.filter((claim) => !allResultText.includes(claim.split('°')[0]))

  const ledger: InvestigationLedger = {
    leads_offered,
    leads_pursued,
    leads_ignored,
    tool_diversity_ratio,
    rounds_with_new_info,
    evidence_fidelity: { unsupported_numeric_claims },
  }

  return {
    ledger,
    I1_tool_reasoning: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR', raw_signal: tool_diversity_ratio },
    I2_lead_following: {
      judgment: null,
      judged_by: 'PENDING_OPUS_AUDITOR',
      leads_pursued_ratio: leads_offered.length > 0 ? leads_pursued.length / leads_offered.length : 1,
    },
    I3_iterative_deepening: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR', raw_signal: rounds_with_new_info },
    I4_coverage_judgment: {
      judgment: null,
      judged_by: 'PENDING_OPUS_AUDITOR',
      benchmark_note: 'cross-read against evals/k2/consumption_grader.ts consumption_ratio for the same transcript',
    },
    I5_evidence_fidelity: {
      judgment: null,
      judged_by: 'PENDING_OPUS_AUDITOR',
      unsupported_claim_count: unsupported_numeric_claims.length,
    },
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// §6.2 — Vidhi planner track (V1–V5): raw ledger against an optional benchmark
// ─────────────────────────────────────────────────────────────────────────────

export interface VidhiReplayInput {
  /** The `plan_retrieval` (or `intent_classify`) response, captured live by a controlled replay
   * per the Darpana design (§6.2): "the auditor re-submits each battery query verbatim to
   * intent_classify + plan_retrieval and grades the returned plan directly." This module does
   * not itself call those tools (that is the harness/replay driver's job) — it accepts the
   * already-captured plan JSON and extracts the raw ledger from it. */
  intent_classify_result?: unknown
  plan_retrieval_result?: unknown
  /** Astrological aspects this question BEARS on, e.g. from the sealed harness's own
   * required_concepts list or a domain benchmark — the denominator for aspects_missed. */
  aspects_required?: string[]
}

export interface VidhiLedger {
  aspects_required: string[]
  aspects_planned: string[]
  aspects_missed: string[]
  plan_tool_names: string[]
  plan_followed: boolean | 'not_captured' // did the transcript's actual calls match plan_tool_names?
  off_plan_rescue: boolean | 'not_captured' // did the transcript call tools the plan never named?
}

export interface VidhiTrack {
  ledger: VidhiLedger
  V1_intent: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR' }
  V2_tool_selection: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; plan_tool_count: number }
  V3_astrological_coverage: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; aspects_missed_count: number }
  V4_instruction_quality: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR' }
  V5_plan_sufficiency: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; off_plan_rescue: boolean | 'not_captured' }
}

/** Best-effort tool-name extraction out of a plan_retrieval-shaped JSON payload — looks for any
 * string field that resembles a registered capability name (snake_case, contains `_get`,
 * `_query`, `assess_`, etc.) without assuming an exact plan schema (the plan schema is owned by
 * a different lane; this stays structurally tolerant on purpose). */
function extractToolNamesFromPlan(plan: unknown): string[] {
  const found = new Set<string>()
  const TOOL_LIKE = /^[a-z][a-z0-9_]*(_get|_query|_compute|_list|_read|_ask)$|^assess_[a-z]+$|^judgment_query$/
  const walk = (node: unknown, depth: number) => {
    if (depth > 12 || node == null) return
    if (typeof node === 'string' && TOOL_LIKE.test(node)) {
      found.add(node)
      return
    }
    if (Array.isArray(node)) {
      for (const item of node) walk(item, depth + 1)
      return
    }
    if (typeof node === 'object') {
      for (const value of Object.values(node as Record<string, unknown>)) walk(value, depth + 1)
    }
  }
  walk(plan, 0)
  return [...found]
}

export function captureVidhiTrack(transcript: NormalizedTranscript, replay?: VidhiReplayInput): VidhiTrack {
  const aspects_required = replay?.aspects_required ?? []
  const planText = JSON.stringify(replay?.plan_retrieval_result ?? '') + JSON.stringify(replay?.intent_classify_result ?? '')
  const aspects_planned = aspects_required.filter((a) => planText.toLowerCase().includes(a.toLowerCase()))
  const aspects_missed = aspects_required.filter((a) => !aspects_planned.includes(a))
  const plan_tool_names = replay?.plan_retrieval_result ? extractToolNamesFromPlan(replay.plan_retrieval_result) : []

  const actualTools = new Set(transcript.calls.map((c) => bareToolName(c.tool)))
  const plan_followed =
    plan_tool_names.length === 0 ? 'not_captured' : plan_tool_names.every((t) => actualTools.has(t))
  const off_plan_rescue =
    plan_tool_names.length === 0
      ? 'not_captured'
      : [...actualTools].some((t) => !plan_tool_names.includes(t))

  const ledger: VidhiLedger = {
    aspects_required,
    aspects_planned,
    aspects_missed,
    plan_tool_names,
    plan_followed,
    off_plan_rescue,
  }

  return {
    ledger,
    V1_intent: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR' },
    V2_tool_selection: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR', plan_tool_count: plan_tool_names.length },
    V3_astrological_coverage: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR', aspects_missed_count: aspects_missed.length },
    V4_instruction_quality: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR' },
    V5_plan_sufficiency: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR', off_plan_rescue },
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// §6.3 — Retrieval-plane track (RE1–RE5): mechanical structural checks
// ─────────────────────────────────────────────────────────────────────────────

const V3_ENVELOPE_FIELDS = ['verdict', 'ranking_basis', 'grounding', 'drill_pointers', 'judgment_flags']
const FALLBACK_MARKERS = [/"fallback"\s*:\s*true/i, /"degraded"\s*:\s*true/i, /fallback[_-]?face/i]
const DENSITY_FIELDS = ['hardFloor', 'catalog_only_rows_in_page', 'catalog_only_note', 'empty_reason', 'density_contract']
const FACT_ID_PATTERN = /^[0-9a-f]{16}$/i

export interface RetrievalPlaneLedger {
  fallback_taken: Array<{ tool: string; trigger: string }>
  envelope_conformance_by_call: Array<{ tool: string; fields_present: string[]; fields_missing: string[] }>
  density_markers_present: Array<{ tool: string; markers: string[] }>
  drill_pointer_resolvable_count: number // cross-read with I2's leads_pursued
  drill_pointer_decorative_count: number // leads offered whose target tool was NEVER called at all
  payload_integrity_issues: string[] // malformed fact_ids, truncation without empty_reason, etc.
}

export interface RetrievalPlaneTrack {
  ledger: RetrievalPlaneLedger
  RE1_routing_fidelity: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; fallback_count: number }
  RE2_envelope_conformance: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; calls_with_full_envelope_ratio: number }
  RE3_density_as_experienced: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; calls_with_density_markers_ratio: number }
  RE4_drill_pointer_efficacy: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; resolvable_ratio: number }
  RE5_payload_integrity: { judgment: null; judged_by: 'PENDING_OPUS_AUDITOR'; issue_count: number }
}

export function captureRetrievalPlaneTrack(
  transcript: NormalizedTranscript,
  investigation: InvestigationTrack,
): RetrievalPlaneTrack {
  const calls = transcript.calls
  const fallback_taken: RetrievalPlaneLedger['fallback_taken'] = []
  const envelope_conformance_by_call: RetrievalPlaneLedger['envelope_conformance_by_call'] = []
  const density_markers_present: RetrievalPlaneLedger['density_markers_present'] = []
  const payload_integrity_issues: string[] = []

  for (const c of calls) {
    const tool = bareToolName(c.tool)
    const raw = c.result_raw ?? ''
    const trigger = FALLBACK_MARKERS.find((p) => p.test(raw))
    if (trigger) fallback_taken.push({ tool, trigger: trigger.source })

    let parsedKeys: Set<string> | null = null
    try {
      const parsed = lenientParseJson<unknown>(raw)
      const keys = new Set<string>()
      const walk = (node: unknown, depth: number) => {
        if (depth > 8 || node == null || typeof node !== 'object') return
        if (Array.isArray(node)) {
          for (const item of node) walk(item, depth + 1)
          return
        }
        for (const k of Object.keys(node as Record<string, unknown>)) keys.add(k)
        for (const v of Object.values(node as Record<string, unknown>)) walk(v, depth + 1)
      }
      walk(parsed, 0)
      parsedKeys = keys
    } catch {
      payload_integrity_issues.push(`${tool}: result_raw is not valid JSON (structural checks skipped for this call)`)
    }

    if (parsedKeys) {
      const present = V3_ENVELOPE_FIELDS.filter((f) => parsedKeys!.has(f))
      const missing = V3_ENVELOPE_FIELDS.filter((f) => !parsedKeys!.has(f))
      envelope_conformance_by_call.push({ tool, fields_present: present, fields_missing: missing })

      const densityHit = DENSITY_FIELDS.filter((f) => parsedKeys!.has(f))
      if (densityHit.length > 0) density_markers_present.push({ tool, markers: densityHit })

      // fact_id well-formedness: any string value under a key literally named "fact_id" or
      // "fact_ids" that does NOT match the 16-hex-char shape used across this codebase.
      const fids: string[] = []
      const collectFids = (node: unknown, key: string | null, depth: number) => {
        if (depth > 10 || node == null) return
        if (Array.isArray(node)) {
          for (const item of node) collectFids(item, key, depth + 1)
          return
        }
        if (typeof node === 'object') {
          for (const [k, v] of Object.entries(node as Record<string, unknown>)) collectFids(v, k, depth + 1)
          return
        }
        if (typeof node === 'string' && (key === 'fact_id' || key === 'fact_ids')) fids.push(node)
      }
      collectFids(lenientParseJsonSafe(raw), null, 0)
      for (const fid of fids) {
        if (!FACT_ID_PATTERN.test(fid)) {
          payload_integrity_issues.push(`${tool}: malformed fact_id "${fid}"`)
        }
      }
    }
  }

  const leadsWithTarget = investigation.ledger.leads_offered
  const drill_pointer_resolvable_count = investigation.ledger.leads_pursued.length
  const drill_pointer_decorative_count = investigation.ledger.leads_ignored.length

  const calls_with_full_envelope_ratio =
    envelope_conformance_by_call.length > 0
      ? envelope_conformance_by_call.filter((c) => c.fields_missing.length === 0).length / envelope_conformance_by_call.length
      : 0
  const calls_with_density_markers_ratio =
    calls.length > 0 ? density_markers_present.length / calls.length : 0

  const ledger: RetrievalPlaneLedger = {
    fallback_taken,
    envelope_conformance_by_call,
    density_markers_present,
    drill_pointer_resolvable_count,
    drill_pointer_decorative_count,
    payload_integrity_issues,
  }

  return {
    ledger,
    RE1_routing_fidelity: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR', fallback_count: fallback_taken.length },
    RE2_envelope_conformance: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR', calls_with_full_envelope_ratio },
    RE3_density_as_experienced: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR', calls_with_density_markers_ratio },
    RE4_drill_pointer_efficacy: {
      judgment: null,
      judged_by: 'PENDING_OPUS_AUDITOR',
      resolvable_ratio:
        leadsWithTarget.length > 0 ? drill_pointer_resolvable_count / leadsWithTarget.length : 1,
    },
    RE5_payload_integrity: { judgment: null, judged_by: 'PENDING_OPUS_AUDITOR', issue_count: payload_integrity_issues.length },
  }
}

function lenientParseJsonSafe(raw: string): unknown {
  try {
    return lenientParseJson(raw)
  } catch {
    return null
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Combined capture
// ─────────────────────────────────────────────────────────────────────────────

export interface InstrumentationCapture {
  experience: ExperienceTelemetry
  investigation: InvestigationTrack
  vidhi: VidhiTrack
  retrieval_plane: RetrievalPlaneTrack
}

export function captureInstrumentation(
  transcript: NormalizedTranscript,
  vidhiReplay?: VidhiReplayInput,
): InstrumentationCapture {
  const experience = captureExperienceTelemetry(transcript)
  const investigation = captureInvestigationTrack(transcript)
  const vidhi = captureVidhiTrack(transcript, vidhiReplay)
  const retrieval_plane = captureRetrievalPlaneTrack(transcript, investigation)
  return { experience, investigation, vidhi, retrieval_plane }
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────

function isMain(): boolean {
  return process.argv[1] != null && import.meta.url === `file://${process.argv[1]}`
}

if (isMain()) {
  const [transcriptPath] = process.argv.slice(2)
  if (!transcriptPath) {
    console.error('Usage: npx tsx evals/k2/instrumentation_tracks.ts <transcript.json> [--vidhi-replay <file>]')
    process.exit(1)
  }
  const rest = process.argv.slice(3)
  const replayFlag = rest.indexOf('--vidhi-replay')
  const vidhiReplay = replayFlag >= 0 ? (JSON.parse(readFileSync(rest[replayFlag + 1], 'utf-8')) as VidhiReplayInput) : undefined
  const transcript = loadTranscript(transcriptPath)
  const capture = captureInstrumentation(transcript, vidhiReplay)
  console.log(JSON.stringify(capture, null, 2))
}
