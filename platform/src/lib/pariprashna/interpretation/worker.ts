/**
 * pariprashna/interpretation/worker.ts — the REAL structured-output call
 * (lane G3-B, PPR-02).
 *
 * Follows the EXACT cross-provider structured-completion pattern this
 * codebase already uses for a single-shot, non-agentic LLM call:
 * `runAdapter(QueryRequest) -> ModelInteraction` with a JSON Schema on
 * `responseSchema`, `interaction.finalText` parsed as JSON and Zod-shape
 * checked, with ONE repair-retry on invalid output — the same discipline
 * `lib/pipeline/pipeline_planner.ts`'s `tryBuildPlan`/repair-retry uses for
 * the plan JSON. `callType: 'worker'` is the SAME CallType this lane's own
 * `summaries/worker.ts` (PB-2/M-3) already established for "title
 * generation, history summarization, any call where minimal latency and
 * minimal cost dominate" (the registry's own docstring) — this is exactly
 * that kind of call, reused rather than a new CallType (adding one would
 * require populating `STACK_ROUTING` for every stack in
 * `lib/models/registry.ts`, outside this lane's `may_touch`).
 *
 * NEVER fabricates candidates client-side: every candidate/rationale/
 * falsifier a reader can eventually see came out of the model's own JSON
 * response. A judgment the call could not produce >=3 genuinely distinct
 * candidates for becomes an explicit WAIVER with a real reason — never a
 * padded-out near-duplicate set (PPR-02's own words: "or an explicit waiver
 * whose rate is monitored").
 */
import 'server-only'

import type { JSONSchema7 } from 'json-schema'

import { runAdapter } from '@/lib/adapters/run_adapter'
import type { QueryRequest } from '@/lib/adapters/types'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import { DEFAULT_STACK_ID } from '@/lib/models/registry'

import type { SignificantJudgment } from './detect'
import { MIN_INTERPRETATION_CANDIDATES, type InterpretationSetEntry } from './schema'

// ---------------------------------------------------------------------------
// The JSON Schema the structured-output call requests.
// ---------------------------------------------------------------------------

const RESPONSE_SCHEMA: JSONSchema7 = {
  type: 'object',
  properties: {
    sets: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          judgment_id: { type: 'string' },
          status: { type: 'string', enum: ['generated', 'waived'] },
          candidates: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                reading: { type: 'string' },
                rationale: { type: 'string' },
              },
              required: ['reading', 'rationale'],
            },
          },
          selected_index: { type: 'number' },
          selected_rationale: { type: 'string' },
          falsifier: { type: 'string' },
          waiver_reason: { type: 'string' },
        },
        required: ['judgment_id', 'status'],
      },
    },
  },
  required: ['sets'],
}

/** The raw per-judgment shape the model returns, before this module's own
 *  structural validation (`coerceEntry`) — NOT trusted as-is. */
interface LlmSetRaw {
  judgment_id: string
  status: 'generated' | 'waived'
  candidates?: Array<{ reading: string; rationale: string }>
  selected_index?: number
  selected_rationale?: string
  falsifier?: string
  waiver_reason?: string
}

function systemPrompt(): string {
  return (
    'You are the interpretation-adjudication step of a Jyotish reading system. ' +
    'For each judgment listed below, produce AT LEAST 3 genuinely DISTINCT candidate ' +
    'readings — different interpretive conclusions a competent astrologer could ' +
    'reasonably draw from the same evidence. They must be substantively different ' +
    'conclusions, never 3 rephrasings of one conclusion. ' +
    'Then select the reading you find strongest, give a rationale for why it beats ' +
    'the others, and state a FALSIFIER: what would have to be true or observed for ' +
    'the selected reading to be wrong. ' +
    'If — and only if — you genuinely cannot produce 3 truly distinct candidates for ' +
    'a judgment (the domain is too narrow, or the evidence supports only one reading), ' +
    'mark that judgment status="waived" and give a specific, non-generic waiver_reason. ' +
    'Do NOT pad with near-duplicate candidates to reach 3 — an honest waiver is required ' +
    'whenever that would happen. ' +
    'Never invent facts not implied by the judgment text. ' +
    'Respond with ONLY a JSON object matching the schema — no prose, no markdown fences, ' +
    'nothing before or after the JSON.'
  )
}

function userMessage(judgments: readonly SignificantJudgment[]): string {
  const lines = judgments.map(
    (j) => `judgment_id: ${j.judgment_id}\ncategory: ${j.category}\ntext: ${j.claim_text}`,
  )
  return `Judgments:\n\n${lines.join('\n\n---\n\n')}`
}

/** Verbatim balanced-brace extractor (same routine as
 *  `pipeline_planner.ts`'s `extractFirstJsonObject`) — some providers
 *  append explanatory text after the closing `}`. */
