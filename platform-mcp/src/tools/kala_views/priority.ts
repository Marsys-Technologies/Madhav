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
        const raw = await callKalaRegistryCap(
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
        )
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
            'general election entry point — per-row actionability is not yet computed at this ' +
            'build tier (item 25, W2); this is not a per-row leverage claim.',
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
          notInCorpusCoverage(
            'salience_vector_five_axis',
            'W2 item 25 (informativeness/consequence/relevance/reliability/actionability) not ' +
            'yet built — priority_score is the legacy single-scalar salience (computed_salience ' +
            '× activation_strength, with a neutral-dignity down-rank), per ' +
            'KALA_SIX_VIEWS_DESIGN_v2_0.md §B.',
          ),
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
        }

        return kalaBudgetedDualOutput(content, TOOL_NAME)
      } catch (err) {
        return kalaErrorOutput(TOOL_NAME, err instanceof Error ? err.message : String(err), { chart_id })
      }
    },
  )
}
