/**
 * POST /api/build/school-consensus
 * Task C (U4): Runs the 7-school triangulation engine for a chart and persists
 * the convergence results to school_analysis_runs + convergence_scores + school_disagreements.
 *
 * Auth: super_admin only (write path touches the four school consensus tables).
 * Idempotency: delete-then-insert per chart_id (§N.3 L4+).
 *
 * Body: { chart_id: string, ayanamsha_id?: string }
 * Returns: { ok: true, domains: 5, analysis_rows: 35, convergence_rows: 5 }
 */
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import {
  buildChartData,
  buildSchoolSignals,
  DOMAIN_AUTHORITY_WEIGHTS,
} from '@/lib/schools/chart_data_adapter'
import { runSchoolsForDomain } from '@/lib/schools/school_runner'
import type { Domain, SchoolName, SignalScore } from '@/lib/schools/types'

const ALL_DOMAINS: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
const ALL_SCHOOLS: SchoolName[] = ['parashari', 'jaimini', 'tajika', 'kp', 'nadi', 'bnn', 'yogini']

async function requireSuperAdmin(): Promise<boolean> {
  const user = await getServerUser()
  if (!user) return false
  const { rows } = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id = $1',
    [user.uid],
  )
  return rows[0]?.role === 'super_admin'
}

