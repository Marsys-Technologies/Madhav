/**
 * D8 Assess-Domain + Yoga-Dasha Bridge — Capability Registration (per-wave file)
 * ================================================================================
 * GATE A compliance: this is the per-wave registration file for D8.
 * It does NOT edit registry/index.ts or registry/types.ts.
 *
 * D8 registers domain reasoning-unit tools (assess_*) and the yoga-dasha bridge.
 * These are reconciled multi-call capabilities that orchestrate existing L2/L3 handlers
 * into a single acharya-grade domain bundle.
 *
 * Capabilities registered by D8:
 *
 *   L-DOMAIN assess tools (R3.1):
 *   marsys://tool/L-DOMAIN/assess_marriage  — 7th lord + Venus + D9 + bhāvat-bhāva + timing
 *   marsys://tool/L-DOMAIN/assess_career    — 10th lord + Saturn + D10 + yogas + timing
 *   marsys://tool/L-DOMAIN/assess_health    — 1st+6th+8th lords + Sun + afflictions + D1/D6
 *   marsys://tool/L-DOMAIN/assess_wealth    — 2nd+11th lords + Jupiter + dasha activation
 *
 *   Timing bridge (R3.2):
 *   marsys://tool/L-TIMING/yoga_activation_by_dasha
 *     — bodha_msr_signals (signal_type_class='yoga') × kala_activation join
 *
 * Total D8 new capabilities: 5
 *
 * Design constraints:
 *   - chart_id is ALWAYS required — no native defaults (principle #14)
 *   - Every returned fact carries its signal_id / fact_id reference from L1/L2
 *   - Contradictions live: bodha_contradictions populated by bo_karanajala (1,034–1,100 rows/aya/chart)
 *   - judgment_flags marks any inference requiring acharya validation
 *   - Calls real handlers (query_domain_reading, query_temporal_activation,
 *     query_contradictions) — no mock/fake data
 *
 * Usage: import this file at application startup after D7 channel is registered.
 */

import { registerCapability } from '../index'
import type { CapabilityDescriptor } from '../types'
import { query } from '@/lib/db/client'
import { deriveDefect001Note } from '../../provenance/freshness_notes'
import { resolveAddress } from '../../address_resolver'
import { SHASTRA_MAP } from './register_d9_judgment'
// ŚODHANA T5 (PŪRTI) — the computed-but-never-joined classical legs + the served
// reading_checklist receipt, shared with judgment_query (MC-030/031/033).
import {
  fetchSensitiveDegreeFirings,
  fetchKpCuspChain,
  fetchGocharaSweep,
  checklistExhaustiveness,
  DOMAIN_KP_CUSPS,
  type ChecklistUnit,
} from './reading_checklist'
import { judgmentFlag, type JudgmentFlagEntry } from '../../envelope'
import { applyCompositeRanking, type MsrSignalRow } from '../../ranking/composite_ranker'
import { fetchL1Context } from '../../ranking/l1_context_fetcher'
import { rankGrahasByShadbala, type GrahaShadbalaInput } from '../../ranking/rank_vocabulary'
import {
  humanizeMachineKey,
  humanizeSnakeLabel,
  displayGraha,
  displayVarga,
  ordinalHouse,
} from '../../ranking/identifier_format'

// Y-2 (D-1.6 Lane S-3, CRIT): assess_* domain-bearing yoga discount, mirroring
// judgment_query's YOGA_BHANGA_DISCOUNT (register_d9_judgment.ts) semantics — a firing whose
// bhaṅga (cancellation) is active is annotated but not treated as a full-strength confirmed
// finding. assess_* does not compute a numeric verdict term (judgment_query does), so this
// constant only affects display ordering/annotation here, not a composite score.
const ASSESS_YOGA_BHANGA_DISCOUNT = 0.3

// ── Shared: domain handler factory ───────────────────────────────────────────
//
// All four assess_* tools share this shape. The factory calls three real
// underlying handlers (query_domain_reading, query_temporal_activation,
// query_contradictions) via their exported capability handlers, then assembles
// a reconciled bundle.

interface AssessDomainArgs {
  chart_id: string
  ayanamsha_id: string
  domain: string
  domain_label: string
  judgment_flag_note: string
}

// F-021R bounding defaults for assess_* tools.
// question_lenses.all_relevant_ranked_jsonb averages 1.4 MB/row; contradictions run 5,000+/chart.
// These caps bound the assembled bundle to ~100k chars (§2.1-1 budget).
const ASSESS_DEFAULT_MAX_SIGNALS_PER_LENS = 10
const ASSESS_MAX_SIGNALS_PER_LENS = 50
const ASSESS_DEFAULT_MAX_CONTRADICTIONS = 15
const ASSESS_MAX_CONTRADICTIONS = 100

// R6 3b-budgets (R-1/R-8): the F-021R caps above bound question_lenses + contradiction
// ITEMS, but left four other unbounded arrays flowing straight through into the assembled
// bundle — karaka_analysis.cdlm_cells, contradictions.discoveries, activating_dasha.
// activations, activating_dasha.predicates. These are exactly the residual bulk behind the
// live-measured 1.04MB assess_career payload (register R-1/R-8). Same cap-and-count
// discipline as the existing F-021R caps: bound the array, report total_count/truncated,
// and name the drill instrument for the remainder — never drop the fact of truncation.
const ASSESS_DEFAULT_MAX_CDLM_CELLS = 20
const ASSESS_MAX_CDLM_CELLS = 100
const ASSESS_DEFAULT_MAX_DISCOVERIES = 10
const ASSESS_MAX_DISCOVERIES = 50
const ASSESS_DEFAULT_MAX_ACTIVATIONS = 10
const ASSESS_MAX_ACTIVATIONS = 50
const ASSESS_DEFAULT_MAX_PREDICATES = 10
const ASSESS_MAX_PREDICATES = 50

// Honest empty-reason for the temporal stage (never faked). The temporal stage empties because
// of a KNOWN L3 kala_activation writer defect (R-45/R-40 shared root: ~99% of rows have NULL
// activation_start/end) — a DATA-PLANE issue owned by WP-2.1, not a serving bug. Disclosed here
// so a consumer knows the stage is pending, not genuinely quiet. (Item-0 R-45 triage,
// AUDIT_STATE.md 2026-07-12.) No chart-specific row counts are embedded here — this string is
// served to every caller regardless of chart context (GT-32/GT-54). Exported so its regression
// protection (checkTextForNativeLeak scan, see register_d8_assess_domain.test.ts /
// chart_agnostic_gate.test.ts) can import the REAL constant rather than a synthetic copy.
export const TEMPORAL_EMPTY_REASON =
  'kala_activation returned no dated windows in range. Known L3 writer defect (R-45/R-40 ' +
  'shared root): ~99% of kala_activation rows have NULL activation_start/end for the ' +
  'lahiri ayanamsha in this scan — PENDING WP-2.1 data-plane fix, not a serving trim. ' +
  'Verify via kala_yoga_activation_get / query_temporal_activation.'

/** Cap an array to `cap` entries, reporting the true total + truncation flag. Never
 *  fabricates a count — `total_count` is always `arr.length` of the REAL array received. */
function capArray<T>(
  value: unknown,
  cap: number,
  drillUri?: string,
): { items: T[]; total_count: number; truncated: boolean; drill_uri?: string } {
  const arr = Array.isArray(value) ? (value as T[]) : []
  const total_count = arr.length
  const items = arr.slice(0, cap)
  const truncated = total_count > cap
  return { items, total_count, truncated, ...(truncated && drillUri ? { drill_uri: drillUri } : {}) }
}

// ── EL-45: direct varga/AV consumption (no "see other tool" stubs) ────────────
// Every domain assessor here consumes ITS classical varga(s) directly from L1 chart_facts
// (graha_dignity_per_varga + ashtakavarga_pinda_sarva_per_varga) instead of pointing the
// caller to chart_facts_query for a layer classical to its own domain. wealth gets BOTH
// classical wealth vargas (D2 Horā for liquid wealth, D11 Labha for gains/income — the
// charter's verified gap: "D11... is not in the wealth floor at all", §0.2.A) plus Indu
// Lagna (the dedicated Jaimini wealth-strength lagna). Exported so a CI check (and the D8
// test suite) can assert every SHASTRA_MAP domain this file serves has a non-empty entry —
// "no domain assessor may ship a stub for a layer classical to its own domain."
export const DOMAIN_DIRECT_VARGAS: Record<string, string[]> = {
  wealth: ['D2', 'D11'],
  career: ['D10'],
  relationship: ['D9'],
  health: ['D6'],
}
const DOMAIN_INDU_LAGNA = new Set(['wealth'])

interface VargaDignityRow {
  graha: string
  dignity: string | null
  sign: string | null
  house: number | null
  fact_id: string
}

/** graha_dignity_per_varga rows for the given vargas, keyed by varga. Real L1 fact_ids
 *  (§N.5) — never restates a computed value, only reads the stored one. */
async function fetchVargaDignity(
  chart_id: string,
  ayanamsha_id: string,
  vargas: string[],
): Promise<Record<string, VargaDignityRow[]>> {
  const out: Record<string, VargaDignityRow[]> = {}
  for (const v of vargas) out[v] = []
  if (vargas.length === 0) return out
  const res = await query<Record<string, unknown>>(
    `SELECT fact_id, fact_subject, fact_value_text, fact_value_jsonb
     FROM chart_facts
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_dignity_per_varga'
       AND fact_value_jsonb->>'varga' = ANY($3)`,
    [chart_id, ayanamsha_id, vargas],
  )
  for (const row of res.rows) {
    const jsonb = row['fact_value_jsonb'] as Record<string, unknown> | null
    const varga = typeof jsonb?.['varga'] === 'string' ? (jsonb['varga'] as string) : null
    if (!varga || !out[varga]) continue
    const subject = String(row['fact_subject'] ?? '')
    const graha = subject.startsWith(`${varga}_`) ? subject.slice(varga.length + 1) : subject
    out[varga].push({
      graha,
      dignity: (row['fact_value_text'] as string | null) ?? null,
      sign: typeof jsonb?.['sign'] === 'string' ? (jsonb['sign'] as string) : null,
      house: typeof jsonb?.['house'] === 'number' ? (jsonb['house'] as number) : null,
      fact_id: String(row['fact_id'] ?? ''),
    })
  }
  return out
}

interface VargaAvResult {
  rows: Array<{ graha: string; pinda_sarva: number; fact_id: string }>
  fact_ids: string[]
  available: boolean
}

/** ashtakavarga_pinda_sarva_per_varga rows for the given vargas, keyed by varga. Honestly
 *  `available: false` (never fabricated) for a varga L1 has not built per-varga AV for yet
 *  (e.g. D11 at the time of writing — a data-plane gap, disclosed, not silently stubbed). */
