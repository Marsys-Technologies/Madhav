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
import { judgmentFlag, type JudgmentFlagEntry } from '../../envelope'

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

    // F-021R: bound question_lenses.all_relevant_ranked_jsonb per lens.
    // The raw handler returns all rows; each can be 1–2 MB of ranked signals.
    const rawLenses = Array.isArray(domainContent['question_lenses'])
      ? (domainContent['question_lenses'] as Record<string, unknown>[])
      : []
    const boundedLenses = rawLenses.map((lens) => {
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
    const contradictions =
      contraResult.is_error
        ? { status: 'error', note: String(contraContent['error']) }
        : (contraContent['contradiction_count'] as number) === 0
        ? {
            status: 'no_data',
            note:
              contraContent['contradictions_note'] ??
              'bodha_contradictions: 0 rows for this chart/ayanamsha — verify chart has been built (bo_karanajala).',
          }
        : {
            status: 'ok',
            items: contraContent['contradictions'],
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
        `SELECT signal_id, signal_type_class, source_subsystem, signal_summary_text, computed_salience
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
      // concept. Reported honestly as always-empty with a drill, rather than a dead filter.
      strength: { count: 0, source: 'L1 chart_facts (shadbala / ashtakavarga) — graha strength is not an MSR signal class', drill_uri: 'marsys://tool/L2/get_domain_reading' },
      varga:    { count: stageVarga.length,  source: 'bodha_msr_signals (source_subsystem=varga)' },
      temporal: {
        count: stageTemporal.length,
        source: 'kala_activation (L3)',
        ...(stageTemporal.length === 0 ? { empty_reason: TEMPORAL_EMPTY_REASON } : {}),
      },
      contradiction_pairs: {
        count: stageContra.length,
        source: 'bodha_contradictions (L2 bo_karanajala)',
        ...(stageContra.length === 0
          ? { empty_reason: 'bodha_contradictions: 0 rows for this chart/ayanamsha (bo_karanajala) — no_data, not a serving trim.' }
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

    return {
      content: {
        domain,
        domain_label,
        chart_id,
        ayanamsha_id,
        ranking_basis: p2RankingBasis,
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
          signals_per_lens_cap: max_signals_per_lens,
          note: 'bodha_question_lenses returned chart-wide (no domain column); reconcile via cdlm_cells. all_relevant_ranked_jsonb capped per lens — drill via get_domain_reading for full signal lists.',
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
        varga_analysis: {
          note: 'Varga refinement (D9/D10/D6) available via chart_facts_query with divisional_chart filter.',
          drill_uri: 'marsys://tool/L1/chart_facts_query',
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
