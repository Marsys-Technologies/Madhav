import { z } from 'zod'
import { getServerUser } from '@/lib/firebase/server'
import { query, withTransaction } from '@/lib/db/client'
import { ownedReading, answerBelongsToReading } from '@/lib/conversations/reading'
import { uuidLike } from '@/lib/conversations/consultation'
import { res } from '@/lib/errors'

const Body = z.object({ hide_reasoning: z.boolean().default(false), hide_methodology: z.boolean().default(false),
  messageId: z.string().regex(uuidLike).optional(), expiresInDays: z.union([z.literal(7), z.literal(30)]).optional() }).strict()
const noStore = { 'Cache-Control': 'private, no-store' }
function scope(req: Request) { return new URL(req.url).searchParams.get('messageId') }
function foreignOrigin(req: Request) { const origin = req.headers.get('origin'); return req.headers.get('sec-fetch-site') === 'cross-site' || (origin && origin !== new URL(req.url).origin) }
function generateSlug() { return crypto.randomUUID().replaceAll('-', '') }

export async function GET(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()
  const { id } = await ctx.params
  const messageId = scope(req)
  if (messageId && !uuidLike.test(messageId)) return res.badRequest('Valid answer required')
  try {
    if (!await ownedReading(id, user.uid)) return res.notFound('conversation')
    const { rows } = await query(`SELECT slug, created_at, expires_at, hide_reasoning, hide_methodology, message_id
      FROM conversation_shares WHERE conversation_id=$1 AND message_id IS NOT DISTINCT FROM $2::uuid
      AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at>now()) ORDER BY created_at DESC, id LIMIT 1`, [id, messageId])
    return Response.json({ share: rows[0] ?? null }, { headers: noStore })
  } catch { return res.dbError() }
}

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()
  if (foreignOrigin(req)) return res.forbidden()
  const { id } = await ctx.params
  let raw: unknown
  try { raw = await req.json() } catch { return res.badRequest('Invalid share options') }
  const parsed = Body.safeParse(raw)
  if (!parsed.success) return res.badRequest('Invalid share options')
  const { messageId, hide_reasoning, hide_methodology, expiresInDays } = parsed.data
  try {
    const conversation = await ownedReading(id, user.uid)
    if (!conversation) return res.notFound('conversation')
    if (conversation.archived_at) return Response.json({ error: 'Historical conversations are read-only.' }, { status: 409 })
    if (messageId && !await answerBelongsToReading(id, messageId)) return res.notFound('answer')
    const slug = await withTransaction(async client => {
      // Serialize scope creation and chart-correction archive on the existing parent row.
      const parent = await client.query(`SELECT id FROM conversations WHERE id=$1 AND user_id=$2 AND archived_at IS NULL FOR UPDATE`, [id, user.uid])
      if (parent.rows.length !== 1) return null
      const existing = await client.query<{ slug: string; hide_reasoning: boolean; hide_methodology: boolean }>(`SELECT slug, hide_reasoning, hide_methodology FROM conversation_shares
        WHERE conversation_id=$1 AND message_id IS NOT DISTINCT FROM $2::uuid AND revoked_at IS NULL
          AND (expires_at IS NULL OR expires_at>now()) ORDER BY created_at DESC, id LIMIT 1`, [id, messageId ?? null])
      const prior = existing.rows[0]
      // A changed disclosure must not silently reuse a link with different options.
      if (prior && prior.hide_reasoning === hide_reasoning && prior.hide_methodology === hide_methodology && !expiresInDays) return prior.slug
      const next = generateSlug()
      await client.query(`INSERT INTO conversation_shares (conversation_id, slug, created_by, hide_reasoning, hide_methodology, message_id, expires_at)
        VALUES ($1,$2,$3,$4,$5,$6,CASE WHEN $7::int IS NULL THEN NULL ELSE now()+make_interval(days=>$7::int) END)`,
        [id, next, user.uid, hide_reasoning, hide_methodology, messageId ?? null, expiresInDays ?? null])
      return next
    })
    if (!slug) return Response.json({ error: 'This conversation is unavailable for sharing.' }, { status: 409 })
    return Response.json({ slug }, { headers: noStore })
  } catch { return res.dbError() }
}

export async function DELETE(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()
  if (foreignOrigin(req)) return res.forbidden()
  const { id } = await ctx.params
  const messageId = scope(req)
  if (messageId && !uuidLike.test(messageId)) return res.badRequest('Valid answer required')
  try {
    if (!await ownedReading(id, user.uid)) return res.notFound('conversation')
    await query(`UPDATE conversation_shares SET revoked_at=now() WHERE conversation_id=$1 AND message_id IS NOT DISTINCT FROM $2::uuid AND revoked_at IS NULL`, [id, messageId])
    return Response.json({ ok: true }, { headers: noStore })
  } catch { return res.dbError() }
}