async function fetchVargaAvPindaSarva(
  chart_id: string,
  ayanamsha_id: string,
  vargas: string[],
): Promise<Record<string, VargaAvResult>> {
  const out: Record<string, VargaAvResult> = {}
  for (const v of vargas) out[v] = { rows: [], fact_ids: [], available: false }
  if (vargas.length === 0) return out
  const res = await query<Record<string, unknown>>(
    `SELECT fact_id, fact_subject, fact_key, fact_value_num
     FROM chart_facts
     WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'ashtakavarga_pinda_sarva_per_varga'
       AND fact_key = ANY($3)`,
    [chart_id, ayanamsha_id, vargas],
  )
  for (const row of res.rows) {
    const v = String(row['fact_key'] ?? '')
    if (!out[v]) continue
    const fact_id = String(row['fact_id'] ?? '')
    out[v].rows.push({
      graha: String(row['fact_subject'] ?? ''),
      pinda_sarva: Number(row['fact_value_num'] ?? 0),
      fact_id,
    })
    out[v].fact_ids.push(fact_id)
    out[v].available = true
  }
  return out
}

interface InduLagnaResult {
  sign: unknown
  sign_lord: unknown
  house_d1: unknown
  nakshatra: unknown
  fact_ids: string[]
  note: string
}

/** special_lagna INDU_LAGNA facts — the dedicated Jaimini wealth-strength lagna. */
async function fetchInduLagna(chart_id: string, ayanamsha_id: string): Promise<InduLagnaResult | null> {
  try {
    const res = await query<Record<string, unknown>>(
      `SELECT fact_id, fact_key, fact_value_text, fact_value_num
       FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'special_lagna' AND fact_subject = 'INDU_LAGNA'`,
      [chart_id, ayanamsha_id],
    )
    if (res.rows.length === 0) return null
    const byKey: Record<string, unknown> = {}
    const fact_ids: string[] = []
    for (const row of res.rows) {
      const key = String(row['fact_key'] ?? '')
      byKey[key] = row['fact_value_text'] ?? row['fact_value_num']
      fact_ids.push(String(row['fact_id'] ?? ''))
    }
    return {
      sign: byKey['sign'] ?? null,
      sign_lord: byKey['sign_lord'] ?? null,
      house_d1: byKey['house_d1'] ?? null,
      nakshatra: byKey['nakshatra'] ?? null,
      fact_ids,
      note: 'Indu Lagna (Jaimini) — computed from Moon + the 9th house counted from Moon; a ' +
        'benefic occupying/aspecting it, or its sign-lord being strong, is a classical ' +
        'wealth-strength indicator distinct from the 2nd/11th house-and-lord reading.',
    }
  } catch {
    return null
  }
}

/**
 * EL-45 — assemble a domain's classical-varga analysis DIRECTLY from L1 chart_facts. Replaces
 * the former uniform "see chart_facts_query" stub for every assess_* tool. A domain with no
 * entry in DOMAIN_DIRECT_VARGAS honestly reports `direct_consumption: false` (never a fake
 * fill) — currently every domain this file serves (wealth/career/marriage/health) has one.
 */
export async function buildVargaAnalysisDirect(
  chart_id: string,
  ayanamsha_id: string,
  domain: string,
): Promise<Record<string, unknown>> {
  const vargas = DOMAIN_DIRECT_VARGAS[domain] ?? []
  if (vargas.length === 0) {
    return {
      direct_consumption: false,
      consumed_vargas: [],
      note: `No classical varga mapped for domain "${domain}" — falling back to drill (chart_facts_query).`,
      drill_uri: 'marsys://tool/L1/chart_facts_query',
    }
  }
  try {
    const [dignityByVarga, avByVarga, induLagna] = await Promise.all([
      fetchVargaDignity(chart_id, ayanamsha_id, vargas),
      fetchVargaAvPindaSarva(chart_id, ayanamsha_id, vargas),
      DOMAIN_INDU_LAGNA.has(domain) ? fetchInduLagna(chart_id, ayanamsha_id) : Promise.resolve(null),
    ])
    const per_varga: Record<string, unknown> = {}
    const fact_ids: string[] = []
    for (const v of vargas) {
      const dignityRows = dignityByVarga[v] ?? []
      const avResult = avByVarga[v]
      for (const r of dignityRows) fact_ids.push(r.fact_id)
      if (avResult) fact_ids.push(...avResult.fact_ids)
      per_varga[v] = {
        varga_display: displayVarga(v),
        graha_dignity: dignityRows.map(r => ({
          graha: displayGraha(r.graha),
          dignity: r.dignity,
          sign: r.sign,
          house: r.house,
          house_display: r.house ? ordinalHouse(r.house) : null,
          humanized: humanizeMachineKey(`${v}_${r.graha}`),
          fact_id: r.fact_id,
        })),
        ashtakavarga_pinda_sarva: avResult?.available ? avResult.rows : null,
        ashtakavarga_available: avResult?.available ?? false,
        ...(avResult?.available
          ? {}
          : {
              empty_reason: `ashtakavarga_pinda_sarva_per_varga has no ${v} rows for this chart — ` +
                `per-varga Ashtakavarga is not yet computed for ${v} at L1 (a data-plane gap, not a ` +
                `serving stub). The ${v} sign/house/dignity placements above ARE real, directly-` +
                'consumed L1 facts.',
            }),
      }
    }
    if (induLagna) fact_ids.push(...induLagna.fact_ids)
    return {
      direct_consumption: true,
      consumed_vargas: vargas,
      per_varga,
      ...(induLagna ? { indu_lagna: induLagna } : {}),
      fact_ids: Array.from(new Set(fact_ids)),
      note: `${vargas.map(displayVarga).join(' + ')} consumed directly from L1 chart_facts ` +
        '(graha_dignity_per_varga + ashtakavarga_pinda_sarva_per_varga)' +
        (induLagna ? ' + Indu Lagna (special_lagna)' : '') +
        ' — not a "see other tool" stub (EL-45). Full per-house Ashtakavarga bindu detail ' +
        '(ashtakavarga_bindu_per_varga) available via the chart_facts_query drill below.',
      drill_uri: 'marsys://tool/L1/chart_facts_query',
    }
  } catch (err) {
    return {
      direct_consumption: false,
      consumed_vargas: vargas,
      error: String(err),
      note: 'Direct varga consumption failed for this call — see error. Not silently downgraded to a stub.',
      drill_uri: 'marsys://tool/L1/chart_facts_query',
    }
  }
}

// ── EL-44: deterministic verdict layer ─────────────────────────────────────────
// 3-5 plain-language sentences summarizing a domain assessment's bottom line, composed by a
// FIXED TEMPLATE over already-graded terms (B.10: no generative call in the serving path —
// every clause is string-concatenation over real counts/labels already computed above, never
// an LLM). Every clause states which real L1/L2 fact_ids it is grounded on; a clause that
// describes an honest absence (no yogas fired, no contradictions) carries `grounded: false`
// with an empty fact_ids array rather than a fabricated citation (B.10).
export interface VerdictClause {
  text: string
  fact_ids: string[]
  grounded: boolean
}
export interface VerdictLayer {
  clauses: VerdictClause[]
  sentence_count: number
  fact_ids_cited: string[]
  template: 'deterministic_v1'
  note: string
}

interface VerdictLayerInputs {
  domain_label: string
  top10: Array<Record<string, unknown>>
  bearingYogaFirings: Array<Record<string, unknown>>
  domainMatchedYogaFactIds: string[]
  vargaAnalysis: Record<string, unknown>
  contradictions: Record<string, unknown>
  chartWideContradictionCount: number
  temporalOk: boolean
  stageTemporalCount: number
}

export function buildVerdictLayer(inputs: VerdictLayerInputs): VerdictLayer {
  const clauses: VerdictClause[] = []

  // 1 — overview (always present; grounded on the top composite signals' own fact_ids).
  const top10FactIds = Array.from(new Set(
    inputs.top10.flatMap(s => (Array.isArray(s['constituent_fact_ids']) ? s['constituent_fact_ids'] as string[] : []))
  ))
  clauses.push({
    text: `${inputs.domain_label} assessment draws on ${inputs.top10.length} composite-ranked ` +
      `signal(s) for this chart, cross-referenced against classical yoga firings, varga ` +
      'placements, contradictions, and dasha timing below.',
    fact_ids: top10FactIds,
    grounded: top10FactIds.length > 0,
  })

  // 2 — yoga findings.
  const domainMatched = inputs.bearingYogaFirings.filter(y => y['domain_match'] === true)
  if (domainMatched.length > 0) {
    const names = domainMatched.slice(0, 3)
      .map(y => humanizeSnakeLabel(String(y['yoga_canonical_id'] ?? '')))
      .filter(Boolean)
      .join(', ')
    clauses.push({
      text: `${domainMatched.length} confirmed yoga(s) fired on this chart (ga_yoga_firings) ` +
        `bear directly on this domain's significators${names ? `, including ${names}` : ''}.`,
      fact_ids: inputs.domainMatchedYogaFactIds,
      grounded: inputs.domainMatchedYogaFactIds.length > 0,
    })
  } else if (inputs.bearingYogaFirings.length > 0) {
    clauses.push({
      text: `${inputs.bearingYogaFirings.length} yoga(s) fired on this chart overall, but none ` +
        "name only this domain's bhāveśa/kāraka(s) — shown for context, not domain-confirmed.",
      fact_ids: [],
      grounded: false,
    })
  } else {
    clauses.push({
      text: 'No confirmed yoga firings are recorded for this chart in ga_yoga_firings — an ' +
        'honest absence, not a fabricated claim either way.',
      fact_ids: [],
      grounded: false,
    })
  }

  // 3 — varga grounding (EL-45 direct consumption).
  if (inputs.vargaAnalysis['direct_consumption'] === true) {
    const vargas = (inputs.vargaAnalysis['consumed_vargas'] as string[] | undefined) ?? []
    const vargaFactIds = (inputs.vargaAnalysis['fact_ids'] as string[] | undefined) ?? []
    clauses.push({
      text: `${vargas.map(displayVarga).join(' + ')} placements were consumed directly from L1 ` +
        "to confirm this domain's operative-varga promise (see varga_analysis.per_varga for " +
        'per-graha dignity and, where computed, per-varga Ashtakavarga).',
      fact_ids: vargaFactIds,
      grounded: vargaFactIds.length > 0,
    })
  }

  // 4 — contradictions (EL-57 domain-filtered).
  const contraStatus = String(inputs.contradictions['status'] ?? '')
  if (contraStatus === 'ok') {
    const items = Array.isArray(inputs.contradictions['items']) ? inputs.contradictions['items'] as Array<Record<string, unknown>> : []
    clauses.push({
      text: `${items.length} domain-tagged tension(s) surfaced for this domain (of ` +
        `${inputs.chartWideContradictionCount} chart-wide) — see contradictions for the adjudication detail.`,
      fact_ids: [],
      grounded: false,
    })
  } else if (contraStatus === 'no_contradictions_in_domain') {
    clauses.push({
      text: `No contradictions are tagged to this domain specifically (${inputs.chartWideContradictionCount} ` +
        'exist chart-wide) — an honest domain-scoped absence, not a silent omission.',
      fact_ids: [],
      grounded: false,
    })
  } else {
    clauses.push({
      text: 'No contradictions are recorded for this chart/ayanamsha at all — verify the chart ' +
        'has completed its L2 build (bo_karanajala) before reading this as a clean chart.',
      fact_ids: [],
      grounded: false,
    })
  }

  // 5 — timing (optional 5th sentence; only added when there is real signal either way).
  if (inputs.temporalOk && inputs.stageTemporalCount > 0) {
    clauses.push({
      text: 'A dated daśā-activation window is available for this domain\'s signals — see ' +
        'activating_dasha for the exact bounds.',
      fact_ids: [],
      grounded: false,
    })
  }

  const bounded = clauses.slice(0, 5)
  return {
    clauses: bounded,
    sentence_count: bounded.length,
    fact_ids_cited: Array.from(new Set(bounded.flatMap(c => c.fact_ids))),
    template: 'deterministic_v1',
    note: 'Composed by a fixed string template over already-graded terms computed above — ' +
      'no generative call in the serving path (B.10). A clause with grounded:false states an ' +
      'absence or a cross-reference pointer honestly rather than fabricating a fact_id for it.',
  }
}

