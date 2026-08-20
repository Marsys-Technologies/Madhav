/**
 * explain.ts — ṢAḌ-DARŚANA W0.4: `kala_explain_get` (SHAD_DARSHANA_BRIEF_v2_0.md §3 W0.4 ·
 * §2 file map; design authority KALA_SIX_VIEWS_DESIGN_v1_0.md §6 / v2_0.md §E "EXPLAIN").
 * ==========================================================================
 * VIEW 6 — EXPLAIN: "Why do you say that?"
 *
 * W0 SCOPE (thin facade over EXISTING substrate — no new computation, per brief §3 W0.4):
 * the v1.0 design's full EXPLAIN ("provenance graph materialized at build time... window →
 * predicates → signals → natal facts") needs the field-write provenance edges (item 11) that
 * do not exist until W2. What already exists TODAY that answers "why do you say that?" for a
 * temporal claim is `pact_query` (registry_bridge.ts) — the PACT protocol as one chained
 * investigation ("promise in the rashi → confirmation in the varga → activation in the dasha
 * → trigger in the transit"), which HALTS HONESTLY at the first denied stage and names it.
 * That halting stage IS v1.0 §6.2's "the weakest link — the least-attested edge, named
 * honestly" for this substrate: the stage the chain currently rests on. This facade wraps
 * `marsys://tool/L-PACT/pact_query` — the same capability `pact_query` calls — and re-serves
 * it through the elevated `kala_envelope.ts` shape.
 *
 * W3K Lane 2 (G-5) ADDED the Law-2 school voice: KP now reads the SAME window the PACT
 * chain reads and either concurs with it or dissents from it, tagged `school: 'kp'` and
 * carried on the envelope's existing `reading.dissent` / `reading.evidence` shapes (the
 * `ArgumentDissent.source` field was already documented with 'KP sub-lord clock' as its
 * worked example). The verdict logic is `lib/kp_school_voice.ts`; this file only fetches
 * and wires. When the KP substrate is absent for a chart the coverage entry stays
 * `honest_empty` with the specific missing fact_category named — never a silent
 * "no dissent found", which would be a green light with no detector behind it (§N.8).
 *
 * NOT YET BUILT (honestly flagged via coverage, never silently omitted per B.10):
 * the classical-citation join (item 11, chain link → śāstra passage, EXPLAIN's "pedagogy
 * mode") and the counterfactual mode (E6, "without the vedha this grades one tier higher").
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'

// ── Item 34: Contrastive field-diff (serving layer) ──────────────────────────

/**
 * A minimal slice of a `kala_field_windows` row carrying the fields needed
 * for a field-diff computation. Serves as input to `computeFieldDiff`.
 * This is the TypeScript counterpart to stage65_insights.py's `InsightWindow`
 * slice — only what the diff algorithm needs, no more.
 */
export interface FieldWindowSlice {
  window_id: string
  event_class: string
  lambda_peak: number
  fact_ids: string[]
}

/** A row in the `new_windows` or `closed_windows` lists. */
export interface FieldDiffWindowRow {
  window_id: string
  event_class: string
  fact_ids: string[]
}

/** A row in the `intensified_windows` or `weakened_windows` lists. */
export interface FieldDiffChangedRow extends FieldDiffWindowRow {
  delta_ln_lambda: number
}

export interface FieldDiffResult {
  new_windows: FieldDiffWindowRow[]
  closed_windows: FieldDiffWindowRow[]
  intensified_windows: FieldDiffChangedRow[]
  weakened_windows: FieldDiffChangedRow[]
}

const CONTRAST_MIN_DELTA_LN_LAMBDA = 0.5

/**
 * Item 34 (W3): compute the contrastive field diff between two window sets.
 *
 * `current` is the present set of field windows; `baseline` is the reference
 * point (last month, last year, a pinned field_snapshot_id, another option).
 * Both are lists of `FieldWindowSlice` — the caller resolves the baseline.
 *
 * Returns:
 * - `new_windows`: present in current but absent from baseline (by window_id).
 * - `closed_windows`: present in baseline but absent from current.
 * - `intensified_windows`: present in both; Δln λ > threshold (lambda rose).
 * - `weakened_windows`: present in both; Δln λ < −threshold (lambda fell).
 *
 * Anti-symmetry: computeFieldDiff(A, B).new_windows window_ids ===
 *                computeFieldDiff(B, A).closed_windows window_ids.
 */
