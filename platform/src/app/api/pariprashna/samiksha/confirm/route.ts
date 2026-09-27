/**
 * SAMĪKṢĀ confirm/dismiss endpoint — PB-3 (SAMĪKṢĀ) lane L-2 (detector seam).
 *
 * The server seam behind the in-stream "Log to Samīkṣā" affordance and the dock
 * prediction card. A HUMAN act (POST) promotes a detected candidate into the
 * L-1 ledger (§14.3 / W-1: no auto-promotion — only this authenticated,
 * human-initiated request writes `confirmed`), or dismisses it with a reason.
 *
 * Scope: this route only COPIES the D-16 stamp and calls L-2's confirm flow
 * (which calls L-1's DAL). It never touches `src/app/api/chat/**` and adds no
 * behaviour to the streaming reading route — it is a separate, additive endpoint.
 */

import 'server-only'
import { NextResponse, type NextRequest } from 'next/server'
import { z } from 'zod'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { confirmCandidate, dismissCandidate } from '@/lib/pariprashna/samiksha/confirm'
import { getConversation } from '@/lib/conversations'
import { archivedReadOnlyResponse, isCorrectionArchived } from '@/lib/conversations/readOnly'
import type { StructuredPredictionCandidate } from '@/lib/pariprashna/samiksha/detector'

const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/

const CandidateSchema = z.object({
  claim_text: z.string().min(1),
  domain: z.string().nullable(),
  window_start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).nullable(),
  window_end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).nullable(),
  direction: z.string().nullable(),
  confidence_stated: z.number().min(0).max(1).optional(),
  technique_refs: z.array(z.string()),
  grounding_fact_ids: z.array(z.string()),
  score: z.number(),
  horizon_text: z.string().nullable(),
})

const ConfidenceBandSchema = z
  .object({ low: z.number().min(0).max(1), high: z.number().min(0).max(1) })
  .refine((b) => b.low <= b.high, { message: 'confidence low must be <= high' })

const BodySchema = z.discriminatedUnion('action', [
  z.object({
    action: z.literal('confirm'),
    chartId: z.string().regex(UUID_RE),
    conversationId: z.string().regex(UUID_RE),
    messagePartId: z.string().regex(UUID_RE).nullable().optional(),
    candidate: CandidateSchema,
    confidence: ConfidenceBandSchema,
    edits: z
      .object({
        claim_text: z.string().min(1).optional(),
        domain: z.string().nullable().optional(),
        direction: z.string().nullable().optional(),
        window_start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).nullable().optional(),
        window_end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).nullable().optional(),
      })
      .optional(),
  }),
  z.object({
    action: z.literal('dismiss'),
    chartId: z.string().regex(UUID_RE),
    conversationId: z.string().regex(UUID_RE),
    messagePartId: z.string().regex(UUID_RE).nullable().optional(),
    candidate: CandidateSchema,
    reason: z.string().min(1),
  }),
])

export async function POST(request: NextRequest) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let raw: unknown
  try {
    raw = await request.json()
  } catch {
    return res.badRequest('Invalid JSON body')
  }

  const parsed = BodySchema.safeParse(raw)
  if (!parsed.success) {
    return res.badRequest(parsed.error.issues.map((i) => i.message).join('; '))
  }
  const body = parsed.data

  // Chart authorization — a caller may only log/dismiss a prediction on a chart
  // they own or have been granted (guest for their own chart per §14.3).
  const profile = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  const isSuperAdmin = profile.rows[0]?.role === 'super_admin'
  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role: isSuperAdmin ? 'super_admin' : 'guest' },
    chartId: body.chartId,
    db: { query },
  })
  if (permission === 'deny') return res.forbidden()

  // Jātaka chart workspace: load and authorize the referenced conversation
  // before any write. A missing, inaccessible or other-chart conversation gets
  // the same 404 (no enumeration); correction-history is read-only, so neither
  // confirm nor dismiss may touch the stamp, lifecycle or ledger for it.
  const conversation = await getConversation({ id: body.conversationId, userId: user.uid, isSuperAdmin })
  if (!conversation || conversation.chart_id !== body.chartId) return res.notFound('conversation')
  if (isCorrectionArchived(conversation)) return archivedReadOnlyResponse()

  // The ledger row is keyed by message part, not conversation: a part from any
  // other conversation (including correction history) would bypass the lock
  // above, so it must belong to the conversation that was just authorized.
  if (body.messagePartId) {
    const owner = await query<{ conversation_id: string }>(
      `SELECT cm.conversation_id
         FROM message_parts mp
         JOIN conversation_messages cm ON cm.id = mp.message_id
        WHERE mp.id = $1`,
      [body.messagePartId],
    )
    if (owner.rows[0]?.conversation_id !== body.conversationId) return res.notFound('message part')
  }

  const candidate = body.candidate as StructuredPredictionCandidate

  try {
    if (body.action === 'confirm') {
      const row = await confirmCandidate({
        chart_id: body.chartId,
        conversation_id: body.conversationId,
        message_part_id: body.messagePartId ?? null,
        candidate,
        confidence: body.confidence,
        edits: body.edits,
      })
      return NextResponse.json({ ok: true, ledger_row: row })
    }
    const row = await dismissCandidate({
      chart_id: body.chartId,
      message_part_id: body.messagePartId ?? null,
      candidate,
      reason: body.reason,
    })
    return NextResponse.json({ ok: true, ledger_row: row })
  } catch (err) {
    console.error('[pariprashna/samiksha/confirm] failed', err)
    return res.internal(err instanceof Error ? err.message : 'confirm failed')
  }
}