async function runAssessDomain(
  args: Record<string, unknown>,
  opts: Pick<AssessDomainArgs, 'domain' | 'domain_label' | 'judgment_flag_note'>
): Promise<{ content: object; is_error: boolean }> {
  const chart_id = args['chart_id'] as string | undefined
  if (!chart_id) {
    return { content: { error: 'chart_id is required' }, is_error: true }
  }

  const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'lahiri_chitrapaksha'
  const { domain, domain_label, judgment_flag_note } = opts

  // F-021R caps: bound signals per lens + contradictions in the assembled bundle.
  const max_signals_per_lens = Math.min(
    Number(args['max_signals_per_lens'] ?? ASSESS_DEFAULT_MAX_SIGNALS_PER_LENS),
    ASSESS_MAX_SIGNALS_PER_LENS
  )
  const max_contradictions = Math.min(
    Number(args['max_contradictions'] ?? ASSESS_DEFAULT_MAX_CONTRADICTIONS),
    ASSESS_MAX_CONTRADICTIONS
  )

  try {
    // ── Step 1: domain reading (L2 Bodha) ──────────────────────────────────
    const { queryDomainReadingCapability } = await import(
      './L2_bodha/query_domain_reading'
    )
    const domainResult = await queryDomainReadingCapability.handler(
      { chart_id, ayanamsha_id, domain },
      undefined
    )

    // M-12: shield Step 1 failure — return partial bundle instead of propagating
    if (domainResult.is_error) {
      return {
        content: {
          step_results: {
            domain_reading: { ok: false, error: domainResult.content },
            temporal: { ok: false },
            contradictions: { ok: false },
          },
          chart_id,
          domain,
          error: 'domain_reading step failed',
        },
        is_error: true,
      }
    }

    // ── Step 2: temporal activation window (L3 Kāla) ──────────────────────
    // Pull signal_id refs from the domain result to filter activations.
    const domainContent = domainResult.content as Record<string, unknown>

    // R6-lens-dedup (γ.E Lane E item 2): bodha_question_lenses serves one row per
    // question_type, but two question_types on the same domain can carry a byte-identical
    // `template_element_ids_jsonb.signal_ids` set (observed live, chart 482012f1: wealth's
    // "property" and "wealth" question_types both resolve to the same 336 signal_ids, same
    // order) — the SAME 1.4MB-scale ranked_signals block served twice under two labels for
    // zero new information. Collapse same-signal-set lenses into ONE served block, keeping
    // every question_type that mapped to it (nothing dropped, B.10 — just not repeated).
    // Dedup key: the ordered signal_ids array (the identity of what a lens ranked), not
    // ranked_signals (which carries denormalized per-signal text — comparing the id list is
    // cheap and exactly captures "is this the same underlying set").
    const rawLenses = Array.isArray(domainContent['question_lenses'])
      ? (domainContent['question_lenses'] as Record<string, unknown>[])
      : []
    const lensDedupSeen = new Map<string, Record<string, unknown>>()
    const lensDedupOrder: string[] = []
    for (const lens of rawLenses) {
      const tej = lens['template_element_ids_jsonb']
      const signalIds = tej && typeof tej === 'object' && Array.isArray((tej as Record<string, unknown>)['signal_ids'])
        ? (tej as Record<string, unknown>)['signal_ids']
        : null
      const dedupKey = signalIds ? JSON.stringify(signalIds) : `__no_signal_ids__:${String(lens['lens_id'] ?? '')}`
      const existing = lensDedupSeen.get(dedupKey)
      if (existing) {
        const collapsed = (existing['collapsed_question_types'] as string[] | undefined) ?? [String(existing['question_type'] ?? '')]
        existing['collapsed_question_types'] = [...collapsed, String(lens['question_type'] ?? '')]
        existing['is_deduped'] = true
      } else {
        const withDedupFlag = { ...lens, is_deduped: false }
        lensDedupSeen.set(dedupKey, withDedupFlag)
        lensDedupOrder.push(dedupKey)
      }
    }
    const dedupedLenses = lensDedupOrder.map(k => lensDedupSeen.get(k)!)
    const lensesDroppedAsDuplicate = rawLenses.length - dedupedLenses.length

    // F-021R: bound question_lenses.all_relevant_ranked_jsonb per lens.
    // The raw handler returns all rows; each can be 1–2 MB of ranked signals.
    const boundedLenses = dedupedLenses.map((lens) => {
      const arj = lens['all_relevant_ranked_jsonb']
      if (arj && typeof arj === 'object') {
        const arjObj = arj as Record<string, unknown>
        const ranked = Array.isArray(arjObj['ranked_signals'])
          ? (arjObj['ranked_signals'] as unknown[])
          : []
        if (ranked.length > max_signals_per_lens) {
          return {
            ...lens,
            all_relevant_ranked_jsonb: {
              ...arjObj,
              ranked_signals: ranked.slice(0, max_signals_per_lens),
              total_count: ranked.length,
              truncated: true,
            },
          }
        }
      }
      return lens
    })

    // M-12: null guard on signal_id_refs before use
    const signalRefs: string[] = Array.isArray(domainContent['signal_id_refs'])
      ? (domainContent['signal_id_refs'] as string[])
      : []

    const { queryTemporalActivationCapability } = await import(
      './L3_kala/query_temporal_activation'
    )
    const today = new Date().toISOString().split('T')[0]!
    const futureDate = new Date(Date.now() + 3 * 365 * 86400000)
      .toISOString()
      .split('T')[0]!

    const temporalArgs: Record<string, unknown> = {
      chart_id,
      ayanamsha_id,
      date_from: today,
      date_to: futureDate,
      top_k: 20,
    }
    if (signalRefs.length > 0) {
      temporalArgs['signal_ids'] = signalRefs
    }

    // M-12: shield Step 2 — return partial bundle on failure rather than throwing
    let temporalResult: { ok: boolean; data: unknown }
    try {
      const rawTemporal = await queryTemporalActivationCapability.handler(
        temporalArgs,
        undefined
      )
      temporalResult = { ok: !rawTemporal.is_error, data: rawTemporal.content }
    } catch (err) {
      temporalResult = { ok: false, data: { error: String(err) } }
    }

    // ── Step 3: contradictions / discoveries (L2 Bodha) ───────────────────
    const { queryContradictionsCapability } = await import(
      './L2_bodha/query_contradictions'
    )
    const contraResult = await queryContradictionsCapability.handler(
      { chart_id, ayanamsha_id, include_discoveries: true },
      undefined
    )

    const contraContent = contraResult.content as Record<string, unknown>

    // EL-57: domain filter on the contradiction surface. bodha_contradictions rows carry
    // domains_affected_array (query_contradictions.ts SELECT) but query_contradictions itself
    // has no domain param (chart/ayanamsha-scoped only, by design — it is a shared L2 leaf) —
    // filtered HERE, at this domain-specific assembly boundary, so assess_wealth never shows a
    // career-only tension pair under "wealth contradictions". The chart-wide count is always
    // retained alongside the filtered one so the caller can tell "domain-empty" from "chart-empty".
    const rawContraItems = Array.isArray(contraContent['contradictions'])
      ? (contraContent['contradictions'] as Record<string, unknown>[])
      : []
    const chartWideContradictionCount = rawContraItems.length
    const domainFilteredContraItems = rawContraItems.filter(row => {
      const arr = row['domains_affected_array']
      return Array.isArray(arr) && arr.includes(domain)
    })

    const contradictions =
      contraResult.is_error
        ? { status: 'error', note: String(contraContent['error']) }
        : chartWideContradictionCount === 0
        ? {
            status: 'no_data',
            note:
              contraContent['contradictions_note'] ??
              'bodha_contradictions: 0 rows for this chart/ayanamsha — verify chart has been built (bo_karanajala).',
          }
        : domainFilteredContraItems.length === 0
        ? {
            // EL-57: honest, EXPLICIT empty state — "N contradictions exist for this chart, but
            // none tag this domain" — distinct from the chart-wide no_data case above, and never
            // a silent omission (B.10): the chart-wide count is stated, plus a drill to the
            // unfiltered surface.
            status: 'no_contradictions_in_domain',
            chart_wide_contradiction_count: chartWideContradictionCount,
            note: `${chartWideContradictionCount} contradiction(s) exist for this chart/ayanamsha, ` +
              `but none are tagged domains_affected_array ∋ "${domain}" — no contradictions ` +
              'found for this domain specifically. Full chart-wide set via query_contradictions (unfiltered).',
            drill_uri: 'marsys://tool/L2/query_contradictions',
          }
        : {
            status: 'ok',
            items: domainFilteredContraItems,
            chart_wide_contradiction_count: chartWideContradictionCount,
            domain_filtered: true,
            discoveries: (() => {
              const capped = capArray(contraContent['discoveries'], ASSESS_DEFAULT_MAX_DISCOVERIES, 'marsys://tool/L2/query_contradictions')
              return { items: capped.items, total_count: capped.total_count, truncated: capped.truncated, drill_uri: capped.drill_uri }
            })(),
          }

    // ── Step 4: composite-ranked signals + ranking_basis (BA-P2 envelope retrofit) ──
    // Calls query_signals (which now composite-ranks when domain is specified, wired in BA-P2 Step 2).
    // Non-fatal: a failure here returns salience_fallback ranking_basis, not a broken bundle.
    let p2RankingBasis: Record<string, unknown> = {
      mode: 'salience_fallback',
      priors_version: '0.9-prov',
      domain,
    }
    let topCompositeSignals: Record<string, unknown>[] = []

    try {
      const { querySignalsCapability } = await import('./L2_bodha/query_signals')
      const signalsResult = await querySignalsCapability.handler(
        { chart_id, ayanamsha_id, domain, top_k: 50 },
        undefined
      )
      if (!signalsResult.is_error) {
        const sc = signalsResult.content as Record<string, unknown>
        topCompositeSignals = Array.isArray(sc['signals'])
          ? (sc['signals'] as Record<string, unknown>[])
          : []
        if (sc['ranking_basis']) {
          p2RankingBasis = sc['ranking_basis'] as Record<string, unknown>
        }
      }
    } catch {
      // Non-fatal: ranking_basis falls back to salience_fallback
    }

    // ── Step 5: direct varga/AV consumption (EL-45) — never a "see other tool" stub ──
    const vargaAnalysis = await buildVargaAnalysisDirect(chart_id, ayanamsha_id, domain)

    // ── Assemble verdict_skeleton (deterministic — no LLM inference) ──────────
    // Groups signals by reasoning-chain stage.
    // Stages: yoga/configuration → karaka_alignment → lord/dispositor (parivartana)
    //         → strength (L1) → varga → temporal → contradiction_pairs
    const stc = (s: Record<string, unknown>) => String(s['signal_type_class'] ?? '')
    const sss = (s: Record<string, unknown>) => String(s['source_subsystem'] ?? '')

    const pickSignals = (sigs: Record<string, unknown>[], n: number) =>
      sigs.slice(0, n).map(s => ({
        signal_id:          s['signal_id'],
        signal_type_class:  s['signal_type_class'],
        summary:            s['signal_summary_text'],
        source_subsystem:   s['source_subsystem'],
        composite_score:    s['composite_score'] ?? null,
        final_rank_score:   s['final_rank_score'] ?? null,
        // WP-1.3(ii) (EL-44 verdict layer): carry the L1 fact_ids this signal is grounded on
        // through to the verdict-layer sentence builder — every verdict clause must cite real
        // fact_ids (B.3), never a bare prose claim.
        constituent_fact_ids: Array.isArray(s['constituent_facts_array']) ? s['constituent_facts_array'] : [],
      }))

    // WP-1.3(i) / R-40 — verdict_skeleton serving fix. Root-cause (prod, chart 482012f1 lahiri):
    //   (a) the `lord` bucket filtered on signal_type_class='relationship' — a DOMAIN name,
    //       never a class; ZERO signals carry it → the bucket was PERMANENTLY empty.
    //   (b) the `strength` bucket filtered on class='magnitude' + source_subsystem=
    //       'strength_ashtakavarga' — neither value exists in bodha_msr_signals (graha strength
    //       is an L1 chart_facts concept, not an MSR signal class) → PERMANENTLY empty.
    //   (c) all structural buckets sliced from the top-50 composite pool, which is ~82%
    //       composite_state, starving the rare classes (configuration=29, yoga=15,
    //       parivartana=42, varga=9 chart-wide) → those stages came back empty though the data
    //       exists.
    // Fix: one bounded, salience-ordered stratified query restricted to the stage-bearing
    // classes, so each structural stage draws from its REAL population (not a composite-ranked
    // slice). Deterministic; no LLM. Non-fatal — falls back to the composite pool on error.
    const STAGE_CLASSES = ['configuration', 'yoga', 'karaka_alignment', 'parivartana', 'varga_pattern']
    let stagePool: Record<string, unknown>[] = []
    try {
      const poolRes = await query<Record<string, unknown>>(
        // R6-composite-score (γ.E Lane E item 2): pulled in the columns applyCompositeRanking
        // needs (signal_type_id, signal_tradition, configuration_jsonb, constituent_facts_array,
        // graph_node_strength_contribution_jsonb) — previously this SELECT carried only enough
        // to bucket-classify a row, so every by_stage signal below served `composite_score: null`
        // (uncomputed, not trimmed — the stagePool rows never went through the ranker at all).
        `SELECT signal_id, signal_type_id, signal_type_class, signal_tradition, source_subsystem,
                signal_summary_text, computed_salience, domains_affected_array,
                constituent_facts_array, configuration_jsonb,
                graph_node_strength_contribution_jsonb
         FROM bodha_msr_signals
         WHERE chart_id = $1 AND ayanamsha_id = $2 AND $3 = ANY(domains_affected_array)
           AND (signal_type_class = ANY($4) OR source_subsystem = 'varga')
         ORDER BY computed_salience DESC NULLS LAST
         LIMIT 200`,
        [chart_id, ayanamsha_id, domain, STAGE_CLASSES],
      )
      stagePool = poolRes.rows
    } catch {
      // Non-fatal: structural stages fall back to the top-50 composite pool.
      stagePool = topCompositeSignals
    }

    // R6-composite-score: run the SAME 4D composite ranker query_signals uses over stagePool,
    // so by_stage.{yoga,karaka,lord,varga} carry real composite_score/final_rank_score instead
    // of null. Non-fatal — on any failure the stage buckets keep their raw stagePool order and
    // composite_score stays honestly null (never fabricated), same as before this fix.
    // l1ctx is hoisted so the graha-strength ranking below (EL-59/20 rank vocabulary) reuses the
    // same fetch (fetchL1Context caches per chart/ayanamsha/date — one real DB round-trip either way).
    let l1ctx: Awaited<ReturnType<typeof fetchL1Context>> | null = null
    let scoredStagePool: Record<string, unknown>[] = stagePool
    try {
      const as_of_date = new Date().toISOString().split('T')[0]!
      l1ctx = await fetchL1Context(chart_id, ayanamsha_id, as_of_date)
      if (stagePool.length > 0) {
        const scored = applyCompositeRanking(stagePool as unknown as MsrSignalRow[], l1ctx, domain)
        scoredStagePool = scored.map(s => {
          const { _subscores, ...rest } = s
          void _subscores
          return rest as unknown as Record<string, unknown>
        })
      }
    } catch {
      // Non-fatal: falls back to raw stagePool (composite_score stays null, honestly).
      scoredStagePool = stagePool
    }
    stagePool = scoredStagePool

    // ── EL-59/20: graha shadbala rank statements (ONE rank vocabulary) ────────────
    // Fills the honest gap noted at stage_status.strength (below): "strength" has no MSR
    // signal class to bucket from bodha_msr_signals — but the REAL L1 shadbala data used to
    // FEED that gap-note IS already fetched above (l1ctx.graha_map) and was previously
    // discarded. Every rank here is served with rank_basis + population_size (rank_vocabulary.ts)
    // — never a bare `rank: n` (the Venus weakest_rank_in_chart:5-vs-"weakest of 7" regression
    // this closes for this file's own served surface).
    let grahaStrengthRanking: ReturnType<typeof rankGrahasByShadbala> = []
    if (l1ctx) {
      const inputs: GrahaShadbalaInput[] = Object.entries(l1ctx.graha_map).map(([graha, info]) => ({
        graha,
        shadbala_total: info.shadbala_total,
      }))
      grahaStrengthRanking = rankGrahasByShadbala(inputs, 'classical_7')
    }

    const temporalContent = (temporalResult.data ?? {}) as Record<string, unknown>
    const contrItems = contradictions.status === 'ok'
      ? ((contradictions as Record<string, unknown>)['items'] as unknown[] ?? [])
      : []

    const stageYoga     = pickSignals(stagePool.filter(s => ['configuration', 'yoga'].includes(stc(s))), 5)
    const stageKaraka   = pickSignals(stagePool.filter(s => stc(s) === 'karaka_alignment'), 5)
    const stageLord     = pickSignals(stagePool.filter(s => stc(s) === 'parivartana'), 5)
    const stageVarga    = pickSignals(stagePool.filter(s => sss(s) === 'varga' || stc(s) === 'varga_pattern'), 5)
    const stageTemporal = temporalResult.ok
      ? (temporalContent['activations'] as unknown[] ?? []).slice(0, 5)
      : []
    const stageContra   = contrItems.slice(0, 5)

    // ── Y-2 (D-1.6 Lane S-3, CRIT): firings-authoritative bearing yogas ────────────────
    // Before this fix, assess_*'s ONLY yoga surface was `stageYoga` above — a slice of
    // bodha_msr_signals (signal_type_class in configuration,yoga), which are single-pass
    // CATALOG label matches (JL-004), not cross-verified confirmed firings (the same
    // provenance ganita_yogas_get's yoga_label rows carry — see CLAUDE.md §N.6.1: "never
    // present catalog/label matches as confirmed findings"). judgment_query already fixed
    // this for its own bearing_yogas (A3/CR-92/R-3); assess_* had not been wired to the
    // same firings-authoritative source (ga_yoga_firings, via ganita_yoga_firings_get).
    // This block adds that source, following the identical pattern: real fired rows first
    // (source: 'ga_yoga_firings', domain_match flag, bhaṅga-aware), the MSR-derived
    // stageYoga slice demoted to corroboration-only via stage_status's source string below.
    let bearingYogaFirings: Record<string, unknown>[] = []
    const yogaFactIds = new Set<string>()
    try {
      const domainSpec = SHASTRA_MAP[domain]
      const domainActors = new Set<string>()
      if (domainSpec) {
        for (const k of domainSpec.karakas) domainActors.add(k.toLowerCase())
        try {
          const lordRes = await resolveAddress(
            chart_id, { type: 'lord_of', house: domainSpec.bhava }, { ayanamsha_id },
          )
          const lordEntity = lordRes.entities[0] as { kind?: string; graha?: string } | undefined
          if (lordEntity?.kind === 'graha' && lordEntity.graha) {
            domainActors.add(lordEntity.graha.toLowerCase())
          }
        } catch {
          // Non-fatal: domain_match degrades to karaka-only matching if bhāveśa resolution fails.
        }
      }
      const { getYogaFiringsCapability } = await import('./L1_ganita/get_yoga_firings')
      const firingsRes = await getYogaFiringsCapability.handler(
        { chart_id, ayanamsha_id, fired: true, limit: 50 },
        undefined,
      )
      if (!firingsRes.is_error) {
        const fc = firingsRes.content as Record<string, unknown>
        const firedRows = (fc['rows'] as Record<string, unknown>[]) ?? []
        bearingYogaFirings = firedRows.map(r => {
          const constituentPlanets = ((r['constituent_planets'] as string[] | null) ?? []).map(p => p.toLowerCase())
          const domainMatch = domainActors.size > 0 && constituentPlanets.length > 0
            && constituentPlanets.every(p => domainActors.has(p))
          if (domainMatch) {
            for (const fid of (r['constituent_fact_ids'] as string[] | null) ?? []) yogaFactIds.add(fid)
          }
          const rawStrength = typeof r['strength'] === 'number' ? r['strength'] as number : Number(r['strength'] ?? 0)
          const bhangaActive = r['bhanga_active'] === true
          return {
            yoga_canonical_id: r['yoga_canonical_id'],
            strength: r['strength'],
            strength_label: r['strength_label'],
            bhanga_active: r['bhanga_active'],
            bhanga_rule_fired: r['bhanga_rule_fired'],
            constituent_planets: r['constituent_planets'],
            constituent_houses: r['constituent_houses'],
            source: 'ga_yoga_firings',
            domain_match: domainMatch,
            // bhaṅga-discounted display weight (never a verdict score here — assess_* has no
            // composite verdict term; judgment_query owns that computation).
            effective_weight: Number.isFinite(rawStrength)
              ? Math.round(rawStrength * (bhangaActive ? ASSESS_YOGA_BHANGA_DISCOUNT : 1) * 10000) / 10000
              : null,
          }
        })
        // Domain-matching firings sort first (same defensive rationale as judgment_query's
        // D-1.5a wave-gate fix): a response-budget trim must not silently drop a
        // domain-relevant confirmed firing while keeping a higher-strength but irrelevant one.
        bearingYogaFirings.sort((a, b) => {
          const am = a['domain_match'] === true, bm = b['domain_match'] === true
          if (am !== bm) return am ? -1 : 1
          const as_ = typeof a['strength'] === 'number' ? a['strength'] as number : 0
          const bs_ = typeof b['strength'] === 'number' ? b['strength'] as number : 0
          return bs_ - as_
        })
      }
    } catch {
      // Non-fatal: bearing_yoga_firings degrades to empty; stageYoga (MSR catalog) still served.
    }

    // Honest empty-reasons (never faked). See module-level TEMPORAL_EMPTY_REASON for the
    // temporal-stage explanation (hoisted + exported for regression-protection testing).
    const stage_status: Record<string, Record<string, unknown>> = {
      // Y-2: stageYoga (bodha_msr_signals) is single-pass catalog-label corroboration only
      // (JL-004) — bearing_yoga_firings (ga_yoga_firings, above) is the firings-authoritative
      // confirmed-finding surface. §N.6.1: a caller must never read this stage's count as
      // "N confirmed yogas."
      yoga:     {
        count: stageYoga.length,
        source: 'bodha_msr_signals (signal_type_class in configuration,yoga) — catalog-label ' +
          'corroboration only (JL-004); see bearing_yoga_firings (ga_yoga_firings) for the ' +
          'firings-authoritative confirmed set',
      },
      karaka:   { count: stageKaraka.length, source: 'bodha_msr_signals (signal_type_class=karaka_alignment)' },
      lord:     { count: stageLord.length,   source: 'bodha_msr_signals (signal_type_class=parivartana — lord/dispositor exchange)' },
      // strength has NO MSR signal source — it is an L1 chart_facts (shadbala/ashtakavarga)
      // concept, so `by_stage.strength` (the MSR-signal-bucket shape every other stage uses)
      // stays honestly empty rather than a dead filter. EL-59/20: the REAL L1 shadbala data
      // that grounds this gap-note is surfaced separately as `graha_shadbala_ranking` — ONE
      // rank vocabulary (rank_vocabulary.ts: rank + population_size + rank_basis on every
      // entry), so a caller gets the actual strength ranking this stage's MSR-shaped bucket
      // structurally cannot hold, instead of only a pointer to go fetch it elsewhere.
      strength: {
        count: 0,
        source: 'L1 chart_facts (shadbala / ashtakavarga) — graha strength is not an MSR signal class',
        drill_uri: 'marsys://tool/L2/get_domain_reading',
        graha_shadbala_ranking: grahaStrengthRanking,
      },
      varga:    { count: stageVarga.length,  source: 'bodha_msr_signals (source_subsystem=varga)' },
      temporal: {
        count: stageTemporal.length,
        source: 'kala_activation (L3)',
        ...(stageTemporal.length === 0 ? { empty_reason: TEMPORAL_EMPTY_REASON } : {}),
      },
      contradiction_pairs: {
        count: stageContra.length,
        source: 'bodha_contradictions (L2 bo_karanajala)',
        // EL-57: the honest empty reason now distinguishes "0 rows chart-wide" (no_data) from
        // "N rows chart-wide, 0 tag this domain" (no_contradictions_in_domain) — never one
        // generic "0 rows" message papering over which case actually happened.
        ...(stageContra.length === 0
          ? {
              empty_reason:
                contradictions.status === 'no_contradictions_in_domain'
                  ? (contradictions as Record<string, unknown>)['note']
                  : 'bodha_contradictions: 0 rows for this chart/ayanamsha (bo_karanajala) — no_data, not a serving trim.',
            }
          : {}),
      },
    }

    // WP-1.8 (cross-surface inconsistency): assess_*'s headline top-10 is the SAME composite
    // ranking get_signals produces WHEN CALLED WITH THIS DOMAIN — but a consumer who calls
    // get_signals WITHOUT a domain gets a chart-wide salience_fallback ordering that shares ~0
    // of these signals, making the two surfaces look contradictory. We (a) prove the agreement by
    // deriving top_10 from the identical query_signals call, and (b) name the exact reproducing
    // call so the surfaces are explicitly reconciled, never silently divergent.
    const top10 = pickSignals(topCompositeSignals, 10)
    const cross_surface = {
      agrees_with: 'get_signals',
      reproducing_call: { tool: 'get_signals', args: { chart_id, ayanamsha_id, domain, top_k: 10 } },
      ranking_mode: (p2RankingBasis['mode'] as string) ?? 'composite_4d',
      note:
        `This top-10 is byte-identical to get_signals({domain:"${domain}", top_k:10}) — the two ` +
        `surfaces share one ranking path (query_signals composite). NOTE: get_signals called ` +
        `WITHOUT a domain uses chart-wide salience ranking and will surface DIFFERENT signals; ` +
        `that is not a contradiction — pass domain:"${domain}" to reproduce this ordering.`,
    }

    const verdict_skeleton = {
      top_10_composite: top10,
      cross_surface,
      // Y-2: firings-authoritative confirmed yogas (ga_yoga_firings), domain-matched against
      // this domain's bhāveśa + kāraka(s) — served ahead of/separate from by_stage.yoga's
      // MSR catalog-label corroboration (§N.6.1).
      bearing_yoga_firings: bearingYogaFirings,
      by_stage: {
        yoga:      stageYoga,
        karaka:    stageKaraka,
        lord:      stageLord,
        strength:  [] as unknown[],
        varga:     stageVarga,
        temporal:  stageTemporal,
        contradiction_pairs: stageContra,
      },
      stage_status,
      note: 'Deterministic classification by signal_type_class + source_subsystem over a ' +
        'salience-ordered stratified pool (top_10_composite uses the domain composite ranking). ' +
        'No LLM inference. stage_status discloses each stage\'s provenance + honest empty reasons ' +
        '(temporal is PENDING WP-2.1 per R-45/R-40; strength is an L1 concept). Drill via ' +
        'query_signals / get_domain_reading for the full per-class sets. bearing_yoga_firings ' +
        '(ga_yoga_firings) is the firings-authoritative yoga source (Y-2, D-1.6/S-3) — ' +
        'by_stage.yoga (bodha_msr_signals) is catalog-label corroboration only.',
    }

    // ── Assemble reconciled bundle ─────────────────────────────────────────

    // F-021R: cap contradictions in the assembled bundle.
    // queryContradictionsCapability returns all rows (5,000+/chart); slice to max_contradictions.
    let boundedContradictions: object
    if (contradictions.status === 'ok') {
      const items = Array.isArray((contradictions as Record<string, unknown>)['items'])
        ? ((contradictions as Record<string, unknown>)['items'] as unknown[])
        : []
      const totalCount = items.length
      const cappedItems = items.slice(0, max_contradictions)
      boundedContradictions = {
        ...contradictions,
        items: cappedItems,
        total_count: totalCount,
        returned_count: cappedItems.length,
        truncated: totalCount > max_contradictions,
        drill_uri: totalCount > max_contradictions
          ? 'marsys://tool/L2/query_contradictions'
          : undefined,
      }
    } else {
      boundedContradictions = contradictions
    }

    // ── T5 (PŪRTI): the three computed-but-never-joined classical legs ─────────────
    // Same legs judgment_query now serves — folded into assess_* so a consumer of the
    // reconciled summary also gets the fired sensitive degrees (MC-030: Mars-in-puṣkara),
    // the KP cuspal wealth/career chain (MC-031: previously tail-only), and the gochara
    // sweep (MC-033), each in its own slot. Serving-only reads (§N.5); non-fatal on error.
    const t5Spec = SHASTRA_MAP[domain]
    const t5SignalDomain = t5Spec?.signal_domain ?? domain
    const [t5Sensitive, t5Kp, t5Gochara] = await Promise.all([
      fetchSensitiveDegreeFirings(chart_id, ayanamsha_id),
      fetchKpCuspChain(chart_id, ayanamsha_id, DOMAIN_KP_CUSPS[domain] ?? (t5Spec ? [t5Spec.bhava as number] : [])),
      fetchGocharaSweep(chart_id, t5SignalDomain, today),
    ])
    const t5KpCusps = DOMAIN_KP_CUSPS[domain] ?? (t5Spec ? [t5Spec.bhava as number] : [])
    const reading_checklist_units: ChecklistUnit[] = [
      { unit: 'bhava_bhavesha', state: 'served', detail: 'domain reading (question lenses + bhāveśa via CDLM cells)' },
      { unit: 'karakas', state: 'served', detail: t5Spec ? t5Spec.karakas.join(', ') : domain },
      { unit: 'operative_vargas', state: (vargaAnalysis && Object.keys(vargaAnalysis).length > 0) ? 'served' : 'not_computed', detail: (DOMAIN_DIRECT_VARGAS[domain] ?? []).join('+') + ' dignity + AV' },
      { unit: 'ashtakavarga', state: 'served', detail: 'per-varga pinda/sarva folded into varga_analysis' },
      { unit: 'special_lagnas', state: DOMAIN_INDU_LAGNA.has(domain) ? 'served' : 'not_joined', detail: DOMAIN_INDU_LAGNA.has(domain) ? 'Indu Lagna (Jaimini wealth lagna)' : 'no special-lagna leg for this domain', ...(DOMAIN_INDU_LAGNA.has(domain) ? {} : { drill: 'ganita_special_lagnas_get' }) },
      { unit: 'sensitive_degree_firings', state: t5Sensitive.firings.length > 0 ? 'served' : (t5Sensitive.available ? 'empty_for_this_chart' : 'not_computed'), count: t5Sensitive.firings.length, detail: 'puṣkara/gaṇḍānta/mṛtyu-bhāga/kartari fired-state (MC-030)' },
      { unit: 'kp_cusp_chain', state: t5Kp.cusps.length > 0 ? 'served' : 'not_computed', count: t5Kp.cusps.length, detail: `KP sub-lord chain for cusp(s) ${t5KpCusps.join('/')} (MC-031)` },
      { unit: 'yogi_avayogi', state: 'not_yet_available', detail: 'yogi/avayogi asset being built in a parallel track (T6) — slot wired, honestly absent' },
      { unit: 'dasha_levels', state: temporalResult.ok && stageTemporal.length > 0 ? 'served' : 'empty_for_this_chart', detail: 'kala activation windows (temporal stage)' },
      { unit: 'gochara_sweep', state: t5Gochara.domain_covered ? 'served' : (t5Gochara.available ? 'empty_for_this_chart' : 'not_computed'), count: t5Gochara.upcoming_window_count, detail: `forward transit windows, domain='${t5SignalDomain}' (MC-033)` },
      { unit: 'bearing_yoga_firings', state: bearingYogaFirings.length > 0 ? 'served' : 'empty_for_this_chart', count: bearingYogaFirings.length, detail: 'ga_yoga_firings (firings-authoritative)' },
      { unit: 'contradictions', state: (contradictions.status === 'ok' && Array.isArray((contradictions as Record<string, unknown>)['items']) && ((contradictions as Record<string, unknown>)['items'] as unknown[]).length > 0) ? 'served' : 'empty_for_this_chart', detail: 'bodha_contradictions dissent surface' },
      { unit: 'tajaka', state: 'not_joined', detail: 'annual (varṣaphala/tājaka) not folded into the natal assessment', drill: 'ganita_tajaka_get' },
    ]
    const t5Exhaustiveness = checklistExhaustiveness(reading_checklist_units)
    const reading_checklist = {
      units: reading_checklist_units,
      ...t5Exhaustiveness,
      note: 'The classical checklist, served: each unit names whether THIS response carried ' +
        'it and — for every absent box — WHY. not_joined units carry a live drill handle. When ' +
        'not every unit is served/empty, the response self-discloses non_exhaustive: ' +
        '"salience_sampled" (an honest "this is not the whole territory").',
    }

    // EL-44: the grounded verdict layer — 3-5 plain-language sentences, deterministic
    // template, every clause citing its real fact_ids (or honestly reporting it has none).
    const verdict = buildVerdictLayer({
      domain_label,
      top10,
      bearingYogaFirings,
      domainMatchedYogaFactIds: Array.from(yogaFactIds),
      vargaAnalysis,
      contradictions,
      chartWideContradictionCount,
      temporalOk: temporalResult.ok,
      stageTemporalCount: stageTemporal.length,
    })

    return {
      content: {
        domain,
        domain_label,
        chart_id,
        ayanamsha_id,
        ranking_basis: p2RankingBasis,
        verdict,
        // T5 (PŪRTI): the served completeness receipt — which classical units this
        // response carried, and WHY each absent one is absent (the Offer-Law fix).
        reading_checklist,
        verdict_skeleton,
        step_results: {
          domain_reading: { ok: true },
          temporal: { ok: temporalResult.ok },
          contradictions: { ok: true },
          composite_ranking: { ok: topCompositeSignals.length > 0 },
        },
        house_analysis: {
          question_lenses: boundedLenses,
          lens_count: domainContent['lens_count'] ?? 0,
          lenses_served_count: boundedLenses.length,
          lenses_deduped_count: lensesDroppedAsDuplicate,
          signals_per_lens_cap: max_signals_per_lens,
          note: 'bodha_question_lenses returned chart-wide (no domain column); reconcile via cdlm_cells. all_relevant_ranked_jsonb capped per lens — drill via get_domain_reading for full signal lists.' +
            (lensesDroppedAsDuplicate > 0
              ? ` ${lensesDroppedAsDuplicate} lens(es) with byte-identical signal_ids collapsed into their surviving twin (see collapsed_question_types on the merged lens) — never repeat the same ranked-signal block under two labels.`
              : ''),
        },
        karaka_analysis: (() => {
          // R6 3b-budgets (R-1/R-8): cdlm_cells was fully unbounded — the largest single
          // contributor to the live-measured 1.04MB assess_career payload. Capped + counted
          // like every other F-021R section; full detail remains reachable via get_domain_reading.
          const capped = capArray(domainContent['cdlm_cells'], ASSESS_DEFAULT_MAX_CDLM_CELLS, 'marsys://tool/L2/query_domain_reading')
          return {
            cdlm_cells: capped.items,
            cdlm_cell_count: domainContent['cdlm_cell_count'] ?? capped.total_count,
            cdlm_cells_returned: capped.items.length,
            cdlm_cells_truncated: capped.truncated,
            ...(capped.truncated ? { cdlm_cells_drill_uri: capped.drill_uri } : {}),
          }
        })(),
        // EL-45: direct consumption, not a "see other tool" stub — see buildVargaAnalysisDirect.
        varga_analysis: vargaAnalysis,
        // T5 (PŪRTI): the three computed-but-never-joined classical legs, served inline.
        sensitive_degree_firings: t5Sensitive.firings,
        kp_cusp_chain: { cusps: t5Kp.cusps, note: t5Kp.note },
        gochara_sweep: {
          domain: t5SignalDomain,
          domain_covered: t5Gochara.domain_covered,
          upcoming_window_count: t5Gochara.upcoming_window_count,
          valence_breakdown: t5Gochara.valence_breakdown,
          window_range: t5Gochara.window_range,
          top_windows: t5Gochara.windows,
          note: t5Gochara.note,
        },
        activating_dasha: (() => {
          const cappedActivations = temporalResult.ok
            ? capArray(temporalContent['activations'], ASSESS_DEFAULT_MAX_ACTIVATIONS, 'marsys://tool/L3/query_temporal_activation')
            : { items: [], total_count: 0, truncated: false }
          const cappedPredicates = temporalResult.ok
            ? capArray(temporalContent['predicates'], ASSESS_DEFAULT_MAX_PREDICATES, 'marsys://tool/L3/query_temporal_activation')
            : { items: [], total_count: 0, truncated: false }
          return {
            activations: cappedActivations.items,
            activations_total_count: cappedActivations.total_count,
            activations_truncated: cappedActivations.truncated,
            activation_count: temporalResult.ok ? (temporalContent['activation_count'] ?? cappedActivations.total_count) : 0,
            predicates: cappedPredicates.items,
            predicates_total_count: cappedPredicates.total_count,
            predicates_truncated: cappedPredicates.truncated,
            window: { date_from: today, date_to: futureDate },
            signal_id_refs: temporalResult.ok ? (temporalContent['signal_id_refs'] ?? []) : [],
            ...(temporalResult.ok ? {} : { partial_failure: temporalContent['error'] }),
          }
        })(),
        contradictions: boundedContradictions,
        // Y-11 (shared with S-2d): bearing_yoga_firings' domain-matching rows cite their real
        // ga_yoga_firings.constituent_fact_ids (→ chart_facts.fact_id, §N.5) — never a shared stub.
        yoga_fact_ids: Array.from(yogaFactIds),
        citations: {
          note: 'Classical citations available via classical_attribution_lookup for signal_id_refs above.',
          drill_uri: 'marsys://tool/L2/classical_attribution_lookup',
          signal_id_refs: signalRefs,
        },
        judgment_flags: [
          judgmentFlag('domain_inference_requires_acharya_validation', judgment_flag_note, 'warning'),
          ...(bearingYogaFirings.length === 0
            ? [judgmentFlag(
                'bearing_yogas_empty',
                'no fired rows returned from ga_yoga_firings ' +
                  '(firings-authoritative) for this chart/ayanamsha — honest absence, not fabricated.',
                'info',
              )]
            : !bearingYogaFirings.some(y => y['domain_match'] === true)
            ? [judgmentFlag(
                'bearing_yogas_no_domain_match',
                `${bearingYogaFirings.length} yoga(s) ` +
                  `fired on this chart but none name only this domain's bhāveśa/kāraka(s) — shown ` +
                  'for context (Y-2, D-1.6/S-3).',
                'info',
              )]
            : []),
          judgmentFlag(
            'catalog_only_rows_present',
            'bearing_yoga_firings (ga_yoga_firings) is the firings-authoritative source; ' +
              'by_stage.yoga / verdict_skeleton.by_stage.yoga (bodha_msr_signals) are single-pass ' +
              'catalog-label matches (JL-004) and must never be read as confirmed findings ' +
              '(CLAUDE.md §N.6.1).',
            'info',
          ),
        ] satisfies JudgmentFlagEntry[],
        provenance: {
          tables: [
            'bodha_msr_signals',
            'bodha_question_lenses',
            'bodha_cdlm_cells',
            'kala_activation',
            'kala_activation_predicates',
            'bodha_contradictions',
            'bodha_discoveries',
          ],
          handlers_called: [
            'marsys://tool/L2/query_domain_reading',
            'marsys://tool/L3/query_temporal_activation',
            'marsys://tool/L2/query_contradictions',
            'marsys://tool/L2/query_signals (BA-P2 composite ranking)',
          ],
          caps_applied: {
            max_signals_per_lens,
            max_contradictions,
            composite_signals_fetched: topCompositeSignals.length,
            note: 'F-021R bounding: question_lenses bounded per-lens; contradictions capped. BA-P2: composite 4D ranking applied to top-50 signals. Drill via listed URIs for full data.',
          },
        },
      },
      is_error: false,
    }
  } catch (err) {
    return {
      content: { error: String(err), chart_id, domain },
      is_error: true,
    }
  }
}

