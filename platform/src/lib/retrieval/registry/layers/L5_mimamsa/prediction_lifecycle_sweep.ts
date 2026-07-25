/**
 * prediction_lifecycle_sweep — prediction/window lifecycle sweep (L5 Mīmāṃsā)
 * ================================================================================
 * Elevation Campaign v2.1, Lane γ.J, EL-58.
 *
 * PROBLEM (charter): rows past their prediction window sit `open` indefinitely
 * unless something re-checks them against the LEL — "the 2011-window-open-in-2026
 * class" (a lapsed window, still nominally open years later, that was never
 * auto-matched or auto-closed).
 *
 * TWO calibration prediction stores exist and this sweep covers BOTH:
 *
 *   1. `brahma_prospective_ledger` (migration 458) — filed standing predictions,
 *      lifecycle_status IN ('open','matched','confirmed','falsified','withdrawn').
 *      A REAL-TIME hook already exists for this table —
 *      `matchOpenPredictionsForLelEvent` (platform/src/lib/lel/prospective_ledger.ts,
 *      out of this lane's manifest — CONSUMED via its exported function, never
 *      edited, mirroring how γ consumes L2_bodha's graha_portrait handler) — but it
 *      fires only when a NEW life_events row is appended, matched against a
 *      CALLER-SUPPLIED event_class. life_events has no event_class column, so this
 *      hook cannot retroactively reconcile predictions against events that already
 *      existed before the hook was wired, or events recorded without an explicit
 *      event_class tag. THAT retroactive gap — and the 'open, window closed,
 *      genuinely never observed' terminal case the hook has no state for at all —
 *      is what this sweep exists for.
 *      - Candidate-match half: reuses `matchOpenPredictionsForLelEvent` UNMODIFIED
 *        for the actual write (never re-implements its UPDATE), inferring candidate
 *        event_class(es) per life_event from domain-prefix -> brahma_event_ontology
 *        .lel_category (life_events has no event_class of its own).
 *      - No-match half (the charter's actual EL-58 ask): a lapsed 'open' row with
 *        no candidate LEL event should become `lapsed_unobserved`. That value is
 *        NOT in this table's live CHECK constraint
 *        (`brahma_prospective_ledger_lifecycle_status_check` — verified live,
 *        2026-07-25: IN ('open','matched','confirmed','falsified','withdrawn')).
 *        `platform/migrations/**` is EXCLUSIVELY β's manifest (charter §4) — this
 *        lane cannot land that ALTER TABLE. See `LAPSED_UNOBSERVED_MIGRATION_SQL`
 *        below: the exact, ready, additive migration text, PARKED-HONEST
 *        blocked-on-β until it lands. Until then this sweep reports these rows
 *        (`would_transition_to: 'lapsed_unobserved', blocked_pending_migration: true`)
 *        but does NOT write to lifecycle_status for them — never invents a state
 *        the schema does not yet support.
 *
 *   2. `mimamsa_predictions` (mi_bhavisya) — sparse early L5 population,
 *      lifecycle_status IN ('pending','confirmed','denied','expired') — NO live DB
 *      CHECK constraint (app-enforced only, verified 2026-07-25), fully in-manifest
 *      (query_predictions.ts, this same directory). `expired` already means exactly
 *      what the charter calls `lapsed_unobserved` for this table — no migration
 *      needed; this sweep writes it directly for lapsed 'pending' rows with no
 *      candidate LEL match. It deliberately does NOT auto-write 'confirmed' or
 *      'denied' for rows WITH a candidate match — those are truth adjudications
 *      only a human/native call may make (mirrors mimamsa_outcome_record's design);
 *      a candidate match here is only ever reported for review, never adjudicated.
 *
 * dry_run (default true): preview only, zero writes, for both tables. Preview
 * match-detection mirrors (does not re-derive the authority of)
 * `matchOpenPredictionsForLelEvent`'s point/interval/chain comparison, using its
 * OWN imported `toleranceDaysFor` (DR-13(d): exact=±45d / month_known=±75d) so the
 * preview and the real write path can never silently drift apart on the tolerance
 * value itself.
 *
 * NO-LEAKAGE: reads life_events (calibration corpus) only to CLOSE predictions
 * against observed reality — never to generate one. Writes only lifecycle_status
 * (+ existing matched_event_id/matched_at/match_note columns via the imported
 * function) — never a claim, confidence, or falsifier value.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import {
  matchOpenPredictionsForLelEvent,
  toleranceDaysFor,
  type DateConfidence,
  type LelEventForMatching,
} from '@/lib/lel/prospective_ledger'

/** Ready-to-apply, additive-only migration text for the β-owned migrations manifest.
 *  NOT executed anywhere in this file — platform/migrations/** is exclusively β's
 *  manifest (charter §4). Reported verbatim in this tool's response so the
 *  ratification/handoff packet (EL-25) can carry it forward without re-deriving it. */