export function computeFieldDiff(
  current: FieldWindowSlice[],
  baseline: FieldWindowSlice[],
  lambdaThreshold: number = CONTRAST_MIN_DELTA_LN_LAMBDA,
): FieldDiffResult {
  const currentById = new Map(current.map((w) => [w.window_id, w]))
  const baselineById = new Map(baseline.map((w) => [w.window_id, w]))

  const currentIds = new Set(currentById.keys())
  const baselineIds = new Set(baselineById.keys())

  const newWindows: FieldDiffWindowRow[] = [...currentIds]
    .filter((id) => !baselineIds.has(id))
    .sort()
    .map((id) => {
      const w = currentById.get(id)!
      return { window_id: id, event_class: w.event_class, fact_ids: [...w.fact_ids] }
    })

  const closedWindows: FieldDiffWindowRow[] = [...baselineIds]
    .filter((id) => !currentIds.has(id))
    .sort()
    .map((id) => {
      const w = baselineById.get(id)!
      return { window_id: id, event_class: w.event_class, fact_ids: [...w.fact_ids] }
    })

  const intensifiedWindows: FieldDiffChangedRow[] = []
  const weakenedWindows: FieldDiffChangedRow[] = []

  const sharedIds = [...currentIds].filter((id) => baselineIds.has(id)).sort()
  for (const id of sharedIds) {
    const wCur = currentById.get(id)!
    const wBase = baselineById.get(id)!
    if (wBase.lambda_peak <= 0 || wCur.lambda_peak <= 0) continue
    const deltaLn = Math.log(wCur.lambda_peak / wBase.lambda_peak)
    const row: FieldDiffChangedRow = {
      window_id: id,
      event_class: wCur.event_class,
      fact_ids: [...wCur.fact_ids],
      delta_ln_lambda: deltaLn,
    }
    if (deltaLn > lambdaThreshold) {
      intensifiedWindows.push(row)
    } else if (-deltaLn > lambdaThreshold) {
      weakenedWindows.push(row)
    }
  }

  return {
    new_windows: newWindows,
    closed_windows: closedWindows,
    intensified_windows: intensifiedWindows,
    weakened_windows: weakenedWindows,
  }
}
import {
  makeKalaEnvelope,
  resolveFieldSnapshot,
  pointerTo,
  noLeverPointer,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  buildKalaFreshness,
  fetchCalibrationMaturity,
  type ArgumentReading,
  type ArgumentEvidence,
  type KalaCoverageEntry,
  type TriPlanePointers,
  type KalaDensityContract,
  type QuestionFrame,
  type ArgumentDissent,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import {
  buildKpSchoolVoice,
  parseKpHouseLadder,
  KP_SCHOOL_LABEL,
  type KpSchoolVoice,
  type KpRunningPeriod,
} from '../../lib/kp_school_voice.js'
import { callKalaRegistryCap, unwrapKalaPayload, kalaBudgetedDualOutput, kalaErrorOutput } from './shared.js'
import { resolveChartFactsAyanamsha } from '../../lib/ayanamsha.js'
// F-73: marsys://tool/L4/gochara_forecast_get was never backed by a registered
// capability (no layers/*/index.ts entry exists for it) — every call 404'd silently,
// forcing A5's gochara agreement to 'insufficient_data' unconditionally. The real logic
// already lives in this same platform-mcp package as a plain exported function; call it
// directly instead of round-tripping through the registry/HTTP capability system.
import { computeGocharaForecast } from '../retrieval/register_gochara_windows.js'
// GA-5 review finding on #1390: computeGocharaForecast is called IN-PROCESS, bypassing
// registerGocharaForecastTool's own remoteAuthorize(principal, chart_id) entitlement gate
// (that gate lives in the tool wrapper, not inside computeGocharaForecast itself) --
// unlike the registry/HTTP path this replaces, which enforced per-call authorizeChartAccess
// for every request. Re-gate explicitly at this call site.
import { remoteAuthorize } from '../../lib/authz.js'

const TOOL_NAME = 'kala_explain_get'
const CAPABILITY_URI = 'marsys://tool/L-PACT/pact_query'

// ── W3K G-5: the KP school voice's two substrate reads ──────────────────────────────
// Both are EXISTING registered capabilities called with existing facets — no new
// computation, no new capability, no second implementation of either read.
const CHART_FACTS_URI = 'marsys://tool/L1/chart_facts_query'
const DASHAS_URI = 'marsys://tool/L1/get_dashas'

/** KP is canonically read in the Krishnamurti ayanāṃśa — the same convention
 *  `get_kp_cusps.ts` already defaults to (school_conventions.ts §3). The PACT chain is read
 *  in the caller's ayanāṃśa. Both are reported on the voice; neither overwrites the other
 *  (brief §W3K: the divergence is served as data, never silently reconciled). */
const KP_AYANAMSHA_ID = 'krishnamurti'
const KP_HOUSE_SIGNIFICATORS_CATEGORY = 'kp_house_significators'
const KP_DASHA_SYSTEM_ID = 'vimshottari_kp'

const QuestionFrameSchema = z.object({
  domain: z.string().optional(),
  entity: z.string().optional(),
  horizon: z.string().optional(),
  intent_verb: z.string().optional(),
  stakes: z.string().optional(),
  comparison_target: z.string().optional(),
}).optional().describe(
  'Optional question frame (Elevation E4): {domain, entity, horizon, intent_verb, stakes, ' +
  'comparison_target}. The chart is always implicit. Echoed back verbatim in the envelope.',
)

type PactStatus =
  | 'denied_at_promise' | 'denied_at_confirmation' | 'denied_at_activation'
  | 'chain_pending_activation' | 'chain_incomplete_infra' | 'chain_complete'

const PACT_STATUS_VERDICT: Record<PactStatus, string> = {
  denied_at_promise:
    'This matter is not promised by the rashi checklist — the chain halts at PROMISE; no later stage can deliver what the rashi does not promise.',
  denied_at_confirmation:
    'The rashi\'s promise is not confirmed in the operative varga — the chain halts at CONFIRMATION.',
  denied_at_activation:
    'The promise is confirmed but has no dasha vehicle left to deliver it — the chain halts at ACTIVATION.',
  chain_pending_activation:
    'The promise is confirmed and a future dasha window carries it, but that window has not opened yet — TRIGGER is not yet reachable.',
  chain_incomplete_infra:
    'All four PACT stages were attempted, but TRIGGER could not be evaluated (ephemeris sidecar unreachable/empty) — an infrastructure gap, not a classical denial.',
  chain_complete:
    'The full PACT chain (promise → confirmation → activation → trigger) is intact as of the evaluation date.',
}

interface PactStage {
  stage?: string
  status?: string
  reason?: string
  dignities?: Array<{ fact_id?: string | null }>
  [k: string]: unknown
}

/** Labels the matter under investigation from pact_query's `about` block (falls back through
 *  label → domain → "bhava N" → a generic honest placeholder — never fabricated). */
function labelAbout(about: Record<string, unknown> | undefined): string {
  if (!about) return 'this matter'
  const label = about['label']
  if (typeof label === 'string' && label.trim()) return label
  const domain = about['domain']
  if (typeof domain === 'string' && domain.trim()) return domain
  const bhava = about['bhava']
  if (typeof bhava === 'number') return `bhava ${bhava}`
  return 'this matter'
}

/** Builds the ArgumentReading from the raw PACT `stages` + `pact_status` the underlying
 *  `pact_query` capability already computed. Pure assembly — no new chain evaluation. */
function buildReading(params: {
  stages: PactStage[]
  pactStatus: PactStatus | string
  aboutLabel: string
  asOfDate: string
}): ArgumentReading {
  const { stages, pactStatus, aboutLabel, asOfDate } = params
  const verdictStatement = PACT_STATUS_VERDICT[pactStatus as PactStatus]
    ?? `PACT status: ${pactStatus} (unrecognized status string — served verbatim, not fabricated).`

  const thesis = `Why for ${aboutLabel} as of ${asOfDate}: ${verdictStatement}`

  // One evidence row per stage actually attempted, in chain order — each carries the
  // stage's own reason sentence (already the most specific claim this substrate makes).
  // Only the CONFIRMATION stage's per-graha dignity rows carry a genuine fact_id at this
  // substrate tier (register_d10_pact.ts's `gradeGrahaInVarga`) — other stages' reasons are
  // NOT re-attributed to a fact_id we don't actually have (§N.7: never overclaim a citation).
  const evidence: ArgumentEvidence[] = stages.map((stage): ArgumentEvidence => {
    const factIds =
      stage.stage === 'CONFIRMATION' && Array.isArray(stage.dignities)
        ? (stage.dignities.map((d) => d.fact_id).filter((f): f is string => typeof f === 'string'))
        : []
    return {
      claim: `${stage.stage ?? 'stage'} (${stage.status ?? 'unknown'}): ${stage.reason ?? 'no reason recorded'}`,
      fact_ids: factIds,
    }
  })

  return {
    thesis,
    evidence,
    dissent: [],
    verdict: { statement: verdictStatement, tier: 'structural_prior' },
    falsifier: null,
  }
}

// ── W3K G-5: fetch + build the KP school voice ──────────────────────────────────────

function asRows(payload: Record<string, unknown>): Array<Record<string, unknown>> {
  const rows = payload['rows']
  return Array.isArray(rows) ? (rows as Array<Record<string, unknown>>) : []
}

export function toKpPeriods(rows: Array<Record<string, unknown>>): KpRunningPeriod[] {
  return rows.map((r) => ({
    level_n: Number(r['level_n'] ?? 0),
    lord_graha: typeof r['lord_graha'] === 'string' ? r['lord_graha'] : null,
    kp_sub_lord: typeof r['kp_sub_lord'] === 'string' ? r['kp_sub_lord'] : null,
    kp_sub_sub_lord: typeof r['kp_sub_sub_lord'] === 'string' ? r['kp_sub_sub_lord'] : null,
    start_date: typeof r['start_date'] === 'string' ? r['start_date'] : null,
    end_date: typeof r['end_date'] === 'string' ? r['end_date'] : null,
  })).filter((p) => Number.isFinite(p.level_n) && p.level_n > 0)
}

/**
 * Reads the KP significator ladder for `bhava` and the running `vimshottari_kp` stack at
 * `asOfDate`, then hands both to the pure verdict builder.
 *
 * A failed/empty substrate read is carried into `empty_reason` verbatim rather than thrown:
 * EXPLAIN's primary answer is the PACT chain, and a KP outage must degrade the KP voice
 * only — never take the whole reading down, and never be mistaken for "KP agrees".
 */
export async function fetchKpSchoolVoice(params: {
  chartId: string
  bhava: number
  asOfDate: string | undefined
  chainAyanamshaId: string
  pactStatus: string
  principal: Principal
}): Promise<KpSchoolVoice> {
  const { chartId, bhava, asOfDate, chainAyanamshaId, pactStatus, principal } = params
  const subject = `HOUSE_${String(bhava).padStart(2, '0')}`

  let ladderRows: Array<Record<string, unknown>> = []
  let periodRows: Array<Record<string, unknown>> = []
  let substrateNote: string | null = null

  try {
    const [factsRaw, dashaRaw] = await Promise.all([
      callKalaRegistryCap(CHART_FACTS_URI, {
        chart_id: chartId,
        ayanamsha_id: KP_AYANAMSHA_ID,
        category: KP_HOUSE_SIGNIFICATORS_CATEGORY,
        fact_subject: subject,
        shape: 'rows',
        limit: 50,
      }, principal),
      callKalaRegistryCap(DASHAS_URI, {
        chart_id: chartId,
        ayanamsha_id: chainAyanamshaId,
        system_id: KP_DASHA_SYSTEM_ID,
        all_levels: true,
        fields: 'all',
        ...(asOfDate ? { as_of_date: asOfDate } : {}),
      }, principal),
    ])
    ladderRows = asRows(unwrapKalaPayload(factsRaw))
    periodRows = asRows(unwrapKalaPayload(dashaRaw))
  } catch (err) {
    substrateNote =
      'KP substrate read failed this call (' +
      (err instanceof Error ? err.message : String(err)).slice(0, 200) +
      ') — an infrastructure gap, NOT an astrological finding. No KP verdict is served.'
  }

  return buildKpSchoolVoice({
    bhava,
    ladder: substrateNote ? null : parseKpHouseLadder(ladderRows, bhava),
    periods: toKpPeriods(periodRows),
    pactStatus,
    kpAyanamshaId: KP_AYANAMSHA_ID,
    chainAyanamshaId,
    substrateNote,
  })
}

/** The KP voice's coverage entry — `computed` only when a real verdict was reached, and
 *  otherwise `honest_empty` carrying the voice's own specific reason. Never `computed`
 *  with an empty verdict behind it (§N.8). */
export function kpCoverageEntry(voice: KpSchoolVoice | null): KalaCoverageEntry {
  if (voice === null) {
    return honestEmptyCoverage(
      'dissent_multi_system_concurrence',
      'the KP school voice needs a bhava to judge; this call resolved neither `bhava` nor a ' +
      'domain the shastra map maps to one.',
    )
  }
  return voice.state === 'computed'
    ? computedCoverage('dissent_multi_system_concurrence')
    : honestEmptyCoverage('dissent_multi_system_concurrence', voice.empty_reason ?? 'unknown')
}

/** Folds the KP voice into the argument reading: a dissent becomes an `ArgumentDissent`
 *  (school-tagged via `source`), a concurrence becomes an `ArgumentEvidence` row. An
 *  `honest_empty` or `not_comparable` voice adds NOTHING to either list — its state is
 *  reported through coverage instead, so a gap can never read as corroboration. */
export function applyKpVoiceToReading(reading: ArgumentReading, voice: KpSchoolVoice | null): ArgumentReading {
  if (voice === null || voice.state !== 'computed') return reading
  if (voice.agreement === 'dissents') {
    const dissent: ArgumentDissent = {
      claim: voice.claim,
      // B.3 / §N.5: the ledger is the actual `chart_facts.fact_id`s of the ladder rows the
      // verdict consumed — scoped to those rows, not to the whole fetched page.
      fact_ids: voice.ladder?.fact_ids ?? [],
      source: KP_SCHOOL_LABEL,
    }
    return { ...reading, dissent: [...reading.dissent, dissent] }
  }
  if (voice.agreement === 'concurs') {
    return {
      ...reading,
      evidence: [
        ...reading.evidence,
        { claim: `${KP_SCHOOL_LABEL} CONCURS: ${voice.claim}`, fact_ids: voice.ladder?.fact_ids ?? [] },
      ],
    }
  }
  return reading
}

// ── SM-γ C4.2: A5 gochara-agreement facet ────────────────────────────────────
// Added behind SM_GAMMA_C4_ENABLED env flag. Fetches gochara windows for the
// event_class being explained (using callKalaRegistryCap, same pattern as KP
// voice above) and assesses whether gochara concurs with or dissents from the
// PACT chain verdict. No new DB query, no new computation (§N.5 / B.10).

export interface A5GocharaAgreement {
  agreement: 'concurs' | 'dissents' | 'insufficient_data'
  gochara_windows_active: number
  dominant_valence: 'gain' | 'loss' | 'neutral' | null
  /** Human-readable agreement note, ≤120 chars (§N.8: never fabricated when empty). */
  note: string
}

/** Maps a PACT status to its chain outcome polarity for agreement logic.
 *  `positive` = chain complete/active (delivery possible); `negative` = denied/blocked. */
function pactStatusPolarity(status: string): 'positive' | 'negative' | 'unknown' {
  if (status === 'chain_complete' || status === 'chain_pending_activation') return 'positive'
  if (
    status === 'denied_at_promise' ||
    status === 'denied_at_confirmation' ||
    status === 'denied_at_activation'
  )
    return 'negative'
  return 'unknown'
}

/** Derives the dominant valence from an array of gochara window objects (whatever the
 *  underlying tool returns in `windows`). Never throws. */
function dominantValenceFromWindows(
  windows: Array<Record<string, unknown>>,
): 'gain' | 'loss' | 'neutral' | null {
  if (windows.length === 0) return null
  const counts: Record<string, number> = {}
  for (const w of windows) {
    const v = typeof w['valence'] === 'string' ? w['valence'] : 'neutral'
    counts[v] = (counts[v] ?? 0) + 1
  }
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0]
  if (top === 'gain' || top === 'loss' || top === 'neutral') return top
  return null
}

