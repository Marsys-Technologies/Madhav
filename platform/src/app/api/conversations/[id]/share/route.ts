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

// A share is ACTIVE when it is not revoked and not expired. Rows with
// expires_at NULL (pre-TTL shares) stay active until revoked.
const ACTIVE_SHARE_PREDICATE = 'revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now())'
const SHARE_COLUMNS = 'slug, created_at, expires_at, revoked_at, hide_reasoning, hide_methodology'

type ShareRow = {
  slug: string
  created_at: string
  expires_at: string | null
  revoked_at: string | null
  hide_reasoning: boolean
  hide_methodology: boolean
}

function isActiveShare(row: ShareRow, nowMs: number): boolean {
  if (row.revoked_at) return false
  if (row.expires_at && new Date(row.expires_at).getTime() <= nowMs) return false
  return true
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

    // SS N-383: a conversation can hold several active shares (one per distinct
    // hide-option pair). `share` keeps its old shape (the most recent active share)
    // so existing clients are unaffected; `shares` additively lists all of them.
    const { rows } = await query<ShareRow>(
      `SELECT ${SHARE_COLUMNS} FROM conversation_shares WHERE conversation_id=$1 AND ${ACTIVE_SHARE_PREDICATE} ORDER BY created_at DESC`,
      [id]
    )

    // SS N-379: tell the dialog whether hide options are OFFERED on a NEW share.
    // (The share PAGE applies a stored share's options regardless of this flag.)
    return Response.json({
      share: rows[0] ?? null,
      shares: rows,
      selective_share_enabled: getFlag('R10_SELECTIVE_SHARE'),
    })
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

  // R10_SELECTIVE_SHARE only controls whether hide options are OFFERED on a NEW
  // share: flag off -> the body is not even read and both options are stored false.
  // Stored options of existing shares are always honoured by the page (SS N-379).
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

    // SS N-383: reuse an ACTIVE share of this conversation only when it has exactly
    // the requested hide options (effective values: booleans, false when the flag
    // is off). Different options mint a NEW share; the old link keeps its own
    // options and stays active. The SQL filter is authoritative; isActiveShare is a
    // defensive re-check so an expired or revoked row can never be handed back.
    const existing = await query<ShareRow>(
      `SELECT ${SHARE_COLUMNS} FROM conversation_shares WHERE conversation_id=$1 AND ${ACTIVE_SHARE_PREDICATE} ORDER BY created_at DESC`,
      [id]
    )
    const nowMs = Date.now()
    const match = existing.rows.find(
      (row) =>
        isActiveShare(row, nowMs) &&
        row.hide_reasoning === hideReasoning &&
        row.hide_methodology === hideMethodology,
    )
    if (match) return Response.json({ slug: match.slug })

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
