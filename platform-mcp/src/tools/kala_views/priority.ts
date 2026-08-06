/**
 * priority.ts — ṢAḌ-DARŚANA W0.4: `kala_priority_get` (SHAD_DARSHANA_BRIEF_v2_0.md §3 W0.4 ·
 * §2 file map; design authority KALA_SIX_VIEWS_DESIGN_v1_0.md §5 / v2_0.md §B/§E "PRIORITIZE").
 * ==========================================================================
 * VIEW 5 — PRIORITIZE: "Of everything, what matters most right now?"
 *
 * W0 SCOPE (thin facade over EXISTING substrate — no new computation, per brief §3 W0.4):
 * wraps the SAME registry capability `kala_priority_ranking_get` (register_p1_aliases.ts)
 * already calls — `marsys://tool/L3/call_priority_ranking` (ka_tulana service, ranks active
 * signals by computed_salience × activation_strength, with a neutral-dignity down-rank) —
 * and re-serves it through the elevated `kala_envelope.ts` shape: argument-shaped reading
 * (`makeKalaEnvelope`/`composeArgument`), `question_frame`, `field_snapshot_id` stub,
 * tri-plane pointers, 3-state coverage, freshness, `calibration_maturity` (always the
 * honest `noLelCalibrationMaturity()` stub at W0 — no calibration plane exists yet
 * anywhere in this campaign, not just for LEL-absent charts).
 *
 * HONESTY NOTE (§N.7 narration fidelity — do not over-claim the legacy scalar): the design
 * doc (KALA_SIX_VIEWS_DESIGN_v2_0.md §B) is explicit that today's `priority_score` is a
 * "salience-monoculture" — a single opaque scalar, not the five-axis vector (informativeness/
 * consequence/relevance/reliability/actionability, item 25) the W2 rebuild will serve. This
 * facade therefore does NOT assign a graded `strength` to each evidence row (that would
 * fabricate a confidence reading the underlying scalar doesn't actually carry) and instead
 * discloses the gap explicitly via a `not_in_corpus` coverage entry.
 *
 * The real W2/W3 PRIORITIZE deepening (the five-axis vector, `surprise_of_absence` rows,
 * submodular top-K selection) is out of scope here — this facade only reserves the envelope
 * SHAPE and honestly flags what it does not yet compute.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import {
  makeKalaEnvelope,
  resolveFieldSnapshot,
  pointerTo,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  buildKalaFreshness,
  noLelCalibrationMaturity,
  type ArgumentReading,
  type ArgumentEvidence,
  type KalaCoverageEntry,
  type TriPlanePointers,
  type KalaDensityContract,
  type QuestionFrame,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import { callKalaRegistryCap, unwrapKalaPayload, kalaBudgetedDualOutput, kalaErrorOutput, round3 } from './shared.js'

// ── W2.7: kala_field_salience DB read (item 25) ──────────────────────────────
// Reads the NEWEST field_snapshot's salience rows for a chart via the whitelisted
// read-only DB proxy (platform/src/app/api/mcp/db/query/route.ts — kala_field_salience
// added to ALLOWED_TABLES in the same PR). Aggregates per-chart via a simple AVG across
// all windows so the five-axis vector is summarised as a scalar per axis for the priority
// envelope (the full per-window breakdown is available via dedicated salience tools).
// Returns `{ state:'honest_empty', rows_count:0 }` when no rows exist yet (the W2.7 fix:
// transitioning the coverage entry from not_in_corpus → honest_empty/computed on real data).

const PLATFORM_URL_FOR_DB = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN_FOR_DB = process.env['MCP_INTERNAL_TOKEN'] ?? ''

export interface SalienceVectorResult {
  state: 'computed' | 'honest_empty' | 'unreachable'
  rows_count: number
  factor_informativeness: number | null
  factor_consequence: number | null
  factor_relevance: number | null
  factor_reliability: number | null
  factor_actionability: number | null
  /** Fraction of rows that are selected (submodular selection outcome) */
  selected_fraction: number | null
  reason?: string
}

/** Fetches the five-axis salience vector summary from kala_field_salience for a chart.
 *  Uses the SAME read-only DB proxy (`/api/mcp/db/query`) that resolveFieldSnapshot uses.
 *  Never throws — any error degrades to state:'unreachable' so the priority envelope is
 *  not brought down by a missing salience table (honest_empty is the designed state for
 *  charts whose ka_kshetra build has not yet run). */