/** Fetches gochara windows for a domain/bhava, using a ±180-day window around today, via a
 *  direct in-process call to `computeGocharaForecast` (F-73: NOT via the registry — see the
 *  import comment above). Returns empty array (never throws) on any failure — A5 then
 *  reports `insufficient_data`. `bhava` is accepted for signature parity with callers but not
 *  forwarded — `computeGocharaForecast` has no bhava parameter; domain is its narrowing
 *  primitive (matches pre-existing behavior: bhava was likewise unused in the fetch here). */
async function fetchA5GocharaWindows(
  chartId: string,
  domain: string | undefined,
  bhava: number | null | undefined,
  principal: Principal,
): Promise<Array<Record<string, unknown>>> {
  const today = new Date().toISOString().slice(0, 10)
  const endParsed = new Date(`${today}T00:00:00Z`)
  endParsed.setUTCDate(endParsed.getUTCDate() + 180)
  const endDate = endParsed.toISOString().slice(0, 10)

  try {
    // GA-5 review finding on #1390: computeGocharaForecast itself performs no entitlement
    // check -- gate here, matching what registerGocharaForecastTool's own handler does
    // before calling the same function.
    if (!(await remoteAuthorize(principal, chartId))) return []
    const result = await computeGocharaForecast(
      chartId,
      { start: today, end: endDate },
      undefined,
      undefined,
      20,
      principal,
      domain ?? undefined,
    )
    return (result['windows'] as Array<Record<string, unknown>> | undefined) ?? []
  } catch {
    return []
  }
}

