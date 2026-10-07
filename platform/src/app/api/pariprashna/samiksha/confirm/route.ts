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
import { query, withTransaction } from '@/lib/db/client'
import { res } from '@/lib/errors'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { toLedgerStamp } from '@/lib/pariprashna/samiksha/confirm'
import { confirmDetectedCandidate } from '@/lib/pariprashna/samiksha/reviewConfirm'
import { transitionLifecycle, type LedgerExecutor } from '@/lib/pariprashna/samiksha/writer'
import { LEDGER_TABLE, toNumrangeLiteral, toDaterangeLiteral, type LedgerRow } from '@/lib/pariprashna/samiksha/schema'
import { isTurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'
import { getConversation } from '@/lib/conversations'
import { archivedReadOnlyResponse, isCorrectionArchived } from '@/lib/conversations/readOnly'

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
  const profile = await query<{ role: string; status: string }>('SELECT role,status FROM profiles WHERE id=$1', [user.uid])
  if (profile.rows[0]?.status !== 'active') return res.forbidden()
  const isSuperAdmin = profile.rows[0]?.role === 'super_admin'
  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role: isSuperAdmin ? 'super_admin' : 'guest' },
    chartId: body.chartId,
    db: { query },
  })
  if (permission !== 'all') return res.forbidden()

  // Jātaka chart workspace: load and authorize the referenced conversation
  // before any write. A missing, inaccessible or other-chart conversation gets
  // the same 404 (no enumeration); correction-history is read-only, so neither
  // confirm nor dismiss may touch the stamp, lifecycle or ledger for it.
  const conversation = await getConversation({ id: body.conversationId, userId: user.uid, isSuperAdmin: false })
  if (!conversation || conversation.chart_id !== body.chartId || conversation.module !== 'consume') return res.notFound('conversation')
  if (isCorrectionArchived(conversation)) return archivedReadOnlyResponse()

  if (conversation.archived_at) return Response.json({ error: 'This conversation is read-only.' }, { status: 409 })
  if (!body.messagePartId) return res.badRequest('A saved prediction is required.')
  const source = await query<{ conversation_id: string }>(`SELECT cm.conversation_id FROM message_parts mp
    JOIN conversation_messages cm ON cm.id=mp.message_id WHERE mp.id=$1
      AND mp.kind='prediction_candidate' AND cm.role='assistant'`, [body.messagePartId])
  if (source.rows[0]?.conversation_id !== body.conversationId) return res.notFound('message part')


  try {
    const row = await withTransaction(async client => {
      const parent = await client.query(`SELECT id FROM conversations WHERE id=$1 AND user_id=$2 AND archived_at IS NULL FOR UPDATE`, [body.conversationId, user.uid])
      if (parent.rows.length !== 1) throw new Error('unavailable')
      const result = await client.query<LedgerRow & { source_metadata: Record<string, unknown> }>(
        `SELECT l.*, cm.metadata_json AS source_metadata FROM ${LEDGER_TABLE} l
           JOIN message_parts mp ON mp.id=l.message_part_id
           JOIN conversation_messages cm ON cm.id=mp.message_id
         WHERE l.message_part_id=$1 AND l.chart_id=$2 AND cm.conversation_id=$3
           AND cm.role='assistant' AND mp.kind='prediction_candidate' AND l.chart_context_stale_at IS NULL
         ORDER BY l.created_at,l.id FOR UPDATE OF l`, [body.messagePartId, body.chartId, body.conversationId])
      const existing = result.rows[0]
      if (!existing || result.rows.length !== 1) throw new Error('unavailable')
      const exec: LedgerExecutor = async <T,>(sql: string, params?: unknown[]) => {
        const value = await client.query(sql, params)
        return { rows: value.rows as T[], rowCount: value.rowCount }
      }
      // Both the stream and the review tab operate on this captured row. Repeated
      // submissions return its existing result instead of creating duplicate claims.
      if (body.action === 'dismiss') {
        if (existing.lifecycle_status === 'dismissed') return existing
        return transitionLifecycle(existing.id, 'dismissed', { dismissed_reason: body.reason }, exec)
      }
      if (['confirmed', 'open', 'window_closed', 'outcome_recorded', 'unverifiable'].includes(existing.lifecycle_status)) return existing
      if (existing.lifecycle_status !== 'detected') throw new Error('unavailable')
      const stamp = existing.source_metadata.provenance_stamp
      if (!isTurnProvenanceStamp(stamp)) throw new Error('missing provenance')
      // Preserve server-captured claim/grounding; apply only explicit human edits.
      const edits = body.edits
      const start = edits?.window_start ?? null
      const end = edits?.window_end ?? null
      if ((start || end) && !(start && end && start <= end)) throw new Error('invalid window')
      await client.query(`UPDATE ${LEDGER_TABLE} SET confidence=$2::numrange,
        claim_text=COALESCE($3,claim_text), domain=CASE WHEN $4 THEN $5 ELSE domain END,
        direction=CASE WHEN $6 THEN $7 ELSE direction END,
        "window"=CASE WHEN $8 THEN $9::daterange ELSE "window" END WHERE id=$1`,
        [existing.id, toNumrangeLiteral(body.confidence), edits?.claim_text ?? null,
         !!edits && 'domain' in edits, edits?.domain ?? null, !!edits && 'direction' in edits, edits?.direction ?? null,
         !!edits && ('window_start' in edits || 'window_end' in edits), start && end ? toDaterangeLiteral({ start, end }) : null])
      return confirmDetectedCandidate({ rowId: existing.id, stamp: toLedgerStamp(stamp), setBandIfMissing: false }, exec)
    })
    const { source_metadata: _privateMetadata, ...safeRow } = row as typeof row & { source_metadata?: unknown }
    return NextResponse.json({ ok: true, ledger_row: safeRow })
  } catch (err) {
    console.error('[pariprashna/samiksha/confirm] failed', err)
    return Response.json({ error: 'This prediction could not be updated. Refresh the review and try again.' }, { status: 409 })
  }
}
