import 'server-only'

import { query } from '@/lib/db/client'

/**
 * Gate I Performance — KPI aggregation library.
 *
 * Brief: CLAUDECODE_BRIEF.md (GATE-I-PERF-CMD-001), W5.
 *
 * Pure DB queries against performance_queries + eval_runs + prediction_ledger
 * + audit_log. Returns the response shape declared in W5. Empty windows
 * surface null (not 0) so the UI can distinguish "no data" from "value=0".
 */

export type Source = 'consume' | 'eval' | 'all'

export interface KpiWindow {
  start: string
  end: string
  source: Source
}

export interface KpiResponse {
  window: KpiWindow
  bundles: {
    pipeline_correctness: {
      plan_accuracy_recall: number | null
      plan_accuracy_precision: number | null
      plan_accuracy_n: number
      plan_accuracy_consume_unjudged_n: number
      citation_rate: number | null
      citation_n: number
    }
    answer_quality: {
      calibration_brier: number | null
      calibration_n: number
      b10_compliance_rate: number | null
      b11_compliance_rate: number | null
      compliance_n: number
    }
    performance_health: {
      latency_p50_ms: number | null
      latency_p95_ms: number | null
      latency_by_class: Record<string, { p50: number | null; p95: number | null }>
      synthesis_pass_rate: number | null
      synthesis_n: number
    }
    retrieval_health: {
      retrieval_hit_rate: number | null
      retrieval_n: number
    }
  }
  sparklines: {
    pipeline_correctness: Array<{ t: string; v: number | null }>
    answer_quality: Array<{ t: string; v: number | null }>
    performance_health: Array<{ t: string; v: number | null }>
    retrieval_health: Array<{ t: string; v: number | null }>
  }
}

function sourceClause(source: Source): { sql: string; params: string[] } {
  if (source === 'all') return { sql: '', params: [] }
  return { sql: ' AND source = $3', params: [source] }
}

/**
 * Computes plan-accuracy recall/precision over rows tagged 'correct' or 'wrong'.
 * Per brief W5: consume rows tagged 'unjudged' are surfaced separately.
 */
async function computePipelineCorrectness(
  start: string,
  end: string,
  source: Source
): Promise<KpiResponse['bundles']['pipeline_correctness']> {
  const sc = sourceClause(source)
  const r = await query<{
    plan_correct: string
    plan_wrong: string
    plan_unjudged_consume: string
    citation_yes: string
    citation_total: string
  }>(
    `SELECT
      COUNT(*) FILTER (WHERE plan_accuracy_label = 'correct')               AS plan_correct,
      COUNT(*) FILTER (WHERE plan_accuracy_label = 'wrong')                 AS plan_wrong,
      COUNT(*) FILTER (WHERE plan_accuracy_label = 'unjudged' AND source = 'consume') AS plan_unjudged_consume,
      COUNT(*) FILTER (WHERE citations_present = true)                      AS citation_yes,
      COUNT(*)                                                              AS citation_total
    FROM performance_queries
    WHERE created_at BETWEEN $1 AND $2${sc.sql}`,
    [start, end, ...sc.params]
  )
  const row = r.rows[0]
  const correct = Number(row.plan_correct)
  const wrong = Number(row.plan_wrong)
  const judgedN = correct + wrong
  const recall = judgedN > 0 ? correct / judgedN : null
  const precision = recall // see W5 note: per-row judge gives one verdict
  const citationTotal = Number(row.citation_total)
  const citationYes = Number(row.citation_yes)
  return {
    plan_accuracy_recall: recall,
    plan_accuracy_precision: precision,
    plan_accuracy_n: judgedN,
    plan_accuracy_consume_unjudged_n: Number(row.plan_unjudged_consume),
    citation_rate: citationTotal > 0 ? citationYes / citationTotal : null,
    citation_n: citationTotal,
  }
}