/** Builds the A5 gochara-agreement facet from the PACT verdict and gochara windows.
 *  Agreement logic (§N.8: never a default-positive; only `concurs` when evidence is present):
 *  - `concurs`: windows found AND dominant valence MATCHES the PACT chain polarity
 *    (positive PACT + gain windows, OR negative PACT + loss windows).
 *  - `dissents`: windows found AND dominant valence CONTRADICTS the PACT chain polarity.
 *  - `insufficient_data`: no windows, or gochara fetch failed, or polarity unknown. */
async function buildA5GocharaAgreement(
  chartId: string,
  pactStatus: string,
  domain: string | undefined,
  bhava: number | null | undefined,
  principal: Principal,
): Promise<A5GocharaAgreement> {
  let windows: Array<Record<string, unknown>> = []
  try {
    windows = await fetchA5GocharaWindows(chartId, domain, bhava, principal)
  } catch {
    // Fetch failure → insufficient_data, never thrown
  }

  if (windows.length === 0) {
    return {
      agreement: 'insufficient_data',
      gochara_windows_active: 0,
      dominant_valence: null,
      note: 'No active gochara windows found for this domain/period.',
    }
  }

  const domValence = dominantValenceFromWindows(windows)
  const pactPolarity = pactStatusPolarity(pactStatus)

  let agreement: 'concurs' | 'dissents' | 'insufficient_data'
  if (pactPolarity === 'unknown' || domValence == null) {
    agreement = 'insufficient_data'
  } else if (
    (pactPolarity === 'positive' && domValence === 'gain') ||
    (pactPolarity === 'negative' && domValence === 'loss')
  ) {
    agreement = 'concurs'
  } else if (
    (pactPolarity === 'positive' && domValence === 'loss') ||
    (pactPolarity === 'negative' && domValence === 'gain')
  ) {
    agreement = 'dissents'
  } else {
    agreement = 'insufficient_data'
  }

  const noteBase = agreement === 'concurs'
    ? `Gochara ${domValence} windows align with PACT ${pactStatus}.`
    : agreement === 'dissents'
      ? `Gochara ${domValence} windows diverge from PACT ${pactStatus}.`
      : `Gochara valence (${domValence ?? 'n/a'}) inconclusive for PACT ${pactStatus}.`
  const note = noteBase.slice(0, 120)

  return {
    agreement,
    gochara_windows_active: windows.length,
    dominant_valence: domValence,
    note,
  }
}

