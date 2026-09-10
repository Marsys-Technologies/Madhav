/**
 * build_tail_watch — the constitutional tail (D-SALIENCE), populated.
 * ===================================================================
 * NIRMĀṆA L2-W3 (N-14 population half, N-15). The protection half — the
 * hard-floored, trim-immune `tail_watch` section — landed separately in
 * `platform-mcp/src/tools/registry_bridge.ts` and `response_budget.ts`. This
 * module fills it.
 *
 * The doctrine (plan §2, D-SALIENCE):
 *
 *   "The tail is constitutional: every umbrella envelope reserves a hard-floored
 *    `tail_watch` section (top consequence-bearers below the salience fold + rare-class
 *    leaders via percentile-in-class + `low_salience_high_consequence` anomalies) that no
 *    budget trim may zero. Demotion (noise side) and promotion (tail side) are both
 *    disclosed on-row."
 *
 * ── What the doctrine names, and what this estate actually has ───────────────
 *
 * The doctrine lists three components. In THIS codebase two of them are served by
 * one detector, and saying so is more useful than shipping a third component that
 * restates the second:
 *
 *   1. rare-class leaders via percentile-in-class — a real, independent population.
 *      Computed here from `salience_pctl_in_class` + a class-cardinality window.
 *   2. `low_salience_high_consequence` anomalies — `bo_anveshana` computes exactly
 *      this in `bodha_anomalies`: `consequence = min(centrality*0.4 + degree*0.3 +
 *      conv_score*0.3, 1.0)` and `non_obviousness = consequence * (1 - salience_norm)`.
 *   3. "top consequence-bearers below the salience fold" — which IS (2). That formula
 *      is literally consequence weighted by the inverse of salience. There is no
 *      separate consequence measure on `bodha_msr_signals` to build a third component
 *      from, and inventing one would be a fabricated judgment (§N.7 item 6).
 *
 * So: two components, honestly labelled, with the overlap stated rather than padded.
 *
 * ── Why `bodha_anomalies` is here at all ────────────────────────────────────
 *
 * D-SERVICE names "built-but-unplugged" as a defect class and `bodha_anomalies` as a
 * standing instance. It carries 2,918 rows per chart, of which 125 are
 * `low_salience_high_consequence` — and W1 confirmed the diagnosis exactly: the sole
 * reader (`query_contradictions.ts`) gates them behind an `include_anomalies`
 * parameter that defaults to `false`, that **no call site in the repository sets**, on
 * a capability that is not registered on the live MCP surface. Three independent
 * reasons the rows could never reach a caller. This is the first path that serves them.
 *
 * Every row discloses WHY it was promoted, per the doctrine's on-row clause. A tail
 * row that cannot say why it is in the tail is just a row.
 */
import { query } from '@/lib/db/client'

/** A class with more members than this is not rare; its top decile is just its top decile. */
export const RARE_CLASS_MAX_MEMBERS = 300
/** Above this rank a signal is above the fold and does not need the tail to be seen. */
export const SALIENCE_FOLD_RANK = 100
/** Top decile within a class. */
export const RARE_CLASS_LEADER_PCTL = 0.9

export type TailComponent = 'rare_class_leader' | 'low_salience_high_consequence'

export interface TailWatchRow {
  component: TailComponent
  signal_id: string | null
  signal_type_id: string | null
  signal_type_class: string | null
  /** Present for rare-class leaders; the tail's own ranking basis. */
  salience_pctl_in_class: number | null
  /** How many signals share this row's class in this (chart, ayanamsha). */
  class_member_count: number | null
  /** Chart-wide salience rank — high means far below the fold. */
  top_k_salience_rank: number | null
  /** Anomaly rows only: sigma from the chart's own baseline. */
  sigma_from_baseline: number | null
  summary: string | null
  /** D-SALIENCE: promotion is disclosed on-row, never silent. */
  promotion_reason: string
}

export interface TailWatchResult {
  tail_watch: TailWatchRow[]
  /** Honest disclosure when the tail is empty — never an unexplained `[]`. */
  tail_watch_empty_reason: string | null
  tail_watch_components: Record<TailComponent, number>
}

interface RareRow {
  signal_id: string
  signal_type_id: string | null
  signal_type_class: string | null
  salience_pctl_in_class: string | number | null
  class_n: string | number | null
  top_k_salience_rank: string | number | null
  signal_summary_text: string | null
}

interface AnomalyRow {
  signal_id: string | null
  signal_type_id: string | null
  signal_type_class: string | null
  sigma_from_baseline: string | number | null
  anomaly_value: string | number | null
  signal_summary_text: string | null
}

const num = (v: string | number | null | undefined): number | null =>
  v === null || v === undefined ? null : Number(v)

/**
 * Rare-class leaders: the top decile OF THEIR OWN CLASS, in a class small enough that
 * being its leader means something, and ranked far enough down the chart-wide order
 * that a salience-ordered read would never surface them.
 *
 * `salience_pctl_in_class IS NOT NULL` is load-bearing and is NOT a convenience filter.
 * Until the satellite writers began setting it, the six rarest classes carried NULL
 * there — so this predicate silently excluded precisely the population it exists to
 * find. Rows with a NULL percentile are reported through `tail_watch_empty_reason`
 * rather than dropped without trace.
 */
const RARE_CLASS_SQL = `
  WITH scoped AS (
    SELECT signal_id, signal_type_id, signal_type_class, signal_summary_text,
           salience_pctl_in_class, top_k_salience_rank,
           COUNT(*) OVER (PARTITION BY signal_type_class) AS class_n
      FROM bodha_msr_signals
     WHERE chart_id = $1 AND ayanamsha_id = $2
  )
  SELECT signal_id, signal_type_id, signal_type_class, signal_summary_text,
         salience_pctl_in_class, top_k_salience_rank, class_n
    FROM scoped
   WHERE salience_pctl_in_class IS NOT NULL
     AND salience_pctl_in_class >= $3
     AND class_n <= $4
     AND top_k_salience_rank > $5
   ORDER BY salience_pctl_in_class DESC, class_n ASC, signal_id ASC
   LIMIT $6`