// ── R3.1a: assess_marriage ────────────────────────────────────────────────────

const assessMarriageCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L-DOMAIN/assess_marriage',
  type: 'tool',
  layer: 'L2',
  name: 'assess_marriage',
  scope: 'per_chart',

  description: [
    'Reconciled marriage/partnership assessment for a chart.',
    '7th lord + Venus kāraka + D9 analysis + bhāvat-bhāva + afflictions + activating dasha window + classical citations.',
    'Orchestrates query_domain_reading (L2 Bodha: CDLM cells + question lenses for relationship domain),',
    'query_temporal_activation (L3 Kāla: dasha activation window for domain signal refs),',
    'and query_contradictions (L2 Bodha: contradiction/discovery surface).',
    'Returns convergences and tensions with judgment_flags marking inferences requiring acharya validation.',
    'Varga refinement (D9) available via chart_facts_query drill (marsys://tool/L1/chart_facts_query).',
    'chart_id is required — never defaulted (principle #14).',
  ].join(' '),

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to use (default: 'LAHIRI').",
    },
    max_signals_per_lens: {
      type: 'number',
      description: `Max ranked signals per question lens (default: ${ASSESS_DEFAULT_MAX_SIGNALS_PER_LENS}, max: ${ASSESS_MAX_SIGNALS_PER_LENS}). Drill via get_domain_reading for full signal lists.`,
    },
    max_contradictions: {
      type: 'number',
      description: `Max contradictions in bundle (default: ${ASSESS_DEFAULT_MAX_CONTRADICTIONS}, max: ${ASSESS_MAX_CONTRADICTIONS}). Remainder via query_contradictions.`,
    },
  },

  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L1/chart_facts_query',
    'marsys://tool/L2/query_signals',
    'marsys://tool/L2/classical_attribution_lookup',
    'marsys://tool/L2/get_domain_reading',
    'marsys://tool/L2/query_contradictions',
  ],

  llm_hints: {
    agentic: { cost_class: 'expensive', cacheable: true },
    bulk_context: { pre_fetch_priority: 30 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    return runAssessDomain(args, {
      domain: 'relationship',
      domain_label: 'Marriage / Partnership',
      judgment_flag_note:
        'Marriage domain synthesis reconciles 7th lord + Venus kāraka + D9 from L1 chart_facts (via drill). CDLM cell reconciliation and affliction assessment require acharya review of the assembled bundle.',
    })
  },
}