export async function POST(req: NextRequest) {
  const ok = await requireSuperAdmin()
  if (!ok) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const body = await req.json().catch(() => null)
  if (!body?.chart_id) {
    return NextResponse.json({ error: 'chart_id required' }, { status: 400 })
  }

  const { chart_id, ayanamsha_id = 'lahiri' } = body as {
    chart_id: string
    ayanamsha_id?: string
  }

  // Step 1: Build live ChartData from L1 (chart_facts + chart_dashas)
  const chartData = await buildChartData(chart_id, ayanamsha_id)

  // Step 2: Build live signals for each school × domain
  type SignalsByDomain = Record<Domain, SignalScore[]>
  const signalsMap: Partial<Record<SchoolName, SignalsByDomain>> = {}
  for (const school of ALL_SCHOOLS) {
    signalsMap[school] = {} as SignalsByDomain
    for (const domain of ALL_DOMAINS) {
      signalsMap[school]![domain] = await buildSchoolSignals(chart_id, school, domain)
    }
  }

  // Step 3: Idempotent delete of prior school consensus data for this chart
  await query('DELETE FROM school_analysis_runs WHERE chart_id = $1', [chart_id])
  await query('DELETE FROM convergence_scores WHERE chart_id = $1', [chart_id])
  await query('DELETE FROM school_disagreements WHERE chart_id = $1', [chart_id])

  const today = new Date().toISOString().split('T')[0]
  let analysisRows = 0
  let convergenceRows = 0
  let disagreementRows = 0

  // Step 4: Run schools × persist per domain
  for (const domain of ALL_DOMAINS) {
    // Build per-school live signals for this domain
    const liveSignals: Partial<Record<SchoolName, SignalScore[]>> = {}
    for (const school of ALL_SCHOOLS) {
      const sigs = signalsMap[school]?.[domain] ?? []
      liveSignals[school] = sigs
    }

    const result = await runSchoolsForDomain(chartData, domain, {
      liveSignals,
      includeNarratives: true,
    })

    // 4a: Insert per-school analysis runs (7 rows per domain)
    for (const schoolResult of result.schoolResults) {
      const w = DOMAIN_AUTHORITY_WEIGHTS[domain][schoolResult.school as SchoolName] ?? (1 / 7)
      const weighted = schoolResult.domainScore * w
      await query(
        `INSERT INTO school_analysis_runs (
           chart_id, run_date, school, chart_type, domain,
           domain_score, direction, top_signals, school_verdict,
           pending_flags, weighted_domain_score, domain_authority_weight
         ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11, $12)`,
        [
          chart_id,
          today,
          schoolResult.school,
          chartData.chartType,
          domain,
          schoolResult.domainScore,
          schoolResult.direction,
          JSON.stringify(schoolResult.topSignals ?? []),
          schoolResult.schoolVerdict,
          schoolResult.pendingFlags ?? [],
          weighted,
          w,
        ],
      )
      analysisRows++
    }

    // 4b: Upsert convergence_scores row (1 per domain)
    const { convergence } = result
    const perSchoolWeighted = result.perSchoolWeighted ?? {}
    await query(
      `INSERT INTO convergence_scores (
         chart_id, domain, schools_agreeing, schools_total,
         mean_domain_score, std_domain_score, weighted_mean_score,
         direction, per_school_scores, per_school_weighted, convergence_narrative
       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb, $11)
       ON CONFLICT (chart_id, domain) DO UPDATE SET
         schools_agreeing = EXCLUDED.schools_agreeing,
         schools_total = EXCLUDED.schools_total,
         mean_domain_score = EXCLUDED.mean_domain_score,
         std_domain_score = EXCLUDED.std_domain_score,
         weighted_mean_score = EXCLUDED.weighted_mean_score,
         direction = EXCLUDED.direction,
         per_school_scores = EXCLUDED.per_school_scores,
         per_school_weighted = EXCLUDED.per_school_weighted,
         convergence_narrative = EXCLUDED.convergence_narrative,
         computed_at = NOW()`,
      [
        chart_id,
        domain,
        convergence.schoolsAgreeing,
        convergence.schoolsTotal,
        convergence.meanDomainScore,
        convergence.stdDomainScore,
        result.weightedMeanScore,
        convergence.direction,
        JSON.stringify(convergence.perSchoolScores ?? {}),
        JSON.stringify(perSchoolWeighted),
        convergence.convergenceNarrative ?? null,
      ],
    )
    convergenceRows++

    // 4c: Insert disagreements (E1 — classify + persist inter-school divergence)
    const schoolScores = result.schoolResults.map(r => ({ school: r.school, score: r.domainScore, direction: r.direction }))
    const positiveSchools = schoolScores.filter(s => s.direction === 'positive').map(s => s.school)
    const negativeSchools = schoolScores.filter(s => s.direction !== 'positive').map(s => s.school)
    const hasDivergence = positiveSchools.length > 0 && negativeSchools.length > 0

    if (hasDivergence) {
      const disId = `DIS.SCH.${chart_id.slice(0, 8)}.${domain}.001`
      // E1: detect if this is a temporal_scope disagreement (schools agree direction but differ on intensity)
      const positiveCount = positiveSchools.length
      const negativeCount = negativeSchools.length
      // temporal_scope: if majority agrees direction but minority differs in timing-sensitive schools (KP, Tājika)
      const timingSchools = ['kp', 'tajika']
      const majorityDirection = positiveCount >= negativeCount ? 'positive' : 'negative'
      const minorSchools = majorityDirection === 'positive' ? negativeSchools : positiveSchools
      const isTimingScope = timingSchools.some(s => minorSchools.includes(s as SchoolName)) && Math.abs(positiveCount - negativeCount) <= 2

      const disClass = isTimingScope
        ? 'temporal_scope'
        : negativeCount <= 1 ? 'signal_gap' : 'method_divergence'
      const resolution = isTimingScope
        ? 'Majority schools confirm outcome direction; KP/Tājika timing divergence signals uncertain window boundaries — widen prediction window.'
        : `${positiveCount}/7 schools positive; ${negativeCount}/7 negative. Context-dependent on dasha timing.`
      const verdict = positiveCount >= 5 ? 'affirming_majority'
        : negativeCount >= 5 ? 'denying_majority'
        : positiveCount === negativeCount ? 'unresolved'
        : 'context_dependent'

      await query(
        `INSERT INTO school_disagreements (
           chart_id, disagreement_id, domain,
           schools_affirming, schools_denying, schools_silent,
           disagreement_class, resolution, resolution_verdict, worked_example_narrative
         ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
         ON CONFLICT (chart_id, disagreement_id) DO NOTHING`,
        [
          chart_id,
          disId,
          domain,
          positiveSchools,
          negativeSchools,
          [],  // silent schools would need signal_gap analysis
          disClass,
          resolution,
          verdict,
          convergence.convergenceNarrative ?? '',
        ],
      )
      disagreementRows++
    }
  }

  return NextResponse.json({
    ok: true,
    chart_id,
    domains: ALL_DOMAINS.length,
    analysis_rows: analysisRows,
    convergence_rows: convergenceRows,
    disagreement_rows: disagreementRows,
  })
}