const ANOMALY_SQL = `
  SELECT a.subject_ref_jsonb->>'signal_id'      AS signal_id,
         a.subject_ref_jsonb->>'signal_type_id' AS signal_type_id,
         m.signal_type_class                    AS signal_type_class,
         a.sigma_from_baseline,
         a.anomaly_value,
         m.signal_summary_text
    FROM bodha_anomalies a
    LEFT JOIN bodha_msr_signals m
      ON m.signal_id = (a.subject_ref_jsonb->>'signal_id')::uuid
     AND m.chart_id = a.chart_id
   WHERE a.chart_id = $1 AND a.ayanamsha_id = $2
     AND a.anomaly_type = 'low_salience_high_consequence'
   ORDER BY a.sigma_from_baseline DESC NULLS LAST, a.anomaly_id ASC
   LIMIT $3`

/** Count of rows the rare-class predicate had to skip because their percentile is unset. */
const NULL_PCTL_SQL = `
  SELECT COUNT(*)::int AS n
    FROM bodha_msr_signals
   WHERE chart_id = $1 AND ayanamsha_id = $2 AND salience_pctl_in_class IS NULL`

export async function buildTailWatch(
  chart_id: string,
  ayanamsha_id: string,
  opts: { limitPerComponent?: number } = {},
): Promise<TailWatchResult> {
  const limit = Math.max(1, Math.min(opts.limitPerComponent ?? 15, 50))
  const empty: TailWatchResult = {
    tail_watch: [],
    tail_watch_empty_reason: null,
    tail_watch_components: { rare_class_leader: 0, low_salience_high_consequence: 0 },
  }

  let rare: RareRow[] = []
  let anomalies: AnomalyRow[] = []
  let nullPctl = 0
  try {
    const [rareRes, anomRes, nullRes] = await Promise.all([
      query<RareRow>(RARE_CLASS_SQL, [
        chart_id, ayanamsha_id, RARE_CLASS_LEADER_PCTL,
        RARE_CLASS_MAX_MEMBERS, SALIENCE_FOLD_RANK, limit,
      ]),
      query<AnomalyRow>(ANOMALY_SQL, [chart_id, ayanamsha_id, limit]),
      query<{ n: number }>(NULL_PCTL_SQL, [chart_id, ayanamsha_id]),
    ])
    rare = rareRes.rows
    anomalies = anomRes.rows
    nullPctl = Number(nullRes.rows[0]?.n ?? 0)
  } catch {
    // An honest failure, not a fabricated empty. A caller must be able to tell
    // "this chart has no tail" from "the tail could not be read".
    return { ...empty, tail_watch_empty_reason: 'tail_watch could not be computed (query error)' }
  }

  const rows: TailWatchRow[] = [
    ...rare.map((r): TailWatchRow => {
      const pctl = num(r.salience_pctl_in_class)
      const classN = num(r.class_n)
      const rank = num(r.top_k_salience_rank)
      return {
        component: 'rare_class_leader',
        signal_id: r.signal_id,
        signal_type_id: r.signal_type_id,
        signal_type_class: r.signal_type_class,
        salience_pctl_in_class: pctl,
        class_member_count: classN,
        top_k_salience_rank: rank,
        sigma_from_baseline: null,
        summary: r.signal_summary_text,
        promotion_reason:
          `promoted: rare-class leader — top ${pctl === null ? '' : Math.round((1 - pctl) * 100) + '% '}` +
          `of ${r.signal_type_class ?? 'its class'} (${classN ?? '?'} signals chart-wide), ` +
          `ranked ${rank ?? '?'} overall so a salience-ordered read would not surface it`,
      }
    }),
    ...anomalies.map((a): TailWatchRow => {
      const sigma = num(a.sigma_from_baseline)
      return {
        component: 'low_salience_high_consequence',
        signal_id: a.signal_id,
        signal_type_id: a.signal_type_id,
        signal_type_class: a.signal_type_class,
        salience_pctl_in_class: null,
        class_member_count: null,
        top_k_salience_rank: null,
        sigma_from_baseline: sigma,
        summary: a.signal_summary_text,
        promotion_reason:
          `promoted: low salience, high consequence — ${sigma === null ? 'sigma unknown' : sigma.toFixed(2) + 'σ'} ` +
          `above this chart's own non-obviousness baseline. Consequence is weighted by the ` +
          `INVERSE of salience, so a high score here means the signal matters and does not look like it`,
      }
    }),
  ]

  const components = {
    rare_class_leader: rare.length,
    low_salience_high_consequence: anomalies.length,
  }

  let emptyReason: string | null = null
  if (rows.length === 0) {
    emptyReason =
      nullPctl > 0
        ? `no tail rows: no class qualified as rare-and-led (<= ${RARE_CLASS_MAX_MEMBERS} members, ` +
          `>= ${RARE_CLASS_LEADER_PCTL} percentile-in-class, ranked below ${SALIENCE_FOLD_RANK}), ` +
          `and no low_salience_high_consequence anomaly was recorded. Note ${nullPctl} signals ` +
          `carry no salience_pctl_in_class and were not eligible for the rare-class half.`
        : `no tail rows: no class qualified as rare-and-led, and no low_salience_high_consequence ` +
          `anomaly was recorded for this (chart, ayanamsha).`
  }

  return { tail_watch: rows, tail_watch_empty_reason: emptyReason, tail_watch_components: components }
}
