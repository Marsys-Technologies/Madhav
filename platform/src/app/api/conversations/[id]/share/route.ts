import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { res } from '@/lib/errors'
import { getFlag } from '@/lib/config/index'
import { SHARE_DEFAULT_TTL_DAYS } from '@/lib/share/constants'
import { shareMutationLimiter } from '@/lib/share/share_rate_limit'

// Share create/revoke is limited per VERIFIED user (SS N-376 / PR-S4). Call only
// after getServerUser() succeeded; the key is the verified uid, never client input.
function rateLimitShareMutation(uid: string) {
  const verdict = shareMutationLimiter.check(`share:${uid}`)
  if (verdict.allowed) return null
  return res.rateLimited(
    'Too many share link changes. Please wait before creating or revoking more links.',
    verdict.retryAfterSeconds,
  )
}

async function resolveAccess(userId: string) {
  const result = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [userId]
  )
  return result.rows[0]?.role === 'super_admin'
}

// URL-safe 10-char slug (~58 bits of entropy). A convenience link, not the only
// credential: the share page also requires a verified, active session.
function generateSlug(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(10))
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let out = ''
  for (const b of bytes) out += chars[b % chars.length]
  return out
}

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    const { rows } = await query<{
      slug: string
      created_at: string
      expires_at: string | null
      revoked_at: string | null
      hide_reasoning: boolean
      hide_methodology: boolean
    }>(
      'SELECT slug, created_at, expires_at, revoked_at, hide_reasoning, hide_methodology FROM conversation_shares WHERE conversation_id=$1 AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now()) ORDER BY created_at DESC LIMIT 1',
      [id]
    )

    return Response.json({ share: rows[0] ?? null })
  } catch {
    return res.dbError()
  }
}

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()
  const limited = rateLimitShareMutation(user.uid)
  if (limited) return limited

  let hideReasoning = false
  let hideMethodology = false
  if (getFlag('R10_SELECTIVE_SHARE')) {
    try {
      const body = await req.json() as { hide_reasoning?: boolean; hide_methodology?: boolean }
      hideReasoning = body.hide_reasoning === true
      hideMethodology = body.hide_methodology === true
    } catch {}
  }

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    // Reuse the active share if one exists — idempotent from the user's POV.
    // An expired share is not active: reusing it would hand back a dead link.
    const existing = await query<{ slug: string }>(
      'SELECT slug FROM conversation_shares WHERE conversation_id=$1 AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now()) LIMIT 1',
      [id]
    )
    if (existing.rows[0]) return Response.json({ slug: existing.rows[0].slug })

    const slug = generateSlug()
    await query(
      "INSERT INTO conversation_shares (conversation_id, slug, created_by, hide_reasoning, hide_methodology, expires_at) VALUES ($1,$2,$3,$4,$5, now() + make_interval(days => $6::int)) RETURNING *",
      [id, slug, user.uid, hideReasoning, hideMethodology, SHARE_DEFAULT_TTL_DAYS]
    )

    return Response.json({ slug })
  } catch {
    return res.dbError()
  }
}

export async function DELETE(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()
  const limited = rateLimitShareMutation(user.uid)
  if (limited) return limited

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    await query(
      'UPDATE conversation_shares SET revoked_at=now() WHERE conversation_id=$1 AND revoked_at IS NULL',
      [id]
    )

    return Response.json({ ok: true })
  } catch {
    return res.dbError()
  }
}