export async function fetchSalienceVector(
  chartId: string,
  principal: { user_uid: string; key_id: string },
): Promise<SalienceVectorResult> {
  try {
    const res = await fetch(`${PLATFORM_URL_FOR_DB}/api/mcp/db/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-mcp-internal-token': MCP_INTERNAL_TOKEN_FOR_DB,
        'x-mcp-user': principal.user_uid,
        'x-mcp-key-id': principal.key_id,
      },
      body: JSON.stringify({
        // AVG across all windows of the newest snapshot for this chart. NULL factors
        // (§6.1: "never imputed") remain NULL in the average — a single NULL axis means
        // the coverage entry must state which axes were computable.
        sql:
          'SELECT COUNT(*) AS rows_count, ' +
          'AVG(factor_informativeness) AS factor_informativeness, ' +
          'AVG(factor_consequence) AS factor_consequence, ' +
          'AVG(factor_relevance) AS factor_relevance, ' +
          'AVG(factor_reliability) AS factor_reliability, ' +
          'AVG(factor_actionability) AS factor_actionability, ' +
          'ROUND((COUNT(*) FILTER (WHERE selected))::numeric / NULLIF(COUNT(*), 0), 4) AS selected_fraction ' +
          'FROM kala_field_salience WHERE chart_id = $1',
        params: [chartId],
      }),
      signal: AbortSignal.timeout(10_000),
    })
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      return {
        state: 'unreachable',
        rows_count: 0,
        factor_informativeness: null,
        factor_consequence: null,
        factor_relevance: null,
        factor_reliability: null,
        factor_actionability: null,
        selected_fraction: null,
        reason: `kala_field_salience read failed (HTTP ${res.status}): ${text.slice(0, 200)}`,
      }
    }
    const data = (await res.json()) as { rows?: Array<Record<string, unknown>> }
    const row = data.rows?.[0]
    if (!row) {
      return {
        state: 'honest_empty',
        rows_count: 0,
        factor_informativeness: null,
        factor_consequence: null,
        factor_relevance: null,
        factor_reliability: null,
        factor_actionability: null,
        selected_fraction: null,
        reason: 'no kala_field_salience rows for this chart — ka_kshetra stage 6 has not yet run',
      }
    }
    const rowsCount = typeof row['rows_count'] === 'number' ? (row['rows_count'] as number) :
      typeof row['rows_count'] === 'string' ? parseInt(row['rows_count'] as string, 10) : 0
    if (rowsCount === 0) {
      return {
        state: 'honest_empty',
        rows_count: 0,
        factor_informativeness: null,
        factor_consequence: null,
        factor_relevance: null,
        factor_reliability: null,
        factor_actionability: null,
        selected_fraction: null,
        reason: 'no kala_field_salience rows for this chart — ka_kshetra stage 6 has not yet run',
      }
    }
    const toNum = (v: unknown): number | null => {
      if (v === null || v === undefined) return null
      const n = typeof v === 'string' ? parseFloat(v) : (v as number)
      return Number.isFinite(n) ? n : null
    }
    return {
      state: 'computed',
      rows_count: rowsCount,
      factor_informativeness: toNum(row['factor_informativeness']),
      factor_consequence: toNum(row['factor_consequence']),
      factor_relevance: toNum(row['factor_relevance']),
      factor_reliability: toNum(row['factor_reliability']),
      factor_actionability: toNum(row['factor_actionability']),
      selected_fraction: toNum(row['selected_fraction']),
    }
  } catch (err) {
    return {
      state: 'unreachable',
      rows_count: 0,
      factor_informativeness: null,
      factor_consequence: null,
      factor_relevance: null,
      factor_reliability: null,
      factor_actionability: null,
      selected_fraction: null,
      reason: `kala_field_salience read threw (${err instanceof Error ? err.message : String(err)})`,
    }
  }
}

/** Builds the KalaCoverageEntry for salience_vector_five_axis based on live DB state.
 *  Before W2.7: always not_in_corpus ("not yet built"). After W2.7: computed when rows
 *  exist, honest_empty when they don't (the difference is visible and meaningful).
 *  Also accepts a raw rows array for test fixtures (rows.length > 0 → computed). */
export function buildSalienceCoverage(salience: SalienceVectorResult | unknown[]): KalaCoverageEntry {
  // Accept a raw rows array from test fixtures
  if (Array.isArray(salience)) {
    if (salience.length === 0) {
      return honestEmptyCoverage(
        'salience_vector_five_axis',
        'no kala_field_salience rows for this chart — ka_kshetra stage 6 has not yet run; ' +
        'prior W0 facade always reported not_in_corpus, W2.7 promotes to honest_empty when the ' +
        'table exists but has no rows for this chart.',
      )
    }
    return computedCoverage('salience_vector_five_axis')
  }
  const s = salience as SalienceVectorResult
  if (s.state === 'computed') {
    return computedCoverage('salience_vector_five_axis')
  }
  if (s.state === 'honest_empty') {
    return honestEmptyCoverage(
      'salience_vector_five_axis',
      (s.reason ?? 'no kala_field_salience rows for this chart') +
      ' — prior W0 facade always reported not_in_corpus; W2.7 promotes to honest_empty ' +
      'when the table exists but has no rows for this chart (KALA_SIX_VIEWS_DESIGN_v2_0.md §B).',
    )
  }
  // unreachable: the DB proxy itself failed — honest disclosure, not fabricated coverage
  return honestEmptyCoverage(
    'salience_vector_five_axis',
    `kala_field_salience unreachable: ${s.reason ?? 'unknown error'} — served as honest_empty, ` +
    'never as not_in_corpus (table exists but was unreadable this call).',
  )
}

const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri: 'lahiri_chitrapaksha', LAHIRI: 'lahiri_chitrapaksha', Lahiri: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha', true_chitra: 'lahiri_chitrapaksha',
}
function resolveAyanamsha(id?: string): string { return id ? (AYANAMSHA_ALIAS[id] ?? id) : 'lahiri_chitrapaksha' }

const TOOL_NAME = 'kala_priority_get'
const CAPABILITY_URI = 'marsys://tool/L3/call_priority_ranking'

// ── question_frame (E4, kala_envelope.ts) — same optional shape across all eight views ──

const QuestionFrameSchema = z.object({
  domain: z.string().optional(),
  entity: z.string().optional(),
  horizon: z.string().optional(),
  intent_verb: z.string().optional(),
  stakes: z.string().optional(),
  comparison_target: z.string().optional(),
}).optional().describe(
  'Optional question frame (Elevation E4): {domain, entity, horizon, intent_verb, stakes, ' +
  'comparison_target}. The chart is always implicit — this is the per-question input that ' +
  'conditions reading composition. Echoed back verbatim in the envelope, not yet used to ' +
  're-rank rows at W0 (that lands with the W2 relevance axis, item 25).'
)

interface RankedSignalRow {
  signal_id?: string
  signal_headline_text?: string
  computed_salience?: number
  domains_affected_array?: string[]
  signal_type_class?: string
  activation_strength?: number
  window_start?: string
  window_end?: string
  trigger_type?: string
  neutral_dignity_downranked?: boolean
  priority_score?: number
}

/** Builds the ArgumentReading (thesis/evidence/dissent/verdict/falsifier) from the raw
 *  `ranked_signals` rows the underlying `call_priority_ranking` capability already computed.
 *  Pure assembly — no new scoring, no invented strength tiers (see file header). */
function buildReading(params: {
  rows: RankedSignalRow[]
  dateFrom: string
  dateTo: string
  domainFilter: string[] | null
}): ArgumentReading {
  const { rows, dateFrom, dateTo, domainFilter } = params
  const domainClause = domainFilter && domainFilter.length > 0 ? ` (domain: ${domainFilter.join(', ')})` : ''

  if (rows.length === 0) {
    return {
      thesis: `No priority-ranked signals activation-overlap ${dateFrom}–${dateTo}${domainClause} for this chart.`,
      evidence: [],
      dissent: [],
      verdict: {
        statement: `Honest empty — nothing to triage in this window${domainClause}.`,
        tier: 'structural_prior',
      },
      falsifier: null,
    }
  }

  const top = rows[0] as RankedSignalRow
  const thesis =
    `Top priority signal for ${dateFrom}–${dateTo}${domainClause}: ` +
    `"${top.signal_headline_text ?? top.signal_id ?? 'unlabeled signal'}"` +
    (top.neutral_dignity_downranked ? ' (down-ranked: neutral-dignity descriptor).' : '.')

  // Up to 5 rows as evidence, in the already-computed priority_score order — no re-ranking.
  const evidence: ArgumentEvidence[] = rows.slice(0, 5).map((row): ArgumentEvidence => ({
    claim:
      `${row.signal_headline_text ?? row.signal_id ?? 'unlabeled signal'} ` +
      `(priority_score ${round3(row.priority_score) ?? 'n/a'}` +
      (row.neutral_dignity_downranked ? ', neutral-dignity down-rank applied' : '') +
      (row.trigger_type ? `, trigger: ${row.trigger_type}` : '') +
      ')',
    fact_ids: row.signal_id ? [row.signal_id] : [],
    // No `strength` assigned — see file header honesty note: priority_score is today's
    // unexamined single scalar, not the calibrated five-axis vector (item 25, W2).
  }))

  return {
    thesis,
    evidence,
    dissent: [],
    verdict: {
      statement: `${rows.length} signal(s) ranked for ${dateFrom}–${dateTo}${domainClause}; ` +
        `see evidence for the top ${Math.min(rows.length, 5)}.`,
      tier: 'structural_prior',
    },
    falsifier: null,
  }
}

export function registerKalaPriorityTool(server: McpServer, principal: Principal): void {
  server.tool(
    TOOL_NAME,
    'VIEW 5 — PRIORITIZE ("of everything, what matters most right now?"). Wraps the same ' +
    'ka_tulana priority-ranking service kala_priority_ranking_get calls, re-served on the ' +
    'elevated kala_* envelope: an argument-shaped reading (thesis/evidence/dissent/verdict/' +
    'falsifier), question_frame echo, field_snapshot_id, tri-plane pointers into EXPLAIN/' +
    'AHEAD/ELECT, 3-state coverage (honestly flags that the W2 five-axis salience vector — ' +
    'informativeness/consequence/relevance/reliability/actionability — is not yet built; ' +
    'today\'s priority_score is the legacy single-scalar salience), freshness, and ' +
    'calibration_maturity (always the honest zero stub at W0 — no calibration plane exists ' +
    'yet). Neutral-dignity descriptor rows are down-ranked (not dropped), same as the ' +
    'underlying capability. [ṢAḌ-DARŚANA W0.4]',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')."),
      date_from: z.string().optional().describe('Start of evaluation period (YYYY-MM-DD). Default: today.'),
      date_to: z.string().optional().describe('End of evaluation period (YYYY-MM-DD). Default: today+90d.'),
      top_k: z.number().int().min(1).max(100).optional().describe('Max signals (default 20, max 100).'),
      domain: z.string().optional().describe(
        'Filter to ONE life domain (e.g. "wealth", "career", "health", "relationship", ' +
        '"spirituality", "character"), case-insensitive. Takes precedence over `domains`.'),
      domains: z.array(z.string()).optional().describe(
        'Filter to ANY of these life domains (OR/overlap match), case-insensitive. Ignored if `domain` is also given.'),
      question_frame: QuestionFrameSchema,
    },
    async (params) => {
      const {
        chart_id, ayanamsha_id, date_from, date_to, top_k, domain, domains, question_frame,
      } = params as Record<string, unknown>

      if (!chart_id || typeof chart_id !== 'string') {
        return kalaErrorOutput(TOOL_NAME, 'chart_id is required')
      }

      try {
        const resolvedAyanamsha = resolveAyanamsha(ayanamsha_id as string | undefined)
        // W2.7: fetch the live five-axis salience vector from kala_field_salience IN PARALLEL
        // with the priority ranking call — both are read-only, independent, and can race.
        const [raw, salienceResult] = await Promise.all([
          callKalaRegistryCap(
            CAPABILITY_URI,
            {
              chart_id,
              ayanamsha_id: resolvedAyanamsha,
              ...(date_from ? { date_from } : {}),
              ...(date_to ? { date_to } : {}),
              ...(top_k != null ? { top_k } : {}),
              ...(domain ? { domain } : {}),
              ...(domains ? { domains } : {}),
            },
            principal,
          ),
          fetchSalienceVector(chart_id, principal),
        ])
        const payload = unwrapKalaPayload(raw)
        const rows = Array.isArray(payload['ranked_signals']) ? (payload['ranked_signals'] as RankedSignalRow[]) : []
        const resolvedDateFrom = (payload['date_from'] as string | undefined) ?? (date_from as string | undefined) ?? 'today'
        const resolvedDateTo = (payload['date_to'] as string | undefined) ?? (date_to as string | undefined) ?? 'today+90d'
        const domainFilter = Array.isArray(payload['domain_filter']) ? (payload['domain_filter'] as string[]) : null

        const reading = buildReading({ rows, dateFrom: resolvedDateFrom, dateTo: resolvedDateTo, domainFilter })

        const triPlane: TriPlanePointers = {
          interpretation_ref: pointerTo(
            'kala_explain_get',
            'drill into the causal chain (PACT stages) behind any of these ranked signals\' domain/bhava.',
          ),
          prediction_ref: pointerTo(
            'kala_ahead_get',
            'see the forward horizon these priority signals belong to.',
          ),
          intervention_ref: pointerTo(
            'kala_elect_get',
            'general election entry point — per-row actionability is computed per-window by ' +
            'ka_kshetra (item 25); the average across served windows is now in salience_vector_five_axis.',
          ),
        }

        const coverage: KalaCoverageEntry[] = [
          rows.length > 0
            ? computedCoverage('priority_ranking_legacy_scalar')
            : honestEmptyCoverage(
                'priority_ranking_legacy_scalar',
                `no signals activation-overlap ${resolvedDateFrom}–${resolvedDateTo}` +
                (domainFilter ? ` for domain(s) ${domainFilter.join(', ')}` : ''),
              ),
          // W2.7: salience_vector_five_axis is now live from kala_field_salience — computed
          // when rows exist, honest_empty when ka_kshetra stage 6 has not run for this chart.
          // The W0 not_in_corpus claim is retired in favour of the live DB state.
          buildSalienceCoverage(salienceResult),
          notInCorpusCoverage(
            'surprise_of_absence',
            'absence-as-signal (item 33, PRIORITIZE deepening) not yet built — lands W3.',
          ),
        ]

        // W2 (E5): the real field snapshot read — served id, or an honest marker; never a stub.
        const fieldSnapshot = await resolveFieldSnapshot(chart_id, principal)

        const freshness = buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: fieldSnapshot.field_content_hash })

        const densityContract: KalaDensityContract = {
          paginated: true,
          facets: ['domain', 'domains'],
          empty_reason: true,
        }

        const envelope = makeKalaEnvelope({
          reading,
          questionFrame: (question_frame as QuestionFrame | undefined) ?? null,
          fieldSnapshot,
          triPlane: triPlane,
          coverage,
          freshness,
          calibrationMaturity: noLelCalibrationMaturity(),
        })

        // W2.7: include the live salience vector in the response when computed.
        // The per-axis averages are served alongside the existing ranked_signals so callers
        // can see the field's overall salience profile for this chart without a separate lookup.
        const salienceVectorPayload = salienceResult.state === 'computed' ? {
          salience_vector_five_axis: {
            state: salienceResult.state,
            rows_count: salienceResult.rows_count,
            factor_informativeness: round3(salienceResult.factor_informativeness),
            factor_consequence: round3(salienceResult.factor_consequence),
            factor_relevance: round3(salienceResult.factor_relevance),
            factor_reliability: round3(salienceResult.factor_reliability),
            factor_actionability: round3(salienceResult.factor_actionability),
            selected_fraction: round3(salienceResult.selected_fraction),
            note: 'Average per axis across all kala_field_salience rows for this chart. NULL axes ' +
              'were not computable (§6.1: never imputed). Per-window breakdown available via dedicated ' +
              'salience tools. factor_informativeness is NULL when bg_synthetic_cohort_md has no rows ' +
              '(md_chain_not_built) or the matched sub-cohort is below minimum (§6.3 fallback).',
          },
        } : {
          salience_vector_five_axis: {
            state: salienceResult.state,
            reason: salienceResult.reason,
            note: 'ka_kshetra stage 6 has not yet built kala_field_salience rows for this chart.',
          },
        }

        const content = {
          ok: true as const,
          tool: TOOL_NAME,
          chart_id,
          ...envelope,
          composed: composeArgument(envelope.reading),
          density_contract: densityContract,
          window: { date_from: resolvedDateFrom, date_to: resolvedDateTo },
          domain_filter: domainFilter,
          ranked_signals: rows,
          signal_count: (payload['signal_count'] as number | undefined) ?? rows.length,
          neutral_dignity_downranked_count: payload['neutral_dignity_downranked_count'] ?? 0,
          ...(payload['neutral_dignity_note'] ? { neutral_dignity_note: payload['neutral_dignity_note'] } : {}),
          ...salienceVectorPayload,
        }

        return kalaBudgetedDualOutput(content, TOOL_NAME)
      } catch (err) {
        return kalaErrorOutput(TOOL_NAME, err instanceof Error ? err.message : String(err), { chart_id })
      }
    },
  )
}