// ── R3.1b: assess_career ──────────────────────────────────────────────────────

const assessCareerCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L-DOMAIN/assess_career',
  type: 'tool',
  layer: 'L2',
  name: 'assess_career',
  scope: 'per_chart',

  description: [
    'Reconciled career/vocation assessment for a chart.',
    '10th lord + Saturn kāraka + D10 analysis + yogas + activating dasha window + classical citations.',
    'Orchestrates query_domain_reading (L2 Bodha: CDLM cells + question lenses for career domain),',
    'query_temporal_activation (L3 Kāla: dasha activation window for domain signal refs),',
    'and query_contradictions (L2 Bodha: contradiction/discovery surface).',
    'Returns convergences and tensions with judgment_flags marking inferences requiring acharya validation.',
    'Varga refinement (D10) available via chart_facts_query drill (marsys://tool/L1/chart_facts_query).',
    'chart_id is required — never defaulted (principle #14).',
  ].join(' '),

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to use (default: 'LAHIRI').",
    },
    max_signals_per_lens: {
      type: 'number',
      description: `Max ranked signals per question lens (default: ${ASSESS_DEFAULT_MAX_SIGNALS_PER_LENS}, max: ${ASSESS_MAX_SIGNALS_PER_LENS}). Drill via get_domain_reading for full signal lists.`,
    },
    max_contradictions: {
      type: 'number',
      description: `Max contradictions in bundle (default: ${ASSESS_DEFAULT_MAX_CONTRADICTIONS}, max: ${ASSESS_MAX_CONTRADICTIONS}). Remainder via query_contradictions.`,
    },
  },

  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L1/chart_facts_query',
    'marsys://tool/L2/query_signals',
    'marsys://tool/L2/classical_attribution_lookup',
    'marsys://tool/L2/get_domain_reading',
    'marsys://tool/L2/query_contradictions',
  ],

  llm_hints: {
    agentic: { cost_class: 'expensive', cacheable: true },
    bulk_context: { pre_fetch_priority: 30 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    return runAssessDomain(args, {
      domain: 'career',
      domain_label: 'Career / Vocation',
      judgment_flag_note:
        'Career domain synthesis reconciles 10th lord + Saturn kāraka + D10 from L1 chart_facts (via drill). Yoga detection and dasha activation windows require acharya review of the assembled bundle.',
    })
  },
}

