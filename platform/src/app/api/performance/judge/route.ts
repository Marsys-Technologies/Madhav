import { randomUUID } from 'crypto'
import { NextResponse } from 'next/server'
import { generateText } from 'ai'

import { query } from '@/lib/db/client'
import { resolveModel } from '@/lib/models/resolver'
import { guardPerformanceRoute } from '../_guard'
import { buildJudgePrompt, parseJudgeResponse } from '@/lib/performance/judge_prompt'

// Brief specifies gemini-2.0-flash-lite. That model id was dropped from the
// project's OpenAI-compat shim on 2026-05-03 (registry.ts:138, :633) and the
// canonical replacement is gemini-2.5-flash-lite. Per audit + W0 adapt-on-
// field-naming-only guidance, we use the live id.
const JUDGE_MODEL = 'gemini-2.5-flash-lite'

const ADVISORY_LOCK_KEY = 'gate1.performance.judge'

export async function POST(request: Request) {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  let body: { window_start?: string; window_end?: string; limit?: number }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'invalid_json_body' }, { status: 400 })
  }
  const { window_start, window_end } = body
  const limit = Math.min(200, Math.max(1, Number(body.limit ?? 100) || 100))
  if (!window_start || !window_end) {
    return NextResponse.json({ error: 'window_start and window_end required' }, { status: 400 })
  }
  if (Number.isNaN(Date.parse(window_start)) || Number.isNaN(Date.parse(window_end))) {
    return NextResponse.json({ error: 'window_start/end must be ISO-8601' }, { status: 400 })
  }

  // Postgres advisory lock — prevents two concurrent judge runs.
  const lockRes = await query<{ locked: boolean }>(
    `SELECT pg_try_advisory_lock(hashtext($1)) AS locked`,
    [ADVISORY_LOCK_KEY]
  )
  if (!lockRes.rows[0]?.locked) {
    return NextResponse.json({ error: 'judge_run_in_progress' }, { status: 409 })
  }

  const judgeRunId = randomUUID()
  const breakdown = { correct: 0, wrong: 0, ambiguous: 0 }
  let judgedCount = 0

  try {
    const candidates = (
      await query<{
        id: string
        query_text: string | null
        query_class: string | null
        plan_type: string | null
        plan_tools_selected: string[] | null
        planner_confidence: number | null
      }>(
        `SELECT id, query_text, query_class, plan_type, plan_tools_selected, planner_confidence
         FROM performance_queries
         WHERE source = 'consume'
           AND plan_accuracy_label = 'unjudged'
           AND created_at BETWEEN $1 AND $2
         ORDER BY created_at DESC
         LIMIT $3`,
        [window_start, window_end, limit]
      )
    ).rows

    for (const row of candidates) {
      const prompt = buildJudgePrompt({
        query_text: row.query_text ?? '',
        query_class: row.query_class,
        plan_type: row.plan_type,
        tools_selected: Array.isArray(row.plan_tools_selected) ? row.plan_tools_selected : [],
        planner_confidence: row.planner_confidence,
      })

      let verdict: 'correct' | 'wrong' | 'ambiguous'
      let reasoning: string
      try {
        const result = await generateText({
          model: resolveModel(JUDGE_MODEL),
          messages: [{ role: 'user', content: prompt }],
          maxOutputTokens: 256,
        })
        const parsed = parseJudgeResponse(result.text ?? '')
        if (parsed) {
          verdict = parsed.verdict
          reasoning = parsed.reasoning
        } else {
          verdict = 'ambiguous'
          reasoning = 'judge_call_failed: parse_error'
        }
      } catch (err) {
        verdict = 'ambiguous'
        reasoning = `judge_call_failed: ${err instanceof Error ? err.message : String(err)}`
      }

      try {
        // Single-statement transaction-equivalent: pg handles each query in
        // an implicit transaction. The two statements together are atomic
        // enough at P0 — the verdict insert and label update share the row id.
        await query(
          `INSERT INTO performance_judge_verdict (
            performance_query_id, judge_run_id, judge_model, planner_verdict,
            planner_reasoning, triggered_by_user_id
          ) VALUES ($1, $2, $3, $4, $5, $6)`,
          [row.id, judgeRunId, JUDGE_MODEL, verdict, reasoning, auth.user.uid ?? null]
        )
        await query(
          `UPDATE performance_queries
           SET plan_accuracy_label = $2, plan_accuracy_source = 'judge'
           WHERE id = $1 AND plan_accuracy_label = 'unjudged'`,
          [row.id, verdict]
        )
        breakdown[verdict] += 1
        judgedCount += 1
      } catch (err) {
        console.error('[judge] persistence failed for row', row.id, err)
      }
    }
  } finally {
    await query(`SELECT pg_advisory_unlock(hashtext($1))`, [ADVISORY_LOCK_KEY])
  }

  return NextResponse.json({
    judge_run_id: judgeRunId,
    judged_count: judgedCount,
    breakdown,
    model: JUDGE_MODEL,
  })
}
