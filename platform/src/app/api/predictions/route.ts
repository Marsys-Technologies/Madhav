/**
 * POST /api/predictions — PPL prediction logger (γ3)
 *
 * Records a user-reviewed prediction to the predictions table.
 * The outcome column is ALWAYS null at write time (Learning Layer rule #4).
 * The migration (062_predictions.sql) must be applied before this route works.
 */

import 'server-only'
import { getServerUser } from '@/lib/firebase/server'
import { res } from '@/lib/errors'
import { query } from '@/lib/db/client'

interface PredictionBody {
  query_id: string
  conversation_id: string | null
  prediction_text: string
  confidence: number | null
  horizon: string | null
  falsifier: string | null
}

export async function POST(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: PredictionBody
  try {
    body = await request.json() as PredictionBody
  } catch {
    return res.badRequest('invalid JSON body')
  }

  if (!body.query_id || typeof body.query_id !== 'string') {
    return res.badRequest('query_id required')
  }
  if (!body.prediction_text || typeof body.prediction_text !== 'string') {
    return res.badRequest('prediction_text required')
  }
  if (body.confidence != null && (typeof body.confidence !== 'number' || body.confidence < 0 || body.confidence > 1)) {
    return res.badRequest('confidence must be 0–1')
  }

  try {
    // Verify the query_id belongs to this user (authorization check)
    const ownerCheck = await query<{ query_id: string }>(
      `SELECT query_id FROM query_trace_steps WHERE query_id = $1 AND user_id = $2 LIMIT 1`,
      [body.query_id, user.uid],
    )
    if (ownerCheck.rows.length === 0) {
      return res.forbidden()
    }

    const result = await query<{ id: string; logged_at: string }>(
      `INSERT INTO predictions
         (query_id, conversation_id, prediction_text, confidence, horizon, falsifier, outcome)
       VALUES ($1, $2, $3, $4, $5, $6, NULL)
       RETURNING id, logged_at`,
      [
        body.query_id,
        body.conversation_id ?? null,
        body.prediction_text,
        body.confidence ?? null,
        body.horizon ?? null,
        body.falsifier ?? null,
      ],
    )

    const row = result.rows[0]
    return Response.json({ id: row.id, logged_at: row.logged_at }, { status: 201 })
  } catch (err) {
    console.error('[api/predictions] write failed', err)
    return res.dbError()
  }
}