async function computeAnswerQuality(
  start: string,
  end: string,
  source: Source
): Promise<KpiResponse['bundles']['answer_quality']> {
  const sc = sourceClause(source)
  const compRow = (
    await query<{
      total: string
      b10_clean: string
      b11_clean: string
    }>(
      `SELECT
        COUNT(*)                                  AS total,
        COUNT(*) FILTER (WHERE b10_violation = false) AS b10_clean,
        COUNT(*) FILTER (WHERE b11_violation = false) AS b11_clean
      FROM performance_queries
      WHERE created_at BETWEEN $1 AND $2${sc.sql}`,
      [start, end, ...sc.params]
    )
  ).rows[0]
  const total = Number(compRow.total)

  // Calibration: average pre-computed Brier from prediction_ledger joined back
  // via audit_log.query_id ↔ performance_queries.audit_event_id. Only outcomes
  // where outcome_observed_at IS NOT NULL contribute.
  const calRow = (
    await query<{ avg_brier: number | null; n: string }>(
      `SELECT
        AVG(pl.brier_score)::numeric AS avg_brier,
        COUNT(*)                     AS n
      FROM performance_queries pq
      JOIN audit_log al           ON al.id = pq.audit_event_id
      JOIN prediction_ledger pl   ON pl.query_id = al.query_id
      WHERE pq.created_at BETWEEN $1 AND $2${sc.sql}
        AND pl.outcome_observed_at IS NOT NULL
        AND pl.brier_score IS NOT NULL`,
      [start, end, ...sc.params]
    )
  ).rows[0]

  return {
    calibration_brier: calRow.avg_brier !== null ? Number(calRow.avg_brier) : null,
    calibration_n: Number(calRow.n),
    b10_compliance_rate: total > 0 ? Number(compRow.b10_clean) / total : null,
    b11_compliance_rate: total > 0 ? Number(compRow.b11_clean) / total : null,
    compliance_n: total,
  }
}

async function computePerformanceHealth(
  start: string,
  end: string,
  source: Source
): Promise<KpiResponse['bundles']['performance_health']> {
  const sc = sourceClause(source)
  const overall = (
    await query<{
      p50: number | null
      p95: number | null
      pass: string
      n: string
    }>(
      `SELECT
        percentile_cont(0.5)  WITHIN GROUP (ORDER BY latency_total_ms)::numeric AS p50,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_total_ms)::numeric AS p95,
        COUNT(*) FILTER (WHERE synthesis_status = 'success') AS pass,
        COUNT(*)                                              AS n
      FROM performance_queries
      WHERE created_at BETWEEN $1 AND $2${sc.sql}
        AND latency_total_ms IS NOT NULL`,
      [start, end, ...sc.params]
    )
  ).rows[0]

  const byClass = (
    await query<{ query_class: string; p50: number | null; p95: number | null }>(
      `SELECT
        query_class,
        percentile_cont(0.5)  WITHIN GROUP (ORDER BY latency_total_ms)::numeric AS p50,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_total_ms)::numeric AS p95
      FROM performance_queries
      WHERE created_at BETWEEN $1 AND $2${sc.sql}
        AND latency_total_ms IS NOT NULL
        AND query_class IS NOT NULL
      GROUP BY query_class`,
      [start, end, ...sc.params]
    )
  ).rows

  const latency_by_class: Record<string, { p50: number | null; p95: number | null }> = {}
  for (const r of byClass) {
    latency_by_class[r.query_class] = {
      p50: r.p50 !== null ? Number(r.p50) : null,
      p95: r.p95 !== null ? Number(r.p95) : null,
    }
  }

  const n = Number(overall.n)
  return {
    latency_p50_ms: overall.p50 !== null ? Math.round(Number(overall.p50)) : null,
    latency_p95_ms: overall.p95 !== null ? Math.round(Number(overall.p95)) : null,
    latency_by_class,
    synthesis_pass_rate: n > 0 ? Number(overall.pass) / n : null,
    synthesis_n: n,
  }
}