function extractFirstJsonObject(text: string): string {
  const start = text.indexOf('{')
  if (start === -1) return text
  let depth = 0
  let inString = false
  let escaped = false
  for (let i = start; i < text.length; i++) {
    const ch = text[i]
    if (escaped) {
      escaped = false
      continue
    }
    if (ch === '\\' && inString) {
      escaped = true
      continue
    }
    if (ch === '"') {
      inString = !inString
      continue
    }
    if (inString) continue
    if (ch === '{') depth++
    else if (ch === '}') {
      depth--
      if (depth === 0) return text.slice(start, i + 1)
    }
  }
  return text
}

// ---------------------------------------------------------------------------
// G3BC hardening defect 5. Minimal, STRUCTURAL, cheap checks — deliberately
// NOT a full NLP quality/similarity system. These close the two EXACT
// constructions the adversary demonstrated pass validation today
// ("If I'm wrong, I'm wrong." / three reworded-but-identical candidates) and
// raise the bar generally, but they do not and cannot guarantee every
// vacuous falsifier or every near-duplicate candidate set is caught — this
// is a floor-raise on top of the prompt's own instructions, not a complete
// quality guarantee. A judgment that fails either check degrades to an
// honest WAIVER (never silently passed through, never silently dropped).
// ---------------------------------------------------------------------------

/** Exact-phrase stock vacuities the adversary demonstrated pass today.
 *  Matched case-insensitively against the TRIMMED falsifier text. Not
 *  exhaustive by design (see module note above) — a denylist of known-bad
 *  constructions, not a classifier. */
const VACUOUS_FALSIFIER_PHRASES: readonly string[] = [
  "if i'm wrong, i'm wrong",
  'if i am wrong, i am wrong',
  'maybe',
  "it's possible i'm mistaken",
  'it is possible i am mistaken',
]

/** A falsifier under this many words cannot structurally carry a real,
 *  checkable condition ("what would have to be true/observed") — a
 *  conservative floor, not a claim that anything longer is automatically
 *  substantive. */
const MIN_FALSIFIER_WORD_COUNT = 5

/** Structural (not semantic) vacuous-falsifier check — see module note. */
function isVacuousFalsifier(falsifier: string): boolean {
  const trimmed = falsifier.trim()
  // Strip trailing sentence punctuation before the stock-phrase compare —
  // "If I'm wrong, I'm wrong." (the adversary's exact construction, with a
  // period) must match the same denylist entry as the bare phrase.
  const normalized = trimmed.toLowerCase().replace(/[.!?]+$/, '')
  if (VACUOUS_FALSIFIER_PHRASES.includes(normalized)) return true
  const wordCount = trimmed.split(/\s+/).filter(Boolean).length
  if (wordCount < MIN_FALSIFIER_WORD_COUNT) return true
  return false
}

/** Normalize to a lowercase token set for the cheap distinctness check —
 *  strips punctuation, collapses whitespace. Deliberately crude (see module
 *  note): this is a shared-token-ratio heuristic, not semantic similarity. */
function tokenSet(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s]/gu, ' ')
      .split(/\s+/)
      .filter(Boolean),
  )
}

/** Shared-token overlap ratio (Jaccard-like, over the SMALLER set's size so
 *  a short candidate fully contained in a longer one still reads as
 *  near-duplicate). >= this ratio is treated as "not genuinely distinct". */
const CANDIDATE_OVERLAP_THRESHOLD = 0.8

function overlapRatio(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 || b.size === 0) return 0
  let shared = 0
  for (const tok of a) if (b.has(tok)) shared++
  return shared / Math.min(a.size, b.size)
}

/** Structural (not semantic) distinctness check across a candidate set — see
 *  module note. Flags the set as non-distinct if ANY pair of candidates'
 *  `reading` texts overlap at or above `CANDIDATE_OVERLAP_THRESHOLD`. */
function hasNearDuplicateCandidates(candidates: readonly { reading: string }[]): boolean {
  const sets = candidates.map((c) => tokenSet(c.reading))
  for (let i = 0; i < sets.length; i++) {
    for (let j = i + 1; j < sets.length; j++) {
      if (overlapRatio(sets[i], sets[j]) >= CANDIDATE_OVERLAP_THRESHOLD) return true
    }
  }
  return false
}

function waiverEntry(j: SignificantJudgment, reason: string): InterpretationSetEntry {
  return {
    judgment_id: j.judgment_id,
    category: j.category,
    status: 'waived',
    detection_basis: j.detection_basis,
    candidates: null,
    selected_index: null,
    selected_rationale: null,
    falsifier: null,
    waiver_reason: reason,
  }
}

/**
 * Structurally validate + coerce one raw model entry. Returns `null` when
 * the model's own answer for this judgment fails the PPR-02 contract (too
 * few candidates, an out-of-range selection, a claimed-waived entry with no
 * reason, …) — the caller turns a `null` into an honest waiver, never a
 * best-effort guess at what the model "probably meant".
 */