// ── R3.1c: assess_health ─────────────────────────────────────────────────────

const assessHealthCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L-DOMAIN/assess_health',
  type: 'tool',
  layer: 'L2',
  name: 'assess_health',
  scope: 'per_chart',

  description: [
    'Reconciled health/vitality assessment for a chart.',
    '1st + 6th + 8th lords + Sun kāraka + afflictions + D1/D6 analysis + activating dasha window.',
    'Orchestrates query_domain_reading (L2 Bodha: CDLM cells + question lenses for health domain),',
    'query_temporal_activation (L3 Kāla: dasha activation window for domain signal refs),',
    'and query_contradictions (L2 Bodha: contradiction/discovery surface).',
    'Returns convergences and tensions with judgment_flags marking inferences requiring acharya validation.',
    'Varga refinement (D6) available via chart_facts_query drill (marsys://tool/L1/chart_facts_query).',
    'chart_id is required — never defaulted (principle #14).',
  ].join(' '),

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to use (default: 'LAHIRI').",
    },
    max_signals_per_lens: {
      type: 'number',
      description: `Max ranked signals per question lens (default: ${ASSESS_DEFAULT_MAX_SIGNALS_PER_LENS}, max: ${ASSESS_MAX_SIGNALS_PER_LENS}). Drill via get_domain_reading for full signal lists.`,
    },
    max_contradictions: {
      type: 'number',
      description: `Max contradictions in bundle (default: ${ASSESS_DEFAULT_MAX_CONTRADICTIONS}, max: ${ASSESS_MAX_CONTRADICTIONS}). Remainder via query_contradictions.`,
    },
  },

  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L1/chart_facts_query',
    'marsys://tool/L2/query_signals',
    'marsys://tool/L2/classical_attribution_lookup',
    'marsys://tool/L2/get_domain_reading',
    'marsys://tool/L2/query_contradictions',
  ],

  llm_hints: {
    agentic: { cost_class: 'expensive', cacheable: true },
    bulk_context: { pre_fetch_priority: 30 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    return runAssessDomain(args, {
      domain: 'health',
      domain_label: 'Health / Vitality',
      judgment_flag_note:
        'Health domain synthesis reconciles 1st/6th/8th lords + Sun kāraka from L1 chart_facts (via drill). Affliction assessment and maraka timing require acharya review of the assembled bundle.',
    })
  },
}