export function registerKalaExplainTool(server: McpServer, principal: Principal): void {
  server.tool(
    TOOL_NAME,
    'VIEW 6 — EXPLAIN ("why do you say that?"). Wraps the same PACT-protocol chained ' +
    'investigation pact_query calls (promise in the rashi → confirmation in the varga → ' +
    'activation in the dasha → trigger in the transit), re-served on the elevated kala_* ' +
    'envelope: an argument-shaped reading naming the causal chain, its weakest link (the ' +
    'stage the chain currently halts at or rests on — v1.0 §6.2\'s "least-attested edge, ' +
    'named honestly"), tri-plane pointers (a denied/pending chain points to kala_upaya_get ' +
    'for intervention diagnosis; a live/complete chain points to kala_elect_get), 3-state ' +
    'coverage (the field-write provenance graph / classical-citation join / counterfactual ' +
    'mode, items 11 and E6, are NOT yet built — honestly flagged, not silently omitted), ' +
    'freshness, and calibration_maturity (read from the chart-level calibration authority). Pass `domain` ' +
    'or `bhava` exactly as judgment_query/pact_query accept — one is required. ' +
    '[ṢAḌ-DARŚANA W0.4]',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')."),
      domain: z.string().optional().describe(
        'Life-domain name (judgment_query\'s shastra map): marriage/relationship/partnership, ' +
        'career/vocation, wealth/finance, health/vitality, progeny/children, education, ' +
        'spirituality. Takes precedence over `bhava` if both given.'),
      bhava: z.number().int().min(1).max(12).optional().describe(
        'Bhava (house) number 1-12. Required if `domain` is omitted.'),
      as_of_date: z.string().optional().describe('Date (YYYY-MM-DD) to evaluate ACTIVATION/TRIGGER as-of. Default: today.'),
      max_signals: z.number().int().min(1).max(50).optional().describe(
        'Forwarded to the PROMISE stage (judgment_query). Default 15, max 50.'),
      question_frame: QuestionFrameSchema,
    },
    async (params) => {
      const {
        chart_id, ayanamsha_id, domain, bhava, as_of_date, max_signals, question_frame,
      } = params as Record<string, unknown>

      if (!chart_id || typeof chart_id !== 'string') {
        return kalaErrorOutput(TOOL_NAME, 'chart_id is required')
      }
      if (!domain && bhava === undefined) {
        return kalaErrorOutput(TOOL_NAME, 'either `domain` or `bhava` is required')
      }

      try {
        const resolvedAyanamsha = resolveChartFactsAyanamsha(ayanamsha_id as string | undefined)
        const raw = await callKalaRegistryCap(
          CAPABILITY_URI,
          {
            chart_id,
            ayanamsha_id: resolvedAyanamsha,
            ...(domain ? { domain } : {}),
            ...(bhava !== undefined ? { bhava } : {}),
            ...(as_of_date ? { as_of_date } : {}),
            ...(max_signals != null ? { max_signals } : {}),
          },
          principal,
        )
        const payload = unwrapKalaPayload(raw)
        const stages = Array.isArray(payload['stages']) ? (payload['stages'] as PactStage[]) : []
        const pactStatus = (payload['pact_status'] as PactStatus | string | undefined) ?? 'unknown'
        const about = (payload['about'] as Record<string, unknown> | undefined) ?? undefined
        const aboutLabel = labelAbout(about)
        const resolvedAsOfDate = (payload['as_of_date'] as string | undefined) ?? (as_of_date as string | undefined) ?? 'today'
        const factIdRefs = Array.isArray(payload['fact_id_refs']) ? (payload['fact_id_refs'] as string[]) : []
        const pactDrillPointers = Array.isArray(payload['drill_pointers']) ? payload['drill_pointers'] : []

        let reading = buildReading({ stages, pactStatus, aboutLabel, asOfDate: resolvedAsOfDate })

        // W3K G-5. The house to judge comes from pact_query's OWN resolved `about.bhava`
        // (so a `domain` call and a `bhava` call judge the same house the chain judged),
        // falling back to the caller's literal `bhava`. No second shastra-map copy here.
        const resolvedBhava =
          typeof about?.['bhava'] === 'number' ? (about['bhava'] as number)
          : typeof bhava === 'number' ? bhava
          : null

        const kpVoice = resolvedBhava === null ? null : await fetchKpSchoolVoice({
          chartId: chart_id,
          bhava: resolvedBhava,
          asOfDate: (payload['as_of_date'] as string | undefined) ?? (as_of_date as string | undefined),
          chainAyanamshaId: resolvedAyanamsha,
          pactStatus: String(pactStatus),
          principal,
        })
        reading = applyKpVoiceToReading(reading, kpVoice)

        const weakestLink = stages.length > 0
          ? (() => {
              const last = stages[stages.length - 1] as PactStage
              return { stage: last.stage ?? null, status: last.status ?? null, reason: last.reason ?? null }
            })()
          : null

        // A denied/pending chain routes to the intervention-leverage engine (UPĀYA-SETU is
        // exactly "this outcome is unlikely for me; what would raise its likelihood?"); a
        // live/complete chain routes to ELECT (timing the act inside an already-open window).
        const chainIsLive = pactStatus === 'chain_complete' || pactStatus === 'chain_pending_activation'
        const triPlane: TriPlanePointers = {
          // ND-1 (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30): was a bare `null`. This reading
          // genuinely IS the interpretive/causal-chain ground for the claim it explains, but
          // see ahead.ts's prediction_ref for why a bare null is still the wrong SHAPE for
          // saying so — tri_plane_no_dead_end_gate.ts grades it `WARN`, an honest no_lever
          // `PASS`.
          interpretation_ref: noLeverPointer(
            'kala_explain_get IS the interpretation plane — this response is itself the '
              + 'interpretive/causal-chain ground for the claim it explains, so there is no '
              + 'further interpretive surface to traverse to. Not a missing pointer: a '
              + 'terminal by construction.',
          ),
          prediction_ref: pointerTo(
            'kala_ahead_get',
            'see the forward-looking windows for this domain/bhava once/while the chain is live.',
          ),
          intervention_ref: chainIsLive
            ? pointerTo('kala_elect_get', 'elect the best window inside this already-confirmed/pending chain.')
            : pointerTo('kala_upaya_get', `diagnose an intervention for the failing link named in weakest_link (${weakestLink?.stage ?? 'n/a'}).`),
        }

        const coverage: KalaCoverageEntry[] = [
          computedCoverage('pact_chain_promise_confirmation_activation_trigger'),
          kpCoverageEntry(kpVoice),
          notInCorpusCoverage(
            'classical_citation_join',
            'field-write provenance edges + rule→classical-chunk citation join (item 11) are not ' +
            'yet built — chain reasons above are computed prose, not yet linked to specific ' +
            'śāstra passages (EXPLAIN\'s pedagogy mode, E6).',
          ),
          notInCorpusCoverage(
            'counterfactual_mode',
            'counterfactual mode ("without the vedha this grades one tier higher", E6) is not yet ' +
            'built — lands W2/W3.',
          ),
        ]

        // W2 (E5): the real field snapshot read — served id, or an honest marker; never a stub.
        const fieldSnapshot = await resolveFieldSnapshot(chart_id, principal)

        const freshness = buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: fieldSnapshot.field_content_hash })

        const densityContract: KalaDensityContract = {
          paginated: false,
          facets: ['domain', 'bhava'],
          empty_reason: true,
        }

        const envelope = makeKalaEnvelope({
          reading,
          questionFrame: (question_frame as QuestionFrame | undefined) ?? null,
          fieldSnapshot,
          triPlane,
          coverage,
          freshness,
          calibrationMaturity: await fetchCalibrationMaturity(chart_id, principal),
        })

        // SM-γ C4.2: A5 gochara-agreement facet (flag-guarded).
        const C4_ENABLED = process.env['SM_GAMMA_C4_ENABLED'] === 'true' || process.env['SM_GAMMA_C4_ENABLED'] === '1'
        const a5GocharaAgreement: A5GocharaAgreement | undefined = C4_ENABLED
          ? await buildA5GocharaAgreement(
              chart_id,
              String(pactStatus),
              domain as string | undefined,
              resolvedBhava,
              principal,
            )
          : undefined

        const baseContent = {
          ok: true as const,
          tool: TOOL_NAME,
          chart_id,
          ...envelope,
          composed: composeArgument(envelope.reading),
          density_contract: densityContract,
          about: about ?? null,
          pact_status: pactStatus,
          weakest_link: weakestLink,
          // W3K G-5: the school-tagged Law-2 voice, served in full so the verdict is
          // auditable in place (which limb, which running lord, which ayanāṃśa).
          school_voices: kpVoice ? [kpVoice] : [],
          chain: stages,
          fact_id_refs: factIdRefs,
          pact_drill_pointers: pactDrillPointers,
        }

        const content = C4_ENABLED && a5GocharaAgreement !== undefined
          ? { ...baseContent, a5_gochara_agreement: a5GocharaAgreement }
          : baseContent

        return kalaBudgetedDualOutput(content, TOOL_NAME)
      } catch (err) {
        return kalaErrorOutput(TOOL_NAME, err instanceof Error ? err.message : String(err), { chart_id })
      }
    },
  )
}