async function computeRetrievalHealth(
  start: string,
  end: string,
  source: Source
): Promise<KpiResponse['bundles']['retrieval_health']> {
  const sc = sourceClause(source)
  const r = (
    await query<{ hit: string; n: string }>(
      `SELECT
        COUNT(*) FILTER (WHERE retrieval_hit = true) AS hit,
        COUNT(*) AS n
      FROM performance_queries
      WHERE created_at BETWEEN $1 AND $2${sc.sql}`,
      [start, end, ...sc.params]
    )
  ).rows[0]
  const n = Number(r.n)
  return {
    retrieval_hit_rate: n > 0 ? Number(r.hit) / n : null,
    retrieval_n: n,
  }
}

/**
 * Compute 24-bucket sparklines for each bundle's headline metric.
 * Buckets are evenly sized over [start, end]. Empty buckets get v=null.
 */
async function computeSparklines(
  start: string,
  end: string,
  source: Source
): Promise<KpiResponse['sparklines']> {
  const sc = sourceClause(source)
  const startMs = Date.parse(start)
  const endMs = Date.parse(end)
  const bucketMs = Math.max(1, Math.floor((endMs - startMs) / 24))
  const intervalSec = Math.floor(bucketMs / 1000)
  const r = await query<{
    bucket: string
    n: string
    correct: string
    wrong: string
    b10_clean: string
    pass: string
    hit: string
  }>(
    `SELECT
      to_timestamp(floor((extract(epoch FROM created_at) - $1) / $2) * $2 + $1) AS bucket,
      COUNT(*) AS n,
      COUNT(*) FILTER (WHERE plan_accuracy_label = 'correct') AS correct,
      COUNT(*) FILTER (WHERE plan_accuracy_label = 'wrong')   AS wrong,
      COUNT(*) FILTER (WHERE b10_violation = false)           AS b10_clean,
      COUNT(*) FILTER (WHERE synthesis_status = 'success')    AS pass,
      COUNT(*) FILTER (WHERE retrieval_hit = true)            AS hit
    FROM performance_queries
    WHERE created_at BETWEEN $3 AND $4${sc.sql.replace('$3', '$5')}
    GROUP BY bucket
    ORDER BY bucket ASC`,
    [Math.floor(startMs / 1000), intervalSec, start, end, ...sc.params]
  )

  const buckets = r.rows
  const mk = (key: 'correct_div_judged' | 'b10' | 'pass' | 'hit') =>
    buckets.map((b) => {
      const n = Number(b.n)
      const correct = Number(b.correct)
      const wrong = Number(b.wrong)
      const judged = correct + wrong
      let v: number | null
      switch (key) {
        case 'correct_div_judged':
          v = judged > 0 ? correct / judged : null
          break
        case 'b10':
          v = n > 0 ? Number(b.b10_clean) / n : null
          break
        case 'pass':
          v = n > 0 ? Number(b.pass) / n : null
          break
        case 'hit':
          v = n > 0 ? Number(b.hit) / n : null
          break
      }
      return { t: b.bucket, v }
    })

  return {
    pipeline_correctness: mk('correct_div_judged'),
    answer_quality: mk('b10'),
    performance_health: mk('pass'),
    retrieval_health: mk('hit'),
  }
}

export async function computeKpis(window: KpiWindow): Promise<KpiResponse> {
  const { start, end, source } = window
  const [pc, aq, ph, rh, sparks] = await Promise.all([
    computePipelineCorrectness(start, end, source),
    computeAnswerQuality(start, end, source),
    computePerformanceHealth(start, end, source),
    computeRetrievalHealth(start, end, source),
    computeSparklines(start, end, source),
  ])
  return {
    window,
    bundles: {
      pipeline_correctness: pc,
      answer_quality: aq,
      performance_health: ph,
      retrieval_health: rh,
    },
    sparklines: sparks,
  }
}