// ── R3.1d: assess_wealth ─────────────────────────────────────────────────────

const assessWealthCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L-DOMAIN/assess_wealth',
  type: 'tool',
  layer: 'L2',
  name: 'assess_wealth',
  scope: 'per_chart',

  description: [
    'Reconciled wealth/prosperity assessment for a chart.',
    '2nd + 11th lords + Jupiter kāraka + dasha activation window + classical citations.',
    'Orchestrates query_domain_reading (L2 Bodha: CDLM cells + question lenses for wealth domain),',
    'query_temporal_activation (L3 Kāla: dasha activation window for domain signal refs),',
    'and query_contradictions (L2 Bodha: contradiction/discovery surface).',
    'Returns convergences and tensions with judgment_flags marking inferences requiring acharya validation.',
    'chart_id is required — never defaulted (principle #14).',
  ].join(' '),

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha to use (default: 'LAHIRI').",
    },
    max_signals_per_lens: {
      type: 'number',
      description: `Max ranked signals per question lens (default: ${ASSESS_DEFAULT_MAX_SIGNALS_PER_LENS}, max: ${ASSESS_MAX_SIGNALS_PER_LENS}). Drill via get_domain_reading for full signal lists.`,
    },
    max_contradictions: {
      type: 'number',
      description: `Max contradictions in bundle (default: ${ASSESS_DEFAULT_MAX_CONTRADICTIONS}, max: ${ASSESS_MAX_CONTRADICTIONS}). Remainder via query_contradictions.`,
    },
  },

  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L1/chart_facts_query',
    'marsys://tool/L2/query_signals',
    'marsys://tool/L2/classical_attribution_lookup',
    'marsys://tool/L2/get_domain_reading',
    'marsys://tool/L2/query_contradictions',
  ],

  llm_hints: {
    agentic: { cost_class: 'expensive', cacheable: true },
    bulk_context: { pre_fetch_priority: 30 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    return runAssessDomain(args, {
      domain: 'wealth',
      domain_label: 'Wealth / Prosperity',
      judgment_flag_note:
        'Wealth domain synthesis reconciles 2nd/11th lords + Jupiter kāraka from L1 chart_facts (via drill). Dhana yoga identification and dasha timing require acharya review of the assembled bundle.',
    })
  },
}

// ── R3.2: yoga_activation_by_dasha ───────────────────────────────────────────