function coerceEntry(j: SignificantJudgment, raw: LlmSetRaw): InterpretationSetEntry | null {
  if (raw.status === 'waived') {
    const reason = raw.waiver_reason?.trim()
    if (!reason) return null
    return waiverEntry(j, reason)
  }
  const candidates = raw.candidates ?? []
  if (candidates.length < MIN_INTERPRETATION_CANDIDATES) return null
  if (candidates.some((c) => !c.reading?.trim() || !c.rationale?.trim())) return null
  // Defect 5(b): reject a candidate set with any near-duplicate pair — a
  // structural floor-raise, not a semantic guarantee (see module note above
  // `waiverEntry`). `coerceEntry` returning `null` here is turned into an
  // honest waiver by the caller, same as every other structural-validation
  // failure this function already produces.
  if (hasNearDuplicateCandidates(candidates)) return null
  const idx = raw.selected_index
  if (idx === undefined || !Number.isInteger(idx) || idx < 0 || idx >= candidates.length) return null
  const selectedRationale = raw.selected_rationale?.trim()
  const falsifier = raw.falsifier?.trim()
  if (!selectedRationale || !falsifier) return null
  // Defect 5(a): reject a structurally-vacuous falsifier (too short, or a
  // known stock non-answer) — same structural-floor-raise discipline.
  if (isVacuousFalsifier(falsifier)) return null
  return {
    judgment_id: j.judgment_id,
    category: j.category,
    status: 'generated',
    detection_basis: j.detection_basis,
    candidates: candidates.map((c) => ({ reading: c.reading.trim(), rationale: c.rationale.trim() })),
    selected_index: idx,
    selected_rationale: selectedRationale,
    falsifier,
    waiver_reason: null,
  }
}

async function callOnce(
  judgments: readonly SignificantJudgment[],
  modelId: string,
  repairNote?: string,
): Promise<Map<string, LlmSetRaw>> {
  const req: QueryRequest = {
    callType: 'worker',
    modelOverride: { modelId },
    systemPrompt: systemPrompt(),
    messages: [
      { role: 'user', content: userMessage(judgments) },
      ...(repairNote ? [{ role: 'user' as const, content: repairNote }] : []),
    ],
    temperature: 0,
    disableSdkRetry: true,
    reasoning: 'disable',
    responseSchema: RESPONSE_SCHEMA,
  }
  const interaction = await runAdapter(req)
  const rawText = interaction.finalText ?? ''
  if (!rawText.trim()) throw new Error('interpretation-sets call returned no text output')
  const fenceStripped = rawText.replace(/^```(?:json)?\s*/im, '').replace(/\s*```\s*$/m, '').trim()
  const jsonText = extractFirstJsonObject(fenceStripped)
  const parsed = JSON.parse(jsonText) as { sets?: LlmSetRaw[] }
  const map = new Map<string, LlmSetRaw>()
  for (const s of parsed.sets ?? []) {
    if (s && typeof s.judgment_id === 'string') map.set(s.judgment_id, s)
  }
  return map
}

/** Injectable seam for tests — defaults to the real `runAdapter`-backed call. */
export type InterpretationLlmCaller = (
  judgments: readonly SignificantJudgment[],
) => Promise<Map<string, LlmSetRaw>>

async function defaultCaller(judgments: readonly SignificantJudgment[]): Promise<Map<string, LlmSetRaw>> {
  const modelId = await getEffectiveModel(DEFAULT_STACK_ID, 'worker', 'primary')
  try {
    return await callOnce(judgments, modelId)
  } catch (err) {
    console.warn(
      '[pariprashna/interpretation] structured-output call failed schema/parse validation, retrying once:',
      err,
    )
    return callOnce(
      judgments,
      modelId,
      'Your previous response was not valid JSON matching the required schema. Reply again with ' +
        'ONLY the JSON object — no prose, no markdown fences, nothing before or after the JSON.',
    )
  }
}

/**
 * Generate interpretation sets for every SIGNIFICANT judgment. NEVER throws:
 * a judgment the call could not produce a valid entry for — because the
 * whole call failed twice, the model omitted that judgment_id, or the
 * model's own answer failed structural validation — becomes an honest
 * waiver with a real, specific reason, never a fabricated set and never a
 * silently-dropped judgment (every input judgment maps to exactly one
 * output entry, by construction).
 */
export async function generateInterpretationSets(
  judgments: readonly SignificantJudgment[],
  caller: InterpretationLlmCaller = defaultCaller,
): Promise<InterpretationSetEntry[]> {
  if (judgments.length === 0) return []

  let byId: Map<string, LlmSetRaw>
  try {
    byId = await caller(judgments)
  } catch (err) {
    console.error(
      '[pariprashna/interpretation] structured-output call failed (incl. repair retry) — ' +
        'waiving every significant judgment this turn:',
      err,
    )
    return judgments.map((j) => waiverEntry(j, 'interpretation-set generation call failed'))
  }

  return judgments.map((j) => {
    const raw = byId.get(j.judgment_id)
    if (!raw) return waiverEntry(j, 'model produced no entry for this judgment_id')
    const entry = coerceEntry(j, raw)
    return (
      entry ??
      waiverEntry(
        j,
        "model's entry for this judgment failed structural validation (too few/invalid candidates, or an incoherent waiver)",
      )
    )
  })
}