export const LAPSED_UNOBSERVED_MIGRATION_SQL = `
-- Additive only: widens an existing CHECK constraint, no data touched, no other
-- table altered. Reversible (DOWN re-narrows the constraint; requires no
-- 'lapsed_unobserved' rows exist at rollback time, or they must be re-triaged first).
BEGIN;
ALTER TABLE public.brahma_prospective_ledger
  DROP CONSTRAINT brahma_prospective_ledger_lifecycle_status_check;
ALTER TABLE public.brahma_prospective_ledger
  ADD CONSTRAINT brahma_prospective_ledger_lifecycle_status_check
  CHECK (lifecycle_status IN
    ('open', 'matched', 'confirmed', 'falsified', 'withdrawn', 'lapsed_unobserved'));
COMMENT ON COLUMN public.brahma_prospective_ledger.lifecycle_status IS
  'open|matched|confirmed|falsified|withdrawn|lapsed_unobserved. lapsed_unobserved '
  '(EL-58, Elevation Campaign v2.1): the claimed window closed and the periodic '
  'lifecycle sweep (prediction_lifecycle_sweep, L5_mimamsa) found no candidate LEL '
  'event — itself calibration data, not a failure state.';
COMMIT;
`.trim()

const MAX_LAPSED_ROWS = 200

interface LedgerRow {
  prediction_id: string
  event_class: string
  claim: string
  claim_shape: 'point' | 'interval' | 'chain'
  observation_window: string | null
  milestone_set: Array<{ milestone_id: string; expected_date: string; name_en?: string }> | null
  window_end: string | null // derived, ISO date — the effective close date used to judge "lapsed"
}

interface LifeEventCandidate {
  event_id: string
  event_date: string
  domain: string | null
  shape: string
  date_confidence: DateConfidence
  interval_start: string | null
  interval_end: string | null
  milestone_label: string | null
}

/** Parses a Postgres daterange text literal, e.g. "[2027-04-09,2027-08-19)". */
function parseDaterange(text: string): [string, string] {
  const m = text.match(/[[(]([^,]*),([^)\]]*)[)\]]/)
  if (!m) throw new Error(`parseDaterange: could not parse '${text}'`)
  return [m[1] as string, m[2] as string]
}

function isPastToday(iso: string, today: string): boolean {
  return iso < today
}

/** Read-only preview mirror of matchOpenPredictionsForLelEvent's comparison — see
 *  file header. The authoritative WRITE path never re-implements this; it calls the
 *  imported function directly. This exists only so dry_run:true costs zero writes. */
function previewWouldMatch(row: LedgerRow, ev: LifeEventCandidate): { hit: boolean; note: string } {
  const toleranceMs = toleranceDaysFor(ev.date_confidence) * 86_400_000
  if (row.claim_shape === 'point' && row.observation_window) {
    const [pointStart] = parseDaterange(row.observation_window)
    const diffMs = Math.abs(new Date(`${ev.event_date}T00:00:00Z`).getTime() - new Date(`${pointStart}T00:00:00Z`).getTime())
    if (diffMs <= toleranceMs) {
      return { hit: true, note: `life_event ${ev.event_id} (${ev.event_date}) within ${ev.date_confidence} tolerance (±${toleranceDaysFor(ev.date_confidence)}d) of point claim ${pointStart}.` }
    }
  } else if (row.claim_shape === 'interval' && row.observation_window) {
    const [winStart, winEnd] = parseDaterange(row.observation_window)
    const evStart = ev.interval_start ?? ev.event_date
    const evEnd = ev.interval_end ?? ev.event_date
    const overlap =
      new Date(`${evStart}T00:00:00Z`).getTime() <= new Date(`${winEnd}T00:00:00Z`).getTime() &&
      new Date(`${evEnd}T00:00:00Z`).getTime() >= new Date(`${winStart}T00:00:00Z`).getTime()
    if (overlap) {
      return { hit: true, note: `life_event ${ev.event_id} [${evStart},${evEnd}] overlaps interval claim [${winStart},${winEnd}].` }
    }
  } else if (row.claim_shape === 'chain' && row.milestone_set && ev.milestone_label) {
    const known = row.milestone_set.some(m => m.milestone_id === ev.milestone_label)
    if (known) {
      return { hit: true, note: `life_event ${ev.event_id}'s milestone_label '${ev.milestone_label}' matches a milestone in chain claim ${row.prediction_id}.` }
    }
  }
  return { hit: false, note: '' }
}