export const yogaActivationByDashaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L-TIMING/yoga_activation_by_dasha',
  type: 'tool',
  layer: 'L3',
  name: 'yoga_activation_by_dasha',
  scope: 'per_chart',

  description: [
    'Which yogas fire in a given dasha-antardasha window?',
    'Joins bodha_msr_signals (signal_type_class = \'yoga\') with kala_activation (active dasha periods)',
    'to return activated yogas with dasha alignment score, activation window, and signal refs.',
    'Filter by dasha_period (e.g. \'saturn-venus\'), date range, or ayanamsha_id.',
    'Returns activated_yogas with: signal_id, signal_summary, yoga_type (signal_type_id),',
    'salience, dasha_alignment_score (dasha_activation_proximity_score), activation_start,',
    'activation_end, active_dasha_periods_jsonb, and constituent_fact_ids.',
    'Bridges the L2 Bodha yoga-signal catalog and the L3 Kāla timing activation surface.',
    'chart_id is required — never defaulted (principle #14).',
  ].join(' '),

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (default: 'LAHIRI').",
    },
    dasha_period: {
      type: 'string',
      description:
        "Dasha-antardasha label to filter by (e.g. 'saturn-venus', 'jupiter-moon'). " +
        'Matched as a case-insensitive substring against active_dasha_periods_jsonb text. Optional.',
    },
    date_from: {
      type: 'string',
      description: 'Start of date window (ISO 8601: YYYY-MM-DD). Default: today.',
    },
    date_to: {
      type: 'string',
      description: 'End of date window (ISO 8601: YYYY-MM-DD). Default: 3 years from today.',
    },
    top_k: {
      type: 'number',
      description: 'Maximum activated yogas to return (default: 30, max: 200).',
    },
    min_salience: {
      type: 'number',
      description: 'Minimum salience threshold on bodha_msr_signals (0..1, default: 0).',
    },
    domain: {
      type: 'string',
      description: 'Filter to yogas whose bodha_msr_signals.domains_affected_array contains this ' +
        'domain (e.g. "career", "wealth", "relationship", "health"). Optional.',
    },
  },

  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L2/query_signals',
    'marsys://tool/L3/query_temporal_activation',
    'marsys://tool/L2/classical_attribution_lookup',
  ],

  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 25 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const chart_id = args['chart_id'] as string | undefined
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'lahiri_chitrapaksha'
    const dasha_period = args['dasha_period'] as string | undefined
    const date_from =
      (args['date_from'] as string | undefined) ??
      new Date().toISOString().split('T')[0]!
    const date_to =
      (args['date_to'] as string | undefined) ??
      new Date(Date.now() + 3 * 365 * 86400000).toISOString().split('T')[0]!
    const top_k = Math.min(Number(args['top_k'] ?? 30), 200)
    const min_salience = Number(args['min_salience'] ?? 0)
    const domain = args['domain'] as string | undefined

    try {
      // Join bodha_msr_signals (yoga signals) with kala_activation on signal_id.
      // kala_activation links back to bodha_msr_signals via signal_id.
      // signal_type_class = 'yoga' is the authoritative yoga filter on bodha_msr_signals
      // (confirmed from query_signals.ts enum: 'yoga'|'dosha'|'karaka_alignment'|...).

      // W4-loop-1 (E-6 group4): the signal_id join itself is correct (74 yoga signals DO
      // join to kala_activation for the native), but ~all yoga activation rows carry NULL
      // activation_start/end (R-45 undated-rows defect) — so the strict
      // `activation_end >= from AND activation_start <= to` window silently dropped every
      // one, returning 0 "activated yogas". Surface the undated activations too (they are
      // the reachable data), keeping the date window as an INCLUSIVE filter for dated rows:
      // a row passes if it has no dates yet OR its window overlaps the requested range.
      //
      // WP-S4-fix2 (Gate Ś #8): admitting undated rows here (correct, above) combined with
      // an ORDER BY that ranked purely on dasha_activation_proximity_score DESC was a second,
      // compounding defect. An undated row's proximity score always defaults to exactly 0.5
      // (date_resolver._proximity_score returns 0.5 whenever no peak resolves) while the
      // MAJORITY of genuinely dated rows compute a real score below 0.5 (most sit ~0.2-0.4 on
      // this chart) — so undated rows, ranking as a false "above-average" 0.5, systematically
      // crowded dated rows out of the top-K page. Root-caused live: 15/15 rows returned for a
      // 2026-2029 window were ALL undated with the tell-tale flat 0.5. The ORDER BY below now
      // sorts dated rows first (regardless of score), THEN by proximity/salience within each
      // tier — undated rows still surface (never silently dropped, B.10) but only fill out the
      // page after every dated, temporally-real activation for the window is shown.
      const conds: string[] = [
        'm.chart_id = $1',
        'm.ayanamsha_id = $2',
        "m.signal_type_class = 'yoga'",
        'ka.chart_id = $1',
        'ka.ayanamsha_id = $2',
        '(ka.activation_start IS NULL OR (ka.activation_end >= $3 AND ka.activation_start <= $4))',
      ]
      const params: unknown[] = [chart_id, ayanamsha_id, date_from, date_to]
      let p = 5

      if (min_salience > 0) {
        conds.push(`m.computed_salience >= $${p++}`)
        params.push(min_salience)
      }

      // dasha_period filter: match against the jsonb text representation.
      // active_dasha_periods_jsonb stores dasha period labels; ILIKE on ::text is pragmatic.
      if (dasha_period) {
        conds.push(`ka.active_dasha_periods_jsonb::text ILIKE $${p++}`)
        params.push(`%${dasha_period}%`)
      }

      if (domain) {
        conds.push(`$${p++} = ANY(m.domains_affected_array)`)
        params.push(domain)
      }

      params.push(top_k)
      const limitPh = `$${p++}`

      const sql = `
        SELECT
          m.signal_id,
          m.signal_type_id            AS yoga_type,
          m.signal_tradition,
          m.computed_salience,
          m.signal_summary_text       AS signal_summary,
          m.constituent_facts_array   AS constituent_fact_ids,
          ka.id                       AS activation_id,
          to_char(ka.activation_start, 'YYYY-MM-DD')      AS activation_start,
          to_char(ka.activation_end, 'YYYY-MM-DD')        AS activation_end,
          to_char(ka.activation_peak_date, 'YYYY-MM-DD')  AS activation_peak_date,
          ka.dasha_activation_proximity_score AS dasha_alignment_score,
          ka.orb_strength,
          ka.convergence_score,
          ka.active_dasha_periods_jsonb,
          ka.source_citation
        FROM bodha_msr_signals m
        JOIN kala_activation ka ON ka.signal_id = m.signal_id
          AND ka.ayanamsha_id = m.ayanamsha_id
          AND ka.chart_id = m.chart_id
        WHERE ${conds.join('\n          AND ')}
        ORDER BY (ka.activation_start IS NULL) ASC,
                 ka.dasha_activation_proximity_score DESC NULLS LAST,
                 m.computed_salience DESC NULLS LAST,
                 ka.activation_start
        LIMIT ${limitPh}
      `

      const result = await query<Record<string, unknown>>(sql, params)

      // CR-37 (SARVA-SIDDHI W-1 T-3) §N.6: a yoga can be undated for two very
      // different reasons, and flattening them into one `undated_activation_count`
      // hides that distinction. ka_kalasutra stamps `:always_on=<reason>` on the
      // source_citation of a Nabhasa/ākṛti distribution yoga (formed by all seven
      // grahas → no single activating daśā lord → CORRECTLY always-on, not a
      // missing window). Annotate each such row with an inspectable
      // `always_on_reason` and count the two undated kinds separately.
      const ALWAYS_ON_RE = /:always_on=([a-z0-9_]+)/i
      for (const row of result.rows as Array<{ source_citation?: string | null; activation_start?: string | null; always_on_reason?: string | null }>) {
        const m = typeof row.source_citation === 'string' ? row.source_citation.match(ALWAYS_ON_RE) : null
        row.always_on_reason = m ? m[1]! : null
      }
      const rowsTyped = result.rows as Array<{ activation_start?: string | null; always_on_reason?: string | null }>
      const structurallyAlwaysOnCount = rowsTyped.filter((r) => r.activation_start == null && r.always_on_reason).length
      const undatedPendingWindowCount = rowsTyped.filter((r) => r.activation_start == null && !r.always_on_reason).length

      // Collect signal_id references
      const signalRefs = [
        ...new Set(
          (result.rows as Array<{ signal_id?: string }>)
            .map((r) => r.signal_id)
            .filter(Boolean) as string[]
        ),
      ]

      // E-2 freshness contract (R5.1 C2 item 1): re-derive DEFECT-001 live over exactly
      // the constituent_fact_ids referenced in THIS response, rather than restating the
      // historical "91.5% orphan (OPEN)" literal, which is stale post-R4.
      const referencedFactIds = Array.from(new Set(
        (result.rows as Array<{ constituent_fact_ids?: string[] | null }>)
          .flatMap((r) => r.constituent_fact_ids ?? [])
          .filter(Boolean)
      ))
      const defect001 = await deriveDefect001Note(chart_id, referencedFactIds)

      return {
        content: {
          chart_id,
          ayanamsha_id,
          query_window: {
            dasha_period: dasha_period ?? null,
            date_from,
            date_to,
          },
          activated_yogas: result.rows,
          total_count: result.rows.length,
          // W4-loop-1: honest disclosure — how many surfaced activations lack computed
          // windows yet (R-45). These are included (not dropped) so activated yogas surface,
          // but their activation_start/end are null pending the ka_kalasutra dating writer.
          undated_activation_count: (result.rows as Array<{ activation_start?: string | null }>)
            .filter((r) => r.activation_start == null).length,
          // CR-37 §N.6: split the undated total by REASON so a caller never reads a
          // correctly-always-on distribution yoga as a missing window.
          //   structurally_always_on_count — Nabhasa/ākṛti yogas with no discrete
          //     activation window BY NATURE (each row carries always_on_reason).
          //   undated_pending_window_count  — genuinely lacking a resolved window.
          structurally_always_on_count: structurallyAlwaysOnCount,
          undated_pending_window_count: undatedPendingWindowCount,
          ...(result.rows.length === 0
            ? { empty_reason: `No yoga signals join to kala_activation for chart ${chart_id} at ayanamsha '${ayanamsha_id}'${domain ? ` in domain '${domain}'` : ''}.` }
            : {}),
          signal_id_refs: signalRefs,
          filters: { dasha_period, date_from, date_to, top_k, min_salience, domain: domain ?? null },
          drill_next: [
            'marsys://tool/L2/query_signals',
            'marsys://tool/L3/query_temporal_activation',
            'marsys://tool/L2/classical_attribution_lookup',
          ],
          provenance: {
            tables: ['bodha_msr_signals', 'kala_activation'],
            join_key: 'signal_id (bodha_msr_signals.signal_id = kala_activation.signal_id)',
            yoga_filter: "signal_type_class = 'yoga'",
            // Structured, live-derived (E-2 freshness contract) — read this, not any
            // historical figure.
            defect_001: defect001,
            // Legacy string field retained (additive) — sourced from the same live derivation.
            defect_001_note: defect001.note,
          },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id },
        is_error: true,
      }
    }
  },
}

// ── Registration export ────────────────────────────────────────────────────────

/**
 * Register D8 domain reasoning-unit + yoga-dasha bridge capabilities.
 * Call at application startup after D7 channel capabilities are registered.
 * GATE A: only registers NEW files for this wave — does not edit registry/index.ts.
 */
export function registerD8AssessDomainCapabilities(): void {
  registerCapability(assessMarriageCapability)
  registerCapability(assessCareerCapability)
  registerCapability(assessHealthCapability)
  registerCapability(assessWealthCapability)
  registerCapability(yogaActivationByDashaCapability)
}

/**
 * D8 capability URI roster (for Gate C reverse-citation checks and roster smoke tests).
 */
export const D8_CAPABILITY_URIS = [
  // R3.1 — Domain reasoning-unit tools
  'marsys://tool/L-DOMAIN/assess_marriage',
  'marsys://tool/L-DOMAIN/assess_career',
  'marsys://tool/L-DOMAIN/assess_health',
  'marsys://tool/L-DOMAIN/assess_wealth',
  // R3.2 — Yoga-Dasha bridge
  'marsys://tool/L-TIMING/yoga_activation_by_dasha',
] as const

// Auto-register on import — consistent with L0-L5 layer pattern (catalog.ts
// imports this file; the import alone triggers registration via this call).
registerD8AssessDomainCapabilities()