export const predictionLifecycleSweepCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/prediction_lifecycle_sweep',
  type:  'tool',
  layer: 'L5',
  name:  'prediction_lifecycle_sweep',

  description: [
    'EL-58 prediction/window lifecycle sweep. Finds predictions whose window has',
    'CLOSED and are still lifecycle_status=open/pending, auto-matches them against',
    'the chart-scoped LEL, and closes the ones with no candidate LEL event so they',
    'do not sit open indefinitely (the charter\'s "2011-window-open-in-2026" class).',
    'Covers both mimamsa_predictions (writes lifecycle_status=expired directly —',
    'no schema change needed) and brahma_prospective_ledger (candidate matches are',
    'written via the existing matchOpenPredictionsForLelEvent hook; no-match rows',
    'are REPORTED as lapsed_unobserved candidates but not written — that value is',
    'not yet in this table\'s CHECK constraint; see the returned',
    'migration_pending_note for the ready ALTER TABLE text). dry_run (default true)',
    'previews with zero writes. Never auto-adjudicates a candidate match to',
    'confirmed/denied/falsified — that stays a human/native call',
    '(mimamsa_outcome_record / a future prospective-ledger adjudication tool).',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID. Required.',
      required: true,
    },
    dry_run: {
      type: 'boolean',
      description: 'Preview only, no writes (default true). Set false to apply schema-safe transitions.',
      required: false,
    },
    table: {
      type: 'string',
      description: "Restrict the sweep to one table: 'mimamsa_predictions' | 'brahma_prospective_ledger'. Omit for both.",
      enum: ['mimamsa_predictions', 'brahma_prospective_ledger'],
      required: false,
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: true,
  // NOT calibration_context_only: that flag (F-R7) is for outcome/LEL-READ tools supplying raw
  // ledger context (lel_query, query_predictions). This tool performs a lifecycle SWEEP/mutation
  // (reclassifying lapsed rows) rather than a context read for planner consumption — a different
  // kind of operation than the documented semantic covers, so left unset rather than force-fit.
  data_source: 'stored',

  llm_hints: {
    agentic: {
      cost_class: 'medium',
      cacheable: false,
    },
    bulk_context: {
      pre_fetch_priority: 25, // maintenance/calibration surface, not a reading-time primitive
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }
    const dryRun = args['dry_run'] === false ? false : true
    const tableFilter = args['table'] === 'mimamsa_predictions' || args['table'] === 'brahma_prospective_ledger'
      ? (args['table'] as string) : null

    const today = new Date().toISOString().slice(0, 10)

    try {
      const results: {
        mimamsa_predictions?: unknown
        brahma_prospective_ledger?: unknown
      } = {}

      // ── mimamsa_predictions half — fully in-manifest, no cross-manifest block ──
      if (!tableFilter || tableFilter === 'mimamsa_predictions') {
        const pendingResult = await query<{
          prediction_id: string; domain: string | null; eval_date: string
          observation_window: string | null; outcome_claim: string
        }>(
          `SELECT prediction_id, domain, to_char(eval_date, 'YYYY-MM-DD') AS eval_date,
                  observation_window::text, outcome_claim
           FROM mimamsa_predictions
           WHERE chart_id = $1 AND lifecycle_status = 'pending' AND eval_date < $2::date
           ORDER BY eval_date ASC
           LIMIT $3`,
          [chart_id, today, MAX_LAPSED_ROWS],
        )
        const lapsed = pendingResult.rows

        // Map ontology domain -> lel_category set, for candidate life_events lookup.
        const domains = [...new Set(lapsed.map(r => r.domain).filter((d): d is string => !!d))]
        const lelCategoriesByDomain = new Map<string, string[]>()
        if (domains.length > 0) {
          const ontRes = await query<{ domain: string; lel_category: string | null }>(
            `SELECT DISTINCT domain, lel_category FROM brahma_event_ontology WHERE domain = ANY($1)`,
            [domains],
          )
          for (const row of ontRes.rows) {
            if (!row.lel_category) continue
            const arr = lelCategoriesByDomain.get(row.domain) ?? []
            arr.push(row.lel_category)
            lelCategoriesByDomain.set(row.domain, arr)
          }
        }

        const mpReport: Array<Record<string, unknown>> = []
        let expiredWritten = 0
        for (const row of lapsed) {
          const categories = row.domain ? (lelCategoriesByDomain.get(row.domain) ?? []) : []
          let candidateEvents: LifeEventCandidate[] = []
          if (categories.length > 0) {
            const [winStart, winEnd] = row.observation_window
              ? parseDaterange(row.observation_window)
              : [row.eval_date, row.eval_date]
            const evRes = await query<LifeEventCandidate>(
              `SELECT event_id, to_char(event_date, 'YYYY-MM-DD') AS event_date, domain, shape,
                      date_confidence,
                      to_char(interval_start, 'YYYY-MM-DD') AS interval_start,
                      to_char(interval_end, 'YYYY-MM-DD') AS interval_end,
                      milestone_label
               FROM life_events
               WHERE chart_id = $1
                 AND split_part(domain, '/', 1) = ANY($2)
                 AND event_date BETWEEN ($3::date - INTERVAL '90 days') AND ($4::date + INTERVAL '90 days')`,
              [chart_id, categories, winStart, winEnd],
            )
            candidateEvents = evRes.rows
          }

          if (candidateEvents.length > 0) {
            mpReport.push({
              prediction_id: row.prediction_id, domain: row.domain, eval_date: row.eval_date,
              outcome_claim: row.outcome_claim, disposition: 'candidate_match_found_no_auto_write',
              candidate_life_events: candidateEvents.map(e => e.event_id),
              note: 'Candidate LEL overlap found — reported for human/native review only. This sweep never auto-writes confirmed/denied.',
            })
          } else {
            mpReport.push({
              prediction_id: row.prediction_id, domain: row.domain, eval_date: row.eval_date,
              outcome_claim: row.outcome_claim,
              disposition: dryRun ? 'would_write_expired' : 'wrote_expired',
            })
            if (!dryRun) {
              await query(
                `UPDATE mimamsa_predictions SET lifecycle_status = 'expired' WHERE chart_id = $1 AND prediction_id = $2`,
                [chart_id, row.prediction_id],
              )
              expiredWritten += 1
            }
          }
        }

        results.mimamsa_predictions = {
          lapsed_pending_count: lapsed.length,
          expired_written: dryRun ? 0 : expiredWritten,
          dry_run: dryRun,
          rows: mpReport,
          note: "lifecycle_status='expired' is this table's existing terminal 'no observed outcome' state (app-enforced enum, no DB CHECK, no migration needed) — functionally the same concept the charter names 'lapsed_unobserved' for the sibling table.",
        }
      }

      // ── brahma_prospective_ledger half — candidate-match write via the existing
      // hook (reused unmodified); no-match half reported only, migration-blocked. ──
      if (!tableFilter || tableFilter === 'brahma_prospective_ledger') {
        const openResult = await query<{
          prediction_id: string; event_class: string; claim: string
          claim_shape: 'point' | 'interval' | 'chain'
          observation_window: string | null
          milestone_set: Array<{ milestone_id: string; expected_date: string; name_en?: string }> | null
        }>(
          `SELECT prediction_id, event_class, claim, claim_shape,
                  observation_window::text, milestone_set
           FROM brahma_prospective_ledger
           WHERE chart_id = $1 AND lifecycle_status = 'open'
           LIMIT $2`,
          [chart_id, MAX_LAPSED_ROWS],
        )

        const lapsedLedgerRows: LedgerRow[] = []
        for (const r of openResult.rows) {
          let windowEnd: string | null = null
          if (r.observation_window) {
            const [, end] = parseDaterange(r.observation_window)
            windowEnd = end
          } else if (r.milestone_set && r.milestone_set.length > 0) {
            windowEnd = r.milestone_set.map(m => m.expected_date).sort().slice(-1)[0] ?? null
          }
          if (windowEnd && isPastToday(windowEnd, today)) {
            lapsedLedgerRows.push({ ...r, window_end: windowEnd })
          }
        }

        // Ontology lookup: event_class -> lel_category, batched.
        const eventClasses = [...new Set(lapsedLedgerRows.map(r => r.event_class))]
        const lelCategoryByClass = new Map<string, string | null>()
        if (eventClasses.length > 0) {
          const ontRes = await query<{ event_class_id: string; lel_category: string | null }>(
            `SELECT event_class_id, lel_category FROM brahma_event_ontology WHERE event_class_id = ANY($1)`,
            [eventClasses],
          )
          for (const row of ontRes.rows) lelCategoryByClass.set(row.event_class_id, row.lel_category)
        }

        const bplReport: Array<Record<string, unknown>> = []
        let matchedApplied = 0
        for (const row of lapsedLedgerRows) {
          const lelCategory = lelCategoryByClass.get(row.event_class)
          let candidateEvents: LifeEventCandidate[] = []
          if (lelCategory) {
            const [winStart, winEnd] = row.observation_window
              ? parseDaterange(row.observation_window)
              : [row.window_end as string, row.window_end as string]
            const evRes = await query<LifeEventCandidate>(
              `SELECT event_id, to_char(event_date, 'YYYY-MM-DD') AS event_date, domain, shape,
                      date_confidence,
                      to_char(interval_start, 'YYYY-MM-DD') AS interval_start,
                      to_char(interval_end, 'YYYY-MM-DD') AS interval_end,
                      milestone_label
               FROM life_events
               WHERE chart_id = $1
                 AND split_part(domain, '/', 1) = $2
                 AND event_date BETWEEN ($3::date - INTERVAL '90 days') AND ($4::date + INTERVAL '90 days')`,
              [chart_id, lelCategory, winStart, winEnd],
            )
            candidateEvents = evRes.rows
          }

          const hits = candidateEvents.filter(ev => previewWouldMatch(row, ev).hit)

          if (hits.length > 0) {
            if (!dryRun) {
              for (const ev of hits) {
                const event: LelEventForMatching = {
                  chart_id, life_event_id: ev.event_id, event_class: row.event_class,
                  event_date: ev.event_date, date_confidence: ev.date_confidence,
                  interval_start: ev.interval_start, interval_end: ev.interval_end,
                  milestone_label: ev.milestone_label,
                }
                // Reuses the existing, tested write path verbatim — never re-implemented here.
                await matchOpenPredictionsForLelEvent(event)
              }
              matchedApplied += 1
            }
            bplReport.push({
              prediction_id: row.prediction_id, event_class: row.event_class, claim: row.claim,
              window_end: row.window_end,
              disposition: dryRun ? 'would_match_via_existing_hook' : 'matched_via_existing_hook',
              candidate_life_events: hits.map(e => e.event_id),
            })
          } else {
            bplReport.push({
              prediction_id: row.prediction_id, event_class: row.event_class, claim: row.claim,
              window_end: row.window_end,
              disposition: 'lapsed_unobserved_candidate',
              would_transition_to: 'lapsed_unobserved',
              blocked_pending_migration: true,
              note: "lifecycle_status stays 'open' in the DB — 'lapsed_unobserved' is not yet in this table's CHECK constraint. See migration_pending_note.",
            })
          }
        }

        results.brahma_prospective_ledger = {
          lapsed_open_count: lapsedLedgerRows.length,
          matched_applied: dryRun ? 0 : matchedApplied,
          lapsed_unobserved_candidates: bplReport.filter(r => r['disposition'] === 'lapsed_unobserved_candidate').length,
          dry_run: dryRun,
          rows: bplReport,
          migration_pending_note: "'lapsed_unobserved' requires an additive CHECK-constraint widening migration. platform/migrations/** is exclusively β's manifest (charter §4) — this lane (γ.J) cannot land it. PARKED-HONEST, blocked-on-β. Ready text: see this tool's exported LAPSED_UNOBSERVED_MIGRATION_SQL constant (prediction_lifecycle_sweep.ts).",
        }
      }

      return {
        content: {
          chart_id,
          dry_run: dryRun,
          today,
          ...results,
          governance: 'life_events is a calibration corpus only — read here strictly to CLOSE existing predictions against observed reality, never to generate one. A candidate match is never auto-adjudicated to confirmed/denied/falsified — that remains a human/native call.',
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
